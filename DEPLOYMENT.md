# Chromi Deployment Guide for Render

## 🚀 Production Deployment Fixes

### **Issues Fixed:**

1. **Security Settings**
   - Added environment variable support for SECRET_KEY
   - Disabled DEBUG in production
   - Added security headers (HSTS, SSL redirect, etc.)

2. **Static Files**
   - Added WhiteNoise middleware for static file serving
   - Configured proper static file storage
   - Added build script for static file collection

3. **Environment Variables**
   - Added python-dotenv support
   - Created environment variable configuration

### **Render Configuration:**

#### **Environment Variables to Set in Render:**
```
SECRET_KEY=your-secure-secret-key-here
DEBUG=False
```

#### **Build Command:**
```bash
chmod +x build.sh && ./build.sh
```

#### **Start Command (Render):**
Use a single worker to prevent OOM while processing videos, a couple of threads for light concurrency, and a higher timeout for movie processing.
```bash
gunicorn chrome_background_converter.wsgi:application --workers 1 --threads 2 --timeout 120
```
Alternatively, the included `gunicorn.conf.py` is configured to mirror this behavior on Render by reading `PORT` and forcing `workers=1`, `threads=2`, `timeout=120`.

### **Files Updated:**

1. **settings.py** - Production-ready configuration
2. **requirements.txt** - Added gunicorn and whitenoise
3. **build.sh** - Build script for deployment
4. **DEPLOYMENT.md** - This guide

### **Key Changes Made:**

#### **Security Enhancements:**
- Environment variable support for SECRET_KEY
- DEBUG mode controlled by environment
- SSL/HTTPS enforcement
- Security headers (HSTS, XSS protection, etc.)

#### **Static Files:**
- WhiteNoise middleware for efficient static file serving
- Proper static file collection in build script
- Compressed static file storage

#### **Production Optimizations:**
- Gunicorn as WSGI server
- Proper ALLOWED_HOSTS configuration
- Environment-based settings

### **Deployment Steps:**

1. **Set Environment Variables in Render:**
   - Go to your Render dashboard
   - Navigate to your service
   - Go to Environment tab
   - Add the environment variables listed above

2. **Deploy:**
   - Push your changes to GitHub
   - Render will automatically deploy using the build script

3. **Verify:**
   - Check that static files are loading
   - Verify HTTPS is working
   - Test video conversion functionality

### **Troubleshooting:**

#### **If Static Files Don't Load:**
- Ensure WhiteNoise is in MIDDLEWARE
- Check that build script runs successfully
- Verify STATIC_ROOT is set correctly

#### **If Video Conversion Fails:**
- Check that MoviePy dependencies are installed
- Verify file upload permissions
- Check media directory permissions

#### **If Environment Variables Don't Work:**
- Ensure python-dotenv is in requirements.txt
- Verify .env file is in root directory
- Check Render environment variable settings

### **Performance and Memory Optimizations (MoviePy/Numpy/Pillow):**

- **Gunicorn workers**: Limit to 1 worker to avoid parallel heavy jobs. `threads=2` for light concurrency, `timeout=120` for long-running conversions.
- **Load videos without audio**: Open videos with `audio=False` unless needed.
- **Early resize**: Apply `.resize(width=1280, height=720)` immediately after trimming to lower memory usage for all subsequent operations.
- **Cleanup**: Always call `clip.close()`, then `del clip` and `gc.collect()` in a `finally` block.
- **GIF encoding**: Prefer `fps=24`, `program='ffmpeg'`, `opt='OptimizePlus'`, `fuzz=1` to balance quality and memory.
- **Pillow images**: Stream or chunk when possible; avoid holding large images in memory.

The `converter/views.py` has been updated to follow these patterns and to optionally use `tracemalloc` for development-only memory tracking.

### **Background Jobs (Optional but Recommended):**

- Enable background processing to avoid blocking the web worker and reduce OOM risk.
- Added lightweight integration using Redis and RQ:
  - `USE_RQ=true` enables queueing
  - `REDIS_URL=redis://:password@host:6379/0`
  - POST `/convert/` enqueues a job and returns `{ enqueued: true, job_id }`
  - GET `/jobs/<job_id>/` returns job status and result when ready

Provision a separate RQ worker on Render using the same codebase and `worker` start command:
```bash
rq worker --url $REDIS_URL
```

If you don't enable RQ, conversions run inline with the same memory-optimized path.

### **Monitoring:**

- Check Render logs for any errors
- Monitor static file serving
- Verify video conversion functionality
- Test on different devices/browsers
 - In development you can enable `ENABLE_TRACEMALLOC=true` to log memory snapshots before/after processing.

## ✅ **Expected Results:**

After deployment, your Chromi application should:
- Load with premium dark theme
- Serve static files efficiently
- Handle video uploads and conversions
- Display creator attribution in footer
- Work securely over HTTPS
- Perform well on all devices

The application is now production-ready with proper security, static file handling, and environment configuration! 