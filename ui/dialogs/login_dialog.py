"""
Login Dialog
Shown before the main window. On first run (no users exist yet), this
dialog switches into "Create Administrator Account" mode instead of
showing a login form.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt

from application.services.auth_service import AuthService, AuthError, UsernameTakenError
from domain.models.user                import User


class LoginDialog(QDialog):
    """Login screen / first-run admin bootstrap screen."""

    def __init__(self, auth_service: AuthService, parent=None) -> None:
        super().__init__(parent)
        self._auth_service = auth_service
        self._user: Optional[User] = None
        self._is_first_run = not auth_service.has_any_users()

        self.setWindowTitle("LabView — Sign In")
        self.setFixedSize(380, 460 if self._is_first_run else 360)
        self.setModal(True)
        self.setStyleSheet(
            "QDialog { background:#1A1A2E; }"
            "QLineEdit { background:#16162A; color:#E2E8F0; border:1px solid #3D3D5A; "
            "border-radius:6px; padding:9px 12px; font-size:13px; }"
            "QLineEdit:focus { border-color:#7C3AED; }"
            "QPushButton { background:#7C3AED; color:white; border:none; border-radius:6px; "
            "padding:10px; font-weight:600; }"
            "QPushButton:hover { background:#6D28D9; }"
        )

        self._build_ui()

    # ─── Build ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(10)

        logo = QLabel("🔬 LabView")
        logo.setStyleSheet("font-size:22px; font-weight:bold; color:#A78BFA;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        if self._is_first_run:
            subtitle = QLabel("Welcome! Create your administrator account to get started.")
        else:
            subtitle = QLabel("Sign in to continue")
        subtitle.setStyleSheet("color:#9CA3AF; font-size:12px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color:#EF4444; font-size:12px;")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText("Username")
        layout.addWidget(self._username_edit)

        if self._is_first_run:
            self._fullname_edit = QLineEdit()
            self._fullname_edit.setPlaceholderText("Full Name")
            layout.addWidget(self._fullname_edit)

        self._password_edit = QLineEdit()
        self._password_edit.setPlaceholderText("Password")
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._password_edit)

        if self._is_first_run:
            self._confirm_edit = QLineEdit()
            self._confirm_edit.setPlaceholderText("Confirm Password")
            self._confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(self._confirm_edit)
            self._confirm_edit.returnPressed.connect(self._submit)
        else:
            self._password_edit.returnPressed.connect(self._submit)

        layout.addSpacing(6)

        submit_btn = QPushButton(
            "Create Administrator Account" if self._is_first_run else "Sign In"
        )
        submit_btn.clicked.connect(self._submit)
        layout.addWidget(submit_btn)

        if self._is_first_run:
            hint = QLabel(
                "This account will have full Administrator access. "
                "You can create additional Viewer/Operator accounts later "
                "from the Users page."
            )
            hint.setStyleSheet("color:#4B5563; font-size:10px;")
            hint.setWordWrap(True)
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(hint)

        layout.addStretch()
        self._username_edit.setFocus()

    # ─── Submit ──────────────────────────────────────────────────
    def _submit(self) -> None:
        if self._is_first_run:
            self._submit_bootstrap()
        else:
            self._submit_login()

    def _submit_login(self) -> None:
        username = self._username_edit.text().strip()
        password = self._password_edit.text()

        if not username or not password:
            self._show_error("Please enter both username and password.")
            return

        user = self._auth_service.login(username, password)
        if user is None:
            self._show_error("Invalid username or password, or the account is disabled.")
            self._password_edit.clear()
            self._password_edit.setFocus()
            return

        self._user = user
        self.accept()

    def _submit_bootstrap(self) -> None:
        username = self._username_edit.text().strip()
        full_name = self._fullname_edit.text().strip()
        password = self._password_edit.text()
        confirm = self._confirm_edit.text()

        if not username or not password:
            self._show_error("Username and password are required.")
            return
        if len(password) < 6:
            self._show_error("Password must be at least 6 characters.")
            return
        if password != confirm:
            self._show_error("Passwords do not match.")
            return

        try:
            user = self._auth_service.bootstrap_admin(username, full_name, password)
        except UsernameTakenError as exc:
            self._show_error(str(exc))
            return
        except AuthError as exc:
            self._show_error(str(exc))
            return

        self._user = user
        self.accept()

    def _show_error(self, message: str) -> None:
        self._error_label.setText(f"⚠  {message}")
        self._error_label.show()

    @property
    def user(self) -> Optional[User]:
        return self._user
