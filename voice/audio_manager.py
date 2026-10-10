"""
Voice Audio Manager
Coordinates microphone capture, voice activity detection,
speech-to-text, and text-to-speech with state management
and echo-prevention.
"""
import enum
import time
import threading
from typing import Optional, Callable
from voice.stt import SpeechToText
from voice.tts import TextToSpeech
from voice.language_manager import LanguageManager


class AudioState(enum.Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"


class AudioManager:
    """Coordinates audio input, speech synthesis, and state machine"""

    def __init__(self, stt: Optional[SpeechToText] = None, tts: Optional[TextToSpeech] = None, state_callback: Optional[Callable[[AudioState], None]] = None):
        self.stt = stt or SpeechToText()
        self.tts = tts or TextToSpeech()
        self.state_callback = state_callback
        self.state = AudioState.IDLE
        self.current_lang = 'en'
        self.lock = threading.Lock()

    def set_state(self, state: AudioState):
        """Update audio state and notify listeners"""
        self.state = state
        if self.state_callback:
            try:
                self.state_callback(state)
            except Exception as e:
                print(f"⚠ State callback error: {e}")

    def speak(self, text: str, lang: Optional[str] = None, block: bool = True):
        """Speak text through TTS and update state"""
        if not text:
            return

        target_lang = lang or self.current_lang
        self.set_state(AudioState.SPEAKING)
        try:
            self.tts.speak(text, lang=target_lang, block=block)
        finally:
            if block:
                self.set_state(AudioState.IDLE)
                # Small pause to allow speaker echo to clear
                time.sleep(0.2)

    def listen(self, timeout: int = 5, phrase_time_limit: int = 15, forced_lang: Optional[str] = None) -> Optional[str]:
        """Listen from mic with VAD and return recognized text"""
        self.set_state(AudioState.LISTENING)
        try:
            text = self.stt.listen_once(timeout=timeout, phrase_time_limit=phrase_time_limit)
            if text:
                self.set_state(AudioState.PROCESSING)
                detected = LanguageManager.detect_language(text)
                self.current_lang = detected
                return text
            return None
        finally:
            self.set_state(AudioState.IDLE)

    def stop(self):
        """Stop all active audio operations"""
        self.tts.stop()
        self.set_state(AudioState.IDLE)
