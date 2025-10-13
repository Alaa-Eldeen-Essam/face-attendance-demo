# Performance Configuration Guide

## Frontend (main.js)

### 🎬 Speed Control

```javascript
// Line ~500 in startRemoteCameraRecognition()
const fetchInterval = Math.max(recognitionInterval / 2, 100);
```
**What it does**: Controls how fast frames are fetched
- **Lower = Faster** (e.g., 50ms = 20 FPS max)
- **Higher = Slower** (e.g., 200ms = 5 FPS max)
- **Default**: 100ms (10 FPS)
- **Recommended**: 50-150ms

```javascript
// Line ~620 in startRemoteCameraFrameFetch()
const fetchInterval = 100; // 10 FPS for smooth display
```
**What it does**: Frame rate when recognition is OFF
- **Recommended**: 100ms (10 FPS)
- **For slower networks**: 150-200ms

---

### 🖼️ Display Size Control

```javascript
// Line ~150 in startCamera() - RTSP/HTTP section
if (!elements.capture.width) {
    elements.capture.width = 1280;   // ← Change this
    elements.capture.height = 720;   // ← Change this
    elements.overlay.width = 1280;   // ← Change this
    elements.overlay.height = 720;   // ← Change this
}
```
**What it does**: Sets canvas display size
- **Common sizes**:
  - 640x360 (Small)
  - 854x480 (Medium)
  - 1280x720 (HD - Default)
  - 1920x1080 (Full HD)

**Note**: Actual frame size is auto-detected from camera

---

## Backend (main.py)

### 📸 Image Quality Control

```python
# Line ~20 in get_camera_frame()
success, buffer = cv2.imencode('.jpg', frame, [
    cv2.IMWRITE_JPEG_QUALITY, 90,  # ← QUALITY (1-100)
    cv2.IMWRITE_JPEG_OPTIMIZE, 1
])
```
**What it does**: JPEG compression quality
- **Lower = Faster, Blurrier** (e.g., 60)
- **Higher = Slower, Sharper** (e.g., 95)
- **Default**: 90
- **Recommended**: 80-95

---

### 📏 Frame Size Control (Transmission)

```python
# Line ~10 in get_camera_frame()
max_width = 1920  # ← Change this
if width > max_width:
    scale = max_width / width
    new_width = int(width * scale)
    new_height = int(height * scale)
    frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
```
**What it does**: Maximum frame width before sending to frontend
- **Lower = Faster, Lower Quality** (e.g., 854, 1280)
- **Higher = Slower, Higher Quality** (e.g., 1920, 2560)
- **Default**: 1920px
- **Recommended**: 1280-1920px

---

### 🔍 Processing Size Control (Recognition Speed)

```python
# Line ~50 in process_camera_frame()
max_process_width = 1280  # ← Change this
if original_width > max_process_width:
    scale_factor = max_process_width / original_width
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)
    process_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
```
**What it does**: Downsample frame for faster face detection
- **Lower = Faster Recognition, Less Accurate** (e.g., 640, 854)
- **Higher = Slower Recognition, More Accurate** (e.g., 1920)
- **Default**: 1280px
- **Recommended**: 854-1280px

---

## Camera Manager (camera_manager.py)

### ⚡ Buffer Control (Latency)

```python
# Line ~30 in get_frame()
for _ in range(5):  # ← SKIP FRAMES (0-10)
    if not cap.grab():
        break
```
**What it does**: Skip old buffered frames
- **0 = No skipping** (more lag, smoother)
- **5 = Skip 5 frames** (less lag, may stutter)
- **10 = Skip 10 frames** (minimal lag, might skip)
- **Default**: 5
- **Recommended**: 3-7

```python
# Line ~80 in add_camera() - RTSP section
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # ← BUFFER SIZE (1-30)
```
**What it does**: OpenCV internal buffer
- **1 = Minimal latency** (Default)
- **5-10 = More stable, slight lag**
- **Recommended**: 1-3

---

## Quick Presets

### 🚀 **High Speed (Low Quality)**
```javascript
// Frontend
fetchInterval = 50  // 20 FPS
```
```python
# Backend
JPEG_QUALITY = 70
max_width = 854
max_process_width = 640
```

### ⚖️ **Balanced (Recommended)**
```javascript
// Frontend
fetchInterval = 100  // 10 FPS
```
```python
# Backend
JPEG_QUALITY = 85
max_width = 1280
max_process_width = 1280
```

### 💎 **High Quality (Slower)**
```javascript
// Frontend
fetchInterval = 150  // 6-7 FPS
```
```python
# Backend
JPEG_QUALITY = 95
max_width = 1920
max_process_width = 1920
```

### 🌐 **Slow Network**
```javascript
// Frontend
fetchInterval = 200  // 5 FPS
```
```python
# Backend
JPEG_QUALITY = 75
max_width = 854
max_process_width = 640
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Too slow/laggy** | Decrease `fetchInterval`, increase `skip frames`, decrease `max_width` |
| **Too blurry** | Increase `JPEG_QUALITY`, increase `max_width` |
| **Choppy/stuttering** | Increase `fetchInterval`, decrease `skip frames` |
| **Recognition too slow** | Decrease `max_process_width` |
| **Too much bandwidth** | Decrease `JPEG_QUALITY`, decrease `max_width` |
| **Frames behind real-time** | Increase `skip frames` to 7-10 |

---

## Advanced: CSS Display Size

Control display without affecting quality:

```css
/* In styles.css */
#capture {
    width: 100%;        /* Responsive */
    max-width: 1280px;  /* Maximum display size */
    height: auto;
}

#overlay {
    width: 100%;
    max-width: 1280px;
    height: auto;
}
```

This scales display visually without changing actual frame size.

---

## Testing Command

After changing settings, monitor performance:

```javascript
// Add to console (browser)
setInterval(() => {
    console.log('Canvas:', elements.capture.width, 'x', elements.capture.height);
    console.log('Stats:', stats);
}, 5000);
```

Check backend logs for processing time per frame.