"""
Mr. Beast - Hybrid Voice Robot
Main Application Entry Point
Integrates: Face Detection + Voice + AI Brain + Database
"""
import cv2
import yaml
import time
from datetime import datetime

# Existing modules (DO NOT REGENERATE)
from core.detector import FaceDetector
from core.age_gender import AgeGenderPredictor

# NEW modules
try:
    from vision.embeddings import FaceEmbeddings
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠ Face embeddings not available (requires face_recognition)")

from vision.capture import FaceCapture
from voice.stt import SpeechToText
from voice.tts import TextToSpeech
from ai.hybrid_brain import HybridBrain

try:
    from db.connection import get_db
    from db.user_store import UserStore
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠ Database not available")

class MrBeastRobot:
    """Main robot controller"""
    
    def __init__(self):
        """Initialize Mr. Beast Robot"""
        print("="*60)
        print("🤖 Initializing Mr. Beast - Hybrid Voice Robot")
        print("="*60)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize existing modules
        print("\n📸 Loading existing vision modules...")
        self.face_detector = FaceDetector()
        self.age_gender_predictor = AgeGenderPredictor()
        
        # Initialize NEW modules
        print("\n🆕 Loading NEW modules...")
        if EMBEDDINGS_AVAILABLE:
            self.face_embeddings = FaceEmbeddings(model='small')  # Use 'small' for speed
        else:
            self.face_embeddings = None
        
        self.face_capture = FaceCapture(
            save_dir=self.config['paths']['captures'],
            auto_delay=self.config['face']['auto_capture_delay']
        )
        
        # Voice system
        print("\n🎤 Initializing voice system...")
        self.tts = TextToSpeech(
            rate=self.config['voice']['speech_rate'],
            volume=self.config['voice']['volume']
        )
        self.stt = SpeechToText(language=self.config['voice']['language'])
        
        # AI Brain
        print("\n🧠 Initializing AI Brain...")
        self.brain = HybridBrain()
        
        # Database
        print("\n🗄️ Connecting to database...")
        self.db = get_db()
        self.user_store = UserStore()
        
        # State
        self.current_user = None
        self.conversation_active = False
        self.onboarding_step = None
        self.pending_data = {}
        
        print("\n✅ Mr. Beast Robot initialized successfully!")
        print("="*60)
    
    def load_config(self):
        """Load configuration from YAML"""
        try:
            with open('config.yml', 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠ Error loading config: {e}")
            # Return default config
            return {
                'robot': {'name': 'Mr. Beast', 'greeting': 'Hello! I am Mr. Beast.'},
                'voice': {'speech_rate': 150, 'volume': 0.9, 'language': 'en-IN'},
                'face': {'similarity_threshold': 0.6, 'auto_capture_delay': 2},
                'paths': {'captures': 'captures/'}
            }
    
    def greet(self):
        """Initial greeting"""
        greeting = self.config['robot']['greeting']
        print(f"\n🔊 {greeting}")
        self.tts.speak(greeting)
    
    def process_face(self, frame, face_bbox):
        """
        Process detected face
        
        Args:
            frame: Video frame
            face_bbox: Face bounding box (x, y, w, h)
            
        Returns:
            Dict with face analysis results
        """
        x, y, w, h = face_bbox
        face_roi = frame[y:y+h, x:x+w]
        
        # Predict age and gender (existing module)
        age, gender, age_range = self.age_gender_predictor.predict(face_roi)
        
        # Generate face embedding (NEW)
        embedding = self.face_embeddings.get_embedding(face_roi)
        
        # Try to match with database (NEW)
        matched_user = None
        if embedding is not None:
            known_embeddings = self.user_store.get_all_embeddings()
            matched_user = self.face_embeddings.find_best_match(
                embedding,
                known_embeddings,
                threshold=self.config['face']['similarity_threshold']
            )
        
        return {
            'age': age,
            'gender': gender,
            'age_range': age_range,
            'embedding': embedding,
            'matched_user': matched_user,
            'face_roi': face_roi,
            'bbox': face_bbox
        }
    
    def handle_matched_user(self, match_info):
        """Handle recognized user"""
        user_name = match_info['name']
        confidence = match_info['confidence']
        
        message = f"I think you are {user_name}. Is that correct?"
        print(f"\n🔊 {message}")
        self.tts.speak(message)
        
        # Listen for confirmation with retry
        print("🎤 Listening for confirmation...")
        response = self.listen_with_prompts(
            prompts=[
                "Please say yes or no.",
                "I'm waiting for your response. Yes or no?",
                "Are you there? Please confirm yes or no."
            ],
            timeout=5
        )
        
        if response:
            print(f"👤 User said: {response}")
            
            # Use AI brain to detect confirmation
            result = self.brain.process_user_input(response)
            
            if result['is_yes']:
                # Confirmed!
                self.current_user = self.user_store.get_user_by_id(match_info['user_id'])
                self.user_store.update_last_seen(match_info['user_id'])
                
                welcome_msg = f"Welcome back, {user_name}! How can I help you today?"
                print(f"\n🔊 {welcome_msg}")
                self.tts.speak(welcome_msg)
                return True
                
            elif result['is_no']:
                # Not the right person
                msg = "Oh, my apologies! Let me treat you as a new visitor."
                print(f"\n🔊 {msg}")
                self.tts.speak(msg)
                return False
        
        return False
    
    def listen_with_prompts(self, prompts, timeout=5, max_attempts=5):
        """
        Listen for speech with repeated prompts if no response
        
        Args:
            prompts: List of prompt messages to cycle through
            timeout: Timeout for each listening attempt
            max_attempts: Maximum number of attempts before giving up
            
        Returns:
            Recognized text or None
        """
        for attempt in range(max_attempts):
            response = self.stt.listen_once(timeout=timeout)
            
            if response:
                return response
            
            # No response, prompt again
            if attempt < max_attempts - 1:
                prompt = prompts[attempt % len(prompts)]
                print(f"\n🔊 {prompt}")
                self.tts.speak(prompt)
        
        # Give up after max attempts
        give_up_msg = "I'm having trouble hearing you. Let's try again later."
        print(f"\n🔊 {give_up_msg}")
        self.tts.speak(give_up_msg)
        return None
    
    def handle_new_user(self, face_data):
        """Handle new user onboarding"""
        # Ask for consent
        consent_msg = "I don't recognize you. May I save your details?"
        print(f"\n🔊 {consent_msg}")
        self.tts.speak(consent_msg)
        
        # Listen for consent with retry
        print("🎤 Listening for consent...")
        response = self.listen_with_prompts(
            prompts=[
                "Please say yes or no.",
                "I need your permission. Yes or no?",
                "Are you there? Please respond yes or no."
            ],
            timeout=5
        )
        
        if not response:
            print("⚠ No response received after multiple attempts")
            return False
        
        print(f"👤 User said: {response}")
        
        # Check consent
        result = self.brain.process_user_input(response)
        
        if not result['is_yes']:
            msg = "No problem! I won't save your information."
            print(f"\n🔊 {msg}")
            self.tts.speak(msg)
            return False
        
        # Start onboarding
        self.pending_data = {
            'age': face_data['age'],
            'gender': face_data['gender'],
            'age_range': face_data['age_range'],
            'embedding': face_data['embedding'],
            'face_roi': face_data['face_roi']
        }
        
        # Ask for name
        name_msg = "Great! What's your name?"
        print(f"\n🔊 {name_msg}")
        self.tts.speak(name_msg)
        
        print("🎤 Listening for name...")
        name_response = self.listen_with_prompts(
            prompts=[
                "Please tell me your name.",
                "I'm waiting. What's your name?",
                "Can you hear me? Please say your name."
            ],
            timeout=5
        )
        
        if name_response:
            print(f"👤 User said: {name_response}")
            name = self.brain.extract_information(name_response, 'name')
            
            if name:
                self.pending_data['name'] = name
                
                # Ask for job/college
                job_msg = f"Nice to meet you, {name}! What do you do? Are you a student or working?"
                print(f"\n🔊 {job_msg}")
                self.tts.speak(job_msg)
                
                print("🎤 Listening for job/college...")
                job_response = self.listen_with_prompts(
                    prompts=[
                        "Please tell me what you do.",
                        "Are you a student or working? Please respond.",
                        "I'm listening. What do you do?"
                    ],
                    timeout=5
                )
                
                if job_response:
                    print(f"👤 User said: {job_response}")
                    job_info = self.brain.extract_information(job_response, 'job')
                    
                    if job_info:
                        self.pending_data['college_or_job'] = job_info
                        
                        # Final confirmation
                        confirm_msg = "Got it! Should I save this information?"
                        print(f"\n🔊 {confirm_msg}")
                        self.tts.speak(confirm_msg)
                        
                        print("🎤 Listening for final confirmation...")
                        final_response = self.listen_with_prompts(
                            prompts=[
                                "Please confirm. Yes or no?",
                                "Should I save this? Yes or no?",
                                "I need confirmation. Yes or no?"
                            ],
                            timeout=5
                        )
                        
                        if final_response:
                            print(f"👤 User said: {final_response}")
                            final_result = self.brain.process_user_input(final_response)
                            
                            if final_result['is_yes']:
                                # Save to database
                                user_id = self.user_store.create_user(
                                    name=self.pending_data['name'],
                                    age_range=self.pending_data['age_range'],
                                    gender=self.pending_data['gender'],
                                    college_or_job=self.pending_data['college_or_job'],
                                    consent='Yes'
                                )
                                
                                if user_id:
                                    # Save face image and embedding
                                    success, file_path, _ = self.face_capture.capture_face(
                                        frame=None,  # We already have face_roi
                                        face_bbox=None,
                                        user_name=self.pending_data['name']
                                    )
                                    
                                    if self.pending_data['embedding'] is not None:
                                        self.user_store.save_user_image(
                                            user_id=user_id,
                                            file_path=file_path if success else 'temp.jpg',
                                            embedding=self.pending_data['embedding'],
                                            is_primary=True
                                        )
                                    
                                    success_msg = f"Perfect! Your information has been saved, {name}."
                                    print(f"\n🔊 {success_msg}")
                                    self.tts.speak(success_msg)
                                    
                                    self.current_user = self.user_store.get_user_by_id(user_id)
                                    return True
        
        return False
    
    def run_demo(self):
        """Run a simple demo without camera"""
        print("\n" + "="*60)
        print("🎮 Running Mr. Beast Demo (No Camera)")
        print("="*60)
        
        # Greet
        self.greet()
        time.sleep(2)
        
        # Simulate conversation
        print("\n📝 Simulating conversation...")
        
        test_inputs = [
            "hello",
            "who are you",
            "yes",
            "thank you"
        ]
        
        for user_input in test_inputs:
            print(f"\n👤 User: {user_input}")
            
            # Process with AI brain
            result = self.brain.process_user_input(user_input)
            
            print(f"🧠 Intent: {result['intent']} (confidence: {result['confidence']:.2f})")
            print(f"🔊 Robot: {result['recommended_response']}")
            
            self.tts.speak(result['recommended_response'])
            time.sleep(1)
        
        print("\n✅ Demo completed!")
    
    def run_with_camera(self):
        """Run with live camera feed"""
        print("\n" + "="*60)
        print("📸 Starting Camera Mode")
        print("="*60)
        
        # Greet
        self.greet()
        
        # Open camera
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("✗ Cannot open camera")
            return
        
        print("\n✓ Camera opened")
        print("Press 'q' to quit")
        
        face_detected_time = None
        face_processed = False
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect faces
            faces = self.face_detector.detect_faces(frame)
            
            if len(faces) > 0:
                # Draw bounding boxes
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, "Face Detected", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Process first face after delay
                if face_detected_time is None:
                    face_detected_time = time.time()
                
                elapsed = time.time() - face_detected_time
                
                if elapsed >= 2 and not face_processed:
                    print("\n🔍 Processing face...")
                    
                    # Process face
                    face_data = self.process_face(frame, faces[0])
                    
                    print(f"Age: {face_data['age']}, Gender: {face_data['gender']}")
                    
                    # Check if matched
                    if face_data['matched_user']:
                        print(f"✓ Matched: {face_data['matched_user']['name']}")
                        self.handle_matched_user(face_data['matched_user'])
                    else:
                        print("✗ No match found - New user")
                        self.handle_new_user(face_data)
                    
                    face_processed = True
            else:
                face_detected_time = None
                face_processed = False
            
            # Display
            cv2.imshow('Mr. Beast Robot', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("\n✓ Camera closed")

def main():
    """Main entry point"""
    try:
        # Initialize robot
        robot = MrBeastRobot()
        
        # Ask user which mode
        print("\n" + "="*60)
        print("Select Mode:")
        print("1. Demo Mode (No camera, test AI)")
        print("2. Camera Mode (Full system with camera)")
        print("="*60)
        
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == '1':
            robot.run_demo()
        elif choice == '2':
            robot.run_with_camera()
        else:
            print("Invalid choice. Running demo mode...")
            robot.run_demo()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
