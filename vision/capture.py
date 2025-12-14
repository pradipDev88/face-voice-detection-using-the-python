"""
Auto Capture Module
Automatically captures face images when detected
"""
import cv2
import os
from datetime import datetime
import time

class FaceCapture:
    """Handles automatic face capture"""
    
    def __init__(self, save_dir='captures/', auto_delay=2):
        """
        Initialize face capture
        
        Args:
            save_dir: Directory to save captured images
            auto_delay: Delay in seconds before auto-capture
        """
        self.save_dir = save_dir
        self.auto_delay = auto_delay
        self.last_capture_time = 0
        self.capture_cooldown = 3  # Minimum seconds between captures
        
        # Create save directory if not exists
        os.makedirs(save_dir, exist_ok=True)
        
        print(f"✓ Face capture initialized (save_dir: {save_dir})")
    
    def can_capture(self):
        """Check if enough time has passed since last capture"""
        current_time = time.time()
        return (current_time - self.last_capture_time) >= self.capture_cooldown
    
    def capture_face(self, frame, face_bbox, user_name=None):
        """
        Capture face from frame
        
        Args:
            frame: Video frame
            face_bbox: Face bounding box (x, y, w, h)
            user_name: Optional user name for filename
            
        Returns:
            tuple: (success, file_path, face_image)
        """
        try:
            if not self.can_capture():
                return False, None, None
            
            x, y, w, h = face_bbox
            
            # Extract face region with some padding
            padding = 20
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(frame.shape[1], x + w + padding)
            y2 = min(frame.shape[0], y + h + padding)
            
            face_image = frame[y1:y2, x1:x2]
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if user_name:
                filename = f"{user_name}_{timestamp}.jpg"
            else:
                filename = f"face_{timestamp}.jpg"
            
            file_path = os.path.join(self.save_dir, filename)
            
            # Save image
            cv2.imwrite(file_path, face_image)
            
            # Update last capture time
            self.last_capture_time = time.time()
            
            print(f"✓ Face captured: {file_path}")
            return True, file_path, face_image
            
        except Exception as e:
            print(f"Error capturing face: {e}")
            return False, None, None
    
    def capture_full_frame(self, frame, user_name=None):
        """
        Capture full frame
        
        Args:
            frame: Video frame
            user_name: Optional user name for filename
            
        Returns:
            tuple: (success, file_path)
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if user_name:
                filename = f"{user_name}_full_{timestamp}.jpg"
            else:
                filename = f"frame_{timestamp}.jpg"
            
            file_path = os.path.join(self.save_dir, filename)
            
            # Save image
            cv2.imwrite(file_path, frame)
            
            print(f"✓ Frame captured: {file_path}")
            return True, file_path
            
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return False, None
    
    def auto_capture_on_detection(self, frame, faces, delay_met=True):
        """
        Automatically capture when face is detected and delay is met
        
        Args:
            frame: Video frame
            faces: List of detected faces [(x, y, w, h), ...]
            delay_met: Whether auto-delay has been met
            
        Returns:
            list: List of captured face info
        """
        if not delay_met or not self.can_capture():
            return []
        
        captured = []
        
        for face_bbox in faces:
            success, file_path, face_image = self.capture_face(frame, face_bbox)
            if success:
                captured.append({
                    'file_path': file_path,
                    'face_image': face_image,
                    'bbox': face_bbox
                })
        
        return captured
