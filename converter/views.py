import os
import uuid
import logging
import gc
import tempfile
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from moviepy.editor import VideoFileClip
import importlib
from django.core.cache import cache

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

import subprocess
import shutil

def convert_with_ffmpeg(input_path, output_path, start_seconds, duration):
    """Convert video to GIF using FFmpeg directly - more reliable than MoviePy."""
    
    # Check if ffmpeg is available
    if not shutil.which('ffmpeg'):
        raise Exception("FFmpeg not found on system")
    
    try:
        # FFmpeg command for high-quality GIF conversion
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', str(start_seconds),  # Start time in seconds
            '-t', str(duration),        # Duration in seconds
            '-vf', 'fps=15,scale=640:360:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
            '-loop', '0',               # Loop forever (Chrome requirement)
            '-y',                       # Overwrite output file
            output_path
        ]
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120,  # 2 minute timeout
            cwd=os.path.dirname(input_path)
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg stderr: {result.stderr}")
            raise Exception(f"FFmpeg failed with return code {result.returncode}: {result.stderr}")
        
        # Check if output file was created and has content
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("FFmpeg did not create a valid output file")
            
        logger.info(f"FFmpeg conversion successful. Output file size: {os.path.getsize(output_path)} bytes")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg conversion timed out")
        raise Exception("Video conversion timed out after 2 minutes")
    except Exception as e:
        logger.error(f"FFmpeg conversion error: {str(e)}")
        raise Exception(f"Video conversion failed: {str(e)}")

def convert_video(request):
    """Convert uploaded video to Chrome-compatible background format (GIF) with trimming."""
    if request.method == 'POST' and request.FILES.get('video'):
        upload_path = None
        output_path = None
        download_token = None
        
        try:
            # Get the uploaded file
            video_file = request.FILES['video']
            
            # Check file extension
            file_ext = os.path.splitext(video_file.name)[1].lower()
            if file_ext not in ['.mp4', '.mov', '.webm', '.gif']:
                return JsonResponse({'error': 'Only .mp4, .mov, .webm, and .gif files are supported'}, status=400)
            
            # Use a secure temporary file for upload
            upload_temp = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
            upload_path = upload_temp.name
            with upload_temp as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)
            
            # Prepare temp output file (GIF)
            output_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.gif')
            output_path = output_temp.name
            output_temp.close()
            
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
                        os.path.basename(output_path),
                        start_seconds,
                        duration,
                    )
                    return JsonResponse({'enqueued': True, 'job_id': job.id})

            # Try FFmpeg first (more reliable)
            try:
                logger.info("Starting video conversion with FFmpeg...")
                convert_with_ffmpeg(upload_path, output_path, start_seconds, duration)
                logger.info("Video conversion completed successfully")
                
                # Register download token
                download_token = str(uuid.uuid4())
                cache.set(f'dl:{download_token}', output_path, timeout=600)
                converted_url = f"/download/{download_token}/"
                return JsonResponse({'success': True, 'converted_url': converted_url})
                
            except Exception as ffmpeg_error:
                logger.error(f"FFmpeg conversion failed: {str(ffmpeg_error)}")
                
                # Fallback to MoviePy if FFmpeg fails
                logger.info("Attempting fallback to MoviePy...")
                
                # Inline processing path with MoviePy fallback
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
                    # Set FFmpeg path for MoviePy
                   
                    os.environ['IMAGEIO_FFMPEG_EXE'] = '/usr/bin/ffmpeg'
                    
                    # Load the video without audio to save memory
                    video = VideoFileClip(upload_path, audio=False)

                    # Validate start time
                    if start_seconds >= video.duration:
                        return JsonResponse({'error': 'Start time exceeds video duration'}, status=400)

                    # Trim first to reduce frames held in memory
                    end_seconds = min(start_seconds + duration, video.duration)
                    trimmed_video = video.subclip(start_seconds, end_seconds)

                    # Smaller resolution to reduce memory footprint
                    trimmed_video = trimmed_video.resize(width=480, height=270)

                    log_mem('before_write')

                    # Convert to GIF with conservative defaults for memory
                    trimmed_video.write_gif(
                        output_path,
                        fps=12,  # Lower FPS
                        program='ffmpeg',
                        opt='OptimizeTransparency',
                        fuzz=2,
                        verbose=False,
                        logger=None
                    )

                    # Register a one-time download token mapped to the temp file
                    download_token = str(uuid.uuid4())
                    cache.set(f'dl:{download_token}', output_path, timeout=600)
                    converted_url = f"/download/{download_token}/"
                    return JsonResponse({'success': True, 'converted_url': converted_url})
                    
                except Exception as moviepy_error:
                    logger.error(f"Both FFmpeg and MoviePy failed. FFmpeg: {ffmpeg_error}, MoviePy: {moviepy_error}")
                    return JsonResponse({'error': 'Video conversion failed. Please try a different video file.'}, status=500)
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
        finally:
            # Cleanup files
            try:
                if upload_path and os.path.exists(upload_path):
                    os.remove(upload_path)
            except Exception:
                pass
            # Only remove output if no download token was created
            try:
                if not download_token and output_path and os.path.exists(output_path):
                    os.remove(output_path)
            except Exception:
                pass
        
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


def download_converted(request, token: str):
    """Stream the converted GIF by a one-time token and delete after streaming."""
    key = f'dl:{token}'
    path = cache.get(key)
    if not path or not os.path.exists(path):
        return JsonResponse({'error': 'File not found or expired'}, status=404)

    # One-time: remove cache entry now
    cache.delete(key)

    def stream_and_delete(file_path: str, chunk_size: int = 8192):
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    yield data
        finally:
            try:
                os.remove(file_path)
            except Exception:
                pass

    response = StreamingHttpResponse(stream_and_delete(path), content_type='image/gif')
    response['Content-Disposition'] = 'attachment; filename="chromi_background.gif"'
    return response
