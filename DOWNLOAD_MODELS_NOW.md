# 📥 DOWNLOAD MODELS NOW

## Current Status

✅ **Face Detection Model** - Already downloaded!  
❌ **Age Model** - Need to download  
❌ **Gender Model** - Need to download  
❌ **Emotion Model** - Need to download (optional - requires TensorFlow)

---

## 🚀 Quick Download Instructions

### Option 1: Manual Download (Recommended)

#### 1. Age Model (~23 MB)
**Direct Download Link:**
```
https://www.dropbox.com/s/xfb20y596869vbb/age_net.caffemodel?dl=1
```

**Steps:**
1. Click the link above or paste in browser
2. File will download as `age_net.caffemodel`
3. Move it to the `models/` folder in this project

#### 2. Gender Model (~23 MB)
**Direct Download Link:**
```
https://www.dropbox.com/s/iyv483wz7ztr9gh/gender_net.caffemodel?dl=1
```

**Steps:**
1. Click the link above or paste in browser
2. File will download as `gender_net.caffemodel`
3. Move it to the `models/` folder in this project

#### 3. Emotion Model (~1 MB) - OPTIONAL
**Note:** This requires TensorFlow which has installation issues on your system.
You can skip this for now and still run face detection + age + gender prediction.

---

### Option 2: PowerShell Download

Open PowerShell in this project folder and run:

```powershell
# Age Model
Invoke-WebRequest -Uri "https://www.dropbox.com/s/xfb20y596869vbb/age_net.caffemodel?dl=1" -OutFile "models/age_net.caffemodel"

# Gender Model
Invoke-WebRequest -Uri "https://www.dropbox.com/s/iyv483wz7ztr9gh/gender_net.caffemodel?dl=1" -OutFile "models/gender_net.caffemodel"
```

---

### Option 3: Use Browser

1. **Age Model:**
   - Go to: https://github.com/GilLevi/AgeGenderDeepLearning
   - Click on `age_net.caffemodel`
   - Click "Download" button
   - Save to `models/` folder

2. **Gender Model:**
   - Go to: https://github.com/GilLevi/AgeGenderDeepLearning
   - Click on `gender_net.caffemodel`
   - Click "Download" button
   - Save to `models/` folder

---

## ✅ After Downloading

Your `models/` folder should contain:

```
models/
├── deploy.prototxt ✓
├── res10_300x300_ssd_iter_140000.caffemodel ✓ (Already have!)
├── age_deploy.prototxt ✓
├── age_net.caffemodel ← Download this
├── gender_deploy.prototxt ✓
├── gender_net.caffemodel ← Download this
└── emotion_model.h5 ← Optional (skip for now)
```

---

## 🎮 Then Run the Application

Once you have the age and gender models:

```bash
python main.py
```

Or use the demo runner:

```bash
python run_demo.py
```

---

## 🔍 Verify Downloads

Run this to check:

```bash
python check_setup.py
```

---

## ⚠️ Note About Emotion Model

The emotion recognition model requires TensorFlow, which has installation issues on your Windows system (Long Path problem).

**You have 2 options:**

### Option A: Skip Emotion Recognition (Recommended for now)
- The app will work fine with just face detection, age, and gender
- You'll see "N/A" for emotion

### Option B: Fix TensorFlow Installation
1. Enable Windows Long Paths:
   - Run as Administrator: `New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force`
   - Restart computer
2. Then install: `pip install tensorflow==2.15.0`
3. Download emotion model

---

## 🎯 Summary

**Minimum to run:**
- ✅ Face detection model (you have this!)
- ❌ Age model (download now)
- ❌ Gender model (download now)

**Total download size:** ~46 MB

**Time needed:** 2-5 minutes depending on internet speed

---

## 💡 Quick Links

- **Age Model Dropbox:** https://www.dropbox.com/s/xfb20y596869vbb/age_net.caffemodel?dl=1
- **Gender Model Dropbox:** https://www.dropbox.com/s/iyv483wz7ztr9gh/gender_net.caffemodel?dl=1

---

**Ready? Download the models and let's run the app!** 🚀
