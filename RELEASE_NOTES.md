# FTC Field Viewer - Release Notes

## Version 1.3.2 - Precision Measurement Controls (Latest)
*Released: October 2025*

### **New Features**
- **Measurement Snap Control**: Added optional grid snapping for measurement tools
  - Toggle "Snap measurements to grid" for precision control
  - Hold Shift while clicking to temporarily disable snapping
  - Works with all measurement tools (distance, angle, area)
  - Default: Snap enabled for maximum precision

### 🔧 **Improvements**
- Enhanced measurement precision with intelligent grid alignment
- Updated help documentation with snap feature guidance
- Improved measurement workflow for both precision and free-form needs

### 📖 **Updated Instructions**
- Added snap control documentation in Help tab
- Clarified measurement tool usage with precision options

---

## Version 1.3.1 - UI/UX Polish & Icon Fixes
*Released: September 2025*

### **Major UI Improvements**
- **Dedicated Help Tab**: Reorganized all instructions into comprehensive help interface
  - Complete usage guide covering all features
  - Organized sections: Quick Start, Controls, Shortcuts, Measurements, Advanced Features
  - Professional tabbed interface separating controls and documentation

- **Fixed Dark Theme Icon Visibility**: Resolved icon visibility issues
  - Custom white text icons replace invisible dark system icons
  - Perfect contrast against dark theme background
  - Unicode symbols for professional appearance (zoom ±, undo/redo ↶↷)
  - Consistent visual design across all toolbar elements

### **Technical Enhancements**
- Improved tab widget architecture for better organization
- Enhanced icon rendering system with anti-aliasing
- Theme-aware icon design for future extensibility

### 📚 **Documentation Updates**
- Comprehensive help system with logical topic grouping
- Step-by-step guides for all major features
- Pro tips section for advanced users

---

## Version 1.3.0 - Complete UX Overhaul
*Released: August 2025*

### **New User Experience**
This version represents a complete transformation from basic tool to professional-grade application.

#### **Quick Action Toolbar**
- **Professional Toolbar**: File, Edit, View, and Toggle operations
- **Modern Design**: Text-under-icon layout, moveable/floatable positioning
- **Smart Recent Files**: Quick access to recently opened configurations
- **Intelligent Tooltips**: Context-aware help for each tool

#### ⌨️ **Keyboard Shortcuts**
- **File Operations**: Ctrl+O (Open), Ctrl+S (Save), Ctrl+L (Load), Ctrl+Q (Exit)
- **Edit Operations**: Ctrl+Z (Undo), Ctrl+Y (Redo), Ctrl+A (Add Point), Delete (Remove)
- **View Controls**: Ctrl+Plus/Minus (Zoom), Ctrl+0 (Reset), Ctrl+G (Grid Toggle)
- **Measurement Tools**: Ctrl+M (Toggle Mode), Ctrl+T (Change Tool)

#### 🖱️ **Advanced Mouse Controls**
- **Context Menus**: Right-click for quick actions throughout the interface
- **Drag & Drop**: Full support for field images and point configurations
- **Multi-Select**: Advanced selection with Ctrl+Click and Shift+Click
- **Precision Controls**: Grid snapping with modifier key overrides

#### 🎛️ **Customizable Interface**
- **Moveable Panels**: Dock widgets can be repositioned anywhere
- **Floating Windows**: Detach panels for multi-monitor workflows
- **Collapsible Groups**: Organize workspace by hiding unused sections
- **Settings Persistence**: Interface layout automatically saved and restored

#### 🔄 **Smart Undo/Redo System**
- **Full Action History**: Every modification tracked with intelligent grouping
- **Visual Feedback**: Clear indication of undo/redo availability
- **Granular Control**: Individual point edits, bulk operations, and tool changes
- **Memory Efficient**: Optimized history management for large projects

#### 🎨 **Enhanced Visual Design**
- **Professional Appearance**: Modern Qt styling with consistent theming
- **Improved Icons**: Vector-based icons that scale perfectly at any size
- **Better Typography**: Optimized fonts and sizing for readability
- **Visual Hierarchy**: Clear information organization and grouping

### 🔧 **Technical Improvements**
- Robust signal/slot architecture for reliable operation
- Enhanced memory management for better performance
- Improved error handling with user-friendly messages
- Modular code structure for easier maintenance and extension

---

## Version 1.2.0 - Measurement Tools & Build System
*Released: July 2025*

