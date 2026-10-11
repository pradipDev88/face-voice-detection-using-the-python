"""
Voice-Guided Profile Creation Flow
Handles interactive voice form-filling:
1. Full Name
2. Age
3. Address / City
4. Job / Profession details
5. Final Confirmation (Yes / No / Corrections)
6. Camera Screenshot / Photo Capture
7. Profile saving into UserStore (MySQL + offline backup) & UI dashboard
"""
import os
import time
import re
from datetime import datetime
import cv2
from typing import Optional, Dict, Any, Callable

from voice.language_manager import LanguageManager


class VoiceProfileFlow:
    """Manages multi-step voice profile creation and camera snapshot"""

    def __init__(self, tts, stt, brain, user_store, face_capture=None, face_embeddings=None, ui_callback=None, profile_service=None):
        self.tts = tts
        self.stt = stt
        self.brain = brain
        self.user_store = user_store
        self.face_capture = face_capture
        self.face_embeddings = face_embeddings
        self.ui_callback = ui_callback
        self.profile_service = profile_service
        
        self.is_active = False
        self.current_lang = 'en'
        self.profile_data = {
            'name': '',
            'age': '',
            'address': '',
            'job': '',
            'gender': 'Not specified',
            'photo_path': '',
            'embedding': None
        }

    def notify_ui(self, status_message: str):
        """Update GUI if callback is registered"""
        if self.ui_callback:
            try:
                self.ui_callback(self.profile_data, status_message)
            except Exception as e:
                print(f"⚠ UI update error: {e}")

    def speak(self, text: str):
        """Speak response and print log with language awareness"""
        print(f"\n🤖 Robot [{self.current_lang.upper()}]: {text}")
        if self.tts:
            try:
                self.tts.speak(text, lang=self.current_lang, block=True)
            except Exception as e:
                print(f"⚠ TTS speak error: {e}")

    def listen_input(self, timeout=6) -> Optional[str]:
        """Listen from microphone with interactive fallback"""
        if self.stt and getattr(self.stt, 'is_available', False):
            text = self.stt.listen_once(timeout=timeout)
            if text:
                print(f"👤 User: {text}")
                detected = LanguageManager.detect_language(text)
                if detected != 'en' or self.current_lang == 'en':
                    self.current_lang = detected
                return text.strip()
        
        # Fallback to console input if microphone has no speech or unavailable
        try:
            print("💬 [Voice/Text]: You can speak or type here:")
            val = input("👤 Your answer: ").strip()
            if val:
                detected = LanguageManager.detect_language(val)
                self.current_lang = detected
            return val if val else None
        except (EOFError, KeyboardInterrupt):
            return None

    def start_flow(self, current_frame=None, detected_gender='Not specified', detected_age=None) -> bool:
        """Execute full multilingual voice profile onboarding flow"""
        self.is_active = True
        self.profile_data = {
            'name': '',
            'age': str(detected_age) if detected_age else '',
            'address': '',
            'job': '',
            'gender': detected_gender or 'Not specified',
            'photo_path': '',
            'embedding': None
        }

        print("\n" + "="*60)
        print("📝 STARTING MULTILINGUAL VOICE PROFILE CREATION")
        print("="*60)

        # Step 1: Full Name
        self.notify_ui("Step 1/5: Full Name")
        prompt = LanguageManager.get_phrase('ask_name', lang=self.current_lang)
        self.speak(prompt)
        
        name = None
        for attempt in range(3):
            reply = self.listen_input(timeout=6)
            if reply:
                if self.brain.detect_cancellation(reply):
                    self.speak(LanguageManager.get_phrase('cancelled', lang=self.current_lang))
                    self.is_active = False
                    return False

                name = self.brain.extract_full_name(reply) or reply.strip().title()
                if name and len(name.split()) >= 1 and name.lower() not in ['no', 'cancel', 'stop']:
                    break
            if attempt < 2:
                reask = LanguageManager.get_phrase('reask_name', lang=self.current_lang)
                self.speak(reask)

        if not name:
            self.speak("We couldn't capture your name. Let's try creating your profile later!")
            self.is_active = False
            return False

        self.profile_data['name'] = name
        self.notify_ui(f"Full Name: {name}")

        # Step 2: Age
        self.notify_ui("Step 2/5: Age")
        prompt = LanguageManager.get_phrase('ask_age', lang=self.current_lang, name=name)
        self.speak(prompt)
        
        age = None
        for attempt in range(3):
            reply = self.listen_input(timeout=6)
            if reply:
                if self.brain.detect_cancellation(reply):
                    self.speak(LanguageManager.get_phrase('cancelled', lang=self.current_lang))
                    self.is_active = False
                    return False

                age = self.brain.extract_age(reply)
                if age:
                    break
            if attempt < 2:
                reask = LanguageManager.get_phrase('reask_age', lang=self.current_lang, name=name)
                self.speak(reask)

        if not age and detected_age:
            age = str(detected_age)
        elif not age:
            age = "25"

        self.profile_data['age'] = str(age)
        self.notify_ui(f"Age: {age}")

        # Step 3: Address / City
        self.notify_ui("Step 3/5: Address / City")
        prompt = LanguageManager.get_phrase('ask_address', lang=self.current_lang)
        self.speak(prompt)
        
        address = None
        for attempt in range(3):
            reply = self.listen_input(timeout=6)
            if reply:
                if self.brain.detect_cancellation(reply):
                    self.speak(LanguageManager.get_phrase('cancelled', lang=self.current_lang))
                    self.is_active = False
                    return False
                if self.brain.detect_skip(reply):
                    address = "Not specified"
                    break

                address = self.brain.extract_address(reply) or reply.strip().title()
                if address and len(address) > 1:
                    break
            if attempt < 2:
                reask = LanguageManager.get_phrase('reask_address', lang=self.current_lang)
                self.speak(reask)

        if not address:
            address = "Not specified"

        self.profile_data['address'] = address
        self.notify_ui(f"Address: {address}")

        # Step 4: Job / Profession Details
        self.notify_ui("Step 4/5: Job / Studies")
        prompt = LanguageManager.get_phrase('ask_job', lang=self.current_lang)
        self.speak(prompt)
        
        job = None
        for attempt in range(3):
            reply = self.listen_input(timeout=6)
            if reply:
                if self.brain.detect_cancellation(reply):
                    self.speak(LanguageManager.get_phrase('cancelled', lang=self.current_lang))
                    self.is_active = False
                    return False
                if self.brain.detect_skip(reply):
                    job = "Not specified"
                    break

                job = self.brain.extract_job_or_college(reply) or reply.strip().title()
                if job and len(job) > 1:
                    break
            if attempt < 2:
                reask = LanguageManager.get_phrase('reask_job', lang=self.current_lang)
                self.speak(reask)

        if not job:
            job = "Not specified"

        self.profile_data['job'] = job
        self.notify_ui(f"Job: {job}")

        # Step 5: Final Confirmation
        self.notify_ui("Step 5/6: Confirmation")
        confirm_text = LanguageManager.get_phrase('confirm_spoken', lang=self.current_lang, **self.profile_data)
        self.speak(confirm_text)

        confirmed = False
        for attempt in range(3):
            reply = self.listen_input(timeout=6)
            if reply:
                if self.brain.detect_cancellation(reply):
                    self.speak(LanguageManager.get_phrase('cancelled', lang=self.current_lang))
                    self.is_active = False
                    return False

                is_yes, is_no, _ = self.brain.detect_confirmation(reply)
                if is_yes:
                    confirmed = True
                    break
                elif is_no:
                    self.speak(LanguageManager.get_phrase('cancelled', lang=self.current_lang))
                    self.is_active = False
                    return False
            if attempt < 2:
                self.speak(LanguageManager.get_phrase('confirm_spoken', lang=self.current_lang, **self.profile_data))

        # Default to confirming if attempts run out
        if not confirmed:
            confirmed = True

        # Step 6: Screenshot / Photo Capture
        self.notify_ui("Step 6/6: Capturing Photo...")
        photo_prompt = LanguageManager.get_phrase('photo_prompt', lang=self.current_lang)
        self.speak(photo_prompt)
        time.sleep(0.4)

        # Capture frame
        photo_path = self._take_photo(current_frame, name)
        self.profile_data['photo_path'] = photo_path
        self.notify_ui(f"Photo captured: {os.path.basename(photo_path)}")

        # Step 7: Save Profile to Database & Storage
        user_id = None
        if self.profile_service:
            saved_record = self.profile_service.save_profile(self.profile_data, frame=current_frame)
            user_id = saved_record.get('user_id')
            if saved_record.get('photo_path'):
                photo_path = saved_record['photo_path']
                self.profile_data['photo_path'] = photo_path
        elif self.user_store:
            user_id = self.user_store.create_user(
                name=self.profile_data['name'],
                age_range=f"({self.profile_data['age']})",
                gender=self.profile_data['gender'],
                college_or_job=self.profile_data['job'],
                address=self.profile_data['address'],
                photo_path=self.profile_data['photo_path'],
                consent='Yes'
            )
            
            # Save embedding if available
            if self.profile_data.get('embedding') is not None and user_id:
                try:
                    self.user_store.save_user_image(
                        user_id=user_id,
                        file_path=self.profile_data['photo_path'],
                        embedding=self.profile_data['embedding'],
                        is_primary=True
                    )
                except Exception as e:
                    print(f"⚠ Embedding save warning: {e}")

        self.notify_ui("Profile Created Successfully! ✅")
        success_message = LanguageManager.get_phrase('save_success', lang=self.current_lang, name=name)
        self.speak(success_message)
        print("\n" + "="*60)
        print(f"✅ PROFILE COMPLETE FOR: {name} (ID: {user_id})")
        print(f"   Photo: {photo_path}")
        print("="*60 + "\n")
        
        self.is_active = False
        return True

    def _take_photo(self, frame, name: str) -> str:
        """Take screenshot from frame or open camera momentarily"""
        os.makedirs('captures', exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower().strip())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_profile_{timestamp}.jpg"
        filepath = os.path.join('captures', filename)

        captured_img = None
        if frame is not None:
            captured_img = frame.copy()
        else:
            try:
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    ret, f = cap.read()
                    if ret:
                        captured_img = f
                    cap.release()
            except Exception as e:
                print(f"⚠ Camera capture error: {e}")

        if captured_img is None:
            import numpy as np
            captured_img = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(captured_img, f"Profile: {name}", (50, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)

        cv2.imwrite(filepath, captured_img)
        print(f"📸 Profile photo snapshot saved: {filepath}")

        if self.face_embeddings:
            try:
                emb = self.face_embeddings.get_embedding(captured_img)
                if emb is not None:
                    self.profile_data['embedding'] = emb
                    print("✓ Face embedding generated and linked to profile")
            except Exception as e:
                print(f"⚠ Face embedding generation: {e}")

        return filepath
