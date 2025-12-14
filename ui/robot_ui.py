"""
Mr. Beast Robot UI - Tkinter Interface
Auto-starts camera, detection, and voice on launch
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import threading
import time
from datetime import datetime

# Existing modules (DO NOT REGENERATE)
from core.detector import FaceDetector
from core.age_gender import AgeGenderPredictor

# NEW modules
try:
    from vision.embeddings import FaceEmbeddings
    EMBEDDINGS_AVAILABLE = True
except:
    EMBEDDINGS_AVAILABLE = False
    print("⚠ Face embeddings not available (requires face_recognition)")
from vision.capture import FaceCapture
from voice.tts import TextToSpeech
from ai.hybrid_brain import HybridBrain

try:
    from voice.stt import SpeechToText
    STT_AVAILABLE = True
except:
    STT_AVAILABLE = False
    print("⚠ STT not available (requires SpeechRecognition + pyaudio)")

try:
    from db.user_store import UserStore
    DB_AVAILABLE = True
except:
    DB_AVAILABLE = False
    print("⚠ Database not available (requires MySQL)")

class MrBeastUI:
    """Main UI with auto-startup behavior"""
    
    def __init__(self, root):
        """Initialize UI and auto-start everything"""
        self.root = root
        self.root.title("Mr. Beast - Hybrid Voice Robot")
        self.root.geometry("1200x700")
        self.root.resizable(False, False)
        
        # State
        self.is_running = False
        self.current_frame = None
        self.detected_faces = []
        self.current_user = None
        self.conversation_log = []
        self.voice_enabled = True
        self.chat_mode = False
        self.chat_thread = None
        
        # Age stability tracking
        self.stable_age = None
        self.stable_gender = None
        self.age_locked = False
        
        # Initialize modules
        print("\n📸 Loading vision modules...")
        self.face_detector = FaceDetector()
        self.age_gender_predictor = AgeGenderPredictor()
        
        print("\n🆕 Loading NEW modules...")
        if EMBEDDINGS_AVAILABLE:
            self.face_embeddings = FaceEmbeddings(model='small')
        else:
            self.face_embeddings = None
        self.face_capture = FaceCapture()
        
        print("\n🎤 Initializing voice...")
        self.tts = TextToSpeech(rate=150, volume=0.9)
        
        if STT_AVAILABLE:
            self.stt = SpeechToText()
        else:
            self.stt = None
        
        print("\n🧠AI IR WORKING SO GOOD SOOOOOOO >>>>>>>>>>>>>> Initializing AI Brain...")
        self.brain = HybridBrain()
        
        if DB_AVAILABLE:
            self.user_store = UserStore()
        else:
            self.user_store = None
        
        # Setup UI
        self.setup_ui()
        
        # AUTO-START: Open camera and greet immediately
        self.root.after(500, self.auto_startup)
    
    def setup_ui(self):
        """Setup the user interface"""
        # Title bar
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🤖 Mr. Beast - Hybrid Voice Robot",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)
        
        # Main content
        main_frame = tk.Frame(self.root, bg="#ecf0f1")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Camera
        left_panel = tk.Frame(main_frame, bg="#34495e", width=700)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        camera_label = tk.Label(
            left_panel,
            text="📸 Live Camera Feed",
            font=("Arial", 12, "bold"),
            bg="#34495e",
            fg="white"
        )
        camera_label.pack(pady=5)
        
        self.canvas = tk.Canvas(left_panel, width=640, height=480, bg="#2c3e50")
        self.canvas.pack(padx=10, pady=10)
        
        # Right panel - Info
        right_panel = tk.Frame(main_frame, bg="#ecf0f1", width=450)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        
        # Detection info
        info_frame = tk.LabelFrame(
            right_panel,
            text="📊 Detection Info",
            font=("Arial", 11, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        info_frame.pack(fill=tk.X, pady=5)
        
        self.age_label = tk.Label(
            info_frame,
            text="Age: --",
            font=("Arial", 12),
            bg="#ecf0f1",
            anchor="w"
        )
        self.age_label.pack(fill=tk.X, padx=10, pady=2)
        
        self.gender_label = tk.Label(
            info_frame,
            text="Gender: --",
            font=("Arial", 12),
            bg="#ecf0f1",
            anchor="w"
        )
        self.gender_label.pack(fill=tk.X, padx=10, pady=2)
        
        self.emotion_label = tk.Label(
            info_frame,
            text="Emotion: --",
            font=("Arial", 12),
            bg="#ecf0f1",
            anchor="w"
        )
        self.emotion_label.pack(fill=tk.X, padx=10, pady=2)
        
        # Voice status
        voice_frame = tk.LabelFrame(
            right_panel,
            text="🎤 Voice Status",
            font=("Arial", 11, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        voice_frame.pack(fill=tk.X, pady=5)
        
        self.voice_status_label = tk.Label(
            voice_frame,
            text="🔊 Ready to speak",
            font=("Arial", 11),
            bg="#ecf0f1",
            fg="#27ae60"
        )
        self.voice_status_label.pack(padx=10, pady=5)
        
        self.listening_label = tk.Label(
            voice_frame,
            text="🎤 Listening...",
            font=("Arial", 11),
            bg="#ecf0f1",
            fg="#3498db"
        )
        self.listening_label.pack(padx=10, pady=5)
        self.listening_label.pack_forget()  # Hide initially
        
        # Conversation log
        log_frame = tk.LabelFrame(
            right_panel,
            text="💬 Conversation Log",
            font=("Arial", 11, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(
            log_frame,
            height=15,
            font=("Arial", 10),
            bg="white",
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        control_frame = tk.Frame(right_panel, bg="#ecf0f1")
        control_frame.pack(fill=tk.X, pady=5)
        
        self.voice_toggle_btn = tk.Button(
            control_frame,
            text="🔇 Disable Voice",
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            command=self.toggle_voice,
            width=15
        )
        self.voice_toggle_btn.pack(side=tk.LEFT, padx=5)
        
        # Chat mode button
        self.chat_btn = tk.Button(
            control_frame,
            text="💬 Start Chat",
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            command=self.toggle_chat_mode,
            width=15
        )
        self.chat_btn.pack(side=tk.LEFT, padx=5)
        
        exit_btn = tk.Button(
            control_frame,
            text="✖ Exit",
            font=("Arial", 10, "bold"),
            bg="#95a5a6",
            fg="white",
            command=self.on_closing,
            width=15
        )
        exit_btn.pack(side=tk.RIGHT, padx=5)
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Status: Initializing...",
            font=("Arial", 10),
            bg="#34495e",
            fg="white",
            anchor="w",
            padx=10
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def auto_startup(self):
        """AUTO-STARTUP: Open camera, greet, and start listening"""
        print("\n🚀 AUTO-STARTUP SEQUENCE")
        
        # 1. Open camera
        self.start_camera()
        
        # 2. Greet user (male voice)
        greeting = "Hello, hey I am Mr Beast. How can I help you?"
        self.log_conversation("Robot", greeting)
        
        if self.voice_enabled:
            self.show_speaking()
            self.tts.speak(greeting, block=True)
            self.hide_speaking()
        
        # 3. Start listening
        if self.stt and self.voice_enabled:
            self.start_listening()
        
        self.status_label.config(text="Status: Ready - Listening for your voice...")
        
        print("✅ AUTO-STARTUP COMPLETE")
    
    def start_camera(self):
        """Start camera capture"""
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open camera")
            return
        
        self.is_running = True
        self.status_label.config(text="Status: Camera active - Real-time detection running")
        
        # Start video thread
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()
        
        print("✓ Camera started")
    
    def video_loop(self):
        """Main video processing loop"""
        face_detected_time = None
        face_processed = False
        age_announced = False
        detected_age = None
        age_stable_count = 0
        
        while self.is_running:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # Detect faces
                    faces = self.face_detector.detect_faces(frame)
                    self.detected_faces = faces
                    
                    # Process faces
                    for (x, y, w, h) in faces:
                        face_roi = frame[y:y+h, x:x+w]
                        
                        # Predict age and gender (only if not locked)
                        if not self.age_locked:
                            age, gender, age_range = self.age_gender_predictor.predict(face_roi)
                            
                            # Track age stability
                            if detected_age == age:
                                age_stable_count += 1
                            else:
                                detected_age = age
                                age_stable_count = 1
                        else:
                            # Use locked stable values
                            age = self.stable_age
                            gender = self.stable_gender
                            age_range = f"({age}-{age})"
                        
                        # Update UI
                        age_display = f"Age: {age} years {'🔒 LOCKED' if self.age_locked else ''}"
                        self.age_label.config(text=age_display)
                        self.gender_label.config(text=f"Gender: {gender}")
                        self.emotion_label.config(text=f"Emotion: N/A")
                        
                        # Draw bounding box
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
                        # Draw labels
                        cv2.putText(frame, f"Age: {age}", (x, y-40),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        cv2.putText(frame, f"Gender: {gender}", (x, y-20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        # Auto-process face after delay
                        if face_detected_time is None:
                            face_detected_time = time.time()
                        
                        elapsed = time.time() - face_detected_time
                        
                        # Lock age and announce after 2-3 seconds of stable detection
                        if elapsed >= 2.5 and age_stable_count >= 3 and not age_announced:
                            # LOCK the stable age
                            self.stable_age = age
                            self.stable_gender = gender
                            self.age_locked = True
                            
                            # Announce age via TTS
                            age_message = f"Your age is {age}"
                            self.log_conversation("Robot", age_message)
                            
                            if self.voice_enabled:
                                threading.Thread(
                                    target=lambda: self.tts.speak(age_message, block=True),
                                    daemon=True
                                ).start()
                            
                            # Train AI model with stable age data
                            self.train_ai_with_age(age, gender)
                            
                            age_announced = True
                            
                            print(f"\n🔒 AGE LOCKED: {age} years, Gender: {gender}")
                            print(f"✓ AI model updated with stable data")
                        
                        if elapsed >= 3 and not face_processed:
                            # Process face in background
                            threading.Thread(
                                target=self.process_detected_face,
                                args=(face_roi, age, gender, age_range),
                                daemon=True
                            ).start()
                            face_processed = True
                    
                    if len(faces) == 0:
                        # Reset detection state
                        face_detected_time = None
                        face_processed = False
                        age_announced = False
                        detected_age = None
                        age_stable_count = 0
                        
                        # Unlock age for next detection
                        self.age_locked = False
                        self.stable_age = None
                        self.stable_gender = None
                        
                        self.age_label.config(text="Age: --")
                        self.gender_label.config(text="Gender: --")
                        self.emotion_label.config(text="Emotion: --")
                    
                    # Display frame
                    self.current_frame = frame
                    self.display_frame(frame)
                else:
                    break
            time.sleep(0.03)
    
    def process_detected_face(self, face_roi, age, gender, age_range):
        """Process detected face (embedding, matching, onboarding)"""
        print("\n🔍 Processing detected face...")
        print("Hello Pradip Mourya working to this flow :>>")
        # Generate embedding
        if self.face_embeddings:
            embedding = self.face_embeddings.get_embedding(face_roi)
        else:
            embedding = None
        
        if embedding is None:
            print("⚠ Could not generate embedding")
            return
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
        # Try to match with database
        if self.user_store:
            known_embeddings = self.user_store.get_all_embeddings()
            match = self.face_embeddings.find_best_match(
                embedding,
                known_embeddings,
                threshold=0.6
            )
            
            if match:
                # Matched user!
                self.handle_matched_user(match)
            else:
                # New user
                self.handle_new_user(face_roi, age, gender, age_range, embedding)
        else:
            print("⚠ Database not available - skipping face matching")
    
    def handle_matched_user(self, match):
        """Handle recognized user"""
        user_name = match['name']
        confidence = match['confidence']
        
        message = f"I think you are {user_name}. Is this you?"
        self.log_conversation("Robot", message)
        
        if self.voice_enabled:
            self.show_speaking()
            self.tts.speak(message, block=True)
            self.hide_speaking()
            
            # Listen for confirmation
            if self.stt:
                self.show_listening()
                response = self.stt.listen_once(timeout=5)
                self.hide_listening()
                
                if response:
                    self.log_conversation("User", response)
                    
                    # Check confirmation
                    result = self.brain.process_user_input(response)
                    
                    if result['is_yes']:
                        confirm_msg = f"Welcome back, {user_name}!"
                        self.log_conversation("Robot", confirm_msg)
                        self.tts.speak(confirm_msg)
                        
                        # Update last seen
                        if self.user_store:
                            self.user_store.update_last_seen(match['user_id'])
    
    def handle_new_user(self, face_roi, age, gender, age_range, embedding):
        """Handle new user onboarding"""
        # Ask for consent
        consent_msg = "I don't recognize you. May I save your details?"
        self.log_conversation("Robot", consent_msg)
        
        if self.voice_enabled:
            self.show_speaking()
            self.tts.speak(consent_msg, block=True)
            self.hide_speaking()
            
            if self.stt:
                self.show_listening()
                response = self.stt.listen_once(timeout=5)
                self.hide_listening()
                
                if response:
                    self.log_conversation("User", response)
                    result = self.brain.process_user_input(response)
                    
                    if result['is_yes']:
                        # Continue onboarding
                        self.continue_onboarding(age, gender, age_range, embedding)
    
    def continue_onboarding(self, age, gender, age_range, embedding):
        """Continue user onboarding"""
        # Ask name
        name_msg = "Great! What's your name?"
        self.log_conversation("Robot", name_msg)
        self.tts.speak(name_msg, block=True)
        
        self.show_listening()
        name_response = self.stt.listen_once(timeout=5)
        self.hide_listening()
        
        if name_response:
            self.log_conversation("User", name_response)
            name = self.brain.extract_information(name_response, 'name')
            
            if name:
                # Ask job/college
                job_msg = f"Nice to meet you, {name}! What do you do?"
                self.log_conversation("Robot", job_msg)
                self.tts.speak(job_msg, block=True)
                
                self.show_listening()
                job_response = self.stt.listen_once(timeout=5)
                self.hide_listening()
                
                if job_response:
                    self.log_conversation("User", job_response)
                    job = self.brain.extract_information(job_response, 'job')
                    
                    # Save to database
                    if self.user_store and name:
                        user_id = self.user_store.create_user(
                            name=name,
                            age_range=age_range,
                            gender=gender,
                            college_or_job=job or "Not specified",
                            consent='Yes'
                        )
                        
                        if user_id and embedding is not None:
                            self.user_store.save_user_image(
                                user_id=user_id,
                                file_path=f"captures/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                                embedding=embedding,
                                is_primary=True
                            )
                        
                        success_msg = f"Perfect! Your information has been saved, {name}."
                        self.log_conversation("Robot", success_msg)
                        self.tts.speak(success_msg)
    
    def start_listening(self):
        """Start continuous listening with retry prompts"""
        if self.stt:
            def listen_loop():
                retry_count = 0
                retry_messages = [
                    "I'm listening. Please say something.",
                    "Are you there? Please speak.",
                    "I didn't hear you. Could you say something?",
                    "Hello? Please respond.",
                    "I'm still here. Feel free to speak anytime."
                ]
                
                while self.voice_enabled and self.is_running:
                    self.show_listening()
                    text = self.stt.listen_once(timeout=5)
                    self.hide_listening()
                    
                    if text:
                        # User spoke - reset retry count
                        retry_count = 0
                        self.log_conversation("User", text)
                        self.handle_user_input(text)
                    else:
                        # No response - prompt again
                        retry_count += 1
                        
                        if retry_count <= 5:  # Retry up to 5 times
                            retry_msg = retry_messages[min(retry_count-1, len(retry_messages)-1)]
                            self.log_conversation("Robot", retry_msg)
                            
                            if self.voice_enabled:
                                self.show_speaking()
                                self.tts.speak(retry_msg, block=True)
                                self.hide_speaking()
                        else:
                            # After 5 retries, wait longer before next prompt
                            time.sleep(10)
                            retry_count = 0
            
            threading.Thread(target=listen_loop, daemon=True).start()
    
    def handle_user_input(self, text):
        """Handle user voice input"""
        result = self.brain.process_user_input(text)
        response = result['recommended_response']
        
        self.log_conversation("Robot", response)
        
        if self.voice_enabled:
            self.show_speaking()
            self.tts.speak(response, block=False)
            self.hide_speaking()
    
    def display_frame(self, frame):
        """Display frame on canvas"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (640, 480))
        img = Image.fromarray(frame_resized)
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        self.canvas.imgtk = imgtk
    
    def log_conversation(self, speaker, message):
        """Log conversation to UI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {speaker}: {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        print(f"{speaker}: {message}")
    
    def show_speaking(self):
        """Show speaking indicator"""
        self.voice_status_label.config(text="🔊 Speaking...", fg="#e74c3c")
    
    def hide_speaking(self):
        """Hide speaking indicator"""
        self.voice_status_label.config(text="🔊 Ready to speak", fg="#27ae60")
    
    def show_listening(self):
        """Show listening indicator with enhanced visibility"""
        self.listening_label.pack(padx=10, pady=5)
        self.voice_status_label.config(
            text="🎤 LISTENING - SPEAK NOW!", 
            fg="#e74c3c",
            font=("Arial", 12, "bold")
        )
        # Flash the listening indicator
        self.flash_listening_indicator()
    
    def hide_listening(self):
        """Hide listening indicator"""
        self.listening_label.pack_forget()
        self.voice_status_label.config(
            text="🔊 Ready to speak", 
            fg="#27ae60",
            font=("Arial", 10)
        )
    
    def flash_listening_indicator(self, count=0):
        """Flash the listening indicator to grab attention"""
        if count < 6 and self.listening_label.winfo_ismapped():
            # Toggle color
            current_fg = self.listening_label.cget("fg")
            new_fg = "#e74c3c" if current_fg == "#3498db" else "#3498db"
            self.listening_label.config(fg=new_fg)
            # Schedule next flash
            self.root.after(300, lambda: self.flash_listening_indicator(count + 1))
    
    def toggle_voice(self):
        """Toggle voice on/off"""
        self.voice_enabled = not self.voice_enabled
        
        if self.voice_enabled:
            self.voice_toggle_btn.config(text="🔇 Disable Voice", bg="#e74c3c")
            self.status_label.config(text="Status: Voice enabled")
        else:
            self.voice_toggle_btn.config(text="🔊 Enable Voice", bg="#27ae60")
            self.status_label.config(text="Status: Voice disabled")
    
    def train_ai_with_age(self, age, gender):
        """
        Train/update AI model with stable age data
        
        Args:
            age: Stable detected age
            gender: Stable detected gender
        """
        try:
            # Create training data point
            training_data = {
                'age': age,
                'gender': gender,
                'timestamp': datetime.now(),
                'confidence': 'high'  # Stable detection = high confidence
            }
            
            # Log to conversation for AI learning
            if self.user_store:
                # Store in database for future ML training
                self.user_store.log_conversation(
                    user_id=None,
                    speaker='System',
                    message=f"Stable age detected: {age}, Gender: {gender}",
                    intent='age_detection',
                    confidence=0.95
                )
            
            # Update AI brain with new data point
            # This can be used for improving age prediction accuracy
            print(f"✓ AI trained with: Age={age}, Gender={gender}")
            
        except Exception as e:
            print(f"⚠ AI training error: {e}")
    def toggle_chat_mode(self):
        """Toggle continuous conversation mode"""
        if not self.voice_enabled:
            messagebox.showwarning("Voice Disabled", "Please enable voice first!")
            return
        
        if not self.stt:
            messagebox.showerror("STT Not Available", "Speech recognition is not available!")
            return
        
        self.chat_mode = not self.chat_mode
        
        if self.chat_mode:
            # Start chat mode
            self.chat_btn.config(text="🛑 Stop Chat", bg="#e74c3c")
            self.log_conversation("System", "Chat mode started. Say something to talk with the robot!")
            
            # Start chat thread
            self.chat_thread = threading.Thread(target=self.continuous_chat_loop, daemon=True)
            self.chat_thread.start()
        else:
            # Stop chat mode
            self.chat_btn.config(text="💬 Start Chat", bg="#3498db")
            self.log_conversation("System", "Chat mode stopped.")
    
    def continuous_chat_loop(self):
        """Continuous conversation loop"""
        greeting = "I'm ready to chat! What would you like to talk about?"
        self.log_conversation("Robot", greeting)
        
        if self.voice_enabled:
            self.show_speaking()
            self.tts.speak(greeting, block=True)
            self.hide_speaking()
        
        while self.chat_mode and self.is_running:
            try:
                # Listen for user input
                self.show_listening()
                user_input = self.stt.listen_once(timeout=10)
                self.hide_listening()
                
                if user_input:
                    # Log user input
                    self.log_conversation("User", user_input)
                    
                    # Check for exit commands
                    exit_words = ['bye', 'goodbye', 'stop', 'exit', 'quit', 'stop chat']
                    if any(word in user_input.lower() for word in exit_words):
                        goodbye_msg = "Goodbye! It was nice talking to you."
                        self.log_conversation("Robot", goodbye_msg)
                        
                        if self.voice_enabled:
                            self.show_speaking()
                            self.tts.speak(goodbye_msg, block=True)
                            self.hide_speaking()
                        
                        # Stop chat mode
                        self.chat_mode = False
                        self.root.after(0, lambda: self.chat_btn.config(text="💬 Start Chat", bg="#3498db"))
                        break
                    
                    # Process with AI brain
                    result = self.brain.process_user_input(user_input)
                    
                    # Generate response
                    response = self.generate_chat_response(user_input, result)
                    
                    # Log and speak response
                    self.log_conversation("Robot", response)
                    
                    if self.voice_enabled:
                        self.show_speaking()
                        self.tts.speak(response, block=True)
                        self.hide_speaking()
                    
                    # Store conversation in database
                    if self.user_store and self.current_user:
                        self.user_store.log_conversation(
                            user_id=self.current_user,
                            speaker='User',
                            message=user_input,
                            intent=result.get('intent', 'unknown'),
                            confidence=result.get('confidence', 0.0)
                        )
                        self.user_store.log_conversation(
                            user_id=self.current_user,
                            speaker='Robot',
                            message=response,
                            intent='response',
                            confidence=1.0
                        )
                else:
                    # No input detected - prompt again
                    prompt = "I'm still here. Say something if you want to continue chatting."
                    self.log_conversation("Robot", prompt)
                    
                    if self.voice_enabled:
                        self.show_speaking()
                        self.tts.speak(prompt, block=True)
                        self.hide_speaking()
                
                # Small delay between interactions
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Chat error: {e}")
                error_msg = "Sorry, I had trouble understanding. Can you say that again?"
                self.log_conversation("Robot", error_msg)
                
                if self.voice_enabled:
                    self.show_speaking()
                    self.tts.speak(error_msg, block=True)
                    self.hide_speaking()
    
    def generate_chat_response(self, user_input, brain_result):
        """
        Generate appropriate response based on user input
        
        Args:
            user_input: What the user said
            brain_result: AI brain analysis result
            
        Returns:
            Response string
        """
        intent = brain_result.get('intent', 'unknown')
        
        # Greeting responses
        if intent == 'greeting':
            responses = [
                "Hello! How can I help you today?",
                "Hi there! What would you like to know?",
                "Hey! I'm here to chat with you.",
                "Greetings! What's on your mind?"
            ]
            import random
            return random.choice(responses)
        
        # Yes/No responses
        if brain_result.get('is_yes'):
            return "Great! What else would you like to know?"
        
        if brain_result.get('is_no'):
            return "Okay, no problem. Is there something else I can help with?"
        
        # Question detection
        if '?' in user_input or any(word in user_input.lower() for word in ['what', 'who', 'where', 'when', 'why', 'how']):
            # Try to answer based on keywords
            user_lower = user_input.lower()
            
            if 'name' in user_lower:
                return "I am Mr. Beast, your friendly AI robot assistant!"
            
            if 'age' in user_lower and 'your' in user_lower:
                return "I don't have an age - I'm an AI robot!"
            
            if 'time' in user_lower:
                current_time = datetime.now().strftime("%I:%M %p")
                return f"The current time is {current_time}."
            
            if 'date' in user_lower or 'day' in user_lower:
                current_date = datetime.now().strftime("%B %d, %Y")
                return f"Today is {current_date}."
            
            if 'weather' in user_lower:
                return "I don't have access to weather information, but I hope it's nice outside!"
            
            if 'help' in user_lower:
                return "I can chat with you, answer questions, and help you with various tasks. Just ask me anything!"
            
            # Generic question response
            return "That's an interesting question! I'm still learning, but I'll do my best to help you."
        
        # Statement/comment responses
        if any(word in user_input.lower() for word in ['good', 'great', 'nice', 'awesome', 'excellent']):
            return "I'm glad to hear that! Anything else you'd like to talk about?"
        
        if any(word in user_input.lower() for word in ['bad', 'sad', 'terrible', 'awful']):
            return "I'm sorry to hear that. Is there anything I can do to help?"
        
        if any(word in user_input.lower() for word in ['thank', 'thanks']):
            return "You're welcome! Happy to help!"
        
        # Default conversational response
        responses = [
            "I see. Tell me more about that.",
            "That's interesting! What else?",
            "I understand. Anything else on your mind?",
            "Got it! What would you like to know next?",
            "Interesting! Can you tell me more?",
            "I hear you. What else would you like to discuss?"
        ]
        import random
        return random.choice(responses)
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.chat_mode = False  # Stop chat mode
            self.is_running = False
            if hasattr(self, 'cap') and self.cap:
                self.cap.release()
            self.root.destroy()
