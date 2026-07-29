from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox

import finsight.delivery.desktop.views.rules_repository_view as rules_view

from finsight.delivery.desktop.views.rules_repository_view import (
    PROTECTED_RULE_DELETE_MESSAGE,
    PROTECTED_RULE_DELETE_TITLE,
    ProtectedChangeDialog,
    ProtectedDecisionDialog,
    RulesRepositoryView,
    WorkspaceBaselineDecisionDialog,
    WorkspaceBaselineUpgradeDialog,
)


pytestmark = pytest.mark.ui


def _rule(rule_id: str, ordinal: int):
    return {
        "rule_id": rule_id,
        "name": f"Protected Rule {ordinal}",
        "version": "2.0.0",
        "severity": "High",
        "baseline_status": "PROTECTED_BASELINE",
        "classification": "CORE_MANDATORY",
        "evaluator_key": "actual_not_over_budget",
        "purpose": "Current governed purpose.",
        "required_fields": ["budget.bgt", "ged.amount"],
        "grouping_keys": ["department_number", "account_number"],
        "parameters": {},
        "lifecycle_status": "ACTIVE",
        "bound": True,
        "enabled": True,
        "ordinal": ordinal,
    }


def _request(*, requester="TEST:rule-admin", status="PENDING_APPROVAL"):
    return {
        "request_id": "protectreq_001",
        "review_id": "review-001",
        "rule_id": "CORE-01",
        "requested_baseline_id": "FINSIGHT-CORE-2.0",
        "predecessor_version": "2.0.0",
        "candidate_version": "2.0.1",
        "change_kind": "SEMANTIC",
        "reason": "Clarify the protected control.",
        "requester_actor_id": requester,
        "requested_at": "2026-07-28T00:00:00Z",
        "status": status,
        "decision_reason": (
            "Independent approval." if status == "APPROVED" else None
        ),
        "approver_actor_id": (
            "TEST:control-approver" if status == "APPROVED" else None
        ),
        "decided_at": (
            "2026-07-28T01:00:00Z" if status == "APPROVED" else None
        ),
        "before_definition": {
            "version": "2.0.0",
            "name": "Budget Overrun",
            "severity": "High",
            "purpose": "Actual spend must not exceed BGT.",
        },
        "after_definition": {
            "version": "2.0.1",
            "name": "Budget Overrun",
            "severity": "High",
            "purpose": "Clarified governed evidence for budget overruns.",
        },
        "candidate_content_hash": "a" * 64,
        "qualification_metrics": {
            "qualification": {
                "suite_id": "FINSIGHT-MVP-CORE-EVALUATOR-SUITE-2.0.0",
                "released_suite_coverage": "POSITIVE_NEGATIVE_BOUNDARY",
                "candidate_dataset_evaluation": {
                    "status": "FAIL",
                    "pass_count": 76,
                    "fail_count": 1,
                    "not_evaluated_count": 0,
                },
                "checks": {
                    "evaluator_key_unchanged": True,
                    "input_fields_unchanged": True,
                    "grouping_keys_unchanged": True,
                    "approved_parameters_unchanged": True,
                    "exact_five_protected_members": True,
                },
            }
        },
        "prior_baseline_id": (
            "FINSIGHT-CORE-2.0" if status == "APPROVED" else None
        ),
        "resulting_baseline_id": (
            "FINSIGHT-CORE-GOV-0001-00000001"
            if status == "APPROVED"
            else None
        ),
    }


def _upgrade_candidate(*, state="UPGRADE_AVAILABLE"):
    return {
        "review_id": "review-001",
        "state": state,
        "upgrade_available": state == "UPGRADE_AVAILABLE",
        "current_rule_set_id": "ruleset_review-001_2",
        "current_baseline_id": "FINSIGHT-CORE-2.0",
        "target_baseline_id": "FINSIGHT-CORE-GOV-0001-00000001",
        "latest_run_id": "run_original",
        "reason": (
            "A Reviewer must run deterministic revalidation."
            if state == "APPLIED_REVALIDATION_REQUIRED"
            else "A newer approved protected baseline is available."
        ),
    }


