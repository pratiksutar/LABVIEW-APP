================================================================================
  LABVIEW  v0.8.0-beta
  Laboratory Workstation Monitoring & Management Platform
================================================================================

OVERVIEW
--------
LabView is a Python desktop application for real-time laboratory workstation
occupancy monitoring. It integrates with SwitchBot Plug Mini devices via the
SwitchBot Cloud API to track power usage and derive workstation status
(Available, Idle, In Use, Maintenance, Disconnected, Failure).

This release adds full Audit Logging and Reporting: every action in the app is
now recorded in a filterable audit log, and a real Reports page delivers
daily/weekly/monthly utilization analytics with CSV and Excel export.

--------------------------------------------------------------------------------
PREREQUISITES
--------------------------------------------------------------------------------

  • Python 3.12 or newer         https://www.python.org/downloads/
  • pip (bundled with Python)
  • Windows 10/11 x64 or ARM64  (Linux/macOS supported for development)
  • A SwitchBot account with at least one Plug Mini device (optional for UI)
  • Internet access for initial dependency installation

--------------------------------------------------------------------------------
INSTALLATION
--------------------------------------------------------------------------------

1. Unzip the project:

       Unzip LabView.zip to a folder of your choice, e.g.:
       C:\Projects\LabView\

2. Open a terminal (Command Prompt or PowerShell) in that folder:

       cd C:\Projects\LabView

3. (Recommended) Create and activate a virtual environment:

       python -m venv .venv
       .venv\Scripts\activate          # Windows
       # or: source .venv/bin/activate  # macOS / Linux

4. Install dependencies:

       pip install -r requirements.txt

   If you see errors for keyring on a headless environment, install the
   fallback backend:

       pip install keyrings.alt

--------------------------------------------------------------------------------
RUNNING THE APPLICATION
--------------------------------------------------------------------------------

   python main.py

The application window will open. On first run the SQLite database is created
automatically at:

   %USERPROFILE%\.labview\labview.db     (Windows)
   ~/.labview/labview.db                  (Linux / macOS)

Log files are written to:

   %USERPROFILE%\.labview\logs\          (Windows)
   ~/.labview/logs/                       (Linux / macOS)

--------------------------------------------------------------------------------
CONFIGURING SWITCHBOT CREDENTIALS
--------------------------------------------------------------------------------

1. Open the SwitchBot mobile app.
2. Go to Profile → Preferences.
3. Tap the App Version number 10 times to reveal Developer Options.
4. Copy your API Token and API Secret.
5. In LabView, go to the Settings page.
6. Paste your Token and Secret into the respective fields.
7. Click "Test Connection" to verify.
8. Click "Save Settings".

Credentials are stored securely using the Windows Credential Manager
(keyring). A file-based fallback is used on non-Windows systems.

--------------------------------------------------------------------------------
ADDING YOUR FIRST WORKSTATION
--------------------------------------------------------------------------------

1. Navigate to Device Registry.
2. Click "Add Workstation".
3. Enter a Name (required), Area, and optional Description.
4. Paste the SwitchBot Device ID into the Device ID field.
   (Find Device IDs in Settings → Test Connection results, or via the API.)
5. Click OK.

Once credentials are configured and polling starts, the Dashboard will show
live power readings and automatically update workstation status.

--------------------------------------------------------------------------------
RUNNING TESTS
--------------------------------------------------------------------------------

   python -m pytest tests/ -v

--------------------------------------------------------------------------------
WHAT'S NEW IN v0.8.0-beta
--------------------------------------------------------------------------------

  • Audit Logging — Every Action Recorded
      All significant actions are now written to the audit_logs table:
      login/logout/failed login, workstation create/update/delete,
      device assignment and removal, ON/OFF commands, maintenance changes,
      floor plan upload/remove, pin place/remove, settings changes,
      user create/update/enable/disable, and password resets.
      The logged username is always the currently signed-in user.

  • Audit Logs Page
      A new "Audit Logs" entry in the sidebar opens a filterable,
      paginated table of all audit records. Filter by user, action type,
      and date range. Export the visible results to CSV or Excel.

  • Real Reports Page
      The placeholder Reports page is now fully functional:
        - Daily view:   hourly In-Use count bar chart + summary stats
        - Weekly view:  daily bar chart for the selected week
        - Monthly view: per-day chart for the selected month
      All views include an overall summary (In Use %, Idle %, Available %,
      Average Power W, Total Records) and a per-workstation breakdown
      table. Navigate to any month/year using the controls in the toolbar.

  • CSV & Excel Export (3 report types)
      - Workstation Status    → current live status snapshot
      - Utilization Report    → daily/weekly/monthly stats + chart data
      - Audit Log             → filtered audit table
      Reports are saved to: ~/.labview/reports/

  • 7-Page Navigation
      The sidebar now has 7 entries: Dashboard, Device Registry, Lab
      Layout, Reports, Audit Logs, Settings, Users (admin only).

