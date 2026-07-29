"""Capture the Stage 2 Financial Review experience in Light and Dark modes.

The capture harness creates a fresh May 2026 review from the approved synthetic
Budget and GED workbooks, runs the real deterministic validation pipeline, and
then records the five primary results views and the Financial Analysis
drill-downs.  It never substitutes screenshot-only financial values.
"""
# ruff: noqa: E402

from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path
import sys
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from PySide6.QtCore import QPoint, QSettings, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QScrollArea, QWidget

from finsight.delivery.desktop.controllers import AppController
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import (
    AppearanceManager,
    AppearanceMode,
    AppearanceSettings,
)
from finsight.domain.source_intake import SourceRole

from workflow1_demo_support import (
    build_workflow1_demo_private_ask_fin_backend,
    build_workflow1_demo_services,
)
from workflow2_demo_support import (
    BUDGET_FIXTURE,
    GED_FIXTURE,
    require_approved_fixtures,
)


DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "initiatives"
    / "configurable-rule-engine-v2"
    / "verification"
    / "screenshots"
    / "stage2"
)
WINDOW_SIZE = (
    int(os.environ.get("FINSIGHT_STAGE2_CAPTURE_WIDTH", "1440")),
    int(os.environ.get("FINSIGHT_STAGE2_CAPTURE_HEIGHT", "960")),
)
MODES = (AppearanceMode.LIGHT, AppearanceMode.DARK)


