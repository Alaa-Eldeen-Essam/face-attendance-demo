/**
 * Frontend JavaScript for Face Attendance System
 * Supports browser webcam and RTSP/HTTP cameras
 */

// Configuration
const API_BASE = 'http://localhost:8000';
let recognitionInterval = 1000;
let similarityThreshold = 0.6;

// State
let stream = null;
let recognitionTimer = null;
let frameTimer = null;
let isRecognizing = false;
let capturedImageData = null;
let currentUnknownId = null;
let currentCameraSource = 'browser'; // browser, rtsp, http
let activeCameraId = null;
let stats = {
    detected: 0,
    recognized: 0,
    unknown: 0
};

// DOM Elements
const elements = {
    video: document.getElementById('video'),
    overlay: document.getElementById('overlay'),
    capture: document.getElementById('capture'),
    startBtn: document.getElementById('startBtn'),
    stopBtn: document.getElementById('stopBtn'),
    toggleRecognition: document.getElementById('toggleRecognition'),
    capturePhoto: document.getElementById('capturePhoto'),
    status: document.getElementById('status'),
    cameraSource: document.getElementById('cameraSource'),
    webcamSelect: document.getElementById('webcamSelect'),
    discoverCameras: document.getElementById('discoverCameras'),
    rtspUrl: document.getElementById('rtspUrl'),
    testRtsp: document.getElementById('testRtsp'),
    httpUrl: document.getElementById('httpUrl'),
    personName: document.getElementById('personName'),
    personId: document.getElementById('personId'),
    uploadImageBtn: document.getElementById('uploadImageBtn'),
    capturePersonBtn: document.getElementById('capturePersonBtn'),
    imageUpload: document.getElementById('imageUpload'),
    uploadCompareBtn: document.getElementById('uploadCompareBtn'),
    compareUpload: document.getElementById('compareUpload'),
    compareResult: document.getElementById('compareResult'),
    seedBtn: document.getElementById('seedBtn'),
    clearBtn: document.getElementById('clearBtn'),
    refreshPeople: document.getElementById('refreshPeople'),
    refreshUnknown: document.getElementById('refreshUnknown'),
    refreshAttendance: document.getElementById('refreshAttendance'),
    intervalInput: document.getElementById('intervalInput'),
    thresholdInput: document.getElementById('thresholdInput'),
    captureModal: document.getElementById('captureModal'),
    migrateModal: document.getElementById('migrateModal')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadPeople();
    loadAttendance();
    loadUnknownFaces();
    updateCameraSourceUI();
});

function setupEventListeners() {
    elements.startBtn.addEventListener('click', startCamera);
    elements.stopBtn.addEventListener('click', stopCamera);
    elements.toggleRecognition.addEventListener('click', toggleRecognitionMode);
    elements.capturePhoto.addEventListener('click', capturePhotoForPerson);
    elements.cameraSource.addEventListener('change', handleCameraSourceChange);
    elements.discoverCameras.addEventListener('click', discoverWebcams);
    elements.testRtsp.addEventListener('click', testRtspConnection);
    elements.uploadImageBtn.addEventListener('click', () => elements.imageUpload.click());
    elements.imageUpload.addEventListener('change', handleImageUpload);
    elements.capturePersonBtn.addEventListener('click', showCaptureModal);
    elements.uploadCompareBtn.addEventListener('click', () => elements.compareUpload.click());
    elements.compareUpload.addEventListener('change', handleCompareUpload);
    elements.seedBtn.addEventListener('click', seedDemoPeople);
    elements.clearBtn.addEventListener('click', clearAllData);
    elements.refreshPeople.addEventListener('click', loadPeople);
    elements.refreshUnknown.addEventListener('click', loadUnknownFaces);
    elements.refreshAttendance.addEventListener('click', loadAttendance);
    
    elements.intervalInput.addEventListener('change', (e) => {
        recognitionInterval = parseInt(e.target.value);
        if (isRecognizing) {
            stopRecognition();
            startRecognition();
        }
    });
    
    elements.thresholdInput.addEventListener('change', (e) => {
        similarityThreshold = parseFloat(e.target.value);
    });
    
    document.getElementById('confirmCapture').addEventListener('click', confirmPersonCapture);
    document.getElementById('cancelCapture').addEventListener('click', () => {
        elements.captureModal.style.display = 'none';
    });
    document.getElementById('confirmMigrate').addEventListener('click', confirmMigrate);
    document.getElementById('cancelMigrate').addEventListener('click', () => {
        elements.migrateModal.style.display = 'none';
    });
    
    document.querySelectorAll('input[name="migrateOption"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            document.getElementById('newPersonFields').style.display = 
                e.target.value === 'new' ? 'block' : 'none';
            document.getElementById('migratePersonSelect').disabled = 
                e.target.value === 'new';
        });
    });
    
    elements.captureModal.addEventListener('click', (e) => {
        if (e.target === elements.captureModal) {
            elements.captureModal.style.display = 'none';
        }
    });
    
    elements.migrateModal.addEventListener('click', (e) => {
        if (e.target === elements.migrateModal) {
            elements.migrateModal.style.display = 'none';
        }
    });
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            elements.captureModal.style.display = 'none';
            elements.migrateModal.style.display = 'none';
        }
    });
    
    elements.video.addEventListener('loadedmetadata', () => {
        elements.overlay.width = elements.video.videoWidth;
        elements.capture.width = elements.video.videoWidth;
        elements.overlay.height = elements.video.videoHeight;
        elements.capture.height = elements.video.videoHeight;
    });
}

