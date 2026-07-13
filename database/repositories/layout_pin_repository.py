"""
Layout Pin Repository
Persists workstation positions on the lab floor plan.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from database.models.layout_pin_model import LayoutPinModel
from database.connection import DatabaseManager


class LayoutPinRepository:
    """Repository for LayoutPin CRUD operations."""

    def __init__(self) -> None:
        self._db = DatabaseManager.instance()

    # ─── Read ────────────────────────────────────────────────────
    def get_all(self) -> List[LayoutPinModel]:
        session: Session = self._db.get_session()
        try:
            return session.query(LayoutPinModel).all()
        finally:
            session.close()

    def get_by_workstation(self, workstation_id: int) -> Optional[LayoutPinModel]:
        session: Session = self._db.get_session()
        try:
            return (session.query(LayoutPinModel)
                    .filter_by(workstation_id=workstation_id)
                    .first())
        finally:
            session.close()

    # ─── Create / Update ─────────────────────────────────────────
    def upsert(self, workstation_id: int, x_relative: float,
               y_relative: float) -> LayoutPinModel:
        """Create or move a pin for a workstation."""
        x_relative = max(0.0, min(1.0, x_relative))
        y_relative = max(0.0, min(1.0, y_relative))

        session: Session = self._db.get_session()
        try:
            existing = (session.query(LayoutPinModel)
                        .filter_by(workstation_id=workstation_id)
                        .first())
            if existing:
                existing.x_relative = x_relative
                existing.y_relative = y_relative
                model = existing
            else:
                model = LayoutPinModel(
                    workstation_id=workstation_id,
                    x_relative=x_relative,
                    y_relative=y_relative,
                )
                session.add(model)
            session.commit()
            session.refresh(model)
            session.expunge(model)
            return model
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ─── Delete ──────────────────────────────────────────────────
    def delete_by_workstation(self, workstation_id: int) -> bool:
        session: Session = self._db.get_session()
        try:
            row = (session.query(LayoutPinModel)
                   .filter_by(workstation_id=workstation_id)
                   .first())
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
