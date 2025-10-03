# FTC Field Viewer - Automated Build and Release Script
# This script automates the process of building the executable and creating a release package

param(
    [string]$Version = "",
    [switch]$SkipClean = $false,
    [switch]$SkipBuild = $false,
    [switch]$SkipPackage = $false
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-Status {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor $InfoColor
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Step "FTC Field Viewer - Automated Build Script"
Write-Status "Build started at: $(Get-Date)" -Color $InfoColor

# Check prerequisites
Write-Step "Checking Prerequisites"

if (-not (Test-Command "python")) {
    Write-Status "ERROR: Python is not installed or not in PATH" -Color $ErrorColor
    exit 1
}

if (-not (Test-Command "pyinstaller")) {
    Write-Status "WARNING: PyInstaller not found. Installing..." -Color $WarningColor
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Status "ERROR: Failed to install PyInstaller" -Color $ErrorColor
        exit 1
    }
}

# Check if required files exist
$RequiredFiles = @("ftc_field_viewer.py", "ftc_field_viewer.spec")
foreach ($file in $RequiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Status "ERROR: Required file not found: $file" -Color $ErrorColor
        exit 1
    }
}

Write-Status "All prerequisites met!" -Color $SuccessColor

# Auto-detect version if not provided
if ($Version -eq "") {
    Write-Step "Auto-detecting Version"
    
    # Try to get version from git tag
    if (Test-Command "git") {
        try {
            $GitTag = git describe --tags --abbrev=0 2>$null
            if ($GitTag -and $LASTEXITCODE -eq 0) {
                $Version = $GitTag.Trim()
                Write-Status "Found git tag: $Version" -Color $InfoColor
            }
        }
        catch {
            # Git tag failed, continue
        }
    }
    
    # If no git tag, try to extract version from Python file
    if ($Version -eq "") {
        $PythonContent = Get-Content "ftc_field_viewer.py" -Raw
        $VersionMatch = [regex]::Match($PythonContent, "__version__\s*=\s*[`"']([^`"']+)[`"']")
        if ($VersionMatch.Success) {
            $Version = $VersionMatch.Groups[1].Value
            Write-Status "Found version in Python file: $Version" -Color $InfoColor
        }
    }
    
    # Default version if nothing found
    if ($Version -eq "") {
        $Version = "v$(Get-Date -Format 'yyyyMMdd-HHmm')"
        Write-Status "Using timestamp version: $Version" -Color $WarningColor
    }
}

Write-Status "Building version: $Version" -Color $InfoColor

# Clean previous builds
if (-not $SkipClean) {
    Write-Step "Cleaning Previous Builds"
    
    $DirsToClean = @("build", "dist", "__pycache__")
    foreach ($dir in $DirsToClean) {
        if (Test-Path $dir) {
            Write-Status "Removing $dir..." -Color $InfoColor
            Remove-Item $dir -Recurse -Force
        }
    }
    
    # Clean .pyc files
    Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    
    # Clean old release files and directories
    Write-Status "Cleaning old release files..." -Color $InfoColor
    Get-ChildItem -Filter "FTC-Field-Viewer-*.zip" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Filter "release-*" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Status "Cleanup completed!" -Color $SuccessColor
}

# Build executable
if (-not $SkipBuild) {
    Write-Step "Building Executable"
    
    Write-Status "Running PyInstaller..." -Color $InfoColor
    pyinstaller ftc_field_viewer.spec --clean
    
    if ($LASTEXITCODE -ne 0) {
        Write-Status "ERROR: PyInstaller build failed!" -Color $ErrorColor
        exit 1
    }
    
    # Check if executable was created
    if (-not (Test-Path "dist\FTC_Field_Viewer.exe")) {
        Write-Status "ERROR: Executable not found in dist folder!" -Color $ErrorColor
        exit 1
    }
    
    $ExeSize = (Get-Item "dist\FTC_Field_Viewer.exe").Length / 1MB
    Write-Status "Build completed! Executable size: $([math]::Round($ExeSize, 2)) MB" -Color $SuccessColor
}

# Create release package
if (-not $SkipPackage) {
    Write-Step "Creating Release Package"
    
    $ReleaseDir = "release-$Version"
    $ZipFile = "FTC-Field-Viewer-$Version.zip"
    
    # Create release directory
    if (Test-Path $ReleaseDir) {
        Remove-Item $ReleaseDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $ReleaseDir | Out-Null
    
    # Copy executable
    Write-Status "Copying executable..." -Color $InfoColor
    Copy-Item "dist\FTC_Field_Viewer.exe" "$ReleaseDir\"
    
    # Copy batch file if it exists
    if (Test-Path "dist\Run_FTC_Field_Viewer.bat") {
        Copy-Item "dist\Run_FTC_Field_Viewer.bat" "$ReleaseDir\"
    }
    
    # Copy documentation
    Write-Status "Copying documentation..." -Color $InfoColor
    $DocsToInclude = @("README.md", "DISTRIBUTION_README.md", "LICENSE")
    foreach ($doc in $DocsToInclude) {
        if (Test-Path $doc) {
            Copy-Item $doc "$ReleaseDir\"
        }
    }
    
    # Copy sample files for users (Field Maps and Default Points as examples)
    Write-Status "Copying sample files..." -Color $InfoColor
    if (Test-Path "Field Maps") {
        Copy-Item "Field Maps" "$ReleaseDir\" -Recurse
    }
    if (Test-Path "Default Points") {
        Copy-Item "Default Points" "$ReleaseDir\" -Recurse
    }
    if (Test-Path "points.json") {
        Copy-Item "points.json" "$ReleaseDir\"
    }
    
    # Create release notes
    Write-Status "Creating release notes..." -Color $InfoColor
    $ReleaseNotes = @"
# FTC Field Viewer $Version

## Release Package Contents

- **FTC_Field_Viewer.exe** - Main executable (no installation required)
- **Run_FTC_Field_Viewer.bat** - Convenience launcher script
- **README.md** - Project documentation
- **DISTRIBUTION_README.md** - User instructions for the executable
- **LICENSE** - License information
- **Field Maps/** - Sample field map images
- **Default Points/** - Sample point configurations
- **points.json** - Sample points file

## System Requirements

- Windows 7 or later (64-bit)
- No Python or additional software installation required

## Quick Start

1. Extract this ZIP file to any folder
2. Double-click **FTC_Field_Viewer.exe** or run **Run_FTC_Field_Viewer.bat**
3. The application will start immediately

## Built Information

- Build Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- Build Version: $Version
- PyInstaller Version: $(pyinstaller --version)
- Python Version: $(python --version)

For more information, see DISTRIBUTION_README.md
"@
    
    $ReleaseNotes | Out-File -FilePath "$ReleaseDir\RELEASE_NOTES.txt" -Encoding UTF8
    
    # Create ZIP file
    Write-Status "Creating ZIP archive..." -Color $InfoColor
    if (Test-Path $ZipFile) {
        Remove-Item $ZipFile -Force
    }
    
    # Use PowerShell's Compress-Archive
    Compress-Archive -Path "$ReleaseDir\*" -DestinationPath $ZipFile -CompressionLevel Optimal
    
    if (Test-Path $ZipFile) {
        $ZipSize = (Get-Item $ZipFile).Length / 1MB
        Write-Status "Release package created: $ZipFile ($([math]::Round($ZipSize, 2)) MB)" -Color $SuccessColor
    } else {
        Write-Status "ERROR: Failed to create ZIP file!" -Color $ErrorColor
        exit 1
    }
    
    # Clean up temporary release directory
    Remove-Item $ReleaseDir -Recurse -Force
}

Write-Step "Build Complete!"
Write-Status "Build finished at: $(Get-Date)" -Color $InfoColor

if (-not $SkipBuild -and -not $SkipPackage) {
    Write-Status "`nRelease files created:" -Color $SuccessColor
    Write-Status "  - Executable: dist\FTC_Field_Viewer.exe" -Color $InfoColor
    Write-Status "  - Release ZIP: $ZipFile" -Color $InfoColor
    Write-Status "`nThe ZIP file is ready for GitHub release upload!" -Color $SuccessColor
}

Write-Status "`nBuild script completed successfully!" -Color $SuccessColor