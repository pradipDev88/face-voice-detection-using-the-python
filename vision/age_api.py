"""
Third-Party Free Age Estimation Service
Integrates free external APIs for age prediction from face images and user names.

Supported Providers:
  1. Hugging Face Inference API (ViT Age Classifier: nateraw/vit-age-classifier)
     - Accepts face image bytes directly
     - Free serverless tier (uses HF_TOKEN env var or config.yml)
  2. Agify.io Name-to-Age API
     - 100% Free, NO API key required
     - Predicts age from user's given name
  3. Local Caffe Fallback
     - Offline fallback when network is unavailable
"""
import os
import json
import urllib.request
import urllib.error
import cv2
import numpy as np


class ThirdPartyAgeService:
    """Handles third-party API age estimation with fallback"""

    def __init__(self, config=None):
        self.config = config or {}
        self.hf_model_url = "https://router.huggingface.co/hf-inference/models/nateraw/vit-age-classifier"
        self.hf_token = os.environ.get("HF_TOKEN") or self._get_config_hf_token()
        self.agify_url = "https://api.agify.io"

        # Label mapping for ViT age classifier
        self.hf_label_to_age = {
            "0-2": 1,
            "3-9": 6,
            "10-19": 16,
            "20-29": 24,
            "30-39": 34,
            "40-49": 44,
            "50-59": 54,
            "60-69": 64,
            "more than 70": 75,
            "70+": 75
        }

    def _get_config_hf_token(self):
        """Extract Hugging Face token from config if present"""
        try:
            return self.config.get('age_prediction', {}).get('huggingface_token', '')
        except Exception:
            return ""

    def estimate_age_from_name(self, name):
        """
        Estimate age using the free Agify API (No API key needed).
        
        Args:
            name: Person's name (string)
            
        Returns:
            dict with 'age', 'provider', 'count' or None
        """
        if not name or not isinstance(name, str):
            return None

        clean_name = name.strip().split()[0]  # First name
        if not clean_name:
            return None

        url = f"{self.agify_url}/?name={urllib.parse.quote(clean_name)}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "MrBeastRobot/1.0"}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    age = data.get("age")
                    if age is not None:
                        print(f"✓ Agify API estimated age for '{clean_name}': {age} years (sample count: {data.get('count', 0)})")
                        return {
                            "age": str(age),
                            "provider": "Agify (Free API)",
                            "count": data.get("count", 0),
                            "name": clean_name
                        }
        except Exception as e:
            print(f"⚠ Agify API query failed ({e})")

        return None

    def estimate_age_from_image(self, face_roi):
        """
        Estimate age from cropped face image using Hugging Face ViT model.
        
        Args:
            face_roi: Numpy array (BGR image of face region)
            
        Returns:
            dict with 'age', 'age_range', 'provider', 'confidence' or None
        """
        if face_roi is None or face_roi.size == 0:
            return None

        # Encode face_roi to JPEG bytes
        try:
            success, encoded_img = cv2.imencode('.jpg', face_roi)
            if not success:
                return None
            img_bytes = encoded_img.tobytes()
        except Exception as e:
            print(f"⚠ Image encoding error: {e}")
            return None

        headers = {
            "Content-Type": "application/octet-stream",
            "User-Agent": "MrBeastRobot/1.0"
        }
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"

        try:
            req = urllib.request.Request(self.hf_model_url, data=img_bytes, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode("utf-8"))
                    # Result is list of {'label': '...', 'score': float}
                    if isinstance(result, list) and len(result) > 0:
                        top = result[0]
                        label = top.get('label', '')
                        score = top.get('score', 0.0)
                        mapped_age = str(self.hf_label_to_age.get(label, label))
                        print(f"✓ Hugging Face API age estimate: {mapped_age} (range: {label}, confidence: {score:.2f})")
                        return {
                            "age": mapped_age,
                            "age_range": f"({label})",
                            "confidence": score,
                            "provider": "Hugging Face ViT API"
                        }
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print("💡 Hugging Face API requires a free token (set HF_TOKEN or in config.yml).")
            else:
                print(f"⚠ Hugging Face API returned HTTP {e.code}")
        except Exception as e:
            print(f"⚠ Third-party image age API error: {e}")

        return None