// Camera Source Management
function handleCameraSourceChange() {
    currentCameraSource = elements.cameraSource.value;
    updateCameraSourceUI();
    
    if (isRecognizing) stopRecognition();
    if (stream || activeCameraId) stopCamera();
}

function updateCameraSourceUI() {
    document.getElementById('browserCameraOptions').style.display = currentCameraSource === 'browser' ? 'flex' : 'none';
    document.getElementById('rtspOptions').style.display = currentCameraSource === 'rtsp' ? 'flex' : 'none';
    document.getElementById('httpOptions').style.display = currentCameraSource === 'http' ? 'flex' : 'none';
}

async function discoverWebcams() {
    try {
        elements.discoverCameras.disabled = true;
        elements.discoverCameras.textContent = 'Discovering...';
        
        const response = await fetch(`${API_BASE}/cameras/discover`);
        const data = await response.json();
        
        elements.webcamSelect.innerHTML = data.available_webcams.length === 0 ?
            '<option value="0">No cameras found</option>' :
            data.available_webcams.map((idx) => 
                `<option value="${idx}">Camera ${idx}${idx === 0 ? ' (Default)' : ''}</option>`
            ).join('');
        
        showNotification(data.available_webcams.length === 0 ? 
            'No webcams found' : `Found ${data.count} webcam(s)`, 
            data.available_webcams.length === 0 ? 'warning' : 'success');
    } catch (err) {
        showNotification('Failed to discover webcams', 'error');
    } finally {
        elements.discoverCameras.disabled = false;
        elements.discoverCameras.textContent = '🔍 Discover';
    }
}

