"""
Text-to-Speech Module
Converts text to speech using pyttsx3
"""
import pyttsx3
import threading
import queue

class TextToSpeech:
    """Handles text-to-speech conversion"""
    
    def __init__(self, rate=150, volume=0.9, voice_id=None):
        """
        Initialize TTS
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            voice_id: Specific voice ID (None for default)
        """
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        
        # Set voice if specified
        if voice_id:
            self.engine.setProperty('voice', voice_id)
        
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        
        print("✓ Text-to-Speech initialized")
    
    def speak(self, text, block=True):
        """
        Speak text
        
        Args:
            text: Text to speak
            block: Whether to block until speech is complete
        """
        if not text:
            return
        
        print(f"🔊 Speaking: {text}")
        
        if block:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            # Speak in background thread
            thread = threading.Thread(target=self._speak_thread, args=(text,), daemon=True)
            thread.start()
    
    def _speak_thread(self, text):
        """Background thread for speaking"""
        self.is_speaking = True
        self.engine.say(text)
        self.engine.runAndWait()
        self.is_speaking = False
    
    def speak_async(self, text):
        """Speak text asynchronously"""
        self.speak(text, block=False)
    
    def stop(self):
        """Stop current speech"""
        try:
            self.engine.stop()
            self.is_speaking = False
        except:
            pass
    
    def get_voices(self):
        """Get available voices"""
        voices = self.engine.getProperty('voices')
        return [(v.id, v.name) for v in voices]
    
    def set_voice(self, voice_id):
        """Set voice by ID"""
        self.engine.setProperty('voice', voice_id)
    
    def set_rate(self, rate):
        """Set speech rate"""
        self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)"""
        self.engine.setProperty('volume', volume)
