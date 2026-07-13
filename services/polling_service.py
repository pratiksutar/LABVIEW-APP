"""
Polling Service
Background QThread that periodically polls SwitchBot devices
and emits signals with updated status data.
"""
from __future__ import annotations

from typing import List, Dict, Any
from loguru import logger

from PySide6.QtCore import QThread, QTimer, QObject, Signal

from database.repositories.device_mapping_repository import DeviceMappingRepository
from infrastructure.switchbot.switchbot_client        import SwitchBotClient, SwitchBotError
from infrastructure.security.credential_manager      import CredentialManager
from application.services.workstation_service        import WorkstationService
from config.settings                                  import AppSettings


class PollingWorker(QObject):
    """Runs inside a QThread; polls all mapped devices on a timer."""

    # Signals
    status_updated  = Signal(int, bool, float, float)  # ws_id, power_state, watts, volts
    device_offline  = Signal(int)                       # ws_id
    poll_started    = Signal()
    poll_finished   = Signal(int, int)                  # success_count, fail_count
    error_occurred  = Signal(str)
    api_health      = Signal(bool)                      # True = healthy

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timer      = QTimer(self)
        self._running    = False
        self._timer.timeout.connect(self._poll)
        self._settings   = AppSettings.instance()
        self._dm_repo    = DeviceMappingRepository()

    # ─── Control ─────────────────────────────────────────────────
    def start_polling(self) -> None:
        interval_ms = self._settings.poll_interval * 1000
        self._timer.start(interval_ms)
        self._running = True
        logger.info(f"[Polling] Started — interval {self._settings.poll_interval}s")
        self._poll()          # Poll immediately on start

    def stop_polling(self) -> None:
        self._timer.stop()
        self._running = False
        logger.info("[Polling] Stopped")

    def update_interval(self, seconds: int) -> None:
        was_active = self._timer.isActive()
        self._timer.stop()
        if was_active:
            self._timer.start(seconds * 1000)
        logger.info(f"[Polling] Interval updated to {seconds}s")

    # ─── Poll ────────────────────────────────────────────────────
    def _poll(self) -> None:
        creds = CredentialManager.instance()
        token  = creds.get_token()
        secret = creds.get_secret()

        if not token or not secret:
            logger.warning("[Polling] No credentials configured — skipping poll")
            self.api_health.emit(False)
            return

        client   = SwitchBotClient(token, secret)
        mappings = self._dm_repo.get_all()

        if not mappings:
            logger.debug("[Polling] No device mappings — nothing to poll")
            return

        self.poll_started.emit()
        success_count = 0
        fail_count    = 0

        for mapping in mappings:
            try:
                status = client.get_device_status(mapping.device_id)
                power_state = status.get("power", "off").lower() == "on"
                # Plug Mini returns electricity stats
                electricity = status.get("electricity", {})
                watts  = float(electricity.get("current", 0))
                volts  = float(electricity.get("voltage", 0))
                self.status_updated.emit(mapping.workstation_id, power_state, watts, volts)
                success_count += 1
            except SwitchBotError as exc:
                logger.warning(f"[Polling] Failed to poll device {mapping.device_id}: {exc}")
                self.device_offline.emit(mapping.workstation_id)
                fail_count += 1

        self.api_health.emit(fail_count == 0)
        self.poll_finished.emit(success_count, fail_count)
        logger.debug(f"[Polling] Done — {success_count} ok, {fail_count} failed")


class PollingService(QThread):
    """Thread wrapper that runs PollingWorker in the background."""

    # Re-expose worker signals
    status_updated = Signal(int, bool, float, float)
    device_offline = Signal(int)
    poll_started   = Signal()
    poll_finished  = Signal(int, int)
    error_occurred = Signal(str)
    api_health     = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._worker: PollingWorker | None = None

    def run(self) -> None:
        """Thread entry point — create worker, wire signals, start polling."""
        self._worker = PollingWorker()
        self._worker.status_updated.connect(self.status_updated)
        self._worker.device_offline.connect(self.device_offline)
        self._worker.poll_started.connect(self.poll_started)
        self._worker.poll_finished.connect(self.poll_finished)
        self._worker.error_occurred.connect(self.error_occurred)
        self._worker.api_health.connect(self.api_health)

        self._worker.start_polling()
        self.exec()   # Start Qt event loop (required for QTimer in thread)

    def stop(self) -> None:
        if self._worker:
            self._worker.stop_polling()
        self.quit()
        self.wait(2000)

    def update_interval(self, seconds: int) -> None:
        if self._worker:
            self._worker.update_interval(seconds)
