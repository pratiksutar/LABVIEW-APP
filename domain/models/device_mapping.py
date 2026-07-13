"""
Device Mapping Domain Model
Maps a physical SwitchBot device to a workstation.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DeviceMapping:
    id:             Optional[int]      = None
    workstation_id: Optional[int]      = None
    device_id:      str                = ""
    device_name:    str                = ""
    device_type:    str                = "Plug Mini"
    is_active:      bool               = True
    created_at:     Optional[datetime] = None

    def __str__(self) -> str:
        return f"DeviceMapping({self.device_name} → WS#{self.workstation_id})"
