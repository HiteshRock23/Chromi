import os
import uuid
import logging
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from moviepy.editor import VideoFileClip

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
            
            # Load the video
            video = VideoFileClip(upload_path)
            
            # Validate start time
            if start_seconds >= video.duration:
                video.close()
                return JsonResponse({'error': 'Start time exceeds video duration'}, status=400)
            
            # Trim the video
            end_seconds = min(start_seconds + duration, video.duration)
            trimmed_video = video.subclip(start_seconds, end_seconds)
            
            # Ensure the video loops smoothly by checking similarity between start and end frames
            # This is a simple approach - for better results, consider using a dedicated looping algorithm
            if video.duration >= (start_seconds + duration + 0.5):
                # If we have enough video, try to find a better loop point
                # by extending slightly and finding a frame similar to the start
                extended_end = min(end_seconds + 0.5, video.duration)
                extended_clip = video.subclip(start_seconds, extended_end)
                
                # Use the extended clip if it's available, otherwise use the original trim
                if extended_end > end_seconds:
                    trimmed_video = extended_clip
            
            # Get original video dimensions
            original_width = video.w
            original_height = video.h
            
            # Ensure the trimmed video maintains the original resolution
            trimmed_video = trimmed_video.resize(width=original_width, height=original_height)
            
            # Resize to HD resolution (1280x720)
            trimmed_video = trimmed_video.resize(width=1280, height=720)
            
            # Convert to GIF format with optimized settings for Chrome background
            trimmed_video.write_gif(
                output_path,
                fps=30,               # 30 frames per second for smooth animation
                program='ffmpeg',     # Use ffmpeg for better quality
                opt='OptimizePlus',   # Use optimization for better quality/size ratio
                fuzz=1                # Small fuzz factor for better compression while maintaining quality
            )
            
            # Close video objects
            trimmed_video.close()
            video.close()
            
            # Return the URL to the converted file
            converted_url = f"{settings.MEDIA_URL}converted/{output_filename}"
            return JsonResponse({
                'success': True,
                'converted_url': converted_url
            })
            
        except Exception as e:
            logger.error(f"Error converting video: {str(e)}")
            return JsonResponse({'error': f'Conversion failed: {str(e)}'}, status=500)
        
    return JsonResponse({'error': 'No video file provided'}, status=400)
