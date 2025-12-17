#!/usr/bin/env python3
"""
Local packaging script for building Windows executable
"""
import os
import sys
import shutil
import subprocess

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Cleaned {dir_name}")

def build_exe():
    """Build exe file"""
    # PyInstaller command parameters
    cmd = [
        'pyinstaller',
        '--windowed',          # Do not display console window
        '--name=teshi',        # exe filename
        '--icon=teshi/assets/teshi_icon256.png',  # icon
        '--add-data=teshi/assets;assets',  # add resource files
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets', 
        '--hidden-import=PySide6.QtGui',
        'teshi/main.py'
    ]
    
    print("Starting packaging...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Packaging successful!")
        print(f"Executable location: {os.path.abspath('dist/teshi/teshi.exe')}")
        print(f"Entire application directory: {os.path.abspath('dist/teshi/')}")
    else:
        print("Packaging failed!")
        print("Error information:")
        print(result.stderr)
        return False
    
    return True

def create_release_package():
    """Create release package"""
    release_dir = 'release'
    if not os.path.exists(release_dir):
        os.makedirs(release_dir)
    
    # Copy the entire application directory
    if os.path.exists('dist/teshi'):
        shutil.copytree('dist/teshi', f'{release_dir}/teshi')
    else:
        print("Error: Cannot find the built application directory")
        return False
    
    # Copy README
    if os.path.exists('README.md'):
        shutil.copy('README.md', f'{release_dir}/README.md')
    
    print(f"Release package created in {release_dir} directory")

if __name__ == '__main__':
    print("=== Teshi Windows EXE Build Tool ===")
    
    # Check dependencies
    try:
        import PyInstaller
    except ImportError:
        print("Please install PyInstaller first: pip install pyinstaller")
        sys.exit(1)
    
    clean_build_dirs()
    
    if build_exe():
        if create_release_package():
            print("\nBuild completed!")
            print("You can run dist/teshi/teshi.exe to test the program")
            print("Release package created in release/teshi/ directory")
        else:
            print("\nBuild failed!")
    else:
        print("\nBuild failed, please check error information")
        sys.exit(1)