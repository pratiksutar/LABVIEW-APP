"""
Unit Tests — Workstation Domain & Service
Run with: python -m pytest tests/ -v
"""
import sys
import os
import pytest
from datetime import datetime

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from domain.enums.workstation_status import WorkstationStatus
from domain.models.workstation       import Workstation


# ─── WorkstationStatus enum ──────────────────────────────────────
class TestWorkstationStatus:

    def test_display_names(self):
        assert WorkstationStatus.AVAILABLE.display_name    == "Available"
        assert WorkstationStatus.IN_USE.display_name       == "In Use"
        assert WorkstationStatus.DISCONNECTED.display_name == "Disconnected"
        assert WorkstationStatus.MAINTENANCE.display_name  == "Maintenance"
        assert WorkstationStatus.FAILURE.display_name      == "Failure"
        assert WorkstationStatus.IDLE.display_name         == "Idle"

    def test_colors_are_hex(self):
        for status in WorkstationStatus:
            color = status.color
            assert color.startswith("#"), f"{status} color should start with #"
            assert len(color) == 7,       f"{status} color should be 7 chars"

    def test_priority_order(self):
        """Maintenance should have highest priority (lowest number)."""
        assert WorkstationStatus.MAINTENANCE.priority  < WorkstationStatus.DISCONNECTED.priority
        assert WorkstationStatus.DISCONNECTED.priority < WorkstationStatus.FAILURE.priority
        assert WorkstationStatus.FAILURE.priority      < WorkstationStatus.IN_USE.priority
        assert WorkstationStatus.IN_USE.priority       < WorkstationStatus.IDLE.priority
        assert WorkstationStatus.IDLE.priority         < WorkstationStatus.AVAILABLE.priority

    def test_from_power_in_use(self):
        status = WorkstationStatus.from_power(120.0)
        assert status == WorkstationStatus.IN_USE

    def test_from_power_idle(self):
        status = WorkstationStatus.from_power(10.0)
        assert status == WorkstationStatus.IDLE

    def test_from_power_available(self):
        status = WorkstationStatus.from_power(0.5)
        assert status == WorkstationStatus.AVAILABLE

    def test_from_power_maintenance_override(self):
        status = WorkstationStatus.from_power(200.0, is_maintenance=True)
        assert status == WorkstationStatus.MAINTENANCE

    def test_from_power_offline_override(self):
        status = WorkstationStatus.from_power(100.0, is_offline=True)
        assert status == WorkstationStatus.DISCONNECTED

    def test_str_value(self):
        """Enum values should be lowercase strings for DB storage."""
        assert WorkstationStatus.IN_USE.value == "in_use"
        assert WorkstationStatus.AVAILABLE.value == "available"


# ─── Workstation domain model ────────────────────────────────────
class TestWorkstation:

    def _make(self, **kwargs) -> Workstation:
        defaults = dict(
            id=1, name="WS-01", area="Lab A",
            status=WorkstationStatus.AVAILABLE,
            device_id="abc123",
        )
        defaults.update(kwargs)
        return Workstation(**defaults)

    def test_str(self):
        ws = self._make()
        assert "WS-01" in str(ws)
        assert "Available" in str(ws)

    def test_is_online_available(self):
        ws = self._make(status=WorkstationStatus.AVAILABLE)
        assert ws.is_online() is True

    def test_is_online_disconnected(self):
        ws = self._make(status=WorkstationStatus.DISCONNECTED)
        assert ws.is_online() is False

    def test_is_online_failure(self):
        ws = self._make(status=WorkstationStatus.FAILURE)
        assert ws.is_online() is False

    def test_is_controllable_with_device(self):
        ws = self._make(status=WorkstationStatus.AVAILABLE, device_id="dev1")
        assert ws.is_controllable() is True

    def test_is_controllable_no_device(self):
        ws = self._make(status=WorkstationStatus.AVAILABLE, device_id=None)
        assert ws.is_controllable() is False

    def test_is_controllable_offline(self):
        ws = self._make(status=WorkstationStatus.DISCONNECTED, device_id="dev1")
        assert ws.is_controllable() is False

    def test_defaults(self):
        ws = Workstation()
        assert ws.status == WorkstationStatus.DISCONNECTED
        assert ws.power_consumption == 0.0
        assert ws.is_maintenance is False
        assert ws.device_id is None


# ─── Config settings ─────────────────────────────────────────────
class TestAppSettings:

    def test_import(self):
        from config.settings import AppSettings
        settings = AppSettings()
        assert settings.poll_interval >= 5
        assert settings.battery_threshold_low < settings.battery_threshold_high

    def test_defaults(self):
        from config.settings import AppSettings, DEFAULTS
        settings = AppSettings()
        assert settings.poll_interval == DEFAULTS["poll_interval"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
