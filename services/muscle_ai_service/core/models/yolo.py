"""
YOLO model loader module
"""
import logging
from functools import lru_cache
from pathlib import Path
import torch

from ...config.settings import Config

logger = logging.getLogger(__name__)

def setup_gpu():
    """Configure GPU settings if available"""
    if torch.cuda.is_available():
        logger.info("CUDA is available. Setting up GPU acceleration")
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.enabled = True
        return True
    logger.info("CUDA not available. Using CPU")
    return False

@lru_cache(maxsize=6)
def get_yolo_model(exercise_type):
    """Load one exercise checkpoint on demand."""
    if exercise_type not in Config.MODEL_PATHS:
        raise ValueError(f"Unsupported exercise type: {exercise_type}")

    from ultralytics import YOLO  # type: ignore

    model_path = Config.MODEL_PATHS[exercise_type]
    if not Path(model_path).exists():
        raise FileNotFoundError(
            f"Missing model checkpoint for {exercise_type}: {model_path}"
        )

    logger.info("Loading YOLO model for %s", exercise_type)
    model = YOLO(model_path)
    if setup_gpu():
        model.to("cuda")
        model.conf = 0.3
        model.iou = 0.45
        model.half()
    return model


@lru_cache(maxsize=1)
def get_yolo_models():
    """Load and optimize YOLO models"""
    try:
        logger.info("Loading YOLO models...")
        models = {
            exercise_type: get_yolo_model(exercise_type)
            for exercise_type in Config.MODEL_PATHS
        }
        logger.info("Models loaded successfully")
        return models
    except Exception as e:
        logger.error(f"Error loading YOLO models: {e}")
        raise