async function testRtspConnection() {
    const url = elements.rtspUrl.value.trim();
    if (!url) {
        showNotification('Please enter RTSP URL', 'warning');
        return;
    }
    
    try {
        elements.testRtsp.disabled = true;
        elements.testRtsp.textContent = 'Testing...';
        
        const formData = new FormData();
        formData.append('url', url);
        
        const response = await fetch(`${API_BASE}/cameras/test-rtsp`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        showNotification(data.message, data.accessible ? 'success' : 'error');
    } catch (err) {
        showNotification('Failed to test RTSP connection', 'error');
    } finally {
        elements.testRtsp.disabled = false;
        elements.testRtsp.textContent = 'Test';
    }
}

// Camera Functions
async function startCamera() {
    try {
        if (currentCameraSource === 'browser') {
            const deviceId = elements.webcamSelect.value;
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    ...(deviceId && deviceId !== '0' ? { deviceId: { exact: deviceId } } : {})
                }
            };
            
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            elements.video.srcObject = stream;
            
            elements.video.style.display = 'block';
            elements.capture.style.display = 'none';
            elements.overlay.style.display = 'block';
            
            elements.startBtn.disabled = true;
            elements.stopBtn.disabled = false;
            elements.toggleRecognition.disabled = false;
            elements.capturePhoto.disabled = false;
            elements.status.textContent = 'Camera: On (Browser)';
            elements.status.className = 'status status-success';
            
        } else if (currentCameraSource === 'rtsp' || currentCameraSource === 'http') {
            const url = currentCameraSource === 'rtsp' ? elements.rtspUrl.value.trim() : elements.httpUrl.value.trim();
            if (!url) {
                showNotification(`Please enter ${currentCameraSource.toUpperCase()} URL`, 'warning');
                return;
            }
            
            showNotification('Connecting to camera...', 'info');
            
            const cameraId = `${currentCameraSource}_${Date.now()}`;
            const formData = new FormData();
            formData.append('camera_id', cameraId);
            formData.append('source', url);
            formData.append('camera_type', currentCameraSource);
            
            const response = await fetch(`${API_BASE}/cameras/add`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to connect to camera');
            }
            
            activeCameraId = cameraId;
            
            elements.video.style.display = 'none';
            elements.capture.style.display = 'block';
            elements.overlay.style.display = 'block';
            
            // Set default canvas size
            if (!elements.capture.width) {
                elements.capture.width = 1280;
                elements.capture.height = 720;
                elements.overlay.width = 1280;
                elements.overlay.height = 720;
            }
            
            // Get first frame to set canvas size
            const firstFrame = await fetch(`${API_BASE}/cameras/${activeCameraId}/get-frame`);
            if (firstFrame.ok) {
                const blob = await firstFrame.blob();
                const img = await createImageBitmap(blob);
                elements.capture.width = img.width;
                elements.capture.height = img.height;
                elements.overlay.width = img.width;
                elements.overlay.height = img.height;
                
                const ctx = elements.capture.getContext('2d');
                ctx.drawImage(img, 0, 0);
            }
            
            startRemoteCameraFrameFetch();
            
            elements.startBtn.disabled = true;
            elements.stopBtn.disabled = false;
            elements.toggleRecognition.disabled = false;
            elements.capturePhoto.disabled = true;
            elements.status.textContent = `Camera: On (${currentCameraSource.toUpperCase()})`;
            elements.status.className = 'status status-success';
            
            showNotification('Camera connected successfully', 'success');
        }
    } catch (err) {
        console.error('Camera error:', err);
        showNotification(`Failed to start camera: ${err.message}`, 'error');
    }
}

