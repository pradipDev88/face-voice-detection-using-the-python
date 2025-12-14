"""
Quick test of AI Brain + TTS without camera or database
"""
from ai.hybrid_brain import HybridBrain
from voice.tts import TextToSpeech
import time

print("="*60)
print("🤖 Mr. Beast AI Brain Demo")
print("="*60)

# Initialize
print("\nInitializing...")
brain = HybridBrain()
tts = TextToSpeech(rate=150)

print("\n✅ Ready!")

# Test conversations
test_conversations = [
    ("hello", "Testing greeting"),
    ("who are you", "Testing info request"),
    ("yes", "Testing confirmation"),
    ("my name is John", "Testing name extraction"),
    ("I work at Google", "Testing job extraction"),
    ("thank you", "Testing thanks"),
    ("bye", "Testing goodbye")
]

print("\n" + "="*60)
print("Starting conversation tests...")
print("="*60)

for user_input, description in test_conversations:
    print(f"\n📝 {description}")
    print(f"👤 User: {user_input}")
    
    # Process with AI brain
    result = brain.process_user_input(user_input)
    
    print(f"🧠 Intent: {result['intent']} (confidence: {result['confidence']:.2f})")
    print(f"🔊 Robot: {result['recommended_response']}")
    
    # Speak response
    tts.speak(result['recommended_response'])
    time.sleep(1)

# Test information extraction
print("\n" + "="*60)
print("Testing information extraction...")
print("="*60)

name = brain.extract_information("my name is Alice", 'name')
print(f"\n✓ Extracted name: {name}")

job = brain.extract_information("I work at Microsoft", 'job')
print(f"✓ Extracted job: {job}")

# Test yes/no detection
print("\n" + "="*60)
print("Testing yes/no detection...")
print("="*60)

test_responses = ["yes", "no", "sure", "nope", "okay", "cancel"]
for response in test_responses:
    result = brain.process_user_input(response)
    print(f"'{response}' → Yes: {result['is_yes']}, No: {result['is_no']}")

print("\n" + "="*60)
print("✅ Demo completed successfully!")
print("="*60)
