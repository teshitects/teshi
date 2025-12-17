# Teshi Windows EXE Build Guide

## Local Build

### 1. Install Dependencies
```bash
# Install project dependencies
poetry install

# Install build dependencies
poetry install --with build
```

### 2. Use Build Script
```bash
python build_exe.py
```

### 3. Manual PyInstaller Usage
```bash
pyinstaller --windowed --name teshi --icon=teshi/assets/teshi_icon256.png --add-data "teshi/assets;assets" teshi/main.py
```

## GitHub Actions Automatic Build

### Trigger Methods

1. **Auto-build on tag push**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Manual trigger**
   - In the GitHub repository's Actions page
   - Select "Build Windows EXE" workflow
   - Click "Run workflow"

### Build Artifacts

- After build completion, exe files are automatically uploaded as GitHub Artifacts
- If triggered by tag, GitHub Release is also created automatically
- You can download `teshi-windows-x64` artifacts to get the complete package

## Build Parameter Explanation

- `--windowed`: Do not display console window (GUI application)
- `--name`: Specify exe filename
- `--icon`: Specify application icon
- `--add-data`: Add resource files (format: source path;target path)
- `--hidden-import`: Explicitly specify modules to import

## Advantages of Multi-file Packaging

1. **Faster startup**: No need to extract to temporary directory
2. **Resource access**: Direct filesystem access, avoid memory usage
3. **Debug friendly**: Can view specific dependency files
4. **Flexible updates**: Can update individual files separately

## Notes

1. **Resource file paths**: Use relative paths when referencing resource files in the program, PyInstaller handles automatically
2. **Dependency check**: Ensure all files in `teshi/assets` directory are correctly packaged
3. **Testing**: Must test in a clean Windows environment after packaging
4. **Antivirus software**: Some antivirus software may false positive, this is a common PyInstaller issue

## Troubleshooting

If you encounter packaging issues:

1. Check if Python version is 3.13
2. Ensure all dependencies are correctly installed
3. Check error information in build logs
4. Try building in a virtual environment

## Release

After build completion, you will get:
- `dist/teshi/`: Directory containing main program and all dependency files
- `dist/teshi/teshi.exe`: Main program file
- `release/teshi/`: Distributable complete application directory