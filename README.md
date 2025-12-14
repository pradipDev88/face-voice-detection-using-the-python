# Face Detection + Age & Gender + Emotion Recognition

A complete Python application with GUI for real-time face detection, age prediction, gender classification, and emotion recognition using deep learning models.

## 🎯 Features

- **Real-time Face Detection** using OpenCV DNN
- **Age Prediction** (8 age ranges)
- **Gender Classification** (Male/Female)
- **Emotion Recognition** (happy, angry, sad, bored, surprise, neutral)
- **Professional Tkinter GUI** with live video feed
- **Photo Capture** functionality to save processed images
- **Multi-face Detection** support

## 📋 Requirements

- Python 3.8 or higher
- Webcam
- Windows/Linux/MacOS

## 🚀 Installation

### Step 1: Clone or Download Project

Download this project to your local machine.

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Download Pre-trained Models

Create a `models/` directory and download the following models:

#### Face Detection Model
- **deploy.prototxt**: [Download](https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt)
- **res10_300x300_ssd_iter_140000.caffemodel**: [Download](https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel)

#### Age Prediction Model
- **age_deploy.prototxt**: [Download](https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/age_deploy.prototxt)
- **age_net.caffemodel**: [Download](https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/age_net.caffemodel)

Alternative link for age_net.caffemodel:
```
https://www.dropbox.com/s/xfb20y596869vbb/age_net.caffemodel?dl=1
```

#### Gender Prediction Model
- **gender_deploy.prototxt**: [Download](https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/gender_deploy.prototxt)
- **gender_net.caffemodel**: [Download](https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/gender_net.caffemodel)

Alternative link for gender_net.caffemodel:
```
https://www.dropbox.com/s/iyv483wz7ztr9gh/gender_net.caffemodel?dl=1
```

#### Emotion Recognition Model
- **emotion_model.h5**: You can train your own or download from:
  - [FER2013 Emotion Model](https://github.com/oarriaga/face_classification/blob/master/trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5)
  - Rename to `emotion_model.h5`

Alternative emotion model sources:
```
https://github.com/serengil/deepface_models/releases/download/v1.0/facial_expression_model_weights.h5
```

### Step 4: Organize Models

Your `models/` folder should contain:
```
models/
├── deploy.prototxt
├── res10_300x300_ssd_iter_140000.caffemodel
├── age_deploy.prototxt
├── age_net.caffemodel
├── gender_deploy.prototxt
├── gender_net.caffemodel
└── emotion_model.h5
```

## 📁 Project Structure

```
project/
│
├── models/                          # Pre-trained models
│   ├── deploy.prototxt
│   ├── res10_300x300_ssd_iter_140000.caffemodel
│   ├── age_deploy.prototxt
│   ├── age_net.caffemodel
│   ├── gender_deploy.prototxt
│   ├── gender_net.caffemodel
│   └── emotion_model.h5
│
├── ui/                              # User interface
│   └── main_ui.py                   # Tkinter GUI implementation
│
├── core/                            # Core functionality
│   ├── detector.py                  # Face detection
│   ├── age_gender.py                # Age & gender prediction
│   └── emotion.py                   # Emotion recognition
│
├── captures/                        # Saved photos (auto-created)
│
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🎮 Usage

### Run the Application

```bash
python main.py
```

### Using the GUI

1. **Start Camera**: Click to begin webcam capture
2. **Stop Camera**: Click to pause the video feed
3. **Capture Photo**: Save current frame with detections to `/captures/` folder
4. **Exit**: Close the application

### Features in Action

- Faces are automatically detected with green bounding boxes
- Age range is displayed above each face
- Gender classification shown for each detected face
- Emotion is recognized and labeled in real-time
- Multiple faces can be detected simultaneously

## 🔧 Configuration

### Adjust Detection Confidence

Edit `core/detector.py`:
```python
self.confidence_threshold = 0.5  # Increase for fewer false positives
```

### Change Video Resolution

Edit `ui/main_ui.py`:
```python
self.canvas = tk.Canvas(video_frame, width=640, height=480, bg="#2c3e50")
```

## 📊 Model Information

### Age Ranges
- (0-2), (4-6), (8-12), (15-20), (25-32), (38-43), (48-53), (60-100)

### Gender Classes
- Male
- Female

### Emotion Classes
- Happy
- Angry
- Sad
- Bored
- Surprise
- Neutral

## 🐛 Troubleshooting

### Camera Not Opening
- Check if webcam is connected
- Ensure no other application is using the camera
- Try changing camera index in code: `cv2.VideoCapture(1)` instead of `0`

### Model Loading Errors
- Verify all model files are in `models/` directory
- Check file names match exactly
- Ensure models are not corrupted (re-download if needed)

### Performance Issues
- Close other applications
- Reduce video resolution
- Increase sleep time in video loop: `time.sleep(0.05)`

## 📝 Notes

- First run may take longer as TensorFlow initializes
- Detection accuracy depends on lighting conditions
- Works best with frontal face views
- Multiple faces can be detected simultaneously

## 🙏 Credits

- **OpenCV** for face detection
- **Gil Levi and Tal Hassner** for Age and Gender models
- **FER2013 Dataset** for emotion recognition
- **TensorFlow/Keras** for deep learning framework

## 📄 License

This project is for educational purposes. Please respect the licenses of the pre-trained models used.

## 🤝 Contributing

Feel free to fork, improve, and submit pull requests!

## 📧 Support

For issues or questions, please open an issue in the repository.

---

**Enjoy detecting faces! 😊**