--------------------------------------------------------------------------------
WHAT'S NEW IN v0.7.0-beta (previous release)
--------------------------------------------------------------------------------

  • Login screen, first-run admin bootstrap, three RBAC roles
    (Viewer/Operator/Administrator), User Management page (admin only),
    session auto-logout after 30 min inactivity, permission gating
    across all pages.

--------------------------------------------------------------------------------
QUICK USAGE NOTES
--------------------------------------------------------------------------------

  1. On first launch, create your administrator account when prompted.
  2. Go to Settings, paste your SwitchBot Token and Secret, and click
     Test Connection to verify. Click Save Settings.
  3. In Device Registry, click "Add Workstation", then click the 🔍 button
     next to Device ID to browse your SwitchBot devices and assign one.
  4. Go to Lab Layout, upload a floor plan image, and double-click
     workstations in the sidebar to place their pins on the map.
  5. To create additional users, go to Users → Add User and assign the
     appropriate role (Viewer, Operator, or Administrator).



LabView/
│
├── main.py                         ← Application entry point
├── requirements.txt
├── README.txt
│
├── config/
│   └── settings.py                 ← JSON-backed app settings (singleton)
│
├── domain/
│   ├── enums/
│   │   └── workstation_status.py   ← Status enum with color, priority, display
│   └── models/
│       ├── workstation.py          ← Workstation dataclass (pure Python)
│       ├── device_mapping.py       ← DeviceMapping dataclass
│       └── layout_pin.py           ← LayoutPin dataclass (NEW)
│
├── database/
│   ├── connection.py               ← DatabaseManager singleton (SQLAlchemy)
│   ├── models/
│   │   ├── base.py                 ← DeclarativeBase
│   │   ├── workstation_model.py    ← Workstations table
│   │   ├── device_mapping_model.py ← DeviceMappings table
│   │   ├── status_history_model.py ← StatusHistory table
│   │   ├── layout_pin_model.py     ← LayoutPins table
│   │   └── battery_automation_model.py
│   └── repositories/
│       ├── workstation_repository.py       ← CRUD for workstations
│       ├── device_mapping_repository.py    ← CRUD for device mappings
│       ├── status_history_repository.py    ← Write/read status history
│       └── layout_pin_repository.py        ← CRUD for floor plan pins (NEW)
│
├── application/
│   └── services/
│       ├── workstation_service.py  ← Business logic, live cache, history hydration
│       └── layout_service.py       ← Floor plan image + pin placement logic (NEW)
│
├── infrastructure/
│   ├── switchbot/
│   │   └── switchbot_client.py     ← HMAC-SHA256 authenticated API client
│   └── security/
│       └── credential_manager.py   ← keyring-backed credential storage
│
├── services/
│   ├── polling_service.py          ← QThread + QTimer background polling
│   └── switchbot_worker.py         ← One-shot background worker for
│                                       discovery, commands, connection test
│
├── ui/
│   ├── main_window.py              ← Main window, sidebar, page stack
│   ├── dialogs/
│   │   ├── device_discovery_dialog.py        ← Browse & select real devices
│   │   └── workstation_quick_view_dialog.py  ← Pin-click popup (NEW)
│   ├── styles/
│   │   └── theme.py                ← Complete dark theme stylesheet
│   ├── pages/
│   │   ├── dashboard_page.py       ← Live workstation grid + summary cards
│   │   ├── device_registry_page.py ← CRUD table with Add/Edit/Delete dialogs
│   │   ├── layout_page.py          ← Floor plan + draggable pins (NEW, v0.6.0)
│   │   ├── reports_page.py         ← Analytics (v0.8.0-beta placeholder)
│   │   └── settings_page.py        ← Credentials + polling + threshold config
│   └── widgets/
│       ├── workstation_card.py     ← Dashboard card with status + controls
│       ├── status_indicator.py     ← Colored circle status dot
│       ├── device_details_panel.py ← Slide-in details side panel
│       ├── floor_plan_canvas.py    ← Zoomable/pannable floor plan view (NEW)
│       └── floor_plan_pin.py       ← Draggable status-colored pin item (NEW)
│
├── reports/
│   └── report_generator.py         ← CSV and Excel export helpers
│
└── tests/
    ├── test_workstation.py         ← pytest unit tests (domain + settings)
    └── test_layout.py              ← pytest unit tests (layout pins) (NEW)

