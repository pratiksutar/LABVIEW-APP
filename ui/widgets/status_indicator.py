"""
Status Indicator Widget
A small colored circle that represents the current workstation status.
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore    import Qt, QSize
from PySide6.QtGui     import QPainter, QColor, QPen, QBrush

from domain.enums.workstation_status import WorkstationStatus


class StatusIndicator(QWidget):
    """Colored circle indicator for workstation status."""

    SIZE = 14

    def __init__(self, status: WorkstationStatus = WorkstationStatus.DISCONNECTED,
                 parent=None) -> None:
        super().__init__(parent)
        self._status = status
        self.setFixedSize(self.SIZE + 4, self.SIZE + 4)
        self.setToolTip(status.display_name)

    def set_status(self, status: WorkstationStatus) -> None:
        self._status = status
        self.setToolTip(status.display_name)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(self._status.color)

        # Glow effect (outer ring)
        glow = QColor(color)
        glow.setAlpha(60)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(0, 0, self.SIZE + 4, self.SIZE + 4)

        # Main dot
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.lighter(130), 1))
        painter.drawEllipse(2, 2, self.SIZE, self.SIZE)

    def sizeHint(self) -> QSize:
        return QSize(self.SIZE + 4, self.SIZE + 4)
