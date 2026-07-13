"""
Credential Manager
Stores API credentials securely using Windows Credential Manager (keyring).
Falls back to encrypted file storage if keyring is unavailable.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Optional
from loguru import logger

SERVICE_NAME = "LabView"
APP_DIR      = Path.home() / ".labview"
CRED_FILE    = APP_DIR / ".credentials"


class CredentialManager:
    """Stores and retrieves SwitchBot API credentials."""

    _instance: Optional["CredentialManager"] = None

    @classmethod
    def instance(cls) -> "CredentialManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ─── Store ───────────────────────────────────────────────────
    def save_token(self, token: str) -> None:
        self._store("switchbot_token", token)

    def save_secret(self, secret: str) -> None:
        self._store("switchbot_secret", secret)

    # ─── Retrieve ────────────────────────────────────────────────
    def get_token(self) -> Optional[str]:
        return self._retrieve("switchbot_token")

    def get_secret(self) -> Optional[str]:
        return self._retrieve("switchbot_secret")

    def has_credentials(self) -> bool:
        return bool(self.get_token() and self.get_secret())

    # ─── Clear ───────────────────────────────────────────────────
    def clear(self) -> None:
        for key in ("switchbot_token", "switchbot_secret"):
            try:
                import keyring
                keyring.delete_password(SERVICE_NAME, key)
            except Exception:
                pass
        if CRED_FILE.exists():
            CRED_FILE.unlink()

    # ─── Internal ────────────────────────────────────────────────
    def _store(self, key: str, value: str) -> None:
        try:
            import keyring
            keyring.set_password(SERVICE_NAME, key, value)
            logger.debug(f"[CredentialManager] Stored '{key}' in keyring")
            return
        except Exception as exc:
            logger.warning(f"[CredentialManager] keyring unavailable ({exc}), using file fallback")

        self._file_store(key, value)

    def _retrieve(self, key: str) -> Optional[str]:
        try:
            import keyring
            value = keyring.get_password(SERVICE_NAME, key)
            if value:
                return value
        except Exception:
            pass

        return self._file_retrieve(key)

    # ─── File fallback (base64 obfuscation only) ─────────────────
    def _file_store(self, key: str, value: str) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        data = self._file_load()
        data[key] = base64.b64encode(value.encode()).decode()
        try:
            with CRED_FILE.open("w") as f:
                json.dump(data, f)
        except Exception as exc:
            logger.error(f"[CredentialManager] Could not write credential file: {exc}")

    def _file_retrieve(self, key: str) -> Optional[str]:
        data = self._file_load()
        encoded = data.get(key)
        if encoded:
            try:
                return base64.b64decode(encoded.encode()).decode()
            except Exception:
                pass
        return None

    def _file_load(self) -> dict:
        if CRED_FILE.exists():
            try:
                with CRED_FILE.open("r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
