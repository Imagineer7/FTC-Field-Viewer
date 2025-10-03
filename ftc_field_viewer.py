# ftc_field_viewer.py
# Interactive FTC field map viewer with grid and editable points.
# See usage instructions at the bottom.
# Version only changes the first number if it is a big feature update. Otherwise for small feature(s)
# changes the second number changes and the last number is for bug fixes.
#see https://semver.org/ for semantic versioning guidelines.
#When making changes, please update the RELEASE_NOTES.md file with a summary of changes.

__version__ = "1.3.1"

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QSettings, QStandardPaths
from PySide6.QtWidgets import QGraphicsEffect
import json
import math
import os
import sys
import argparse
from typing import List, Optional

FIELD_SIZE_IN = 141.0
HALF_FIELD = FIELD_SIZE_IN / 2.0

# Settings for storing user preferences
SETTINGS_ORG = "FTC-Tools"
SETTINGS_APP = "FTC-Field-Viewer"
MAX_RECENT_FILES = 10

def load_default_points_for_image(image_path: str) -> list:
    """Load default points from JSON file based on image filename"""
    if not image_path or not os.path.exists(image_path):
        return []
    
    # Get the base filename without extension
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    # Look for corresponding JSON file in Default Points directory
    script_dir = os.path.dirname(__file__)
    default_points_dir = os.path.join(script_dir, "Default Points")
    json_file = os.path.join(default_points_dir, f"{base_name}.json")
    
    try:
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                points = json.load(f)
                # Validate that each point has required fields
                validated_points = []
                for point in points:
                    if all(key in point for key in ['name', 'x', 'y', 'color']):
                        validated_points.append(point)
                    else:
                        print(f"Warning: Invalid point in {json_file}: {point}")
                return validated_points
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading default points from {json_file}: {e}")
    
    return []  # Return empty list if no valid points file found

class PointCreationDialog(QtWidgets.QDialog):
    """Dialog for creating new points with name, color, and coordinate input"""
    
    def __init__(self, x, y, parent=None):
        super().__init__(parent)
        self.x = x
        self.y = y
        self.setWindowTitle("Create New Point")
        self.setModal(True)
        self.resize(350, 200)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Coordinates display (read-only)
        coord_group = QtWidgets.QGroupBox("Position")
        coord_layout = QtWidgets.QHBoxLayout(coord_group)
        coord_label = QtWidgets.QLabel(f"X: {x:.1f} in,  Y: {y:.1f} in")
        coord_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        coord_layout.addWidget(coord_label)
        layout.addWidget(coord_group)
        
        # Point name input
        name_group = QtWidgets.QGroupBox("Point Name")
        name_layout = QtWidgets.QVBoxLayout(name_group)
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Enter point name...")
        self.name_input.setText("New Point")
        self.name_input.selectAll()
        name_layout.addWidget(self.name_input)
        layout.addWidget(name_group)
        
        # Color selection
        color_group = QtWidgets.QGroupBox("Point Color")
        color_layout = QtWidgets.QHBoxLayout(color_group)
        
        # Color preview button
        self.color_button = QtWidgets.QPushButton()
        self.color_button.setFixedSize(40, 30)
        self.selected_color = QtGui.QColor("#ffd166")  # Default yellow
        self.color_button.setStyleSheet(f"background-color: {self.selected_color.name()}; border: 2px solid #333;")
        self.color_button.clicked.connect(self._choose_color)
        
        # Color label
        color_label = QtWidgets.QLabel("Click to change color")
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(color_label)
        color_layout.addStretch()
        layout.addWidget(color_group)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        create_button = QtWidgets.QPushButton("Create Point")
        create_button.setDefault(True)
        create_button.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(create_button)
        layout.addLayout(button_layout)
        
        # Focus on name input
        self.name_input.setFocus()
    
    def _choose_color(self):
        """Open color picker dialog"""
        color = QtWidgets.QColorDialog.getColor(self.selected_color, self, "Choose Point Color")
        if color.isValid():
            self.selected_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 2px solid #333;")
    
    def get_point_data(self):
        """Return the point data from the dialog"""
        return {
            "name": self.name_input.text().strip() or "New Point",
            "x": self.x,
            "y": self.y,
            "color": self.selected_color.name()
        }

