"""
Reports Page
Utilization analytics: daily / weekly / monthly views,
an inline bar chart, per-workstation breakdown, and export buttons.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QComboBox, QSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QScrollArea,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui  import QPainter, QColor, QFont

from application.services.report_service import ReportService
from reports.report_generator            import ReportGenerator


# ─── Inline bar chart widget ─────────────────────────────────────
class BarChartWidget(QWidget):
    """Simple QPainter bar chart — no external chart library needed."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(180)
        self._labels: List[str] = []
        self._values: List[int] = []
        self._title  = ""
        self._color  = QColor("#7C3AED")

    def set_data(self, labels: List[str], values: List[int],
                 title: str = "", color: str = "#7C3AED") -> None:
        self._labels = labels
        self._values = values
        self._title  = title
        self._color  = QColor(color)
        self.update()

    def paintEvent(self, event) -> None:
        if not self._values:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        W, H        = self.width(), self.height()
        pad_l       = 10
        pad_r       = 10
        pad_top     = 28
        pad_bot     = 32
        chart_h     = H - pad_top - pad_bot
        chart_w     = W - pad_l - pad_r
        n           = len(self._values)
        max_val     = max(self._values) or 1
        bar_w       = max(4, chart_w // n - 2)
        spacing     = chart_w // n

        # Title
        p.setPen(QColor("#9CA3AF"))
        f = QFont("Segoe UI", 9)
        f.setBold(True)
        p.setFont(f)
        p.drawText(pad_l, 18, self._title)

        p.setFont(QFont("Segoe UI", 7))
        for i, (lbl, val) in enumerate(zip(self._labels, self._values)):
            x      = pad_l + i * spacing
            bar_h  = int((val / max_val) * chart_h)
            y      = pad_top + chart_h - bar_h

            # Bar
            p.setPen(Qt.PenStyle.NoPen)
            color = QColor(self._color)
            if val == 0:
                color.setAlpha(40)
            p.setBrush(color)
            p.drawRoundedRect(x, y, bar_w, bar_h, 2, 2)

            # Value label above bar (only if few bars)
            if n <= 31 and val > 0:
                p.setPen(QColor("#CBD5E1"))
                p.drawText(x, max(pad_top + 12, y - 2), str(val))

            # x-axis label (sparse if many bars)
            if n <= 12 or i % max(1, n // 12) == 0:
                p.setPen(QColor("#6B7280"))
                p.drawText(x, H - 8, lbl[:5])


# ─── Stat card ───────────────────────────────────────────────────
def _stat_card(value: str, label: str, color: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("summaryCard")
    frame.setFixedHeight(80)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 10, 16, 10)
    val_lbl = QLabel(value)
    val_lbl.setStyleSheet(f"font-size:24px; font-weight:bold; color:{color};")
    lbl = QLabel(label)
    lbl.setStyleSheet("font-size:11px; color:#9CA3AF;")
    lay.addWidget(val_lbl)
    lay.addWidget(lbl)
    return frame


class ReportsPage(QWidget):
    """Utilization analytics with export."""

    def __init__(self, report_service: ReportService, parent=None) -> None:
        super().__init__(parent)
        self._svc = report_service
        self._gen = ReportGenerator()
        self._current_data: Dict[str, Any] = {}
        self._build_ui()
        self._load_report("daily")

    # ─── Build ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(70)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(28, 0, 28, 0)
        h_lay.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Reports & Analytics")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Workstation utilization trends and statistics")
        subtitle.setObjectName("pageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        h_lay.addLayout(title_col)
        h_lay.addStretch()

        csv_btn = QPushButton("⬇  CSV")
        csv_btn.setFixedWidth(90)
        csv_btn.setObjectName("btnSecondary")
        csv_btn.clicked.connect(self._export_csv)
        h_lay.addWidget(csv_btn)

        xlsx_btn = QPushButton("⬇  Excel")
        xlsx_btn.setFixedWidth(100)
        xlsx_btn.setObjectName("btnSecondary")
        xlsx_btn.clicked.connect(self._export_xlsx)
        h_lay.addWidget(xlsx_btn)

        root.addWidget(header)

        # Period selector bar
        ctrl_bar = QWidget()
        ctrl_bar.setStyleSheet("background:#16162A; border-bottom:1px solid #2D2D4A;")
        c_lay = QHBoxLayout(ctrl_bar)
        c_lay.setContentsMargins(28, 8, 28, 8)
        c_lay.setSpacing(12)

        self._period_btns: List[QPushButton] = []
        for label, period in [("Daily", "daily"), ("Weekly", "weekly"), ("Monthly", "monthly")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedWidth(90)
            btn.clicked.connect(lambda _, p=period: self._load_report(p))
            self._period_btns.append(btn)
            c_lay.addWidget(btn)

        c_lay.addSpacing(20)

        # Date navigation
        c_lay.addWidget(QLabel("Month:"))
        self._month_spin = QSpinBox()
        self._month_spin.setRange(1, 12)
        self._month_spin.setValue(date.today().month)
        self._month_spin.setFixedWidth(60)
        c_lay.addWidget(self._month_spin)

        c_lay.addWidget(QLabel("Year:"))
        self._year_spin = QSpinBox()
        self._year_spin.setRange(2020, 2100)
        self._year_spin.setValue(date.today().year)
        self._year_spin.setFixedWidth(80)
        c_lay.addWidget(self._year_spin)

        go_btn = QPushButton("Go")
        go_btn.setFixedWidth(60)
        go_btn.clicked.connect(self._go_to_date)
        c_lay.addWidget(go_btn)

        c_lay.addStretch()
        self._period_label = QLabel("")
        self._period_label.setStyleSheet("color:#9CA3AF; font-size:12px;")
        c_lay.addWidget(self._period_label)

        root.addWidget(ctrl_bar)

        # Scrollable body
        body_widget = QWidget()
        body_lay = QVBoxLayout(body_widget)
        body_lay.setContentsMargins(28, 20, 28, 20)
        body_lay.setSpacing(20)

        # Summary stat cards
        self._cards_row = QHBoxLayout()
        self._cards_row.setSpacing(14)
        self._in_use_card  = _stat_card("—", "In Use %",    "#3B82F6")
        self._idle_card    = _stat_card("—", "Idle %",       "#F59E0B")
        self._avail_card   = _stat_card("—", "Available %",  "#10B981")
        self._power_card   = _stat_card("—", "Avg Power (W)","#A78BFA")
        self._total_card   = _stat_card("—", "Total Records","#6B7280")
        for c in (self._in_use_card, self._idle_card, self._avail_card,
                  self._power_card, self._total_card):
            self._cards_row.addWidget(c)
        body_lay.addLayout(self._cards_row)

        # Bar chart
        chart_label = QLabel("Occupancy Over Time")
        chart_label.setObjectName("sectionTitle")
        body_lay.addWidget(chart_label)

        self._chart = BarChartWidget()
        body_lay.addWidget(self._chart)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2D2D4A;")
        body_lay.addWidget(sep)

        # Per-workstation table
        ws_label = QLabel("Per-Workstation Breakdown")
        ws_label.setObjectName("sectionTitle")
        body_lay.addWidget(ws_label)

        self._ws_table = QTableWidget()
        self._ws_table.setColumnCount(5)
        self._ws_table.setHorizontalHeaderLabels(
            ["Workstation", "In Use %", "Idle %", "Available %", "Records"]
        )
        self._ws_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._ws_table.setAlternatingRowColors(True)
        self._ws_table.verticalHeader().setVisible(False)
        self._ws_table.setShowGrid(False)
        self._ws_table.setFixedHeight(260)

        hdr = self._ws_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 5):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        body_lay.addWidget(self._ws_table)
        body_lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(body_widget)
        root.addWidget(scroll, 1)

    # ─── Data loading ─────────────────────────────────────────────
    def _load_report(self, period: str, target_date: date | None = None) -> None:
        for btn, p in zip(self._period_btns, ["daily", "weekly", "monthly"]):
            btn.setChecked(p == period)

        d = target_date or date.today()
        if period == "daily":
            data = self._svc.daily_report(d)
        elif period == "weekly":
            data = self._svc.weekly_report(d)
        else:
            data = self._svc.monthly_report(d.year, d.month)

        self._current_data = data
        self._period_label.setText(data.get("label", ""))
        self._populate(data)

    def _go_to_date(self) -> None:
        m = self._month_spin.value()
        y = self._year_spin.value()
        period = next(
            (p for btn, p in zip(self._period_btns, ["daily", "weekly", "monthly"])
             if btn.isChecked()), "monthly"
        )
        try:
            target = date(y, m, 1)
        except ValueError:
            return
        self._load_report(period, target)

    def _populate(self, data: Dict[str, Any]) -> None:
        stats = data.get("stats", {})

        def _update_card(card, value, suffix=""):
            lbl = card.findChildren(QLabel)[0]
            lbl.setText(f"{value}{suffix}")

        _update_card(self._in_use_card,  stats.get("in_use_pct", 0),  "%")
        _update_card(self._idle_card,    stats.get("idle_pct", 0),    "%")
        _update_card(self._avail_card,   stats.get("available_pct", 0), "%")
        _update_card(self._power_card,   stats.get("avg_power_w", 0), "W")
        _update_card(self._total_card,   stats.get("total_records", 0))

        self._chart.set_data(
            labels=data.get("chart_labels", []),
            values=data.get("chart_values", []),
            title=data.get("chart_title", ""),
        )

        ws_rows = data.get("per_workstation", [])
        self._ws_table.setRowCount(len(ws_rows))

        STATUS_COLORS = {"in_use_pct": "#3B82F6", "idle_pct": "#F59E0B",
                         "avail_pct": "#10B981"}

        for row_idx, ws in enumerate(ws_rows):
            self._ws_table.setRowHeight(row_idx, 32)
            self._ws_table.setItem(row_idx, 0, QTableWidgetItem(ws["name"]))
            for col, key, color in [(1, "in_use_pct", "#3B82F6"),
                                     (2, "idle_pct",   "#F59E0B"),
                                     (3, "avail_pct",  "#10B981"),
                                     (4, "total",      "#9CA3AF")]:
                val = ws.get(key, 0)
                item = QTableWidgetItem(f"{val}%" if col < 4 else str(val))
                item.setForeground(QColor(color))
                self._ws_table.setItem(row_idx, col, item)

    def refresh(self) -> None:
        period = next(
            (p for btn, p in zip(self._period_btns, ["daily", "weekly", "monthly"])
             if btn.isChecked()), "daily"
        )
        self._load_report(period)

    # ─── Export ──────────────────────────────────────────────────
    def _export_csv(self) -> None:
        if not self._current_data:
            return
        try:
            path = self._gen.export_utilization_csv(self._current_data)
            QMessageBox.information(self, "Exported", f"Report saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    def _export_xlsx(self) -> None:
        if not self._current_data:
            return
        try:
            path = self._gen.export_utilization_xlsx(self._current_data)
            QMessageBox.information(self, "Exported", f"Report saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))
