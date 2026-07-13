"""
Device Mapping Repository
Manages device-to-workstation associations in the database.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from database.models.device_mapping_model import DeviceMappingModel
from database.connection import DatabaseManager


class DeviceMappingRepository:
    """Repository for DeviceMapping CRUD operations."""

    def __init__(self) -> None:
        self._db = DatabaseManager.instance()

    # ─── Read ────────────────────────────────────────────────────
    def get_all(self) -> List[DeviceMappingModel]:
        session: Session = self._db.get_session()
        try:
            return session.query(DeviceMappingModel).all()
        finally:
            session.close()

    def get_by_workstation(self, workstation_id: int) -> Optional[DeviceMappingModel]:
        session: Session = self._db.get_session()
        try:
            return (session.query(DeviceMappingModel)
                    .filter_by(workstation_id=workstation_id, is_active=True)
                    .first())
        finally:
            session.close()

    def get_by_device_id(self, device_id: str) -> Optional[DeviceMappingModel]:
        session: Session = self._db.get_session()
        try:
            return session.query(DeviceMappingModel).filter_by(device_id=device_id).first()
        finally:
            session.close()

    # ─── Create / Update ─────────────────────────────────────────
    def upsert(self, workstation_id: int, device_id: str,
                device_name: str = "", device_type: str = "Plug Mini") -> DeviceMappingModel:
        """Create or update a device mapping for a workstation."""
        session: Session = self._db.get_session()
        try:
            existing = (session.query(DeviceMappingModel)
                        .filter_by(workstation_id=workstation_id)
                        .first())
            if existing:
                existing.device_id   = device_id
                existing.device_name = device_name
                existing.device_type = device_type
                existing.is_active   = True
                model = existing
            else:
                model = DeviceMappingModel(
                    workstation_id=workstation_id,
                    device_id=device_id,
                    device_name=device_name,
                    device_type=device_type,
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
            rows = (session.query(DeviceMappingModel)
                    .filter_by(workstation_id=workstation_id)
                    .all())
            for row in rows:
                session.delete(row)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
