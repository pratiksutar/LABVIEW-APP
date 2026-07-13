"""
Application Settings Manager
Persists settings to ~/.labview/settings.json
"""
import json
from pathlib import Path
from typing import Any, Optional

APP_DIR = Path.home() / ".labview"
APP_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = APP_DIR / "settings.json"

DEFAULTS: dict[str, Any] = {
    "poll_interval":          30,
    "battery_threshold_low":  20,
    "battery_threshold_high": 80,
    "theme":                  "dark",
    "auto_refresh":           True,
    "idle_threshold_watts":   5.0,
    "in_use_threshold_watts": 50.0,
}


class AppSettings:
    """Singleton application settings backed by a JSON file."""

    _instance: Optional["AppSettings"] = None

    def __init__(self) -> None:
        self._data: dict[str, Any] = dict(DEFAULTS)
        self._load()

    # ─── Singleton ────────────────────────────────────────────────
    @classmethod
    def instance(cls) -> "AppSettings":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ─── Persistence ──────────────────────────────────────────────
    def _load(self) -> None:
        if SETTINGS_FILE.exists():
            try:
                with SETTINGS_FILE.open("r", encoding="utf-8") as f:
                    stored = json.load(f)
                self._data.update(stored)
            except Exception:
                pass  # Use defaults if file is corrupt

    def _save(self) -> None:
        try:
            with SETTINGS_FILE.open("w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as exc:
            print(f"[Settings] Could not save: {exc}")

    # ─── Generic access ───────────────────────────────────────────
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._save()

    # ─── Typed convenience properties ─────────────────────────────
    @property
    def poll_interval(self) -> int:
        return int(self.get("poll_interval", 30))

    @poll_interval.setter
    def poll_interval(self, value: int) -> None:
        self.set("poll_interval", max(5, int(value)))

    @property
    def battery_threshold_low(self) -> int:
        return int(self.get("battery_threshold_low", 20))

    @battery_threshold_low.setter
    def battery_threshold_low(self, value: int) -> None:
        self.set("battery_threshold_low", int(value))

    @property
    def battery_threshold_high(self) -> int:
        return int(self.get("battery_threshold_high", 80))

    @battery_threshold_high.setter
    def battery_threshold_high(self, value: int) -> None:
        self.set("battery_threshold_high", int(value))

    @property
    def idle_threshold_watts(self) -> float:
        return float(self.get("idle_threshold_watts", 5.0))

    @property
    def in_use_threshold_watts(self) -> float:
        return float(self.get("in_use_threshold_watts", 50.0))

    @property
    def auto_refresh(self) -> bool:
        return bool(self.get("auto_refresh", True))

    @auto_refresh.setter
    def auto_refresh(self, value: bool) -> None:
        self.set("auto_refresh", value)
