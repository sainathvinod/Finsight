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
        started_at: str | None = None,
    ):
        review = self._require_review(review_id)
        basis = self._repo.generation_basis(review_id)
        if basis is None or basis["dataset_fingerprint"] != dataset.fingerprint:
            raise FinancialReviewError("The validation dataset does not match the confirmed review.")
        if evaluation.dataset_fingerprint != dataset.fingerprint:
            raise FinancialReviewError("The rule results do not match the confirmed review.")
        current_rule_set = self._repo.current_rule_set_id(review_id)
        if not current_rule_set or evaluation.rule_set_id != current_rule_set:
            raise FinancialReviewError(
                "The evaluated Rule Set Version is no longer current."
            )
        latest = self._repo.latest_run(review_id)
        is_reanalysis = latest is not None
        if not is_reanalysis and review.status is not ReviewStatus.DATA_REVIEWED:
            raise FinancialReviewError(
                "Reviewed data must be confirmed before validation."
            )
        if is_reanalysis:
            if latest["rule_set_id"] == evaluation.rule_set_id:
                raise FinancialReviewError(
                    "Revalidation requires a successor Rule Set Version."
                )
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
        run_id = "run_" + self._id()
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
                revalidation_reason=(
                    "RULESET_REANALYSIS"
                    if is_reanalysis
                    else "INITIAL_VALIDATION"
                ),
            )
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
            if is_reanalysis:
                self._uow.dal.conn.execute(
                    "INSERT INTO generation_supersessions("
                    "prior_generation_id,successor_generation_id,superseded_at,actor,reason"
                    ") VALUES(?,?,?,?,?)",
                    (
                        latest["generation_id"],
                        generation_id,
                        timestamp,
                        self._actor.actor_id,
                        "RULESET_REANALYSIS",
                    ),
                )
            self._cycle_lifecycle.set_published_generation(review_id, generation_id)
            self._uow.dal.conn.execute(
                "UPDATE cycles SET state='Summarized' WHERE cycle_id=?", (review_id,)
            )
            self._uow.dal.conn.execute(
                "UPDATE v2_review_cycle_pointers SET published_generation_id=?,"
                "current_rule_set_id=?,revision=revision+1 WHERE review_id=?",
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
            self._audit.append(
                review_id=review_id,
                event_type="deterministic_validation_completed",
                actor=self._actor,
                occurred_at=timestamp,
                correlation_id="corr_" + self._id(),
                payload={
                    "run_id": run_id,
                    "generation_id": generation_id,
                    "rule_set_id": evaluation.rule_set_id,
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
        return self._repo.run_projection(review_id)

    def results(self, review_id: str):
        self._require_review(review_id)
        return self._repo.run_projection(review_id)

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
