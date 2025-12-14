"""
Face Detection Module using OpenCV Haar Cascade
"""
import cv2
import os

class FaceDetector:
    """Face detector using OpenCV Haar Cascade"""
    
    def __init__(self):
        """Initialize face detector"""
        # Use Haar Cascade (more reliable and doesn't need prototxt)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load Haar Cascade face detector")
        
        print("✓ Face detector loaded (Haar Cascade)")
    
    def detect_faces(self, frame):
        """
        Detect faces in frame
        
        Args:
            frame: Input image frame
            
        Returns:
            List of face bounding boxes [(x, y, w, h), ...]
        """
        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Convert numpy array to list of tuples
        return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
