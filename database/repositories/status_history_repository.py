"""
Status History Repository
Persists workstation status changes and provides lookups,
including the most recent record for cache hydration on startup.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models.status_history_model import StatusHistoryModel
from database.connection import DatabaseManager


class StatusHistoryRepository:
    """Repository for StatusHistory read/write operations."""

    def __init__(self) -> None:
        self._db = DatabaseManager.instance()

    # ─── Write ───────────────────────────────────────────────────
    def record(self, workstation_id: int, status: str,
               power_consumption: float = 0.0, power_state: bool = False) -> None:
        session: Session = self._db.get_session()
        try:
            entry = StatusHistoryModel(
                workstation_id=workstation_id,
                status=status,
                power_consumption=power_consumption,
                power_state=power_state,
            )
            session.add(entry)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ─── Read ────────────────────────────────────────────────────
    def get_latest_for_workstation(self, workstation_id: int) -> Optional[StatusHistoryModel]:
        session: Session = self._db.get_session()
        try:
            row = (session.query(StatusHistoryModel)
                   .filter_by(workstation_id=workstation_id)
                   .order_by(desc(StatusHistoryModel.recorded_at))
                   .first())
            if row is not None:
                session.expunge(row)
            return row
        finally:
            session.close()

    def get_recent(self, workstation_id: int, limit: int = 50) -> List[StatusHistoryModel]:
        session: Session = self._db.get_session()
        try:
            rows = (session.query(StatusHistoryModel)
                    .filter_by(workstation_id=workstation_id)
                    .order_by(desc(StatusHistoryModel.recorded_at))
                    .limit(limit)
                    .all())
            for r in rows:
                session.expunge(r)
            return rows
        finally:
            session.close()

    def prune_older_than(self, days: int = 90) -> int:
        """Delete history older than N days. Returns rows deleted."""
        from datetime import datetime, timedelta
        session: Session = self._db.get_session()
        try:
            cutoff = datetime.now() - timedelta(days=days)
            count = (session.query(StatusHistoryModel)
                     .filter(StatusHistoryModel.recorded_at < cutoff)
                     .delete())
            session.commit()
            return count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
