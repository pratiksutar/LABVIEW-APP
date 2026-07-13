"""
Workstation Database Model
SQLAlchemy ORM representation of the workstations table.
"""
from sqlalchemy import Integer, String, Boolean, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
from database.models.base import Base


class WorkstationModel(Base):
    __tablename__ = "workstations"

    id:             Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:           Mapped[str]            = mapped_column(String(100), nullable=False, unique=True)
    description:    Mapped[Optional[str]]  = mapped_column(String(500), nullable=True)
    area:           Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
    is_maintenance: Mapped[bool]           = mapped_column(Boolean, default=False, nullable=False)
    created_at:     Mapped[datetime]       = mapped_column(DateTime, server_default=func.now())
    updated_at:     Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=func.now())

    # Relationships
    device_mappings: Mapped[List["DeviceMappingModel"]] = relationship(
        "DeviceMappingModel", back_populates="workstation", cascade="all, delete-orphan"
    )
    status_history: Mapped[List["StatusHistoryModel"]] = relationship(
        "StatusHistoryModel", back_populates="workstation", cascade="all, delete-orphan"
    )
    layout_pins: Mapped[List["LayoutPinModel"]] = relationship(
        "LayoutPinModel", back_populates="workstation", cascade="all, delete-orphan"
    )
    battery_automation: Mapped[List["BatteryAutomationModel"]] = relationship(
        "BatteryAutomationModel", back_populates="workstation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<WorkstationModel(id={self.id}, name='{self.name}')>"
