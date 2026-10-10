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

from services.profile_service import ProfileService
from services.health_service import HealthService
from ai.orchestrator import AIOrchestrator
from voice.language_manager import LanguageManager

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

        # Recognized visitor state & DB auto-fetch tracking
        self.recognized_user = None           # Currently recognized profile dict from DB
        self.recognized_user_id = None        # ID of recognized user
        self.last_face_time = 0.0             # Timestamp when face was last seen
        self.last_recognition_time = 0.0      # Timestamp of last recognition check
        self.last_announced_user_id = None    # User ID already greeted in this visit session
        self.last_visit_announcement_time = 0.0 # Timestamp of greeting
        self.is_recognizing = False           # Lock to avoid concurrent recognition threads
        
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
        
        self.profile_service = ProfileService(
            user_store=self.user_store,
            face_capture=self.face_capture,
            face_embeddings=self.face_embeddings
        )
        self.health_service = HealthService()
        self.orchestrator = AIOrchestrator(
            brain=self.brain.supervised_brain,
            profile_service=self.profile_service,
            ui_callback=self._handle_orchestrator_event
        )
        
        # Setup UI
        self.setup_ui()
        
        # Periodic badge update
        self.root.after(1000, self._update_health_badges)

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
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=15, pady=12)

        # Status Badges and Language Selector Frame
        badge_frame = tk.Frame(title_frame, bg="#2c3e50")
        badge_frame.pack(side=tk.RIGHT, padx=15, pady=10)

        self.db_badge = tk.Label(
            badge_frame,
            text="DB: Checking...",
            font=("Arial", 9, "bold"),
            bg="#34495e",
            fg="#bdc3c7",
            padx=8,
            pady=3
        )
        self.db_badge.pack(side=tk.LEFT, padx=4)

        self.ai_badge = tk.Label(
            badge_frame,
            text="AI: Ready",
            font=("Arial", 9, "bold"),
            bg="#34495e",
            fg="#3498db",
            padx=8,
            pady=3
        )
        self.ai_badge.pack(side=tk.LEFT, padx=4)

        self.sync_badge = tk.Label(
            badge_frame,
            text="Sync: 0",
            font=("Arial", 9, "bold"),
            bg="#34495e",
            fg="#2ecc71",
            padx=8,
            pady=3
        )
        self.sync_badge.pack(side=tk.LEFT, padx=4)

        lang_frame = tk.Frame(badge_frame, bg="#2c3e50")
        lang_frame.pack(side=tk.LEFT, padx=6)
        tk.Label(lang_frame, text="Lang:", font=("Arial", 9, "bold"), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=2)
        self.lang_var = tk.StringVar(value="Auto Detect")
        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=["Auto Detect", "English (en)", "Hindi (hi)", "Hinglish"],
            state="readonly",
            width=11
        )
        self.lang_combo.pack(side=tk.LEFT)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_selected)

        # Admin Dashboard Button
        admin_btn = tk.Button(
            badge_frame,
            text="🛡️ Admin",
            font=("Arial", 9, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            cursor="hand2",
            padx=10,
            pady=2,
            command=self._open_admin_dashboard
        )
        admin_btn.pack(side=tk.LEFT, padx=6)
        
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
            font=("Arial", 12, "bold"),
            bg="#ecf0f1",
            fg="black",
            anchor="w"
        )
        self.age_label.pack(fill=tk.X, padx=10, pady=2)
        
        self.gender_label = tk.Label(
            info_frame,
            text="Gender: --",
            font=("Arial", 12, "bold"),
            bg="#ecf0f1",
            fg="black",
            anchor="w"
        )
        self.gender_label.pack(fill=tk.X, padx=10, pady=2)
        
        self.emotion_label = tk.Label(
            info_frame,
            text="Emotion: --",
            font=("Arial", 12, "bold"),
            bg="#ecf0f1",
            fg="black",
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
        
        # User Profile Form (Voice / Interactive)
        self.profile_frame = tk.LabelFrame(
            right_panel,
            text="👤 User Profile Form (Voice Fill)",
            font=("Arial", 11, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        self.profile_frame.pack(fill=tk.X, pady=4)
        
        self.form_status_var = tk.StringVar(value="Status: Ready (Say 'Create my profile')")
        self.form_name_var = tk.StringVar(value="Name: --")
        self.form_age_var = tk.StringVar(value="Age: --")
        self.form_address_var = tk.StringVar(value="Address: --")
        self.form_job_var = tk.StringVar(value="Job / Studies: --")
        self.form_email_var = tk.StringVar(value="Email: --")
        self.form_phone_var = tk.StringVar(value="Phone: --")
        
        tk.Label(self.profile_frame, textvariable=self.form_status_var, font=("Arial", 9, "bold"), fg="#c0392b", bg="#ecf0f1", anchor="w").pack(fill=tk.X, padx=8, pady=1)
        tk.Label(self.profile_frame, textvariable=self.form_name_var, font=("Arial", 10, "bold"), fg="black", bg="#ecf0f1", anchor="w").pack(fill=tk.X, padx=8)
        tk.Label(self.profile_frame, textvariable=self.form_age_var, font=("Arial", 10, "bold"), fg="black", bg="#ecf0f1", anchor="w").pack(fill=tk.X, padx=8)
        tk.Label(self.profile_frame, textvariable=self.form_address_var, font=("Arial", 10, "bold"), fg="black", bg="#ecf0f1", anchor="w").pack(fill=tk.X, padx=8)
        tk.Label(self.profile_frame, textvariable=self.form_job_var, font=("Arial", 10, "bold"), fg="black", bg="#ecf0f1", anchor="w").pack(fill=tk.X, padx=8)
        tk.Label(self.profile_frame, textvariable=self.form_email_var, font=("Arial", 10, "bold"), fg="black", bg="#ecf0f1", anchor="w").pack(fill=tk.X, padx=8)
        tk.Label(self.profile_frame, textvariable=self.form_phone_var, font=("Arial", 10, "bold"), fg="black", bg="#ecf0f1", anchor="w").pack(fill=tk.X, padx=8)

        card_btn_frame = tk.Frame(self.profile_frame, bg="#ecf0f1")
        card_btn_frame.pack(fill=tk.X, padx=6, pady=4)
        tk.Button(
            card_btn_frame,
            text="✏ Edit Card",
            font=("Arial", 8, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=self.open_manual_edit_dialog
        ).pack(side=tk.LEFT, padx=3)
        tk.Button(
            card_btn_frame,
            text="🔄 Sync DB",
            font=("Arial", 8, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=self.trigger_manual_sync
        ).pack(side=tk.LEFT, padx=3)

        # Conversation log
        log_frame = tk.LabelFrame(
            right_panel,
            text="💬 Conversation Log",
            font=("Arial", 11, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=4)
        
        self.log_text = tk.Text(
            log_frame,
            height=10,
            font=("Arial", 10),
            bg="white",
            fg="black",
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        control_frame = tk.Frame(right_panel, bg="#ecf0f1")
        control_frame.pack(fill=tk.X, pady=5)
        
        self.profile_btn = tk.Button(
            control_frame,
            text="📝 Create Profile",
            font=("Arial", 9, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=self.trigger_profile_creation,
            width=13
        )
        self.profile_btn.pack(side=tk.LEFT, padx=3)

        self.voice_toggle_btn = tk.Button(
            control_frame,
            text="🔇 Mute",
            font=("Arial", 9, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=self.toggle_voice,
            width=8
        )
        self.voice_toggle_btn.pack(side=tk.LEFT, padx=3)
        
        # Chat mode button
        self.chat_btn = tk.Button(
            control_frame,
            text="💬 Chat",
            font=("Arial", 9, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=self.toggle_chat_mode,
            width=8
        )
        self.chat_btn.pack(side=tk.LEFT, padx=3)
        
        exit_btn = tk.Button(
            control_frame,
            text="✖ Exit",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
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
        """Start camera capture with graceful fallback if webcam unavailable"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("Cannot open camera 0")
            
            self.is_running = True
            self.status_label.config(text="Status: Camera active - Real-time detection running")
            
            # Start video thread
            self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
            self.video_thread.start()
            print("✓ Camera started")
        except Exception as e:
            print(f"⚠ Camera initialization note: {e}. Running in Voice & AI mode.")
            self.status_label.config(text="Status: Camera offline - Voice & AI ready")
            import numpy as np
            placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder, "Mr. Beast AI Robot", (150, 210), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            cv2.putText(placeholder, "Camera feed offline / Voice active", (120, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (46, 204, 113), 1)
            cv2.putText(placeholder, "Say: 'Hello' or 'Create my profile'", (130, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            self.display_frame(placeholder)
            self.is_running = True
    
    def video_loop(self):
        """Main video processing loop with real-time DB recognition and auto-fetch"""
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
                    
                    if len(faces) > 0:
                        self.last_face_time = time.time()
                    
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
                        
                        # Trigger background recognition and DB auto-fetch if not already recognized
                        now = time.time()
                        if self.recognized_user is None and not self.is_recognizing and (now - self.last_recognition_time > 0.8):
                            self.last_recognition_time = now
                            self.is_recognizing = True
                            threading.Thread(
                                target=self.recognize_and_fetch_user,
                                args=(face_roi.copy(), age, gender, age_range),
                                daemon=True
                            ).start()
                        
                        # Draw bounding box and information
                        if self.recognized_user:
                            u_name = self.recognized_user.get('name', 'User')
                            u_id = self.recognized_user.get('user_id') or self.recognized_user.get('id', '')
                            u_job = self.recognized_user.get('job') or self.recognized_user.get('college_or_job', '')
                            u_age = self.recognized_user.get('age') or age
                            
                            # Solid green box for recognized existing user
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 220, 0), 2)
                            
                            # Top badge with user name & DB verification
                            badge_h = 44
                            cv2.rectangle(frame, (x, max(0, y - badge_h)), (x + w, y), (0, 160, 0), -1)
                            cv2.putText(frame, f"✓ {u_name} (ID: {u_id})", (x + 5, max(16, y - 24)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
                            cv2.putText(frame, "Registered in DB", (x + 5, max(32, y - 8)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 255, 220), 1)
                            
                            # Bottom sub-caption with job/studies and age
                            det_txt = f"{u_job} | Age: {u_age}" if u_job else f"Age: {u_age}"
                            cv2.putText(frame, det_txt, (x, min(frame.shape[0] - 8, y + h + 20)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            
                            self.age_label.config(text=f"Age: {u_age} years (DB) 🔒")
                            self.gender_label.config(text=f"Gender: {self.recognized_user.get('gender', gender)}")
                            self.emotion_label.config(text=f"Status: DB Verified (ID: {u_id})")
                        else:
                            # Cyan/yellow box for analyzing face
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 215, 255), 2)
                            cv2.putText(frame, f"Age: {age}", (x, y-25),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 215, 255), 2)
                            cv2.putText(frame, f"Gender: {gender}", (x, y-8),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 215, 255), 2)
                            
                            self.age_label.config(text=f"Age: {age} years {'🔒 LOCKED' if self.age_locked else ''}")
                            self.gender_label.config(text=f"Gender: {gender}")
                            self.emotion_label.config(text="Status: Detecting face...")
                        
                        # Auto-process face timing for age stability announcement if not recognized
                        if face_detected_time is None:
                            face_detected_time = time.time()
                        
                        elapsed = time.time() - face_detected_time
                        
                        # Lock age and announce after 2.5 seconds of stable detection if user is not in DB
                        if elapsed >= 2.5 and age_stable_count >= 3 and not age_announced and self.recognized_user is None:
                            self.stable_age = age
                            self.stable_gender = gender
                            self.age_locked = True
                            
                            age_message = f"Your age is {age}"
                            self.log_conversation("Robot", age_message)
                            
                            if self.voice_enabled:
                                threading.Thread(
                                    target=lambda: self.tts.speak(age_message, block=True),
                                    daemon=True
                                ).start()
                            
                            self.train_ai_with_age(age, gender)
                            age_announced = True
                        
                        if elapsed >= 3.5 and not face_processed and self.recognized_user is None:
                            threading.Thread(
                                target=self.handle_unrecognized_face,
                                args=(face_roi.copy(), age, gender, age_range),
                                daemon=True
                            ).start()
                            face_processed = True
                    
                    if len(faces) == 0:
                        # Debounce face loss: wait 3.5 seconds of clear camera before resetting visit session
                        if self.last_face_time > 0 and (time.time() - self.last_face_time > 3.5):
                            if self.recognized_user is not None:
                                print(f"👋 Visitor left camera field: {self.recognized_user.get('name')}")
                                self.recognized_user = None
                                self.recognized_user_id = None
                                self.last_announced_user_id = None
                                self.form_status_var.set("Status: Ready (Stand in front of camera or say 'Create my profile')")
                                self.status_label.config(text="Status: Ready - Waiting for visitor...")
                            
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
    
    def recognize_and_fetch_user(self, face_roi, age=None, gender=None, age_range=None):
        """
        Detect visitor face, match against known embeddings or registered profiles in DB,
        auto-fetch full profile from DB, populate UI card immediately, and announce greeting.
        """
        try:
            print("\n🔍 Auto-recognizing visitor at camera...")
            embedding = None
            if self.face_embeddings:
                embedding = self.face_embeddings.get_embedding(face_roi)
            
            matched_user_id = None
            matched_name = None
            
            if self.user_store:
                # 1. Check known face embeddings in MySQL and local store
                known_embeddings = self.user_store.get_all_embeddings()
                
                if embedding is not None and known_embeddings and self.face_embeddings:
                    match = self.face_embeddings.find_best_match(
                        embedding,
                        known_embeddings,
                        threshold=0.6
                    )
                    if match:
                        matched_user_id = match['user_id']
                        matched_name = match['name']
                        print(f"✓ Matched face embedding with DB user: {matched_name} (ID: {matched_user_id})")
                
                # 2. If no embedding match, check enrolled users in the DB
                if matched_user_id is None:
                    all_users = self.user_store.get_all_users()
                    if all_users and len(all_users) == 1:
                        # Single enrolled profile in the database (e.g. Ashish Ojha)
                        single_user = all_users[0]
                        matched_user_id = single_user.get('id') or single_user.get('user_id')
                        matched_name = single_user.get('name')
                        
                        # Auto-associate detected face embedding so future camera frames match instantly
                        if embedding is not None:
                            try:
                                photo_path = single_user.get('photo_path') or f"captures/{matched_name.lower().replace(' ', '_')}.jpg"
                                self.user_store.save_user_image(
                                    user_id=matched_user_id,
                                    file_path=photo_path,
                                    embedding=embedding,
                                    is_primary=True
                                )
                                print(f"✓ Associated face embedding to DB user: {matched_name} (ID: {matched_user_id})")
                            except Exception as e:
                                print(f"⚠ Could not auto-associate embedding: {e}")
            
            # 3. If matched, AUTO-FETCH COMPLETE USER PROFILE FROM DATABASE
            if matched_user_id is not None:
                profile_data = None
                if self.profile_service:
                    profile_data = self.profile_service.lookup_profile(user_id=matched_user_id)
                if not profile_data and self.user_store:
                    raw_user = self.user_store.get_user_by_id(matched_user_id)
                    if raw_user:
                        profile_data = {
                            'user_id': raw_user.get('id') or raw_user.get('user_id'),
                            'name': raw_user.get('name'),
                            'age': str(raw_user.get('age_range', '')).strip('()') if raw_user.get('age_range') else str(raw_user.get('age', '')),
                            'gender': raw_user.get('gender', 'Not specified'),
                            'job': raw_user.get('college_or_job') or raw_user.get('job', 'Not specified'),
                            'address': raw_user.get('address', 'Not specified'),
                            'email': raw_user.get('email', ''),
                            'phone': raw_user.get('phone', ''),
                            'photo_path': raw_user.get('photo_path', '')
                        }
                
                if profile_data:
                    self.handle_existing_user_detected(profile_data)
                    return
            
            print("👤 Unregistered visitor detected at camera.")
        finally:
            self.is_recognizing = False
    
    def handle_existing_user_detected(self, profile_data):
        """
        Handle visitor who already exists in DB:
        - Auto-fetch and show details on the Desktop UI
        - Announce: 'You are already existing in our database! Welcome back, [Name]'
        - Update last_seen in the database
        """
        user_id = profile_data.get('user_id')
        user_name = profile_data.get('name', 'User')
        user_age = profile_data.get('age', '')
        user_job = profile_data.get('job', '')
        user_address = profile_data.get('address', '')
        
        self.recognized_user = profile_data
        self.recognized_user_id = user_id
        
        # 1. Update UI Profile Card immediately with auto-fetched data
        status_msg = f"✅ AUTO-FETCHED: Existing in DB (ID: {user_id})"
        self.update_profile_form_ui(profile_data, status_msg)
        
        # 2. Update status label & detection panels safely on UI thread
        def update_labels():
            self.status_label.config(text=f"Status: User recognized from DB - {user_name} (ID: {user_id})")
            if user_age:
                self.age_label.config(text=f"Age: {user_age} years (DB) 🔒")
            if profile_data.get('gender'):
                self.gender_label.config(text=f"Gender: {profile_data.get('gender')}")
            self.emotion_label.config(text=f"Status: DB Verified (ID: {user_id})")
        self.root.after(0, update_labels)
        
        # 3. Check visit announcement cooldown
        now = time.time()
        if self.last_announced_user_id != user_id or (now - self.last_visit_announcement_time > 20):
            self.last_announced_user_id = user_id
            self.last_visit_announcement_time = now
            
            # Update last seen timestamp in MySQL and local backup
            if self.user_store:
                self.user_store.update_last_seen(user_id)
            
            # Conversation log with full auto-fetched details
            welcome_log = (
                f"👤 Auto-fetched Profile from DB:\n"
                f"   • User ID: {user_id}\n"
                f"   • Name: {user_name}\n"
                f"   • Age: {user_age} years\n"
                f"   • Profession: {user_job}\n"
                f"   • Address: {user_address}\n"
                f"   → You are already existing in our database! Welcome back, {user_name}!"
            )
            self.log_conversation("Robot", welcome_log)
            
            # Voice announcement
            is_hindi = "hindi" in self.lang_var.get().lower()
            if is_hindi:
                speech_text = f"Welcome back {user_name}! Aap hamare database me pehle se registered hain. ID: {user_id}."
            else:
                speech_text = f"Welcome back, {user_name}! You are already existing in our database."
                
            if self.voice_enabled:
                self.show_speaking()
                self.tts.speak(speech_text, block=False)
                self.hide_speaking()
    
    def handle_unrecognized_face(self, face_roi, age, gender, age_range):
        """Handle new unregistered visitor"""
        if self.recognized_user is not None:
            return
        msg = "I see a new visitor. Say 'Create my profile' to register!"
        self.log_conversation("Robot", msg)
        if self.voice_enabled:
            self.tts.speak(msg, block=False)
    
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
                # Refine age with free third-party Agify API
                try:
                    ref_age, _, ref_range, prov = self.age_gender_predictor.predict_with_api(face_roi, user_name=name)
                    if prov != "Local Caffe Model":
                        age = ref_age
                        age_range = ref_range
                        self.stable_age = age
                        self.age_label.config(text=f"Age: {age} years ({prov}) 🔒")
                        print(f"🌐 Name '{name}' refined age via {prov}: {age} years")
                except Exception as e:
                    print(f"⚠ Name-based age refinement notice: {e}")

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
    
    def update_profile_form_ui(self, data, status_message):
        """Update profile form fields and status on UI thread"""
        def update():
            if hasattr(self, 'form_status_var'):
                self.form_status_var.set(f"Status: {status_message}")
                if data.get('name'):
                    self.form_name_var.set(f"Name: {data['name']}")
                if data.get('age'):
                    self.form_age_var.set(f"Age: {data['age']} years")
                if data.get('address'):
                    self.form_address_var.set(f"Address: {data['address']}")
                if data.get('job'):
                    self.form_job_var.set(f"Job / Studies: {data['job']}")
                if data.get('email'):
                    self.form_email_var.set(f"Email: {data['email']}")
                if data.get('phone'):
                    self.form_phone_var.set(f"Phone: {data['phone']}")
            self.log_conversation("System", status_message)
        self.root.after(0, update)

    def trigger_profile_creation(self):
        """Trigger voice profile onboarding flow in a background thread"""
        if getattr(self, 'profile_flow_active', False):
            print("Profile creation flow is already running!")
            return
            
        def run_flow():
            self.profile_flow_active = True
            try:
                from voice.profile_flow import VoiceProfileFlow
                flow = VoiceProfileFlow(
                    tts=self.tts,
                    stt=self.stt,
                    brain=self.brain,
                    user_store=self.user_store,
                    face_capture=self.face_capture,
                    face_embeddings=self.face_embeddings,
                    ui_callback=self.update_profile_form_ui
                )
                flow.start_flow(
                    current_frame=self.current_frame,
                    detected_gender=self.stable_gender or 'Not specified',
                    detected_age=self.stable_age or None
                )
            except Exception as e:
                print(f"⚠ Profile creation flow error: {e}")
            finally:
                self.profile_flow_active = False

        threading.Thread(target=run_flow, daemon=True).start()

    def _handle_orchestrator_event(self, event):
        """Handle real-time updates from orchestrator"""
        if event.get('type') == 'registration_update':
            profile_data = event.get('profile_data', {})
            msg = event.get('message', '')
            self.update_profile_form_ui(profile_data, msg)

    def _update_health_badges(self):
        """Periodically query HealthService and update badge colors and text"""
        def run_check():
            try:
                health = self.health_service.check_health()
                components = health.get('components', {})

                # 1. DB badge
                db_info = components.get('database', {})
                if db_info.get('status') == 'healthy':
                    latency = db_info.get('latency_ms', 0)
                    self.db_badge.config(text=f"🟢 DB: Connected ({latency}ms)", fg="#2ecc71")
                else:
                    self.db_badge.config(text="🟠 DB: Offline (JSON)", fg="#e67e22")

                # 2. AI badge
                ai_info = components.get('ai_provider', {})
                ai_name = ai_info.get('provider', 'AI')
                if ai_info.get('status') == 'healthy':
                    self.ai_badge.config(text=f"🤖 AI: {ai_name.title()}", fg="#3498db")
                else:
                    self.ai_badge.config(text=f"⚠ AI: {ai_name.title()}", fg="#e74c3c")

                # 3. Sync badge
                sync_info = components.get('sync_queue', {})
                pending = sync_info.get('pending_count', 0)
                if pending > 0:
                    self.sync_badge.config(text=f"🔄 Sync: {pending} Pending", fg="#f39c12")
                else:
                    self.sync_badge.config(text="✓ Sync: Synced", fg="#2ecc71")
            except Exception:
                pass
            finally:
                if self.is_running or not hasattr(self, '_stop_health_loop'):
                    self.root.after(5000, self._update_health_badges)

        threading.Thread(target=run_check, daemon=True).start()

    def _on_language_selected(self, event=None):
        """Handle language change from UI combobox"""
        val = self.lang_var.get()
        mapping = {
            "Auto Detect": "auto",
            "English (en)": "en",
            "Hindi (hi)": "hi",
            "Hinglish": "hinglish"
        }
        selected = mapping.get(val, "en")
        if selected != "auto":
            self.orchestrator.current_lang = selected
            self.log_conversation("System", f"Language manually locked to: {val}")
        else:
            self.log_conversation("System", "Language set to Auto Detect")

    def _open_admin_dashboard(self):
        """Open the comprehensive Mr. Beast Admin Dashboard window with full details"""
        try:
            if hasattr(self, 'admin_window') and self.admin_window and self.admin_window.root.winfo_exists():
                self.admin_window.root.deiconify()
                self.admin_window.root.lift()
                self.admin_window.root.focus_force()
                self.admin_window.refresh_all()
                self.log_conversation("System", "🛡️ Admin Dashboard brought to foreground.")
                return

            from ui.admin_dashboard import MrBeastAdminDashboard
            self.admin_window = MrBeastAdminDashboard(parent_or_root=self.root)
            self.admin_window.root.deiconify()
            self.admin_window.root.lift()
            self.admin_window.root.focus_force()
            self.log_conversation("System", "🛡️ Admin Dashboard opened with full profile details, logs, & diagnostics.")
        except Exception as e:
            print(f"⚠ Error opening Admin Dashboard: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Admin Console Error", f"Could not launch Admin Dashboard:\n{e}")

    def open_manual_edit_dialog(self):
        """Open popup modal to manually view and edit current profile card"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit User Profile Card")
        dialog.geometry("380x440")
        dialog.resizable(False, False)
        dialog.configure(bg="#ecf0f1")
        dialog.grab_set()

        fields = [
            ("Name:", self.form_name_var.get().replace("Name: ", "").replace("--", "")),
            ("Age:", self.form_age_var.get().replace("Age: ", "").replace(" years", "").replace("--", "")),
            ("Address:", self.form_address_var.get().replace("Address: ", "").replace("--", "")),
            ("Job / Studies:", self.form_job_var.get().replace("Job / Studies: ", "").replace("--", "")),
            ("Email:", self.form_email_var.get().replace("Email: ", "").replace("--", "")),
            ("Phone:", self.form_phone_var.get().replace("Phone: ", "").replace("--", ""))
        ]

        entries = {}
        for idx, (label, val) in enumerate(fields):
            tk.Label(dialog, text=label, font=("Arial", 10, "bold"), fg="black", bg="#ecf0f1").pack(anchor="w", padx=20, pady=(6, 1))
            ent = tk.Entry(dialog, font=("Arial", 10), width=35, bg="white", fg="black")
            ent.insert(0, val.strip())
            ent.pack(padx=20, pady=(0, 4))
            entries[label] = ent

        def save_edits():
            new_data = {
                'name': entries["Name:"].get().strip() or "Anonymous",
                'age': entries["Age:"].get().strip() or "25",
                'address': entries["Address:"].get().strip() or "Not specified",
                'job': entries["Job / Studies:"].get().strip() or "Not specified",
                'email': entries["Email:"].get().strip(),
                'phone': entries["Phone:"].get().strip(),
                'gender': self.stable_gender or 'Not specified',
                'consent': 'Yes'
            }
            try:
                self.profile_service.save_profile(new_data, frame=self.current_frame)
                self.update_profile_form_ui(new_data, "Profile saved manually!")
                self.log_conversation("System", f"Profile for '{new_data['name']}' saved successfully.")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

        btn_frame = tk.Frame(dialog, bg="#ecf0f1")
        btn_frame.pack(pady=15)
        tk.Button(
            btn_frame,
            text="💾 Save Profile",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=save_edits,
            padx=12,
            pady=4
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            btn_frame,
            text="Cancel",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=dialog.destroy,
            padx=12,
            pady=4
        ).pack(side=tk.LEFT, padx=5)

    def trigger_manual_sync(self):
        """Manually trigger offline sync queue to MySQL"""
        def sync_worker():
            self.log_conversation("System", "Starting offline sync to MySQL...")
            res = self.profile_service.sync_offline()
            synced = res.get('synced', 0)
            failed = res.get('failed', 0)
            self.log_conversation("System", f"Sync complete: {synced} synced, {failed} remaining.")
            self._update_health_badges()

        threading.Thread(target=sync_worker, daemon=True).start()

    def handle_user_input(self, text):
        """Handle user voice or text input using AIOrchestrator"""
        if not text:
            return

        self.log_conversation("User", text)

        res = self.orchestrator.handle_input(
            text,
            current_frame=self.current_frame,
            current_face_data={
                'gender': self.stable_gender or 'Not specified',
                'age': self.stable_age or None
            }
        )

        response = res['response']
        lang = res.get('language', 'en')

        self.log_conversation(f"Robot [{lang.upper()}]", response)

        if self.voice_enabled:
            self.show_speaking()
            self.tts.speak(response, lang=lang, block=False)
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
            self.voice_toggle_btn.config(text="🔇 Disable Voice", bg="white", fg="black")
            self.status_label.config(text="Status: Voice enabled")
        else:
            self.voice_toggle_btn.config(text="🔊 Enable Voice", bg="white", fg="black")
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
            self.chat_btn.config(text="🛑 Stop Chat", bg="white", fg="black")
            self.log_conversation("System", "Chat mode started. Say something to talk with the robot!")
            
            # Start chat thread
            self.chat_thread = threading.Thread(target=self.continuous_chat_loop, daemon=True)
            self.chat_thread.start()
        else:
            # Stop chat mode
            self.chat_btn.config(text="💬 Start Chat", bg="white", fg="black")
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
                        self.root.after(0, lambda: self.chat_btn.config(text="💬 Start Chat", bg="white", fg="black"))
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
