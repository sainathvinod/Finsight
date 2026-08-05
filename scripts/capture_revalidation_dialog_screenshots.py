"""Capture focused evidence for governed revalidation and modern dialogs.

The harness uses the approved synthetic May 2026 Budget and GED workbooks,
creates a real recorded validation run, and then exercises the production
Rules/Revalidate presentation against the preserved verified working data. It
does not replace financial values or rule-engine results for screenshots.
"""
# ruff: noqa: E402

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication, QDialog, QScrollArea

from capture_stage2_screenshots import (
    _CaptureSession,
    _open_results_view,
    _settle,
    _wait,
)
from finsight.delivery.desktop.components import (
    DialogVariant,
    InAppMessageDialog,
)
from finsight.delivery.desktop.controllers import AppController
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import (
    AppearanceManager,
    AppearanceSettings,
)
from finsight.delivery.desktop.views.rules_repository_view import (
    ProtectedCoreActionDialog,
    RuleSetConfirmationDialog,
)
from finsight.domain.source_intake import SourceRole
from workflow1_demo_support import build_workflow1_demo_services
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
    / "flexible-revalidation-and-modern-dialogs"
)
OPTIONAL_RULE = {
    "name": "Large GED Transaction Review",
    "purpose": (
        "Surface unusually large individual GED transactions for financial review."
    ),
    "severity": "Medium",
    "evaluator_key": "ged_amount_threshold",
    "parameters": {"operator": "LTE", "threshold": "50000.00"},
}


def _accept_named_modal(app: QApplication, object_name: str) -> None:
    """Accept the next matching modal while leaving all other dialogs alone."""

    def accept_when_ready() -> None:
        dialog = app.activeModalWidget()
        if isinstance(dialog, QDialog) and dialog.objectName() == object_name:
            dialog.accept()
            return
        QTimer.singleShot(20, accept_when_ready)

    QTimer.singleShot(20, accept_when_ready)


def _scroll_rules_to_top(app: QApplication, rules) -> None:
    scroll = rules.findChild(QScrollArea)
    if scroll is not None:
        scroll.verticalScrollBar().setValue(0)
    _settle(app)


def _show_and_capture_dialog(
    app: QApplication,
    capture: _CaptureSession,
    name: str,
    dialog: QDialog,
) -> None:
    dialog.show()
    _wait(app, dialog.isVisible, f"{dialog.windowTitle()} dialog")
    capture.dialog(name, dialog)
    dialog.reject()
    _settle(app)


def _create_initial_validated_review(
    app: QApplication,
    window: MainWindow,
):
    """Drive the real review journey without capturing unrelated Stage 2 UI."""

    window.show_review_management()
    management = window.view("review_management")
    management.show_create()
    management._month.setCurrentIndex(management._month.findData(5))
    management._year.setText("2026")
    management._create_submit.click()
    _wait(
        app,
        lambda: window.current_view_key() == "upload_extraction",
        "Upload Reports",
    )

    intake = window.view("source_intake")
    intake.select_source_path(SourceRole.BUDGET, str(BUDGET_FIXTURE))
    _wait(app, lambda: intake._budget is not None, "Budget extraction")
    intake.select_source_path(SourceRole.GED, str(GED_FIXTURE))
    _wait(app, lambda: intake._ged is not None, "GED extraction")
    _wait(app, lambda: intake.current_pair() is not None, "source-pair match")
    intake._save_button.click()
    _wait(
        app,
        lambda: window.current_view_key() == "verify_data",
        "Verify Data",
        timeout=90,
    )

    financial = window.view("financial_review")
    financial._attestation.setChecked(True)
    _accept_named_modal(app, "ConfirmReviewedDataDialog")
    financial._open_confirmation()
    _wait(
        app,
        lambda: window.current_view_key() == "rules_repository",
        "the initial Rules Repository",
    )

    _accept_named_modal(app, "RuleSetConfirmationDialog")
    window.view("rules_repository")._continue()
    _wait(
        app,
        lambda: window.current_view_key() == "validation_progress",
        "the initial validation run to start",
    )
    _wait(
        app,
        lambda: window.current_view_key() == "financial_review_results",
        "the initial validation run results",
        timeout=90,
    )
    return financial


