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
5. **Use the "Refresh Image List" button** to discover newly added field images

The field selector automatically scans for common FTC field image names and formats (PNG, JPG, JPEG) and provides an intuitive way to switch between different field configurations without needing to use the File menu. All images are automatically resized to maintain proper coordinate system scaling for accurate measurements and grid alignment.
