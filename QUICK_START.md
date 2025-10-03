# Quick Start Guide for Build Scripts

The PowerShell syntax error has been resolved and the build system is now fully functional.

### **Quick Commands:**

```cmd
# Build with automatic version detection (from __version__ in Python file)
build_release.bat

# Build with specific version
build_release.bat -Version "v2.1.0"

# Build only executable (no ZIP package)
build_release.bat -SkipPackage

# Clean build (removes old files first)
build_release.bat -Version "v2.1.0"
```

### 🔧 **What Was Fixed:**

1. **PowerShell Regex Syntax Error** - Fixed the version detection regex pattern
2. **Enhanced Cleanup** - Now removes old release ZIP files and directories
3. **Version Detection** - Added `__version__ = "2.0.0"` to the Python file for automatic detection

### 📦 **Current Setup:**

- **Automatic Version**: Script detects version "2.0.0" from `ftc_field_viewer.py`
- **Complete Cleanup**: Removes old builds, ZIPs, and temporary files
- **Error Handling**: Proper error checking and user feedback
- **Release Ready**: Creates GitHub-ready ZIP packages

### 📝 **Next Steps:**

1. Run `build_release.bat` to create your first release
2. Upload the generated ZIP to GitHub releases
3. Update the version number in `ftc_field_viewer.py` for future releases

The build system is now ready for production use!