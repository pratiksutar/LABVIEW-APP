"""
Workstation Card Widget
Card-style widget displayed on the dashboard for each workstation.
"""
from __future__ import annotations

from typing import Optional, Callable
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore    import Qt, Signal
from PySide6.QtGui     import QColor

from domain.models.workstation       import Workstation
from domain.enums.workstation_status import WorkstationStatus
from ui.widgets.status_indicator     import StatusIndicator


class WorkstationCard(QFrame):
    """Dashboard card for a single workstation."""

    turn_on_requested  = Signal(int)  # workstation_id
    turn_off_requested = Signal(int)
    details_requested  = Signal(int)

    def __init__(self, workstation: Workstation, controls_allowed: bool = True,
                 parent=None) -> None:
        super().__init__(parent)
        self._ws = workstation
        self._controls_allowed = controls_allowed
        self.setObjectName("wsCard")
        self.setFixedWidth(240)
        self.setMinimumHeight(170)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()
        self.refresh(workstation)

    # ─── Build ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # ── Header row ──
        header = QHBoxLayout()
        header.setSpacing(8)

        self._indicator = StatusIndicator()
        header.addWidget(self._indicator)

        self._name_label = QLabel()
        self._name_label.setObjectName("wsName")
        self._name_label.setWordWrap(True)
        header.addWidget(self._name_label, 1)
        layout.addLayout(header)

        # ── Area ──
        self._area_label = QLabel()
        self._area_label.setObjectName("wsArea")
        layout.addWidget(self._area_label)

        # ── Status text ──
        self._status_label = QLabel()
        self._status_label.setObjectName("wsStatus")
        layout.addWidget(self._status_label)

        # ── Power ──
        self._power_label = QLabel()
        self._power_label.setObjectName("wsPower")
        layout.addWidget(self._power_label)

        layout.addStretch()

        # ── Control buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._btn_on = QPushButton("ON")
        self._btn_on.setObjectName("btnSuccess btnSmall")
        self._btn_on.setFixedHeight(28)
        self._btn_on.setStyleSheet(
            "QPushButton { background:#059669; color:white; border-radius:4px; "
            "font-size:11px; font-weight:600; padding:0 10px; }"
            "QPushButton:hover { background:#047857; }"
            "QPushButton:disabled { background:#374151; color:#6B7280; }"
        )
        self._btn_on.clicked.connect(lambda: self.turn_on_requested.emit(self._ws.id))

        self._btn_off = QPushButton("OFF")
        self._btn_off.setObjectName("btnDanger btnSmall")
        self._btn_off.setFixedHeight(28)
        self._btn_off.setStyleSheet(
            "QPushButton { background:#DC2626; color:white; border-radius:4px; "
            "font-size:11px; font-weight:600; padding:0 10px; }"
            "QPushButton:hover { background:#B91C1C; }"
            "QPushButton:disabled { background:#374151; color:#6B7280; }"
        )
        self._btn_off.clicked.connect(lambda: self.turn_off_requested.emit(self._ws.id))

        self._btn_details = QPushButton("Details")
        self._btn_details.setFixedHeight(28)
        self._btn_details.setStyleSheet(
            "QPushButton { background:#2D2D4A; color:#CBD5E1; border-radius:4px; "
            "font-size:11px; padding:0 10px; }"
            "QPushButton:hover { background:#3D3D5A; }"
        )
        self._btn_details.clicked.connect(lambda: self.details_requested.emit(self._ws.id))

        btn_row.addWidget(self._btn_on)
        btn_row.addWidget(self._btn_off)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_details)
        layout.addLayout(btn_row)

    # ─── Refresh ─────────────────────────────────────────────────
    def refresh(self, workstation: Workstation, controls_allowed: bool | None = None) -> None:
        self._ws = workstation
        if controls_allowed is not None:
            self._controls_allowed = controls_allowed
        self._name_label.setText(workstation.name)
        self._area_label.setText(f"📍 {workstation.area}" if workstation.area else "No area set")
        self._indicator.set_status(workstation.status)

        color = workstation.status.color
        self._status_label.setText(workstation.status.display_name)
        self._status_label.setStyleSheet(f"color: {color}; font-weight: 600;")

        if workstation.power_consumption > 0:
            self._power_label.setText(f"⚡ {workstation.power_consumption:.1f} W")
        else:
            self._power_label.setText("⚡ 0.0 W")

        controllable = workstation.is_controllable() and self._controls_allowed
        self._btn_on.setEnabled(controllable and not workstation.power_state)
        self._btn_off.setEnabled(controllable and workstation.power_state)
        if not self._controls_allowed:
            tip = "Your account does not have permission to control devices."
            self._btn_on.setToolTip(tip)
            self._btn_off.setToolTip(tip)
        else:
            self._btn_on.setToolTip("")
            self._btn_off.setToolTip("")

        # Border color reflects status
        self.setStyleSheet(
            f"QFrame#wsCard {{ background-color: #22223A; border: 1px solid #2D2D4A; "
            f"border-top: 3px solid {color}; border-radius: 12px; }}"
            f"QFrame#wsCard:hover {{ border-color: {color}; border-top: 3px solid {color}; }}"
        )
