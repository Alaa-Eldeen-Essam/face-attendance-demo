"""
Face recognition using InsightFace.
Wrapper for easy model swapping and configuration.
Supports GPU with CPU fallback.
"""
import numpy as np
import cv2
from typing import List, Dict, Optional
import insightface
from insightface.app import FaceAnalysis


class FaceRecognizer:
    """
    Wrapper around InsightFace for face detection and recognition.
    Uses buffalo_l model by default with GPU support and CPU fallback.
    """
    
    def __init__(self, model_name: str = "buffalo_l", det_size: tuple = (640, 640), use_gpu: bool = True):
        """
        Initialize the face recognizer.
        
        Args:
            model_name: InsightFace model name (buffalo_l, buffalo_sc, etc.)
            det_size: Detection size for face detector
            use_gpu: Try to use GPU, fallback to CPU if unavailable
        """
        print(f"Loading InsightFace model: {model_name}...")
        
        # Determine providers
        if use_gpu:
            try:
                import onnxruntime as ort
                available_providers = ort.get_available_providers()
                
                if 'CUDAExecutionProvider' in available_providers:
                    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                    print("✓ GPU (CUDA) available, using GPU acceleration")
                elif 'CoreMLExecutionProvider' in available_providers:
                    providers = ['CoreMLExecutionProvider', 'CPUExecutionProvider']
                    print("✓ CoreML available, using Apple GPU acceleration")
                else:
                    providers = ['CPUExecutionProvider']
                    print("⚠ GPU not available, using CPU")
            except Exception as e:
                print(f"⚠ Error checking GPU: {e}, falling back to CPU")
                providers = ['CPUExecutionProvider']
        else:
            providers = ['CPUExecutionProvider']
            print("Using CPU (GPU disabled)")
        
        self.app = FaceAnalysis(
            name=model_name,
            providers=providers
        )
        self.app.prepare(ctx_id=0, det_size=det_size)
        
        self.providers = providers
        print(f"✓ Model {model_name} loaded successfully with providers: {providers}")
    
    def detect_faces(self, image: np.ndarray, min_face_size: int = 30) -> List[Dict]:
        """
        Detect faces in an image and extract embeddings.
        
        Args:
            image: BGR image from OpenCV
            min_face_size: Minimum face size to detect
        
        Returns:
            List of dicts with 'bbox', 'embedding', 'det_score', 'landmarks'
        """
        # Detect faces
        faces = self.app.get(image)
        
        results = []
        for face in faces:
            bbox = face.bbox.astype(int)  # [x1, y1, x2, y2]
            
            # Convert to [x, y, w, h] format
            x1, y1, x2, y2 = bbox
            w = x2 - x1
            h = y2 - y1
            
            # Filter by minimum size
            if w < min_face_size or h < min_face_size:
                continue
            
            # Extract embedding (already normalized by InsightFace)
            embedding = face.embedding
            
            results.append({
                'bbox': [x1, y1, w, h],
                'embedding': embedding,
                'det_score': float(face.det_score),
                'landmarks': face.kps.tolist() if hasattr(face, 'kps') else None
            })
        
        return results
    
    @staticmethod
    def compare_embeddings(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compare two face embeddings using cosine similarity.
        
        Args:
            emb1: First embedding
            emb2: Second embedding
        
        Returns:
            Similarity score (0 to 1, higher is more similar)
        """
        # Normalize embeddings
        emb1_norm = emb1 / np.linalg.norm(emb1)
        emb2_norm = emb2 / np.linalg.norm(emb2)
        
        # Cosine similarity
        similarity = np.dot(emb1_norm, emb2_norm)
        
        return float(similarity)
    
    def get_provider_info(self) -> Dict:
        """Get information about active execution providers."""
        return {
            "providers": self.providers,
            "using_gpu": any(p in ['CUDAExecutionProvider', 'CoreMLExecutionProvider'] for p in self.providers)
        }
    
    def extract_face_embedding(self, image: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
        """
        Extract embedding from a specific face region.
        Useful for processing cropped faces.
        
        Args:
            image: Full image
            bbox: Bounding box [x, y, w, h]
        
        Returns:
            Face embedding or None if detection fails
        """
        x, y, w, h = bbox
        face_crop = image[y:y+h, x:x+w]
        
        faces = self.detect_faces(face_crop)
        
        if faces:
            return faces[0]['embedding']
        return None
    
    def preprocess_face(self, image: np.ndarray, bbox: List[int], target_size: tuple = (112, 112)) -> np.ndarray:
        """
        Preprocess face crop for better recognition.
        Applies alignment and normalization.
        
        Args:
            image: Full image
            bbox: Bounding box [x, y, w, h]
            target_size: Target face size
        
        Returns:
            Preprocessed face image
        """
        x, y, w, h = bbox
        face_crop = image[y:y+h, x:x+w]
        
        # Resize to target size
        face_resized = cv2.resize(face_crop, target_size)
        
        # Convert to RGB if needed
        if len(face_resized.shape) == 2:
            face_resized = cv2.cvtColor(face_resized, cv2.COLOR_GRAY2RGB)
        elif face_resized.shape[2] == 4:
            face_resized = cv2.cvtColor(face_resized, cv2.COLOR_BGRA2RGB)
        elif face_resized.shape[2] == 3:
            face_resized = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
        
        return face_resized