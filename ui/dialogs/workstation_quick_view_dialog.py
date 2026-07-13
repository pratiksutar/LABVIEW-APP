"""
Workstation Quick View Dialog
A compact popup wrapping the existing DeviceDetailsPanel, opened by
double-clicking (or right-click → View Details on) a pin on the
Lab Layout floor plan.
"""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtCore     import Qt

from ui.widgets.device_details_panel import DeviceDetailsPanel
from domain.models.workstation       import Workstation


class WorkstationQuickViewDialog(QDialog):
    """Modal popup showing live workstation details from the floor plan."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Workstation Details")
        self.setFixedSize(320, 580)
        self.setModal(True)
        self.setStyleSheet("QDialog { background:#16162A; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.panel = DeviceDetailsPanel()
        self.panel.close_requested.connect(self.accept)
        layout.addWidget(self.panel)

    def load(self, workstation: Workstation, controls_allowed: bool = True) -> None:
        self.panel.load(workstation, controls_allowed)
