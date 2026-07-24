# Implements: Phase 4C.5, FR-099 — AskFinService: the synchronous, application-layer AI explanation
# coordinator. It ONLY sequences already-tested components; it contains no masking, prompt, provider,
# validation, citation, persistence, retry, or UI logic. Every outcome is a total, deterministic
# AskFinResult, and every terminal failure is fail-fast (no later stage runs). Imports no PySide6,
# asyncio, threading, urllib, sqlite3, infrastructure repositories, or provider transport.
#
# Delivery runs this off the PySide6 UI thread (NFR-004); this module stays synchronous and pure of UI.
from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional

from finsight.application.ai.ask_fin_contracts import (
    AiExecutionMetadata, AskFinRequest, AskFinResult, AskFinStage, AskFinStatus,
)
from finsight.application.ai.citations import assemble_ai_answer
from finsight.application.ai.errors import (
    AiAuthorizationError, AiScopeError, CitationError, ConversationNotFoundError,
    GroundingUnavailableError, MaskingError, PromptBudgetError, PromptBuildError, ProviderError,
    ProviderTimeoutError, ResponseFormatError,
)
from finsight.application.ai.retry import RetryPolicy, Sleeper
from finsight.diagnostics import get_logger
from finsight.domain.ai.contracts import AiInteractionEntry, InteractionEvent

_log = get_logger("ai.ask_fin")


# --- dependency bundles (composition wiring; injected — no service locator, no runtime lookup) ---
@dataclass(frozen=True)
class AiContextSources:
    grounding: object            # GroundingQueryService
    conversations: object        # ConversationService
    memory: object               # ReviewMemoryService
    preferences: object          # PreferencesService


@dataclass(frozen=True)
class AiPipeline:
    masking: object              # MaskingService
    prompt_builder: object       # PromptBuilder
    provider_runtime: object     # AiProviderRuntime
    validator: object            # ResponseValidator
    verifier: object             # CitationVerifier


@dataclass(frozen=True)
class AiOrchestrationInfra:
    journal: object              # AiInteractionJournal (append-only)
    retry_policy: RetryPolicy
    sleeper: Sleeper
    clock: object                # .now() -> timestamp str
    new_id: object               # () -> id str
    monotonic: object = None     # optional () -> float, for elapsed_ms; None = not measured


@dataclass
class _RunState:
    provider: Optional[str] = None
    model: Optional[str] = None
    schema_version: Optional[str] = None
    prompt_version: Optional[str] = None
    masking_policy_version: Optional[str] = None
    citation_format_version: Optional[str] = None
    grounding_confidence: Optional[str] = None
    citation_count: int = 0
    citation_namespace_counts: Dict[str, int] = field(default_factory=dict)
    masking_counts: Dict[str, int] = field(default_factory=dict)
    truncation_counts: Dict[str, int] = field(default_factory=dict)
    provider_attempts: int = 0
    validation_retries: int = 0
    timeout_retries: int = 0
    started: Optional[float] = None
    conversation_recorded: Optional[bool] = None


def _masking_counts(summary) -> Dict[str, int]:
    return {"employee_name": summary.employee_name, "email": summary.email, "phone": summary.phone,
            "tax_id": summary.tax_id, "banking_id": summary.banking_id, "actor": summary.actor}


def _truncation_counts(t) -> Dict[str, int]:
    return {"findings_omitted": t.findings_omitted, "conversation_dropped": t.conversation_dropped,
            "memory_dropped": t.memory_dropped, "provenance_dropped": t.provenance_dropped,
            "audit_dropped": t.audit_dropped}


def _namespace_counts(refs) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for r in refs:
        counts[r.namespace.value] = counts.get(r.namespace.value, 0) + 1
    return counts


