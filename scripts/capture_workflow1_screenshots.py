"""Capture deterministic Workflow 1 desktop evidence without touching user review data."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from finsight.delivery.desktop.controllers import AppController
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import build_qss
from workflow1_demo_support import build_workflow1_demo_services


DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "initiatives"
    / "configurable-rule-engine-v2"
    / "verification"
    / "screenshots"
    / "workflow-01"
)


def _capture(app: QApplication, window: MainWindow, path: Path) -> None:
    app.processEvents()
    image = window.grab()
    if image.isNull() or not image.save(str(path), "PNG"):
        raise RuntimeError(f"Could not capture {path.name}")


def main(output_directory: str | None = None) -> int:
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("FinSight")
    app.setStyleSheet(build_qss())

    with tempfile.TemporaryDirectory(prefix="finsight-wf1-screens-") as temporary:
        services = build_workflow1_demo_services(Path(temporary))
        controller = AppController(services, ask_fin_backend=None)
        window = MainWindow(controller)
        window.resize(1180, 720)
        window.show()
        view = window.view("review_management")

        view.show_welcome()
        _capture(app, window, output / "01-welcome-empty.png")

        view.show_create()
        view._month.setCurrentIndex(view._month.findData(5))
        view._year.setText("2026")
        _capture(app, window, output / "02-create-new-review.png")

        review = controller.create_managed_review(5, 2026, "screenshot-create-request")
        view._show_review(review, "Review created and saved.")
        _capture(app, window, output / "03-review-workspace-draft.png")

        view.show_welcome()
        _capture(app, window, output / "04-welcome-with-saved-review.png")

        view.show_past()
        _capture(app, window, output / "05-past-reviews.png")
        window.close()

    print(f"Captured 5 Workflow 1 screenshots in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
