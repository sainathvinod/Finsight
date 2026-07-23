# FinSight desktop entrypoint. Creates the QApplication, configures logging, applies the theme,
# wires the read-only query + workflow services through the composition root, and shows the main
# window. Contains no business logic, SQL, or repository construction.
from __future__ import annotations
import os
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication

from finsight.app import build_query_services
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import build_qss
from finsight.diagnostics import configure_logging, get_logger, app_support_dir

_log = get_logger("ui.app")


def default_db_path() -> str:
    """Per-user application database location (created on first run via migrations)."""
    return os.path.join(app_support_dir(), "finsight.db")


def resolve_db_path(db_path: Optional[str] = None) -> str:
    return db_path or os.environ.get("FINSIGHT_DB") or default_db_path()


def _install_excepthook() -> None:
    previous = sys.excepthook

    def hook(exc_type, exc, tb):
        _log.error("uncaught exception at the UI boundary: %s", exc_type.__name__,
                   exc_info=(exc_type, exc, tb))
        previous(exc_type, exc, tb)

    sys.excepthook = hook


def run(db_path: Optional[str] = None, argv: Optional[list] = None) -> int:
    configure_logging()
    _install_excepthook()
    _log.info("desktop startup")

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
