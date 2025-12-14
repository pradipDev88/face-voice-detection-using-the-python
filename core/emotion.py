"""
Emotion Recognition Module using Keras model
"""
import cv2
import numpy as np
from tensorflow import keras

class EmotionPredictor:
    """Predict emotion using pre-trained Keras model"""
    
    def __init__(self):
        """Initialize emotion recognition model"""
        # Load emotion model
        self.model = keras.models.load_model('models/emotion_model.h5')
        
        # Emotion labels
        self.emotion_labels = [
            'angry',
            'bored',
            'happy',
            'neutral',
            'sad',
            'surprise'
        ]
        
        print("✓ Emotion model loaded")
    
    def predict(self, face_img):
        """
        Predict emotion from face image
        
        Args:
            face_img: Face region image
            
        Returns:
            Emotion label string
        """
        try:
            # Preprocess face image
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (48, 48))
            normalized = resized / 255.0
            reshaped = normalized.reshape(1, 48, 48, 1)
            
            # Predict emotion
            predictions = self.model.predict(reshaped, verbose=0)
            emotion_idx = np.argmax(predictions[0])
            emotion = self.emotion_labels[emotion_idx]
            
            return emotion
        except Exception as e:
            return "neutral"
