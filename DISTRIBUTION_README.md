# FTC Field Viewer - Standalone Executable

This is a standalone Windows executable version of the FTC Field Viewer that can run on any Windows computer without requiring Python or additional installations.

## What's Included

- `FTC_Field_Viewer.exe` - The main executable (45.6 MB)
- All required Python libraries and dependencies are bundled inside the executable
- Field Maps and Default Points are included in the executable

## How to Use

1. **Download the executable**: Get `FTC_Field_Viewer.exe` from the `dist` folder
2. **Run the program**: Double-click `FTC_Field_Viewer.exe` to launch the application
3. **No installation required**: The executable is self-contained and portable

## System Requirements

- Windows 7 or later (64-bit)
- No Python installation required
- No additional libraries need to be installed

## Features

- Interactive FTC field map viewer
- Grid overlay system
- Editable and saveable points
- Support for custom field maps and point configurations
- Load/save point configurations as JSON files

## Command Line Usage

You can also run the executable from command line with arguments:
```
FTC_Field_Viewer.exe [arguments]
```

## Distribution

This executable can be distributed to other users by simply copying the `FTC_Field_Viewer.exe` file. No installation or setup is required on the target computer.

## File Size

The executable is approximately 45.6 MB due to the included PySide6 (Qt) GUI framework and all Python dependencies.

## Build Information

- Built with PyInstaller 6.16.0
- Python 3.13.3
- PySide6 (Qt for Python)
- Windows 11 target platform

## Troubleshooting

If the executable doesn't start:
1. Make sure you're running on a 64-bit Windows system
2. Try running as administrator if you get permission errors
3. Check Windows Defender or antivirus software - they sometimes flag PyInstaller executables as suspicious
4. Ensure the executable wasn't corrupted during download/transfer

## Notes

- The Zone Tester script is not included in this build as requested
- Field Maps and Default Points folders are embedded in the executable
- The executable will look for additional field maps and point JSON files in the same directory if needed