class LineCreationDialog(QtWidgets.QDialog):
    """Dialog for creating new lines with two endpoints, name, and color"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Line")
        self.setModal(True)
        self.resize(400, 300)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Line name input
        name_group = QtWidgets.QGroupBox("Line Name")
        name_layout = QtWidgets.QVBoxLayout(name_group)
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Enter line name...")
        self.name_input.setText("New Line")
        self.name_input.selectAll()
        name_layout.addWidget(self.name_input)
        layout.addWidget(name_group)
        
        # Endpoints group
        endpoints_group = QtWidgets.QGroupBox("Line Endpoints")
        endpoints_layout = QtWidgets.QGridLayout(endpoints_group)
        
        # Point 1
        endpoints_layout.addWidget(QtWidgets.QLabel("Point 1:"), 0, 0)
        endpoints_layout.addWidget(QtWidgets.QLabel("X (in):"), 1, 0)
        self.x1_input = QtWidgets.QDoubleSpinBox()
        self.x1_input.setRange(-HALF_FIELD, HALF_FIELD)
        self.x1_input.setDecimals(3)
        self.x1_input.setValue(0.0)
        endpoints_layout.addWidget(self.x1_input, 1, 1)
        
        endpoints_layout.addWidget(QtWidgets.QLabel("Y (in):"), 2, 0)
        self.y1_input = QtWidgets.QDoubleSpinBox()
        self.y1_input.setRange(-HALF_FIELD, HALF_FIELD)
        self.y1_input.setDecimals(3)
        self.y1_input.setValue(0.0)
        endpoints_layout.addWidget(self.y1_input, 2, 1)
        
        # Point 2
        endpoints_layout.addWidget(QtWidgets.QLabel("Point 2:"), 0, 2)
        endpoints_layout.addWidget(QtWidgets.QLabel("X (in):"), 1, 2)
        self.x2_input = QtWidgets.QDoubleSpinBox()
        self.x2_input.setRange(-HALF_FIELD, HALF_FIELD)
        self.x2_input.setDecimals(3)
        self.x2_input.setValue(10.0)
        endpoints_layout.addWidget(self.x2_input, 1, 3)
        
        endpoints_layout.addWidget(QtWidgets.QLabel("Y (in):"), 2, 2)
        self.y2_input = QtWidgets.QDoubleSpinBox()
        self.y2_input.setRange(-HALF_FIELD, HALF_FIELD)
        self.y2_input.setDecimals(3)
        self.y2_input.setValue(10.0)
        endpoints_layout.addWidget(self.y2_input, 2, 3)
        
        layout.addWidget(endpoints_group)
        
        # Color selection
        color_group = QtWidgets.QGroupBox("Line Color")
        color_layout = QtWidgets.QHBoxLayout(color_group)
        
        # Color preview button
        self.color_button = QtWidgets.QPushButton()
        self.color_button.setFixedSize(40, 30)
        self.selected_color = QtGui.QColor("#4da6ff")  # Default blue
        self.color_button.setStyleSheet(f"background-color: {self.selected_color.name()}; border: 2px solid #333;")
        self.color_button.clicked.connect(self._choose_color)
        
        # Color label
        color_label = QtWidgets.QLabel("Click to change color")
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(color_label)
        color_layout.addStretch()
        layout.addWidget(color_group)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        create_button = QtWidgets.QPushButton("Create Line")
        create_button.setDefault(True)
        create_button.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(create_button)
        layout.addLayout(button_layout)
        
        # Focus on name input
        self.name_input.setFocus()
    
    def _choose_color(self):
        """Open color picker dialog"""
        color = QtWidgets.QColorDialog.getColor(self.selected_color, self, "Choose Line Color")
        if color.isValid():
            self.selected_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 2px solid #333;")
    
    def get_line_data(self):
        """Return the line data from the dialog"""
        return {
            "name": self.name_input.text().strip() or "New Line",
            "x1": self.x1_input.value(),
            "y1": self.y1_input.value(),
            "x2": self.x2_input.value(),
            "y2": self.y2_input.value(),
            "color": self.selected_color.name()
        }

class VectorCreationDialog(QtWidgets.QDialog):
    """Dialog for creating new vectors with name, magnitude, direction, and color"""
    
    def __init__(self, x, y, parent=None):
        super().__init__(parent)
        self.x = x
        self.y = y
        self.setWindowTitle("Create New Vector")
        self.setModal(True)
        self.resize(350, 280)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Coordinates display (read-only)
        coord_group = QtWidgets.QGroupBox("Position")
        coord_layout = QtWidgets.QHBoxLayout(coord_group)
        coord_label = QtWidgets.QLabel(f"X: {x:.1f} in,  Y: {y:.1f} in")
        coord_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        coord_layout.addWidget(coord_label)
        layout.addWidget(coord_group)
        
        # Vector name input
        name_group = QtWidgets.QGroupBox("Vector Name")
        name_layout = QtWidgets.QVBoxLayout(name_group)
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Enter vector name...")
        self.name_input.setText("New Vector")
        self.name_input.selectAll()
        name_layout.addWidget(self.name_input)
        layout.addWidget(name_group)
        
        # Magnitude and direction inputs
        props_group = QtWidgets.QGroupBox("Vector Properties")
        props_layout = QtWidgets.QGridLayout(props_group)
        
        # Magnitude
        props_layout.addWidget(QtWidgets.QLabel("Magnitude (in):"), 0, 0)
        self.magnitude_input = QtWidgets.QDoubleSpinBox()
        self.magnitude_input.setRange(0.1, 1000.0)
        self.magnitude_input.setValue(10.0)
        self.magnitude_input.setSuffix(" in")
        props_layout.addWidget(self.magnitude_input, 0, 1)
        
        # Direction
        props_layout.addWidget(QtWidgets.QLabel("Direction (°):"), 1, 0)
        self.direction_input = QtWidgets.QDoubleSpinBox()
        self.direction_input.setRange(0.0, 359.9)
        self.direction_input.setValue(0.0)
        self.direction_input.setSuffix("°")
        self.direction_input.setWrapping(True)
        props_layout.addWidget(self.direction_input, 1, 1)
        
        layout.addWidget(props_group)
        
        # Color selection
        color_group = QtWidgets.QGroupBox("Vector Color")
        color_layout = QtWidgets.QHBoxLayout(color_group)
        
        # Color preview button
        self.color_button = QtWidgets.QPushButton()
        self.color_button.setFixedSize(40, 30)
        self.selected_color = QtGui.QColor("#ff6b6b")  # Default red
        self.color_button.setStyleSheet(f"background-color: {self.selected_color.name()}; border: 2px solid #333;")
        self.color_button.clicked.connect(self._choose_color)
        
        # Color label
        color_label = QtWidgets.QLabel("Click to change color")
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(color_label)
        color_layout.addStretch()
        layout.addWidget(color_group)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        create_button = QtWidgets.QPushButton("Create Vector")
        create_button.setDefault(True)
        create_button.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(create_button)
        layout.addLayout(button_layout)
        
        # Focus on name input
        self.name_input.setFocus()
    
    def _choose_color(self):
        """Open color picker dialog"""
        color = QtWidgets.QColorDialog.getColor(self.selected_color, self, "Choose Vector Color")
        if color.isValid():
            self.selected_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 2px solid #333;")
    
    def get_vector_data(self):
        """Return the vector data from the dialog"""
        return {
            "name": self.name_input.text().strip() or "New Vector",
            "x": self.x,
            "y": self.y,
            "magnitude": self.magnitude_input.value(),
            "direction": self.direction_input.value(),
            "color": self.selected_color.name()
        }

DARK_QSS = """
QWidget {
    background-color: #111418;
    color: #e6e6e6;
    font-family: 'Segoe UI', 'Inter', 'Roboto', Arial, sans-serif;
    font-size: 12pt;
}
QToolTip {
    background-color: #1b2128;
    color: #e6e6e6;
    border: 1px solid #2a2f36;
}
QGroupBox {
    border: 1px solid #2a2f36;
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #9fb3c8;
    font-weight: 600;
}
QPushButton {
    background-color: #1f2730;
    border: 1px solid #2f3b47;
    border-radius: 8px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #24303b;
}
QPushButton:pressed {
    background-color: #303c48;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
    background-color: #0d1117;
    color: #e6e6e6;
    border: 1px solid #2a2f36;
    border-radius: 6px;
    padding: 4px 6px;
    selection-background-color: #315a8b;
}
QSlider::groove:horizontal {
    border: 1px solid #2a2f36;
    height: 6px;
    background: #0d1117;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #4a90e2;
    border: 1px solid #2a2f36;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QCheckBox::indicator {
    width: 18px; height: 18px;
}
QCheckBox::indicator:unchecked {
    image: none;
    border: 1px solid #2a2f36;
    background: #0d1117;
    border-radius: 4px;
}
QCheckBox::indicator:checked {
    image: none;
    background: #4a90e2;
    border: 1px solid #2a2f36;
    border-radius: 4px;
}
QListWidget {
    background: #0d1117;
    border: 1px solid #2a2f36;
    border-radius: 6px;
}
QStatusBar {
    background: #0d1117;
    color: #cfd9e5;
    border-top: 1px solid #2a2f36;
}
"""

def clamp(v, lo, hi):
    return max(lo, min(hi, v))



class FieldView(QtWidgets.QGraphicsView):
    cursorMoved = QtCore.Signal(float, float)  # emits field coords (x,y) inches
    pointSelected = QtCore.Signal(int)        # emits index in points list or -1
    pointAdded = QtCore.Signal()              # emits when a new point is created
    pointsReloaded = QtCore.Signal()          # emits when default points are reloaded
    vectorSelected = QtCore.Signal(int)       # emits index in vectors list or -1
    vectorAdded = QtCore.Signal()             # emits when a new vector is created
    lineSelected = QtCore.Signal(int)         # emits index in lines list or -1
    lineAdded = QtCore.Signal()               # emits when a new line is created

    def __init__(self, scene, image_pixmap, image_path: str = "", *args, **kwargs):
        super().__init__(scene, *args, **kwargs)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Point dragging state
        self.dragging_point = False
        self.drag_point_index = -1

        self.image_item = QtWidgets.QGraphicsPixmapItem(image_pixmap)
        self.scene().addItem(self.image_item)
        self.current_image_path = image_path

        self.grid_opacity = 0.5
        self.grid_pen = QtGui.QPen(QtGui.QColor(0, 188, 255, int(255*self.grid_opacity)), 0.0)
        self.major_grid_every = 6  # bold every N lines
        self.major_grid_pen = QtGui.QPen(QtGui.QColor(0, 188, 255, int(255*self.grid_opacity)), 0.0)
        self.major_grid_pen.setWidthF(1.2)

        # Load default points based on the image
        self.default_points = load_default_points_for_image(image_path)
        self.user_points = []               # User-added points separate from defaults
        self.point_items = []               # QGraphicsEllipseItem + label
        self.selected_index = -1
        self.show_labels = True
        self.show_default_points = True    # Control visibility of default points
        
        # Vector management
        self.vectors = []                   # list of dicts with name,x,y,magnitude,direction,color
        self.vector_items = []              # QGraphicsItem for vector arrows
        self.selected_vector_index = -1
        
        # Line management
        self.lines = []                     # list of dicts with name,x1,y1,x2,y2,color
        self.line_items = []                # QGraphicsItem for line segments
        self.selected_line_index = -1

        # Measurement system
        self.measurement_mode = False       # Toggle measurement mode
        self.measurement_tool = "distance"  # distance, angle, area, point_to_line
        self.measurement_points = []        # Points selected for current measurement
        self.measurement_items = []         # Visual items for measurements
        self.show_pixel_coords = False     # Toggle between field and pixel coordinates
        self.measurement_snap_to_grid = True  # Whether measurements snap to grid
        
        # Cursor-following snap point
        self.cursor_point = None
        self.cursor_field_pos = (0, 0)  # Current snapped position in field coordinates
        self.menu_open = False  # Track if context menu is open
        
        self.image_rect = self.image_item.boundingRect()
        self.setSceneRect(self.image_rect)
        self.setBackgroundBrush(QtGui.QColor("#0b0f14"))

        self._rebuild_overlays()

    @property
    def points(self):
        """Get all visible points (default + user points based on visibility settings)"""
        visible_points = []
        if self.show_default_points:
            visible_points.extend(self.default_points)
        visible_points.extend(self.user_points)
        return visible_points
    
    def reload_default_points_for_image(self, image_path: str):
        """Reload default points when switching to a different field image"""
        self.current_image_path = image_path
        
        # Ask user if they want to load default points for the new field
        if self.user_points or self.default_points:  # If there are existing points
            reply = QtWidgets.QMessageBox.question(
                self,
                "Load Default Points",
                f"Load default points for {os.path.basename(image_path)}?\n\n"
                "This will replace your current points. Choose:\n"
                "• Yes: Replace default points (user points preserved)\n"
                "• No: Keep your current points",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.Yes
            )
            if reply == QtWidgets.QMessageBox.StandardButton.No:
                return
        
        # Load the new default points
        self.default_points = load_default_points_for_image(image_path)
        self.selected_index = -1
        
        # Refresh the display
        self._rebuild_overlays()
        
        # Notify that points were reloaded
        self.pointsReloaded.emit()

    # --- Coordinate transforms ---
    def field_to_scene(self, x_in, y_in):
        """Map field inches (origin center) to scene/image pixels."""
        iw = self.image_rect.width()
        ih = self.image_rect.height()
        sx = (x_in + HALF_FIELD) * (iw / FIELD_SIZE_IN)
        sy = (HALF_FIELD - y_in) * (ih / FIELD_SIZE_IN)
        return QtCore.QPointF(self.image_rect.left() + sx, self.image_rect.top() + sy)

    def scene_to_field(self, scene_pos):
        """Convert scene coordinates to field coordinates (inches)"""
        iw = self.image_rect.width()
        ih = self.image_rect.height()
        left = self.image_rect.left()
        top = self.image_rect.top()
        sx = scene_pos.x() - left
        sy = scene_pos.y() - top
        x_in = (sx * FIELD_SIZE_IN / iw) - HALF_FIELD
        y_in = HALF_FIELD - (sy * FIELD_SIZE_IN / ih)
        return x_in, y_in
    
    def snap_to_grid(self, x_in, y_in, resolution=1.0):
        """Snap field coordinates to specified resolution grid"""
        snapped_x = round(x_in / resolution) * resolution
        snapped_y = round(y_in / resolution) * resolution
        return snapped_x, snapped_y
    
    def _get_current_grid_spacing(self):
        """Get the current grid spacing in inches based on zoom level"""
        # Get current zoom level from transform
        current_transform = self.transform()
        zoom_level = current_transform.m11()  # horizontal scale factor
        
        # Calculate dynamic spacing - same logic as _draw_grid
        base_spacing = 23.5  # inches at full zoom out (actual FTC tile size)
        
        if zoom_level <= 1.0:
            return base_spacing
        elif zoom_level <= 2.0:
            return base_spacing / 2  # 11.75 inches
        elif zoom_level <= 4.0:
            return base_spacing / 4  # 5.875 inches
        elif zoom_level <= 8.0:
            return base_spacing / 8  # 2.9375 inches
        elif zoom_level <= 16.0:
            return base_spacing / 16  # 1.46875 inches
        else:
            return 1.0  # 1 inch for very high zoom

    # --- Line equation calculations ---
    def calculate_line_equation(self, x1, y1, x2, y2):
        """
        Calculate line equation in standard form: Ax + By + C = 0
        Returns (A, B, C) coefficients
        """
        # Handle vertical line case (x2 == x1)
        if abs(x2 - x1) < 1e-10:
            # Vertical line: x = x1, or x - x1 = 0, or 1*x + 0*y - x1 = 0
            return (1.0, 0.0, -x1)
        
        # Handle horizontal line case (y2 == y1)
        if abs(y2 - y1) < 1e-10:
            # Horizontal line: y = y1, or 0*x + 1*y - y1 = 0
            return (0.0, 1.0, -y1)
        
        # General case: convert from two-point form to standard form
        # Two-point form: (y - y1)/(y2 - y1) = (x - x1)/(x2 - x1)
        # Cross multiply: (y - y1)(x2 - x1) = (x - x1)(y2 - y1)
        # Expand: y(x2 - x1) - y1(x2 - x1) = x(y2 - y1) - x1(y2 - y1)
        # Rearrange: y(x2 - x1) - x(y2 - y1) = y1(x2 - x1) - x1(y2 - y1)
        # Standard form: (y1 - y2)x + (x2 - x1)y + (x1(y2 - y1) - y1(x2 - x1)) = 0
        
        A = y1 - y2
        B = x2 - x1
        C = x1 * (y2 - y1) - y1 * (x2 - x1)
        
        return (A, B, C)
    
    def evaluate_line_equation(self, A, B, C, x, y):
        """
        Evaluate line equation Ax + By + C at point (x, y)
        Returns: 
        - 0 if point is on the line
        - positive if point is on one side
        - negative if point is on the other side
        """
        return A * x + B * y + C
    
    def get_line_equation_string(self, x1, y1, x2, y2, include_evaluation=True):
        """
        Get a formatted string representation of the line equation and evaluation function
        """
        A, B, C = self.calculate_line_equation(x1, y1, x2, y2)
        
        result = []
        
        # Zone inequality equations
        result.append("Zone Boundary Equations:")
        if abs(A) < 1e-10 and abs(B) < 1e-10:
            result.append("Invalid line (both points are the same)")
            return "\n".join(result)
        elif abs(B) < 1e-10:  # Vertical line
            x_val = -C/A
            result.append(f"⁅x ≥ {x_val:.3f}⁆  (right side)")
            result.append(f"⁅x ≤ {x_val:.3f}⁆  (left side)")
        elif abs(A) < 1e-10:  # Horizontal line
            y_val = -C/B
            result.append(f"⁅y ≥ {y_val:.3f}⁆  (above line)")
            result.append(f"⁅y ≤ {y_val:.3f}⁆  (below line)")
        else:
            # Convert to slope-intercept form for zone inequalities
            m = -A/B
            b = -C/B
            
            # Format the slope as a fraction if it's a simple ratio
            if abs(m - round(m * 2) / 2) < 1e-6:  # Check if it's a half-integer
                if abs(m - round(m)) < 1e-6:  # Whole number
                    m_str = f"{int(round(m))}" if round(m) != 1 else ""
                    if round(m) == -1:
                        m_str = "-"
                elif abs(m - 0.5) < 1e-6:
                    m_str = "1/2 "
                elif abs(m + 0.5) < 1e-6:
                    m_str = "-1/2 "
                elif abs(m - 1.5) < 1e-6:
                    m_str = "3/2 "
                elif abs(m + 1.5) < 1e-6:
                    m_str = "-3/2 "
                else:
                    # Try to express as a simple fraction
                    for denom in [2, 3, 4, 5, 6, 8]:
                        if abs(m - round(m * denom) / denom) < 1e-6:
                            num = int(round(m * denom))
                            if num == denom:
                                m_str = ""
                            elif num == -denom:
                                m_str = "-"
                            else:
                                m_str = f"{num}/{denom} " if abs(num) != 1 else ("" if num == 1 else "-")
                            break
                    else:
                        m_str = f"{m:.3f} "
            else:
                m_str = f"{m:.3f} " if abs(m - 1) > 1e-6 else ""
                if abs(m + 1) < 1e-6:
                    m_str = "-"
            
            # Format the y-intercept
            if abs(b) < 1e-6:
                b_str = ""
            elif b > 0:
                b_str = f" + {b:.3f}" if abs(b - round(b)) > 1e-6 else f" + {int(round(b))}"
            else:
                b_str = f" - {abs(b):.3f}" if abs(b - round(b)) > 1e-6 else f" - {int(round(abs(b)))}"
            
            # Create the inequality equations
            if m_str == "":
                if b_str == "":
                    pos_eq = "⁅y ≥ x⁆"
                    neg_eq = "⁅y ≤ x⁆"
                else:
                    pos_eq = f"⁅y ≥ x{b_str}⁆"
                    neg_eq = f"⁅y ≤ x{b_str}⁆"
            elif m_str == "-":
                if b_str == "":
                    pos_eq = "⁅y ≥ -x⁆"
                    neg_eq = "⁅y ≤ -x⁆"
                else:
                    pos_eq = f"⁅y ≥ -x{b_str}⁆"
                    neg_eq = f"⁅y ≤ -x{b_str}⁆"
            else:
                if b_str == "":
                    pos_eq = f"⁅y ≥ {m_str}x⁆"
                    neg_eq = f"⁅y ≤ {m_str}x⁆"
                else:
                    pos_eq = f"⁅y ≥ {m_str}x{b_str}⁆"
                    neg_eq = f"⁅y ≤ {m_str}x{b_str}⁆"
            
            result.append(f"{pos_eq}  (above/positive side)")
            result.append(f"{neg_eq}  (below/negative side)")
        
        # Standard form for reference
        result.append("")
        result.append("Standard Form (for reference):")
        result.append(f"{A:.3f}x + {B:.3f}y + {C:.3f} = 0")
        
        if include_evaluation:
            result.append("")
            result.append("Robot Code Evaluation Function:")
            result.append("// Returns: 0 = on line, >0 = above/positive, <0 = below/negative")
            result.append(f"double evaluateLine(double x, double y) {{")
            result.append(f"    return {A:.3f} * x + {B:.3f} * y + {C:.3f};")
            result.append(f"}}")
            result.append("")
            result.append("Zone Check Examples:")
            if abs(B) < 1e-10:  # Vertical line
                result.append("if (evaluateLine(robotX, robotY) > 0) {")
                result.append("    // Robot is on the right side of the line")
                result.append("}")
                result.append("if (evaluateLine(robotX, robotY) < 0) {")
                result.append("    // Robot is on the left side of the line")
                result.append("}")
            else:
                result.append("if (evaluateLine(robotX, robotY) > 0) {")
                result.append("    // Robot is above the line")
                result.append("}")
                result.append("if (evaluateLine(robotX, robotY) < 0) {")
                result.append("    // Robot is below the line")
                result.append("}")
        
        return "\n".join(result)

    # --- Grid and points drawing ---
    def _clear_overlays(self):
        # Remove all but image
        for item in list(self.scene().items()):
            if item is self.image_item:
                continue
            self.scene().removeItem(item)

    def _rebuild_overlays(self):
        self._clear_overlays()
        self._draw_grid()
        self._draw_points()
        self._draw_vectors()
        self._draw_lines()
        self._draw_cursor_point()

    def _draw_grid(self):
        iw = self.image_rect.width()
        ih = self.image_rect.height()
        left = self.image_rect.left()
        top = self.image_rect.top()

        # Get current zoom level from transform
        current_transform = self.transform()
        zoom_level = current_transform.m11()  # horizontal scale factor
        
        # Calculate appropriate grid spacing based on zoom
        # At zoom=1.0 (full zoom out), use 23.5-inch tiles (actual FTC field tile size)
        # As zoom increases, subdivide to smaller grids
        base_spacing = 23.5  # inches at full zoom out (actual FTC tile size)
        
        # Calculate dynamic spacing - subdivide as we zoom in
        if zoom_level <= 1.0:
            step_in = base_spacing
        elif zoom_level <= 2.0:
            step_in = base_spacing / 2  # 11.75 inches
        elif zoom_level <= 4.0:
            step_in = base_spacing / 4  # 5.875 inches
        elif zoom_level <= 8.0:
            step_in = base_spacing / 8  # 2.9375 inches
        elif zoom_level <= 16.0:
            step_in = base_spacing / 16  # 1.46875 inches
        else:
            step_in = 1.0  # 1 inch for very high zoom
        
        # Calculate grid lines needed to cover the field plus some margin
        margin_factor = 1.5  # Extra grid lines beyond field edges
        total_coverage = FIELD_SIZE_IN * margin_factor
        num_lines = int(total_coverage / step_in)
        
        # Calculate pixel step - use the smaller scale to ensure square grid cells
        # This makes the grid always display as squares regardless of image aspect ratio
        scale_x = iw / FIELD_SIZE_IN
        scale_y = ih / FIELD_SIZE_IN
        # Use the smaller scale to ensure grid stays within image bounds
        grid_scale = min(scale_x, scale_y)
        px_step = grid_scale * step_in  # Same step size for both X and Y
        
        # Center grid on field center (image center)
        center_x = left + iw / 2
        center_y = top + ih / 2
        
        # Calculate starting positions to center the grid
        half_lines = num_lines // 2
        start_x = center_x - half_lines * px_step
        start_y = center_y - half_lines * px_step
        
        # Draw vertical lines
        for i in range(num_lines + 1):
            x = start_x + i * px_step
            line = QtCore.QLineF(x, top, x, top + ih)
            # Make every nth line major for 23.5-inch spacing intervals
            major_every = max(1, int(23.5 / step_in))
            is_major = (i - half_lines) % major_every == 0
            pen = self.major_grid_pen if is_major else self.grid_pen
            self.scene().addLine(line, pen)
        
        # Draw horizontal lines
        for i in range(num_lines + 1):
            y = start_y + i * px_step
            line = QtCore.QLineF(left, y, left + iw, y)
            major_every = max(1, int(23.5 / step_in))
            is_major = (i - half_lines) % major_every == 0
            pen = self.major_grid_pen if is_major else self.grid_pen
            self.scene().addLine(line, pen)

        # Axes lines through origin
        origin_scene = self.field_to_scene(0, 0)
        x_axis = QtCore.QLineF(left, origin_scene.y(), left + iw, origin_scene.y())
        y_axis = QtCore.QLineF(origin_scene.x(), top, origin_scene.x(), top + ih)
        axis_pen = QtGui.QPen(QtGui.QColor("#00ffd0"), 0.0)
        axis_pen.setWidthF(1.5)
        self.scene().addLine(x_axis, axis_pen)
        self.scene().addLine(y_axis, axis_pen)

        # Origin marker
        r = 6
        origin_marker = self.scene().addEllipse(origin_scene.x()-r/2, origin_scene.y()-r/2, r, r,
                                                QtGui.QPen(QtCore.Qt.PenStyle.NoPen),
                                                QtGui.QBrush(QtGui.QColor("#00ffd0")))
        origin_label = self.scene().addText("(0,0)")
        origin_label.setDefaultTextColor(QtGui.QColor("#8fbcd4"))
        origin_label.setPos(origin_scene + QtCore.QPointF(8, -18))

    def _draw_points(self):
        # Clear existing point items from scene
        for item in self.point_items:
            if item.scene() == self.scene():
                self.scene().removeItem(item)
        self.point_items.clear()
        
        for idx, p in enumerate(self.points):
            color = QtGui.QColor(p.get("color", "#ffd166"))
            pos = self.field_to_scene(p["x"], p["y"])
            r = 12.0 if idx == self.selected_index else 10.0
            
            # Create simple point circle
            pen = QtGui.QPen(QtGui.QColor("#000000"))
            pen.setWidthF(2.0 if idx == self.selected_index else 1.0)
            brush = QtGui.QBrush(color)
            
            point = self.scene().addEllipse(
                pos.x() - r/2, pos.y() - r/2, r, r, pen, brush
            )
            point.setZValue(5)
            self.point_items.append(point)

            if self.show_labels:
                # Create text label with background
                label = self.scene().addText(p["name"])
                
                # Set larger, bold font
                font = QtGui.QFont("Arial", 12, QtGui.QFont.Weight.Bold)
                label.setFont(font)
                label.setDefaultTextColor(color.lighter(150))
                label.setPos(pos + QtCore.QPointF(15, -25))
                label.setZValue(6)
                
                # Create background rectangle
                text_rect = label.boundingRect()
                padding = 4
                bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
                
                # Position background relative to label
                bg_pos = label.pos()
                background = self.scene().addRect(
                    bg_rect.translated(bg_pos),
                    QtGui.QPen(color.darker(120)),
                    QtGui.QBrush(QtGui.QColor(0, 0, 0, 180))  # Semi-transparent black
                )
                background.setZValue(5)  # Behind text but above points
                
                self.point_items.append(background)
                self.point_items.append(label)
    
    def _draw_vectors(self):
        """Draw vectors as arrows with magnitude and direction"""
        # Clear existing vector items from scene
        for item in self.vector_items:
            if item.scene() == self.scene():
                self.scene().removeItem(item)
        self.vector_items.clear()
        
        for idx, v in enumerate(self.vectors):
            color = QtGui.QColor(v.get("color", "#ff6b6b"))
            pos = self.field_to_scene(v["x"], v["y"])
            magnitude = v["magnitude"]
            direction = v["direction"]
            
            # Convert direction to radians (0° = positive X axis)
            direction_rad = math.radians(direction)
            
            # Calculate scale factor for magnitude (pixels per inch)
            # Use the same scaling as the field coordinates
            scale_factor = min(self.image_rect.width() / FIELD_SIZE_IN, self.image_rect.height() / FIELD_SIZE_IN)
            arrow_length = magnitude * scale_factor
            
            # Calculate end point of arrow
            end_x = pos.x() + arrow_length * math.cos(direction_rad)
            end_y = pos.y() - arrow_length * math.sin(direction_rad)  # Negative because Y axis is flipped
            
            # Draw arrow shaft
            line_width = 3.0 if idx == self.selected_vector_index else 2.0
            pen = QtGui.QPen(color)
            pen.setWidthF(line_width)
            pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
            
            arrow_line = self.scene().addLine(pos.x(), pos.y(), end_x, end_y, pen)
            arrow_line.setZValue(4)
            self.vector_items.append(arrow_line)
            
            # Draw arrowhead
            arrow_head_length = 12.0
            arrow_head_angle = math.radians(25)  # 25 degrees from shaft
            
            # Calculate arrowhead points
            head1_x = end_x - arrow_head_length * math.cos(direction_rad - arrow_head_angle)
            head1_y = end_y + arrow_head_length * math.sin(direction_rad - arrow_head_angle)
            head2_x = end_x - arrow_head_length * math.cos(direction_rad + arrow_head_angle)
            head2_y = end_y + arrow_head_length * math.sin(direction_rad + arrow_head_angle)
            
            # Create arrowhead as polygon
            arrowhead = QtGui.QPolygonF([
                QtCore.QPointF(end_x, end_y),
                QtCore.QPointF(head1_x, head1_y),
                QtCore.QPointF(head2_x, head2_y)
            ])
            
            arrowhead_item = self.scene().addPolygon(arrowhead, pen, QtGui.QBrush(color))
            arrowhead_item.setZValue(4)
            self.vector_items.append(arrowhead_item)
            
            # Add vector label if labels are enabled
            if self.show_labels:
                # Create text label with magnitude and direction info
                label_text = f"{v['name']}\n{magnitude:.1f}in @ {direction:.0f}°"
                label = self.scene().addText(label_text)
                
                # Set font and color
                font = QtGui.QFont("Arial", 10, QtGui.QFont.Weight.Bold)
                label.setFont(font)
                label.setDefaultTextColor(color.lighter(150))
                
                # Smart label positioning to avoid covering vector
                # Position label on the opposite side from where vector is pointing
                text_rect = label.boundingRect()
                
                # For small vectors (< 30 pixels), place label further away
                if arrow_length < 30:
                    offset_distance = 50  # Further away for small vectors
                else:
                    offset_distance = 35  # Closer for larger vectors
                
                # Calculate opposite direction (180 degrees from vector direction)
                opposite_direction_rad = direction_rad + math.pi
                label_offset_x = offset_distance * math.cos(opposite_direction_rad)
                label_offset_y = -offset_distance * math.sin(opposite_direction_rad)
                
                # Position label on the opposite side of where the vector points
                label_pos = pos + QtCore.QPointF(label_offset_x, label_offset_y - text_rect.height()/2)
                label.setPos(label_pos)
                label.setZValue(6)
                
                # Create background for label
                text_rect = label.boundingRect()
                padding = 3
                bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
                
                background = self.scene().addRect(
                    bg_rect.translated(label.pos()),
                    QtGui.QPen(color.darker(120)),
                    QtGui.QBrush(QtGui.QColor(0, 0, 0, 180))
                )
                background.setZValue(5)
                
                self.vector_items.append(background)
                self.vector_items.append(label)
    
    def _draw_lines(self):
        """Draw lines as line segments between two points"""
        # Clear existing line items from scene
        for item in self.line_items:
            if item.scene() == self.scene():
                self.scene().removeItem(item)
        self.line_items.clear()
        
        for idx, line in enumerate(self.lines):
            color = QtGui.QColor(line.get("color", "#4da6ff"))
            
            # Convert field coordinates to scene coordinates
            pos1 = self.field_to_scene(line["x1"], line["y1"])
            pos2 = self.field_to_scene(line["x2"], line["y2"])
            
            # Draw line segment
            line_width = 4.0 if idx == self.selected_line_index else 3.0
            pen = QtGui.QPen(color)
            pen.setWidthF(line_width)
            pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
            
            line_segment = self.scene().addLine(pos1.x(), pos1.y(), pos2.x(), pos2.y(), pen)
            line_segment.setZValue(3)  # Behind vectors but above grid
            self.line_items.append(line_segment)
            
            # Draw endpoint markers
            endpoint_radius = 6.0 if idx == self.selected_line_index else 4.0
            endpoint_pen = QtGui.QPen(color.darker(120))
            endpoint_pen.setWidthF(2.0)
            endpoint_brush = QtGui.QBrush(color.lighter(150))
            
            # Point 1 marker
            endpoint1 = self.scene().addEllipse(
                pos1.x() - endpoint_radius/2, pos1.y() - endpoint_radius/2,
                endpoint_radius, endpoint_radius, endpoint_pen, endpoint_brush
            )
            endpoint1.setZValue(4)
            self.line_items.append(endpoint1)
            
            # Point 2 marker
            endpoint2 = self.scene().addEllipse(
                pos2.x() - endpoint_radius/2, pos2.y() - endpoint_radius/2,
                endpoint_radius, endpoint_radius, endpoint_pen, endpoint_brush
            )
            endpoint2.setZValue(4)
            self.line_items.append(endpoint2)
            
            # Add line label if labels are enabled
            if self.show_labels:
                # Calculate line equation for display
                A, B, C = self.calculate_line_equation(line["x1"], line["y1"], line["x2"], line["y2"])
                
                # Format equation string in zone inequality format
                if abs(B) < 1e-10:  # Vertical line
                    equation_str = f"x = {-C/A:.2f}"
                elif abs(A) < 1e-10:  # Horizontal line
                    equation_str = f"y = {-C/B:.2f}"
                else:
                    # Convert to slope-intercept form for zone display
                    m = -A/B
                    b = -C/B
                    
                    # Format slope as fraction if simple
                    if abs(m - 0.5) < 1e-6:
                        m_str = "1/2"
                    elif abs(m + 0.5) < 1e-6:
                        m_str = "-1/2"
                    elif abs(m - round(m)) < 1e-6:
                        m_val = int(round(m))
                        m_str = str(m_val) if m_val != 1 else ""
                        if m_val == -1:
                            m_str = "-"
                    else:
                        m_str = f"{m:.2f}"
                    
                    # Format equation
                    if abs(b) < 1e-10:
                        if m_str == "":
                            equation_str = "⁅y ≥ x⁆"
                        elif m_str == "-":
                            equation_str = "⁅y ≥ -x⁆"
                        else:
                            equation_str = f"⁅y ≥ {m_str}x⁆"
                    else:
                        b_str = f" + {b:.2f}" if b >= 0 else f" - {abs(b):.2f}"
                        if abs(b - round(b)) < 1e-6:
                            b_str = f" + {int(round(b))}" if b >= 0 else f" - {int(round(abs(b)))}"
                        
                        if m_str == "":
                            equation_str = f"⁅y ≥ x{b_str}⁆"
                        elif m_str == "-":
                            equation_str = f"⁅y ≥ -x{b_str}⁆"
                        else:
                            equation_str = f"⁅y ≥ {m_str}x{b_str}⁆"
                
                label_text = f"{line['name']}\n{equation_str}"
                label = self.scene().addText(label_text)
                
                # Set font and color
                font = QtGui.QFont("Arial", 10, QtGui.QFont.Weight.Bold)
                label.setFont(font)
                label.setDefaultTextColor(color.lighter(150))
                
                # Position label at the midpoint of the line, offset slightly
                mid_x = (pos1.x() + pos2.x()) / 2
                mid_y = (pos1.y() + pos2.y()) / 2
                
                # Calculate perpendicular offset for label positioning
                dx = pos2.x() - pos1.x()
                dy = pos2.y() - pos1.y()
                length = math.sqrt(dx*dx + dy*dy)
                
                if length > 0:
                    # Perpendicular direction (rotated 90 degrees)
                    perp_x = -dy / length
                    perp_y = dx / length
                    offset_distance = 25
                    label_x = mid_x + perp_x * offset_distance
                    label_y = mid_y + perp_y * offset_distance
                else:
                    label_x = mid_x
                    label_y = mid_y - 20
                
                label.setPos(label_x, label_y)
                label.setZValue(6)
                
                # Create background for label
                text_rect = label.boundingRect()
                padding = 3
                bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
                
                background = self.scene().addRect(
                    bg_rect.translated(label.pos()),
                    QtGui.QPen(color.darker(120)),
                    QtGui.QBrush(QtGui.QColor(0, 0, 0, 180))
                )
                background.setZValue(5)
                
                self.line_items.append(background)
                self.line_items.append(label)

    def _draw_cursor_point(self):
        """Draw the cursor-following snap point"""
        if self.cursor_point and self.cursor_point.scene() == self.scene():
            self.scene().removeItem(self.cursor_point)
            self.cursor_point = None
        
        # Create a semi-transparent cursor point
        scene_pos = self.field_to_scene(*self.cursor_field_pos)
        cursor_color = QtGui.QColor(255, 255, 255, 150)  # Semi-transparent white
        cursor_pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 200))
        cursor_pen.setWidthF(2.0)
        
        self.cursor_point = self.scene().addEllipse(
            scene_pos.x() - 6, scene_pos.y() - 6, 12, 12,
            cursor_pen, QtGui.QBrush(cursor_color)
        )
        self.cursor_point.setZValue(10)  # Above other points

    # --- Interaction ---
    def wheelEvent(self, event: QtGui.QWheelEvent):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        # Get current zoom level
        current_zoom = self.transform().m11()
        
        # Calculate proposed new zoom level
        proposed_zoom = current_zoom * (zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor)
        
        # Set minimum zoom level (e.g., 0.1 = 10% of original size)
        min_zoom = 0.1
        max_zoom = 50.0  # Also add a reasonable maximum
        
        # Only apply zoom if within bounds
        if min_zoom <= proposed_zoom <= max_zoom:
            zoom = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
            self.scale(zoom, zoom)
            # Redraw grid with new zoom level
            self._rebuild_overlays()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.measurement_mode:
            # Handle measurement tool clicks
            scene_pos = self.mapToScene(event.position().toPoint())
            field_x, field_y = self.scene_to_field(scene_pos)
            
            # Apply snapping if enabled and Shift is not held
            if self.measurement_snap_to_grid and not (event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier):
                snap_resolution = self._get_current_grid_spacing()
                field_x, field_y = self.snap_to_grid(field_x, field_y, snap_resolution)
            
            if self.measurement_tool == "distance":
                self.add_measurement_point(field_x, field_y)
                if len(self.measurement_points) >= 2:
                    # Distance measurement complete, reset for next measurement
                    QtCore.QTimer.singleShot(2000, self.clear_current_measurement)  # Clear after 2 seconds
            elif self.measurement_tool == "angle":
                self.add_measurement_point(field_x, field_y)
                if len(self.measurement_points) >= 3:
                    # Angle measurement complete, reset for next measurement
                    QtCore.QTimer.singleShot(3000, self.clear_current_measurement)  # Clear after 3 seconds
            elif self.measurement_tool == "area":
                self.add_measurement_point(field_x, field_y)
                # Area measurement continues until user switches tools or disables measurement mode
        
        elif event.button() == QtCore.Qt.MouseButton.LeftButton and not self.measurement_mode:
            # Check if we're clicking on a point for dragging
            field_x, field_y = self.scene_to_field(self.mapToScene(event.position().toPoint()))
            point_index = self._find_point_at_position(field_x, field_y)
            
            if point_index >= 0:
                # Start dragging point
                self.dragging_point = True
                self.drag_point_index = point_index
                self.selected_index = point_index
                self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)  # Disable view panning while dragging point
                self._rebuild_overlays()
                self.pointSelected.emit(point_index)
            else:
                # Normal view interaction
                self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
                
        elif event.button() == QtCore.Qt.MouseButton.RightButton and not self.measurement_mode:
            # Show context menu for point creation (only when not in measurement mode)
            self._show_context_menu(event.globalPosition().toPoint())
        elif event.button() == QtCore.Qt.MouseButton.RightButton and self.measurement_mode:
            # Right-click in measurement mode clears current measurement
            self.clear_current_measurement()
            
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        # Handle point dragging
        if self.dragging_point and self.drag_point_index >= 0:
            field_x, field_y = self.scene_to_field(self.mapToScene(event.position().toPoint()))
            
            # Update point position
            if self.drag_point_index < len(self.points):
                self.points[self.drag_point_index]['x'] = field_x
                self.points[self.drag_point_index]['y'] = field_y
                self._rebuild_overlays()
            
            self.cursorMoved.emit(field_x, field_y)
            return  # Don't call super() to prevent view panning during point drag
            
        # Normal mouse move handling
        scene_pos = self.mapToScene(event.position().toPoint())
        field_x, field_y = 0.0, 0.0  # Default values
        
        if self.image_rect.contains(scene_pos):
            # Convert to field coordinates and track cursor
            field_x, field_y = self.scene_to_field(scene_pos)
            
            # Update the cursor position for display/snapping
            if not self.menu_open:
                self._update_cursor_tracking(event)
        
        self.cursorMoved.emit(field_x, field_y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.dragging_point:
            # Finish point dragging
            self.dragging_point = False
            self.drag_point_index = -1
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)  # Re-enable view panning
            
        super().mouseReleaseEvent(event)

    def _find_point_at_position(self, field_x: float, field_y: float, tolerance: float = 5.0) -> int:
        """Find if there's a point at the given field position within tolerance (in inches)"""
        for i, point in enumerate(self.points):
            dx = point['x'] - field_x
            dy = point['y'] - field_y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance <= tolerance:
                return i
        return -1

    def _update_cursor_tracking(self, event: QtGui.QMouseEvent):
        """Update cursor tracking for normal (non-dragging) mouse movement"""
        scene_pos = self.mapToScene(event.position().toPoint())
        field_x, field_y = self.scene_to_field(scene_pos)
        
        # Snap cursor to grid unless Shift is held
        if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
            # No snapping when shift is pressed
            self.cursor_field_pos = (field_x, field_y)
        else:
            # Use the same grid spacing as the visual grid for cursor snapping
            snap_resolution = self._get_current_grid_spacing()
            snapped_x, snapped_y = self.snap_to_grid(field_x, field_y, snap_resolution)
            self.cursor_field_pos = (snapped_x, snapped_y)
        self._draw_cursor_point()
    
    def _show_context_menu(self, global_pos):
        """Show context menu for creating new points"""
        self.menu_open = True
        
        menu = QtWidgets.QMenu(self)
        
        # Add point creation action
        create_point_action = menu.addAction("Create Point Here")
        create_point_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon))
        
        # Add vector creation action
        create_vector_action = menu.addAction("Create Vector Here")
        create_vector_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ArrowRight))
        
        # Add line creation action
        create_line_action = menu.addAction("Create Line...")
        create_line_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogOkButton))
        
        # Add separator and coordinates info
        menu.addSeparator()
        coord_text = f"Position: ({self.cursor_field_pos[0]:.1f}, {self.cursor_field_pos[1]:.1f}) in"
        coord_action = menu.addAction(coord_text)
        coord_action.setEnabled(False)  # Make it non-clickable info
        
        # Connect actions
        create_point_action.triggered.connect(self._create_point_at_cursor)
        create_vector_action.triggered.connect(self._create_vector_at_cursor)
        create_line_action.triggered.connect(self._create_line)
        
        # Show menu and handle closing
        action = menu.exec(global_pos)
        self.menu_open = False
        
        # If no action was selected, just resume cursor tracking
        if not action:
            pass
    
    def _create_point_at_cursor(self):
        """Create a new point at the current cursor position using a dialog"""
        x, y = self.cursor_field_pos
        
        # Show point creation dialog
        dialog = PointCreationDialog(x, y, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Get point data from dialog
            new_point = dialog.get_point_data()
            
            # Ensure unique name
            existing_names = {p["name"] for p in self.points}
            original_name = new_point["name"]
            counter = 1
            while new_point["name"] in existing_names:
                new_point["name"] = f"{original_name} ({counter})"
                counter += 1
            
            # Add to points list
            self.points.append(new_point)
            
            # Select the new point
            self.selected_index = len(self.points) - 1
            
            # Rebuild display and emit signals
            self._rebuild_overlays()
            self.pointAdded.emit()
            self.pointSelected.emit(self.selected_index)
    
    def _create_vector_at_cursor(self):
        """Create a new vector at the current cursor position using a dialog"""
        x, y = self.cursor_field_pos
        
        # Show vector creation dialog
        dialog = VectorCreationDialog(x, y, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Get vector data from dialog
            new_vector = dialog.get_vector_data()
            
            # Ensure unique name
            existing_names = {v["name"] for v in self.vectors}
            original_name = new_vector["name"]
            counter = 1
            while new_vector["name"] in existing_names:
                new_vector["name"] = f"{original_name} ({counter})"
                counter += 1
            
            # Add to vectors list
            self.vectors.append(new_vector)
            
            # Select the new vector
            self.selected_vector_index = len(self.vectors) - 1
            
            # Rebuild display and emit signals
            self._rebuild_overlays()
            self.vectorAdded.emit()
            self.vectorSelected.emit(self.selected_vector_index)
    
    def _create_line(self):
        """Create a new line using a dialog"""
        # Show line creation dialog
        dialog = LineCreationDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Get line data from dialog
            new_line = dialog.get_line_data()
            
            # Validate that the two points are different
            if (abs(new_line["x1"] - new_line["x2"]) < 1e-6 and 
                abs(new_line["y1"] - new_line["y2"]) < 1e-6):
                QtWidgets.QMessageBox.warning(
                    self, "Invalid Line", 
                    "The two endpoints cannot be the same point. Please enter different coordinates."
                )
                return
            
            # Ensure unique name
            existing_names = {line["name"] for line in self.lines}
            original_name = new_line["name"]
            counter = 1
            while new_line["name"] in existing_names:
                new_line["name"] = f"{original_name} ({counter})"
                counter += 1
            
            # Add to lines list
            self.lines.append(new_line)
            
            # Select the new line
            self.selected_line_index = len(self.lines) - 1
            
            # Rebuild display and emit signals
            self._rebuild_overlays()
            self.lineAdded.emit()
            self.lineSelected.emit(self.selected_line_index)

    # --- Public API for controls ---
    def set_grid_opacity(self, op: float):
        self.grid_opacity = clamp(op, 0.05, 1.0)
        c = QtGui.QColor(0, 188, 255, int(255*self.grid_opacity))
        self.grid_pen = QtGui.QPen(c, 0.0)
        self.major_grid_pen = QtGui.QPen(c, 0.0)
        self.major_grid_pen.setWidthF(1.2)
        self._rebuild_overlays()

    def set_show_labels(self, show: bool):
        self.show_labels = show
        self._rebuild_overlays()
    
    def set_show_default_points(self, show: bool):
        """Control visibility of default points"""
        self.show_default_points = show
        self._rebuild_overlays()
        self.pointsReloaded.emit()  # Notify control panel to refresh

    def add_point(self, name, x, y, color="#ffd166"):
        self.user_points.append({"name": name, "x": float(x), "y": float(y), "color": color})
        # Update selected index to account for all visible points
        all_points = self.points
        self.selected_index = len(all_points) - 1
        self._rebuild_overlays()

    def remove_selected(self):
        all_points = self.points
        if 0 <= self.selected_index < len(all_points):
            # Determine if this is a default point or user point
            default_count = len(self.default_points) if self.show_default_points else 0
            if self.selected_index < default_count:
                # This is a default point - remove from default_points
                actual_index = self.selected_index
                del self.default_points[actual_index]
            else:
                # This is a user point - remove from user_points
                user_index = self.selected_index - default_count
                del self.user_points[user_index]
            self.selected_index = -1
            self.selected_index = -1
            self._rebuild_overlays()

    def update_selected(self, name=None, x=None, y=None, color=None):
        all_points = self.points
        if 0 <= self.selected_index < len(all_points):
            # Determine if this is a default point or user point
            default_count = len(self.default_points) if self.show_default_points else 0
            if self.selected_index < default_count:
                # This is a default point - update in default_points
                actual_index = self.selected_index
                p = self.default_points[actual_index]
            else:
                # This is a user point - update in user_points
                user_index = self.selected_index - default_count
                p = self.user_points[user_index]
            
            # Update the point
            if name is not None: p["name"] = name
            if x is not None: p["x"] = float(x)
            if y is not None: p["y"] = float(y)
            if color is not None: p["color"] = color
            self._rebuild_overlays()

    def add_vector(self, name, x, y, magnitude, direction, color="#ff6b6b"):
        self.vectors.append({
            "name": name, 
            "x": float(x), 
            "y": float(y), 
            "magnitude": float(magnitude),
            "direction": float(direction),
            "color": color
        })
        self.selected_vector_index = len(self.vectors) - 1
        self._rebuild_overlays()

    def remove_selected_vector(self):
        if 0 <= self.selected_vector_index < len(self.vectors):
            del self.vectors[self.selected_vector_index]
            self.selected_vector_index = -1
            self._rebuild_overlays()

    def update_selected_vector(self, name=None, x=None, y=None, magnitude=None, direction=None, color=None):
        if 0 <= self.selected_vector_index < len(self.vectors):
            v = self.vectors[self.selected_vector_index]
            if name is not None: v["name"] = name
            if x is not None: v["x"] = float(x)
            if y is not None: v["y"] = float(y)
            if magnitude is not None: v["magnitude"] = float(magnitude)
            if direction is not None: v["direction"] = float(direction)
            if color is not None: v["color"] = color
            self._rebuild_overlays()

    def add_line(self, name, x1, y1, x2, y2, color="#4da6ff"):
        """Add a new line to the field"""
        self.lines.append({
            "name": name,
            "x1": float(x1),
            "y1": float(y1), 
            "x2": float(x2),
            "y2": float(y2),
            "color": color
        })
        self.selected_line_index = len(self.lines) - 1
        self._rebuild_overlays()

    def remove_selected_line(self):
        """Remove the currently selected line"""
        if 0 <= self.selected_line_index < len(self.lines):
            del self.lines[self.selected_line_index]
            self.selected_line_index = -1
            self._rebuild_overlays()

    def update_selected_line(self, name=None, x1=None, y1=None, x2=None, y2=None, color=None):
        """Update the currently selected line"""
        if 0 <= self.selected_line_index < len(self.lines):
            line = self.lines[self.selected_line_index]
            if name is not None: line["name"] = name
            if x1 is not None: line["x1"] = float(x1)
            if y1 is not None: line["y1"] = float(y1)
            if x2 is not None: line["x2"] = float(x2)
            if y2 is not None: line["y2"] = float(y2)
            if color is not None: line["color"] = color
            self._rebuild_overlays()

    def save_points(self, path):
        # Save both default and user points with metadata
        data = {
            "default_points": self.default_points,
            "user_points": self.user_points,
            "show_default_points": self.show_default_points
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_points(self, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                # Legacy format - treat as user points
                self.user_points = data
                self.default_points = []
            else:
                # New format with separate default and user points
                self.default_points = data.get("default_points", [])
                self.user_points = data.get("user_points", [])
                self.show_default_points = data.get("show_default_points", True)
        self.selected_index = -1
        self._rebuild_overlays()

    # === Measurement Tools ===
    def set_measurement_mode(self, enabled: bool):
        """Enable/disable measurement mode"""
        self.measurement_mode = enabled
        if not enabled:
            self.clear_current_measurement()
    
    def set_measurement_tool(self, tool: str):
        """Set the active measurement tool"""
        self.measurement_tool = tool
        self.clear_current_measurement()
    
    def set_coordinate_display_mode(self, show_pixel: bool):
        """Toggle between field coordinates and pixel coordinates"""
        self.show_pixel_coords = show_pixel
        self.update()
    
    def clear_current_measurement(self):
        """Clear the current measurement in progress"""
        self.measurement_points.clear()
        for item in self.measurement_items:
            if item.scene() == self.scene():
                self.scene().removeItem(item)
        self.measurement_items.clear()
    
    def add_measurement_point(self, field_x: float, field_y: float):
        """Add a point to the current measurement"""
        self.measurement_points.append((field_x, field_y))
        self._update_measurement_display()
    
    def _update_measurement_display(self):
        """Update the visual display of the current measurement"""
        # Clear previous measurement visuals
        for item in self.measurement_items:
            if item.scene() == self.scene():
                self.scene().removeItem(item)
        self.measurement_items.clear()
        
        if len(self.measurement_points) < 2:
            return
            
        pen = QtGui.QPen(QtGui.QColor("#ff6b6b"), 2.0)
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        
        if self.measurement_tool == "distance" and len(self.measurement_points) >= 2:
            self._draw_distance_measurement()
        elif self.measurement_tool == "angle" and len(self.measurement_points) >= 3:
            self._draw_angle_measurement()
        elif self.measurement_tool == "area" and len(self.measurement_points) >= 3:
            self._draw_area_measurement()
    
    def _draw_distance_measurement(self):
        """Draw distance measurement between two points"""
        if len(self.measurement_points) < 2:
            return
            
        p1 = self.field_to_scene(*self.measurement_points[0])
        p2 = self.field_to_scene(*self.measurement_points[1])
        
        # Draw line
        pen = QtGui.QPen(QtGui.QColor("#ff6b6b"), 2.0)
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        line = self.scene().addLine(p1.x(), p1.y(), p2.x(), p2.y(), pen)
        line.setZValue(10)
        self.measurement_items.append(line)
        
        # Calculate distance
        x1, y1 = self.measurement_points[0]
        x2, y2 = self.measurement_points[1]
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # Draw measurement label
        mid_x = (p1.x() + p2.x()) / 2
        mid_y = (p1.y() + p2.y()) / 2
        
        label = self.scene().addText(f"{distance:.2f} in")
        label.setDefaultTextColor(QtGui.QColor("#ff6b6b"))
        label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Weight.Bold))
        label.setPos(mid_x, mid_y - 20)
        label.setZValue(11)
        self.measurement_items.append(label)
    
    def _draw_angle_measurement(self):
        """Draw angle measurement between three points"""
        if len(self.measurement_points) < 3:
            return
            
        # Get the three points
        p1_field = self.measurement_points[0]
        p2_field = self.measurement_points[1]  # Vertex point
        p3_field = self.measurement_points[2]
        
        # Convert to scene coordinates
        p1 = self.field_to_scene(*p1_field)
        p2 = self.field_to_scene(*p2_field)
        p3 = self.field_to_scene(*p3_field)
        
        # Draw lines from vertex to other points
        pen = QtGui.QPen(QtGui.QColor("#ff6b6b"), 2.0)
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        
        line1 = self.scene().addLine(p2.x(), p2.y(), p1.x(), p1.y(), pen)
        line2 = self.scene().addLine(p2.x(), p2.y(), p3.x(), p3.y(), pen)
        line1.setZValue(10)
        line2.setZValue(10)
        self.measurement_items.extend([line1, line2])
        
        # Calculate angle
        x1, y1 = p1_field[0] - p2_field[0], p1_field[1] - p2_field[1]
        x2, y2 = p3_field[0] - p2_field[0], p3_field[1] - p2_field[1]
        
        angle1 = math.atan2(y1, x1)
        angle2 = math.atan2(y2, x2)
        angle_diff = abs(angle2 - angle1)
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff
        angle_degrees = math.degrees(angle_diff)
        
        # Draw angle label
        label = self.scene().addText(f"{angle_degrees:.1f}°")
        label.setDefaultTextColor(QtGui.QColor("#ff6b6b"))
        label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Weight.Bold))
        label.setPos(p2.x() + 15, p2.y() - 15)
        label.setZValue(11)
        self.measurement_items.append(label)
    
    def _draw_area_measurement(self):
        """Draw area measurement for polygon"""
        if len(self.measurement_points) < 3:
            return
            
        # Convert points to scene coordinates
        scene_points = [self.field_to_scene(*pt) for pt in self.measurement_points]
        
        # Create polygon
        polygon = QtGui.QPolygonF([QtCore.QPointF(p.x(), p.y()) for p in scene_points])
        
        # Draw polygon outline
        pen = QtGui.QPen(QtGui.QColor("#ff6b6b"), 2.0)
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        brush = QtGui.QBrush(QtGui.QColor(255, 107, 107, 50))  # Semi-transparent fill
        
        poly_item = self.scene().addPolygon(polygon, pen, brush)
        poly_item.setZValue(9)
        self.measurement_items.append(poly_item)
        
        # Calculate area using shoelace formula
        area = 0.0
        n = len(self.measurement_points)
        for i in range(n):
            j = (i + 1) % n
            area += self.measurement_points[i][0] * self.measurement_points[j][1]
            area -= self.measurement_points[j][0] * self.measurement_points[i][1]
        area = abs(area) / 2.0
        
        # Draw area label at centroid
        cx = sum(pt[0] for pt in self.measurement_points) / len(self.measurement_points)
        cy = sum(pt[1] for pt in self.measurement_points) / len(self.measurement_points)
        center_scene = self.field_to_scene(cx, cy)
        
        label = self.scene().addText(f"{area:.1f} sq in")
        label.setDefaultTextColor(QtGui.QColor("#ff6b6b"))
        label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Weight.Bold))
        label.setPos(center_scene.x() - 30, center_scene.y() - 10)
        label.setZValue(11)
        self.measurement_items.append(label)
    
    def calculate_point_to_line_distance(self, point_field: tuple, line_index: int) -> float:
        """Calculate perpendicular distance from a point to a line"""
        if line_index < 0 or line_index >= len(self.lines):
            return 0.0
            
        line = self.lines[line_index]
        px, py = point_field
        x1, y1 = line["x1"], line["y1"]
        x2, y2 = line["x2"], line["y2"]
        
        # Calculate perpendicular distance using formula
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        
        distance = abs(A * px + B * py + C) / math.sqrt(A * A + B * B)
        return distance

    def export_snapshot(self, path):
        # Render the current scene view to an image
        img = QtGui.QImage(self.viewport().size(), QtGui.QImage.Format.Format_ARGB32)
        painter = QtGui.QPainter(img)
        self.render(painter)
        painter.end()
        img.save(path)


