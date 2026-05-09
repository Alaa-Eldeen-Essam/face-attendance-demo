# Face Attendance Demo

A real-time face attendance system built with FastAPI, InsightFace, PostgreSQL, pgvector, and a browser-based camera UI. The project supports live webcam recognition, multi-photo enrollment per person, vector search for face embeddings, attendance logging, unknown-face review, camera stream integration, and lightweight track-level identity smoothing.

This repository is structured as a polished demo suitable for portfolio and CV discussion. It shows practical integration of computer vision, vector databases, backend APIs, frontend camera handling, Docker, and GPU-aware model execution.

## Highlights

- Real-time face detection and recognition with InsightFace `buffalo_l`.
- PostgreSQL plus pgvector for 512-dimensional face embedding search.
- Multiple face samples per person for more robust laptop-camera recognition.
- Track IDs and identity smoothing to reduce flicker and single-frame misclassification.
- Frontend overlay prediction for smoother bounding boxes between backend responses.
- Attendance deduplication using a configurable time window.
- Unknown-face capture, review, migration, and deletion.
- Docker Compose stack with PostgreSQL, pgAdmin, and FastAPI backend.
- Local GPU mode with ONNX Runtime CUDA provider support.
- Configurable thresholds, tracking behavior, and recognition interval.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | FastAPI, Uvicorn, SQLAlchemy |
| Face recognition | InsightFace, ONNX Runtime |
| Vector search | PostgreSQL, pgvector |
| Computer vision | OpenCV, NumPy |
| Frontend | HTML, CSS, vanilla JavaScript, Canvas API |
| Tracking | Lightweight IoU tracker with velocity prediction |
| Deployment | Docker Compose, pgAdmin |

## Current Architecture

```text
Browser UI
  - Webcam capture
  - Camera controls
  - Canvas overlay
  - Smooth client-side box prediction
        |
        | JPEG frames / API calls
        v
FastAPI backend
  - InsightFace detection and embeddings
  - pgvector nearest-neighbor matching
  - Track-level identity smoothing
  - Attendance and unknown-face logic
        |
        v
PostgreSQL + pgvector
  - persons
  - person_embeddings
  - attendance
  - unknown_faces
```

## Project Structure

```text
face-attendance-demo/
  backend/
    main.py                    FastAPI application and API routes
    recognition.py             InsightFace wrapper and provider selection
    tracker.py                 Lightweight tracker with velocity prediction
    database.py                PostgreSQL/pgvector setup
    models.py                  SQLAlchemy models
    cuda_dlls.py               Windows CUDA DLL path helper
    requirements.txt           CPU Docker/runtime dependencies
    requirements-gpu-cu12.txt  Local/GPU dependency set
    Dockerfile                 CPU backend image
    Dockerfile.gpu             GPU backend image
  frontend/
    index.html                 Browser UI
    main.js                    Camera, API, and overlay logic
    styles.css                 UI styling
  docker-compose.yml           Local Docker stack: backend, db, pgAdmin
  docker-compose.prod.yml      GPU-oriented Docker stack
  init-db.sql                  pgvector extension initialization
```

## Recommended Run Modes

### Option 1: Docker Stack

Use this when you want the whole stack in containers.

```powershell
cd D:\DEBI\Hackathon\attendance_system_vision_project\face-attendance-demo
docker compose up --build
```

Open:

```text
Application: http://127.0.0.1:8000
pgAdmin:     http://127.0.0.1:5050
```

pgAdmin login:

```text
Email:    admin@example.com
Password: admin
```

Database connection from pgAdmin:

```text
Host:     db
Port:     5432
Database: attendance_demo
Username: attendance
Password: attendance
```

Stop the stack:

```powershell
docker compose down
```

### Option 2: Docker Database + Local GPU Backend

Use this when you want CUDA acceleration from your local Conda environment.

Start PostgreSQL and pgAdmin:

```powershell
cd D:\DEBI\Hackathon\attendance_system_vision_project\face-attendance-demo
docker compose up -d db pgadmin
```

Start the backend locally:

```powershell
cd D:\DEBI\Hackathon\attendance_system_vision_project\face-attendance-demo\backend
conda activate hackathon_1_gpu
uvicorn main:app --host 127.0.0.1 --port 8000
```

