"""
Dashboard Page
Main monitoring view with summary stats and workstation cards.
"""
from __future__ import annotations

from typing import Dict, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QGridLayout,
    QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from loguru import logger

from application.services.workstation_service import WorkstationService
from application.services.auth_service        import AuthService
from domain.models.workstation                import Workstation
from domain.enums.workstation_status          import WorkstationStatus
from ui.widgets.workstation_card              import WorkstationCard
from ui.widgets.device_details_panel         import DeviceDetailsPanel
from services.switchbot_worker                import SwitchBotWorker


def _summary_card(value: str, label: str, color: str) -> QFrame:
    """Create a colored summary stat card."""
    frame = QFrame()
    frame.setObjectName("summaryCard")
    frame.setFixedHeight(100)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 16, 20, 16)
    layout.setSpacing(4)

    val_lbl = QLabel(value)
    val_lbl.setObjectName("cardValue")
    val_lbl.setStyleSheet(f"font-size:32px; font-weight:bold; color:{color};")
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)

    lbl = QLabel(label)
    lbl.setObjectName("cardLabel")

    layout.addWidget(val_lbl)
    layout.addWidget(lbl)
    return frame


class DashboardPage(QWidget):
    """Real-time workstation monitoring dashboard."""

    command_result = Signal(str, bool)  # message, success — for status bar

    def __init__(self, service: WorkstationService, auth_service: AuthService,
                 parent=None) -> None:
        super().__init__(parent)
        self._service       = service
        self._auth_service  = auth_service
        self._cards: Dict[int, WorkstationCard] = {}
        self._workers: List[SwitchBotWorker] = []  # keep refs alive until finished
        self._build_ui()
        self.refresh()

    # ─── Build ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Page header ──
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(70)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(28, 0, 28, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Real-time workstation occupancy")
        subtitle.setObjectName("pageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        h_lay.addLayout(title_col)
        h_lay.addStretch()

        self._refresh_btn = QPushButton("⟳  Refresh")
        self._refresh_btn.setFixedWidth(110)
        self._refresh_btn.clicked.connect(self.refresh)
        h_lay.addWidget(self._refresh_btn)
        root.addWidget(header)

        # ── Main content ──
        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(0)

        # Left: scrollable content
        self._scroll_content = QWidget()
        content_layout = QVBoxLayout(self._scroll_content)
        content_layout.setContentsMargins(28, 20, 28, 20)
        content_layout.setSpacing(20)

        # Summary row
        self._summary_row = QHBoxLayout()
        self._summary_row.setSpacing(16)
        self._cards_placeholder: List[QFrame] = []

        self._total_card  = _summary_card("0", "Total",         "#E2E8F0")
        self._avail_card  = _summary_card("0", "Available",     "#10B981")
        self._inuse_card  = _summary_card("0", "In Use",        "#3B82F6")
        self._offline_card = _summary_card("0", "Offline",      "#6B7280")
        self._maint_card  = _summary_card("0", "Maintenance",   "#F97316")

        for card in (self._total_card, self._avail_card, self._inuse_card,
                     self._offline_card, self._maint_card):
            self._summary_row.addWidget(card)

        content_layout.addLayout(self._summary_row)

        # Workstation grid label
        grid_header = QLabel("Workstations")
        grid_header.setObjectName("sectionTitle")
        content_layout.addWidget(grid_header)

        # Workstation grid
        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(16)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(self._grid_widget)

        self._empty_label = QLabel(
            "No workstations configured.\nGo to Device Registry to add one."
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color:#4B5563; font-size:14px;")
        self._empty_label.hide()
        content_layout.addWidget(self._empty_label)
        content_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self._scroll_content)
        main_row.addWidget(scroll, 1)

        # Right: details panel (hidden by default)
        self._details_panel = DeviceDetailsPanel()
        self._details_panel.hide()
        self._details_panel.close_requested.connect(self._hide_details)
        self._details_panel.turn_on_requested.connect(self._turn_on)
        self._details_panel.turn_off_requested.connect(self._turn_off)
        self._details_panel.maintenance_toggled.connect(self._toggle_maintenance)
        main_row.addWidget(self._details_panel)

        root.addLayout(main_row)

    # ─── Refresh ─────────────────────────────────────────────────
    def refresh(self) -> None:
        workstations = self._service.get_all_workstations()
        summary      = self._service.get_summary()

        # Update summary cards
        self._get_card_value(self._total_card).setText(str(summary["total"]))
        self._get_card_value(self._avail_card).setText(str(summary["available"]))
        self._get_card_value(self._inuse_card).setText(str(summary["in_use"]))
        offline = summary["disconnected"] + summary["failure"]
        self._get_card_value(self._offline_card).setText(str(offline))
        self._get_card_value(self._maint_card).setText(str(summary["maintenance"]))

        if not workstations:
            self._empty_label.show()
            self._grid_widget.hide()
        else:
            self._empty_label.hide()
            self._grid_widget.show()
            self._rebuild_grid(workstations)

    def _rebuild_grid(self, workstations: List[Workstation]) -> None:
        # Remove old cards
        for card in self._cards.values():
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

        controls_allowed = self._auth_service.can_control_devices()
        col_count = 4
        for i, ws in enumerate(workstations):
            card = WorkstationCard(ws, controls_allowed=controls_allowed)
            card.turn_on_requested.connect(self._turn_on)
            card.turn_off_requested.connect(self._turn_off)
            card.details_requested.connect(self._show_details)
            self._grid_layout.addWidget(card, i // col_count, i % col_count)
            self._cards[ws.id] = card

    def update_workstation(self, ws: Workstation) -> None:
        """Called by polling service to update a single card."""
        if ws.id in self._cards:
            self._cards[ws.id].refresh(ws, controls_allowed=self._auth_service.can_control_devices())

    # ─── Details panel ───────────────────────────────────────────
    def _show_details(self, ws_id: int) -> None:
        ws = self._service.get_workstation(ws_id)
        if ws:
            self._details_panel.load(ws, controls_allowed=self._auth_service.can_control_devices())
            self._details_panel.show()

    def _hide_details(self) -> None:
        self._details_panel.hide()

    # ─── Device control ──────────────────────────────────────────
    def _turn_on(self, ws_id: int) -> None:
        self._send_command(ws_id, "on")

    def _turn_off(self, ws_id: int) -> None:
        self._send_command(ws_id, "off")

    def _send_command(self, ws_id: int, action: str) -> None:
        if not self._auth_service.can_control_devices():
            QMessageBox.warning(self, "Permission Denied",
                                "Your account does not have permission to control devices.")
            return

        ws = self._service.get_workstation(ws_id)
        if not ws or not ws.device_id:
            QMessageBox.warning(
                self, "No Device Assigned",
                "This workstation has no SwitchBot device assigned.\n"
                "Go to Device Registry to assign one."
            )
            return

        logger.info(f"[Dashboard] Sending '{action}' command to ws #{ws_id} ({ws.device_id})")

        worker = SwitchBotWorker(self)
        worker.command_finished.connect(self._on_command_finished)
        worker.command_failed.connect(self._on_command_failed)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.send_command(ws_id, ws.device_id, action)

    def _on_command_finished(self, ws_id: int, action: str) -> None:
        self._service.set_power_state_optimistic(ws_id, action == "on")
        ws = self._service.get_workstation(ws_id)
        if ws:
            self.update_workstation(ws)
            if self._details_panel.isVisible():
                self._details_panel.load(ws)
        verb = "ON" if action == "on" else "OFF"
        self.command_result.emit(f"Workstation turned {verb} successfully.", True)

    def _on_command_failed(self, ws_id: int, action: str, error: str) -> None:
        logger.error(f"[Dashboard] Command '{action}' failed for ws #{ws_id}: {error}")
        self.command_result.emit(f"Command failed: {error}", False)
        QMessageBox.critical(self, "Command Failed", f"Could not send command:\n{error}")

    def _cleanup_worker(self, worker: SwitchBotWorker) -> None:
        if worker in self._workers:
            self._workers.remove(worker)
        worker.deleteLater()

    def _toggle_maintenance(self, ws_id: int, is_maintenance: bool) -> None:
        if not self._auth_service.can_control_devices():
            QMessageBox.warning(self, "Permission Denied",
                                "Your account does not have permission to change maintenance status.")
            return
        self._service.set_maintenance(ws_id, is_maintenance)
        self.refresh()

    # ─── Helpers ─────────────────────────────────────────────────
    def _get_card_value(self, card: QFrame) -> QLabel:
        return card.findChild(QLabel, "cardValue") or card.findChildren(QLabel)[0]
