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
#     lives in the architecture-approved machine scope (not a user profile or CWD). FINSIGHT_SMOKE
#     launches+exits for packaging verification. Deterministic core + Ask Fin degrade honestly with
#     no AI provider.
from __future__ import annotations
import os
import sys
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finsight.app import (
    AuthorizationConfigurationError,
    acquire_single_instance,
    authorization_configuration_preflight,
    build_private_ask_fin_backend,
    build_query_services,
    prepare_local_identity,
    qualified_machine_runtime_paths,
)
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import AppearanceManager
from finsight.delivery.desktop.theme import tokens as t
from finsight.delivery.desktop.views.review_management_view import WELCOME_TITLE
from finsight.diagnostics import configure_logging, get_logger

_log = get_logger("ui.app")


def default_db_path() -> str:
    """Machine-scoped authoritative store shared by sequential approved actors."""
    return qualified_machine_runtime_paths().store_path


def resolve_db_path(db_path: Optional[str] = None) -> str:
    # Tests/developer tools may inject an explicit path through this Python API.
    # Production startup never accepts a user-controlled process-environment redirect.
    return db_path or default_db_path()


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
    appearance_manager = AppearanceManager(qapp, parent=qapp)
    qapp.aboutToQuit.connect(appearance_manager.dispose)

    db = resolve_db_path(db_path)
    registry_root = (
        None
        if db_path is not None
        else qualified_machine_runtime_paths().disposal_registry_root
    )
    identity = prepare_local_identity()
    if not identity.resolution.is_resolved:
        _log.error("protected review storage remains locked: stable actor identity is unresolved")
        return _run_restricted_window(
            qapp,
            "FinSight could not verify a stable operating-system account. Review data remains "
            "locked, and protected storage was not opened. Sign in with a supported account and "
            "restart FinSight.",
        )
    try:
        authorization_configuration_preflight()
    except AuthorizationConfigurationError:
        _log.error("protected review storage remains locked: role manifest is unavailable")
        return _run_restricted_window(
            qapp,
            "FinSight could not verify administrator-provisioned role assignments. Review data "
            "remains locked, and protected storage was not opened. Contact your FinSight "
            "administrator.",
        )

    # Single-instance protection (ADR-013 §3): refuse a second instance on the same database WITHOUT
    # opening or modifying it. Advisory OS lock; auto-recovers from a crashed instance's stale lock.
    try:
        lock = acquire_single_instance(db)
    except OSError:
        _log.error(
            "protected review storage remains locked: machine store is not provisioned"
        )
        return _run_restricted_window(
            qapp,
            "FinSight could not access its administrator-provisioned machine workspace. "
            "Review data remains locked, and protected storage was not opened. Contact your "
            "FinSight administrator.",
        )
    if lock is None:
        _log.error("refusing second instance: database already in use: %s", db)
        _refuse_second_instance(db)
        appearance_manager.dispose()
        return 1

    try:
        try:
            services = build_query_services(
                db,
                identity_provider=identity.provider,
                registry_root=registry_root,
            )
        except PermissionError:
            _log.error("protected review storage remains locked: actor identity changed")
            return _run_restricted_window(
                qapp,
                "FinSight could no longer verify the operating-system account. Review data "
                "remains locked. Restart FinSight after confirming your signed-in account.",
            )
        ask_fin_backend = build_private_ask_fin_backend(
            db,
            identity_provider=identity.provider,
            registry_root=registry_root,
        )
        return _run_window(
            qapp,
            services,
            appearance_manager,
            ask_fin_backend=ask_fin_backend,
        )
    finally:
        lock.release()
        appearance_manager.dispose()


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


def _run_window(
    qapp, services, appearance_manager, *, ask_fin_backend=None
) -> int:
    from finsight.delivery.desktop.controllers import AppController
    window = MainWindow(
        AppController(services, ask_fin_backend=ask_fin_backend),
        appearance_manager=appearance_manager,
    )
    window.show()
    # Packaging/clean-environment launch smoke: start, render one event cycle, then exit cleanly.
    # Proves the packaged app launches + composes the window without a human at the display.
    if os.environ.get("FINSIGHT_SMOKE"):
        from PySide6.QtCore import QTimer
        _log.info("smoke launch: window shown, exiting cleanly")
        QTimer.singleShot(0, qapp.quit)
    return qapp.exec()


def _run_restricted_window(qapp, reason: str) -> int:
    """Show only a non-sensitive shell when a stable OS actor cannot be established."""

    window = QMainWindow()
    window.setWindowTitle("FinSight — Access Locked")
    window.resize(900, 560)
    holder = QWidget()
    outer = QHBoxLayout(holder)
    outer.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
    outer.addStretch(1)
    card = QWidget()
    card.setProperty("role", "card")
    card.setMaximumWidth(700)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(t.SP_6, t.SP_6, t.SP_6, t.SP_6)
    layout.setSpacing(t.SP_3)
    title = QLabel(WELCOME_TITLE)
    title.setProperty("role", "sectionHeader")
    title.setWordWrap(True)
    title.setAccessibleName(WELCOME_TITLE)
    layout.addWidget(title)
    message = QLabel(reason)
    message.setProperty("role", "error")
    message.setWordWrap(True)
    message.setAccessibleName("Identity verification failed. Review data remains locked.")
    layout.addWidget(message)
    create = QPushButton("Create New Review")
    create.setEnabled(False)
    create.setAccessibleName("Create New Review unavailable")
    create.setAccessibleDescription("Unavailable until FinSight can verify your account.")
    layout.addWidget(create)
    past = QPushButton("View Past Reviews")
    past.setEnabled(False)
    past.setAccessibleName("View Past Reviews unavailable")
    past.setAccessibleDescription("Unavailable until FinSight can verify your account.")
    layout.addWidget(past)
    layout.addStretch(1)
    outer.addWidget(card, 1)
    outer.addStretch(1)
    window.setCentralWidget(holder)
    window.show()
    if os.environ.get("FINSIGHT_SMOKE"):
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, qapp.quit)
    return qapp.exec()


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