This mode uses the `DATABASE_URL` in `backend/.env`, normally:

```text
postgresql+psycopg2://attendance:attendance@localhost:5433/attendance_demo
```

### Option 3: GPU Docker

Use this only after Docker can access the NVIDIA GPU.

Verify GPU visibility:

```powershell
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

Start the GPU stack:

```powershell
cd D:\DEBI\Hackathon\attendance_system_vision_project\face-attendance-demo
docker compose -f docker-compose.prod.yml up --build
```

Expected provider when GPU is working:

```text
CUDAExecutionProvider
```

If the app reports only `CPUExecutionProvider`, Docker is not exposing GPU access to the backend container or the ONNX Runtime CUDA provider cannot load the required libraries.

## Application Workflow

1. Open `http://127.0.0.1:8000`.
2. Register a person using an uploaded photo or camera capture.
3. Add multiple photos for the same person to improve recognition under different lighting, angles, and camera quality.
4. Start the camera.
5. Start recognition.
6. The app detects faces, assigns temporary track IDs, searches pgvector for the nearest embedding, and confirms identity over multiple frames.
7. Confirmed people are added to attendance automatically.
8. Unknown faces are saved only after repeated unknown frames, reducing noise from single bad frames.
9. Unknown faces can be migrated into a new or existing person record.

## Recognition and Tracking Flow

```text
Frame captured by browser
  -> FastAPI receives JPEG
  -> InsightFace detects faces and extracts embeddings
  -> pgvector nearest-neighbor search finds candidate identities
  -> IoU tracker assigns track_id
  -> identity smoothing confirms or rejects candidate identity
  -> attendance or unknown-face action is applied
  -> frontend renders predicted overlay boxes between backend responses
```

Tracking behavior:

- `tracker.py` uses IoU matching plus simple velocity prediction.
- Each detection receives a stable `track_id` while it remains visible.
- Identity confirmation uses a short rolling history per track.
- Confirmed known tracks are protected from being immediately saved as unknown when a few frames are weak.
- Frontend overlay boxes are animated with short-term prediction to reduce visual lag.

## Configuration

Main runtime settings live in `backend/.env` and Docker Compose environment variables.

```env
SIMILARITY_THRESHOLD=0.45
FACE_QUALITY_THRESHOLD=0.5
ATTENDANCE_WINDOW_MINUTES=30
UNKNOWN_SIMILARITY_THRESHOLD=0.5

TRACKER_MAX_AGE=10
TRACKER_MIN_HITS=1
TRACKER_IOU_THRESHOLD=0.3

TRACK_IDENTITY_HISTORY=5
TRACK_IDENTITY_CONFIRM_FRAMES=3
UNKNOWN_CONFIRM_FRAMES=5
IDENTITY_LOCK_MIN_SCORE=0.50
IDENTITY_LOCK_DECAY_FRAMES=10
UNKNOWN_SUPPRESS_KNOWN_TRACKS=true

DATABASE_URL=postgresql+psycopg2://attendance:attendance@localhost:5433/attendance_demo
RESET_DATABASE_ON_START=false
INSIGHTFACE_MODEL=buffalo_l
```

Important tuning notes:

- Lower `SIMILARITY_THRESHOLD` accepts weaker matches but increases false positives.
- Increase `TRACK_IDENTITY_CONFIRM_FRAMES` for stricter identity confirmation.
- Increase `UNKNOWN_CONFIRM_FRAMES` to reduce unknown-face noise.
- Keep browser recognition interval around `500-1000ms` for a good balance between latency and CPU/GPU load.

## API Overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Redirects to the frontend |
| `GET` | `/health` | Model, provider, and tracking status |
| `POST` | `/add-person/` | Add a person from uploaded photo |
| `POST` | `/capture-person/` | Add a person from camera/base64 image |
| `POST` | `/people/{person_id}/embeddings` | Add another photo/embedding to an existing person |
| `GET` | `/people/` | List registered people and embedding counts |
| `POST` | `/process-frame/` | Process a browser camera frame |
| `POST` | `/compare-image/` | Compare an uploaded image |
| `GET` | `/attendance/` | List attendance records |
| `GET` | `/unknown-faces/` | List unknown faces |
| `POST` | `/migrate-unknown/` | Convert unknown face to new or existing person |
| `DELETE` | `/unknown-faces/{unknown_id}` | Delete an unknown face |
| `DELETE` | `/clear-data/` | Clear demo data |
| `POST` | `/cameras/add` | Add RTSP/HTTP/file camera source |
| `GET` | `/cameras/{camera_id}/get-frame` | Fetch current remote-camera frame |
| `POST` | `/process-camera-frame/{camera_id}` | Process a remote-camera frame |