--------------------------------------------------------------------------------
DATABASE TABLES (auto-created on first run)
--------------------------------------------------------------------------------

  workstations          Core workstation registry
  device_mappings       SwitchBot device → workstation associations
  status_history        Status/power change log; used to restore last-known
                         state on startup and compute utilization reports
  layout_pins           Workstation positions on the floor plan (relative coords)
  battery_automation    Per-device charge threshold settings
  users                 Application user accounts with bcrypt passwords
  audit_logs            Full action audit trail (ACTIVE since v0.8.0)

--------------------------------------------------------------------------------
WORKSTATION STATUS LOGIC
--------------------------------------------------------------------------------

  Status          Power Reading         Priority
  ─────────────── ─────────────────── ──────────
  Maintenance     is_maintenance=True       0  (highest)
  Disconnected    API unreachable           1
  Failure         API error                 2
  In Use          ≥ 50 W                   3
  Idle            ≥ 5 W  and < 50 W        4
  Available       < 5 W                    5  (lowest)

Thresholds are configurable from the Settings page.

--------------------------------------------------------------------------------
VERSIONING ROADMAP
--------------------------------------------------------------------------------

  v0.1.0-alpha  ✅  Project skeleton, architecture, README
  v0.2.0-alpha  ✅  Database foundation (SQLAlchemy + repositories)
  v0.3.0-alpha  ✅  Core UI framework (PySide6, dark theme, navigation)
  v0.4.0-alpha  ✅  Device Registry module (CRUD, dialogs)
  v0.5.0-beta   ✅  SwitchBot integration (live discovery, real device
                     control, persistent status history)
  v0.6.0-beta   ✅  Lab Layout (floor plan upload, drag-and-drop pins,
                     zoom/pan, live status colors, click-through control)
  v0.7.0-beta   ✅  Authentication & RBAC (login, first-run bootstrap,
                     Viewer/Operator/Administrator roles, User Management
                     page, session auto-logout, full permission gating)
  v0.8.0-beta   ✅  Audit Logs & Reports (full audit trail, filterable
                     audit log page, daily/weekly/monthly utilization
                     charts, CSV and Excel export for all report types)
  v0.9.0-beta       Notifications (in-app + Windows toast alerts)
  v0.9.5-rc         Testing, performance, security review
  v1.0.0            Production release + installer

--------------------------------------------------------------------------------
TECHNOLOGY STACK
--------------------------------------------------------------------------------

  Python 3.12+    Core language
  PySide6         Qt6-based UI framework
  SQLAlchemy 2.0  ORM + repository pattern
  SQLite          Embedded local database
  httpx           Synchronous HTTP client for SwitchBot API
  loguru          Structured logging
  keyring         Secure credential storage
  openpyxl        Excel report export
  pytest          Unit testing

--------------------------------------------------------------------------------
TROUBLESHOOTING
--------------------------------------------------------------------------------

  Problem: Window does not open / black screen
  Solution: Ensure PySide6 is correctly installed.
            Try: pip install --upgrade PySide6

  Problem: "Database not initialized" error
  Solution: Make sure main.py is run from the project root folder.
            The db_manager.initialize() call in main.py must run first.

  Problem: Credentials not saving (keyring error)
  Solution: On headless/server environments install: pip install keyrings.alt
            The app will fall back to a file-based credential store.

  Problem: SwitchBot test connection fails
  Solution: Verify your Token and Secret from the SwitchBot app.
            Check your internet connection and firewall settings.
            Confirm the SwitchBot API is reachable: https://api.switch-bot.com

  Problem: Device discovery dialog shows "No devices found"
  Solution: Confirm the device is registered and online in the official
            SwitchBot app. Only devices linked to the account matching
            your API Token/Secret will appear.

  Problem: Turn ON / Turn OFF button does nothing visible
  Solution: Check the status bar at the bottom of the window for a
            success or failure message — commands run in the background
            and don't block the UI, so there's no popup on success.

  Problem: Floor plan image won't upload / shows "Upload Failed"
  Solution: Confirm the file is a valid PNG, JPG, BMP, or GIF and is not
            corrupted. Very large images (>20 MB) may take a moment to
            process — wait a few seconds and try again.

  Problem: Dragging a pin doesn't seem to save its new position
  Solution: The position saves automatically the instant you release the
            mouse button. If you drag again immediately afterward without
            releasing, only the final position is kept — this is expected.

--------------------------------------------------------------------------------
AUTHOR & LICENSE
--------------------------------------------------------------------------------

  Project : LabView
  Version : v0.1.0-alpha
  Stack   : Python + PySide6 + SQLAlchemy + SwitchBot API

  This is proprietary software for internal laboratory use.

================================================================================
