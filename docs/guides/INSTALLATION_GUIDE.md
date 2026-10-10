# Quick Installation Guide

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Model Files

You need to download the following model files and place them in the `models/` folder:

#### Required Files:

1. **Face Detection Model**
   - File: `res10_300x300_ssd_iter_140000.caffemodel`
   - Download: https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel
   - Location: `models/res10_300x300_ssd_iter_140000.caffemodel`

2. **Age Prediction Model**
   - File: `age_net.caffemodel`
   - Download: https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/age_net.caffemodel
   - Location: `models/age_net.caffemodel`
   - Size: ~23 MB

3. **Gender Prediction Model**
   - File: `gender_net.caffemodel`
   - Download: https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/gender_net.caffemodel
   - Location: `models/gender_net.caffemodel`
   - Size: ~23 MB

4. **Emotion Recognition Model**
   - File: `emotion_model.h5`
   - Download: https://github.com/oarriaga/face_classification/blob/master/trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5
   - Rename to: `emotion_model.h5`
   - Location: `models/emotion_model.h5`
   - Size: ~1 MB

### 3. Verify Model Files

After downloading, your `models/` folder should contain:

```
models/
├── deploy.prototxt (already included)
├── res10_300x300_ssd_iter_140000.caffemodel (download)
├── age_deploy.prototxt (already included)
├── age_net.caffemodel (download)
├── gender_deploy.prototxt (already included)
├── gender_net.caffemodel (download)
└── emotion_model.h5 (download)
```

### 4. Run the Application

```bash
python main.py
```

## Quick Download Commands

### Using wget (Linux/Mac):

```bash
cd models

# Face detector
wget https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel

# Age model
wget https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/age_net.caffemodel

# Gender model
wget https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/gender_net.caffemodel
```

### Using PowerShell (Windows):

```powershell
cd models

# Face detector
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel" -OutFile "res10_300x300_ssd_iter_140000.caffemodel"

# Age model
Invoke-WebRequest -Uri "https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/age_net.caffemodel" -OutFile "age_net.caffemodel"

# Gender model
Invoke-WebRequest -Uri "https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/gender_net.caffemodel" -OutFile "gender_net.caffemodel"
```

## Troubleshooting

### Models Not Loading
- Verify all files are in the `models/` directory
- Check file sizes (caffemodels should be ~23MB each)
- Ensure files are not corrupted

### Camera Not Working
- Check webcam permissions
- Try changing camera index in code (0 to 1)
- Ensure no other app is using the camera

### Import Errors
- Reinstall dependencies: `pip install -r requirements.txt --upgrade`
- Check Python version (3.8+ required)

## Ready to Run!

Once all models are downloaded, simply run:

```bash
python main.py
```

Enjoy! 🎉
