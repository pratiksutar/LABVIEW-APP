"""
Audit Log Service
Singleton used by all other services to emit audit events.
Callers pass the current username explicitly so the service stays
stateless with respect to authentication.
"""
from __future__ import annotations

from typing import Optional
from loguru import logger

from database.repositories.audit_log_repository import AuditLogRepository
from domain.enums.audit_action import AuditAction


class AuditService:
    """Thin wrapper around AuditLogRepository for convenient audit logging."""

    _instance: Optional["AuditService"] = None

    def __init__(self) -> None:
        self._repo = AuditLogRepository()

    @classmethod
    def instance(cls) -> "AuditService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ─── Core log method ─────────────────────────────────────────
    def log(
        self,
        action:    AuditAction,
        username:  str            = "system",
        entity:    str            = "",
        entity_id: Optional[int]  = None,
        old_value: Optional[str]  = None,
        new_value: Optional[str]  = None,
    ) -> None:
        logger.debug(f"[Audit] {username} | {action.value} | {entity} #{entity_id}")
        try:
            self._repo.record(
                username=username,
                action=action.value,
                entity=entity,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
            )
        except Exception as exc:
            # Audit failures must never crash the app
            logger.error(f"[Audit] Failed to persist log entry: {exc}")

    # ─── Query helpers (used by AuditLogsPage) ───────────────────
    def get_recent(self, **kwargs):
        return self._repo.get_recent(**kwargs)

    def get_distinct_usernames(self):
        return self._repo.get_distinct_usernames()

    def total_count(self) -> int:
        return self._repo.count()
