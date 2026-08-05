"""Application service for the integrated V2 reviewed-data and validation flow."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Mapping

from finsight.domain.finding_explanations import (
    FindingReviewStatus,
    build_finding_explanations,
    build_leadership_summary,
)
from finsight.domain.financial_validation import (
    WorkingFinancialDataset,
    dataset_from_inspections,
)
from finsight.domain.identity import Permission
from finsight.domain.lifecycle import (
    AnalyticalState,
    CreationReason,
    ReviewGeneration,
)
from finsight.domain.review_management import (
    ReviewStatus,
    ReviewStatusEvent,
    StatusOwnerKind,
)
from finsight.domain.source_intake import SourceRole
from finsight.infrastructure.audit_stream import AuditScope


class FinancialReviewError(RuntimeError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


class FinancialReviewService:
    """Coordinates review-local edits and sealed deterministic results.

    The pure engine owns every pass/fail decision. This service owns lifecycle,
    attributable audit, and all-or-nothing persistence.
    """

    def __init__(
        self,
        *,
        repository,
        review_repository,
        source_repository,
        generation_repository,
        cycle_lifecycle_repository,
        audit_stream,
        unit_of_work,
        extractor,
        engine,
        actor,
        clock,
        authorizer=None,
        id_factory=None,
    ):
        self._repo = repository
        self._reviews = review_repository
        self._sources = source_repository
        self._generations = generation_repository
        self._cycle_lifecycle = cycle_lifecycle_repository
        self._audit = audit_stream
        self._uow = unit_of_work
        self._extractor = extractor
        self._engine = engine
        self._actor = actor
        self._clock = clock
        self._authorizer = authorizer
        self._id = id_factory or (lambda: uuid.uuid4().hex)

    def reconstruction_inputs(self, review_id: str) -> dict[str, Any]:
        review = self._require_review(review_id)
        summary = self._sources.get_summary(review_id)
        sources = self._sources.get_current_pair(review_id)
        if summary is None or set(sources) != {"BUDGET", "GED"}:
            raise FinancialReviewError("Both saved source reports are required.")
        return {
            "review": review,
            "summary": summary,
            "sources": sources,
            "corrections": self._repo.current_corrections(review_id),
        }

    def timestamp(self) -> str:
        """Return the injected application clock value for a validation attempt."""
        return self._clock.now()

    def inspect_reconstruction_sources(self, inputs: Mapping[str, Any]):
        """Read-only work intended for a worker thread (no SQLite access)."""

        budget_ref = inputs["sources"]["BUDGET"]
        ged_ref = inputs["sources"]["GED"]
        budget = self._extractor.inspect(budget_ref["path_hint"], SourceRole.BUDGET)
        ged = self._extractor.inspect(ged_ref["path_hint"], SourceRole.GED)
        for inspection, reference in ((budget, budget_ref), (ged, ged_ref)):
            if not inspection.is_compatible:
                raise FinancialReviewError(
                    f"{inspection.role.label} can no longer be read under the approved layout."
                )
            if (
                inspection.sha256 != reference["sha256"]
                or inspection.byte_size != int(reference["byte_size"])
            ):
                raise FinancialReviewError(
                    f"{inspection.role.label} changed after it was saved. "
                    "The reviewed copy was not reconstructed."
                )
        return budget, ged

    def build_dataset(
        self,
        inputs: Mapping[str, Any],
        budget,
        ged,
    ) -> WorkingFinancialDataset:
        summary = inputs["summary"]
        return dataset_from_inspections(
            inputs["review"].review_id,
            budget,
            ged,
            department_number=summary["resolved_department_number"],
            department_name=summary["resolved_department_name"] or "Department name unavailable",
            reporting_period=inputs["review"].period.label,
            corrections=inputs["corrections"],
        )

    def reconstruct_dataset(self, review_id: str) -> WorkingFinancialDataset:
        inputs = self.reconstruction_inputs(review_id)
        budget, ged = self.inspect_reconstruction_sources(inputs)
        return self.build_dataset(inputs, budget, ged)

    def save_correction(
        self,
        review_id: str,
        dataset: WorkingFinancialDataset,
        *,
        record_id: str,
        field_name: str,
        new_value: Any,
    ) -> dict[str, Any]:
        review = self._require_review(review_id)
        if review.status is not ReviewStatus.DATA_UPLOADED or not review.candidate_id:
            raise FinancialReviewError("Only reviewed working data may be edited.")
        record = next(
            (
                item
                for item in (*dataset.budget_records, *dataset.ged_records)
                if item.record_id == record_id
            ),
            None,
        )
        if record is None or field_name not in record.current:
            raise FinancialReviewError("The selected source field is not available.")
        prior = self._repo.current_correction(review_id, record_id, field_name)
        original = record.original.get(field_name)
        prior_value = record.current.get(field_name)
        action = "REVERT" if new_value == original else "EDIT"
        timestamp = self._clock.now()
        correction_id = "corr_" + self._id()
        event = {
            "correction_id": correction_id,
            "review_id": review_id,
            "candidate_id": review.candidate_id,
            "record_id": record_id,
            "source_role": record.source_role,
            "worksheet_name": record.worksheet,
            "source_row": record.row_number,
            "field_name": field_name,
            "source_cell": record.cells[field_name],
            "original_value": original,
            "prior_value": prior_value,
            "new_value": new_value,
            "action": action,
            "actor_id": self._actor.actor_id,
            "occurred_at": timestamp,
            "predecessor_correction_id": prior["correction_id"] if prior else None,
        }
        event["event_hash"] = _digest(event)
        with self._uow.atomic():
            self._repo.append_correction(event)
            self._audit.append(
                review_id=review_id,
                event_type="review_data_corrected",
                actor=self._actor,
                occurred_at=timestamp,
                correlation_id="corr_" + self._id(),
                payload={
                    "record_id": record_id,
                    "field_name": field_name,
                    "source_cell": record.cells[field_name],
                    "original_value": original,
                    "prior_value": prior_value,
                    "new_value": new_value,
                    "action": action,
                },
                scopes=(
                    AuditScope("Review", review_id),
                    AuditScope("WorkingCandidate", review.candidate_id),
                    AuditScope("SourceCell", f"{record.worksheet}!{record.cells[field_name]}"),
                ),
            )
        event["current_correction_count"] = len(
            self._repo.current_corrections(review_id)
        )
        return event

    def correction_history(self, review_id: str) -> list[dict[str, Any]]:
        self._require_review(review_id)
        return self._repo.correction_history(review_id)

    def confirm_reviewed_data(
        self,
        review_id: str,
        dataset: WorkingFinancialDataset,
        *,
        attestation_text: str,
    ):
        review = self._require_review(review_id)
        if review.status is not ReviewStatus.DATA_UPLOADED or not review.candidate_id:
            raise FinancialReviewError("Data must be uploaded before it can be confirmed.")
        inputs = self.reconstruction_inputs(review_id)
        current_corrections = inputs["corrections"]
        if len(current_corrections) != dataset.correction_count:
            raise FinancialReviewError("Saved edits changed; reload the reviewed data before confirming.")
        sequence = self._generations.next_sequence_number(review_id)
        generation_id = f"{review_id}-gen-{sequence}"
        timestamp = self._clock.now()
        confirmation_id = "confirm_" + self._id()
        summary = inputs["summary"]
        generation = ReviewGeneration(
            generation_id=generation_id,
            cycle_id=review_id,
            sequence_number=sequence,
            analytical_state=AnalyticalState.VERIFIED,
            creation_reason=CreationReason.INITIAL_VERIFICATION,
            based_on_generation_id=None,
            verification_basis_generation_id=None,
            verified_fingerprint=dataset.fingerprint,
            extractor_version=summary["extraction_profile_version"],
            verification_actor=self._actor.actor_id,
            verified_at=timestamp,
            created_by=self._actor.actor_id,
            created_at=timestamp,
        )
        confirmation = {
            "confirmation_id": confirmation_id,
            "review_id": review_id,
            "candidate_id": review.candidate_id,
            "generation_id": generation_id,
            "dataset_fingerprint": dataset.fingerprint,
            "budget_sha256": dataset.budget_fingerprint,
            "ged_sha256": dataset.ged_fingerprint,
            "correction_count": dataset.correction_count,
            "attestation_text": attestation_text,
            "actor_id": self._actor.actor_id,
            "confirmed_at": timestamp,
            "department_number": dataset.department_number,
            "department_name": dataset.department_name,
            "reporting_period": dataset.reporting_period,
            "budget_filename": summary["budget_filename"],
            "ged_filename": summary["ged_filename"],
            "budget_record_count": len(dataset.budget_details),
            "ged_transaction_count": len(dataset.ged_transactions),
            "extractor_profile_version": summary["extraction_profile_version"],
        }
        with self._uow.atomic():
            self._generations.insert(generation)
            self._cycle_lifecycle.set_working_generation(review_id, generation_id)
            self._repo.append_confirmation(confirmation)
            self._reviews.append_status(
                ReviewStatusEvent(
                    event_id="status_" + self._id(),
                    review_id=review_id,
                    owner_kind=StatusOwnerKind.GENERATION,
                    owner_id=generation_id,
                    sequence=1,
                    previous_status=ReviewStatus.DATA_UPLOADED,
                    status=ReviewStatus.DATA_REVIEWED,
                    actor_id=self._actor.actor_id,
                    occurred_at=timestamp,
                    reason="REVIEWED_DATA_CONFIRMED",
                )
            )
            rule_set_id = self._repo.ensure_initial_rule_set(
                review_id,
                actor_id=self._actor.actor_id,
                created_at=timestamp,
            )
            self._uow.dal.conn.execute(
                "UPDATE v2_review_cycle_pointers SET active_candidate_id=NULL,"
                "working_generation_id=?,current_rule_set_id=?,revision=revision+1 "
                "WHERE review_id=?",
                (generation_id, rule_set_id, review_id),
            )
            self._uow.dal.conn.execute(
                "UPDATE cycles SET state='Verified' WHERE cycle_id=?", (review_id,)
            )
            self._uow.dal.conn.execute(
                "INSERT INTO v2_generation_analytical_state_events("
                "event_id,generation_id,review_id,ordinal,origin,prior_state,new_state,"
                "trigger_type,trigger_id,actor_id,occurred_at,event_hash"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "state_" + self._id(), generation_id, review_id, 1, "NATIVE",
                    None, "VERIFIED", "DATA_CONFIRMATION", confirmation_id,
                    self._actor.actor_id, timestamp,
                    _digest([generation_id, "VERIFIED", confirmation_id]),
                ),
            )
            self._audit.append(
                review_id=review_id,
                event_type="reviewed_data_confirmed",
                actor=self._actor,
                occurred_at=timestamp,
                correlation_id="corr_" + self._id(),
                payload={
                    "confirmation_id": confirmation_id,
                    "generation_id": generation_id,
                    "dataset_fingerprint": dataset.fingerprint,
                    "correction_count": dataset.correction_count,
                    "budget_record_count": len(dataset.budget_details),
                    "ged_transaction_count": len(dataset.ged_transactions),
                },
                scopes=(
                    AuditScope("Review", review_id),
                    AuditScope("ReviewGeneration", generation_id),
                ),
            )
        return self._require_review(review_id)

    def evaluate(self, dataset: WorkingFinancialDataset):
        return self._engine.evaluate(dataset, self.rule_manifest(dataset.review_id))

    def record_revalidation_entry(self, review_id: str) -> dict[str, Any]:
        """Audit direct entry from retained results into Rules/Revalidate."""

        self._require_review(review_id)
        latest = self._repo.latest_run(review_id)
        basis = self._repo.generation_basis(review_id)
        if latest is None or basis is None:
            raise FinancialReviewError(
                "A retained Validation Run and verified working data are required."
            )
        timestamp = self._clock.now()
        payload = {
            "prior_run_id": latest["run_id"],
            "prior_rule_set_id": latest["rule_set_id"],
            "source_generation_id": basis["generation_id"],
            "dataset_fingerprint": basis["dataset_fingerprint"],
            "reason": "REVIEW_RULES_AND_REVALIDATE_SELECTED",
        }
        with self._uow.atomic():
            self._audit.append(
                review_id=review_id,
                event_type="revalidation_entered",
                actor=self._actor,
                occurred_at=timestamp,
                correlation_id="corr_" + self._id(),
                payload=payload,
                scopes=(
                    AuditScope("Review", review_id),
                    AuditScope("ValidationRun", latest["run_id"]),
                ),
            )
        return payload

    def validation_rule_set_proposal(
        self, review_id: str, dataset: WorkingFinancialDataset
    ) -> dict[str, Any]:
        """Build the exact review-local proposal shown before validation."""

        review = self._require_review(review_id)
        basis = self._repo.generation_basis(review_id)
        if basis is None or basis["dataset_fingerprint"] != dataset.fingerprint:
            raise FinancialReviewError(
                "Data reverification required. The working data no longer "
                "matches the verified Budget and GED data."
            )
        if review.status not in {
            ReviewStatus.DATA_REVIEWED,
            ReviewStatus.VALIDATION_COMPLETE,
            ReviewStatus.REVIEWED,
            ReviewStatus.CLOSED,
        }:
            raise FinancialReviewError(
                "Reviewed data must be confirmed before a Rule Set can be confirmed."
            )
        rule_set_id = self._repo.current_rule_set_id(review_id)
        if not rule_set_id:
            raise FinancialReviewError(
                "No governed Rule Set Version is assigned to this review."
            )
        history = self._repo.rule_set_history(review_id)
        rule_set = next(
            (
                item
                for item in history
                if item["rule_set_id"] == rule_set_id
            ),
            None,
        )
        if rule_set is None:
            raise FinancialReviewError(
                "The proposed Rule Set Version cannot be inspected."
            )
        rules: list[dict[str, Any]] = []
        for member in self._repo.rule_set_members(rule_set_id):
            definition = self._repo.rule_version(
                member["rule_id"], member["rule_version"]
            )
            if definition is None:
                raise FinancialReviewError(
                    "A required Rule Version is missing from the proposed Rule Set."
                )
            lifecycle = str(definition.get("lifecycle_status") or "ACTIVE")
            # The immutable Rule Set member is authoritative for this review.
            # A later global retirement/supersession must not silently remove a
            # version that remains pinned to an existing workspace; doing so
            # would break historical replay and protected-baseline continuity.
            included = bool(member["enabled"])
            status = (
                "Active"
                if included
                else ("Retired" if lifecycle == "RETIRED" else "Disabled")
            )
            rules.append(
                {
                    "ordinal": int(member["ordinal"]),
                    "rule_id": str(definition["rule_id"]),
                    "rule_version": str(definition["version"]),
                    "name": str(definition["name"]),
                    "baseline_status": str(definition["baseline_status"]),
                    "status": status,
                    "included": included,
                    "severity": str(definition["severity"]),
                    "evaluator_key": str(definition["evaluator_key"]),
                    "parameters": dict(definition.get("parameters") or {}),
                    "required_fields": list(
                        definition.get("required_fields") or ()
                    ),
                    "grouping_keys": list(
                        definition.get("grouping_keys") or ()
                    ),
                    "content_hash": str(definition.get("content_hash") or ""),
                }
            )
        bound_versions = {
            (item["rule_id"], item["rule_version"])
            for item in rules
        }
        exclusions = {
            (str(item["rule_id"]), str(item["rule_version"])): item
            for item in self._repo.current_rule_proposal_draft_exclusions(
                review_id
            )
        }
        draft_candidates = []
        for definition in self._repo.latest_optional_rule_versions():
            identity = (
                str(definition["rule_id"]),
                str(definition["version"]),
            )
            if (
                identity in bound_versions
                or definition.get("lifecycle_status")
                not in {"DRAFT", "TESTED"}
            ):
                continue
            draft_candidates.append(
                {
                    "rule_id": identity[0],
                    "rule_version": identity[1],
                    "name": str(definition["name"]),
                    "status": str(definition["lifecycle_status"]).title(),
                    "excluded": identity in exclusions,
                }
            )
        unresolved = [
            item for item in draft_candidates if not item["excluded"]
        ]
        included_rules = [item for item in rules if item["included"]]
        protected_ids = {
            item["rule_id"]
            for item in included_rules
            if item["baseline_status"] == "PROTECTED_BASELINE"
        }
        expected_protected = {
            "CORE-01",
            "CORE-02",
            "CORE-03",
            "CORE-04",
            "CORE-05",
        }
        readiness_reasons = []
        if protected_ids != expected_protected:
            readiness_reasons.append(
                "All five protected core rules must be active."
            )
        if unresolved:
            names = ", ".join(item["name"] for item in unresolved)
            readiness_reasons.append(
                f"{len(unresolved)} draft rule(s) are unresolved: {names}. "
                "Test and activate each rule, or exclude it from the proposed Rule Set."
            )
        latest = self._repo.latest_run(review_id)
        prior_rules: dict[str, dict[str, Any]] = {}
        if latest is not None:
            prior_projection = self._repo.run_projection(
                review_id, latest["run_id"]
            )
            if prior_projection is not None:
                prior_rules = {
                    str(item["rule_id"]): item
                    for item in prior_projection["executions"]
                }
        current_by_id = {
            item["rule_id"]: item for item in included_rules
        }
        changes: list[dict[str, Any]] = []
        for rule_id in sorted(set(current_by_id) - set(prior_rules)):
            item = current_by_id[rule_id]
            changes.append(
                {
                    "kind": "ADDED",
                    "rule_id": rule_id,
                    "label": f"+ {item['name']} v{item['rule_version']} activated",
                }
            )
        for rule_id in sorted(set(prior_rules) - set(current_by_id)):
            item = prior_rules[rule_id]
            changes.append(
                {
                    "kind": "REMOVED",
                    "rule_id": rule_id,
                    "label": f"− {item['rule_name']} v{item['version']} disabled or retired",
                }
            )
        for rule_id in sorted(set(prior_rules) & set(current_by_id)):
            before = prior_rules[rule_id]
            after = current_by_id[rule_id]
            if str(before["version"]) != after["rule_version"]:
                changes.append(
                    {
                        "kind": "VERSION_CHANGED",
                        "rule_id": rule_id,
                        "label": (
                            f"~ {after['name']} v{before['version']} → "
                            f"v{after['rule_version']}"
                        ),
                    }
                )
        same_rule_set = bool(
            latest is not None and latest["rule_set_id"] == rule_set_id
        )
        proposal = {
            "review_id": review_id,
            "reporting_period": dataset.reporting_period,
            "department_number": dataset.department_number,
            "department_name": dataset.department_name,
            "working_data_label": (
                f"{dataset.reporting_period} verified Budget and GED data"
            ),
            "budget_filename": basis["budget_filename"],
            "ged_filename": basis["ged_filename"],
            "budget_record_count": int(basis["budget_record_count"]),
            "ged_transaction_count": int(basis["ged_transaction_count"]),
            "dataset_fingerprint": dataset.fingerprint,
            "source_generation_id": basis["generation_id"],
            "source_data_version": (
                f"{basis['generation_id']}:{dataset.fingerprint}"
            ),
            "rule_set_id": rule_set_id,
            "rule_set_version": str(rule_set["version"]),
            "rules": rules,
            "included_rules": included_rules,
            "excluded_drafts": [
                item for item in draft_candidates if item["excluded"]
            ],
            "draft_candidates": draft_candidates,
            "unresolved_drafts": unresolved,
            "counts": {
                "protected_core": sum(
                    item["baseline_status"] == "PROTECTED_BASELINE"
                    for item in included_rules
                ),
                "enabled_optional": sum(
                    item["baseline_status"] != "PROTECTED_BASELINE"
                    for item in included_rules
                ),
                "draft": len(unresolved),
                "disabled_included": 0,
                "disabled_available": sum(
                    not item["included"] for item in rules
                ),
            },
            "changes": changes,
            "prior_run_id": latest["run_id"] if latest else None,
            "prior_rule_set_id": latest["rule_set_id"] if latest else None,
            "same_rule_set_rerun": same_rule_set,
            "ready": not readiness_reasons,
            "readiness_reasons": readiness_reasons,
        }
        proposal["proposal_hash"] = _digest(proposal)
        return proposal

    def confirm_validation_rule_set(
        self,
        review_id: str,
        dataset: WorkingFinancialDataset,
        *,
        proposal_hash: str,
    ) -> dict[str, Any]:
        """Seal the exact proposed rules and reviewed data before execution."""

        proposal = self.validation_rule_set_proposal(review_id, dataset)
        if not proposal["ready"]:
            raise FinancialReviewError(" ".join(proposal["readiness_reasons"]))
        if proposal["proposal_hash"] != proposal_hash:
            raise FinancialReviewError(
                "The proposed Rule Set changed before confirmation. Review it again."
            )
        timestamp = self._clock.now()
        confirmation = {
            "confirmation_id": "ruleconfirm_" + self._id(),
            "run_id": "run_" + self._id(),
            "review_id": review_id,
            "rule_set_id": proposal["rule_set_id"],
            "rule_set_version": proposal["rule_set_version"],
            "dataset_fingerprint": proposal["dataset_fingerprint"],
            "source_generation_id": proposal["source_generation_id"],
            "source_data_version": proposal["source_data_version"],
            "prior_run_id": proposal["prior_run_id"],
            "rules": proposal["rules"],
            "excluded_drafts": proposal["excluded_drafts"],
            "changes": proposal["changes"],
            "actor_id": self._actor.actor_id,
            "confirmed_at": timestamp,
            "proposal_hash": proposal_hash,
        }
        confirmation["confirmation_hash"] = _digest(confirmation)
        event = self._validation_attempt_event(
            confirmation["confirmation_id"],
            "CONFIRMED",
            timestamp=timestamp,
            reason="RULE_SET_AND_WORKING_DATA_CONFIRMED",
            payload={
                "rule_set_id": proposal["rule_set_id"],
                "rule_set_version": proposal["rule_set_version"],
                "proposal_hash": proposal_hash,
                "dataset_fingerprint": proposal["dataset_fingerprint"],
                "source_generation_id": proposal["source_generation_id"],
                "prior_run_id": proposal["prior_run_id"],
                "same_rule_set_rerun": proposal["same_rule_set_rerun"],
                "included_rule_ids_and_versions": [
                    {
                        "rule_id": item["rule_id"],
                        "rule_version": item["rule_version"],
                    }
                    for item in proposal["included_rules"]
                ],
                "excluded_drafts": proposal["excluded_drafts"],
            },
            ordinal=1,
            run_id=confirmation["run_id"],
        )
        with self._uow.atomic():
            self._repo.append_validation_rule_set_confirmation(confirmation)
            self._repo.append_validation_attempt_event(event)
            self._audit.append(
                review_id=review_id,
                event_type="validation_rule_set_confirmed",
                actor=self._actor,
                occurred_at=timestamp,
                correlation_id="corr_" + self._id(),
                payload={
                    "confirmation_id": confirmation["confirmation_id"],
                    "run_id": confirmation["run_id"],
                    "confirmation_hash": confirmation["confirmation_hash"],
                    **event["payload"],
                },
                scopes=(
                    AuditScope("Review", review_id),
                    AuditScope("RuleSet", proposal["rule_set_id"]),
                ),
            )
        return self._repo.validation_rule_set_confirmation(
            confirmation["confirmation_id"]
        )

    def start_validation_attempt(
        self,
        confirmation_id: str,
        dataset: WorkingFinancialDataset,
    ):
        """Re-verify and start one confirmed deterministic validation attempt."""

        confirmation = self._require_validation_confirmation(
            confirmation_id, dataset
        )
        events = confirmation["events"]
        if not events or events[-1]["event_type"] != "CONFIRMED":
            raise FinancialReviewError(
                "This Rule Set confirmation has already been used. Confirm again."
            )
        manifest = self._repo.rule_set_manifest(confirmation["rule_set_id"])
        if manifest is None:
            raise FinancialReviewError(
                "The confirmed Rule Set Version is no longer available."
            )
        timestamp = self._clock.now()
        event = self._validation_attempt_event(
            confirmation_id,
            "STARTED",
            timestamp=timestamp,
            reason="DETERMINISTIC_VALIDATION_STARTED",
            payload={
                "rule_set_id": confirmation["rule_set_id"],
                "dataset_fingerprint": dataset.fingerprint,
                "prior_run_id": confirmation["prior_run_id"],
            },
            ordinal=2,
            run_id=confirmation["run_id"],
        )
        with self._uow.atomic():
            self._repo.append_validation_attempt_event(event)
            self._audit.append(
                review_id=confirmation["review_id"],
                event_type="deterministic_validation_started",
                actor=self._actor,
                occurred_at=timestamp,
                correlation_id="corr_" + self._id(),
                payload={
                    "confirmation_id": confirmation_id,
                    "run_id": confirmation["run_id"],
                    **event["payload"],
                },
                scopes=(
                    AuditScope("Review", confirmation["review_id"]),
                    AuditScope("RuleSet", confirmation["rule_set_id"]),
                ),
            )
        return manifest

    def record_validation_failure(
        self, confirmation_id: str, error: BaseException
    ) -> None:
        confirmation = self._repo.validation_rule_set_confirmation(
            confirmation_id
        )
        if confirmation is None:
            return
        events = confirmation["events"]
        if not events or events[-1]["event_type"] in {"COMPLETED", "FAILED"}:
            return
        timestamp = self._clock.now()
        correlation_id = "corr_" + self._id()
        event = self._validation_attempt_event(
            confirmation_id,
            "FAILED",
            timestamp=timestamp,
            reason="DETERMINISTIC_VALIDATION_FAILED",
            payload={
                "prior_run_id": confirmation["prior_run_id"],
                "rule_set_id": confirmation["rule_set_id"],
                "failure_type": type(error).__name__,
                "correlation_id": correlation_id,
            },
            ordinal=self._repo.next_validation_attempt_ordinal(
                confirmation_id
            ),
            run_id=confirmation["run_id"],
        )
        with self._uow.atomic():
            self._repo.append_validation_attempt_event(event)
            self._audit.append(
                review_id=confirmation["review_id"],
                event_type="deterministic_validation_failed",
                actor=self._actor,
                occurred_at=timestamp,
                correlation_id=correlation_id,
                outcome="FAILED",
                payload={
                    "confirmation_id": confirmation_id,
                    "run_id": confirmation["run_id"],
                    **event["payload"],
                },
                scopes=(
                    AuditScope("Review", confirmation["review_id"]),
                    AuditScope("RuleSet", confirmation["rule_set_id"]),
                ),
            )

    def _require_validation_confirmation(
        self,
        confirmation_id: str,
        dataset: WorkingFinancialDataset,
    ) -> dict[str, Any]:
        confirmation = self._repo.validation_rule_set_confirmation(
            confirmation_id
        )
        if confirmation is None:
            raise FinancialReviewError(
                "Confirm the proposed Rule Set before validation."
            )
        if confirmation["review_id"] != dataset.review_id:
            raise FinancialReviewError(
                "The Rule Set confirmation belongs to another review."
            )
        if confirmation["actor_id"] != self._actor.actor_id:
            raise FinancialReviewError(
                "The confirmation actor does not match the validation actor."
            )
        basis = self._repo.generation_basis(dataset.review_id)
        latest = self._repo.latest_run(dataset.review_id)
        current_rule_set = self._repo.current_rule_set_id(dataset.review_id)
        if (
            basis is None
            or basis["dataset_fingerprint"] != dataset.fingerprint
            or confirmation["dataset_fingerprint"] != dataset.fingerprint
            or confirmation["source_generation_id"] != basis["generation_id"]
        ):
            raise FinancialReviewError(
                "Data reverification required. The verified working data changed."
            )
        if current_rule_set != confirmation["rule_set_id"]:
            raise FinancialReviewError(
                "The Rule Set changed after confirmation. Review and confirm it again."
            )
        latest_run_id = latest["run_id"] if latest else None
        if latest_run_id != confirmation["prior_run_id"]:
            raise FinancialReviewError(
                "A newer Validation Run exists. Review and confirm the Rule Set again."
            )
        current = self.validation_rule_set_proposal(
            dataset.review_id, dataset
        )
        if not current["ready"]:
            raise FinancialReviewError(
                "The confirmed proposal is no longer ready. "
                + " ".join(current["readiness_reasons"])
            )
        if _digest(current["rules"]) != _digest(confirmation["rules"]):
            raise FinancialReviewError(
                "The confirmed Rule Versions or configuration changed."
            )
        if _digest(current["excluded_drafts"]) != _digest(
            confirmation["excluded_drafts"]
        ):
            raise FinancialReviewError(
                "The confirmed draft-rule exclusions changed. Review and "
                "confirm the proposed Rule Set again."
            )
        return confirmation

    def _validation_attempt_event(
        self,
        confirmation_id: str,
        event_type: str,
        *,
        timestamp: str,
        reason: str,
        payload: Mapping[str, Any],
        ordinal: int,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        event = {
            "event_id": "validationevt_" + self._id(),
            "confirmation_id": confirmation_id,
            "ordinal": ordinal,
            "event_type": event_type,
            "run_id": run_id,
            "actor_id": self._actor.actor_id,
            "occurred_at": timestamp,
            "reason": reason,
            "payload": dict(payload),
        }
        event["event_hash"] = _digest(event)
        return event

    def rule_manifest(self, review_id: str):
        self._require_review(review_id)
        rule_set_id = self._repo.current_rule_set_id(review_id)
        if not rule_set_id:
            raise FinancialReviewError(
                "No governed Rule Set Version is assigned to this review."
            )
        manifest = self._repo.rule_set_manifest(rule_set_id)
        if manifest is None:
            raise FinancialReviewError(
                "The assigned Rule Set Version cannot be loaded."
            )
        return manifest

    def evaluate_manifest(self, dataset: WorkingFinancialDataset, manifest):
        """Pure engine entry point for a manifest loaded before worker dispatch."""

        return self._engine.evaluate(dataset, manifest)

    def persist_evaluation(
        self,
        review_id: str,
        dataset: WorkingFinancialDataset,
        evaluation,
        *,
        confirmation_id: str,
        started_at: str | None = None,
    ):
        review = self._require_review(review_id)
        confirmation = self._repo.validation_rule_set_confirmation(
            confirmation_id
        )
        if confirmation is None:
            raise FinancialReviewError(
                "Confirm the proposed Rule Set before validation."
            )
        if confirmation["review_id"] != review_id:
            raise FinancialReviewError(
                "The Rule Set confirmation belongs to another review."
            )
        if (
            not confirmation["events"]
            or confirmation["events"][-1]["event_type"] != "STARTED"
        ):
            raise FinancialReviewError(
                "The confirmed validation attempt was not started or is no longer active."
            )
        basis = self._repo.generation_basis(review_id)
        if basis is None or basis["dataset_fingerprint"] != dataset.fingerprint:
            raise FinancialReviewError("The validation dataset does not match the confirmed review.")
        if evaluation.dataset_fingerprint != dataset.fingerprint:
            raise FinancialReviewError("The rule results do not match the confirmed review.")
        current_rule_set = self._repo.current_rule_set_id(review_id)
        if (
            not current_rule_set
            or evaluation.rule_set_id != current_rule_set
            or evaluation.rule_set_id != confirmation["rule_set_id"]
        ):
            raise FinancialReviewError(
                "The evaluated Rule Set Version is no longer current."
            )
        latest = self._repo.latest_run(review_id)
        is_reanalysis = latest is not None
        latest_run_id = latest["run_id"] if latest else None
        if latest_run_id != confirmation["prior_run_id"]:
            raise FinancialReviewError(
                "A newer Validation Run exists. Review and confirm the Rule Set again."
            )
        if not is_reanalysis and review.status is not ReviewStatus.DATA_REVIEWED:
            raise FinancialReviewError(
                "Reviewed data must be confirmed before validation."
            )
        if is_reanalysis:
            if review.status not in {
                ReviewStatus.VALIDATION_COMPLETE,
                ReviewStatus.REVIEWED,
                ReviewStatus.CLOSED,
            }:
                raise FinancialReviewError(
                    "The retained Validation Run is not ready for rule-set reanalysis."
                )
        timestamp = self._clock.now()
        started = started_at or timestamp
        run_id = confirmation["run_id"]
        generation_id = basis["generation_id"]
        reanalysis_generation = None
        if is_reanalysis:
            generation_id = (
                f"{review_id}-gen-{self._generations.next_sequence_number(review_id)}"
            )
            reanalysis_generation = ReviewGeneration(
                generation_id=generation_id,
                cycle_id=review_id,
                sequence_number=self._generations.next_sequence_number(review_id),
                analytical_state=AnalyticalState.VERIFIED,
                creation_reason=CreationReason.RULESET_REANALYSIS,
                based_on_generation_id=latest["generation_id"],
                verification_basis_generation_id=basis["generation_id"],
                verified_fingerprint=basis["dataset_fingerprint"],
                extractor_version=basis["extractor_profile_version"],
                verification_actor=None,
                verified_at=None,
                created_by=self._actor.actor_id,
                created_at=timestamp,
            )
        manifest = self._repo.rule_set_manifest(evaluation.rule_set_id)
        if manifest is None:
            raise FinancialReviewError(
                "The evaluated Rule Set Version is no longer available."
            )
        source_files = {
            "BUDGET": {
                "file_name": basis["budget_filename"],
                "sha256": basis["budget_sha256"],
            },
            "GED": {
                "file_name": basis["ged_filename"],
                "sha256": basis["ged_sha256"],
            },
        }
        explanations = build_finding_explanations(
            dataset,
            evaluation,
            manifest,
            run_id=run_id,
            generation_id=generation_id,
            actor_id=self._actor.actor_id,
            recorded_at=timestamp,
            source_files=source_files,
        )
        explanation_by_finding = {
            item["finding_id"]: item for item in explanations
        }
        leadership_findings = []
        for finding in evaluation.findings:
            finding_id = f"{run_id}_{finding.finding_id}"
            explanation = explanation_by_finding[finding_id]
            leadership_findings.append(
                {
                    "finding_id": finding_id,
                    "severity": finding.severity,
                    "business_title": explanation["business_title"],
                    "department_number": finding.department_number,
                    "account_number": finding.account_number,
                    "review_status": FindingReviewStatus.NEW.value,
                    "review_required": True,
                    "explain_this": explanation,
                }
            )
        leadership_summary = build_leadership_summary(
            review_id=review_id,
            run_id=run_id,
            generation_id=generation_id,
            rule_set_id=manifest.rule_set_id,
            rule_set_version=manifest.version,
            completed_at=timestamp,
            metrics=evaluation.metrics,
            findings=leadership_findings,
            basis=basis,
        )
        ledger_payload = {
            "review_id": review_id,
            "generation_id": generation_id,
            "confirmation_id": confirmation_id,
            "rule_set_id": evaluation.rule_set_id,
            "dataset_fingerprint": evaluation.dataset_fingerprint,
            "executions": [item.__dict__ for item in evaluation.executions],
            "scope_results": [item.__dict__ for item in evaluation.scope_results],
            "findings": [item.__dict__ for item in evaluation.findings],
            "metrics": dict(evaluation.metrics),
            "finding_explanations": list(explanations),
            "leadership_summary": leadership_summary,
        }
        ledger_hash = _digest(ledger_payload)
        completion_seal = _digest(
            [run_id, ledger_hash, evaluation.dataset_fingerprint, timestamp]
        )
        revalidation_reason = (
            (
                "SAME_RULE_SET_RERUN"
                if latest is not None
                and latest["rule_set_id"] == evaluation.rule_set_id
                else "RULESET_REANALYSIS"
            )
            if is_reanalysis
            else "INITIAL_VALIDATION"
        )
        comparison = None
        with self._uow.atomic():
            if reanalysis_generation is not None:
                self._generations.insert(reanalysis_generation)
                self._cycle_lifecycle.set_working_generation(
                    review_id, generation_id
                )
                self._repo.append_reanalysis_basis(
                    {
                        "generation_id": generation_id,
                        "review_id": review_id,
                        "source_generation_id": basis["generation_id"],
                        "dataset_fingerprint": basis["dataset_fingerprint"],
                        "rule_set_id": evaluation.rule_set_id,
                        "created_by": self._actor.actor_id,
                        "created_at": timestamp,
                    }
                )
                self._uow.dal.conn.execute(
                    "UPDATE v2_review_cycle_pointers SET working_generation_id=?,"
                    "revision=revision+1 WHERE review_id=?",
                    (generation_id, review_id),
                )
                self._uow.dal.conn.execute(
                    "INSERT INTO v2_generation_analytical_state_events("
                    "event_id,generation_id,review_id,ordinal,origin,prior_state,new_state,"
                    "trigger_type,trigger_id,actor_id,occurred_at,event_hash"
                    ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        "state_" + self._id(),
                        generation_id,
                        review_id,
                        1,
                        "NATIVE",
                        None,
                        "VERIFIED",
                        "RULESET_REANALYSIS",
                        evaluation.rule_set_id,
                        self._actor.actor_id,
                        timestamp,
                        _digest([generation_id, "VERIFIED", evaluation.rule_set_id]),
                    ),
                )
                self._uow.dal.conn.execute(
                    "INSERT INTO v2_review_status_events("
                    "event_id,review_id,owner_kind,owner_id,sequence,previous_status,"
                    "status,actor_id,occurred_at,reason,origin) "
                    "VALUES(?,?,?,?,1,NULL,?,?,?,?,?)",
                    (
                        "status_" + self._id(),
                        review_id,
                        StatusOwnerKind.GENERATION.value,
                        generation_id,
                        ReviewStatus.DATA_REVIEWED.value,
                        self._actor.actor_id,
                        timestamp,
                        "RULESET_REANALYSIS_BASIS_INHERITED",
                        "NATIVE",
                    ),
                )
            self._repo.persist_validation(
                run_id=run_id,
                review_id=review_id,
                generation_id=generation_id,
                actor_id=self._actor.actor_id,
                started_at=started,
                completed_at=timestamp,
                ledger_hash=ledger_hash,
                completion_seal=completion_seal,
                evaluation=evaluation,
                finding_explanations=explanations,
                leadership_summary=leadership_summary,
                revalidation_reason=revalidation_reason,
            )
            link = {
                "confirmation_id": confirmation_id,
                "run_id": run_id,
                "prior_run_id": latest_run_id,
                "linked_at": timestamp,
            }
            link["link_hash"] = _digest(link)
            self._repo.append_validation_confirmation_run_link(link)
            self._generations.advance_analytical_state(
                generation_id, AnalyticalState.ANALYZED
            )
            self._uow.dal.conn.execute(
                "INSERT INTO v2_generation_analytical_state_events("
                "event_id,generation_id,review_id,ordinal,origin,prior_state,new_state,"
                "trigger_type,trigger_id,actor_id,occurred_at,event_hash"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "state_" + self._id(), generation_id, review_id, 2, "NATIVE",
                    "VERIFIED", "ANALYZED", "VALIDATION_RUN", run_id,
                    self._actor.actor_id, timestamp,
                    _digest([generation_id, "ANALYZED", run_id]),
                ),
            )
            self._generations.advance_analytical_state(
                generation_id, AnalyticalState.SUMMARIZED
            )
            self._uow.dal.conn.execute(
                "INSERT INTO v2_generation_analytical_state_events("
                "event_id,generation_id,review_id,ordinal,origin,prior_state,new_state,"
                "trigger_type,trigger_id,actor_id,occurred_at,event_hash"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "state_" + self._id(), generation_id, review_id, 3, "NATIVE",
                    "ANALYZED", "SUMMARIZED", "RESULTS_PREPARED", run_id,
                    self._actor.actor_id, timestamp,
                    _digest([generation_id, "SUMMARIZED", run_id]),
                ),
            )
            # A successor reanalysis is a reviewable Working generation. It
            # must not silently replace or supersede the prior Published
            # generation; governed promotion is a separate lifecycle action.
            publication_state = "Working" if is_reanalysis else "Published"
            if not is_reanalysis:
                self._cycle_lifecycle.set_published_generation(
                    review_id, generation_id
                )
            self._uow.dal.conn.execute(
                "UPDATE cycles SET state='Summarized' WHERE cycle_id=?", (review_id,)
            )
            if is_reanalysis:
                self._uow.dal.conn.execute(
                    "UPDATE v2_review_cycle_pointers SET current_rule_set_id=?,"
                    "revision=revision+1 WHERE review_id=?",
                    (evaluation.rule_set_id, review_id),
                )
            else:
                self._uow.dal.conn.execute(
                    "UPDATE v2_review_cycle_pointers SET "
                    "published_generation_id=?,current_rule_set_id=?,"
                    "revision=revision+1 WHERE review_id=?",
                    (generation_id, evaluation.rule_set_id, review_id),
                )
            self._reviews.append_status(
                ReviewStatusEvent(
                    event_id="status_" + self._id(),
                    review_id=review_id,
                    owner_kind=StatusOwnerKind.GENERATION,
                    owner_id=generation_id,
                    sequence=self._reviews.next_status_sequence(
                        StatusOwnerKind.GENERATION, generation_id
                    ),
                    previous_status=ReviewStatus.DATA_REVIEWED,
                    status=ReviewStatus.VALIDATION_COMPLETE,
                    actor_id=self._actor.actor_id,
                    occurred_at=timestamp,
                    reason="DETERMINISTIC_VALIDATION_COMPLETE",
                )
            )
            if latest_run_id is not None:
                comparison = self._repo.compare_runs(
                    review_id, latest_run_id, run_id
                )
            comparison_summary = {
                "findings_added": len(
                    (comparison or {}).get("findings_added", ())
                ),
                "findings_removed": len(
                    (comparison or {}).get("findings_removed", ())
                ),
                "findings_changed": len(
                    (comparison or {}).get("findings_changed", ())
                ),
                "findings_unchanged": len(
                    (comparison or {}).get("findings_unchanged", ())
                ),
                "rules_added": len(
                    (comparison or {}).get("rules_added", ())
                ),
                "rules_removed": len(
                    (comparison or {}).get("rules_removed", ())
                ),
                "rules_changed": len(
                    (comparison or {}).get("rules_changed", ())
                ),
                "rules_unchanged": len(
                    (comparison or {}).get("rules_unchanged", ())
                ),
            }
            completed_event = self._validation_attempt_event(
                confirmation_id,
                "COMPLETED",
                timestamp=timestamp,
                reason=revalidation_reason,
                run_id=run_id,
                ordinal=self._repo.next_validation_attempt_ordinal(
                    confirmation_id
                ),
                payload={
                    "prior_run_id": latest_run_id,
                    "new_run_id": run_id,
                    "rule_set_id": evaluation.rule_set_id,
                    "generation_id": generation_id,
                    "publication_state": publication_state,
                    "comparison": comparison_summary,
                },
            )
            self._repo.append_validation_attempt_event(completed_event)
            self._audit.append(
                review_id=review_id,
                event_type="deterministic_validation_completed",
                actor=self._actor,
                occurred_at=timestamp,
                correlation_id="corr_" + self._id(),
                payload={
                    "confirmation_id": confirmation_id,
                    "run_id": run_id,
                    "prior_run_id": latest_run_id,
                    "generation_id": generation_id,
                    "rule_set_id": evaluation.rule_set_id,
                    "revalidation_reason": revalidation_reason,
                    "publication_state": publication_state,
                    "dataset_fingerprint": evaluation.dataset_fingerprint,
                    "ledger_hash": ledger_hash,
                    "completion_seal": completion_seal,
                    "metrics": dict(evaluation.metrics),
                },
                scopes=(
                    AuditScope("Review", review_id),
                    AuditScope("ReviewGeneration", generation_id),
                    AuditScope("ValidationRun", run_id),
                ),
            )
            if comparison is not None:
                self._audit.append(
                    review_id=review_id,
                    event_type="validation_result_comparison_recorded",
                    actor=self._actor,
                    occurred_at=timestamp,
                    correlation_id="corr_" + self._id(),
                    payload={
                        "confirmation_id": confirmation_id,
                        "prior_run_id": latest_run_id,
                        "new_run_id": run_id,
                        "prior_rule_set_id": comparison[
                            "prior_rule_set_id"
                        ],
                        "current_rule_set_id": comparison[
                            "current_rule_set_id"
                        ],
                        "comparison": comparison_summary,
                    },
                    scopes=(
                        AuditScope("Review", review_id),
                        AuditScope("ValidationRun", latest_run_id),
                        AuditScope("ValidationRun", run_id),
                    ),
                )
        projection = self._repo.run_projection(review_id)
        if projection is not None:
            projection["comparison"] = comparison
            projection["confirmation"] = (
                self._repo.validation_rule_set_confirmation(
                    confirmation_id
                )
            )
        return projection

    def results(self, review_id: str):
        self._require_review(review_id)
        projection = self._repo.run_projection(review_id)
        if (
            projection is not None
            and projection.get("predecessor_run_id")
        ):
            projection["comparison"] = self._repo.compare_runs(
                review_id,
                projection["predecessor_run_id"],
                projection["run_id"],
            )
        return projection

    def validation_history(self, review_id: str):
        self._require_review(review_id)
        return self._repo.run_history(review_id)

    def compare_validation_runs(
        self, review_id: str, prior_run_id: str, current_run_id: str
    ):
        self._require_review(review_id)
        return self._repo.compare_runs(
            review_id, prior_run_id, current_run_id
        )

    def explain_finding(
        self, review_id: str, finding_id: str
    ) -> dict[str, Any]:
        """Return the deterministic recorded explanation for one finding."""

        self._require_review(review_id)
        location = self._repo.finding_location(review_id, finding_id)
        if location is None:
            raise FinancialReviewError(
                "The selected finding is not part of this review."
            )
        projection = self._repo.run_projection(
            review_id, location["run_id"]
        )
        if projection is None:
            raise FinancialReviewError(
                "The finding's sealed Validation Run is unavailable."
            )
        finding = next(
            (
                item
                for item in projection["findings"]
                if item["finding_id"] == finding_id
            ),
            None,
        )
        if finding is None:
            raise FinancialReviewError(
                "The selected finding is not part of this review."
            )
        return dict(finding["explain_this"])

    def finding_review_history(
        self, review_id: str, finding_id: str
    ) -> list[dict[str, Any]]:
        self._require_review(review_id)
        if self._repo.finding_location(review_id, finding_id) is None:
            raise FinancialReviewError(
                "The selected finding is not part of this review."
            )
        return self._repo.finding_review_history(review_id, finding_id)

    def update_finding_review_status(
        self,
        review_id: str,
        finding_id: str,
        status: FindingReviewStatus | str,
        *,
        reason: str,
    ) -> dict[str, Any]:
        """Append an authorized human-review state without mutating the finding."""

        self._require_review(review_id)
        try:
            target = (
                status
                if isinstance(status, FindingReviewStatus)
                else FindingReviewStatus(str(status))
            )
        except ValueError as exc:
            raise FinancialReviewError(
                "The requested finding review status is not supported."
            ) from exc
        clean_reason = str(reason).strip()
        if not clean_reason:
            raise FinancialReviewError(
                "A reason is required for a finding review-status change."
            )
        if len(clean_reason) > 500:
            raise FinancialReviewError(
                "The finding review-status reason is too long."
            )
        if self._authorizer is None:
            raise FinancialReviewError(
                "Finding review-status authorization is unavailable."
            )
        self._authorizer(Permission.REVIEW_ADVANCE)
        location = self._repo.finding_location(review_id, finding_id)
        if location is None:
            raise FinancialReviewError(
                "The selected finding is not part of this review."
            )
        run_id = location["run_id"]
        projection = self._repo.run_projection(review_id, run_id)
        if projection is None:
            raise FinancialReviewError(
                "The finding's sealed Validation Run is unavailable."
            )
        finding = next(
            (
                item
                for item in projection["findings"]
                if item["finding_id"] == finding_id
            ),
            None,
        )
        if finding is None:
            raise FinancialReviewError(
                "The selected finding is not part of this review."
            )
        current = FindingReviewStatus(
            finding.get("review_status", FindingReviewStatus.NEW.value)
        )
        if current is target:
            raise FinancialReviewError(
                f"The finding is already {target.value}."
            )
        timestamp = self._clock.now()
        review_required = target not in {
            FindingReviewStatus.RESOLVED,
            FindingReviewStatus.DISMISSED,
        }
        event = {
            "event_id": "finding_status_" + self._id(),
            "review_id": review_id,
            "run_id": run_id,
            "finding_id": finding_id,
            "ordinal": self._repo.next_finding_review_status_ordinal(
                finding_id
            ),
            "previous_status": current.value,
            "status": target.value,
            "event_kind": "REVIEW_UPDATE",
            # Only the reviewer's explicit terminal status clears follow-up.
            # This never changes the rule result or records financial approval.
            "review_required": review_required,
            "actor_id": self._actor.actor_id,
            "occurred_at": timestamp,
            "reason": clean_reason,
        }
        event["event_hash"] = _digest(event)
        with self._uow.atomic():
            self._repo.ensure_finding_explanation(
                review_id=review_id,
                run_id=run_id,
                finding_id=finding_id,
                projection=finding["explain_this"],
                actor_id=self._actor.actor_id,
                occurred_at=timestamp,
            )
            # A retained pre-0013 finding receives its initial state above.
            event["ordinal"] = self._repo.next_finding_review_status_ordinal(
                finding_id
            )
            event["event_hash"] = _digest(event)
            self._repo.append_finding_review_status(event)
            self._audit.append(
                review_id=review_id,
                event_type="finding_review_status_changed",
                actor=self._actor,
                occurred_at=timestamp,
                correlation_id="corr_" + self._id(),
                payload={
                    "finding_id": finding_id,
                    "run_id": run_id,
                    "previous_status": current.value,
                    "status": target.value,
                    "reason": clean_reason,
                    "review_required": review_required,
                    "financial_decision_recorded": False,
                },
                scopes=(
                    AuditScope("Review", review_id),
                    AuditScope("ValidationRun", run_id),
                    AuditScope("Finding", finding_id),
                ),
            )
        return self._repo.finding_review_history(
            review_id, finding_id
        )[-1]

    def leadership_summary(
        self, review_id: str, run_id: str | None = None
    ) -> dict[str, Any]:
        """Return the recorded financial summary plus current review statuses."""

        self._require_review(review_id)
        projection = self._repo.run_projection(review_id, run_id)
        if projection is None:
            raise FinancialReviewError(
                "A sealed Validation Run is required for the leadership summary."
            )
        return dict(projection["leadership_summary"])

    def complete_review(self, review_id: str, note: str = "Financial review completed."):
        review = self._require_review(review_id)
        if review.status is ReviewStatus.CLOSED:
            return review
        if review.status is not ReviewStatus.VALIDATION_COMPLETE:
            raise FinancialReviewError("Validation must be complete before closing the review.")
        run = self._repo.latest_run(review_id)
        basis = self._repo.generation_basis(review_id)
        if run is None or basis is None:
            raise FinancialReviewError("The completed validation ledger is unavailable.")
        generation_id = run["generation_id"]
        timestamp = self._clock.now()
        completion_id = "complete_" + self._id()
        seal = _digest(
            [review_id, generation_id, run["run_id"], timestamp, note]
        )
        with self._uow.atomic():
            prior = ReviewStatus.VALIDATION_COMPLETE
            for target, reason in (
                (ReviewStatus.REVIEWED, "RESULTS_REVIEWED"),
                (ReviewStatus.CLOSED, "REVIEW_COMPLETED"),
            ):
                self._reviews.append_status(
                    ReviewStatusEvent(
                        event_id="status_" + self._id(),
                        review_id=review_id,
                        owner_kind=StatusOwnerKind.GENERATION,
                        owner_id=generation_id,
                        sequence=self._reviews.next_status_sequence(
                            StatusOwnerKind.GENERATION, generation_id
                        ),
                        previous_status=prior,
                        status=target,
                        actor_id=self._actor.actor_id,
                        occurred_at=timestamp,
                        reason=reason,
                    )
                )
                prior = target
            self._repo.append_completion(
                {
                    "completion_id": completion_id,
                    "review_id": review_id,
                    "generation_id": generation_id,
                    "run_id": run["run_id"],
                    "completed_by": self._actor.actor_id,
                    "completed_at": timestamp,
                    "completion_note": note,
                    "seal_hash": seal,
                }
            )
            self._audit.append(
                review_id=review_id,
                event_type="financial_review_completed",
                actor=self._actor,
                occurred_at=timestamp,
                correlation_id="corr_" + self._id(),
                payload={
                    "completion_id": completion_id,
                    "generation_id": generation_id,
                    "run_id": run["run_id"],
                    "seal_hash": seal,
                },
                scopes=(
                    AuditScope("Review", review_id),
                    AuditScope("ValidationRun", run["run_id"]),
                ),
            )
        return self._require_review(review_id)

    def _require_review(self, review_id: str):
        review = self._reviews.get(review_id)
        if review is None:
            raise FinancialReviewError("The selected review no longer exists.")
        return review
