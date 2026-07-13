"""
SwitchBot Worker
A short-lived QThread that runs a single SwitchBot API operation
(device discovery, command send, or connection test) off the UI thread.

A fresh instance is created per operation rather than reused, since
each call is quick and independent. Callers must keep a reference to
the instance alive until its 'finished' signal fires (Qt requirement).
"""
from __future__ import annotations

from typing import Optional, Literal
from PySide6.QtCore import QThread, Signal
from loguru import logger

from infrastructure.switchbot.switchbot_client   import SwitchBotClient, SwitchBotError
from infrastructure.security.credential_manager import CredentialManager

OperationType = Literal["discover", "command", "test"]


class SwitchBotWorker(QThread):
    """Runs one SwitchBot API call in the background."""

    # Device discovery
    discovery_finished = Signal(list)   # list[dict] of device info
    discovery_failed    = Signal(str)

    # Device command (turn on/off)
    command_finished = Signal(int, str)        # workstation_id, action ("on"/"off")
    command_failed    = Signal(int, str, str)   # workstation_id, action, error message

    # Credential / connection test
    connection_tested = Signal(bool, str, int)  # success, message, device_count

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._op: Optional[tuple] = None

    # ─── Task setup (call one, then .start()) ─────────────────────
    def discover_devices(self) -> None:
        self._op = ("discover",)
        self.start()

    def send_command(self, workstation_id: int, device_id: str, action: str) -> None:
        """action must be 'on' or 'off'."""
        self._op = ("command", workstation_id, device_id, action)
        self.start()

    def test_connection(self, token: str, secret: str) -> None:
        self._op = ("test", token, secret)
        self.start()

    # ─── Thread entry point ────────────────────────────────────────
    def run(self) -> None:
        if self._op is None:
            return
        kind = self._op[0]

        if kind == "discover":
            self._run_discover()
        elif kind == "command":
            self._run_command()
        elif kind == "test":
            self._run_test()

    # ─── Implementations ────────────────────────────────────────────
    def _run_discover(self) -> None:
        creds = CredentialManager.instance()
        token, secret = creds.get_token(), creds.get_secret()
        if not token or not secret:
            self.discovery_failed.emit("No SwitchBot credentials configured. Set them in Settings first.")
            return
        try:
            client  = SwitchBotClient(token, secret)
            devices = client.get_devices()
            logger.info(f"[SwitchBotWorker] Discovered {len(devices)} device(s)")
            self.discovery_finished.emit(devices)
        except SwitchBotError as exc:
            logger.error(f"[SwitchBotWorker] Discovery failed: {exc}")
            self.discovery_failed.emit(str(exc))

    def _run_command(self) -> None:
        _, workstation_id, device_id, action = self._op
        creds = CredentialManager.instance()
        token, secret = creds.get_token(), creds.get_secret()
        if not token or not secret:
            self.command_failed.emit(workstation_id, action, "No SwitchBot credentials configured.")
            return
        try:
            client = SwitchBotClient(token, secret)
            if action == "on":
                client.turn_on(device_id)
            else:
                client.turn_off(device_id)
            logger.info(f"[SwitchBotWorker] Command '{action}' sent to {device_id}")
            self.command_finished.emit(workstation_id, action)
        except SwitchBotError as exc:
            logger.error(f"[SwitchBotWorker] Command '{action}' on {device_id} failed: {exc}")
            self.command_failed.emit(workstation_id, action, str(exc))

    def _run_test(self) -> None:
        _, token, secret = self._op
        try:
            client  = SwitchBotClient(token, secret)
            devices = client.get_devices()
            self.connection_tested.emit(True, "Connected successfully.", len(devices))
        except SwitchBotError as exc:
            self.connection_tested.emit(False, str(exc), 0)
