"""
Floor Plan Pin Item
A draggable, color-coded marker representing one workstation on the
lab floor plan canvas.
"""
from __future__ import annotations

from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem, QMenu
from PySide6.QtCore     import Qt, QRectF, QPointF, Signal
from PySide6.QtGui      import QPainter, QColor, QPen, QFont


class PinItem(QGraphicsObject):
    """Draggable status-colored pin on the floor plan."""

    RADIUS = 16

    moved            = Signal(int, float, float)  # workstation_id, x_rel, y_rel
    clicked          = Signal(int)                 # workstation_id
    remove_requested = Signal(int)                  # workstation_id

    def __init__(self, workstation_id: int, name: str, color: str,
                 editable: bool = True, parent=None) -> None:
        super().__init__(parent)
        self.workstation_id = workstation_id
        self.name  = name
        self.color = QColor(color)
        self.editable = editable

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, editable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.CursorShape.OpenHandCursor if editable
                        else Qt.CursorShape.PointingHandCursor)
        self.setZValue(10)
        self.setAcceptHoverEvents(True)
        self._hovered = False

    # ─── Qt overrides ────────────────────────────────────────────
    def boundingRect(self) -> QRectF:
        return QRectF(-65, -52, 130, 80)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = self.RADIUS

        # Glow ring
        glow = QColor(self.color)
        glow.setAlpha(90 if self._hovered else 60)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(0, 0), r + 6, r + 6)

        # Main circle
        painter.setBrush(self.color)
        pen_color = self.color.lighter(150) if self.isSelected() else self.color.lighter(130)
        painter.setPen(QPen(pen_color, 2))
        painter.drawEllipse(QPointF(0, 0), r, r)

        # Selection ring
        if self.isSelected():
            painter.setPen(QPen(QColor("#A78BFA"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(0, 0), r + 10, r + 10)

        # Label background
        label_rect = QRectF(-58, -48, 116, 18)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(15, 15, 30, 225))
        painter.drawRoundedRect(label_rect, 5, 5)

        # Label text
        font = QFont("Segoe UI", 8)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#E2E8F0"))
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self._elided_name())

    def _elided_name(self) -> str:
        return self.name if len(self.name) <= 16 else self.name[:14] + "…"

    # ─── Drag constraint ────────────────────────────────────────
    def itemChange(self, change, value):
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
                and self.scene() is not None):
            rect = self.scene().sceneRect()
            new_pos: QPointF = value
            x = min(max(new_pos.x(), rect.left()), rect.right())
            y = min(max(new_pos.y(), rect.top()), rect.bottom())
            return QPointF(x, y)
        return super().itemChange(change, value)

    # ─── Mouse interaction ──────────────────────────────────────
    def mousePressEvent(self, event) -> None:
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        self.setCursor(Qt.CursorShape.OpenHandCursor if self.editable
                        else Qt.CursorShape.PointingHandCursor)
        if not self.editable or event.button() != Qt.MouseButton.LeftButton or self.scene() is None:
            return
        rect = self.scene().sceneRect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        x_rel = (self.pos().x() - rect.left()) / rect.width()
        y_rel = (self.pos().y() - rect.top()) / rect.height()
        self.moved.emit(self.workstation_id, max(0.0, min(1.0, x_rel)),
                         max(0.0, min(1.0, y_rel)))

    def mouseDoubleClickEvent(self, event) -> None:
        self.clicked.emit(self.workstation_id)
        super().mouseDoubleClickEvent(event)

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { background:#22223A; color:#E2E8F0; border:1px solid #3D3D5A; }"
            "QMenu::item:selected { background:#3D2D7A; }"
        )
        view_action   = menu.addAction("View Details")
        remove_action = menu.addAction("Remove from Layout") if self.editable else None
        chosen = menu.exec(event.screenPos())
        if chosen == view_action:
            self.clicked.emit(self.workstation_id)
        elif remove_action is not None and chosen == remove_action:
            self.remove_requested.emit(self.workstation_id)

    # ─── External update ────────────────────────────────────────
    def set_color(self, color: str) -> None:
        self.color = QColor(color)
        self.update()

    def set_name(self, name: str) -> None:
        self.name = name
        self.update()
