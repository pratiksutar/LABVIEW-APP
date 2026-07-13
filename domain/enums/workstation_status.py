"""
Workstation Status Enum
Defines all possible states for a workstation with associated metadata.
"""
from enum import Enum


class WorkstationStatus(str, Enum):
    AVAILABLE    = "available"
    IDLE         = "idle"
    IN_USE       = "in_use"
    DISCONNECTED = "disconnected"
    MAINTENANCE  = "maintenance"
    FAILURE      = "failure"

    @property
    def display_name(self) -> str:
        return {
            WorkstationStatus.AVAILABLE:    "Available",
            WorkstationStatus.IDLE:         "Idle",
            WorkstationStatus.IN_USE:       "In Use",
            WorkstationStatus.DISCONNECTED: "Disconnected",
            WorkstationStatus.MAINTENANCE:  "Maintenance",
            WorkstationStatus.FAILURE:      "Failure",
        }[self]

    @property
    def color(self) -> str:
        """Hex color for UI indicators."""
        return {
            WorkstationStatus.AVAILABLE:    "#10B981",  # Green
            WorkstationStatus.IDLE:         "#F59E0B",  # Amber
            WorkstationStatus.IN_USE:       "#3B82F6",  # Blue
            WorkstationStatus.DISCONNECTED: "#6B7280",  # Gray
            WorkstationStatus.MAINTENANCE:  "#F97316",  # Orange
            WorkstationStatus.FAILURE:      "#EF4444",  # Red
        }[self]

    @property
    def priority(self) -> int:
        """Lower number = higher priority for display sorting."""
        return {
            WorkstationStatus.MAINTENANCE:  0,
            WorkstationStatus.DISCONNECTED: 1,
            WorkstationStatus.FAILURE:      2,
            WorkstationStatus.IN_USE:       3,
            WorkstationStatus.IDLE:         4,
            WorkstationStatus.AVAILABLE:    5,
        }[self]

    @staticmethod
    def from_power(power_watts: float, is_maintenance: bool = False,
                   is_offline: bool = False) -> "WorkstationStatus":
        """Derive status from power reading."""
        if is_maintenance:
            return WorkstationStatus.MAINTENANCE
        if is_offline:
            return WorkstationStatus.DISCONNECTED
        if power_watts >= 50.0:
            return WorkstationStatus.IN_USE
        if power_watts >= 5.0:
            return WorkstationStatus.IDLE
        return WorkstationStatus.AVAILABLE