def _upgrade_request(
    *,
    requester="TEST:rule-admin",
    status="PENDING_APPROVAL",
    stale=False,
):
    terminal = status in {"APPROVED", "REJECTED"}
    return {
        "request_id": "workspaceup_001",
        "review_id": "review-001",
        "requested_rule_set_id": "ruleset_review-001_2",
        "requested_run_id": "run_original",
        "source_baseline_id": "FINSIGHT-CORE-2.0",
        "target_baseline_id": "FINSIGHT-CORE-GOV-0001-00000001",
        "requester_actor_id": requester,
        "requested_at": "2026-07-28T02:00:00Z",
        "reason": "Apply the independently approved baseline.",
        "status": status,
        "stale": stale,
        "approver_actor_id": (
            "TEST:control-approver" if terminal else None
        ),
        "decided_at": "2026-07-28T03:00:00Z" if terminal else None,
        "decision_reason": (
            "Independent workspace authorization." if terminal else None
        ),
        "resulting_rule_set_id": (
            "ruleset_review-001_3" if status == "APPROVED" else None
        ),
        "applied_at": (
            "2026-07-28T03:00:00Z" if status == "APPROVED" else None
        ),
    }


class _Controller:
    def __init__(
        self,
        roles,
        actor_id,
        requests,
        *,
        upgrade_candidates=(),
        upgrade_requests=(),
    ):
        self.roles = tuple(roles)
        self.actor_id = actor_id
        self.requests = list(requests)
        self.upgrade_candidates = list(upgrade_candidates)
        self.upgrade_requests = list(upgrade_requests)
        self.for_decision = None
        self.upgrade_for_decision = None

    def review_management_availability(self):
        return SimpleNamespace(role_labels=self.roles)

    def current_actor_id(self):
        return self.actor_id

    def bound_rules(self, _review_id):
        return {
            "rule_set_id": "ruleset-review-001-1",
            "rule_set_version": 1,
            "rules": [
                _rule(f"CORE-0{ordinal}", ordinal)
                for ordinal in range(1, 6)
            ],
        }

    def validation_history(self, _review_id):
        return []

    def protected_change_requests(self, *, for_decision=False):
        self.for_decision = for_decision
        return self.requests

    def workspace_upgrade_status(self, _review_id):
        return (
            self.upgrade_candidates[0]
            if self.upgrade_candidates
            else {
                **_upgrade_candidate(state="UP_TO_DATE"),
                "upgrade_available": False,
            }
        )

    def workspace_upgrade_candidates(self):
        return self.upgrade_candidates

    def workspace_upgrade_requests(
        self, *, review_id=None, for_decision=False
    ):
        self.upgrade_for_decision = for_decision
        if review_id is None:
            return self.upgrade_requests
        return [
            item
            for item in self.upgrade_requests
            if item["review_id"] == review_id
        ]


def _review():
    return SimpleNamespace(
        review_id="review-001",
        period=SimpleNamespace(label="May 2026"),
        status=SimpleNamespace(value="Data Reviewed"),
    )


def test_default_rules_surface_is_simple_and_hides_advanced_governance(qtbot):
    controller = _Controller(
        ("Rule Administrator",),
        "TEST:rule-admin",
        [],
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)
    view.open_review(_review(), object())

    assert view._page_title.text() == "Validation Rules"
    assert "which financial checks" in view._page_subtitle.text()
    assert view._back.text() == "← Back"
    assert view._add_button.text() == "Add Rule"
    assert view._validate.text() == "Run Validation"
    assert view._rule_table.headerItem().text(0) == "Rule"
    assert view._rule_table.headerItem().text(5) == "Actions"
    assert view._rule_table.topLevelItemCount() == 5
    assert {
        view._rule_table.topLevelItem(row).text(1)
        for row in range(view._rule_table.topLevelItemCount())
    } == {"Core Rule"}
    assert view._governance_card.isHidden()
    assert view._workspace_upgrade_card.isHidden()
    assert view._advanced_details.isHidden()
    assert view._rule_table.minimumHeight() >= 300
    assert "must not exceed BGT" in view._detail_values["parameters"].text()


def test_rule_table_keeps_focus_for_repeated_keyboard_row_navigation(qtbot):
    controller = _Controller(
        ("Rule Administrator",),
        "TEST:rule-admin",
        [],
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)
    view.show()
    view.open_review(_review(), object())
    view.activateWindow()
    view._rule_table.setFocus()
    qtbot.waitUntil(view._rule_table.hasFocus, timeout=1000)

    qtbot.keyClick(view._rule_table, Qt.Key.Key_Down)
    qtbot.keyClick(view._rule_table, Qt.Key.Key_Down)

    assert view._rule_table.hasFocus()
    assert view._rule_table.indexOfTopLevelItem(
        view._rule_table.currentItem()
    ) == 2


