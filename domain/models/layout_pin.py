"""
Layout Pin Domain Model
Pure Python dataclass representing a workstation's position on the floor plan.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class LayoutPin:
    id:             Optional[int]      = None
    workstation_id: Optional[int]      = None
    x_relative:     float              = 0.5
    y_relative:     float              = 0.5
    created_at:     Optional[datetime] = None

    def __str__(self) -> str:
        return f"LayoutPin(ws#{self.workstation_id} @ {self.x_relative:.2f},{self.y_relative:.2f})"
