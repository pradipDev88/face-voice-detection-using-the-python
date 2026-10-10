"""
Quick Model Downloader - Command Line Version
Downloads the required model files automatically
"""
import urllib.request
import os
import sys

def download_file(url, destination, description):
    """Download a file with progress"""
    print(f"\n{'='*60}")
    print(f"Downloading: {description}")
    print(f"URL: {url}")
    print(f"Destination: {destination}")
    print(f"{'='*60}")
    
    try:
        def progress_hook(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            sys.stdout.write(f"\rProgress: {percent}% ")
            sys.stdout.flush()
        
        urllib.request.urlretrieve(url, destination, progress_hook)
        
        size_mb = os.path.getsize(destination) / (1024 * 1024)
        print(f"\n✓ Downloaded successfully! ({size_mb:.1f} MB)")
        return True
        
    except Exception as e:
        print(f"\n✗ Download failed: {str(e)}")
        return False

def main():
    print("="*60)
    print("QUICK MODEL DOWNLOADER")
    print("="*60)
    print("\nThis will download 2 model files (~46 MB total)")
    print("Estimated time: 2-5 minutes\n")
    
    # Create models directory if needed
    if not os.path.exists('models'):
        os.makedirs('models')
        print("✓ Created models/ directory")
    
    models = [
        {
            'name': 'age_net.caffemodel',
            'url': 'https://www.dropbox.com/s/xfb20y596869vbb/age_net.caffemodel?dl=1',
            'description': 'Age Prediction Model (~23 MB)'
        },
        {
            'name': 'gender_net.caffemodel',
            'url': 'https://www.dropbox.com/s/iyv483wz7ztr9gh/gender_net.caffemodel?dl=1',
            'description': 'Gender Classification Model (~23 MB)'
        }
    ]
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    for model in models:
        destination = os.path.join('models', model['name'])
        
        # Check if already exists
        if os.path.exists(destination):
            size_mb = os.path.getsize(destination) / (1024 * 1024)
            print(f"\n✓ {model['description']}")
            print(f"  Already exists ({size_mb:.1f} MB) - Skipping")
            skipped += 1
            continue
        
        # Download
        if download_file(model['url'], destination, model['description']):
            downloaded += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)
    print(f"Downloaded: {downloaded}")
    print(f"Skipped (already exist): {skipped}")
    print(f"Failed: {failed}")
    print("="*60)
    
    if failed == 0:
        print("\n✓ All models ready!")
        print("\nYou can now run the application:")
        print("  python main.py")
    else:
        print("\n⚠ Some downloads failed.")
        print("Please try again or download manually.")
        print("See DOWNLOAD_MODELS_NOW.md for manual download links.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user.")
    except Exception as e:
        print(f"\n\nError: {str(e)}")
