"""Versioned Rules Repository step in the guided financial-review journey."""
from __future__ import annotations

import json
from typing import Any
import uuid

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finsight.delivery.desktop.components import (
    AdaptiveSidebar,
    NavItem,
    ReviewProgress,
)
from finsight.delivery.desktop.theme import tokens as t
from finsight.application.failure_contracts import safe_failure_message


PROTECTED_RULE_DELETE_TITLE = "This is a protected core rule"
PROTECTED_RULE_DELETE_MESSAGE = (
    "This rule is part of FinSight’s baseline financial controls and cannot "
    "be deleted. Removing it could prevent important budget, GED, mapping, "
    "completeness, or duplicate checks from running.\n\nYou may review the "
    "rule or create a governed replacement version, but the original core "
    "control remains preserved."
)

CORE_RULE_CONDITIONS = {
    "CORE-01": (
        "Summed GED Amount for each Department + Account must not exceed BGT."
    ),
    "CORE-02": (
        "Every GED Department + Account combination must exist in the Budget report."
    ),
    "CORE-03": (
        "Flag GED rows that match across all material transaction fields."
    ),
    "CORE-04": (
        "Required GED fields must be present and parseable."
    ),
    "CORE-05": (
        "Budget ATD must equal summed GED Amount for each Department + Account."
    ),
}


def _label(text: str, role: str = "kvVal", *, wrap: bool = False) -> QLabel:
    label = QLabel(text)
    label.setProperty("role", role)
    label.setWordWrap(wrap)
    return label


def _safe_error(error: BaseException) -> str:
    return safe_failure_message(
        error, fallback_correlation_id="corr_ui_" + uuid.uuid4().hex
    )


def _content_page() -> tuple[QScrollArea, QVBoxLayout]:
    scroll = QScrollArea()
    scroll.setObjectName("Workflow1Page")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    holder = QWidget()
    holder.setObjectName("Workflow1PageCanvas")
    outer = QHBoxLayout(holder)
    outer.setContentsMargins(t.SP_6, t.SP_5, t.SP_6, t.SP_6)
    content = QWidget()
    content.setObjectName("Workflow1Content")
    content.setMaximumWidth(1320)
    layout = QVBoxLayout(content)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(t.SP_4)
    outer.addWidget(content, 1, Qt.AlignmentFlag.AlignTop)
    scroll.setWidget(holder)
    return scroll, layout