class FieldImageSelector(QtWidgets.QWidget):
    """Widget for selecting field images with previews"""
    imageSelected = QtCore.Signal(str)  # Signal emitted when a field image is selected
    
    def __init__(self, current_image_path: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_image_path = current_image_path
        self.available_images = []
        self._build_ui()
        self._discover_field_images()
    
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Title
        title = QtWidgets.QLabel("Field Images")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #8fbcd4;")
        layout.addWidget(title)
        
        # Search field images button
        refresh_btn = QtWidgets.QPushButton("Refresh Image List")
        refresh_btn.clicked.connect(self._discover_field_images)
        layout.addWidget(refresh_btn)
        
        # Scroll area for image list
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for image items
        self.images_container = QtWidgets.QWidget()
        self.images_layout = QtWidgets.QVBoxLayout(self.images_container)
        self.images_layout.setContentsMargins(5, 5, 5, 5)
        self.images_layout.setSpacing(8)
        
        scroll_area.setWidget(self.images_container)
        layout.addWidget(scroll_area)
        
        # Instructions
        instructions = QtWidgets.QLabel(
            "Click on any field image to switch to it. Images are automatically discovered from:\n"
            "• Field Maps/ directory\n"
            "• Current directory\n"
            "• Common field image locations"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        layout.addWidget(instructions)
    
    def _discover_field_images(self):
        """Discover available field images in common locations"""
        self.available_images.clear()
        
        # Search paths - use a more comprehensive list
        search_paths = [
            "Field Maps",  # Relative to current directory
            os.path.join(os.path.dirname(__file__), "Field Maps"),  # Relative to script
            ".",  # Current directory
        ]
        
        # Also add the directory of the current image if it's different
        if self.current_image_path and os.path.exists(self.current_image_path):
            current_dir = os.path.dirname(os.path.abspath(self.current_image_path))
            search_paths.append(current_dir)
        
        # Normalize search paths to absolute paths and remove duplicates
        normalized_paths = set()
        for path in search_paths:
            if os.path.exists(path):
                abs_path = os.path.abspath(path)
                normalized_paths.add(abs_path)
        
        # Common field image patterns
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        field_keywords = ['field', 'decode', 'centerstage', 'powerplay', 'freight', 'skystone', 'rover', 'relic']
        
        found_images = set()  # Use set to avoid duplicates
        field_related_images = set()
        other_images = set()
        
        for search_path in normalized_paths:
            try:
                for root, dirs, files in os.walk(search_path):
                    for file in files:
                        file_lower = file.lower()
                        # Check if it's an image file
                        if any(file_lower.endswith(ext) for ext in image_extensions):
                            full_path = os.path.abspath(os.path.join(root, file))
                            # Separate field-related from other images
                            if any(keyword in file_lower for keyword in field_keywords):
                                field_related_images.add(full_path)
                            else:
                                other_images.add(full_path)
            except (OSError, PermissionError):
                continue
        
        # Combine field-related images first, then add up to 20 other images that aren't already included
        found_images.update(field_related_images)
        other_images_list = sorted(list(other_images - field_related_images))  # Remove any overlap
        found_images.update(other_images_list[:max(0, 25 - len(field_related_images))])
        
        # Convert to sorted list
        self.available_images = sorted(list(found_images))
        
        # Always include the current image if it's not in the list
        if self.current_image_path and os.path.exists(self.current_image_path):
            abs_current = os.path.abspath(self.current_image_path)
            if abs_current not in self.available_images:
                self.available_images.insert(0, abs_current)
        
        self._update_image_list()
    
    def _update_image_list(self):
        """Update the UI with the discovered images"""
        # Clear existing items properly (both widgets and layout items)
        while self.images_layout.count():
            child = self.images_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
            elif child.spacerItem():
                # Remove spacer items properly
                del child
        
        # Add image items
        for image_path in self.available_images:
            image_item = self._create_image_item(image_path)
            self.images_layout.addWidget(image_item)
        
        # Add stretch to push items to top
        self.images_layout.addStretch()
    
    def _create_image_item(self, image_path: str):
        """Create a widget for displaying an image option"""
        # Container widget
        container = QtWidgets.QWidget()
        container.setFixedHeight(120)
        
        # Check if this is the current image
        is_current = os.path.abspath(image_path) == os.path.abspath(self.current_image_path) if self.current_image_path else False
        
        # Style the container
        border_color = "#00ffd0" if is_current else "#555"
        background_color = "#2d2d2d" if is_current else "#1e1e1e"
        container.setStyleSheet(f"""
            QWidget {{
                border: 2px solid {border_color};
                border-radius: 8px;
                background-color: {background_color};
                margin: 2px;
            }}
            QWidget:hover {{
                border-color: #8fbcd4;
                background-color: #2a2a2a;
            }}
        """)
        
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Preview image
        preview_label = QtWidgets.QLabel()
        preview_label.setFixedSize(100, 100)
        preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("border: 1px solid #444; background-color: #333;")
        
        # Load and scale the image for preview
        if os.path.exists(image_path):
            try:
                pixmap = QtGui.QPixmap(image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(98, 98, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
                    preview_label.setPixmap(scaled_pixmap)
                else:
                    preview_label.setText("Invalid\nImage")
            except Exception:
                preview_label.setText("Error\nLoading")
        else:
            preview_label.setText("File\nNot Found")
        
        layout.addWidget(preview_label)
        
        # Info section
        info_layout = QtWidgets.QVBoxLayout()
        
        # File name
        filename = os.path.basename(image_path)
        name_label = QtWidgets.QLabel(filename)
        name_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        name_label.setWordWrap(True)
        info_layout.addWidget(name_label)
        
        # File path (truncated)
        rel_path = os.path.relpath(image_path)
        if len(rel_path) > 40:
            rel_path = "..." + rel_path[-37:]
        path_label = QtWidgets.QLabel(rel_path)
        path_label.setStyleSheet("color: #a0a0a0; font-size: 10px;")
        path_label.setWordWrap(True)
        info_layout.addWidget(path_label)
        
        # Current indicator
        if is_current:
            current_label = QtWidgets.QLabel("● CURRENT")
            current_label.setStyleSheet("color: #00ffd0; font-weight: bold; font-size: 10px;")
            info_layout.addWidget(current_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Make the container clickable
        container.mousePressEvent = lambda event, path=image_path: self._select_image(path)
        container.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        
        return container
    
    def _select_image(self, image_path: str):
        """Handle image selection"""
        if os.path.exists(image_path):
            old_path = self.current_image_path
            self.current_image_path = image_path
            self.imageSelected.emit(image_path)
            # Only refresh the UI display, don't re-discover images unless path changed significantly
            if old_path != image_path:
                self._update_image_list()  # Refresh to update current indicators
    
    def set_current_image(self, image_path: str):
        """Update the current image selection from external source"""
        self.current_image_path = image_path
        self._update_image_list()


class ControlPanel(QtWidgets.QWidget):
    requestAddPointAtCursor = QtCore.Signal()
    imageChangeRequested = QtCore.Signal(str)  # New signal for image change requests

    def __init__(self, view: FieldView, current_image_path: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view = view
        self.current_image_path = current_image_path
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        # Create tab widget
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)
        
        # Create controls tab (existing functionality)
        controls_tab = self._create_controls_tab()
        self.tab_widget.addTab(controls_tab, "Controls")
        
        # Create field selector tab
        self.field_selector = FieldImageSelector(self.current_image_path)
        self.field_selector.imageSelected.connect(self.imageChangeRequested.emit)
        self.tab_widget.addTab(self.field_selector, "Field Images")
        
        layout.addWidget(self.tab_widget)

    def _create_controls_tab(self):
        """Create the original controls tab content"""
        controls_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(controls_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Coordinates display
        coord_group = QtWidgets.QGroupBox("Cursor / Selected")
        g = QtWidgets.QGridLayout(coord_group)
        self.lbl_cursor = QtWidgets.QLabel("Cursor: (x=?, y=?) in")
        self.lbl_snapped = QtWidgets.QLabel("Snapped: (x=?, y=?) in")
        self.lbl_selected = QtWidgets.QLabel("Selected: none")
        g.addWidget(self.lbl_cursor, 0, 0, 1, 2)
        g.addWidget(self.lbl_snapped, 1, 0, 1, 2)
        g.addWidget(self.lbl_selected, 2, 0, 1, 2)
        layout.addWidget(coord_group)

        # Grid controls
        grid_group = QtWidgets.QGroupBox("Grid")
        gg = QtWidgets.QGridLayout(grid_group)
        gg.addWidget(QtWidgets.QLabel("Opacity:"), 0, 0)
        self.slider_opacity = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(5, 100)
        self.slider_opacity.setValue(50)
        gg.addWidget(self.slider_opacity, 0, 1)
        self.lbl_opacity_val = QtWidgets.QLabel("0.50")
        gg.addWidget(self.lbl_opacity_val, 0, 2)

        self.chk_labels = QtWidgets.QCheckBox("Show point labels")
        self.chk_labels.setChecked(True)
        gg.addWidget(self.chk_labels, 1, 0, 1, 3)
        
        self.chk_default_points = QtWidgets.QCheckBox("Show default points")
        self.chk_default_points.setChecked(True)
        gg.addWidget(self.chk_default_points, 2, 0, 1, 3)

        layout.addWidget(grid_group)

        # Measurement tools
        measure_group = QtWidgets.QGroupBox("Measurement Tools")
        mg = QtWidgets.QGridLayout(measure_group)
        
        # Measurement mode toggle
        self.chk_measurement_mode = QtWidgets.QCheckBox("Enable Measurement Mode")
        mg.addWidget(self.chk_measurement_mode, 0, 0, 1, 3)
        
        # Measurement tool selection
        mg.addWidget(QtWidgets.QLabel("Tool:"), 1, 0)
        self.combo_measurement_tool = QtWidgets.QComboBox()
        self.combo_measurement_tool.addItems(["Distance", "Angle", "Area"])
        self.combo_measurement_tool.setEnabled(False)  # Initially disabled
        mg.addWidget(self.combo_measurement_tool, 1, 1, 1, 2)
        
        # Coordinate display mode
        self.chk_pixel_coords = QtWidgets.QCheckBox("Show pixel coordinates")
        mg.addWidget(self.chk_pixel_coords, 2, 0, 1, 3)
        
        # Measurement snap to grid option
        self.chk_measurement_snap = QtWidgets.QCheckBox("Snap measurements to grid")
        self.chk_measurement_snap.setChecked(True)  # Default to snapping enabled
        self.chk_measurement_snap.setToolTip("When enabled, measurement points snap to grid intersections for precision")
        mg.addWidget(self.chk_measurement_snap, 3, 0, 1, 3)
        
        # Clear measurements button
        self.btn_clear_measurements = QtWidgets.QPushButton("Clear Measurements")
        self.btn_clear_measurements.setEnabled(False)  # Initially disabled
        mg.addWidget(self.btn_clear_measurements, 4, 0, 1, 3)
        
        # Instructions label
        self.lbl_measurement_instructions = QtWidgets.QLabel("Enable measurement mode and select a tool to begin")
        self.lbl_measurement_instructions.setStyleSheet("color: #a0a0a0; font-size: 10px;")
        self.lbl_measurement_instructions.setWordWrap(True)
        mg.addWidget(self.lbl_measurement_instructions, 5, 0, 1, 3)
        
        layout.addWidget(measure_group)

        # Points list + editor
        pts_group = QtWidgets.QGroupBox("Points")
        pg = QtWidgets.QGridLayout(pts_group)

        self.list_points = QtWidgets.QListWidget()
        self.list_points.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_points.customContextMenuRequested.connect(self._show_points_context_menu)
        self._refresh_points_list()
        pg.addWidget(self.list_points, 0, 0, 5, 1)

        pg.addWidget(QtWidgets.QLabel("Name"), 0, 1)
        self.ed_name = QtWidgets.QLineEdit()
        pg.addWidget(self.ed_name, 0, 2)

        pg.addWidget(QtWidgets.QLabel("X (in)"), 1, 1)
        self.ed_x = QtWidgets.QDoubleSpinBox()
        self.ed_x.setRange(-HALF_FIELD, HALF_FIELD)
        self.ed_x.setDecimals(3)
        pg.addWidget(self.ed_x, 1, 2)

        pg.addWidget(QtWidgets.QLabel("Y (in)"), 2, 1)
        self.ed_y = QtWidgets.QDoubleSpinBox()
        self.ed_y.setRange(-HALF_FIELD, HALF_FIELD)
        self.ed_y.setDecimals(3)
        pg.addWidget(self.ed_y, 2, 2)

        pg.addWidget(QtWidgets.QLabel("Color"), 3, 1)
        self.ed_color = QtWidgets.QLineEdit("#ffd166")
        pg.addWidget(self.ed_color, 3, 2)

        btn_row = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("Add")
        self.btn_update = QtWidgets.QPushButton("Update")
        self.btn_remove = QtWidgets.QPushButton("Remove")
        btn_row.addWidget(self.btn_add); btn_row.addWidget(self.btn_update); btn_row.addWidget(self.btn_remove)
        pg.addLayout(btn_row, 4, 1, 1, 2)

        layout.addWidget(pts_group)

        # Vectors list + editor
        vec_group = QtWidgets.QGroupBox("Vectors")
        vg = QtWidgets.QGridLayout(vec_group)

        self.list_vectors = QtWidgets.QListWidget()
        self._refresh_vectors_list()
        vg.addWidget(self.list_vectors, 0, 0, 6, 1)

        vg.addWidget(QtWidgets.QLabel("Name"), 0, 1)
        self.ed_vec_name = QtWidgets.QLineEdit()
        vg.addWidget(self.ed_vec_name, 0, 2)

        vg.addWidget(QtWidgets.QLabel("X (in)"), 1, 1)
        self.ed_vec_x = QtWidgets.QDoubleSpinBox()
        self.ed_vec_x.setRange(-HALF_FIELD, HALF_FIELD)
        self.ed_vec_x.setDecimals(3)
        vg.addWidget(self.ed_vec_x, 1, 2)

        vg.addWidget(QtWidgets.QLabel("Y (in)"), 2, 1)
        self.ed_vec_y = QtWidgets.QDoubleSpinBox()
        self.ed_vec_y.setRange(-HALF_FIELD, HALF_FIELD)
        self.ed_vec_y.setDecimals(3)
        vg.addWidget(self.ed_vec_y, 2, 2)

        vg.addWidget(QtWidgets.QLabel("Mag (in)"), 3, 1)
        self.ed_vec_mag = QtWidgets.QDoubleSpinBox()
        self.ed_vec_mag.setRange(0.1, 1000.0)
        self.ed_vec_mag.setDecimals(2)
        vg.addWidget(self.ed_vec_mag, 3, 2)

        vg.addWidget(QtWidgets.QLabel("Dir (°)"), 4, 1)
        self.ed_vec_dir = QtWidgets.QDoubleSpinBox()
        self.ed_vec_dir.setRange(0.0, 359.9)
        self.ed_vec_dir.setDecimals(1)
        self.ed_vec_dir.setWrapping(True)
        vg.addWidget(self.ed_vec_dir, 4, 2)

        vg.addWidget(QtWidgets.QLabel("Color"), 5, 1)
        self.ed_vec_color = QtWidgets.QLineEdit("#ff6b6b")
        vg.addWidget(self.ed_vec_color, 5, 2)

        vec_btn_row = QtWidgets.QHBoxLayout()
        self.btn_vec_add = QtWidgets.QPushButton("Add")
        self.btn_vec_update = QtWidgets.QPushButton("Update")
        self.btn_vec_remove = QtWidgets.QPushButton("Remove")
        vec_btn_row.addWidget(self.btn_vec_add); vec_btn_row.addWidget(self.btn_vec_update); vec_btn_row.addWidget(self.btn_vec_remove)
        vg.addLayout(vec_btn_row, 6, 1, 1, 2)

        layout.addWidget(vec_group)

        # Lines list + editor
        lines_group = QtWidgets.QGroupBox("Lines")
        lg = QtWidgets.QGridLayout(lines_group)

        self.list_lines = QtWidgets.QListWidget()
        self._refresh_lines_list()
        lg.addWidget(self.list_lines, 0, 0, 8, 1)

        lg.addWidget(QtWidgets.QLabel("Name"), 0, 1)
        self.ed_line_name = QtWidgets.QLineEdit()
        lg.addWidget(self.ed_line_name, 0, 2)

        lg.addWidget(QtWidgets.QLabel("Point 1 X (in)"), 1, 1)
        self.ed_line_x1 = QtWidgets.QDoubleSpinBox()
        self.ed_line_x1.setRange(-HALF_FIELD, HALF_FIELD)
        self.ed_line_x1.setDecimals(3)
        lg.addWidget(self.ed_line_x1, 1, 2)

        lg.addWidget(QtWidgets.QLabel("Point 1 Y (in)"), 2, 1)
        self.ed_line_y1 = QtWidgets.QDoubleSpinBox()
        self.ed_line_y1.setRange(-HALF_FIELD, HALF_FIELD)
        self.ed_line_y1.setDecimals(3)
        lg.addWidget(self.ed_line_y1, 2, 2)

        lg.addWidget(QtWidgets.QLabel("Point 2 X (in)"), 3, 1)
        self.ed_line_x2 = QtWidgets.QDoubleSpinBox()
        self.ed_line_x2.setRange(-HALF_FIELD, HALF_FIELD)
        self.ed_line_x2.setDecimals(3)
        lg.addWidget(self.ed_line_x2, 3, 2)

        lg.addWidget(QtWidgets.QLabel("Point 2 Y (in)"), 4, 1)
        self.ed_line_y2 = QtWidgets.QDoubleSpinBox()
        self.ed_line_y2.setRange(-HALF_FIELD, HALF_FIELD)
        self.ed_line_y2.setDecimals(3)
        lg.addWidget(self.ed_line_y2, 4, 2)

        lg.addWidget(QtWidgets.QLabel("Color"), 5, 1)
        self.ed_line_color = QtWidgets.QLineEdit("#4da6ff")
        lg.addWidget(self.ed_line_color, 5, 2)

        # Line equation display
        lg.addWidget(QtWidgets.QLabel("Equation"), 6, 1)
        equation_btn_layout = QtWidgets.QHBoxLayout()
        self.btn_show_equation = QtWidgets.QPushButton("Show Equation")
        self.btn_show_equation.clicked.connect(self._show_line_equation)
        self.btn_test_zone = QtWidgets.QPushButton("Test Zone")
        self.btn_test_zone.clicked.connect(self._test_line_zone)
        equation_btn_layout.addWidget(self.btn_show_equation)
        equation_btn_layout.addWidget(self.btn_test_zone)
        lg.addLayout(equation_btn_layout, 6, 2)

        line_btn_row = QtWidgets.QHBoxLayout()
        self.btn_line_add = QtWidgets.QPushButton("Add")
        self.btn_line_update = QtWidgets.QPushButton("Update")
        self.btn_line_remove = QtWidgets.QPushButton("Remove")
        line_btn_row.addWidget(self.btn_line_add)
        line_btn_row.addWidget(self.btn_line_update)
        line_btn_row.addWidget(self.btn_line_remove)
        lg.addLayout(line_btn_row, 7, 1, 1, 2)

        layout.addWidget(lines_group)

        # Save/Load/Export
        io_group = QtWidgets.QGroupBox("I/O")
        ig = QtWidgets.QHBoxLayout(io_group)
        self.btn_save = QtWidgets.QPushButton("Save Points")
        self.btn_load = QtWidgets.QPushButton("Load Points")
        self.btn_export = QtWidgets.QPushButton("Export Snapshot")
        ig.addWidget(self.btn_save); ig.addWidget(self.btn_load); ig.addWidget(self.btn_export)
        layout.addWidget(io_group)
        
        layout.addStretch(1)

        # Wire signals
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)
        self.chk_labels.toggled.connect(self.view.set_show_labels)
        self.chk_default_points.toggled.connect(self.view.set_show_default_points)
        
        # Measurement controls
        self.chk_measurement_mode.toggled.connect(self._on_measurement_mode_toggled)
        self.combo_measurement_tool.currentTextChanged.connect(self._on_measurement_tool_changed)
        self.chk_pixel_coords.toggled.connect(self.view.set_coordinate_display_mode)
        self.chk_measurement_snap.toggled.connect(self._on_measurement_snap_toggled)
        self.btn_clear_measurements.clicked.connect(self.view.clear_current_measurement)
        
        self.list_points.currentRowChanged.connect(self._on_point_chosen)
        self.btn_add.clicked.connect(self._on_add)
        self.btn_update.clicked.connect(self._on_update)
        self.btn_remove.clicked.connect(self._on_remove)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_load.clicked.connect(self._on_load)
        self.btn_export.clicked.connect(self._on_export)

        self.view.cursorMoved.connect(self._on_cursor_move)
        self.view.pointSelected.connect(self._on_point_selected)
        self.view.pointAdded.connect(self._refresh_points_list)
        self.view.pointsReloaded.connect(self._refresh_points_list)
        self.view.vectorSelected.connect(self._on_vector_selected)
        self.view.vectorAdded.connect(self._refresh_vectors_list)
        self.view.lineSelected.connect(self._on_line_selected)
        self.view.lineAdded.connect(self._refresh_lines_list)
        
        # Vector button connections
        self.list_vectors.currentRowChanged.connect(self._on_vector_chosen)
        self.btn_vec_add.clicked.connect(self._on_vec_add)
        self.btn_vec_update.clicked.connect(self._on_vec_update)
        self.btn_vec_remove.clicked.connect(self._on_vec_remove)
        
        # Line button connections
        self.list_lines.currentRowChanged.connect(self._on_line_chosen)
        self.btn_line_add.clicked.connect(self._on_line_add)
        self.btn_line_update.clicked.connect(self._on_line_update)
        self.btn_line_remove.clicked.connect(self._on_line_remove)

        return controls_widget

    def update_field_image_path(self, new_path: str):
        """Update the field selector with the new current image path"""
        self.current_image_path = new_path
        if hasattr(self, 'field_selector'):
            self.field_selector.set_current_image(new_path)

    def _on_cursor_move(self, x, y):
        # Check if we should show pixel coordinates
        if self.chk_pixel_coords.isChecked():
            # Convert field coordinates back to pixel coordinates
            pixel_point = self.view.field_to_scene(x, y)
            self.lbl_cursor.setText(f"Cursor: (x={pixel_point.x():0.0f}, y={pixel_point.y():0.0f}) px")
            
            # Get current grid spacing and calculate snapped coordinates
            grid_spacing = self.view._get_current_grid_spacing()
            snapped_x, snapped_y = self.view.snap_to_grid(x, y, grid_spacing)
            snapped_pixel_point = self.view.field_to_scene(snapped_x, snapped_y)
            self.lbl_snapped.setText(f"Snapped: (x={snapped_pixel_point.x():0.0f}, y={snapped_pixel_point.y():0.0f}) px")
        else:
            # Show field coordinates in inches (default)
            self.lbl_cursor.setText(f"Cursor: (x={x:0.2f}, y={y:0.2f}) in")
            
            # Get current grid spacing and calculate snapped coordinates
            grid_spacing = self.view._get_current_grid_spacing()
            snapped_x, snapped_y = self.view.snap_to_grid(x, y, grid_spacing)
            self.lbl_snapped.setText(f"Snapped: (x={snapped_x:0.2f}, y={snapped_y:0.2f}) in")

    def _on_point_selected(self, idx):
        self.list_points.setCurrentRow(idx)
        self._populate_editor_from_view()

    def _refresh_points_list(self):
        if not hasattr(self, "list_points"):
            return
        self.list_points.clear()
        
        # Add default points (if visible)
        if self.view.show_default_points:
            for p in self.view.default_points:
                self.list_points.addItem(f"📍 {p['name']}")  # Emoji to indicate default point
        
        # Add user points
        for p in self.view.user_points:
            self.list_points.addItem(f"🔹 {p['name']}")  # Emoji to indicate user point
        
        # Select the current point if there is one
        if 0 <= self.view.selected_index < len(self.view.points):
            self.list_points.setCurrentRow(self.view.selected_index)
            self._populate_editor_from_view()
    
    def _refresh_vectors_list(self):
        if not hasattr(self, "list_vectors"):
            return
        self.list_vectors.clear()
        for v in self.view.vectors:
            self.list_vectors.addItem(v["name"])
        
        # Select the current vector if there is one
        if 0 <= self.view.selected_vector_index < len(self.view.vectors):
            self.list_vectors.setCurrentRow(self.view.selected_vector_index)
            self._populate_vector_editor_from_view()
    
    def _on_vector_selected(self, idx):
        self.list_vectors.setCurrentRow(idx)
        self._populate_vector_editor_from_view()
    
    def _on_vector_chosen(self, row):
        if 0 <= row < len(self.view.vectors):
            self.view.selected_vector_index = row
            self.view._rebuild_overlays()
            self._populate_vector_editor_from_view()
    
    def _populate_vector_editor_from_view(self):
        idx = self.list_vectors.currentRow()
        if 0 <= idx < len(self.view.vectors):
            v = self.view.vectors[idx]
            self.ed_vec_name.setText(v["name"])
            self.ed_vec_x.setValue(v["x"])
            self.ed_vec_y.setValue(v["y"])
            self.ed_vec_mag.setValue(v["magnitude"])
            self.ed_vec_dir.setValue(v["direction"])
            self.ed_vec_color.setText(v.get("color", "#ff6b6b"))
        else:
            self.ed_vec_name.clear()
            self.ed_vec_x.setValue(0.0)
            self.ed_vec_y.setValue(0.0)
            self.ed_vec_mag.setValue(10.0)
            self.ed_vec_dir.setValue(0.0)
            self.ed_vec_color.setText("#ff6b6b")
    
    def _on_vec_add(self):
        name = self.ed_vec_name.text().strip() or "New Vector"
        x = self.ed_vec_x.value()
        y = self.ed_vec_y.value()
        magnitude = self.ed_vec_mag.value()
        direction = self.ed_vec_dir.value()
        color = self.ed_vec_color.text().strip() or "#ff6b6b"
        self.view.add_vector(name, x, y, magnitude, direction, color)
        self._refresh_vectors_list()
        self.list_vectors.setCurrentRow(self.view.selected_vector_index)
    
    def _on_vec_update(self):
        name = self.ed_vec_name.text().strip() or None
        x = self.ed_vec_x.value()
        y = self.ed_vec_y.value()
        magnitude = self.ed_vec_mag.value()
        direction = self.ed_vec_dir.value()
        color = self.ed_vec_color.text().strip() or None
        self.view.update_selected_vector(name, x, y, magnitude, direction, color)
        self._refresh_vectors_list()
        self.list_vectors.setCurrentRow(self.view.selected_vector_index)
    
    def _on_vec_remove(self):
        self.view.remove_selected_vector()
        self._refresh_vectors_list()
        self._populate_vector_editor_from_view()
    
    def _refresh_lines_list(self):
        if not hasattr(self, "list_lines"):
            return
        self.list_lines.clear()
        for line in self.view.lines:
            self.list_lines.addItem(line["name"])
        
        # Select the current line if there is one
        if 0 <= self.view.selected_line_index < len(self.view.lines):
            self.list_lines.setCurrentRow(self.view.selected_line_index)
            self._populate_line_editor_from_view()
    
    def _on_line_selected(self, idx):
        self.list_lines.setCurrentRow(idx)
        self._populate_line_editor_from_view()
    
    def _on_line_chosen(self, row):
        if 0 <= row < len(self.view.lines):
            self.view.selected_line_index = row
            self.view._rebuild_overlays()
            self._populate_line_editor_from_view()
    
    def _populate_line_editor_from_view(self):
        idx = self.list_lines.currentRow()
        if 0 <= idx < len(self.view.lines):
            line = self.view.lines[idx]
            self.ed_line_name.setText(line["name"])
            self.ed_line_x1.setValue(line["x1"])
            self.ed_line_y1.setValue(line["y1"])
            self.ed_line_x2.setValue(line["x2"])
            self.ed_line_y2.setValue(line["y2"])
            self.ed_line_color.setText(line.get("color", "#4da6ff"))
        else:
            self.ed_line_name.clear()
            self.ed_line_x1.setValue(0.0)
            self.ed_line_y1.setValue(0.0)
            self.ed_line_x2.setValue(10.0)
            self.ed_line_y2.setValue(10.0)
            self.ed_line_color.setText("#4da6ff")
    
    def _on_line_add(self):
        name = self.ed_line_name.text().strip() or "New Line"
        x1 = self.ed_line_x1.value()
        y1 = self.ed_line_y1.value()
        x2 = self.ed_line_x2.value()
        y2 = self.ed_line_y2.value()
        color = self.ed_line_color.text().strip() or "#4da6ff"
        
        # Validate that the two points are different
        if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
            QtWidgets.QMessageBox.warning(
                self, "Invalid Line", 
                "The two endpoints cannot be the same point. Please enter different coordinates."
            )
            return
        
        self.view.add_line(name, x1, y1, x2, y2, color)
        self._refresh_lines_list()
        self.list_lines.setCurrentRow(self.view.selected_line_index)
    
    def _on_line_update(self):
        name = self.ed_line_name.text().strip() or None
        x1 = self.ed_line_x1.value()
        y1 = self.ed_line_y1.value()
        x2 = self.ed_line_x2.value()
        y2 = self.ed_line_y2.value()
        color = self.ed_line_color.text().strip() or None
        
        # Validate that the two points are different
        if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
            QtWidgets.QMessageBox.warning(
                self, "Invalid Line", 
                "The two endpoints cannot be the same point. Please enter different coordinates."
            )
            return
        
        self.view.update_selected_line(name, x1, y1, x2, y2, color)
        self._refresh_lines_list()
        self.list_lines.setCurrentRow(self.view.selected_line_index)
    
    def _on_line_remove(self):
        self.view.remove_selected_line()
        self._refresh_lines_list()
        self._populate_line_editor_from_view()
    
    def _show_line_equation(self):
        """Show line equation and evaluation code in a dialog"""
        idx = self.list_lines.currentRow()
        if 0 <= idx < len(self.view.lines):
            line = self.view.lines[idx]
            equation_text = self.view.get_line_equation_string(
                line["x1"], line["y1"], line["x2"], line["y2"]
            )
            
            # Create dialog to show equation
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(f"Line Equation: {line['name']}")
            dialog.setModal(True)
            dialog.resize(500, 400)
            
            layout = QtWidgets.QVBoxLayout(dialog)
            
            # Text area with equation
            text_area = QtWidgets.QTextEdit()
            text_area.setPlainText(equation_text)
            text_area.setReadOnly(True)
            text_area.setFont(QtGui.QFont("Courier New", 10))
            layout.addWidget(text_area)
            
            # Close button
            close_button = QtWidgets.QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.exec()
        else:
            QtWidgets.QMessageBox.information(self, "No Line Selected", 
                                            "Please select a line to show its equation.")
    
    def _test_line_zone(self):
        """Test which side of the line a point is on"""
        idx = self.list_lines.currentRow()
        if 0 <= idx < len(self.view.lines):
            line = self.view.lines[idx]
            
            # Create test dialog
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(f"Test Zone for Line: {line['name']}")
            dialog.setModal(True)
            dialog.resize(450, 350)
            
            layout = QtWidgets.QVBoxLayout(dialog)
            
            # Line info
            info_group = QtWidgets.QGroupBox("Line Information")
            info_layout = QtWidgets.QVBoxLayout(info_group)
            info_text = f"Line: {line['name']}\n"
            info_text += f"Point 1: ({line['x1']:.3f}, {line['y1']:.3f})\n"
            info_text += f"Point 2: ({line['x2']:.3f}, {line['y2']:.3f})"
            info_label = QtWidgets.QLabel(info_text)
            info_layout.addWidget(info_label)
            layout.addWidget(info_group)
            
            # Test point input
            test_group = QtWidgets.QGroupBox("Test Point")
            test_layout = QtWidgets.QGridLayout(test_group)
            
            test_layout.addWidget(QtWidgets.QLabel("X (in):"), 0, 0)
            test_x = QtWidgets.QDoubleSpinBox()
            test_x.setRange(-HALF_FIELD, HALF_FIELD)
            test_x.setDecimals(3)
            test_x.setValue(0.0)
            test_layout.addWidget(test_x, 0, 1)
            
            test_layout.addWidget(QtWidgets.QLabel("Y (in):"), 1, 0)
            test_y = QtWidgets.QDoubleSpinBox()
            test_y.setRange(-HALF_FIELD, HALF_FIELD)
            test_y.setDecimals(3)
            test_y.setValue(0.0)
            test_layout.addWidget(test_y, 1, 1)
            
            test_button = QtWidgets.QPushButton("Test Point")
            test_layout.addWidget(test_button, 2, 0, 1, 2)
            
            layout.addWidget(test_group)
            
            # Results display
            results_group = QtWidgets.QGroupBox("Test Results")
            results_layout = QtWidgets.QVBoxLayout(results_group)
            results_text = QtWidgets.QTextEdit()
            results_text.setReadOnly(True)
            results_text.setMaximumHeight(120)
            results_layout.addWidget(results_text)
            layout.addWidget(results_group)
            
            # Get line equation
            A, B, C = self.view.calculate_line_equation(line["x1"], line["y1"], line["x2"], line["y2"])
            
            def test_point():
                x = test_x.value()
                y = test_y.value()
                result = self.view.evaluate_line_equation(A, B, C, x, y)
                
                result_text = f"Test Point: ({x:.3f}, {y:.3f})\n"
                result_text += f"Equation Result: {result:.6f}\n\n"
                
                if abs(result) < 1e-6:
                    result_text += "✓ Point is ON the line\n"
                elif result > 0:
                    if abs(B) < 1e-10:  # Vertical line
                        result_text += "✓ Point is on the RIGHT side\n"
                        result_text += f"  Zone: ⁅x ≥ {-C/A:.3f}⁆\n"
                        result_text += "  Code: if (evaluateLine(x, y) > 0) { /* right side */ }\n"
                    else:
                        result_text += "✓ Point is ABOVE the line\n"
                        # Show zone inequality
                        m = -A/B
                        b = -C/B
                        if abs(m - 0.5) < 1e-6:
                            m_str = "1/2 "
                        elif abs(m + 0.5) < 1e-6:
                            m_str = "-1/2 "
                        elif abs(m - round(m)) < 1e-6:
                            m_val = int(round(m))
                            m_str = f"{m_val} " if m_val != 1 else ""
                            if m_val == -1:
                                m_str = "-"
                        else:
                            m_str = f"{m:.3f} "
                        
                        if abs(b) < 1e-6:
                            zone_eq = f"⁅y ≥ {m_str}x⁆" if m_str != "" else "⁅y ≥ x⁆"
                            if m_str == "-":
                                zone_eq = "⁅y ≥ -x⁆"
                        else:
                            b_str = f" + {b:.3f}" if b >= 0 else f" - {abs(b):.3f}"
                            zone_eq = f"⁅y ≥ {m_str}x{b_str}⁆" if m_str != "" else f"⁅y ≥ x{b_str}⁆"
                            if m_str == "-":
                                zone_eq = f"⁅y ≥ -x{b_str}⁆"
                        
                        result_text += f"  Zone: {zone_eq}\n"
                        result_text += "  Code: if (evaluateLine(x, y) > 0) { /* above line */ }\n"
                else:
                    if abs(B) < 1e-10:  # Vertical line
                        result_text += "✓ Point is on the LEFT side\n"
                        result_text += f"  Zone: ⁅x ≤ {-C/A:.3f}⁆\n"
                        result_text += "  Code: if (evaluateLine(x, y) < 0) { /* left side */ }\n"
                    else:
                        result_text += "✓ Point is BELOW the line\n"
                        # Show zone inequality
                        m = -A/B
                        b = -C/B
                        if abs(m - 0.5) < 1e-6:
                            m_str = "1/2 "
                        elif abs(m + 0.5) < 1e-6:
                            m_str = "-1/2 "
                        elif abs(m - round(m)) < 1e-6:
                            m_val = int(round(m))
                            m_str = f"{m_val} " if m_val != 1 else ""
                            if m_val == -1:
                                m_str = "-"
                        else:
                            m_str = f"{m:.3f} "
                        
                        if abs(b) < 1e-6:
                            zone_eq = f"⁅y ≤ {m_str}x⁆" if m_str != "" else "⁅y ≤ x⁆"
                            if m_str == "-":
                                zone_eq = "⁅y ≤ -x⁆"
                        else:
                            b_str = f" + {b:.3f}" if b >= 0 else f" - {abs(b):.3f}"
                            zone_eq = f"⁅y ≤ {m_str}x{b_str}⁆" if m_str != "" else f"⁅y ≤ x{b_str}⁆"
                            if m_str == "-":
                                zone_eq = f"⁅y ≤ -x{b_str}⁆"
                        
                        result_text += f"  Zone: {zone_eq}\n"
                        result_text += "  Code: if (evaluateLine(x, y) < 0) { /* below line */ }\n"
                
                results_text.setPlainText(result_text)
            
            test_button.clicked.connect(test_point)
            
            # Robot code section
            code_group = QtWidgets.QGroupBox("Robot Code Function")
            code_layout = QtWidgets.QVBoxLayout(code_group)
            code_text = QtWidgets.QTextEdit()
            code_text.setReadOnly(True)
            code_text.setMaximumHeight(80)
            code_function = f"double evaluateLine(double x, double y) {{\n"
            code_function += f"    return {A:.6f} * x + {B:.6f} * y + {C:.6f};\n"
            code_function += f"}}"
            code_text.setPlainText(code_function)
            code_text.setFont(QtGui.QFont("Courier New", 9))
            code_layout.addWidget(code_text)
            layout.addWidget(code_group)
            
            # Close button
            close_button = QtWidgets.QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            # Test the line endpoints initially
            test_point()
            
            dialog.exec()
        else:
            QtWidgets.QMessageBox.information(self, "No Line Selected", 
                                            "Please select a line to test its zone.")

    def _populate_editor_from_view(self):
        idx = self.list_points.currentRow()
        if 0 <= idx < len(self.view.points):
            p = self.view.points[idx]
            self.ed_name.setText(p["name"])
            self.ed_x.setValue(p["x"])
            self.ed_y.setValue(p["y"])
            self.ed_color.setText(p.get("color", "#ffd166"))
            self.lbl_selected.setText(f"Selected: {p['name']}  ({p['x']:0.2f}, {p['y']:0.2f}) in")
        else:
            self.ed_name.clear()
            self.ed_x.setValue(0.0)
            self.ed_y.setValue(0.0)
            self.ed_color.setText("#ffd166")
            self.lbl_selected.setText("Selected: none")

    def _on_opacity_changed(self, val):
        op = val / 100.0
        self.lbl_opacity_val.setText(f"{op:0.2f}")
        self.view.set_grid_opacity(op)

    def _on_measurement_mode_toggled(self, enabled: bool):
        """Handle measurement mode toggle"""
        self.view.set_measurement_mode(enabled)
        self.combo_measurement_tool.setEnabled(enabled)
        self.btn_clear_measurements.setEnabled(enabled)
        
        if enabled:
            tool = self.combo_measurement_tool.currentText().lower()
            self.view.set_measurement_tool(tool)
            
            instructions = {
                "distance": "Click two points to measure distance",
                "angle": "Click three points to measure angle (vertex in middle)",
                "area": "Click multiple points to measure area (polygon)"
            }
            self.lbl_measurement_instructions.setText(instructions.get(tool, "Select a measurement tool"))
        else:
            self.lbl_measurement_instructions.setText("Enable measurement mode and select a tool to begin")
    
    def _on_measurement_tool_changed(self, tool_name: str):
        """Handle measurement tool change"""
        tool = tool_name.lower()
        self.view.set_measurement_tool(tool)
        
        instructions = {
            "distance": "Click two points to measure distance",
            "angle": "Click three points to measure angle (vertex in middle)", 
            "area": "Click multiple points to measure area (polygon)"
        }
        self.lbl_measurement_instructions.setText(instructions.get(tool, "Select a measurement tool"))

    def _on_measurement_snap_toggled(self, enabled: bool):
        """Handle measurement snap to grid toggle"""
        self.view.measurement_snap_to_grid = enabled

    def _on_point_chosen(self, row):
        self.view.selected_index = row
        self.view._rebuild_overlays()
        self._populate_editor_from_view()

    def _on_add(self):
        name = self.ed_name.text().strip() or "Point"
        x = self.ed_x.value()
        y = self.ed_y.value()
        color = self.ed_color.text().strip() or "#ffd166"
        self.view.add_point(name, x, y, color)
        self._refresh_points_list()
        self.list_points.setCurrentRow(self.view.selected_index)

    def _on_update(self):
        name = self.ed_name.text().strip() or None
        x = self.ed_x.value()
        y = self.ed_y.value()
        color = self.ed_color.text().strip() or None
        self.view.update_selected(name, x, y, color)
        self._refresh_points_list()
        self.list_points.setCurrentRow(self.view.selected_index)

    def _on_remove(self):
        self.view.remove_selected()
        self._refresh_points_list()
        self._populate_editor_from_view()

    def _on_save(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Points", "points.json", "JSON (*.json)")
        if path:
            try:
                self.view.save_points(path)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Save Error", str(e))

    def _on_load(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Points", "", "JSON (*.json)")
        if path:
            try:
                self.view.load_points(path)
                self._refresh_points_list()
                self._populate_editor_from_view()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Load Error", str(e))

    def _on_export(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Snapshot", "field_view.png", "PNG (*.png)")
        if path:
            try:
                self.view.export_snapshot(path)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Export Error", str(e))

    def _show_points_context_menu(self, position):
        """Show context menu for points list"""
        if not self.list_points.itemAt(position):
            return  # No item at position
            
        menu = QtWidgets.QMenu(self)
        
        # Get selected point info
        current_row = self.list_points.currentRow()
        if 0 <= current_row < len(self.view.points):
            point = self.view.points[current_row]
            
            # Edit point action
            edit_action = menu.addAction("Edit Point")
            edit_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
            edit_action.triggered.connect(self._edit_selected_point)
            
            # Copy coordinates action
            copy_action = menu.addAction("Copy Coordinates")
            copy_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogListView))
            copy_action.triggered.connect(self._copy_point_coordinates)
            
            # Copy point data action
            copy_data_action = menu.addAction("Copy Point Data")
            copy_data_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton))
            copy_data_action.triggered.connect(self._copy_point_data)
            
            menu.addSeparator()
            
            # Zoom to point action
            zoom_action = menu.addAction("Zoom to Point")
            zoom_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon))
            zoom_action.triggered.connect(self._zoom_to_point)
            
            menu.addSeparator()
            
            # Delete point action
            delete_action = menu.addAction("Delete Point")
            delete_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TrashIcon))
            delete_action.triggered.connect(self._delete_selected_point_from_list)
            
            # Show point info
            menu.addSeparator()
            info_text = f"Point: {point['name']} at ({point['x']:.1f}, {point['y']:.1f})"
            info_action = menu.addAction(info_text)
            info_action.setEnabled(False)
            
        menu.exec(self.list_points.mapToGlobal(position))

    def _edit_selected_point(self):
        """Open edit dialog for selected point"""
        current_row = self.list_points.currentRow()
        if 0 <= current_row < len(self.view.points):
            self.list_points.setCurrentRow(current_row)
            self._on_point_selected(current_row)

    def _copy_point_coordinates(self):
        """Copy point coordinates to clipboard"""
        current_row = self.list_points.currentRow()
        if 0 <= current_row < len(self.view.points):
            point = self.view.points[current_row]
            coords_text = f"{point['x']:.2f}, {point['y']:.2f}"
            QtWidgets.QApplication.clipboard().setText(coords_text)

    def _copy_point_data(self):
        """Copy full point data to clipboard as JSON"""
        current_row = self.list_points.currentRow()
        if 0 <= current_row < len(self.view.points):
            point = self.view.points[current_row]
            data_text = json.dumps(point, indent=2)
            QtWidgets.QApplication.clipboard().setText(data_text)

    def _zoom_to_point(self):
        """Zoom and center view on selected point"""
        current_row = self.list_points.currentRow()
        if 0 <= current_row < len(self.view.points):
            point = self.view.points[current_row]
            # Convert field coordinates to scene coordinates
            scene_point = self.view.field_to_scene(point['x'], point['y'])
            # Center view on the point
            self.view.centerOn(scene_point)
            # Set a reasonable zoom level
            self.view.setTransform(QtGui.QTransform().scale(2.0, 2.0))

    def _delete_selected_point_from_list(self):
        """Delete selected point from list with confirmation"""
        current_row = self.list_points.currentRow()
        if 0 <= current_row < len(self.view.points):
            point = self.view.points[current_row]
            reply = QtWidgets.QMessageBox.question(self, "Delete Point", 
                                                  f"Delete point '{point['name']}'?",
                                                  QtWidgets.QMessageBox.StandardButton.Yes | 
                                                  QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                del self.view.points[current_row]
                self.view.selected_index = -1
                self.view._rebuild_overlays()
                self._refresh_points_list()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, image_path: str):
        super().__init__()
        
        # Initialize settings
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Store the current image path
        self.current_image_path = image_path
        
        # Initialize recent files list
        self.recent_files = self._load_recent_files()
        
        # Track undo/redo actions
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_levels = 50  # Maximum number of undo operations to remember

        # Load background image
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        original_pixmap = QtGui.QPixmap(image_path)
        if original_pixmap.isNull():
            raise RuntimeError("Failed to load image (unsupported format or corrupt file).")
        
        # Auto-resize the image for consistent coordinate system
        pixmap = self._auto_resize_field_image(original_pixmap)

        # Scene + View
        scene = QtWidgets.QGraphicsScene(self)
        self.view = FieldView(scene, pixmap, image_path)
        self.setCentralWidget(self.view)
        
        # Create toolbar first
        self._create_toolbar()

        # Controls (dock on right) - wrapped in scroll area
        self.panel = ControlPanel(self.view, self.current_image_path)
        
        # Connect image change signal
        self.panel.imageChangeRequested.connect(self._on_image_change_requested)
        
        # Create tab widget for controls and instructions
        tab_widget = QtWidgets.QTabWidget()
        
        # Add controls tab
        controls_scroll = QtWidgets.QScrollArea()
        controls_scroll.setWidget(self.panel)
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        controls_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tab_widget.addTab(controls_scroll, "Controls")
        
        # Add instructions tab
        instructions_widget = self._create_instructions_widget()
        instructions_scroll = QtWidgets.QScrollArea()
        instructions_scroll.setWidget(instructions_widget)
        instructions_scroll.setWidgetResizable(True)
        tab_widget.addTab(instructions_scroll, "Help & Instructions")
        
        # Create scroll area for the tab widget
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(tab_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(350)  # Ensure minimum width for tabs
        
        dock = QtWidgets.QDockWidget("Controls", self)
        dock.setWidget(scroll_area)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                        QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        dock.setAllowedAreas(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea | 
                           QtCore.Qt.DockWidgetArea.RightDockWidgetArea |
                           QtCore.Qt.DockWidgetArea.TopDockWidgetArea |
                           QtCore.Qt.DockWidgetArea.BottomDockWidgetArea)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock)

        # Window styling
        self.setWindowTitle(f"FTC Field Map Viewer – {os.path.basename(image_path)}")
        self.setMinimumSize(1100, 800)

        # Status bar – live coordinate readout
        self.status = self.statusBar()
        self.coord_lbl = QtWidgets.QLabel("Cursor: (x=?, y=?) in")
        self.status.addWidget(self.coord_lbl)
        self.view.cursorMoved.connect(self._update_status_coords)

        # Menu actions
        self._build_menu()
    
    def _on_image_change_requested(self, new_image_path: str):
        """Handle requests to change the field image"""
        try:
            if not os.path.exists(new_image_path):
                QtWidgets.QMessageBox.warning(self, "Image Not Found", f"The selected image file was not found:\n{new_image_path}")
                return
                
            original_pixmap = QtGui.QPixmap(new_image_path)
            if original_pixmap.isNull():
                QtWidgets.QMessageBox.warning(self, "Invalid Image", f"Cannot load the selected image file:\n{new_image_path}\n\nPlease ensure it's a valid image format.")
                return
            
            # Auto-resize image to maintain field coordinate system consistency
            pixmap = self._auto_resize_field_image(original_pixmap)
            
            # Update the image in the view
            self.view.image_item.setPixmap(pixmap)
            self.view.image_rect = self.view.image_item.boundingRect()
            self.view.setSceneRect(self.view.image_rect)
            
            # Reload default points for the new field
            self.view.reload_default_points_for_image(new_image_path)
            
            # Rebuild overlays after points are loaded
            self.view._rebuild_overlays()
            
            # Update current image path
            self.current_image_path = new_image_path
            
            # Update window title
            self.setWindowTitle(f"FTC Field Map Viewer – {os.path.basename(new_image_path)}")
            
            # Reset view to fit the new image
            self._reset_view()
            
            # Update the field selector to reflect the new current image
            self.panel.update_field_image_path(new_image_path)
            
            # Add to recent files
            self._add_recent_file(new_image_path)
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error Loading Image", f"An error occurred while loading the image:\n{str(e)}")
    
    def _auto_resize_field_image(self, pixmap: QtGui.QPixmap) -> QtGui.QPixmap:
        """Auto-resize field image to maintain consistent coordinate system scaling"""
        # Target size for optimal field representation
        # We want the field to be well-sized for the coordinate grid
        # Standard field is 141" x 141", so we maintain square aspect ratio
        
        # Calculate target size based on field dimensions
        # Use a reasonable default size that works well with the grid system
        target_size = 800  # pixels for 141-inch field
        
        # Get original dimensions
        original_width = pixmap.width()
        original_height = pixmap.height()
        
        # Calculate aspect ratio
        aspect_ratio = original_width / original_height
        
        # For FTC fields, we typically want square or near-square images
        # If the image is significantly non-square, we'll fit it to a square
        if abs(aspect_ratio - 1.0) < 0.2:  # Nearly square (within 20%)
            # Keep it square
            new_size = target_size
            scaled_pixmap = pixmap.scaled(new_size, new_size, 
                                        QtCore.Qt.AspectRatioMode.IgnoreAspectRatio, 
                                        QtCore.Qt.TransformationMode.SmoothTransformation)
        else:
            # Maintain aspect ratio but fit within target size
            if aspect_ratio > 1.0:  # Wide image
                new_width = target_size
                new_height = int(target_size / aspect_ratio)
            else:  # Tall image
                new_width = int(target_size * aspect_ratio)
                new_height = target_size
            
            scaled_pixmap = pixmap.scaled(new_width, new_height, 
                                        QtCore.Qt.AspectRatioMode.KeepAspectRatio, 
                                        QtCore.Qt.TransformationMode.SmoothTransformation)
        
        return scaled_pixmap

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        act_open = QtGui.QAction("Open Field Image…", self)
        act_open.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self._open_image)
        file_menu.addAction(act_open)
        
        act_save = QtGui.QAction("Save Points…", self)
        act_save.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self._save_points)
        file_menu.addAction(act_save)
        
        act_load = QtGui.QAction("Load Points…", self)
        act_load.setShortcut(QtGui.QKeySequence("Ctrl+L"))
        act_load.triggered.connect(self._load_points)
        file_menu.addAction(act_load)
        
        file_menu.addSeparator()
        
        # Recent files submenu
        recent_menu = file_menu.addMenu("Recent Files")
        self._update_recent_files_menu(recent_menu)
        
        file_menu.addSeparator()

        act_exit = QtGui.QAction("Exit", self)
        act_exit.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        act_undo = QtGui.QAction("Undo", self)
        act_undo.setShortcut(QtGui.QKeySequence.StandardKey.Undo)
        act_undo.triggered.connect(self._undo)
        edit_menu.addAction(act_undo)
        
        act_redo = QtGui.QAction("Redo", self)
        act_redo.setShortcut(QtGui.QKeySequence.StandardKey.Redo)
        act_redo.triggered.connect(self._redo)
        edit_menu.addAction(act_redo)
        
        edit_menu.addSeparator()
        
        act_add_point = QtGui.QAction("Add Point", self)
        act_add_point.setShortcut(QtGui.QKeySequence("Ctrl+A"))
        act_add_point.triggered.connect(self._add_point_at_center)
        edit_menu.addAction(act_add_point)
        
        act_delete_point = QtGui.QAction("Delete Selected Point", self)
        act_delete_point.setShortcut(QtGui.QKeySequence.StandardKey.Delete)
        act_delete_point.triggered.connect(self._delete_selected_point)
        edit_menu.addAction(act_delete_point)
        
        act_copy_coords = QtGui.QAction("Copy Coordinates", self)
        act_copy_coords.setShortcut(QtGui.QKeySequence.StandardKey.Copy)
        act_copy_coords.triggered.connect(self._copy_coordinates)
        edit_menu.addAction(act_copy_coords)

        # View Menu
        view_menu = menubar.addMenu("&View")
        
        act_zoom_in = QtGui.QAction("Zoom In", self)
        act_zoom_in.setShortcut(QtGui.QKeySequence.StandardKey.ZoomIn)
        act_zoom_in.triggered.connect(self._zoom_in)
        view_menu.addAction(act_zoom_in)
        
        act_zoom_out = QtGui.QAction("Zoom Out", self)
        act_zoom_out.setShortcut(QtGui.QKeySequence.StandardKey.ZoomOut)
        act_zoom_out.triggered.connect(self._zoom_out)
        view_menu.addAction(act_zoom_out)
        
        reset_zoom = QtGui.QAction("Reset View", self)
        reset_zoom.setShortcut(QtGui.QKeySequence("Ctrl+0"))
        reset_zoom.triggered.connect(self._reset_view)
        view_menu.addAction(reset_zoom)
        
        view_menu.addSeparator()
        
        act_toggle_grid = QtGui.QAction("Toggle Grid", self)
        act_toggle_grid.setShortcut(QtGui.QKeySequence("Ctrl+G"))
        act_toggle_grid.triggered.connect(self._toggle_grid)
        view_menu.addAction(act_toggle_grid)
        
        act_toggle_measurement = QtGui.QAction("Toggle Measurement Mode", self)
        act_toggle_measurement.setShortcut(QtGui.QKeySequence("Ctrl+M"))
        act_toggle_measurement.triggered.connect(self._toggle_measurement_mode)
        view_menu.addAction(act_toggle_measurement)
        
        view_menu.addSeparator()
        
        # UI Layout options
        act_reset_layout = QtGui.QAction("Reset UI Layout", self)
        act_reset_layout.setShortcut(QtGui.QKeySequence("Ctrl+Shift+R"))
        act_reset_layout.triggered.connect(self._reset_ui_layout)
        view_menu.addAction(act_reset_layout)
        
        act_fullscreen = QtGui.QAction("Toggle Fullscreen", self)
        act_fullscreen.setShortcut(QtGui.QKeySequence.StandardKey.FullScreen)
        act_fullscreen.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(act_fullscreen)
        
        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        
        act_clear_measurements = QtGui.QAction("Clear Measurements", self)
        act_clear_measurements.setShortcut(QtGui.QKeySequence("Ctrl+Shift+C"))
        act_clear_measurements.triggered.connect(self._clear_measurements)
        tools_menu.addAction(act_clear_measurements)
        
        act_export_image = QtGui.QAction("Export as Image…", self)
        act_export_image.setShortcut(QtGui.QKeySequence("Ctrl+E"))
        act_export_image.triggered.connect(self._export_image)
        tools_menu.addAction(act_export_image)

        help_menu = menubar.addMenu("&Help")
        about = QtGui.QAction("About", self)
        about.triggered.connect(self._about)
        help_menu.addAction(about)
        
        # Keyboard shortcuts help
        shortcuts_help = QtGui.QAction("Keyboard Shortcuts", self)
        shortcuts_help.setShortcut(QtGui.QKeySequence.StandardKey.HelpContents)
        shortcuts_help.triggered.connect(self._show_shortcuts_help)
        help_menu.addAction(shortcuts_help)

    def _update_status_coords(self, x, y):
        self.coord_lbl.setText(f"Cursor: (x={x:0.2f}, y={y:0.2f}) in")

    def _reset_view(self):
        self.view.resetTransform()
        self.view.fitInView(self.view.image_rect, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def _open_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Field Image", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            # Use the new image change mechanism
            self._on_image_change_requested(path)

    def _about(self):
        QtWidgets.QMessageBox.information(self, "About",
            f"FTC Field Map Viewer v{__version__}\n\n"
            "Professional field visualization and measurement tool\n\n"
            "Features:\n"
            "• Interactive field visualization with measurement tools\n"
            "• Points, vectors, and lines with drag & drop support\n"
            "• Comprehensive keyboard shortcuts and context menus\n"
            "• Undo/redo system with 50-level history\n"
            "• Customizable UI with moveable panels\n"
            "• Recent files management\n"
            "• Professional toolbar and help system\n\n"
            "Check the 'Help & Instructions' tab for complete usage guide.\n"
            "Dark theme with smooth antialiased rendering."
        )

    def _create_toolbar(self):
        """Create the main toolbar with common actions"""
        toolbar = self.addToolBar("Quick Actions")
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # File operations
        open_action = QtGui.QAction("Open", self)
        open_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon))
        open_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        open_action.setToolTip("Open field image (Ctrl+O)")
        open_action.triggered.connect(self._open_image)
        toolbar.addAction(open_action)
        
        save_action = QtGui.QAction("Save", self)
        save_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton))
        save_action.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        save_action.setToolTip("Save points configuration (Ctrl+S)")
        save_action.triggered.connect(self._save_points)
        toolbar.addAction(save_action)
        
        # Recent files menu
        recent_action = QtGui.QAction("Recent", self)
        recent_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
        recent_action.setToolTip("Open recent file")
        recent_menu = QtWidgets.QMenu(self)
        self._update_recent_files_menu(recent_menu)
        recent_action.setMenu(recent_menu)
        toolbar.addAction(recent_action)
        
        toolbar.addSeparator()
        
        # View operations
        zoom_in_action = QtGui.QAction("Zoom In", self)
        zoom_in_icon = self._create_text_icon("+", QtGui.QColor("white"))
        zoom_in_action.setIcon(zoom_in_icon)
        zoom_in_action.setShortcut(QtGui.QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.setToolTip("Zoom in (Ctrl++)")
        zoom_in_action.triggered.connect(self._zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QtGui.QAction("Zoom Out", self)
        zoom_out_icon = self._create_text_icon("−", QtGui.QColor("white"))
        zoom_out_action.setIcon(zoom_out_icon)
        zoom_out_action.setShortcut(QtGui.QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.setToolTip("Zoom out (Ctrl+-)")
        zoom_out_action.triggered.connect(self._zoom_out)
        toolbar.addAction(zoom_out_action)
        
        reset_view_action = QtGui.QAction("Fit View", self)
        reset_view_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload))
        reset_view_action.setShortcut(QtGui.QKeySequence("Ctrl+0"))
        reset_view_action.setToolTip("Reset and fit view (Ctrl+0)")
        reset_view_action.triggered.connect(self._reset_view)
        toolbar.addAction(reset_view_action)
        
        toolbar.addSeparator()
        
        # Edit operations
        undo_action = QtGui.QAction("Undo", self)
        undo_icon = self._create_text_icon("↶", QtGui.QColor("white"))
        undo_action.setIcon(undo_icon)
        undo_action.setShortcut(QtGui.QKeySequence.StandardKey.Undo)
        undo_action.setToolTip("Undo last action (Ctrl+Z)")
        undo_action.triggered.connect(self._undo)
        toolbar.addAction(undo_action)
        
        redo_action = QtGui.QAction("Redo", self)
        redo_icon = self._create_text_icon("↷", QtGui.QColor("white"))
        redo_action.setIcon(redo_icon)
        redo_action.setShortcut(QtGui.QKeySequence.StandardKey.Redo)
        redo_action.setToolTip("Redo last action (Ctrl+Y)")
        redo_action.triggered.connect(self._redo)
        toolbar.addAction(redo_action)
        
        toolbar.addSeparator()
        
        # Grid and measurement toggles
        grid_action = QtGui.QAction("Grid", self)
        grid_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton))
        grid_action.setCheckable(True)
        grid_action.setChecked(True)
        grid_action.setShortcut(QtGui.QKeySequence("Ctrl+G"))
        grid_action.setToolTip("Toggle grid visibility (Ctrl+G)")
        grid_action.triggered.connect(self._toggle_grid)
        toolbar.addAction(grid_action)
        
        measurement_action = QtGui.QAction("Measure", self)
        measurement_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon))
        measurement_action.setCheckable(True)
        measurement_action.setShortcut(QtGui.QKeySequence("Ctrl+M"))
        measurement_action.setToolTip("Toggle measurement mode (Ctrl+M)")
        measurement_action.triggered.connect(self._toggle_measurement_mode)
        toolbar.addAction(measurement_action)
        
        # Store action references for later use
        self.toolbar_actions = {
            'undo': undo_action,
            'redo': redo_action,
            'grid': grid_action,
            'measurement': measurement_action,
            'recent_menu': recent_menu
        }

    def _load_recent_files(self) -> List[str]:
        """Load recent files from settings"""
        recent = self.settings.value("recent_files", [])
        if isinstance(recent, str):
            recent = [recent]
        elif not isinstance(recent, list):
            recent = []
        
        # Filter out non-existent files
        existing_files = [f for f in recent if os.path.exists(f)]
        return existing_files[:MAX_RECENT_FILES]

    def _save_recent_files(self):
        """Save recent files to settings"""
        self.settings.setValue("recent_files", self.recent_files)

    def _add_recent_file(self, file_path: str):
        """Add a file to recent files list"""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:MAX_RECENT_FILES]
        self._save_recent_files()
        self._update_recent_files_menu(self.toolbar_actions['recent_menu'])

    def _update_recent_files_menu(self, menu: QtWidgets.QMenu):
        """Update the recent files menu"""
        menu.clear()
        if not self.recent_files:
            no_recent = QtGui.QAction("No recent files", self)
            no_recent.setEnabled(False)
            menu.addAction(no_recent)
        else:
            for file_path in self.recent_files:
                action = QtGui.QAction(os.path.basename(file_path), self)
                action.setToolTip(file_path)
                action.triggered.connect(lambda checked, path=file_path: self._on_image_change_requested(path))
                menu.addAction(action)
            
            menu.addSeparator()
            clear_action = QtGui.QAction("Clear Recent Files", self)
            clear_action.triggered.connect(self._clear_recent_files)
            menu.addAction(clear_action)

    def _clear_recent_files(self):
        """Clear the recent files list"""
        self.recent_files.clear()
        self._save_recent_files()
        self._update_recent_files_menu(self.toolbar_actions['recent_menu'])

    def _save_points(self):
        """Save current points configuration"""
        if hasattr(self.view, 'points'):
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Points", "", "JSON Files (*.json)")
            if path:
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(self.view.points, f, indent=2)
                    self.statusBar().showMessage(f"Points saved to {path}", 3000)
                    self._add_recent_file(path)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Save Error", f"Failed to save points:\n{str(e)}")

    def _zoom_in(self):
        """Zoom in by a factor"""
        self.view.scale(1.25, 1.25)

    def _zoom_out(self):
        """Zoom out by a factor"""
        self.view.scale(0.8, 0.8)

    def _toggle_grid(self):
        """Toggle grid visibility"""
        # Grid is always visible in this implementation
        # You could add a grid_visible property to FieldView if needed
        self.statusBar().showMessage("Grid toggle not yet implemented", 2000)

    def _toggle_measurement_mode(self):
        """Toggle measurement mode"""
        if hasattr(self.panel, 'chk_measurement_mode'):
            current_state = self.panel.chk_measurement_mode.isChecked()
            self.panel.chk_measurement_mode.setChecked(not current_state)

    def _undo(self):
        """Undo last action"""
        if self.undo_stack:
            action = self.undo_stack.pop()
            
            # Create reverse action for redo
            reverse_action = self._create_reverse_action(action)
            self.redo_stack.append(reverse_action)
            
            # Apply the undo action
            self._apply_action(action)
            self._update_undo_redo_state()
            self.statusBar().showMessage(f"Undid: {action.get('description', 'Unknown action')}", 2000)

    def _redo(self):
        """Redo last undone action"""
        if self.redo_stack:
            action = self.redo_stack.pop()
            
            # Create reverse action for undo
            reverse_action = self._create_reverse_action(action)
            self.undo_stack.append(reverse_action)
            
            # Apply the redo action
            self._apply_action(action)
            self._update_undo_redo_state()
            self.statusBar().showMessage(f"Redid: {action.get('description', 'Unknown action')}", 2000)

    def _record_action(self, action_type: str, description: str, data: dict):
        """Record an action for undo/redo"""
        action = {
            'type': action_type,
            'description': description,
            'data': data.copy(),
            'timestamp': QtCore.QDateTime.currentDateTime().toString()
        }
        
        self.undo_stack.append(action)
        
        # Limit undo stack size
        if len(self.undo_stack) > self.max_undo_levels:
            self.undo_stack.pop(0)
        
        # Clear redo stack when new action is recorded
        self.redo_stack.clear()
        self._update_undo_redo_state()

    def _create_reverse_action(self, action: dict) -> dict:
        """Create the reverse action for undo/redo"""
        action_type = action['type']
        
        if action_type == 'add_point':
            return {
                'type': 'delete_point',
                'description': f"Remove point {action['data']['point']['name']}",
                'data': {'index': action['data']['index']}
            }
        elif action_type == 'delete_point':
            return {
                'type': 'add_point',
                'description': f"Restore point {action['data']['point']['name']}",
                'data': {
                    'point': action['data']['point'],
                    'index': action['data']['index']
                }
            }
        elif action_type == 'modify_point':
            return {
                'type': 'modify_point',
                'description': f"Revert point {action['data']['new_point']['name']} changes",
                'data': {
                    'index': action['data']['index'],
                    'old_point': action['data']['new_point'],
                    'new_point': action['data']['old_point']
                }
            }
        elif action_type == 'load_points':
            return {
                'type': 'load_points',
                'description': "Restore previous points configuration",
                'data': {
                    'old_points': action['data']['new_points'],
                    'new_points': action['data']['old_points']
                }
            }
        
        return action  # Fallback for unknown action types

    def _apply_action(self, action: dict):
        """Apply an undo/redo action"""
        action_type = action['type']
        data = action['data']
        
        if action_type == 'add_point':
            # Insert point at specific index in user_points
            index = data['index']
            point = data['point']
            # Calculate the correct index in user_points
            user_index = max(0, index - len(self.view.default_points) if self.view.show_default_points else index)
            self.view.user_points.insert(user_index, point)
            
        elif action_type == 'delete_point':
            # Remove point at specific index from user_points
            index = data['index']
            # Calculate the correct index in user_points
            if self.view.show_default_points and index < len(self.view.default_points):
                # Can't delete default points
                return
            user_index = index - len(self.view.default_points) if self.view.show_default_points else index
            if 0 <= user_index < len(self.view.user_points):
                del self.view.user_points[user_index]
                
        elif action_type == 'modify_point':
            # Modify point at specific index
            index = data['index']
            new_point = data['new_point']
            # Calculate the correct index in user_points
            if self.view.show_default_points and index < len(self.view.default_points):
                # Can't modify default points
                return
            user_index = index - len(self.view.default_points) if self.view.show_default_points else index
            if 0 <= user_index < len(self.view.user_points):
                self.view.user_points[user_index] = new_point.copy()
                
        elif action_type == 'load_points':
            # Replace all user points
            self.view.user_points = data['new_points'].copy()
        
        # Update UI
        self.view._rebuild_overlays()
        self.panel._refresh_points_list()

    def _update_undo_redo_state(self):
        """Update undo/redo button states"""
        if hasattr(self, 'toolbar_actions'):
            self.toolbar_actions['undo'].setEnabled(bool(self.undo_stack))
            self.toolbar_actions['redo'].setEnabled(bool(self.redo_stack))
            
            # Update tooltips with action descriptions
            if self.undo_stack:
                last_action = self.undo_stack[-1]
                self.toolbar_actions['undo'].setToolTip(f"Undo: {last_action.get('description', 'Unknown action')}")
            else:
                self.toolbar_actions['undo'].setToolTip("Undo (no actions to undo)")
                
            if self.redo_stack:
                last_action = self.redo_stack[-1]
                self.toolbar_actions['redo'].setToolTip(f"Redo: {last_action.get('description', 'Unknown action')}")
            else:
                self.toolbar_actions['redo'].setToolTip("Redo (no actions to redo)")

    def closeEvent(self, event):
        """Handle application closing"""
        # Save UI layout
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self._save_recent_files()
        super().closeEvent(event)

    def showEvent(self, event):
        """Handle application showing"""
        # Restore UI layout
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)
            
        super().showEvent(event)

    def _load_points(self):
        """Load points configuration from file"""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Points", "", "JSON Files (*.json)")
        if path:
            try:
                self.view.load_points(path)
                self.panel._refresh_points_list()
                self.statusBar().showMessage(f"Points loaded from {path}", 3000)
                self._add_recent_file(path)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Load Error", f"Failed to load points:\n{str(e)}")

    def _add_point_at_center(self):
        """Add a new point at the center of the field"""
        new_point = {
            "name": f"Point {len(self.view.points) + 1}",
            "x": 0.0,
            "y": 0.0,
            "color": "#FF0000"
        }
        
        # Record action for undo
        action_data = {
            'point': new_point.copy(),
            'index': len(self.view.points)
        }
        self._record_action('add_point', f"Add point {new_point['name']}", action_data)
        
        self.view.user_points.append(new_point)
        self.view._rebuild_overlays()
        self.panel._refresh_points_list()
        self.statusBar().showMessage("New point added at center", 2000)

    def _delete_selected_point(self):
        """Delete the currently selected point"""
        if hasattr(self.view, 'selected_index') and 0 <= self.view.selected_index < len(self.view.points):
            point = self.view.points[self.view.selected_index]
            point_name = point['name']
            
            # Check if it's a default point (can't delete those)
            if self.view.show_default_points and self.view.selected_index < len(self.view.default_points):
                self.statusBar().showMessage("Cannot delete default points", 2000)
                return
            
            # Record action for undo
            action_data = {
                'point': point.copy(),
                'index': self.view.selected_index
            }
            self._record_action('delete_point', f"Delete point {point_name}", action_data)
            
            # Calculate user_points index
            user_index = self.view.selected_index - len(self.view.default_points) if self.view.show_default_points else self.view.selected_index
            if 0 <= user_index < len(self.view.user_points):
                del self.view.user_points[user_index]
                
            self.view.selected_index = -1
            self.view._rebuild_overlays()
            self.panel._refresh_points_list()
            self.statusBar().showMessage(f"Point '{point_name}' deleted", 2000)
        else:
            self.statusBar().showMessage("No point selected to delete", 2000)

    def _copy_coordinates(self):
        """Copy selected point coordinates to clipboard"""
        if hasattr(self.view, 'selected_index') and 0 <= self.view.selected_index < len(self.view.points):
            point = self.view.points[self.view.selected_index]
            coords_text = f"{point['x']:.2f}, {point['y']:.2f}"
            QtWidgets.QApplication.clipboard().setText(coords_text)
            self.statusBar().showMessage(f"Coordinates copied: {coords_text}", 2000)
        else:
            self.statusBar().showMessage("No point selected to copy", 2000)

    def _clear_measurements(self):
        """Clear all measurement data"""
        if hasattr(self.view, 'measurement_points'):
            self.view.measurement_points.clear()
            self.view._rebuild_overlays()
            self.statusBar().showMessage("Measurements cleared", 2000)

    def _export_image(self):
        """Export current view as image"""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Image", "", "PNG Files (*.png);;JPEG Files (*.jpg)")
        if path:
            try:
                # Create a pixmap of the current view
                pixmap = self.view.grab()
                pixmap.save(path)
                self.statusBar().showMessage(f"Image exported to {path}", 3000)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Export Error", f"Failed to export image:\n{str(e)}")

    def _show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog"""
        shortcuts_text = """
