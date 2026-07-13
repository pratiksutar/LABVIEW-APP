"""
Layout Pin Database Model
Stores the position of workstation pins on the lab floor plan.
"""
from sqlalchemy import Integer, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.models.base import Base


class LayoutPinModel(Base):
    __tablename__ = "layout_pins"

    id:             Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    workstation_id: Mapped[int]      = mapped_column(Integer, ForeignKey("workstations.id"), nullable=False)
    x_relative:     Mapped[float]   = mapped_column(Float, nullable=False, default=0.0)
    y_relative:     Mapped[float]   = mapped_column(Float, nullable=False, default=0.0)
    created_at:     Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    workstation: Mapped["WorkstationModel"] = relationship("WorkstationModel", back_populates="layout_pins")

    def __repr__(self) -> str:
        return f"<LayoutPinModel(ws_id={self.workstation_id}, x={self.x_relative:.2f}, y={self.y_relative:.2f})>"
