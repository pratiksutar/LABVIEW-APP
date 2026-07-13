"""
Floor Plan Canvas
QGraphicsView-based widget displaying the lab floor plan image with
draggable, color-coded workstation pins. Supports mouse-wheel zoom
and click-and-drag panning.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QFrame
from PySide6.QtCore     import Qt, QRectF, Signal
from PySide6.QtGui      import QPixmap, QPainter, QColor

from ui.widgets.floor_plan_pin import PinItem

MIN_ZOOM_STEPS = -8
MAX_ZOOM_STEPS = 14


class FloorPlanCanvas(QGraphicsView):
    """Interactive floor plan viewer with draggable status pins."""

    pin_moved            = Signal(int, float, float)  # workstation_id, x_rel, y_rel
    pin_clicked          = Signal(int)
    pin_remove_requested = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setBackgroundBrush(QColor("#0F0F1E"))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self._bg_item: Optional[object] = None
        self._pins: Dict[int, PinItem] = {}
        self._zoom_steps = 0

    # ─── Floor plan ──────────────────────────────────────────────
    def has_floor_plan(self) -> bool:
        return self._bg_item is not None

    def load_floor_plan(self, path: Path) -> bool:
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return False

        self._scene.clear()
        self._pins.clear()

        self._bg_item = self._scene.addPixmap(pixmap)
        self._bg_item.setZValue(0)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self.fit_to_view()
        return True

    def fit_to_view(self) -> None:
        if self._bg_item is not None:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self._zoom_steps = 0

    # ─── Pins ────────────────────────────────────────────────────
    def set_pins(self, pins: List[Dict[str, Any]], editable: bool = True) -> None:
        """
        pins: list of dicts with keys
              workstation_id, name, status_color, x_relative, y_relative
        """
        if self._bg_item is None:
            return

        existing_ids = set(self._pins.keys())
        new_ids      = {p["workstation_id"] for p in pins}

        for removed_id in existing_ids - new_ids:
            item = self._pins.pop(removed_id)
            self._scene.removeItem(item)

        rect = self._scene.sceneRect()
        for p in pins:
            wid   = p["workstation_id"]
            x     = rect.left() + p["x_relative"] * rect.width()
            y     = rect.top()  + p["y_relative"] * rect.height()

            if wid in self._pins:
                item = self._pins[wid]
                item.set_color(p["status_color"])
                item.set_name(p["name"])
                if item.editable != editable:
                    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, editable)
                    item.editable = editable
                if not item.isSelected():  # avoid fighting an active drag
                    item.setPos(x, y)
            else:
                item = PinItem(wid, p["name"], p["status_color"], editable=editable)
                item.moved.connect(self.pin_moved)
                item.clicked.connect(self.pin_clicked)
                item.remove_requested.connect(self.pin_remove_requested)
                item.setPos(x, y)
                self._scene.addItem(item)
                self._pins[wid] = item

    def add_pin_at_center(self, workstation_id: int, name: str, color: str) -> None:
        """Place a new pin in the middle of the floor plan and persist it."""
        if self._bg_item is None:
            return
        rect = self._scene.sceneRect()
        x_rel, y_rel = 0.5, 0.5
        x = rect.left() + x_rel * rect.width()
        y = rect.top()  + y_rel * rect.height()

        item = PinItem(workstation_id, name, color)
        item.moved.connect(self.pin_moved)
        item.clicked.connect(self.pin_clicked)
        item.remove_requested.connect(self.pin_remove_requested)
        item.setPos(x, y)
        self._scene.addItem(item)
        self._pins[workstation_id] = item
        self.pin_moved.emit(workstation_id, x_rel, y_rel)

    def update_pin_status(self, workstation_id: int, color: str) -> None:
        item = self._pins.get(workstation_id)
        if item:
            item.set_color(color)

    def remove_pin_item(self, workstation_id: int) -> None:
        item = self._pins.pop(workstation_id, None)
        if item:
            self._scene.removeItem(item)

    def clear(self) -> None:
        self._scene.clear()
        self._pins.clear()
        self._bg_item = None

    # ─── Zoom ────────────────────────────────────────────────────
    def wheelEvent(self, event) -> None:
        if self._bg_item is None:
            super().wheelEvent(event)
            return

        direction = 1 if event.angleDelta().y() > 0 else -1
        new_steps = self._zoom_steps + direction
        if new_steps < MIN_ZOOM_STEPS or new_steps > MAX_ZOOM_STEPS:
            return

        factor = 1.15 if direction > 0 else 1 / 1.15
        self.scale(factor, factor)
        self._zoom_steps = new_steps

    def zoom_in(self) -> None:
        if self._bg_item is not None and self._zoom_steps < MAX_ZOOM_STEPS:
            self.scale(1.15, 1.15)
            self._zoom_steps += 1

    def zoom_out(self) -> None:
        if self._bg_item is not None and self._zoom_steps > MIN_ZOOM_STEPS:
            self.scale(1 / 1.15, 1 / 1.15)
            self._zoom_steps -= 1
