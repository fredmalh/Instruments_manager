import os
import sys
import shutil
from PyInstaller.__main__ import run

def build_application():
    # Get the directory where the script is located
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Base directory: {base_dir}")
    
    # Create dist directory if it doesn't exist
    dist_dir = os.path.join(base_dir, 'dist')
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)
        print(f"Created dist directory: {dist_dir}")
    else:
        print(f"Dist directory already exists: {dist_dir}")
    
    # Build the application using PyInstaller
    print("Building application with PyInstaller...")
    run([
        'main.py',
        '--onefile',
        '--windowed',
        '--name=main',
        '--distpath=' + dist_dir,
        '--workpath=' + os.path.join(base_dir, 'build'),
        '--specpath=' + base_dir,
        '--clean'
    ])
    
    # Verify the executable was created
    exe_path = os.path.join(dist_dir, 'main.exe')
    if os.path.exists(exe_path):
        print(f"Application built successfully at: {exe_path}")
    else:
        print(f"ERROR: Application was not built at: {exe_path}")
        return
    
    print("\nBuild completed successfully!")
    print(f"Application is in: {dist_dir}")
    print("\nTo run the application:")
    print(f"1. Navigate to: {dist_dir}")
    print("2. Run main.exe")
    print("\nNote: The database will be created in the same directory as the executable (lab_instruments.db)")

if __name__ == "__main__":
    build_application()