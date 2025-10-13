# Project Structure Guide

## Complete Directory Layout

```
face-attendance-demo/           # ← PROJECT ROOT (run start_demo.sh from here)
│
├── start_demo.sh              # ← Linux/Mac startup script
├── start_demo.bat             # ← Windows startup script
├── README.md                  # ← Main documentation
├── .gitignore                 # ← Git exclusions
│
├── backend/                   # ← Backend application
│   ├── main.py               # ← FastAPI app & endpoints (START HERE)
│   ├── models.py             # ← Database models (Person, Attendance, Unknown)
│   ├── database.py           # ← SQLAlchemy configuration
│   ├── recognition.py        # ← InsightFace wrapper for face recognition
│   ├── requirements.txt      # ← Python dependencies
│   ├── run_demo.sh          # ← Backend-only startup script
│   ├── .env.example         # ← Configuration template
│   │
│   ├── venv/                # ← Virtual environment (created automatically)
│   └── attendance_demo.db   # ← SQLite database (created at runtime)
│
└── frontend/                  # ← Frontend application
    ├── index.html            # ← Main UI page
    ├── main.js               # ← Frontend logic (webcam, API calls)
    └── styles.css            # ← Styling
```

## File Purposes

### Root Directory Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `start_demo.sh` | Complete startup for Linux/Mac | **Use this to start everything** |
| `start_demo.bat` | Complete startup for Windows | **Use this to start everything** |
| `README.md` | Full documentation | Reference for setup and usage |
| `.gitignore` | Git exclusions | Automatic |

### Backend Files

| File | Purpose | Key Features |
|------|---------|--------------|
| `main.py` | Core application | • API endpoints<br>• Request handling<br>• Frontend serving<br>• Attendance logic |
| `models.py` | Data models | • Person table<br>• Attendance table<br>• Unknown faces table |
| `database.py` | DB configuration | • SQLAlchemy setup<br>• Session management |
| `recognition.py` | Face recognition | • InsightFace wrapper<br>• Face detection<br>• Embedding comparison<br>• Cosine similarity |
| `requirements.txt` | Dependencies | • All Python packages<br>• Version specifications |

### Frontend Files