def test_optional_rule_ui_dispatches_versioned_lifecycle_and_shows_history(
    qtbot, monkeypatch
):
    class Controller(_Controller):
        def __init__(self):
            super().__init__(
                ("Rule Administrator",),
                "TEST:rule-admin",
                [],
            )
            self.optional = None
            self.calls = []

        def bound_rules(self, _review_id):
            rules = [
                _rule(f"CORE-0{ordinal}", ordinal)
                for ordinal in range(1, 6)
            ]
            if self.optional is not None:
                rules.append(dict(self.optional))
            return {
                "rule_set_id": "ruleset-review-001-1",
                "rule_set_version": 1,
                "rules": rules,
            }

        def create_optional_rule(self, review_id, definition):
            self.calls.append(("create", review_id, definition))
            self.optional = {
                "rule_id": "OPT-001",
                "name": definition["name"],
                "version": "1.0.0",
                "severity": definition["severity"],
                "baseline_status": "OPTIONAL_CONFIGURABLE",
                "classification": "OPTIONAL_CONFIGURABLE",
                "evaluator_key": "ged_amount_threshold",
                "purpose": definition["purpose"],
                "required_fields": ["ged.amount"],
                "grouping_keys": [
                    "department_number",
                    "account_number",
                ],
                "parameters": definition["parameters"],
                "lifecycle_status": "DRAFT",
                "bound": False,
                "enabled": False,
                "ordinal": 6,
                "previous_versions": [],
            }

        def edit_optional_rule(
            self, review_id, rule_id, definition
        ):
            self.calls.append(("edit", review_id, rule_id, definition))
            previous = dict(self.optional)
            self.optional.update(
                definition,
                version="1.0.1",
                previous_versions=[previous],
            )

        def test_optional_rule(self, review_id, rule_id, _dataset):
            self.calls.append(("test", review_id, rule_id))
            self.optional["lifecycle_status"] = "TESTED"
            return {"records_evaluated": 258, "findings": 1}

        def activate_optional_rule(self, review_id, rule_id, version):
            self.calls.append(("activate", review_id, rule_id, version))
            self.optional.update(
                lifecycle_status="ACTIVE", bound=True, enabled=True
            )

        def set_optional_rule_enabled(
            self, review_id, rule_id, enabled
        ):
            self.calls.append(("enabled", review_id, rule_id, enabled))
            self.optional["enabled"] = enabled

        def delete_optional_rule(self, review_id, rule_id):
            self.calls.append(("retire", review_id, rule_id))
            self.optional = None

    class AcceptedRuleDialog:
        def __init__(self, existing=None, parent=None):
            self.existing = existing

        def exec(self):
            return QDialog.DialogCode.Accepted

        def value(self):
            return {
                "name": "Large GED Transaction",
                "purpose": "Flag unusually large GED transactions.",
                "severity": "Medium",
                "evaluator_key": "ged_amount_threshold",
                "parameters": {
                    "operator": "LTE",
                    "threshold": "5000.00",
                },
            }

    controller = Controller()
    monkeypatch.setattr(
        rules_view, "OptionalRuleDialog", AcceptedRuleDialog
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Ok,
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)
    view.open_review(_review(), object())

    view._add_optional()
    view._rule_table.setCurrentItem(view._rule_table.topLevelItem(5))
    view._edit_selected()
    view._rule_table.setCurrentItem(view._rule_table.topLevelItem(5))
    assert "1.0.0" in view._version_history.text()

    view._test_selected()
    view._activate_selected()
    view._rule_table.setCurrentItem(view._rule_table.topLevelItem(5))
    view._toggle_enabled()
    view._rule_table.setCurrentItem(view._rule_table.topLevelItem(5))
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    view._delete_selected()

    assert [call[0] for call in controller.calls] == [
        "create",
        "edit",
        "test",
        "activate",
        "enabled",
        "retire",
    ]


def test_protected_rule_delete_explains_control_without_deleting(
    qtbot, monkeypatch
):
    controller = _Controller(
        ("Rule Administrator",),
        "TEST:rule-admin",
        [],
    )
    controller.delete_calls = []
    controller.delete_optional_rule = (
        lambda *args: controller.delete_calls.append(args)
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)
    view.open_review(_review(), object())
    captured = {}

    def fake_exec(message_box):
        captured["title"] = message_box.windowTitle()
        captured["text"] = message_box.text()
        captured["details"] = message_box.informativeText()
        return QMessageBox.StandardButton.Cancel

    monkeypatch.setattr(QMessageBox, "exec", fake_exec)
    view._delete_selected()

    assert PROTECTED_RULE_DELETE_TITLE == "This is a protected core rule"
    assert "cannot be deleted" in PROTECTED_RULE_DELETE_MESSAGE
    assert controller.delete_calls == []


