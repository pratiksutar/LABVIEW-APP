"""
User Dialog
Add/Edit user dialog for Administrator use, plus a small password
reset dialog. Both used from the User Management page.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QFormLayout, QDialogButtonBox, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt

from domain.models.user      import User
from domain.enums.user_role  import UserRole

ROLE_OPTIONS = [UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMINISTRATOR]


class UserDialog(QDialog):
    """Add or edit a user account."""

    def __init__(self, user: Optional[User] = None, parent=None) -> None:
        super().__init__(parent)
        self._user = user
        self.setWindowTitle("Add User" if user is None else "Edit User")
        self.setFixedWidth(420)
        self.setModal(True)
        self._build_ui()
        if user:
            self._populate(user)

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

        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText("e.g. jsmith")
        if self._user is not None:
            self._username_edit.setEnabled(False)  # username is immutable after creation

        self._fullname_edit = QLineEdit()
        self._fullname_edit.setPlaceholderText("e.g. Jordan Smith")

        self._role_combo = QComboBox()
        for role in ROLE_OPTIONS:
            self._role_combo.addItem(role.display_name, role)

        form.addRow("Username *",  self._username_edit)
        form.addRow("Full Name",   self._fullname_edit)
        form.addRow("Role *",      self._role_combo)

        if self._user is None:
            self._password_edit = QLineEdit()
            self._password_edit.setPlaceholderText("Minimum 6 characters")
            self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)

            self._confirm_edit = QLineEdit()
            self._confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)

            form.addRow("Password *",         self._password_edit)
            form.addRow("Confirm Password *", self._confirm_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self, user: User) -> None:
        self._username_edit.setText(user.username)
        self._fullname_edit.setText(user.full_name)
        idx = self._role_combo.findData(user.role)
        if idx >= 0:
            self._role_combo.setCurrentIndex(idx)

    def _accept(self) -> None:
        if not self._username_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Username is required.")
            return
        if self._user is None:
            if len(self._password_edit.text()) < 6:
                QMessageBox.warning(self, "Validation", "Password must be at least 6 characters.")
                return
            if self._password_edit.text() != self._confirm_edit.text():
                QMessageBox.warning(self, "Validation", "Passwords do not match.")
                return
        self.accept()

    @property
    def username(self) -> str:
        return self._username_edit.text().strip()

    @property
    def full_name(self) -> str:
        return self._fullname_edit.text().strip()

    @property
    def role(self) -> UserRole:
        return self._role_combo.currentData()

    @property
    def password(self) -> str:
        return self._password_edit.text() if self._user is None else ""


class ResetPasswordDialog(QDialog):
    """Small dialog for setting a new password on an existing account."""

    def __init__(self, username: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Reset Password — {username}")
        self.setFixedWidth(360)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel(f"Reset Password")
        title.setStyleSheet("font-size:15px; font-weight:bold; color:#E2E8F0;")
        layout.addWidget(title)

        subtitle = QLabel(f"Set a new password for '{username}'.")
        subtitle.setStyleSheet("color:#9CA3AF; font-size:12px;")
        layout.addWidget(subtitle)

        self._password_edit = QLineEdit()
        self._password_edit.setPlaceholderText("New password (minimum 6 characters)")
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._password_edit)

        self._confirm_edit = QLineEdit()
        self._confirm_edit.setPlaceholderText("Confirm new password")
        self._confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._confirm_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept(self) -> None:
        if len(self._password_edit.text()) < 6:
            QMessageBox.warning(self, "Validation", "Password must be at least 6 characters.")
            return
        if self._password_edit.text() != self._confirm_edit.text():
            QMessageBox.warning(self, "Validation", "Passwords do not match.")
            return
        self.accept()

    @property
    def new_password(self) -> str:
        return self._password_edit.text()
