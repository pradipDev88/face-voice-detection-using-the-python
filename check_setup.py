"""
Setup Verification Script
Run this to check if everything is properly installed and configured
"""
import os
import sys

def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (Need 3.8+)")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")
    required = {
        'cv2': 'opencv-python',
        'tensorflow': 'tensorflow',
        'keras': 'keras',
        'numpy': 'numpy',
        'PIL': 'Pillow',
        'tkinter': 'tkinter (built-in)'
    }
    
    all_ok = True
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (NOT INSTALLED)")
            all_ok = False
    
    return all_ok

def check_model_files():
    """Check if all model files exist"""
    print("\nChecking model files...")
    
    required_files = {
        'models/deploy.prototxt': 'Face detector architecture',
        'models/res10_300x300_ssd_iter_140000.caffemodel': 'Face detector weights',
        'models/age_deploy.prototxt': 'Age predictor architecture',
        'models/age_net.caffemodel': 'Age predictor weights',
        'models/gender_deploy.prototxt': 'Gender predictor architecture',
        'models/gender_net.caffemodel': 'Gender predictor weights',
        'models/emotion_model.h5': 'Emotion predictor model'
    }
    
    all_ok = True
    for filepath, description in required_files.items():
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            size_mb = size / (1024 * 1024)
            print(f"✓ {description} ({size_mb:.1f} MB)")
        else:
            print(f"✗ {description} (MISSING)")
            all_ok = False
    
    return all_ok

def check_directories():
    """Check if required directories exist"""
    print("\nChecking directories...")
    
    directories = ['models', 'core', 'ui', 'captures']
    all_ok = True
    
    for directory in directories:
        if os.path.exists(directory) and os.path.isdir(directory):
            print(f"✓ {directory}/")
        else:
            print(f"✗ {directory}/ (MISSING)")
            all_ok = False
    
    return all_ok

def check_webcam():
    """Check if webcam is accessible"""
    print("\nChecking webcam...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                print("✓ Webcam accessible")
                return True
            else:
                print("✗ Webcam opened but cannot read frames")
                return False
        else:
            print("✗ Cannot open webcam")
            return False
    except Exception as e:
        print(f"✗ Error checking webcam: {str(e)}")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("Face Detection Application - Setup Verification")
    print("=" * 60)
    
    results = {
        'Python Version': check_python_version(),
        'Dependencies': check_dependencies(),
        'Directories': check_directories(),
        'Model Files': check_model_files(),
        'Webcam': check_webcam()
    }
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for check, status in results.items():
        status_str = "✓ PASS" if status else "✗ FAIL"
        print(f"{check}: {status_str}")
    
    print("=" * 60)
    
    if all(results.values()):
        print("\n✓ All checks passed! You're ready to run the application.")
        print("\nRun: python main.py")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("\nFor help, see:")
        print("  - README.md")
        print("  - INSTALLATION_GUIDE.md")
        print("  - models/README.md")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
