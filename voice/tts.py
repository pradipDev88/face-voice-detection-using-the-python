"""
Text-to-Speech Module
Supports multilingual voice synthesis (English, Hindi, Hinglish)
using pyttsx3 with dynamic voice switching and macOS native voice integration.
"""
import threading
import queue
import subprocess
import sys
import os
import pyttsx3
from typing import Optional
from voice.language_manager import LanguageManager


class TextToSpeech:
    """Handles multilingual text-to-speech conversion"""
    
    def __init__(self, rate=160, volume=0.9, default_lang='en'):
        """
        Initialize Multilingual TTS
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            default_lang: Default language ('en', 'hi', 'hinglish')
        """
        self.rate = rate
        self.volume = volume
        self.default_lang = default_lang
        self.lock = threading.Lock()
        self.is_speaking = False
        self.current_process = None

        self.engine = None
        self.hindi_voice_id = None
        self.english_voice_id = None

        self._init_engine()
        print(f"✓ Multilingual Text-to-Speech initialized (Rate: {rate}, Hindi Voice: {self.hindi_voice_id or 'Auto'}, EN Voice: {self.english_voice_id or 'Default'})")

    def _init_engine(self):
        """Initialize pyttsx3 engine and detect available voices"""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)

            voices = self.engine.getProperty('voices')
            for v in voices:
                v_id = str(v.id).lower()
                v_name = str(v.name).lower()
                langs = [str(l).lower() for l in getattr(v, 'languages', [])]

                # Match Hindi voice (e.g. Lekha)
                if not self.hindi_voice_id and ('lekha' in v_name or 'hi-in' in v_id or any('hi' in l for l in langs)):
                    self.hindi_voice_id = v.id

                # Match Indian English voice (e.g. Rishi, Aman)
                if not self.english_voice_id and ('rishi' in v_name or 'aman' in v_name or 'en-in' in v_id or any('en_in' in l for l in langs)):
                    self.english_voice_id = v.id

            # Fallback for English if no en-IN found
            if not self.english_voice_id and voices:
                self.english_voice_id = voices[0].id

        except Exception as e:
            print(f"⚠ TTS engine initialization warning: {e}")
            self.engine = None

    def _select_voice_for_text(self, text: str, lang: str = None) -> Optional[str]:
        """Determine voice ID based on language and text content"""
        detected_lang = lang or LanguageManager.detect_language(text)

        if detected_lang == 'hi' and self.hindi_voice_id:
            return self.hindi_voice_id
        if self.english_voice_id:
            return self.english_voice_id
        return None

    def speak(self, text: str, lang: str = None, block: bool = True):
        """
        Speak text with appropriate language voice
        
        Args:
            text: Text to speak
            lang: Language code ('en', 'hi', 'hinglish', or None for auto)
            block: Whether to block until speech completes
        """
        if not text or not text.strip():
            return

        clean_text = text.strip()
        print(f"🔊 Speaking: {clean_text}")

        if block:
            self._do_speak(clean_text, lang)
        else:
            t = threading.Thread(target=self._do_speak, args=(clean_text, lang), daemon=True)
            t.start()

    def _do_speak(self, text: str, lang: str = None):
        """Internal speech execution with pyttsx3 or macOS say fallback"""
        with self.lock:
            self.is_speaking = True
            detected_lang = lang or LanguageManager.detect_language(text)

            # On macOS, if text contains Devanagari or is Hindi, native `say -v Lekha` is crisp & non-blocking
            if sys.platform == 'darwin':
                try:
                    voice_name = "Lekha" if detected_lang == 'hi' else ("Rishi" if detected_lang in ('hinglish', 'en') else "Samantha")
                    # Try using subprocess say
                    proc = subprocess.Popen(['say', '-v', voice_name, '-r', str(self.rate), text])
                    self.current_process = proc
                    proc.wait()
                    self.is_speaking = False
                    self.current_process = None
                    return
                except Exception as e:
                    # Fallback to pyttsx3
                    pass

            # Pyttsx3 fallback
            if self.engine:
                try:
                    voice_id = self._select_voice_for_text(text, lang=detected_lang)
                    if voice_id:
                        self.engine.setProperty('voice', voice_id)
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"⚠ Pyttsx3 speak warning: {e}")
                    # Reinitialize engine in case of loop error
                    self._init_engine()

            self.is_speaking = False

    def speak_async(self, text: str, lang: str = None):
        """Asynchronously speak text"""
        self.speak(text, lang=lang, block=False)

    def stop(self):
        """Stop speaking immediately"""
        self.is_speaking = False
        if self.current_process:
            try:
                self.current_process.terminate()
            except Exception:
                pass
            self.current_process = None

        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass

    def get_voices(self):
        """Get list of available voices"""
        if not self.engine:
            return []
        voices = self.engine.getProperty('voices')
        return [(v.id, v.name) for v in voices]

    def set_rate(self, rate: int):
        """Set speech rate"""
        self.rate = rate
        if self.engine:
            self.engine.setProperty('rate', rate)

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        self.volume = volume
        if self.engine:
            self.engine.setProperty('volume', volume)
