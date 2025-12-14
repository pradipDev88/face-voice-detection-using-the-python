"""
Speech-to-Text Module
Converts speech to text using Google Speech Recognition
"""
import speech_recognition as sr
import threading
import queue

class SpeechToText:
    """Handles speech recognition"""
    
    def __init__(self, language='en-IN'):
        """Initialize STT"""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.language = language
        self.is_listening = False
        self.text_queue = queue.Queue()
        
        # Configure recognizer for better sensitivity
        self.recognizer.energy_threshold = 300  # Lower = more sensitive
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.8  # Seconds of silence to consider end of phrase
        self.recognizer.phrase_threshold = 0.3  # Minimum seconds of speaking audio
        self.recognizer.non_speaking_duration = 0.5  # Seconds of silence at start
        
        # Adjust for ambient noise
        with self.microphone as source:
            print("🎤 Calibrating microphone for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print(f"   Energy threshold: {self.recognizer.energy_threshold}")
        
        print("✓ Speech-to-Text initialized")
    
    def listen_once(self, timeout=5):
        """
        Listen for single speech input
        
        Args:
            timeout: Maximum time to wait for speech
            
        Returns:
            Recognized text or None
        """
        try:
            with self.microphone as source:
                # Quick ambient noise adjustment before listening
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                print(f"🎤 Listening... (energy threshold: {self.recognizer.energy_threshold:.0f})")
                print("   Speak now!")
                
                # Listen with longer phrase time limit
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=15
                )
                
            print("🔄 Processing speech...")
            
            # Try recognition with multiple attempts
            try:
                text = self.recognizer.recognize_google(audio, language=self.language)
                print(f"✓ Recognized: '{text}'")
                return text
            except sr.UnknownValueError:
                # Try with alternative language if primary fails
                print("⚠ Trying alternative recognition...")
                try:
                    text = self.recognizer.recognize_google(audio, language='en-US')
                    print(f"✓ Recognized (alt): '{text}'")
                    return text
                except:
                    print("⚠ Could not understand audio")
                    return None
            
        except sr.WaitTimeoutError:
            print("⚠ No speech detected within timeout period")
            print("   Make sure your microphone is working and volume is up")
            return None
        except sr.RequestError as e:
            print(f"✗ Speech recognition service error: {e}")
            print("   Check your internet connection")
            return None
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return None
    
    def listen_with_retry(self, timeout=5, max_retries=3, retry_prompts=None):
        """
        Listen for speech with automatic retry prompts if no speech detected
        
        Args:
            timeout: Maximum time to wait for speech per attempt
            max_retries: Maximum number of retry attempts (None for infinite)
            retry_prompts: List of messages to cycle through when prompting
            
        Returns:
            Recognized text or None (only if max_retries reached)
        """
        if retry_prompts is None:
            retry_prompts = [
                "I didn't hear anything. Please say something.",
                "Are you there? Please speak.",
                "I'm still listening. Please say something.",
                "Please respond so I can hear you."
            ]
        
        attempt = 0
        while max_retries is None or attempt < max_retries:
            text = self.listen_once(timeout=timeout)
            
            if text:
                return text
            
            # No speech detected, return the prompt message
            prompt_index = attempt % len(retry_prompts)
            yield retry_prompts[prompt_index]
            
            attempt += 1
        
        return None
    
    def start_continuous_listening(self, callback=None):
        """
        Start continuous listening in background
        
        Args:
            callback: Function to call with recognized text
        """
        if self.is_listening:
            print("Already listening")
            return
        
        self.is_listening = True
        
        def listen_loop():
            while self.is_listening:
                text = self.listen_once(timeout=3)
                if text:
                    self.text_queue.put(text)
                    if callback:
                        callback(text)
        
        thread = threading.Thread(target=listen_loop, daemon=True)
        thread.start()
        print("✓ Continuous listening started")
    
    def stop_listening(self):
        """Stop continuous listening"""
        self.is_listening = False
        print("✓ Listening stopped")
    
    def get_text(self):
        """Get recognized text from queue"""
        try:
            return self.text_queue.get_nowait()
        except queue.Empty:
            return None
    
    def test_microphone(self):
        """
        Test microphone and speech recognition
        
        Returns:
            bool: True if test successful
        """
        print("\n" + "="*50)
        print("MICROPHONE TEST")
        print("="*50)
        
        # List available microphones
        print("\n📋 Available microphones:")
        try:
            mics = sr.Microphone.list_microphone_names()
            for i, mic in enumerate(mics):
                print(f"   {i}: {mic}")
        except Exception as e:
            print(f"   ⚠ Could not list microphones: {e}")
        
        # Test current microphone
        print(f"\n🎤 Current microphone: {self.microphone.device_index if hasattr(self.microphone, 'device_index') else 'Default'}")
        print(f"   Energy threshold: {self.recognizer.energy_threshold:.0f}")
        
        # Test audio input
        print("\n🔊 Testing audio input...")
        print("   Please say something in the next 5 seconds...")
        
        try:
            with self.microphone as source:
                # Adjust for ambient noise
                print("   Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print(f"   New energy threshold: {self.recognizer.energy_threshold:.0f}")
                
                # Listen for speech
                print("   Listening... SPEAK NOW!")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                print("   ✓ Audio captured!")
                print(f"   Audio data size: {len(audio.frame_data)} bytes")
                
                # Try to recognize
                print("   Attempting recognition...")
                text = self.recognizer.recognize_google(audio, language=self.language)
                
                print(f"\n✓ SUCCESS! Recognized: '{text}'")
                print("="*50 + "\n")
                return True
                
        except sr.WaitTimeoutError:
            print("\n✗ FAILED: No speech detected")
            print("   Possible issues:")
            print("   - Microphone is muted or volume too low")
            print("   - Wrong microphone selected")
            print("   - Microphone not connected")
            print("="*50 + "\n")
            return False
            
        except sr.UnknownValueError:
            print("\n⚠ Audio captured but could not understand speech")
            print("   Try speaking louder and clearer")
            print("="*50 + "\n")
            return False
            
        except Exception as e:
            print(f"\n✗ FAILED: {e}")
            print("="*50 + "\n")
            return False
    
    def set_microphone(self, device_index):
        """
        Change microphone device
        
        Args:
            device_index: Index of microphone to use
        """
        try:
            self.microphone = sr.Microphone(device_index=device_index)
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"✓ Microphone changed to device {device_index}")
            return True
        except Exception as e:
            print(f"✗ Error changing microphone: {e}")
            return False
