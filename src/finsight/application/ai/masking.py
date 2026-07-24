# Implements: Phase 4C.3, NFR-016, FR-098, ADR-009
#
# MaskingService — deterministic redaction of AI-bound content BEFORE prompt construction. It sits in
# the (future) pipeline at: Authorization → Scope → Grounding → **Masking** → PromptBuilder → Provider.
# This phase implements only the service and its contracts; no pipeline wiring, no provider.
#
# Guarantees (Trust > AI):
#   - Pure and deterministic: no I/O, no persistence, no network. Same inputs → equal result.
#   - Never mutates its inputs; returns new immutable structures.
#   - Redacts configured employee names, emails, phones, tax ids, banking ids, and structured actor
#     fields. NEVER masks deterministic financial facts (amounts, percentages, variances, GL/
#     accounting account numbers, invoice numbers, findings, rules, source refs, fingerprints, review
#     identifiers, vendor/resource names).
#   - Fail-closed: any error raises MaskingError and yields NO partial result — the provider must not
#     be called on partially-masked content.
#   - Irreversible: category tokens only; no token map, no hashes, no reversible data retained (ADR-009).
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple

from finsight.application.ai.errors import MaskingError
from finsight.application.ai.masking_policy import TOKENS, apply_text, build_employee_patterns
from finsight.domain.ai.contracts import (
    AiGroundingContext, ConversationMessage, GroundedAuditEvent, GroundedFinding, MaskCategory,
    MaskingConfiguration, ReviewMemoryEntry,
)


@dataclass(frozen=True)
class MaskingSummary:
    """Deterministic counts-only summary of what was redacted, by category. Contains NO original
    values, NO hashes, NO token map, and NO reversible data."""
    employee_name: int = 0
    email: int = 0
    phone: int = 0
    tax_id: int = 0
    banking_id: int = 0
    actor: int = 0

    @property
    def total(self) -> int:
        return (self.employee_name + self.email + self.phone + self.tax_id
                + self.banking_id + self.actor)


@dataclass(frozen=True)
class MaskingResult:
    """Masked copies of every AI-bound structure plus a counts-only summary. Returned whole or not at
    all (fail-closed)."""
    grounding: AiGroundingContext
    conversation: Tuple[ConversationMessage, ...]
    memory: Tuple[ReviewMemoryEntry, ...]
    question: str
    summary: MaskingSummary


class MaskingService:
    """Applies the deterministic redaction policy to AI-bound content. Configured once with a
    MaskingConfiguration; the employee-name list is validated at construction (empty by default and
    never blocking)."""

    def __init__(self, config: Optional[MaskingConfiguration] = None):
        self._config = config if config is not None else MaskingConfiguration()
        # Validates the configured names (raises MaskingError on empty/whitespace entries).
        self._employee_patterns = build_employee_patterns(self._config.employee_names)

    def mask(self, *, grounding: AiGroundingContext, question: str,
             conversation: Sequence[ConversationMessage] = (),
             memory: Sequence[ReviewMemoryEntry] = ()) -> MaskingResult:
        counts: Dict[str, int] = {}
        try:
            masked_question = self._text(question, counts)
            masked_grounding = self._mask_grounding(grounding, counts)
            masked_conv = tuple(self._mask_message(m, counts) for m in conversation)
            masked_mem = tuple(self._mask_memory(e, counts) for e in memory)
        except MaskingError:
            raise                                   # fail-closed: no partial result
        except Exception as exc:                    # defensive: wrap any unexpected failure
            raise MaskingError("masking failed", detail=str(exc)) from exc
        return MaskingResult(masked_grounding, masked_conv, masked_mem, masked_question,
                             self._summary(counts))

    # --- structured traversal (new objects only; inputs never mutated) ---
    def _mask_grounding(self, g: AiGroundingContext, counts: Dict[str, int]) -> AiGroundingContext:
        # review/summary/rule_run/provenance carry only deterministic facts and vendor/resource
        # names — never masked. Only finding evidence VALUES and audit actors are person/PII-bearing.
        return AiGroundingContext(
            review=g.review,
            findings=[self._mask_finding(f, counts) for f in g.findings],
            summary=g.summary,
            rule_run=g.rule_run,
            provenance=list(g.provenance),
            audit_events=[self._mask_audit(e, counts) for e in g.audit_events],
        )

    def _mask_finding(self, f: GroundedFinding, counts: Dict[str, int]) -> GroundedFinding:
        # Mask evidence VALUES only; keys, id, account, rule_id, severity, type, period, source_refs,
        # and state are deterministic facts and are preserved verbatim.
        evidence = {k: self._text(v, counts) for k, v in f.evidence.items()}
        return GroundedFinding(f.id, f.account, f.rule_id, f.severity, f.finding_type,
                               f.period, evidence, list(f.source_refs), f.state)

    def _mask_audit(self, e: GroundedAuditEvent, counts: Dict[str, int]) -> GroundedAuditEvent:
        return GroundedAuditEvent(e.action, self._actor(e.actor, counts), e.ts)

    def _mask_message(self, m: ConversationMessage, counts: Dict[str, int]) -> ConversationMessage:
        return ConversationMessage(m.message_id, m.conversation_id, m.role,
                                   self._text(m.content, counts), m.seq, m.created_ts)

    def _mask_memory(self, e: ReviewMemoryEntry, counts: Dict[str, int]) -> ReviewMemoryEntry:
        return ReviewMemoryEntry(e.memory_id, e.user_id, e.cycle_id, e.memory_type,
                                 self._text(e.content, counts), self._actor(e.actor, counts),
                                 e.created_ts, e.updated_ts, e.source_type, e.source_id)

    # --- field-level redaction ---
    def _text(self, value: str, counts: Dict[str, int]) -> str:
        return apply_text(value, self._employee_patterns, counts)

    def _actor(self, value: str, counts: Dict[str, int]) -> str:
        """Structured actor fields: wholly redacted to [REDACTED_ACTOR] when mask_actor_fields is on
        (idempotent — an already-redacted actor is not re-counted). When off, the actor is still run
        through the standard free-text categories so a configured name/email there is not leaked."""
        if not value:
            return value
        if self._config.mask_actor_fields:
            token = TOKENS[MaskCategory.ACTOR]
            if value == token:
                return value                        # already redacted: idempotent, no double count
            counts[MaskCategory.ACTOR.value] = counts.get(MaskCategory.ACTOR.value, 0) + 1
            return token
        return self._text(value, counts)

    def _summary(self, counts: Dict[str, int]) -> MaskingSummary:
        return MaskingSummary(
            employee_name=counts.get(MaskCategory.EMPLOYEE_NAME.value, 0),
            email=counts.get(MaskCategory.EMAIL.value, 0),
            phone=counts.get(MaskCategory.PHONE.value, 0),
            tax_id=counts.get(MaskCategory.TAX_ID.value, 0),
            banking_id=counts.get(MaskCategory.BANKING_ID.value, 0),
            actor=counts.get(MaskCategory.ACTOR.value, 0),
        )
