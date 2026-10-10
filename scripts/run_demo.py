"""
Demo runner - Shows what the application can do
This version works without all models downloaded
"""
import os
import sys

print("=" * 60)
print("Face Detection Application - Demo Runner")
print("=" * 60)

# Check what models are available
models_dir = "models"
required_models = {
    "res10_300x300_ssd_iter_140000.caffemodel": "Face Detection",
    "age_net.caffemodel": "Age Prediction",
    "gender_net.caffemodel": "Gender Prediction",
    "emotion_model.h5": "Emotion Recognition"
}

print("\nChecking available models...")
available_models = []
missing_models = []

for model_file, description in required_models.items():
    model_path = os.path.join(models_dir, model_file)
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"✓ {description}: {model_file} ({size_mb:.1f} MB)")
        available_models.append(description)
    else:
        print(f"✗ {description}: {model_file} (MISSING)")
        missing_models.append((model_file, description))

print("\n" + "=" * 60)

if len(available_models) == len(required_models):
    print("✓ All models available! Running full application...")
    print("=" * 60)
    os.system("python main.py")
elif "Face Detection" in available_models:
    print("⚠ Some models are missing, but we can run a basic demo")
    print("=" * 60)
    print("\nMissing models:")
    for model_file, description in missing_models:
        print(f"  - {description}: {model_file}")
    
    print("\nTo download missing models, see: models/README.md")
    print("\nDownload links:")
    print("  Age Model: https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/age_net.caffemodel")
    print("  Gender Model: https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/gender_net.caffemodel")
    print("  Emotion Model: https://github.com/oarriaga/face_classification/blob/master/trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5")
    
    print("\n" + "=" * 60)
    response = input("\nWould you like to run with available models only? (y/n): ")
    if response.lower() == 'y':
        print("Starting application...")
        os.system("python main.py")
    else:
        print("Please download the missing models and try again.")
else:
    print("✗ Critical models missing!")
    print("=" * 60)
    print("\nYou need to download the model files first.")
    print("\nPlease see: models/README.md for download instructions")
    print("\nQuick download (run these commands):")
    print('\nInvoke-WebRequest -Uri "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel" -OutFile "models/res10_300x300_ssd_iter_140000.caffemodel"')
    print("\nThen download age, gender, and emotion models from the links in models/README.md")
    print("=" * 60)
