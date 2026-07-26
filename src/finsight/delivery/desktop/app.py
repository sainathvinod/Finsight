# Implements:
#   Feature: F-01-01 — Monthly Review Cycle Workspace (application shell/launch)
#   ADRs: ADR-002 (delivery layering — UI wires services, no SQL/repos); ADR-013 §3 (single-instance);
#         ADR-013 (Ollama-optional core)
#
# Product purpose / UI surface:
#   The FinSight desktop entry point (`finsight` console script / `python -m finsight`). Creates the
#   QApplication, configures logging + theme, acquires the single-instance lock, wires the query +
#   workflow + recovery + abandonment services through the composition root, and shows the main window.
#
# Trust / lifecycle constraints:
#   - No business logic, SQL, or repository construction here; delivery depends only on finsight.app.
#   - A second instance on the same database is refused WITHOUT opening it (ADR-013 §3). The database
#     lives in the per-user app-support dir (not the CWD). FINSIGHT_SMOKE launches+exits for packaging
#     verification. Deterministic core + Ask Fin degrade honestly with no AI provider.
from __future__ import annotations
import os
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication

from finsight.app import build_query_services, build_ask_fin_backend, acquire_single_instance
from finsight.delivery.desktop.main_window import MainWindow
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
    # Apply the persisted accessibility theme + zoom (§20); falls back to Light at scale 1.0.
    from finsight.delivery.desktop.theme.theming import ThemeManager
    _theme = ThemeManager()
    _theme.apply(qapp)

    db = resolve_db_path(db_path)

    # Single-instance protection (ADR-013 §3): refuse a second instance on the same database WITHOUT
    # opening or modifying it. Advisory OS lock; auto-recovers from a crashed instance's stale lock.
    lock = acquire_single_instance(db)
    if lock is None:
        _log.error("refusing second instance: database already in use: %s", db)
        _refuse_second_instance(db)
        return 1

    try:
        services = build_query_services(db)
        return _run_window(qapp, db, services, _theme)
    finally:
        lock.release()


def _refuse_second_instance(db: str) -> None:
    msg = ("FinSight is already running for this database.\n\nClose the other FinSight window and try "
           "again. Your data was not opened or changed.")
    print(msg, file=sys.stderr)                # always emit (logs/console); never lost
    # Show a modal dialog only when there is an interactive display. In headless/offscreen/smoke runs a
    # modal would block with no one to dismiss it, so we skip it there.
    headless = os.environ.get("FINSIGHT_SMOKE") or os.environ.get("QT_QPA_PLATFORM") == "offscreen"
    if headless:
        return
    try:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(None, "FinSight is already running", msg)
    except Exception:
        pass


def _run_window(qapp, db, services, theme_manager=None) -> int:
    # Ask Fin backend runs the whole pipeline off the UI thread on a worker-local SQLite connection.
    # Authorization is the fail-closed development/demo policy (FINSIGHT_AI_DEMO_AUTHORIZED) — NOT
    # production consent; provider selection follows FINSIGHT_AI_PROVIDER.
    ask_fin_backend = build_ask_fin_backend(db)
    from finsight.delivery.desktop.controllers import AppController
    window = MainWindow(AppController(services, ask_fin_backend=ask_fin_backend),
                        theme_manager=theme_manager)
    window.show()
    # Packaging/clean-environment launch smoke: start, render one event cycle, then exit cleanly.
    # Proves the packaged app launches + composes the window without a human at the display.
    if os.environ.get("FINSIGHT_SMOKE"):
        from PySide6.QtCore import QTimer
        _log.info("smoke launch: window shown, exiting cleanly")
        QTimer.singleShot(0, qapp.quit)
    return qapp.exec()


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
