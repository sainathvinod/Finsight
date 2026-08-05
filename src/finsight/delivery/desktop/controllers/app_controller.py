# Implements:
#   ADRs: ADR-002 (delivery layering — UI depends only on composed services, never repositories/SQL);
#         ADR-011 §7/§9 (active-review pointer, working vs published); ADR-012 §3 (recovery);
#         ADR-013 (Ollama-independent core, AI optional)
#
# Product purpose / UI surface:
#   The desktop controller coordinating every workflow screen with the read-only query services and
#   the stateless review workflow command service. Owns the ACTIVE-REVIEW pointer + the cycle-keyed
#   ReviewWorkingSetManager, and drives off-UI-thread processing, reconstruction, and Ask Fin.
#
# Trust / lifecycle constraints:
#   - The UI never touches repositories, SQL, the rules engine, or the database; performs no financial
#     logic. Reconstruction/analysis run off the UI thread; installs are build-then-swap.
#   - Ask Fin is optional and runs off-thread; the deterministic workflow works with no AI provider.
#   - Recovery divergence is audited once per (document, fingerprint pair); no path/hash reaches AI.
from __future__ import annotations
from typing import Callable, List, Optional
from PySide6.QtCore import QObject, Signal
from finsight.application.read_models.views import (
    ReviewStatusView, FindingView, AuditEventView, SummaryView,
)
from finsight.application.workflow import UploadResult, ValidationResult, AnalysisResult, ExportResult
from finsight.application.review_working_set import ReviewWorkingSetManager
from finsight.application.reconstruction import (
    RecoveryStatus, ready_from_cache, no_source_required as _no_source)
from finsight.domain.review_cycle import has_reached, CycleState
from finsight.application.ai.ask_fin_contracts import AskFinRequest
from finsight.application.ai.private_contracts import (
    AskFinContext,
    PrivateAskFinRequest,
)
from finsight.delivery.desktop.async_worker import run_async
from finsight.diagnostics import get_logger

_log = get_logger("ui.controller")

# Single-user local desktop convention (no authentication/user-management in this application).
DEFAULT_USER_ID = "local-user"