class AskFinService:
    """Coordinator only. Constructor takes injected interfaces/services grouped into cohesive bundles;
    nothing depends back on it (no cycles). One public entry point, a fixed linear pipeline, fail-fast."""

    def __init__(self, authorization, context: AiContextSources, pipeline: AiPipeline,
                 infra: AiOrchestrationInfra):
        self._authorization = authorization        # AiAuthorizationPolicy
        self._context = context
        self._pipeline = pipeline
        self._infra = infra

    # ------------------------------------------------------------------ public API
    def explain(self, request: AskFinRequest) -> AskFinResult:
        state = _RunState()
        if self._infra.monotonic is not None:
            state.started = self._infra.monotonic()
        self._journal_requested(request)          # one REQUESTED per user request (best-effort)

        ctx, pipe = self._context, self._pipeline

        # 1. Authorization (fail-closed → REFUSED, no AiAnswer, no provider call)
        try:
            self._authorization.authorize(user_id=request.user_id, cycle_id=request.cycle_id)
        except AiAuthorizationError as ex:
            return self._finalize(request, state, AskFinStatus.REFUSED, None,
                                  ex.code or "authorization_denied", AskFinStage.AUTHORIZATION)

        # 2. Scope / conversation validation (also loads history when a conversation is supplied)
        history: List[object] = []
        if request.conversation_id:
            try:
                _conv, history = ctx.conversations.load(
                    request.conversation_id, request.user_id, request.cycle_id)
            except AiScopeError as ex:
                return self._finalize(request, state, AskFinStatus.REFUSED, None,
                                      ex.code or "scope_denied", AskFinStage.SCOPE)
            except ConversationNotFoundError as ex:
                return self._finalize(request, state, AskFinStatus.FAILED, None,
                                      ex.code or "conversation_not_found", AskFinStage.SCOPE)

        # 3. Grounding (no deterministic review → cannot explain → FAILED)
        try:
            grounding = ctx.grounding.context(request.cycle_id)
        except GroundingUnavailableError as ex:
            return self._finalize(request, state, AskFinStatus.FAILED, None,
                                  ex.code or "grounding_unavailable", AskFinStage.GROUNDING)
        if grounding.review is None:
            return self._finalize(request, state, AskFinStatus.FAILED, None,
                                  "grounding_unavailable", AskFinStage.GROUNDING)

        # 4. Memory retrieval
        memory = ctx.memory.list(request.user_id, request.cycle_id)

        # 5. Preference resolution: request override → preference → None
        audience = (request.audience if request.audience is not None
                    else ctx.preferences.get(request.user_id, "audience"))
        answer_detail = (request.answer_detail if request.answer_detail is not None
                         else ctx.preferences.get(request.user_id, "answer_detail"))

        # 6. Masking (fail-closed → FAILED before any prompt is built)
        try:
            masked = pipe.masking.mask(grounding=grounding, question=request.question,
                                       conversation=history, memory=memory)
        except MaskingError as ex:
            return self._finalize(request, state, AskFinStatus.FAILED, None,
                                  ex.code or "masking_failed", AskFinStage.MASKING)
        state.masking_counts = _masking_counts(masked.summary)
        state.masking_policy_version = masked.summary.policy_version

        # 7. PromptBuilder — receives ONLY masked values (critical confidentiality invariant)
        try:
            built = pipe.prompt_builder.build(
                grounding=masked.grounding, question=masked.question,
                conversation=masked.conversation, memory=masked.memory,
                audience=audience, answer_detail=answer_detail)
        except (PromptBuildError, PromptBudgetError) as ex:
            return self._finalize(request, state, AskFinStatus.FAILED, None,
                                  ex.code or "prompt_build_failed", AskFinStage.PROMPT_BUILD)
        state.schema_version = built.request.schema_version
        state.prompt_version = built.request.prompt_version
        state.truncation_counts = _truncation_counts(built.truncation)
        has_citable = bool(built.citation_index.valid_keys)

        # 8-9. Provider execution + response validation, with retry.
        # AskFinService owns the attempt counters; RetryPolicy owns the bounds; Sleeper owns the delay.
        terminal, execution, validated = self._execute_with_retry(request, state, built)
        if terminal is not None:          # a terminal FAILED result was produced inside the loop
            return terminal

        # 10. Citation verification (no retry)
        try:
            citations = pipe.verifier.verify(validated, built.citation_index)
        except CitationError as ex:
            return self._finalize(request, state, AskFinStatus.FAILED, None,
                                  ex.code or "citation", AskFinStage.CITATION)
        state.citation_count = len(citations)
        state.citation_namespace_counts = _namespace_counts(citations)

        # 11. AiAnswer assembly (validated + verified output only)
        answer = assemble_ai_answer(
            validated=validated, citations=citations,
            provider=execution.provider, model=execution.model,
            schema_version=built.request.schema_version, prompt_version=built.request.prompt_version,
            masking_policy_version=masked.summary.policy_version,
            has_citable_grounding=has_citable, truncated=built.truncation.truncated)
        state.grounding_confidence = answer.grounding_confidence.value
        state.citation_format_version = answer.citation_format_version

        if not answer.unable_to_answer:
            status = AskFinStatus.OK
        elif execution.degraded or not execution.generation_available:
            status = AskFinStatus.DEGRADED         # NullProvider / fallback refusal
        else:
            status = AskFinStatus.UNANSWERABLE     # active provider genuinely refused

        # 12. Conversation persistence — only a valid answer, only with a conversation, gated by the
        # user's conversation_persistence policy. Records success/failure/None without corrupting the
        # answer on failure.
        if request.conversation_id:
            state.conversation_recorded = self._persist(request, answer)

        # 13-14. completion journal + return
        return self._finalize(request, state, status, answer, None, AskFinStage.COMPLETE)

    # ------------------------------------------------------------------ provider+validation loop
    def _execute_with_retry(self, request, state, built):
        """Returns (terminal_result, execution, validated). On exhausted failure the first element is a
        terminal FAILED AskFinResult and the rest are None; on success it is (None, execution,
        validated). Provider unavailability is degraded inside AiProviderRuntime, not here."""
        policy, pipe, infra = self._infra.retry_policy, self._pipeline, self._infra
        while True:
            state.provider_attempts += 1
            # 8. Provider
            try:
                execution = pipe.provider_runtime.execute(built.request)
            except ProviderTimeoutError as ex:
                if state.timeout_retries < policy.max_timeout_retries:
                    state.timeout_retries += 1
                    infra.sleeper.sleep(policy.retry_delay_seconds)
                    continue
                return (self._finalize(request, state, AskFinStatus.FAILED, None,
                                       ex.code or "provider_timeout", AskFinStage.PROVIDER), None, None)
            except ProviderError as ex:            # non-timeout, non-unavailable transport failure
                return (self._finalize(request, state, AskFinStatus.FAILED, None,
                                       ex.code or "provider_error", AskFinStage.PROVIDER), None, None)
            state.provider, state.model = execution.provider, execution.model
            # 9. Validation
            try:
                validated = pipe.validator.validate(
                    execution.response.text, schema_version=built.request.schema_version)
            except ResponseFormatError as ex:
                if state.validation_retries < policy.max_response_format_retries:
                    state.validation_retries += 1
                    infra.sleeper.sleep(policy.retry_delay_seconds)
                    continue
                return (self._finalize(request, state, AskFinStatus.FAILED, None,
                                       ex.code or "response_format", AskFinStage.VALIDATION), None, None)
            return (None, execution, validated)

    # ------------------------------------------------------------------ side effects (isolated)
    def _persist(self, request, answer) -> Optional[bool]:
        # None when persistence is disabled by preference; True on success; False on caught failure.
        # A persistence failure must NOT corrupt a valid answer. Decided via existing services only —
        # no repository access here.
        if not self._context.preferences.conversation_persistence_enabled(request.user_id):
            return None
        conv = self._context.conversations
        try:
            conv.append_user_message(request.conversation_id, request.user_id, request.cycle_id,
                                     request.question)
            conv.append_assistant_message(request.conversation_id, request.user_id, request.cycle_id,
                                          answer.answer_text)
            return True
        except Exception:
            _log.warning("ask_fin conversation persistence failed cid=%s", request.cycle_id)
            return False

    def _finalize(self, request, state, status, answer, error_code, stage) -> AskFinResult:
        meta = self._build_metadata(state, error_code, stage)
        journal_ok = self._journal_completed(request, status, meta)
        meta = replace(meta, journal_recorded=journal_ok)
        _log.info("ask_fin status=%s last_stage=%s provider=%s attempts=%d error=%s",
                  status.value, meta.last_stage, meta.provider, meta.provider_attempts, error_code)
        return AskFinResult(status, answer, error_code, stage, meta)

    def _build_metadata(self, state, error_code, stage) -> AiExecutionMetadata:
        elapsed = None
        if state.started is not None and self._infra.monotonic is not None:
            elapsed = int((self._infra.monotonic() - state.started) * 1000)
        return AiExecutionMetadata(
            provider=state.provider, model=state.model, schema_version=state.schema_version,
            prompt_version=state.prompt_version, masking_policy_version=state.masking_policy_version,
            citation_format_version=state.citation_format_version,
            grounding_confidence=state.grounding_confidence, citation_count=state.citation_count,
            citation_namespace_counts=dict(state.citation_namespace_counts),
            masking_counts=dict(state.masking_counts), truncation_counts=dict(state.truncation_counts),
            provider_attempts=state.provider_attempts, validation_retries=state.validation_retries,
            timeout_retries=state.timeout_retries, error_code=error_code, last_stage=stage.value,
            elapsed_ms=elapsed, conversation_recorded=state.conversation_recorded)

    def _journal_requested(self, request) -> None:
        try:
            self._infra.journal.append(AiInteractionEntry(
                self._infra.new_id(), request.user_id, request.cycle_id, request.conversation_id,
                InteractionEvent.EXPLANATION_REQUESTED, "ok", {}, self._infra.clock.now()))
        except Exception:
            _log.warning("ask_fin requested-journal failed cid=%s", request.cycle_id)

    def _journal_completed(self, request, status, meta: AiExecutionMetadata) -> bool:
        try:
            self._infra.journal.append(AiInteractionEntry(
                self._infra.new_id(), request.user_id, request.cycle_id, request.conversation_id,
                InteractionEvent.EXPLANATION_COMPLETED, status.value, meta.as_journal_metadata(),
                self._infra.clock.now()))
            return True
        except Exception:
            # A journal failure must NOT discard a valid answer — surface it, never swallow it.
            _log.warning("ask_fin completion-journal failed cid=%s status=%s", request.cycle_id,
                         status.value)
            return False
