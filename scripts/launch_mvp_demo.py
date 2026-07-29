"""Launch the integrated FinSight MVP with an isolated, persistent demo store."""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from finsight.app import acquire_single_instance
from finsight.delivery.desktop.controllers import AppController
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import AppearanceManager

from workflow2_demo_support import (
    BUDGET_FIXTURE,
    GED_FIXTURE,
    build_workflow1_demo_services,
    require_approved_fixtures,
)
from workflow1_demo_support import (
    build_workflow1_demo_private_ask_fin_backend,
)


DEFAULT_STORE = REPOSITORY_ROOT / "artifacts" / "mvp-hands-on-store"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Launch the complete FinSight guided MVP with the approved synthetic "
            "Budget and GED fixtures available for hands-on testing."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_STORE,
        help=(
            "Persistent demo store. Reuse the same directory to verify close/reopen "
            "behavior (default: artifacts/mvp-hands-on-store)."
        ),
    )
    args = parser.parse_args(argv)
    require_approved_fixtures()
    data_directory = args.data_dir.resolve()
    data_directory.mkdir(parents=True, exist_ok=True)
    database = data_directory / "finsight.db"
    lock = acquire_single_instance(str(database))
    if lock is None:
        print("FinSight is already using this demo store.", file=sys.stderr)
        return 1
    try:
        services = build_workflow1_demo_services(data_directory)
        ask_fin = build_workflow1_demo_private_ask_fin_backend(
            data_directory
        )
        app = QApplication.instance() or QApplication(sys.argv[:1])
        app.setApplicationName("FinSight")
        app.setApplicationDisplayName("FinSight")
        appearance = AppearanceManager(app, parent=app)
        controller = AppController(services, ask_fin_backend=ask_fin)
        window = MainWindow(controller, appearance_manager=appearance)
        window.resize(1280, 900)
        window.show()
        if os.environ.get("FINSIGHT_SMOKE"):
            QTimer.singleShot(150, app.quit)
        print("FinSight integrated MVP developer profile")
        print(f"Budget fixture: {BUDGET_FIXTURE}")
        print(f"GED fixture: {GED_FIXTURE}")
        print(f"Persistent demo store: {data_directory}")
        return app.exec()
    finally:
        lock.release()


if __name__ == "__main__":
    raise SystemExit(main())
