"""
Session Monitor
Watches for application-wide user activity (mouse/keyboard) and emits
session_expired after a period of inactivity, for auto-logout.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, QEvent, Signal
from loguru import logger

ACTIVITY_EVENTS = {
    QEvent.Type.MouseMove,
    QEvent.Type.MouseButtonPress,
    QEvent.Type.MouseButtonRelease,
    QEvent.Type.KeyPress,
    QEvent.Type.Wheel,
}


class SessionMonitor(QObject):
    """Installs as an application-wide event filter to detect idle time."""

    session_expired = Signal()

    def __init__(self, timeout_minutes: int, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.set_timeout(timeout_minutes)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)

    def set_timeout(self, timeout_minutes: int) -> None:
        self._timeout_ms = max(1, timeout_minutes) * 60 * 1000

    def start(self) -> None:
        self._timer.start(self._timeout_ms)

    def stop(self) -> None:
        self._timer.stop()

    def reset(self) -> None:
        if self._timeout_ms > 0:
            self._timer.start(self._timeout_ms)

    def _on_timeout(self) -> None:
        logger.info("[Session] Idle timeout reached — expiring session")
        self.session_expired.emit()

    # ─── QObject event filter ─────────────────────────────────────
    def eventFilter(self, watched, event) -> bool:
        if event.type() in ACTIVITY_EVENTS:
            self.reset()
        return False  # Never consume the event — just observe it
