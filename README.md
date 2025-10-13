# Facial Recognition Attendance System - Demo

A lightweight, educational demo of a facial recognition attendance system using **InsightFace** for face detection/recognition and a simple HTML/JavaScript frontend.

![Demo Banner](https://img.shields.io/badge/Status-Demo-orange) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)

⚠️ **IMPORTANT: This is a demo/proof-of-concept only. Not production-ready. No authentication or security features.**

## Features

- 🎥 **Real-time Face Detection** - Live webcam processing with bounding box overlays
- 🧠 **InsightFace Recognition** - Buffalo_l model for accurate face embeddings
- 📊 **Smart Attendance** - Automatic deduplication within configurable time windows
- 💾 **SQLite Database** - Lightweight local storage for people and attendance records
- 🎨 **Clean UI** - Vanilla HTML/JS/CSS interface, no frameworks required
- ⚡ **FastAPI Backend** - Async endpoints for high performance
- 🔗 **Integrated Frontend** - Backend automatically serves frontend at root URL

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│                   http://localhost:8000                         │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │   Webcam     │───▶│  Canvas      │───▶│   Overlay    │    │
│  │   Stream     │    │  Capture     │    │   (Boxes)    │    │
│  └──────────────┘    └──────┬───────┘    └──────────────┘    │
│                              │                                  │
│                              │ POST /process-frame/            │
│                              ▼                                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ JPEG Frame
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│                   (Python + Uvicorn)                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    main.py                                │  │
│  │  • Serves frontend at /                                   │  │
│  │  • Handles API requests                                   │  │
│  │  • Manages attendance logic                               │  │
│  └────────────┬───────────────────────────┬──────────────────┘  │
│               │                           │                     │
│               ▼                           ▼                     │
│  ┌──────────────────────┐    ┌──────────────────────┐         │
│  │   recognition.py     │    │    database.py       │         │
│  │                      │    │                      │         │
│  │  ┌────────────────┐ │    │  ┌────────────────┐ │         │
│  │  │  InsightFace   │ │    │  │  SQLAlchemy    │ │         │
│  │  │  buffalo_l     │ │    │  │                │ │         │
│  │  │  • Detect      │ │    │  │  Person        │ │         │
│  │  │  • Extract     │ │    │  │  Attendance    │ │         │
│  │  │  • Compare     │ │    │  │  Unknown       │ │         │
│  │  └────────────────┘ │    │  └────────────────┘ │         │
│  └──────────────────────┘    └──────────┬───────────┘         │
│                                          │                     │
│                                          ▼                     │
│                              ┌──────────────────────┐          │
│                              │  attendance_demo.db  │          │
│                              │     (SQLite)         │          │
│                              └──────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
face-attendance-demo/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # SQLAlchemy database models
│   ├── database.py          # Database configuration
│   ├── recognition.py       # InsightFace wrapper
│   ├── requirements.txt     # Python dependencies
│   ├── run_demo.sh          # Quick start script
│   └── .env.example         # Configuration template
├── frontend/
│   ├── index.html           # Main UI
│   ├── main.js              # Frontend logic
│   └── styles.css           # Styling
├── README.md                # This file
└── .gitignore
```

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Webcam
- Internet connection (for initial model download)

### One-Command Startup (Easiest)

From the project root directory:

```bash
# Linux/Mac
chmod +x start_demo.sh
./start_demo.sh

# Windows
start_demo.bat
```

This script will:
1. ✅ Create virtual environment
2. ✅ Install all dependencies
3. ✅ Start the backend server
4. ✅ Serve the frontend automatically

Then just open **http://localhost:8000** in your browser!

### Manual Setup (Alternative)

### Manual Setup (Alternative)

If you prefer to run commands manually:

#### 1. Clone/Download

```bash
git clone <repository-url>
cd face-attendance-demo
```

##### 2. Install Backend Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Note:** First run will download the InsightFace buffalo_l model (~150MB). This may take a few minutes.

##### 3. Run Backend

```bash
# From backend directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will start on `http://localhost:8000` and automatically serve the frontend.

#### 4. Access the Application

Simply open your browser and visit: **http://localhost:8000**

- Main App: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

#### 5. Initialize Demo Data

1. Click **"Seed Demo People"** button to create 4 sample people
2. Click **"Start Camera"** to enable webcam
3. Click **"Start Recognition"** to begin face detection

## Usage Guide

### Basic Workflow

1. **Seed Demo People**: Creates sample personnel records with placeholder images
2. **Start Camera**: Requests webcam permission and displays live feed
3. **Start Recognition**: Begins processing frames at configured interval (default: 1000ms)
4. **View Results**: 
   - Green boxes = Recognized faces
   - Red boxes = Unknown faces
   - Attendance automatically logged for recognized faces

### Configuration

Edit settings in the UI or via environment variables:

**In-App Settings:**
- **Frame Interval**: Time between recognition requests (100-5000ms)
- **Threshold**: Similarity threshold for matches (0.0-1.0, default: 0.6)

**Environment Variables** (create `.env` file in backend/):
```bash
SIMILARITY_THRESHOLD=0.6
FACE_QUALITY_THRESHOLD=0.7
ATTENDANCE_WINDOW_MINUTES=30
```

### Smart Attendance Logic

The system prevents duplicate attendance entries:
- If a person was detected < 30 minutes ago, no new entry is created
- Configurable via `ATTENDANCE_WINDOW_MINUTES`
- Each entry has `arrival_time` and optional `departure_time`

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/seed-demo/` | Seed demo people |
| POST | `/process-frame/` | Process video frame for recognition |
| GET | `/people/` | List all known people |
| GET | `/attendance/` | List attendance records |
| DELETE | `/clear-data/` | Clear all data |

### Example: Process Frame

```bash
curl -X POST "http://localhost:8000/process-frame/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@frame.jpg"
```

Response:
```json
{
  "faces": [
    {
      "known": true,
      "person_id": 1,
      "name": "Ahmed Hassan",
      "identifier": "MIL-001",
      "bbox": [100, 150, 200, 250],
      "score": 0.87
    }
  ]
}
```

## Technical Details

### Face Recognition Pipeline

1. **Detection**: InsightFace detects faces in frame
2. **Embedding**: 512-dimensional face embedding extracted
3. **Matching**: Cosine similarity against known embeddings
4. **Threshold**: Matches above threshold are considered recognized
5. **Logging**: Attendance record created/updated

### Database Schema

**Person Table:**
- `id`: Primary key
- `name`: Person's name
- `identifier`: Unique ID (e.g., employee/military ID)
- `image_data`: Stored face photo (BLOB)
- `embeddings`: 512-float face embedding (BLOB)
- `created_at`: Timestamp
- `deleted`: Soft delete flag

**Attendance Table:**
- `id`: Primary key
- `person_id`: Foreign key to Person
- `name`: Denormalized for quick queries
- `identifier`: Denormalized
- `arrival_time`: Entry timestamp
- `departure_time`: Exit timestamp (nullable)
- `auto`: Auto-detected vs manual entry
- `created_at`: Record creation time

**Unknown Table:**
- `id`: Primary key
- `image_data`: Face crop of unknown person
- `embeddings`: Face embedding
- `detected_at`: Detection timestamp

### Model Information

**InsightFace Buffalo_L:**
- 512-dimensional embeddings
- High accuracy for face recognition
- ~150MB download on first run
- Stored in `~/.insightface/models/`

## Limitations & Known Issues

⚠️ **This is a DEMO - Known Limitations:**

1. **No Authentication**: Backend has no access control
2. **No HTTPS**: Unencrypted communication
3. **Demo Embeddings**: Seeded people use random embeddings (for real use, upload actual face photos)
4. **Single-Face Optimization**: Works best with one face in frame
5. **Lighting Sensitivity**: Performance degrades in poor lighting
6. **No Persistence**: Data lost if database file deleted
7. **CPU-Only**: No GPU acceleration configured (can be enabled)

## Troubleshooting

### Camera Not Working

- **Check permissions**: Ensure browser has webcam access
- **HTTPS required**: Some browsers require HTTPS for getUserMedia (use localhost exemption)
- **Wrong device**: Camera might be occupied by another app

### Model Download Issues

```bash
# Manual model download
mkdir -p ~/.insightface/models/buffalo_l
# Download from: https://github.com/deepinsight/insightface/releases
```

### Poor Recognition Accuracy

- Ensure good lighting
- Face should be clearly visible and front-facing
- Adjust `SIMILARITY_THRESHOLD` (lower = more lenient)
- Use real face photos instead of demo placeholders

### CORS Errors

- Run frontend via HTTP server instead of file://
- Or configure backend to serve frontend:
  ```python
  app.mount("/", StaticFiles(directory="../frontend", html=True))
  ```

## Advanced Configuration

### GPU Acceleration

Edit `backend/recognition.py`:

```python
self.app = FaceAnalysis(
    name=model_name,
    providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
)
```

Requires: `pip install onnxruntime-gpu`

### Custom Model

Change model in `backend/recognition.py`:

```python
recognizer = FaceRecognizer(model_name="buffalo_sc")  # Smaller, faster
```

Available models: `buffalo_l`, `buffalo_sc`, `buffalo_s`

### Production Deployment

**DO NOT use this demo in production without:**

1. Adding authentication (OAuth2, JWT)
2. Implementing HTTPS/TLS
3. Adding rate limiting
4. Implementing proper error handling
5. Adding logging and monitoring
6. Database migrations (Alembic)
7. Input validation and sanitization
8. Privacy controls (GDPR compliance)
9. Audit trails
10. Secure credential storage

## Development

### Running Tests

```bash
cd backend
pytest tests/
```

### Project Dependencies

- **FastAPI**: Web framework
- **InsightFace**: Face recognition
- **OpenCV**: Image processing
- **SQLAlchemy**: ORM for database
- **Uvicorn**: ASGI server

## Resources

- [InsightFace Documentation](https://github.com/deepinsight/insightface)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## License

This is a demo project for educational purposes. Use at your own risk.

## Contributing

This is a demo/learning project. Feel free to fork and modify for your own learning!

## Acknowledgments

- InsightFace team for the excellent face recognition models
- FastAPI for the modern Python web framework

---

**Setup Time:** ~15 minutes including dependencies

**Questions?** Check the API docs at `http://localhost:8000/docs` or review the code comments.

---

## 📥 File Download Instructions

All files mentioned in this README are provided as separate artifacts in this conversation. To set up the project:

### Method 1: Copy Files Individually
1. Create the directory structure as shown in "Project Structure"
2. Copy each file content from the artifacts into the corresponding file
3. Ensure proper file names and extensions

### Method 2: Complete File List

**Root Directory Files:**
- `start_demo.sh` - Startup script for Linux/Mac
- `start_demo.bat` - Startup script for Windows  
- `README.md` - This documentation
- `PROJECT_STRUCTURE.md` - Architecture guide
- `QUICK_REFERENCE.md` - Quick reference
- `.gitignore` - Git exclusions

**backend/ Files:**
- `backend/main.py` - FastAPI application
- `backend/models.py` - Database models
- `backend/database.py` - Database config
- `backend/recognition.py` - Face recognition
- `backend/requirements.txt` - Dependencies
- `backend/run_demo.sh` - Backend startup
- `backend/.env.example` - Config template

**frontend/ Files:**
- `frontend/index.html` - UI page
- `frontend/main.js` - JavaScript logic
- `frontend/styles.css` - Styling

**Total: 16 core files** (19 including documentation)

### Quick Setup Commands

```bash
# Create directory structure
mkdir -p face-attendance-demo/backend
mkdir -p face-attendance-demo/frontend

# Copy files to their locations
# (Copy each artifact content to the corresponding file)

# Make scripts executable (Linux/Mac)
chmod +x face-attendance-demo/start_demo.sh
chmod +x face-attendance-demo/backend/run_demo.sh

# Run the demo
cd face-attendance-demo
./start_demo.sh
```