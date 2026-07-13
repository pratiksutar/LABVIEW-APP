"""
User Role Enum
Defines the three RBAC roles and the permissions each one grants.

Permission matrix (per project roadmap):
  Viewer        — view dashboards, layout, device details (read-only)
  Operator      — Viewer permissions + toggle devices + enable maintenance
  Administrator — full access: registry editing, layout editing, settings,
                  user management
"""
from enum import Enum


class UserRole(str, Enum):
    VIEWER        = "viewer"
    OPERATOR      = "operator"
    ADMINISTRATOR = "administrator"

    @property
    def display_name(self) -> str:
        return {
            UserRole.VIEWER:        "Viewer",
            UserRole.OPERATOR:      "Operator",
            UserRole.ADMINISTRATOR: "Administrator",
        }[self]

    @property
    def level(self) -> int:
        """Higher number = more privileged. Used for >= comparisons."""
        return {
            UserRole.VIEWER:        1,
            UserRole.OPERATOR:      2,
            UserRole.ADMINISTRATOR: 3,
        }[self]

    @property
    def badge_color(self) -> str:
        return {
            UserRole.VIEWER:        "#6B7280",
            UserRole.OPERATOR:      "#3B82F6",
            UserRole.ADMINISTRATOR: "#A78BFA",
        }[self]

    # ─── Permissions ────────────────────────────────────────────
    @property
    def can_control_devices(self) -> bool:
        """Turn devices ON/OFF, toggle maintenance flag."""
        return self.level >= UserRole.OPERATOR.level

    @property
    def can_edit_registry(self) -> bool:
        """Add / edit / delete workstations and device mappings."""
        return self.level >= UserRole.ADMINISTRATOR.level

    @property
    def can_edit_layout_structure(self) -> bool:
        """Upload/remove the floor plan image, add/remove/reposition pins."""
        return self.level >= UserRole.ADMINISTRATOR.level

    @property
    def can_manage_settings(self) -> bool:
        """Access API credentials, polling, and threshold configuration."""
        return self.level >= UserRole.ADMINISTRATOR.level

    @property
    def can_manage_users(self) -> bool:
        """Create/disable users, assign roles, reset passwords."""
        return self.level >= UserRole.ADMINISTRATOR.level

    @staticmethod
    def from_value(value: str) -> "UserRole":
        try:
            return UserRole(value)
        except ValueError:
            return UserRole.VIEWER
