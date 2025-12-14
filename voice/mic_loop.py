"""
Continuous Microphone Loop Controller
Real-time voice conversation system
"""
import threading
import time
import queue
from voice.stt import SpeechToText
from voice.tts import TextToSpeech
from ai.brain import ConversationBrain

class ContinuousVoiceLoop:
    """Manages continuous voice conversation loop"""
    
    def __init__(self):
        """Initialize the voice loop system"""
        print("🎤 Initializing Mr. Beast Voice System...")
        
        # Initialize components
        self.stt = SpeechToText()
        self.tts = TextToSpeech(rate=180, volume=0.9)  # Energetic voice
        self.brain = ConversationBrain()
        
        # State management
        self.is_running = False
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        
        # Configure TTS for Mr. Beast personality
        self.configure_voice()
        
        print("✅ Mr. Beast Voice System ready!")
    
    def configure_voice(self):
        """Configure TTS for energetic Mr. Beast voice"""
        try:
            # Try to set a male voice
            voices = self.tts.engine.getProperty('voices')
            for voice in voices:
                if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                    self.tts.engine.setProperty('voice', voice.id)
                    break
            
            # Set energetic speaking parameters
            self.tts.engine.setProperty('rate', 180)  # Faster, more energetic
            self.tts.engine.setProperty('volume', 0.9)  # Loud and clear
            
        except Exception as e:
            print(f"⚠ Voice config warning: {e}")
    
    def start_conversation(self):
        """Start the continuous conversation loop"""
        if self.is_running:
            print("⚠ Conversation already running!")
            return
        
        self.is_running = True
        print("\n🚀 Starting continuous conversation...")
        
        # Initial greeting
        greeting = "Hey! I'm Mr. Beast. How can I help you today?"
        print(f"🤖 Mr. Beast: {greeting}")
        self.speak(greeting)
        
        # Start listening thread
        listen_thread = threading.Thread(target=self._continuous_listen, daemon=True)
        listen_thread.start()
        
        # Start processing thread
        process_thread = threading.Thread(target=self._process_speech, daemon=True)
        process_thread.start()
        
        print("✅ Conversation started! Speak anything...")
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
                    print("🎤 Listening...")
                    
                    # Listen for speech
                    text = self.stt.listen_once(timeout=3)
                    
                    if text:
                        print(f"👤 You: {text}")
                        self.speech_queue.put(text)
                    
                else:
                    # Wait while speaking
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"⚠ Listen error: {e}")
                time.sleep(1)
    
    def _process_speech(self):
        """Process speech and generate responses"""
        while self.is_running:
            try:
                # Get speech from queue (blocking)
                text = self.speech_queue.get(timeout=1)
                
                # Check for exit commands
                if any(word in text.lower() for word in ['goodbye', 'bye', 'stop', 'exit', 'quit']):
                    goodbye = "Awesome chatting with you! See you later!"
                    print(f"🤖 Mr. Beast: {goodbye}")
                    self.speak(goodbye)
                    self.stop_conversation()
                    break
                
                # Generate AI response
                response = self.brain.generate_response(text)
                print(f"🤖 Mr. Beast: {response}")
                
                # Speak response
                self.speak(response)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠ Process error: {e}")
    
    def speak(self, text):
        """Speak text with proper state management"""
        self.is_speaking = True
        try:
            self.tts.speak(text, block=True)
        except Exception as e:
            print(f"⚠ TTS error: {e}")
        finally:
            self.is_speaking = False
            time.sleep(0.5)  # Brief pause before listening again
    
    def stop_conversation(self):
        """Stop the conversation loop"""
        print("\n🛑 Stopping conversation...")
        self.is_running = False
        
        # Clear queue
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
        
        print("✅ Conversation stopped!")
    
    def test_system(self):
        """Test all components"""
        print("\n🧪 Testing Mr. Beast Voice System...")
        
        # Test TTS
        print("1. Testing Text-to-Speech...")
        self.speak("Hey! This is Mr. Beast testing the voice system!")
        
        # Test STT
        print("2. Testing Speech-to-Text...")
        print("   Say something in the next 5 seconds...")
        text = self.stt.listen_once(timeout=5)
        if text:
            print(f"   ✅ Heard: '{text}'")
        else:
            print("   ⚠ No speech detected")
        
        # Test AI Brain
        print("3. Testing AI Brain...")
        response = self.brain.generate_response("Hello")
        print(f"   ✅ AI Response: '{response}'")
        
        print("✅ System test complete!")

if __name__ == "__main__":
    # Quick test
    loop = ContinuousVoiceLoop()
    loop.test_system()