def _card() -> tuple[QFrame, QVBoxLayout]:
    card = QFrame()
    card.setProperty("role", "surfaceCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(t.SP_4, t.SP_4, t.SP_4, t.SP_4)
    layout.setSpacing(t.SP_2)
    return card, layout


class OptionalRuleDialog(QDialog):
    """Bounded optional-rule editor; arbitrary expressions are not accepted."""

    def __init__(self, existing: dict[str, Any] | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("OptionalRuleDialog")
        self.setWindowTitle(
            "Edit Optional Rule" if existing else "Add Optional Rule"
        )
        self.setModal(True)
        self.setMinimumWidth(560)
        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        root.addWidget(
            _label(
                "Edit Optional Rule" if existing else "Add Optional Rule",
                "sectionHeader",
            )
        )
        root.addWidget(
            _label(
                "MVP optional rules use an approved deterministic template: "
                "flag GED transactions whose Amount exceeds a configured threshold.",
                "sectionSub",
                wrap=True,
            )
        )
        form = QFormLayout()
        form.setHorizontalSpacing(t.SP_4)
        form.setVerticalSpacing(t.SP_3)
        self.name = QLineEdit()
        self.name.setAccessibleName("Optional rule name")
        self.name.setText(
            str((existing or {}).get("name", "Large GED Transaction"))
        )
        form.addRow("Rule name", self.name)
        self.purpose = QLineEdit()
        self.purpose.setAccessibleName("Optional rule purpose")
        self.purpose.setText(
            str(
                (existing or {}).get(
                    "purpose",
                    "Surface unusually large individual GED transactions for review.",
                )
            )
        )
        form.addRow("Business purpose", self.purpose)
        self.threshold = QLineEdit()
        self.threshold.setAccessibleName("GED Amount threshold")
        parameters = (existing or {}).get("parameters", {})
        self.threshold.setText(str(parameters.get("threshold", "5000.00")))
        form.addRow("Amount threshold", self.threshold)
        self.severity = QComboBox()
        self.severity.setAccessibleName("Optional rule severity")
        self.severity.addItems(("Critical", "High", "Medium", "Low"))
        self.severity.setCurrentText(
            str((existing or {}).get("severity", "Medium"))
        )
        form.addRow("Severity", self.severity)
        root.addLayout(form)
        self.message = _label("", "error", wrap=True)
        self.message.setVisible(False)
        root.addWidget(self.message)
        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setProperty("role", "secondary")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        save = QPushButton(
            "Save New Version" if existing else "Create Draft"
        )
        save.setProperty("role", "primary")
        save.clicked.connect(self._validate_and_accept)
        actions.addWidget(save)
        root.addLayout(actions)

    def _validate_and_accept(self) -> None:
        try:
            threshold = float(self.threshold.text().strip())
        except ValueError:
            threshold = -1
        if not self.name.text().strip() or not self.purpose.text().strip():
            self.message.setText("Enter a rule name and business purpose.")
            self.message.setVisible(True)
            return
        decimals = self.threshold.text().partition(".")[2]
        if threshold < 0 or len(decimals) > 2:
            self.message.setText(
                "Enter a positive amount threshold with no more than two decimals."
            )
            self.message.setVisible(True)
            return
        self.accept()

    def value(self) -> dict[str, Any]:
        return {
            "name": self.name.text().strip(),
            "purpose": self.purpose.text().strip(),
            "severity": self.severity.currentText(),
            "evaluator_key": "ged_amount_threshold",
            "parameters": {
                "operator": "LTE",
                "threshold": f"{float(self.threshold.text().strip()):.2f}",
            },
        }


class ProtectedChangeDialog(QDialog):
    """Bounded authoring surface for one governed protected successor."""

    def __init__(self, existing: dict[str, Any], parent=None):
        super().__init__(parent)
        self.setObjectName("ProtectedChangeDialog")
        self.setWindowTitle("Request Protected Rule Change")
        self.setModal(True)
        self.setMinimumWidth(640)
        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        root.addWidget(_label("Request Protected Rule Change", "sectionHeader"))
        root.addWidget(
            _label(
                "This creates an immutable Tested candidate and a Pending Approval "
                "request. A different Financial Control Approver must decide it.",
                "sectionSub",
                wrap=True,
            )
        )
        form = QFormLayout()
        form.setHorizontalSpacing(t.SP_4)
        form.setVerticalSpacing(t.SP_3)
        self.proposed_version = QLineEdit(
            self._next_version(str(existing.get("version", "")))
        )
        self.proposed_version.setObjectName("ProtectedProposedVersion")
        self.proposed_version.setAccessibleName("Proposed protected rule version")
        form.addRow("Proposed version", self.proposed_version)
        self.change_kind = QComboBox()
        self.change_kind.setObjectName("ProtectedChangeKind")
        self.change_kind.setAccessibleName("Protected change category")
        self.change_kind.addItem("Semantic", "SEMANTIC")
        form.addRow("Change category", self.change_kind)
        self.name = QLineEdit(str(existing.get("name", "")))
        self.name.setAccessibleName("Proposed protected rule name")
        form.addRow("Rule name", self.name)
        self.purpose = QPlainTextEdit(str(existing.get("purpose", "")))
        self.purpose.setObjectName("ProtectedProposedPurpose")
        self.purpose.setAccessibleName("Proposed protected business purpose")
        self.purpose.setMaximumHeight(86)
        form.addRow("Business purpose", self.purpose)
        self.severity = QComboBox()
        self.severity.setAccessibleName("Proposed protected severity")
        self.severity.addItems(("Critical", "High", "Medium", "Low"))
        self.severity.setCurrentText(str(existing.get("severity", "High")))
        form.addRow("Severity", self.severity)
        self.parameters = QPlainTextEdit(
            json.dumps(existing.get("parameters", {}), indent=2, sort_keys=True)
        )
        self.parameters.setObjectName("ProtectedProposedParameters")
        self.parameters.setAccessibleName(
            "Current protected configuration JSON"
        )
        self.parameters.setReadOnly(True)
        self.parameters.setToolTip(
            "No configurable parameters are approved for the five MVP "
            "protected evaluators."
        )
        self.parameters.setMaximumHeight(100)
        form.addRow("Configuration (read only)", self.parameters)
        self.reason = QPlainTextEdit()
        self.reason.setObjectName("ProtectedChangeReason")
        self.reason.setAccessibleName("Protected change business reason")
        self.reason.setPlaceholderText(
            "Explain the policy need and expected future behavior."
        )
        self.reason.setMaximumHeight(86)
        form.addRow("Business reason", self.reason)
        root.addLayout(form)
        self.message = _label("", "error", wrap=True)
        self.message.setAccessibleName("Protected change request error")
        self.message.setVisible(False)
        root.addWidget(self.message)
        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setProperty("role", "secondary")
        cancel.setAccessibleName("Cancel protected change request")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        submit = QPushButton("Submit for Approval")
        submit.setObjectName("SubmitProtectedChange")
        submit.setProperty("role", "primary")
        submit.setAccessibleName("Submit protected change for approval")
        submit.clicked.connect(self._validate_and_accept)
        actions.addWidget(submit)
        root.addLayout(actions)

    @staticmethod
    def _next_version(version: str) -> str:
        parts = version.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            return ""
        return f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"

    def _validate_and_accept(self) -> None:
        try:
            parameters = json.loads(self.parameters.toPlainText() or "{}")
        except json.JSONDecodeError:
            parameters = None
        if (
            not self.proposed_version.text().strip()
            or not self.name.text().strip()
            or not self.purpose.toPlainText().strip()
            or not self.reason.toPlainText().strip()
        ):
            self.message.setText(
                "Enter the proposed version, rule meaning, and business reason."
            )
            self.message.setVisible(True)
            return
        if not isinstance(parameters, dict):
            self.message.setText("Configuration JSON must be a JSON object.")
            self.message.setVisible(True)
            return
        self.accept()

    def value(self) -> dict[str, Any]:
        return {
            "proposed_version": self.proposed_version.text().strip(),
            "change_kind": str(self.change_kind.currentData()),
            "name": self.name.text().strip(),
            "purpose": self.purpose.toPlainText().strip(),
            "severity": self.severity.currentText(),
            "parameters": json.loads(self.parameters.toPlainText() or "{}"),
            "reason": self.reason.toPlainText().strip(),
        }


class ProtectedDecisionDialog(QDialog):
    """Explicit, attributable approval or rejection reason."""

    def __init__(self, request: dict[str, Any], decision: str, parent=None):
        super().__init__(parent)
        self.setObjectName("ProtectedDecisionDialog")
        self._decision = decision.upper()
        verb = "Approve" if self._decision == "APPROVED" else "Reject"
        self.setWindowTitle(f"{verb} Protected Change")
        self.setModal(True)
        self.setMinimumWidth(560)
        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        root.addWidget(_label(f"{verb} Protected Change", "sectionHeader"))
        root.addWidget(
            _label(
                f"{request['rule_id']} · v{request['predecessor_version']} → "
                f"v{request['candidate_version']}\n"
                f"Requested by {request['requester_actor_id']}",
                "sectionSub",
                wrap=True,
            )
        )
        self.reason = QPlainTextEdit()
        self.reason.setObjectName("ProtectedDecisionReason")
        self.reason.setAccessibleName(
            f"{verb} protected change decision reason"
        )
        self.reason.setPlaceholderText(
            "Record the independent control decision and rationale."
        )
        self.reason.setMaximumHeight(110)
        root.addWidget(self.reason)
        self.message = _label("", "error", wrap=True)
        self.message.setVisible(False)
        root.addWidget(self.message)
        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setProperty("role", "secondary")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        submit = QPushButton(verb)
        submit.setObjectName("SubmitProtectedDecision")
        submit.setProperty(
            "role", "primary" if self._decision == "APPROVED" else "destructive"
        )
        submit.setAccessibleName(f"{verb} protected change request")
        submit.clicked.connect(self._validate_and_accept)
        actions.addWidget(submit)
        root.addLayout(actions)

    def _validate_and_accept(self) -> None:
        if not self.reason.toPlainText().strip():
            self.message.setText("Enter a decision reason.")
            self.message.setVisible(True)
            return
        self.accept()

    def value(self) -> dict[str, str]:
        return {
            "decision": self._decision,
            "reason": self.reason.toPlainText().strip(),
        }


class WorkspaceBaselineUpgradeDialog(QDialog):
    """Explicit request to apply one effective protected baseline to a workspace."""

    def __init__(self, status: dict[str, Any], parent=None):
        super().__init__(parent)
        self.setObjectName("WorkspaceBaselineUpgradeDialog")
        self.setWindowTitle("Request Workspace Baseline Upgrade")
        self.setModal(True)
        self.setMinimumWidth(620)
        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        root.addWidget(
            _label("Request Workspace Baseline Upgrade", "sectionHeader")
        )
        root.addWidget(
            _label(
                "This request preserves the current Rule Set and Validation Run. "
                "A different Financial Control Approver must authorize the new "
                "workspace Rule Set before a Reviewer can create the required "
                "successor Review Version and Validation Run.",
                "sectionSub",
                wrap=True,
            )
        )
        evidence, evidence_layout = _card()
        evidence.setAccessibleName("Workspace baseline upgrade evidence")
        grid = QGridLayout()
        for row, (title, value) in enumerate(
            (
                ("Review / workspace", status.get("review_id", "—")),
                (
                    "Current Rule Set",
                    status.get("current_rule_set_id")
                    or status.get("requested_rule_set_id")
                    or "—",
                ),
                (
                    "Current protected baseline",
                    status.get("current_baseline_id")
                    or status.get("source_baseline_id")
                    or "—",
                ),
                (
                    "Target protected baseline",
                    status.get("target_baseline_id")
                    or status.get("current_global_baseline_id")
                    or "—",
                ),
                (
                    "Preserved Validation Run",
                    status.get("latest_run_id") or "—",
                ),
            )
        ):
            grid.addWidget(_label(title, "kvKey"), row, 0)
            field = _label(str(value), "kvVal", wrap=True)
            field.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.TextSelectableByMouse
            )
            grid.addWidget(field, row, 1)
        grid.setColumnStretch(1, 1)
        evidence_layout.addLayout(grid)
        root.addWidget(evidence)
        self.reason = QPlainTextEdit()
        self.reason.setObjectName("WorkspaceUpgradeReason")
        self.reason.setAccessibleName("Workspace baseline upgrade business reason")
        self.reason.setPlaceholderText(
            "Explain why this review should adopt the approved protected baseline."
        )
        self.reason.setMaximumHeight(100)
        root.addWidget(_label("Business reason", "kvKey"))
        root.addWidget(self.reason)
        self.message = _label("", "error", wrap=True)
        self.message.setAccessibleName("Workspace baseline upgrade request error")
        self.message.setVisible(False)
        root.addWidget(self.message)
        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setProperty("role", "secondary")
        cancel.setAccessibleName("Cancel workspace baseline upgrade request")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        submit = QPushButton("Submit for Approval")
        submit.setObjectName("SubmitWorkspaceBaselineUpgrade")
        submit.setProperty("role", "primary")
        submit.setAccessibleName(
            "Submit workspace baseline upgrade for approval"
        )
        submit.clicked.connect(self._validate_and_accept)
        actions.addWidget(submit)
        root.addLayout(actions)

    def _validate_and_accept(self) -> None:
        if not self.reason.toPlainText().strip():
            self.message.setText("Enter a business reason for this upgrade.")
            self.message.setVisible(True)
            return
        self.accept()

    def value(self) -> dict[str, str]:
        return {"reason": self.reason.toPlainText().strip()}


class WorkspaceBaselineDecisionDialog(QDialog):
    """Attributable approval or rejection of one workspace baseline upgrade."""

    def __init__(
        self,
        request: dict[str, Any],
        decision: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("WorkspaceBaselineDecisionDialog")
        self._decision = decision.upper()
        verb = "Authorize" if self._decision == "APPROVED" else "Reject"
        self.setWindowTitle(f"{verb} Workspace Baseline Upgrade")
        self.setModal(True)
        self.setMinimumWidth(600)
        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        root.addWidget(
            _label(f"{verb} Workspace Baseline Upgrade", "sectionHeader")
        )
        root.addWidget(
            _label(
                f"Review {request.get('review_id', '—')}\n"
                f"{request.get('requested_rule_set_id', '—')} → "
                f"{request.get('target_baseline_id', '—')}\n"
                f"Requested by {request.get('requester_actor_id', '—')}",
                "sectionSub",
                wrap=True,
            )
        )
        root.addWidget(
            _label(
                "Authorization creates one successor workspace Rule Set only. "
                "Historical runs remain unchanged, and a Reviewer must create "
                "the successor Review Version and Validation Run.",
                "cardDetail",
                wrap=True,
            )
        )
        self.reason = QPlainTextEdit()
        self.reason.setObjectName("WorkspaceUpgradeDecisionReason")
        self.reason.setAccessibleName(
            f"{verb} workspace baseline upgrade decision reason"
        )
        self.reason.setPlaceholderText(
            "Record the independent control decision and rationale."
        )
        self.reason.setMaximumHeight(110)
        root.addWidget(self.reason)
        self.message = _label("", "error", wrap=True)
        self.message.setVisible(False)
        root.addWidget(self.message)
        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setProperty("role", "secondary")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        submit = QPushButton(verb)
        submit.setObjectName("SubmitWorkspaceBaselineDecision")
        submit.setProperty(
            "role",
            "primary" if self._decision == "APPROVED" else "destructive",
        )
        submit.setAccessibleName(
            f"{verb} workspace baseline upgrade request"
        )
        submit.clicked.connect(self._validate_and_accept)
        actions.addWidget(submit)
        root.addLayout(actions)

    def _validate_and_accept(self) -> None:
        if not self.reason.toPlainText().strip():
            self.message.setText("Enter a decision reason.")
            self.message.setVisible(True)
            return
        self.accept()

    def value(self) -> dict[str, str]:
        return {
            "decision": self._decision,
            "reason": self.reason.toPlainText().strip(),
        }


class RulesRepositoryView(QWidget):
    homeRequested = Signal()
    pastReviewsRequested = Signal()
    settingsRequested = Signal()
    backRequested = Signal(object)
    validationRequested = Signal(object, object, bool)
    askFinRequested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.setObjectName("RulesRepository")
        self._c = controller
        self._review = None
        self._dataset = None
        self._revalidation = False
        self._governance_only = False
        self._rules: list[dict[str, Any]] = []
        self._selected_rule: dict[str, Any] | None = None
        self._active_rule_set_id = ""
        self._rules_ready = False
        self._can_manage_optional = False
        self._can_request_protected = False
        self._can_decide_protected = False
        self._can_request_workspace_upgrade = False
        self._can_authorize_workspace_upgrade = False
        self._can_view_governance = False
        self._current_actor_id = ""
        self._governance_requests: list[dict[str, Any]] = []
        self._selected_governance_request: dict[str, Any] | None = None
        self._workspace_upgrade_status: dict[str, Any] = {}
        self._upgrade_candidates: list[dict[str, Any]] = []
        self._selected_upgrade_candidate: dict[str, Any] | None = None
        self._upgrade_requests: list[dict[str, Any]] = []
        self._selected_upgrade_request: dict[str, Any] | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        workspace = QWidget()
        workspace.setObjectName("Workflow1Workspace")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        workspace_layout.addWidget(self._build_topbar())
        page, layout = _content_page()
        self._build_content(layout)
        workspace_layout.addWidget(page, 1)
        root.addWidget(workspace, 1)

    def _build_sidebar(self) -> QWidget:
        side = AdaptiveSidebar()
        side.setObjectName("Workflow1Sidebar")
        side.setAccessibleName("FinSight primary navigation")
        layout = QVBoxLayout(side)
        layout.setContentsMargins(t.SP_3, t.SP_4, t.SP_3, t.SP_3)
        layout.setSpacing(t.SP_1)
        layout.addWidget(_label("FinSight", "appTitle"))
        layout.addWidget(
            _label("Financial Review Assistant", "context", wrap=True)
        )
        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("REVIEW WORKSPACE", "navGroup"))
        home = NavItem("home", "Home")
        home.activated.connect(lambda _key: self.homeRequested.emit())
        layout.addWidget(home)
        past = NavItem("past", "Past Reviews")
        past.activated.connect(lambda _key: self.pastReviewsRequested.emit())
        layout.addWidget(past)
        self._rules_nav = NavItem("rules", "Review Rules")
        self._rules_nav.setChecked(True)
        layout.addWidget(self._rules_nav)
        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("APPLICATION", "navGroup"))
        self._settings_nav = NavItem("settings", "Settings")
        self._settings_nav.activated.connect(
            lambda _key: self.settingsRequested.emit()
        )
        layout.addWidget(self._settings_nav)
        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("ASSISTANCE", "navGroup"))
        ask = NavItem("ask", "Ask Fin")
        ask.activated.connect(
            lambda _key: self.askFinRequested.emit()
        )
        layout.addWidget(ask)
        layout.addStretch(1)
        return side

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("Workflow1TopBar")
        bar.setFixedHeight(t.TOPBAR_H)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(t.SP_5, 0, t.SP_5, 0)
        self._crumb = _label("Review Rules", "context")
        layout.addWidget(self._crumb)
        layout.addStretch(1)
        self._context = _label("No review selected", "context")
        layout.addWidget(self._context)
        return bar

    def _build_content(self, layout: QVBoxLayout) -> None:
        self._progress = ReviewProgress(3)
        layout.addWidget(self._progress)
        self._back = QPushButton("← Back")
        self._back.setProperty("role", "quiet")
        self._back.setAccessibleName("Back to the previous FinSight view")
        self._back.clicked.connect(
            lambda: self.backRequested.emit(self._review)
        )
        layout.addWidget(self._back, 0, Qt.AlignmentFlag.AlignLeft)

        heading = QHBoxLayout()
        titles = QVBoxLayout()
        self._page_title = _label("Validation Rules", "sectionHeader")
        titles.addWidget(self._page_title)
        self._page_subtitle = _label(
            "These rules determine which financial checks FinSight runs for "
            "this review.",
            "sectionSub",
            wrap=True,
        )
        titles.addWidget(self._page_subtitle)
        heading.addLayout(titles, 1)
        self._add_button = QPushButton("Add Rule")
        self._add_button.setProperty("role", "secondary")
        self._add_button.setAccessibleName("Add optional deterministic rule")
        self._add_button.clicked.connect(self._add_optional)
        heading.addWidget(self._add_button)
        self._validate = QPushButton("Run Validation")
        self._validate.setProperty("role", "primary")
        self._validate.setAccessibleName(
            "Run validation with the active rule set"
        )
        self._validate.clicked.connect(self._continue)
        heading.addWidget(self._validate)
        layout.addLayout(heading)

        self._set_status = _label("", "statusPill", wrap=True)
        self._set_status.setAccessibleName("Bound rule set version")
        self._set_status.setMinimumHeight(38)
        self._set_status.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        layout.addWidget(self._set_status)

        list_card, list_layout = _card()
        list_layout.addWidget(_label("Rules for this review", "cardTitle"))
        self._rule_table = QTreeWidget()
        self._rule_table.setObjectName("ValidationRulesTable")
        self._rule_table.setAccessibleName("Validation rules")
        self._rule_table.setColumnCount(6)
        self._rule_table.setHeaderLabels(
            (
                "Rule",
                "Type",
                "Severity",
                "Status",
                "Last Updated",
                "Actions",
            )
        )
        self._rule_table.setRootIsDecorated(False)
        self._rule_table.setAlternatingRowColors(True)
        self._rule_table.setUniformRowHeights(True)
        self._rule_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._rule_table.currentItemChanged.connect(
            self._select_rule_table_item
        )
        # Header plus five protected baseline rows must be visible at the
        # standard desktop viewport without clipping the final control.
        self._rule_table.setMinimumHeight(304)
        list_layout.addWidget(self._rule_table)
        layout.addWidget(list_card)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setAccessibleName("Rules and selected rule details")
        compatibility_list_card, compatibility_list_layout = _card()
        self._rule_list = QListWidget()
        self._rule_list.setAccessibleName("Bound rules")
        self._rule_list.currentRowChanged.connect(self._select_rule)
        compatibility_list_layout.addWidget(self._rule_list)
        compatibility_list_card.setVisible(False)
        splitter.addWidget(compatibility_list_card)

        detail_card, detail_layout = _card()
        detail_layout.addWidget(_label("Rule details", "cardTitle"))
        self._rule_name = _label("Select a rule.", "cardValue", wrap=True)
        detail_layout.addWidget(self._rule_name)
        self._classification = _label("", "statusPill", wrap=True)
        self._classification.setMinimumHeight(28)
        detail_layout.addWidget(
            self._classification, 0, Qt.AlignmentFlag.AlignLeft
        )
        detail_grid = QGridLayout()
        self._detail_values: dict[str, QLabel] = {}
        for row, (key, title) in enumerate(
            (
                ("purpose", "Purpose"),
                ("severity", "Severity"),
                ("required_fields", "Fields used"),
                ("grouping_keys", "Matching / grouping keys"),
                ("parameters", "Condition"),
                ("version", "Current version"),
                ("lifecycle_status", "Status"),
            )
        ):
            detail_grid.addWidget(_label(title, "kvKey"), row, 0)
            value = _label("—", "kvVal", wrap=True)
            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._detail_values[key] = value
            detail_grid.addWidget(value, row, 1)
        detail_grid.setColumnStretch(1, 1)
        detail_layout.addLayout(detail_grid)
        self._version_history = _label(
            "Previous versions: —", "cardDetail", wrap=True
        )
        self._version_history.setAccessibleName("Previous rule versions")
        detail_layout.addWidget(self._version_history)
        detail_actions = QHBoxLayout()
        self._test_button = QPushButton("Test Rule")
        self._test_button.setProperty("role", "secondary")
        self._test_button.clicked.connect(self._test_selected)
        detail_actions.addWidget(self._test_button)
        self._edit_button = QPushButton("Edit")
        self._edit_button.setProperty("role", "secondary")
        self._edit_button.clicked.connect(self._edit_selected)
        detail_actions.addWidget(self._edit_button)
        self._enable_button = QPushButton("Disable")
        self._enable_button.setProperty("role", "secondary")
        self._enable_button.clicked.connect(self._toggle_enabled)
        detail_actions.addWidget(self._enable_button)
        self._activate_button = QPushButton("Save New Rule Version")
        self._activate_button.setProperty("role", "primary")
        self._activate_button.setAccessibleName(
            "Activate the tested optional rule as a new rule-set version"
        )
        self._activate_button.clicked.connect(self._activate_selected)
        detail_actions.addWidget(self._activate_button)
        self._delete_button = QPushButton("Delete")
        self._delete_button.setProperty("role", "destructive")
        self._delete_button.clicked.connect(self._delete_selected)
        detail_actions.addWidget(self._delete_button)
        detail_actions.addStretch(1)
        detail_layout.addLayout(detail_actions)
        self._governance_note = _label("", "cardDetail", wrap=True)
        detail_layout.addWidget(self._governance_note)
        self._advanced_toggle = QPushButton("Advanced details")
        self._advanced_toggle.setCheckable(True)
        self._advanced_toggle.setProperty("role", "quiet")
        self._advanced_toggle.setAccessibleName(
            "Show or hide advanced rule metadata"
        )
        detail_layout.addWidget(
            self._advanced_toggle, 0, Qt.AlignmentFlag.AlignLeft
        )
        self._advanced_details = _label("", "context", wrap=True)
        self._advanced_details.setVisible(False)
        self._advanced_details.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._advanced_toggle.toggled.connect(
            self._advanced_details.setVisible
        )
        detail_layout.addWidget(self._advanced_details)
        splitter.addWidget(detail_card)
        splitter.setSizes((0, 1000))
        self._rules_splitter = splitter
        layout.addWidget(splitter)

        comparison, comparison_layout = _card()
        comparison_layout.addWidget(
            _label("Validation Run Comparison", "cardTitle")
        )
        self._comparison = _label(
            "No prior run is available. The first validation will establish the baseline.",
            "cardDetail",
            wrap=True,
        )
        comparison_layout.addWidget(self._comparison)
        self._comparison_card = comparison
        layout.addWidget(comparison)

        governance, governance_layout = _card()
        governance_heading = QHBoxLayout()
        governance_titles = QVBoxLayout()
        governance_titles.addWidget(
            _label("Protected Change Governance", "cardTitle")
        )
        governance_titles.addWidget(
            _label(
                "Protected successors remain Pending Approval until a different "
                "Financial Control Approver records a terminal decision. Approval "
                "creates a new global baseline without changing existing workspaces.",
                "cardDetail",
                wrap=True,
            )
        )
        governance_heading.addLayout(governance_titles, 1)
        self._request_protected_button = QPushButton(
            "Request Protected Change"
        )
        self._request_protected_button.setObjectName(
            "RequestProtectedChange"
        )
        self._request_protected_button.setProperty("role", "secondary")
        self._request_protected_button.setAccessibleName(
            "Request a governed protected rule change"
        )
        self._request_protected_button.clicked.connect(
            self._request_protected
        )
        governance_heading.addWidget(self._request_protected_button)
        governance_layout.addLayout(governance_heading)
        governance_splitter = QSplitter(Qt.Orientation.Horizontal)
        governance_splitter.setAccessibleName(
            "Protected rule and workspace upgrade governance history"
        )
        self._governance_request_list = QListWidget()
        self._governance_request_list.setObjectName(
            "ProtectedChangeRequestList"
        )
        self._governance_request_list.setAccessibleName(
            "Protected governance requests"
        )
        self._governance_request_list.currentRowChanged.connect(
            self._select_governance_request
        )
        governance_splitter.addWidget(self._governance_request_list)
        governance_detail = QWidget()
        governance_detail_layout = QVBoxLayout(governance_detail)
        governance_detail_layout.setContentsMargins(
            t.SP_3, t.SP_2, t.SP_2, t.SP_2
        )
        self._governance_detail_values: dict[str, QLabel] = {}
        self._governance_detail_titles: dict[str, QLabel] = {}
        governance_grid = QGridLayout()
        governance_grid.setContentsMargins(0, 0, 0, 0)
        governance_grid.setHorizontalSpacing(t.SP_3)
        governance_grid.setVerticalSpacing(t.SP_1)
        for column in range(4):
            governance_grid.setColumnStretch(column, 1)

        def add_governance_field(
            key: str,
            title: str,
            row: int,
            column: int,
            column_span: int = 1,
        ) -> None:
            title_label = _label(title, "kvKey")
            self._governance_detail_titles[key] = title_label
            governance_grid.addWidget(
                title_label, row, column, 1, column_span
            )
            value = _label("—", "kvVal", wrap=True)
            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._governance_detail_values[key] = value
            governance_grid.addWidget(
                value, row + 1, column, 1, column_span
            )

        add_governance_field("status", "Status", 0, 0)
        add_governance_field("rule_id", "Protected rule", 0, 1)
        add_governance_field(
            "candidate_version", "Proposed version", 0, 2
        )
        add_governance_field(
            "change_kind", "Change category", 0, 3
        )
        add_governance_field(
            "requested_baseline_id", "Baseline at request", 2, 0, 2
        )
        add_governance_field("requester_actor_id", "Requester", 2, 2, 2)
        add_governance_field("reason", "Request reason", 4, 0, 4)
        add_governance_field(
            "before_definition", "Before definition", 6, 0, 2
        )
        add_governance_field(
            "after_definition", "Proposed definition", 6, 2, 2
        )
        add_governance_field(
            "candidate_content_hash", "Candidate content hash", 8, 0, 4
        )
        add_governance_field(
            "qualification_metrics", "Qualification evidence", 10, 0, 4
        )
        add_governance_field(
            "future_effect", "Future binding effect", 12, 0, 4
        )
        add_governance_field(
            "approver_actor_id", "Decision actor", 14, 0, 2
        )
        add_governance_field(
            "decided_at", "Decision timestamp", 14, 2, 2
        )
        add_governance_field(
            "decision_reason", "Decision reason", 16, 0, 4
        )
        add_governance_field(
            "prior_baseline_id", "Prior baseline", 18, 0, 2
        )
        add_governance_field(
            "resulting_baseline_id", "Activated baseline", 18, 2, 2
        )
        governance_detail_layout.addLayout(governance_grid)
        decision_actions = QHBoxLayout()
        self._approve_request_button = QPushButton("Approve")
        self._approve_request_button.setObjectName(
            "ApproveProtectedChange"
        )
        self._approve_request_button.setProperty("role", "primary")
        self._approve_request_button.setAccessibleName(
            "Approve selected protected governance request"
        )
        self._approve_request_button.clicked.connect(
            lambda: self._decide_protected("APPROVED")
        )
        decision_actions.addWidget(self._approve_request_button)
        self._reject_request_button = QPushButton("Reject")
        self._reject_request_button.setObjectName("RejectProtectedChange")
        self._reject_request_button.setProperty("role", "destructive")
        self._reject_request_button.setAccessibleName(
            "Reject selected protected governance request"
        )
        self._reject_request_button.clicked.connect(
            lambda: self._decide_protected("REJECTED")
        )
        decision_actions.addWidget(self._reject_request_button)
        decision_actions.addStretch(1)
        governance_detail_layout.addLayout(decision_actions)
        governance_splitter.addWidget(governance_detail)
        governance_splitter.setSizes((500, 700))
        governance_layout.addWidget(governance_splitter)
        self._governance_message = _label("", "cardDetail", wrap=True)
        self._governance_message.setAccessibleName(
            "Protected governance status"
        )
        governance_layout.addWidget(self._governance_message)
        self._governance_card = governance
        layout.addWidget(governance)
        self._build_workspace_upgrade_card(layout)

        self._message = _label("", "cardDetail", wrap=True)
        self._message.setAccessibleName("Rule repository status")
        layout.addWidget(self._message)
        self._actions_bar = QWidget()
        self._actions_bar.setVisible(False)

    def _build_workspace_upgrade_card(self, layout: QVBoxLayout) -> None:
        card, card_layout = _card()
        card.setObjectName("WorkspaceBaselineGovernanceCard")
        card.setAccessibleName("Workspace protected baseline governance")
        card_layout.addWidget(
            _label("Workspace Baseline Upgrades", "cardTitle")
        )
        card_layout.addWidget(
            _label(
                "An effective protected baseline never moves an existing "
                "workspace silently. A Rule Administrator requests one exact "
                "upgrade, a different Financial Control Approver authorizes it, "
                "and a Reviewer runs the required deterministic revalidation.",
                "cardDetail",
                wrap=True,
            )
        )
        tabs = QTabWidget()
        tabs.setObjectName("WorkspaceUpgradeTabs")
        tabs.setAccessibleName("Workspace baseline upgrade governance")

        candidates = QWidget()
        candidate_layout = QHBoxLayout(candidates)
        candidate_layout.setContentsMargins(
            t.SP_2, t.SP_3, t.SP_2, t.SP_2
        )
        candidate_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._upgrade_candidate_list = QListWidget()
        self._upgrade_candidate_list.setObjectName(
            "WorkspaceUpgradeCandidateList"
        )
        self._upgrade_candidate_list.setAccessibleName(
            "Workspace protected baseline status"
        )
        self._upgrade_candidate_list.setWordWrap(True)
        self._upgrade_candidate_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._upgrade_candidate_list.currentRowChanged.connect(
            self._select_workspace_upgrade_candidate
        )
        candidate_splitter.addWidget(self._upgrade_candidate_list)
        candidate_detail = QWidget()
        candidate_detail_layout = QVBoxLayout(candidate_detail)
        candidate_detail_layout.setContentsMargins(
            t.SP_3, t.SP_2, t.SP_2, t.SP_2
        )
        candidate_grid = QGridLayout()
        self._upgrade_candidate_values: dict[str, QLabel] = {}
        for row, (key, title) in enumerate(
            (
                ("state", "Upgrade state"),
                ("review_id", "Review / workspace"),
                ("current_rule_set_id", "Current Rule Set"),
                ("current_baseline_id", "Current protected baseline"),
                ("target_baseline_id", "Target effective baseline"),
                ("latest_run_id", "Preserved Validation Run"),
                ("reason", "Eligibility / next action"),
            )
        ):
            candidate_grid.addWidget(_label(title, "kvKey"), row, 0)
            value = _label("—", "kvVal", wrap=True)
            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._upgrade_candidate_values[key] = value
            candidate_grid.addWidget(value, row, 1)
        candidate_grid.setColumnStretch(1, 1)
        candidate_detail_layout.addLayout(candidate_grid)
        candidate_actions = QHBoxLayout()
        self._request_workspace_upgrade_button = QPushButton(
            "Request Baseline Upgrade"
        )
        self._request_workspace_upgrade_button.setObjectName(
            "RequestWorkspaceBaselineUpgrade"
        )
        self._request_workspace_upgrade_button.setProperty(
            "role", "primary"
        )
        self._request_workspace_upgrade_button.setAccessibleName(
            "Request the selected protected baseline workspace upgrade"
        )
        self._request_workspace_upgrade_button.clicked.connect(
            self._request_workspace_upgrade
        )
        candidate_actions.addWidget(
            self._request_workspace_upgrade_button
        )
        candidate_actions.addStretch(1)
        candidate_detail_layout.addLayout(candidate_actions)
        candidate_splitter.addWidget(candidate_detail)
        candidate_splitter.setSizes((430, 770))
        candidate_layout.addWidget(candidate_splitter)
        tabs.addTab(candidates, "Workspace Status")

        requests = QWidget()
        request_layout = QHBoxLayout(requests)
        request_layout.setContentsMargins(
            t.SP_2, t.SP_3, t.SP_2, t.SP_2
        )
        request_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._upgrade_request_list = QListWidget()
        self._upgrade_request_list.setObjectName(
            "WorkspaceUpgradeRequestList"
        )
        self._upgrade_request_list.setAccessibleName(
            "Workspace baseline upgrade requests"
        )
        self._upgrade_request_list.setWordWrap(True)
        self._upgrade_request_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._upgrade_request_list.currentRowChanged.connect(
            self._select_workspace_upgrade_request
        )
        request_splitter.addWidget(self._upgrade_request_list)
        request_detail = QWidget()
        request_detail_layout = QVBoxLayout(request_detail)
        request_detail_layout.setContentsMargins(
            t.SP_3, t.SP_2, t.SP_2, t.SP_2
        )
        request_grid = QGridLayout()
        request_grid.setHorizontalSpacing(t.SP_3)
        request_grid.setVerticalSpacing(t.SP_1)
        self._upgrade_request_values: dict[str, QLabel] = {}
        request_fields = (
            ("status", "Status", 0, 0),
            ("review_id", "Review / workspace", 0, 1),
            ("requested_rule_set_id", "Rule Set at request", 2, 0),
            ("requested_run_id", "Validation Run at request", 2, 1),
            ("source_baseline_id", "Source baseline", 4, 0),
            ("target_baseline_id", "Target baseline", 4, 1),
            ("requester_actor_id", "Requester", 6, 0),
            ("requested_at", "Requested at", 6, 1),
            ("reason", "Request reason", 8, 0),
            ("approver_actor_id", "Decision actor", 10, 0),
            ("decided_at", "Decision timestamp", 10, 1),
            ("decision_reason", "Decision reason", 12, 0),
            ("resulting_rule_set_id", "Resulting Rule Set", 14, 0),
            ("applied_at", "Applied at", 14, 1),
            ("evidence", "Protected binding evidence", 16, 0),
            ("effect", "Effect and next action", 18, 0),
        )
        self._upgrade_request_titles: dict[str, QLabel] = {}
        for key, title, row, column in request_fields:
            span = 2 if key in {
                "reason",
                "decision_reason",
                "evidence",
                "effect",
            } else 1
            title_label = _label(title, "kvKey")
            self._upgrade_request_titles[key] = title_label
            request_grid.addWidget(
                title_label, row, column, 1, span
            )
            value = _label("—", "kvVal", wrap=True)
            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._upgrade_request_values[key] = value
            request_grid.addWidget(
                value, row + 1, column, 1, span
            )
        request_grid.setColumnStretch(0, 1)
        request_grid.setColumnStretch(1, 1)
        request_detail_layout.addLayout(request_grid)
        decision_actions = QHBoxLayout()
        self._authorize_upgrade_button = QPushButton(
            "Authorize & Apply"
        )
        self._authorize_upgrade_button.setObjectName(
            "AuthorizeWorkspaceBaselineUpgrade"
        )
        self._authorize_upgrade_button.setProperty("role", "primary")
        self._authorize_upgrade_button.setAccessibleName(
            "Authorize and apply selected workspace baseline upgrade"
        )
        self._authorize_upgrade_button.clicked.connect(
            lambda: self._decide_workspace_upgrade("APPROVED")
        )
        decision_actions.addWidget(self._authorize_upgrade_button)
        self._reject_upgrade_button = QPushButton("Reject")
        self._reject_upgrade_button.setObjectName(
            "RejectWorkspaceBaselineUpgrade"
        )
        self._reject_upgrade_button.setProperty("role", "destructive")
        self._reject_upgrade_button.setAccessibleName(
            "Reject selected workspace baseline upgrade"
        )
        self._reject_upgrade_button.clicked.connect(
            lambda: self._decide_workspace_upgrade("REJECTED")
        )
        decision_actions.addWidget(self._reject_upgrade_button)
        decision_actions.addStretch(1)
        request_detail_layout.addLayout(decision_actions)
        request_splitter.addWidget(request_detail)
        request_splitter.setSizes((430, 770))
        request_layout.addWidget(request_splitter)
        tabs.addTab(requests, "Requests && Decisions")

        self._workspace_upgrade_tabs = tabs
        card_layout.addWidget(tabs)
        self._workspace_upgrade_message = _label(
            "", "cardDetail", wrap=True
        )
        self._workspace_upgrade_message.setAccessibleName(
            "Workspace baseline governance status"
        )
        card_layout.addWidget(self._workspace_upgrade_message)
        self._workspace_upgrade_card = card
        layout.addWidget(card)

    def open_review(self, review, dataset, *, revalidation: bool = False) -> None:
        self._set_governance_only(False)
        self._review = review
        self._dataset = dataset
        self._revalidation = revalidation
        self._context.setText(
            f"Active review: {review.period.label} · {review.status.value}"
        )
        self._back.setText("← Back")
        self._validate.setText(
            "Create New Validation Run" if revalidation else "Run Validation"
        )
        try:
            roles = set(
                self._c.review_management_availability().role_labels
            )
        except Exception:
            roles = set()
        self._can_manage_optional = "Rule Administrator" in roles
        self._can_request_protected = "Rule Administrator" in roles
        self._can_request_workspace_upgrade = (
            "Rule Administrator" in roles
        )
        self._can_decide_protected = (
            "Financial Control Approver" in roles
        )
        self._can_authorize_workspace_upgrade = (
            "Financial Control Approver" in roles
        )
        self._can_view_governance = bool(
            roles
            & {
                "Rule Administrator",
                "Financial Control Approver",
            }
        )
        self._current_actor_id = self._c.current_actor_id()
        self._add_button.setEnabled(self._can_manage_optional)
        self._add_button.setToolTip(
            "Create a governed optional rule."
            if self._can_manage_optional
            else "A Rule Administrator role is required."
        )
        self.refresh()

    def open_governance_queue(self) -> None:
        """Open the global protected-change queue without review data."""

        self._review = None
        self._dataset = None
        self._revalidation = False
        self._set_governance_only(True)
        try:
            roles = set(
                self._c.review_management_availability().role_labels
            )
        except Exception:
            roles = set()
        self._can_manage_optional = False
        self._can_request_protected = False
        self._can_request_workspace_upgrade = (
            "Rule Administrator" in roles
        )
        self._can_decide_protected = (
            "Financial Control Approver" in roles
        )
        self._can_authorize_workspace_upgrade = (
            "Financial Control Approver" in roles
        )
        self._can_view_governance = bool(
            roles
            & {
                "Rule Administrator",
                "Financial Control Approver",
            }
        )
        self._current_actor_id = self._c.current_actor_id()
        self._context.setText("Protected governance queue")
        self._refresh_governance()
        self._refresh_workspace_upgrades()
        self._back.setFocus()

    def _set_governance_only(self, enabled: bool) -> None:
        self._governance_only = bool(enabled)
        self._progress.setVisible(not enabled)
        self._set_status.setVisible(not enabled)
        self._rule_table.setVisible(not enabled)
        self._rule_table.parentWidget().setVisible(not enabled)
        self._rules_splitter.setVisible(not enabled)
        self._comparison_card.setVisible(not enabled)
        self._message.setVisible(not enabled)
        self._add_button.setVisible(not enabled)
        self._validate.setVisible(not enabled)
        self._request_protected_button.setVisible(not enabled)
        self._governance_card.setVisible(enabled)
        self._workspace_upgrade_card.setVisible(enabled)
        self._crumb.setText(
            "Advanced Governance" if enabled else "Validation Rules"
        )
        self._rules_nav.setText(
            "Advanced Governance" if enabled else "Validation Rules"
        )
        self._page_title.setText(
            "Advanced Governance"
            if enabled
            else "Validation Rules"
        )
        self._page_subtitle.setText(
            (
                "Administrative controls for protected-rule requests and "
                "workspace baseline upgrades."
            )
            if enabled
            else (
                "These rules determine which financial checks FinSight runs "
                "for this review."
            )
        )
        self._back.setText("← Back")

    def refresh(self) -> None:
        if self._governance_only:
            self._refresh_governance()
            self._refresh_workspace_upgrades()
            return
        if self._review is None:
            return
        try:
            projection = self._c.bound_rules(self._review.review_id)
        except Exception as exc:
            self._message.setText(
                "Rules could not be loaded. Return to Verify Data and try again. "
                + _safe_error(exc)
            )
            self._validate.setEnabled(False)
            return
        if isinstance(projection, dict):
            self._rules = list(projection.get("rules", ()))
            self._active_rule_set_id = str(
                projection.get("rule_set_id", "")
            )
        else:
            self._rules = list(projection)
        self._workspace_upgrade_status = {}
        if hasattr(self._c, "workspace_upgrade_status"):
            try:
                self._workspace_upgrade_status = dict(
                    self._c.workspace_upgrade_status(
                        self._review.review_id
                    )
                    or {}
                )
            except Exception as exc:
                self._message.setText(
                    "Workspace baseline status could not be loaded. "
                    + _safe_error(exc)
                )
        core_count = sum(
            rule.get("baseline_status") == "PROTECTED_BASELINE"
            for rule in self._rules
        )
        optional_count = len(self._rules) - core_count
        status_text = (
            f"Active Rule Set · {core_count} core rules · "
            f"{optional_count} optional rules"
        )
        self._set_status.setText(status_text)
        upgrade_available = bool(
            self._workspace_upgrade_status.get("upgrade_available")
        )
        pending_upgrade = bool(
            self._workspace_upgrade_status.get("pending_request_id")
            or self._workspace_upgrade_status.get("pending_request")
            or (
                isinstance(
                    self._workspace_upgrade_status.get("latest_request"),
                    dict,
                )
                and self._workspace_upgrade_status["latest_request"].get(
                    "status"
                )
                == "PENDING_APPROVAL"
            )
        )
        self._request_workspace_upgrade_button.setEnabled(
            self._can_request_workspace_upgrade
            and upgrade_available
            and not pending_upgrade
        )
        self._request_workspace_upgrade_button.setToolTip(
            (
                "Request independent authorization to apply the effective "
                "protected baseline to this existing review."
                if upgrade_available and not pending_upgrade
                else (
                    "A workspace baseline upgrade is already Pending Approval."
                    if pending_upgrade
                    else (
                        "This workspace already uses the effective protected "
                        "baseline."
                        if self._can_request_workspace_upgrade
                        else "A Rule Administrator role is required."
                    )
                )
            )
        )
        self._rule_list.clear()
        self._rule_table.clear()
        for rule in self._rules:
            classification = (
                "Protected Core Rule"
                if rule.get("baseline_status") == "PROTECTED_BASELINE"
                else "Optional Rule"
            )
            status = (
                "Disabled"
                if rule.get("bound") and not rule.get("enabled", True)
                else str(rule.get("lifecycle_status", "ACTIVE")).title()
            )
            item = QListWidgetItem(
                f"{rule.get('name', rule.get('rule_id', 'Rule'))}\n"
                f"{classification} · {status} · v{rule.get('version', '—')}"
            )
            item.setData(Qt.ItemDataRole.UserRole, rule)
            self._rule_list.addItem(item)
            updated = str(
                rule.get("updated_at")
                or rule.get("created_at")
                or rule.get("effective_at")
                or "—"
            )
            if "T" in updated:
                updated = updated.split("T", 1)[0]
            table_item = QTreeWidgetItem(
                (
                    str(rule.get("name", rule.get("rule_id", "Rule"))),
                    (
                        "Core Rule"
                        if classification == "Protected Core Rule"
                        else "Optional"
                    ),
                    str(rule.get("severity") or "—").title(),
                    status,
                    updated,
                    "View",
                )
            )
            table_item.setData(0, Qt.ItemDataRole.UserRole, rule)
            self._rule_table.addTopLevelItem(table_item)
            if classification == "Protected Core Rule":
                table_item.setToolTip(
                    1,
                    "Core rules are protected baseline financial controls.",
                )
            table_item.setToolTip(
                5, "Open the selected rule details below."
            )
        for column in range(6):
            self._rule_table.resizeColumnToContents(column)
        self._rule_table.header().setStretchLastSection(False)
        self._rule_table.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._rules_ready = (
            sum(
                rule.get("baseline_status") == "PROTECTED_BASELINE"
                and rule.get("enabled", True)
                for rule in self._rules
            )
            >= 5
        )
        self._validate.setEnabled(self._rules_ready)
        if self._rule_list.count():
            self._rule_list.setCurrentRow(0)
        if self._rule_table.topLevelItemCount():
            self._rule_table.setCurrentItem(
                self._rule_table.topLevelItem(0)
            )
        self._refresh_comparison()
        self._refresh_governance()
        self._refresh_workspace_upgrades()

    def _select_rule_table_item(
        self,
        current: QTreeWidgetItem | None,
        _previous: QTreeWidgetItem | None,
    ) -> None:
        if current is None:
            return
        rule = current.data(0, Qt.ItemDataRole.UserRole)
        try:
            row = self._rules.index(rule)
        except ValueError:
            return
        self._rule_list.setCurrentRow(row)

    def _refresh_comparison(self) -> None:
        if self._review is None:
            return
        try:
            history = self._c.validation_history(self._review.review_id)
        except Exception:
            history = []
        if not history:
            self._comparison.setText(
                "No prior run is available. The first validation will establish the baseline."
            )
            self._comparison_card.setVisible(False)
            return
        self._comparison_card.setVisible(True)
        latest = history[-1]
        metrics = latest.get("metrics", {})
        if self._revalidation and latest.get("rule_set_id") == self._active_rule_set_id:
            self._comparison.setText(
                "The current results already use this Rule Set Version. "
                "Create, activate, enable, disable, or retire an optional rule "
                "before creating another validation run."
            )
            self._validate.setEnabled(False)
            return
        self._validate.setEnabled(self._rules_ready)
        self._comparison.setText(
            f"Prior run preserved · {metrics.get('rules_passed', 0)} rules passed · "
            f"{metrics.get('rules_failed', 0)} failed · "
            f"{metrics.get('findings', 0)} findings. The next run will be stored "
            "as a separate version for comparison."
        )

    def _select_rule(self, row: int) -> None:
        if row < 0 or row >= len(self._rules):
            return
        rule = self._rules[row]
        self._selected_rule = rule
        protected = rule.get("baseline_status") == "PROTECTED_BASELINE"
        lifecycle = str(rule.get("lifecycle_status", "ACTIVE"))
        bound = bool(rule.get("bound", True))
        enabled = bool(rule.get("enabled", True))
        self._rule_name.setText(str(rule.get("name", rule.get("rule_id", "Rule"))))
        self._classification.setText(
            "Core Rule · Protected" if protected else "Optional Rule"
        )
        for key, label in self._detail_values.items():
            value = rule.get(key, "—")
            if key == "parameters" and not value:
                text = CORE_RULE_CONDITIONS.get(
                    str(rule.get("rule_id", "")),
                    "No additional condition is configured.",
                )
            elif isinstance(value, dict):
                operator = value.get("operator")
                threshold = value.get("threshold")
                if operator and threshold is not None:
                    text = (
                        f"GED Amount {operator} {threshold} for each matching "
                        "Department + Account."
                    )
                else:
                    text = " · ".join(
                        f"{name}: {item}" for name, item in value.items()
                    )
            elif isinstance(value, (list, tuple)):
                text = ", ".join(str(item) for item in value) or "None"
            else:
                text = str(value or "—")
            label.setText(text)
        previous_versions = tuple(rule.get("previous_versions") or ())
        if previous_versions:
            rendered_versions = ", ".join(
                str(
                    item.get("version", "—")
                    if isinstance(item, dict)
                    else item
                )
                for item in previous_versions
            )
        else:
            rendered_versions = "None recorded"
        self._version_history.setText(
            f"Previous versions: {rendered_versions}"
        )
        self._advanced_details.setText(
            "\n".join(
                (
                    f"Rule ID: {rule.get('rule_id', '—')}",
                    f"Rule Set: {self._active_rule_set_id or '—'}",
                    f"Baseline status: {rule.get('baseline_status', '—')}",
                    f"Evaluator: {rule.get('evaluator_key', '—')}",
                )
            )
        )
        self._test_button.setEnabled(
            self._can_manage_optional
            and not protected
            and lifecycle in {"DRAFT", "TESTED"}
        )
        self._edit_button.setEnabled(
            (
                self._can_request_protected
                if protected
                else self._can_manage_optional
            )
        )
        self._edit_button.setText(
            "Create New Version" if protected else "Edit"
        )
        self._enable_button.setEnabled(
            self._can_manage_optional
            and not protected
            and bound
            and lifecycle == "ACTIVE"
        )
        self._delete_button.setEnabled(
            self._can_manage_optional
            and lifecycle != "RETIRED"
        )
        if protected:
            self._delete_button.setToolTip(
                "Protected core rules cannot be deleted. Select Delete to "
                "review the protected-control explanation."
            )
        else:
            self._delete_button.setToolTip(
                "Retire this rule from future validation while preserving "
                "historical versions and results."
            )
        self._activate_button.setEnabled(
            self._can_manage_optional
            and not protected
            and lifecycle == "TESTED"
            and not bound
        )
        self._enable_button.setText(
            "Enable" if bound and not enabled else "Disable"
        )
        self._request_protected_button.setEnabled(
            self._can_request_protected and protected
        )
        self._request_protected_button.setToolTip(
            "Create an immutable Tested successor and submit it for independent approval."
            if self._can_request_protected and protected
            else (
                "Select a protected rule."
                if self._can_request_protected
                else "A Rule Administrator role is required."
            )
        )
        self._governance_note.setText(
            "This baseline control is protected. Changes use a governed new "
            "version so prior results remain reproducible."
            if protected
            else (
                "Changes create a new version. Disabling or retiring this rule "
                "affects future validations only; historical results remain."
                if self._can_manage_optional
                else "A Rule Administrator can test, version, enable, disable, "
                "or retire this optional rule."
            )
        )

    def _request_protected(self) -> None:
        rule = self._selected_rule
        if (
            rule is None
            or rule.get("baseline_status") != "PROTECTED_BASELINE"
        ):
            return
        dialog = ProtectedChangeDialog(
            rule.get("governance_current") or rule,
            self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            request = self._c.request_protected_change(
                self._review.review_id,
                self._dataset,
                str(rule["rule_id"]),
                dialog.value(),
            )
        except Exception as exc:
            QMessageBox.warning(
                self, "Protected request not submitted", _safe_error(exc)
            )
            return
        self._governance_message.setText(
            f"{request['rule_id']} v{request['candidate_version']} is Pending "
            "Approval. The active baseline is unchanged."
        )
        self.refresh()

    def _request_workspace_upgrade(self) -> None:
        candidate = (
            self._selected_upgrade_candidate
            or self._workspace_upgrade_status
        )
        review_id = candidate.get("review_id")
        if not review_id:
            return
        dialog = WorkspaceBaselineUpgradeDialog(
            candidate,
            self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            request = self._c.request_workspace_upgrade(
                str(review_id),
                reason=dialog.value()["reason"],
                target_baseline_id=candidate.get("target_baseline_id"),
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Workspace upgrade not submitted",
                _safe_error(exc),
            )
            return
        target = request.get(
            "target_baseline_id", "the effective protected baseline"
        )
        self._governance_message.setText(
            f"Workspace upgrade to {target} is Pending Approval. The current "
            "Rule Set and Validation Run are unchanged."
        )
        self._workspace_upgrade_tabs.setCurrentIndex(1)
        if self._governance_only:
            self._refresh_workspace_upgrades()
        else:
            self.refresh()

    def _refresh_workspace_upgrades(self) -> None:
        self._upgrade_candidates = []
        self._upgrade_requests = []
        self._selected_upgrade_candidate = None
        self._selected_upgrade_request = None
        self._upgrade_candidate_list.clear()
        self._upgrade_request_list.clear()
        for value in self._upgrade_candidate_values.values():
            value.setText("—")
        for value in self._upgrade_request_values.values():
            value.setText("—")
        self._request_workspace_upgrade_button.setEnabled(False)
        self._authorize_upgrade_button.setEnabled(False)
        self._reject_upgrade_button.setEnabled(False)

        if self._governance_only:
            if (
                self._can_request_workspace_upgrade
                and hasattr(self._c, "workspace_upgrade_candidates")
            ):
                try:
                    self._upgrade_candidates = list(
                        self._c.workspace_upgrade_candidates()
                    )
                except Exception as exc:
                    self._workspace_upgrade_message.setText(
                        "Eligible workspaces could not be loaded. "
                        + _safe_error(exc)
                    )
                    return
        elif self._review is not None:
            status = dict(self._workspace_upgrade_status or {})
            if status:
                status.setdefault("review_id", self._review.review_id)
                self._upgrade_candidates = [status]

        if (
            self._can_request_workspace_upgrade
            or self._can_authorize_workspace_upgrade
        ) and hasattr(self._c, "workspace_upgrade_requests"):
            try:
                self._upgrade_requests = list(
                    self._c.workspace_upgrade_requests(
                        review_id=(
                            None
                            if self._governance_only
                            else self._review.review_id
                        ),
                        for_decision=self._can_authorize_workspace_upgrade,
                    )
                )
            except Exception as exc:
                self._workspace_upgrade_message.setText(
                    "Workspace upgrade history could not be loaded. "
                    + _safe_error(exc)
                )
                return

        for candidate in self._upgrade_candidates:
            state = self._workspace_candidate_state(candidate)
            review_label = self._compact_workspace_identifier(
                candidate.get("review_id"), "Review"
            )
            current_label = self._compact_workspace_identifier(
                candidate.get("current_baseline_id")
                or candidate.get("source_baseline_id"),
                "Baseline",
            )
            target_label = self._compact_workspace_identifier(
                candidate.get("target_baseline_id"), "Baseline"
            ) if candidate.get("target_baseline_id") else "No newer baseline"
            item = QListWidgetItem(
                f"{review_label}\n"
                f"{state.replace('_', ' ').title()} · "
                f"{current_label} → {target_label}"
            )
            item.setData(Qt.ItemDataRole.UserRole, candidate)
            self._upgrade_candidate_list.addItem(item)
        for request in self._upgrade_requests:
            review_label = self._compact_workspace_identifier(
                request.get("review_id"), "Review"
            )
            target_label = self._compact_workspace_identifier(
                request.get("target_baseline_id"), "Baseline"
            )
            item = QListWidgetItem(
                f"{review_label}\n"
                f"{str(request.get('status', 'UNKNOWN')).replace('_', ' ').title()} · "
                f"{target_label}"
            )
            item.setData(Qt.ItemDataRole.UserRole, request)
            self._upgrade_request_list.addItem(item)

        if self._upgrade_candidates:
            self._upgrade_candidate_list.setCurrentRow(0)
        if self._upgrade_requests:
            self._upgrade_request_list.setCurrentRow(0)

        if self._can_authorize_workspace_upgrade and not (
            self._can_request_workspace_upgrade
        ):
            self._workspace_upgrade_tabs.setCurrentIndex(1)
        if self._upgrade_requests:
            self._workspace_upgrade_message.setText(
                "Request-time Rule Set, target baseline, actor, decision, "
                "and resulting Rule Set evidence are retained for replay."
            )
        elif self._upgrade_candidates:
            self._workspace_upgrade_message.setText(
                "Select a workspace to inspect its protected-baseline state "
                "and permitted next action."
            )
        else:
            self._workspace_upgrade_message.setText(
                "No eligible workspace upgrades or governed requests are "
                "available for this role."
            )

    @staticmethod
    def _compact_workspace_identifier(value: Any, prefix: str) -> str:
        text = str(value or "").strip()
        if not text:
            return f"{prefix} —"
        if prefix == "Baseline":
            if text.startswith("FINSIGHT-CORE-GOV-"):
                return f"Core GOV …{text[-8:]}"
            if text.startswith("FINSIGHT-CORE-"):
                return f"Core {text.removeprefix('FINSIGHT-CORE-')}"
        if len(text) <= 16:
            return f"{prefix} {text}"
        return f"{prefix} …{text[-8:]}"

    @staticmethod
    def _workspace_candidate_state(candidate: dict[str, Any]) -> str:
        latest_request = candidate.get("latest_request")
        if (
            isinstance(latest_request, dict)
            and latest_request.get("status") == "PENDING_APPROVAL"
        ):
            stale = any(
                (
                    latest_request.get("requested_rule_set_id")
                    != candidate.get("current_rule_set_id"),
                    latest_request.get("target_baseline_id")
                    != candidate.get("target_baseline_id"),
                    latest_request.get("requested_run_id")
                    != candidate.get("latest_run_id"),
                )
            )
            return "STALE_PENDING" if stale else "PENDING_APPROVAL"
        raw = str(
            candidate.get("state")
            or candidate.get("workspace_upgrade_state")
            or candidate.get("upgrade_state")
            or (
                "PENDING_APPROVAL"
                if candidate.get("pending_request_id")
                else (
                    "UPGRADE_AVAILABLE"
                    if candidate.get("upgrade_available")
                    else "UP_TO_DATE"
                )
            )
        ).upper()
        return {
            "CURRENT": "UP_TO_DATE",
            "AVAILABLE": "UPGRADE_AVAILABLE",
            "APPLIED": "APPLIED_REVALIDATION_REQUIRED",
        }.get(raw, raw)

    def _select_workspace_upgrade_candidate(self, row: int) -> None:
        if row < 0 or row >= len(self._upgrade_candidates):
            return
        candidate = self._upgrade_candidates[row]
        self._selected_upgrade_candidate = candidate
        state = self._workspace_candidate_state(candidate)
        for key, label in self._upgrade_candidate_values.items():
            if key == "state":
                value = state.replace("_", " ").title()
            elif key == "current_baseline_id":
                value = (
                    candidate.get(key)
                    or candidate.get("source_baseline_id")
                )
            elif key == "latest_run_id":
                value = (
                    candidate.get(key)
                    or candidate.get("requested_run_id")
                )
            elif key == "reason":
                if state in {
                    "PENDING_APPROVAL",
                    "STALE_PENDING",
                    "APPLIED_REVALIDATION_REQUIRED",
                    "VALIDATED",
                }:
                    value = self._workspace_candidate_next_action(state)
                else:
                    value = (
                        candidate.get("reason")
                        or candidate.get("state_reason")
                        or candidate.get("upgrade_reason")
                        or self._workspace_candidate_next_action(state)
                    )
            else:
                value = candidate.get(key)
            label.setText(str(value or "—"))
        can_request = (
            self._can_request_workspace_upgrade
            and state == "UPGRADE_AVAILABLE"
        )
        self._request_workspace_upgrade_button.setEnabled(can_request)
        self._request_workspace_upgrade_button.setToolTip(
            ""
            if can_request
            else (
                "A Rule Administrator may request only an eligible, newer "
                "effective baseline."
            )
        )

    @staticmethod
    def _workspace_candidate_next_action(state: str) -> str:
        return {
            "UP_TO_DATE": "No action is required.",
            "UPGRADE_AVAILABLE": (
                "A Rule Administrator may submit this exact target for "
                "independent authorization."
            ),
            "PENDING_APPROVAL": (
                "The current Rule Set remains active while the request awaits "
                "a different Financial Control Approver."
            ),
            "STALE_PENDING": (
                "The request can no longer be approved; it may still be rejected."
            ),
            "APPLIED_REVALIDATION_REQUIRED": (
                "A Reviewer must run deterministic revalidation. The governed "
                "service will create the successor Review Version."
            ),
            "VALIDATED": "The effective baseline has a completed Validation Run.",
            "NOT_ELIGIBLE": "This workspace is not eligible for upgrade.",
            "BLOCKED": "The upgrade is blocked by persisted lifecycle evidence.",
        }.get(state, "Review the persisted governance evidence.")

    def _select_workspace_upgrade_request(self, row: int) -> None:
        if row < 0 or row >= len(self._upgrade_requests):
            return
        request = self._upgrade_requests[row]
        self._selected_upgrade_request = request
        for key, label in self._upgrade_request_values.items():
            if key == "status":
                value = str(
                    request.get("status", "UNKNOWN")
                ).replace("_", " ").title()
            elif key == "requested_run_id":
                value = (
                    request.get(key) or request.get("latest_run_id")
                )
            elif key == "effect":
                value = self._workspace_upgrade_effect(request)
            elif key == "evidence":
                value = self._workspace_upgrade_evidence(request)
            else:
                value = request.get(key)
            label.setText(str(value or "—"))
        terminal = request.get("status") in {
            "APPROVED",
            "APPLIED",
            "REJECTED",
        }
        for key in (
            "approver_actor_id",
            "decided_at",
            "decision_reason",
            "resulting_rule_set_id",
            "applied_at",
        ):
            visible = terminal and bool(request.get(key))
            self._upgrade_request_titles[key].setVisible(visible)
            self._upgrade_request_values[key].setVisible(visible)
        self_request = (
            request.get("requester_actor_id") == self._current_actor_id
        )
        stale = bool(request.get("stale")) or str(
            request.get("state", "")
        ).upper() == "STALE_PENDING"
        pending = request.get("status") == "PENDING_APPROVAL"
        can_authorize = (
            self._can_authorize_workspace_upgrade
            and pending
            and not self_request
            and not stale
        )
        can_reject = (
            self._can_authorize_workspace_upgrade
            and pending
            and not self_request
        )
        self._authorize_upgrade_button.setEnabled(can_authorize)
        self._reject_upgrade_button.setEnabled(can_reject)
        if self_request:
            tooltip = (
                "A different Financial Control Approver must decide this request."
            )
        elif stale:
            tooltip = (
                "This request is stale and cannot be authorized. It may still "
                "receive a terminal rejection."
            )
        elif not pending:
            tooltip = "This request already has a terminal decision."
        else:
            tooltip = "A Financial Control Approver role is required."
        self._authorize_upgrade_button.setToolTip(
            "" if can_authorize else tooltip
        )
        self._reject_upgrade_button.setToolTip(
            "" if can_reject else tooltip
        )

    @staticmethod
    def _workspace_upgrade_evidence(request: dict[str, Any]) -> str:
        changes = (
            request.get("protected_rule_changes")
            or request.get("protected_member_changes")
            or ()
        )
        rendered_changes = []
        for item in changes:
            if not isinstance(item, dict):
                continue
            rendered_changes.append(
                f"{item.get('rule_id', 'Protected rule')} "
                f"v{item.get('source_version') or item.get('source_rule_version') or '—'} → "
                f"v{item.get('target_version') or item.get('target_rule_version') or '—'}"
            )
        change_text = (
            "; ".join(rendered_changes)
            if rendered_changes
            else "Five protected rule bindings are pinned by the target baseline."
        )
        optional_count = request.get(
            "preserved_optional_binding_count",
            request.get(
                "preserved_optional_member_count",
                request.get(
                    "preserved_optional_advisory_binding_count", "All"
                ),
            ),
        )
        target_version = request.get("target_baseline_version")
        target_hash = request.get("target_baseline_hash")
        target_metadata = " · ".join(
            item
            for item in (
                (
                    f"Target baseline v{target_version}"
                    if target_version
                    else None
                ),
                (
                    f"effective {request.get('target_effective_at')}"
                    if request.get("target_effective_at")
                    else None
                ),
                f"hash {target_hash}" if target_hash else None,
            )
            if item
        )
        result_metadata = " · ".join(
            item
            for item in (
                (
                    f"Resulting Rule Set v"
                    f"{request.get('resulting_rule_set_version')}"
                    if request.get("resulting_rule_set_version")
                    else None
                ),
                (
                    f"hash {request.get('resulting_rule_set_content_hash')}"
                    if request.get("resulting_rule_set_content_hash")
                    else None
                ),
            )
            if item
        )
        return "\n".join(
            item
            for item in (
                target_metadata,
                change_text,
                f"{optional_count} optional/advisory bindings preserved",
                result_metadata,
            )
            if item
        )

    @staticmethod
    def _workspace_upgrade_effect(request: dict[str, Any]) -> str:
        status = request.get("status")
        if status in {"APPROVED", "APPLIED"}:
            return (
                f"Created {request.get('resulting_rule_set_id', 'a successor Rule Set')} "
                "for this workspace only. Historical runs and other workspaces "
                "are unchanged. Reviewer revalidation is required."
            )
        if status == "REJECTED":
            return (
                "No Rule Set or Validation Run changed. A revised proposal "
                "requires a new request."
            )
        if bool(request.get("stale")):
            return (
                "Approval is blocked because the request-time workspace basis "
                "changed. Rejection remains available."
            )
        return (
            "No binding changes while Pending Approval. Authorization would "
            "create one successor workspace Rule Set; historical runs and "
            "other workspaces remain unchanged."
        )

    def _decide_workspace_upgrade(self, decision: str) -> None:
        request = self._selected_upgrade_request
        if request is None:
            return
        dialog = WorkspaceBaselineDecisionDialog(request, decision, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            saved = self._c.decide_workspace_upgrade(
                request["request_id"], **dialog.value()
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Workspace upgrade decision not saved",
                _safe_error(exc),
            )
            return
        self._workspace_upgrade_message.setText(
            (
                f"Authorized and applied as "
                f"{saved.get('resulting_rule_set_id', 'a successor Rule Set')}. "
                "The Reviewer can now run the required deterministic revalidation."
                if saved["status"] in {"APPROVED", "APPLIED"}
                else (
                    "Rejected. The workspace Rule Set and prior Validation "
                    "Run are unchanged."
                )
            )
        )
        self._refresh_workspace_upgrades()

    def _refresh_governance(self) -> None:
        self._governance_request_list.clear()
        self._governance_requests = []
        self._selected_governance_request = None
        for value in self._governance_detail_values.values():
            value.setText("—")
        self._approve_request_button.setEnabled(False)
        self._reject_request_button.setEnabled(False)
        if not self._can_view_governance:
            self._governance_message.setText(
                "Protected governance history is available to Rule "
                "Administrators and Financial Control Approvers."
            )
            return
        try:
            self._governance_requests = list(
                self._c.protected_change_requests(
                    for_decision=self._can_decide_protected
                )
            )
        except Exception as exc:
            self._governance_message.setText(
                "Protected governance history could not be loaded. "
                + _safe_error(exc)
            )
            return
        for request in self._governance_requests:
            item = QListWidgetItem(
                f"{request['rule_id']} · v{request['candidate_version']}\n"
                f"{str(request['status']).replace('_', ' ').title()} · "
                f"requested by {request['requester_actor_id']}"
            )
            item.setData(Qt.ItemDataRole.UserRole, request)
            self._governance_request_list.addItem(item)
        if self._governance_requests:
            self._governance_request_list.setCurrentRow(0)
            self._governance_message.setText(
                "Every request and decision is immutable, attributable, and "
                "retained for historical replay."
            )
        else:
            self._governance_message.setText(
                "No protected governance requests have been submitted."
            )

    def _select_governance_request(self, row: int) -> None:
        if row < 0 or row >= len(self._governance_requests):
            return
        request = self._governance_requests[row]
        self._selected_governance_request = request
        workspace_upgrade = (
            request.get("request_type")
            == "WORKSPACE_BASELINE_UPGRADE"
        )
        title_overrides = (
            {
                "rule_id": "Review / workspace",
                "candidate_version": "Target baseline",
                "change_kind": "Request type",
                "requested_baseline_id": "Rule Set at request",
                "before_definition": "Current workspace binding",
                "after_definition": "Authorized target binding",
                "candidate_content_hash": "Request evidence hash",
                "qualification_metrics": "Upgrade invariants",
                "prior_baseline_id": "Source baseline",
                "resulting_baseline_id": "Resulting Rule Set",
            }
            if workspace_upgrade
            else {
                "rule_id": "Protected rule",
                "candidate_version": "Proposed version",
                "change_kind": "Change category",
                "requested_baseline_id": "Baseline at request",
                "before_definition": "Before definition",
                "after_definition": "Proposed definition",
                "candidate_content_hash": "Candidate content hash",
                "qualification_metrics": "Qualification evidence",
                "prior_baseline_id": "Prior baseline",
                "resulting_baseline_id": "Activated baseline",
            }
        )
        for key, title in title_overrides.items():
            self._governance_detail_titles[key].setText(title)
        for key, label in self._governance_detail_values.items():
            value = request.get(key)
            label.setText(self._governance_value(key, value, request))
        terminal = request["status"] in {"APPROVED", "REJECTED"}
        for key in (
            "approver_actor_id",
            "decided_at",
            "decision_reason",
        ):
            self._governance_detail_titles[key].setVisible(terminal)
            self._governance_detail_values[key].setVisible(terminal)
        for key in ("prior_baseline_id", "resulting_baseline_id"):
            mapped_key = (
                {
                    "prior_baseline_id": "source_baseline_id",
                    "resulting_baseline_id": "resulting_rule_set_id",
                }[key]
                if workspace_upgrade
                else key
            )
            visible = bool(request.get(mapped_key))
            self._governance_detail_titles[key].setVisible(visible)
            self._governance_detail_values[key].setVisible(visible)
        self_request = (
            request["requester_actor_id"] == self._current_actor_id
        )
        can_decide = (
            (
                self._can_authorize_workspace_upgrade
                if workspace_upgrade
                else self._can_decide_protected
            )
            and request["status"] == "PENDING_APPROVAL"
            and not self_request
        )
        self._approve_request_button.setText(
            "Authorize" if workspace_upgrade else "Approve"
        )
        self._approve_request_button.setAccessibleName(
            (
                "Authorize selected workspace baseline upgrade"
                if workspace_upgrade
                else "Approve selected protected rule change"
            )
        )
        self._reject_request_button.setAccessibleName(
            (
                "Reject selected workspace baseline upgrade"
                if workspace_upgrade
                else "Reject selected protected rule change"
            )
        )
        self._approve_request_button.setEnabled(can_decide)
        self._reject_request_button.setEnabled(can_decide)
        tooltip = (
            "A different Financial Control Approver must decide this request."
            if self_request
            else (
                "This request already has a terminal decision."
                if request["status"] != "PENDING_APPROVAL"
                else "A Financial Control Approver role is required."
            )
        )
        self._approve_request_button.setToolTip(
            "" if can_decide else tooltip
        )
        self._reject_request_button.setToolTip(
            "" if can_decide else tooltip
        )

    @staticmethod
    def _governance_value(
        key: str, value: Any, request: dict[str, Any]
    ) -> str:
        if (
            request.get("request_type")
            == "WORKSPACE_BASELINE_UPGRADE"
        ):
            if key == "rule_id":
                return str(request.get("review_id") or "—")
            if key == "candidate_version":
                return str(request.get("target_baseline_id") or "—")
            if key == "change_kind":
                return "Workspace Baseline Upgrade"
            if key == "requested_baseline_id":
                return str(request.get("requested_rule_set_id") or "—")
            if key == "before_definition":
                return (
                    f"Rule Set {request.get('requested_rule_set_id', '—')}\n"
                    f"Protected baseline "
                    f"{request.get('source_baseline_id', '—')} · "
                    f"Validation Run {request.get('requested_run_id') or request.get('latest_run_id') or '—'}"
                )
            if key == "after_definition":
                return (
                    f"Protected baseline "
                    f"{request.get('target_baseline_id', '—')}\n"
                    "All five protected controls replaced atomically; optional "
                    "and advisory bindings preserved."
                )
            if key == "candidate_content_hash":
                return str(
                    request.get("request_hash")
                    or request.get("evidence_hash")
                    or request.get("application_hash")
                    or "—"
                )
            if key == "qualification_metrics":
                protected_count = request.get(
                    "target_protected_member_count", 5
                )
                optional_count = request.get(
                    "preserved_optional_member_count", "all"
                )
                return (
                    f"{protected_count} protected controls in target baseline · "
                    f"{optional_count} optional/advisory bindings preserved\n"
                    "Request-time Rule Set, Validation Run, target baseline, "
                    "and distinct-actor authorization are pinned."
                )
            if key == "future_effect":
                status = request.get("status")
                if status == "APPROVED":
                    return (
                        f"Workspace Rule Set "
                        f"{request.get('resulting_rule_set_id', '—')} was "
                        "created. Historical runs are unchanged. A Reviewer "
                        "must create the successor Review Version and Validation Run."
                    )
                if status == "REJECTED":
                    return (
                        "No workspace Rule Set or Validation Run changed. A "
                        "revised proposal requires a new request."
                    )
                return (
                    "No binding changes while Pending Approval. Authorization "
                    "would create one successor Rule Set for this workspace only."
                )
            if key == "prior_baseline_id":
                return str(request.get("source_baseline_id") or "—")
            if key == "resulting_baseline_id":
                return str(request.get("resulting_rule_set_id") or "—")
        if key in {"status", "change_kind"} and value:
            return str(value).replace("_", " ").title()
        if key in {"before_definition", "after_definition"}:
            definition = value if isinstance(value, dict) else {}
            if not definition:
                return "—"
            return (
                f"v{definition.get('version', '—')} · "
                f"{definition.get('name', 'Unnamed rule')} · "
                f"{definition.get('severity', '—')}\n"
                f"{definition.get('purpose', 'No purpose recorded.')}"
            )
        if key == "qualification_metrics":
            metrics = value if isinstance(value, dict) else {}
            qualification = metrics.get("qualification", {})
            evaluation = qualification.get(
                "candidate_dataset_evaluation", {}
            )
            checks = qualification.get("checks", {})
            passed_checks = sum(bool(item) for item in checks.values())
            return (
                f"{qualification.get('suite_id', 'Suite unavailable')} · "
                "released positive / negative / boundary coverage\n"
                f"Confirmed dataset: {evaluation.get('status', '—')} · "
                f"{evaluation.get('pass_count', 0)} passed · "
                f"{evaluation.get('fail_count', 0)} failed · "
                f"{evaluation.get('not_evaluated_count', 0)} not evaluated\n"
                f"{passed_checks} of {len(checks)} candidate invariants passed"
            )
        if key == "future_effect":
            if request.get("status") == "APPROVED":
                return (
                    "The successor is active for new workspaces. Existing "
                    "workspace Rule Set Versions remain pinned for replay."
                )
            if request.get("status") == "REJECTED":
                return (
                    "No baseline or workspace binding changed. A revision "
                    "requires a new linked request."
                )
            return (
                "No binding changes while Pending Approval. Approval would "
                "create a new baseline for future workspaces only."
            )
        return str(value or "—")

    def _decide_protected(self, decision: str) -> None:
        request = self._selected_governance_request
        if request is None:
            return
        workspace_upgrade = (
            request.get("request_type")
            == "WORKSPACE_BASELINE_UPGRADE"
        )
        dialog = (
            WorkspaceBaselineDecisionDialog(request, decision, self)
            if workspace_upgrade
            else ProtectedDecisionDialog(request, decision, self)
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            saved = (
                self._c.decide_workspace_upgrade(
                    request["request_id"], **dialog.value()
                )
                if workspace_upgrade
                else self._c.decide_protected_change(
                    request["request_id"], **dialog.value()
                )
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                (
                    "Workspace upgrade decision not saved"
                    if workspace_upgrade
                    else "Protected decision not saved"
                ),
                _safe_error(exc),
            )
            return
        if workspace_upgrade:
            message = (
                f"Authorized and applied as "
                f"{saved.get('resulting_rule_set_id', 'a successor Rule Set')}. "
                "The prior Validation Run is preserved; a Reviewer must now "
                "create the successor Review Version and Validation Run."
                if saved["status"] in {"APPROVED", "APPLIED"}
                else (
                    "Rejected. The workspace Rule Set and prior Validation "
                    "Run are unchanged."
                )
            )
        else:
            message = (
                f"Approved and activated as {saved['resulting_baseline_id']}. "
                "Existing reviews retain their prior Rule Set Versions."
                if saved["status"] == "APPROVED"
                else "Rejected. The active protected baseline is unchanged."
            )
        self._governance_message.setText(message)
        self.refresh()

    def _add_optional(self) -> None:
        dialog = OptionalRuleDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self._c.create_optional_rule(
                self._review.review_id, dialog.value()
            )
        except Exception as exc:
            QMessageBox.warning(self, "Rule not created", _safe_error(exc))
            return
        self._message.setText(
            "Optional rule draft created. Test it before activating the new version."
        )
        self.refresh()

    def _edit_selected(self) -> None:
        if not self._selected_rule:
            return
        if (
            self._selected_rule.get("baseline_status")
            == "PROTECTED_BASELINE"
        ):
            self._request_protected()
            return
        dialog = OptionalRuleDialog(self._selected_rule, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self._c.edit_optional_rule(
                self._review.review_id,
                self._selected_rule["rule_id"],
                dialog.value(),
            )
        except Exception as exc:
            QMessageBox.warning(
                self, "Rule version not saved", _safe_error(exc)
            )
            return
        self._message.setText(
            "A new immutable optional-rule version was saved."
        )
        self.refresh()

    def _test_selected(self) -> None:
        if not self._selected_rule:
            return
        try:
            result = self._c.test_optional_rule(
                self._review.review_id,
                self._selected_rule["rule_id"],
                self._dataset,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Draft test failed", _safe_error(exc))
            return
        message = (
            f"Draft test complete: {result.get('records_evaluated', 0)} records "
            f"evaluated, {result.get('findings', 0)} would be flagged. "
            "No review result was changed."
        )
        self._message.setText(message)
        QMessageBox.information(self, "Draft Test Complete", message)

    def _toggle_enabled(self) -> None:
        if not self._selected_rule:
            return
        enabled = not bool(self._selected_rule.get("enabled", True))
        try:
            self._c.set_optional_rule_enabled(
                self._review.review_id,
                self._selected_rule["rule_id"],
                enabled,
            )
        except Exception as exc:
            QMessageBox.warning(
                self, "Rule status not changed", _safe_error(exc)
            )
            return
        self._message.setText(
            "Optional rule enabled in a new Rule Set Version."
            if enabled
            else "Optional rule disabled in a new Rule Set Version."
        )
        self.refresh()

    def _activate_selected(self) -> None:
        if not self._selected_rule:
            return
        try:
            self._c.activate_optional_rule(
                self._review.review_id,
                self._selected_rule["rule_id"],
                self._selected_rule["version"],
            )
        except Exception as exc:
            QMessageBox.warning(
                self, "Rule version not activated", _safe_error(exc)
            )
            return
        self._message.setText(
            "The tested optional rule was activated in a new immutable "
            "Rule Set Version. Prior versions remain reproducible."
        )
        self.refresh()

    def _delete_selected(self) -> None:
        if not self._selected_rule:
            return
        if (
            self._selected_rule.get("baseline_status")
            == "PROTECTED_BASELINE"
        ):
            warning = QMessageBox(self)
            warning.setIcon(QMessageBox.Icon.Warning)
            warning.setWindowTitle(PROTECTED_RULE_DELETE_TITLE)
            warning.setText(PROTECTED_RULE_DELETE_TITLE)
            warning.setInformativeText(PROTECTED_RULE_DELETE_MESSAGE)
            return_button = warning.addButton(
                "Return to Rule", QMessageBox.ButtonRole.RejectRole
            )
            version_button = warning.addButton(
                "Create New Version", QMessageBox.ButtonRole.ActionRole
            )
            warning.setDefaultButton(return_button)
            warning.exec()
            if warning.clickedButton() is version_button:
                self._request_protected()
            return
        choice = QMessageBox.question(
            self,
            "Delete optional rule?",
            "This rule will not run in future validations. Previous results and "
            "rule versions will remain available.\n\nDelete this optional rule "
            "from the active rule set?",
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        try:
            self._c.delete_optional_rule(
                self._review.review_id, self._selected_rule["rule_id"]
            )
        except Exception as exc:
            QMessageBox.warning(self, "Rule not deleted", _safe_error(exc))
            return
        self._message.setText(
            "Optional rule removed from the active set. Historical versions were preserved."
        )
        self.refresh()

    def _continue(self) -> None:
        self.validationRequested.emit(
            self._review, self._dataset, self._revalidation
        )

    def current_screen(self) -> str:
        return (
            "rule_governance"
            if self._governance_only
            else "rules_repository"
        )

    def rule_names(self) -> list[str]:
        return [str(item.get("name", "")) for item in self._rules]
