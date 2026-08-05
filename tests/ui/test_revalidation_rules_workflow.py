from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QDialog

import finsight.delivery.desktop.views.rules_repository_view as rules_view

from finsight.delivery.desktop.views.rules_repository_view import (
    RuleSetConfirmationDialog,
    RulesRepositoryView,
)


pytestmark = pytest.mark.ui


def _core_rule(ordinal: int) -> dict:
    return {
        "rule_id": f"CORE-0{ordinal}",
        "name": f"Protected Rule {ordinal}",
        "version": "2.0.0",
        "severity": "High",
        "baseline_status": "PROTECTED_BASELINE",
        "classification": "CORE_MANDATORY",
        "evaluator_key": "actual_not_over_budget",
        "purpose": "Mandatory deterministic financial control.",
        "required_fields": ["budget.bgt", "ged.amount"],
        "grouping_keys": ["department_number", "account_number"],
        "parameters": {},
        "lifecycle_status": "ACTIVE",
        "bound": True,
        "enabled": True,
        "ordinal": ordinal,
    }


def _review():
    return SimpleNamespace(
        review_id="review-001",
        period=SimpleNamespace(label="May 2026"),
        status=SimpleNamespace(value="Validation Complete"),
    )


class _Controller:
    def __init__(self, *, draft: bool = False):
        self.draft = draft
        self.draft_excluded = False
        self.confirmed_hashes: list[str] = []
        self.revalidation_entries: list[str] = []

    def review_management_availability(self):
        return SimpleNamespace(
            role_labels=("Reviewer", "Rule Administrator")
        )

    def current_actor_id(self):
        return "TEST:reviewer"

    def record_revalidation_entry(self, review_id):
        self.revalidation_entries.append(review_id)

    def bound_rules(self, _review_id):
        rules = [_core_rule(ordinal) for ordinal in range(1, 6)]
        if self.draft:
            rules.append(
                {
                    "rule_id": "OPT-001",
                    "name": "Large GED Transaction",
                    "version": "1.0.0",
                    "severity": "Medium",
                    "baseline_status": "OPTIONAL_CONFIGURABLE",
                    "classification": "OPTIONAL_CONFIGURABLE",
                    "evaluator_key": "ged_amount_threshold",
                    "purpose": "Flag large individual GED amounts.",
                    "required_fields": ["ged.amount"],
                    "grouping_keys": ["source_record"],
                    "parameters": {
                        "operator": "LTE",
                        "threshold": "5000.00",
                    },
                    "lifecycle_status": "DRAFT",
                    "bound": False,
                    "enabled": False,
                    "ordinal": 6,
                    "excluded_from_proposed_set": self.draft_excluded,
                    "previous_versions": [],
                }
            )
        return {
            "rule_set_id": "ruleset_review-001_1",
            "rule_set_version": 1,
            "rules": rules,
        }

    def validation_history(self, _review_id):
        return [
            {
                "run_id": "run_prior",
                "rule_set_id": "ruleset_review-001_1",
                "metrics": {"findings": 4, "rules_executed": 5},
            }
        ]

    def validation_rule_set_proposal(self, _dataset):
        unresolved = []
        excluded = []
        if self.draft:
            identity = {
                "rule_id": "OPT-001",
                "rule_version": "1.0.0",
                "name": "Large GED Transaction",
                "status": "Draft",
                "excluded": self.draft_excluded,
            }
            (excluded if self.draft_excluded else unresolved).append(identity)
        included = [
            {
                "ordinal": ordinal,
                "rule_id": f"CORE-0{ordinal}",
                "rule_version": "2.0.0",
                "name": f"Protected Rule {ordinal}",
                "baseline_status": "PROTECTED_BASELINE",
                "status": "Active",
                "included": True,
                "severity": "High",
                "evaluator_key": "actual_not_over_budget",
                "parameters": {},
                "required_fields": ["budget.bgt", "ged.amount"],
                "grouping_keys": [
                    "department_number",
                    "account_number",
                ],
                "content_hash": f"hash-{ordinal}",
            }
            for ordinal in range(1, 6)
        ]
        return {
            "review_id": "review-001",
            "reporting_period": "May 2026",
            "department_number": "00-0245",
            "department_name": "Applications Enginee",
            "working_data_label": "May 2026 verified Budget and GED data",
            "budget_filename": "Sample_Budget_Report.xlsx",
            "ged_filename": "Sample_GED_Report.xlsx",
            "budget_record_count": 71,
            "ged_transaction_count": 258,
            "dataset_fingerprint": "dataset-fingerprint",
            "source_generation_id": "review-001-gen-1",
            "source_data_version": "review-001-gen-1:dataset-fingerprint",
            "rule_set_id": "ruleset_review-001_1",
            "rule_set_version": "1",
            "rules": included,
            "included_rules": included,
            "excluded_drafts": excluded,
            "draft_candidates": [*unresolved, *excluded],
            "unresolved_drafts": unresolved,
            "counts": {
                "protected_core": 5,
                "enabled_optional": 0,
                "draft": len(unresolved),
                "disabled_included": 0,
                "disabled_available": 0,
            },
            "changes": [],
            "prior_run_id": "run_prior",
            "prior_rule_set_id": "ruleset_review-001_1",
            "same_rule_set_rerun": True,
            "ready": not unresolved,
            "readiness_reasons": (
                [
                    "1 draft rule is unresolved. Test and activate it, or "
                    "exclude it from the proposed Rule Set."
                ]
                if unresolved
                else []
            ),
            "proposal_hash": "proposal-hash",
        }

    def confirm_validation_rule_set(self, _dataset, proposal_hash):
        self.confirmed_hashes.append(proposal_hash)
        return {
            "confirmation_id": "ruleconfirm-001",
            "actor_id": "TEST:reviewer",
            "confirmed_at": "2026-07-31T10:00:00Z",
        }

    def set_optional_draft_excluded(
        self, _review_id, _rule_id, _version, *, excluded
    ):
        self.draft_excluded = excluded
        return {"action": "EXCLUDED" if excluded else "RESTORED"}

    def protected_change_requests(self, *, for_decision=False):
        return []

    def workspace_upgrade_status(self, _review_id):
        return {"upgrade_available": False}

    def workspace_upgrade_candidates(self):
        return []

    def workspace_upgrade_requests(
        self, *, review_id=None, for_decision=False
    ):
        return []


