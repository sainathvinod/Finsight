"""Launch the completed Workflow 1 increment with a persistent developer store."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from finsight.app import acquire_single_instance
from finsight.delivery.desktop.controllers import AppController
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import build_qss

from workflow1_demo_support import build_workflow1_demo_services


DEFAULT_DATA = Path(__file__).resolve().parents[1] / "artifacts" / "workflow1-demo"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Launch the developer-only FinSight Workflow 1 increment."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA,
        help="Persistent encrypted demo-store directory.",
    )
    args = parser.parse_args(argv)
    database = args.data_dir.resolve() / "finsight.db"
    lock = acquire_single_instance(str(database))
    if lock is None:
        print(
            "FinSight Workflow 1 is already using this demo store.",
            file=sys.stderr,
        )
        return 1
    try:
        services = build_workflow1_demo_services(args.data_dir.resolve())
        app = QApplication.instance() or QApplication(sys.argv[:1])
        app.setApplicationName("FinSight")
        app.setApplicationDisplayName("FinSight")
        app.setStyleSheet(build_qss(palette=app.palette()))
        window = MainWindow(AppController(services, ask_fin_backend=None))
        window.show()
        if os.environ.get("FINSIGHT_SMOKE"):
            QTimer.singleShot(0, app.quit)
        return app.exec()
    finally:
        lock.release()


if __name__ == "__main__":
    raise SystemExit(main())
