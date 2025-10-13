# Quick Reference Guide

## 🚀 Start in 3 Steps

### Step 1: Get the Files
Download all project files and extract to a directory called `face-attendance-demo`

### Step 2: Run Startup Script
```bash
# Linux/Mac
cd face-attendance-demo
chmod +x start_demo.sh
./start_demo.sh

# Windows
cd face-attendance-demo
start_demo.bat
```

### Step 3: Open Browser
Visit: **http://localhost:8000**

**That's it!** 🎉

---

## 📋 Complete File Checklist

Make sure you have all these files:

```
✅ Root Directory (9 files)
   - start_demo.sh              (Linux/Mac startup)
   - start_demo.bat             (Windows startup)
   - README.md                  (Full documentation)
   - PROJECT_STRUCTURE.md       (Architecture guide)
   - QUICK_REFERENCE.md         (This file)
   - .gitignore                 (Git exclusions)

✅ backend/ Directory (7 files)
   - main.py                    (FastAPI application)
   - models.py                  (Database models)
   - database.py                (DB configuration)
   - recognition.py             (Face recognition logic)
   - requirements.txt           (Python dependencies)
   - run_demo.sh                (Backend-only script)
   - .env.example               (Config template)

✅ frontend/ Directory (3 files)
   - index.html                 (UI page)
   - main.js                    (JavaScript logic)
   - styles.css                 (Styling)
```

**Total: 19 files**

---

## 🎯 First-Time Usage Flow

### After Starting the Server:

1. **Browser opens to** `http://localhost:8000`
   
2. **Click "Seed Demo People"**
   - Creates 4 test personnel
   - Uses placeholder embeddings (random for demo)
   - See them appear in "Known People" panel

3. **Click "Start Camera"**
   - Browser asks for webcam permission → Allow
   - Live video feed appears

4. **Click "Start Recognition"**
   - System starts processing frames every 1 second
   - Green boxes = Recognized faces
   - Red boxes = Unknown faces
   - Names appear above green boxes
   - Attendance automatically logged

5. **Check Results**
   - "Recent Attendance" panel updates in real-time
   - Statistics show detection counts
   - Green badge indicates auto-detected

---

## 🔧 Common Configuration Changes

### Change Recognition Speed

**In the UI:**
- Adjust "Frame Interval" slider (100-5000ms)
- Lower = faster recognition, higher CPU usage
- Higher = slower recognition, lower CPU usage

### Change Recognition Threshold

**In the UI:**
- Adjust "Threshold" slider (0.0-1.0)
- Lower = more lenient (more false positives)
- Higher = more strict (more false negatives)
- Default: 0.6

**Via Environment Variable:**
```bash
# Edit backend/.env
SIMILARITY_THRESHOLD=0.7
```

### Change Attendance Window

Prevent duplicate entries within X minutes:

```bash
# Edit backend/.env
ATTENDANCE_WINDOW_MINUTES=30
```

---

## 📡 API Endpoints Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Redirects to frontend |
| `/health` | GET | Server health check |
| `/seed-demo/` | POST | Create demo people |
| `/process-frame/` | POST | Process video frame |
| `/people/` | GET | List known people |
| `/attendance/` | GET | List attendance records |
| `/clear-data/` | DELETE | Clear all data |
| `/docs` | GET | API documentation |

**Test API with curl:**
```bash
# Health check
curl http://localhost:8000/health

# List people
curl http://localhost:8000/people/

# List attendance
curl http://localhost:8000/attendance/
```

---

## 🐛 Troubleshooting Quick Fixes

### Server Won't Start

**Error:** `Port 8000 already in use`
```bash
# Find and kill process on port 8000
# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Error:** `Python not found`
```bash
# Install Python 3.8+
# Linux: sudo apt install python3
# Mac: brew install python3
# Windows: Download from python.org
```

### Camera Not Working

**Issue:** Browser doesn't show video
- Check camera is not in use by another app
- Allow camera permissions in browser
- Try a different browser (Chrome recommended)
- Check camera works in other apps first

**Issue:** `getUserMedia is not defined`
- Must use http://localhost or https://
- File:// protocol has restrictions
- Use the provided startup script (serves via HTTP)

### Recognition Not Working

**Issue:** No faces detected
- Ensure good lighting
- Face camera directly
- Move closer to camera
- Check "Faces Detected" counter increases

**Issue:** Faces detected but not recognized
- Lower the threshold (try 0.5)
- Remember: Demo uses random embeddings!
- For real recognition, upload actual face photos

### Database Issues

**Error:** `database is locked`
```bash
# Stop server, delete DB, restart
rm backend/attendance_demo.db
./start_demo.sh
```

**Error:** `no such table`
```bash
# Database not initialized
# Just restart - lifespan event will recreate tables
```

---

## 💡 Tips & Best Practices

### For Best Recognition Results:

1. **Good Lighting** 
   - Face should be well-lit
   - Avoid backlighting
   - No harsh shadows

2. **Camera Position**
   - Face the camera directly
   - Keep face centered in frame
   - Distance: 1-2 meters optimal

3. **Face Visibility**
   - Remove glasses/hats if possible
   - Hair shouldn't cover face
   - Look at camera

4. **Threshold Tuning**
   - Start at 0.6 (default)
   - Too many unknowns? Lower to 0.5
   - Too many false matches? Raise to 0.7

### Performance Optimization:

```javascript
// In frontend/main.js
// Slower interval = less CPU usage
recognitionInterval = 2000;  // 2 seconds instead of 1

