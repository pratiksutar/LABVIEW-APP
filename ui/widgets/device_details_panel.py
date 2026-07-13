"""
Device Details Panel
A side panel showing detailed workstation and device information.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from domain.models.workstation       import Workstation
from domain.enums.workstation_status import WorkstationStatus
from ui.widgets.status_indicator     import StatusIndicator


def _row(label_text: str, value_text: str) -> QWidget:
    """Create a two-column info row."""
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 2, 0, 2)

    lbl = QLabel(label_text)
    lbl.setStyleSheet("color:#6B7280; font-size:12px;")
    lbl.setFixedWidth(110)

    val = QLabel(value_text)
    val.setStyleSheet("color:#E2E8F0; font-size:12px;")
    val.setWordWrap(True)

    layout.addWidget(lbl)
    layout.addWidget(val, 1)
    return widget


class DeviceDetailsPanel(QWidget):
    """Right-side details panel for the selected workstation."""

    close_requested      = Signal()
    turn_on_requested    = Signal(int)
    turn_off_requested   = Signal(int)
    maintenance_toggled  = Signal(int, bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setObjectName("detailsPanel")
        self.setStyleSheet(
            "QWidget#detailsPanel {"
            "  background-color: #16162A;"
            "  border-left: 1px solid #2D2D4A;"
            "}"
        )
        self._ws: Workstation | None = None
        self._build_ui()

    # ─── Build ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet("background:#0F0F1E; border-bottom:1px solid #2D2D4A;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)

        title = QLabel("Device Details")
        title.setStyleSheet("color:#A78BFA; font-size:14px; font-weight:600;")
        h_lay.addWidget(title)
        h_lay.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(
            "QPushButton { background:#2D2D4A; color:#94A3B8; border-radius:4px; "
            "font-size:14px; font-weight:bold; border:none; }"
            "QPushButton:hover { background:#3D3D5A; color:white; }"
        )
        close_btn.clicked.connect(self.close_requested)
        h_lay.addWidget(close_btn)
        root.addWidget(header)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(16, 16, 16, 16)
        self._content_layout.setSpacing(12)
        self._content_layout.addStretch()

        scroll.setWidget(self._content)
        root.addWidget(scroll)

    # ─── Load workstation ─────────────────────────────────────────
    def load(self, ws: Workstation, controls_allowed: bool = True) -> None:
        self._ws = ws
        self._controls_allowed = controls_allowed
        # Clear old content
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        idx = 0

        def insert(w: QWidget) -> None:
            nonlocal idx
            self._content_layout.insertWidget(idx, w)
            idx += 1

        # ── Status block ──
        status_widget = QWidget()
        st_lay = QHBoxLayout(status_widget)
        st_lay.setContentsMargins(0, 0, 0, 0)
        ind = StatusIndicator(ws.status)
        st_label = QLabel(ws.status.display_name)
        st_label.setStyleSheet(
            f"color:{ws.status.color}; font-size:16px; font-weight:600;"
        )
        st_lay.addWidget(ind)
        st_lay.addWidget(st_label)
        st_lay.addStretch()
        insert(status_widget)

        # ── Separator ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2D2D4A;")
        insert(sep)

        # ── Info rows ──
        insert(_row("Name",        ws.name))
        insert(_row("Area",        ws.area or "—"))
        insert(_row("Description", ws.description or "—"))

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color:#2D2D4A;")
        insert(sep2)

        insert(_row("Device ID",   ws.device_id or "Not assigned"))
        insert(_row("Power State", "ON" if ws.power_state else "OFF"))
        insert(_row("Consumption", f"{ws.power_consumption:.1f} W"))
        insert(_row("Voltage",     f"{ws.voltage:.1f} V" if ws.voltage else "—"))
        insert(_row("Maintenance", "Yes" if ws.is_maintenance else "No"))
        if ws.last_updated:
            insert(_row("Last Update", ws.last_updated.strftime("%H:%M:%S")))

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet("color:#2D2D4A;")
        insert(sep3)

        # ── Controls ──
        ctrl_label = QLabel("Controls")
        ctrl_label.setStyleSheet("color:#A78BFA; font-size:13px; font-weight:600;")
        insert(ctrl_label)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        btn_on = QPushButton("Turn ON")
        btn_on.setStyleSheet(
            "QPushButton { background:#059669; color:white; border-radius:6px; "
            "padding:8px; font-weight:500; }"
            "QPushButton:hover { background:#047857; }"
            "QPushButton:disabled { background:#374151; color:#6B7280; }"
        )
        btn_on.setEnabled(ws.is_controllable() and not ws.power_state and controls_allowed)
        btn_on.clicked.connect(lambda: self.turn_on_requested.emit(ws.id))

        btn_off = QPushButton("Turn OFF")
        btn_off.setStyleSheet(
            "QPushButton { background:#DC2626; color:white; border-radius:6px; "
            "padding:8px; font-weight:500; }"
            "QPushButton:hover { background:#B91C1C; }"
            "QPushButton:disabled { background:#374151; color:#6B7280; }"
        )
        btn_off.setEnabled(ws.is_controllable() and ws.power_state and controls_allowed)
        btn_off.clicked.connect(lambda: self.turn_off_requested.emit(ws.id))

        if not controls_allowed:
            tip = "Your account does not have permission to control devices."
            btn_on.setToolTip(tip)
            btn_off.setToolTip(tip)

        btn_layout.addWidget(btn_on)
        btn_layout.addWidget(btn_off)
        insert(btn_row)

        is_maint = ws.is_maintenance
        btn_maint = QPushButton(
            "Remove Maintenance" if is_maint else "Set Maintenance"
        )
        btn_maint.setStyleSheet(
            "QPushButton { background:#F97316; color:white; border-radius:6px; "
            "padding:8px; font-weight:500; }"
            "QPushButton:hover { background:#EA580C; }"
            "QPushButton:disabled { background:#374151; color:#6B7280; }"
        )
        btn_maint.setEnabled(controls_allowed)
        if not controls_allowed:
            btn_maint.setToolTip("Your account does not have permission to control devices.")
        btn_maint.clicked.connect(
            lambda: self.maintenance_toggled.emit(ws.id, not is_maint)
        )
        insert(btn_maint)
