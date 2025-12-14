"""
Microphone Controller
Manages microphone input and voice activity detection
"""
import speech_recognition as sr
import numpy as np

class MicrophoneController:
    """Controls microphone and detects voice activity"""
    
    def __init__(self):
        """Initialize microphone controller"""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_active = False
        self.energy_threshold = 300  # Default energy threshold
        
        # Calibrate
        self.calibrate()
        
        print("✓ Microphone controller initialized")
    
    def calibrate(self, duration=1):
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                print("🎤 Calibrating microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                self.energy_threshold = self.recognizer.energy_threshold
                print(f"✓ Calibration complete (threshold: {self.energy_threshold})")
        except Exception as e:
            print(f"⚠ Calibration error: {e}")
    
    def is_voice_detected(self):
        """
        Check if voice is currently detected
        
        Returns:
            bool: True if voice detected
        """
        try:
            with self.microphone as source:
                # Listen for very short duration
                audio = self.recognizer.listen(source, timeout=0.5, phrase_time_limit=0.5)
                # If we got audio, voice was detected
                return True
        except:
            return False
    
    def get_audio_level(self):
        """
        Get current audio input level
        
        Returns:
            float: Audio level (0.0 to 1.0)
        """
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=0.1, phrase_time_limit=0.1)
                # Rough estimate of audio level
                return min(1.0, len(audio.frame_data) / 10000.0)
        except:
            return 0.0
    
    def test_microphone(self):
        """Test if microphone is working"""
        try:
            with self.microphone as source:
                print("🎤 Testing microphone... Say something!")
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=3)
                print("✓ Microphone is working!")
                return True
        except Exception as e:
            print(f"✗ Microphone test failed: {e}")
            return False
    
    def list_microphones(self):
        """List available microphones"""
        return sr.Microphone.list_microphone_names()
    
    def set_microphone(self, device_index):
        """Set microphone by device index"""
        try:
            self.microphone = sr.Microphone(device_index=device_index)
            self.calibrate()
            print(f"✓ Microphone set to device {device_index}")
            return True
        except Exception as e:
            print(f"✗ Error setting microphone: {e}")
            return False
