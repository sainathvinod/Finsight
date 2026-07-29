"""Capture the complete seven-step FinSight MVP in Light and Dark modes.

The harness uses the approved synthetic workbooks and an isolated temporary
store.  It intentionally drives the same presentation and application-service
seams as a reviewer; no production business logic is replaced for screenshots.
"""
# ruff: noqa: E402

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import os
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from PySide6.QtCore import QPoint, QSettings, QTimer, Qt
from PySide6.QtGui import QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QWidget,
)

from finsight.app import build_query_services
from finsight.application.security import (
    IdentityResolution,
    StaticRoleAssignmentSource,
)
from finsight.delivery.desktop.controllers import AppController
from finsight.delivery.desktop.components.charts import FinancialChartCard
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import (
    AppearanceManager,
    AppearanceMode,
    AppearanceSettings,
)
from finsight.domain.identity import Actor, Role
from finsight.domain.source_intake import SourceRole
from finsight.infrastructure.authorization_manifest import (
    build_local_reviewer_bootstrap_policy,
)
from finsight.infrastructure.identity import FixedIdentityProvider
from finsight.infrastructure.secure_store import (
    TestEnvironmentStoreKeyProvider,
)

from workflow2_demo_support import (
    BUDGET_FIXTURE,
    GED_FIXTURE,
    build_workflow1_demo_services,
    require_approved_fixtures,
)


DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "initiatives"
    / "configurable-rule-engine-v2"
    / "verification"
    / "screenshots"
    / "mvp-end-to-end"
)
WINDOW_SIZE = (
    int(os.environ.get("FINSIGHT_CAPTURE_WIDTH", "1280")),
    int(os.environ.get("FINSIGHT_CAPTURE_HEIGHT", "900")),
)
MODES = (AppearanceMode.LIGHT, AppearanceMode.DARK)
LANDING_ONLY = os.environ.get(
    "FINSIGHT_CAPTURE_LANDING_ONLY", ""
).strip().lower() in {"1", "true", "yes", "on"}
VERIFY_DATA_ONLY = os.environ.get(
    "FINSIGHT_CAPTURE_VERIFY_DATA_ONLY", ""
).strip().lower() in {"1", "true", "yes", "on"}


