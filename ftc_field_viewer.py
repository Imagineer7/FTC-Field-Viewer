# ftc_field_viewer.py
# Interactive FTC field map viewer with grid and editable points.
# See usage instructions at the bottom.

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtWidgets import QGraphicsEffect
import json
import math
import os
import sys
import argparse

FIELD_SIZE_IN = 141.0
HALF_FIELD = FIELD_SIZE_IN / 2.0

DEFAULT_POINTS = [
    {"name": "Red Goal (ID 24)", "x": -58.3727, "y": 55.6425, "color": "#ff4d4d"},
    {"name": "Blue Goal (ID 20)", "x": -58.3727, "y": -55.6425, "color": "#4da6ff"},
]

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
    vectorSelected = QtCore.Signal(int)       # emits index in vectors list or -1
    vectorAdded = QtCore.Signal()             # emits when a new vector is created

    def __init__(self, scene, image_pixmap, *args, **kwargs):
        super().__init__(scene, *args, **kwargs)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.image_item = QtWidgets.QGraphicsPixmapItem(image_pixmap)
        self.scene().addItem(self.image_item)

        self.grid_opacity = 0.5
        self.grid_pen = QtGui.QPen(QtGui.QColor(0, 188, 255, int(255*self.grid_opacity)), 0.0)
        self.major_grid_every = 6  # bold every N lines
        self.major_grid_pen = QtGui.QPen(QtGui.QColor(0, 188, 255, int(255*self.grid_opacity)), 0.0)
        self.major_grid_pen.setWidthF(1.2)

        self.points = list(DEFAULT_POINTS)  # list of dicts with name,x,y,color
        self.point_items = []               # QGraphicsEllipseItem + label
        self.selected_index = -1
        self.show_labels = True
        
        # Vector management
        self.vectors = []                   # list of dicts with name,x,y,magnitude,direction,color
        self.vector_items = []              # QGraphicsItem for vector arrows
        self.selected_vector_index = -1

        # Cursor-following snap point
        self.cursor_point = None
        self.cursor_field_pos = (0, 0)  # Current snapped position in field coordinates
        self.menu_open = False  # Track if context menu is open
        
        self.image_rect = self.image_item.boundingRect()
        self.setSceneRect(self.image_rect)
        self.setBackgroundBrush(QtGui.QColor("#0b0f14"))

        self._rebuild_overlays()

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

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        scene_pos = self.mapToScene(event.position().toPoint())
        x_in, y_in = self.scene_to_field(scene_pos)
        
        # Update cursor point position (only if menu is not open)
        if not self.menu_open:
            # Check if Shift key is pressed to disable snapping
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier:
                # No snapping when shift is pressed
                self.cursor_field_pos = (x_in, y_in)
            else:
                # Use the same grid spacing as the visual grid for cursor snapping
                snap_resolution = self._get_current_grid_spacing()
                snapped_x, snapped_y = self.snap_to_grid(x_in, y_in, snap_resolution)
                self.cursor_field_pos = (snapped_x, snapped_y)
            self._draw_cursor_point()
        
        self.cursorMoved.emit(x_in, y_in)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            # Show context menu for point creation
            self._show_context_menu(event.globalPosition().toPoint())
        super().mousePressEvent(event)
    
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
        
        # Add separator and coordinates info
        menu.addSeparator()
        coord_text = f"Position: ({self.cursor_field_pos[0]:.1f}, {self.cursor_field_pos[1]:.1f}) in"
        coord_action = menu.addAction(coord_text)
        coord_action.setEnabled(False)  # Make it non-clickable info
        
        # Connect actions
        create_point_action.triggered.connect(self._create_point_at_cursor)
        create_vector_action.triggered.connect(self._create_vector_at_cursor)
        
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

    def add_point(self, name, x, y, color="#ffd166"):
        self.points.append({"name": name, "x": float(x), "y": float(y), "color": color})
        self.selected_index = len(self.points) - 1
        self._rebuild_overlays()

    def remove_selected(self):
        if 0 <= self.selected_index < len(self.points):
            del self.points[self.selected_index]
            self.selected_index = -1
            self._rebuild_overlays()

    def update_selected(self, name=None, x=None, y=None, color=None):
        if 0 <= self.selected_index < len(self.points):
            p = self.points[self.selected_index]
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

    def save_points(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.points, f, indent=2)

    def load_points(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.points = json.load(f)
        self.selected_index = -1
        self._rebuild_overlays()

    def export_snapshot(self, path):
        # Render the current scene view to an image
        img = QtGui.QImage(self.viewport().size(), QtGui.QImage.Format.Format_ARGB32)
        painter = QtGui.QPainter(img)
        self.render(painter)
        painter.end()
        img.save(path)


class ControlPanel(QtWidgets.QWidget):
    requestAddPointAtCursor = QtCore.Signal()

    def __init__(self, view: FieldView, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view = view
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12,12,12,12)
        layout.setSpacing(10)

        # Coordinates display
        coord_group = QtWidgets.QGroupBox("Cursor / Selected")
        g = QtWidgets.QGridLayout(coord_group)
        self.lbl_cursor = QtWidgets.QLabel("Cursor: (x=?, y=?) in")
        self.lbl_selected = QtWidgets.QLabel("Selected: none")
        g.addWidget(self.lbl_cursor, 0, 0, 1, 2)
        g.addWidget(self.lbl_selected, 1, 0, 1, 2)
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

        layout.addWidget(grid_group)

        # Points list + editor
        pts_group = QtWidgets.QGroupBox("Points")
        pg = QtWidgets.QGridLayout(pts_group)

        self.list_points = QtWidgets.QListWidget()
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

        # Save/Load/Export
        io_group = QtWidgets.QGroupBox("I/O")
        ig = QtWidgets.QHBoxLayout(io_group)
        self.btn_save = QtWidgets.QPushButton("Save Points")
        self.btn_load = QtWidgets.QPushButton("Load Points")
        self.btn_export = QtWidgets.QPushButton("Export Snapshot")
        ig.addWidget(self.btn_save); ig.addWidget(self.btn_load); ig.addWidget(self.btn_export)
        layout.addWidget(io_group)

        # Instructions
        info = QtWidgets.QGroupBox("Instructions")
        il = QtWidgets.QVBoxLayout(info)
        lbl = QtWidgets.QLabel(
            "• Pan: click + drag  • Zoom: mouse wheel\n"
            "• Click a point to select it\n"
            "• Use Add/Update/Remove to manage points\n"
            "• Grid spacing is in inches (bold every 6)"
        )
        lbl.setWordWrap(True)
        il.addWidget(lbl)
        layout.addWidget(info)
        layout.addStretch(1)

        # Wire signals
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)
        self.chk_labels.toggled.connect(self.view.set_show_labels)
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
        self.view.vectorSelected.connect(self._on_vector_selected)
        self.view.vectorAdded.connect(self._refresh_vectors_list)
        
        # Vector button connections
        self.list_vectors.currentRowChanged.connect(self._on_vector_chosen)
        self.btn_vec_add.clicked.connect(self._on_vec_add)
        self.btn_vec_update.clicked.connect(self._on_vec_update)
        self.btn_vec_remove.clicked.connect(self._on_vec_remove)

    def _on_cursor_move(self, x, y):
        self.lbl_cursor.setText(f"Cursor: (x={x:0.2f}, y={y:0.2f}) in")

    def _on_point_selected(self, idx):
        self.list_points.setCurrentRow(idx)
        self._populate_editor_from_view()

    def _refresh_points_list(self):
        if not hasattr(self, "list_points"):
            return
        self.list_points.clear()
        for p in self.view.points:
            self.list_points.addItem(p["name"])
        
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


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, image_path: str):
        super().__init__()

        # Load background image
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        pixmap = QtGui.QPixmap(image_path)
        if pixmap.isNull():
            raise RuntimeError("Failed to load image (unsupported format or corrupt file).")

        # Scene + View
        scene = QtWidgets.QGraphicsScene(self)
        self.view = FieldView(scene, pixmap)
        self.setCentralWidget(self.view)

        # Controls (dock on right) - wrapped in scroll area
        self.panel = ControlPanel(self.view)
        
        # Create scroll area for the control panel
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(self.panel)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumWidth(320)  # Ensure minimum width for controls
        
        dock = QtWidgets.QDockWidget("Controls", self)
        dock.setWidget(scroll_area)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock)

        # Window styling
        self.setWindowTitle("FTC Field Map Viewer – DECODE")
        self.setMinimumSize(1100, 800)

        # Status bar – live coordinate readout
        self.status = self.statusBar()
        self.coord_lbl = QtWidgets.QLabel("Cursor: (x=?, y=?) in")
        self.status.addWidget(self.coord_lbl)
        self.view.cursorMoved.connect(self._update_status_coords)

        # Menu actions
        self._build_menu()

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        act_open = QtGui.QAction("Open Field Image…", self)
        act_open.triggered.connect(self._open_image)
        file_menu.addAction(act_open)

        act_exit = QtGui.QAction("Exit", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        view_menu = menubar.addMenu("&View")
        reset_zoom = QtGui.QAction("Reset View", self)
        reset_zoom.triggered.connect(self._reset_view)
        view_menu.addAction(reset_zoom)

        help_menu = menubar.addMenu("&Help")
        about = QtGui.QAction("About", self)
        about.triggered.connect(self._about)
        help_menu.addAction(about)

    def _update_status_coords(self, x, y):
        self.coord_lbl.setText(f"Cursor: (x={x:0.2f}, y={y:0.2f}) in")

    def _reset_view(self):
        self.view.resetTransform()
        self.view.fitInView(self.view.image_rect, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def _open_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Field Image", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            pixmap = QtGui.QPixmap(path)
            if not pixmap.isNull():
                self.view.image_item.setPixmap(pixmap)
                self.view.image_rect = self.view.image_item.boundingRect()
                self.view.setSceneRect(self.view.image_rect)
                self.view._rebuild_overlays()
                self._reset_view()

    def _about(self):
        QtWidgets.QMessageBox.information(self, "About",
            "FTC Field Map Viewer – DECODE\n\n"
            "• Drag to pan, wheel to zoom\n"
            "• Grid spacing adjustable (inches)\n"
            "• Add/remove/rename points, save/load JSON\n"
            "• Export snapshot as PNG\n"
            "Dark theme, smooth antialiased rendering.\n"
        )


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
