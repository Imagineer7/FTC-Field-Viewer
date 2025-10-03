# FTC-Field-Viewer
An Interactive Python App that displays the First Tech Challenge field map with the coordinate grid and points of interest.

## Features

### Field Image Selector
The app now includes a **Field Images** tab in the sidebar that allows you to:
- **Browse available field images** with thumbnail previews
- **Switch between different field maps** instantly by clicking on them
- **Automatically discover field images** from common locations:
  - `Field Maps/` directory
  - Current directory
  - Script directory
- **Visual indicators** showing the currently selected field image
- **Refresh functionality** to rescan for new field images

### JSON-Based Default Points System
Each field map can have its own set of **default points** automatically loaded:
- **Field-specific points** defined in JSON files in the `Default Points/` directory
- **Automatic loading** when switching between field maps
- **User choice** to keep existing points or load defaults when switching
- **Easy customization** by creating new JSON files for additional field maps

**Included Default Points:**
- **DECODE field** (`decode-dark.json`): Red/Blue Goals
- **Into The Deep field** (`into-the-deep-normal.json`): Alliance stations, scoring zones, submersible, and observation zone

### Auto-Resize Field Images
Field images are **automatically resized** to ensure consistent coordinate system scaling:
- **Maintains coordinate grid accuracy** regardless of original image dimensions
- **Optimizes image size** for better performance and display quality
- **Preserves aspect ratio** for non-square images while fitting them appropriately
- **Standardizes field representation** to 800x800 pixels for square images
- **Ensures consistent scaling** across different field image sources

### Usage
1. **Launch the application** with `python ftc_field_viewer.py`
2. **Click on the "Field Images" tab** in the right sidebar
3. **Browse available field images** with their thumbnail previews
4. **Click on any field image** to instantly switch to it
5. **Choose whether to load default points** for the new field when prompted
6. **Use the "Refresh Image List" button** to discover newly added field images

### Creating Custom Default Points
To add default points for a new field map:

1. Create a JSON file in the `Default Points/` directory
2. Name it the same as your field image (e.g., `powerplay-field.json`)
3. Use this format:
```json
[
    {
        "name": "Point Name",
        "x": 0.0,
        "y": 0.0,
        "color": "#hexcolor"
    }
]
```

The field selector automatically scans for common FTC field image names and formats (PNG, JPG, JPEG) and provides an intuitive way to switch between different field configurations. All images are automatically resized to maintain proper coordinate system scaling, and field-specific default points are loaded automatically to get you started quickly with each field layout.