function startRemoteCameraFrameFetch() {
    console.log('Starting remote camera frame fetch...');
    const fetchInterval = Math.max(recognitionInterval, 500);
    let frameCount = 0;
    let errorCount = 0;
    
    frameTimer = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/cameras/${activeCameraId}/get-frame`, {
                method: 'GET',
                cache: 'no-cache'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);
            
            const img = new Image();
            img.onload = () => {
                const captureCtx = elements.capture.getContext('2d');
                captureCtx.drawImage(img, 0, 0, elements.capture.width, elements.capture.height);
                
                URL.revokeObjectURL(imageUrl);
                
                frameCount++;
                errorCount = 0;
                
                if (frameCount === 1) {
                    console.log('✓ First frame displayed successfully!');
                    showNotification('Camera feed active', 'success');
                } else if (frameCount % 100 === 0) {
                    console.log(`✓ ${frameCount} frames displayed`);
                }
            };
            
            img.onerror = () => {
                errorCount++;
                console.error('Image load error');
            };
            
            img.src = imageUrl;
            
            if (isRecognizing) {
                await processRemoteCameraFrame(blob);
            }
        } catch (err) {
            console.error('Frame fetch error:', err);
            errorCount++;
            
            if (errorCount === 3) {
                showNotification(`Camera feed error: ${err.message}`, 'error');
            }
            
            if (errorCount >= 10) {
                clearInterval(frameTimer);
                frameTimer = null;
                showNotification('Camera disconnected. Please reconnect.', 'error');
                elements.status.textContent = 'Camera: Error';
                elements.status.className = 'status status-error';
            }
        }
    }, fetchInterval);
}

async function processRemoteCameraFrame(blob) {
    try {
        const formData = new FormData();
        formData.append('file', blob, 'frame.jpg');
        
        const response = await fetch(`${API_BASE}/process-frame/`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        handleRecognitionResult(data);
    } catch (err) {
        console.error('Recognition error:', err);
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        elements.video.srcObject = null;
        stream = null;
    }
    
    if (frameTimer) {
        clearInterval(frameTimer);
        frameTimer = null;
    }
    
    if (activeCameraId) {
        fetch(`${API_BASE}/cameras/${activeCameraId}`, {
            method: 'DELETE'
        }).catch(err => console.error('Failed to remove camera:', err));
        activeCameraId = null;
    }
    
    stopRecognition();
    clearOverlay();
    
    elements.video.style.display = 'block';
    elements.capture.style.display = 'none';
    elements.overlay.style.display = 'block';
    
    elements.startBtn.disabled = false;
    elements.stopBtn.disabled = true;
    elements.toggleRecognition.disabled = true;
    elements.capturePhoto.disabled = true;
    elements.status.textContent = 'Camera: Off';
    elements.status.className = 'status';
}

function toggleRecognitionMode() {
    if (isRecognizing) {
        stopRecognition();
    } else {
        startRecognition();
    }
}

function startRecognition() {
    isRecognizing = true;
    elements.toggleRecognition.textContent = 'Stop Recognition';
    elements.toggleRecognition.className = 'btn btn-warning';
    elements.status.textContent = elements.status.textContent.replace('Camera: On', 'Camera: On | Recognition: Active');
    elements.status.className = 'status status-active';
    
    if (currentCameraSource === 'browser') {
        recognitionTimer = setInterval(captureAndRecognize, recognitionInterval);
    } else {
        // For RTSP/HTTP: stop separate frame fetching, start combined recognition
        if (frameTimer) {
            clearInterval(frameTimer);
            frameTimer = null;
        }
        startRemoteCameraRecognition();
    }
}

function stopRecognition() {
    isRecognizing = false;
    if (recognitionTimer) {
        clearInterval(recognitionTimer);
        recognitionTimer = null;
    }
    if (frameTimer) {
        clearInterval(frameTimer);
        frameTimer = null;
    }
    elements.toggleRecognition.textContent = 'Start Recognition';
    elements.toggleRecognition.className = 'btn btn-success';
    elements.status.textContent = elements.status.textContent.replace(' | Recognition: Active', '');
    elements.status.className = 'status status-success';
    clearOverlay();
    
    // Restart frame fetching for RTSP/HTTP if camera is on but recognition is off
    if ((currentCameraSource === 'rtsp' || currentCameraSource === 'http') && activeCameraId) {
        startRemoteCameraFrameFetch();
    }
}
function startRemoteCameraRecognition() {
    console.log('Starting optimized remote camera recognition...');
    
    let frameCount = 0;
    let errorCount = 0;
    let lastProcessTime = Date.now();
    let fpsSum = 0;
    let fpsCount = 0;
    
    // Reduced interval for smoother video
    const fetchInterval = Math.max(recognitionInterval / 2, 100); // Min 100ms = 10 FPS max
    
    frameTimer = setInterval(async () => {
        const startTime = Date.now();
        
        try {
            // Fetch frame AND process it in ONE request
            const response = await fetch(
                `${API_BASE}/process-camera-frame/${activeCameraId}`,
                { 
                    method: 'POST',
                    cache: 'no-cache'
                }
            );
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const recognitionData = await response.json();
            
            // Now fetch the display frame
            const frameResponse = await fetch(
                `${API_BASE}/cameras/${activeCameraId}/get-frame`,
                { cache: 'no-cache' }
            );
            
            if (!frameResponse.ok) {
                throw new Error(`Frame HTTP ${frameResponse.status}`);
            }
            
            const blob = await frameResponse.blob();
            
            // Use createImageBitmap for faster rendering
            const imageBitmap = await createImageBitmap(blob);
            
            // Draw frame
            const captureCtx = elements.capture.getContext('2d');
            captureCtx.drawImage(imageBitmap, 0, 0, elements.capture.width, elements.capture.height);
            
            // Draw recognition overlays
            drawRecognitionOverlay(recognitionData);
            
            frameCount++;
            errorCount = 0;
            
            // Calculate FPS
            const elapsed = Date.now() - lastProcessTime;
            const currentFps = 1000 / elapsed;
            lastProcessTime = Date.now();
            fpsSum += currentFps;
            fpsCount++;
            
            if (frameCount === 1) {
                console.log('✓ Recognition started');
                showNotification('Recognition active', 'success');
            } else if (frameCount % 30 === 0) {
                const avgFps = fpsSum / fpsCount;
                console.log(`Processed ${frameCount} frames (${avgFps.toFixed(1)} FPS avg)`);
                fpsSum = 0;
                fpsCount = 0;
            }
            
        } catch (err) {
            console.error('Recognition error:', err);
            errorCount++;
            
            if (errorCount === 5) {
                showNotification(`Camera error: ${err.message}`, 'warning');
            }
            
            if (errorCount >= 15) {
                stopRecognition();
                showNotification('Camera disconnected. Please reconnect.', 'error');
                elements.status.textContent = 'Camera: Error';
                elements.status.className = 'status status-error';
            }
        }
    }, fetchInterval);
}

// NEW: Draw recognition results efficiently
function drawRecognitionOverlay(data) {
    const overlayCtx = elements.overlay.getContext('2d');
    overlayCtx.clearRect(0, 0, elements.overlay.width, elements.overlay.height);
    
    if (!data.faces || data.faces.length === 0) {
        return;
    }
    
    data.faces.forEach(face => {
        const [x, y, w, h] = face.bbox;
        
        // Draw bounding box with glow effect
        overlayCtx.strokeStyle = face.known ? '#00ff00' : '#ff0000';
        overlayCtx.lineWidth = 3;
        overlayCtx.shadowBlur = 10;
        overlayCtx.shadowColor = face.known ? '#00ff00' : '#ff0000';
        overlayCtx.strokeRect(x, y, w, h);
        overlayCtx.shadowBlur = 0;
        
        // Draw label with better styling
        const label = face.known ? 
            `${face.name} (${(face.score * 100).toFixed(0)}%)` : 
            'Unknown';
        
        overlayCtx.font = 'bold 16px Arial';
        const metrics = overlayCtx.measureText(label);
        const textWidth = metrics.width;
        const padding = 10;
        const labelHeight = 28;
        
        // Semi-transparent background
        overlayCtx.fillStyle = face.known ? 'rgba(0, 255, 0, 0.8)' : 'rgba(255, 0, 0, 0.8)';
        overlayCtx.fillRect(x, y - labelHeight - 5, textWidth + padding * 2, labelHeight);
        
        // Text
        overlayCtx.fillStyle = '#000';
        overlayCtx.fillText(label, x + padding, y - 10);
        
        // Update stats
        stats.detected++;
        if (face.known) stats.recognized++;
        else stats.unknown++;
    });
    
    updateStats();
    
    // Update lists if needed
    if (data.faces.some(f => f.known)) loadAttendance();
    if (data.faces.some(f => !f.known)) loadUnknownFaces();
}

// Update startRemoteCameraFrameFetch for display-only mode (no recognition)
function startRemoteCameraFrameFetch() {
    console.log('Starting remote camera frame display (no recognition)...');
    
    const fetchInterval = 100; // 10 FPS for smooth display
    let frameCount = 0;
    let errorCount = 0;
    
    frameTimer = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/cameras/${activeCameraId}/get-frame`, {
                method: 'GET',
                cache: 'no-cache'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const blob = await response.blob();
            const imageBitmap = await createImageBitmap(blob);
            
            const captureCtx = elements.capture.getContext('2d');
            captureCtx.drawImage(imageBitmap, 0, 0, elements.capture.width, elements.capture.height);
            
            frameCount++;
            errorCount = 0;
            
            if (frameCount === 1) {
                console.log('✓ Camera feed active');
                showNotification('Camera feed active', 'success');
            } else if (frameCount % 100 === 0) {
                console.log(`✓ ${frameCount} frames displayed`);
            }
        } catch (err) {
            console.error('Frame fetch error:', err);
            errorCount++;
            
            if (errorCount >= 10) {
                clearInterval(frameTimer);
                frameTimer = null;
                showNotification('Camera disconnected', 'error');
            }
        }
    }, fetchInterval);
}
async function captureAndRecognize() {
    if (!elements.video.videoWidth || !elements.video.videoHeight) return;
    
    const ctx = elements.capture.getContext('2d');
    ctx.drawImage(elements.video, 0, 0, elements.capture.width, elements.capture.height);
    
    elements.capture.toBlob(async (blob) => {
        if (!blob) return;
        
        try {
            const formData = new FormData();
            formData.append('file', blob, 'frame.jpg');
            
            const response = await fetch(`${API_BASE}/process-frame/`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            handleRecognitionResult(data);
        } catch (err) {
            console.error('Recognition error:', err);
            elements.status.textContent = `Error: ${err.message}`;
            elements.status.className = 'status status-error';
        }
    }, 'image/jpeg', 0.8);
}

function handleRecognitionResult(data) {
    clearOverlay();
    
    if (!data.faces || data.faces.length === 0) return;
    
    const ctx = elements.overlay.getContext('2d');
    const scaleX = currentCameraSource === 'browser' && elements.video.videoWidth ?
        elements.overlay.width / elements.video.videoWidth : 1;
    const scaleY = currentCameraSource === 'browser' && elements.video.videoHeight ?
        elements.overlay.height / elements.video.videoHeight : 1;
    
    data.faces.forEach(face => {
        const [x, y, w, h] = face.bbox;
        const sx = x * scaleX;
        const sy = y * scaleY;
        const sw = w * scaleX;
        const sh = h * scaleY;
        
        // Draw bounding box
        ctx.strokeStyle = face.known ? '#00ff00' : '#ff0000';
        ctx.lineWidth = 3;
        ctx.strokeRect(sx, sy, sw, sh);
        
        // Draw label
        const label = face.known ? `${face.name} (${(face.score * 100).toFixed(0)}%)` : 'Unknown';
        ctx.font = 'bold 18px Arial';
        const textWidth = ctx.measureText(label).width;
        
        ctx.fillStyle = face.known ? '#00ff00' : '#ff0000';
        ctx.fillRect(sx, sy - 30, textWidth + 20, 30);
        
        ctx.fillStyle = '#000';
        ctx.fillText(label, sx + 10, sy - 8);
        
        stats.detected++;
        if (face.known) stats.recognized++;
        else stats.unknown++;
    });
    
    updateStats();
    
    if (data.faces.some(f => f.known)) loadAttendance();
    if (data.faces.some(f => !f.known)) loadUnknownFaces();
}

function clearOverlay() {
    const ctx = elements.overlay.getContext('2d');
    ctx.clearRect(0, 0, elements.overlay.width, elements.overlay.height);
}

function updateStats() {
    document.getElementById('facesDetected').textContent = stats.detected;
    document.getElementById('facesRecognized').textContent = stats.recognized;
    document.getElementById('facesUnknown').textContent = stats.unknown;
    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 10);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Person Management
async function handleImageUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const name = elements.personName.value.trim();
    const id = elements.personId.value.trim();
    
    if (!name || !id) {
        showNotification('Please enter name and ID', 'warning');
        return;
    }
    
    try {
        elements.uploadImageBtn.disabled = true;
        elements.uploadImageBtn.textContent = 'Uploading...';
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);
        formData.append('identifier', id);
        
        const response = await fetch(`${API_BASE}/add-person/`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }
        
        const data = await response.json();
        showNotification(data.message, 'success');
        
        elements.personName.value = '';
        elements.personId.value = '';
        elements.imageUpload.value = '';
        loadPeople();
    } catch (err) {
        showNotification(`Failed to add person: ${err.message}`, 'error');
    } finally {
        elements.uploadImageBtn.disabled = false;
        elements.uploadImageBtn.textContent = '📁 Upload Photo';
    }
}