### 🆕 **Comprehensive Measurement System**
- **Distance Measurement**: Click two points to measure distance with visual line indicator
- **Angle Measurement**: Click three points to measure angles with visual arc display
- **Area Measurement**: Click multiple points to define and measure polygonal areas
- **Interactive Mode**: Dedicated measurement mode with specialized UI controls
- **Real-time Feedback**: Live measurement display during point selection

### 📏 **Advanced Coordinate Systems**
- **Dual Coordinate Display**: Toggle between field coordinates (inches) and pixel coordinates
- **Real-time Updates**: Live coordinate display for cursor position and snapped points
- **Flexible Units**: Support for different measurement needs and workflows

### 👁️ **Enhanced Point Management**
- **Show/Hide Default Points**: Toggle visibility of pre-loaded field markers
- **Separate Point Types**: Independent management of default vs user-created points
- **Improved Visibility Controls**: Better point display options for cleaner visualization

### 📦 **Automated Build System**
- **PowerShell Build Script**: `build_release.ps1` for automated executable creation
- **Cross-Platform Support**: Batch file alternative for different environments
- **Automated Packaging**: ZIP creation and distribution preparation
- **PyInstaller Integration**: Standalone executable generation with dependencies

### 🔧 **Technical Enhancements**
- Enhanced mouse event handling for measurement interactions
- Improved coordinate system conversions (field ↔ pixel)
- Better UI organization with logical control grouping
- Robust signal handling for new measurement features

### 📖 **Documentation & Guides**
- Comprehensive measurement tool usage instructions
- Build system documentation and troubleshooting
- Updated README with new feature descriptions

---

## Version 1.1.0 - Foundation Features
*Released: June 2025*

### 🏗️ **Core Functionality**
- **Field Visualization**: Load and display FTC field maps
- **Point Creation**: Interactive point placement and editing
- **Grid System**: Precise grid snapping for accurate positioning
- **Coordinate System**: Field-based coordinate system for measurements
- **Data Persistence**: JSON import/export for point configurations

### 🎯 **Initial Feature Set**
- Basic field image loading and display
- Point creation with property editing
- Grid overlay with snapping functionality
- Simple coordinate display
- Configuration save/load capabilities

### 🔧 **Technical Foundation**
- PySide6/Qt-based GUI framework
- Graphics view architecture for scalable rendering
- JSON-based configuration format
- Cross-platform compatibility (Windows, macOS, Linux)

---

## Installation & Compatibility

### **System Requirements**
- **Operating System**: Windows 10/11, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher (for source installation)
- **Memory**: 512MB RAM minimum, 1GB recommended
- **Display**: 1024x768 minimum resolution

### **Installation Options**

#### Option 1: Standalone Executable (Recommended)
1. Download the latest release ZIP file
2. Extract to desired location
3. Run `ftc_field_viewer.exe` (Windows) or equivalent for your platform
4. No additional dependencies required

#### Option 2: From Source
```bash
# Clone repository
git clone https://github.com/Imagineer7/FTC-Field-Viewer.git
cd FTC-Field-Viewer

# Install dependencies
pip install -r requirements.txt

# Run application
python ftc_field_viewer.py
```

#### Option 3: Build Your Own Executable
```bash
# Windows PowerShell
.\build_release.ps1

# Or using batch file
build_release.bat

# Linux/macOS
chmod +x build_release.sh
./build_release.sh
```

---

## Quick Start Guide

### **Getting Started in 4 Steps**
1. **Open Field Image**: File → Open or drag & drop field image
2. **Load Points**: File → Load Points or use included default sets
3. **Create Points**: Right-click field to add new points
4. **Measure & Analyze**: Enable measurement mode for distance/angle/area analysis

### **Pro Tips**
- Use **Ctrl+G** to toggle grid visibility
- **Right-click** anywhere for context menus
- **Drag toolbar** to customize layout
- **Hold Shift** to override grid snapping
- **Ctrl+Z/Y** for unlimited undo/redo

---

## Support & Contributing

### **Getting Help**
- **In-App Help**: Click the Help tab for comprehensive guides
- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check README and wiki for detailed information

### **Contributing**
- Fork the repository and submit pull requests
- Report issues with detailed reproduction steps
- Suggest new features through GitHub discussions
- Help improve documentation and examples

---

## License
This project is released under the MIT License. See LICENSE file for details.

---

*For the latest updates and download links, visit: https://github.com/Imagineer7/FTC-Field-Viewer*