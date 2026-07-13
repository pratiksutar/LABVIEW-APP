"""
Battery Automation Database Model
Stores battery automation thresholds per workstation.
"""
from sqlalchemy import Integer, Float, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.models.base import Base


class BatteryAutomationModel(Base):
    __tablename__ = "battery_automation"

    id:              Mapped[int]     = mapped_column(Integer, primary_key=True, autoincrement=True)
    workstation_id:  Mapped[int]     = mapped_column(Integer, ForeignKey("workstations.id"), nullable=False)
    enabled:         Mapped[bool]    = mapped_column(Boolean, default=False)
    charge_below:    Mapped[float]   = mapped_column(Float, default=20.0)
    stop_above:      Mapped[float]   = mapped_column(Float, default=80.0)
    created_at:      Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    workstation: Mapped["WorkstationModel"] = relationship("WorkstationModel", back_populates="battery_automation")

    def __repr__(self) -> str:
        return f"<BatteryAutomationModel(ws_id={self.workstation_id}, below={self.charge_below}%, above={self.stop_above}%)>"