function capturePhotoForPerson() {
    if (!elements.video.videoWidth || !elements.video.videoHeight) {
        showNotification('Please start camera first', 'warning');
        return;
    }
    
    const name = elements.personName.value.trim();
    const id = elements.personId.value.trim();
    
    if (!name || !id) {
        showNotification('Please enter name and ID first', 'warning');
        return;
    }
    
    showCaptureModal();
}

function showCaptureModal() {
    if (!elements.video.videoWidth || !elements.video.videoHeight) {
        showNotification('Please start camera first', 'warning');
        return;
    }
    
    const ctx = elements.capture.getContext('2d');
    ctx.drawImage(elements.video, 0, 0, elements.capture.width, elements.capture.height);
    
    elements.capture.toBlob((blob) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            capturedImageData = e.target.result;
            const capturedCanvas = document.getElementById('capturedImage');
            const img = new Image();
            img.onload = () => {
                capturedCanvas.width = img.width;
                capturedCanvas.height = img.height;
                capturedCanvas.getContext('2d').drawImage(img, 0, 0);
            };
            img.src = capturedImageData;
            elements.captureModal.style.display = 'flex';
        };
        reader.readAsDataURL(blob);
    }, 'image/jpeg');
}

async function confirmPersonCapture() {
    const name = elements.personName.value.trim();
    const id = elements.personId.value.trim();
    
    if (!name || !id || !capturedImageData) {
        showNotification('Missing information', 'warning');
        return;
    }
    
    try {
        const confirmBtn = document.getElementById('confirmCapture');
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Adding...';
        
        const formData = new FormData();
        formData.append('name', name);
        formData.append('identifier', id);
        formData.append('image_base64', capturedImageData);
        
        const response = await fetch(`${API_BASE}/capture-person/`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }
        
        const data = await response.json();
        showNotification(data.message, 'success');
        
        elements.personName.value = '';
        elements.personId.value = '';
        capturedImageData = null;
        elements.captureModal.style.display = 'none';
        loadPeople();
    } catch (err) {
        showNotification(`Failed to capture person: ${err.message}`, 'error');
    } finally {
        const confirmBtn = document.getElementById('confirmCapture');
        confirmBtn.disabled = false;
        confirmBtn.textContent = '✓ Use This Photo';
    }
}

