"""
Settings Page
Configure SwitchBot API credentials, polling interval, and thresholds.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QFrame, QScrollArea, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from loguru import logger

from config.settings                             import AppSettings
from infrastructure.security.credential_manager import CredentialManager
from application.services.auth_service          import AuthService
from services.switchbot_worker                   import SwitchBotWorker


def _section(title: str) -> QLabel:
    lbl = QLabel(title)
    lbl.setObjectName("sectionTitle")
    lbl.setStyleSheet(
        "color:#A78BFA; font-size:14px; font-weight:600; "
        "padding-top:8px; border-bottom:1px solid #2D2D4A; padding-bottom:6px;"
    )
    return lbl


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("fieldLabel")
    lbl.setFixedWidth(180)
    return lbl


def _hint(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color:#4B5563; font-size:11px;")
    lbl.setWordWrap(True)
    return lbl


class SettingsPage(QWidget):
    """Application settings and credential management."""

    poll_interval_changed = Signal(int)  # emitted when interval is saved

    def __init__(self, auth_service: AuthService, parent=None) -> None:
        super().__init__(parent)
        self._settings = AppSettings.instance()
        self._creds    = CredentialManager.instance()
        self._auth_service = auth_service
        self._test_worker: SwitchBotWorker | None = None
        self._build_ui()
        self._load_values()

    # ─── Build ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Page header
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(70)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(28, 0, 28, 0)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title   = QLabel("Settings")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Configure API credentials and application preferences")
        subtitle.setObjectName("pageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        h_lay.addLayout(title_col)
        root.addWidget(header)

        # Scrollable body
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(28, 24, 28, 24)
        body_layout.setSpacing(16)
        body_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── SwitchBot Credentials ──
        body_layout.addWidget(_section("SwitchBot API Credentials"))
        body_layout.addWidget(_hint(
            "Obtain your API Token and Secret from the SwitchBot app: "
            "Profile → Preferences → App Version (tap 10×) → Developer Options."
        ))

        body_layout.addLayout(self._row("API Token", self._make_token_field()))
        body_layout.addLayout(self._row("API Secret", self._make_secret_field()))

        test_btn = QPushButton("🔌  Test Connection")
        test_btn.setFixedWidth(160)
        test_btn.clicked.connect(self._test_connection)
        body_layout.addWidget(test_btn)
        self._test_btn = test_btn

        # ── Polling ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2D2D4A; margin:8px 0;")
        body_layout.addWidget(sep)
        body_layout.addWidget(_section("Polling Configuration"))

        self._poll_spin = QSpinBox()
        self._poll_spin.setRange(5, 3600)
        self._poll_spin.setSuffix(" s")
        self._poll_spin.setFixedWidth(120)
        body_layout.addLayout(self._row("Poll Interval", self._poll_spin))
        body_layout.addWidget(_hint("How often to fetch live device status (5–3600 seconds)."))

        self._auto_refresh_check = QCheckBox("Enable auto-refresh on startup")
        body_layout.addWidget(self._auto_refresh_check)

        # ── Status Thresholds ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color:#2D2D4A; margin:8px 0;")
        body_layout.addWidget(sep2)
        body_layout.addWidget(_section("Status Thresholds (Watts)"))
        body_layout.addWidget(_hint(
            "Power usage thresholds for determining workstation status. "
            "Below Idle = Available, below In-Use = Idle, above = In Use."
        ))

        self._idle_spin = QDoubleSpinBox()
        self._idle_spin.setRange(0.1, 1000.0)
        self._idle_spin.setSuffix(" W")
        self._idle_spin.setDecimals(1)
        self._idle_spin.setFixedWidth(120)
        body_layout.addLayout(self._row("Idle Threshold", self._idle_spin))

        self._inuse_spin = QDoubleSpinBox()
        self._inuse_spin.setRange(1.0, 5000.0)
        self._inuse_spin.setSuffix(" W")
        self._inuse_spin.setDecimals(1)
        self._inuse_spin.setFixedWidth(120)
        body_layout.addLayout(self._row("In-Use Threshold", self._inuse_spin))

        # ── Battery Automation ──
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet("color:#2D2D4A; margin:8px 0;")
        body_layout.addWidget(sep3)
        body_layout.addWidget(_section("Battery Automation"))

        self._batt_low_spin = QSpinBox()
        self._batt_low_spin.setRange(1, 50)
        self._batt_low_spin.setSuffix(" %")
        self._batt_low_spin.setFixedWidth(120)
        body_layout.addLayout(self._row("Charge Below", self._batt_low_spin))

        self._batt_high_spin = QSpinBox()
        self._batt_high_spin.setRange(51, 100)
        self._batt_high_spin.setSuffix(" %")
        self._batt_high_spin.setFixedWidth(120)
        body_layout.addLayout(self._row("Stop Charging Above", self._batt_high_spin))

        # ── Save button ──
        sep4 = QFrame()
        sep4.setFrameShape(QFrame.Shape.HLine)
        sep4.setStyleSheet("color:#2D2D4A; margin:8px 0;")
        body_layout.addWidget(sep4)

        can_manage = self._auth_service.can_manage_settings()

        if not can_manage:
            notice = QLabel("🔒  Settings are read-only for your account role. "
                            "Administrator access is required to make changes.")
            notice.setStyleSheet(
                "color:#F59E0B; font-size:12px; background:#1E1A0A; "
                "border:1px solid #78350F; border-radius:6px; padding:8px 12px;"
            )
            notice.setWordWrap(True)
            body_layout.addWidget(notice)

        save_row = QHBoxLayout()
        self._save_btn = QPushButton("💾  Save Settings")
        self._save_btn.setFixedWidth(160)
        self._save_btn.setEnabled(can_manage)
        if not can_manage:
            self._save_btn.setToolTip("Administrator access required.")
        self._save_btn.clicked.connect(self._save)
        save_row.addWidget(self._save_btn)
        save_row.addStretch()
        body_layout.addLayout(save_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(body_widget)
        root.addWidget(scroll)

    def _row(self, label_text: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)
        row.addWidget(_field_label(label_text))
        row.addWidget(widget)
        row.addStretch()
        return row

    def _make_token_field(self) -> QLineEdit:
        self._token_edit = QLineEdit()
        self._token_edit.setPlaceholderText("Enter your SwitchBot API Token")
        self._token_edit.setMinimumWidth(380)
        self._token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        return self._token_edit

    def _make_secret_field(self) -> QLineEdit:
        self._secret_edit = QLineEdit()
        self._secret_edit.setPlaceholderText("Enter your SwitchBot API Secret")
        self._secret_edit.setMinimumWidth(380)
        self._secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        return self._secret_edit

    # ─── Load / Save ─────────────────────────────────────────────
    def _load_values(self) -> None:
        token  = self._creds.get_token()
        secret = self._creds.get_secret()
        if token:
            self._token_edit.setText(token)
        if secret:
            self._secret_edit.setText(secret)

        self._poll_spin.setValue(self._settings.poll_interval)
        self._auto_refresh_check.setChecked(self._settings.auto_refresh)
        self._idle_spin.setValue(self._settings.idle_threshold_watts)
        self._inuse_spin.setValue(self._settings.in_use_threshold_watts)
        self._batt_low_spin.setValue(self._settings.battery_threshold_low)
        self._batt_high_spin.setValue(self._settings.battery_threshold_high)

    def _save(self) -> None:
        if not self._auth_service.can_manage_settings():
            QMessageBox.warning(self, "Permission Denied",
                                "Administrator access is required to change settings.")
            return
        token  = self._token_edit.text().strip()
        secret = self._secret_edit.text().strip()

        if token:
            self._creds.save_token(token)
        if secret:
            self._creds.save_secret(secret)

        old_interval = self._settings.poll_interval
        new_interval = self._poll_spin.value()

        self._settings.poll_interval          = new_interval
        self._settings.auto_refresh           = self._auto_refresh_check.isChecked()
        self._settings.set("idle_threshold_watts",   self._idle_spin.value())
        self._settings.set("in_use_threshold_watts", self._inuse_spin.value())
        self._settings.battery_threshold_low  = self._batt_low_spin.value()
        self._settings.battery_threshold_high = self._batt_high_spin.value()

        if new_interval != old_interval:
            self.poll_interval_changed.emit(new_interval)

        logger.info("[Settings] Settings saved successfully.")
        QMessageBox.information(self, "Saved", "Settings saved successfully.")

    # ─── Test connection ─────────────────────────────────────────
    def _test_connection(self) -> None:
        token  = self._token_edit.text().strip()
        secret = self._secret_edit.text().strip()
        if not token or not secret:
            QMessageBox.warning(self, "Missing Credentials",
                                "Please enter both API Token and Secret before testing.")
            return

        self._test_btn.setEnabled(False)
        self._test_btn.setText("🔌  Testing…")

        self._test_worker = SwitchBotWorker(self)
        self._test_worker.connection_tested.connect(self._on_connection_tested)
        self._test_worker.finished.connect(self._on_test_worker_finished)
        self._test_worker.test_connection(token, secret)

    def _on_connection_tested(self, success: bool, message: str, device_count: int) -> None:
        if success:
            QMessageBox.information(
                self, "Connection Successful",
                f"✅ Connected to SwitchBot API.\n{device_count} device(s) found."
            )
        else:
            QMessageBox.critical(self, "Connection Failed",
                                 f"❌ Could not connect to SwitchBot API:\n{message}")

    def _on_test_worker_finished(self) -> None:
        self._test_btn.setEnabled(True)
        self._test_btn.setText("🔌  Test Connection")
