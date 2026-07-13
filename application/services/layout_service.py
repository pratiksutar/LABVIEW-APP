"""
Layout Application Service
Manages the floor plan image file and workstation pin placements.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Dict, Any
from loguru import logger

from PySide6.QtGui import QPixmap

from database.repositories.layout_pin_repository import LayoutPinRepository
from application.services.workstation_service     import WorkstationService
from domain.models.layout_pin                     import LayoutPin
from domain.models.workstation                    import Workstation

LAYOUT_DIR       = Path.home() / ".labview" / "layout"
FLOOR_PLAN_PATH  = LAYOUT_DIR / "floorplan.png"


class LayoutService:
    """Service layer for the Lab Layout floor plan and pin placement."""

    def __init__(self, workstation_service: WorkstationService) -> None:
        self._pin_repo = LayoutPinRepository()
        self._ws_service = workstation_service
        LAYOUT_DIR.mkdir(parents=True, exist_ok=True)

    # ─── Floor plan image ───────────────────────────────────────
    def has_floor_plan(self) -> bool:
        return FLOOR_PLAN_PATH.exists()

    def get_floor_plan_path(self) -> Optional[Path]:
        return FLOOR_PLAN_PATH if FLOOR_PLAN_PATH.exists() else None

    def set_floor_plan(self, source_path: str) -> bool:
        """Load an image from any supported format and store it as PNG."""
        pixmap = QPixmap(source_path)
        if pixmap.isNull():
            logger.error(f"[Layout] Could not load image: {source_path}")
            return False
        ok = pixmap.save(str(FLOOR_PLAN_PATH), "PNG")
        if ok:
            logger.info(f"[Layout] Floor plan saved → {FLOOR_PLAN_PATH}")
        return ok

    def clear_floor_plan(self) -> None:
        """Remove the floor plan image. Pin coordinates are preserved
        so re-uploading a plan restores the same layout."""
        if FLOOR_PLAN_PATH.exists():
            FLOOR_PLAN_PATH.unlink()
            logger.info("[Layout] Floor plan image removed")

    # ─── Pins ────────────────────────────────────────────────────
    def get_placed_pins(self) -> List[Dict[str, Any]]:
        """Return pins joined with live workstation info for rendering."""
        result: List[Dict[str, Any]] = []
        for pin_model in self._pin_repo.get_all():
            ws = self._ws_service.get_workstation(pin_model.workstation_id)
            if ws is None:
                continue
            result.append({
                "workstation_id": ws.id,
                "name":           ws.name,
                "status":         ws.status,
                "x_relative":     pin_model.x_relative,
                "y_relative":     pin_model.y_relative,
            })
        return result

    def get_unplaced_workstations(self) -> List[Workstation]:
        placed_ids = {p.workstation_id for p in self._pin_repo.get_all()}
        return [w for w in self._ws_service.get_all_workstations() if w.id not in placed_ids]

    def is_placed(self, workstation_id: int) -> bool:
        return self._pin_repo.get_by_workstation(workstation_id) is not None

    def save_pin_position(self, workstation_id: int, x_relative: float,
                           y_relative: float) -> None:
        self._pin_repo.upsert(workstation_id, x_relative, y_relative)

    def remove_pin(self, workstation_id: int) -> bool:
        return self._pin_repo.delete_by_workstation(workstation_id)
