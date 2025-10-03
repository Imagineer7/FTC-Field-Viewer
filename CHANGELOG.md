# FTC Field Viewer - Changelog

## Version 1.2.0 - Measurement Tools & Enhanced Features

### 🆕 New Features
- **Comprehensive Measurement Tools System**
  - Distance measurement between two points (with visual line indicator)
  - Angle measurement between three points (with visual angle arc)
  - Area measurement for polygonal regions (with visual polygon outline)
  - Interactive measurement mode with dedicated UI controls

- **Enhanced Point Management**
  - Show/Hide default points toggle for cleaner field visualization
  - Separate management of default vs user-created points
  - Improved point visibility controls

- **Advanced Coordinate Display**
  - Toggle between field coordinates (inches) and pixel coordinates
  - Real-time coordinate updates for both cursor and snapped positions
  - Dual coordinate system support for different measurement needs

- **Automated Build System**
  - PowerShell build script (`build_release.ps1`) for automated executable creation
  - Batch file alternative (`build_release.bat`) for different environments
  - Automated packaging and ZIP creation for distribution

### 🔧 Technical Improvements
- Enhanced mouse event handling for measurement interactions
- Improved coordinate system conversions (field ↔ pixel)
- Better UI organization with measurement controls grouped logically
- Robust signal handling for new measurement features

### 📦 Build & Distribution
- Added PyInstaller configuration for standalone executable creation
- Automated build scripts with error handling and cleanup
- Improved packaging for easier distribution

### 🔄 Code Organization
- Separated measurement logic into dedicated methods
- Improved class structure for better maintainability
- Enhanced error handling throughout the application

---

## Version 1.1.0 - Previous Features
- Basic field visualization
- Point creation and editing
- Grid snapping functionality
- Field coordinate system
- JSON import/export capabilities

---

## Installation & Usage

### Running from Source
```bash
pip install -r requirements.txt
python ftc_field_viewer.py
```

### Building Executable
```bash
# Windows PowerShell
.\build_release.ps1

# Or using batch file
build_release.bat
```

### Measurement Tools Usage
1. Enable "Measurement Mode" checkbox
2. Select measurement tool from dropdown (Distance/Angle/Area)
3. Click points on the field to take measurements
4. Use "Clear Measurements" to reset
5. Toggle "Show Pixel Coordinates" for different coordinate display

### New Features Guide
- **Show Default Points**: Toggle visibility of pre-loaded field points
- **Measurement Mode**: Enter interactive measurement mode
- **Coordinate Display**: Switch between inches and pixels
- **Build Scripts**: Automated executable creation for distribution