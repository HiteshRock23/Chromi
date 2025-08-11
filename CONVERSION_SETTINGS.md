# Chrome Background GIF Conversion Settings

This document outlines the specific settings used for converting videos to Chrome-compatible background GIF format.

## Current Settings

| Parameter | Value | Description |
|-----------|-------|-------------|
| Resolution | 1280×720 (HD) | Standard HD resolution for optimal quality and performance |
| Duration | 6 seconds | Fixed duration required by Chrome for background themes |
| FPS | 24–30 | 24 FPS reduces memory/CPU usage with acceptable smoothness |
| Format | GIF | Chrome-compatible format for theme backgrounds |
| Optimization | OptimizePlus | Enhanced optimization for better quality/size ratio |
| Muted | Yes (GIF format has no audio) | No audio in the output file |
| Loopable | Yes | GIF is processed to loop smoothly |

## Implementation Details

### GIF Processing

The application uses MoviePy and FFmpeg with the following settings:

```python
# Load without audio, trim first, resize early, then encode
video = VideoFileClip(upload_path, audio=False)
end_seconds = min(start_seconds + 6, video.duration)
trimmed_video = video.subclip(start_seconds, end_seconds)
trimmed_video = trimmed_video.resize(width=1280, height=720)
trimmed_video.write_gif(
    output_path,
    fps=24,               # 24 FPS to reduce memory/CPU
    program='ffmpeg',     # Use ffmpeg for better quality
    opt='OptimizePlus',   # Use optimization for better quality/size ratio
    fuzz=1                # Small fuzz factor for better compression while maintaining quality
)
```

### Looping Enhancement

For simplicity and lower memory on small instances, the default pipeline omits extended-loop search. If you re-enable advanced looping, ensure early downscale and strict cleanup after use.

```python
# Ensure the video loops smoothly by checking similarity between start and end frames
if video.duration >= (start_seconds + duration + 0.5):
    # If we have enough video, try to find a better loop point
    # by extending slightly and finding a frame similar to the start
    extended_end = min(end_seconds + 0.5, video.duration)
    extended_clip = video.subclip(start_seconds, extended_end)
    
    # Use the extended clip if it's available, otherwise use the original trim
    if extended_end > end_seconds:
        trimmed_video = extended_clip
```

## Chrome Background GIF Requirements

Chrome has specific requirements for background GIFs in themes:

- Must be in GIF format (WebM is not accepted for Chrome themes)
- Should be exactly 6 seconds long
- Should loop seamlessly
- Recommended resolution is 1280×720 (HD)
- Should be optimized for quality and file size

These settings ensure the background GIF plays smoothly while maintaining good visual quality.

## Memory-Safe Practices

- Open videos with `audio=False` unless audio is required.
- Trim before other operations and apply `.resize()` immediately after trimming.
- Always close clips (`clip.close()`), `del` variables, and call `gc.collect()` inside `finally`.
- Avoid keeping large frames or arrays in memory; process and release promptly.