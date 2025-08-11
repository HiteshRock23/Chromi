import os
import uuid
import logging
import gc
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from moviepy.editor import VideoFileClip
import importlib

try:
    import tracemalloc  # stdlib; used for memory tracking when enabled
except Exception:  # pragma: no cover
    tracemalloc = None

# Set up logging
logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def home(request):
    """Render the home page with the video converter interface."""
    return render(request, 'converter/home.html')

def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({'status': 'healthy', 'message': 'Chromi is running!'})

def convert_video(request):
    """Convert uploaded video to Chrome-compatible background format (GIF) with trimming."""
    if request.method == 'POST' and request.FILES.get('video'):
        try:
            # Get the uploaded file
            video_file = request.FILES['video']
            
            # Check file extension
            file_ext = os.path.splitext(video_file.name)[1].lower()
            if file_ext not in ['.mp4', '.mov', '.webm', '.gif']:
                return JsonResponse({'error': 'Only .mp4, .mov, .webm, and .gif files are supported'}, status=400)
            
            # Ensure media directories exist
            os.makedirs(os.path.join(settings.MEDIA_ROOT, 'uploads'), exist_ok=True)
            os.makedirs(os.path.join(settings.MEDIA_ROOT, 'converted'), exist_ok=True)
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            upload_path = os.path.join(settings.MEDIA_ROOT, 'uploads', unique_filename)
            
            # Save the uploaded file
            with open(upload_path, 'wb+') as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)
            
            # Generate output filename
            output_filename = f"{uuid.uuid4()}.gif"
            output_path = os.path.join(settings.MEDIA_ROOT, 'converted', output_filename)
            
            # Get trim parameters
            start_time = request.POST.get('start_time', '00:00:00')
            duration = int(request.POST.get('duration', 6))
            
            # Set duration to 6 seconds (Chrome background requirement)
            duration = 6
            
            # Convert start time from HH:MM:SS to seconds
            start_seconds = 0
            if start_time and start_time != '00:00:00':
                time_parts = start_time.split(':')
                if len(time_parts) == 3:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(time_parts[2])
                    start_seconds = hours * 3600 + minutes * 60 + seconds
            
            # If configured, offload heavy work to background queue
            use_rq = getattr(settings, 'USE_RQ', False)
            if use_rq:
                try:
                    rq_module = importlib.import_module('rq')
                    redis_module = importlib.import_module('redis')
                except Exception:
                    rq_module = None
                    redis_module = None
                if rq_module and redis_module:
                    Redis = getattr(redis_module, 'Redis')
                    Queue = getattr(rq_module, 'Queue')
                    redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
                    redis_conn = Redis.from_url(redis_url)
                    queue = Queue(connection=redis_conn)
                job = queue.enqueue(
                    'converter.tasks.convert_video_task',
                    upload_path,
                    output_filename,
                    start_seconds,
                    duration,
                )
                return JsonResponse({'enqueued': True, 'job_id': job.id})

            # Inline processing path
            if settings.DEBUG and getattr(settings, 'ENABLE_TRACEMALLOC', False) and tracemalloc and not tracemalloc.is_tracing():
                tracemalloc.start()

            def log_mem(stage: str) -> None:
                if getattr(settings, 'ENABLE_TRACEMALLOC', False) and tracemalloc and tracemalloc.is_tracing():
                    current, peak = tracemalloc.get_traced_memory()
                    logger.info(f"mem[{stage}] current={current/1e6:.1f}MB peak={peak/1e6:.1f}MB")

            log_mem('before_load')

            video = None
            trimmed_video = None
            try:
                # Load the video without audio to save memory
                video = VideoFileClip(upload_path, audio=False)

                # Validate start time
                if start_seconds >= video.duration:
                    return JsonResponse({'error': 'Start time exceeds video duration'}, status=400)

                # Trim first to reduce frames held in memory
                end_seconds = min(start_seconds + duration, video.duration)
                trimmed_video = video.subclip(start_seconds, end_seconds)

                # Early downscale to lower memory footprint
                trimmed_video = trimmed_video.resize(width=1280, height=720)

                log_mem('before_write')

                # Convert to GIF with conservative defaults for memory
                trimmed_video.write_gif(
                    output_path,
                    fps=24,
                    program='ffmpeg',
                    opt='OptimizePlus',
                    fuzz=1,
                )

                # Return the URL to the converted file
                converted_url = f"{settings.MEDIA_URL}converted/{output_filename}"
                return JsonResponse({'success': True, 'converted_url': converted_url})
            finally:
                # Ensure resources are freed
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
                log_mem('after_cleanup')
            
        except Exception as e:
            logger.error(f"Error converting video: {str(e)}")
            return JsonResponse({'error': f'Conversion failed: {str(e)}'}, status=500)
        
    return JsonResponse({'error': 'No video file provided'}, status=400)


def job_status(request, job_id: str):
    """Return RQ job status and result URL if available."""
    use_rq = getattr(settings, 'USE_RQ', False)
    if not use_rq:
        return JsonResponse({'error': 'RQ not enabled'}, status=400)

    try:
        rq_job_module = importlib.import_module('rq.job')
        redis_module = importlib.import_module('redis')
    except Exception:
        return JsonResponse({'error': 'RQ/Redis not available'}, status=400)

    Redis = getattr(redis_module, 'Redis')
    Job = getattr(rq_job_module, 'Job')
    redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
    redis_conn = Redis.from_url(redis_url)
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return JsonResponse({'error': 'Job not found'}, status=404)

    response = {
        'id': job.id,
        'status': job.get_status(),
    }
    # Include result or meta if present
    if job.is_finished and job.result:
        response['result'] = job.result
    if getattr(job, 'meta', None) and 'converted_url' in job.meta:
        response['converted_url'] = job.meta['converted_url']
    return JsonResponse(response)
