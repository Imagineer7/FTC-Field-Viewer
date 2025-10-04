# field_editor.py
# Comprehensive Field Editor for FTC Field Viewer
# 
# FEATURES:
# 🎯 Point Management: Create, edit, delete field points with coordinates and colors
# 🖼️ Image Association: Link field images to point configurations
# 📐 Zone Creation: Define field zones using mathematical equations (e.g., x >= 23 && y > 22)
# 💾 Data Persistence: Save/load field configurations as JSON files
# 🔄 Live Preview: Real-time visualization of zones and points on the field
# 
# USAGE:
# - Access via "Field Editor" tab in the main FTC Field Viewer window
# - Switch between "Field Viewer" mode (path planning, measurements) and "Field Editor" mode
# - Create custom field configurations for different game seasons or field layouts
# - Export configurations for team sharing and version control
#
# ZONE EQUATIONS:
# - Use x, y coordinates in field inches (origin at center)
# - Operators: >=, <=, >, <, ==, !=
# - Logic: && (and), || (or)
# - Parentheses for grouping
# - Examples:
#   * x >= 0 && x <= 50 && y > 20    (Rectangular region)
#   * (x > -30 && x < 30) || y > 40  (Complex zone with OR logic)
#   * x*x + y*y <= 900              (Circular region with radius 30)

__version__ = "1.0.0"

from PySide6 import QtCore, QtGui, QtWidgets
import json
import os
import re
import math
from typing import List, Dict, Optional, Tuple
import copy

class Zone:
    """Represents a field zone with equation-based boundaries"""
    
    # Define zone type color schemes
    ZONE_TYPE_COLORS = {
        "red_alliance": "#ff4d4d",
        "blue_alliance": "#4da6ff", 
        "neutral": "#ffaa00",
        "launch": "#ff8800",
        "parking": "#cc6600",
        "loading": "#990033",
        "risky": "#ffff00",
        "custom": "#ff6b6b"
    }
    
    def __init__(self, name: str, equation: str, color: str | None = None, opacity: float = 0.3, zone_type: str = "custom"):
        self.name = name
        self.equation = equation
        self.zone_type = zone_type
        self.opacity = opacity
        
        # Determine color based on zone type if not explicitly provided
        if color is None:
            self.color = self.ZONE_TYPE_COLORS.get(zone_type, self.ZONE_TYPE_COLORS["custom"])
        else:
            self.color = color
            
        self.compiled_expression = None
        self.is_valid = self._compile_equation()
        
    def _compile_equation(self) -> bool:
        """Compile the equation string into a usable expression"""
        try:
            # Replace logical operators with Python equivalents
            expr = self.equation.replace("&&", " and ").replace("||", " or ")
            expr = expr.replace(">=", " >= ").replace("<=", " <= ")
            expr = expr.replace(">", " > ").replace("<", " < ")
            expr = expr.replace("==", " == ").replace("!=", " != ")
            
            # Validate that only x, y, numbers, and operators are used
            allowed_pattern = r'^[xy\d\s\+\-\*\/\(\)\.\<\>=!&|]+$'
            if not re.match(allowed_pattern, expr.replace(" and ", "").replace(" or ", "")):
                return False
                
            self.compiled_expression = expr
            return True
        except:
            return False
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within this zone"""
        if not self.is_valid or self.compiled_expression is None:
            return False
        try:
            return eval(self.compiled_expression, {"__builtins__": {}}, {"x": x, "y": y})
        except:
            return False

class FieldConfiguration:
    """Manages field configuration including points, images, and zones"""
    def __init__(self):
        self.name = "New Field"
        self.points = []
        self.associated_images = []  # List of image paths
        self.zones = []
        self.metadata = {
            "created": "",
            "modified": "",
            "description": ""
        }
    
    def add_point(self, name: str, x: float, y: float, color: str = "#ff6b6b"):
        """Add a new point to the field"""
        point = {
            "name": name,
            "x": x,
            "y": y,
            "color": color
        }
        self.points.append(point)
    
    def remove_point(self, index: int):
        """Remove a point by index"""
        if 0 <= index < len(self.points):
            self.points.pop(index)
    
    def update_point(self, index: int, name: Optional[str] = None, x: Optional[float] = None, y: Optional[float] = None, color: Optional[str] = None):
        """Update a point's properties"""
        if 0 <= index < len(self.points):
            point = self.points[index]
            if name is not None:
                point["name"] = name
            if x is not None:
                point["x"] = x
            if y is not None:
                point["y"] = y
            if color is not None:
                point["color"] = color
    
    def add_zone(self, zone: Zone):
        """Add a zone to the field"""
        self.zones.append(zone)
    
    def remove_zone(self, index: int):
        """Remove a zone by index"""
        if 0 <= index < len(self.zones):
            self.zones.pop(index)
    
    def to_dict(self) -> dict:
        """Convert field configuration to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "points": self.points,
            "associated_images": self.associated_images,
            "zones": [
                {
                    "name": zone.name,
                    "equation": zone.equation,
                    "color": zone.color,
                    "opacity": zone.opacity,
                    "zone_type": zone.zone_type
                } for zone in self.zones
            ],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create field configuration from dictionary"""
        config = cls()
        config.name = data.get("name", "New Field")
        config.points = data.get("points", [])
        config.associated_images = data.get("associated_images", [])
        config.metadata = data.get("metadata", {})
        
        # Reconstruct zones
        for zone_data in data.get("zones", []):
            zone = Zone(
                zone_data["name"],
                zone_data["equation"],
                zone_data.get("color", None),  # Let Zone class determine color based on type
                zone_data.get("opacity", 0.3),
                zone_data.get("zone_type", "custom")
            )
            config.zones.append(zone)
        
        return config

