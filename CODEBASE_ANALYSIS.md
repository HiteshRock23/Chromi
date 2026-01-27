# Chromi - Complete Codebase Analysis

## 📋 Table of Contents
1. [High-Level Overview](#high-level-overview)
2. [Project Architecture](#project-architecture)
3. [File-by-File Explanation](#file-by-file-explanation)
4. [Feature Breakdown](#feature-breakdown)
5. [Data Flow & User Journey](#data-flow--user-journey)
6. [Important Business Logic](#important-business-logic)
7. [Safe vs Risky Areas](#safe-vs-risky-areas)
8. [Deployment & Configuration](#deployment--configuration)

---

## 🎯 High-Level Overview

### What Problem It Solves
**Chromi** is a web application that converts video files into Chrome-compatible animated background GIFs. Chrome themes require specific GIF formats (6 seconds, loopable, optimized), and this tool automates that conversion process.

### Who It's For
- Users who want to create custom Chrome theme backgrounds from their videos
- Anyone needing to convert video segments to optimized GIF format
- Developers/creators who want a simple, no-login-required conversion tool

### Main Features
- **Drag & Drop Upload**: Easy file selection interface
- **Video Preview**: See your video before conversion
- **Video Trimming**: Select start time and duration (fixed 6 seconds for Chrome)
- **Preview Trimmed Clip**: Test your selection before converting
- **One-Click Conversion**: Converts to Chrome-compatible GIF format
- **Secure Download**: One-time token-based file delivery
- **No Login Required**: Simple, straightforward user experience
- **Memory-Safe Processing**: Optimized for low-memory environments

---

## 🏗️ Project Architecture

### Django Apps Structure
```
chrome_background_converter/     # Main Django project
├── settings.py                  # Configuration
├── urls.py                      # Root URL routing
└── wsgi.py                      # WSGI application

converter/                       # Main Django app
├── views.py                     # Core business logic
├── urls.py                      # App URL patterns
├── tasks.py                     # Background job processing
├── models.py                    # (Empty - stateless app)
├── admin.py                     # (Empty - no admin needed)
└── apps.py                      # App configuration
```

### URL → View → Logic → Template Flow

```
User Request
    ↓
chrome_background_converter/urls.py (root)
    ↓
converter/urls.py (app routing)
    ↓
converter/views.py (business logic)
    ↓
templates/converter/home.html (frontend)
    OR
MoviePy/FFmpeg (video processing)
    ↓
Django Cache (token storage)
    ↓
StreamingHttpResponse (file delivery)
```

### Static Files, Media Files, and Settings

**Static Files:**
- Location: `static/` directory
- Served by: WhiteNoise middleware (production) or Django dev server
- Contains: CSS styles, background video (`static/videos/bg.mp4`)

**Media Files:**
- Location: `media/` directory
- Structure:
  - `media/uploads/` - Temporary uploaded videos (cleaned up after processing)
  - `media/converted/` - Converted GIFs (served via token, then deleted)
- **Important**: Files are NOT stored permanently - they're deleted after download

**Settings:**
- Currently configured for **local development** (DEBUG=True, no HTTPS)
- Production settings are commented out at the top of `settings.py`
- Key settings:
  - `FILE_UPLOAD_MAX_MEMORY_SIZE = 100MB` (upload limit)
  - `USE_RQ` - Optional background job processing
  - `ENABLE_TRACEMALLOC` - Optional memory diagnostics

---

## 📁 File-by-File Explanation

### Core Application Files

#### `converter/views.py` (462 lines) - **THE HEART OF THE APPLICATION**

**What it does:**
Contains all the main business logic for video conversion and file handling.

**Why it exists:**
This is where the magic happens - video upload, processing, conversion, and secure download delivery.

**Key Functions:**

1. **`home(request)`** (lines 23-25)
   - Renders the main upload interface
   - Simple view that returns the HTML template
   - Sets CSRF cookie for form submissions

2. **`convert_video(request)`** (lines 258-401) - **CRITICAL FUNCTION**
   - Handles POST requests with video files
   - Validates file type (MP4, MOV, WebM, GIF only)
   - Saves uploaded file to temporary location
   - Parses trim parameters (start time, duration)
   - **Core conversion logic:**
     - Loads video with MoviePy (no audio for memory efficiency)
     - Validates start time doesn't exceed video duration
     - Trims video to specified segment
     - Resizes to 1280×720 (HD resolution)
     - Converts to GIF with optimized settings (24fps, OptimizePlus)
   - Generates UUID download token
   - Stores token → file path mapping in Django cache (10 min TTL)
   - Returns JSON with download URL
   - **Memory management:** Closes all video objects, deletes temp files, runs garbage collection

3. **`download_converted(request, token)`** (lines 435-461) - **SECURITY-CRITICAL**
   - Retrieves file path from cache using token
   - **One-time use:** Deletes token immediately after lookup
   - Streams file to user via `StreamingHttpResponse`
   - Deletes file after streaming completes
   - Returns 404 if token expired or invalid

4. **`job_status(request, job_id)`** (lines 402-432)
   - Checks status of background RQ job (if enabled)
   - Returns job status and result URL when ready
   - Only works if `USE_RQ=True` in settings

5. **`health_check(request)`** (lines 27-29)
   - Simple endpoint to verify server is running
   - Returns JSON status

**What depends on it:**
- `converter/urls.py` - Routes requests to these views
- `templates/converter/home.html` - Frontend calls these endpoints
- `converter/tasks.py` - Background version mirrors this logic

**What breaks if removed:**
- **Everything** - This is the core of the application

---

#### `converter/tasks.py` (90 lines) - **BACKGROUND PROCESSING**

**What it does:**
Contains the same conversion logic as `views.py`, but designed to run in background workers (RQ/Redis).

**Why it exists:**
Allows heavy video processing to run asynchronously, preventing request timeouts and improving user experience.

**Key Function:**

- **`convert_video_task(upload_path, output_basename, start_seconds, duration)`**
  - Same conversion pipeline as `convert_video()` in views.py
  - Designed to be called by RQ workers
  - Stores result URL in RQ job metadata
  - Returns success/error dict

**What depends on it:**
- `converter/views.py` - Enqueues this task when `USE_RQ=True`
- RQ workers must be running separately

**What breaks if removed:**
- Background job processing feature (app still works synchronously)

---

#### `converter/urls.py` (12 lines) - **URL ROUTING**

**What it does:**
Defines URL patterns for the converter app.

**URL Patterns:**
- `''` → `home` view (main page)
- `'convert/'` → `convert_video` view (POST video conversion)
- `'health/'` → `health_check` view (health endpoint)
- `'jobs/<job_id>/'` → `job_status` view (RQ job status)
- `'download/<token>/'` → `download_converted` view (secure file download)

**Why it exists:**
Maps user requests to appropriate view functions.

**What depends on it:**
- `chrome_background_converter/urls.py` - Includes this app's URLs
- All views in `converter/views.py`

**What breaks if removed:**
- All URLs would 404 - app becomes inaccessible

---

#### `templates/converter/home.html` (455 lines) - **FRONTEND INTERFACE**

**What it does:**
Single-page application with drag-and-drop upload, video preview, trim controls, and conversion status.

**Why it exists:**
Provides the user interface for the entire application.

**Key Sections:**

1. **HTML Structure:**
   - Background video element (fullscreen decorative video)
   - Drop area for file uploads
   - Video preview container (hidden until file selected)
   - Trim controls (start time slider, duration slider)
   - Conversion status loader
   - Download container
   - Error container

2. **JavaScript Logic (lines 162-452):**
   - **File Handling:**
     - Drag-and-drop event listeners
     - File input change handler
     - File validation (type, size)
   - **Video Preview:**
     - Creates object URL for video preview
     - Displays video with controls
   - **Trim Controls:**
     - Start time slider (0-100% of video)
     - Duration slider (3-10 seconds, but backend enforces 6 seconds)
     - Preview trimmed clip button
   - **Conversion:**
     - POSTs to `/convert/` with FormData
     - Shows loading spinner
     - Handles success/error responses
   - **Download:**
     - Creates download link from token URL
     - Triggers browser download

**What depends on it:**
- `converter/views.py` - Calls `/convert/` and `/download/` endpoints
- `static/css/styles.css` - Styling
- `static/videos/bg.mp4` - Background video

**What breaks if removed:**
- Users can't interact with the application (no UI)

---

#### `chrome_background_converter/settings.py` (283 lines) - **CONFIGURATION**

**What it does:**
Django project settings - database, middleware, apps, security, file handling.

**Why it exists:**
Central configuration for the entire Django project.

**Key Settings:**

1. **Security (lines 166-182):**
   - Currently set for **local development** (DEBUG=True, no HTTPS)
   - Production settings commented out at top (lines 1-155)
   - `ALLOWED_HOSTS = ['*']` - Accepts all hosts (dev only)

2. **File Handling (lines 256-261):**
   - `MEDIA_ROOT = BASE_DIR / 'media'` - Where uploaded/converted files go
   - `MEDIA_URL = '/media/'` - URL prefix for media files
   - `FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600` - 100MB upload limit

3. **Static Files (lines 249-254):**
   - `STATIC_ROOT` - Where collected static files go
   - `STATICFILES_STORAGE` - Uses default storage (not compressed) for dev

4. **Optional Features (lines 279-282):**
   - `USE_RQ` - Enable background job processing
   - `REDIS_URL` - Redis connection string
   - `ENABLE_TRACEMALLOC` - Memory diagnostics

**What depends on it:**
- **Everything** - All Django apps use these settings

**What breaks if removed:**
- Django won't start - settings file is required

---

#### `chrome_background_converter/urls.py` (30 lines) - **ROOT URL ROUTING**

**What it does:**
Root URL configuration - includes admin and converter app URLs.

**URL Patterns:**
- `'admin/'` → Django admin interface
- `''` → Includes `converter.urls` (all converter app URLs)

**Why it exists:**
Top-level URL routing for the entire project.

**What depends on it:**
- `converter/urls.py` - Included here
- Django admin (if used)

**What breaks if removed:**
- All URLs would 404

---

#### `converter/apps.py` (7 lines) - **APP CONFIGURATION**

**What it does:**
Django app configuration - minimal setup.

**Why it exists:**
Standard Django app structure requirement.

**What depends on it:**
- `INSTALLED_APPS` in settings.py references this

**What breaks if removed:**
- App won't be recognized by Django

---

#### `converter/models.py` (4 lines) - **EMPTY - NO DATABASE MODELS**

**What it does:**
Nothing - file is empty (just a comment).

**Why it exists:**
Standard Django app structure, but this app is **stateless** - no database needed.

**What depends on it:**
- Nothing - no models are used

**What breaks if removed:**
- Nothing - but Django expects this file

---

#### `converter/admin.py` (4 lines) - **EMPTY - NO ADMIN INTERFACE**

**What it does:**
Nothing - file is empty.

**Why it exists:**
Standard Django app structure, but no admin interface needed (stateless app).

**What depends on it:**
- Nothing

**What breaks if removed:**
- Nothing - but Django expects this file

---

#### `converter/tests.py` (4 lines) - **EMPTY - NO TESTS**

**What it does:**
Nothing - no tests written yet.

**Why it exists:**
Standard Django app structure.

**What depends on it:**
- Nothing

**What breaks if removed:**
- Nothing - but good practice to have this file

---

### Configuration & Deployment Files

#### `gunicorn.conf.py` (39 lines) - **PRODUCTION SERVER CONFIG**

**What it does:**
Gunicorn WSGI server configuration for production deployment.

**Key Settings:**
- `workers = 1` - Single worker (low memory usage)
- `threads = 2` - Two threads per worker
- `timeout = 120` - 2 minute timeout (for long conversions)
- `max_requests = 1000` - Restart worker after 1000 requests (prevent memory leaks)

**Why it exists:**
Optimized for low-memory environments (like Render.com free tier).

**What depends on it:**
- Production deployment scripts
- Gunicorn server startup

**What breaks if removed:**
- Production server won't start properly

---

#### `build.sh` (46 lines) - **DEPLOYMENT BUILD SCRIPT**

**What it does:**
Automated build script for deployment (e.g., Render.com).

**Steps:**
1. Install Python dependencies
2. Create media directories
3. Run Pillow compatibility fix (if script exists)
4. Collect static files
5. Run database migrations

**Why it exists:**
Automates setup process for deployment platforms.

**What depends on it:**
- Deployment platform (Render, Heroku, etc.)
- `requirements.txt`
- `fix_pillow_antialias.py` (if exists)

**What breaks if removed:**
- Manual deployment steps required

---

#### `requirements.txt` (12 lines) - **PYTHON DEPENDENCIES**

**What it does:**
Lists all Python packages needed for the project.

**Key Dependencies:**
- `Django==5.2.4` - Web framework
- `moviepy==1.0.3` - Video processing
- `numpy==2.3.2` - Numerical operations (MoviePy dependency)
- `Pillow==11.3.0` - Image processing
- `gunicorn==23.0.0` - Production server
- `whitenoise==6.9.0` - Static file serving
- `redis==5.0.8` - Background jobs (optional)
- `rq==1.16.2` - Job queue (optional)
- `python-decouple==3.8` - Environment variable management

**Why it exists:**
Ensures consistent dependency versions across environments.

**What depends on it:**
- `build.sh` - Installs from this file
- `pip install -r requirements.txt`

**What breaks if removed:**
- Can't install dependencies automatically

---

### Documentation Files

#### `README.md` - **PROJECT DOCUMENTATION**

**What it does:**
User-facing documentation explaining what the project does, features, installation, and deployment.

**Why it exists:**
Helps users and developers understand the project.

---

#### `CONVERSION_SETTINGS.md` - **TECHNICAL SPECIFICATIONS**

**What it does:**
Documents the exact conversion settings used (resolution, FPS, duration, optimization).

**Why it exists:**
Reference for understanding why specific settings were chosen for Chrome compatibility.

---

#### `TROUBLESHOOTING.md` - **PROBLEM SOLVING GUIDE**

**What it does:**
Documents common issues (NumPy compatibility, Pillow ANTIALIAS deprecation) and solutions.

**Why it exists:**
Helps developers fix common compatibility issues.

---

## 🎬 Feature Breakdown

### Feature 1: Video Upload

**User Journey:**
1. User drags file onto drop area OR clicks "Choose a file"
2. JavaScript validates file type (MP4, MOV only in frontend, but backend accepts more)
3. JavaScript validates file size (100MB limit)
4. File is stored in browser memory as `File` object
5. Video preview is displayed

**Backend Flow:**
- No backend interaction yet - all client-side

**Key Logic:**
- File validation happens in JavaScript (lines 267-278 in home.html)
- Object URL created for preview (line 287)
- File stored in `currentFile` variable for later use

---

### Feature 2: Video Trimming

**User Journey:**
1. User sees video preview with controls
2. User adjusts "Start Time" slider (0-100% of video)
3. User adjusts "Duration" slider (3-10 seconds, but backend enforces 6)
4. User clicks "Preview Trimmed Clip" to test selection
5. Video plays from start time for specified duration

**Backend Flow:**
- No backend interaction - all client-side preview

**Key Logic:**
- Start time calculated as percentage of total video duration (lines 342-356)
- Duration slider value stored (lines 336-339)
- Preview uses `video.currentTime` and `setTimeout` to play for duration (lines 368-389)

---

### Feature 3: Video Conversion

**User Journey:**
1. User clicks "Convert to Chrome Background"
2. Loading spinner appears
3. Frontend POSTs to `/convert/` with file and trim parameters
4. Backend processes video (can take 30+ seconds)
5. Success response returns download URL
6. Download button appears

**Backend Flow (Step-by-Step):**

```
POST /convert/
    ↓
convert_video(request) in views.py
    ↓
1. Validate file type (MP4, MOV, WebM, GIF)
    ↓
2. Save uploaded file to temp location
    tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
    ↓
3. Parse trim parameters
    - start_time: "HH:MM:SS" → seconds
    - duration: Always set to 6 seconds (Chrome requirement)
    ↓
4. Check if RQ is enabled
    - If YES: Enqueue background job, return job_id
    - If NO: Continue with inline processing
    ↓
5. Load video with MoviePy
    VideoFileClip(upload_path, audio=False)  # No audio = less memory
    ↓
6. Validate start time
    if start_seconds >= video.duration: return error
    ↓
7. Trim video
    end_seconds = min(start_seconds + 6, video.duration)
    trimmed_video = video.subclip(start_seconds, end_seconds)
    ↓
8. Resize to HD
    trimmed_video = trimmed_video.resize(width=1280, height=720)
    ↓
9. Convert to GIF
    trimmed_video.write_gif(
        output_path,
        fps=24,
        program='ffmpeg',
        opt='OptimizePlus',
        fuzz=1
    )
    ↓
10. Generate download token
    download_token = str(uuid.uuid4())
    cache.set(f'dl:{download_token}', output_path, timeout=600)
    ↓
11. Cleanup
    - Close video objects
    - Delete upload temp file
    - Run garbage collection
    ↓
12. Return JSON response
    {'success': True, 'converted_url': '/download/<token>/'}
```

**Key Logic Points:**
- **Memory Management:** Trim before resize, close objects immediately, delete temp files
- **Error Handling:** Try/except blocks around all file operations
- **Token System:** UUID token stored in Django cache with 10-minute TTL

---

### Feature 4: Secure File Download

**User Journey:**
1. User clicks "Download Chrome Background"
2. Browser requests `/download/<token>/`
3. File streams to browser
4. Browser saves file as `chromi_background.gif`

**Backend Flow:**

```
GET /download/<token>/
    ↓
download_converted(request, token) in views.py
    ↓
1. Look up file path from cache
    path = cache.get(f'dl:{token}')
    ↓
2. Validate file exists
    if not path or not os.path.exists(path): return 404
    ↓
3. Delete token immediately (one-time use)
    cache.delete(f'dl:{token}')
    ↓
4. Stream file to user
    StreamingHttpResponse(stream_and_delete(path), content_type='image/gif')
    ↓
5. Delete file after streaming
    (happens in stream_and_delete generator)
```

**Key Logic Points:**
- **One-Time Token:** Token deleted immediately after lookup
- **Streaming:** Uses `StreamingHttpResponse` to handle large files
- **Auto-Cleanup:** File deleted after streaming completes
- **Security:** Token must be valid and not expired (10 min TTL)

---

### Feature 5: Background Job Processing (Optional)

**User Journey:**
1. Same as Feature 3, but response returns `{'enqueued': True, 'job_id': '...'}`
2. Frontend polls `/jobs/<job_id>/` every few seconds
3. When status is "finished", download URL is available

**Backend Flow:**

```
POST /convert/ (with USE_RQ=True)
    ↓
convert_video() enqueues job
    queue.enqueue('converter.tasks.convert_video_task', ...)
    ↓
RQ worker picks up job
    ↓
convert_video_task() runs in background
    (same conversion logic as inline version)
    ↓
Result stored in job metadata
    job.meta['converted_url'] = converted_url
    ↓
GET /jobs/<job_id>/
    ↓
job_status() returns job status and result
```

**Key Logic Points:**
- Only active if `USE_RQ=True` in settings
- Requires Redis server running
- Requires RQ workers running separately
- Same conversion logic, just async

---

## 🔄 Data Flow & User Journey

### Complete Request-Response Cycle

```
1. User visits site
   GET / → home() → home.html rendered

2. User uploads video
   (Client-side only - no backend request)

3. User clicks convert
   POST /convert/
   Body: FormData with video file + trim params
   ↓
   convert_video() processes
   ↓
   Response: {'success': True, 'converted_url': '/download/abc123/'}

4. User clicks download
   GET /download/abc123/
   ↓
   download_converted() streams file
   ↓
   Response: StreamingHttpResponse (GIF file)
   ↓
   File deleted after streaming
```

### Data Storage Flow

```
Uploaded Video
    ↓
Temp file (tempfile.NamedTemporaryFile)
    ↓
Processed GIF
    ↓
Temp file (tempfile.NamedTemporaryFile)
    ↓
Django Cache: {'dl:token': '/path/to/file'}
    ↓
User downloads
    ↓
File streamed
    ↓
File deleted
```

**Important:** No permanent storage - everything is temporary and cleaned up.

---

## 💡 Important Business Logic

### Memory Management (Critical for Production)

**Why it matters:**
Video processing is memory-intensive. Without careful management, the server can run out of memory (OOM errors).

**Key Practices:**

1. **Load without audio** (line 339):
   ```python
   video = VideoFileClip(upload_path, audio=False)
   ```
   - Saves significant memory

2. **Trim before resize** (lines 345-350):
   ```python
   trimmed_video = video.subclip(start_seconds, end_seconds)
   trimmed_video = trimmed_video.resize(width=1280, height=720)
   ```
   - Fewer frames in memory = less memory usage

3. **Explicit cleanup** (lines 368-395):
   ```python
   finally:
       if trimmed_video is not None:
           trimmed_video.close()
       if video is not None:
           video.close()
       del trimmed_video
       del video
       gc.collect()
   ```
   - Ensures resources are freed immediately

4. **Delete temp files** (lines 385-395):
   - Upload file deleted after processing
   - Output file deleted after download

### Conversion Settings (Chrome Requirements)

**Why these specific settings:**

1. **6-second duration** (line 287):
   - Chrome theme requirement - backgrounds must be exactly 6 seconds

2. **1280×720 resolution** (line 350):
   - HD quality without being too large
   - Balance between quality and file size

3. **24 FPS** (line 357):
   - Smooth animation without excessive file size
   - Lower FPS = smaller files

4. **OptimizePlus** (line 359):
   - Best quality/size ratio for GIFs
   - Chrome-compatible optimization

5. **GIF format**:
   - Only format Chrome accepts for theme backgrounds
   - WebM not supported for themes

### Security Features

1. **One-Time Download Tokens:**
   - UUID tokens prevent unauthorized access
   - Token deleted immediately after use
   - 10-minute expiration prevents token reuse

2. **File Type Validation:**
   - Only allows MP4, MOV, WebM, GIF
   - Prevents malicious file uploads

3. **File Size Limit:**
   - 100MB maximum prevents DoS attacks
   - Enforced in Django settings

4. **CSRF Protection:**
   - All POST requests require CSRF token
   - Prevents cross-site request forgery

5. **Temporary File Storage:**
   - Files never stored permanently
   - Auto-deleted after use
   - Prevents disk space issues

---

## ⚠️ Safe vs Risky Areas

### ✅ Safe to Modify

**Frontend Styling:**
- `templates/converter/home.html` - Visual changes, UX improvements
- `static/css/styles.css` - All styling changes
- JavaScript in `home.html` - UI behavior (as long as API calls stay the same)

**Configuration (Non-Critical):**
- `chrome_background_converter/settings.py` - Non-security settings
  - Logging configuration
  - Static file settings
  - Time zone, language

**Documentation:**
- `README.md`, `CONVERSION_SETTINGS.md`, `TROUBLESHOOTING.md`
- All documentation files

**Conversion Parameters (If You Understand Chrome Requirements):**
- Duration (currently 6 seconds) - line 287 in views.py
- Resolution (currently 1280×720) - line 350 in views.py
- FPS (currently 24) - line 357 in views.py
- Optimization settings - line 359 in views.py

**Tests:**
- `converter/tests.py` - Add tests (currently empty)

---

### ⚠️ Risky (Change Carefully)

**Core Conversion Logic:**
- `converter/views.py` - `convert_video()` function
  - **Memory cleanup code (lines 368-395)** - Removing this WILL cause memory leaks
  - **Token generation (lines 364-366)** - Breaking this breaks downloads
  - **File validation (lines 266-268)** - Security risk if removed
  - **Error handling** - Removing try/except blocks can crash the app

**Download System:**
- `converter/views.py` - `download_converted()` function
  - **Token lookup (line 438)** - Security-critical
  - **One-time deletion (line 443)** - Prevents token reuse
  - **File streaming (lines 445-457)** - Complex, easy to break

**Background Processing:**
- `converter/tasks.py` - Must match `views.py` logic exactly
  - If logic diverges, background and inline processing behave differently

**Settings (Production):**
- `chrome_background_converter/settings.py` - Production deployment settings
  - Security settings (HTTPS, HSTS, etc.)
  - Database configuration
  - Secret key management

---

### 🚫 Core Backbone (Don't Touch Unless Necessary)

**URL Routing:**
- `converter/urls.py` - Breaking URLs breaks the entire app
- `chrome_background_converter/urls.py` - Root routing

**Token System:**
- The entire download token mechanism is security-critical
- Changing token format breaks existing downloads
- Cache key format (`f'dl:{token}'`) is hardcoded in multiple places

**File Cleanup Logic:**
- Temp file deletion prevents disk space issues
- Removing cleanup can fill up server disk

**Memory Management:**
- All the `close()`, `del`, and `gc.collect()` calls
- Removing these causes memory leaks and OOM errors

---

## 🚀 Deployment & Configuration

### Current Configuration

**Development Mode:**
- `DEBUG = True`
- `ALLOWED_HOSTS = ['*']`
- No HTTPS enforcement
- No secure cookies
- Static files served by Django dev server

**Production Settings (Commented Out):**
- Lines 1-155 in `settings.py` contain production-ready settings
- Includes HTTPS enforcement, HSTS, secure cookies
- Uses environment variables via `python-decouple`

### Deployment Checklist

1. **Uncomment production settings** in `settings.py`
2. **Set environment variables:**
   - `SECRET_KEY` - Django secret key
   - `DEBUG=False`
   - `ALLOWED_HOSTS` - Your domain
   - `USE_HTTPS=True` (if using HTTPS)
3. **Run build script:** `bash build.sh`
4. **Start Gunicorn:** `gunicorn chrome_background_converter.wsgi:application`
5. **Set up static file serving:** WhiteNoise is configured
6. **Optional:** Set up Redis + RQ for background jobs

### Gunicorn Configuration

**Current settings (low memory):**
- 1 worker, 2 threads
- 120 second timeout (for long conversions)
- Max 1000 requests per worker (prevent memory leaks)

**For higher traffic:**
- Increase workers (but watch memory usage)
- Consider background job processing instead

### Optional Features

**Background Job Processing:**
- Set `USE_RQ=True` in environment
- Set `REDIS_URL` to your Redis instance
- Run RQ workers: `rq worker`
- Frontend must poll `/jobs/<job_id>/` for status

**Memory Diagnostics:**
- Set `ENABLE_TRACEMALLOC=True` in environment
- Logs memory usage at each conversion stage
- Useful for debugging OOM issues

---

## 📊 Summary

### What You Built

A **stateless video-to-GIF converter** optimized for Chrome theme backgrounds. The application:
- Accepts video uploads (MP4, MOV, WebM, GIF)
- Allows users to trim 6-second segments
- Converts to optimized GIF format (1280×720, 24fps)
- Provides secure, one-time download links
- Manages memory carefully for production deployment

### Key Strengths

1. **Memory-Safe:** Careful resource management prevents OOM errors
2. **Secure:** Token-based downloads, file validation, CSRF protection
3. **User-Friendly:** Drag-and-drop, preview, trim controls
4. **Production-Ready:** Gunicorn config, optional background jobs, deployment scripts

### Architecture Highlights

- **Stateless:** No database needed - uses cache for temporary token storage
- **Single-Page App:** All UI in one template with JavaScript
- **Modular:** Conversion logic can run inline or in background
- **Clean:** Temporary files auto-deleted, no permanent storage

### Where to Make Changes

- **UI/UX:** `templates/converter/home.html`, `static/css/styles.css`
- **Conversion Settings:** `converter/views.py` lines 287, 350, 357, 359
- **Configuration:** `chrome_background_converter/settings.py`
- **Background Jobs:** `converter/tasks.py` (must match views.py logic)

### Critical Files

1. **`converter/views.py`** - Core business logic
2. **`templates/converter/home.html`** - User interface
3. **`chrome_background_converter/settings.py`** - Configuration
4. **`converter/urls.py`** - URL routing

---

**You now have full context and ownership of your codebase!** 🎉

