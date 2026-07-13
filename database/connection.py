"""
Database Connection Manager
Manages SQLAlchemy engine and session lifecycle.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from typing import Optional, Generator
from database.models.base import Base

# Import all models so they are registered with Base.metadata
from database.models.workstation_model        import WorkstationModel       # noqa: F401
from database.models.device_mapping_model     import DeviceMappingModel     # noqa: F401
from database.models.status_history_model     import StatusHistoryModel     # noqa: F401
from database.models.layout_pin_model         import LayoutPinModel         # noqa: F401
from database.models.battery_automation_model import BatteryAutomationModel # noqa: F401
from database.models.user_model               import UserModel              # noqa: F401
from database.models.audit_log_model          import AuditLogModel          # noqa: F401

APP_DIR = Path.home() / ".labview"
APP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DIR / "labview.db"


class DatabaseManager:
    """Singleton database manager."""

    _instance: Optional["DatabaseManager"] = None

    def __init__(self) -> None:
        self.engine       = None
        self.SessionLocal = None

    @classmethod
    def instance(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self) -> None:
        """Create engine, session factory, and all tables."""
        db_url = f"sqlite:///{DB_PATH}"
        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        # Enable WAL mode for better concurrent read performance
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.commit()

        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Return a new session. Caller is responsible for closing."""
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.SessionLocal()

    def get_db(self) -> Generator[Session, None, None]:
        """Context manager style session for use in services."""
        session = self.get_session()
        try:
            yield session
        finally:
            session.close()
