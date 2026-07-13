"""
Main Window — v0.8.0-beta
Root application window with login gate, session monitor, sidebar
navigation, and all page/service wiring.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget,
    QStatusBar, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Slot
from loguru import logger

from application.services.workstation_service import WorkstationService
from application.services.layout_service       import LayoutService
from application.services.auth_service         import AuthService
from application.services.audit_service        import AuditService
from application.services.report_service       import ReportService
from infrastructure.security.credential_manager import CredentialManager
from services.polling_service                  import PollingService
from services.session_monitor                  import SessionMonitor
from config.settings                           import AppSettings

from ui.styles.theme                  import DARK_THEME
from ui.pages.dashboard_page          import DashboardPage
from ui.pages.device_registry_page    import DeviceRegistryPage
from ui.pages.layout_page             import LayoutPage
from ui.pages.reports_page            import ReportsPage
from ui.pages.audit_logs_page         import AuditLogsPage
from ui.pages.settings_page           import SettingsPage
from ui.pages.user_management_page    import UserManagementPage
from ui.dialogs.login_dialog          import LoginDialog

APP_VERSION       = "v0.8.0-beta"
SESSION_TIMEOUT_M = 30

# Page index constants
PAGE_DASHBOARD = 0
PAGE_REGISTRY  = 1
PAGE_LAYOUT    = 2
PAGE_REPORTS   = 3
PAGE_AUDIT     = 4
PAGE_SETTINGS  = 5
PAGE_USERS     = 6


class MainWindow(QMainWindow):
    """Primary application window — gated behind login."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"LabView  {APP_VERSION}")
        self.setMinimumSize(1280, 780)
        self.resize(1400, 860)

        # ── Services ──────────────────────────────────────────────
        self._auth_service   = AuthService()
        self._audit_service  = AuditService.instance()
        self._ws_service     = WorkstationService()
        self._ws_service.hydrate_cache_from_history()
        self._layout_service = LayoutService(self._ws_service)
        self._report_service = ReportService()
        self._settings       = AppSettings.instance()
        self._polling        = PollingService(self)

        # ── Session monitor ───────────────────────────────────────
        self._session_monitor = SessionMonitor(SESSION_TIMEOUT_M, self)
        self._session_monitor.session_expired.connect(self._on_session_expired)
        QApplication.instance().installEventFilter(self._session_monitor)

        self.setStyleSheet(DARK_THEME)
        self._build_ui()
        self._wire_polling()

        if not self._show_login():
            raise SystemExit(0)

        self._apply_session_user()
        self._start_polling_if_configured()

    # ─── Login gate ──────────────────────────────────────────────
    def _show_login(self) -> bool:
        dlg = LoginDialog(self._auth_service, parent=None)
        result = dlg.exec()
        return result == LoginDialog.DialogCode.Accepted and dlg.user is not None

    def _apply_session_user(self) -> None:
        user = self._auth_service.current_user()
        if user is None:
            return
        # Tell WorkstationService who is acting so audit records the right username
        self._ws_service.set_actor(user.username)
        self._update_user_indicator()
        self._update_nav_visibility()
        self._session_monitor.start()
        logger.info(f"[MainWindow] Session started: {user.username} ({user.role.display_name})")

    # ─── UI build ────────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        main_lay = QHBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        main_lay.addWidget(self._build_sidebar())
        main_lay.addWidget(self._build_content(), 1)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

        self._api_indicator = QLabel("● API")
        self._api_indicator.setStyleSheet("color:#6B7280; font-size:12px;")
        self._status_bar.addPermanentWidget(self._api_indicator)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Logo block
        logo_block = QWidget()
        logo_block.setFixedHeight(72)
        logo_block.setStyleSheet("background:#0F0F1E; border-bottom:1px solid #1E1E3A;")
        logo_lay = QVBoxLayout(logo_block)
        logo_lay.setContentsMargins(20, 12, 20, 12)
        logo_lay.setSpacing(2)
        app_title = QLabel("🔬 LabView")
        app_title.setObjectName("appTitle")
        version_lbl = QLabel(APP_VERSION)
        version_lbl.setObjectName("appVersion")
        logo_lay.addWidget(app_title)
        logo_lay.addWidget(version_lbl)
        lay.addWidget(logo_block)

        # Navigation items: (icon, label, page_index)
        nav_items = [
            ("📊", "Dashboard",       PAGE_DASHBOARD),
            ("🖥️",  "Device Registry", PAGE_REGISTRY),
            ("🗺️",  "Lab Layout",      PAGE_LAYOUT),
            ("📈",  "Reports",         PAGE_REPORTS),
            ("📋",  "Audit Logs",      PAGE_AUDIT),
            ("⚙️",  "Settings",        PAGE_SETTINGS),
            ("👤",  "Users",           PAGE_USERS),
        ]

        self._nav_buttons: list[QPushButton] = []
        nav_container = QWidget()
        nav_lay = QVBoxLayout(nav_container)
        nav_lay.setContentsMargins(8, 12, 8, 12)
        nav_lay.setSpacing(2)

        for icon, label, page_idx in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda checked, idx=page_idx: self._navigate(idx))
            nav_lay.addWidget(btn)
            self._nav_buttons.append(btn)

        nav_lay.addStretch()
        lay.addWidget(nav_container, 1)

        # Bottom: user info + logout
        bottom = QWidget()
        bottom.setStyleSheet("border-top:1px solid #1E1E3A;")
        bot_lay = QVBoxLayout(bottom)
        bot_lay.setContentsMargins(12, 8, 12, 8)
        bot_lay.setSpacing(4)

        self._user_label = QLabel("Not signed in")
        self._user_label.setStyleSheet("color:#9CA3AF; font-size:11px; font-weight:500;")
        self._role_label = QLabel("")
        self._role_label.setStyleSheet("color:#4B5563; font-size:10px;")
        self._poll_status = QLabel("Polling: Off")
        self._poll_status.setStyleSheet("color:#4B5563; font-size:11px;")

        logout_btn = QPushButton("↩  Sign Out")
        logout_btn.setFixedHeight(28)
        logout_btn.setStyleSheet(
            "QPushButton { background:#2D2D4A; color:#9CA3AF; border-radius:4px; "
            "font-size:11px; border:none; padding:0 8px; }"
            "QPushButton:hover { background:#3D3D5A; color:#E2E8F0; }"
        )
        logout_btn.clicked.connect(self._logout)

        bot_lay.addWidget(self._user_label)
        bot_lay.addWidget(self._role_label)
        bot_lay.addWidget(self._poll_status)
        bot_lay.addWidget(logout_btn)
        lay.addWidget(bottom)

        return sidebar

    def _build_content(self) -> QWidget:
        content = QWidget()
        content.setObjectName("contentArea")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._stack = QStackedWidget()
        self._create_pages()
        lay.addWidget(self._stack)
        self._navigate(PAGE_DASHBOARD)
        self._wire_page_signals()
        return content

    def _create_pages(self) -> None:
        # Clear existing pages first
        while self._stack.count():
            w = self._stack.widget(0)
            self._stack.removeWidget(w)
            w.deleteLater()

        self._dashboard_page = DashboardPage(self._ws_service, self._auth_service)
        self._registry_page  = DeviceRegistryPage(self._ws_service, self._auth_service)
        self._layout_page    = LayoutPage(self._layout_service, self._ws_service,
                                           self._auth_service)
        self._reports_page   = ReportsPage(self._report_service)
        self._audit_page     = AuditLogsPage(self._audit_service)
        self._settings_page  = SettingsPage(self._auth_service)
        self._users_page     = UserManagementPage(self._auth_service)

        for page in (self._dashboard_page, self._registry_page, self._layout_page,
                     self._reports_page,   self._audit_page,    self._settings_page,
                     self._users_page):
            self._stack.addWidget(page)

    def _wire_page_signals(self) -> None:
        self._dashboard_page.command_result.connect(self._on_command_result)
        self._settings_page.poll_interval_changed.connect(self._on_interval_changed)

    # ─── Navigation ──────────────────────────────────────────────
    def _navigate(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

        refresh_map = {
            PAGE_DASHBOARD: lambda: self._dashboard_page.refresh(),
            PAGE_REGISTRY:  lambda: self._registry_page.refresh(),
            PAGE_LAYOUT:    lambda: self._layout_page.refresh(),
            PAGE_REPORTS:   lambda: self._reports_page.refresh(),
            PAGE_AUDIT:     lambda: self._audit_page.refresh(),
            PAGE_USERS:     lambda: self._users_page.refresh(),
        }
        if index in refresh_map:
            refresh_map[index]()

    def _update_nav_visibility(self) -> None:
        can_users  = self._auth_service.can_manage_users()
        # Nav button index 6 = Users
        self._nav_buttons[PAGE_USERS].setVisible(can_users)

    # ─── Session ─────────────────────────────────────────────────
    def _logout(self) -> None:
        self._polling.stop()
        self._session_monitor.stop()
        self._auth_service.logout()
        if not self._show_login():
            self.close()
            return
        self._apply_session_user()
        self._create_pages()
        self._wire_page_signals()
        self._navigate(PAGE_DASHBOARD)
        self._start_polling_if_configured()

    @Slot()
    def _on_session_expired(self) -> None:
        logger.info("[MainWindow] Session expired due to inactivity")
        QMessageBox.information(self, "Session Expired",
                                "Your session has expired due to inactivity.\n"
                                "Please sign in again.")
        self._logout()

    # ─── Polling ─────────────────────────────────────────────────
    def _wire_polling(self) -> None:
        self._polling.status_updated.connect(self._on_status_updated)
        self._polling.device_offline.connect(self._on_device_offline)
        self._polling.poll_finished.connect(self._on_poll_finished)
        self._polling.api_health.connect(self._on_api_health)

    def _start_polling_if_configured(self) -> None:
        creds = CredentialManager.instance()
        if creds.has_credentials() and self._settings.auto_refresh:
            if not self._polling.isRunning():
                self._polling.start()
            self._poll_status.setText(f"Polling: {self._settings.poll_interval}s")
            self._poll_status.setStyleSheet("color:#10B981; font-size:11px;")

    @Slot(int, bool, float, float)
    def _on_status_updated(self, ws_id: int, power_state: bool,
                            watts: float, volts: float) -> None:
        self._ws_service.update_live_status(ws_id, power_state, watts, volts)
        ws = self._ws_service.get_workstation(ws_id)
        if ws:
            self._dashboard_page.update_workstation(ws)
            self._layout_page.update_pin_status(ws_id, ws.status.color)

    @Slot(int)
    def _on_device_offline(self, ws_id: int) -> None:
        self._ws_service.mark_offline(ws_id)
        ws = self._ws_service.get_workstation(ws_id)
        if ws:
            self._dashboard_page.update_workstation(ws)
            self._layout_page.update_pin_status(ws_id, ws.status.color)

    @Slot(int, int)
    def _on_poll_finished(self, success: int, fail: int) -> None:
        msg = f"Last poll: {success} ok" + (f", {fail} failed" if fail else "")
        self._status_bar.showMessage(msg, 8000)

    @Slot(bool)
    def _on_api_health(self, healthy: bool) -> None:
        color = "#10B981" if healthy else "#EF4444"
        self._api_indicator.setStyleSheet(f"color:{color}; font-size:12px;")

    @Slot(int)
    def _on_interval_changed(self, seconds: int) -> None:
        self._polling.update_interval(seconds)
        self._poll_status.setText(f"Polling: {seconds}s")

    @Slot(str, bool)
    def _on_command_result(self, message: str, success: bool) -> None:
        self._status_bar.showMessage(message, 6000)

    # ─── Helpers ─────────────────────────────────────────────────
    def _update_user_indicator(self) -> None:
        user = self._auth_service.current_user()
        if user:
            self._user_label.setText(f"👤  {user.display_label}")
            self._role_label.setText(user.role.display_name)
            self._role_label.setStyleSheet(
                f"color:{user.role.badge_color}; font-size:10px; font-weight:600;"
            )

    def closeEvent(self, event) -> None:
        logger.info("[MainWindow] Closing — stopping polling and session monitor")
        self._polling.stop()
        self._session_monitor.stop()
        event.accept()
