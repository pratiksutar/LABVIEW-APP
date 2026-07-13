"""
Auth Application Service
Handles login, first-run admin bootstrap, the current session, and
RBAC permission checks consumed by the UI layer.
"""
from __future__ import annotations

from typing import List, Optional
from loguru import logger

from database.repositories.user_repository       import UserRepository
from database.models.user_model                  import UserModel
from domain.models.user                          import User
from domain.enums.user_role                       import UserRole
from domain.enums.audit_action                   import AuditAction
from infrastructure.security.password_hasher     import hash_password, verify_password


class AuthError(Exception):
    """Base exception for authentication/authorization failures."""


class UsernameTakenError(AuthError):
    """Raised when attempting to create a user with an existing username."""


class AuthService:
    """Service layer for authentication, sessions, and user management."""

    def __init__(self) -> None:
        self._user_repo = UserRepository()
        self._current_user: Optional[User] = None

    def _audit(self) -> "AuditService":  # lazy import avoids circular deps
        from application.services.audit_service import AuditService
        return AuditService.instance()

    # ─── First-run bootstrap ──────────────────────────────────────
    def has_any_users(self) -> bool:
        return self._user_repo.count() > 0

    def bootstrap_admin(self, username: str, full_name: str, password: str) -> User:
        """Create the very first user, always as Administrator, and log them in."""
        if self._user_repo.get_by_username(username) is not None:
            raise UsernameTakenError(f"Username '{username}' is already taken.")

        model = self._user_repo.create(
            username=username,
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRole.ADMINISTRATOR.value,
            is_active=True,
        )
        logger.info(f"[Auth] Bootstrap administrator account created: {username}")
        self._user_repo.update_last_login(model.id)
        user = self._model_to_domain(model)
        self._current_user = user
        self._audit().log(AuditAction.USER_CREATED, username=username,
                          entity="User", entity_id=model.id,
                          new_value="Administrator (bootstrap)")
        self._audit().log(AuditAction.LOGIN, username=username, entity="Session")
        return user

    # ─── Login / Logout ───────────────────────────────────────────
    def login(self, username: str, password: str) -> Optional[User]:
        model = self._user_repo.get_by_username(username.strip())
        if model is None:
            logger.warning(f"[Auth] Login failed — unknown username: {username}")
            self._audit().log(AuditAction.LOGIN_FAILED, username=username, entity="Session")
            return None
        if not model.is_active:
            logger.warning(f"[Auth] Login rejected — account disabled: {username}")
            self._audit().log(AuditAction.LOGIN_FAILED, username=username,
                              entity="Session", new_value="account disabled")
            return None
        if not verify_password(password, model.password_hash):
            logger.warning(f"[Auth] Login failed — bad password for: {username}")
            self._audit().log(AuditAction.LOGIN_FAILED, username=username, entity="Session")
            return None

        self._user_repo.update_last_login(model.id)
        user = self._model_to_domain(model)
        self._current_user = user
        logger.info(f"[Auth] Login successful: {username} ({user.role.display_name})")
        self._audit().log(AuditAction.LOGIN, username=username, entity="Session")
        return user

    def logout(self) -> None:
        if self._current_user:
            self._audit().log(AuditAction.LOGOUT,
                              username=self._current_user.username, entity="Session")
            logger.info(f"[Auth] Logout: {self._current_user.username}")
        self._current_user = None

    def current_user(self) -> Optional[User]:
        return self._current_user

    def is_authenticated(self) -> bool:
        return self._current_user is not None

    # ─── Permission checks (delegate to role) ─────────────────────
    def can_control_devices(self) -> bool:
        return self._current_user is not None and self._current_user.role.can_control_devices

    def can_edit_registry(self) -> bool:
        return self._current_user is not None and self._current_user.role.can_edit_registry

    def can_edit_layout_structure(self) -> bool:
        return self._current_user is not None and self._current_user.role.can_edit_layout_structure

    def can_manage_settings(self) -> bool:
        return self._current_user is not None and self._current_user.role.can_manage_settings

    def can_manage_users(self) -> bool:
        return self._current_user is not None and self._current_user.role.can_manage_users

    # ─── User management (Administrator operations) ───────────────
    def list_users(self) -> List[User]:
        return [self._model_to_domain(m) for m in self._user_repo.get_all()]

    def create_user(self, username: str, full_name: str, password: str,
                     role: UserRole) -> User:
        username = username.strip()
        if not username:
            raise AuthError("Username is required.")
        if len(password) < 6:
            raise AuthError("Password must be at least 6 characters.")
        if self._user_repo.get_by_username(username) is not None:
            raise UsernameTakenError(f"Username '{username}' is already taken.")

        model = self._user_repo.create(
            username=username,
            password_hash=hash_password(password),
            full_name=full_name.strip(),
            role=role.value,
            is_active=True,
        )
        logger.info(f"[Auth] User created: {username} ({role.display_name})")
        actor = self._current_user.username if self._current_user else "system"
        self._audit().log(AuditAction.USER_CREATED, username=actor,
                          entity="User", entity_id=model.id,
                          new_value=f"{username} / {role.display_name}")
        return self._model_to_domain(model)

    def update_user(self, user_id: int, full_name: Optional[str] = None,
                     role: Optional[UserRole] = None) -> Optional[User]:
        old_model = self._user_repo.get_by_id(user_id)
        old_info  = f"{old_model.full_name} / {old_model.role}" if old_model else None
        model = self._user_repo.update(
            user_id,
            full_name=full_name,
            role=role.value if role is not None else None,
        )
        if model:
            actor = self._current_user.username if self._current_user else "system"
            self._audit().log(AuditAction.USER_UPDATED, username=actor,
                              entity="User", entity_id=user_id,
                              old_value=old_info,
                              new_value=f"{model.full_name} / {model.role}")
        return self._model_to_domain(model) if model else None

    def set_active(self, user_id: int, is_active: bool) -> bool:
        if (self._current_user and self._current_user.id == user_id and not is_active):
            raise AuthError("You cannot disable your own account while logged in.")
        ok = self._user_repo.set_active(user_id, is_active)
        if ok:
            logger.info(f"[Auth] User #{user_id} active={is_active}")
            actor  = self._current_user.username if self._current_user else "system"
            action = AuditAction.USER_ENABLED if is_active else AuditAction.USER_DISABLED
            self._audit().log(action, username=actor, entity="User", entity_id=user_id)
        return ok

    def reset_password(self, user_id: int, new_password: str) -> bool:
        if len(new_password) < 6:
            raise AuthError("Password must be at least 6 characters.")
        ok = self._user_repo.set_password(user_id, hash_password(new_password))
        if ok:
            logger.info(f"[Auth] Password reset for user #{user_id}")
            actor = self._current_user.username if self._current_user else "system"
            self._audit().log(AuditAction.PASSWORD_RESET, username=actor,
                              entity="User", entity_id=user_id)
        return ok

    # ─── Helpers ────────────────────────────────────────────────
    def _model_to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            full_name=model.full_name,
            role=UserRole.from_value(model.role),
            is_active=model.is_active,
            last_login=model.last_login,
            created_at=model.created_at,
        )
