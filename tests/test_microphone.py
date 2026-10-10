"""
Microphone Test Script
Run this to diagnose speech recognition issues
"""
import sys
from voice.stt import SpeechToText

def main():
    print("\n" + "="*60)
    print("SPEECH RECOGNITION DIAGNOSTIC TOOL")
    print("="*60)
    print("\nThis tool will help diagnose microphone issues.")
    print("Make sure your microphone is connected and not muted.\n")
    
    try:
        # Initialize STT
        print("Initializing speech recognition...")
        stt = SpeechToText()
        
        # Run microphone test
        success = stt.test_microphone()
        
        if success:
            print("\n✓ Your microphone is working correctly!")
            print("  The robot should be able to hear you.")
        else:
            print("\n✗ Microphone test failed!")
            print("\nTroubleshooting steps:")
            print("1. Check if your microphone is connected")
            print("2. Make sure microphone is not muted")
            print("3. Increase microphone volume in system settings")
            print("4. Try selecting a different microphone")
            print("5. Check if other apps can use the microphone")
            print("6. Restart your computer")
            
            if not getattr(stt, 'is_available', False):
                print("\n💡 PyAudio is not installed. To fix:")
                print("   1. brew install portaudio")
                print("   2. ./venv/bin/pip install pyaudio")
                return

            # Offer to try different microphone
            try:
                print("\nWould you like to try a different microphone? (y/n)")
                choice = input("> ").strip().lower()
                
                if choice == 'y':
                    if getattr(stt, 'backend', None) == 'sounddevice':
                        import sounddevice as sd
                        print("\nAvailable sounddevice microphones:")
                        for i, dev in enumerate(sd.query_devices()):
                            if dev.get('max_input_channels', 0) > 0:
                                print(f"  [{i}] {dev['name']}")
                    else:
                        import speech_recognition as sr
                        mics = sr.Microphone.list_microphone_names()
                        print("\nAvailable microphones:")
                        for i, mic in enumerate(mics):
                            print(f"  [{i}] {mic}")
                    
                    print("\nEnter microphone number to test:")
                    try:
                        mic_index = int(input("> "))
                        stt.set_microphone(mic_index)
                        stt.test_microphone()
                    except Exception:
                        print("Invalid input")
            except (EOFError, KeyboardInterrupt):
                return
        
        # Additional test
        if not getattr(stt, 'is_available', False):
            return

        print("\n" + "="*60)
        print("CONTINUOUS LISTENING TEST")
        print("="*60)
        try:
            print("\nWould you like to test continuous listening? (y/n)")
            choice = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = 'n'
        
        if choice == 'y':
            print("\nSpeak 3 times. The robot will try to recognize each time.")
            print("Press Ctrl+C to stop.\n")
            
            for i in range(3):
                print(f"\n--- Attempt {i+1}/3 ---")
                result = stt.listen_once(timeout=10)
                if result:
                    print(f"✓ Success: '{result}'")
                else:
                    print("✗ No speech detected or recognition failed")
            
            print("\n✓ Test complete!")
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Test complete. Press Enter to exit...")
    input()

if __name__ == "__main__":
    main()
