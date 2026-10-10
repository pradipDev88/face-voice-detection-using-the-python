"""
Mr. Beast — Advanced Multilingual AI Voice Robot & Autonomous Profile Management System
Main Unified Application Entry Point

Running `python main.py` starts the entire system:
  1. Desktop GUI Mode (Tkinter) with live camera feed, face detection, voice conversation,
     health badges, language selector, and interactive registration card.
  2. Automatic Fallback to OpenCV Camera Robot Mode if Tkinter is missing.
  3. Automatic Fallback to Terminal Voice Assistant Mode if camera is unavailable.

Command-line flags supported:
  - (default)       : Full multimodal project execution
  - --gui, -g       : Force Desktop Tkinter UI mode
  - --cli, -c       : Interactive terminal OpenCV robot mode
  - --voice, -v     : Continuous hands-free voice chat mode
  - --admin, -a     : Launch Desktop Tkinter Admin Dashboard
  - --web-admin, -w : Launch In-Browser Web Admin Dashboard (http://localhost:8080)
  - --sync          : Flush offline sync queue to MySQL
  - --test-all      : Run full automated test suite (all 31 tests)
  - --test-mic      : Test CoreAudio microphone input & speech recognition
  - --test-tts      : Test multilingual speech synthesis (English & Hindi)
  - --test-db       : Test MySQL database connectivity & tables
  - --check         : Comprehensive system & environment diagnostic
"""
import sys
import os
import argparse
import time

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def print_banner():
    """Display startup banner and active subsystems"""
    print("=" * 64)
    print("🤖 MR. BEAST AI — MULTILINGUAL VOICE ROBOT & PROFILE SYSTEM")
    print("=" * 64)
    print("✓ Multilingual Voice Engine (English, Hindi, Hinglish)")
    print("✓ 11-State Autonomous Registration Agent with In-Flight Edits")
    print("✓ Vision & Demographic Analytics (OpenCV + Caffe Models)")
    print("✓ Dual-Store Database Architecture (MySQL + Durable Sync Queue)")
    print("✓ Safe Application Tool Router (Math AST, Datetime, Diagnostics)")
    print("=" * 64 + "\n")


def launch_gui():
    """
    Launch full Desktop Tkinter GUI with camera, detection, voice, and database.
    Gracefully falls back to OpenCV Camera or Voice Terminal mode if Tkinter is unavailable.
    """
    try:
        import tkinter as tk
        from ui.robot_ui import MrBeastUI

        print("🚀 Launching Mr. Beast Desktop UI (Tkinter)...")
        root = tk.Tk()
        app = MrBeastUI(root)
        root.mainloop()
    except (ImportError, ModuleNotFoundError) as e:
        print("\n" + "=" * 60)
        print("⚠ Tkinter is not installed in this Python environment.")
        print("=" * 60)
        print("On macOS (Homebrew Python), you can install it with:")
        print("    brew install python-tk@3.12")
        print("\nSwitching to OpenCV Camera & Voice Robot mode instead...")
        print("=" * 60 + "\n")
        launch_cli_camera()
    except Exception as e:
        print(f"\n⚠ Desktop GUI could not be initialized: {e}")
        print("Switching to OpenCV Camera & Voice Robot mode instead...\n")
        launch_cli_camera()


def launch_cli_camera():
    """Launch OpenCV camera robot with face detection and voice interaction"""
    try:
        from main_robot import MrBeastRobot
        print("📸 Launching Mr. Beast OpenCV Camera & Voice Robot...")
        robot = MrBeastRobot()
        robot.run_with_camera()
    except Exception as e:
        print(f"\n⚠ Camera robot could not run: {e}")
        print("Switching to Hands-Free Voice Assistant mode instead...\n")
        launch_voice_chat()


def launch_cli():
    """Launch interactive terminal robot selection menu"""
    from main_robot import main as cli_main
    cli_main()


def launch_voice_chat():
    """Launch hands-free continuous voice conversation loop in terminal"""
    try:
        from voice.mic_loop import ContinuousVoiceLoop
        print("=" * 60)
        print("🎤 Starting Mr. Beast Hands-Free Voice Assistant (Terminal)")
        print("=" * 60)
        loop = ContinuousVoiceLoop()
        loop.start_conversation()
        
        # Keep main thread alive while background voice loop is running
        while getattr(loop, 'is_running', False):
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\n👋 Voice chat ended. Goodbye!")


def launch_admin_gui():
    """Launch standalone Desktop Tkinter Admin Dashboard"""
    try:
        from ui.admin_dashboard import launch_admin_dashboard
        print("🛡️ Launching Mr. Beast Desktop Admin Console...")
        launch_admin_dashboard()
    except Exception as e:
        print(f"\n⚠ Desktop Admin Console could not be initialized: {e}")
        print("Launching Web Admin Dashboard on http://localhost:8080 instead...\n")
        launch_web_admin()


