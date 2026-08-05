"""Governed, versioned optional-rule management for reviewed financial data."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping

from finsight.application.security import AuthorizationContext
from finsight.domain.financial_validation import (
    RuleDefinitionVersion,
    RuleSetManifest,
)
from finsight.domain.identity import Permission
from finsight.infrastructure.audit_stream import AuditScope


class RuleManagementError(RuntimeError):
    pass


_PROTECTED_EVALUATOR_SUITE_ID = "FINSIGHT-MVP-CORE-EVALUATOR-SUITE-2.0.0"
_PROTECTED_CERTIFIED_EVALUATORS = frozenset(
    {
        "actual_not_over_budget",
        "valid_mapping",
        "exact_duplicates",
        "required_fields",
        "atd_reconciliation",
    }
)
_PROTECTED_PARAMETER_FIELDS = {
    "CORE-01": frozenset(),
    "CORE-02": frozenset(),
    "CORE-03": frozenset(),
    "CORE-04": frozenset(),
    "CORE-05": frozenset(),
}
_WORKSPACE_UPGRADE_AUDIT_SCHEMA = (
    "NFR-090_EXISTING_WORKSPACE_BASELINE_UPGRADE_V1"
)
_PROTECTED_REQUEST_AUDIT_SCHEMA = (
    "NFR-090_PROTECTED_REQUEST_SUBMITTED_V1"
)
_PROTECTED_DECISION_AUDIT_SCHEMA = (
    "NFR-090_PROTECTED_TERMINAL_DECISION_V1"
)
_WORKSPACE_UPGRADE_ACTION = (
    "APPLY_PROTECTED_BASELINE_TO_EXISTING_WORKSPACE"
)
_NOT_APPLICABLE = "N/A"


def _canonical(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _canonical_threshold(value: Any) -> str:
    text = str(value).strip()
    if not re.fullmatch(r"[+-]?[0-9]+(?:\.[0-9]{1,2})?", text):
        raise RuleManagementError(
            "Threshold must be a finite financial amount with no more than "
            "two decimal places."
        )
    try:
        amount = Decimal(text)
    except InvalidOperation as error:
        raise RuleManagementError("Threshold is not a valid financial amount.") from error
    if not amount.is_finite():
        raise RuleManagementError("Threshold must be a finite financial amount.")
    return format(amount.quantize(Decimal("0.01")), ".2f")


class RuleManagementService:
    """Application boundary for the closed, non-executable optional-rule surface."""

    def __init__(
        self,
        *,
        repository,
        unit_of_work,
        audit_stream,
        engine,
        actor,
        clock,
        authorizer: Callable[[Permission], None],
        authorization_executor=None,
        id_factory=None,
    ):
        self._repo = repository
        self._uow = unit_of_work
        self._audit = audit_stream
        self._engine = engine
        self._actor = actor
        self._clock = clock
        self._authorize = authorizer
        self._authorization_executor = authorization_executor
        self._id = id_factory or (lambda: uuid.uuid4().hex)

    @property
    def actor_id(self) -> str:
        return self._actor.actor_id

    def ensure_initial_rule_set(self, review_id: str) -> str:
        self._authorize(Permission.RULE_BOUND_READ)
        with self._uow.atomic():
            return self._repo.ensure_initial_rule_set(
                review_id,
                actor_id=self._actor.actor_id,
                created_at=self._clock.now(),
            )

    def list_bound_rules(self, review_id: str) -> list[dict[str, Any]]:
        self._authorize(Permission.RULE_BOUND_READ)
        return self._bound_rules(review_id)

    def _bound_rules(self, review_id: str) -> list[dict[str, Any]]:
        rule_set_id = self._repo.current_rule_set_id(review_id)
        if not rule_set_id:
            return []
        output = []
        for member in self._repo.rule_set_members(rule_set_id):
            definition = self._repo.rule_version(
                member["rule_id"], member["rule_version"]
            )
            if definition:
                governance_current = (
                    self._repo.current_protected_rule(member["rule_id"])
                    if definition["baseline_status"]
                    == "PROTECTED_BASELINE"
                    else None
                )
                output.append(
                    {
                        **definition,
                        **member,
                        "rule_set_id": rule_set_id,
                        "governance_current": governance_current,
                    }
                )
        return output

    def list_repository_rules(
        self, review_id: str, *, administrative: bool = False
    ) -> list[dict[str, Any]]:
        """Return bound rules plus the latest unbound Draft/Tested versions."""

        self._authorize(
            Permission.RULE_LIBRARY_READ
            if administrative
            else Permission.RULE_BOUND_READ
        )
        def with_history(item: dict[str, Any]) -> dict[str, Any]:
            history = self._repo.rule_version_history(str(item["rule_id"]))
            return {
                **item,
                "previous_versions": [
                    version
                    for version in history
                    if str(version.get("version"))
                    != str(item.get("version"))
                ],
            }

        bound = [
            {**with_history(item), "bound": True}
            for item in self._bound_rules(review_id)
        ]
        bound_versions = {
            (str(item["rule_id"]), str(item["version"])) for item in bound
        }
        if not administrative:
            return bound
        exclusions = {
            (str(item["rule_id"]), str(item["rule_version"]))
            for item in self._repo.current_rule_proposal_draft_exclusions(
                review_id
            )
        }
        drafts = [
            {
                **with_history(item),
                "bound": False,
                "enabled": False,
                "rule_set_id": None,
                "ordinal": None,
                "excluded_from_proposed_set": (
                    str(item["rule_id"]), str(item["version"])
                )
                in exclusions,
            }
            for item in self._repo.latest_optional_rule_versions()
            if (str(item["rule_id"]), str(item["version"]))
            not in bound_versions
            and item.get("lifecycle_status") in {"DRAFT", "TESTED"}
        ]
        return [*bound, *drafts]

    def set_draft_excluded_from_proposed_set(
        self,
        review_id: str,
        rule_id: str,
        version: str,
        *,
        excluded: bool,
    ) -> dict[str, Any]:
        """Record one explicit, review-local Draft proposal disposition."""

        self._authorize(Permission.RULE_OPTIONAL_DRAFT_MANAGE)
        definition = self._require_optional(rule_id, version)
        if definition["lifecycle_status"] not in {"DRAFT", "TESTED"}:
            raise RuleManagementError(
                "Only a Draft or Tested optional version can be excluded "
                "from the proposed Rule Set."
            )
        current_set_id = self._repo.current_rule_set_id(review_id)
        if current_set_id and any(
            item["rule_id"] == rule_id
            and item["rule_version"] == version
            and item["enabled"]
            for item in self._repo.rule_set_members(current_set_id)
        ):
            raise RuleManagementError(
                "An active optional rule must be disabled, not excluded as a Draft."
            )
        timestamp = self._clock.now()
        action = "EXCLUDED" if excluded else "RESTORED"
        event = {
            "event_id": "draftproposal_" + self._id(),
            "review_id": review_id,
            "rule_id": rule_id,
            "rule_version": version,
            "action": action,
            "actor_id": self._actor.actor_id,
            "occurred_at": timestamp,
            "reason": (
                "DRAFT_EXCLUDED_FROM_PROPOSED_RULE_SET"
                if excluded
                else "DRAFT_RETURNED_TO_PROPOSAL_REVIEW"
            ),
        }
        event["event_hash"] = _digest(event)
        with self._uow.atomic():
            self._repo.append_rule_proposal_draft_event(event)
            self._append_audit(
                (
                    "optional_rule_excluded_from_proposed_set"
                    if excluded
                    else "optional_rule_returned_to_proposal_review"
                ),
                {
                    "review_id": review_id,
                    "rule_id": rule_id,
                    "rule_version": version,
                    "action": action,
                    "reason": event["reason"],
                },
                review_id=review_id,
                occurred_at=timestamp,
            )
        return event

    def draft_proposal_exclusions(
        self, review_id: str
    ) -> list[dict[str, Any]]:
        self._authorize(Permission.RULE_BOUND_READ)
        return self._repo.current_rule_proposal_draft_exclusions(review_id)

    def create_optional_draft(
        self,
        *,
        name: str,
        purpose: str,
        severity: str,
        operator: str,
        threshold: str,
    ) -> dict[str, Any]:
        self._authorize(Permission.RULE_OPTIONAL_DRAFT_MANAGE)
        rule_id = "OPT-" + self._id()[:12].upper()
        return self._append_draft(
            rule_id=rule_id,
            version="1.0.0",
            predecessor_version=None,
            name=name,
            purpose=purpose,
            severity=severity,
            operator=operator,
            threshold=threshold,
            reason="OPTIONAL_RULE_CREATED",
        )

    def edit_optional_draft(
        self,
        rule_id: str,
        *,
        name: str,
        purpose: str,
        severity: str,
        operator: str,
        threshold: str,
    ) -> dict[str, Any]:
        self._authorize(Permission.RULE_OPTIONAL_DRAFT_MANAGE)
        current = self._require_optional(rule_id)
        version = self._next_version(current["version"])
        return self._append_draft(
            rule_id=rule_id,
            version=version,
            predecessor_version=current["version"],
            name=name,
            purpose=purpose,
            severity=severity,
            operator=operator,
            threshold=threshold,
            reason="OPTIONAL_RULE_EDITED_AS_SUCCESSOR",
        )

    def test_draft(
        self,
        review_id: str,
        dataset,
        rule_id: str,
        version: str,
    ) -> dict[str, Any]:
        self._authorize(Permission.RULE_OPTIONAL_DRAFT_MANAGE)
        definition = self._require_optional(rule_id, version)
        if definition["lifecycle_status"] not in {"DRAFT", "TESTED"}:
            raise RuleManagementError("Only a Draft or Tested rule version can be tested.")
        current_set_id = self._repo.current_rule_set_id(review_id)
        if not current_set_id:
            raise RuleManagementError("The review has no governed Rule Set Version.")
        base = self._repo.rule_set_manifest(current_set_id)
        if base is None:
            raise RuleManagementError("The current Rule Set Version cannot be loaded.")
        candidate = self._domain_definition(
            definition,
            ordinal=max((item.ordinal for item in base.rules), default=0) + 1,
        )
        rules = tuple(item for item in base.rules if item.rule_id != rule_id) + (
            candidate,
        )
        manifest = RuleSetManifest(
            f"test-{rule_id}-{version}",
            version,
            rules,
            base.protected_baseline_id,
        )
        evaluation = self._engine.evaluate(dataset, manifest)
        execution = next(
            item for item in evaluation.executions if item.rule_id == rule_id
        )
        metrics = {
            "status": execution.status.value,
            "pass_count": execution.pass_count,
            "fail_count": execution.fail_count,
            "not_evaluated_count": execution.not_evaluated_count,
        }
        tested_at = self._clock.now()
        test_id = "ruletest_" + self._id()
        ledger_hash = _digest(
            {
                "test_id": test_id,
                "review_id": review_id,
                "rule_id": rule_id,
                "rule_version": version,
                "dataset_fingerprint": dataset.fingerprint,
                "metrics": metrics,
            }
        )
        with self._uow.atomic():
            self._repo.append_rule_test(
                {
                    "test_id": test_id,
                    "review_id": review_id,
                    "rule_id": rule_id,
                    "rule_version": version,
                    "dataset_fingerprint": dataset.fingerprint,
                    "status": "COMPLETE",
                    "metrics": metrics,
                    "ledger_hash": ledger_hash,
                    "actor_id": self._actor.actor_id,
                    "tested_at": tested_at,
                }
            )
            if definition["lifecycle_status"] == "DRAFT":
                self._append_lifecycle(
                    rule_id,
                    version,
                    "TESTED",
                    "DRAFT_RULE_TEST_COMPLETED",
                    tested_at,
                )
            self._append_audit(
                "optional_rule_tested",
                {
                    "review_id": review_id,
                    "test_id": test_id,
                    "rule_id": rule_id,
                    "rule_version": version,
                    "dataset_fingerprint": dataset.fingerprint,
                    "metrics": metrics,
                },
                review_id=review_id,
            )
        return {
            "test_id": test_id,
            "rule_id": rule_id,
            "version": version,
            "dataset_fingerprint": dataset.fingerprint,
            "metrics": metrics,
            "ledger_hash": ledger_hash,
        }

    def activate_optional_version(
        self, review_id: str, rule_id: str, version: str
    ) -> RuleSetManifest:
        self._authorize(Permission.RULE_OPTIONAL_LIFECYCLE_MANAGE)
        definition = self._require_optional(rule_id, version)
        test = self._repo.latest_successful_rule_test(review_id, rule_id, version)
        if test is None:
            raise RuleManagementError(
                "Test this exact Draft Rule Version before saving it as active."
            )
        if definition["lifecycle_status"] not in {"TESTED", "ACTIVE"}:
            raise RuleManagementError("Only a Tested optional rule can be activated.")
        predecessor = None
        predecessor_version = definition.get("predecessor_version")
        if predecessor_version:
            predecessor = self._require_optional(
                rule_id, str(predecessor_version)
            )
        timestamp = self._clock.now()
        with self._uow.atomic():
            if (
                predecessor is not None
                and predecessor["lifecycle_status"] != "RETIRED"
            ):
                self._append_lifecycle(
                    rule_id,
                    str(predecessor["version"]),
                    "RETIRED",
                    f"SUPERSEDED_BY_{version}",
                    timestamp,
                )
            if definition["lifecycle_status"] != "ACTIVE":
                self._append_lifecycle(
                    rule_id,
                    version,
                    "ACTIVE",
                    "TESTED_OPTIONAL_RULE_ACTIVATED",
                    timestamp,
                )
            rule_set_id = self._replace_binding(
                review_id,
                rule_id,
                version,
                enabled=True,
                timestamp=timestamp,
                reason="OPTIONAL_RULE_VERSION_ACTIVATED",
            )
            self._append_audit(
                "optional_rule_activated",
                {
                    "review_id": review_id,
                    "rule_id": rule_id,
                    "rule_version": version,
                    "rule_set_id": rule_set_id,
                    "test_id": test["test_id"],
                    "superseded_rule_version": (
                        str(predecessor["version"])
                        if predecessor is not None
                        else None
                    ),
                },
                review_id=review_id,
            )
        manifest = self._repo.rule_set_manifest(rule_set_id)
        assert manifest is not None
        return manifest

    def set_optional_enabled(
        self, review_id: str, rule_id: str, enabled: bool
    ) -> RuleSetManifest:
        self._authorize(Permission.RULE_OPTIONAL_LIFECYCLE_MANAGE)
        member = self._bound_member(review_id, rule_id)
        current = self._require_optional(rule_id, member["rule_version"])
        if current["lifecycle_status"] == "RETIRED" and enabled:
            raise RuleManagementError("A Retired optional version cannot be re-enabled.")
        timestamp = self._clock.now()
        with self._uow.atomic():
            rule_set_id = self._replace_binding(
                review_id,
                rule_id,
                current["version"],
                enabled=enabled,
                timestamp=timestamp,
                reason=(
                    "OPTIONAL_RULE_ENABLED"
                    if enabled
                    else "OPTIONAL_RULE_DISABLED"
                ),
            )
            self._append_audit(
                "optional_rule_binding_changed",
                {
                    "review_id": review_id,
                    "rule_id": rule_id,
                    "rule_version": current["version"],
                    "enabled": enabled,
                    "rule_set_id": rule_set_id,
                },
                review_id=review_id,
            )
        manifest = self._repo.rule_set_manifest(rule_set_id)
        assert manifest is not None
        return manifest

    def retire_optional_rule(
        self, review_id: str, rule_id: str
    ) -> RuleSetManifest:
        self._authorize(Permission.RULE_OPTIONAL_LIFECYCLE_MANAGE)
        member = self._bound_member(review_id, rule_id)
        current = self._require_optional(rule_id, member["rule_version"])
        timestamp = self._clock.now()
        with self._uow.atomic():
            if current["lifecycle_status"] != "RETIRED":
                self._append_lifecycle(
                    rule_id,
                    current["version"],
                    "RETIRED",
                    "OPTIONAL_RULE_RETIRED",
                    timestamp,
                )
            rule_set_id = self._replace_binding(
                review_id,
                rule_id,
                current["version"],
                enabled=False,
                timestamp=timestamp,
                reason="OPTIONAL_RULE_RETIRED",
            )
            self._append_audit(
                "optional_rule_retired",
                {
                    "review_id": review_id,
                    "rule_id": rule_id,
                    "rule_version": current["version"],
                    "rule_set_id": rule_set_id,
                },
                review_id=review_id,
            )
        manifest = self._repo.rule_set_manifest(rule_set_id)
        assert manifest is not None
        return manifest

    def rule_set_history(
        self, review_id: str, *, administrative: bool = False
    ) -> list[dict[str, Any]]:
        self._authorize(
            Permission.RULE_LIBRARY_READ
            if administrative
            else Permission.RULE_BOUND_READ
        )
        return self._repo.rule_set_history(review_id)

    def submit_protected_change_request(
        self,
        *,
        review_id: str,
        dataset,
        rule_id: str,
        proposed_version: str,
        change_kind: str,
        name: str,
        purpose: str,
        severity: str,
        parameters: Mapping[str, Any],
        reason: str,
        prior_request_id: str | None = None,
    ) -> dict[str, Any]:
        """Create, test, lock, and submit one immutable protected successor."""

        self._authorize(Permission.RULE_PROTECTED_DRAFT_MANAGE)
        timestamp = self._clock.now()
        request_id = "protectreq_" + self._id()

        def submit() -> dict[str, Any]:
            basis = self._repo.generation_basis(review_id)
            if (
                getattr(dataset, "review_id", None) != review_id
                or basis is None
                or basis["dataset_fingerprint"] != dataset.fingerprint
            ):
                raise RuleManagementError(
                    "Protected qualification requires this review's confirmed "
                    "working dataset."
                )
            budget_count = len(dataset.budget_details)
            ged_count = len(dataset.ged_transactions)
            if (
                budget_count < 1
                or ged_count < 1
                or budget_count != int(basis["budget_record_count"])
                or ged_count != int(basis["ged_transaction_count"])
            ):
                raise RuleManagementError(
                    "Protected qualification requires the complete confirmed "
                    "Budget and GED populations."
                )
            current = self._repo.current_protected_rule(rule_id)
            if current is None or current["lifecycle_status"] != "ACTIVE":
                raise RuleManagementError(
                    "The active protected rule version is unavailable."
                )
            if current["evaluator_key"] not in _PROTECTED_CERTIFIED_EVALUATORS:
                raise RuleManagementError(
                    "The protected evaluator has no approved release "
                    "qualification suite."
                )
            proposed = str(proposed_version).strip()
            if not self._is_later_version(proposed, str(current["version"])):
                raise RuleManagementError(
                    "The proposed Rule Version must be later than the active version."
                )
            if self._repo.rule_version(rule_id, proposed) is not None:
                raise RuleManagementError(
                    "That protected Rule Version already exists."
                )
            requested_reason = str(reason).strip()
            if not requested_reason:
                raise RuleManagementError(
                    "A business reason is required for a protected change."
                )
            proposed_name = str(name).strip()
            proposed_purpose = str(purpose).strip()
            proposed_severity = str(severity)
            if not proposed_name or not proposed_purpose:
                raise RuleManagementError(
                    "Rule name and business purpose are required."
                )
            if proposed_severity not in {"Critical", "High", "Medium", "Low"}:
                raise RuleManagementError("Select a supported rule severity.")
            proposed_parameters = self._plain_json_mapping(parameters)
            approved_parameter_fields = _PROTECTED_PARAMETER_FIELDS.get(
                rule_id
            )
            if approved_parameter_fields is None:
                raise RuleManagementError(
                    "The protected Rule ID has no approved configuration schema."
                )
            unapproved_parameters = sorted(
                set(proposed_parameters) - approved_parameter_fields
            )
            if unapproved_parameters:
                raise RuleManagementError(
                    "No configurable parameters are approved for this protected "
                    "rule. Remove: " + ", ".join(unapproved_parameters)
                )
            semantic_changed = any(
                (
                    proposed_name != current["name"],
                    proposed_purpose != current["purpose"],
                    proposed_severity != current["severity"],
                )
            )
            parameter_changed = proposed_parameters != current["parameters"]
            if parameter_changed:
                raise RuleManagementError(
                    "This protected rule has no approved parameter change for "
                    "the current evaluator release."
                )
            actual_kind = (
                "SEMANTIC_AND_PARAMETER"
                if semantic_changed and parameter_changed
                else (
                    "SEMANTIC"
                    if semantic_changed
                    else ("PARAMETER" if parameter_changed else "")
                )
            )
            if not actual_kind:
                raise RuleManagementError(
                    "Change at least one semantic or configuration value."
                )
            if str(change_kind).upper() != actual_kind:
                raise RuleManagementError(
                    f"Select {actual_kind.replace('_', ' ').title()} for this proposal."
                )
            if prior_request_id:
                previous = self._repo.protected_change_request(prior_request_id)
                if (
                    previous is None
                    or previous["rule_id"] != rule_id
                    or previous["status"] == "PENDING_APPROVAL"
                ):
                    raise RuleManagementError(
                        "A revised proposal must reference a terminal prior "
                        "request for the same protected rule."
                    )

            definition = {
                "rule_id": rule_id,
                "version": proposed,
                "classification": "CORE_MANDATORY",
                "name": proposed_name,
                "purpose": proposed_purpose,
                "severity": proposed_severity,
                "baseline_status": "PROTECTED_BASELINE",
                # The governed product definition may evolve; executable evaluator
                # substitution remains a code/release concern, never user-authored input.
                "evaluator_key": current["evaluator_key"],
                "parameters": proposed_parameters,
                "required_fields": tuple(current["required_fields"]),
                "grouping_keys": tuple(current["grouping_keys"]),
                "predecessor_version": current["version"],
                "created_by": self._actor.actor_id,
                "created_at": timestamp,
            }
            definition["content_hash"] = _digest(definition)
            self._repo.append_rule_version(definition)
            self._append_lifecycle(
                rule_id,
                proposed,
                "DRAFT",
                "PROTECTED_SUCCESSOR_AUTHORED",
                timestamp,
            )

            baseline_id = self._repo.current_protected_baseline_id()
            definitions: list[RuleDefinitionVersion] = []
            for member in self._repo.protected_baseline_members(baseline_id):
                value = (
                    definition
                    if member["rule_id"] == rule_id
                    else self._repo.rule_version(
                        member["rule_id"], member["rule_version"]
                    )
                )
                if value is None:
                    raise RuleManagementError(
                        "The active protected baseline cannot be reconstructed."
                    )
                definitions.append(
                    self._domain_definition(
                        value, ordinal=int(member["ordinal"])
                    )
                )
            candidate_manifest = RuleSetManifest(
                rule_set_id=f"protected-test-{request_id}",
                version=proposed,
                rules=tuple(definitions),
                protected_baseline_id=baseline_id,
            )
            evaluation = self._engine.evaluate(dataset, candidate_manifest)
            execution = next(
                item
                for item in evaluation.executions
                if item.rule_id == rule_id
            )
            if execution.pass_count + execution.fail_count < 1:
                raise RuleManagementError(
                    "The confirmed review did not provide an evaluable scope for "
                    "this protected candidate."
                )
            protected_rule_ids = {
                definition.rule_id for definition in definitions
            }
            qualification = {
                "suite_id": _PROTECTED_EVALUATOR_SUITE_ID,
                "released_suite_coverage": (
                    "POSITIVE_NEGATIVE_BOUNDARY"
                ),
                "basis": "NON_EXECUTABLE_SEMANTIC_SUCCESSOR",
                "inherited_evaluator_from_version": current["version"],
                "candidate_dataset_evaluation": {
                    "status": execution.status.value,
                    "pass_count": execution.pass_count,
                    "fail_count": execution.fail_count,
                    "not_evaluated_count": execution.not_evaluated_count,
                },
                "checks": {
                    "evaluator_key_unchanged": (
                        definition["evaluator_key"]
                        == current["evaluator_key"]
                    ),
                    "input_fields_unchanged": (
                        tuple(definition["required_fields"])
                        == tuple(current["required_fields"])
                    ),
                    "grouping_keys_unchanged": (
                        tuple(definition["grouping_keys"])
                        == tuple(current["grouping_keys"])
                    ),
                    "approved_parameters_unchanged": (
                        definition["parameters"] == current["parameters"]
                    ),
                    "exact_five_protected_members": (
                        len(definitions) == 5
                        and protected_rule_ids
                        == {
                            "CORE-01",
                            "CORE-02",
                            "CORE-03",
                            "CORE-04",
                            "CORE-05",
                        }
                    ),
                },
            }
            if not all(qualification["checks"].values()):
                raise RuleManagementError(
                    "The protected candidate failed deterministic qualification."
                )
            metrics = {
                "status": execution.status.value,
                "pass_count": execution.pass_count,
                "fail_count": execution.fail_count,
                "not_evaluated_count": execution.not_evaluated_count,
                "qualification": qualification,
            }
            test_id = "ruletest_" + self._id()
            evidence_context_hash = _digest(
                {
                    "review_id": review_id,
                    "dataset_fingerprint": dataset.fingerprint,
                }
            )
            ledger_hash = _digest(
                {
                    "test_id": test_id,
                    "review_id": review_id,
                    "rule_id": rule_id,
                    "rule_version": proposed,
                    "dataset_fingerprint": dataset.fingerprint,
                    "metrics": metrics,
                }
            )
            self._repo.append_protected_candidate_test(
                {
                    "test_id": test_id,
                    "rule_id": rule_id,
                    "rule_version": proposed,
                    "evidence_context_hash": evidence_context_hash,
                    "dataset_fingerprint": dataset.fingerprint,
                    "metrics": metrics,
                    "ledger_hash": ledger_hash,
                    "actor_id": self._actor.actor_id,
                    "tested_at": timestamp,
                }
            )
            self._append_lifecycle(
                rule_id,
                proposed,
                "TESTED",
                "PROTECTED_SUCCESSOR_QUALIFIED_AGAINST_PINNED_SUITE",
                timestamp,
            )
            request = {
                "request_id": request_id,
                "rule_id": rule_id,
                "requested_baseline_id": baseline_id,
                "predecessor_version": current["version"],
                "candidate_version": proposed,
                "change_kind": actual_kind,
                "reason": requested_reason,
                "proposed_effective_at": timestamp,
                "requester_actor_id": self._actor.actor_id,
                "requested_at": timestamp,
                "candidate_content_hash": definition["content_hash"],
                "evidence_context_hash": evidence_context_hash,
                "before_definition": self._request_definition(current),
                "after_definition": self._request_definition(definition),
                "test_id": test_id,
                "prior_request_id": prior_request_id,
            }
            self._repo.append_protected_change_request(request)
            self._append_audit(
                "protected_change_requested",
                {
                    "request_id": request_id,
                    "review_id": review_id,
                    "rule_id": rule_id,
                    "requested_baseline_id": baseline_id,
                    "predecessor_version": current["version"],
                    "candidate_version": proposed,
                    "change_kind": actual_kind,
                    "candidate_content_hash": definition["content_hash"],
                    "test_id": test_id,
                    "reason": requested_reason,
                },
                review_id=review_id,
            )
            saved = self._repo.protected_change_request(request_id)
            assert saved is not None
            return saved

        return self._execute_governed(
            Permission.RULE_PROTECTED_CHANGE_REQUEST,
            submit,
        )

    def list_protected_change_requests(
        self, *, for_decision: bool = False
    ) -> list[dict[str, Any]]:
        self._authorize(
            Permission.RULE_PROTECTED_CHANGE_DECIDE
            if for_decision
            else Permission.RULE_PROTECTED_CHANGE_REQUEST
        )
        return self._repo.list_protected_change_requests()

    def decide_protected_change(
        self,
        request_id: str,
        *,
        decision: str,
        reason: str,
    ) -> dict[str, Any]:
        """Approve/activate or reject one request under distinct-actor control."""

        self._authorize(Permission.RULE_PROTECTED_CHANGE_DECIDE)
        initial = self._repo.protected_change_request(request_id)
        if initial is None:
            raise RuleManagementError("The protected change request is unavailable.")
        if initial["requester_actor_id"] == self._actor.actor_id:
            raise RuleManagementError(
                "The requester cannot approve or reject their own protected change."
            )
        context = AuthorizationContext(
            protected_requester_actor_id=initial["requester_actor_id"]
        )
        normalized = str(decision).strip().upper()
        if normalized not in {"APPROVED", "REJECTED"}:
            raise RuleManagementError("Select Approve or Reject.")
        decision_reason = str(reason).strip()
        if not decision_reason:
            raise RuleManagementError(
                "A decision reason is required for protected governance."
            )

        def decide() -> dict[str, Any]:
            request = self._repo.protected_change_request(request_id)
            if request is None:
                raise RuleManagementError(
                    "The protected change request is unavailable."
                )
            if request["status"] != "PENDING_APPROVAL":
                raise RuleManagementError(
                    "This protected change request already has a terminal decision."
                )
            if normalized == "APPROVED" and (
                self._repo.current_protected_baseline_id()
                != request["requested_baseline_id"]
            ):
                raise RuleManagementError(
                    "The protected baseline changed after this request. "
                    "Submit a revised successor against the current baseline."
                )
            timestamp = self._clock.now()
            decision_value = {
                "request_id": request_id,
                "decision": normalized,
                "approver_actor_id": self._actor.actor_id,
                "decided_at": timestamp,
                "reason": decision_reason,
            }
            decision_value["decision_hash"] = _digest(decision_value)
            self._repo.append_protected_change_decision(decision_value)
            resulting_baseline_id = None
            if normalized == "APPROVED":
                current = self._repo.current_protected_rule(request["rule_id"])
                if (
                    current is None
                    or current["version"] != request["predecessor_version"]
                ):
                    raise RuleManagementError(
                        "The active baseline changed after this request. "
                        "Reject it and submit a revised successor."
                    )
                activation_hash = _digest(
                    {
                        "request_id": request_id,
                        "rule_id": request["rule_id"],
                        "candidate_version": request["candidate_version"],
                        "approver_actor_id": self._actor.actor_id,
                        "activated_at": timestamp,
                    }
                )
                resulting_baseline_id = self._repo.activate_protected_change(
                    request,
                    activated_at=timestamp,
                    activation_hash=activation_hash,
                )
                self._append_lifecycle(
                    request["rule_id"],
                    request["predecessor_version"],
                    "RETIRED",
                    f"SUPERSEDED_BY_{request['candidate_version']}",
                    timestamp,
                )
                self._append_lifecycle(
                    request["rule_id"],
                    request["candidate_version"],
                    "ACTIVE",
                    "PROTECTED_CHANGE_APPROVED_AND_ACTIVATED",
                    timestamp,
                )
            self._append_audit(
                (
                    "protected_change_approved_and_activated"
                    if normalized == "APPROVED"
                    else "protected_change_rejected"
                ),
                {
                    "request_id": request_id,
                    "rule_id": request["rule_id"],
                    "candidate_version": request["candidate_version"],
                    "decision": normalized,
                    "decision_reason": decision_reason,
                    "requester_actor_id": request["requester_actor_id"],
                    "approver_actor_id": self._actor.actor_id,
                    "resulting_baseline_id": resulting_baseline_id,
                },
            )
            saved = self._repo.protected_change_request(request_id)
            assert saved is not None
            return saved

        return self._execute_governed(
            Permission.RULE_PROTECTED_CHANGE_DECIDE,
            decide,
            context=context,
        )

    def workspace_upgrade_status(
        self, review_id: str
    ) -> dict[str, Any] | None:
        """Return the minimal bound-rule upgrade state a Reviewer may inspect."""

        self._authorize(Permission.RULE_BOUND_READ)
        return self._repo.workspace_upgrade_status(review_id)

    def list_workspace_upgrade_candidates(self) -> list[dict[str, Any]]:
        """Return non-financial workspace metadata for global governance."""

        self._authorize(
            Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_REQUEST
        )
        return self._repo.list_workspace_upgrade_candidates()

    def list_workspace_upgrade_requests(
        self,
        review_id: str | None = None,
        *,
        for_decision: bool = False,
    ) -> list[dict[str, Any]]:
        self._authorize(
            Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE
            if for_decision
            else Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_REQUEST
        )
        return self._repo.list_workspace_upgrade_requests(
            review_id=review_id
        )

    def request_workspace_upgrade(
        self,
        review_id: str,
        reason: str,
        target_baseline_id: str | None = None,
    ) -> dict[str, Any]:
        """Request one explicit existing-workspace protected-baseline upgrade."""

        requested_reason = str(reason).strip()
        if not requested_reason:
            raise RuleManagementError(
                "A business reason is required for a workspace baseline upgrade."
            )
        request_id = "workspaceupgradereq_" + self._id()
        timestamp = self._clock.now()

        def submit() -> dict[str, Any]:
            candidate = next(
                (
                    value
                    for value in self._repo.list_workspace_upgrade_candidates()
                    if value["review_id"] == review_id
                ),
                None,
            )
            if candidate is None:
                raise RuleManagementError(
                    "The selected review has no governed workspace Rule Set."
                )
            if not candidate["upgrade_available"]:
                raise RuleManagementError(candidate["upgrade_reason"])
            selected_target = (
                str(target_baseline_id)
                if target_baseline_id is not None
                else str(candidate["target_baseline_id"])
            )
            if selected_target != candidate["target_baseline_id"]:
                raise RuleManagementError(
                    "The selected target is not the currently effective "
                    "Protected Baseline Version."
                )
            pending = next(
                (
                    value
                    for value in self._repo.list_workspace_upgrade_requests(
                        review_id=review_id
                    )
                    if value["status"] == "PENDING_APPROVAL"
                    and value["requested_rule_set_id"]
                    == candidate["current_rule_set_id"]
                    and value["target_baseline_id"] == selected_target
                ),
                None,
            )
            if pending is not None:
                raise RuleManagementError(
                    "This workspace already has a pending request for the "
                    "effective Protected Baseline Version."
                )
            request = {
                "request_id": request_id,
                "request_type": "WORKSPACE_BASELINE_UPGRADE",
                "review_id": review_id,
                "requested_rule_set_id": candidate["current_rule_set_id"],
                "requested_rule_set_content_hash": candidate[
                    "current_rule_set_content_hash"
                ],
                "source_baseline_id": candidate["source_baseline_id"],
                "target_baseline_id": selected_target,
                "target_baseline_hash": candidate["target_baseline_hash"],
                "requested_run_id": candidate["latest_run_id"],
                "requested_generation_id": candidate[
                    "latest_generation_id"
                ],
                "requester_actor_id": self._actor.actor_id,
                "requested_at": timestamp,
                "reason": requested_reason,
            }
            request["request_hash"] = _digest(request)
            self._repo.append_workspace_upgrade_request(request)
            saved = self._repo.workspace_upgrade_request(request_id)
            assert saved is not None
            self._append_audit(
                "workspace_baseline_upgrade_requested",
                self._workspace_upgrade_audit_payload(
                    saved, transition="REQUESTED"
                ),
                review_id=review_id,
                outcome="PENDING_APPROVAL",
                occurred_at=timestamp,
            )
            return saved

        return self._execute_governed(
            Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_REQUEST,
            submit,
        )

    def decide_workspace_upgrade(
        self,
        request_id: str,
        *,
        decision: str,
        reason: str,
    ) -> dict[str, Any]:
        """Approve/apply or reject one workspace upgrade with separation of duties."""

        initial = self._repo.workspace_upgrade_request(request_id)
        context = (
            AuthorizationContext(
                protected_requester_actor_id=initial[
                    "requester_actor_id"
                ]
            )
            if initial is not None
            else None
        )

        def decide() -> dict[str, Any]:
            normalized = str(decision).strip().upper()
            if normalized not in {"APPROVED", "REJECTED"}:
                raise RuleManagementError("Select Approve or Reject.")
            decision_reason = str(reason).strip()
            if not decision_reason:
                raise RuleManagementError(
                    "A decision reason is required for workspace baseline governance."
                )
            request = self._repo.workspace_upgrade_request(request_id)
            if request is None:
                raise RuleManagementError(
                    "The workspace baseline upgrade request is unavailable."
                )
            if request["status"] != "PENDING_APPROVAL":
                raise RuleManagementError(
                    "This workspace baseline upgrade already has a terminal decision."
                )
            if normalized == "APPROVED":
                status = self._repo.workspace_upgrade_status(
                    request["review_id"]
                )
                if (
                    status is None
                    or status["current_rule_set_id"]
                    != request["requested_rule_set_id"]
                ):
                    raise RuleManagementError(
                        "The workspace Rule Set changed after this request. "
                        "Reject it and submit a current request."
                    )
                if (
                    status["target_baseline_id"]
                    != request["target_baseline_id"]
                    or status["target_baseline_hash"]
                    != request["target_baseline_hash"]
                ):
                    raise RuleManagementError(
                        "The effective protected baseline changed after this "
                        "request. Reject it and submit a current request."
                    )
                if (
                    status["latest_run_id"] != request["requested_run_id"]
                    or status["latest_generation_id"]
                    != request["requested_generation_id"]
                ):
                    raise RuleManagementError(
                        "The authoritative Validation Run changed after this "
                        "request. Reject it and submit a current request."
                    )
            timestamp = self._clock.now()
            decision_value = {
                "request_id": request_id,
                "decision": normalized,
                "approver_actor_id": self._actor.actor_id,
                "decided_at": timestamp,
                "reason": decision_reason,
            }
            decision_value["decision_hash"] = _digest(decision_value)
            self._repo.append_workspace_upgrade_decision(decision_value)
            if normalized == "APPROVED":
                try:
                    self._repo.apply_workspace_baseline_upgrade(
                        request,
                        actor_id=self._actor.actor_id,
                        applied_at=timestamp,
                    )
                except ValueError as exc:
                    raise RuleManagementError(str(exc)) from exc
            saved = self._repo.workspace_upgrade_request(request_id)
            assert saved is not None
            transition = (
                "APPROVED_AND_APPLIED"
                if normalized == "APPROVED"
                else "REJECTED"
            )
            audit_outcome = (
                "APPLIED" if normalized == "APPROVED" else "REJECTED"
            )
            self._append_audit(
                (
                    "workspace_baseline_upgrade_approved_and_applied"
                    if normalized == "APPROVED"
                    else "workspace_baseline_upgrade_rejected"
                ),
                self._workspace_upgrade_audit_payload(
                    saved, transition=transition
                ),
                review_id=request["review_id"],
                outcome=audit_outcome,
                occurred_at=timestamp,
            )
            return saved

        return self._execute_governed(
            Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE,
            decide,
            context=context,
        )

    def _append_draft(self, **value) -> dict[str, Any]:
        name = str(value["name"]).strip()
        purpose = str(value["purpose"]).strip()
        severity = str(value["severity"])
        operator = str(value["operator"]).upper()
        threshold = _canonical_threshold(value["threshold"])
        if not name or not purpose:
            raise RuleManagementError("Rule name and business purpose are required.")
        if severity not in {"Critical", "High", "Medium", "Low"}:
            raise RuleManagementError("Select a supported rule severity.")
        if operator not in {"EQ", "NE", "LT", "LTE", "GT", "GTE"}:
            raise RuleManagementError("Select a supported comparison operator.")
        definition = {
            "rule_id": value["rule_id"],
            "version": value["version"],
            "classification": "OPTIONAL_CONFIGURABLE",
            "name": name,
            "purpose": purpose,
            "severity": severity,
            "baseline_status": "OPTIONAL_CONFIGURABLE",
            "evaluator_key": "ged_amount_threshold",
            "parameters": {"operator": operator, "threshold": threshold},
            "required_fields": ("ged.amount",),
            "grouping_keys": ("source_record",),
            "predecessor_version": value["predecessor_version"],
            "created_by": self._actor.actor_id,
            "created_at": self._clock.now(),
        }
        definition["content_hash"] = _digest(definition)
        with self._uow.atomic():
            self._repo.append_rule_version(definition)
            self._append_lifecycle(
                definition["rule_id"],
                definition["version"],
                "DRAFT",
                value["reason"],
                definition["created_at"],
            )
            self._append_audit(
                "optional_rule_draft_saved",
                {
                    "rule_id": definition["rule_id"],
                    "rule_version": definition["version"],
                    "content_hash": definition["content_hash"],
                    "predecessor_version": definition["predecessor_version"],
                },
            )
        saved = self._repo.rule_version(
            definition["rule_id"], definition["version"]
        )
        assert saved is not None
        return saved

    def _replace_binding(
        self,
        review_id: str,
        rule_id: str,
        rule_version: str,
        *,
        enabled: bool,
        timestamp: str,
        reason: str,
    ) -> str:
        current_set = self._repo.current_rule_set_id(review_id)
        if not current_set:
            current_set = self._repo.ensure_initial_rule_set(
                review_id,
                actor_id=self._actor.actor_id,
                created_at=timestamp,
            )
        members = self._repo.rule_set_members(current_set)
        replaced = False
        for item in members:
            if item["rule_id"] == rule_id:
                item["rule_version"] = rule_version
                item["enabled"] = enabled
                replaced = True
        if not replaced:
            members.append(
                {
                    "ordinal": max(
                        (int(item["ordinal"]) for item in members), default=0
                    )
                    + 1,
                    "rule_id": rule_id,
                    "rule_version": rule_version,
                    "enabled": enabled,
                }
            )
        return self._repo.create_successor_rule_set(
            review_id,
            members=members,
            actor_id=self._actor.actor_id,
            created_at=timestamp,
            reason=reason,
        )

    def _append_lifecycle(
        self,
        rule_id: str,
        version: str,
        status: str,
        reason: str,
        timestamp: str,
    ) -> None:
        ordinal = self._repo.next_rule_lifecycle_ordinal(rule_id, version)
        payload = {
            "rule_id": rule_id,
            "rule_version": version,
            "ordinal": ordinal,
            "status": status,
            "actor_id": self._actor.actor_id,
            "occurred_at": timestamp,
            "reason": reason,
        }
        payload["event_id"] = "ruleevt_" + self._id()
        payload["event_hash"] = _digest(payload)
        self._repo.append_rule_lifecycle(payload)

    def _append_audit(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        review_id: str | None = None,
        outcome: str = "SUCCEEDED",
        occurred_at: str | None = None,
    ) -> None:
        if self._audit is None:
            return
        scopes = []
        if payload.get("rule_id"):
            scopes.append(AuditScope("Rule", str(payload["rule_id"])))
        target_baseline = payload.get(
            "target_baseline_id"
        ) or payload.get("target_protected_baseline_id")
        if target_baseline:
            scopes.append(
                AuditScope(
                    "ProtectedBaseline",
                    str(target_baseline),
                )
            )
        if review_id:
            scopes.append(AuditScope("Review", review_id))
        if not scopes:
            scopes.append(AuditScope("RuleGovernance", event_type))
        self._audit.append(
            event_type=event_type,
            actor=self._actor,
            occurred_at=occurred_at or self._clock.now(),
            correlation_id="corr_rule_" + self._id(),
            payload=payload,
            outcome=outcome,
            stream_type="RULE_GOVERNANCE",
            scopes=tuple(scopes),
        )

    def _require_optional(
        self, rule_id: str, version: str | None = None
    ) -> dict[str, Any]:
        if rule_id.startswith("CORE-"):
            raise RuleManagementError(
                "Protected Core Rules cannot be changed through optional-rule actions."
            )
        value = (
            self._repo.rule_version(rule_id, version)
            if version
            else self._repo.latest_rule_version(rule_id)
        )
        if value is None or value["classification"] != "OPTIONAL_CONFIGURABLE":
            raise RuleManagementError("The selected optional rule version is unavailable.")
        return value

    def _bound_member(self, review_id: str, rule_id: str) -> dict[str, Any]:
        rule_set_id = self._repo.current_rule_set_id(review_id)
        if not rule_set_id:
            raise RuleManagementError("The review has no governed Rule Set Version.")
        member = next(
            (
                item
                for item in self._repo.rule_set_members(rule_set_id)
                if item["rule_id"] == rule_id
            ),
            None,
        )
        if member is None:
            raise RuleManagementError(
                "The selected optional rule is not bound to this review."
            )
        return member

    def _execute_governed(
        self,
        permission: Permission,
        operation,
        *,
        context: AuthorizationContext | None = None,
    ):
        if self._authorization_executor is not None:
            return self._authorization_executor(permission, operation, context)
        if context is None:
            self._authorize(permission)
        else:
            self._authorize(permission, context)
        with self._uow.atomic():
            return operation()

    @staticmethod
    def _workspace_upgrade_audit_payload(
        request: Mapping[str, Any],
        *,
        transition: str,
    ) -> dict[str, Any]:
        """Build the applicable complete NFR-090 event schema."""

        if transition not in {
            "REQUESTED",
            "REJECTED",
            "APPROVED_AND_APPLIED",
        }:
            raise RuleManagementError(
                "The workspace-upgrade audit transition is unsupported."
            )

        def required(field: str):
            value = request.get(field)
            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                raise RuleManagementError(
                    f"Workspace-upgrade audit evidence is missing {field}."
                )
            return value

        protected_ids = list(required("protected_rule_ids"))
        expected_ids = [
            "CORE-01",
            "CORE-02",
            "CORE-03",
            "CORE-04",
            "CORE-05",
        ]
        if protected_ids != expected_ids:
            raise RuleManagementError(
                "Workspace-upgrade audit evidence must contain the exact "
                "five protected Rule IDs."
            )
        source_evidence = list(required("source_protected_rule_evidence"))
        target_evidence = list(required("target_protected_rule_evidence"))
        if (
            [item["rule_id"] for item in source_evidence]
            != expected_ids
            or [item["rule_id"] for item in target_evidence]
            != expected_ids
        ):
            raise RuleManagementError(
                "Workspace-upgrade audit evidence must resolve every "
                "protected Rule Version."
            )

        def definitions(evidence):
            return [
                {
                    "rule_id": item["rule_id"],
                    "rule_version": item["rule_version"],
                    "definition_content_hash": item[
                        "definition_content_hash"
                    ],
                }
                for item in evidence
            ]

        def configurations(evidence):
            return [
                {
                    "rule_id": item["rule_id"],
                    "rule_version": item["rule_version"],
                    "configuration": item["configuration"],
                    "configuration_hash": item["configuration_hash"],
                }
                for item in evidence
            ]

        def versions(evidence):
            return [
                {
                    "rule_id": item["rule_id"],
                    "rule_version": item["rule_version"],
                }
                for item in evidence
            ]

        before_binding = {
            "workspace_id": required("review_id"),
            "workspace_rule_set_id": required("requested_rule_set_id"),
            "workspace_rule_set_version": required(
                "requested_rule_set_version"
            ),
            "workspace_rule_set_content_hash": required(
                "requested_rule_set_content_hash"
            ),
            "protected_baseline_id": required("source_baseline_id"),
            "protected_baseline_version": required(
                "source_baseline_version"
            ),
            "protected_baseline_hash": required("source_baseline_hash"),
            "protected_rule_versions": versions(source_evidence),
            "optional_advisory_binding_count": required(
                "preserved_optional_advisory_binding_count"
            ),
            "optional_advisory_binding_hash": required(
                "preserved_optional_advisory_binding_hash"
            ),
            "optional_advisory_rule_ids": list(
                required("preserved_optional_advisory_rule_ids")
            ),
        }
        proposed_after_binding = {
            "workspace_id": required("review_id"),
            "workspace_rule_set_id": (
                f"ruleset_{required('review_id')}_"
                f"{int(required('requested_rule_set_version')) + 1}"
            ),
            "workspace_rule_set_version": (
                int(required("requested_rule_set_version")) + 1
            ),
            "protected_baseline_id": required("target_baseline_id"),
            "protected_baseline_version": required(
                "target_baseline_version"
            ),
            "protected_baseline_hash": required("target_baseline_hash"),
            "protected_rule_versions": versions(target_evidence),
            "preserved_optional_advisory_binding_count": required(
                "preserved_optional_advisory_binding_count"
            ),
            "preserved_optional_advisory_binding_hash": required(
                "preserved_optional_advisory_binding_hash"
            ),
            "preserved_optional_advisory_rule_ids": list(
                required("preserved_optional_advisory_rule_ids")
            ),
        }
        requested = transition == "REQUESTED"
        rejected = transition == "REJECTED"
        event_outcome = (
            "PENDING_APPROVAL"
            if requested
            else ("REJECTED" if rejected else "APPLIED")
        )
        common = {
            "transition": transition,
            "requested_action": _WORKSPACE_UPGRADE_ACTION,
            "protected_rule_id_set": protected_ids,
            "outcome": event_outcome,
            "reason": (
                required("reason")
                if requested
                else required("decision_reason")
            ),
            "request_id": required("request_id"),
            "workspace_id": required("review_id"),
            "target_protected_baseline_id": required(
                "target_baseline_id"
            ),
            "target_protected_baseline_version": required(
                "target_baseline_version"
            ),
            "requester_actor_id": required("requester_actor_id"),
            "request_timestamp": required("requested_at"),
        }
        proposal = {
            "before_rule_definition": definitions(source_evidence),
            "before_rule_configuration": configurations(
                source_evidence
            ),
            "before_binding": before_binding,
            "old_rule_version": versions(source_evidence),
            "proposed_after_rule_definition": definitions(
                target_evidence
            ),
            "proposed_after_rule_configuration": configurations(
                target_evidence
            ),
            "proposed_after_binding": proposed_after_binding,
            "proposed_successor_rule_version": versions(target_evidence),
            "proposed_effective_time": (
                "IMMEDIATE_ON_DISTINCT_FINANCIAL_CONTROL_APPROVAL"
            ),
        }
        if requested:
            return {
                "event_schema": _PROTECTED_REQUEST_AUDIT_SCHEMA,
                **common,
                **proposal,
                "approver_actor_id": _NOT_APPLICABLE,
                "decision_timestamp": _NOT_APPLICABLE,
                "decision_reason": _NOT_APPLICABLE,
                "activation_timestamp": _NOT_APPLICABLE,
                "prior_protected_baseline_version": _NOT_APPLICABLE,
                "resulting_protected_baseline_version": (
                    _NOT_APPLICABLE
                ),
                "activation_outcome": _NOT_APPLICABLE,
            }
        if rejected:
            return {
                "event_schema": _PROTECTED_DECISION_AUDIT_SCHEMA,
                **common,
                **proposal,
                "approver_actor_id": required("approver_actor_id"),
                "decision_timestamp": required("decided_at"),
                "decision_reason": required("decision_reason"),
                "decision_outcome": "REJECTED",
                "activation_timestamp": _NOT_APPLICABLE,
                "prior_protected_baseline_version": _NOT_APPLICABLE,
                "resulting_protected_baseline_version": (
                    _NOT_APPLICABLE
                ),
                "activation_outcome": _NOT_APPLICABLE,
            }

        resulting_binding = {
            **proposed_after_binding,
            "workspace_rule_set_id": required("resulting_rule_set_id"),
            "workspace_rule_set_version": required(
                "resulting_rule_set_version"
            ),
            "workspace_rule_set_content_hash": required(
                "resulting_rule_set_content_hash"
            ),
        }
        return {
            "event_schema": _WORKSPACE_UPGRADE_AUDIT_SCHEMA,
            **common,
            "source_protected_baseline_id": required(
                "source_baseline_id"
            ),
            "source_protected_baseline_version": required(
                "source_baseline_version"
            ),
            "prior_workspace_rule_set_id": required(
                "requested_rule_set_id"
            ),
            "prior_workspace_rule_set_version": required(
                "requested_rule_set_version"
            ),
            "resulting_workspace_rule_set_id": required(
                "resulting_rule_set_id"
            ),
            "resulting_workspace_rule_set_version": required(
                "resulting_rule_set_version"
            ),
            "prior_binding": before_binding,
            "resulting_binding": resulting_binding,
            "authorizing_financial_control_approver_actor_id": required(
                "approver_actor_id"
            ),
            "authorization_timestamp": required("decided_at"),
            "activation_timestamp": required("applied_at"),
            "activation_outcome": "APPLIED",
            "before_rule_definition": _NOT_APPLICABLE,
            "after_rule_definition": _NOT_APPLICABLE,
            "proposed_successor_rule_version": _NOT_APPLICABLE,
        }

    @staticmethod
    def _plain_json_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise RuleManagementError(
                "Protected configuration parameters must be a JSON object."
            )
        try:
            encoded = json.dumps(
                dict(value),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            decoded = json.loads(encoded)
        except (TypeError, ValueError) as exc:
            raise RuleManagementError(
                "Protected configuration parameters must contain plain JSON values."
            ) from exc
        return dict(decoded)

    @staticmethod
    def _request_definition(value: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: value[key]
            for key in (
                "rule_id",
                "version",
                "name",
                "purpose",
                "severity",
                "evaluator_key",
                "parameters",
                "required_fields",
                "grouping_keys",
                "content_hash",
            )
        }

    @staticmethod
    def _is_later_version(candidate: str, predecessor: str) -> bool:
        def parse(value: str) -> tuple[int, int, int] | None:
            parts = value.split(".")
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                return None
            return tuple(int(part) for part in parts)  # type: ignore[return-value]

        candidate_value = parse(candidate)
        predecessor_value = parse(predecessor)
        return (
            candidate_value is not None
            and predecessor_value is not None
            and candidate_value > predecessor_value
        )

    @staticmethod
    def _next_version(version: str) -> str:
        parts = version.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise RuleManagementError("The current Rule Version is invalid.")
        return f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"

    @staticmethod
    def _domain_definition(
        value: Mapping[str, Any], *, ordinal: int
    ) -> RuleDefinitionVersion:
        return RuleDefinitionVersion(
            rule_id=str(value["rule_id"]),
            name=str(value["name"]),
            version=str(value["version"]),
            severity=str(value["severity"]),
            baseline_status=str(value["baseline_status"]),
            evaluator_key=str(value["evaluator_key"]),
            ordinal=ordinal,
            classification=str(value["classification"]),
            purpose=str(value["purpose"]),
            required_fields=tuple(value["required_fields"]),
            grouping_keys=tuple(value["grouping_keys"]),
            parameters=dict(value["parameters"]),
        )
