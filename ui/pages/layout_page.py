"""
Lab Layout Page
Interactive floor plan with drag-and-drop workstation pins.
Implements roadmap v0.6.0-beta.
"""
from __future__ import annotations

from typing import List, Optional
from loguru import logger

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QStackedWidget, QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QSizePolicy
)
from PySide6.QtCore import Qt

from application.services.layout_service          import LayoutService
from application.services.workstation_service      import WorkstationService
from application.services.auth_service             import AuthService
from ui.widgets.floor_plan_canvas                  import FloorPlanCanvas
from ui.dialogs.workstation_quick_view_dialog       import WorkstationQuickViewDialog
from services.switchbot_worker                      import SwitchBotWorker

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"


def _legend_row(color: str, label: str) -> QWidget:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 2, 0, 2)
    lay.setSpacing(8)

    dot = QLabel()
    dot.setFixedSize(10, 10)
    dot.setStyleSheet(f"background:{color}; border-radius:5px;")

    text = QLabel(label)
    text.setStyleSheet("color:#9CA3AF; font-size:11px;")

    lay.addWidget(dot)
    lay.addWidget(text)
    lay.addStretch()
    return row


class LayoutPage(QWidget):
    """Lab floor plan viewer and pin editor."""

    def __init__(self, layout_service: LayoutService,
                 workstation_service: WorkstationService,
                 auth_service: AuthService, parent=None) -> None:
        super().__init__(parent)
        self._layout_service      = layout_service
        self._workstation_service = workstation_service
        self._auth_service        = auth_service
        self._workers: List[SwitchBotWorker] = []
        self._build_ui()
        self.refresh()

    # ─── Build ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        self._body_stack = QStackedWidget()
        self._body_stack.addWidget(self._build_empty_state())   # index 0
        self._body_stack.addWidget(self._build_canvas_view())   # index 1
        root.addWidget(self._body_stack, 1)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(70)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(28, 0, 28, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Lab Layout")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Visual floor plan with live workstation status")
        subtitle.setObjectName("pageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        h_lay.addLayout(title_col)
        h_lay.addStretch()

        self._fit_btn = QPushButton("⤢  Fit View")
        self._fit_btn.setObjectName("btnSecondary")
        self._fit_btn.setFixedWidth(100)
        self._fit_btn.clicked.connect(lambda: self._canvas.fit_to_view())
        h_lay.addWidget(self._fit_btn)

        can_edit = self._auth_service.can_edit_layout_structure()

        self._clear_btn = QPushButton("🗑  Remove Image")
        self._clear_btn.setObjectName("btnSecondary")
        self._clear_btn.setFixedWidth(140)
        self._clear_btn.setEnabled(can_edit)
        if not can_edit:
            self._clear_btn.setToolTip("Administrator access required.")
        self._clear_btn.clicked.connect(self._clear_floor_plan)
        h_lay.addWidget(self._clear_btn)

        self._upload_btn = QPushButton("📂  Upload Floor Plan")
        self._upload_btn.setFixedWidth(170)
        self._upload_btn.setEnabled(can_edit)
        if not can_edit:
            self._upload_btn.setToolTip("Administrator access required.")
        self._upload_btn.clicked.connect(self._upload_floor_plan)
        h_lay.addWidget(self._upload_btn)

        return header

    def _build_empty_state(self) -> QWidget:
        body = QWidget()
        b_lay = QVBoxLayout(body)
        b_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b_lay.setSpacing(14)

        icon = QLabel("🗺️")
        icon.setStyleSheet("font-size:64px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("No Floor Plan Uploaded")
        title.setStyleSheet("font-size:20px; font-weight:bold; color:#E2E8F0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel(
            "Upload an image of your lab to start placing workstation pins.\n"
            "PNG, JPG, and BMP files are supported."
        )
        desc.setStyleSheet("color:#9CA3AF; font-size:13px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        upload_cta = QPushButton("📂  Upload Floor Plan")
        upload_cta.setFixedWidth(200)
        upload_cta.clicked.connect(self._upload_floor_plan)

        b_lay.addWidget(icon)
        b_lay.addWidget(title)
        b_lay.addWidget(desc)
        b_lay.addWidget(upload_cta, alignment=Qt.AlignmentFlag.AlignHCenter)
        return body

    def _build_canvas_view(self) -> QWidget:
        body = QWidget()
        lay = QHBoxLayout(body)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._canvas = FloorPlanCanvas()
        self._canvas.pin_moved.connect(self._on_pin_moved)
        self._canvas.pin_clicked.connect(self._on_pin_clicked)
        self._canvas.pin_remove_requested.connect(self._on_pin_remove_requested)
        lay.addWidget(self._canvas, 1)

        lay.addWidget(self._build_sidebar())
        return body

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet(
            "QFrame { background:#16162A; border-left:1px solid #2D2D4A; }"
        )
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        title = QLabel("Unplaced Workstations")
        title.setStyleSheet("color:#A78BFA; font-size:13px; font-weight:600;")
        lay.addWidget(title)

        hint = QLabel("Double-click to add to the map, then drag to position.")
        hint.setStyleSheet("color:#6B7280; font-size:11px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        self._unplaced_list = QListWidget()
        self._unplaced_list.setStyleSheet(
            "QListWidget { background:#1A1A2E; border:1px solid #2D2D4A; "
            "border-radius:6px; }"
            "QListWidget::item { padding:8px; border-radius:4px; }"
            "QListWidget::item:hover { background:#22223A; }"
        )
        self._unplaced_list.itemDoubleClicked.connect(self._on_add_to_canvas)
        lay.addWidget(self._unplaced_list, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2D2D4A;")
        lay.addWidget(sep)

        legend_title = QLabel("Status Legend")
        legend_title.setStyleSheet("color:#A78BFA; font-size:13px; font-weight:600;")
        lay.addWidget(legend_title)

        lay.addWidget(_legend_row("#10B981", "Available"))
        lay.addWidget(_legend_row("#F59E0B", "Idle"))
        lay.addWidget(_legend_row("#3B82F6", "In Use"))
        lay.addWidget(_legend_row("#F97316", "Maintenance"))
        lay.addWidget(_legend_row("#6B7280", "Disconnected"))
        lay.addWidget(_legend_row("#EF4444", "Failure"))

        zoom_hint = QLabel("Scroll to zoom • Drag empty space to pan")
        zoom_hint.setStyleSheet("color:#4B5563; font-size:10px;")
        zoom_hint.setWordWrap(True)
        lay.addWidget(zoom_hint)

        return sidebar

    # ─── Refresh ─────────────────────────────────────────────────
    def refresh(self) -> None:
        has_plan = self._layout_service.has_floor_plan()
        self._clear_btn.setEnabled(has_plan)
        self._fit_btn.setEnabled(has_plan)
        self._body_stack.setCurrentIndex(1 if has_plan else 0)

        if not has_plan:
            return

        path = self._layout_service.get_floor_plan_path()
        if not self._canvas.has_floor_plan():
            self._canvas.load_floor_plan(path)

        can_edit = self._auth_service.can_edit_layout_structure()
        pins = self._layout_service.get_placed_pins()
        canvas_pins = [{
            "workstation_id": p["workstation_id"],
            "name":           p["name"],
            "status_color":   p["status"].color,
            "x_relative":     p["x_relative"],
            "y_relative":     p["y_relative"],
        } for p in pins]
        self._canvas.set_pins(canvas_pins, editable=can_edit)
        self._refresh_unplaced_list(can_edit)

    def _refresh_unplaced_list(self, can_edit: bool = True) -> None:
        self._unplaced_list.clear()
        self._unplaced_list.setEnabled(can_edit)
        if not can_edit:
            tip = QListWidgetItem("🔒  Administrator access required to place pins")
            tip.setFlags(Qt.ItemFlag.NoItemFlags)
            tip.setForeground(__import__("PySide6.QtGui", fromlist=["QColor"]).QColor("#6B7280"))
            self._unplaced_list.addItem(tip)
            return
        unplaced = self._layout_service.get_unplaced_workstations()
        if not unplaced:
            placeholder = QListWidgetItem("✓  All workstations placed")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            self._unplaced_list.addItem(placeholder)
            return
        for ws in unplaced:
            item = QListWidgetItem(f"➕  {ws.name}")
            item.setData(Qt.ItemDataRole.UserRole, ws.id)
            self._unplaced_list.addItem(item)

    def update_pin_status(self, workstation_id: int, color: str) -> None:
        """Called by MainWindow on live poll updates while this page is visible."""
        if hasattr(self, "_canvas"):
            self._canvas.update_pin_status(workstation_id, color)

    # ─── Floor plan actions ─────────────────────────────────────
    def _upload_floor_plan(self) -> None:
        if not self._auth_service.can_edit_layout_structure():
            QMessageBox.warning(self, "Permission Denied",
                                "Administrator access required to upload a floor plan.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Lab Floor Plan Image", "", IMAGE_FILTER
        )
        if not path:
            return
        ok = self._layout_service.set_floor_plan(path)
        if not ok:
            QMessageBox.critical(self, "Upload Failed",
                                 "Could not load this image. Please try a different file.")
            return
        self._canvas.clear()
        self.refresh()

    def _clear_floor_plan(self) -> None:
        if not self._auth_service.can_edit_layout_structure():
            QMessageBox.warning(self, "Permission Denied",
                                "Administrator access required to remove the floor plan.")
            return
        reply = QMessageBox.question(
            self, "Remove Floor Plan",
            "Remove the floor plan image?\n\nWorkstation pin positions will be "
            "preserved and restored if you upload a plan again.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._layout_service.clear_floor_plan()
        self._canvas.clear()
        self.refresh()

    # ─── Pin actions ─────────────────────────────────────────────
    def _on_add_to_canvas(self, item: QListWidgetItem) -> None:
        if not self._auth_service.can_edit_layout_structure():
            return
        ws_id = item.data(Qt.ItemDataRole.UserRole)
        if ws_id is None:
            return
        ws = self._workstation_service.get_workstation(ws_id)
        if ws:
            self._canvas.add_pin_at_center(ws_id, ws.name, ws.status.color)
            self._refresh_unplaced_list(can_edit=True)

    def _on_pin_moved(self, ws_id: int, x_rel: float, y_rel: float) -> None:
        if not self._auth_service.can_edit_layout_structure():
            return
        self._layout_service.save_pin_position(ws_id, x_rel, y_rel)
        logger.debug(f"[Layout] Pin for ws #{ws_id} saved at ({x_rel:.2f}, {y_rel:.2f})")

    def _on_pin_remove_requested(self, ws_id: int) -> None:
        if not self._auth_service.can_edit_layout_structure():
            QMessageBox.warning(self, "Permission Denied",
                                "Administrator access required to remove pins.")
            return
        ws = self._workstation_service.get_workstation(ws_id)
        name = ws.name if ws else f"#{ws_id}"
        reply = QMessageBox.question(
            self, "Remove Pin",
            f"Remove '{name}' from the floor plan?\nIt will move back to the "
            "Unplaced Workstations list.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._layout_service.remove_pin(ws_id)
        self._canvas.remove_pin_item(ws_id)
        self._refresh_unplaced_list(can_edit=True)

    def _on_pin_clicked(self, ws_id: int) -> None:
        ws = self._workstation_service.get_workstation(ws_id)
        if not ws:
            return
        controls_allowed = self._auth_service.can_control_devices()
        dlg = WorkstationQuickViewDialog(self)
        dlg.panel.turn_on_requested.connect(lambda wid: self._send_command(wid, "on"))
        dlg.panel.turn_off_requested.connect(lambda wid: self._send_command(wid, "off"))
        dlg.panel.maintenance_toggled.connect(self._toggle_maintenance)
        dlg.load(ws, controls_allowed=controls_allowed)
        dlg.exec()

    # ─── Device control (mirrors DashboardPage) ──────────────────
    def _send_command(self, ws_id: int, action: str) -> None:
        if not self._auth_service.can_control_devices():
            QMessageBox.warning(self, "Permission Denied",
                                "Your account does not have permission to control devices.")
            return
        ws = self._workstation_service.get_workstation(ws_id)
        if not ws or not ws.device_id:
            QMessageBox.warning(self, "No Device Assigned",
                                "This workstation has no SwitchBot device assigned.")
            return

        worker = SwitchBotWorker(self)
        worker.command_finished.connect(self._on_command_finished)
        worker.command_failed.connect(self._on_command_failed)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._workers.append(worker)
        worker.send_command(ws_id, ws.device_id, action)

    def _on_command_finished(self, ws_id: int, action: str) -> None:
        self._workstation_service.set_power_state_optimistic(ws_id, action == "on")
        ws = self._workstation_service.get_workstation(ws_id)
        if ws:
            self.update_pin_status(ws_id, ws.status.color)

    def _on_command_failed(self, ws_id: int, action: str, error: str) -> None:
        QMessageBox.critical(self, "Command Failed", f"Could not send command:\n{error}")

    def _cleanup_worker(self, worker: SwitchBotWorker) -> None:
        if worker in self._workers:
            self._workers.remove(worker)
        worker.deleteLater()

    def _toggle_maintenance(self, ws_id: int, is_maintenance: bool) -> None:
        self._workstation_service.set_maintenance(ws_id, is_maintenance)
        ws = self._workstation_service.get_workstation(ws_id)
        if ws:
            self.update_pin_status(ws_id, ws.status.color)
