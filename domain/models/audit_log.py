"""
Audit Log Domain Model
Pure Python dataclass representing one audit record.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from domain.enums.audit_action import AuditAction


@dataclass
class AuditLog:
    id:          Optional[int]      = None
    timestamp:   Optional[datetime] = None
    username:    str                = ""
    action:      str                = ""
    entity:      str                = ""
    entity_id:   Optional[int]      = None
    old_value:   Optional[str]      = None
    new_value:   Optional[str]      = None

    @property
    def action_display(self) -> str:
        try:
            return AuditAction(self.action).display_name
        except ValueError:
            return self.action

    @property
    def category(self) -> str:
        try:
            return AuditAction(self.action).category
        except ValueError:
            return "Other"
