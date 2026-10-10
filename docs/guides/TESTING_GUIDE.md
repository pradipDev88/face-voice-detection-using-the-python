# Testing Guide

## Pre-Testing Checklist

Before running the application, ensure:

- [ ] Python 3.8+ is installed
- [ ] All dependencies are installed (`pip install -r requirements.txt`)
- [ ] All model files are downloaded and placed in `models/` folder
- [ ] Webcam is connected and working
- [ ] No other application is using the webcam

## Testing Steps

### 1. Verify Installation

```bash
python -c "import cv2, tensorflow, tkinter; print('All imports successful!')"
```

Expected output: `All imports successful!`

### 2. Check Model Files

Verify all required files exist:

```
models/
├── deploy.prototxt ✓
├── res10_300x300_ssd_iter_140000.caffemodel ✓
├── age_deploy.prototxt ✓
├── age_net.caffemodel ✓
├── gender_deploy.prototxt ✓
├── gender_net.caffemodel ✓
└── emotion_model.h5 ✓
```

### 3. Run the Application

```bash
python main.py
```

### 4. Test UI Features

#### Test 1: Start Camera
1. Click "Start Camera" button
2. **Expected:** Webcam feed appears on canvas
3. **Expected:** Button becomes disabled
4. **Expected:** Stop and Capture buttons become enabled
5. **Expected:** Status bar shows "Camera Running"

#### Test 2: Face Detection
1. Position your face in front of camera
2. **Expected:** Green bounding box appears around face
3. **Expected:** Age range displayed (e.g., "Age: (25-32)")
4. **Expected:** Gender displayed (e.g., "Gender: Male")
5. **Expected:** Emotion displayed (e.g., "Emotion: happy")

#### Test 3: Multiple Faces
1. Have multiple people in frame
2. **Expected:** Each face gets its own bounding box
3. **Expected:** Each face shows individual predictions

#### Test 4: Emotion Changes
1. Try different facial expressions:
   - Smile → Should detect "happy"
   - Frown → Should detect "sad" or "angry"
   - Neutral face → Should detect "neutral"
   - Surprised expression → Should detect "surprise"

#### Test 5: Capture Photo
1. Click "Capture Photo" button
2. **Expected:** Success message appears
3. **Expected:** File saved in `captures/` folder
4. **Expected:** Filename format: `capture_YYYYMMDD_HHMMSS.jpg`
5. **Expected:** Status bar shows saved filename

#### Test 6: Stop Camera
1. Click "Stop Camera" button
2. **Expected:** Video feed freezes
3. **Expected:** Start button becomes enabled
4. **Expected:** Stop and Capture buttons become disabled
5. **Expected:** Status bar shows "Camera Stopped"

#### Test 7: Exit Application
1. Click "Exit" button
2. **Expected:** Confirmation dialog appears
3. Click "OK"
4. **Expected:** Application closes cleanly
5. **Expected:** Camera is released

## Performance Testing

### Frame Rate
- **Expected:** ~25-30 FPS on modern hardware
- **Acceptable:** 15-20 FPS on older hardware
- **Issue if:** <10 FPS (check CPU usage)

### Detection Accuracy
- **Good lighting:** 95%+ face detection rate
- **Poor lighting:** 70%+ face detection rate
- **Multiple faces:** Should detect 2-5 faces simultaneously

### Memory Usage
- **Initial:** ~500 MB
- **Running:** ~800 MB - 1 GB
- **Issue if:** >2 GB (possible memory leak)

## Common Issues and Solutions

### Issue 1: Camera Not Opening
**Symptoms:** Error message "Cannot access webcam"

**Solutions:**
- Check if webcam is connected
- Try changing camera index in `ui/main_ui.py`:
  ```python
  self.cap = cv2.VideoCapture(1)  # Try 1 instead of 0
  ```
- Close other applications using webcam
- Check webcam permissions

### Issue 2: Model Loading Errors
**Symptoms:** Error on startup about missing models

**Solutions:**
- Verify all model files are in `models/` folder
- Check file names match exactly
- Re-download corrupted models
- Check file sizes (caffemodels should be ~23MB)

### Issue 3: Slow Performance
**Symptoms:** Laggy video feed, low FPS

**Solutions:**
- Close other applications
- Reduce video resolution in code
- Increase sleep time in video loop
- Check CPU usage

### Issue 4: Incorrect Predictions
**Symptoms:** Wrong age/gender/emotion detected

**Solutions:**
- Ensure good lighting
- Face camera directly
- Remove glasses/hats if possible
- Models have inherent accuracy limitations

### Issue 5: TensorFlow Warnings
**Symptoms:** Warning messages about CPU instructions

**Solutions:**
- These are informational, not errors
- Can be ignored if application works
- Or install TensorFlow with AVX support

## Validation Checklist

After testing, verify:

- [ ] Application starts without errors
- [ ] All models load successfully
- [ ] Camera feed displays correctly
- [ ] Face detection works
- [ ] Age prediction shows reasonable ranges
- [ ] Gender classification works
- [ ] Emotion recognition responds to expressions
- [ ] Multiple faces can be detected
- [ ] Photos can be captured and saved
- [ ] Application exits cleanly
- [ ] No memory leaks after extended use

## Reporting Issues

If you encounter issues:

1. Note the exact error message
2. Check Python version: `python --version`
3. Check installed packages: `pip list`
4. Verify model files exist and sizes
5. Test webcam with other applications
6. Check system resources (CPU, RAM)

## Success Criteria

The application is working correctly if:

✓ All UI buttons function as expected  
✓ Face detection works in real-time  
✓ Predictions update smoothly  
✓ Photos save correctly  
✓ No crashes or freezes  
✓ Performance is acceptable (>15 FPS)  
✓ Application exits cleanly  

## Next Steps

Once testing is complete:

1. Experiment with different lighting conditions
2. Test with different face angles
3. Try with accessories (glasses, hats)
4. Test with different age groups
5. Capture sample photos for documentation

Happy Testing! 🎉
