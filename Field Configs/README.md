# Field Configurations

This directory contains pre-built field configurations for various FTC seasons and custom field layouts.

## 📁 Available Configurations

### Official FTC Seasons
- **into-the-deep-normal.json** - 2024-25 INTO THE DEEP season
- **decode-dark.json** - 2023-24 DECODE season

## 🎯 Configuration Format

Each field configuration includes:
- **Points**: Named locations with coordinates and colors
- **Images**: Associated field map images  
- **Zones**: Mathematical regions defined by equations
- **Metadata**: Creation info and descriptions

## 🔧 Usage

### Quick Load (Recommended)
1. Open Field Editor tab
2. Use "Quick Load Field Configs" section
3. Double-click or select + "Load Selected Config"

### Manual Load
1. Open Field Editor tab
2. Click "Load" button
3. Navigate to this directory and select a .json file

## 📝 Creating Custom Configs

1. Use Field Editor to create points, associate images, and define zones
2. Save using "Save As" to create your own configuration
3. Files saved here will appear in the Quick Load list

## 🎮 Zone Equations

Define field regions using mathematical expressions:
- `x >= 0 && y <= 50` - Rectangular area
- `x*x + y*y <= 900` - Circular area (radius 30)
- `(x > -30 && x < 30) || y > 40` - Complex shapes

Coordinates are in field inches with origin at center.