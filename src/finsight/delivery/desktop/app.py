# FinSight desktop entrypoint. Creates the QApplication, applies the theme, wires the read-only
# query services through the composition root, and shows the main window. Contains no business
# logic, SQL, or repository construction.
from __future__ import annotations
import os
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication

from finsight.app import build_query_services
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import build_qss


def default_db_path() -> str:
    """Per-user application database location (created on first run via migrations)."""
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/FinSight")
    elif os.name == "nt":
        base = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "FinSight")
    else:
        base = os.path.join(os.path.expanduser("~/.local/share"), "FinSight")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "finsight.db")


def resolve_db_path(db_path: Optional[str] = None) -> str:
    return db_path or os.environ.get("FINSIGHT_DB") or default_db_path()


def run(db_path: Optional[str] = None, argv: Optional[list] = None) -> int:
    qapp = QApplication.instance() or QApplication(argv if argv is not None else sys.argv[:1])
    qapp.setApplicationName("FinSight")
    qapp.setApplicationDisplayName("FinSight")
    qapp.setStyleSheet(build_qss())

    services = build_query_services(resolve_db_path(db_path))
    from finsight.delivery.desktop.controllers import AppController
    window = MainWindow(AppController(services))
    window.show()
    return qapp.exec()


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
