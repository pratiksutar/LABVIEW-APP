"""
Unit Tests — Audit Logs & Reports (v0.8.0-beta)
Run with: python -m pytest tests/test_audit_reports.py -v
"""
import sys
import os
import uuid
import pytest
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from domain.enums.audit_action import AuditAction


# ─── AuditAction enum ────────────────────────────────────────────
class TestAuditAction:

    def test_all_values_are_strings(self):
        for a in AuditAction:
            assert isinstance(a.value, str)

    def test_display_names_are_title_case(self):
        for a in AuditAction:
            assert a.display_name, f"{a} has empty display_name"

    def test_categories_assigned(self):
        assert AuditAction.LOGIN.category         == "Auth"
        assert AuditAction.WS_CREATED.category    == "Registry"
        assert AuditAction.DEVICE_ON.category     == "Control"
        assert AuditAction.PIN_PLACED.category    == "Layout"
        assert AuditAction.SETTINGS_CHANGED.category == "Settings"
        assert AuditAction.USER_CREATED.category  == "Users"

    def test_roundtrip_from_value(self):
        for a in AuditAction:
            assert AuditAction(a.value) == a


# ─── AuditLog domain model ───────────────────────────────────────
class TestAuditLogModel:

    def test_action_display_valid(self):
        from domain.models.audit_log import AuditLog
        entry = AuditLog(action=AuditAction.LOGIN.value)
        assert entry.action_display == AuditAction.LOGIN.display_name

    def test_action_display_invalid(self):
        from domain.models.audit_log import AuditLog
        entry = AuditLog(action="unknown_action")
        assert entry.action_display == "unknown_action"

    def test_category_valid(self):
        from domain.models.audit_log import AuditLog
        entry = AuditLog(action=AuditAction.USER_CREATED.value)
        assert entry.category == "Users"

    def test_category_invalid(self):
        from domain.models.audit_log import AuditLog
        entry = AuditLog(action="not_real")
        assert entry.category == "Other"


# ─── AuditService integration ────────────────────────────────────
class TestAuditServiceIntegration:

    @pytest.fixture(autouse=True)
    def _setup(self):
        from database.connection import DatabaseManager
        db = DatabaseManager.instance()
        if db.SessionLocal is None:
            db.initialize()

        # Reset singleton so each test gets fresh state
        from application.services import audit_service as _mod
        _mod.AuditService._instance = None

        from application.services.audit_service import AuditService
        self.svc = AuditService.instance()
        self._tag = uuid.uuid4().hex[:8]
        yield

    def test_log_and_retrieve(self):
        username = f"tester_{self._tag}"
        self.svc.log(AuditAction.LOGIN, username=username, entity="Session")

        rows = self.svc.get_recent(username=username, limit=5)
        assert len(rows) >= 1
        assert rows[0].username == username
        assert rows[0].action   == AuditAction.LOGIN.value

    def test_multiple_actions_recorded(self):
        username = f"multi_{self._tag}"
        self.svc.log(AuditAction.LOGIN,       username=username, entity="Session")
        self.svc.log(AuditAction.WS_CREATED,  username=username, entity="Workstation", entity_id=99)
        self.svc.log(AuditAction.LOGOUT,      username=username, entity="Session")

        rows = self.svc.get_recent(username=username, limit=10)
        actions = {r.action for r in rows}
        assert AuditAction.LOGIN.value       in actions
        assert AuditAction.WS_CREATED.value  in actions
        assert AuditAction.LOGOUT.value      in actions

    def test_filter_by_action(self):
        username = f"filt_{self._tag}"
        self.svc.log(AuditAction.LOGIN,  username=username)
        self.svc.log(AuditAction.LOGOUT, username=username)

        rows = self.svc.get_recent(username=username,
                                    action=AuditAction.LOGIN.value, limit=10)
        assert all(r.action == AuditAction.LOGIN.value for r in rows)

    def test_old_value_new_value_stored(self):
        username = f"val_{self._tag}"
        self.svc.log(AuditAction.WS_UPDATED, username=username,
                     entity="Workstation", entity_id=1,
                     old_value="Old Name", new_value="New Name")

        rows = self.svc.get_recent(username=username, limit=5)
        assert rows[0].old_value == "Old Name"
        assert rows[0].new_value == "New Name"

    def test_total_count_increases(self):
        before = self.svc.total_count()
        self.svc.log(AuditAction.SETTINGS_CHANGED,
                     username=f"cnt_{self._tag}", entity="Settings")
        assert self.svc.total_count() >= before + 1

    def test_distinct_usernames(self):
        u1 = f"duser1_{self._tag}"
        u2 = f"duser2_{self._tag}"
        self.svc.log(AuditAction.LOGIN, username=u1)
        self.svc.log(AuditAction.LOGIN, username=u2)
        names = self.svc.get_distinct_usernames()
        assert u1 in names
        assert u2 in names


# ─── ReportService ───────────────────────────────────────────────
class TestReportService:

    @pytest.fixture(autouse=True)
    def _setup(self):
        from database.connection import DatabaseManager
        db = DatabaseManager.instance()
        if db.SessionLocal is None:
            db.initialize()
        from application.services.report_service import ReportService
        self.svc = ReportService()
        yield

    def test_daily_report_structure(self):
        data = self.svc.daily_report(date.today())
        assert data["period"] == "daily"
        assert "label"  in data
        assert "stats"  in data
        assert "chart_labels" in data
        assert "chart_values" in data
        assert len(data["chart_labels"]) == 24  # 24 hours
        assert len(data["chart_values"]) == 24

    def test_weekly_report_structure(self):
        data = self.svc.weekly_report()
        assert data["period"] == "weekly"
        assert len(data["chart_labels"]) == 7
        assert len(data["chart_values"]) == 7

    def test_monthly_report_structure(self):
        today = date.today()
        data  = self.svc.monthly_report(today.year, today.month)
        assert data["period"] == "monthly"
        assert len(data["chart_labels"]) > 0
        assert len(data["chart_values"]) > 0
        assert "per_workstation" in data

    def test_stats_keys_present(self):
        data  = self.svc.daily_report()
        stats = data["stats"]
        for key in ("in_use_pct", "idle_pct", "available_pct",
                     "avg_power_w", "total_records"):
            assert key in stats, f"Missing stats key: {key}"

    def test_stats_percentages_are_floats(self):
        stats = self.svc.daily_report()["stats"]
        assert isinstance(stats["in_use_pct"],  float)
        assert isinstance(stats["idle_pct"],    float)
        assert isinstance(stats["available_pct"], float)

    def test_per_workstation_is_list(self):
        data = self.svc.monthly_report()
        assert isinstance(data["per_workstation"], list)

    def test_report_with_no_data_returns_zeroes(self):
        # A date far in the past with no data
        data  = self.svc.daily_report(date(2000, 1, 1))
        stats = data["stats"]
        assert stats["total_records"] == 1   # denominator floor
        assert stats["in_use_pct"]    == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
