"""
Tkinter GUI for Face Detection Application
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import threading
import time
import os
from datetime import datetime
from core.detector import FaceDetector
from core.age_gender import AgeGenderPredictor
from core.face_matcher import FaceMatcher

class FaceDetectionApp:
    """Main application class for Face Detection UI"""
    
    def __init__(self, root):
        """Initialize the application"""
        self.root = root
        self.root.title("Face Detection + Age & Gender + Emotion Recognition")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
        
        # Video capture variables
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.thread = None
        
        # Initialize models
        self.initialize_models()
        
        # Setup UI
        self.setup_ui()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def initialize_models(self):
        """Load all detection and prediction models"""
        try:
            self.face_detector = FaceDetector()
            self.age_gender_predictor = AgeGenderPredictor()
            self.face_matcher = FaceMatcher()  # NEW: Face matching with AI
            
            # Try to load emotion predictor, but continue if it fails
            try:
                from core.emotion import EmotionPredictor
                self.emotion_predictor = EmotionPredictor()
                self.has_emotion = True
            except Exception as e:
                print(f"⚠ Emotion model not available: {str(e)}")
                self.emotion_predictor = None
                self.has_emotion = False
            print("✓ All available models loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load models: {str(e)}")
            self.root.destroy()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Title Label
        title_label = tk.Label(
            self.root,
            text="Face Detection + Age & Gender + Emotion Recognition",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=10
        )
        title_label.pack(fill=tk.X)
        
        # Main container
        main_frame = tk.Frame(self.root, bg="#ecf0f1")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video display frame
        video_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.SUNKEN, bd=2)
        video_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Canvas for video display
        self.canvas = tk.Canvas(video_frame, width=640, height=480, bg="#2c3e50")
        self.canvas.pack(padx=5, pady=5)
        
        # Control panel
        control_frame = tk.Frame(main_frame, bg="#ecf0f1", width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        
        # Controls title
        controls_title = tk.Label(
            control_frame,
            text="Controls",
            font=("Arial", 14, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        controls_title.pack(pady=10)
        
        # Button style
        button_style = {
            'font': ("Arial", 11, "bold"),
            'width': 20,
            'height': 2,
            'relief': tk.RAISED,
            'bd': 3
        }
        
        # Start Camera Button
        self.start_btn = tk.Button(
            control_frame,
            text="▶ Start Camera",
            bg="#27ae60",
            fg="white",
            command=self.start_camera,
            **button_style
        )
        self.start_btn.pack(pady=10)
        
        # Stop Camera Button
        self.stop_btn = tk.Button(
            control_frame,
            text="⏸ Stop Camera",
            bg="#e74c3c",
            fg="white",
            command=self.stop_camera,
            state=tk.DISABLED,
            **button_style
        )
        self.stop_btn.pack(pady=10)
        
        # Capture Photo Button
        self.capture_btn = tk.Button(
            control_frame,
            text="📷 Capture Photo",
            bg="#3498db",
            fg="white",
            command=self.capture_photo,
            state=tk.DISABLED,
            **button_style
        )
        self.capture_btn.pack(pady=10)
        
        # Info Button
        self.info_btn = tk.Button(
            control_frame,
            text="ℹ️ Face Info",
            bg="#9b59b6",
            fg="white",
            command=self.show_face_info,
            state=tk.DISABLED,
            **button_style
        )
        self.info_btn.pack(pady=10)
        
        # Exit Button
        self.exit_btn = tk.Button(
            control_frame,
            text="✖ Exit",
            bg="#95a5a6",
            fg="white",
            command=self.on_closing,
            **button_style
        )
        self.exit_btn.pack(pady=10)
        
        # Info panel
        info_frame = tk.LabelFrame(
            control_frame,
            text="Information",
            font=("Arial", 11, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50",
            relief=tk.GROOVE,
            bd=2
        )
        info_frame.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)
        
        info_text = """
        ℹ Instructions:
        
        1. Click 'Start Camera' to begin
        2. Face detection runs automatically
        3. Age, Gender & Emotion displayed
        4. Click 'Capture Photo' to save
        5. Photos saved in /captures/
        6. Click 'Stop Camera' to pause
        7. Click 'Exit' to close app
        """
        
        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=("Arial", 9),
            bg="#ecf0f1",
            fg="#34495e",
            justify=tk.LEFT,
            anchor="w"
        )
        info_label.pack(padx=10, pady=10)
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Status: Ready",
            font=("Arial", 10),
            bg="#34495e",
            fg="white",
            anchor="w",
            padx=10
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def start_camera(self):
        """Start the webcam capture"""
        if not self.is_running:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Cannot access webcam")
                return
            
            self.is_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.capture_btn.config(state=tk.NORMAL)
            self.info_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Camera Running")
            
            # Start video thread
            self.thread = threading.Thread(target=self.video_loop, daemon=True)
            self.thread.start()
    
    def stop_camera(self):
        """Stop the webcam capture"""
        if self.is_running:
            self.is_running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.capture_btn.config(state=tk.DISABLED)
            self.info_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Status: Camera Stopped")
            
            if self.cap:
                self.cap.release()
                self.cap = None
    
    def video_loop(self):
        """Main video processing loop"""
        while self.is_running:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # Process frame
                    processed_frame = self.process_frame(frame)
                    self.current_frame = processed_frame.copy()
                    
                    # Display frame
                    self.display_frame(processed_frame)
                else:
                    break
            time.sleep(0.03)  # ~30 FPS
    
    def process_frame(self, frame):
        """Process frame with face detection and predictions"""
        # Clear previous face details
        self.face_details = []
        
        # Detect faces
        faces = self.face_detector.detect_faces(frame)
        
        for (x, y, w, h) in faces:
            # Extract face region
            face_roi = frame[y:y+h, x:x+w]
            
            # Predict age and gender
            age, gender, age_range = self.age_gender_predictor.predict(face_roi)
            
            # Match face with celebrities using AI
            celebrity_match = self.face_matcher.match_face(face_roi, age, gender)
            
            # Store detailed info for this face
            if not hasattr(self, 'face_details'):
                self.face_details = []
            
            # Get base info
            base_info = self.age_gender_predictor.get_detailed_info(age_range)
            
            # Update with AI-matched celebrity
            base_info['film_stars'] = ', '.join(celebrity_match['top_3'])
            base_info['best_match'] = celebrity_match['best_match']
            base_info['similarity'] = f"{celebrity_match['similarity']*100:.1f}%"
            base_info['match_method'] = celebrity_match['method']
            
            self.face_details.append({
                'position': (x, y, w, h),
                'age': age,
                'gender': gender,
                'age_range': age_range,
                'info': base_info,
                'celebrity_match': celebrity_match
            })
            
            # Predict emotion (if available)
            if self.has_emotion and self.emotion_predictor:
                emotion = self.emotion_predictor.predict(face_roi)
            else:
                emotion = "N/A"
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Prepare text labels
            label_y = y - 10
            
            # Draw labels with background
            labels = [
                f"Age: {age} yrs",
                f"Gender: {gender}",
                f"Emotion: {emotion}",
                f"[i] More Info"
            ]
            
            for i, label in enumerate(labels):
                text_y = y - 10 - (i * 25)
                if text_y < 20:
                    text_y = y + h + 20 + (i * 25)
                
                # Get text size for background
                (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                
                # Draw background rectangle
                cv2.rectangle(frame, (x, text_y - text_h - 5), (x + text_w + 5, text_y + 5), (0, 255, 0), -1)
                
                # Draw text
                cv2.putText(frame, label, (x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return frame
    
    def display_frame(self, frame):
        """Display frame on canvas"""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize to fit canvas
        frame_resized = cv2.resize(frame_rgb, (640, 480))
        
        # Convert to PIL Image
        img = Image.fromarray(frame_resized)
        imgtk = ImageTk.PhotoImage(image=img)
        
        # Update canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        self.canvas.imgtk = imgtk  # Keep reference
    
    def capture_photo(self):
        """Capture and save current frame"""
        if self.current_frame is not None:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"captures/capture_{timestamp}.jpg"
            
            # Save image
            cv2.imwrite(filename, self.current_frame)
            
            self.status_label.config(text=f"Status: Photo saved as {filename}")
            messagebox.showinfo("Success", f"Photo saved as:\n{filename}")
        else:
            messagebox.showwarning("Warning", "No frame to capture")
    
    def show_face_info(self):
        """Show detailed information about detected faces"""
        if not hasattr(self, 'face_details') or not self.face_details:
            messagebox.showinfo("No Faces", "No faces detected yet.\nStart the camera and position your face.")
            return
        
        # Create info window
        info_window = tk.Toplevel(self.root)
        info_window.title("Face Information")
        info_window.geometry("500x600")
        info_window.resizable(False, False)
        
        # Title
        title = tk.Label(
            info_window,
            text="🔍 Detailed Face Analysis",
            font=("Arial", 16, "bold"),
            bg="#9b59b6",
            fg="white",
            pady=15
        )
        title.pack(fill=tk.X)
        
        # Scrollable frame
        canvas = tk.Canvas(info_window, bg="#ecf0f1")
        scrollbar = tk.Scrollbar(info_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ecf0f1")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display info for each face
        for i, face in enumerate(self.face_details, 1):
            info = face['info']
            
            # Face frame
            face_frame = tk.LabelFrame(
                scrollable_frame,
                text=f"Face #{i}",
                font=("Arial", 12, "bold"),
                bg="#ecf0f1",
                fg="#2c3e50",
                relief=tk.GROOVE,
                bd=2
            )
            face_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # Get celebrity match info
            celeb_match = face.get('celebrity_match', {})
            match_method = celeb_match.get('method', 'Age-based')
            
            # Basic info with AI matching
            basic_info = f"""
📊 Basic Information:
   Age: {face['age']} years
   Gender: {face['gender']}
   Category: {info['category']}

🐾 Animal Similarity:
   You're like a {info['animal']}!
   
✨ Personality Traits:
   {info['traits']}

🎬 AI Celebrity Match:
   Method: {match_method}
   Best Match: {info.get('best_match', 'Unknown')}
   Similarity: {info.get('similarity', 'N/A')}
   
   Top Matches:
   {info['film_stars']}

💭 Description:
   {info['description']}
            """
            
            info_label = tk.Label(
                face_frame,
                text=basic_info,
                font=("Arial", 10),
                bg="#ecf0f1",
                fg="#2c3e50",
                justify=tk.LEFT,
                anchor="w"
            )
            info_label.pack(padx=10, pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        close_btn = tk.Button(
            info_window,
            text="Close",
            bg="#95a5a6",
            fg="white",
            font=("Arial", 11, "bold"),
            command=info_window.destroy,
            height=2
        )
        close_btn.pack(fill=tk.X, padx=10, pady=10)
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.stop_camera()
            self.root.destroy()
