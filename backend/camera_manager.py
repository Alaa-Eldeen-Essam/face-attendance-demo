import cv2
import numpy as np
from typing import Optional, Dict, List
from enum import Enum
import threading
import time
from datetime import datetime


class CameraType(str, Enum):
    WEBCAM = "webcam"
    RTSP = "rtsp"
    HTTP = "http"
    FILE = "file"


class CameraManager:
    """
    Manages camera connections from various sources.
    Supports webcams, RTSP streams, HTTP/IP cameras, and video files.
    """
    
    def __init__(self):
        self.cameras: Dict[str, Dict] = {}
        self.active_cameras: Dict[str, cv2.VideoCapture] = {}
        self.lock = threading.Lock()
    
    def add_camera(self, camera_id: str, source: str, camera_type: CameraType) -> bool:
        """
        Add a new camera source with aggressive optimization.
        """
        with self.lock:
            if camera_id in self.cameras:
                self.remove_camera(camera_id)
            
            try:
                if camera_type == CameraType.WEBCAM:
                    cap_source = int(source)
                    cap = cv2.VideoCapture(cap_source)
                    
                elif camera_type == CameraType.RTSP:
                    # Aggressive RTSP optimization
                    cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                    
                    # Critical settings for low latency
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # Additional RTSP optimizations (if supported)
                    try:
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
                    except:
                        pass
                    
                elif camera_type == CameraType.HTTP:
                    cap = cv2.VideoCapture(source)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                elif camera_type == CameraType.FILE:
                    cap = cv2.VideoCapture(source)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                else:
                    raise ValueError(f"Unsupported camera type: {camera_type}")
                
                if not cap.isOpened():
                    print(f"Failed to open camera source: {source}")
                    return False
                
                # Read test frame
                ret, frame = cap.read()
                if not ret or frame is None:
                    print(f"Failed to read test frame from {source}")
                    cap.release()
                    return False
                
                # Get properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                self.cameras[camera_id] = {
                    "id": camera_id,
                    "type": camera_type,
                    "source": source,
                    "capture": cap,
                    "active": True,
                    "connected_at": datetime.now(),
                    "last_frame_time": datetime.now(),
                    "frame_count": 1,
                    "width": width,
                    "height": height,
                    "fps": fps if fps > 0 else 30,
                    "connected": True
                }
                
                self.active_cameras[camera_id] = cap
                print(f"✓ Camera {camera_id} added: {width}x{height} @ {fps if fps > 0 else 30} FPS")
                return True
                
            except Exception as e:
                print(f"Failed to add camera {camera_id}: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    def remove_camera(self, camera_id: str) -> bool:
        """Remove and release a camera."""
        with self.lock:
            if camera_id in self.cameras:
                try:
                    self.cameras[camera_id]["capture"].release()
                    del self.cameras[camera_id]
                    if camera_id in self.active_cameras:
                        del self.active_cameras[camera_id]
                    print(f"✓ Camera removed: {camera_id}")
                    return True
                except Exception as e:
                    print(f"Error removing camera {camera_id}: {e}")
                    return False
            return False
    
    def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """
        Get current frame from camera - ultra optimized.
        
        Args:
            camera_id: Camera identifier
        
        Returns:
            Frame as numpy array (BGR) or None if failed
        """
        camera = self.cameras.get(camera_id)
        if not camera:
            return None
        
        if not camera["active"]:
            return None
        
        cap = camera["capture"]
        
        try:
            # For RTSP/HTTP: AGGRESSIVELY skip old frames
            if camera["type"] in [CameraType.RTSP, CameraType.HTTP]:
                # Skip up to 5 buffered frames to get the absolute latest
                for _ in range(5):
                    if not cap.grab():
                        break
            
            # Retrieve the latest frame
            ret, frame = cap.retrieve()
            
            if not ret or frame is None:
                # Try one more time with read()
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    print(f"Failed to read frame from camera {camera_id}")
                    camera["active"] = False
                    camera["connected"] = False
                    return None
            
            camera["last_frame_time"] = datetime.now()
            camera["frame_count"] += 1
            camera["connected"] = True
            
            return frame
            
        except Exception as e:
            print(f"Error reading frame from {camera_id}: {e}")
            camera["active"] = False
            camera["connected"] = False
            return None

    
    def get_camera_info(self, camera_id: str) -> Optional[Dict]:
        """Get info for specific camera (JSON serializable)."""
        with self.lock:
            if camera_id not in self.cameras:
                return None
            
            info = self.cameras[camera_id]
            return {
                "id": camera_id,
                "type": info["type"].value if hasattr(info["type"], "value") else str(info["type"]),
                "source": info["source"],
                "active": info["active"],
                "connected": info.get("connected", False),
                "connected_at": info["connected_at"].isoformat() if info.get("connected_at") else None,
                "last_frame_time": info["last_frame_time"].isoformat() if info.get("last_frame_time") else None,
                "frame_count": info["frame_count"],
                "width": info["width"],
                "height": info["height"],
                "fps": info["fps"]
            }
    
    def list_cameras(self) -> List[Dict]:
        """List all active cameras with their info (JSON serializable)."""
        with self.lock:
            cameras_info = []
            for cam_id in self.cameras:
                info = self.get_camera_info(cam_id)
                if info:
                    cameras_info.append(info)
            return cameras_info
    
    def is_connected(self, camera_id: str) -> bool:
        """Check if camera is connected and working."""
        with self.lock:
            if camera_id not in self.cameras:
                return False
            return self.cameras[camera_id].get("connected", False)
    
    def reconnect_camera(self, camera_id: str) -> bool:
        """Attempt to reconnect a camera."""
        with self.lock:
            if camera_id not in self.cameras:
                return False
            
            info = self.cameras[camera_id]
            source = info["source"]
            cam_type = info["type"]
        
        # Remove old connection (release lock first)
        self.remove_camera(camera_id)
        
        # Try to reconnect
        return self.add_camera(camera_id, source, cam_type)
    
    def close_all(self):
        """Close all cameras."""
        with self.lock:
            for camera_id in list(self.cameras.keys()):
                try:
                    self.cameras[camera_id]["capture"].release()
                except:
                    pass
            
            self.cameras.clear()
            self.active_cameras.clear()
            print("✓ All cameras closed")
    
    @staticmethod
    def discover_webcams() -> List[int]:
        """
        Discover available webcam indices.
        Returns list of available camera indices.
        """
        available = []
        for i in range(10):  # Check first 10 indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available
    
    @staticmethod
    def test_rtsp_connection(url: str, timeout: int = 5) -> bool:
        """
        Test if RTSP stream is accessible.
        
        Args:
            url: RTSP URL
            timeout: Connection timeout in seconds
        
        Returns:
            True if accessible, False otherwise
        """
        try:
            cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                ret, frame = cap.read()
                if ret:
                    cap.release()
                    return True
                time.sleep(0.1)
            
            cap.release()
            return False
            
        except Exception as e:
            print(f"RTSP test failed: {e}")
            return False


# Global camera manager instance
camera_manager = CameraManager()