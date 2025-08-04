# Chromi

A Django web application that allows users to trim and convert video files into Chrome-compatible background format (GIF) for Chrome themes.

## Features

- **Single-page website** with a clean, responsive interface
- **Drag & drop upload** for easy file selection
- **Video preview** after upload
- **Video trimming** with customizable start time and fixed 6-second duration (Chrome requirement)
- **Preview trimmed clip** before conversion
- **One-click conversion** to Chrome-compatible GIF format
- **Optimized conversion** with HD resolution (1280×720) and high-quality settings
- **Loopable GIF output** that plays smoothly when repeated
- **Download button** for the converted file
- **No login required** - simple and straightforward
- **Mobile-friendly** design

## Technical Details

### Frontend
- HTML5 for structure
- CSS3 for styling
- JavaScript for interactive features
- Drag and drop API for file uploads
- Video preview functionality
- Video trimming controls with time input and duration slider
- Trimmed clip preview

### Backend
- Django web framework
- MoviePy for video conversion and trimming
- FFmpeg (used by MoviePy) for GIF processing with Chrome-optimized settings:
  - HD resolution (1280×720)
  - 30 FPS frame rate
  - OptimizePlus quality settings
  - Optimized color palette
  - Loopable output (smooth transitions between loops)
- Video trimming with precise start time and fixed 6-second duration
- CSRF protection for form submissions

### Compatibility
- Compatible with Pillow 10.0.0+ (includes fix for PIL.Image.ANTIALIAS deprecation)
- Includes utility script (`fix_pillow_antialias.py`) to patch MoviePy for newer Pillow versions

### File Handling
- Accepts MP4, WebM, and GIF video formats
- Converts to GIF format (Chrome theme compatible)
- 100MB file size limit
- Temporary file storage (files not stored permanently)

## Project Structure

```
├── chrome_background_converter/  # Django project settings
├── converter/                    # Main Django app
├── fix_pillow_antialias.py      # Utility script to fix PIL.Image.ANTIALIAS deprecation
├── media/                        # Media files directory
│   ├── uploads/                  # Temporary storage for uploaded files
│   └── converted/                # Storage for converted files
├── static/                       # Static files
│   └── css/                      # CSS stylesheets
├── templates/                    # HTML templates
│   └── converter/                # App-specific templates
└── manage.py                     # Django management script
```

## Installation

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install django moviepy
   ```
3. Run the development server:
   ```
   python manage.py runserver
   ```
4. Access the application at http://127.0.0.1:8000/

## Requirements

- Python 3.6+
- Django 3.0+
- MoviePy
- FFmpeg (installed and available in PATH)

## Deployment

This application can be deployed to any Django-compatible hosting service. Make sure to:

1. Set `DEBUG = False` in production
2. Configure proper static and media file serving
3. Set up appropriate security measures

## License

This project is open source and available for personal and commercial use.