def test_same_rule_set_revalidation_is_enabled_confirmed_and_emitted(
    qtbot, monkeypatch
):
    controller = _Controller()
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)
    view.open_review(_review(), object(), revalidation=True)

    assert controller.revalidation_entries == ["review-001"]
    assert view._validate.isEnabled()
    assert "Same rules will be rerun" in view._comparison.text()
    assert "prior Validation Run" in view._comparison.text()
    assert view._validate.accessibleDescription()

    monkeypatch.setattr(
        rules_view.RuleSetConfirmationDialog,
        "exec",
        lambda _dialog: QDialog.DialogCode.Accepted,
    )
    with qtbot.waitSignal(view.validationRequested) as signal:
        view._validate.click()

    assert controller.confirmed_hashes == ["proposal-hash"]
    assert signal.args[2] is True
    assert signal.args[3]["confirmation_id"] == "ruleconfirm-001"
    assert not view._validate.isEnabled()
    assert "already running" in view._validate.toolTip().lower()


def test_unresolved_draft_has_explicit_actions_and_exclusion_unblocks_run(qtbot):
    controller = _Controller(draft=True)
    view = RulesRepositoryView(controller)
    qtbot.addWidget(view)
    view.open_review(_review(), object(), revalidation=True)

    assert view._draft_banner.isVisibleTo(view)
    assert not view._validate.isEnabled()
    assert "draft rule" in view._validate.toolTip().lower()
    assert view._draft_test.text() == "Test Rule"
    assert view._draft_activate.text() == "Activate Rule"
    assert view._draft_exclude.text() == "Exclude Draft Rule"
    assert view._draft_review.text() == "Review Rule"

    view._exclude_first_unresolved_draft()

    assert controller.draft_excluded is True
    assert view._validate.isEnabled()
    assert not view._draft_banner.isVisibleTo(view)
    optional = view._rule_table.topLevelItem(5)
    assert "Excluded" in optional.text(3)


def test_confirmation_dialog_exposes_exact_inputs_and_safe_accessibility(qtbot):
    proposal = _Controller().validation_rule_set_proposal(object())
    dialog = RuleSetConfirmationDialog(proposal)
    qtbot.addWidget(dialog)

    assert dialog.isModal()
    assert dialog.accessibleName()
    assert dialog.accessibleDescription()
    assert dialog.rules_table.topLevelItemCount() == 5
    assert dialog.rules_table.accessibleName()
    assert dialog.cancel_button.isDefault()
    assert dialog.cancel_button.accessibleName()
    assert dialog.run_button.accessibleName()


def test_protected_and_unavailable_actions_explain_why_they_are_disabled(qtbot):
    view = RulesRepositoryView(_Controller())
    qtbot.addWidget(view)
    view.open_review(_review(), object())

    assert not view._enable_button.isEnabled()
    assert "protected" in view._enable_button.toolTip().lower()
    assert view._enable_button.accessibleDescription()
    assert not view._activate_button.isEnabled()
    assert view._activate_button.toolTip()
    assert view._activate_button.accessibleDescription()
