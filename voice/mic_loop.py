"""
Continuous Microphone Loop Controller
Real-time multilingual voice conversation system
"""
import threading
import time
import queue
from voice.stt import SpeechToText
from voice.tts import TextToSpeech
from voice.language_manager import LanguageManager
from ai.orchestrator import AIOrchestrator
from services.profile_service import ProfileService


class ContinuousVoiceLoop:
    """Manages continuous multilingual voice conversation loop"""
    
    def __init__(self):
        """Initialize the voice loop system"""
        print("🎤 Initializing Mr. Beast Multilingual Voice System...")
        
        # Initialize components
        self.stt = SpeechToText()
        self.tts = TextToSpeech(rate=160, volume=0.9)
        self.profile_service = ProfileService()
        self.orchestrator = AIOrchestrator(profile_service=self.profile_service)
        
        # State management
        self.is_running = False
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        
        print("✅ Mr. Beast Multilingual Voice System ready!")
    
    def start_conversation(self):
        """Start the continuous conversation loop"""
        if self.is_running:
            print("⚠ Conversation already running!")
            return
        
        self.is_running = True
        print("\n🚀 Starting continuous conversation...")
        
        # Initial greeting
        greeting = "Hey! I'm Mr. Beast. How can I help you today? Aap mujhse Hindi ya English me baat kar sakte hain!"
        print(f"🤖 Mr. Beast: {greeting}")
        self.speak(greeting, lang='hinglish')
        
        # Start listening thread
        listen_thread = threading.Thread(target=self._continuous_listen, daemon=True)
        listen_thread.start()
        
        # Start processing thread
        process_thread = threading.Thread(target=self._process_speech, daemon=True)
        process_thread.start()
        
        print("✅ Conversation started! Speak anything in English, Hindi, or Hinglish...")
        print("💡 Say 'goodbye' or 'stop' to end conversation")
        print("-" * 50)
        
        # Keep main thread alive
        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_conversation()
    
    def _continuous_listen(self):
        """Continuous listening thread"""
        while self.is_running:
            try:
                # Only listen when not speaking
                if not self.is_speaking:
                    text = self.stt.listen_once(timeout=4)
                    
                    if text:
                        print(f"👤 You: {text}")
                        self.speech_queue.put(text)
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"⚠ Listen error: {e}")
                time.sleep(1)
    
    def _process_speech(self):
        """Process speech and generate responses via AIOrchestrator"""
        while self.is_running:
            try:
                # Get speech from queue (blocking)
                text = self.speech_queue.get(timeout=1)
                
                # Check for explicit exit command when NOT in registration
                if not self.orchestrator.registration_agent.is_active() and any(
                    word in text.lower().split() for word in ['exit', 'quit', 'alvida']
                ):
                    goodbye = "Awesome chatting with you! See you later!"
                    print(f"🤖 Mr. Beast: {goodbye}")
                    self.speak(goodbye)
                    self.stop_conversation()
                    break

                # Process via AIOrchestrator
                res = self.orchestrator.handle_input(text)
                response = res['response']
                lang = res.get('language', 'en')
                
                print(f"🤖 Mr. Beast [{lang.upper()}]: {response}")
                self.speak(response, lang=lang)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠ Process error: {e}")
    
    def speak(self, text, lang='en'):
        """Speak text with proper state management and language matching"""
        self.is_speaking = True
        try:
            self.tts.speak(text, lang=lang, block=True)
        except Exception as e:
            print(f"⚠ TTS error: {e}")
        finally:
            self.is_speaking = False
            time.sleep(0.3)  # Brief pause before listening again
    
    def stop_conversation(self):
        """Stop the conversation loop"""
        print("\n🛑 Stopping conversation...")
        self.is_running = False
        
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
        
        print("✅ Conversation stopped!")