Interactive API docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Database Model

The schema is created automatically at startup.

Core tables:

- `persons`: registered identities.
- `person_embeddings`: multiple image samples and 512-dimensional face embeddings per person.
- `attendance`: arrival/departure-style attendance records.
- `unknown_faces`: saved unknown face crops and embeddings for review.

Vector indexes:

- `person_embeddings_embedding_hnsw_idx`
- `unknown_faces_embeddings_hnsw_idx`

## Camera Support

Supported sources:

- Browser webcam through `getUserMedia`.
- HTTP/MJPEG streams through OpenCV.
- RTSP streams through OpenCV/FFmpeg.
- Local video files if mounted into the backend environment.

When running in Docker, remote camera URLs must be reachable from inside the backend container. A stream that works in a desktop browser may still fail in Docker if DNS, routing, authentication, or OpenCV's video backend cannot access it.

Useful diagnostics:

```powershell
docker compose logs --tail=50 backend
docker compose exec backend python -c "import cv2; print(cv2.getBuildInformation())"
docker compose exec backend python -c "import socket; print(socket.gethostbyname('example.com'))"
```

## GPU Notes

Local Windows GPU mode uses:

- Python 3.11 Conda environment.
- `onnxruntime-gpu[cuda,cudnn]`.
- `cuda_dlls.py` to help Windows find CUDA/cuDNN DLLs installed by NVIDIA Python packages.

Health output should show:

```json
{
  "gpu_enabled": true,
  "providers": ["CUDAExecutionProvider", "CPUExecutionProvider"]
}
```

Docker CPU mode is expected to show:

```json
{
  "gpu_enabled": false,
  "providers": ["CPUExecutionProvider"]
}
```

## Troubleshooting

### Frontend returns 404

Rebuild after Dockerfile or frontend path changes:

```powershell
docker compose down
docker compose up --build
```

Then hard-refresh the browser:

```text
Ctrl + F5
```

### Docker cannot access GPU

Run:

```powershell
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

If this fails, fix Docker Desktop GPU/WSL/NVIDIA runtime first.

### RTSP or HTTP camera fails

Check whether the container can resolve and open the stream:

```powershell
docker compose exec backend python -c "import socket; print(socket.gethostbyname('your-hostname'))"
docker compose exec backend python -c "import cv2; url='YOUR_URL'; cap=cv2.VideoCapture(url); print(cap.isOpened()); ok, frame=cap.read(); print(ok, None if frame is None else frame.shape)"
```

Public camera streams can be unstable or reject repeated clients.

### Recognition is unstable

Recommended actions:

1. Add multiple photos per person.
2. Use better lighting and keep the face centered.
3. Keep recognition interval at `500-1000ms`.
4. Tune `SIMILARITY_THRESHOLD` and `IDENTITY_LOCK_MIN_SCORE`.
5. Use local GPU mode for faster feedback.

## Security and Production Notes

This is a demo/portfolio project, not a production access-control system.

Before production use, add:

- Authentication and authorization.
- HTTPS and secure CORS settings.
- Audit logging.
- Data retention and deletion policies.
- Encrypted secrets management.
- Model and threshold validation for the target environment.
- Consent and privacy controls for biometric data.

## CV Summary

This project demonstrates:

- Computer vision application development with InsightFace and OpenCV.
- Vector similarity search using PostgreSQL and pgvector.
- Real-time API design with FastAPI.
- Browser camera integration and Canvas overlay rendering.
- Lightweight object tracking and temporal identity smoothing.
- Dockerized service orchestration with PostgreSQL and pgAdmin.
- GPU-aware ONNX Runtime deployment and fallback handling.
