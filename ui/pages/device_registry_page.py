"""
Device Registry Page
Manages workstation creation, editing, deletion, and device assignments.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QCheckBox, QDialogButtonBox,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui  import QColor

from application.services.workstation_service import WorkstationService
from application.services.auth_service        import AuthService
from domain.models.workstation                import Workstation
from domain.enums.workstation_status          import WorkstationStatus
from ui.dialogs.device_discovery_dialog       import DeviceDiscoveryDialog


# ─────────────────────────────────────────────────────────────────
#  Add / Edit Dialog
# ─────────────────────────────────────────────────────────────────
class WorkstationDialog(QDialog):
    def __init__(self, workstation: Workstation | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Workstation" if workstation is None else "Edit Workstation")
        self.setFixedWidth(440)
        self.setModal(True)
        self._ws = workstation
        self._build_ui()
        if workstation:
            self._populate(workstation)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel(self.windowTitle())
        title.setStyleSheet("font-size:16px; font-weight:bold; color:#E2E8F0;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Workstation A1")

        self._area_edit = QLineEdit()
        self._area_edit.setPlaceholderText("e.g. Lab Section B")

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Optional description")

        self._device_edit = QLineEdit()
        self._device_edit.setPlaceholderText("SwitchBot Device ID (optional)")

        device_row = QWidget()
        device_row_lay = QHBoxLayout(device_row)
        device_row_lay.setContentsMargins(0, 0, 0, 0)
        device_row_lay.setSpacing(8)
        device_row_lay.addWidget(self._device_edit, 1)

        discover_btn = QPushButton("🔍")
        discover_btn.setFixedWidth(36)
        discover_btn.setToolTip("Discover devices from your SwitchBot account")
        discover_btn.setStyleSheet(
            "QPushButton { background:#2D2D4A; color:#CBD5E1; padding:6px; }"
            "QPushButton:hover { background:#3D3D5A; }"
        )
        discover_btn.clicked.connect(self._open_device_discovery)
        device_row_lay.addWidget(discover_btn)

        self._maint_check = QCheckBox("Mark as Maintenance")

        for label, widget in [
            ("Name *",      self._name_edit),
            ("Area",        self._area_edit),
            ("Description", self._desc_edit),
            ("Device ID",   device_row),
            ("",            self._maint_check),
        ]:
            form.addRow(label, widget)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self, ws: Workstation) -> None:
        self._name_edit.setText(ws.name)
        self._area_edit.setText(ws.area)
        self._desc_edit.setText(ws.description)
        self._device_edit.setText(ws.device_id or "")
        self._maint_check.setChecked(ws.is_maintenance)

    def _open_device_discovery(self) -> None:
        dlg = DeviceDiscoveryDialog(parent=self)
        dlg.device_selected.connect(self._on_device_selected)
        dlg.exec()

    def _on_device_selected(self, device_id: str, device_name: str) -> None:
        self._device_edit.setText(device_id)
        if not self._name_edit.text().strip():
            self._name_edit.setText(device_name)

    def _accept(self) -> None:
        if not self._name_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Workstation name is required.")
            return
        self.accept()

    @property
    def name(self) -> str:        return self._name_edit.text().strip()
    @property
    def area(self) -> str:        return self._area_edit.text().strip()
    @property
    def description(self) -> str: return self._desc_edit.text().strip()
    @property
    def device_id(self) -> str:   return self._device_edit.text().strip()
    @property
    def is_maintenance(self) -> bool: return self._maint_check.isChecked()


# ─────────────────────────────────────────────────────────────────
#  Device Registry Page
# ─────────────────────────────────────────────────────────────────
class DeviceRegistryPage(QWidget):
    COLUMNS = ["#", "Name", "Area", "Device ID", "Status", "Actions"]

    def __init__(self, service: WorkstationService, auth_service: AuthService,
                 parent=None) -> None:
        super().__init__(parent)
        self._service      = service
        self._auth_service = auth_service
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(70)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(28, 0, 28, 0)

        title_col = QVBoxLayout()
        title = QLabel("Device Registry")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Manage workstations and device assignments")
        subtitle.setObjectName("pageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        h_lay.addLayout(title_col)
        h_lay.addStretch()

        can_edit = self._auth_service.can_edit_registry()
        add_btn = QPushButton("＋  Add Workstation")
        add_btn.setFixedWidth(160)
        add_btn.setEnabled(can_edit)
        if not can_edit:
            add_btn.setToolTip("Administrator access required to add workstations.")
        add_btn.clicked.connect(self._add_workstation)
        h_lay.addWidget(add_btn)
        root.addWidget(header)

        # ── Table ──
        body = QWidget()
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(28, 20, 28, 20)
        b_lay.setSpacing(12)

        self._table = QTableWidget()
        self._table.setColumnCount(len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 40)
        self._table.setColumnWidth(5, 160)

        b_lay.addWidget(self._table)
        root.addWidget(body)

    # ─── CRUD ────────────────────────────────────────────────────
    def refresh(self) -> None:
        workstations = self._service.get_all_workstations()
        self._table.setRowCount(len(workstations))

        for row, ws in enumerate(workstations):
            self._table.setRowHeight(row, 48)

            def _item(text: str, color: str | None = None) -> QTableWidgetItem:
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if color:
                    item.setForeground(QColor(color))
                return item

            self._table.setItem(row, 0, _item(str(ws.id or row + 1)))
            self._table.setItem(row, 1, _item(ws.name))
            self._table.setItem(row, 2, _item(ws.area or "—"))
            self._table.setItem(row, 3, _item(ws.device_id or "Not assigned", "#6B7280" if not ws.device_id else None))
            self._table.setItem(row, 4, _item(ws.status.display_name, ws.status.color))

            # Action buttons cell
            action_widget = QWidget()
            action_lay = QHBoxLayout(action_widget)
            action_lay.setContentsMargins(8, 4, 8, 4)
            action_lay.setSpacing(6)

            ws_id = ws.id
            can_edit = self._auth_service.can_edit_registry()

            edit_btn = QPushButton("✎ Edit")
            edit_btn.setFixedHeight(30)
            edit_btn.setFixedWidth(65)
            edit_btn.setStyleSheet(
                "QPushButton { background:#2D2D4A; color:#CBD5E1; border-radius:4px; "
                "font-size:11px; border:none; }"
                "QPushButton:hover { background:#3D3D5A; }"
                "QPushButton:disabled { background:#1A1A2E; color:#4B5563; }"
            )
            edit_btn.setEnabled(can_edit)
            if not can_edit:
                edit_btn.setToolTip("Administrator access required.")
            edit_btn.clicked.connect(lambda checked, wid=ws_id: self._edit_workstation(wid))

            del_btn = QPushButton("✕")
            del_btn.setFixedHeight(30)
            del_btn.setFixedWidth(35)
            del_btn.setStyleSheet(
                "QPushButton { background:#7F1D1D; color:#FCA5A5; border-radius:4px; "
                "font-size:11px; font-weight:bold; border:none; }"
                "QPushButton:hover { background:#DC2626; color:white; }"
                "QPushButton:disabled { background:#1A1A2E; color:#4B5563; }"
            )
            del_btn.setEnabled(can_edit)
            if not can_edit:
                del_btn.setToolTip("Administrator access required.")
            del_btn.clicked.connect(lambda checked, wid=ws_id: self._delete_workstation(wid))

            action_lay.addWidget(edit_btn)
            action_lay.addWidget(del_btn)
            action_lay.addStretch()
            self._table.setCellWidget(row, 5, action_widget)

    def _add_workstation(self) -> None:
        dlg = WorkstationDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                ws = self._service.create_workstation(
                    name=dlg.name,
                    description=dlg.description,
                    area=dlg.area,
                )
                if dlg.device_id:
                    self._service.assign_device(ws.id, dlg.device_id)
                if dlg.is_maintenance:
                    self._service.set_maintenance(ws.id, True)
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to create workstation:\n{exc}")

    def _edit_workstation(self, ws_id: int) -> None:
        ws = self._service.get_workstation(ws_id)
        if not ws:
            return
        dlg = WorkstationDialog(ws, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._service.update_workstation(
                    ws_id,
                    name=dlg.name,
                    description=dlg.description,
                    area=dlg.area,
                )
                if dlg.device_id:
                    self._service.assign_device(ws_id, dlg.device_id)
                self._service.set_maintenance(ws_id, dlg.is_maintenance)
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to update workstation:\n{exc}")

    def _delete_workstation(self, ws_id: int) -> None:
        ws = self._service.get_workstation(ws_id)
        if not ws:
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete workstation '{ws.name}'?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete_workstation(ws_id)
            self.refresh()
