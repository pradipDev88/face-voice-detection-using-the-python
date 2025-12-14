"""
Mr. Beast - Hybrid Voice Robot
Main Application with Auto-Startup
Automatically opens camera, greets user, and starts listening
"""
import tkinter as tk
from ui.robot_ui import MrBeastUI

def main():
    """Main entry point with auto-startup"""
    print("="*60)
    print("🤖 Starting Mr. Beast - Hybrid Voice Robot")
    print("="*60)
    
    # Create Tkinter root
    root = tk.Tk()
    
    # Create and run application (auto-starts everything)
    app = MrBeastUI(root)
    
    # Start Tkinter main loop
    root.mainloop()

if __name__ == "__main__":
    main()
