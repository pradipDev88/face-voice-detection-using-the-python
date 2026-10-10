"""
Age and Gender Prediction Module using Caffe models
"""
import cv2
import numpy as np
import os

class AgeGenderPredictor:
    """Predict age and gender using pre-trained Caffe models"""
    
    def __init__(self):
        """Initialize age and gender models"""
        # Check if model files exist
        age_model_path = 'models/age_net.caffemodel'
        gender_model_path = 'models/gender_net.caffemodel'
        
        if not os.path.exists(age_model_path):
            raise FileNotFoundError(
                f"\n\n❌ Missing: {age_model_path}\n\n"
                "Please download the age model:\n"
                "1. Go to: https://www.dropbox.com/s/xfb20y596869vbb/age_net.caffemodel?dl=1\n"
                "2. Save as: models/age_net.caffemodel\n\n"
                "Or see DOWNLOAD_MODELS_NOW.md for detailed instructions."
            )
        
        if not os.path.exists(gender_model_path):
            raise FileNotFoundError(
                f"\n\n❌ Missing: {gender_model_path}\n\n"
                "Please download the gender model:\n"
                "1. Go to: https://www.dropbox.com/s/iyv483wz7ztr9gh/gender_net.caffemodel?dl=1\n"
                "2. Save as: models/gender_net.caffemodel\n\n"
                "Or see DOWNLOAD_MODELS_NOW.md for detailed instructions."
            )
        
        # Age model
        self.age_net = cv2.dnn.readNetFromCaffe(
            'models/age_deploy.prototxt',
            age_model_path
        )
        
        # Gender model
        self.gender_net = cv2.dnn.readNetFromCaffe(
            'models/gender_deploy.prototxt',
            gender_model_path
        )
        
        # Age ranges (model outputs - cannot be changed)
        self.age_list = [
            '(0-2)', '(4-6)', '(8-12)', '(15-20)',
            '(25-32)', '(38-43)', '(48-53)', '(60-100)'
        ]
        
        # Age display mapping - shows single age number
        self.age_display_map = {
            '(0-2)': '1',       # Baby/Toddler
            '(4-6)': '5',       # Young Child
            '(8-12)': '10',     # Child
            '(15-20)': '18',    # Teen
            '(20-24)': '22',    # Young Adult
            '(25-32)': '28',    # Young Adult
            '(38-43)': '40',    # Adult
            '(48-53)': '50',    # Middle Age
            '(60-100)': '65'    # Senior
        }
        
        # Detailed info for each age category (for info button)
        # Now featuring Bollywood actors!
        self.age_info = {
            '(0-2)': {
                'category': 'Baby/Toddler',
                'animal': 'Puppy 🐶',
                'traits': 'Innocent, Playful, Curious',
                'film_stars': 'Child actors from Bollywood',
                'description': 'Full of wonder and discovery'
            },
            '(4-6)': {
                'category': 'Young Child',
                'animal': 'Kitten 🐱',
                'traits': 'Energetic, Imaginative, Joyful',
                'film_stars': 'Young Bollywood talents',
                'description': 'Learning and exploring the world'
            },
            '(8-12)': {
                'category': 'Child',
                'animal': 'Rabbit 🐰',
                'traits': 'Active, Curious, Growing',
                'film_stars': 'Darsheel Safary, Harshaali Malhotra',
                'description': 'Building skills and friendships'
            },
            '(15-20)': {
                'category': 'Teen',
                'animal': 'Deer 🦌',
                'traits': 'Energetic, Ambitious, Social',
                'film_stars': 'Suhana Khan, Agastya Nanda, Khushi Kapoor, Vedang Raina',
                'description': 'Finding identity and purpose'
            },
            '(20-24)': {
                'category': 'Young Adult',
                'animal': 'Cheetah 🐆',
                'traits': 'Fast, Dynamic, Adventurous',
                'film_stars': 'Janhvi Kapoor, Sara Ali Khan, Ananya Panday, Ishaan Khatter',
                'description': 'Full of energy and possibilities'
            },
            '(25-32)': {
                'category': 'Young Adult',
                'animal': 'Lion 🦁',
                'traits': 'Strong, Confident, Driven',
                'film_stars': 'Ranveer Singh, Deepika Padukone, Vicky Kaushal, Alia Bhatt',
                'description': 'Peak energy and ambition'
            },
            '(38-43)': {
                'category': 'Adult',
                'animal': 'Eagle 🦅',
                'traits': 'Wise, Experienced, Focused',
                'film_stars': 'Hrithik Roshan, Priyanka Chopra, Shahid Kapoor, Kareena Kapoor',
                'description': 'Mature and accomplished'
            },
            '(48-53)': {
                'category': 'Middle Age',
                'animal': 'Elephant 🐘',
                'traits': 'Wise, Patient, Respected',
                'film_stars': 'Shah Rukh Khan, Salman Khan, Aamir Khan, Kajol, Madhuri Dixit',
                'description': 'Experienced and influential'
            },
            '(60-100)': {
                'category': 'Senior',
                'animal': 'Owl 🦉',
                'traits': 'Wise, Knowledgeable, Calm',
                'film_stars': 'Amitabh Bachchan, Jaya Bachchan, Anupam Kher, Naseeruddin Shah',
                'description': 'Full of wisdom and life experience'
            }
        }
        
        # Gender labels
        self.gender_list = ['Male', 'Female']
        
        # Model mean values
        self.MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
        
        # Third-party Age Service
        try:
            from vision.age_api import ThirdPartyAgeService
            self.api_service = ThirdPartyAgeService()
        except Exception:
            self.api_service = None

        print("✓ Age and Gender models loaded")
    
    def predict(self, face_img):
        """
        Predict age and gender from face image using local Caffe models
        
        Args:
            face_img: Face region image
            
        Returns:
            Tuple of (age_display, gender, age_range_key)
        """
        # Prepare blob
        blob = cv2.dnn.blobFromImage(
            face_img,
            1.0,
            (227, 227),
            self.MODEL_MEAN_VALUES,
            swapRB=False
        )
        
        # Predict gender
        self.gender_net.setInput(blob)
        gender_preds = self.gender_net.forward()
        gender_idx = gender_preds[0].argmax()
        gender = self.gender_list[gender_idx]
        
        # Predict age
        self.age_net.setInput(blob)
        age_preds = self.age_net.forward()
        age_idx = age_preds[0].argmax()
        age_range = self.age_list[age_idx]
        
        # Convert to single age number
        age_display = self.age_display_map.get(age_range, age_range)
        
        return age_display, gender, age_range

    def predict_with_api(self, face_img, user_name=None):
        """
        Estimate age using free third-party APIs (Agify by name, HuggingFace by image),
        falling back gracefully to local Caffe model.
        
        Args:
            face_img: Face region image (numpy array)
            user_name: Optional user name for free Agify API lookup
            
        Returns:
            Tuple of (age_display, gender, age_range, provider_name)
        """
        # Run local prediction for baseline gender and fallback age
        local_age, gender, local_range = self.predict(face_img)
        
        # Try Agify free API if user name is known
        if user_name and self.api_service:
            agify_res = self.api_service.estimate_age_from_name(user_name)
            if agify_res and agify_res.get('age'):
                return str(agify_res['age']), gender, f"({agify_res['age']})", agify_res['provider']
                
        # Try Hugging Face image API if configured
        if self.api_service:
            api_res = self.api_service.estimate_age_from_image(face_roi=face_img)
            if api_res and api_res.get('age'):
                return api_res['age'], gender, api_res.get('age_range', local_range), api_res['provider']
                
        # Fallback to local model
        return local_age, gender, local_range, "Local Caffe Model"
    
    def get_detailed_info(self, age_range):
        """
        Get detailed information about the age category
        
        Args:
            age_range: Age range key (e.g., '(25-32)')
            
        Returns:
            Dictionary with detailed information
        """
        return self.age_info.get(age_range, {
            'category': 'Unknown',
            'animal': 'Human 👤',
            'traits': 'Unique individual',
            'film_stars': 'Various',
            'description': 'Every age is special'
        })
