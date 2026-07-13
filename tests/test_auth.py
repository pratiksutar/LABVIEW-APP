"""
Unit Tests — Authentication & RBAC (v0.7.0-beta)
Run with: python -m pytest tests/test_auth.py -v
"""
import sys
import os
import uuid
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from domain.enums.user_role import UserRole
from domain.models.user     import User
from infrastructure.security.password_hasher import hash_password, verify_password


# ─── UserRole enum ───────────────────────────────────────────────
class TestUserRole:

    def test_display_names(self):
        assert UserRole.VIEWER.display_name        == "Viewer"
        assert UserRole.OPERATOR.display_name      == "Operator"
        assert UserRole.ADMINISTRATOR.display_name == "Administrator"

    def test_level_ordering(self):
        assert UserRole.VIEWER.level        < UserRole.OPERATOR.level
        assert UserRole.OPERATOR.level      < UserRole.ADMINISTRATOR.level

    def test_viewer_permissions(self):
        r = UserRole.VIEWER
        assert r.can_control_devices        is False
        assert r.can_edit_registry          is False
        assert r.can_edit_layout_structure  is False
        assert r.can_manage_settings        is False
        assert r.can_manage_users           is False

    def test_operator_permissions(self):
        r = UserRole.OPERATOR
        assert r.can_control_devices        is True
        assert r.can_edit_registry          is False
        assert r.can_edit_layout_structure  is False
        assert r.can_manage_settings        is False
        assert r.can_manage_users           is False

    def test_administrator_permissions(self):
        r = UserRole.ADMINISTRATOR
        assert r.can_control_devices        is True
        assert r.can_edit_registry          is True
        assert r.can_edit_layout_structure  is True
        assert r.can_manage_settings        is True
        assert r.can_manage_users           is True

    def test_from_value_valid(self):
        assert UserRole.from_value("viewer")        == UserRole.VIEWER
        assert UserRole.from_value("operator")      == UserRole.OPERATOR
        assert UserRole.from_value("administrator") == UserRole.ADMINISTRATOR

    def test_from_value_invalid_falls_back_to_viewer(self):
        assert UserRole.from_value("superuser") == UserRole.VIEWER
        assert UserRole.from_value("")           == UserRole.VIEWER

    def test_badge_colors_are_hex(self):
        for role in UserRole:
            c = role.badge_color
            assert c.startswith("#") and len(c) == 7, f"{role} badge_color invalid"


# ─── Password hasher ─────────────────────────────────────────────
class TestPasswordHasher:

    def test_hash_is_not_plaintext(self):
        h = hash_password("secret123")
        assert h != "secret123"
        assert len(h) > 20

    def test_verify_correct(self):
        h = hash_password("mypassword")
        assert verify_password("mypassword", h) is True

    def test_verify_wrong(self):
        h = hash_password("mypassword")
        assert verify_password("wrongpass", h) is False

    def test_verify_empty_password(self):
        h = hash_password("abc123")
        assert verify_password("", h) is False

    def test_two_hashes_differ(self):
        """bcrypt salts are randomised — same password gives different hashes."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2
        assert verify_password("same", h1) is True
        assert verify_password("same", h2) is True


# ─── AuthService integration (real SQLite DB) ────────────────────
class TestAuthServiceIntegration:

    @pytest.fixture(autouse=True)
    def _setup(self):
        from database.connection import DatabaseManager
        db = DatabaseManager.instance()
        if db.SessionLocal is None:
            db.initialize()

        from application.services.auth_service import AuthService
        self.auth = AuthService()
        self._created_ids: list[int] = []
        yield
        # Cleanup users created during test
        from database.repositories.user_repository import UserRepository
        repo = UserRepository()
        for uid in self._created_ids:
            repo.set_active(uid, False)     # soft-delete is sufficient for cleanup

    def _unique(self) -> str:
        return f"testuser_{uuid.uuid4().hex[:8]}"

    def _create_user(self, role=UserRole.VIEWER, password="pass1234"):
        username = self._unique()
        user = self.auth.create_user(username, "Test User", password, role)
        self._created_ids.append(user.id)
        return user, username, password

    def test_bootstrap_creates_admin_and_logs_in(self):
        # Only valid on empty DB — skip if users already exist
        if self.auth.has_any_users():
            pytest.skip("DB already has users; bootstrap already ran")
        username = self._unique()
        user = self.auth.bootstrap_admin(username, "Admin User", "adminpass")
        self._created_ids.append(user.id)
        assert user.role == UserRole.ADMINISTRATOR
        assert self.auth.is_authenticated()
        assert self.auth.current_user().username == username

    def test_create_user_and_login_success(self):
        user, username, password = self._create_user(UserRole.OPERATOR)
        self.auth.logout()
        logged_in = self.auth.login(username, password)
        assert logged_in is not None
        assert logged_in.username == username
        assert logged_in.role == UserRole.OPERATOR
        assert self.auth.is_authenticated()

    def test_login_wrong_password_returns_none(self):
        _, username, _ = self._create_user()
        self.auth.logout()
        result = self.auth.login(username, "wrongpassword")
        assert result is None
        assert not self.auth.is_authenticated()

    def test_login_unknown_user_returns_none(self):
        self.auth.logout()
        result = self.auth.login("nobody_xyz_999", "anything")
        assert result is None

    def test_disabled_account_cannot_login(self):
        user, username, password = self._create_user()
        self.auth.set_active(user.id, False)
        self.auth.logout()
        result = self.auth.login(username, password)
        assert result is None

    def test_logout_clears_session(self):
        _, username, password = self._create_user()
        self.auth.login(username, password)
        assert self.auth.is_authenticated()
        self.auth.logout()
        assert not self.auth.is_authenticated()
        assert self.auth.current_user() is None

    def test_duplicate_username_raises(self):
        from application.services.auth_service import UsernameTakenError
        _, username, _ = self._create_user()
        with pytest.raises(UsernameTakenError):
            user2 = self.auth.create_user(username, "Other", "pass1234", UserRole.VIEWER)
            self._created_ids.append(user2.id)

    def test_reset_password(self):
        user, username, _ = self._create_user(password="old_pass")
        ok = self.auth.reset_password(user.id, "new_pass_99")
        assert ok is True
        self.auth.logout()
        result = self.auth.login(username, "new_pass_99")
        assert result is not None

    def test_permission_checks_for_viewer(self):
        _, username, password = self._create_user(UserRole.VIEWER)
        self.auth.login(username, password)
        assert self.auth.can_control_devices()        is False
        assert self.auth.can_edit_registry()          is False
        assert self.auth.can_manage_settings()        is False
        assert self.auth.can_manage_users()           is False

    def test_permission_checks_for_operator(self):
        _, username, password = self._create_user(UserRole.OPERATOR)
        self.auth.login(username, password)
        assert self.auth.can_control_devices()        is True
        assert self.auth.can_edit_registry()          is False
        assert self.auth.can_manage_settings()        is False
        assert self.auth.can_manage_users()           is False

    def test_permission_checks_for_administrator(self):
        _, username, password = self._create_user(UserRole.ADMINISTRATOR)
        self.auth.login(username, password)
        assert self.auth.can_control_devices()        is True
        assert self.auth.can_edit_registry()          is True
        assert self.auth.can_manage_settings()        is True
        assert self.auth.can_manage_users()           is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
