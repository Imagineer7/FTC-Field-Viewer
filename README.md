# FTC Field Viewer

[![Version](https://img.shields.io/badge/version-1.3.2-blue.svg)](https://github.com/Imagineer7/FTC-Field-Viewer/releases)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-GNU-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/Imagineer7/FTC-Field-Viewer)

An **interactive application** for visualizing First Tech Challenge (FTC) field maps with advanced measurement tools, coordinate systems, and point management capabilities.

Purpose of this program is to make it easy to find and get coordinates for points or zones in the FTC field.

![FTC Field Viewer Interface](Field%20Maps/decode-dark.png)

## ✨ Key Features

### **Measurement Tools**
- **Distance Measurement**: Click two points for precise distance calculations
- **Angle Measurement**: Three-point angle measurement with visual arc display
- **Area Measurement**: Polygon area calculation for complex regions
- **Grid Snapping**: Optional precision snapping with Shift override
- **Real-time Feedback**: Live measurements during point selection

### **Modern User Interface**
- **Quick Action Toolbar**: Professional toolbar with file, edit, view, and toggle operations
- **Comprehensive Keyboard Shortcuts**: Streamlined workflow with full keyboard support
- **Customizable Layout**: Moveable, dockable panels and floating windows
- **Context Menus**: Right-click access to relevant actions throughout the interface
- **Dark Theme**: Professional appearance with optimized icon visibility

### **Coordinate Systems**
- **Dual Display Modes**: Toggle between field coordinates (inches) and pixel coordinates
- **Grid Overlay**: Precise positioning with customizable grid snapping
- **Real-time Cursor Tracking**: Live coordinate display for precise positioning
- **Field-to-Pixel Conversion**: Accurate coordinate system transformations

### **Point Management**
- **Interactive Point Creation**: Right-click field placement with property editing
- **Drag & Drop Support**: Direct manipulation of points and file loading
- **Default Point Sets**: Pre-configured points for standard FTC fields
- **Show/Hide Controls**: Toggle visibility of different point categories
- **Multi-Select Operations**: Bulk editing with Ctrl+Click and Shift+Click

### **Field Image System**
- **Multiple Field Support**: Instant switching between different FTC field maps
- **Auto-Resize Technology**: Consistent coordinate scaling across different image sources
- **Thumbnail Browser**: Visual field selection with preview thumbnails
- **Automatic Discovery**: Scans common directories for field images
- **Format Support**: PNG, JPG, JPEG image formats

### **Smart Data Management**
- **Unlimited Undo/Redo**: Complete action history with intelligent grouping
- **JSON Configuration**: Save and load point configurations
- **Recent Files**: Quick access to recently used configurations
- **Auto-Save**: Persistent interface settings and preferences

### 📦 **Easy Distribution**
- **Standalone Executables**: No Python installation required
- **Cross-Platform**: Windows, macOS, and Linux support
- **Automated Build System**: PowerShell and batch scripts for easy deployment

## Quick Start

### Option 1: Download Executable (Recommended)
1. Download the latest release from [Releases](https://github.com/Imagineer7/FTC-Field-Viewer/releases)
2. Extract the ZIP file to your desired location
3. Run `ftc_field_viewer.exe` (Windows) or equivalent for your platform
4. Start visualizing immediately - no setup required!

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/Imagineer7/FTC-Field-Viewer.git
cd FTC-Field-Viewer

# Install dependencies
pip install -r requirements.txt

# Launch the application
python ftc_field_viewer.py
```

## 📋 Getting Started Guide

### **Basic Workflow**
1. **Load Field Image**: File → Open or drag & drop your field image
2. **Select Field Points**: Use included defaults or File → Load Points
3. **Create Custom Points**: Right-click anywhere on the field
4. **Take Measurements**: Enable measurement mode and select your tool
5. **Save Configuration**: File → Save Points for future use

### **Pro Tips**
- **Ctrl+G**: Toggle grid visibility
- **Ctrl+M**: Toggle measurement mode
- **Ctrl+Z/Y**: Undo/redo actions
- **Right-click**: Access context menus anywhere
- **Shift+Click**: Override grid snapping temporarily
- **Drag toolbar**: Customize interface layout

## 🔧 System Requirements

- **Operating System**: Windows 10/11, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.8+ (for source installation only)
- **Memory**: 512MB RAM minimum, 1GB recommended
- **Display**: 1024x768 minimum resolution

## 📖 Documentation

- **[Release Notes](RELEASE_NOTES.md)**: Detailed version history and features
- **[Quick Start Guide](QUICK_START.md)**: Step-by-step beginner tutorial
- **[Build Instructions](BUILD_INSTRUCTIONS.md)**: Creating your own executable

## 🤝 Contributing

We welcome contributions! Here's how you can help:

- **Report Bugs**: Use GitHub Issues with detailed reproduction steps
- **Request Features**: Submit feature requests through GitHub Discussions
- **Submit Pull Requests**: Fork the repo and submit your improvements
- **Improve Documentation**: Help expand guides and examples

## 📄 License

This project is licensed under the GNU License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [PySide6](https://www.qt.io/qt-for-python) for modern Qt GUI framework
- Inspired by the FIRST Tech Challenge community
- Special thanks to all contributors and users providing feedback

---

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/Imagineer7/FTC-Field-Viewer/issues)
- **Documentation**: Check the Help tab in the application for comprehensive guides
- **Community**: Join discussions in the [GitHub Discussions](https://github.com/Imagineer7/FTC-Field-Viewer/discussions)

**⭐ Star this repository if you find it useful!**

---

*Made with ❤️ for the FTC community*
