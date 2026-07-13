"""
Workstation Domain Model
Pure Python dataclass representing a workstation entity.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from domain.enums.workstation_status import WorkstationStatus


@dataclass
class Workstation:
    id:                Optional[int]              = None
    name:              str                        = ""
    description:       str                        = ""
    area:              str                        = ""
    device_id:         Optional[str]              = None
    status:            WorkstationStatus           = WorkstationStatus.DISCONNECTED
    is_maintenance:    bool                       = False
    power_state:       bool                       = False
    power_consumption: float                      = 0.0
    voltage:           float                      = 0.0
    last_updated:      Optional[datetime]         = None
    created_at:        Optional[datetime]         = None

    def __str__(self) -> str:
        return f"Workstation({self.name}, {self.status.display_name})"

    def is_online(self) -> bool:
        return self.status not in (
            WorkstationStatus.DISCONNECTED,
            WorkstationStatus.FAILURE,
        )

    def is_controllable(self) -> bool:
        return self.device_id is not None and self.is_online()