def _wait(
    app: QApplication,
    predicate: Callable[[], bool],
    description: str,
    *,
    timeout: float = 45.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return
        QTest.qWait(10)
    raise TimeoutError(f"Timed out waiting for {description}.")


def _settle(app: QApplication) -> None:
    for _iteration in range(4):
        app.processEvents()
        QTest.qWait(25)


def _save_window(
    app: QApplication,
    window: MainWindow,
    path: Path,
) -> None:
    _settle(app)
    image = window.grab()
    if image.isNull() or image.size().width() != WINDOW_SIZE[0]:
        raise RuntimeError(
            f"Could not capture a {WINDOW_SIZE[0]}px-wide image for {path.name}."
        )
    if not image.save(str(path), "PNG"):
        raise RuntimeError(f"Could not capture {path.name}.")


def _save_modal(
    app: QApplication,
    window: MainWindow,
    dialog: QDialog,
    path: Path,
) -> None:
    _settle(app)
    base = window.grab()
    overlay = dialog.grab()
    painter = QPainter(base)
    painter.drawPixmap(
        max(0, (base.width() - overlay.width()) // 2),
        max(0, (base.height() - overlay.height()) // 2),
        overlay,
    )
    painter.end()
    if base.isNull() or not base.save(str(path), "PNG"):
        raise RuntimeError(f"Could not capture modal {path.name}.")


class _CaptureSession:
    """One application-wide appearance manager and a deterministic file ledger."""

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

    def screen_once(
        self,
        name: str,
        mode: AppearanceMode = AppearanceMode.LIGHT,
    ) -> None:
        self.appearance.set_mode(mode)
        path = self.output / mode.value / f"{name}.png"
        _save_window(self.app, self.window, path)
        self.paths.append(path.resolve())

    def modal(self, name: str, dialog: QDialog) -> None:
        for mode in MODES:
            self.appearance.set_mode(mode)
            path = self.output / mode.value / f"{name}.png"
            _save_modal(self.app, self.window, dialog, path)
            self.paths.append(path.resolve())
        self.appearance.set_mode(AppearanceMode.LIGHT)

    def modal_once(
        self,
        name: str,
        dialog: QDialog,
        mode: AppearanceMode = AppearanceMode.LIGHT,
    ) -> None:
        self.appearance.set_mode(mode)
        path = self.output / mode.value / f"{name}.png"
        _save_modal(self.app, self.window, dialog, path)
        self.paths.append(path.resolve())

    def invoke_modal(
        self,
        name: str,
        invoke: Callable[[], None],
        finish: Callable[[QDialog], None],
    ) -> None:
        completed = {"value": False}

        def capture_when_ready() -> None:
            dialog = self.app.activeModalWidget()
            if not isinstance(dialog, QDialog):
                QTimer.singleShot(20, capture_when_ready)
                return
            self.modal(name, dialog)
            completed["value"] = True
            finish(dialog)

        QTimer.singleShot(30, capture_when_ready)
        invoke()
        if not completed["value"]:
            raise RuntimeError(f"The {name} modal did not become available.")

    def invoke_modal_once(
        self,
        name: str,
        invoke: Callable[[], None],
        finish: Callable[[QDialog], None],
        mode: AppearanceMode = AppearanceMode.LIGHT,
    ) -> None:
        completed = {"value": False}

        def capture_when_ready() -> None:
            dialog = self.app.activeModalWidget()
            if not isinstance(dialog, QDialog):
                QTimer.singleShot(20, capture_when_ready)
                return
            self.modal_once(name, dialog, mode)
            completed["value"] = True
            finish(dialog)

        QTimer.singleShot(30, capture_when_ready)
        invoke()
        if not completed["value"]:
            raise RuntimeError(f"The {name} modal did not become available.")


def _accept_dialog(dialog: QDialog) -> None:
    dialog.accept()


def _accept_acknowledged_dialog(dialog: QDialog) -> None:
    acknowledgment = dialog.findChild(QCheckBox)
    if acknowledgment is None:
        raise RuntimeError("The governed confirmation checkbox was not found.")
    acknowledgment.setChecked(True)
    dialog.accept()


def _reject_dialog(dialog: QDialog) -> None:
    dialog.reject()


def _stage_demonstration_edit(financial) -> None:
    """Stage one non-financial notes edit in the review-local working copy."""

    financial._toggle_edit()
    if financial._pending:
        raise RuntimeError(
            "Entering Edit Mode incorrectly staged presentation-only changes."
        )
    model = financial._budget_model
    column = next(
        (
            index
            for index in range(model.columnCount())
            if model.horizontalHeaderItem(index).text() == "Notes"
        ),
        None,
    )
    if column is None:
        raise RuntimeError("Budget Notes column is unavailable for the edit demo.")
    item = next(
        (
            model.item(row, column)
            for row in range(model.rowCount())
            if model.item(row, column).data() is not None
        ),
        None,
    )
    if item is None:
        raise RuntimeError("No reviewable Budget Notes cell was found.")
    item.setText("Reviewed in FinSight — synthetic test data.")
    if not financial._save_changes.isEnabled():
        raise RuntimeError("The staged reviewed-data edit was not detected.")


def _scroll_active_page(financial, value: int) -> None:
    page = financial._stack.currentWidget()
    scroll = (
        page
        if isinstance(page, QScrollArea)
        else (page.findChild(QScrollArea) if page is not None else None)
    )
    if scroll is not None:
        scroll.verticalScrollBar().setValue(value)


def _active_scroll_area(financial) -> QScrollArea:
    page = financial._stack.currentWidget()
    scroll = (
        page
        if isinstance(page, QScrollArea)
        else (page.findChild(QScrollArea) if page is not None else None)
    )
    if not isinstance(scroll, QScrollArea) or scroll.widget() is None:
        raise RuntimeError("The active Financial Review scroll surface was not found.")
    return scroll


def _scroll_active_to_widget(
    app: QApplication,
    financial,
    widget: QWidget,
    *,
    top_offset: int = 150,
) -> None:
    """Place a result artifact near the top of the screenshot deterministically."""

    _settle(app)
    scroll = _active_scroll_area(financial)
    content = scroll.widget()
    position = widget.mapTo(content, QPoint(0, 0))
    bar = scroll.verticalScrollBar()
    target = max(bar.minimum(), min(bar.maximum(), position.y() - top_offset))
    bar.setValue(target)
    _settle(app)


def _result_chart(financial, title: str) -> FinancialChartCard:
    page = financial._results_tabs.currentWidget()
    if page is None:
        raise RuntimeError(f"Could not locate the {title!r} result chart.")
    for card in page.findChildren(FinancialChartCard):
        if card.accessibleName() == title:
            return card
    raise RuntimeError(f"The {title!r} result chart was not found.")


def _result_heading(financial, text: str) -> QLabel:
    page = financial._results_tabs.currentWidget()
    if page is None:
        raise RuntimeError(f"Could not locate the {text!r} result section.")
    for label in page.findChildren(QLabel):
        if label.text() == text:
            return label
    raise RuntimeError(f"The {text!r} result section was not found.")


def _select_account_drilldown(
    app: QApplication,
    financial,
    scope_key: str,
) -> None:
    selector = financial._account_selector
    index = selector.findData(scope_key)
    if index < 0:
        raise RuntimeError(
            f"The requested account drill-down scope {scope_key!r} was not found."
        )
    selector.setCurrentIndex(index)
    financial._show_account_drilldown(index)
    _wait(
        app,
        lambda: (
            selector.currentData() == scope_key
            and financial._account_transactions.rowCount() > 0
        ),
        f"{scope_key} account hierarchy",
    )


def _select_finding(financial, rule_id: str) -> None:
    financial._findings_search.clear()
    financial._findings_severity.setCurrentText("All severities")
    financial._findings_rule.setCurrentText(rule_id)
    _wait(
        QApplication.instance(),
        lambda: financial._findings_proxy.rowCount() > 0,
        f"{rule_id} finding",
    )
    financial._findings_result_table.selectRow(0)
    financial._show_finding_detail(
        financial._findings_proxy.index(0, 0),
        financial._findings_proxy.index(-1, -1),
    )


def _scroll_rules_page(rules, *, to_end: bool) -> None:
    scroll = rules.findChild(QScrollArea, "Workflow1Page")
    if scroll is None:
        raise RuntimeError("The Rules Repository scroll surface was not found.")
    bar = scroll.verticalScrollBar()
    bar.setValue(bar.maximum() if to_end else bar.minimum())


def _show_workspace_upgrade_card(rules) -> None:
    scroll = rules.findChild(QScrollArea, "Workflow1Page")
    if scroll is None:
        raise RuntimeError("The Rules Repository scroll surface was not found.")
    scroll.ensureWidgetVisible(rules._workspace_upgrade_card, 0, 16)
    scroll.verticalScrollBar().setValue(
        max(0, rules._workspace_upgrade_card.y() - 16)
    )


def _select_rule(rules, predicate: Callable[[dict], bool]) -> dict:
    for row, rule in enumerate(rules._rules):
        if predicate(rule):
            rules._rule_list.setCurrentRow(row)
            return rule
    raise RuntimeError("The requested repository rule was not found.")


def _submit_protected_request(dialog: QDialog) -> None:
    purpose = dialog.findChild(QPlainTextEdit, "ProtectedProposedPurpose")
    reason = dialog.findChild(QPlainTextEdit, "ProtectedChangeReason")
    if purpose is None or reason is None:
        raise RuntimeError("Protected request fields were not found.")
    purpose.setPlainText(
        purpose.toPlainText().rstrip()
        + " The governed version also clarifies retained source evidence."
    )
    reason.setPlainText(
        "Clarify the control evidence wording under the protected two-person "
        "change policy."
    )
    dialog.accept()


def _approve_protected_request(dialog: QDialog) -> None:
    reason = dialog.findChild(QPlainTextEdit, "ProtectedDecisionReason")
    if reason is None:
        raise RuntimeError("Protected decision reason was not found.")
    reason.setPlainText(
        "Independent Financial Control review confirmed the semantic successor "
        "and its pinned qualification evidence."
    )
    dialog.accept()


def _submit_workspace_upgrade(dialog: QDialog) -> None:
    reason = dialog.findChild(QPlainTextEdit, "WorkspaceUpgradeReason")
    if reason is None:
        raise RuntimeError("Workspace upgrade reason was not found.")
    reason.setPlainText(
        "Apply the independently approved protected baseline to this existing "
        "workspace while preserving the completed Validation Run."
    )
    dialog.accept()


def _approve_workspace_upgrade(dialog: QDialog) -> None:
    reason = dialog.findChild(
        QPlainTextEdit, "WorkspaceUpgradeDecisionReason"
    )
    if reason is None:
        raise RuntimeError("Workspace upgrade decision reason was not found.")
    reason.setPlainText(
        "The request-time Rule Set, completed Validation Run, and exact target "
        "baseline were independently verified."
    )
    dialog.accept()


def _build_approver_services(data_directory: Path):
    """Open the same demo store as a distinct governed control approver."""

    actor = Actor(
        "DEMO:financial-control-approver",
        "Financial Control Approver",
        "DEMO_IDP",
    )
    effective_from = datetime(2020, 1, 1, tzinfo=timezone.utc)
    base = build_local_reviewer_bootstrap_policy(actor, effective_from)
    assignment = replace(
        base.assignments[0],
        allow_roles=frozenset({Role.FINANCIAL_CONTROL_APPROVER}),
    )
    assignment_source = StaticRoleAssignmentSource(
        replace(
            base,
            version="LOCAL-DEMO-FINANCIAL-CONTROL-APPROVER-1",
            fingerprint=hashlib.sha256(
                (
                    base.fingerprint
                    + "|Financial Control Approver"
                ).encode("utf-8")
            ).hexdigest(),
            assignments=(assignment,),
        )
    )
    return build_query_services(
        str(data_directory / "finsight.db"),
        identity_provider=FixedIdentityProvider(
            IdentityResolution.resolved(actor)
        ),
        role_assignment_source=assignment_source,
        key_provider=TestEnvironmentStoreKeyProvider(),
        registry_root=str(data_directory / "disposal-registry"),
    )


def _select_budget_overrun_rule(financial) -> None:
    model = financial._rule_summary_model
    for row in range(model.rowCount()):
        if model.item(row, 0).text() == "Budget Overrun":
            financial._rule_summary_table.selectRow(row)
            financial._show_rule_evidence(
                model.index(row, 0), model.index(-1, -1)
            )
            return
    raise RuntimeError("The Budget Overrun rule was not found.")


def _select_duplicate_finding(financial) -> None:
    financial._findings_rule.setCurrentText("CORE-03")
    _wait(
        QApplication.instance(),
        lambda: financial._findings_proxy.rowCount() > 0,
        "duplicate finding",
    )
    financial._findings_result_table.selectRow(0)
    financial._show_finding_detail(
        financial._findings_proxy.index(0, 0),
        financial._findings_proxy.index(-1, -1),
    )


def main(output_directory: str | None = None) -> int:
    require_approved_fixtures()
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("FinSight")
    app.setApplicationDisplayName("FinSight")

    with tempfile.TemporaryDirectory(prefix="finsight-mvp-screens-") as temporary:
        temporary_path = Path(temporary)
        settings = QSettings(
            str(temporary_path / "appearance.ini"),
            QSettings.Format.IniFormat,
        )
        appearance = AppearanceManager(
            app,
            settings=AppearanceSettings(settings),
        )
        services = build_workflow1_demo_services(temporary_path / "store")
        controller = AppController(services, ask_fin_backend=None)
        window = MainWindow(controller, appearance_manager=appearance)
        window.resize(*WINDOW_SIZE)
        window.show()
        capture = _CaptureSession(app, window, appearance, output)
        management = window.view("review_management")

        management.show_welcome()
        if VERIFY_DATA_ONLY:
            management.show_create()
            management._month.setCurrentIndex(management._month.findData(5))
            management._year.setText("2026")
            management._create_submit.click()
            _wait(
                app,
                lambda: window.current_view_key() == "upload_extraction",
                "Upload Documents",
            )
            intake = window.view("source_intake")
            intake.select_source_path(SourceRole.BUDGET, str(BUDGET_FIXTURE))
            _wait(app, lambda: intake._budget is not None, "Budget extraction")
            intake.select_source_path(SourceRole.GED, str(GED_FIXTURE))
            _wait(app, lambda: intake._ged is not None, "GED extraction")
            _wait(app, lambda: intake.current_pair() is not None, "source pair")
            intake._save_button.click()
            _wait(
                app,
                lambda: window.current_view_key() == "verify_data",
                "Verify Data",
            )
            financial = window.view("financial_review")
            capture.screen_once("01-budget-data")
            financial._data_tabs.setCurrentIndex(1)
            capture.screen_once("02-ged-data")
            financial._data_tabs.setCurrentIndex(0)
            model = financial._budget_table.model()
            account_name_column = next(
                column
                for column in range(model.columnCount())
                if model.headerData(column, Qt.Orientation.Horizontal)
                == "Account Name"
            )
            financial._budget_table.setCurrentIndex(
                model.index(0, account_name_column)
            )
            _wait(
                app,
                lambda: financial._source_details.isEnabled(),
                "View Source action",
            )
            capture.invoke_modal_once(
                "03-source-details-open",
                financial._open_source_details,
                _reject_dialog,
            )
            appearance.set_mode(AppearanceMode.SYSTEM)
            _settle(app)
            system_theme = appearance.resolved_palette.name
            window.close()
            appearance.dispose()
            print(
                f"Captured {len(capture.paths)} Verify Data screenshots at "
                f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}:"
            )
            for path in capture.paths:
                print(path)
            print(f"System Default smoke check resolved to: {system_theme}")
            return 0
        capture.screen("01-welcome")
        if LANDING_ONLY:
            appearance.set_mode(AppearanceMode.SYSTEM)
            _settle(app)
            system_theme = appearance.resolved_palette.name
            window.close()
            appearance.dispose()
            print(
                f"Captured the FinSight landing page in Light and Dark at "
                f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}:"
            )
            for path in capture.paths:
                print(path)
            print(f"System Default smoke check resolved to: {system_theme}")
            return 0
        management._settings_nav.click()
        _wait(app, lambda: window.current_view_key() == "settings", "Settings")
        capture.screen("01a-settings-appearance")
        window.view("settings").back_button.click()
        _wait(app, lambda: window.current_view_key() == "welcome", "Welcome")

        management.show_create()
        management._month.setCurrentIndex(management._month.findData(5))
        management._year.setText("2026")
        capture.screen("02-create-review")
        management._year.clear()
        management._create_submit.click()
        capture.screen("02a-create-review-required-error")
        management._year.setText("2026")
        management._create_submit.click()
        _wait(
            app,
            lambda: window.current_view_key() == "upload_extraction",
            "Upload Documents",
        )

        intake = window.view("source_intake")
        capture.screen("03-upload-empty")
        intake.select_source_path(SourceRole.BUDGET, str(BUDGET_FIXTURE))
        _wait(app, lambda: intake._budget is not None, "Budget extraction")
        intake.select_source_path(SourceRole.GED, str(GED_FIXTURE))
        _wait(app, lambda: intake._ged is not None, "GED extraction")
        _wait(app, lambda: intake.current_pair() is not None, "source pair")
        capture.screen("04-upload-ready")

        intake._save_button.click()
        _wait(
            app,
            lambda: window.current_view_key() == "processing",
            "processing stage",
        )
        capture.screen("05-processing")
        _wait(
            app,
            lambda: window.current_view_key() == "verify_data",
            "Verify Data",
        )

        financial = window.view("financial_review")
        capture.screen("06-verify-budget")
        financial._data_tabs.setCurrentIndex(1)
        capture.screen("07-verify-ged")
        financial._data_tabs.setCurrentIndex(0)
        _stage_demonstration_edit(financial)
        capture.screen("08-verify-budget-staged-edit")
        capture.invoke_modal(
            "09-governed-save-changes",
            financial._save_pending_changes,
            _accept_acknowledged_dialog,
        )
        capture.screen("10-verify-budget-saved-edit")
        capture.invoke_modal(
            "11-change-history",
            financial._show_history,
            _accept_dialog,
        )

        financial._attestation.setChecked(True)
        capture.invoke_modal(
            "12-confirm-data-for-validation",
            financial._open_confirmation,
            _accept_dialog,
        )
        _wait(
            app,
            lambda: window.current_view_key() == "rules_repository",
            "Rules Repository",
        )

        rules = window.view("rules_repository")
        _select_rule(
            rules,
            lambda rule: rule.get("name") == "Budget-to-GED Reconciliation",
        )
        capture.screen("13-rules-core-list-and-detail")

        capture.invoke_modal(
            "13a-protected-change-request",
            rules._request_protected,
            _submit_protected_request,
        )
        _wait(
            app,
            lambda: rules._governance_request_list.count() == 1,
            "Pending Approval protected request",
        )
        _scroll_rules_page(rules, to_end=True)
        capture.screen("13b-protected-change-pending")

        approver_services = _build_approver_services(
            temporary_path / "store"
        )
        approver_controller = AppController(
            approver_services, ask_fin_backend=None
        )
        approver_window = MainWindow(
            approver_controller,
            appearance_manager=appearance,
        )
        approver_window.resize(*WINDOW_SIZE)
        approver_window.show()
        approver_management = approver_window.view("review_management")
        approver_management.show_welcome()
        approver_management._rule_governance_nav.click()
        _wait(
            app,
            lambda: (
                approver_window.current_view_key() == "rule_governance"
                and approver_window.view(
                    "rules_repository"
                )._governance_request_list.count()
                == 1
            ),
            "Financial Control Approver queue",
        )
        approver_rules = approver_window.view("rules_repository")
        _scroll_rules_page(approver_rules, to_end=True)
        capture.window = approver_window
        capture.screen("13c-protected-change-approver-queue")
        capture.invoke_modal(
            "13d-protected-change-approval",
            lambda: approver_rules._decide_protected("APPROVED"),
            _approve_protected_request,
        )
        _wait(
            app,
            lambda: (
                approver_rules._selected_governance_request is not None
                and approver_rules._selected_governance_request["status"]
                == "APPROVED"
            ),
            "approved protected successor",
        )
        _scroll_rules_page(approver_rules, to_end=True)
        capture.screen("13e-protected-change-approved-history")
        approver_window.close()
        approver_services.financial_review._uow.dal.conn.close()
        capture.window = window
        rules.refresh()
        _scroll_rules_page(rules, to_end=False)

        capture.invoke_modal(
            "14-optional-rule-add",
            rules._add_optional,
            _accept_dialog,
        )
        _select_rule(
            rules,
            lambda rule: (
                rule.get("baseline_status") != "PROTECTED_BASELINE"
                and rule.get("lifecycle_status") == "DRAFT"
            ),
        )
        capture.screen("15-optional-rule-draft")

        def accept_edited_optional(dialog: QDialog) -> None:
            threshold = next(
                (
                    field
                    for field in dialog.findChildren(QLineEdit)
                    if field.accessibleName() == "GED Amount threshold"
                ),
                None,
            )
            if threshold is None:
                raise RuntimeError("Optional-rule threshold field was not found.")
            # Demonstrate a real successor version without flooding the final
            # baseline-control review with advisory findings.
            threshold.setText("2000000.00")
            dialog.accept()

        capture.invoke_modal(
            "16-optional-rule-edit",
            rules._edit_selected,
            accept_edited_optional,
        )
        _select_rule(
            rules,
            lambda rule: (
                rule.get("baseline_status") != "PROTECTED_BASELINE"
                and rule.get("lifecycle_status") == "DRAFT"
                and str(rule.get("parameters", {}).get("threshold", "")).startswith(
                    "2000000"
                )
            ),
        )

        capture.invoke_modal(
            "17-optional-rule-test-result",
            rules._test_selected,
            _accept_dialog,
        )
        rules.refresh()
        _select_rule(
            rules,
            lambda rule: (
                rule.get("baseline_status") != "PROTECTED_BASELINE"
                and rule.get("lifecycle_status") == "TESTED"
            ),
        )
        capture.screen("18-optional-rule-tested")
        rules._activate_selected()
        _select_rule(
            rules,
            lambda rule: (
                rule.get("baseline_status") != "PROTECTED_BASELINE"
                and rule.get("lifecycle_status") == "ACTIVE"
                and rule.get("bound")
            ),
        )
        capture.screen("19-optional-rule-activated")

        rules._continue()
        _wait(
            app,
            lambda: window.current_view_key() == "validation_progress",
            "validation progress",
        )
        capture.screen("20-validation-progress")
        _wait(
            app,
            lambda: window.current_view_key() == "financial_review_results",
            "Financial Review Results",
            timeout=60,
        )

        financial._results_tabs.setCurrentIndex(0)
        _scroll_active_page(financial, 0)
        capture.screen("21-executive-overview")
        _scroll_active_page(financial, 420)
        capture.screen("22-executive-analytics")
        _scroll_active_to_widget(
            app,
            financial,
            _result_chart(financial, "Reconciliation coverage"),
        )
        capture.screen("22a-overview-reconciliation-and-utilization")
        _scroll_active_page(financial, 0)

        for index, name in (
            (1, "23-budget-chart-and-evidence"),
            (2, "24-ged-charts-and-evidence"),
            (3, "25-budget-ged-comparison-chart"),
        ):
            financial._results_tabs.setCurrentIndex(index)
            _scroll_active_page(financial, 0)
            capture.screen(name)

        financial._results_tabs.setCurrentIndex(2)
        _scroll_active_to_widget(
            app,
            financial,
            _result_chart(financial, "Top vendors by GED spend"),
        )
        capture.screen("24a-ged-vendor-and-largest-transaction-charts")
        _scroll_active_to_widget(
            app,
            financial,
            _result_chart(financial, "Positive versus negative GED activity"),
        )
        capture.screen("24b-ged-positive-negative-activity")

        financial._results_tabs.setCurrentIndex(3)
        _scroll_active_to_widget(
            app,
            financial,
            _result_chart(
                financial,
                "Accounts ranked by remaining budget and overrun",
            ),
        )
        capture.screen("25a-comparison-ranked-and-reconciliation-charts")
        _select_account_drilldown(app, financial, "00-0245|555035")
        _scroll_active_to_widget(
            app,
            financial,
            financial._account_selector,
            top_offset=100,
        )
        capture.screen("25b-account-555035-budget-and-ged-summary")
        _scroll_active_to_widget(
            app,
            financial,
            financial._account_transactions,
            top_offset=130,
        )
        capture.screen("25c-account-555035-contributing-transactions")

        financial._results_tabs.setCurrentIndex(4)
        _scroll_active_page(financial, 0)
        _select_budget_overrun_rule(financial)
        capture.screen("26-validation-results-evidence")

        financial._results_tabs.setCurrentIndex(5)
        _scroll_active_page(financial, 0)
        _select_duplicate_finding(financial)
        capture.screen("27-findings-duplicate-evidence")
        for rule_id, name in (
            ("CORE-01", "27a-core-01-budget-overrun-evidence"),
            ("CORE-02", "27b-core-02-budget-mapping-evidence"),
            ("CORE-03", "27c-core-03-exact-duplicate-evidence"),
            ("CORE-04", "27d-core-04-required-data-evidence"),
            ("CORE-05", "27e-core-05-reconciliation-evidence"),
        ):
            _select_finding(financial, rule_id)
            _scroll_active_page(financial, 0)
            capture.screen(name)

        financial._results_tabs.setCurrentIndex(6)
        _scroll_active_page(financial, 0)
        capture.screen("28-data-quality-and-coverage")
        _scroll_active_to_widget(
            app,
            financial,
            _result_heading(financial, "Exact Financial Control Totals"),
            top_offset=105,
        )
        capture.screen("28q-exact-financial-control-totals")
        _scroll_active_to_widget(
            app,
            financial,
            _result_heading(financial, "Row Inclusion and Exclusion"),
            top_offset=105,
        )
        capture.screen("28r-row-inclusion-and-exclusion")
        _scroll_active_to_widget(
            app,
            financial,
            _result_heading(financial, "Approved Source Field Coverage"),
            top_offset=105,
        )
        capture.screen("28s-approved-source-field-coverage")

        financial._results_tabs.setCurrentIndex(0)
        financial._review_rules_button.click()
        _wait(
            app,
            lambda: window.current_view_key() == "rules_repository",
            "Rules Repository for protected baseline upgrade",
        )
        rules._workspace_upgrade_tabs.setCurrentIndex(0)
        _wait(
            app,
            lambda: (
                rules._upgrade_candidate_list.count() == 1
                and rules._workspace_candidate_state(
                    rules._upgrade_candidates[0]
                )
                == "UPGRADE_AVAILABLE"
            ),
            "eligible existing-workspace baseline upgrade",
        )
        _show_workspace_upgrade_card(rules)
        capture.screen("28a-workspace-upgrade-available")
        capture.invoke_modal(
            "28b-workspace-upgrade-request",
            rules._request_workspace_upgrade,
            _submit_workspace_upgrade,
        )
        _wait(
            app,
            lambda: (
                rules._upgrade_request_list.count() == 1
                and rules._upgrade_requests[0]["status"]
                == "PENDING_APPROVAL"
            ),
            "pending existing-workspace baseline upgrade",
        )
        rules._workspace_upgrade_tabs.setCurrentIndex(1)
        _show_workspace_upgrade_card(rules)
        capture.screen("28c-workspace-upgrade-pending")

        upgrade_approver_services = _build_approver_services(
            temporary_path / "store"
        )
        upgrade_approver_controller = AppController(
            upgrade_approver_services, ask_fin_backend=None
        )
        upgrade_approver_window = MainWindow(
            upgrade_approver_controller,
            appearance_manager=appearance,
        )
        upgrade_approver_window.resize(*WINDOW_SIZE)
        upgrade_approver_window.show()
        upgrade_approver_management = upgrade_approver_window.view(
            "review_management"
        )
        upgrade_approver_management.show_welcome()
        upgrade_approver_management._rule_governance_nav.click()
        _wait(
            app,
            lambda: (
                upgrade_approver_window.current_view_key()
                == "rule_governance"
                and upgrade_approver_window.view(
                    "rules_repository"
                )._upgrade_request_list.count()
                == 1
            ),
            "workspace upgrade Financial Control Approver queue",
        )
        upgrade_approver_rules = upgrade_approver_window.view(
            "rules_repository"
        )
        upgrade_approver_rules._workspace_upgrade_tabs.setCurrentIndex(1)
        _show_workspace_upgrade_card(upgrade_approver_rules)
        capture.window = upgrade_approver_window
        capture.screen("28d-workspace-upgrade-approver-queue")
        capture.invoke_modal(
            "28e-workspace-upgrade-authorization",
            lambda: upgrade_approver_rules._decide_workspace_upgrade(
                "APPROVED"
            ),
            _approve_workspace_upgrade,
        )
        _wait(
            app,
            lambda: (
                upgrade_approver_rules._selected_upgrade_request is not None
                and upgrade_approver_rules._selected_upgrade_request["status"]
                == "APPLIED"
            ),
            "authorized and applied workspace baseline upgrade",
        )
        _show_workspace_upgrade_card(upgrade_approver_rules)
        capture.screen("28f-workspace-upgrade-applied-history")
        upgrade_approver_window.close()
        upgrade_approver_services.financial_review._uow.dal.conn.close()

        capture.window = window
        rules.refresh()
        rules._workspace_upgrade_tabs.setCurrentIndex(0)
        _wait(
            app,
            lambda: (
                rules._upgrade_candidates
                and rules._workspace_candidate_state(
                    rules._upgrade_candidates[0]
                )
                == "APPLIED_REVALIDATION_REQUIRED"
            ),
            "Reviewer revalidation requirement",
        )
        _show_workspace_upgrade_card(rules)
        capture.screen("28g-workspace-upgrade-revalidation-required")
        rules._continue()
        _wait(
            app,
            lambda: window.current_view_key() == "validation_progress",
            "protected baseline revalidation progress",
        )
        capture.screen("28h-workspace-upgrade-revalidation-progress")
        _wait(
            app,
            lambda: window.current_view_key() == "financial_review_results",
            "protected baseline revalidation results",
            timeout=60,
        )
        financial._results_tabs.setCurrentIndex(0)
        _scroll_active_page(financial, 0)
        capture.screen("28i-workspace-upgrade-revalidated-results")
        financial._results_tabs.setCurrentIndex(4)
        _scroll_active_page(financial, 0)
        capture.screen("28j-rule-edit-and-revalidation-comparison")

        financial._results_tabs.setCurrentIndex(0)
        financial._complete_review()
        capture.screen("29-review-complete")
        window._show_past_reviews()
        _wait(app, lambda: bool(management._past_cards), "Past Reviews")
        capture.screen("30-past-reviews")
        management._past_cards[0].open_button.click()
        _wait(
            app,
            lambda: window.current_view_key() == "financial_review_results",
            "reopened saved results",
            timeout=60,
        )
        _wait(
            app,
            lambda: financial.current_dataset() is not None,
            "reopened saved source rows",
        )
        financial._results_tabs.setCurrentIndex(0)
        _scroll_active_page(financial, 0)
        capture.screen("31-reopened-results")
        financial._results_tabs.setCurrentIndex(4)
        _scroll_active_page(financial, 0)
        capture.screen("31a-reopened-run-comparison")
        financial._results_tabs.setCurrentIndex(3)
        _select_account_drilldown(app, financial, "00-0245|555035")
        _scroll_active_to_widget(
            app,
            financial,
            financial._account_selector,
            top_offset=100,
        )
        capture.screen("31b-reopened-account-financial-hierarchy")
        capture.invoke_modal(
            "32-delete-review-confirmation",
            financial._delete_review,
            _reject_dialog,
        )
        appearance.set_mode(AppearanceMode.SYSTEM)
        _settle(app)
        system_theme = appearance.resolved_palette.name
        window.close()
        appearance.dispose()

    print(
        f"Captured {len(capture.paths)} deterministic screenshots "
        f"({len(capture.paths) // 2} screens × 2 themes) at {WINDOW_SIZE[0]}x"
        f"{WINDOW_SIZE[1]}:"
    )
    print(f"System Default smoke check resolved to: {system_theme}")
    for path in capture.paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