async function handleCompareUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    try {
        elements.uploadCompareBtn.disabled = true;
        elements.uploadCompareBtn.textContent = 'Comparing...';
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE}/compare-image/`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        displayCompareResult(data);
        elements.compareUpload.value = '';
    } catch (err) {
        showNotification(`Comparison failed: ${err.message}`, 'error');
    } finally {
        elements.uploadCompareBtn.disabled = false;
        elements.uploadCompareBtn.textContent = '📁 Upload & Compare';
    }
}

function displayCompareResult(data) {
    elements.compareResult.innerHTML = !data.faces || data.faces.length === 0 ?
        '<p class="empty-state">No faces detected in image</p>' :
        `<div class="compare-results">${data.faces.map((face, i) => `
            <div class="compare-item ${face.known ? 'match' : 'no-match'}">
                <strong>Face ${i + 1}:</strong> ${face.known ? 
                    `${face.name} (${face.identifier})` : 'Unknown'}<br>
                <span class="score">Confidence: ${(face.score * 100).toFixed(1)}%</span>
            </div>
        `).join('')}</div>`;
}

async function loadUnknownFaces() {
    try {
        const response = await fetch(`${API_BASE}/unknown-faces/`);
        const data = await response.json();
        
        document.getElementById('unknownCount').textContent = data.unknowns.length;
        document.getElementById('unknownList').innerHTML = data.unknowns.length === 0 ?
            '<p class="empty-state">No unknown faces detected.</p>' :
            data.unknowns.map(unknown => `
                <div class="unknown-card">
                    <img src="${unknown.image}" alt="Unknown face">
                    <div class="unknown-info">
                        <div class="unknown-time">${new Date(unknown.detected_at).toLocaleString()}</div>
                        <div class="unknown-actions">
                            <button onclick="window.showMigrateModal(${unknown.id}, '${unknown.image}')" 
                                    class="btn btn-primary btn-xs">Identify</button>
                            <button onclick="window.deleteUnknown(${unknown.id})" 
                                    class="btn btn-danger btn-xs">Delete</button>
                        </div>
                    </div>
                </div>
            `).join('');
    } catch (err) {
        console.error('Load unknown error:', err);
    }
}

window.showMigrateModal = async function(unknownId, imageUrl) {
    currentUnknownId = unknownId;
    document.getElementById('migrateImage').src = imageUrl;
    document.getElementById('migrateName').value = '';
    document.getElementById('migrateId').value = '';
    document.querySelector('input[name="migrateOption"][value="new"]').checked = true;
    document.getElementById('newPersonFields').style.display = 'block';
    document.getElementById('migratePersonSelect').disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/people/`);
        const data = await response.json();
        
        const select = document.getElementById('migratePersonSelect');
        select.innerHTML = '<option value="">Select person...</option>' +
            data.people.map(person => 
                `<option value="${person.id}">${person.name} (${person.identifier})</option>`
            ).join('');
    } catch (err) {
        console.error('Load people error:', err);
    }
    
    elements.migrateModal.style.display = 'flex';
};

