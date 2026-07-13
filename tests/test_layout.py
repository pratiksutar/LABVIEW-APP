"""
Unit Tests — Lab Layout (v0.6.0-beta)
Run with: python -m pytest tests/test_layout.py -v
"""
import sys
import os
import uuid
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from domain.models.layout_pin import LayoutPin


# ─── LayoutPin domain model ──────────────────────────────────────
class TestLayoutPin:

    def test_defaults(self):
        pin = LayoutPin()
        assert pin.id is None
        assert pin.workstation_id is None
        assert pin.x_relative == 0.5
        assert pin.y_relative == 0.5

    def test_str(self):
        pin = LayoutPin(workstation_id=7, x_relative=0.25, y_relative=0.75)
        text = str(pin)
        assert "7" in text
        assert "0.25" in text
        assert "0.75" in text

    def test_custom_values(self):
        pin = LayoutPin(id=1, workstation_id=3, x_relative=0.1, y_relative=0.9)
        assert pin.id == 1
        assert pin.workstation_id == 3
        assert pin.x_relative == 0.1
        assert pin.y_relative == 0.9


# ─── LayoutService integration (real SQLite DB) ──────────────────
class TestLayoutServiceIntegration:
    """
    Exercises the full repository → service round trip against a real
    (temporary-data) SQLite database, mirroring how the app uses it.
    """

    @pytest.fixture(autouse=True)
    def _setup(self):
        from database.connection import DatabaseManager
        self.db = DatabaseManager.instance()
        if self.db.SessionLocal is None:
            self.db.initialize()

        from application.services.workstation_service import WorkstationService
        from application.services.layout_service import LayoutService

        self.ws_service = WorkstationService()
        self.layout_service = LayoutService(self.ws_service)

        # Unique name per run to avoid collisions across repeated test runs
        suffix = uuid.uuid4().hex[:8]
        self.ws = self.ws_service.create_workstation(f"TestBench-{suffix}", area="Test Area")

        yield

        # Cleanup
        self.layout_service.remove_pin(self.ws.id)
        self.ws_service.delete_workstation(self.ws.id)

    def test_workstation_starts_unplaced(self):
        unplaced_ids = {w.id for w in self.layout_service.get_unplaced_workstations()}
        assert self.ws.id in unplaced_ids
        assert self.layout_service.is_placed(self.ws.id) is False

    def test_save_and_retrieve_pin_position(self):
        self.layout_service.save_pin_position(self.ws.id, 0.3, 0.6)
        assert self.layout_service.is_placed(self.ws.id) is True

        pins = self.layout_service.get_placed_pins()
        match = next(p for p in pins if p["workstation_id"] == self.ws.id)
        assert match["x_relative"] == pytest.approx(0.3)
        assert match["y_relative"] == pytest.approx(0.6)
        assert match["name"] == self.ws.name

    def test_pin_clamped_to_valid_range(self):
        self.layout_service.save_pin_position(self.ws.id, 1.5, -0.5)
        pins = self.layout_service.get_placed_pins()
        match = next(p for p in pins if p["workstation_id"] == self.ws.id)
        assert 0.0 <= match["x_relative"] <= 1.0
        assert 0.0 <= match["y_relative"] <= 1.0

    def test_moving_pin_updates_existing_row_not_duplicate(self):
        self.layout_service.save_pin_position(self.ws.id, 0.1, 0.1)
        self.layout_service.save_pin_position(self.ws.id, 0.9, 0.9)
        pins = [p for p in self.layout_service.get_placed_pins()
                if p["workstation_id"] == self.ws.id]
        assert len(pins) == 1
        assert pins[0]["x_relative"] == pytest.approx(0.9)

    def test_remove_pin_returns_to_unplaced(self):
        self.layout_service.save_pin_position(self.ws.id, 0.5, 0.5)
        assert self.layout_service.is_placed(self.ws.id) is True

        removed = self.layout_service.remove_pin(self.ws.id)
        assert removed is True
        assert self.layout_service.is_placed(self.ws.id) is False

        unplaced_ids = {w.id for w in self.layout_service.get_unplaced_workstations()}
        assert self.ws.id in unplaced_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