class PointEditorWidget(QtWidgets.QWidget):
    """Widget for editing field points"""
    
    pointsChanged = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.field_config = FieldConfiguration()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Header
        header_label = QtWidgets.QLabel("Point Editor")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        layout.addWidget(header_label)
        
        # Point list
        self.point_list = QtWidgets.QListWidget()
        self.point_list.setMaximumHeight(200)
        self.point_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.point_list)
        
        # Point details
        details_group = QtWidgets.QGroupBox("Point Details")
        details_layout = QtWidgets.QFormLayout(details_group)
        
        self.name_edit = QtWidgets.QLineEdit()
        self.x_spin = QtWidgets.QDoubleSpinBox()
        self.x_spin.setRange(-200, 200)
        self.x_spin.setDecimals(2)
        self.y_spin = QtWidgets.QDoubleSpinBox()
        self.y_spin.setRange(-200, 200)
        self.y_spin.setDecimals(2)
        
        self.color_button = QtWidgets.QPushButton()
        self.color_button.setMaximumWidth(50)
        self.color_button.clicked.connect(self._choose_color)
        
        details_layout.addRow("Name:", self.name_edit)
        details_layout.addRow("X:", self.x_spin)
        details_layout.addRow("Y:", self.y_spin)
        details_layout.addRow("Color:", self.color_button)
        
        layout.addWidget(details_group)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.add_btn = QtWidgets.QPushButton("Add Point")
        self.add_btn.clicked.connect(self._add_point)
        
        self.update_btn = QtWidgets.QPushButton("Update")
        self.update_btn.clicked.connect(self._update_point)
        self.update_btn.setEnabled(False)
        
        self.delete_btn = QtWidgets.QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_point)
        self.delete_btn.setEnabled(False)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.update_btn)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
        
        # Connect change signals
        self.name_edit.textChanged.connect(self._enable_update)
        self.x_spin.valueChanged.connect(self._enable_update)
        self.y_spin.valueChanged.connect(self._enable_update)
        
        self._update_color_button("#ff6b6b")
    
    def _setup_point_list(self):
        """Refresh the point list display"""
        self.point_list.clear()
        for i, point in enumerate(self.field_config.points):
            item_text = f"{point['name']} ({point['x']:.1f}, {point['y']:.1f})"
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, i)
            self.point_list.addItem(item)
    
    def _on_selection_changed(self):
        """Handle point selection change"""
        current_item = self.point_list.currentItem()
        if current_item:
            index = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            point = self.field_config.points[index]
            
            self.name_edit.setText(point["name"])
            self.x_spin.setValue(point["x"])
            self.y_spin.setValue(point["y"])
            self._update_color_button(point["color"])
            
            self.update_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.update_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def _add_point(self):
        """Add a new point"""
        name = self.name_edit.text().strip()
        if not name:
            name = f"Point {len(self.field_config.points) + 1}"
        
        self.field_config.add_point(
            name,
            self.x_spin.value(),
            self.y_spin.value(),
            self.color_button.property("color")
        )
        
        self._setup_point_list()
        self.pointsChanged.emit()
        
        # Clear inputs
        self.name_edit.clear()
        self.x_spin.setValue(0)
        self.y_spin.setValue(0)
    
    def _update_point(self):
        """Update the selected point"""
        current_item = self.point_list.currentItem()
        if current_item:
            index = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            self.field_config.update_point(
                index,
                self.name_edit.text().strip(),
                self.x_spin.value(),
                self.y_spin.value(),
                self.color_button.property("color")
            )
            self._setup_point_list()
            self.pointsChanged.emit()
    
    def _delete_point(self):
        """Delete the selected point"""
        current_item = self.point_list.currentItem()
        if current_item:
            index = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            self.field_config.remove_point(index)
            self._setup_point_list()
            self.pointsChanged.emit()
            
            # Clear selection
            self.name_edit.clear()
            self.x_spin.setValue(0)
            self.y_spin.setValue(0)
    
    def _choose_color(self):
        """Open color picker dialog"""
        current_color = QtGui.QColor(self.color_button.property("color"))
        color = QtWidgets.QColorDialog.getColor(current_color, self, "Choose Point Color")
        if color.isValid():
            self._update_color_button(color.name())
    
    def _update_color_button(self, color: str):
        """Update the color button appearance"""
        self.color_button.setProperty("color", color)
        self.color_button.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
    
    def _enable_update(self):
        """Enable update button when changes are made"""
        if self.point_list.currentItem():
            self.update_btn.setEnabled(True)
    
    def set_field_config(self, config: FieldConfiguration):
        """Set the field configuration to edit"""
        self.field_config = config
        self._setup_point_list()
    
    def get_field_config(self) -> FieldConfiguration:
        """Get the current field configuration"""
        return self.field_config

