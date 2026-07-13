"""
Device Mapping Database Model
Links a SwitchBot device to a workstation.
"""
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from database.models.base import Base


class DeviceMappingModel(Base):
    __tablename__ = "device_mappings"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    workstation_id: Mapped[int]           = mapped_column(Integer, ForeignKey("workstations.id"), nullable=False)
    device_id:      Mapped[str]           = mapped_column(String(200), nullable=False, unique=True)
    device_name:    Mapped[str]           = mapped_column(String(200), nullable=False, default="")
    device_type:    Mapped[str]           = mapped_column(String(100), nullable=False, default="Plug Mini")
    is_active:      Mapped[bool]          = mapped_column(Boolean, default=True)
    created_at:     Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())

    # Relationship
    workstation: Mapped["WorkstationModel"] = relationship("WorkstationModel", back_populates="device_mappings")

    def __repr__(self) -> str:
        return f"<DeviceMappingModel(device_id='{self.device_id}', ws_id={self.workstation_id})>"
