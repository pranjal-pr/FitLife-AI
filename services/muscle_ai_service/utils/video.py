"""
Video processing utilities
"""
import logging
import cv2
import torch
from ..core.models.analyzer import MovementAnalyzer

logger = logging.getLogger(__name__)


CORE_KEYPOINTS = (5, 6, 11, 12, 13, 14, 15, 16)


def _best_pose_index(result):
    """Choose the detection with the most reliable body joints."""
    keypoints = getattr(result, 'keypoints', None)
    scores = getattr(keypoints, 'conf', None) if keypoints is not None else None
    if scores is not None and len(scores) > 0:
        core_scores = scores[:, list(CORE_KEYPOINTS)]
        return int(core_scores.mean(dim=1).argmax().item())

    boxes = getattr(result, 'boxes', None)
    if boxes is not None and len(boxes) > 0:
        return int(boxes.conf.argmax().item())
    return None


def process_video(video_path, output_path, web_path, exercise_type, yolo_model):
    """
    Process a video using the YOLO model and movement analyzer
    
    Args:
        video_path (str): Path to the input video
        output_path (str): Path for the processed video
        web_path (str): Path for the web-friendly video
        exercise_type (str): Type of exercise for analysis
        yolo_model: The YOLO model to use for detection
        
    Returns:
        dict: Movement metrics
    """
    try:
        use_gpu = torch.cuda.is_available()
        logger.info(f"Processing video with GPU acceleration: {use_gpu}")
        
        analyzer = MovementAnalyzer(exercise_type)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError("Error opening video file")

        # Get video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_seconds = round(total_frames / fps, 2) if fps else 0

        # Use an MP4-compatible codec for the intermediate output on both CPU and GPU.
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        out = cv2.VideoWriter(
            output_path,
            fourcc,
            fps,
            (frame_width, frame_height)
        )

        # Batch processing parameters
        batch_size = 4 if use_gpu else 1
        
        for frame_offset in range(0, total_frames, batch_size):
            frames_buffer = []
            for _ in range(batch_size):
                ret, frame = cap.read()
                if ret:
                    frames_buffer.append(frame)
                else:
                    break

            if not frames_buffer:
                break

            # Ultralytics accepts OpenCV frames directly and performs the required
            # BGR-to-RGB, BHWC-to-BCHW, resize, and normalization steps itself.
            # Passing a manually-created BHWC CUDA tensor bypasses that preprocessing
            # and crashes on GPU with an incompatible input-shape error.
            results = yolo_model(
                frames_buffer,
                stream=True,
                verbose=False,
                device=0 if use_gpu else 'cpu',
                # These custom pose checkpoints retain accurate keypoints on
                # real-world footage even when their movement-class confidence
                # is low. The scorer validates joint confidence separately.
                conf=0.01,
                iou=0.5,
                max_det=3,
            )

            # Process results
            for frame, result in zip(frames_buffer, results):
                labels = {}
                pose_index = _best_pose_index(result)
                pose_xy = None
                pose_scores = None

                if pose_index is not None and result.boxes is not None and len(result.boxes) > pose_index:
                    box = result.boxes[pose_index]
                    class_id = int(box.cls)
                    labels[result.names[class_id]] = float(box.conf)

                if pose_index is not None and getattr(result, 'keypoints', None) is not None:
                    keypoints_xy = getattr(result.keypoints, 'xy', None)
                    keypoints_conf = getattr(result.keypoints, 'conf', None)
                    if keypoints_xy is not None and len(keypoints_xy) > pose_index:
                        pose_xy = keypoints_xy[pose_index].detach().cpu().numpy()
                    if keypoints_conf is not None and len(keypoints_conf) > pose_index:
                        pose_scores = keypoints_conf[pose_index].detach().cpu().numpy()

                form_value, down_value = analyzer.process_frame(
                    labels,
                    keypoints=pose_xy,
                    keypoint_scores=pose_scores,
                    frame_shape=frame.shape,
                )

                if pose_xy is not None:
                    for index, point in enumerate(pose_xy):
                        if pose_scores is not None and pose_scores[index] < 0.15:
                            continue
                        x, y = int(point[0]), int(point[1])
                        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

                metrics = analyzer.get_metrics()
                if metrics:
                    cv2.putText(frame, f"Score: {metrics['movement_assessment']['score']}/10",
                              (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f"Reps: {metrics['repetitions']}",
                              (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                out.write(frame)

            # Clear GPU cache periodically
            if use_gpu and frame_offset % (batch_size * 10) == 0:
                torch.cuda.empty_cache()

        cap.release()
        out.release()

        metrics = analyzer.get_metrics() or {
            'frames_analyzed': 0,
            'repetitions': 0,
            'form_metrics': {
                'average': 0.0,
                'min': 0.0,
                'max': 0.0,
                'consistency': 0.0,
            },
            'depth_metrics': {
                'average': 0.0,
                'min': 0.0,
                'max': 0.0,
                'consistency': 0.0,
            },
            'movement_assessment': {
                'form_quality': 0,
                'depth_quality': 0,
                'form_consistency': 0,
                'depth_consistency': 0,
                'score': 0.0,
            },
        }
        metrics['duration_seconds'] = duration_seconds
        metrics['fps'] = round(fps, 2) if fps else 0
        metrics['web_video_available'] = False

        # Convert to web format if moviepy/ffmpeg is available. Analysis still succeeds without it.
        if web_path:
            try:
                from moviepy.video.io.VideoFileClip import VideoFileClip  # type: ignore

                logger.info("Converting video to web format")
                clip = VideoFileClip(output_path)
                try:
                    if use_gpu:
                        clip.write_videofile(
                            web_path,
                            codec='libx264',
                            preset='fast',
                            threads=4,
                            ffmpeg_params=[
                                '-hwaccel', 'cuda',
                                '-hwaccel_output_format', 'cuda',
                                '-c:v', 'h264_nvenc',
                                '-preset', 'p4',
                                '-tune', 'zerolatency',
                            ],
                        )
                    else:
                        clip.write_videofile(web_path, codec='libx264')
                    metrics['web_video_available'] = True
                finally:
                    clip.close()
            except Exception as conversion_error:
                logger.warning(f"Skipping web video conversion: {conversion_error}")

        return metrics

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        raise