<h3>Keyboard Shortcuts</h3>
<table style="font-family: monospace;">
<tr><td><b>File Operations:</b></td><td></td></tr>
<tr><td>Ctrl+O</td><td>Open field image</td></tr>
<tr><td>Ctrl+S</td><td>Save points configuration</td></tr>
<tr><td>Ctrl+L</td><td>Load points configuration</td></tr>
<tr><td>Ctrl+Q</td><td>Exit application</td></tr>

<tr><td><b>Edit Operations:</b></td><td></td></tr>
<tr><td>Ctrl+Z</td><td>Undo last action</td></tr>
<tr><td>Ctrl+Y</td><td>Redo last action</td></tr>
<tr><td>Ctrl+A</td><td>Add point at center</td></tr>
<tr><td>Delete</td><td>Delete selected point</td></tr>
<tr><td>Ctrl+C</td><td>Copy point coordinates</td></tr>

<tr><td><b>View Operations:</b></td><td></td></tr>
<tr><td>Ctrl++</td><td>Zoom in</td></tr>
<tr><td>Ctrl+-</td><td>Zoom out</td></tr>
<tr><td>Ctrl+0</td><td>Reset view to fit</td></tr>
<tr><td>Ctrl+G</td><td>Toggle grid</td></tr>
<tr><td>Ctrl+M</td><td>Toggle measurement mode</td></tr>

