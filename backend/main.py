import os
import io
import base64
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import numpy as np
from PIL import Image
import cv2

from database import SessionLocal, init_db, Person, Attendance, Unknown
from recognition import FaceRecognizer
from camera_manager import CameraManager, CameraType, camera_manager

# Configuration
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.6"))
ATTENDANCE_WINDOW_MINUTES = int(os.getenv("ATTENDANCE_WINDOW_MINUTES", "30"))
FACE_QUALITY_THRESHOLD = float(os.getenv("FACE_QUALITY_THRESHOLD", "0.7"))
UNKNOWN_SIMILARITY_THRESHOLD = float(os.getenv("UNKNOWN_SIMILARITY_THRESHOLD", "0.5"))

# Global recognizer instance
recognizer: Optional[FaceRecognizer] = None

# Request/Response Models
class AddPersonRequest(BaseModel):
    name: str
    identifier: str

class MigrateUnknownRequest(BaseModel):
    unknown_id: int
    person_id: Optional[int] = None
    name: Optional[str] = None
    identifier: Optional[str] = None

class CompareImageRequest(BaseModel):
    image_base64: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    global recognizer
    
    # Initialize database
    init_db()
    print("✓ Database initialized")
    
    # Initialize face recognizer with GPU support
    try:
        recognizer = FaceRecognizer(model_name="buffalo_l", use_gpu=True)
        print("✓ InsightFace model loaded (GPU)")
    except Exception as e:
        print(f"⚠ GPU initialization failed: {e}")
        print("Falling back to CPU...")
        recognizer = FaceRecognizer(model_name="buffalo_l", use_gpu=False)
        print("✓ InsightFace model loaded (CPU)")
    
    yield
    
    # Cleanup
    camera_manager.close_all()
    print("Shutting down...")