def main(output_directory: str | None = None) -> int:
    require_approved_fixtures()
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    # Keep unrelated Ask Fin status deterministic while the screenshot harness
    # focuses exclusively on governed rules and validation dialogs.
    os.environ["FINSIGHT_AI_PROVIDER"] = "ollama"
    os.environ["FINSIGHT_OLLAMA_BASE_URL"] = "http://127.0.0.1:1"
    os.environ["FINSIGHT_AI_STATUS_TIMEOUT"] = "0.25"

    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("FinSight")
    app.setApplicationDisplayName("FinSight")

    with tempfile.TemporaryDirectory(
        prefix="finsight-revalidation-dialog-screens-"
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
        controller = AppController(services)
        window = MainWindow(controller, appearance_manager=appearance)
        window.resize(1440, 1000)
        window.show()

        # The first run uses the same explicit confirmations as revalidation.
        # Accept them without bypassing the production services so the recorded
        # baseline remains genuine.
        financial = _create_initial_validated_review(app, window)
        capture = _CaptureSession(app, window, appearance, output)

        window._show_rules_repository(
            financial._review,
            financial._dataset,
            revalidation=True,
        )
        rules = window.view("rules_repository")
        _wait(
            app,
            lambda: rules._rule_table.topLevelItemCount() >= 5,
            "the completed review Rules/Revalidate page",
        )

        draft = controller.create_optional_rule(
            financial._review.review_id,
            OPTIONAL_RULE,
        )
        draft_rule_id = str(draft["rule_id"])
        draft_version = str(draft["version"])
        rules.refresh()
        rules._select_rule_by_id(draft_rule_id)
        _scroll_rules_to_top(app, rules)
        if rules._validate.isEnabled():
            raise RuntimeError(
                "Validation unexpectedly remained enabled with an unresolved Draft rule."
            )
        if not rules._draft_banner.isVisible():
            raise RuntimeError("The unresolved Draft explanation is not visible.")
        capture.screen("01-revalidation-draft-actions")

        test_result = controller.test_optional_rule(
            financial._review.review_id,
            draft_rule_id,
            financial._dataset,
        )
        controller.activate_optional_rule(
            financial._review.review_id,
            draft_rule_id,
            draft_version,
        )
        rules.refresh()
        rules._select_rule_by_id(draft_rule_id)
        _scroll_rules_to_top(app, rules)
        if not rules._validate.isEnabled():
            raise RuntimeError(
                "Validation did not become available after the optional rule was activated."
            )
        capture.screen("02-active-rule-set-ready")

        proposal = controller.validation_rule_set_proposal(financial._dataset)
        if not proposal.get("ready"):
            raise RuntimeError(
                "The activated Rule Set is not ready for confirmation: "
                + " ".join(proposal.get("readiness_reasons", ()))
            )
        confirmation_dialog = RuleSetConfirmationDialog(proposal, rules)
        _show_and_capture_dialog(
            app,
            capture,
            "03-pre-validation-rule-set-confirmation",
            confirmation_dialog,
        )

        protected_rule = next(
            rule
            for rule in rules._rules
            if rule.get("baseline_status") == "PROTECTED_BASELINE"
        )
        rules._select_rule_by_id(str(protected_rule["rule_id"]))
        protected_dialog = ProtectedCoreActionDialog(protected_rule, rules)
        _show_and_capture_dialog(
            app,
            capture,
            "04-protected-core-action",
            protected_dialog,
        )

        rules._select_rule_by_id(draft_rule_id)
        retirement_dialog = InAppMessageDialog(
            "Retire optional rule?",
            "“Large GED Transaction Review” will not run in future Rule Sets. "
            "Historical Validation Runs and prior Rule Versions will remain unchanged.",
            variant=DialogVariant.WARNING,
            parent=rules,
            accept_text="Retire Optional Rule",
            cancel_text="Cancel",
            accept_role="destructive",
        )
        _show_and_capture_dialog(
            app,
            capture,
            "05-optional-rule-retirement-warning",
            retirement_dialog,
        )

        confirmation = controller.confirm_validation_rule_set(
            financial._dataset,
            str(proposal["proposal_hash"]),
        )
        window._start_validation_from_rules(
            financial._review,
            financial._dataset,
            revalidation=True,
            confirmation=confirmation,
        )
        _wait(
            app,
            lambda: window.current_view_key() == "validation_progress",
            "the successor validation run to start",
        )
        _wait(
            app,
            lambda: window.current_view_key() == "financial_review_results",
            "the successor validation run results",
            timeout=90,
        )
        _open_results_view(app, financial, financial._overview_tab)
        capture.screen("06-new-validation-run-comparison")

        print(
            "Draft preview: "
            f"{test_result.get('records_evaluated', 0)} records evaluated; "
            f"{test_result.get('findings', 0)} would be flagged."
        )
        print(
            "Confirmed Rule Set: "
            f"{proposal['rule_set_id']} · v{proposal['rule_set_version']} · "
            f"{len(proposal['included_rules'])} active rules."
        )
        print(f"Captured {len(capture.paths)} focused screenshots:")
        for path in capture.paths:
            print(path)

        window.close()
        appearance.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
