"""
Helper script to download all required model files
Run this script to automatically download all models
"""
import urllib.request
import os

def download_file(url, destination):
    """Download file from URL to destination"""
    print(f"Downloading {os.path.basename(destination)}...")
    try:
        urllib.request.urlretrieve(url, destination)
        print(f"✓ Downloaded {os.path.basename(destination)}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {os.path.basename(destination)}: {str(e)}")
        return False

def main():
    """Download all model files"""
    print("=" * 60)
    print("Model Downloader for Face Detection Application")
    print("=" * 60)
    
    # Create models directory if it doesn't exist
    if not os.path.exists('models'):
        os.makedirs('models')
        print("✓ Created models/ directory")
    
    # Model URLs
    models = {
        'models/res10_300x300_ssd_iter_140000.caffemodel': 
            'https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel',
        
        # Note: Age and Gender caffemodels are large files
        # Users should download manually from the links in README
    }
    
    print("\nDownloading models...")
    print("-" * 60)
    
    success_count = 0
    for destination, url in models.items():
        if download_file(url, destination):
            success_count += 1
    
    print("-" * 60)
    print(f"\nDownloaded {success_count}/{len(models)} models successfully")
    
    print("\n" + "=" * 60)
    print("IMPORTANT: Manual Downloads Required")
    print("=" * 60)
    print("\nPlease manually download the following large model files:")
    print("\n1. Age Model (age_net.caffemodel):")
    print("   https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/age_net.caffemodel")
    print("   Save to: models/age_net.caffemodel")
    
    print("\n2. Gender Model (gender_net.caffemodel):")
    print("   https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/gender_net.caffemodel")
    print("   Save to: models/gender_net.caffemodel")
    
    print("\n3. Emotion Model (emotion_model.h5):")
    print("   https://github.com/oarriaga/face_classification/blob/master/trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5")
    print("   Rename to: models/emotion_model.h5")
    
    print("\nAlternative links are available in README.md")
    print("=" * 60)

if __name__ == "__main__":
    main()
