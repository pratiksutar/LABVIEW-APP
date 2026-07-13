"""
Status History Database Model
Records historical status changes for workstations.
"""
from sqlalchemy import Integer, String, Float, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from database.models.base import Base


class StatusHistoryModel(Base):
    __tablename__ = "status_history"

    id:                Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    workstation_id:    Mapped[int]           = mapped_column(Integer, ForeignKey("workstations.id"), nullable=False)
    status:            Mapped[str]           = mapped_column(String(50), nullable=False)
    power_consumption: Mapped[float]         = mapped_column(Float, default=0.0)
    power_state:       Mapped[bool]          = mapped_column(Boolean, default=False)
    recorded_at:       Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())

    workstation: Mapped["WorkstationModel"] = relationship("WorkstationModel", back_populates="status_history")

    def __repr__(self) -> str:
        return f"<StatusHistoryModel(ws_id={self.workstation_id}, status='{self.status}')>"
