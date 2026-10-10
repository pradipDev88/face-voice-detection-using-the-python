# Application Architecture

Visual representation of the Face Detection Application architecture.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE (Tkinter)                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────┐│
│  │   Start    │  │    Stop    │  │  Capture   │  │  Exit  ││
│  │   Camera   │  │   Camera   │  │   Photo    │  │        ││
│  └────────────┘  └────────────┘  └────────────┘  └────────┘│
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │              Video Display Canvas (640x480)            │  │
│  │                                                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  Status: Camera Running | Ready | Stopped                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   VIDEO PROCESSING THREAD                    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. Capture Frame from Webcam                        │   │
│  │  2. Detect Faces                                     │   │
│  │  3. For Each Face:                                   │   │
│  │     - Extract Face Region                            │   │
│  │     - Predict Age                                    │   │
│  │     - Predict Gender                                 │   │
│  │     - Recognize Emotion                              │   │
│  │     - Draw Bounding Box                              │   │
│  │     - Add Text Labels                                │   │
│  │  4. Display Processed Frame                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      AI MODEL LAYER                          │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     Face     │  │  Age/Gender  │  │   Emotion    │      │
│  │   Detector   │  │  Predictor   │  │  Recognizer  │      │
│  │              │  │              │  │              │      │
│  │  OpenCV DNN  │  │    Caffe     │  │    Keras     │      │
│  │     SSD      │  │     CNN      │  │  Mini-XCEP   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                   (Application Entry)                        │
│                                                               │
│  • Initialize Tkinter                                        │
│  • Create captures/ directory                                │
│  • Launch FaceDetectionApp                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   ui/main_ui.py                              │
│                 (FaceDetectionApp)                           │
│                                                              │
│  • Setup GUI components                                      │
│  • Handle button events                                      │
│  • Manage video thread                                       │
│  • Process and display frames                                │
│  • Capture photos                                            │
└─────────────────────────────────────────────────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│core/         │  │core/         │  │core/         │
│detector.py   │  │age_gender.py │  │emotion.py    │
│              │  │              │  │              │
│FaceDetector  │  │AgeGender     │  │Emotion       │
│              │  │Predictor     │  │Predictor     │
│              │  │              │  │              │
│• detect_     │  │• predict()   │  │• predict()   │
│  faces()     │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Data Flow

```
Webcam
  │
  ▼
[Capture Frame]
  │
  ▼
[Face Detection] ──────────────────┐
  │                                 │
  ▼                                 │
[Extract Face ROI]                  │
  │                                 │
  ├──────────────┬─────────────┐   │
  ▼              ▼             ▼   │
[Age Model]  [Gender Model] [Emotion Model]
  │              │             │   │
  ▼              ▼             ▼   │
[Age Range]  [Male/Female]  [Emotion]
  │              │             │   │
  └──────────────┴─────────────┘   │
                 │                  │
                 ▼                  │
         [Draw Annotations] ◄───────┘
                 │
                 ▼
         [Display Frame]
                 │
                 ▼
         [User Interface]
```

## Class Hierarchy

```
FaceDetectionApp (ui/main_ui.py)
│
├── __init__()
│   ├── Initialize Tkinter window
│   ├── Load models
│   └── Setup UI
│
├── initialize_models()
│   ├── Create FaceDetector
│   ├── Create AgeGenderPredictor
│   └── Create EmotionPredictor
│
├── setup_ui()
│   ├── Create title label
│   ├── Create video canvas
│   ├── Create control buttons
│   └── Create status bar
│
├── start_camera()
│   ├── Open VideoCapture
│   ├── Start video thread
│   └── Update button states
│
├── video_loop()
│   ├── Capture frame
│   ├── Process frame
│   └── Display frame
│
├── process_frame()
│   ├── Detect faces
│   ├── For each face:
│   │   ├── Predict age/gender
│   │   ├── Recognize emotion
│   │   └── Draw annotations
│   └── Return processed frame
│
├── capture_photo()
│   ├── Save current frame
│   └── Show notification
│
└── stop_camera()
    ├── Stop video thread
    └── Release camera

FaceDetector (core/detector.py)
│
├── __init__()
│   └── Load DNN model
│
└── detect_faces(frame)
    ├── Prepare blob
    ├── Run detection
    └── Return bounding boxes

AgeGenderPredictor (core/age_gender.py)
│
├── __init__()
│   ├── Load age model
│   └── Load gender model
│
└── predict(face_img)
    ├── Prepare blob
    ├── Predict age
    ├── Predict gender
    └── Return (age, gender)

EmotionPredictor (core/emotion.py)
│
├── __init__()
│   └── Load emotion model
│
└── predict(face_img)
    ├── Preprocess image
    ├── Run prediction
    └── Return emotion label
```

## Threading Model

