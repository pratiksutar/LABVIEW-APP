"""
User Domain Model
Pure Python dataclass representing an authenticated application user.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from domain.enums.user_role import UserRole


@dataclass
class User:
    id:            Optional[int]      = None
    username:      str                = ""
    full_name:     str                = ""
    role:          UserRole           = UserRole.VIEWER
    is_active:     bool               = True
    last_login:    Optional[datetime] = None
    created_at:    Optional[datetime] = None

    def __str__(self) -> str:
        return f"User({self.username}, {self.role.display_name})"

    @property
    def display_label(self) -> str:
        return self.full_name if self.full_name else self.username
