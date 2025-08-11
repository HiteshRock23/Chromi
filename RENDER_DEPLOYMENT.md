## Host Chromi (Django + MoviePy) on Render

This guide walks you through deploying the Chromi app to Render with memory-safe defaults, optional background processing, and persistent media storage.

### What you will set up

- Web Service: Django app served by Gunicorn (with memory-friendly settings)
- Optional Redis: for background jobs (RQ)
- Optional Worker: RQ worker to process heavy video conversions off the web process
- Persistent Disk: to store user-uploaded media under `media/`

---

## 1) Prerequisites

- GitHub or GitLab repo with this project
- Render account
- For background jobs: a Redis instance on Render

---

## 2) Web Service (Django)

1. Create a new Web Service in Render and connect your repo.
2. Set the following fields:
   - Environment: `Python 3`
   - Build Command:
     ```bash
     chmod +x build.sh && ./build.sh
     ```
   - Start Command:
     ```bash
     gunicorn chrome_background_converter.wsgi:application --workers 1 --threads 2 --timeout 120
     ```
     Notes:
     - `workers=1` prevents parallel heavy jobs from causing out-of-memory (OOM)
     - `threads=2` allows light concurrency
     - `timeout=120` accommodates longer video conversions
3. Environment variables (Web Service → Settings → Environment):
   - `SECRET_KEY`: set a strong random value
   - `DEBUG`: `False`
   - Optional memory diagnostics (development only): `ENABLE_TRACEMALLOC=true`
   - Optional background jobs:
     - `USE_RQ=true`
     - `REDIS_URL=<redis-connection-url>` (only if using Redis/RQ)

4. Persistent Disk (recommended for uploads):
   - Add a disk to the Web Service and mount it at:
     - Mount path: `/opt/render/project/src/media`
     - Size: 1–5 GB to start (adjust as needed)
   - This matches `MEDIA_ROOT = BASE_DIR / 'media'`

5. Health Check (optional):
   - Set health check path to `/health/`
   - The endpoint returns 200 JSON when the app is healthy

6. Static files are served by WhiteNoise:
   - `build.sh` should run `collectstatic`
   - No CDN needed for basic setups

7. Deploy. Watch logs to confirm boot and initial health.

---

## 3) Optional: Redis and Background Worker

For large uploads or long conversions, offload processing to a worker. The web app enqueues a job and returns quickly.

### Create a Redis instance

1. Create a Redis service on Render.
2. Copy its connection URL and set it as `REDIS_URL` on both the Web and Worker services.

### Create a Worker service

1. Create a new Worker in Render pointing to the same repo.
2. Start Command:
   ```bash
   rq worker --url $REDIS_URL
   ```
3. Environment variables:
   - `REDIS_URL`: from your Redis service
   - Optional: `USE_RQ=true` (not strictly required for worker)

### How it works

- POST `/convert/` with a file enqueues the job and returns `{ enqueued: true, job_id }`
- Poll GET `/jobs/<job_id>/` for job status and the `converted_url` when complete

If `USE_RQ` is not set, conversions run inline on the web process using the same memory-optimized pipeline.

---

## 4) Memory and performance guidance

- Gunicorn: keep `workers=1`, `threads=2`, and `timeout=120`
- MoviePy:
  - Load videos with `audio=False`
  - Trim first, resize early to 1280×720
  - Encode GIF at ~24 FPS to reduce CPU/memory
  - Always close clips (`close()`), delete references, and call `gc.collect()`
- Prefer background jobs to avoid HTTP timeouts and reduce OOM risk
- Start small (512 MB–1 GB) and scale memory up only if needed

---

## 5) Testing the deployment

Once deployed, test the endpoints:

- Health check:
  ```bash
  curl -s https://<your-service>.onrender.com/health/
  ```
- Inline conversion (small test file):
  ```bash
  curl -F "video=@sample.mp4" -F "start_time=00:00:00" -F "duration=6" \
       https://<your-service>.onrender.com/convert/
  ```
- Background job flow (when `USE_RQ=true`):
  1) Enqueue
  ```bash
  curl -F "video=@sample.mp4" https://<your-service>.onrender.com/convert/
  # → { "enqueued": true, "job_id": "<id>" }
  ```
  2) Poll status
  ```bash
  curl https://<your-service>.onrender.com/jobs/<id>/
  ```

---

## 6) Troubleshooting

- OOM (memory kill):
  - Ensure `workers=1` and `threads=2`
  - Prefer background jobs for large files
  - Keep resolution at 1280×720 and FPS around 24
  - Review logs for memory snapshots (enable `ENABLE_TRACEMALLOC=true` in development)

- Timeouts:
  - Keep Gunicorn `timeout=120`
  - Long conversions should run via background jobs

- Media not persisting:
  - Confirm a disk is mounted at `/opt/render/project/src/media`

- Static files missing:
  - Ensure `build.sh` runs `collectstatic`
  - WhiteNoise is enabled in `MIDDLEWARE`

- FFmpeg issues:
  - MoviePy uses `imageio-ffmpeg` which may auto-download the binary on first use
  - If needed, add `imageio-ffmpeg` to `requirements.txt` or set `IMAGEIO_FFMPEG_EXE` to a known binary

- Database persistence:
  - Default is SQLite (file-based). For production persistence, use a managed Postgres service instead of SQLite on ephemeral disks.

---

## 7) Optional: Render Blueprint (render.yaml)

You can codify the setup via a `render.yaml`. Example skeleton:

```yaml
services:
  - type: web
    name: chromi-web
    env: python
    buildCommand: chmod +x build.sh && ./build.sh
    startCommand: gunicorn chrome_background_converter.wsgi:application --workers 1 --threads 2 --timeout 120
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: USE_RQ
        value: "true"
      - key: REDIS_URL
        fromService:
          type: redis
          name: chromi-redis
          property: connectionString
    disks:
      - name: uploads
        mountPath: /opt/render/project/src/media
        sizeGB: 5

  - type: worker
    name: chromi-worker
    env: python
    startCommand: rq worker --url $REDIS_URL
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: chromi-redis
          property: connectionString

  - type: redis
    name: chromi-redis
```

This blueprint is optional, but useful for repeatable deployments.

---

## 8) Summary

- Use a single Gunicorn worker with two threads and a longer timeout
- Keep MoviePy memory footprint low by loading without audio, trimming first, resizing early, and closing resources
- Add a disk for `media/` so uploads persist across deploys
- For heavier workloads, enable Redis + RQ and run a worker service

