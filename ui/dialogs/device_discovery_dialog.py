"""
Device Discovery Dialog
Fetches the live list of registered SwitchBot devices and lets the
user pick one to assign to a workstation, instead of typing a
Device ID by hand.
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame
)
from PySide6.QtCore import Qt, Signal

from services.switchbot_worker import SwitchBotWorker


class DeviceDiscoveryDialog(QDialog):
    """Modal dialog that discovers and lists SwitchBot devices."""

    device_selected = Signal(str, str)  # device_id, device_name

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Discover SwitchBot Devices")
        self.setFixedSize(440, 480)
        self.setModal(True)

        self._worker: Optional[SwitchBotWorker] = None
        self._devices: List[Dict[str, Any]] = []

        self._build_ui()
        self._start_discovery()

    # ─── Build ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Discover SwitchBot Devices")
        title.setStyleSheet("font-size:16px; font-weight:bold; color:#E2E8F0;")
        layout.addWidget(title)

        self._status_label = QLabel("Connecting to SwitchBot Cloud API…")
        self._status_label.setStyleSheet("color:#9CA3AF; font-size:12px;")
        layout.addWidget(self._status_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2D2D4A;")
        layout.addWidget(sep)

        self._list = QListWidget()
        self._list.setStyleSheet(
            "QListWidget { background:#1A1A2E; border:1px solid #2D2D4A; "
            "border-radius:6px; padding:4px; }"
            "QListWidget::item { padding:10px 8px; border-radius:4px; }"
            "QListWidget::item:selected { background:#3D2D7A; color:#E2E8F0; }"
            "QListWidget::item:hover { background:#22223A; }"
        )
        self._list.itemDoubleClicked.connect(lambda _: self._select_current())
        layout.addWidget(self._list, 1)

        # Buttons
        btn_row = QHBoxLayout()
        self._refresh_btn = QPushButton("⟳  Refresh")
        self._refresh_btn.setStyleSheet(
            "QPushButton { background:#2D2D4A; color:#CBD5E1; }"
            "QPushButton:hover { background:#3D3D5A; }"
        )
        self._refresh_btn.clicked.connect(self._start_discovery)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            "QPushButton { background:#2D2D4A; color:#CBD5E1; }"
            "QPushButton:hover { background:#3D3D5A; }"
        )
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self._select_btn = QPushButton("Use Selected Device")
        self._select_btn.setEnabled(False)
        self._select_btn.clicked.connect(self._select_current)
        btn_row.addWidget(self._select_btn)

        layout.addLayout(btn_row)

        self._list.itemSelectionChanged.connect(
            lambda: self._select_btn.setEnabled(bool(self._list.selectedItems()))
        )

    # ─── Discovery ───────────────────────────────────────────────
    def _start_discovery(self) -> None:
        self._list.clear()
        self._devices = []
        self._select_btn.setEnabled(False)
        self._refresh_btn.setEnabled(False)
        self._status_label.setText("Connecting to SwitchBot Cloud API…")
        self._status_label.setStyleSheet("color:#9CA3AF; font-size:12px;")

        self._worker = SwitchBotWorker(self)
        self._worker.discovery_finished.connect(self._on_discovered)
        self._worker.discovery_failed.connect(self._on_failed)
        self._worker.finished.connect(lambda: self._refresh_btn.setEnabled(True))
        self._worker.discover_devices()

    def _on_discovered(self, devices: List[Dict[str, Any]]) -> None:
        self._devices = devices
        plug_minis = [
            d for d in devices
            if "plug" in str(d.get("deviceType", "")).lower()
        ]
        display_devices = plug_minis or devices  # fall back to all if no plugs found

        if not display_devices:
            self._status_label.setText("No devices found on this SwitchBot account.")
            self._status_label.setStyleSheet("color:#F59E0B; font-size:12px;")
            return

        self._status_label.setText(
            f"Found {len(display_devices)} device(s). Select one to assign:"
        )
        self._status_label.setStyleSheet("color:#10B981; font-size:12px;")

        for device in display_devices:
            name      = device.get("deviceName", "Unnamed Device")
            dev_id    = device.get("deviceId", "")
            dev_type  = device.get("deviceType", "Unknown")
            item = QListWidgetItem(f"🔌  {name}\n     {dev_type}  •  {dev_id}")
            item.setData(Qt.ItemDataRole.UserRole, (dev_id, name))
            self._list.addItem(item)

    def _on_failed(self, error: str) -> None:
        self._status_label.setText(f"❌  {error}")
        self._status_label.setStyleSheet("color:#EF4444; font-size:12px;")

    # ─── Selection ───────────────────────────────────────────────
    def _select_current(self) -> None:
        items = self._list.selectedItems()
        if not items:
            return
        device_id, device_name = items[0].data(Qt.ItemDataRole.UserRole)
        self.device_selected.emit(device_id, device_name)
        self.accept()
