# Default Points System

This directory contains JSON files that define default points for each field map. Each JSON file should have the same name as the corresponding field image (without the extension) and contain an array of point objects.

## JSON Format

Each point object should have the following structure:

```json
{
    "name": "Point Name",
    "x": 0.0,
    "y": 0.0,
    "color": "#hexcolor"
}
```

Where:
- `name`: Descriptive name for the point
- `x`: X coordinate in inches (field coordinate system)
- `y`: Y coordinate in inches (field coordinate system)
- `color`: Hex color code for the point

## Creating New Default Points

To create default points for a new field map:

1. Create a new JSON file with the same name as your field image
2. For example, if your field image is `powerplay-field.png`, create `powerplay-field.json`
3. Add an array of point objects following the format above
4. The points will automatically load when that field map is selected

## Example Files

- `decode-dark.json` - Default points for the DECODE field
- `into-the-deep-normal.json` - Default points for the Into The Deep field

## Coordinate System

The field coordinate system:
- Origin (0,0) is at the center of the field
- X-axis: Positive to the right, negative to the left
- Y-axis: Positive up, negative down
- Field dimensions: 141" x 141" (-70.5" to +70.5" in each direction)