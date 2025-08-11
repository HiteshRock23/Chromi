import os
import uuid
import logging
import gc
from django.conf import settings
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)


def convert_video_task(upload_path: str, output_filename: str, start_seconds: int, duration: int):
    """
    Background task: convert a trimmed segment of a video into a GIF suitable for Chrome backgrounds.
    Memory-conscious: loads without audio, trims early, downscales early, and ensures resources are closed.
    Returns a dict with converted_url on success.
    """
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'converted'), exist_ok=True)
    output_path = os.path.join(settings.MEDIA_ROOT, 'converted', output_filename)

    video = None
    trimmed_video = None
    try:
        video = VideoFileClip(upload_path, audio=False)

        if start_seconds >= video.duration:
            raise ValueError('Start time exceeds video duration')

        end_seconds = min(start_seconds + duration, video.duration)
        trimmed_video = video.subclip(start_seconds, end_seconds)

        # Early downscale
        trimmed_video = trimmed_video.resize(width=1280, height=720)

        trimmed_video.write_gif(
            output_path,
            fps=24,
            program='ffmpeg',
            opt='OptimizePlus',
            fuzz=1,
        )

        converted_url = f"{settings.MEDIA_URL}converted/{output_filename}"
        # Optional: if running under RQ, store meta
        try:
            # Import lazily to avoid hard dependency when RQ is not installed
            from importlib import import_module
            rq_module = import_module('rq')
            get_current_job = getattr(rq_module, 'get_current_job', None)
            if get_current_job is not None:
                job = get_current_job()
                if job is not None:
                    job.meta['converted_url'] = converted_url
                    job.save_meta()
        except Exception:
            pass

        return {'success': True, 'converted_url': converted_url}
    except Exception as exc:
        logger.exception("Background conversion failed: %s", exc)
        return {'success': False, 'error': str(exc)}
    finally:
        try:
            if trimmed_video is not None:
                trimmed_video.close()
        except Exception:
            pass
        try:
            if video is not None:
                video.close()
        except Exception:
            pass
        del trimmed_video
        del video
        gc.collect()

