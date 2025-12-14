# Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Install Python Packages (1 min)

```bash
pip install -r requirements.txt
```

## Step 2: Download Models (3 min)

Download these 4 files and place them in the `models/` folder:

### 1. Face Detector (~10 MB)
```
https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel
```
Save as: `models/res10_300x300_ssd_iter_140000.caffemodel`

### 2. Age Model (~23 MB)
```
https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/age_net.caffemodel
```
Save as: `models/age_net.caffemodel`

### 3. Gender Model (~23 MB)
```
https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/gender_net.caffemodel
```
Save as: `models/gender_net.caffemodel`

### 4. Emotion Model (~1 MB)
```
https://github.com/oarriaga/face_classification/blob/master/trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5
```
Save as: `models/emotion_model.h5` (rename after download)

## Step 3: Verify Setup (30 sec)

```bash
python check_setup.py
```

Should show all checks passing ✓

## Step 4: Run Application (30 sec)

```bash
python main.py
```

## Step 5: Use the App

1. Click **"Start Camera"**
2. Position your face in view
3. See age, gender, and emotion detected!
4. Click **"Capture Photo"** to save
5. Photos saved in `captures/` folder

## That's It! 🎉

You're now running real-time face detection with AI!

## Need Help?

- **Full docs:** See `README.md`
- **Installation issues:** See `INSTALLATION_GUIDE.md`
- **Testing:** See `TESTING_GUIDE.md`
- **Model downloads:** See `models/README.md`

## Quick Tips

- Works best with good lighting
- Face the camera directly
- Multiple faces supported
- Try different expressions for emotion detection

Enjoy! 😊
