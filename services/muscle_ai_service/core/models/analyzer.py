"""Pose-based movement analysis for the workout checkpoints."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


# COCO keypoint indexes produced by the YOLO pose checkpoints.
LEFT_SIDE = (5, 11, 13, 15)  # shoulder, hip, knee, ankle
RIGHT_SIDE = (6, 12, 14, 16)
CORE_KEYPOINTS = (5, 6, 11, 12, 13, 14, 15, 16)


def _clip(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return float(max(minimum, min(maximum, value)))


def _angle(first: np.ndarray, center: np.ndarray, last: np.ndarray) -> float | None:
    """Return the smaller angle between three points in degrees."""
    first_vector = first - center
    last_vector = last - center
    denominator = float(np.linalg.norm(first_vector) * np.linalg.norm(last_vector))
    if denominator <= 1e-6:
        return None
    cosine = float(np.dot(first_vector, last_vector) / denominator)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _moving_median(values: list[float], window: int = 5) -> np.ndarray:
    source = np.asarray(values, dtype=float)
    if len(source) < 3:
        return source

    radius = max(1, window // 2)
    return np.asarray(
        [
            np.median(source[max(0, index - radius) : index + radius + 1])
            for index in range(len(source))
        ],
        dtype=float,
    )


class MovementAnalyzer:
    """Turn YOLO pose keypoints into form, depth, and repetition metrics.

    The checkpoints classify movement phases (``down``, ``ibw``, ``up``).
    Their class probability is not a form score. Older code treated that
    probability as form quality and required two different phase classes in
    the same clip, which caused clear out-of-domain videos to return 0/10.
    This analyzer instead uses the checkpoint's body keypoints and derives the
    movement phase from joint geometry.
    """

    def __init__(self, exercise_type: str):
        self.exercise_type = exercise_type
        self.form_scores: list[float] = []
        self.phase_values: list[float] = []
        self.total_frames_seen = 0
        self.pose_frames = 0

    @property
    def _is_squat(self) -> bool:
        return self.exercise_type in {"squat", "front_squat", "zercher_squat"}

    def _pose_measurements(
        self,
        keypoints: Any,
        keypoint_scores: Any,
        frame_shape: tuple[int, ...] | None,
    ) -> tuple[float, float] | None:
        points = np.asarray(keypoints, dtype=float)
        scores = np.asarray(keypoint_scores, dtype=float).reshape(-1)
        if points.ndim != 2 or points.shape[0] < 17 or points.shape[1] < 2:
            return None
        if scores.shape[0] < 17:
            return None

        side = max(
            (LEFT_SIDE, RIGHT_SIDE),
            key=lambda indexes: float(np.mean(scores[list(indexes)])),
        )
        shoulder, hip, knee, ankle = side
        side_scores = scores[list(side)]
        visible_side = side_scores >= 0.15
        if int(np.count_nonzero(visible_side)) < 3 or float(np.mean(side_scores)) < 0.20:
            return None

        knee_angle = _angle(points[hip], points[knee], points[ankle])
        hip_angle = _angle(points[shoulder], points[hip], points[knee])
        if knee_angle is None or hip_angle is None:
            return None

        torso_vector = points[shoulder] - points[hip]
        torso_angle = abs(
            math.degrees(math.atan2(float(torso_vector[1]), float(torso_vector[0])))
        )
        torso_angle = min(torso_angle, 180.0 - torso_angle)

        # Reject obviously collapsed skeletons while retaining side-on poses,
        # where the left and right joints naturally overlap.
        height, width = (frame_shape or (1, 1))[:2]
        frame_diagonal = max(1.0, math.hypot(float(width), float(height)))
        segment_lengths = [
            float(np.linalg.norm(points[shoulder] - points[hip])),
            float(np.linalg.norm(points[hip] - points[knee])),
            float(np.linalg.norm(points[knee] - points[ankle])),
        ]
        usable_segments = sum(length >= frame_diagonal * 0.015 for length in segment_lengths)
        if usable_segments < 2:
            return None

        core_scores = scores[list(CORE_KEYPOINTS)]
        coverage = float(np.mean(core_scores >= 0.15))
        side_confidence = float(np.mean(side_scores))
        geometry_quality = usable_segments / len(segment_lengths)

        # Confidence indicates how reliably the body joints were localized.
        # Rescale it because pose confidences around 0.5-0.8 are normal even
        # for clear real-world footage outside the training set.
        localization_quality = _clip((side_confidence - 0.15) / 0.70)
        form_quality = _clip(
            0.45
            + 0.35 * localization_quality
            + 0.12 * coverage
            + 0.08 * geometry_quality
        )

        knee_extension = _clip((knee_angle - 70.0) / 110.0)
        hip_extension = _clip((hip_angle - 70.0) / 110.0)
        torso_extension = _clip((torso_angle - 20.0) / 70.0)

        if self._is_squat:
            phase = (
                0.50 * knee_extension
                + 0.30 * hip_extension
                + 0.20 * torso_extension
            )
        else:
            phase = (
                0.25 * knee_extension
                + 0.35 * hip_extension
                + 0.40 * torso_extension
            )

        return form_quality, _clip(phase)

    def _legacy_measurements(self, labels: dict[str, float]) -> tuple[float, float] | None:
        """Use phase labels only when a checkpoint does not expose keypoints."""
        if not labels:
            return None

        label, confidence = max(labels.items(), key=lambda item: item[1])
        confidence = _clip(float(confidence))
        if confidence < 0.05:
            return None

        phases = {"down": 0.0, "bottom_position": 0.0, "ibw": 0.5, "up": 1.0}
        phase = phases.get(label)
        if phase is None:
            return None

        # This fallback measures tracking quality, not biomechanical form.
        tracking_quality = _clip(0.45 + confidence * 0.55)
        return tracking_quality, phase

    def process_frame(
        self,
        labels: dict[str, float],
        *,
        keypoints: Any = None,
        keypoint_scores: Any = None,
        frame_shape: tuple[int, ...] | None = None,
    ) -> tuple[float | None, float | None]:
        """Process one frame and return form quality and movement phase."""
        self.total_frames_seen += 1
        measurements = None
        if keypoints is not None and keypoint_scores is not None:
            measurements = self._pose_measurements(
                keypoints,
                keypoint_scores,
                frame_shape,
            )
            if measurements is not None:
                self.pose_frames += 1

        if measurements is None:
            measurements = self._legacy_measurements(labels)
        if measurements is None:
            return None, None

        form_quality, phase = measurements
        self.form_scores.append(form_quality)
        self.phase_values.append(phase)
        return form_quality, phase

    def _count_repetitions(self, smoothed_phases: np.ndarray) -> int:
        if len(smoothed_phases) < 8:
            return 0

        bottom = float(np.quantile(smoothed_phases, 0.05))
        top = float(np.quantile(smoothed_phases, 0.90))
        movement_range = top - bottom
        if movement_range < 0.14:
            return 0

        down_threshold = bottom + movement_range * 0.30
        up_threshold = bottom + movement_range * 0.70
        in_bottom = False
        down_streak = 0
        up_streak = 0
        repetitions = 0

        for phase in smoothed_phases:
            if not in_bottom:
                down_streak = down_streak + 1 if phase <= down_threshold else 0
                if down_streak >= 2:
                    in_bottom = True
                    down_streak = 0
            else:
                up_streak = up_streak + 1 if phase >= up_threshold else 0
                if up_streak >= 2:
                    repetitions += 1
                    in_bottom = False
                    up_streak = 0

        return repetitions

    def get_metrics(self) -> dict[str, Any] | None:
        """Calculate aggregate workout metrics."""
        if not self.form_scores or not self.phase_values:
            return None

        form = np.asarray(self.form_scores, dtype=float)
        phases = _moving_median(self.phase_values)
        phase_bottom = float(np.quantile(phases, 0.05))
        phase_top = float(np.quantile(phases, 0.95))
        movement_range = max(0.0, phase_top - phase_bottom)

        expected_range = 0.42 if self._is_squat else 0.35
        depth_quality = _clip((movement_range - 0.06) / (expected_range - 0.06))
        form_consistency = _clip(1.0 - float(np.std(form)) * 1.75)
        phase_differences = np.diff(phases)
        depth_consistency = _clip(
            1.0 - (float(np.std(phase_differences)) * 3.5 if len(phase_differences) else 0.0)
        )

        form_average = float(np.mean(form))
        overall_score = (
            form_average * 0.50
            + depth_quality * 0.30
            + form_consistency * 0.10
            + depth_consistency * 0.10
        ) * 10.0

        return {
            "frames_analyzed": len(self.form_scores),
            "frames_seen": self.total_frames_seen,
            "pose_frames": self.pose_frames,
            "repetitions": self._count_repetitions(phases),
            "form_metrics": {
                "average": round(form_average, 4),
                "min": round(float(np.min(form)), 4),
                "max": round(float(np.max(form)), 4),
                "consistency": round(form_consistency, 4),
            },
            "depth_metrics": {
                "average": round(depth_quality, 4),
                "min": round(phase_bottom, 4),
                "max": round(phase_top, 4),
                "range": round(movement_range, 4),
                "consistency": round(depth_consistency, 4),
            },
            "movement_assessment": {
                "form_quality": self.get_quality_assessment(form_average),
                "depth_quality": self.get_quality_assessment(depth_quality),
                "form_consistency": self.get_quality_assessment(form_consistency),
                "depth_consistency": self.get_quality_assessment(depth_consistency),
                "score": round(overall_score, 1),
            },
        }

    @staticmethod
    def get_quality_assessment(value: float) -> int:
        return int(round(_clip(float(value)) * 10))