async function confirmMigrate() {
    const option = document.querySelector('input[name="migrateOption"]:checked').value;
    let requestData;
    
    if (option === 'new') {
        const name = document.getElementById('migrateName').value.trim();
        const id = document.getElementById('migrateId').value.trim();
        if (!name || !id) {
            showNotification('Please enter name and ID', 'warning');
            return;
        }
        requestData = { unknown_id: currentUnknownId, name, identifier: id };
    } else {
        const personId = document.getElementById('migratePersonSelect').value;
        if (!personId) {
            showNotification('Please select a person', 'warning');
            return;
        }
        requestData = { unknown_id: currentUnknownId, person_id: parseInt(personId) };
    }
    
    try {
        const confirmBtn = document.getElementById('confirmMigrate');
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Migrating...';
        
        const response = await fetch(`${API_BASE}/migrate-unknown/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }
        
        const data = await response.json();
        showNotification(data.message, 'success');
        elements.migrateModal.style.display = 'none';
        loadUnknownFaces();
        loadPeople();
    } catch (err) {
        showNotification(`Migration failed: ${err.message}`, 'error');
    } finally {
        const confirmBtn = document.getElementById('confirmMigrate');
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Migrate';
    }
}

window.deleteUnknown = async function(unknownId) {
    if (!confirm('Delete this unknown face?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/unknown-faces/${unknownId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        showNotification('Unknown face deleted', 'success');
        loadUnknownFaces();
    } catch (err) {
        showNotification(`Failed to delete: ${err.message}`, 'error');
    }
};

async function seedDemoPeople() {
    if (!confirm('Seed demo people? This will create sample records.')) return;
    
    try {
        elements.seedBtn.disabled = true;
        elements.seedBtn.textContent = 'Seeding...';
        
        const response = await fetch(`${API_BASE}/seed-demo/`, { method: 'POST' });
        const data = await response.json();
        showNotification(data.message + (data.note ? '\n\n' + data.note : ''), 'success');
        loadPeople();
    } catch (err) {
        showNotification(`Failed to seed demo people: ${err.message}`, 'error');
    } finally {
        elements.seedBtn.disabled = false;
        elements.seedBtn.textContent = 'Seed Demo People';
    }
}

async function clearAllData() {
    if (!confirm('Clear ALL data? This cannot be undone!')) return;
    
    try {
        elements.clearBtn.disabled = true;
        elements.clearBtn.textContent = 'Clearing...';
        
        const response = await fetch(`${API_BASE}/clear-data/`, { method: 'DELETE' });
        const data = await response.json();
        showNotification(data.message, 'success');
        
        loadPeople();
        loadAttendance();
        loadUnknownFaces();
        stats = { detected: 0, recognized: 0, unknown: 0 };
        updateStats();
    } catch (err) {
        showNotification(`Failed to clear data: ${err.message}`, 'error');
    } finally {
        elements.clearBtn.disabled = false;
        elements.clearBtn.textContent = 'Clear All Data';
    }
}

async function loadPeople() {
    try {
        const response = await fetch(`${API_BASE}/people/`);
        const data = await response.json();
        
        document.getElementById('peopleCount').textContent = data.people.length;
        document.getElementById('peopleList').innerHTML = data.people.length === 0 ?
            '<p class="empty-state">No people registered.</p>' :
            data.people.map(person => `
                <div class="person-card">
                    <img src="${person.image}" alt="${person.name}">
                    <div class="person-info">
                        <div class="person-name">${person.name}</div>
                        <div class="person-id">${person.identifier}</div>
                    </div>
                </div>
            `).join('');
    } catch (err) {
        console.error('Load people error:', err);
    }
}

async function loadAttendance() {
    try {
        const response = await fetch(`${API_BASE}/attendance/?limit=20`);
        const data = await response.json();
        
        document.getElementById('attendanceList').innerHTML = data.attendance.length === 0 ?
            '<p class="empty-state">No attendance records.</p>' :
            data.attendance.map(record => `
                <div class="attendance-card">
                    <div class="attendance-name">${record.name}</div>
                    <div class="attendance-id">${record.identifier}</div>
                    <div class="attendance-time">${new Date(record.arrival_time).toLocaleString()}</div>
                    ${record.auto ? '<span class="badge">Auto</span>' : ''}
                </div>
            `).join('');
    } catch (err) {
        console.error('Load attendance error:', err);
    }
}