| File | Purpose | Key Features |
|------|---------|--------------|
| `index.html` | UI structure | • Video display<br>• Controls<br>• People list<br>• Attendance log |
| `main.js` | Application logic | • Webcam access<br>• Frame capture<br>• API communication<br>• UI updates |
| `styles.css` | Visual design | • Modern styling<br>• Responsive layout<br>• Animations |

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
│  (Browser: http://localhost:8000)                          │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│  │ Webcam   │───>│ Canvas   │───>│ Capture  │            │
│  │ Stream   │    │ Overlay  │    │ (JPEG)   │            │
│  └──────────┘    └──────────┘    └────┬─────┘            │
│                                        │                    │
└────────────────────────────────────────┼────────────────────┘
                                         │ HTTP POST
                                         │ /process-frame/
                                         ▼
┌─────────────────────────────────────────────────────────────┐
│                         BACKEND                             │
│  (FastAPI: http://localhost:8000)                          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ FastAPI      │───>│ InsightFace  │───>│ Database     │ │
│  │ Endpoints    │    │ Recognition  │    │ (SQLite)     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Receive frame                                    │  │
│  │  2. Detect faces (bbox + embeddings)                │  │
│  │  3. Compare with known people (cosine similarity)   │  │
│  │  4. Record attendance if match found                │  │
│  │  5. Return results (JSON)                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │ JSON Response
                            │ {faces: [...]}
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (UI Update)                     │
│                                                             │
│  • Draw bounding boxes on overlay canvas                   │
│  • Display names for recognized faces                      │
│  • Update attendance list                                  │
│  • Update statistics                                       │
└─────────────────────────────────────────────────────────────┘
```

## Request Flow Example

### 1. User Clicks "Start Recognition"

```javascript
// frontend/main.js
startRecognition() {
  recognitionTimer = setInterval(captureAndRecognize, 1000);
}
```

### 2. Frame Captured Every Second

```javascript
// frontend/main.js
captureAndRecognize() {
  // Draw video to canvas
  ctx.drawImage(video, 0, 0);
  
  // Convert to blob and POST
  canvas.toBlob(async (blob) => {
    const formData = new FormData();
    formData.append('file', blob, 'frame.jpg');
    
    const response = await fetch('http://localhost:8000/process-frame/', {
      method: 'POST',
      body: formData
    });
  });
}
```

### 3. Backend Processes Frame

```python
# backend/main.py
@app.post("/process-frame/")
async def process_frame(file: UploadFile):
    # 1. Read image
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 2. Detect faces
    faces = recognizer.detect_faces(img)
    
    # 3. Match against known people
    for face in faces:
        best_match = find_best_match(face.embedding)
        
        if best_match.score >= THRESHOLD:
            # 4. Record attendance
            record_attendance(db, best_match.person_id)
    
    # 5. Return results
    return {"faces": results}
```

### 4. Frontend Updates UI

```javascript
// frontend/main.js
handleRecognitionResult(data) {
  data.faces.forEach(face => {
    // Draw green box for known, red for unknown
    ctx.strokeStyle = face.known ? '#00ff00' : '#ff0000';
    ctx.strokeRect(x, y, w, h);
    
    // Display name
    ctx.fillText(face.name, x, y - 8);
  });
}
```

## Database Schema

### Person Table
```sql
CREATE TABLE persons (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    identifier TEXT UNIQUE NOT NULL,
    image_data BLOB NOT NULL,
    embeddings BLOB NOT NULL,      -- 512 floats (2048 bytes)
    created_at DATETIME NOT NULL,
    deleted BOOLEAN DEFAULT 0
);
```

### Attendance Table
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY,
    person_id INTEGER NOT NULL,
    name TEXT NOT NULL,             -- Denormalized
    identifier TEXT NOT NULL,       -- Denormalized
    arrival_time DATETIME NOT NULL,
    departure_time DATETIME,
    auto BOOLEAN DEFAULT 1,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (person_id) REFERENCES persons(id)
);
```

### Unknown Table
```sql
CREATE TABLE unknown_faces (
    id INTEGER PRIMARY KEY,
    image_data BLOB NOT NULL,
    embeddings BLOB NOT NULL,
    detected_at DATETIME NOT NULL
);
```

## Configuration Options

### Environment Variables (backend/.env)

```bash
# Face recognition threshold (0.0 - 1.0)
# Lower = more lenient, Higher = more strict
SIMILARITY_THRESHOLD=0.6

# Minimum face quality score (0.0 - 1.0)
FACE_QUALITY_THRESHOLD=0.7

# Time window to prevent duplicate attendance (minutes)
ATTENDANCE_WINDOW_MINUTES=30

# InsightFace model name
INSIGHTFACE_MODEL=buffalo_l

# Server configuration
HOST=0.0.0.0
PORT=8000
```

### Frontend Configuration (frontend/main.js)

```javascript
// API endpoint
const API_BASE = 'http://localhost:8000';

// Frame capture interval (milliseconds)
let recognitionInterval = 1000;

// Recognition threshold
let similarityThreshold = 0.6;
```

## Common Operations

### Adding Real People (Instead of Demo Data)

1. Capture face photo
2. Extract embedding:
```python
from recognition import FaceRecognizer
recognizer = FaceRecognizer()
faces = recognizer.detect_faces(photo)
embedding = faces[0]['embedding']
```
3. Store in database:
```python
person = Person(
    name="John Doe",
    identifier="EMP-001",
    image_data=photo_bytes,
    embeddings=embedding.tobytes()
)
db.add(person)
db.commit()
```

### Adjusting Recognition Sensitivity

**Too many false positives?** Increase threshold:
```bash
export SIMILARITY_THRESHOLD=0.75
```

**Too many false negatives?** Decrease threshold:
```bash
export SIMILARITY_THRESHOLD=0.50
```

### Viewing Logs

Backend logs show recognition activity:
```
INFO: Face detected with score 0.87 - Match: Ahmed Hassan (MIL-001)
INFO: Attendance recorded for person_id=1
```

## Troubleshooting by File

| Issue | Check This File | Look For |
|-------|----------------|----------|
| Server won't start | `backend/main.py` | Import errors, port conflicts |
| No faces detected | `backend/recognition.py` | Model loading, detection parameters |
| Database errors | `backend/database.py` | Connection string, permissions |
| Camera not working | `frontend/main.js` | getUserMedia permissions |
| UI not updating | `frontend/main.js` | API_BASE URL, CORS errors |
| Styling issues | `frontend/styles.css` | CSS conflicts, responsiveness |

## Development Workflow

1. **Make backend changes**: Edit `backend/*.py`
2. **Server auto-reloads**: Thanks to `--reload` flag
3. **Make frontend changes**: Edit `frontend/*`
4. **Refresh browser**: Changes take effect immediately
5. **Check logs**: Terminal shows all requests/errors

## Production Considerations

This is a **DEMO**. For production, you must add:

- [ ] Authentication (OAuth2/JWT)
- [ ] HTTPS/TLS encryption
- [ ] Rate limiting
- [ ] Input validation
- [ ] Error logging (Sentry, etc.)
- [ ] Database migrations (Alembic)
- [ ] Proper secret management
- [ ] GDPR/privacy compliance
- [ ] Load balancing
- [ ] Monitoring & alerts

---

**Quick Reference**: Run `./start_demo.sh` from project root, then visit http://localhost:8000