def launch_web_admin(port: int = 8080):
    """Launch zero-dependency Web Admin Dashboard on http://localhost:8080"""
    from services.web_admin import run_web_admin
    run_web_admin(port=port)


def run_checks():
    """Run system setup check"""
    from scripts.check_setup import main as check_main
    check_main()


def run_download():
    """Run model downloader"""
    from scripts.quick_download import main as download_main
    download_main()


def run_mic_test():
    """Run microphone diagnostic"""
    from tests.test_microphone import main as mic_main
    mic_main()


def run_db_test():
    """Run database diagnostic"""
    from tests.test_database import main as db_main
    db_main()


def run_tts_test():
    """Run text-to-speech test across languages"""
    from voice.tts import TextToSpeech
    tts = TextToSpeech(rate=160, volume=0.9)
    print("Testing English / Hinglish TTS...")
    tts.speak("Hello! I am Mr. Beast, your AI voice assistant.", lang='en', block=True)
    print("Testing Hindi TTS (Apple native Lekha)...")
    tts.speak("नमस्ते! मैं मिस्टर बीस्ट बोल रहा हूँ।", lang='hi', block=True)
    print("✓ Multilingual TTS test complete!")


def run_sync():
    """Manually flush offline sync queue to MySQL"""
    from services.profile_service import ProfileService
    ps = ProfileService()
    print("🔄 Flushing durable offline queue to MySQL...")
    res = ps.sync_offline()
    synced = res.get('synced', 0)
    failed = res.get('failed', 0)
    print(f"✓ Sync complete: {synced} synced, {failed} remaining/offline.")


def run_all_tests():
    """Run full automated test suite (31 unit tests)"""
    import unittest
    print_banner()
    print("🧪 Running End-to-End Automated Test Suite...\n")
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n✅ All unit tests passed successfully!")
    else:
        print(f"\n❌ Test failures detected ({len(result.failures)} failures, {len(result.errors)} errors).")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Mr. Beast — Advanced Multilingual AI Voice Robot & Autonomous Profile Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python main.py             # Start entire project (Desktop GUI with Camera & Voice)
  python main.py --admin     # Start Desktop Tkinter Admin Dashboard
  python main.py --web-admin # Start In-Browser Web Admin Dashboard (http://localhost:8080)
  python main.py --cli       # Start interactive OpenCV camera robot in terminal
  python main.py --voice     # Start hands-free continuous voice chat without camera
  python main.py --sync      # Flush offline sync queue to MySQL
  python main.py --test-all  # Run full automated test suite (all 31 unit tests)
  python main.py --test-mic  # Test CoreAudio microphone input & speech recognition
  python main.py --test-tts  # Test multilingual text-to-speech engine
  python main.py --test-db   # Test MySQL database connection & tables
  python main.py --check     # Verify installation, models, and dependencies
"""
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--gui", "-g", action="store_true", help="Launch primary Desktop GUI mode")
    group.add_argument("--admin", "-a", action="store_true", help="Launch Desktop Admin Dashboard console")
    group.add_argument("--web-admin", "-w", action="store_true", help="Launch In-Browser Web Admin Dashboard (port 8080)")
    group.add_argument("--cli", "-c", action="store_true", help="Run interactive terminal robot mode")
    group.add_argument("--voice", "-v", action="store_true", help="Run hands-free continuous voice chat")
    group.add_argument("--sync", action="store_true", help="Flush durable offline sync queue to MySQL")
    group.add_argument("--check", action="store_true", help="Run environment and model verification")
    group.add_argument("--download", "-d", action="store_true", help="Download required model weights")
    group.add_argument("--test-mic", action="store_true", help="Run microphone diagnostic test")
    group.add_argument("--test-tts", action="store_true", help="Run multilingual speech synthesis test")
    group.add_argument("--test-db", action="store_true", help="Test MySQL database connection")
    group.add_argument("--test-all", action="store_true", help="Run full automated test suite")
    
    args = parser.parse_args()

    try:
        if args.admin:
            print_banner()
            launch_admin_gui()
        elif args.web_admin:
            print_banner()
            launch_web_admin()
        elif args.cli:
            print_banner()
            launch_cli()
        elif args.voice:
            print_banner()
            launch_voice_chat()
        elif args.sync:
            run_sync()
        elif args.check:
            run_checks()
        elif args.download:
            run_download()
        elif args.test_mic:
            run_mic_test()
        elif args.test_tts:
            run_tts_test()
        elif args.test_db:
            run_db_test()
        elif args.test_all:
            run_all_tests()
        else:
            # Default action: Run the entire project!
            print_banner()
            launch_gui()
    except KeyboardInterrupt:
        print("\n\n👋 Mr. Beast has shut down cleanly. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
