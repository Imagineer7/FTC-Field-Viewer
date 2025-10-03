@echo off
:: Simple batch wrapper for the PowerShell build script
:: This makes it easier for users who prefer batch files

echo FTC Field Viewer - Build Script
echo ================================

:: Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell detected'" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PowerShell is required but not found!
    echo Please install PowerShell or run build_release.ps1 directly.
    pause
    exit /b 1
)

:: Run the PowerShell script
echo Running build script...
powershell -ExecutionPolicy Bypass -File "%~dp0build_release.ps1" %*

if errorlevel 1 (
    echo.
    echo Build failed! Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Check the generated ZIP file for your release package.
pause