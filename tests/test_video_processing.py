from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

from services.muscle_ai_service.utils import video as video_module


class _FakeCapture:
    def __init__(self, frame: np.ndarray):
        self.frames = [frame]

    def isOpened(self):
        return True

    def get(self, property_id):
        values = {
            video_module.cv2.CAP_PROP_FRAME_WIDTH: 64,
            video_module.cv2.CAP_PROP_FRAME_HEIGHT: 64,
            video_module.cv2.CAP_PROP_FPS: 10,
            video_module.cv2.CAP_PROP_FRAME_COUNT: 1,
        }
        return values[property_id]

    def read(self):
        if self.frames:
            return True, self.frames.pop(0)
        return False, None

    def release(self):
        return None


class _FakeWriter:
    def __init__(self):
        self.frames = []

    def write(self, frame):
        self.frames.append(frame)

    def release(self):
        return None


class _FakeResult:
    boxes = None
    keypoints = None
    names = {}


class _FakeYolo:
    def __init__(self):
        self.source = None
        self.options = None

    def __call__(self, source, **options):
        self.source = source
        self.options = options
        return iter([_FakeResult() for _ in source])


class VideoProcessingTests(unittest.TestCase):
    def test_gpu_path_leaves_frame_preprocessing_to_ultralytics(self):
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        capture = _FakeCapture(frame)
        writer = _FakeWriter()
        model = _FakeYolo()

        with (
            patch.object(video_module.cv2, 'VideoCapture', return_value=capture),
            patch.object(video_module.cv2, 'VideoWriter', return_value=writer),
            patch.object(video_module.torch.cuda, 'is_available', return_value=True),
            patch.object(video_module.torch.cuda, 'empty_cache'),
        ):
            metrics = video_module.process_video(
                'input.mp4',
                'output.mp4',
                None,
                'regular_deadlift',
                model,
            )

        self.assertIsInstance(model.source, list)
        self.assertEqual(model.source[0].shape, (64, 64, 3))
        self.assertEqual(
            model.options,
            {
                'stream': True,
                'verbose': False,
                'device': 0,
            },
        )
        self.assertEqual(len(writer.frames), 1)
        self.assertEqual(metrics['frames_analyzed'], 0)


if __name__ == '__main__':
    unittest.main()
