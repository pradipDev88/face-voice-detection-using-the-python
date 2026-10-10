"""
Mr. Beast AI — Setup & System Verification Script
Validates environment, Python libraries, models, directories, and database connectivity.
"""
import os
import sys

def check_python_version():
    print("Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (Need 3.10+)")
        return False

def check_dependencies():
    print("\nChecking core dependencies...")
    required = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'PIL': 'Pillow',
        'tkinter': 'tkinter (built-in / python-tk)',
        'yaml': 'pyyaml',
        'sklearn': 'scikit-learn',
        'sounddevice': 'sounddevice',
        'speech_recognition': 'SpeechRecognition',
        'pyttsx3': 'pyttsx3',
        'mysql.connector': 'mysql-connector-python'
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
    print("\nChecking model files...")
    required_files = {
        'models/age_deploy.prototxt': 'Age predictor architecture',
        'models/age_net.caffemodel': 'Age predictor weights',
        'models/gender_deploy.prototxt': 'Gender predictor architecture',
        'models/gender_net.caffemodel': 'Gender predictor weights'
    }
    
    all_ok = True
    for filepath, description in required_files.items():
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"✓ {description} ({size_mb:.1f} MB)")
        else:
            print(f"✗ {description} (MISSING)")
            all_ok = False
            
    # Check Haar Cascade
    try:
        import cv2
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(cascade_path):
            print(f"✓ OpenCV Haar Cascade face detector (OK)")
        else:
            print(f"⚠ OpenCV Haar Cascade default xml not found at {cascade_path}")
    except Exception:
        pass
    
    return all_ok

def check_directories():
    print("\nChecking system directories...")
    directories = ['models', 'core', 'ui', 'voice', 'ai', 'db', 'services', 'captures']
    all_ok = True
    
    for directory in directories:
        if os.path.exists(directory) and os.path.isdir(directory):
            print(f"✓ {directory}/")
        else:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ {directory}/ (created)")
    
    return all_ok

def check_subsystems():
    print("\nChecking subsystems & services...")
    # 1. Database
    try:
        from db.connection import get_db
        db = get_db()
        if db and db.is_connected:
            print("✓ Database: Connected to MySQL (localhost:3306, mr_beast_db)")
        else:
            print("⚠ Database: MySQL server offline. Offline JSON mode active (captures/profiles.json)")
    except Exception as e:
        print(f"⚠ Database check note: {e}")

    # 2. TTS
    try:
        from voice.tts import TextToSpeech
        tts = TextToSpeech(rate=160)
        hi_voice = getattr(tts, 'hindi_voice_id', 'None')
        en_voice = getattr(tts, 'english_voice_id', 'None')
        print(f"✓ Audio TTS: Initialized (Hindi Voice: {hi_voice}, English Voice: {en_voice})")
    except Exception as e:
        print(f"⚠ TTS check note: {e}")

    # 3. AI Brain
    try:
        from ai.brain import AIBrain
        brain = AIBrain()
        print("✓ AI Brain: Intent classifier & entity extractors loaded")
    except Exception as e:
        print(f"⚠ AI Brain check note: {e}")

def main():
    print("=" * 60)
    print("MR. BEAST AI — SETUP VERIFICATION")
    print("=" * 60)
    
    v_ok = check_python_version()
    d_ok = check_dependencies()
    m_ok = check_model_files()
    dir_ok = check_directories()
    check_subsystems()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Python Version: {'✓ PASS' if v_ok else '✗ FAIL'}")
    print(f"Dependencies:   {'✓ PASS' if d_ok else '✗ FAIL'}")
    print(f"Model Files:    {'✓ PASS' if m_ok else '✗ FAIL'}")
    print(f"Directories:    {'✓ PASS' if dir_ok else '✗ FAIL'}")
    print("=" * 60)
    
    if v_ok and d_ok and m_ok and dir_ok:
        print("\n🎉 Everything is installed and configured properly!")
        print("Run the robot with: python main.py")
    else:
        print("\n⚠ Some components require attention. See details above.")

if __name__ == "__main__":
    main()
