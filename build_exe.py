#!/usr/bin/env python3
"""
Local packaging script for building Windows executable
"""
import os
import sys
import shutil
import subprocess
import time

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"Cleaned {dir_name}")
            except PermissionError:
                print(f"Warning: Cannot clean {dir_name}, may be in use. Trying again...")
                time.sleep(1)
                try:
                    shutil.rmtree(dir_name)
                    print(f"Cleaned {dir_name}")
                except Exception as e:
                    print(f"Warning: Failed to clean {dir_name}: {e}")
                    print("Continuing anyway...")

def build_exe():
    """Build exe file"""
    # PyInstaller command parameters
    cmd = [
        'pyinstaller',
        '--clean',             # Clean PyInstaller cache and temporary files
        '-y',                  # Remove output directory without confirmation
        '--windowed',          # Do not display console window
        '--name=teshi',        # exe filename
        '--icon=teshi/assets/teshi_icon256.png',  # icon
        '--add-data=teshi/assets;assets',  # add resource files (包括所有子目录)
        '--paths=.',           # 添加当前目录到 Python 路径
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets', 
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=markdown',
        '--hidden-import=xlrd',
        # 收集整个 teshi 包
        '--collect-all=teshi',
        # 排除不需要的 PySide6 模块以减小体积
        '--exclude-module=PySide6.QtWebEngineCore',
        '--exclude-module=PySide6.QtWebEngineWidgets',
        '--exclude-module=PySide6.QtWebEngineQuick',
        '--exclude-module=PySide6.Qt3DCore',
        '--exclude-module=PySide6.Qt3DRender',
        '--exclude-module=PySide6.Qt3DAnimation',
        '--exclude-module=PySide6.Qt3DExtras',
        '--exclude-module=PySide6.Qt3DInput',
        '--exclude-module=PySide6.Qt3DLogic',
        '--exclude-module=PySide6.QtCharts',
        '--exclude-module=PySide6.QtDataVisualization',
        '--exclude-module=PySide6.QtQuick',
        '--exclude-module=PySide6.QtQuick3D',
        '--exclude-module=PySide6.QtQuickWidgets',
        '--exclude-module=PySide6.QtQml',
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
    
    # 如果目标目录存在，先删除
    release_teshi_dir = f'{release_dir}/teshi'
    if os.path.exists(release_teshi_dir):
        shutil.rmtree(release_teshi_dir)
        print(f"Cleaned existing {release_teshi_dir}")
    
    # Copy the entire application directory
    if os.path.exists('dist/teshi'):
        shutil.copytree('dist/teshi', release_teshi_dir)
    else:
        print("Error: Cannot find the built application directory")
        return False
    
    # Copy README
    if os.path.exists('README.md'):
        shutil.copy('README.md', f'{release_dir}/README.md')
    
    print(f"Release package created in {release_dir} directory")
    return True

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