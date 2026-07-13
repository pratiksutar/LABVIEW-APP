"""
Workstation Repository
Handles all database operations for workstations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from database.models.workstation_model import WorkstationModel
from database.connection import DatabaseManager


class WorkstationRepository:
    """Repository for Workstation CRUD operations."""

    def __init__(self) -> None:
        self._db = DatabaseManager.instance()

    # ─── Read ────────────────────────────────────────────────────
    def get_all(self) -> List[WorkstationModel]:
        session: Session = self._db.get_session()
        try:
            return session.query(WorkstationModel).order_by(WorkstationModel.name).all()
        finally:
            session.close()

    def get_by_id(self, workstation_id: int) -> Optional[WorkstationModel]:
        session: Session = self._db.get_session()
        try:
            return session.get(WorkstationModel, workstation_id)
        finally:
            session.close()

    def get_by_name(self, name: str) -> Optional[WorkstationModel]:
        session: Session = self._db.get_session()
        try:
            return session.query(WorkstationModel).filter_by(name=name).first()
        finally:
            session.close()

    def count(self) -> int:
        session: Session = self._db.get_session()
        try:
            return session.query(WorkstationModel).count()
        finally:
            session.close()

    # ─── Create ──────────────────────────────────────────────────
    def create(self, name: str, description: str = "", area: str = "",
                is_maintenance: bool = False) -> WorkstationModel:
        session: Session = self._db.get_session()
        try:
            model = WorkstationModel(
                name=name,
                description=description,
                area=area,
                is_maintenance=is_maintenance,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            # Detach from session so it can be used outside
            session.expunge(model)
            return model
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ─── Update ──────────────────────────────────────────────────
    def update(self, workstation_id: int, name: Optional[str] = None,
                description: Optional[str] = None, area: Optional[str] = None,
                is_maintenance: Optional[bool] = None) -> Optional[WorkstationModel]:
        session: Session = self._db.get_session()
        try:
            model = session.get(WorkstationModel, workstation_id)
            if model is None:
                return None
            if name is not None:
                model.name = name
            if description is not None:
                model.description = description
            if area is not None:
                model.area = area
            if is_maintenance is not None:
                model.is_maintenance = is_maintenance
            session.commit()
            session.refresh(model)
            session.expunge(model)
            return model
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def set_maintenance(self, workstation_id: int, is_maintenance: bool) -> bool:
        result = self.update(workstation_id, is_maintenance=is_maintenance)
        return result is not None

    # ─── Delete ──────────────────────────────────────────────────
    def delete(self, workstation_id: int) -> bool:
        session: Session = self._db.get_session()
        try:
            model = session.get(WorkstationModel, workstation_id)
            if model is None:
                return False
            session.delete(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