```
┌─────────────────────────────────────────────────────────────┐
│                      MAIN THREAD                             │
│                   (Tkinter Event Loop)                       │
│                                                               │
│  • Handle button clicks                                      │
│  • Update UI elements                                        │
│  • Display frames on canvas                                  │
│  • Show notifications                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ (spawns)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     VIDEO THREAD                             │
│                    (Daemon Thread)                           │
│                                                               │
│  while is_running:                                           │
│      • Capture frame from webcam                             │
│      • Detect faces                                          │
│      • Predict age/gender/emotion                            │
│      • Draw annotations                                      │
│      • Update display                                        │
│      • Sleep (30ms for ~30 FPS)                              │
└─────────────────────────────────────────────────────────────┘
```

## Model Pipeline

```
Input Frame (640x480 BGR)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FACE DETECTION                            │
│                                                               │
│  Input:  Frame (640x480x3)                                   │
│  Model:  OpenCV DNN SSD                                      │
│  Blob:   300x300x3                                           │
│  Output: [(x, y, w, h), ...]                                 │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
    Face ROI (variable size)
         │
         ├──────────────────┬──────────────────┐
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ AGE MODEL    │  │ GENDER MODEL │  │ EMOTION MODEL│
│              │  │              │  │              │
│ Input:       │  │ Input:       │  │ Input:       │
│ 227x227x3    │  │ 227x227x3    │  │ 48x48x1      │
│ RGB          │  │ RGB          │  │ Grayscale    │
│              │  │              │  │              │
│ Output:      │  │ Output:      │  │ Output:      │
│ 8 classes    │  │ 2 classes    │  │ 6 classes    │
│ (age ranges) │  │ (M/F)        │  │ (emotions)   │
└──────────────┘  └──────────────┘  └──────────────┘
         │                  │                  │
         └──────────────────┴──────────────────┘
                            │
                            ▼
                  Annotated Frame
                            │
                            ▼
                    Display on Canvas
```

## File Dependencies

```
main.py
  └── ui/main_ui.py
       ├── core/detector.py
       ├── core/age_gender.py
       └── core/emotion.py

models/
  ├── deploy.prototxt ──────────┐
  ├── res10_300x300_ssd.caffemodel ──► core/detector.py
  ├── age_deploy.prototxt ──────┐
  ├── age_net.caffemodel ────────┼──► core/age_gender.py
  ├── gender_deploy.prototxt ────┤
  ├── gender_net.caffemodel ─────┘
  └── emotion_model.h5 ──────────────► core/emotion.py
```

## State Machine

```
┌─────────┐
│  INIT   │
└────┬────┘
     │
     ▼
┌─────────┐  Start Camera   ┌─────────┐
│  READY  │ ───────────────► │ RUNNING │
└─────────┘                  └────┬────┘
     ▲                            │
     │         Stop Camera        │
     └────────────────────────────┘
                                   │
                                   │ Capture Photo
                                   ▼
                            ┌─────────────┐
                            │   SAVING    │
                            └──────┬──────┘
                                   │
                                   ▼
                            ┌─────────────┐
                            │   RUNNING   │
                            └─────────────┘
```

## Performance Optimization

```
┌─────────────────────────────────────────────────────────────┐
│                   OPTIMIZATION STRATEGIES                    │
│                                                               │
│  1. Threading                                                │
│     • Separate video capture from UI                         │
│     • Non-blocking frame processing                          │
│                                                               │
│  2. Frame Rate Control                                       │
│     • Sleep 30ms between frames (~30 FPS)                    │
│     • Prevents CPU overload                                  │
│                                                               │
│  3. Model Caching                                            │
│     • Load models once at startup                            │
│     • Reuse for all predictions                              │
│                                                               │
│  4. Efficient Image Processing                               │
│     • Resize only when necessary                             │
│     • Use OpenCV optimized functions                         │
│                                                               │
│  5. Memory Management                                        │
│     • Release camera on stop                                 │
│     • Clean up threads properly                              │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
Try to Load Models
  │
  ├─ Success ──► Continue
  │
  └─ Failure ──► Show Error Dialog ──► Exit Application

Try to Open Camera
  │
  ├─ Success ──► Start Video Thread
  │
  └─ Failure ──► Show Error Message ──► Disable Buttons

Try to Predict
  │
  ├─ Success ──► Display Results
  │
  └─ Failure ──► Use Default Value ──► Continue
```

## Summary

The application follows a clean, modular architecture with:

- **Separation of Concerns**: UI, detection, and prediction are separate modules
- **Threading**: Non-blocking video processing
- **Error Handling**: Graceful degradation
- **Resource Management**: Proper cleanup
- **Scalability**: Easy to add new features
- **Maintainability**: Clear code structure

This architecture ensures reliable, performant, and maintainable code.
