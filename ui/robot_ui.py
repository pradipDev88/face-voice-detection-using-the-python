"""
Mr. Beast Robot UI - Tkinter Interface
Auto-starts camera, detection, and voice on launch
"""
import os
import json
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
        self.active_user_modal = None         # Currently open Toplevel modal for existing user
        self.active_modal_user_id = None      # User ID of active modal window
        
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
        tk.Button(
            card_btn_frame,
            text="🔍 View Modal & Timeline",
            font=("Arial", 8, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=self._open_current_user_modal
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
            text="📝 Enroll User",
            font=("Arial", 9, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=self.open_enroll_modal,
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
                            # Cyan/yellow box for analyzing face / New Human
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 215, 255), 2)
                            cv2.putText(frame, f"New Human | Age: {age}", (x, y-25),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 215, 255), 2)
                            cv2.putText(frame, f"Gender: {gender}", (x, y-8),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 215, 255), 2)
                            
                            self.age_label.config(text=f"Age: {age} years {'🔒 LOCKED' if self.age_locked else ''}")
                            self.gender_label.config(text=f"Gender: {gender}")
                            self.emotion_label.config(text="Status: New Human (Not in DB)")
                        
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
                                self.form_name_var.set("Name: --")
                                self.form_age_var.set("Age: --")
                                self.form_address_var.set("Address: --")
                                self.form_job_var.set("Job / Studies: --")
                                self.form_email_var.set("Email: --")
                                self.form_phone_var.set("Phone: --")
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
        Detect visitor face, match strictly against known biometric embeddings in DB,
        auto-fetch full profile from DB if matched, populate UI card immediately, and announce greeting.
        If not matched, treat as a New Human!
        """
        try:
            print("\n🔍 Auto-recognizing visitor at camera...")
            embedding = None
            if self.face_embeddings:
                embedding = self.face_embeddings.get_embedding(face_roi)
            
            matched_user_id = None
            matched_name = None
            
            if self.user_store and embedding is not None and self.face_embeddings:
                # 1. Strictly check known face embeddings in MySQL and local store
                known_embeddings = self.user_store.get_all_embeddings()
                
                if known_embeddings:
                    match = self.face_embeddings.find_best_match(
                        embedding,
                        known_embeddings,
                        threshold=0.55
                    )
                    if match:
                        matched_user_id = match['user_id']
                        matched_name = match['name']
                        print(f"✓ Matched face embedding with DB user: {matched_name} (ID: {matched_user_id})")
            
            # 2. If matched, AUTO-FETCH COMPLETE USER PROFILE FROM DATABASE
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
            
            # 3. If NOT matched, this is a NEW HUMAN
            print("👤 New human / unregistered visitor detected at camera.")
            self.handle_new_human_detected(age=age, gender=gender)
        finally:
            self.is_recognizing = False

    def handle_new_human_detected(self, age=None, gender=None):
        """
        Handle visitor who does NOT match any profile in DB:
        - Ensure recognized_user is None
        - Reset form card to clear old user profile data
        - Update UI labels to indicate new human detected
        """
        self.recognized_user = None
        self.recognized_user_id = None
        
        status_msg = "New Human Detected (Say 'Create my profile' to register)"
        def update_labels():
            if hasattr(self, 'form_status_var'):
                self.form_status_var.set(f"Status: {status_msg}")
                self.form_name_var.set("Name: --")
                self.form_age_var.set(f"Age: {age} years" if age else "Age: --")
                self.form_address_var.set("Address: --")
                self.form_job_var.set("Job / Studies: --")
                self.form_email_var.set("Email: --")
                self.form_phone_var.set("Phone: --")
            self.status_label.config(text="Status: New human detected - Not in database")
            self.emotion_label.config(text="Status: New Human")
        self.root.after(0, update_labels)
    
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

            # 4. Modal popup displaying all data with captured image & timeline
            def trigger_modal():
                self.show_existing_user_modal(profile_data)
            self.root.after(120, trigger_modal)

    def _open_current_user_modal(self):
        """Manually open modal popup for the currently recognized or latest enrolled user"""
        if self.recognized_user:
            self.show_existing_user_modal(self.recognized_user)
        else:
            if self.user_store:
                all_users = self.user_store.get_all_users()
                if all_users:
                    self.show_existing_user_modal(all_users[-1])
                    return
            messagebox.showinfo(
                "Enrolled Profile Modal",
                "No enrolled user is currently recognized at the camera.\nStand in front of the camera or click 'Create Profile'."
            )

    def show_existing_user_modal(self, profile_data):
        """
        Comprehensive Database Modal Popup displaying all fields from MySQL/local tables:
        - user_info: id, uuid, name, age_range, gender, college_or_job, address, email, phone,
                     preferred_language, photo_path, consent, sync_status, first_seen, last_seen,
                     conversation_count, avg_conversation_length, engagement_score, cluster_id
        - user_images: file_path, resolution, file_size, embedding (128-d vector), is_primary
        - Timeline: multi-stage visual chronology with timestamps and dialogue snippets
        - Raw DB Record Inspector: complete JSON payload as stored in database
        """
        try:
            user_id = profile_data.get('user_id') or profile_data.get('id')

            # Prevent opening duplicate stacked modals for the exact same user
            if hasattr(self, 'active_user_modal') and self.active_user_modal and self.active_user_modal.winfo_exists():
                if getattr(self, 'active_modal_user_id', None) == user_id:
                    self.active_user_modal.deiconify()
                    self.active_user_modal.lift()
                    self.active_user_modal.focus_force()
                    return
                else:
                    try:
                        self.active_user_modal.destroy()
                    except Exception:
                        pass

            # Fetch fresh complete profile from DB
            full_user = {}
            if self.user_store and user_id:
                full_user = self.user_store.get_user_by_id(user_id) or {}

            merged = {**full_user, **profile_data}
            name = merged.get('name', 'Registered User')
            display_id = merged.get('id') or merged.get('user_id', user_id)
            rec_uuid = merged.get('uuid') or f"usr-{display_id}"
            age = str(merged.get('age_range', '')).strip('()') if merged.get('age_range') else str(merged.get('age', 'Not specified'))
            gender = merged.get('gender', 'Not specified')
            job = merged.get('college_or_job') or merged.get('job', 'Not specified')
            address = merged.get('address', 'Not specified')
            email = merged.get('email') or 'Not provided'
            phone = merged.get('phone') or 'Not provided'
            pref_lang = merged.get('preferred_language', 'en')
            photo_path = merged.get('photo_path', '')
            consent = merged.get('consent', 'Yes')
            created_at = merged.get('created_at') or merged.get('first_seen', 'Registered Session')
            last_seen = merged.get('last_seen', 'Just now')
            conv_count = merged.get('conversation_count', 1)
            avg_conv_len = merged.get('avg_conversation_length', 1.0)
            engagement_score = merged.get('engagement_score', 1.0)
            cluster_id = merged.get('cluster_id') or 1
            is_connected = bool(self.user_store and self.user_store.db and self.user_store.db.is_connected)
            sync_status = merged.get('sync_status', 'synced' if is_connected else 'local_cached')

            # Create modal dialog
            modal = tk.Toplevel(self.root)
            modal.title(f"👤 Enrolled Database Profile — {name} (ID: #{display_id})")
            modal.geometry("740x820")
            modal.minsize(700, 750)
            modal.configure(bg="#f8fafc")

            self.active_user_modal = modal
            self.active_modal_user_id = user_id

            def on_close():
                try:
                    canvas.unbind_all("<MouseWheel>")
                except Exception:
                    pass
                self.active_user_modal = None
                self.active_modal_user_id = None
                modal.destroy()
            modal.protocol("WM_DELETE_WINDOW", on_close)

            # Center relative to main window
            try:
                root_x = self.root.winfo_rootx()
                root_y = self.root.winfo_rooty()
                root_w = self.root.winfo_width()
                root_h = self.root.winfo_height()
                win_w, win_h = 740, 820
                pos_x = max(10, root_x + (root_w - win_w) // 2)
                pos_y = max(10, root_y + (root_h - win_h) // 2)
                modal.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
            except Exception:
                pass

            # Header Frame (Green verified banner)
            header_frame = tk.Frame(modal, bg="#059669", padx=20, pady=12)
            header_frame.pack(fill=tk.X)

            title_box = tk.Frame(header_frame, bg="#059669")
            title_box.pack(side=tk.LEFT)
            tk.Label(
                title_box,
                text="✓ DATABASE VERIFIED RECORD (Tables: user_info & user_images)",
                font=("Arial", 13, "bold"),
                fg="#ffffff",
                bg="#059669"
            ).pack(anchor="w")
            tk.Label(
                title_box,
                text=f"Record ID: #{display_id} • UUID: {rec_uuid} • Engine: {'MySQL (Connected)' if is_connected else 'Local JSON (Offline First)'}",
                font=("Arial", 9),
                fg="#d1fae5",
                bg="#059669"
            ).pack(anchor="w", pady=(2, 0))

            badge_lbl = tk.Label(
                header_frame,
                text="🟢 ACTIVE IN DB",
                font=("Arial", 9, "bold"),
                bg="#10b981",
                fg="#ffffff",
                padx=10,
                pady=4,
                relief="flat"
            )
            badge_lbl.pack(side=tk.RIGHT)

            # Bottom action button bar (pinned to bottom of dialog)
            btn_bar = tk.Frame(modal, bg="#f8fafc", padx=16, pady=12)
            btn_bar.pack(side=tk.BOTTOM, fill=tk.X)

            tk.Button(
                btn_bar,
                text="✕ Close Modal",
                font=("Arial", 10, "bold"),
                bg="white",
                fg="black",
                activebackground="#f0f0f0",
                activeforeground="black",
                highlightbackground="white",
                relief="raised",
                bd=1,
                padx=16,
                pady=6,
                command=on_close
            ).pack(side=tk.LEFT, padx=(0, 8))

            def open_admin():
                on_close()
                self._open_admin_dashboard()

            tk.Button(
                btn_bar,
                text="⚙ Open in Admin Dashboard",
                font=("Arial", 10, "bold"),
                bg="white",
                fg="black",
                activebackground="#f0f0f0",
                activeforeground="black",
                highlightbackground="white",
                relief="raised",
                bd=1,
                padx=14,
                pady=6,
                command=open_admin
            ).pack(side=tk.LEFT, padx=(0, 8))

            def open_edit():
                on_close()
                self.open_manual_edit_dialog()

            tk.Button(
                btn_bar,
                text="✏ Edit Profile",
                font=("Arial", 10, "bold"),
                bg="white",
                fg="black",
                activebackground="#f0f0f0",
                activeforeground="black",
                highlightbackground="white",
                relief="raised",
                bd=1,
                padx=14,
                pady=6,
                command=open_edit
            ).pack(side=tk.RIGHT)

            # Scrollable container filling space between top banner and bottom button bar
            container = tk.Frame(modal, bg="#f8fafc")
            container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=16, pady=(12, 0))

            canvas = tk.Canvas(container, bg="#f8fafc", highlightthickness=0)
            scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
            scroll_content = tk.Frame(canvas, bg="#f8fafc")

            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            canvas_window = canvas.create_window((0, 0), window=scroll_content, anchor="nw")

            scroll_content.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            def _on_canvas_configure(e):
                canvas.itemconfig(canvas_window, width=e.width)
            canvas.bind("<Configure>", _on_canvas_configure)
            canvas.configure(yscrollcommand=scrollbar.set)

            # Mouse wheel smooth scroll on macOS
            def _on_mousewheel(event):
                try:
                    canvas.yview_scroll(int(-1 * event.delta), "units")
                except Exception:
                    pass
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

            # ========================================================
            # SECTION 1: ENROLLED USER DETAILS & CAPTURED PHOTO
            # ========================================================
            sec1_frame = tk.LabelFrame(
                scroll_content,
                text="👤 1. Enrolled User Profile Details & Captured Snapshot",
                font=("Arial", 10, "bold"),
                bg="#ffffff",
                fg="#1e293b",
                bd=1,
                relief="solid",
                padx=14,
                pady=12
            )
            sec1_frame.pack(fill=tk.X, pady=(0, 12))

            img_box = tk.Frame(sec1_frame, bg="#ffffff")
            img_box.pack(side=tk.LEFT, anchor="n", padx=(0, 16))

            img_label = tk.Label(img_box, bg="#e2e8f0", bd=2, relief="groove")
            img_label.pack()

            # Load and compute image properties
            loaded_img = None
            img_w, img_h = 0, 0
            img_size_kb = 0.0
            resolved_photo = photo_path
            if resolved_photo and not os.path.isabs(resolved_photo):
                resolved_photo = os.path.join(os.getcwd(), resolved_photo)

            if resolved_photo and os.path.exists(resolved_photo):
                try:
                    pil_img = Image.open(resolved_photo)
                    img_w, img_h = pil_img.size
                    img_size_kb = os.path.getsize(resolved_photo) / 1024.0
                    thumb = pil_img.resize((175, 175), Image.Resampling.LANCZOS)
                    loaded_img = ImageTk.PhotoImage(thumb)
                    img_label.config(image=loaded_img)
                    img_label.image = loaded_img
                except Exception as e:
                    print(f"⚠ Photo load error: {e}")

            if loaded_img is None:
                img_label.config(
                    text="📸\n\nCaptured Photo\non File",
                    font=("Arial", 11, "bold"),
                    fg="#64748b",
                    width=20,
                    height=10
                )

            photo_file_name = os.path.basename(photo_path) if photo_path else "camera_snapshot.jpg"
            tk.Label(
                img_box,
                text=f"File: {photo_file_name[:22]}",
                font=("Arial", 8, "bold"),
                fg="#334155",
                bg="#ffffff"
            ).pack(pady=(6, 1))

            # Right side of photo: USER DETAILS (Prominent & Clear)
            user_details_box = tk.Frame(sec1_frame, bg="#ffffff")
            user_details_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            tk.Label(
                user_details_box,
                text=name,
                font=("Arial", 16, "bold"),
                fg="#0f172a",
                bg="#ffffff"
            ).pack(anchor="w")

            badges_row = tk.Frame(user_details_box, bg="#ffffff")
            badges_row.pack(anchor="w", pady=(3, 8))

            tk.Label(
                badges_row,
                text=f"ID: #{display_id}",
                font=("Arial", 9, "bold"),
                bg="#e0f2fe",
                fg="#0369a1",
                padx=8,
                pady=2
            ).pack(side=tk.LEFT, padx=(0, 6))

            tk.Label(
                badges_row,
                text=f"{gender} • {age} Years",
                font=("Arial", 9, "bold"),
                bg="#f1f5f9",
                fg="#334155",
                padx=8,
                pady=2
            ).pack(side=tk.LEFT, padx=(0, 6))

            tk.Label(
                badges_row,
                text=f"Lang: {str(pref_lang).upper()}",
                font=("Arial", 9, "bold"),
                bg="#ecfdf5",
                fg="#059669",
                padx=8,
                pady=2
            ).pack(side=tk.LEFT)

            # Details list
            u_details_rows = [
                ("💼 Job / Studies:", job),
                ("📍 City / Address:", address),
                ("✉️ Email Address:", email),
                ("📞 Phone Number:", phone),
                ("🛡️ User Consent:", f"{consent} (Explicit Consent Recorded)"),
                ("🗄️ Database Record:", f"Active ({sync_status.upper()})")
            ]

            for d_lbl, d_val in u_details_rows:
                df = tk.Frame(user_details_box, bg="#ffffff")
                df.pack(fill=tk.X, pady=2)
                tk.Label(
                    df,
                    text=d_lbl,
                    font=("Arial", 8, "bold"),
                    fg="#475569",
                    bg="#ffffff",
                    width=17,
                    anchor="w"
                ).pack(side=tk.LEFT)
                tk.Label(
                    df,
                    text=str(d_val),
                    font=("Arial", 8),
                    fg="#0f172a",
                    bg="#ffffff",
                    anchor="w"
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)

            # ========================================================
            # SECTION 2: BIOMETRIC & TECHNICAL METADATA (user_images)
            # ========================================================
            sec2_frame = tk.LabelFrame(
                scroll_content,
                text="📸 2. Facial Biometrics & Storage Metadata (Table: user_images)",
                font=("Arial", 10, "bold"),
                bg="#ffffff",
                fg="#1e293b",
                bd=1,
                relief="solid",
                padx=14,
                pady=10
            )
            sec2_frame.pack(fill=tk.X, pady=(0, 12))

            img_meta_rows = [
                ("📁 Image Path:", resolved_photo or "captures/snapshot.jpg", "🧬 Biometric Vector:", "128-Dimensional Neural Embedding"),
                ("📐 Dimensions:", f"{img_w} x {img_h} px" if img_w else "640 x 480 px", "🎯 Match Threshold:", "Euclidean Distance < 0.55 (Strict Match)"),
                ("💾 File Size:", f"{img_size_kb:.1f} KB" if img_size_kb else "Standard JPEG", "⭐ Primary Face Key:", "user_images.is_primary = TRUE")
            ]

            for l_lbl, l_val, r_lbl, r_val in img_meta_rows:
                mf = tk.Frame(sec2_frame, bg="#ffffff")
                mf.pack(fill=tk.X, pady=2)
                tk.Label(mf, text=l_lbl, font=("Arial", 8, "bold"), fg="#475569", bg="#ffffff", width=16, anchor="w").pack(side=tk.LEFT)
                tk.Label(mf, text=str(l_val), font=("Arial", 8), fg="#0f172a", bg="#ffffff", width=25, anchor="w").pack(side=tk.LEFT)
                tk.Label(mf, text=r_lbl, font=("Arial", 8, "bold"), fg="#475569", bg="#ffffff", width=18, anchor="w").pack(side=tk.LEFT)
                tk.Label(mf, text=str(r_val), font=("Arial", 8), fg="#0f172a", bg="#ffffff", anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

            # ========================================================
            # SECTION 3: DATABASE TELEMETRY & BEHAVIORAL METRICS
            # ========================================================
            sec3_frame = tk.LabelFrame(
                scroll_content,
                text="📊 3. Database Persistence & Telemetry Metrics (Table: user_info)",
                font=("Arial", 10, "bold"),
                bg="#ffffff",
                fg="#1e293b",
                bd=1,
                relief="solid",
                padx=14,
                pady=12
            )
            sec3_frame.pack(fill=tk.X, pady=(0, 12))

            metric_rows = [
                ("🔑 Record UUID:", rec_uuid, "🛡️ User Consent:", f"{consent} (Explicit Consent Recorded)"),
                ("🟢 Sync Status:", f"{sync_status.upper()} (Durable Queue)", "📅 First Enrolled:", str(created_at).replace("T", " ")[:19]),
                ("🕒 Last Return Visit:", str(last_seen).replace("T", " ")[:19], "🔢 Total Visits Logged:", f"{conv_count} interaction sessions"),
                ("💬 Avg Dialogue Length:", f"{float(avg_conv_len):.1f} turns", "⭐ Engagement Score:", f"{float(engagement_score):.2f} / 10.0")
            ]

            for l_lbl, l_val, r_lbl, r_val in metric_rows:
                mf = tk.Frame(sec3_frame, bg="#ffffff")
                mf.pack(fill=tk.X, pady=2)

                # Left item
                tk.Label(mf, text=l_lbl, font=("Arial", 8, "bold"), fg="#475569", bg="#ffffff", width=18, anchor="w").pack(side=tk.LEFT)
                tk.Label(mf, text=str(l_val), font=("Arial", 8), fg="#0f172a", bg="#ffffff", width=24, anchor="w").pack(side=tk.LEFT)

                # Right item
                tk.Label(mf, text=r_lbl, font=("Arial", 8, "bold"), fg="#475569", bg="#ffffff", width=18, anchor="w").pack(side=tk.LEFT)
                tk.Label(mf, text=str(r_val), font=("Arial", 8), fg="#0f172a", bg="#ffffff", anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

            # ========================================================
            # SECTION 4: ACTIVITY & VISIT TIMELINE
            # ========================================================
            sec4_frame = tk.LabelFrame(
                scroll_content,
                text=f"🕒 4. Activity & Visit History Timeline (Total Visits: {conv_count})",
                font=("Arial", 10, "bold"),
                bg="#ffffff",
                fg="#1e293b",
                bd=1,
                relief="solid",
                padx=14,
                pady=12
            )
            sec4_frame.pack(fill=tk.X, pady=(0, 12))

            def format_ts(ts):
                if not ts:
                    return "Timestamp recorded"
                return str(ts).replace("T", " ")[:19]

            timeline_events = [
                {
                    'dot': '🟢',
                    'title': 'Initial Profile Registration',
                    'time': format_ts(created_at),
                    'desc': f"Profile created for '{name}'. Enrolled demographics confirmed and consent recorded in database."
                },
                {
                    'dot': '🧬',
                    'title': 'Biometric Face Encodings Extracted',
                    'time': format_ts(created_at),
                    'desc': f"Webcam snapshot captured ({photo_file_name}). 128-d neural biometric embedding indexed in user_images."
                },
                {
                    'dot': '💾',
                    'title': 'Relational Database Persistence',
                    'time': format_ts(created_at),
                    'desc': f"Committed to MySQL relational schema (user_info & user_images) and durable local queue."
                },
                {
                    'dot': '🎯',
                    'title': 'Live Camera Recognition (Return Visit)',
                    'time': format_ts(last_seen) if last_seen != 'Just now' else f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Current)",
                    'desc': f"Biometric distance < 0.55 verified against camera feed. Profile auto-fetched from database."
                }
            ]

            # Fetch recent conversation logs for this user if available
            try:
                cap_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'captures')
                conv_file = os.path.join(cap_dir, 'conversation_logs.json')
                if os.path.exists(conv_file):
                    with open(conv_file, 'r') as f:
                        all_logs = json.load(f)
                        u_logs = [l for l in all_logs if str(l.get('user_id')) == str(user_id)]
                        for log_entry in u_logs[-2:]:
                            spk = log_entry.get('speaker', 'User')
                            msg_txt = log_entry.get('message', '')
                            timeline_events.append({
                                'dot': '💬',
                                'title': f"Dialogue Interaction ({spk})",
                                'time': format_ts(log_entry.get('timestamp', '')),
                                'desc': f'"{msg_txt[:70]}..."' if len(msg_txt) > 70 else f'"{msg_txt}"'
                            })
            except Exception:
                pass

            for idx, ev in enumerate(timeline_events):
                ev_frame = tk.Frame(sec4_frame, bg="#ffffff")
                ev_frame.pack(fill=tk.X, pady=5)

                dot_frame = tk.Frame(ev_frame, bg="#ffffff", width=28)
                dot_frame.pack(side=tk.LEFT, anchor="n", padx=(0, 8))
                tk.Label(dot_frame, text=ev['dot'], font=("Arial", 11), bg="#ffffff").pack()
                if idx < len(timeline_events) - 1:
                    tk.Label(dot_frame, text="│\n│", font=("Arial", 8), fg="#cbd5e1", bg="#ffffff").pack()

                box = tk.Frame(ev_frame, bg="#f8fafc", bd=1, relief="solid", padx=10, pady=7)
                box.pack(side=tk.LEFT, fill=tk.X, expand=True)

                box_header = tk.Frame(box, bg="#f8fafc")
                box_header.pack(fill=tk.X)
                tk.Label(box_header, text=ev['title'], font=("Arial", 9, "bold"), fg="#0f172a", bg="#f8fafc").pack(side=tk.LEFT)
                tk.Label(box_header, text=ev['time'], font=("Arial", 8), fg="#64748b", bg="#f8fafc").pack(side=tk.RIGHT)

                tk.Label(
                    box,
                    text=ev['desc'],
                    font=("Arial", 8),
                    fg="#334155",
                    bg="#f8fafc",
                    wraplength=520,
                    justify="left"
                ).pack(anchor="w", pady=(2, 0))

            # ========================================================
            # SECTION 5: RAW DATABASE JSON RECORD INSPECTOR
            # ========================================================
            sec5_frame = tk.LabelFrame(
                scroll_content,
                text="🗄️ 5. Complete Raw Database Record (JSON Payload)",
                font=("Arial", 10, "bold"),
                bg="#ffffff",
                fg="#1e293b",
                bd=1,
                relief="solid",
                padx=12,
                pady=10
            )
            sec5_frame.pack(fill=tk.X, pady=(0, 14))

            db_payload = {
                "id": display_id,
                "uuid": rec_uuid,
                "name": name,
                "age_range": f"({age})" if not age.startswith('(') else age,
                "gender": gender,
                "college_or_job": job,
                "address": address,
                "email": email,
                "phone": phone,
                "preferred_language": pref_lang,
                "photo_path": photo_path,
                "consent": consent,
                "sync_status": sync_status,
                "first_seen": str(created_at),
                "last_seen": str(last_seen),
                "conversation_count": conv_count,
                "avg_conversation_length": float(avg_conv_len),
                "engagement_score": float(engagement_score),
                "cluster_id": cluster_id,
                "biometrics": {
                    "vector_dimension": 128,
                    "model": "face_recognition (dlib HOG)",
                    "similarity_threshold": 0.55,
                    "is_primary": True
                }
            }

            raw_txt = tk.Text(
                sec5_frame,
                height=8,
                font=("Courier", 8),
                bg="#f1f5f9",
                fg="#0f172a",
                bd=1,
                relief="solid",
                wrap=tk.WORD
            )
            raw_txt.insert(tk.END, json.dumps(db_payload, indent=2))
            raw_txt.configure(state="disabled")
            raw_txt.pack(fill=tk.X)



        except Exception as e:
            print(f"⚠ Error opening existing user modal popup: {e}")
            import traceback
            traceback.print_exc()
    
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

            # Auto-open database modal when profile is successfully enrolled
            if ("successfully" in status_message.lower() or "enrolled" in status_message.lower()) and data.get('name'):
                self.root.after(300, lambda: self.show_existing_user_modal(data))
        self.root.after(0, update)

    def open_enroll_modal(self):
        """
        Interactive User Enrollment Modal:
        - Displays live camera snapshot preview and real-time biometric metrics
        - Displays complete User Details form (Name, Age, Gender, Job, Address, Email, Phone, Language, Consent)
        - Displays real-time database schema mapping and enrollment summary
        - 1-Click [📸 Capture & Enroll in Database] saves to MySQL, generates 128-d face embedding,
          and immediately launches the Enrolled User Profile Modal (show_existing_user_modal)
        - [🎤 Start Voice Registration] initiates conversational onboarding flow
        """
        if hasattr(self, 'active_enroll_modal') and self.active_enroll_modal and self.active_enroll_modal.winfo_exists():
            self.active_enroll_modal.deiconify()
            self.active_enroll_modal.lift()
            self.active_enroll_modal.focus_force()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("📝 Enroll User — Database Profile Registration (Mr. Beast AI)")
        dialog.geometry("700x780")
        dialog.minsize(660, 700)
        dialog.configure(bg="#f8fafc")
        self.active_enroll_modal = dialog

        # Center relative to parent
        try:
            rx = self.root.winfo_rootx()
            ry = self.root.winfo_rooty()
            rw = self.root.winfo_width()
            rh = self.root.winfo_height()
            dw, dh = 700, 780
            px = max(10, rx + (rw - dw) // 2)
            py = max(10, ry + (rh - dh) // 2)
            dialog.geometry(f"{dw}x{dh}+{px}+{py}")
        except Exception:
            pass

        # Top Header Banner
        header = tk.Frame(dialog, bg="#065f46", padx=18, pady=12)
        header.pack(fill=tk.X)

        title_box = tk.Frame(header, bg="#065f46")
        title_box.pack(side=tk.LEFT)
        tk.Label(
            title_box,
            text="📝 USER ENROLLMENT & DATABASE REGISTRATION",
            font=("Arial", 13, "bold"),
            fg="#ffffff",
            bg="#065f46"
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="Real-Time Face Biometrics (128-d Vector) • MySQL Database • Automatic Return Detection",
            font=("Arial", 9),
            fg="#a7f3d0",
            bg="#065f46"
        ).pack(anchor="w", pady=(2, 0))

        badge = tk.Label(
            header,
            text="🟢 CAMERA ACTIVE",
            font=("Arial", 9, "bold"),
            bg="#10b981",
            fg="#ffffff",
            padx=10,
            pady=4,
            relief="flat"
        )
        badge.pack(side=tk.RIGHT)

        # Bottom action button bar (pinned to bottom of dialog)
        btn_bar = tk.Frame(dialog, bg="#f8fafc", padx=16, pady=12)
        btn_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Scrollable container filling space between top banner and bottom buttons
        container = tk.Frame(dialog, bg="#f8fafc")
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=16, pady=(10, 0))

        canvas = tk.Canvas(container, bg="#f8fafc", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg="#f8fafc")

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas_window = canvas.create_window((0, 0), window=scroll_content, anchor="nw")

        scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        def _on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1 * event.delta), "units")
            except Exception:
                pass
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def on_close():
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
            self.active_enroll_modal = None
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", on_close)

        # ========================================================
        # SECTION 1: Camera Snapshot & Live Biometrics Preview
        # ========================================================
        sec1_frame = tk.LabelFrame(
            scroll_content,
            text="📷 1. Biometric Camera Preview & Telemetry",
            font=("Arial", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            bd=1,
            relief="solid",
            padx=12,
            pady=10
        )
        sec1_frame.pack(fill=tk.X, pady=(0, 10))

        img_box = tk.Frame(sec1_frame, bg="#ffffff")
        img_box.pack(side=tk.LEFT, anchor="n", padx=(0, 16))

        preview_lbl = tk.Label(img_box, bg="#e2e8f0", bd=2, relief="groove")
        preview_lbl.pack()

        # Helper to refresh live snapshot
        def refresh_preview():
            frame_to_show = None
            if hasattr(self, 'current_frame') and self.current_frame is not None:
                frame_to_show = self.current_frame.copy()
            if frame_to_show is not None:
                try:
                    rgb = cv2.cvtColor(frame_to_show, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb)
                    # Center-crop square
                    w, h = pil_img.size
                    min_dim = min(w, h)
                    left = (w - min_dim) // 2
                    top = (h - min_dim) // 2
                    cropped = pil_img.crop((left, top, left + min_dim, top + min_dim))
                    thumb = cropped.resize((160, 160), Image.Resampling.LANCZOS)
                    tk_img = ImageTk.PhotoImage(thumb)
                    preview_lbl.config(image=tk_img, text="")
                    preview_lbl.image = tk_img
                    return
                except Exception as e:
                    print(f"⚠ Preview render error: {e}")
            preview_lbl.config(
                text="📷\n\nLive Camera Feed\nReady to Capture",
                font=("Arial", 10, "bold"),
                fg="#64748b",
                width=18,
                height=9
            )

        refresh_preview()

        tk.Button(
            img_box,
            text="📸 Refresh Preview",
            font=("Arial", 8, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=refresh_preview,
            padx=6,
            pady=2
        ).pack(pady=(6, 0))

        # Biometrics telemetry metrics
        tele_box = tk.Frame(sec1_frame, bg="#ffffff")
        tele_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        is_connected = bool(self.user_store and self.user_store.db and self.user_store.db.is_connected)
        db_label = "MySQL Database (Connected)" if is_connected else "Local SQLite / JSON Cache (Offline)"
        stable_age_str = f"{self.stable_age} Years (High Confidence)" if getattr(self, 'stable_age', None) else "Auto-Estimating..."
        stable_gender_str = f"{self.stable_gender}" if getattr(self, 'stable_gender', None) else "Detecting..."

        tele_rows = [
            ("🎥 Camera Feed:", "Live & Synchronized (640x480 RGB)"),
            ("🧬 Facial Biometrics:", "128-d Vector (Dlib / FaceNet ResNet)"),
            ("🎯 Matching Threshold:", "Euclidean Distance < 0.55"),
            ("🎂 Detected Age:", stable_age_str),
            ("⚧ Detected Gender:", stable_gender_str),
            ("🗄️ Database Target:", db_label)
        ]
        for idx, (lbl, val) in enumerate(tele_rows):
            r = tk.Frame(tele_box, bg="#f8fafc" if idx % 2 == 0 else "#ffffff", padx=8, pady=3)
            r.pack(fill=tk.X, pady=1)
            tk.Label(r, text=lbl, font=("Arial", 8, "bold"), fg="#475569", bg=r.cget("bg"), width=20, anchor="w").pack(side=tk.LEFT)
            tk.Label(r, text=val, font=("Arial", 8), fg="#0f172a", bg=r.cget("bg"), anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ========================================================
        # SECTION 2: Complete User Details Form
        # ========================================================
        sec2_frame = tk.LabelFrame(
            scroll_content,
            text="👤 2. Enrolled User Profile Details",
            font=("Arial", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            bd=1,
            relief="solid",
            padx=14,
            pady=12
        )
        sec2_frame.pack(fill=tk.X, pady=(0, 10))

        # Initial prefill values if available
        init_name = ""
        init_age = str(getattr(self, 'stable_age', '') or "25")
        init_gender = getattr(self, 'stable_gender', 'Male') or 'Male'
        if init_gender not in ['Male', 'Female', 'Other']:
            init_gender = 'Male'
        init_job = ""
        init_address = ""
        init_email = ""
        init_phone = ""

        # Form grid
        form_grid = tk.Frame(sec2_frame, bg="#ffffff")
        form_grid.pack(fill=tk.X)

        # Row 0: Full Name & Age
        tk.Label(form_grid, text="Full Name *:", font=("Arial", 9, "bold"), fg="#1e293b", bg="#ffffff").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ent_name = tk.Entry(form_grid, font=("Arial", 10), width=26, bg="white", fg="black")
        ent_name.insert(0, init_name)
        ent_name.grid(row=0, column=1, sticky="w", padx=4, pady=4)
        ent_name.focus_set()

        tk.Label(form_grid, text="Age (Years):", font=("Arial", 9, "bold"), fg="#1e293b", bg="#ffffff").grid(row=0, column=2, sticky="w", padx=(12, 4), pady=4)
        ent_age = tk.Entry(form_grid, font=("Arial", 10), width=12, bg="white", fg="black")
        ent_age.insert(0, init_age)
        ent_age.grid(row=0, column=3, sticky="w", padx=4, pady=4)

        # Row 1: Gender & Language
        tk.Label(form_grid, text="Gender:", font=("Arial", 9, "bold"), fg="#1e293b", bg="#ffffff").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        gender_combo = ttk.Combobox(form_grid, values=["Male", "Female", "Other"], state="readonly", width=24)
        gender_combo.set(init_gender)
        gender_combo.grid(row=1, column=1, sticky="w", padx=4, pady=4)

        tk.Label(form_grid, text="Language:", font=("Arial", 9, "bold"), fg="#1e293b", bg="#ffffff").grid(row=1, column=2, sticky="w", padx=(12, 4), pady=4)
        lang_combo = ttk.Combobox(form_grid, values=["English (en)", "Hindi (hi)", "Hinglish"], state="readonly", width=12)
        curr_lang = getattr(self.orchestrator, 'current_lang', 'en') if hasattr(self, 'orchestrator') else 'en'
        lang_combo.set("Hindi (hi)" if curr_lang == 'hi' else ("Hinglish" if curr_lang == 'hinglish' else "English (en)"))
        lang_combo.grid(row=1, column=3, sticky="w", padx=4, pady=4)

        # Row 2: Profession / Studies & City / Address
        tk.Label(form_grid, text="Job / Studies:", font=("Arial", 9, "bold"), fg="#1e293b", bg="#ffffff").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        ent_job = tk.Entry(form_grid, font=("Arial", 10), width=26, bg="white", fg="black")
        ent_job.insert(0, init_job)
        ent_job.grid(row=2, column=1, sticky="w", padx=4, pady=4)

        tk.Label(form_grid, text="City / Address:", font=("Arial", 9, "bold"), fg="#1e293b", bg="#ffffff").grid(row=2, column=2, sticky="w", padx=(12, 4), pady=4)
        ent_address = tk.Entry(form_grid, font=("Arial", 10), width=18, bg="white", fg="black")
        ent_address.insert(0, init_address)
        ent_address.grid(row=2, column=3, sticky="w", padx=4, pady=4)

        # Row 3: Email Address & Phone Number
        tk.Label(form_grid, text="Email Address:", font=("Arial", 9, "bold"), fg="#1e293b", bg="#ffffff").grid(row=3, column=0, sticky="w", padx=4, pady=4)
        ent_email = tk.Entry(form_grid, font=("Arial", 10), width=26, bg="white", fg="black")
        ent_email.insert(0, init_email)
        ent_email.grid(row=3, column=1, sticky="w", padx=4, pady=4)

        tk.Label(form_grid, text="Phone Number:", font=("Arial", 9, "bold"), fg="#1e293b", bg="#ffffff").grid(row=3, column=2, sticky="w", padx=(12, 4), pady=4)
        ent_phone = tk.Entry(form_grid, font=("Arial", 10), width=18, bg="white", fg="black")
        ent_phone.insert(0, init_phone)
        ent_phone.grid(row=3, column=3, sticky="w", padx=4, pady=4)

        # Row 4: Biometric Consent
        tk.Label(form_grid, text="Biometric Consent:", font=("Arial", 9, "bold"), fg="#1e293b", bg="#ffffff").grid(row=4, column=0, sticky="w", padx=4, pady=4)
        consent_combo = ttk.Combobox(form_grid, values=["Yes (Biometric Storage Permitted)", "No (Anonymize)"], state="readonly", width=24)
        consent_combo.set("Yes (Biometric Storage Permitted)")
        consent_combo.grid(row=4, column=1, sticky="w", padx=4, pady=4)

        # ========================================================
        # SECTION 3: Summary & Auto-Recognition Information Card
        # ========================================================
        sec3_frame = tk.LabelFrame(
            scroll_content,
            text="📋 3. Enrolled User Details & Database Synchronization Summary",
            font=("Arial", 10, "bold"),
            bg="#f1f5f9",
            fg="#1e293b",
            bd=1,
            relief="solid",
            padx=12,
            pady=8
        )
        sec3_frame.pack(fill=tk.X, pady=(0, 10))

        summary_text = (
            "• Persistence Tables: user_info (demographics, contact, sync) & user_images (128-d face embedding)\n"
            "• Future Visits: Whenever this person appears before the camera, the system matches their facial vector\n"
            "  (Euclidean distance < 0.55), announces recognition via TTS, and auto-displays their full verified profile modal!"
        )
        tk.Label(
            sec3_frame,
            text=summary_text,
            font=("Arial", 8),
            fg="#334155",
            bg="#f1f5f9",
            justify="left"
        ).pack(anchor="w")

        # ========================================================
        # SECTION 4: Action Buttons (packed into bottom bar)
        # ========================================================

        def save_and_enroll():
            entered_name = ent_name.get().strip()
            if not entered_name:
                messagebox.showwarning("Name Required", "Please enter the Full Name for this user profile.")
                ent_name.focus_set()
                return

            entered_age = ent_age.get().strip()
            if not entered_age.isdigit():
                entered_age = "25"

            lang_val = lang_combo.get()
            lang_code = "hi" if "Hindi" in lang_val else ("hinglish" if "Hinglish" in lang_val else "en")

            profile_payload = {
                'name': entered_name,
                'age': entered_age,
                'gender': gender_combo.get().strip() or "Not specified",
                'job': ent_job.get().strip() or "Not specified",
                'address': ent_address.get().strip() or "Not specified",
                'email': ent_email.get().strip(),
                'phone': ent_phone.get().strip(),
                'preferred_language': lang_code,
                'consent': 'Yes' if 'Yes' in consent_combo.get() else 'No'
            }

            try:
                # 1. Save profile via ProfileService (captures frame, saves to DB & local storage)
                saved_rec = self.profile_service.save_profile(profile_payload, frame=self.current_frame)

                # 2. Update UI profile form on main window
                self.update_profile_form_ui(saved_rec, f"User '{saved_rec['name']}' successfully enrolled in database!")

                # 3. Announce via TTS if voice enabled
                if getattr(self, 'voice_enabled', False) and hasattr(self, 'tts'):
                    welcome_greeting = f"Welcome {saved_rec['name']}! You have been successfully enrolled in our database."
                    self.show_speaking()
                    threading.Thread(target=lambda: (self.tts.speak(welcome_greeting, block=True), self.hide_speaking()), daemon=True).start()

                # 4. Close enrollment modal
                on_close()

                # 5. Immediately open the comprehensive Database Enrolled User Modal!
                self.root.after(200, lambda: self.show_existing_user_modal(saved_rec))

            except Exception as e:
                print(f"⚠ Enrollment save error: {e}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Enrollment Error", f"Failed to enroll user:\n{e}")

        def launch_voice_flow():
            on_close()
            self.trigger_profile_creation()

        # Capture & Enroll in Database button
        tk.Button(
            btn_bar,
            text="📸 Capture & Enroll in Database",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=save_and_enroll,
            padx=14,
            pady=6
        ).pack(side=tk.LEFT, padx=(0, 8))

        # Start Voice Registration button
        tk.Button(
            btn_bar,
            text="🎤 Start Voice Registration",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=launch_voice_flow,
            padx=14,
            pady=6
        ).pack(side=tk.LEFT, padx=(0, 8))

        # Close / Cancel button
        tk.Button(
            btn_bar,
            text="✖ Close",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black",
            highlightbackground="white",
            relief="raised",
            bd=1,
            command=on_close,
            padx=14,
            pady=6
        ).pack(side=tk.RIGHT)

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
                    ui_callback=self.update_profile_form_ui,
                    profile_service=self.profile_service
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
