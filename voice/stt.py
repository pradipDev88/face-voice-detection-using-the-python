"""
Speech-to-Text Module
Converts speech to text using Google Speech Recognition.
Supports sounddevice (macOS CoreAudio, no portaudio build issues)
as well as standard PyAudio backends.
"""
import threading
import queue
import time
import speech_recognition as sr
import numpy as np

from voice.language_manager import LanguageManager

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False


class SpeechToText:
    """Handles speech recognition with sounddevice and pyaudio support"""
    
    def __init__(self, language='en-IN', prefer_sounddevice=True):
        """Initialize STT"""
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.language = language
        self.last_detected_language = 'en'
        self.is_listening = False
        self.text_queue = queue.Queue()
        self.is_available = False
        self.backend = None
        self.sd_device_index = None
        self.sd_sample_rate = 16000

        # Try SoundDevice backend first (ideal on macOS)
        if prefer_sounddevice and SOUNDDEVICE_AVAILABLE:
            try:
                devices = sd.query_devices()
                input_devs = [i for i, d in enumerate(devices) if d.get('max_input_channels', 0) > 0]
                if input_devs:
                    self.backend = 'sounddevice'
                    self.sd_device_index = input_devs[0]
                    self.is_available = True
                    print(f"✓ Speech-to-Text initialized (backend: sounddevice / CoreAudio, device [{self.sd_device_index}]: {devices[self.sd_device_index]['name']})")
            except Exception as e:
                print(f"⚠ sounddevice probe warning: {e}")

        # If sounddevice not chosen or unavailable, try PyAudio / sr.Microphone
        if not self.is_available:
            try:
                self.microphone = sr.Microphone()
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.dynamic_energy_adjustment_damping = 0.15
                self.recognizer.dynamic_energy_ratio = 1.5
                self.recognizer.pause_threshold = 0.8
                self.recognizer.phrase_threshold = 0.3
                self.recognizer.non_speaking_duration = 0.5
                
                with self.microphone as source:
                    print("🎤 Calibrating microphone for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                self.backend = 'pyaudio'
                self.is_available = True
                print("✓ Speech-to-Text initialized (backend: pyaudio)")
            except Exception as e:
                print(f"⚠ PyAudio / Microphone not available: {e}")

        if not self.is_available:
            print("⚠ No audio input backend available. Voice recognition will use text fallback.")

    def _recognize_audio(self, audio, forced_language=None):
        """Convert captured AudioData to text via Google STT with multi-lingual fallback"""
        target_lang = forced_language or self.language
        text = None

        # Pass 1: Try target language (e.g. en-IN or specified)
        try:
            text = self.recognizer.recognize_google(audio, language=target_lang)
        except sr.UnknownValueError:
            # Pass 2: If primary was en-IN, try Hindi (hi-IN)
            if target_lang != 'hi-IN':
                try:
                    text = self.recognizer.recognize_google(audio, language='hi-IN')
                except Exception:
                    pass
            # Pass 3: Try standard US English
            if not text:
                try:
                    text = self.recognizer.recognize_google(audio, language='en-US')
                except Exception:
                    pass
        except sr.RequestError as e:
            print(f"✗ Speech recognition network service error: {e}")
            return None
        except Exception as e:
            print(f"✗ Unexpected recognition error: {e}")
            return None

        if text:
            detected_lang = LanguageManager.detect_language(text)
            self.last_detected_language = detected_lang
            print(f"✓ Recognized [{detected_lang.upper()}]: '{text}'")
            return text

        print("⚠ Could not understand audio")
        return None

    def _listen_sounddevice(self, timeout=5, phrase_time_limit=15):
        """Listen using sounddevice with voice activity detection"""
        samplerate = self.sd_sample_rate
        chunk_samples = int(samplerate * 0.1)  # 100ms chunks

        try:
            # 1. Quick noise calibration (0.3s)
            calib_chunks = []
            with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16', device=self.sd_device_index) as stream:
                for _ in range(3):
                    chunk, _ = stream.read(chunk_samples)
                    calib_chunks.append(chunk)

                ambient_arr = np.concatenate(calib_chunks).astype(np.float32)
                ambient_rms = np.sqrt(np.mean(ambient_arr ** 2))
                threshold = max(ambient_rms * 1.5, 300)

                print(f"🎤 Listening... (speech threshold: {threshold:.0f})")
                print("   Speak now!")

                # 2. Wait for speech to start (up to timeout)
                start_wait = time.time()
                speech_detected = False
                recorded_chunks = []

                while time.time() - start_wait < timeout:
                    chunk, _ = stream.read(chunk_samples)
                    chunk_rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
                    if chunk_rms > threshold:
                        speech_detected = True
                        recorded_chunks.append(chunk)
                        break

                if not speech_detected:
                    print("⚠ No speech detected within timeout period")
                    return None

                # 3. Record while speaking until silence or time limit
                print("   Recording speech...")
                silence_duration = 0.0
                speech_start = time.time()

                while time.time() - speech_start < phrase_time_limit:
                    chunk, _ = stream.read(chunk_samples)
                    recorded_chunks.append(chunk)
                    chunk_rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                    if chunk_rms < threshold:
                        silence_duration += 0.1
                        if silence_duration >= 0.8:  # 0.8s silence ends speech
                            break
                    else:
                        silence_duration = 0.0

            # 4. Convert captured buffer to AudioData
            total_audio = np.concatenate(recorded_chunks)
            audio_bytes = total_audio.tobytes()
            audio = sr.AudioData(audio_bytes, samplerate, 2)

            print("🔄 Processing speech...")
            return self._recognize_audio(audio)

        except Exception as e:
            print(f"✗ sounddevice listen error: {e}")
            return None

    def listen_once(self, timeout=5, phrase_time_limit=15):
        """
        Listen for single speech input
        
        Args:
            timeout: Maximum time to wait for speech
            phrase_time_limit: Maximum duration of speaking
            
        Returns:
            Recognized text or None
        """
        if not self.is_available:
            return None

        if self.backend == 'sounddevice':
            return self._listen_sounddevice(timeout=timeout, phrase_time_limit=phrase_time_limit)

        if self.backend == 'pyaudio' and self.microphone is not None:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    print(f"🎤 Listening... (energy threshold: {self.recognizer.energy_threshold:.0f})")
                    print("   Speak now!")
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit
                    )
                print("🔄 Processing speech...")
                return self._recognize_audio(audio)
            except sr.WaitTimeoutError:
                print("⚠ No speech detected within timeout period")
                return None
            except Exception as e:
                print(f"✗ PyAudio listen error: {e}")
                return None

        return None

    def listen_with_retry(self, timeout=5, max_retries=3, retry_prompts=None):
        """Listen for speech with automatic retry prompts if no speech detected"""
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
            prompt_index = attempt % len(retry_prompts)
            yield retry_prompts[prompt_index]
            attempt += 1
        
        return None

    def start_continuous_listening(self, callback=None):
        """Start continuous listening in background thread"""
        if not self.is_available:
            print("⚠ Continuous listening unavailable: no audio input backend.")
            return

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
        """Test microphone and speech recognition"""
        print("\n" + "="*50)
        print("MICROPHONE TEST")
        print("="*50)

        if not self.is_available:
            print("\n⚠ Microphone is not available.")
            print("  Make sure sounddevice or PyAudio is installed.")
            return False

        print(f"Active backend: {self.backend}")

        if self.backend == 'sounddevice':
            print("\n📋 Available sounddevice microphones:")
            try:
                for i, dev in enumerate(sd.query_devices()):
                    if dev.get('max_input_channels', 0) > 0:
                        is_sel = " [SELECTED]" if i == self.sd_device_index else ""
                        print(f"   [{i}] {dev['name']} ({dev['max_input_channels']} in){is_sel}")
            except Exception as e:
                print(f"   ⚠ Could not list devices: {e}")

        elif self.backend == 'pyaudio':
            print("\n📋 Available PyAudio microphones:")
            try:
                for i, mic in enumerate(sr.Microphone.list_microphone_names()):
                    print(f"   [{i}] {mic}")
            except Exception as e:
                print(f"   ⚠ Could not list microphones: {e}")

        print("\n🔊 Testing audio input...")
        print("   Please speak a short phrase in the next 5 seconds...")
        text = self.listen_once(timeout=5)

        if text:
            print(f"\n✓ SUCCESS! Recognized: '{text}'")
            print("="*50 + "\n")
            return True
        else:
            print("\n✗ FAILED: No speech recognized or timeout reached.")
            print("="*50 + "\n")
            return False

    def set_microphone(self, device_index):
        """Change microphone device"""
        if self.backend == 'sounddevice':
            self.sd_device_index = device_index
            print(f"✓ sounddevice microphone changed to index {device_index}")
            return True
        elif self.backend == 'pyaudio':
            try:
                self.microphone = sr.Microphone(device_index=device_index)
                print(f"✓ PyAudio microphone changed to device {device_index}")
                return True
            except Exception as e:
                print(f"✗ Error changing microphone: {e}")
                return False
        return False
