"""
Audit Log Repository
Handles persistence and filtered querying of audit records.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models.audit_log_model import AuditLogModel
from database.connection import DatabaseManager


class AuditLogRepository:
    """Repository for AuditLog write and query operations."""

    def __init__(self) -> None:
        self._db = DatabaseManager.instance()

    # ─── Write ───────────────────────────────────────────────────
    def record(
        self,
        username:  str,
        action:    str,
        entity:    str        = "",
        entity_id: Optional[int] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
    ) -> None:
        session: Session = self._db.get_session()
        try:
            entry = AuditLogModel(
                username=username,
                action=action,
                entity=entity,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
            )
            session.add(entry)
            session.commit()
        except Exception:
            session.rollback()
            # Never crash the caller over a logging failure
        finally:
            session.close()

    # ─── Query ───────────────────────────────────────────────────
    def get_recent(
        self,
        limit:      int                = 200,
        username:   Optional[str]      = None,
        action:     Optional[str]      = None,
        entity:     Optional[str]      = None,
        since:      Optional[datetime] = None,
        until:      Optional[datetime] = None,
    ) -> List[AuditLogModel]:
        session: Session = self._db.get_session()
        try:
            q = session.query(AuditLogModel)
            if username:
                q = q.filter(AuditLogModel.username == username)
            if action:
                q = q.filter(AuditLogModel.action == action)
            if entity:
                q = q.filter(AuditLogModel.entity.ilike(f"%{entity}%"))
            if since:
                q = q.filter(AuditLogModel.timestamp >= since)
            if until:
                q = q.filter(AuditLogModel.timestamp <= until)
            rows = q.order_by(desc(AuditLogModel.timestamp)).limit(limit).all()
            for r in rows:
                session.expunge(r)
            return rows
        finally:
            session.close()

    def count(self) -> int:
        session: Session = self._db.get_session()
        try:
            return session.query(AuditLogModel).count()
        finally:
            session.close()

    def get_distinct_usernames(self) -> List[str]:
        session: Session = self._db.get_session()
        try:
            rows = session.query(AuditLogModel.username).distinct().all()
            return sorted({r[0] for r in rows if r[0]})
        finally:
            session.close()
