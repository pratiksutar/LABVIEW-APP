"""
User Database Model
SQLAlchemy ORM representation of the users table.
"""
from sqlalchemy import Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from database.models.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id:            Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    username:      Mapped[str]            = mapped_column(String(80), nullable=False, unique=True)
    password_hash: Mapped[str]            = mapped_column(String(255), nullable=False)
    full_name:     Mapped[str]            = mapped_column(String(150), nullable=False, default="")
    role:          Mapped[str]            = mapped_column(String(30), nullable=False, default="viewer")
    is_active:     Mapped[bool]           = mapped_column(Boolean, default=True, nullable=False)
    last_login:    Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at:    Mapped[datetime]       = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, username='{self.username}', role='{self.role}')>"
