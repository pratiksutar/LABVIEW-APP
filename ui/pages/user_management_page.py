"""
User Management Page
Administrator-only page for creating, editing, disabling, and
resetting passwords for application user accounts.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui  import QColor

from application.services.auth_service import AuthService, AuthError, UsernameTakenError
from domain.models.user                import User
from ui.dialogs.user_dialog            import UserDialog, ResetPasswordDialog


class UserManagementPage(QWidget):
    """CRUD table for user accounts (Administrator only)."""

    COLUMNS = ["Username", "Full Name", "Role", "Status", "Last Login", "Actions"]

    def __init__(self, auth_service: AuthService, parent=None) -> None:
        super().__init__(parent)
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
        title_col.setSpacing(2)
        title = QLabel("Users")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Manage accounts, roles, and access")
        subtitle.setObjectName("pageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        h_lay.addLayout(title_col)
        h_lay.addStretch()

        add_btn = QPushButton("＋  Add User")
        add_btn.setFixedWidth(140)
        add_btn.clicked.connect(self._add_user)
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
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(5, 230)

        b_lay.addWidget(self._table)
        root.addWidget(body)

    # ─── Data ────────────────────────────────────────────────────
    def refresh(self) -> None:
        users = self._auth_service.list_users()
        self._table.setRowCount(len(users))
        current_id = (self._auth_service.current_user().id
                      if self._auth_service.current_user() else None)

        for row, user in enumerate(users):
            self._table.setRowHeight(row, 46)

            def _item(text: str, color: str | None = None) -> QTableWidgetItem:
                item = QTableWidgetItem(text)
                if color:
                    item.setForeground(QColor(color))
                return item

            username_text = user.username + ("  (you)" if user.id == current_id else "")
            self._table.setItem(row, 0, _item(username_text))
            self._table.setItem(row, 1, _item(user.full_name or "—"))
            self._table.setItem(row, 2, _item(user.role.display_name, user.role.badge_color))
            status_text  = "Active" if user.is_active else "Disabled"
            status_color = "#10B981" if user.is_active else "#EF4444"
            self._table.setItem(row, 3, _item(status_text, status_color))
            last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"
            self._table.setItem(row, 4, _item(last_login, "#6B7280" if not user.last_login else None))

            self._table.setCellWidget(row, 5, self._build_action_widget(user, is_self=user.id == current_id))

    def _build_action_widget(self, user: User, is_self: bool) -> QWidget:
        widget = QWidget()
        lay = QHBoxLayout(widget)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(6)

        def _small_btn(text: str, bg: str, hover: str, fg: str = "white") -> QPushButton:
            btn = QPushButton(text)
            btn.setFixedHeight(28)
            btn.setStyleSheet(
                f"QPushButton {{ background:{bg}; color:{fg}; border-radius:4px; "
                f"font-size:11px; border:none; padding:0 8px; }}"
                f"QPushButton:hover {{ background:{hover}; }}"
            )
            return btn

        edit_btn = _small_btn("✎ Edit", "#2D2D4A", "#3D3D5A", "#CBD5E1")
        edit_btn.clicked.connect(lambda checked, uid=user.id: self._edit_user(uid))
        lay.addWidget(edit_btn)

        reset_btn = _small_btn("🔑 Reset", "#2D2D4A", "#3D3D5A", "#CBD5E1")
        reset_btn.clicked.connect(lambda checked, uid=user.id, uname=user.username:
                                   self._reset_password(uid, uname))
        lay.addWidget(reset_btn)

        if user.is_active:
            toggle_btn = _small_btn("Disable", "#7F1D1D", "#DC2626", "#FCA5A5")
        else:
            toggle_btn = _small_btn("Enable", "#064E3B", "#059669", "#6EE7B7")
        toggle_btn.setEnabled(not is_self)
        if is_self:
            toggle_btn.setToolTip("You cannot disable your own account.")
        toggle_btn.clicked.connect(
            lambda checked, uid=user.id, active=user.is_active: self._toggle_active(uid, not active)
        )
        lay.addWidget(toggle_btn)
        lay.addStretch()
        return widget

    # ─── Actions ─────────────────────────────────────────────────
    def _add_user(self) -> None:
        dlg = UserDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._auth_service.create_user(
                    username=dlg.username,
                    full_name=dlg.full_name,
                    password=dlg.password,
                    role=dlg.role,
                )
                self.refresh()
            except UsernameTakenError as exc:
                QMessageBox.warning(self, "Username Taken", str(exc))
            except AuthError as exc:
                QMessageBox.warning(self, "Could Not Create User", str(exc))

    def _edit_user(self, user_id: int) -> None:
        user = next((u for u in self._auth_service.list_users() if u.id == user_id), None)
        if not user:
            return
        dlg = UserDialog(user, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._auth_service.update_user(user_id, full_name=dlg.full_name, role=dlg.role)
            self.refresh()

    def _reset_password(self, user_id: int, username: str) -> None:
        dlg = ResetPasswordDialog(username, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._auth_service.reset_password(user_id, dlg.new_password)
                QMessageBox.information(self, "Password Reset",
                                        f"Password for '{username}' has been updated.")
            except AuthError as exc:
                QMessageBox.warning(self, "Could Not Reset Password", str(exc))

    def _toggle_active(self, user_id: int, new_active: bool) -> None:
        action = "enable" if new_active else "disable"
        reply = QMessageBox.question(
            self, f"Confirm {action.title()}",
            f"Are you sure you want to {action} this account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self._auth_service.set_active(user_id, new_active)
            self.refresh()
        except AuthError as exc:
            QMessageBox.warning(self, "Action Not Allowed", str(exc))
