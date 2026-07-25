from __future__ import annotations

import unittest

import numpy as np

from services.muscle_ai_service.core.models.analyzer import MovementAnalyzer


def _pose(*, bottom: bool) -> tuple[np.ndarray, np.ndarray]:
    points = np.zeros((17, 2), dtype=float)
    scores = np.full(17, 0.85, dtype=float)

    if bottom:
        points[6] = (75, 55)   # right shoulder
        points[12] = (55, 85)  # right hip
        points[14] = (70, 120) # right knee
        points[16] = (70, 165) # right ankle
    else:
        points[6] = (70, 40)
        points[12] = (70, 85)
        points[14] = (70, 125)
        points[16] = (70, 165)

    # Make the unused side less attractive but still visible.
    points[5] = points[6] + (-4, 0)
    points[11] = points[12] + (-4, 0)
    points[13] = points[14] + (-4, 0)
    points[15] = points[16] + (-4, 0)
    scores[[5, 11, 13, 15]] = 0.45
    return points, scores


class MovementAnalyzerTests(unittest.TestCase):
    def test_pose_sequence_produces_nonzero_metrics_and_rep(self):
        analyzer = MovementAnalyzer("regular_deadlift")
        top = _pose(bottom=False)
        bottom = _pose(bottom=True)

        sequence = [top] * 5 + [bottom] * 5 + [top] * 5
        for points, scores in sequence:
            analyzer.process_frame(
                {},
                keypoints=points,
                keypoint_scores=scores,
                frame_shape=(200, 140, 3),
            )

        metrics = analyzer.get_metrics()
        self.assertIsNotNone(metrics)
        assert metrics is not None
        self.assertEqual(metrics["frames_analyzed"], 15)
        self.assertGreater(metrics["movement_assessment"]["score"], 0)
        self.assertGreaterEqual(metrics["repetitions"], 1)

    def test_no_detection_returns_no_metrics(self):
        analyzer = MovementAnalyzer("regular_deadlift")
        analyzer.process_frame({})
        self.assertIsNone(analyzer.get_metrics())


if __name__ == "__main__":
    unittest.main()
