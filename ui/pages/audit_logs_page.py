"""
Audit Logs Page
Filterable, exportable view of the application audit log.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QDateTimeEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui  import QColor
from loguru import logger

from application.services.audit_service  import AuditService
from reports.report_generator            import ReportGenerator


CATEGORY_COLORS = {
    "Auth":     "#A78BFA",
    "Registry": "#3B82F6",
    "Control":  "#F59E0B",
    "Layout":   "#10B981",
    "Settings": "#F97316",
    "Users":    "#EC4899",
    "Other":    "#6B7280",
}


class AuditLogsPage(QWidget):
    """Paginated, filterable audit log viewer."""

    PAGE_SIZE = 100

    def __init__(self, audit_service: AuditService, parent=None) -> None:
        super().__init__(parent)
        self._audit_service = audit_service
        self._gen           = ReportGenerator()
        self._rows          = []
        self._build_ui()
        self.refresh()

    # ─── Build ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(70)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(28, 0, 28, 0)
        h_lay.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Audit Logs")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Full history of all user actions")
        subtitle.setObjectName("pageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        h_lay.addLayout(title_col)
        h_lay.addStretch()

        csv_btn = QPushButton("⬇  CSV")
        csv_btn.setFixedWidth(90)
        csv_btn.setObjectName("btnSecondary")
        csv_btn.clicked.connect(self._export_csv)
        h_lay.addWidget(csv_btn)

        xlsx_btn = QPushButton("⬇  Excel")
        xlsx_btn.setFixedWidth(100)
        xlsx_btn.setObjectName("btnSecondary")
        xlsx_btn.clicked.connect(self._export_xlsx)
        h_lay.addWidget(xlsx_btn)

        root.addWidget(header)

        # Filter bar
        filter_bar = QWidget()
        filter_bar.setStyleSheet("background:#16162A; border-bottom:1px solid #2D2D4A;")
        f_lay = QHBoxLayout(filter_bar)
        f_lay.setContentsMargins(28, 8, 28, 8)
        f_lay.setSpacing(12)

        f_lay.addWidget(QLabel("User:"))
        self._user_combo = QComboBox()
        self._user_combo.setFixedWidth(150)
        self._user_combo.addItem("All Users", None)
        f_lay.addWidget(self._user_combo)

        f_lay.addWidget(QLabel("Action:"))
        self._action_combo = QComboBox()
        self._action_combo.setFixedWidth(200)
        self._action_combo.addItem("All Actions", None)
        from domain.enums.audit_action import AuditAction
        for a in AuditAction:
            self._action_combo.addItem(a.display_name, a.value)
        f_lay.addWidget(self._action_combo)

        f_lay.addWidget(QLabel("From:"))
        self._from_dt = QDateTimeEdit()
        self._from_dt.setCalendarPopup(True)
        self._from_dt.setFixedWidth(160)
        self._from_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        self._from_dt.setDateTime(QDateTime.currentDateTime().addDays(-7))
        f_lay.addWidget(self._from_dt)

        f_lay.addWidget(QLabel("To:"))
        self._to_dt = QDateTimeEdit()
        self._to_dt.setCalendarPopup(True)
        self._to_dt.setFixedWidth(160)
        self._to_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        self._to_dt.setDateTime(QDateTime.currentDateTime())
        f_lay.addWidget(self._to_dt)

        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.refresh)
        f_lay.addWidget(apply_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(70)
        clear_btn.setObjectName("btnSecondary")
        clear_btn.clicked.connect(self._clear_filters)
        f_lay.addWidget(clear_btn)

        f_lay.addStretch()
        self._count_label = QLabel("")
        self._count_label.setStyleSheet("color:#6B7280; font-size:11px;")
        f_lay.addWidget(self._count_label)

        root.addWidget(filter_bar)

        # Table
        body = QWidget()
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(28, 16, 28, 16)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["Timestamp", "User", "Category", "Action", "Entity", "Old Value", "New Value"]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        b_lay.addWidget(self._table)
        root.addWidget(body, 1)

    # ─── Refresh ─────────────────────────────────────────────────
    def refresh(self) -> None:
        # Populate user filter
        current_user = self._user_combo.currentData()
        self._user_combo.clear()
        self._user_combo.addItem("All Users", None)
        for uname in self._audit_service.get_distinct_usernames():
            self._user_combo.addItem(uname, uname)
        if current_user:
            idx = self._user_combo.findData(current_user)
            if idx >= 0:
                self._user_combo.setCurrentIndex(idx)

        since  = self._from_dt.dateTime().toPython()
        until  = self._to_dt.dateTime().toPython()
        user   = self._user_combo.currentData()
        action = self._action_combo.currentData()

        self._rows = self._audit_service.get_recent(
            limit=self.PAGE_SIZE,
            username=user,
            action=action,
            since=since,
            until=until,
        )
        self._populate_table(self._rows)
        total = self._audit_service.total_count()
        self._count_label.setText(
            f"Showing {len(self._rows)} of {total} total entries"
        )

    def _populate_table(self, rows: list) -> None:
        self._table.setRowCount(len(rows))
        for row_idx, r in enumerate(rows):
            self._table.setRowHeight(row_idx, 36)

            ts_str = r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else ""
            try:
                from domain.enums.audit_action import AuditAction
                action_obj = AuditAction(r.action)
                cat   = action_obj.category
                label = action_obj.display_name
            except ValueError:
                cat   = "Other"
                label = r.action

            color = CATEGORY_COLORS.get(cat, "#6B7280")

            def _item(text: str, fg: str | None = None) -> QTableWidgetItem:
                item = QTableWidgetItem(str(text) if text else "")
                if fg:
                    item.setForeground(QColor(fg))
                return item

            self._table.setItem(row_idx, 0, _item(ts_str, "#9CA3AF"))
            self._table.setItem(row_idx, 1, _item(r.username, "#E2E8F0"))
            self._table.setItem(row_idx, 2, _item(cat, color))
            self._table.setItem(row_idx, 3, _item(label))
            self._table.setItem(row_idx, 4, _item(r.entity, "#CBD5E1"))
            self._table.setItem(row_idx, 5, _item(r.old_value or "", "#6B7280"))
            self._table.setItem(row_idx, 6, _item(r.new_value or "", "#10B981"))

    def _clear_filters(self) -> None:
        self._user_combo.setCurrentIndex(0)
        self._action_combo.setCurrentIndex(0)
        self._from_dt.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self._to_dt.setDateTime(QDateTime.currentDateTime())
        self.refresh()

    # ─── Export ──────────────────────────────────────────────────
    def _export_csv(self) -> None:
        if not self._rows:
            QMessageBox.information(self, "No Data", "No records to export.")
            return
        try:
            path = self._gen.export_audit_csv(self._rows)
            QMessageBox.information(self, "Export Complete",
                                    f"Audit log exported to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    def _export_xlsx(self) -> None:
        if not self._rows:
            QMessageBox.information(self, "No Data", "No records to export.")
            return
        try:
            path = self._gen.export_audit_xlsx(self._rows)
            QMessageBox.information(self, "Export Complete",
                                    f"Audit log exported to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))