class AppController(QObject):
    """Coordinates the UI with the read-only query services and the stateless review workflow
    command service. The controller owns the ACTIVE-REVIEW POINTER and a ReviewWorkingSetManager
    (transient working data keyed by cycle_id); switching reviews never destroys another review's
    working data (Phase 6.4a). The UI never touches repositories, SQL, the rules engine, or the
    database, and performs no financial logic."""

    activeReviewChanged = Signal(str)   # cycle_id, or "" when cleared
    reviewsChanged = Signal()           # a review was created
    workflowChanged = Signal(str)       # a transition occurred for cycle_id
    processingChanged = Signal(bool)    # processing started (True) / finished (False)
    reviewRecoveryChanged = Signal(str) # cycle_id whose recovery status changed (Phase 6.4c)
    reviewDispositionChanged = Signal(str)  # cycle_id abandoned/resumed (R1-M4, ADR-014/DEC-035)
    reviewManagementChanged = Signal()      # Workflow 1 create/list availability changed
    managedReviewOpened = Signal(str)       # explicit audited reopen or new Draft selection
    sourceIntakeChanged = Signal(str)       # Workflow 2 source pair/status changed
    financialReviewChanged = Signal(str)    # V2 reviewed data, validation, or completion changed

    def __init__(self, services, parent=None, ask_fin_backend=None):
        super().__init__(parent)
        self._s = services
        self._active: Optional[str] = None
        # Transient working data per cycle (Phase 6.4a), now with fingerprint-verified reconstruction
        # (Phase 6.4c). In-process only; NOT persisted. Reconstruction reads persisted bindings and
        # rebuilds off the UI thread; a candidate is installed (build-then-swap) only on success.
        self._working = ReviewWorkingSetManager()
        self._recovery_state: dict = {}        # cycle_id -> last RecoveryStatus value (in-session)
        self._last_recovery: dict = {}         # cycle_id -> last RecoveryResult (for the UI banner)
        self._reconstructing: set = set()      # cycles with an in-flight reconstruction (no double)
        # Presentation-only source names captured from reconstruction inputs that
        # have already passed the authorized read boundary. Keeping these in
        # memory lets Verify Data label source details without issuing another
        # repository read or authorization/audit event.
        self._financial_source_names: dict[str, dict[str, str]] = {}
        # Ask Fin backend runs the whole AskFinService pipeline OFF the UI thread on a worker-local
        # SQLite connection (injected; None disables Ask Fin). The controller never constructs a
        # provider or touches the AI stack directly.
        self._ask_fin = ask_fin_backend
        self._ask_fin_preferences = None
        if (
            self._ask_fin is not None
            and hasattr(self._ask_fin, "set_settings")
        ):
            # Endpoint/model identity are non-secret desktop preferences.
            # Environment configuration remains the higher-precedence
            # deployment seam.
            from finsight.delivery.desktop.ask_fin_preferences import (
                PrivateAskFinPreferenceStore,
            )

            self._ask_fin_preferences = PrivateAskFinPreferenceStore()
            try:
                self._ask_fin.set_settings(
                    self._ask_fin_preferences.effective_settings()
                )
            except ValueError:
                # Keep startup fail-closed and let the setup UI explain the
                # invalid local configuration instead of blocking FinSight.
                pass
        resolution = getattr(services, "identity_resolution", None)
        self._user_id = (
            resolution.actor.actor_id
            if resolution is not None and resolution.is_resolved
            else DEFAULT_USER_ID
        )

    # --- active review pointer + cycle-keyed working sets ---
    @property
    def active_review_id(self) -> Optional[str]:
        return self._active

    def _session_for(self, cycle_id: str):
        """The workflow session (controlled mutable working data) for a cycle. Preserved across
        review switches; obtaining it never changes the active review or resets another cycle."""
        return self._working.get_or_create(cycle_id).session

    def select_review(self, cycle_id: str) -> None:
        if cycle_id == self._active:
            return                                  # re-selecting the active review is a no-op
        self._active = cycle_id
        if cycle_id:
            self._working.get_or_create(cycle_id)   # ensure a working set; never resets others
        self.activeReviewChanged.emit(cycle_id or "")

    def clear_review(self) -> None:
        # Clears only the active-review pointer; working sets are preserved (a later re-select
        # returns the same data; a new review gets its own set).
        self._active = None
        self.activeReviewChanged.emit("")

    def begin_new_review(self) -> None:
        self.clear_review()

    # --- V2 Workflow 1: Review Management (no upload/extraction/validation dependency) ---
    def review_management_availability(self):
        return self._s.review_management.availability()

    def create_managed_review(self, month: int, year: int, idempotency_key: str):
        review = self._s.review_management.create_review(
            month, year, idempotency_key=idempotency_key
        )
        self._active = review.review_id
        self._working.get_or_create(review.review_id)
        self.activeReviewChanged.emit(review.review_id)
        self.reviewsChanged.emit()
        self.reviewManagementChanged.emit()
        self.managedReviewOpened.emit(review.review_id)
        return review

    def managed_reviews(self, statuses=None):
        return self._s.review_management.list_reviews(statuses=statuses)

    def managed_review_period_count(self, month: int, year: int) -> int:
        return self._s.review_management.existing_review_count_for_period(month, year)

    def reopen_managed_review(self, review_id: str):
        review = self._s.review_management.open_review(review_id)
        self._active = review.review_id
        self._working.get_or_create(review.review_id)
        self.activeReviewChanged.emit(review.review_id)
        self.managedReviewOpened.emit(review.review_id)
        return review

    def prepare_review_disposal(self, review_id: str):
        """Create the governed, one-use deletion preview shown by the UI."""

        return self._s.review_management.prepare_disposal(review_id)

    def cancel_review_disposal(self, confirmation_token: str) -> bool:
        return self._s.review_management.cancel_disposal(confirmation_token)

    def confirm_review_disposal(
        self, review_id: str, confirmation_token: str
    ):
        receipt = self._s.review_management.confirm_disposal(
            review_id, confirmation_token
        )
        if self._active == review_id:
            self.clear_review()
        self._working.invalidate(review_id)
        self.reviewsChanged.emit()
        self.reviewManagementChanged.emit()
        return receipt

    # --- V2 Workflow 2: read-only source inspection and atomic pair binding ---
    def inspect_source_async(
        self,
        path,
        role,
        on_result: Callable,
        on_error: Callable,
    ) -> None:
        review_id = self._active
        if not review_id:
            on_error(RuntimeError("No active review is available for source intake."))
            return
        try:
            self._s.review_management.begin_source_inspection(review_id, role)
        except Exception as exc:
            on_error(exc)
            return
        self.processingChanged.emit(True)

        def work():
            return self._s.source_intake.inspect(path, role)

        def done(inspection):
            try:
                inspection = self._s.review_management.record_source_inspection(
                    review_id, inspection
                )
            except Exception as exc:
                self.processingChanged.emit(False)
                on_error(exc)
                return
            self.processingChanged.emit(False)
            on_result(inspection)

        def failed(exc):
            self.processingChanged.emit(False)
            surfaced_error = exc
            try:
                surfaced_error = (
                    self._s.review_management.record_source_inspection_failure(
                        review_id, role
                    )
                )
            except Exception as recording_error:
                surfaced_error = recording_error
            _log.error(
                "source inspection failed rid=%s role=%s: %s",
                review_id,
                getattr(role, "value", role),
                type(exc).__name__,
                exc_info=exc,
            )
            on_error(surfaced_error)

        run_async(work, done, failed)

    def evaluate_source_pair(self, budget, ged, selected_period):
        return self._s.source_intake.evaluate(
            budget=budget,
            ged=ged,
            selected_period=selected_period,
        )

    def commit_source_pair_async(
        self,
        review_id: str,
        pair,
        idempotency_key: str,
        on_result: Callable,
        on_error: Callable,
    ) -> None:
        if review_id != self._active:
            on_error(RuntimeError("The active review changed before source intake."))
            return
        self.processingChanged.emit(True)

        def work():
            # Bounded, read-only source identity check happens off the UI thread.
            self._s.source_intake.assert_pair_unchanged(pair)
            return None

        def done(_ignored):
            try:
                result = self._s.review_management.commit_source_intake(
                    review_id,
                    pair,
                    idempotency_key=idempotency_key,
                )
            except Exception as exc:
                self.processingChanged.emit(False)
                on_error(exc)
                return
            self.processingChanged.emit(False)
            self.reviewManagementChanged.emit()
            self.sourceIntakeChanged.emit(review_id)
            self.workflowChanged.emit(review_id)
            on_result(result)

        def failed(exc):
            self.processingChanged.emit(False)
            _log.error(
                "source identity verification failed rid=%s: %s",
                review_id,
                type(exc).__name__,
                exc_info=exc,
            )
            on_error(exc)

        run_async(work, done, failed)

    def source_intake_summary(self, review_id: str):
        return self._s.review_management.source_intake_summary(review_id)

    # --- Integrated V2 reviewed-data and deterministic validation flow ---
    def prepare_financial_data_async(
        self,
        review_id: str,
        on_progress: Callable,
        on_result: Callable,
        on_error: Callable,
    ) -> None:
        if review_id != self._active:
            on_error(RuntimeError("The active review changed before data preparation."))
            return
        try:
            inputs = self._s.financial_review.reconstruction_inputs(review_id)
        except Exception as exc:
            on_error(exc)
            return
        self._financial_source_names[review_id] = {
            role: str(source.get("filename") or f"{role.title()} Report")
            for role, source in inputs["sources"].items()
        }
        self.processingChanged.emit(True)
        on_progress("Reading files")

        def work():
            budget, ged = self._s.financial_review.inspect_reconstruction_sources(inputs)
            return self._s.financial_review.build_dataset(inputs, budget, ged)

        def done(dataset):
            self.processingChanged.emit(False)
            on_result(dataset)

        def failed(exc):
            self.processingChanged.emit(False)
            _log.error(
                "financial data reconstruction failed rid=%s: %s",
                review_id,
                type(exc).__name__,
                exc_info=exc,
            )
            on_error(exc)

        run_async(work, done, failed)

    def financial_source_file_name(
        self, review_id: str, source_role: str
    ) -> str:
        """Return already-loaded display metadata without another source read."""

        role = str(source_role).strip().upper()
        return self._financial_source_names.get(review_id, {}).get(
            role,
            "Budget Report" if role == "BUDGET" else "GED Report",
        )

    def save_financial_correction(
        self,
        dataset,
        *,
        record_id: str,
        field_name: str,
        new_value,
    ):
        event = self._s.financial_review.save_correction(
            dataset.review_id,
            dataset,
            record_id=record_id,
            field_name=field_name,
            new_value=new_value,
        )
        self.financialReviewChanged.emit(dataset.review_id)
        return event

    def financial_correction_history(self, review_id: str):
        return self._s.financial_review.correction_history(review_id)

    def confirm_financial_data(self, dataset, attestation_text: str):
        review = self._s.financial_review.confirm_reviewed_data(
            dataset.review_id,
            dataset,
            attestation_text=attestation_text,
        )
        self.reviewManagementChanged.emit()
        self.workflowChanged.emit(dataset.review_id)
        self.financialReviewChanged.emit(dataset.review_id)
        return review

    def validate_financial_async(
        self,
        dataset,
        on_progress: Callable,
        on_result: Callable,
        on_error: Callable,
        *,
        confirmation_id: str,
    ) -> None:
        review_id = dataset.review_id
        def record_failure(error: BaseException) -> None:
            try:
                self._s.financial_review.record_validation_failure(
                    confirmation_id, error
                )
            except Exception:
                _log.exception(
                    "validation failure audit could not be recorded rid=%s",
                    review_id,
                )

        if review_id != self._active:
            error = RuntimeError(
                "The active review changed before validation."
            )
            record_failure(error)
            on_error(error)
            return
        try:
            manifest = self._s.financial_review.start_validation_attempt(
                confirmation_id, dataset
            )
        except Exception as exc:
            record_failure(exc)
            on_error(exc)
            return
        self.processingChanged.emit(True)
        started_at = self._s.financial_review.timestamp()

        def work():
            return self._s.financial_review.evaluate_manifest(dataset, manifest)

        def done(evaluation):
            try:
                projection = self._s.financial_review.persist_evaluation(
                    review_id,
                    dataset,
                    evaluation,
                    confirmation_id=confirmation_id,
                    started_at=started_at,
                )
            except Exception as exc:
                record_failure(exc)
                self.processingChanged.emit(False)
                if self._active != review_id:
                    _log.info(
                        "validation persistence failed for inactive review "
                        "rid=%s; failure recorded and UI callback suppressed "
                        "active_rid=%s",
                        review_id,
                        self._active or "",
                    )
                    return
                on_error(exc)
                return
            self.processingChanged.emit(False)
            self.reviewManagementChanged.emit()
            self.workflowChanged.emit(review_id)
            self.financialReviewChanged.emit(review_id)
            if self._active != review_id:
                # The completed result belongs to the review that started the
                # worker and remains legitimately persisted there.  A review
                # switch must not deliver that result into the now-active
                # review's presentation callbacks, however.
                _log.info(
                    "validation completed for inactive review rid=%s; "
                    "result persisted and UI callback suppressed active_rid=%s",
                    review_id,
                    self._active or "",
                )
                return
            on_result(projection)

        def failed(exc):
            record_failure(exc)
            self.processingChanged.emit(False)
            _log.error(
                "deterministic validation failed rid=%s: %s",
                review_id,
                type(exc).__name__,
                exc_info=exc,
            )
            if self._active != review_id:
                _log.info(
                    "validation failed for inactive review rid=%s; "
                    "failure recorded and UI callback suppressed active_rid=%s",
                    review_id,
                    self._active or "",
                )
                return
            on_error(exc)

        try:
            run_async(work, done, failed)
        except Exception as exc:
            record_failure(exc)
            self.processingChanged.emit(False)
            on_error(exc)

    def validation_rule_set_proposal(self, dataset):
        return self._s.financial_review.validation_rule_set_proposal(
            dataset.review_id, dataset
        )

    def confirm_validation_rule_set(self, dataset, proposal_hash: str):
        return self._s.financial_review.confirm_validation_rule_set(
            dataset.review_id,
            dataset,
            proposal_hash=proposal_hash,
        )

    def record_revalidation_entry(self, review_id: str):
        return self._s.financial_review.record_revalidation_entry(review_id)

    def financial_results(self, review_id: str):
        return self._s.financial_review.results(review_id)

    def financial_explain_finding(self, review_id: str, finding_id: str):
        return self._s.financial_review.explain_finding(
            review_id, finding_id
        )

    def financial_finding_review_history(
        self, review_id: str, finding_id: str
    ):
        return self._s.financial_review.finding_review_history(
            review_id, finding_id
        )

    def financial_update_finding_status(
        self,
        review_id: str,
        finding_id: str,
        status: str,
        *,
        reason: str,
    ):
        event = self._s.financial_review.update_finding_review_status(
            review_id,
            finding_id,
            status,
            reason=reason,
        )
        self.financialReviewChanged.emit(review_id)
        return event

    def financial_leadership_summary(
        self, review_id: str, run_id: str | None = None
    ):
        return self._s.financial_review.leadership_summary(
            review_id, run_id
        )

    # --- Versioned Rules Repository ---
    def bound_rules(self, review_id: str):
        service = getattr(self._s, "rule_management", None)
        if service is not None:
            try:
                roles = set(
                    self.review_management_availability().role_labels
                )
            except Exception:
                roles = set()
            administrative = "Rule Administrator" in roles
            rules = service.list_repository_rules(
                review_id, administrative=administrative
            )
            history = service.rule_set_history(
                review_id, administrative=administrative
            )
            current = history[-1] if history else {}
            return {
                "rule_set_id": current.get("rule_set_id", ""),
                "rule_set_version": current.get("version", ""),
                "rules": rules,
            }
        manifest = self._s.financial_review.rule_manifest(review_id)
        return {
            "rule_set_id": manifest.rule_set_id,
            "rule_set_version": manifest.version,
            "rules": [
                {
                    "rule_id": item.rule_id,
                    "name": item.name,
                    "version": item.version,
                    "severity": item.severity,
                    "baseline_status": item.baseline_status,
                    "evaluator_key": item.evaluator_key,
                    "purpose": getattr(item, "purpose", ""),
                    "required_fields": list(
                        getattr(item, "required_fields", ())
                    ),
                    "grouping_keys": list(
                        getattr(item, "grouping_keys", ())
                    ),
                    "parameters": dict(getattr(item, "parameters", {})),
                    "lifecycle_status": getattr(
                        item, "lifecycle_status", "ACTIVE"
                    ),
                }
                for item in manifest.rules
            ],
        }

    def create_optional_rule(self, review_id: str, definition):
        parameters = definition.get("parameters", {})
        result = self._s.rule_management.create_optional_draft(
            name=definition["name"],
            purpose=definition["purpose"],
            severity=definition["severity"],
            operator=self._normalize_optional_operator(
                parameters.get("operator")
            ),
            threshold=str(parameters.get("threshold", "")),
        )
        self.financialReviewChanged.emit(review_id)
        return result

    def edit_optional_rule(self, review_id: str, rule_id: str, definition):
        parameters = definition.get("parameters", {})
        result = self._s.rule_management.edit_optional_draft(
            rule_id,
            name=definition["name"],
            purpose=definition["purpose"],
            severity=definition["severity"],
            operator=self._normalize_optional_operator(
                parameters.get("operator")
            ),
            threshold=str(parameters.get("threshold", "")),
        )
        self.financialReviewChanged.emit(review_id)
        return result

    def test_optional_rule(self, review_id: str, rule_id: str, dataset):
        rules = self._s.rule_management.list_repository_rules(
            review_id, administrative=True
        )
        selected = next(
            (
                item
                for item in reversed(rules)
                if item["rule_id"] == rule_id
                and item.get("lifecycle_status") in {"DRAFT", "TESTED"}
            ),
            None,
        )
        if selected is None:
            raise RuntimeError("Select a Draft or Tested optional rule version.")
        result = self._s.rule_management.test_draft(
            review_id, dataset, rule_id, selected["version"]
        )
        metrics = result["metrics"]
        return {
            **result,
            "records_evaluated": sum(
                int(metrics.get(key, 0))
                for key in (
                    "pass_count",
                    "fail_count",
                    "not_evaluated_count",
                )
            ),
            "findings": int(metrics.get("fail_count", 0)),
        }

    def set_optional_draft_excluded(
        self,
        review_id: str,
        rule_id: str,
        version: str,
        *,
        excluded: bool,
    ):
        result = (
            self._s.rule_management.set_draft_excluded_from_proposed_set(
                review_id,
                rule_id,
                version,
                excluded=excluded,
            )
        )
        self.financialReviewChanged.emit(review_id)
        return result

    def activate_optional_rule(
        self, review_id: str, rule_id: str, version: str
    ):
        result = self._s.rule_management.activate_optional_version(
            review_id, rule_id, version
        )
        self.financialReviewChanged.emit(review_id)
        return result

    def set_optional_rule_enabled(
        self, review_id: str, rule_id: str, enabled: bool
    ):
        result = self._s.rule_management.set_optional_enabled(
            review_id, rule_id, enabled
        )
        self.financialReviewChanged.emit(review_id)
        return result

    def delete_optional_rule(self, review_id: str, rule_id: str):
        result = self._s.rule_management.retire_optional_rule(
            review_id, rule_id
        )
        self.financialReviewChanged.emit(review_id)
        return result

    def current_actor_id(self) -> str:
        resolution = getattr(self._s, "identity_resolution", None)
        if resolution is None or not resolution.is_resolved:
            return ""
        return resolution.require_actor().actor_id

    def protected_change_requests(self, *, for_decision: bool = False):
        return self._s.rule_management.list_protected_change_requests(
            for_decision=for_decision
        )

    def request_protected_change(
        self,
        review_id: str,
        dataset,
        rule_id: str,
        proposal,
    ):
        result = self._s.rule_management.submit_protected_change_request(
            review_id=review_id,
            dataset=dataset,
            rule_id=rule_id,
            proposed_version=proposal["proposed_version"],
            change_kind=proposal["change_kind"],
            name=proposal["name"],
            purpose=proposal["purpose"],
            severity=proposal["severity"],
            parameters=proposal["parameters"],
            reason=proposal["reason"],
            prior_request_id=proposal.get("prior_request_id"),
        )
        self.financialReviewChanged.emit(review_id)
        return result

    def decide_protected_change(
        self,
        request_id: str,
        *,
        decision: str,
        reason: str,
    ):
        result = self._s.rule_management.decide_protected_change(
            request_id,
            decision=decision,
            reason=reason,
        )
        if self._active:
            self.financialReviewChanged.emit(self._active)
        return result

    def workspace_upgrade_status(self, review_id: str):
        return self._s.rule_management.workspace_upgrade_status(review_id)

    def workspace_upgrade_candidates(self):
        return self._s.rule_management.list_workspace_upgrade_candidates()

    def workspace_upgrade_requests(
        self,
        *,
        review_id: str | None = None,
        for_decision: bool = False,
    ):
        return self._s.rule_management.list_workspace_upgrade_requests(
            review_id=review_id,
            for_decision=for_decision
        )

    def request_workspace_upgrade(
        self,
        review_id: str,
        *,
        reason: str,
        target_baseline_id: str | None = None,
    ):
        result = self._s.rule_management.request_workspace_upgrade(
            review_id,
            reason=reason,
            target_baseline_id=target_baseline_id,
        )
        self.financialReviewChanged.emit(review_id)
        return result

    def decide_workspace_upgrade(
        self,
        request_id: str,
        *,
        decision: str,
        reason: str,
    ):
        result = self._s.rule_management.decide_workspace_upgrade(
            request_id,
            decision=decision,
            reason=reason,
        )
        review_id = result.get("review_id")
        if review_id:
            self.financialReviewChanged.emit(str(review_id))
        return result

    @staticmethod
    def _normalize_optional_operator(value) -> str:
        return {
            "GREATER_THAN": "GT",
            ">": "GT",
            "GT": "GT",
        }.get(str(value or "").upper(), str(value or "").upper())

    def validation_history(self, review_id: str):
        service = getattr(self._s, "rule_management", None)
        if service is not None and hasattr(service, "validation_history"):
            return service.validation_history(review_id)
        if hasattr(self._s.financial_review, "validation_history"):
            return self._s.financial_review.validation_history(review_id)
        projection = self._s.financial_review.results(review_id)
        return [projection] if projection else []

    def latest_validation_comparison(self, review_id: str):
        history = self._s.financial_review.validation_history(review_id)
        if len(history) < 2:
            return None
        return self._s.financial_review.compare_validation_runs(
            review_id,
            history[-2]["run_id"],
            history[-1]["run_id"],
        )

    def complete_financial_review(self, review_id: str):
        review = self._s.financial_review.complete_review(review_id)
        self.reviewManagementChanged.emit()
        self.workflowChanged.emit(review_id)
        self.financialReviewChanged.emit(review_id)
        return review

    # --- Phase 6.4a test seams ---
    def working_set_cycle_ids(self) -> List[str]:
        return self._working.cycle_ids()

    def has_working_set(self, cycle_id: str) -> bool:
        return self._working.get(cycle_id) is not None

    def working_set_identity(self, cycle_id: str) -> Optional[int]:
        ws = self._working.get(cycle_id)
        return id(ws) if ws is not None else None

    # --- Phase 6.4c: fingerprint-verified reconstruction & recovery ---
    def recovery_state(self, cycle_id: str) -> Optional[str]:
        """The last observed RecoveryStatus for a cycle in this session (None until first attempt)."""
        return self._recovery_state.get(cycle_id)

    def last_recovery(self, cycle_id: str):
        """The last RecoveryResult for a cycle (carries the presentation-neutral recovery message)."""
        return self._last_recovery.get(cycle_id)

    def is_reconstructing(self, cycle_id: str) -> bool:
        return cycle_id in self._reconstructing

    def _record_recovery(self, cycle_id: str, result) -> None:
        self._recovery_state[cycle_id] = result.status.value
        self._last_recovery[cycle_id] = result

    def _apply_recovery(self, cycle_id: str, result):
        # UI thread: install a validated candidate (build-then-swap) and record divergence once. A
        # failed reconstruction carries no session, so a valid cached working set is never replaced.
        if result.usable_session is not None:
            self._working.install(cycle_id, result.usable_session)
        self._s.recovery.record_divergence(cycle_id, result)   # persisted, per-pair idempotent
        self._record_recovery(cycle_id, result)
        return result

    def reconstruct_sync(self, cycle_id: str):
        """Load + reconstruct + install on the calling thread. Used by tests and as the building block
        of the async path. Never mutates workflow/generation state."""
        if not cycle_id:
            return None
        state = self.workflow_state(cycle_id)
        if state is None:
            return None
        if not has_reached(state, CycleState.INTAKE):
            self._record_recovery(cycle_id, _no_source(cycle_id))
            return None
        if self._working.has_working_data(cycle_id):
            result = ready_from_cache(cycle_id)
            self._record_recovery(cycle_id, result)
            return result
        inputs = self._s.recovery.load_inputs(cycle_id)
        if inputs is None:
            return None
        return self._apply_recovery(cycle_id, self._s.recovery.reconstruct(inputs))

    def reconstruct_async(self, cycle_id: str, on_result: Callable, on_error: Callable) -> None:
        """Reconstruct off the UI thread. DB reads (load_inputs) + install happen on the UI thread;
        the expensive fingerprint+extract+verify compute runs on a worker. Prevents double-triggering."""
        if not cycle_id or cycle_id in self._reconstructing:
            return
        state = self.workflow_state(cycle_id)
        if state is None:
            on_error(RuntimeError("review_not_found"))
            return
        if not has_reached(state, CycleState.INTAKE):
            self._record_recovery(cycle_id, _no_source(cycle_id))
            self.reviewRecoveryChanged.emit(cycle_id)
            return
        if self._working.has_working_data(cycle_id):
            result = ready_from_cache(cycle_id)
            self._record_recovery(cycle_id, result)
            self.reviewRecoveryChanged.emit(cycle_id)
            on_result(result)
            return
        inputs = self._s.recovery.load_inputs(cycle_id)      # UI-thread DB read
        if inputs is None:
            on_error(RuntimeError("review_not_found"))
            return
        self._reconstructing.add(cycle_id)
        self.processingChanged.emit(True)

        def work():
            return self._s.recovery.reconstruct(inputs)      # worker: DB-free compute

        def done(result):
            self._reconstructing.discard(cycle_id)
            self.processingChanged.emit(False)
            self._apply_recovery(cycle_id, result)           # UI thread: install + divergence audit
            self.reviewRecoveryChanged.emit(cycle_id)
            on_result(result)

        def failed(exc):
            self._reconstructing.discard(cycle_id)
            self.processingChanged.emit(False)
            _log.error("reconstruction failed cid=%s: %s", cycle_id, type(exc).__name__, exc_info=exc)
            on_error(exc)

        run_async(work, done, failed)

    def rebind_source(self, cycle_id: str, document_type: str, new_path: str):
        """Locate/re-select a moved source. Updates ONLY the path hint on a fingerprint match (never a
        divergent file), invalidating the stale working set so the next reconstruction rebuilds it."""
        result = self._s.recovery.apply_rebind(cycle_id, document_type, new_path)
        if result.status == RecoveryStatus.MOVED_SOURCE_CANDIDATE:
            self._working.invalidate(cycle_id)               # force rebuild from the new location
        self._record_recovery(cycle_id, result)
        self.reviewRecoveryChanged.emit(cycle_id)
        return result

    # --- R1-M4: review abandonment + inactivity (ADR-014 / DEC-035; explicit, audited, reversible) ---
    def abandon_review(self, cycle_id: str) -> None:
        self._s.abandonment.abandon(cycle_id)
        self.reviewDispositionChanged.emit(cycle_id)
        self.reviewsChanged.emit()

    def resume_abandoned_review(self, cycle_id: str) -> None:
        self._s.abandonment.resume(cycle_id)
        self.reviewDispositionChanged.emit(cycle_id)
        self.reviewsChanged.emit()

    def review_lifecycle_status(self, cycle_id: str):
        """(disposition, inactive_days, InactivityLevel, message) — deterministic; no AI."""
        return self._s.abandonment.status(cycle_id)

    # --- read-only queries ---
    def reviews_with_status(self) -> List[ReviewStatusView]:
        return self._s.reviews.list_with_status()

    def review_status(self, cycle_id: str) -> Optional[ReviewStatusView]:
        return self._s.reviews.get_status(cycle_id)

    def summary(self, cycle_id: str) -> Optional[SummaryView]:
        return self._s.summary.for_cycle(cycle_id)

    def findings(self, cycle_id: str) -> List[FindingView]:
        return self._s.findings.list_for_cycle(cycle_id)

    def audit_timeline(self, cycle_id: str) -> List[AuditEventView]:
        return self._s.audit.timeline(cycle_id)

    def workflow_state(self, cycle_id: str) -> Optional[str]:
        return self._s.workflow.state(cycle_id)

    def portfolio(self):
        """Deterministic cross-review portfolio summary (Phase 5.3). Built on demand from the existing
        read-only query services — no caching, so it always reflects current persisted state."""
        from finsight.application.read_models.portfolio import PortfolioQueryService
        return PortfolioQueryService(self._s.reviews, self._s.findings).summary()

    # --- Phase 5.4: verification preview, account labels, readiness (session-scoped where noted) ---
    def verification_preview(self, cycle_id: str):
        ws = self._working.get(cycle_id)
        return self._s.workflow.verification_preview(ws.session) if ws else None

    def review_readiness(self, cycle_id: str):
        """Deterministic readiness derived from persisted state, enriched by the session snapshot."""
        from finsight.application.read_models.verification import build_readiness
        return build_readiness(cycle_id, self.workflow_state(cycle_id),
                               self.validation_snapshot(cycle_id))

    def has_session_context(self, cycle_id: str) -> bool:
        ws = self._working.get(cycle_id)
        return bool(ws and ws.has_files())

    def validation_snapshot(self, cycle_id: str):
        ws = self._working.get(cycle_id)
        return self._s.workflow.validation_snapshot(ws.session) if ws else None

    # --- workflow commands (may raise finsight.application.errors.FinsightAppError) ---
    def create_review(self, cycle_id: str, month: str, year: str):
        cycle = self._s.workflow.create_review(cycle_id, month, year)
        self._active = cycle.cycle_id
        self._working.get_or_create(cycle.cycle_id)   # distinct working set for the new cycle
        self.activeReviewChanged.emit(cycle.cycle_id)
        self.reviewsChanged.emit()
        self.workflowChanged.emit(cycle.cycle_id)
        return cycle

    def upload(self, cycle_id: str, ged_path: str, budget_path: str) -> UploadResult:
        result = self._s.workflow.upload(self._session_for(cycle_id), ged_path, budget_path)
        self.workflowChanged.emit(cycle_id)
        return result

    def process_async(self, cycle_id: str, on_result: Callable[[ValidationResult], None],
                      on_error: Callable[[Exception], None]) -> None:
        """Heavy extraction off the UI thread; DB transition on the UI thread (SQLite is thread-bound)."""
        session = self._session_for(cycle_id)
        self.processingChanged.emit(True)

        def work():
            self._s.workflow.prepare_extraction(session)

        def done(_ignored):
            try:
                result = self._s.workflow.finalize_processing(session)
            except Exception as exc:
                self.processingChanged.emit(False)
                on_error(exc)
                return
            self.processingChanged.emit(False)
            self.workflowChanged.emit(cycle_id)
            on_result(result)

        def failed(exc):
            self.processingChanged.emit(False)
            _log.error("processing worker failed cid=%s: %s", cycle_id, type(exc).__name__, exc_info=exc)
            on_error(exc)

        run_async(work, done, failed)

    def verify(self, cycle_id: str) -> None:
        self._s.workflow.verify(self._session_for(cycle_id))
        self.workflowChanged.emit(cycle_id)

    def analyze(self, cycle_id: str) -> AnalysisResult:
        result = self._s.workflow.analyze(self._session_for(cycle_id))
        self.workflowChanged.emit(cycle_id)
        return result

    def summarize(self, cycle_id: str) -> SummaryView:
        result = self._s.workflow.summarize(self._session_for(cycle_id))
        self.workflowChanged.emit(cycle_id)
        return result

    def export(self, cycle_id: str) -> ExportResult:
        result = self._s.workflow.export(self._session_for(cycle_id))
        self.workflowChanged.emit(cycle_id)
        return result

    # --- Ask Fin (explanation-only; the whole pipeline runs off the UI thread) ---
    def ask_fin_available(self) -> bool:
        return self._ask_fin is not None

    def private_ask_fin_available(self) -> bool:
        return bool(
            self._ask_fin is not None
            and hasattr(self._ask_fin, "session")
            and hasattr(self._ask_fin, "ask")
        )

    def private_ask_fin_provider_status_async(
        self, on_result: Callable, on_error: Callable
    ) -> None:
        if not self.private_ask_fin_available():
            on_error(RuntimeError("private_ask_fin_unavailable"))
            return
        run_async(self._ask_fin.provider_status, on_result, on_error)

    def private_ask_fin_configuration(self):
        if self._ask_fin_preferences is None:
            from finsight.delivery.desktop.ask_fin_preferences import (
                PrivateAskFinPreferenceStore,
            )

            self._ask_fin_preferences = PrivateAskFinPreferenceStore()
        return self._ask_fin_preferences.snapshot()

    def private_ask_fin_save_configuration(
        self,
        *,
        endpoint: str,
        model: str,
        approved_model_digest: str,
    ):
        if self._ask_fin_preferences is None:
            from finsight.delivery.desktop.ask_fin_preferences import (
                PrivateAskFinPreferenceStore,
            )

            self._ask_fin_preferences = PrivateAskFinPreferenceStore()
        saved = self._ask_fin_preferences.save(
            endpoint=endpoint,
            model=model,
            approved_model_digest=approved_model_digest,
        )
        if self._ask_fin is not None and hasattr(
            self._ask_fin, "set_settings"
        ):
            self._ask_fin.set_settings(
                self._ask_fin_preferences.effective_settings()
            )
        return saved

    def private_ask_fin_setup_status_async(
        self,
        on_result: Callable,
        on_error: Callable,
        *,
        endpoint: str | None = None,
        model: str | None = None,
        approved_model_digest: str | None = None,
    ) -> None:
        if (
            self._ask_fin is None
            or not hasattr(self._ask_fin, "setup_status")
        ):
            on_error(RuntimeError("private_ask_fin_setup_unavailable"))
            return
        run_async(
            lambda: self._ask_fin.setup_status(
                base_url=endpoint,
                model=model,
                approved_model_digest=approved_model_digest,
            ),
            on_result,
            on_error,
        )

    def private_ask_fin_session_async(
        self,
        on_result: Callable,
        on_error: Callable,
        *,
        context: AskFinContext | None = None,
        review_id: str | None = None,
    ) -> None:
        selected_review = review_id or self._active
        if (
            not self.private_ask_fin_available()
            or not selected_review
            or selected_review != self._active
        ):
            on_error(RuntimeError("private_ask_fin_unavailable"))
            return
        run_async(
            lambda: self._ask_fin.session(
                user_id=self._user_id,
                review_id=selected_review,
                context=context,
            ),
            on_result,
            on_error,
        )

    def private_ask_fin_ask_async(
        self,
        question: str,
        on_result: Callable,
        on_error: Callable,
        *,
        context: AskFinContext | None = None,
        review_id: str | None = None,
    ) -> None:
        selected_review = review_id or self._active
        if (
            not self.private_ask_fin_available()
            or not selected_review
            or selected_review != self._active
        ):
            on_error(RuntimeError("private_ask_fin_unavailable"))
            return
        request = PrivateAskFinRequest(
            user_id=self._user_id,
            review_id=selected_review,
            question=question,
            context=context,
        )
        run_async(
            lambda: self._ask_fin.ask(request),
            on_result,
            on_error,
        )

    def ask_fin_provider_status_async(self, on_result: Callable, on_error: Callable) -> None:
        """Fetch bounded provider status off the UI thread (DB-free)."""
        if self._ask_fin is None:
            on_error(RuntimeError("ask_fin_unavailable"))
            return
        run_async(self._ask_fin.provider_status, on_result, on_error)

    def ask_fin_explain_async(self, question: str, on_result: Callable, on_error: Callable, *,
                              audience: Optional[str] = None,
                              answer_detail: Optional[str] = None) -> None:
        """Run the full AskFinService pipeline off the UI thread for the CURRENT review only. The
        caller supplies only the question + optional formatting overrides; grounding/memory/history
        are never injected here."""
        if self._ask_fin is None:
            on_error(RuntimeError("ask_fin_unavailable"))
            return
        request = AskFinRequest(user_id=self._user_id, cycle_id=self._active or "", question=question,
                                audience=audience, answer_detail=answer_detail)
        run_async(lambda: self._ask_fin.explain(request), on_result, on_error)
