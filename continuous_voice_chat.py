"""
Mr. Beast Continuous Voice Chat
Real-time STT → AI → TTS conversation system
"""
import sys
import time
from voice.mic_loop import ContinuousVoiceLoop

def main():
    """Main entry point for continuous voice chat"""
    print("="*60)
    print("🎤 MR. BEAST CONTINUOUS VOICE CHAT")
    print("="*60)
    print("\nFeatures:")
    print("✅ Real-time speech recognition")
    print("✅ Instant AI responses")
    print("✅ Energetic Mr. Beast personality")
    print("✅ Continuous conversation loop")
    print("✅ No UI needed - pure voice!")
    print("\nInstructions:")
    print("• Speak naturally after the robot greets you")
    print("• Ask any question or make any comment")
    print("• Say 'goodbye' or 'stop' to end")
    print("• Press Ctrl+C to force quit")
    print("="*60)
    
    try:
        # Initialize the voice loop system
        voice_loop = ContinuousVoiceLoop()
        
        # Test system first (optional)
        print("\n🧪 Quick system test...")
        voice_loop.test_system()
        
        print("\n🚀 Starting continuous conversation...")
        print("Get ready to chat with Mr. Beast!")
        time.sleep(2)
        
        # Start the conversation
        voice_loop.start_conversation()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Conversation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Thanks for chatting with Mr. Beast!")
        print("="*60)

if __name__ == "__main__":
    main()