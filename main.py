"""
LabView — Entry Point
Initializes logging, database, and the PySide6 application window.
"""
import sys
from pathlib import Path

# Ensure project root is importable regardless of working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from loguru import logger
from PySide6.QtWidgets import QApplication
from PySide6.QtCore    import Qt


def _setup_logging() -> None:
    log_dir = Path.home() / ".labview" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()  # Remove default stderr handler
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
        colorize=True,
    )
    logger.add(
        str(log_dir / "labview_{time:YYYY-MM-DD}.log"),
        rotation="1 day",
        retention="14 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}",
        encoding="utf-8",
    )


def main() -> None:
    _setup_logging()
    logger.info("=" * 50)
    logger.info("LabView v0.8.0-beta  starting up")
    logger.info("=" * 50)

    # ── Qt Application ──
    app = QApplication(sys.argv)
    app.setApplicationName("LabView")
    app.setApplicationVersion("0.8.0-beta")
    app.setOrganizationName("LabView")
    app.setOrganizationDomain("labview.local")

    # ── Database ──
    logger.info("Initializing database …")
    from database.connection import DatabaseManager
    db = DatabaseManager.instance()
    db.initialize()
    logger.info("Database ready.")

    # ── Main Window ──
    logger.info("Launching main window …")
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    logger.info("Application running.")
    exit_code = app.exec()
    logger.info(f"Application exited with code {exit_code}.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
