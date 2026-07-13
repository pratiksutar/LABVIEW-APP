"""
Audit Log Database Model
SQLAlchemy ORM representation of the audit_logs table.
"""
from sqlalchemy import Integer, String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from database.models.base import Base


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id:         Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp:  Mapped[datetime]       = mapped_column(DateTime, server_default=func.now(), index=True)
    username:   Mapped[str]            = mapped_column(String(80), nullable=False, default="system", index=True)
    action:     Mapped[str]            = mapped_column(String(80), nullable=False, index=True)
    entity:     Mapped[str]            = mapped_column(String(100), nullable=False, default="")
    entity_id:  Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
    old_value:  Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    new_value:  Mapped[Optional[str]]  = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog({self.timestamp}, {self.username}, {self.action})>"