// Smaller video resolution
video: { width: 640, height: 480 }  // Instead of 1280x720
```

### Using Real Face Data:

Instead of demo seed data, add real people:

```python
# Upload actual photo and extract embedding
from recognition import FaceRecognizer
recognizer = FaceRecognizer()

# Load photo
img = cv2.imread('person_photo.jpg')

# Extract embedding
faces = recognizer.detect_faces(img)
embedding = faces[0]['embedding']

# Save to database
person = Person(
    name="Real Person",
    identifier="EMP-123",
    image_data=open('person_photo.jpg', 'rb').read(),
    embeddings=embedding.tobytes()
)
db.add(person)
db.commit()
```

---

## 📊 Understanding the Statistics

### Faces Detected
- Total number of face detections across all frames
- Increments for every face found, known or unknown

### Recognized
- Faces matched with known people
- Match score above threshold

### Unknown
- Faces detected but not matched
- Either new people or match score too low

### Last Update
- Timestamp of most recent frame processing
- Should update every 1 second (default interval)

---

## 🔐 Security Reminders

⚠️ **THIS IS A DEMO - NOT PRODUCTION READY**

**Missing Security Features:**
- ❌ No authentication
- ❌ No authorization
- ❌ No HTTPS/TLS
- ❌ No input validation
- ❌ No rate limiting
- ❌ No audit logging
- ❌ No data encryption
- ❌ No privacy controls

**For Production Use, Add:**
- ✅ User authentication (OAuth2/JWT)
- ✅ Role-based access control
- ✅ HTTPS with proper certificates
- ✅ Input sanitization
- ✅ Rate limiting (Redis + middleware)
- ✅ Comprehensive logging
- ✅ Database encryption at rest
- ✅ GDPR compliance features
- ✅ Consent management
- ✅ Data retention policies

---

## 📞 Getting Help

### Check Logs
```bash
# Server logs show everything
# Watch the terminal where server is running
```

### API Documentation
```
http://localhost:8000/docs
```
Interactive API docs with test interface

### Common Log Messages

**Good Signs:**
```
✓ Database initialized
✓ InsightFace model loaded
INFO: Face detected with score 0.87
INFO: Attendance recorded
```

**Warning Signs:**
```
WARNING: No faces detected in frame
WARNING: Low confidence match (0.45)
ERROR: Camera access denied
ERROR: Model not found
```

---

## 🎓 Learning Resources

### Understanding the Code:

1. **Start with:** `backend/main.py`
   - See endpoint definitions
   - Understand request flow

2. **Then read:** `backend/recognition.py`
   - Face detection logic
   - Embedding extraction
   - Similarity calculation

3. **Frontend:** `frontend/main.js`
   - Webcam handling
   - API communication
   - UI updates

### Key Concepts:

- **Face Embedding:** 512-dimensional vector representing a face
- **Cosine Similarity:** Measure of similarity between embeddings (0-1)
- **Threshold:** Minimum similarity to consider a match
- **Smart Attendance:** Deduplication logic to prevent double entries

---

## 🚦 Project Status Indicators

### Server Running Successfully:
```
✓ Database initialized
✓ InsightFace model loaded
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete
```

### Frontend Working:
- Video feed displays
- Controls are responsive
- Statistics update in real-time
- No errors in browser console (F12)

### Recognition Active:
- "Last Update" timestamp changes every interval
- "Faces Detected" counter increases
- Bounding boxes appear on video
- Attendance list updates

---

## 📝 Quick Command Reference

```bash
# Start everything (from project root)
./start_demo.sh                    # Linux/Mac
start_demo.bat                     # Windows

# Start backend only
cd backend
source venv/bin/activate
uvicorn main:app --reload

# View API docs
open http://localhost:8000/docs

# Check server health
curl http://localhost:8000/health

# Stop server
Ctrl + C

# Clear all data
curl -X DELETE http://localhost:8000/clear-data/

# Install dependencies only
cd backend
pip install -r requirements.txt
```

---

**Last Updated:** 2025  
**Version:** 1.0.0  
**Status:** Demo/Educational Use Only  

---

Need more details? Check **README.md** for comprehensive documentation!