"""
GUI Model Downloader - Downloads required model files
"""
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import os
import threading

class ModelDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Download Required Models")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Model URLs
        self.models = {
            'age_net.caffemodel': {
                'url': 'https://www.dropbox.com/s/xfb20y596869vbb/age_net.caffemodel?dl=1',
                'size': '~23 MB',
                'description': 'Age Prediction Model'
            },
            'gender_net.caffemodel': {
                'url': 'https://www.dropbox.com/s/iyv483wz7ztr9gh/gender_net.caffemodel?dl=1',
                'size': '~23 MB',
                'description': 'Gender Classification Model'
            }
        }
        
        self.setup_ui()
        self.check_existing_models()
    
    def setup_ui(self):
        # Title
        title = tk.Label(
            self.root,
            text="Download Required Models",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=15
        )
        title.pack(fill=tk.X)
        
        # Info frame
        info_frame = tk.Frame(self.root, bg="#ecf0f1")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        info_text = """
The application needs 2 model files to work:

1. Age Prediction Model (~23 MB)
2. Gender Classification Model (~23 MB)

Click the buttons below to download them automatically.
This will take 2-5 minutes depending on your internet speed.
        """
        
        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=("Arial", 10),
            bg="#ecf0f1",
            justify=tk.LEFT
        )
        info_label.pack(pady=10)
        
        # Models frame
        models_frame = tk.LabelFrame(
            info_frame,
            text="Models",
            font=("Arial", 11, "bold"),
            bg="#ecf0f1"
        )
        models_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Age model
        self.age_frame = tk.Frame(models_frame, bg="#ecf0f1")
        self.age_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.age_label = tk.Label(
            self.age_frame,
            text="Age Model: Not Downloaded",
            font=("Arial", 10),
            bg="#ecf0f1",
            anchor="w"
        )
        self.age_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.age_btn = tk.Button(
            self.age_frame,
            text="Download",
            bg="#3498db",
            fg="white",
            command=lambda: self.download_model('age_net.caffemodel'),
            width=15
        )
        self.age_btn.pack(side=tk.RIGHT)
        
        # Age progress
        self.age_progress = ttk.Progressbar(
            models_frame,
            mode='indeterminate',
            length=500
        )
        self.age_progress.pack(padx=10, pady=5)
        
        # Gender model
        self.gender_frame = tk.Frame(models_frame, bg="#ecf0f1")
        self.gender_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.gender_label = tk.Label(
            self.gender_frame,
            text="Gender Model: Not Downloaded",
            font=("Arial", 10),
            bg="#ecf0f1",
            anchor="w"
        )
        self.gender_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.gender_btn = tk.Button(
            self.gender_frame,
            text="Download",
            bg="#3498db",
            fg="white",
            command=lambda: self.download_model('gender_net.caffemodel'),
            width=15
        )
        self.gender_btn.pack(side=tk.RIGHT)
        
        # Gender progress
        self.gender_progress = ttk.Progressbar(
            models_frame,
            mode='indeterminate',
            length=500
        )
        self.gender_progress.pack(padx=10, pady=5)
        
        # Bottom buttons
        button_frame = tk.Frame(self.root, bg="#ecf0f1")
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.download_all_btn = tk.Button(
            button_frame,
            text="Download All Models",
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            command=self.download_all,
            height=2
        )
        self.download_all_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.close_btn = tk.Button(
            button_frame,
            text="Close",
            bg="#95a5a6",
            fg="white",
            font=("Arial", 11, "bold"),
            command=self.root.destroy,
            height=2
        )
        self.close_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Status: Ready",
            font=("Arial", 9),
            bg="#34495e",
            fg="white",
            anchor="w",
            padx=10
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def check_existing_models(self):
        """Check which models are already downloaded"""
        models_dir = 'models'
        
        # Check age model
        if os.path.exists(os.path.join(models_dir, 'age_net.caffemodel')):
            size_mb = os.path.getsize(os.path.join(models_dir, 'age_net.caffemodel')) / (1024 * 1024)
            self.age_label.config(text=f"Age Model: ✓ Downloaded ({size_mb:.1f} MB)", fg="green")
            self.age_btn.config(state=tk.DISABLED, text="✓ Done")
        
        # Check gender model
        if os.path.exists(os.path.join(models_dir, 'gender_net.caffemodel')):
            size_mb = os.path.getsize(os.path.join(models_dir, 'gender_net.caffemodel')) / (1024 * 1024)
            self.gender_label.config(text=f"Gender Model: ✓ Downloaded ({size_mb:.1f} MB)", fg="green")
            self.gender_btn.config(state=tk.DISABLED, text="✓ Done")
    
    def download_model(self, model_name):
        """Download a specific model"""
        thread = threading.Thread(target=self._download_thread, args=(model_name,), daemon=True)
        thread.start()
    
    def _download_thread(self, model_name):
        """Download thread"""
        model_info = self.models[model_name]
        url = model_info['url']
        destination = os.path.join('models', model_name)
        
        # Update UI
        if model_name == 'age_net.caffemodel':
            self.age_btn.config(state=tk.DISABLED)
            self.age_progress.start()
            self.age_label.config(text=f"Age Model: Downloading...")
        else:
            self.gender_btn.config(state=tk.DISABLED)
            self.gender_progress.start()
            self.gender_label.config(text=f"Gender Model: Downloading...")
        
        self.status_label.config(text=f"Status: Downloading {model_name}...")
        
        try:
            # Download file
            urllib.request.urlretrieve(url, destination)
            
            # Success
            size_mb = os.path.getsize(destination) / (1024 * 1024)
            
            if model_name == 'age_net.caffemodel':
                self.age_progress.stop()
                self.age_label.config(text=f"Age Model: ✓ Downloaded ({size_mb:.1f} MB)", fg="green")
                self.age_btn.config(text="✓ Done")
            else:
                self.gender_progress.stop()
                self.gender_label.config(text=f"Gender Model: ✓ Downloaded ({size_mb:.1f} MB)", fg="green")
                self.gender_btn.config(text="✓ Done")
            
            self.status_label.config(text=f"Status: {model_name} downloaded successfully!")
            messagebox.showinfo("Success", f"{model_info['description']} downloaded successfully!")
            
        except Exception as e:
            # Error
            if model_name == 'age_net.caffemodel':
                self.age_progress.stop()
                self.age_label.config(text=f"Age Model: ✗ Download Failed", fg="red")
                self.age_btn.config(state=tk.NORMAL)
            else:
                self.gender_progress.stop()
                self.gender_label.config(text=f"Gender Model: ✗ Download Failed", fg="red")
                self.gender_btn.config(state=tk.NORMAL)
            
            self.status_label.config(text=f"Status: Download failed")
            messagebox.showerror("Error", f"Failed to download {model_name}:\n{str(e)}")
    
    def download_all(self):
        """Download all models"""
        for model_name in self.models.keys():
            model_path = os.path.join('models', model_name)
            if not os.path.exists(model_path):
                self.download_model(model_name)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModelDownloader(root)
    root.mainloop()