app = FastAPI(
    title="Face Attendance Demo - Enhanced",
    description="Enhanced facial recognition attendance system with multi-camera support",
    version="2.0.0",
    lifespan=lifespan
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Demo only - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files from root
import os.path
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.get("/")
async def root():
    """Root endpoint - redirect to app."""
    return RedirectResponse(url="/app/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint with GPU info."""
    gpu_info = recognizer.get_provider_info() if recognizer else {"providers": [], "using_gpu": False}
    return {
        "status": "running",
        "model": "buffalo_l",
        "threshold": SIMILARITY_THRESHOLD,
        "gpu_enabled": gpu_info["using_gpu"],
        "providers": gpu_info["providers"]
    }

# Person Management Endpoints

@app.post("/add-person/")
async def add_person(
    name: str = Form(...),
    identifier: str = Form(...),
    file: UploadFile = File(...)
):
    """Add a new person with a face photo."""
    if not recognizer:
        raise HTTPException(status_code=503, detail="Recognizer not initialized")
    
    db = SessionLocal()
    try:
        existing = db.query(Person).filter(Person.identifier == identifier).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Person with identifier {identifier} already exists")
        
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        faces = recognizer.detect_faces(img)
        
        if not faces:
            raise HTTPException(status_code=400, detail="No face detected in image")
        
        if len(faces) > 1:
            raise HTTPException(status_code=400, detail="Multiple faces detected. Please upload image with single face.")
        
        face = faces[0]
        embedding = face['embedding']
        
        _, buffer = cv2.imencode('.jpg', img)
        image_bytes = buffer.tobytes()
        
        person = Person(
            name=name,
            identifier=identifier,
            image_data=image_bytes,
            embeddings=embedding.tobytes(),
            created_at=datetime.utcnow(),
            deleted=False
        )
        
        db.add(person)
        db.commit()
        db.refresh(person)
        
        return {
            "message": "Person added successfully",
            "person_id": person.id,
            "name": person.name,
            "identifier": person.identifier
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add person: {str(e)}")
    finally:
        db.close()

@app.post("/capture-person/")
async def capture_person(
    name: str = Form(...),
    identifier: str = Form(...),
    image_base64: str = Form(...)
):
    """Add a new person from camera capture (base64 image)."""
    if not recognizer:
        raise HTTPException(status_code=503, detail="Recognizer not initialized")
    
    db = SessionLocal()
    try:
        existing = db.query(Person).filter(Person.identifier == identifier).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Person with identifier {identifier} already exists")
        
        image_data = base64.b64decode(image_base64.split(',')[1] if ',' in image_base64 else image_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        faces = recognizer.detect_faces(img)
        
        if not faces:
            raise HTTPException(status_code=400, detail="No face detected in captured image")
        
        if len(faces) > 1:
            raise HTTPException(status_code=400, detail="Multiple faces detected. Please capture with single face.")
        
        face = faces[0]
        embedding = face['embedding']
        
        _, buffer = cv2.imencode('.jpg', img)
        image_bytes = buffer.tobytes()
        
        person = Person(
            name=name,
            identifier=identifier,
            image_data=image_bytes,
            embeddings=embedding.tobytes(),
            created_at=datetime.utcnow(),
            deleted=False
        )
        
        db.add(person)
        db.commit()
        db.refresh(person)
        
        return {
            "message": "Person captured and added successfully",
            "person_id": person.id,
            "name": person.name,
            "identifier": person.identifier
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to capture person: {str(e)}")
    finally:
        db.close()

@app.post("/compare-image/")
async def compare_image(file: UploadFile = File(...)):
    """Compare uploaded image against all known people."""
    if not recognizer:
        raise HTTPException(status_code=503, detail="Recognizer not initialized")
    
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        faces = recognizer.detect_faces(img)
        
        if not faces:
            return {"faces": [], "message": "No faces detected"}
        
        db = SessionLocal()
        try:
            known_people = db.query(Person).filter(Person.deleted == False).all()
            
            results = []
            for face in faces:
                bbox = face['bbox']
                embedding = face['embedding']
                
                best_match = None
                best_score = -1
                
                for person in known_people:
                    stored_embedding = np.frombuffer(person.embeddings, dtype=np.float32)
                    score = recognizer.compare_embeddings(embedding, stored_embedding)
                    
                    if score > best_score:
                        best_score = score
                        best_match = person
                
                if best_match and best_score >= SIMILARITY_THRESHOLD:
                    results.append({
                        "known": True,
                        "person_id": best_match.id,
                        "name": best_match.name,
                        "identifier": best_match.identifier,
                        "bbox": [int(x) for x in bbox],
                        "score": float(best_score)
                    })
                else:
                    results.append({
                        "known": False,
                        "bbox": [int(x) for x in bbox],
                        "score": float(best_score) if best_match else 0.0
                    })
            
            return {"faces": results}
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@app.post("/seed-demo/")
async def seed_demo():
    """Seed the database with demo people."""
    db = SessionLocal()
    try:
        existing = db.query(Person).count()
        if existing > 0:
            return {"message": f"Database already has {existing} people. Clear first to reseed."}
        
        demo_people = [
            {"name": "Ahmed Hassan", "identifier": "MIL-001"},
            {"name": "Fatima Ali", "identifier": "MIL-002"},
            {"name": "Omar Khalil", "identifier": "MIL-003"},
            {"name": "Layla Mostafa", "identifier": "MIL-004"},
        ]
        
        created = []
        for person_data in demo_people:
            color = np.random.randint(50, 200, 3, dtype=np.uint8)
            img = np.ones((200, 200, 3), dtype=np.uint8) * color
            
            cv2.putText(img, person_data["name"].split()[0], (20, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
            
            _, buffer = cv2.imencode('.jpg', img)
            image_bytes = buffer.tobytes()
            
            embedding = np.random.randn(512).astype(np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            
            person = Person(
                name=person_data["name"],
                identifier=person_data["identifier"],
                image_data=image_bytes,
                embeddings=embedding.tobytes(),
                created_at=datetime.utcnow(),
                deleted=False
            )
            db.add(person)
            created.append(person_data["name"])
        
        db.commit()
        
        return {
            "message": f"Successfully seeded {len(created)} demo people",
            "people": created,
            "note": "These use placeholder embeddings. Upload real face photos for actual recognition."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")
    finally:
        db.close()

@app.post("/process-frame/")
async def process_frame(file: UploadFile = File(...)):
    """Process a single video frame for face recognition."""
    if not recognizer:
        raise HTTPException(status_code=503, detail="Recognizer not initialized")
    
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        faces = recognizer.detect_faces(img)
        
        if not faces:
            return {"faces": [], "message": "No faces detected"}
        
        db = SessionLocal()
        try:
            known_people = db.query(Person).filter(Person.deleted == False).all()
            
            results = []
            for face in faces:
                bbox = face['bbox']
                embedding = face['embedding']
                
                best_match = None
                best_score = -1
                
                for person in known_people:
                    stored_embedding = np.frombuffer(person.embeddings, dtype=np.float32)
                    score = recognizer.compare_embeddings(embedding, stored_embedding)
                    
                    if score > best_score:
                        best_score = score
                        best_match = person
                
                if best_match and best_score >= SIMILARITY_THRESHOLD:
                    record_attendance(db, best_match.id, best_match.name, best_match.identifier)
                    
                    results.append({
                        "known": True,
                        "person_id": best_match.id,
                        "name": best_match.name,
                        "identifier": best_match.identifier,
                        "bbox": [int(x) for x in bbox],
                        "score": float(best_score)
                    })
                else:
                    unk_id = save_unknown_face(db, img, bbox, embedding)
                    
                    results.append({
                        "known": False,
                        "bbox": [int(x) for x in bbox],
                        "score": float(best_score) if best_match else 0.0,
                        "unk_id": unk_id
                    })
            
            db.commit()
            return {"faces": results}
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

def record_attendance(db, person_id: int, name: str, identifier: str):
    """Record or update attendance for a person."""
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=ATTENDANCE_WINDOW_MINUTES)
    
    recent = db.query(Attendance).filter(
        Attendance.person_id == person_id,
        Attendance.arrival_time >= window_start,
        Attendance.departure_time.is_(None)
    ).first()
    
    if recent:
        return recent
    
    attendance = Attendance(
        person_id=person_id,
        name=name,
        identifier=identifier,
        arrival_time=now,
        departure_time=None,
        auto=True,
        created_at=now
    )
    db.add(attendance)
    return attendance

def save_unknown_face(db, img, bbox, embedding) -> Optional[int]:
    """
    Save unknown face with intelligent deduplication.
    Only saves if:
    1. No existing unknown with similarity >= threshold
    2. No recent unknown (within last 5 minutes) with high similarity
    """
    x, y, w, h = [int(v) for v in bbox]
    
    # Validate bbox
    if x < 0 or y < 0 or w <= 0 or h <= 0:
        return None
    
    # Ensure we don't go out of bounds
    img_h, img_w = img.shape[:2]
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = min(w, img_w - x)
    h = min(h, img_h - y)
    
    face_crop = img[y:y+h, x:x+w]
    
    # Encode face crop as JPEG
    success, buffer = cv2.imencode('.jpg', face_crop)
    if not success:
        return None
    
    image_bytes = buffer.tobytes()
    
    # Get recent unknowns (last 5 minutes)
    from datetime import timedelta
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    
    recent_unknowns = db.query(Unknown).filter(
        Unknown.detected_at >= five_minutes_ago
    ).all()
    
    # Check similarity against recent unknowns
    for existing in recent_unknowns:
        existing_embedding = np.frombuffer(existing.embeddings, dtype=np.float32)
        similarity = recognizer.compare_embeddings(embedding, existing_embedding)
        
        # If very similar to recent unknown, don't create duplicate
        if similarity >= UNKNOWN_SIMILARITY_THRESHOLD:
            print(f"Duplicate unknown face detected (similarity: {similarity:.3f}), using existing ID: {existing.id}")
            return existing.id
    
    # Also check ALL unknowns with a slightly higher threshold
    # This prevents duplicates even if time window passed
    all_unknowns = db.query(Unknown).all()
    
    for existing in all_unknowns:
        if existing in recent_unknowns:
            continue  # Already checked
        
        existing_embedding = np.frombuffer(existing.embeddings, dtype=np.float32)
        similarity = recognizer.compare_embeddings(embedding, existing_embedding)
        
        # Use even higher threshold for old unknowns
        if similarity >= 0.90:  # 90% similarity
            print(f"Very similar to existing unknown (similarity: {similarity:.3f}), using existing ID: {existing.id}")
            return existing.id
    
    # No similar unknown found, create new entry
    unknown = Unknown(
        image_data=image_bytes,
        embeddings=embedding.tobytes(),
        detected_at=datetime.utcnow()
    )
    db.add(unknown)
    db.flush()
    
    print(f"New unknown face saved with ID: {unknown.id}")
    return unknown.id

# Unknown Face Management

@app.get("/unknown-faces/")
async def list_unknown_faces():
    """List all unknown faces detected."""
    db = SessionLocal()
    try:
        unknowns = db.query(Unknown).order_by(Unknown.detected_at.desc()).all()
        
        result = []
        for unknown in unknowns:
            img_b64 = base64.b64encode(unknown.image_data).decode('utf-8')
            
            result.append({
                "id": unknown.id,
                "image": f"data:image/jpeg;base64,{img_b64}",
                "detected_at": unknown.detected_at.isoformat()
            })
        
        return {"unknowns": result}
    finally:
        db.close()

@app.post("/migrate-unknown/")
async def migrate_unknown(request: MigrateUnknownRequest):
    """Migrate an unknown face to person."""
    db = SessionLocal()
    try:
        unknown = db.query(Unknown).filter(Unknown.id == request.unknown_id).first()
        if not unknown:
            raise HTTPException(status_code=404, detail="Unknown face not found")
        
        embedding = np.frombuffer(unknown.embeddings, dtype=np.float32)
        
        if request.person_id:
            person = db.query(Person).filter(Person.id == request.person_id).first()
            if not person:
                raise HTTPException(status_code=404, detail="Person not found")
            
            message = f"Unknown face associated with existing person: {person.name}"
            
        elif request.name and request.identifier:
            existing = db.query(Person).filter(Person.identifier == request.identifier).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Identifier {request.identifier} already exists")
            
            person = Person(
                name=request.name,
                identifier=request.identifier,
                image_data=unknown.image_data,
                embeddings=unknown.embeddings,
                created_at=datetime.utcnow(),
                deleted=False
            )
            db.add(person)
            db.flush()
            
            message = f"Unknown face migrated to new person: {request.name}"
        else:
            raise HTTPException(status_code=400, detail="Must provide either person_id or (name and identifier)")
        
        db.delete(unknown)
        db.commit()
        
        return {"message": message, "person_id": person.id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")
    finally:
        db.close()

@app.delete("/unknown-faces/{unknown_id}")
async def delete_unknown(unknown_id: int):
    """Delete an unknown face."""
    db = SessionLocal()
    try:
        unknown = db.query(Unknown).filter(Unknown.id == unknown_id).first()
        if not unknown:
            raise HTTPException(status_code=404, detail="Unknown face not found")
        
        db.delete(unknown)
        db.commit()
        
        return {"message": "Unknown face deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# People & Attendance Endpoints

@app.get("/people/")
async def list_people():
    """List all known people with their images."""
    db = SessionLocal()
    try:
        people = db.query(Person).filter(Person.deleted == False).all()
        
        result = []
        for person in people:
            img_b64 = base64.b64encode(person.image_data).decode('utf-8')
            
            result.append({
                "id": person.id,
                "name": person.name,
                "identifier": person.identifier,
                "image": f"data:image/jpeg;base64,{img_b64}",
                "created_at": person.created_at.isoformat()
            })
        
        return {"people": result}
    finally:
        db.close()

@app.get("/attendance/")
async def list_attendance(limit: int = 50):
    """List recent attendance records."""
    db = SessionLocal()
    try:
        records = db.query(Attendance)\
            .order_by(Attendance.arrival_time.desc())\
            .limit(limit)\
            .all()
        
        result = []
        for record in records:
            result.append({
                "id": record.id,
                "person_id": record.person_id,
                "name": record.name,
                "identifier": record.identifier,
                "arrival_time": record.arrival_time.isoformat(),
                "departure_time": record.departure_time.isoformat() if record.departure_time else None,
                "auto": record.auto
            })
        
        return {"attendance": result}
    finally:
        db.close()

@app.delete("/clear-data/")
async def clear_data():
    """Clear all data."""
    db = SessionLocal()
    try:
        db.query(Attendance).delete()
        db.query(Person).delete()
        db.query(Unknown).delete()
        db.commit()
        return {"message": "All data cleared"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# Camera Management Endpoints

@app.get("/cameras/discover")
async def discover_cameras():
    """Discover available webcams."""
    available = CameraManager.discover_webcams()
    return {"available_webcams": available, "count": len(available)}

@app.post("/cameras/add")
async def add_camera(
    camera_id: str = Form(...),
    source: str = Form(...),
    camera_type: str = Form(...)
):
    """Add a camera source."""
    try:
        cam_type = CameraType(camera_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid camera type: {camera_type}")
    
    success = camera_manager.add_camera(camera_id, source, cam_type)
    
    if success:
        return {
            "message": f"Camera {camera_id} added successfully",
            "camera": camera_manager.get_camera_info(camera_id)
        }
    else:
        raise HTTPException(status_code=500, detail=f"Failed to add camera {camera_id}")

@app.get("/cameras/list")
async def list_cameras():
    """List all active cameras."""
    cameras = camera_manager.list_cameras()
    return {"cameras": cameras, "count": len(cameras)}

@app.get("/cameras/{camera_id}")
async def get_camera_info(camera_id: str):
    """Get info for specific camera."""
    info = camera_manager.get_camera_info(camera_id)
    if info:
        return info
    raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")

@app.delete("/cameras/{camera_id}")
async def remove_camera(camera_id: str):
    """Remove a camera."""
    success = camera_manager.remove_camera(camera_id)
    if success:
        return {"message": f"Camera {camera_id} removed"}
    raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")

@app.post("/cameras/{camera_id}/reconnect")
async def reconnect_camera(camera_id: str):
    """Attempt to reconnect a camera."""
    success = camera_manager.reconnect_camera(camera_id)
    if success:
        return {"message": f"Camera {camera_id} reconnected", "camera": camera_manager.get_camera_info(camera_id)}
    raise HTTPException(status_code=500, detail=f"Failed to reconnect camera {camera_id}")

@app.post("/cameras/test-rtsp")
async def test_rtsp(url: str = Form(...)):
    """Test RTSP connection."""
    success = CameraManager.test_rtsp_connection(url)
    return {
        "url": url,
        "accessible": success,
        "message": "RTSP stream is accessible" if success else "Failed to connect to RTSP stream"
    }

# Replace these endpoints in main.py

@app.get("/cameras/{camera_id}/get-frame")
async def get_camera_frame(camera_id: str):
    """
    Get a single frame from camera. Optimized for quality and speed.
    """
    frame = camera_manager.get_frame(camera_id)
    
    if frame is None:
        raise HTTPException(status_code=500, detail=f"Failed to get frame from camera {camera_id}")
    
    # Resize only if absolutely necessary (keep quality)
    height, width = frame.shape[:2]
    max_width = 1920  # Increased from 1280
    if width > max_width:
        scale = max_width / width
        new_width = int(width * scale)
        new_height = int(height * scale)
        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)  # Better quality
    
    # Higher quality JPEG encoding
    success, buffer = cv2.imencode('.jpg', frame, [
        cv2.IMWRITE_JPEG_QUALITY, 90,  # Increased from 75
        cv2.IMWRITE_JPEG_OPTIMIZE, 1
    ])
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode frame")
    
    from fastapi.responses import Response
    return Response(
        content=buffer.tobytes(),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.post("/process-camera-frame/{camera_id}")
async def process_camera_frame(camera_id: str):
    """
    Process frame with optimized performance.
    Uses cached frame and smart downscaling.
    """
    if not recognizer:
        raise HTTPException(status_code=503, detail="Recognizer not initialized")
    
    frame = camera_manager.get_frame(camera_id)
    if frame is None:
        raise HTTPException(status_code=500, detail=f"Failed to get frame from camera {camera_id}")
    
    try:
        original_height, original_width = frame.shape[:2]
        
        # Smart resizing for processing
        process_frame = frame
        scale_factor = 1.0
        
        # Only downscale if very large (> 1280px)
        max_process_width = 1280
        if original_width > max_process_width:
            scale_factor = max_process_width / original_width
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            process_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Detect faces
        faces = recognizer.detect_faces(process_frame)
        
        if not faces:
            return {
                "faces": [], 
                "message": "No faces detected", 
                "camera_id": camera_id,
                "frame_size": {"width": original_width, "height": original_height}
            }
        
        db = SessionLocal()
        try:
            known_people = db.query(Person).filter(Person.deleted == False).all()
            
            # Pre-load embeddings for faster comparison
            known_embeddings = []
            for person in known_people:
                emb = np.frombuffer(person.embeddings, dtype=np.float32)
                known_embeddings.append((person, emb))
            
            results = []
            for face in faces:
                bbox = face['bbox']
                embedding = face['embedding']
                
                # Scale bbox back to original if needed
                if scale_factor != 1.0:
                    bbox = [
                        int(bbox[0] / scale_factor),
                        int(bbox[1] / scale_factor),
                        int(bbox[2] / scale_factor),
                        int(bbox[3] / scale_factor)
                    ]
                
                best_match = None
                best_score = -1
                
                # Faster comparison with pre-loaded embeddings
                for person, stored_embedding in known_embeddings:
                    score = recognizer.compare_embeddings(embedding, stored_embedding)
                    if score > best_score:
                        best_score = score
                        best_match = person
                
                if best_match and best_score >= SIMILARITY_THRESHOLD:
                    record_attendance(db, best_match.id, best_match.name, best_match.identifier)
                    
                    results.append({
                        "known": True,
                        "person_id": best_match.id,
                        "name": best_match.name,
                        "identifier": best_match.identifier,
                        "bbox": bbox,
                        "score": float(best_score)
                    })
                else:
                    unk_id = save_unknown_face(db, frame, bbox, embedding)
                    
                    results.append({
                        "known": False,
                        "bbox": bbox,
                        "score": float(best_score) if best_match else 0.0,
                        "unk_id": unk_id
                    })
            
            db.commit()
            return {
                "faces": results, 
                "camera_id": camera_id,
                "frame_size": {"width": original_width, "height": original_height}
            }
            
        finally:
            db.close()
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)