# ftc_field_viewer.py
# Interactive FTC field map viewer with grid and editable points.
# See usage instructions at the bottom.

from PySide6 import QtCore, QtGui, QtWidgets
import json
import os
import sys
import argparse

FIELD_SIZE_IN = 141.0
HALF_FIELD = FIELD_SIZE_IN / 2.0

DEFAULT_POINTS = [
    {"name": "Red Goal (ID 24)", "x": -58.3727, "y": 55.6425, "color": "#ff4d4d"},
    {"name": "Blue Goal (ID 20)", "x": -58.3727, "y": -55.6425, "color": "#4da6ff"},
]

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

    def __init__(self, scene, image_pixmap, *args, **kwargs):
        super().__init__(scene, *args, **kwargs)
        self.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        self.image_item = QtWidgets.QGraphicsPixmapItem(image_pixmap)
        self.scene().addItem(self.image_item)

        self.grid_spacing_in = 1  # inches per grid line
        self.grid_opacity = 0.5
        self.grid_pen = QtGui.QPen(QtGui.QColor(0, 188, 255, int(255*self.grid_opacity)), 0.0)
        self.major_grid_every = 6  # bold every N lines
        self.major_grid_pen = QtGui.QPen(QtGui.QColor(0, 188, 255, int(255*self.grid_opacity)), 0.0)
        self.major_grid_pen.setWidthF(1.2)

        self.points = list(DEFAULT_POINTS)  # list of dicts with name,x,y,color
        self.point_items = []               # QGraphicsEllipseItem + label
        self.selected_index = -1
        self.show_labels = True

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

    def scene_to_field(self, p: QtCore.QPointF):
        iw = self.image_rect.width()
        ih = self.image_rect.height()
        sx = p.x() - self.image_rect.left()
        sy = p.y() - self.image_rect.top()
        x_in = (sx * FIELD_SIZE_IN / iw) - HALF_FIELD
        y_in = HALF_FIELD - (sy * FIELD_SIZE_IN / ih)
        return x_in, y_in

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

    def _draw_grid(self):
        iw = self.image_rect.width()
        ih = self.image_rect.height()
        left = self.image_rect.left()
        top = self.image_rect.top()

        # number of grid lines across the 141 in field
        step_in = clamp(self.grid_spacing_in, 1, 24)
        num_lines = int(FIELD_SIZE_IN / step_in)

        # pixel step
        px_step_x = (iw / FIELD_SIZE_IN) * step_in
        px_step_y = (ih / FIELD_SIZE_IN) * step_in

        # Draw vertical lines
        for i in range(num_lines + 1):
            x = left + i * px_step_x
            line = QtCore.QLineF(x, top, x, top + ih)
            pen = self.major_grid_pen if (i % self.major_grid_every == 0) else self.grid_pen
            self.scene().addLine(line, pen)

        # Draw horizontal lines
        for i in range(num_lines + 1):
            y = top + i * px_step_y
            line = QtCore.QLineF(left, y, left + iw, y)
            pen = self.major_grid_pen if (i % self.major_grid_every == 0) else self.grid_pen
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
                                                QtGui.QPen(QtCore.Qt.NoPen),
                                                QtGui.QBrush(QtGui.QColor("#00ffd0")))
        origin_label = self.scene().addText("(0,0)")
        origin_label.setDefaultTextColor(QtGui.QColor("#8fbcd4"))
        origin_label.setPos(origin_scene + QtCore.QPointF(8, -18))

    def _draw_points(self):
        self.point_items.clear()
        for idx, p in enumerate(self.points):
            color = QtGui.QColor(p.get("color", "#ffd166"))
            pos = self.field_to_scene(p["x"], p["y"])
            r = 10.0 if idx == self.selected_index else 8.0
            pen = QtGui.QPen(QtGui.QColor("#000000"))
            pen.setWidthF(1.0)
            ellipse = self.scene().addEllipse(pos.x()-r/2, pos.y()-r/2, r, r, pen, QtGui.QBrush(color))
            ellipse.setZValue(5)
            ellipse.setData(0, idx)  # store index
            self.point_items.append(ellipse)

            if self.show_labels:
                label = self.scene().addText(p["name'])
                label.setDefaultTextColor(color.lighter(150))
                label.setPos(pos + QtCore.QPointF(10, -18))
                label.setZValue(5)
                self.point_items.append(label)

    # --- Interaction ---
    def wheelEvent(self, event: QtGui.QWheelEvent):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        zoom = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
        self.scale(zoom, zoom)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        scene_pos = self.mapToScene(event.position().toPoint())
        x_in, y_in = self.scene_to_field(scene_pos)
        self.cursorMoved.emit(x_in, y_in)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        scene_pos = self.mapToScene(event.position().toPoint())
        if event.button() == QtCore.Qt.LeftButton:
            # Check selection on points (nearest within radius)
            nearest_idx = -1
            nearest_dist2 = 12*12
            for item in self.scene().items(scene_pos):
                if isinstance(item, QtWidgets.QGraphicsEllipseItem):
                    idx = item.data(0)
                    if isinstance(idx, int):
                        center = item.rect().center() + item.pos()
                        d2 = (center.x()-scene_pos.x())**2 + (center.y()-scene_pos.y())**2
                        if d2 < nearest_dist2:
                            nearest_dist2 = d2
                            nearest_idx = idx
            if nearest_idx != -1:
                self.selected_index = nearest_idx
                self.pointSelected.emit(nearest_idx)
                self._rebuild_overlays()
        super().mousePressEvent(event)

    # --- Public API for controls ---
    def set_grid_spacing(self, inches: int):
        self.grid_spacing_in = clamp(int(inches), 1, 24)
        self._rebuild_overlays()

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
        gg.addWidget(QtWidgets.QLabel("Spacing (in):"), 0, 0)
        self.slider_spacing = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_spacing.setRange(1, 24)
        self.slider_spacing.setValue(1)
        gg.addWidget(self.slider_spacing, 0, 1)
        self.lbl_spacing_val = QtWidgets.QLabel("1")
        gg.addWidget(self.lbl_spacing_val, 0, 2)

        gg.addWidget(QtWidgets.QLabel("Opacity:"), 1, 0)
        self.slider_opacity = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_opacity.setRange(5, 100)
        self.slider_opacity.setValue(50)
        gg.addWidget(self.slider_opacity, 1, 1)
        self.lbl_opacity_val = QtWidgets.QLabel("0.50")
        gg.addWidget(self.lbl_opacity_val, 1, 2)

        self.chk_labels = QtWidgets.QCheckBox("Show point labels")
        self.chk_labels.setChecked(True)
        gg.addWidget(self.chk_labels, 2, 0, 1, 3)

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
        self.slider_spacing.valueChanged.connect(self._on_spacing_changed)
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

    def _on_spacing_changed(self, val):
        self.lbl_spacing_val.setText(str(val))
        self.view.set_grid_spacing(val)

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

        # Controls (dock on right)
        self.panel = ControlPanel(self.view)
        dock = QtWidgets.QDockWidget("Controls", self)
        dock.setWidget(self.panel)
        dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

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
        self.view.fitInView(self.view.image_rect, QtCore.Qt.KeepAspectRatio)

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
    parser.add_argument("--image", default="decode-custom-field-image.png",
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
