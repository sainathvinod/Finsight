"""Launch Workflow 2 with an isolated developer store and synthetic fixtures."""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from contextlib import nullcontext
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from finsight.app import acquire_single_instance
from finsight.delivery.desktop.controllers import AppController
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import build_qss

from workflow2_demo_support import (
    build_workflow1_demo_services,
    create_may_2026_intake,
    require_approved_fixtures,
    select_approved_pair,
)


def _launch(data_directory: Path, *, empty: bool) -> int:
    budget, ged = require_approved_fixtures()
    database = data_directory.resolve() / "finsight.db"
    lock = acquire_single_instance(str(database))
    if lock is None:
        print(
            "FinSight Workflow 2 is already using this demo store.",
            file=sys.stderr,
        )
        return 1
    try:
        services = build_workflow1_demo_services(data_directory.resolve())
        app = QApplication.instance() or QApplication(sys.argv[:1])
        app.setApplicationName("FinSight")
        app.setApplicationDisplayName("FinSight")
        app.setStyleSheet(build_qss(palette=app.palette()))
        controller = AppController(services, ask_fin_backend=None)
        window = MainWindow(controller)
        intake = create_may_2026_intake(window, controller)
        window.show()
        if not empty and intake.current_screen() == "upload_extraction":
            QTimer.singleShot(0, lambda: select_approved_pair(intake))
        if os.environ.get("FINSIGHT_SMOKE"):
            QTimer.singleShot(100, app.quit)
        print("Workflow 2 developer profile")
        print(f"Budget fixture: {budget}")
        print(f"GED fixture: {ged}")
        print(f"Demo store: {data_directory.resolve()}")
        return app.exec()
    finally:
        lock.release()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Launch FinSight Workflow 2 with approved synthetic fixtures. "
            "The default store is temporary and is removed after exit."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        help=(
            "Optional persistent developer-only store. Omit for a fresh temporary "
            "store that is deleted after the application closes."
        ),
    )
    parser.add_argument(
        "--empty",
        action="store_true",
        help="Open empty upload cards instead of selecting the approved fixtures.",
    )
    args = parser.parse_args(argv)

    context = (
        nullcontext(args.data_dir.resolve())
        if args.data_dir is not None
        else tempfile.TemporaryDirectory(prefix="finsight-wf2-demo-")
    )
    with context as directory:
        return _launch(Path(directory), empty=args.empty)


if __name__ == "__main__":
    raise SystemExit(main())