<tr><td><b>Tools:</b></td><td></td></tr>
<tr><td>Ctrl+Shift+C</td><td>Clear measurements</td></tr>
<tr><td>Ctrl+E</td><td>Export as image</td></tr>
<tr><td>F1</td><td>Show this help</td></tr>

<tr><td><b>Mouse Controls:</b></td><td></td></tr>
<tr><td>Left Click</td><td>Select/place point</td></tr>
<tr><td>Right Click</td><td>Context menu</td></tr>
<tr><td>Mouse Wheel</td><td>Zoom in/out</td></tr>
<tr><td>Drag</td><td>Pan view</td></tr>
<tr><td>Shift+Click</td><td>Precise placement (no grid snap)</td></tr>
</table>
        """
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setTextFormat(QtCore.Qt.TextFormat.RichText)
        msg.setText(shortcuts_text)
        msg.exec()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        """Handle global keyboard shortcuts"""
        key = event.key()
        modifiers = event.modifiers()
        
        # Handle additional shortcuts not covered by menu actions
        if key == QtCore.Qt.Key.Key_Escape:
            # Exit measurement mode or clear selection
            if hasattr(self.panel, 'chk_measurement_mode') and self.panel.chk_measurement_mode.isChecked():
                self.panel.chk_measurement_mode.setChecked(False)
            elif hasattr(self.view, 'selected_index'):
                self.view.selected_index = -1
                self.view._rebuild_overlays()
            self.statusBar().showMessage("Selection cleared", 1000)
            
        elif key == QtCore.Qt.Key.Key_Space:
            # Quick measurement mode toggle
            if hasattr(self.panel, 'chk_measurement_mode'):
                current_state = self.panel.chk_measurement_mode.isChecked()
                self.panel.chk_measurement_mode.setChecked(not current_state)
                
        elif key >= QtCore.Qt.Key.Key_1 and key <= QtCore.Qt.Key.Key_9:
            # Quick point selection (1-9)
            point_index = key - QtCore.Qt.Key.Key_1
            if point_index < len(self.view.points):
                self.view.selected_index = point_index
                self.view._rebuild_overlays()
                self.panel._refresh_points_list()
                point_name = self.view.points[point_index]['name']
                self.statusBar().showMessage(f"Selected point: {point_name}", 2000)
        
        super().keyPressEvent(event)

    def _reset_ui_layout(self):
        """Reset UI layout to default"""
        # Clear saved layout settings
        self.settings.remove("geometry")
        self.settings.remove("windowState")
        
        # Reset window to default size and position
        self.resize(1100, 800)
        self.move(100, 100)
        
        # Reset dock widget to right side
        for dock in self.findChildren(QtWidgets.QDockWidget):
            dock.setFloating(False)
            self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock)
        
        # Reset toolbar to top
        for toolbar in self.findChildren(QtWidgets.QToolBar):
            toolbar.setFloatable(False)
            self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, toolbar)
            toolbar.setFloatable(True)
        
        self.statusBar().showMessage("UI layout reset to default", 3000)

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
            self.statusBar().showMessage("Exited fullscreen mode", 2000)
        else:
            self.showFullScreen()
            self.statusBar().showMessage("Entered fullscreen mode - Press F11 to exit", 3000)

    def _create_text_icon(self, text: str, color: QtGui.QColor, size: int = 16) -> QtGui.QIcon:
        """Create a text-based icon with specified color for better visibility"""
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        font = painter.font()
        font.setPointSize(size - 4)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(color)
        
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        
        return QtGui.QIcon(pixmap)

    def _create_instructions_widget(self) -> QtWidgets.QWidget:
        """Create the comprehensive instructions widget for the help tab"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Welcome section
        welcome = QtWidgets.QLabel("Welcome to FTC Field Viewer")
        welcome.setStyleSheet("font-size: 18px; font-weight: bold; color: #00bcff; margin-bottom: 10px;")
        layout.addWidget(welcome)
        
        # Quick start section
        quick_start = QtWidgets.QGroupBox("Quick Start")
        qs_layout = QtWidgets.QVBoxLayout(quick_start)
        qs_text = QtWidgets.QLabel(
            "1. Use the Field Image selector to choose your field\n"
            "2. Right-click on the field to add points, vectors, or lines\n"
            "3. Use the toolbar for quick access to common actions\n"
            "4. Enable measurement mode for distance, angle, and area calculations"
        )
        qs_text.setWordWrap(True)
        qs_layout.addWidget(qs_text)
        layout.addWidget(quick_start)
        
        # Mouse controls section
        mouse_controls = QtWidgets.QGroupBox("Mouse Controls")
        mc_layout = QtWidgets.QVBoxLayout(mouse_controls)
        mc_text = QtWidgets.QLabel(
            "• Left Click: Select points, create measurements\n"
            "• Right Click: Context menu (add points, vectors, lines)\n"
            "• Drag: Pan the view around\n"
            "• Mouse Wheel: Zoom in/out\n"
            "• Shift + Click: Precise placement (no grid snap)\n"
            "• Drag Points: Click and drag existing points to move them"
        )
        mc_text.setWordWrap(True)
        mc_layout.addWidget(mc_text)
        layout.addWidget(mouse_controls)
        
        # Keyboard shortcuts section
        shortcuts = QtWidgets.QGroupBox("Essential Keyboard Shortcuts")
        sc_layout = QtWidgets.QVBoxLayout(shortcuts)
        sc_text = QtWidgets.QLabel(
            "File Operations:\n"
            "  Ctrl+O: Open field image\n"
            "  Ctrl+S: Save points configuration\n"
            "  Ctrl+L: Load points configuration\n\n"
            "Edit Operations:\n"
            "  Ctrl+Z: Undo last action\n"
            "  Ctrl+Y: Redo last action\n"
            "  Ctrl+A: Add point at center\n"
            "  Delete: Delete selected point\n"
            "  Ctrl+C: Copy point coordinates\n\n"
            "View Operations:\n"
            "  Ctrl++: Zoom in\n"
            "  Ctrl+-: Zoom out\n"
            "  Ctrl+0: Reset view to fit\n"
            "  Ctrl+G: Toggle grid\n"
            "  Ctrl+M: Toggle measurement mode\n"
            "  F11: Toggle fullscreen\n\n"
            "Quick Access:\n"
            "  F1: Show complete keyboard shortcuts\n"
            "  Escape: Clear selection/exit measurement mode\n"
            "  Space: Quick measurement mode toggle\n"
            "  1-9: Quick point selection"
        )
        sc_text.setWordWrap(True)
        sc_text.setStyleSheet("font-family: monospace; font-size: 10px;")
        sc_layout.addWidget(sc_text)
        layout.addWidget(shortcuts)
        
        # Measurement tools section
        measurement = QtWidgets.QGroupBox("Measurement Tools")
        m_layout = QtWidgets.QVBoxLayout(measurement)
        m_text = QtWidgets.QLabel(
            "1. Enable 'Measurement Mode' checkbox\n"
            "2. Select measurement tool from dropdown:\n"
            "   • Distance: Click two points to measure distance\n"
            "   • Angle: Click three points to measure angle\n"
            "   • Area: Click multiple points to define polygon area\n"
            "3. Use 'Snap measurements to grid' for precision\n"
            "   • Hold Shift to temporarily disable snapping\n"
            "4. Use 'Clear Measurements' to reset\n"
            "5. Toggle 'Show Pixel Coordinates' for different coordinate systems"
        )
        m_text.setWordWrap(True)
        m_layout.addWidget(m_text)
        layout.addWidget(measurement)
        
        # Points and objects section
        objects = QtWidgets.QGroupBox("Points, Vectors & Lines")
        o_layout = QtWidgets.QVBoxLayout(objects)
        o_text = QtWidgets.QLabel(
            "Points:\n"
            "• Right-click field → 'Create Point Here'\n"
            "• Edit properties in the Controls tab\n"
            "• Right-click point list for more options\n"
            "• Drag points directly on the field\n\n"
            "Vectors:\n"
            "• Right-click field → 'Create Vector Here'\n"
            "• Set magnitude and direction\n"
            "• Useful for robot heading visualization\n\n"
            "Lines:\n"
            "• Create boundary lines for zones\n"
            "• Generate equations for robot code\n"
            "• Test point positions relative to lines"
        )
        o_text.setWordWrap(True)
        o_layout.addWidget(o_text)
        layout.addWidget(objects)
        
        # Advanced features section
        advanced = QtWidgets.QGroupBox("Advanced Features")
        a_layout = QtWidgets.QVBoxLayout(advanced)
        a_text = QtWidgets.QLabel(
            "Drag & Drop:\n"
            "• Drag image files from explorer to load them\n"
            "• Drag JSON files to load point configurations\n\n"
            "UI Customization:\n"
            "• Drag dock panels to any edge or float them\n"
            "• Use 'Reset UI Layout' to restore defaults\n"
            "• Fullscreen mode for presentations\n\n"
            "File Management:\n"
            "• Recent files dropdown in toolbar\n"
            "• Export current view as image\n"
            "• Save/load complete configurations"
        )
        a_text.setWordWrap(True)
        a_layout.addWidget(a_text)
        layout.addWidget(advanced)
        
        # Tips section
        tips = QtWidgets.QGroupBox("Pro Tips")
        t_layout = QtWidgets.QVBoxLayout(tips)
        t_text = QtWidgets.QLabel(
            "🎯 Hold Shift while clicking to disable grid snapping for precise placement\n"
            "⚡ Use number keys 1-9 to quickly select points\n"
            "🔄 All actions are undoable - experiment freely!\n"
            "📏 Grid spacing automatically adjusts based on zoom level\n"
            "🎨 Default points are read-only, but you can hide them\n"
            "💾 Your UI layout and recent files are remembered between sessions\n"
            "🖱️ Context menus (right-click) are available everywhere\n"
            "⌨️ Press F1 anytime for complete keyboard shortcuts reference"
        )
        t_text.setWordWrap(True)
        t_layout.addWidget(t_text)
        layout.addWidget(tips)
        
        layout.addStretch()
        return widget

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            # Check if any of the URLs are valid file types
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.json']:
                        event.acceptProposedAction()
                        return
        event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        """Handle drag move events"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        """Handle drop events"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = os.path.splitext(file_path)[1].lower()
                    
                    if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                        # Handle image files
                        self._on_image_change_requested(file_path)
                        self.statusBar().showMessage(f"Loaded image: {os.path.basename(file_path)}", 3000)
                        event.acceptProposedAction()
                        return
                    elif file_ext == '.json':
                        # Handle JSON configuration files
                        try:
                            self.view.load_points(file_path)
                            self.panel._refresh_points_list()
                            self.statusBar().showMessage(f"Loaded points: {os.path.basename(file_path)}", 3000)
                            self._add_recent_file(file_path)
                            event.acceptProposedAction()
                            return
                        except Exception as e:
                            QtWidgets.QMessageBox.critical(self, "Load Error", f"Failed to load JSON file:\n{str(e)}")
                            
        event.ignore()


def run_app():
    parser = argparse.ArgumentParser(description="FTC Field Map Viewer – DECODE")
    parser.add_argument("--image", default="Field Maps/decode-dark.png",
                        help="Path to the field background image")
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_QSS)

    win = MainWindow(args.image)
    win.show()
    win._reset_view()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()
