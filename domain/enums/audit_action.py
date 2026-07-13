"""
Audit Action Enum
Every action category that gets recorded in the audit log.
"""
from enum import Enum


class AuditAction(str, Enum):
    # ── Auth ──────────────────────────────────
    LOGIN         = "login"
    LOGOUT        = "logout"
    LOGIN_FAILED  = "login_failed"

    # ── Workstations ──────────────────────────
    WS_CREATED    = "workstation_created"
    WS_UPDATED    = "workstation_updated"
    WS_DELETED    = "workstation_deleted"
    WS_DEVICE_ASSIGNED = "device_assigned"
    WS_DEVICE_REMOVED  = "device_removed"

    # ── Device control ────────────────────────
    DEVICE_ON           = "device_turned_on"
    DEVICE_OFF          = "device_turned_off"
    MAINTENANCE_ENABLED  = "maintenance_enabled"
    MAINTENANCE_DISABLED = "maintenance_disabled"

    # ── Layout ────────────────────────────────
    FLOOR_PLAN_UPLOADED = "floor_plan_uploaded"
    FLOOR_PLAN_REMOVED  = "floor_plan_removed"
    PIN_PLACED          = "pin_placed"
    PIN_REMOVED         = "pin_removed"

    # ── Settings ──────────────────────────────
    SETTINGS_CHANGED    = "settings_changed"
    CREDENTIALS_UPDATED = "credentials_updated"

    # ── Users ─────────────────────────────────
    USER_CREATED        = "user_created"
    USER_UPDATED        = "user_updated"
    USER_DISABLED       = "user_disabled"
    USER_ENABLED        = "user_enabled"
    PASSWORD_RESET      = "password_reset"

    @property
    def display_name(self) -> str:
        return self.value.replace("_", " ").title()

    @property
    def category(self) -> str:
        mapping = {
            "login": "Auth",   "logout": "Auth",   "login_failed": "Auth",
            "workstation_": "Registry", "device_assigned": "Registry",
            "device_removed": "Registry",
            "device_turned_": "Control", "maintenance_": "Control",
            "floor_plan_": "Layout", "pin_": "Layout",
            "settings_": "Settings", "credentials_": "Settings",
            "user_": "Users", "password_": "Users",
        }
        for prefix, cat in mapping.items():
            if self.value.startswith(prefix):
                return cat
        return "Other"