def _wait(
    app: QApplication,
    predicate: Callable[[], bool],
    description: str,
    *,
    timeout: float = 60.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return
        QTest.qWait(10)
    raise TimeoutError(f"Timed out waiting for {description}.")


def _settle(app: QApplication) -> None:
    for _iteration in range(6):
        app.processEvents()
        QTest.qWait(30)


def _save_window(
    app: QApplication,
    window: MainWindow,
    path: Path,
) -> None:
    _settle(app)
    image = window.grab()
    if image.isNull() or image.width() < 1000 or image.height() < 600:
        raise RuntimeError(
            f"Could not capture a desktop-sized image for {path.name}."
        )
    if not image.save(str(path), "PNG"):
        raise RuntimeError(f"Could not capture {path.name}.")


def _save_dialog_composite(
    app: QApplication,
    window: MainWindow,
    dialog: QDialog,
    path: Path,
) -> None:
    """Composite a modeless tool dialog over the offscreen main window."""

    _settle(app)
    base = window.grab()
    overlay = dialog.grab()
    if base.isNull() or overlay.isNull():
        raise RuntimeError(f"Could not capture {path.name}.")
    painter = QPainter(base)
    painter.drawPixmap(
        max(0, base.width() - overlay.width() - 18),
        max(0, (base.height() - overlay.height()) // 2),
        overlay,
    )
    painter.end()
    if not base.save(str(path), "PNG"):
        raise RuntimeError(f"Could not capture {path.name}.")


class _CaptureSession:
    def __init__(
        self,
        app: QApplication,
        window: MainWindow,
        appearance: AppearanceManager,
        output: Path,
    ):
        self.app = app
        self.window = window
        self.appearance = appearance
        self.output = output
        self.paths: list[Path] = []
        for mode in MODES:
            (output / mode.value).mkdir(parents=True, exist_ok=True)

    def screen(self, name: str) -> None:
        for mode in MODES:
            self.appearance.set_mode(mode)
            path = self.output / mode.value / f"{name}.png"
            _save_window(self.app, self.window, path)
            self.paths.append(path.resolve())
        self.appearance.set_mode(AppearanceMode.LIGHT)

    def dialog(self, name: str, dialog: QDialog) -> None:
        for mode in MODES:
            self.appearance.set_mode(mode)
            path = self.output / mode.value / f"{name}.png"
            _save_dialog_composite(
                self.app,
                self.window,
                dialog,
                path,
            )
            self.paths.append(path.resolve())
        self.appearance.set_mode(AppearanceMode.LIGHT)


def _accept_next_modal(app: QApplication) -> None:
    def accept_when_ready() -> None:
        dialog = app.activeModalWidget()
        if not isinstance(dialog, QDialog):
            QTimer.singleShot(20, accept_when_ready)
            return
        dialog.accept()

    QTimer.singleShot(20, accept_when_ready)


def _active_scroll_area(financial) -> QScrollArea:
    page = financial._stack.currentWidget()
    scroll = (
        page
        if isinstance(page, QScrollArea)
        else (page.findChild(QScrollArea) if page is not None else None)
    )
    if not isinstance(scroll, QScrollArea):
        raise RuntimeError("The Financial Review scroll surface was not found.")
    return scroll


def _scroll_to_top(app: QApplication, financial) -> None:
    _active_scroll_area(financial).verticalScrollBar().setValue(0)
    _settle(app)


def _scroll_to_widget(
    app: QApplication,
    financial,
    widget: QWidget,
    *,
    top_offset: int = 120,
) -> None:
    scroll = _active_scroll_area(financial)
    content = scroll.widget()
    if content is None:
        raise RuntimeError("The Financial Review scroll content was not found.")
    position = widget.mapTo(content, QPoint(0, 0))
    bar = scroll.verticalScrollBar()
    bar.setValue(
        max(
            bar.minimum(),
            min(bar.maximum(), position.y() - top_offset),
        )
    )
    _settle(app)


def _open_results_view(app: QApplication, financial, widget: QWidget) -> None:
    financial._open_results_tab(widget)
    _scroll_to_top(app, financial)


def _select_first_finding(app: QApplication, financial) -> None:
    financial._open_results_tab(financial._finding_list_tab)
    financial._finding_sections.setCurrentWidget(financial._finding_list_tab)
    financial._findings_search.clear()
    financial._findings_severity.setCurrentText("All severities")
    financial._findings_rule.setCurrentText("CORE-01")
    financial._findings_status.setCurrentIndex(0)
    _wait(
        app,
        lambda: financial._findings_proxy.rowCount() > 0,
        "a deterministic CORE-01 finding",
    )
    financial._findings_result_table.selectRow(0)
    financial._show_finding_detail(
        financial._findings_proxy.index(0, 0),
        financial._findings_proxy.index(-1, -1),
    )


def _create_validated_may_review(
    app: QApplication,
    window: MainWindow,
    capture: _CaptureSession,
):
    window.show_review_management()
    management = window.view("review_management")
    capture.screen("00-home")
    management.show_create()
    management._month.setCurrentIndex(management._month.findData(5))
    management._year.setText("2026")
    capture.screen("00a-create-review")
    management._create_submit.click()
    _wait(
        app,
        lambda: window.current_view_key() == "upload_extraction",
        "Upload Reports",
    )

    intake = window.view("source_intake")
    capture.screen("00b-upload-empty")
    intake.select_source_path(SourceRole.BUDGET, str(BUDGET_FIXTURE))
    _wait(app, lambda: intake._budget is not None, "Budget extraction")
    intake.select_source_path(SourceRole.GED, str(GED_FIXTURE))
    _wait(app, lambda: intake._ged is not None, "GED extraction")
    _wait(app, lambda: intake.current_pair() is not None, "source-pair match")
    capture.screen("00c-upload-complete")
    intake._save_button.click()
    _wait(
        app,
        lambda: window.current_view_key()
        in {"financial_processing", "verify_data"},
        "review-local data preparation or Verify Data",
    )
    financial = window.view("financial_review")
    if window.current_view_key() == "financial_processing":
        financial._process_timer.stop()
        capture.screen("00d-processing")
        financial._process_timer.start()
    _wait(
        app,
        lambda: window.current_view_key() == "verify_data",
        "Verify Data",
    )

    financial._data_tabs.setCurrentIndex(0)
    capture.screen("00e-verify-budget")
    financial._data_tabs.setCurrentIndex(1)
    capture.screen("00f-verify-ged")
    financial._data_tabs.setCurrentIndex(0)

    financial._show_ask_fin()
    _wait(
        app,
        lambda: (
            hasattr(financial, "_private_ask_fin_dialog")
            and financial._private_ask_fin_dialog.isVisible()
        ),
        "the pre-validation private Ask Fin panel",
    )
    help_dialog = financial._private_ask_fin_dialog
    _wait(
        app,
        lambda: help_dialog._mode.text() in {"Help Mode", "Unavailable"},
        "private Ask Fin Help Mode",
    )
    capture.dialog("00g-private-ask-fin-help-mode", help_dialog)
    help_dialog.close()

    financial._attestation.setChecked(True)
    _accept_next_modal(app)
    financial._open_confirmation()
    _wait(
        app,
        lambda: window.current_view_key() == "rules_repository",
        "Rules Repository",
    )
    capture.screen("00h-review-rules")
    window.view("rules_repository")._continue()
    _wait(
        app,
        lambda: window.current_view_key() == "validation_progress",
        "validation progress",
    )
    financial._validation_timer.stop()
    capture.screen("00i-validation-progress")
    financial._validation_timer.start()
    _wait(
        app,
        lambda: window.current_view_key() == "financial_review_results",
        "Financial Review results",
        timeout=90,
    )
    return financial


def main(output_directory: str | None = None) -> int:
    require_approved_fixtures()
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    # Keep the screenshot deterministic even on a workstation where a local
    # Ollama runtime happens to be active. The captured panel still exercises
    # the real fail-closed loopback-only provider path and explicitly reports
    # that local inference is unavailable.
    os.environ["FINSIGHT_AI_PROVIDER"] = "ollama"
    os.environ["FINSIGHT_OLLAMA_BASE_URL"] = "http://127.0.0.1:1"
    os.environ["FINSIGHT_AI_STATUS_TIMEOUT"] = "0.25"

    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("FinSight")
    app.setApplicationDisplayName("FinSight")

    with tempfile.TemporaryDirectory(
        prefix="finsight-stage2-screens-"
    ) as temporary:
        temporary_path = Path(temporary)
        data_directory = temporary_path / "store"
        settings = QSettings(
            str(temporary_path / "appearance.ini"),
            QSettings.Format.IniFormat,
        )
        appearance = AppearanceManager(
            app,
            settings=AppearanceSettings(settings),
        )
        services = build_workflow1_demo_services(data_directory)
        ask_fin = build_workflow1_demo_private_ask_fin_backend(data_directory)
        controller = AppController(services, ask_fin_backend=ask_fin)
        window = MainWindow(controller, appearance_manager=appearance)
        window.resize(*WINDOW_SIZE)
        window.show()
        capture = _CaptureSession(app, window, appearance, output)

        financial = _create_validated_may_review(
            app,
            window,
            capture,
        )

        _open_results_view(app, financial, financial._overview_tab)
        capture.screen("01-overview")

        _open_results_view(app, financial, financial._account_analysis_tab)
        capture.screen("02-financial-analysis-account")

        _open_results_view(app, financial, financial._vendor_analysis_tab)
        capture.screen("03-financial-analysis-vendor")

        _open_results_view(
            app,
            financial,
            financial._department_analysis_tab,
        )
        capture.screen("04-financial-analysis-department")

        _open_results_view(app, financial, financial._comparison_tab)
        capture.screen("05-financial-analysis-budget-vs-actual")

        _open_results_view(app, financial, financial._reconciliation_tab)
        capture.screen("06-financial-analysis-reconciliation")

        _open_results_view(app, financial, financial._ged_transactions_tab)
        capture.screen("07-ged-detail")

        financial._ged_results_table.selectRow(0)
        opened_transaction_details: list[QDialog] = []
        original_dialog_exec = QDialog.exec

        def capture_transaction_details(dialog):
            opened_transaction_details.append(dialog)
            return QDialog.DialogCode.Accepted

        QDialog.exec = capture_transaction_details
        try:
            financial._open_selected_ged_details()
        finally:
            QDialog.exec = original_dialog_exec
        transaction_details = opened_transaction_details[-1]
        transaction_details.show()
        capture.dialog("07a-ged-transaction-details", transaction_details)
        transaction_details.close()

        _open_results_view(app, financial, financial._finding_list_tab)
        financial._findings_search.clear()
        financial._findings_severity.setCurrentText("All severities")
        financial._findings_rule.setCurrentText("All rules")
        financial._findings_status.setCurrentText("All statuses")
        financial._findings_account.setCurrentText("All accounts")
        financial._findings_vendor.setCurrentText("All vendors")
        financial._findings_department.setCurrentText("All departments")
        financial._findings_review_required.setCurrentText(
            "All review states"
        )
        financial._findings_result_table.selectRow(0)
        financial._set_finding_explanation_visible(False)
        _scroll_to_top(app, financial)
        capture.screen("08-findings")

        _select_first_finding(app, financial)
        financial._set_finding_explanation_visible(False)
        financial._set_finding_explanation_visible(True)
        _scroll_to_widget(
            app,
            financial,
            financial._findings_splitter,
            top_offset=100,
        )
        capture.screen("09-explain-this-open")
        _scroll_to_widget(
            app,
            financial,
            financial._finding_transactions,
            top_offset=150,
        )
        capture.screen("09a-explain-transactions-and-actions")

        _open_results_view(app, financial, financial._review_summary_tab)
        capture.screen("10-review-summary")

        _open_results_view(app, financial, financial._overview_tab)
        financial._show_ask_fin()
        _wait(
            app,
            lambda: (
                hasattr(financial, "_private_ask_fin_dialog")
                and financial._private_ask_fin_dialog.isVisible()
            ),
            "the private Ask Fin panel",
        )
        ask_fin_dialog = financial._private_ask_fin_dialog
        _wait(
            app,
            lambda: (
                ask_fin_dialog._provider.text()
                in {"Local Ollama ready", "Local Ollama unavailable"}
                and ask_fin_dialog._mode.text()
                in {"Help Mode", "Financial Review Mode", "Unavailable"}
            ),
            "private Ask Fin local status",
        )
        capture.dialog("11-private-ask-fin-local-status", ask_fin_dialog)
        ask_fin_dialog.close()

        window._show_past_reviews()
        capture.screen("12-past-reviews")
        window._show_settings()
        capture.screen("13-settings")

        appearance.set_mode(AppearanceMode.SYSTEM)
        _settle(app)
        system_theme = appearance.resolved_palette.name
        window.close()
        appearance.dispose()

    print(
        f"Captured {len(capture.paths)} Stage 2 screenshots at "
        f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}:"
    )
    for path in capture.paths:
        print(path)
    print(f"System Default smoke check resolved to: {system_theme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(sys.argv[1] if len(sys.argv) > 1 else None)
    )
