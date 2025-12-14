# Models Directory

This folder contains all the pre-trained deep learning models required for the application.

## Required Files

### ✓ Already Included (Prototxt files)
- `deploy.prototxt` - Face detection network architecture
- `age_deploy.prototxt` - Age prediction network architecture
- `gender_deploy.prototxt` - Gender prediction network architecture

### ⬇ Need to Download (Model weights)

#### 1. Face Detection Model
**File:** `res10_300x300_ssd_iter_140000.caffemodel`  
**Size:** ~10 MB  
**Download:** https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel

#### 2. Age Prediction Model
**File:** `age_net.caffemodel`  
**Size:** ~23 MB  
**Download:** https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/age_net.caffemodel

#### 3. Gender Prediction Model
**File:** `gender_net.caffemodel`  
**Size:** ~23 MB  
**Download:** https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/gender_net.caffemodel

#### 4. Emotion Recognition Model
**File:** `emotion_model.h5`  
**Size:** ~1 MB  
**Download:** https://github.com/oarriaga/face_classification/blob/master/trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5  
**Note:** Rename downloaded file to `emotion_model.h5`

## Quick Download (Windows PowerShell)

```powershell
# Face detector
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel" -OutFile "res10_300x300_ssd_iter_140000.caffemodel"
```

## Quick Download (Linux/Mac)

```bash
# Face detector
wget https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel
```

## Final Structure

After downloading all models, this folder should contain:

```
models/
├── README.md (this file)
├── deploy.prototxt ✓
├── res10_300x300_ssd_iter_140000.caffemodel ⬇
├── age_deploy.prototxt ✓
├── age_net.caffemodel ⬇
├── gender_deploy.prototxt ✓
├── gender_net.caffemodel ⬇
└── emotion_model.h5 ⬇
```

✓ = Already included  
⬇ = Need to download