def test_rule_administrator_sees_request_action_but_cannot_self_decide(
    qtbot,
):
    controller = _Controller(
        ("Rule Administrator",),
        "TEST:rule-admin",
        [_request()],
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)
    view.open_review(_review(), object())

    assert view._request_protected_button.isEnabled()
    assert view._request_protected_button.accessibleName()
    assert controller.for_decision is False
    assert view._governance_request_list.count() == 1
    assert not view._approve_request_button.isEnabled()
    assert not view._reject_request_button.isEnabled()
    assert "different Financial Control Approver" in (
        view._approve_request_button.toolTip()
    )


def test_different_approver_sees_enabled_terminal_decision_controls(qtbot):
    controller = _Controller(
        ("Financial Control Approver",),
        "TEST:control-approver",
        [_request()],
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)
    view.open_review(_review(), object())

    assert controller.for_decision is True
    assert not view._request_protected_button.isEnabled()
    assert view._approve_request_button.isEnabled()
    assert view._reject_request_button.isEnabled()
    assert (
        view._governance_detail_values["candidate_version"].text()
        == "2.0.1"
    )
    assert "v2.0.0" in (
        view._governance_detail_values["before_definition"].text()
    )
    assert "positive / negative / boundary" in (
        view._governance_detail_values["qualification_metrics"].text()
    )
    assert "No binding changes" in (
        view._governance_detail_values["future_effect"].text()
    )


def test_pure_approver_can_open_global_governance_queue(qtbot):
    controller = _Controller(
        ("Financial Control Approver",),
        "TEST:control-approver",
        [_request()],
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)

    view.open_governance_queue()

    assert view.current_screen() == "rule_governance"
    assert controller.for_decision is True
    assert not view._governance_card.isHidden()
    assert view._progress.isHidden()
    assert view._rules_splitter.isHidden()
    assert view._validate.isHidden()
    assert view._approve_request_button.isEnabled()
    assert view._reject_request_button.isEnabled()
    assert view._context.text() == "Protected governance queue"


def test_terminal_governance_history_is_visible_but_not_actionable(qtbot):
    controller = _Controller(
        ("Financial Control Approver",),
        "TEST:control-approver",
        [_request(status="APPROVED")],
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)
    view.open_review(_review(), object())

    assert view._governance_detail_values["status"].text() == "Approved"
    assert "FINSIGHT-CORE-GOV" in (
        view._governance_detail_values["resulting_baseline_id"].text()
    )
    assert (
        view._governance_detail_values["approver_actor_id"].text()
        == "TEST:control-approver"
    )
    assert (
        view._governance_detail_values["decided_at"].text()
        == "2026-07-28T01:00:00Z"
    )
    assert (
        view._governance_detail_values["requested_baseline_id"].text()
        == "FINSIGHT-CORE-2.0"
    )
    assert "new workspaces" in (
        view._governance_detail_values["future_effect"].text()
    )
    assert not view._approve_request_button.isEnabled()
    assert not view._reject_request_button.isEnabled()


def test_pure_rule_administrator_can_request_global_workspace_upgrade(qtbot):
    controller = _Controller(
        ("Rule Administrator",),
        "TEST:rule-admin",
        [],
        upgrade_candidates=[_upgrade_candidate()],
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)

    view.open_governance_queue()

    assert view.current_screen() == "rule_governance"
    assert not view._workspace_upgrade_card.isHidden()
    assert view._upgrade_candidate_list.count() == 1
    assert view._request_workspace_upgrade_button.isEnabled()
    assert (
        view._upgrade_candidate_values["current_rule_set_id"].text()
        == "ruleset_review-001_2"
    )
    assert (
        view._upgrade_candidate_values["target_baseline_id"].text()
        == "FINSIGHT-CORE-GOV-0001-00000001"
    )
    assert not view._authorize_upgrade_button.isEnabled()


