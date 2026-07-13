"""
Reports Service
Computes utilization statistics from the status_history table and
prepares data structures consumed by the Reports page and exporters.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from database.connection import DatabaseManager
from database.models.status_history_model import StatusHistoryModel
from database.models.workstation_model     import WorkstationModel


class ReportService:
    """Generates utilization and occupancy analytics."""

    def __init__(self) -> None:
        self._db = DatabaseManager.instance()

    # ─── Helpers ────────────────────────────────────────────────
    def _session(self) -> Session:
        return self._db.get_session()

    # ─── Status history raw query ────────────────────────────────
    def _history_in_range(self, since: datetime,
                           until: datetime) -> List[StatusHistoryModel]:
        session = self._session()
        try:
            return (session.query(StatusHistoryModel)
                    .filter(StatusHistoryModel.recorded_at >= since,
                            StatusHistoryModel.recorded_at <= until)
                    .order_by(StatusHistoryModel.recorded_at)
                    .all())
        finally:
            session.close()

    def _all_workstations(self) -> List[WorkstationModel]:
        session = self._session()
        try:
            return session.query(WorkstationModel).order_by(WorkstationModel.name).all()
        finally:
            session.close()

    # ─── Occupancy summary ───────────────────────────────────────
    def _occupancy_stats(self, rows: List[StatusHistoryModel]) -> Dict[str, Any]:
        """Count records per status for the given history slice."""
        totals: Dict[str, int] = defaultdict(int)
        power_sum = 0.0
        for r in rows:
            totals[r.status] += 1
            power_sum += r.power_consumption or 0.0

        total = len(rows) or 1
        return {
            "total_records":    total,
            "in_use_pct":       round(totals.get("in_use", 0)       / total * 100, 1),
            "idle_pct":         round(totals.get("idle", 0)         / total * 100, 1),
            "available_pct":    round(totals.get("available", 0)    / total * 100, 1),
            "maintenance_pct":  round(totals.get("maintenance", 0)  / total * 100, 1),
            "disconnected_pct": round(totals.get("disconnected", 0) / total * 100, 1),
            "avg_power_w":      round(power_sum / total, 2),
            "raw_counts":       dict(totals),
        }

    # ─── Daily report ────────────────────────────────────────────
    def daily_report(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        d     = target_date or date.today()
        since = datetime(d.year, d.month, d.day, 0, 0, 0)
        until = since + timedelta(days=1) - timedelta(seconds=1)
        rows  = self._history_in_range(since, until)

        # Per-hour buckets
        hourly: Dict[int, Dict[str, int]] = {h: defaultdict(int) for h in range(24)}
        for r in rows:
            hour = r.recorded_at.hour
            hourly[hour][r.status] += 1

        hourly_in_use = [hourly[h].get("in_use", 0) for h in range(24)]
        hourly_labels = [f"{h:02d}:00" for h in range(24)]

        return {
            "period":       "daily",
            "date":         d.isoformat(),
            "label":        d.strftime("%B %d, %Y"),
            "stats":        self._occupancy_stats(rows),
            "chart_labels": hourly_labels,
            "chart_values": hourly_in_use,
            "chart_title":  "In-Use Records per Hour",
            "per_workstation": self._per_workstation_stats(rows),
        }

    # ─── Weekly report ───────────────────────────────────────────
    def weekly_report(self, week_start: Optional[date] = None) -> Dict[str, Any]:
        today  = date.today()
        start  = week_start or (today - timedelta(days=today.weekday()))
        end    = start + timedelta(days=6)
        since  = datetime(start.year, start.month, start.day, 0, 0, 0)
        until  = datetime(end.year, end.month, end.day, 23, 59, 59)
        rows   = self._history_in_range(since, until)

        # Per-day buckets
        daily: Dict[date, Dict[str, int]] = {}
        for i in range(7):
            daily[start + timedelta(days=i)] = defaultdict(int)
        for r in rows:
            day = r.recorded_at.date()
            if day in daily:
                daily[day][r.status] += 1

        labels = [(start + timedelta(days=i)).strftime("%a %d") for i in range(7)]
        values = [daily[start + timedelta(days=i)].get("in_use", 0) for i in range(7)]

        return {
            "period":       "weekly",
            "date":         start.isoformat(),
            "label":        f"Week of {start.strftime('%B %d, %Y')}",
            "stats":        self._occupancy_stats(rows),
            "chart_labels": labels,
            "chart_values": values,
            "chart_title":  "In-Use Records per Day",
            "per_workstation": self._per_workstation_stats(rows),
        }

    # ─── Monthly report ──────────────────────────────────────────
    def monthly_report(self, year: Optional[int] = None,
                        month: Optional[int] = None) -> Dict[str, Any]:
        today = date.today()
        y     = year  or today.year
        m     = month or today.month
        start = date(y, m, 1)
        # Last day of month
        if m == 12:
            end = date(y + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(y, m + 1, 1) - timedelta(days=1)

        since = datetime(start.year, start.month, start.day, 0, 0, 0)
        until = datetime(end.year, end.month, end.day, 23, 59, 59)
        rows  = self._history_in_range(since, until)

        # Per-day buckets for chart
        num_days = (end - start).days + 1
        daily: Dict[date, Dict[str, int]] = {
            start + timedelta(days=i): defaultdict(int) for i in range(num_days)
        }
        for r in rows:
            d = r.recorded_at.date()
            if d in daily:
                daily[d][r.status] += 1

        labels = [(start + timedelta(days=i)).strftime("%d") for i in range(num_days)]
        values = [daily[start + timedelta(days=i)].get("in_use", 0)
                  for i in range(num_days)]

        return {
            "period":       "monthly",
            "date":         start.isoformat(),
            "label":        start.strftime("%B %Y"),
            "stats":        self._occupancy_stats(rows),
            "chart_labels": labels,
            "chart_values": values,
            "chart_title":  f"In-Use Records per Day — {start.strftime('%B %Y')}",
            "per_workstation": self._per_workstation_stats(rows),
        }

    # ─── Per-workstation breakdown ───────────────────────────────
    def _per_workstation_stats(self, rows: List[StatusHistoryModel]) -> List[Dict]:
        by_ws: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in rows:
            by_ws[r.workstation_id][r.status] += 1

        ws_map = {w.id: w.name for w in self._all_workstations()}
        result = []
        for ws_id, counts in sorted(by_ws.items(), key=lambda x: ws_map.get(x[0], "")):
            total = sum(counts.values()) or 1
            result.append({
                "id":         ws_id,
                "name":       ws_map.get(ws_id, f"#{ws_id}"),
                "in_use_pct": round(counts.get("in_use", 0) / total * 100, 1),
                "idle_pct":   round(counts.get("idle", 0)   / total * 100, 1),
                "avail_pct":  round(counts.get("available", 0) / total * 100, 1),
                "total":      total,
            })
        return result

    # ─── Quick summary (used by dashboard header) ─────────────────
    def today_summary(self) -> Dict[str, Any]:
        return self.daily_report()["stats"]
