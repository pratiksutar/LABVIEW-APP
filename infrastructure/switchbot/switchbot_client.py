"""
SwitchBot Cloud API Client
Handles HMAC-SHA256 authentication and HTTP calls to the SwitchBot v1.1 API.
"""
import hmac
import hashlib
import base64
import time
import uuid
from typing import Optional, Dict, Any, List

import httpx
from loguru import logger

# SWITCHBOT_API_BASE = "https://api.switch-bot.com/v1.1"
SWITCHBOT_API_BASE = "http://127.0.0.1:5000/v1.1"
REQUEST_TIMEOUT    = 10.0


class SwitchBotError(Exception):
    """Raised when a SwitchBot API call fails."""


class SwitchBotClient:
    """Synchronous SwitchBot API client with HMAC authentication."""

    def __init__(self, token: str, secret: str) -> None:
        self.token  = token
        self.secret = secret

    # ─── Auth ────────────────────────────────────────────────────
    def _headers(self) -> Dict[str, str]:
        """Generate signed request headers."""
        t     = str(int(round(time.time() * 1000)))
        nonce = str(uuid.uuid4())
        raw   = f"{self.token}{t}{nonce}"
        sign  = base64.b64encode(
            hmac.new(
                self.secret.encode("utf-8"),
                msg=raw.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        return {
            "Authorization": self.token,
            "Content-Type":  "application/json; charset=utf8",
            "t":             t,
            "sign":          sign,
            "nonce":         nonce,
        }

    # ─── Devices ─────────────────────────────────────────────────
    def get_devices(self) -> List[Dict[str, Any]]:
        """Return list of all registered SwitchBot devices."""
        try:
            resp = httpx.get(
                f"{SWITCHBOT_API_BASE}/devices",
                headers=self._headers(),
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("statusCode") != 100:
                raise SwitchBotError(f"API error: {data.get('message')}")
            return data["body"].get("deviceList", [])
        except httpx.HTTPError as exc:
            logger.error(f"[SwitchBot] get_devices failed: {exc}")
            raise SwitchBotError(str(exc)) from exc

    def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Return the live status of a single device."""
        try:
            resp = httpx.get(
                f"{SWITCHBOT_API_BASE}/devices/{device_id}/status",
                headers=self._headers(),
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("statusCode") != 100:
                raise SwitchBotError(f"API error: {data.get('message')}")
            return data["body"]
        except httpx.HTTPError as exc:
            logger.error(f"[SwitchBot] get_device_status({device_id}) failed: {exc}")
            raise SwitchBotError(str(exc)) from exc

    # ─── Commands ────────────────────────────────────────────────
    def _send_command(self, device_id: str, command: str) -> Dict[str, Any]:
        payload = {
            "command":     command,
            "parameter":   "default",
            "commandType": "command",
        }
        try:
            resp = httpx.post(
                f"{SWITCHBOT_API_BASE}/devices/{device_id}/commands",
                headers=self._headers(),
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("statusCode") not in (100, 200):
                raise SwitchBotError(f"Command failed: {data.get('message')}")
            return data
        except httpx.HTTPError as exc:
            logger.error(f"[SwitchBot] command({command}) on {device_id} failed: {exc}")
            raise SwitchBotError(str(exc)) from exc

    def turn_on(self, device_id: str) -> bool:
        """Turn a Plug Mini ON."""
        logger.debug(f"[SwitchBot] turn_on({device_id})")
        self._send_command(device_id, "turnOn")
        return True

    def turn_off(self, device_id: str) -> bool:
        """Turn a Plug Mini OFF."""
        logger.debug(f"[SwitchBot] turn_off({device_id})")
        self._send_command(device_id, "turnOff")
        return True

    # ─── Health ──────────────────────────────────────────────────
    def ping(self) -> bool:
        """Return True if the API is reachable with current credentials."""
        try:
            self.get_devices()
            return True
        except SwitchBotError:
            return False