def test_pure_approver_can_authorize_workspace_upgrade_from_global_queue(
    qtbot,
):
    controller = _Controller(
        ("Financial Control Approver",),
        "TEST:control-approver",
        [],
        upgrade_requests=[_upgrade_request()],
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)

    view.open_governance_queue()

    assert controller.upgrade_for_decision is True
    assert view._workspace_upgrade_tabs.currentIndex() == 1
    assert view._upgrade_request_list.count() == 1
    assert view._authorize_upgrade_button.isEnabled()
    assert view._reject_upgrade_button.isEnabled()
    assert (
        view._upgrade_request_values["requested_rule_set_id"].text()
        == "ruleset_review-001_2"
    )
    assert "historical runs" in (
        view._upgrade_request_values["effect"].text().lower()
    )


def test_stale_workspace_upgrade_blocks_authorization_but_allows_rejection(
    qtbot,
):
    controller = _Controller(
        ("Financial Control Approver",),
        "TEST:control-approver",
        [],
        upgrade_requests=[_upgrade_request(stale=True)],
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)

    view.open_governance_queue()

    assert not view._authorize_upgrade_button.isEnabled()
    assert view._reject_upgrade_button.isEnabled()
    assert "stale" in view._authorize_upgrade_button.toolTip().lower()


def test_applied_workspace_upgrade_history_identifies_required_revalidation(
    qtbot,
):
    controller = _Controller(
        ("Financial Control Approver",),
        "TEST:control-approver",
        [],
        upgrade_requests=[_upgrade_request(status="APPROVED")],
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)

    view.open_governance_queue()

    assert (
        view._upgrade_request_values["resulting_rule_set_id"].text()
        == "ruleset_review-001_3"
    )
    assert "Reviewer revalidation is required" in (
        view._upgrade_request_values["effect"].text()
    )
    assert not view._authorize_upgrade_button.isEnabled()
    assert not view._reject_upgrade_button.isEnabled()


def test_reviewer_sees_applied_workspace_upgrade_revalidation_state(qtbot):
    controller = _Controller(
        ("Reviewer",),
        "TEST:reviewer",
        [],
        upgrade_candidates=[
            _upgrade_candidate(state="APPLIED_REVALIDATION_REQUIRED")
        ],
    )
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)

    view.open_review(_review(), object(), revalidation=True)

    assert (
        view._upgrade_candidate_values["state"].text()
        == "Applied Revalidation Required"
    )
    assert "Reviewer must run deterministic revalidation" in (
        view._upgrade_candidate_values["reason"].text()
    )
    assert not view._request_workspace_upgrade_button.isEnabled()


def test_protected_request_and_decision_dialogs_expose_governed_evidence(
    qtbot,
):
    rule = _rule("CORE-01", 1)
    request_dialog = ProtectedChangeDialog(rule)
    qtbot.addWidget(request_dialog)
    request_dialog.purpose.setPlainText("A governed successor purpose.")
    request_dialog.reason.setPlainText("Policy changed after control review.")

    proposal = request_dialog.value()

    assert proposal["proposed_version"] == "2.0.1"
    assert proposal["change_kind"] == "SEMANTIC"
    assert proposal["parameters"] == {}
    assert proposal["reason"] == "Policy changed after control review."
    assert request_dialog.parameters.isReadOnly()
    assert request_dialog.change_kind.count() == 1

    decision_dialog = ProtectedDecisionDialog(
        _request(), "APPROVED"
    )
    qtbot.addWidget(decision_dialog)
    decision_dialog.reason.setPlainText("Independent approval completed.")

    assert decision_dialog.value() == {
        "decision": "APPROVED",
        "reason": "Independent approval completed.",
    }


def test_workspace_upgrade_dialogs_expose_exact_binding_evidence(qtbot):
    request_dialog = WorkspaceBaselineUpgradeDialog(_upgrade_candidate())
    qtbot.addWidget(request_dialog)
    request_dialog.reason.setPlainText(
        "Adopt the approved control baseline for future review work."
    )

    assert request_dialog.value() == {
        "reason": "Adopt the approved control baseline for future review work."
    }
    assert request_dialog.reason.accessibleName()

    decision_dialog = WorkspaceBaselineDecisionDialog(
        _upgrade_request(), "APPROVED"
    )
    qtbot.addWidget(decision_dialog)
    decision_dialog.reason.setPlainText(
        "The request-time Rule Set and target baseline were independently verified."
    )

    assert decision_dialog.value() == {
        "decision": "APPROVED",
        "reason": (
            "The request-time Rule Set and target baseline were independently "
            "verified."
        ),
    }
    assert decision_dialog.reason.accessibleName()
