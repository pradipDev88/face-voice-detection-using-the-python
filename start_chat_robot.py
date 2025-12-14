"""
Quick Start - Mr. Beast Robot with Chat Mode
"""
import tkinter as tk
from ui.robot_ui import MrBeastUI

if __name__ == "__main__":
    print("="*60)
    print("🤖 Starting Mr. Beast Robot with Chat Mode")
    print("="*60)
    print("\nFeatures:")
    print("✅ Real-time face detection")
    print("✅ Age & gender prediction")
    print("✅ Voice conversation (TTS/STT)")
    print("✅ Continuous chat mode")
    print("✅ Face recognition & profile creation")
    print("\nClick '💬 Start Chat' button to begin conversation!")
    print("="*60)
    
    root = tk.Tk()
    app = MrBeastUI(root)
    root.mainloop()
