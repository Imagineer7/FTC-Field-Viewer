# Build Scripts Documentation

This document explains how to use the automated build scripts to compile and package the FTC Field Viewer for release.

## Overview

The build system consists of two scripts:
- **`build_release.ps1`** - Main PowerShell script with full functionality
- **`build_release.bat`** - Simple batch wrapper for the PowerShell script

## Quick Start

### Option 1: Using the Batch File (Recommended for beginners)
```cmd
# Simple build with automatic version detection
build_release.bat

# Build with specific version
build_release.bat -Version "v2.1.0"
```

### Option 2: Using PowerShell Directly
```powershell
# Simple build with automatic version detection
.\build_release.ps1

# Build with specific version
.\build_release.ps1 -Version "v2.1.0"

# Advanced options
.\build_release.ps1 -Version "v2.1.0" -SkipClean -SkipBuild
```

## What the Scripts Do

### 1. **Prerequisites Check**
- Verifies Python is installed
- Installs PyInstaller if missing
- Checks for required files

### 2. **Version Detection** (if not specified)
- Attempts to get version from git tags
- Looks for `__version__` in Python files  
- Falls back to timestamp version

### 3. **Clean Previous Builds**
- Removes `build/`, `dist/`, `__pycache__/` directories
- Deletes `.pyc` files

### 4. **Build Executable**
- Runs PyInstaller with the spec file
- Creates standalone executable in `dist/`
- Reports executable size

### 5. **Create Release Package**
- Creates versioned release directory
- Copies executable and documentation
- Includes sample Field Maps and Default Points
- Generates release notes
- Creates ZIP file for GitHub upload

## Command Line Options

### PowerShell Script Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `-Version` | Specify release version | `-Version "v2.1.0"` |
| `-SkipClean` | Skip cleaning previous builds | `-SkipClean` |
| `-SkipBuild` | Skip building executable | `-SkipBuild` |
| `-SkipPackage` | Skip creating release package | `-SkipPackage` |

### Usage Examples

```powershell
# Full build with custom version
.\build_release.ps1 -Version "v2.1.0"

# Only create package (if executable already exists)
.\build_release.ps1 -Version "v2.1.0" -SkipBuild

# Build without cleaning (faster for testing)
.\build_release.ps1 -SkipClean

# Only build executable, no packaging
.\build_release.ps1 -SkipPackage
```

## Output Files

After a successful build, you'll have:

### In `dist/` folder:
- `FTC_Field_Viewer.exe` - The standalone executable
- `Run_FTC_Field_Viewer.bat` - Convenience launcher

### In project root:
- `FTC-Field-Viewer-[version].zip` - Complete release package

### Release ZIP Contents:
- `FTC_Field_Viewer.exe` - Main executable
- `Run_FTC_Field_Viewer.bat` - Launcher script
- `README.md` - Project documentation
- `DISTRIBUTION_README.md` - User instructions
- `LICENSE` - License file
- `RELEASE_NOTES.txt` - Generated release notes
- `Field Maps/` - Sample field images
- `Default Points/` - Sample point configurations
- `points.json` - Sample points file

## Troubleshooting

### Common Issues

**"Python is not installed or not in PATH"**
- Install Python and ensure it's in your system PATH
- Or run from a Python environment where Python is available

**"PyInstaller build failed"**
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Ensure `ftc_field_viewer.spec` file exists and is valid

**"PowerShell execution policy error"**
- Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Or use the batch file which handles this automatically

**"ZIP creation failed"**
- Ensure you have write permissions in the project directory
- Check that PowerShell version supports `Compress-Archive` (Windows 8.1+)

### Manual Steps

If the script fails, you can run the steps manually:

```powershell
# 1. Clean
Remove-Item build, dist, __pycache__ -Recurse -Force -ErrorAction SilentlyContinue

# 2. Build
pyinstaller ftc_field_viewer.spec --clean

# 3. Package (manual)
# Create a folder with all files and ZIP it manually
```

## Integration with Development Workflow

### For Regular Development
```cmd
# Quick build for testing
build_release.bat -SkipPackage
```

### For Release Preparation
```cmd
# Full release build
build_release.bat -Version "v2.1.0"
```

### For GitHub Releases
1. Run the build script with your version number
2. Upload the generated ZIP file to GitHub releases
3. Use the generated `RELEASE_NOTES.txt` as release description

## Customization

### Adding Version to Python File
Add this line to `ftc_field_viewer.py` for automatic version detection:
```python
__version__ = "2.1.0"
```

### Modifying Build Process
Edit `build_release.ps1` to:
- Change included files
- Modify ZIP structure
- Add custom build steps
- Change executable name

## Requirements

- **Windows** (PowerShell script is Windows-specific)
- **Python 3.7+** with pip
- **PyInstaller** (auto-installed if missing)
- **Git** (optional, for version detection from tags)