"""
Face Embeddings Module
Generates face embeddings for recognition using face_recognition library
"""
import face_recognition
import numpy as np
import cv2

class FaceEmbeddings:
    """Generate and compare face embeddings"""
    
    def __init__(self, model='large'):
        """
        Initialize face embeddings
        
        Args:
            model: 'small' (faster) or 'large' (more accurate)
        """
        self.model = model
        print(f"✓ Face embeddings initialized (model: {model})")
    
    def get_embedding(self, face_image):
        """
        Generate face embedding from image
        
        Args:
            face_image: Face image (BGR or RGB)
            
        Returns:
            numpy array of 128 dimensions or None
        """
        try:
            # Convert BGR to RGB if needed
            if len(face_image.shape) == 3 and face_image.shape[2] == 3:
                rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = face_image
            
            # Get face encodings
            encodings = face_recognition.face_encodings(
                rgb_image, 
                model=self.model
            )
            
            # If cropped face ROI doesn't trigger HOG face detection, fall back to explicit ROI bounds
            if len(encodings) == 0 and rgb_image.shape[0] >= 10 and rgb_image.shape[1] >= 10:
                h, w = rgb_image.shape[:2]
                encodings = face_recognition.face_encodings(
                    rgb_image,
                    known_face_locations=[(0, w, h, 0)],
                    model=self.model
                )
            
            if len(encodings) > 0:
                return encodings[0]  # Return first face encoding
            else:
                print("⚠ No face found in image for embedding")
                return None
                
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def compare_embeddings(self, embedding1, embedding2, threshold=0.6):
        """
        Compare two face embeddings
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            threshold: Similarity threshold (default 0.6)
            
        Returns:
            tuple: (is_match, distance)
        """
        try:
            # Convert to numpy arrays if needed
            if not isinstance(embedding1, np.ndarray):
                embedding1 = np.array(embedding1)
            if not isinstance(embedding2, np.ndarray):
                embedding2 = np.array(embedding2)
            
            # Calculate face distance (lower = more similar)
            distance = face_recognition.face_distance([embedding1], embedding2)[0]
            
            # Check if match (distance < threshold means match)
            is_match = distance < threshold
            
            # Convert distance to similarity score (0-1, higher = more similar)
            similarity = 1 - distance
            
            return is_match, similarity
            
        except Exception as e:
            print(f"Error comparing embeddings: {e}")
            return False, 0.0
    
    def find_best_match(self, target_embedding, known_embeddings, threshold=0.6):
        """
        Find best matching face from known embeddings
        
        Args:
            target_embedding: Target face embedding
            known_embeddings: List of dicts with 'user_id', 'name', 'embedding'
            threshold: Similarity threshold
            
        Returns:
            dict: Best match info or None
        """
        if not known_embeddings:
            return None
        
        best_match = None
        best_similarity = 0.0
        
        for known in known_embeddings:
            is_match, similarity = self.compare_embeddings(
                target_embedding, 
                known['embedding'], 
                threshold
            )
            
            if is_match and similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    'user_id': known['user_id'],
                    'name': known['name'],
                    'similarity': similarity,
                    'confidence': similarity * 100
                }
        
        return best_match
    
    def get_embedding_from_file(self, image_path):
        """
        Generate embedding from image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            Face embedding or None
        """
        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image, model=self.model)
            
            if len(encodings) > 0:
                return encodings[0]
            else:
                print(f"⚠ No face found in {image_path}")
                return None
                
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