class ImageAssociationWidget(QtWidgets.QWidget):
    """Widget for managing field image associations"""
    
    imagesChanged = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.field_config = FieldConfiguration()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Header
        header_label = QtWidgets.QLabel("Image Association")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        layout.addWidget(header_label)
        
        # Image list
        self.image_list = QtWidgets.QListWidget()
        self.image_list.setMaximumHeight(150)
        layout.addWidget(self.image_list)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.add_image_btn = QtWidgets.QPushButton("Add Image")
        self.add_image_btn.clicked.connect(self._add_image)
        
        self.remove_image_btn = QtWidgets.QPushButton("Remove")
        self.remove_image_btn.clicked.connect(self._remove_image)
        self.remove_image_btn.setEnabled(False)
        
        self.preview_btn = QtWidgets.QPushButton("Preview")
        self.preview_btn.clicked.connect(self._preview_image)
        self.preview_btn.setEnabled(False)
        
        button_layout.addWidget(self.add_image_btn)
        button_layout.addWidget(self.remove_image_btn)
        button_layout.addWidget(self.preview_btn)
        
        layout.addLayout(button_layout)
        
        # Image selection handler
        self.image_list.itemSelectionChanged.connect(self._on_image_selection_changed)
    
    def _setup_image_list(self):
        """Refresh the image list display"""
        self.image_list.clear()
        for image_path in self.field_config.associated_images:
            filename = os.path.basename(image_path)
            item = QtWidgets.QListWidgetItem(filename)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, image_path)
            item.setToolTip(image_path)
            self.image_list.addItem(item)
    
    def _on_image_selection_changed(self):
        """Handle image selection change"""
        has_selection = bool(self.image_list.currentItem())
        self.remove_image_btn.setEnabled(has_selection)
        self.preview_btn.setEnabled(has_selection)
    
    def _add_image(self):
        """Add a new image association"""
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFiles)
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                if file_path not in self.field_config.associated_images:
                    self.field_config.associated_images.append(file_path)
            
            self._setup_image_list()
            self.imagesChanged.emit()
    
    def _remove_image(self):
        """Remove selected image association"""
        current_item = self.image_list.currentItem()
        if current_item:
            image_path = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            if image_path in self.field_config.associated_images:
                self.field_config.associated_images.remove(image_path)
            
            self._setup_image_list()
            self.imagesChanged.emit()
    
    def _preview_image(self):
        """Preview selected image"""
        current_item = self.image_list.currentItem()
        if current_item:
            image_path = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            if os.path.exists(image_path):
                # Create simple preview dialog
                dialog = QtWidgets.QDialog(self)
                dialog.setWindowTitle(f"Preview: {os.path.basename(image_path)}")
                dialog.setModal(True)
                
                layout = QtWidgets.QVBoxLayout(dialog)
                
                # Image label
                pixmap = QtGui.QPixmap(image_path)
                if not pixmap.isNull():
                    # Scale image to fit preview
                    scaled_pixmap = pixmap.scaled(400, 400, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
                    image_label = QtWidgets.QLabel()
                    image_label.setPixmap(scaled_pixmap)
                    image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(image_label)
                
                # Close button
                close_btn = QtWidgets.QPushButton("Close")
                close_btn.clicked.connect(dialog.accept)
                layout.addWidget(close_btn)
                
                dialog.exec()
            else:
                QtWidgets.QMessageBox.warning(self, "Warning", f"Image file not found:\n{image_path}")
    
    def set_field_config(self, config: FieldConfiguration):
        """Set the field configuration to edit"""
        self.field_config = config
        self._setup_image_list()
    
    def get_field_config(self) -> FieldConfiguration:
        """Get the current field configuration"""
        return self.field_config

class ZoneEditorWidget(QtWidgets.QWidget):
    """Widget for creating and editing field zones with equations"""
    
    zonesChanged = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.field_config = FieldConfiguration()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Header
        header_label = QtWidgets.QLabel("Zone Editor")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        layout.addWidget(header_label)
        
        # Zone list
        self.zone_list = QtWidgets.QListWidget()
        self.zone_list.setMaximumHeight(150)
        self.zone_list.itemSelectionChanged.connect(self._on_zone_selection_changed)
        layout.addWidget(self.zone_list)
        
        # Zone details
        details_group = QtWidgets.QGroupBox("Zone Details")
        details_layout = QtWidgets.QFormLayout(details_group)
        
        self.zone_name_edit = QtWidgets.QLineEdit()
        self.equation_edit = QtWidgets.QLineEdit()
        self.equation_edit.setPlaceholderText("e.g., x >= 23 && y > 22")
        
        self.zone_color_button = QtWidgets.QPushButton()
        self.zone_color_button.setMaximumWidth(50)
        self.zone_color_button.clicked.connect(self._choose_zone_color)
        
        self.opacity_spin = QtWidgets.QDoubleSpinBox()
        self.opacity_spin.setRange(0.1, 1.0)
        self.opacity_spin.setSingleStep(0.1)
        self.opacity_spin.setValue(0.3)
        
        # Zone type dropdown
        self.zone_type_combo = QtWidgets.QComboBox()
        self.zone_type_combo.addItems([
            "custom", "red_alliance", "blue_alliance", "neutral", 
            "launch", "parking", "loading", "risky"
        ])
        self.zone_type_combo.setToolTip("Zone type determines automatic coloring")
        self.zone_type_combo.currentTextChanged.connect(self._on_zone_type_changed)
        
        details_layout.addRow("Name:", self.zone_name_edit)
        details_layout.addRow("Type:", self.zone_type_combo)
        details_layout.addRow("Equation:", self.equation_edit)
        details_layout.addRow("Color:", self.zone_color_button)
        details_layout.addRow("Opacity:", self.opacity_spin)
        
        layout.addWidget(details_group)
        
        # Equation help
        help_text = QtWidgets.QLabel(
            "🔧 Equation Help:\n"
            "• Use x and y for coordinates\n"
            "• Operators: >=, <=, >, <, ==, !=\n"
            "• Logic: && (and), || (or)\n"
            "• Parentheses: ( ) for grouping\n"
            "• Example: x >= 0 && x <= 50 && y > 20\n"
            "• Example: (x > -30 && x < 30) || y > 40"
        )
        help_text.setStyleSheet("color: #666; font-size: 10px; padding: 5px; background: #f8f9fa; border-radius: 3px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.add_zone_btn = QtWidgets.QPushButton("Add Zone")
        self.add_zone_btn.clicked.connect(self._add_zone)
        
        self.update_zone_btn = QtWidgets.QPushButton("Update")
        self.update_zone_btn.clicked.connect(self._update_zone)
        self.update_zone_btn.setEnabled(False)
        
        self.delete_zone_btn = QtWidgets.QPushButton("Delete")
        self.delete_zone_btn.clicked.connect(self._delete_zone)
        self.delete_zone_btn.setEnabled(False)
        
        self.test_zone_btn = QtWidgets.QPushButton("Test")
        self.test_zone_btn.clicked.connect(self._test_zone)
        
        button_layout.addWidget(self.add_zone_btn)
        button_layout.addWidget(self.update_zone_btn)
        button_layout.addWidget(self.delete_zone_btn)
        button_layout.addWidget(self.test_zone_btn)
        
        layout.addLayout(button_layout)
        
        # Set default zone type and color
        self.zone_type_combo.setCurrentText("custom")
        self._update_zone_color_button(Zone.ZONE_TYPE_COLORS["custom"])
    
    def _setup_zone_list(self):
        """Refresh the zone list display"""
        self.zone_list.clear()
        for i, zone in enumerate(self.field_config.zones):
            status = "✓" if zone.is_valid else "✗"
            item_text = f"{status} {zone.name}: {zone.equation}"
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, i)
            
            # Color code based on validity
            if zone.is_valid:
                item.setForeground(QtGui.QColor("#2c3e50"))
            else:
                item.setForeground(QtGui.QColor("#e74c3c"))
            
            self.zone_list.addItem(item)
    
    def _on_zone_selection_changed(self):
        """Handle zone selection change"""
        current_item = self.zone_list.currentItem()
        if current_item:
            index = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            zone = self.field_config.zones[index]
            
            self.zone_name_edit.setText(zone.name)
            self.zone_type_combo.setCurrentText(getattr(zone, 'zone_type', 'custom'))
            self.equation_edit.setText(zone.equation)
            self.opacity_spin.setValue(zone.opacity)
            self._update_zone_color_button(zone.color)
            
            self.update_zone_btn.setEnabled(True)
            self.delete_zone_btn.setEnabled(True)
        else:
            self.update_zone_btn.setEnabled(False)
            self.delete_zone_btn.setEnabled(False)
    
    def _add_zone(self):
        """Add a new zone"""
        name = self.zone_name_edit.text().strip()
        equation = self.equation_edit.text().strip()
        
        if not name:
            name = f"Zone {len(self.field_config.zones) + 1}"
        
        if not equation:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter an equation for the zone.")
            return
        
        zone = Zone(
            name,
            equation,
            self.zone_color_button.property("color"),
            self.opacity_spin.value(),
            self.zone_type_combo.currentText()
        )
        
        if not zone.is_valid:
            QtWidgets.QMessageBox.warning(
                self, "Invalid Equation", 
                f"The equation '{equation}' is not valid. Please check the syntax."
            )
            return
        
        self.field_config.add_zone(zone)
        self._setup_zone_list()
        self.zonesChanged.emit()
        
        # Clear inputs
        self.zone_name_edit.clear()
        self.equation_edit.clear()
    
    def _update_zone(self):
        """Update the selected zone"""
        current_item = self.zone_list.currentItem()
        if current_item:
            index = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            
            name = self.zone_name_edit.text().strip()
            equation = self.equation_edit.text().strip()
            
            if not equation:
                QtWidgets.QMessageBox.warning(self, "Warning", "Please enter an equation for the zone.")
                return
            
            zone = Zone(
                name,
                equation,
                self.zone_color_button.property("color"),
                self.opacity_spin.value(),
                self.zone_type_combo.currentText()
            )
            
            if not zone.is_valid:
                QtWidgets.QMessageBox.warning(
                    self, "Invalid Equation", 
                    f"The equation '{equation}' is not valid. Please check the syntax."
                )
                return
            
            self.field_config.zones[index] = zone
            self._setup_zone_list()
            self.zonesChanged.emit()
    
    def _delete_zone(self):
        """Delete the selected zone"""
        current_item = self.zone_list.currentItem()
        if current_item:
            index = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            self.field_config.remove_zone(index)
            self._setup_zone_list()
            self.zonesChanged.emit()
            
            # Clear inputs
            self.zone_name_edit.clear()
            self.equation_edit.clear()
    
    def _test_zone(self):
        """Test the current zone equation"""
        equation = self.equation_edit.text().strip()
        if not equation:
            QtWidgets.QMessageBox.information(self, "Test Zone", "Please enter an equation to test.")
            return
        
        test_zone = Zone("Test", equation)
        
        if not test_zone.is_valid:
            QtWidgets.QMessageBox.warning(
                self, "Invalid Equation", 
                f"The equation '{equation}' is not valid. Please check the syntax."
            )
            return
        
        # Test with some sample points
        test_points = [(0, 0), (25, 25), (-25, -25), (50, 0), (0, 50)]
        results = []
        
        for x, y in test_points:
            contains = test_zone.contains_point(x, y)
            results.append(f"({x}, {y}): {'✓' if contains else '✗'}")
        
        QtWidgets.QMessageBox.information(
            self, "Zone Test Results", 
            f"Equation: {equation}\n\nTest Points:\n" + "\n".join(results)
        )
    
    def _choose_zone_color(self):
        """Open color picker dialog for zone"""
        current_color = QtGui.QColor(self.zone_color_button.property("color"))
        color = QtWidgets.QColorDialog.getColor(current_color, self, "Choose Zone Color")
        if color.isValid():
            self._update_zone_color_button(color.name())
    
    def _update_zone_color_button(self, color: str):
        """Update the zone color button appearance"""
        self.zone_color_button.setProperty("color", color)
        self.zone_color_button.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
    
    def _on_zone_type_changed(self, zone_type: str):
        """Handle zone type change - update color automatically"""
        if zone_type in Zone.ZONE_TYPE_COLORS:
            auto_color = Zone.ZONE_TYPE_COLORS[zone_type]
            self._update_zone_color_button(auto_color)
    
    def set_field_config(self, config: FieldConfiguration):
        """Set the field configuration to edit"""
        self.field_config = config
        self._setup_zone_list()
    
    def get_field_config(self) -> FieldConfiguration:
        """Get the current field configuration"""
        return self.field_config

class FieldEditorPanel(QtWidgets.QWidget):
    """Main control panel for field editor mode"""
    
    configurationChanged = QtCore.Signal()
    imageChangeRequested = QtCore.Signal(str)  # Signal for image changes
    zoneVisibilityChanged = QtCore.Signal(bool)  # Signal for zone visibility changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_config = FieldConfiguration()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header with field name
        header_layout = QtWidgets.QHBoxLayout()
        
        header_label = QtWidgets.QLabel("Field Editor")
        header_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50;")
        
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Field name
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(QtWidgets.QLabel("Field Name:"))
        self.field_name_edit = QtWidgets.QLineEdit("New Field")
        self.field_name_edit.textChanged.connect(self._on_field_name_changed)
        name_layout.addWidget(self.field_name_edit)
        
        # Status indicator
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 10px;")
        name_layout.addWidget(self.status_label)
        
        layout.addLayout(name_layout)
        
        # Display controls
        display_group = QtWidgets.QGroupBox("Display Controls")
        display_layout = QtWidgets.QGridLayout(display_group)
        
        self.chk_editor_show_zones = QtWidgets.QCheckBox("Show zones")
        self.chk_editor_show_zones.setChecked(True)
        self.chk_editor_show_zones.setToolTip("Toggle visibility of field zones in editor")
        display_layout.addWidget(self.chk_editor_show_zones, 0, 0)
        
        layout.addWidget(display_group)
        
        # Quick Load section
        quick_load_group = QtWidgets.QGroupBox("📚 Quick Load Field Configs")
        quick_load_layout = QtWidgets.QVBoxLayout(quick_load_group)
        
        # Auto-discovered configs list
        self.config_list = QtWidgets.QListWidget()
        self.config_list.setMaximumHeight(120)
        self.config_list.itemDoubleClicked.connect(self._quick_load_config)
        self.config_list.itemSelectionChanged.connect(self._on_config_selection_changed)
        quick_load_layout.addWidget(self.config_list)
        
        # Quick load button
        quick_load_btn = QtWidgets.QPushButton("Load Selected Config")
        quick_load_btn.clicked.connect(self._quick_load_selected)
        quick_load_layout.addWidget(quick_load_btn)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_config_list)
        quick_load_layout.addWidget(refresh_btn)
        
        layout.addWidget(quick_load_group)
        
        # File operations
        file_group = QtWidgets.QGroupBox("File Operations")
        file_layout = QtWidgets.QVBoxLayout(file_group)
        
        file_button_layout = QtWidgets.QHBoxLayout()
        
        self.new_btn = QtWidgets.QPushButton("New")
        self.new_btn.clicked.connect(self._new_field)
        
        self.load_btn = QtWidgets.QPushButton("Load")
        self.load_btn.clicked.connect(self._load_field)
        
        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.clicked.connect(self._save_field)
        
        self.save_as_btn = QtWidgets.QPushButton("Save As")
        self.save_as_btn.clicked.connect(self._save_as_field)
        
        file_button_layout.addWidget(self.new_btn)
        file_button_layout.addWidget(self.load_btn)
        file_button_layout.addWidget(self.save_btn)
        file_button_layout.addWidget(self.save_as_btn)
        
        file_layout.addLayout(file_button_layout)
        layout.addWidget(file_group)
        
        # Create tab widget for different editors
        self.tab_widget = QtWidgets.QTabWidget()
        
        # Point editor tab
        self.point_editor = PointEditorWidget()
        self.point_editor.pointsChanged.connect(self._on_config_changed)
        self.tab_widget.addTab(self.point_editor, "📍 Points")
        
        # Image association tab
        self.image_editor = ImageAssociationWidget()
        self.image_editor.imagesChanged.connect(self._on_config_changed)
        self.tab_widget.addTab(self.image_editor, "🖼️ Images")
        
        # Zone editor tab
        self.zone_editor = ZoneEditorWidget()
        self.zone_editor.zonesChanged.connect(self._on_config_changed)
        self.tab_widget.addTab(self.zone_editor, "🎯 Zones")
        
        layout.addWidget(self.tab_widget)
        
        # Current file label
        self.current_file_label = QtWidgets.QLabel("Unsaved field configuration")
        self.current_file_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.current_file_label)
        
        layout.addStretch()
        
        self.current_file = None
        
        # Initialize the config list
        self._refresh_config_list()
        
        # Connect zone visibility control
        self.chk_editor_show_zones.toggled.connect(self.zoneVisibilityChanged.emit)
    
    def _on_field_name_changed(self):
        """Handle field name change"""
        self.current_config.name = self.field_name_edit.text()
        self._on_config_changed()
    
    def _on_config_changed(self):
        """Handle configuration changes"""
        # Sync all editors
        self.current_config = self.point_editor.get_field_config()
        self.image_editor.set_field_config(self.current_config)
        self.zone_editor.set_field_config(self.current_config)
        
        # Update status
        point_count = len(self.current_config.points)
        image_count = len(self.current_config.associated_images)
        zone_count = len(self.current_config.zones)
        
        status_text = f"✓ {point_count} points, {image_count} images, {zone_count} zones"
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 10px;")
        
        # Use a small delay to ensure all UI elements are updated before emitting
        QtCore.QTimer.singleShot(50, self.configurationChanged.emit)
    
    def _new_field(self):
        """Create a new field configuration"""
        self.current_config = FieldConfiguration()
        self.field_name_edit.setText("New Field")
        self.current_file = None
        
        # Update all editors
        self.point_editor.set_field_config(self.current_config)
        self.image_editor.set_field_config(self.current_config)
        self.zone_editor.set_field_config(self.current_config)
        
        self.current_file_label.setText("Unsaved field configuration")
        self.configurationChanged.emit()
    
    def _load_field(self):
        """Load a field configuration from file"""
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("Field Configuration (*.json)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.current_config = FieldConfiguration.from_dict(data)
                self.field_name_edit.setText(self.current_config.name)
                self.current_file = file_path
                
                # Update all editors
                self.point_editor.set_field_config(self.current_config)
                self.image_editor.set_field_config(self.current_config)
                self.zone_editor.set_field_config(self.current_config)
                
                self.current_file_label.setText(f"Loaded: {os.path.basename(file_path)}")
                self.configurationChanged.emit()
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Error Loading Field", 
                    f"Could not load field configuration:\n{str(e)}"
                )
    
    def _save_field(self):
        """Save the current field configuration"""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self._save_as_field()
    
    def _save_as_field(self):
        """Save the field configuration to a new file"""
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("Field Configuration (*.json)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.AnyFile)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setDefaultSuffix("json")
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self._save_to_file(file_path)
    
    def _save_to_file(self, file_path: str):
        """Save configuration to specified file"""
        try:
            # Update metadata
            import datetime
            now = datetime.datetime.now().isoformat()
            if not self.current_config.metadata.get("created"):
                self.current_config.metadata["created"] = now
            self.current_config.metadata["modified"] = now
            
            # Get updated config from editors
            self._on_config_changed()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_config.to_dict(), f, indent=2)
            
            self.current_file = file_path
            self.current_file_label.setText(f"Saved: {os.path.basename(file_path)}")
            
            QtWidgets.QMessageBox.information(
                self, "Success", 
                f"Field configuration saved to:\n{file_path}"
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error Saving Field", 
                f"Could not save field configuration:\n{str(e)}"
            )
    
    def get_field_configuration(self) -> FieldConfiguration:
        """Get the current field configuration"""
        return self.current_config
    
    def set_field_configuration(self, config: FieldConfiguration):
        """Set the field configuration"""
        self.current_config = config
        self.field_name_edit.setText(config.name)
        
        # Update all editors
        self.point_editor.set_field_config(config)
        self.image_editor.set_field_config(config)
        self.zone_editor.set_field_config(config)
        
        self.configurationChanged.emit()
    
    def _refresh_config_list(self):
        """Refresh the list of available field configurations"""
        self.config_list.clear()
        
        # Look for field configs in the Field Configs directory
        script_dir = os.path.dirname(__file__)
        configs_dir = os.path.join(script_dir, "Field Configs")
        
        if not os.path.exists(configs_dir):
            return
        
        try:
            for filename in os.listdir(configs_dir):
                if filename.endswith('.json'):
                    config_path = os.path.join(configs_dir, filename)
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Create list item with config name and file info
                        display_name = data.get('name', filename.replace('.json', ''))
                        description = data.get('metadata', {}).get('description', '')
                        
                        if description:
                            item_text = f"{display_name}\n   {description}"
                        else:
                            item_text = display_name
                        
                        item = QtWidgets.QListWidgetItem(item_text)
                        item.setData(QtCore.Qt.ItemDataRole.UserRole, config_path)
                        item.setToolTip(f"File: {filename}\nPath: {config_path}")
                        
                        # Color code by field type
                        if 'into-the-deep' in filename.lower():
                            item.setForeground(QtGui.QColor("#2ecc71"))  # Green for current season
                        elif 'decode' in filename.lower():
                            item.setForeground(QtGui.QColor("#3498db"))  # Blue for previous season
                        else:
                            item.setForeground(QtGui.QColor("#34495e"))  # Dark gray for custom
                        
                        self.config_list.addItem(item)
                        
                    except Exception as e:
                        print(f"Error reading config {filename}: {e}")
                        
        except Exception as e:
            print(f"Error scanning configs directory: {e}")
    
    def _quick_load_config(self, item):
        """Load config when item is double-clicked"""
        self._load_config_from_item(item)
    
    def _on_config_selection_changed(self):
        """Load config when selection changes (single click)"""
        current_item = self.config_list.currentItem()
        if current_item:
            # Capture the config path immediately to avoid Qt object deletion issues
            config_path = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            if config_path:
                # Add a small delay to prevent rapid firing during selection changes
                QtCore.QTimer.singleShot(100, lambda path=config_path: self._load_config_from_path(path))
    
    def _quick_load_selected(self):
        """Load the currently selected config"""
        current_item = self.config_list.currentItem()
        if current_item:
            self._load_config_from_item(current_item)
    
    def _load_config_from_item(self, item):
        """Load configuration from a list item"""
        config_path = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self._load_config_from_path(config_path)
    
    def _load_config_from_path(self, config_path):
        """Load configuration from a file path"""
        if not config_path or not os.path.exists(config_path):
            QtWidgets.QMessageBox.warning(
                self, "File Not Found", 
                f"Configuration file not found:\n{config_path}"
            )
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert relative image paths to absolute paths
            script_dir = os.path.dirname(__file__)
            if 'associated_images' in data:
                absolute_images = []
                for img_path in data['associated_images']:
                    if not os.path.isabs(img_path):
                        # Convert relative path to absolute
                        absolute_path = os.path.join(script_dir, img_path)
                        absolute_images.append(absolute_path)
                    else:
                        absolute_images.append(img_path)
                data['associated_images'] = absolute_images
            
            self.current_config = FieldConfiguration.from_dict(data)
            self.field_name_edit.setText(self.current_config.name)
            self.current_file = config_path
            
            # Update all editors first
            self.point_editor.set_field_config(self.current_config)
            self.image_editor.set_field_config(self.current_config)
            self.zone_editor.set_field_config(self.current_config)
            
            self.current_file_label.setText(f"Loaded: {os.path.basename(config_path)}")
            
            # Trigger image change if there are associated images
            if self.current_config.associated_images:
                primary_image = self.current_config.associated_images[0]
                if os.path.exists(primary_image):
                    self.imageChangeRequested.emit(primary_image)
                    # Wait for image to load before updating configuration
                    QtCore.QTimer.singleShot(300, self._delayed_config_update)
            else:
                # No image change needed, update configuration immediately
                self._delayed_config_update()
            
            QtWidgets.QMessageBox.information(
                self, "Config Loaded", 
                f"Successfully loaded field configuration:\n{self.current_config.name}"
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error Loading Config", 
                f"Could not load field configuration:\n{str(e)}"
            )
    
    def _delayed_config_update(self):
        """Delayed configuration update to ensure proper synchronization"""
        # Force configuration update after image has loaded
        self._on_config_changed()