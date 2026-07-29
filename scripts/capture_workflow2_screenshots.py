"""Capture deterministic Workflow 2 evidence without touching user review data."""
# ruff: noqa: E402

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from openpyxl import load_workbook
from PySide6.QtWidgets import QApplication

from finsight.delivery.desktop.controllers import AppController
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import build_qss
from finsight.domain.source_intake import SourceRole

from workflow2_demo_support import (
    BUDGET_FIXTURE,
    GED_FIXTURE,
    build_workflow1_demo_services,
    create_may_2026_intake,
    require_approved_fixtures,
)


DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "initiatives"
    / "configurable-rule-engine-v2"
    / "verification"
    / "screenshots"
    / "workflow-02"
)


def _wait(app: QApplication, predicate, description: str) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return
        time.sleep(0.01)
    raise TimeoutError(f"Timed out waiting for {description}.")


def _capture(app: QApplication, window: MainWindow, path: Path) -> None:
    app.processEvents()
    image = window.grab()
    if image.isNull() or not image.save(str(path), "PNG"):
        raise RuntimeError(f"Could not capture {path.name}")


def _new_intake(window: MainWindow, controller: AppController, ordinal: int):
    review = controller.create_managed_review(
        5,
        2026,
        f"workflow2-screenshot-create-{ordinal}",
    )
    window._show_source_intake(review)
    return window.view("source_intake")


def _select(
    app: QApplication,
    intake,
    role: SourceRole,
    path: Path,
    *,
    compatible: bool | None = None,
) -> None:
    intake.select_source_path(role, str(path))
    attribute = "_budget" if role is SourceRole.BUDGET else "_ged"
    _wait(
        app,
        lambda: getattr(intake, attribute) is not None,
        f"{role.label} extraction",
    )
    inspection = getattr(intake, attribute)
    if compatible is not None and inspection.is_compatible is not compatible:
        raise AssertionError(
            f"{path.name} compatibility was {inspection.is_compatible}, "
            f"expected {compatible}."
        )


def _select_pair(
    app: QApplication,
    intake,
    budget: Path,
    ged: Path,
) -> None:
    _select(app, intake, SourceRole.BUDGET, budget, compatible=True)
    _select(app, intake, SourceRole.GED, ged, compatible=True)
    _wait(app, lambda: intake.current_pair() is not None, "pair evaluation")


def _save_pair(app: QApplication, intake) -> None:
    if not intake._save_button.isEnabled():
        raise AssertionError("Expected the source-pair save action to be enabled.")
    intake._save_button.click()
    _wait(
        app,
        lambda: intake.current_screen() == "workspace_identity",
        "saved source metadata",
    )


def _derived_ged(
    source: Path,
    destination: Path,
    *,
    period: str | None = None,
    department_total: str | None = None,
) -> Path:
    shutil.copyfile(source, destination)
    workbook = load_workbook(destination)
    worksheet = workbook["GED"]
    if period is not None:
        worksheet["A3"] = period
    if department_total is not None:
        worksheet["A297"] = department_total
    workbook.save(destination)
    workbook.close()
    return destination


def _invalid_budget_layout(source: Path, destination: Path) -> Path:
    shutil.copyfile(source, destination)
    workbook = load_workbook(destination)
    workbook["Original Budget"].title = "Budget - Wrong Worksheet"
    workbook.save(destination)
    workbook.close()
    return destination


def main(output_directory: str | None = None) -> int:
    require_approved_fixtures()
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("FinSight")
    app.setApplicationDisplayName("FinSight")
    app.setStyleSheet(build_qss(palette=app.palette()))

    with tempfile.TemporaryDirectory(prefix="finsight-wf2-screens-") as temporary:
        temporary_path = Path(temporary)
        services = build_workflow1_demo_services(temporary_path / "store")
        controller = AppController(services, ask_fin_backend=None)
        window = MainWindow(controller)
        window.resize(1180, 720)
        window.show()

        intake = create_may_2026_intake(window, controller)
        _capture(app, window, output / "01-upload-empty.png")

        _select(
            app,
            intake,
            SourceRole.BUDGET,
            BUDGET_FIXTURE,
            compatible=True,
        )
        _capture(app, window, output / "02-budget-extracted.png")

        _select(
            app,
            intake,
            SourceRole.GED,
            GED_FIXTURE,
            compatible=True,
        )
        _wait(app, lambda: intake.current_pair() is not None, "approved pair")
        _capture(app, window, output / "03-both-extracted.png")

        _save_pair(app, intake)
        _capture(app, window, output / "04-metadata-matched.png")

        invalid_type = temporary_path / "Budget_Report.xls"
        shutil.copyfile(BUDGET_FIXTURE, invalid_type)
        intake = _new_intake(window, controller, 2)
        _select(
            app,
            intake,
            SourceRole.BUDGET,
            invalid_type,
            compatible=False,
        )
        _select(
            app,
            intake,
            SourceRole.GED,
            GED_FIXTURE,
            compatible=True,
        )
        _capture(app, window, output / "05-file-type-error.png")

        invalid_layout = _invalid_budget_layout(
            BUDGET_FIXTURE,
            temporary_path / "Budget_Wrong_Worksheet.xlsx",
        )
        intake = _new_intake(window, controller, 3)
        _select(
            app,
            intake,
            SourceRole.BUDGET,
            invalid_layout,
            compatible=False,
        )
        _select(
            app,
            intake,
            SourceRole.GED,
            GED_FIXTURE,
            compatible=True,
        )
        _capture(app, window, output / "06-layout-error.png")

        period_mismatch = _derived_ged(
            GED_FIXTURE,
            temporary_path / "GED_April_2026.xlsx",
            period="Year-To-Date for Period April 2026",
        )
        intake = _new_intake(window, controller, 4)
        _select_pair(app, intake, BUDGET_FIXTURE, period_mismatch)
        _save_pair(app, intake)
        _capture(app, window, output / "07-reporting-period-mismatch.png")

        department_mismatch = _derived_ged(
            GED_FIXTURE,
            temporary_path / "GED_Department_0099.xlsx",
            department_total="TOTAL FOR DEPARTMENT -  00-0099",
        )
        intake = _new_intake(window, controller, 5)
        _select_pair(app, intake, BUDGET_FIXTURE, department_mismatch)
        _save_pair(app, intake)
        _capture(app, window, output / "08-department-mismatch.png")
        window.close()

    print(f"Captured 8 Workflow 2 screenshots in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
