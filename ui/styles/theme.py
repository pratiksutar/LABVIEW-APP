"""
LabView Dark Theme
Complete Qt stylesheet for a modern dark UI.
"""

DARK_THEME = """
/* ── Global ───────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #1A1A2E;
    color: #E2E8F0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background: #1A1A2E;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #4A4A6A;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #6B6B9B; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #1A1A2E;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #4A4A6A;
    border-radius: 4px;
}

/* ── Sidebar ──────────────────────────────────────────── */
QWidget#sidebar {
    background-color: #0F0F1E;
    border-right: 1px solid #2D2D4A;
}

QLabel#appTitle {
    color: #A78BFA;
    font-size: 18px;
    font-weight: bold;
    padding: 4px 0;
}

QLabel#appVersion {
    color: #4B5563;
    font-size: 11px;
}

/* ── Nav Buttons ──────────────────────────────────────── */
QPushButton#navBtn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    padding: 12px 20px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#navBtn:hover {
    background-color: #1E1E3A;
    color: #CBD5E1;
    border-left-color: #4A4A7A;
}
QPushButton#navBtn:checked {
    background-color: #1E1E3A;
    color: #A78BFA;
    border-left-color: #7C3AED;
    font-weight: 600;
}

/* ── Content area ─────────────────────────────────────── */
QWidget#contentArea {
    background-color: #1A1A2E;
}

QWidget#pageHeader {
    background-color: #1A1A2E;
    border-bottom: 1px solid #2D2D4A;
}

QLabel#pageTitle {
    font-size: 22px;
    font-weight: bold;
    color: #E2E8F0;
}

QLabel#pageSubtitle {
    font-size: 12px;
    color: #6B7280;
}

/* ── Summary Cards ────────────────────────────────────── */
QFrame#summaryCard {
    background-color: #22223A;
    border: 1px solid #2D2D4A;
    border-radius: 10px;
}

QLabel#cardValue {
    font-size: 28px;
    font-weight: bold;
    color: #E2E8F0;
}

QLabel#cardLabel {
    font-size: 12px;
    color: #9CA3AF;
}

/* ── Workstation Cards ────────────────────────────────── */
QFrame#wsCard {
    background-color: #22223A;
    border: 1px solid #2D2D4A;
    border-radius: 12px;
    padding: 4px;
}
QFrame#wsCard:hover {
    border-color: #4A4A7A;
}

QLabel#wsName {
    font-size: 15px;
    font-weight: 600;
    color: #E2E8F0;
}

QLabel#wsArea {
    font-size: 11px;
    color: #6B7280;
}

QLabel#wsStatus {
    font-size: 12px;
    font-weight: 500;
}

QLabel#wsPower {
    font-size: 12px;
    color: #9CA3AF;
}

/* ── Buttons ──────────────────────────────────────────── */
QPushButton {
    background-color: #7C3AED;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
}
QPushButton:hover    { background-color: #6D28D9; }
QPushButton:pressed  { background-color: #5B21B6; }
QPushButton:disabled { background-color: #374151; color: #6B7280; }

QPushButton#btnSecondary {
    background-color: #2D2D4A;
    color: #CBD5E1;
}
QPushButton#btnSecondary:hover { background-color: #3D3D5A; }

QPushButton#btnDanger {
    background-color: #DC2626;
    color: white;
}
QPushButton#btnDanger:hover { background-color: #B91C1C; }

QPushButton#btnSuccess {
    background-color: #059669;
    color: white;
}
QPushButton#btnSuccess:hover { background-color: #047857; }

QPushButton#btnSmall {
    padding: 4px 10px;
    font-size: 11px;
    border-radius: 4px;
}

/* ── Table ────────────────────────────────────────────── */
QTableWidget {
    background-color: #22223A;
    gridline-color: #2D2D4A;
    border: 1px solid #2D2D4A;
    border-radius: 8px;
    selection-background-color: #3D2D7A;
    alternate-background-color: #1E1E36;
}
QTableWidget::item {
    padding: 8px 12px;
    border: none;
}
QTableWidget::item:selected {
    background-color: #3D2D7A;
    color: #E2E8F0;
}
QHeaderView::section {
    background-color: #1A1A2E;
    color: #9CA3AF;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid #2D2D4A;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
}

/* ── Inputs ───────────────────────────────────────────── */
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background-color: #1A1A2E;
    color: #E2E8F0;
    border: 1px solid #3D3D5A;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #7C3AED;
    outline: none;
}
QLineEdit::placeholder { color: #4B5563; }

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #22223A;
    border: 1px solid #3D3D5A;
    selection-background-color: #3D2D7A;
}

/* ── Labels ───────────────────────────────────────────── */
QLabel#fieldLabel {
    color: #9CA3AF;
    font-size: 12px;
    font-weight: 500;
}

QLabel#sectionTitle {
    color: #A78BFA;
    font-size: 14px;
    font-weight: 600;
}

/* ── Dialog ───────────────────────────────────────────── */
QDialog {
    background-color: #1A1A2E;
    border: 1px solid #3D3D5A;
    border-radius: 12px;
}

/* ── Status Bar ───────────────────────────────────────── */
QStatusBar {
    background-color: #0F0F1E;
    color: #6B7280;
    border-top: 1px solid #2D2D4A;
    font-size: 12px;
}

/* ── Separator ────────────────────────────────────────── */
QFrame[frameShape="4"],   /* HLine */
QFrame[frameShape="5"] {  /* VLine */
    color: #2D2D4A;
}

/* ── CheckBox ─────────────────────────────────────────── */
QCheckBox {
    color: #CBD5E1;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 2px solid #4A4A7A;
    border-radius: 3px;
    background: #1A1A2E;
}
QCheckBox::indicator:checked {
    background-color: #7C3AED;
    border-color: #7C3AED;
}

/* ── ToolTip ──────────────────────────────────────────── */
QToolTip {
    background-color: #22223A;
    color: #E2E8F0;
    border: 1px solid #4A4A7A;
    border-radius: 4px;
    padding: 4px 8px;
}
"""


STATUS_COLORS = {
    "available":    "#10B981",
    "idle":         "#F59E0B",
    "in_use":       "#3B82F6",
    "disconnected": "#6B7280",
    "maintenance":  "#F97316",
    "failure":      "#EF4444",
}
