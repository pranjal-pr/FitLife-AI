"""
Shared workout-analysis helpers used by the gateway and the standalone service.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config.settings import Config
from ..utils.video import process_video
from .models.yolo import get_yolo_model, get_yolo_models

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _is_huggingface_space() -> bool:
    return os.environ.get('FITLIFE_RUNTIME') == 'huggingface'


PROCESSED_DIR = (Path('/tmp/fitlife') if _is_huggingface_space() else PROJECT_ROOT / 'data') / 'processed' / 'videos'
STATIC_VIDEO_DIR = (Path('/tmp/fitlife') if _is_huggingface_space() else PROJECT_ROOT / 'web' / 'static') / 'videos'


def _exercise_label(exercise_type: str) -> str:
    return exercise_type.replace('_', ' ').title()


def _normalize_score(value: float | int | None) -> float:
    score = float(value or 0)
    return round(max(0.0, min(100.0, score * 10)), 1)


def _build_feedback(exercise_type: str, metrics: dict[str, Any]) -> list[str]:
    feedback: list[str] = []
    form_avg = float(metrics.get('form_metrics', {}).get('average', 0) or 0)
    depth_avg = float(metrics.get('depth_metrics', {}).get('average', 0) or 0)
    form_consistency = float(metrics.get('form_metrics', {}).get('consistency', 0) or 0)
    depth_consistency = float(metrics.get('depth_metrics', {}).get('consistency', 0) or 0)
    reps = int(metrics.get('repetitions', 0) or 0)

    if metrics.get('frames_analyzed', 0) == 0:
        return [
            'No confident pose detections were found. Re-record with the full body in frame and better lighting.',
            f'Use a clearer side or front angle for the {_exercise_label(exercise_type).lower()} to improve tracking.',
        ]

    if form_avg < 0.75:
        feedback.append('Form confidence is low. Slow the tempo and keep the lifter fully visible in frame.')
    elif form_avg < 0.9:
        feedback.append('Form looks mostly stable, but several frames were borderline. Tighten setup before each rep.')
    else:
        feedback.append('Form confidence stayed high for most of the set.')

    if depth_avg < 0.75:
        feedback.append('Range-of-motion confidence is inconsistent. Make sure the camera captures the full bottom position.')
    elif depth_avg >= 0.9:
        feedback.append('Depth tracking stayed strong across the set.')

    if form_consistency < 0.7 or depth_consistency < 0.7:
        feedback.append('Rep-to-rep consistency dropped. Keep stance, bar path, and camera angle fixed through the whole set.')

    if reps <= 1:
        feedback.append('The model only counted one clear rep. Longer clips usually produce more reliable rep estimates.')
    elif reps >= 8:
        feedback.append('Higher-rep sets can accumulate fatigue. Review the final reps first when checking technique drift.')

    return feedback[:4]


def format_analysis_result(
    exercise_type: str,
    metrics: dict[str, Any] | None,
    video_url: str | None = None,
) -> dict[str, Any]:
    metrics = metrics or {
        'frames_analyzed': 0,
        'repetitions': 0,
        'duration_seconds': 0,
        'form_metrics': {'average': 0.0, 'min': 0.0, 'max': 0.0, 'consistency': 0.0},
        'depth_metrics': {'average': 0.0, 'min': 0.0, 'max': 0.0, 'consistency': 0.0},
        'movement_assessment': {
            'form_quality': 0,
            'depth_quality': 0,
            'form_consistency': 0,
            'depth_consistency': 0,
            'score': 0.0,
        },
    }

    movement_assessment = dict(metrics.get('movement_assessment', {}))
    raw_score = float(movement_assessment.get('score', 0) or 0)
    form_score = _normalize_score(raw_score)

    return {
        'exercise_type': exercise_type,
        'exercise_label': _exercise_label(exercise_type),
        'form_score': form_score,
        'score': form_score,
        'raw_score': round(raw_score, 2),
        'reps': int(metrics.get('repetitions', 0) or 0),
        'rep_count': int(metrics.get('repetitions', 0) or 0),
        'frames_analyzed': int(metrics.get('frames_analyzed', 0) or 0),
        'duration_seconds': float(metrics.get('duration_seconds', 0) or 0),
        'feedback': _build_feedback(exercise_type, metrics),
        'recommendations': _build_feedback(exercise_type, metrics),
        'movement_assessment': movement_assessment,
        'form_metrics': metrics.get('form_metrics', {}),
        'depth_metrics': metrics.get('depth_metrics', {}),
        'video_url': video_url,
        'model_labels': get_yolo_model(exercise_type).names,
    }


def analyze_saved_video(video_path: str | Path, exercise_type: str) -> dict[str, Any]:
    if exercise_type not in Config.SUPPORTED_EXERCISES:
        raise ValueError(f'Unsupported exercise type: {exercise_type}')

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f'Video file not found: {video_path}')

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    stem = video_path.stem
    processed_path = PROCESSED_DIR / f'processed_{timestamp}_{stem}.mp4'
    web_filename = f'web_{timestamp}_{stem}.mp4'
    web_path = STATIC_VIDEO_DIR / web_filename
    wants_web_video = not _is_huggingface_space()

    models = get_yolo_models()
    metrics = process_video(
        str(video_path),
        str(processed_path),
        str(web_path) if wants_web_video else None,
        exercise_type,
        models[exercise_type],
    )

    video_url = f'/static/videos/{web_filename}' if wants_web_video and web_path.exists() else None

    if processed_path.exists():
        processed_path.unlink()

    return format_analysis_result(exercise_type, metrics, video_url=video_url)
