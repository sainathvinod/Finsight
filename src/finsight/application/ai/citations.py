# Implements: Phase 4C.4, FR-099 (AI answer citation) — CitationVerifier, grounding confidence, and a
# pure AiAnswer factory.
#
# ANSWER-LEVEL citation validity ONLY: every cited key must be well-formed, a supported namespace, and
# present in THIS turn's CitationIndex. This does NOT prove that the surrounding sentence is entailed
# by the cited fact — semantic/claim-level verification would require another model and would violate
# Trust > AI, so it is explicitly out of scope. Citation existence != claim correctness.
#
# Pure, deterministic, provider-independent, side-effect-free. Parsing is case-sensitive; keys are
# never lowercased or repaired. The ONLY normalization is removing exactly one surrounding [..] pair —
# the context-display syntax the prompt shows (e.g. [finding:F1]) — before namespace parsing; the bare
# key is the canonical form. No whitespace stripping, no nested/partial-bracket repair. CitationError
# (non-retryable) carries a NON-SENSITIVE code only — never answer content, raw output, prompts, or
# original values (ADR-009/ADR-010).
from __future__ import annotations
from typing import Tuple

from finsight.application.ai.contracts import (
    CITATION_FORMAT_VERSION, AiAnswer, CitationIndex, CitationNamespace, CitationReference,
    GroundingConfidence, ValidatedResponse,
)
from finsight.application.ai.errors import CitationError

# Approved canonical namespace rank = enum definition order (finding, run, prov, audit, memory).
_NAMESPACE_RANK = {ns: i for i, ns in enumerate(CitationNamespace)}
_NAMESPACE_BY_VALUE = {ns.value: ns for ns in CitationNamespace}


class CitationVerifier:
    """Resolve model-supplied citation keys against ONE turn's CitationIndex. Does not parse prompt
    text, inspect providers, query repositories, re-run PromptBuilder budgeting, copy evidence, or
    mutate inputs. Returns a canonically ordered tuple of verified references, or raises CitationError."""

    def verify(self, validated: ValidatedResponse,
               index: CitationIndex) -> Tuple[CitationReference, ...]:
        if index.format_version != CITATION_FORMAT_VERSION:
            raise CitationError("unsupported citation format version",
                                code="unsupported_citation_format")
        refs = []
        seen = set()
        for key in validated.citation_keys:
            ref = self._parse(key)
            if ref.key in seen:                          # canonical duplicate; never silently deduped
                raise CitationError("duplicate citation", code="duplicate_citation")
            seen.add(ref.key)
            self._resolve(ref, index)
            refs.append(ref)
        # Canonical ordering: approved namespace rank, then identifier. Deterministic regardless of the
        # order the model emitted citations in.
        refs.sort(key=lambda r: (_NAMESPACE_RANK[r.namespace], r.identifier))
        return tuple(refs)

    def _parse(self, key: str) -> CitationReference:
        core = self._strip_one_bracket_pair(key)  # canonicalize [finding:F1] → finding:F1
        if "[" in core or "]" in core:            # nested/partial brackets remain → malformed
            raise CitationError("bracketed citation key", code="malformed_citation")
        if any(ch.isspace() for ch in core):      # e.g. "[ finding:F1 ]", "finding :F1", trailing text
            raise CitationError("citation key contains whitespace", code="malformed_citation")
        if ":" not in core:
            raise CitationError("citation key missing namespace separator", code="malformed_citation")
        ns_str, identifier = core.split(":", 1)   # split on FIRST ':' — an audit timestamp contains ':'
        if identifier == "":
            raise CitationError("citation key has empty identifier", code="malformed_citation")
        ns = _NAMESPACE_BY_VALUE.get(ns_str)      # case-sensitive; 'omitted-finding' is not a member
        if ns is None:
            raise CitationError("unknown citation namespace", code="unknown_namespace")
        return CitationReference(ns, identifier, core)   # canonical bare key

    @staticmethod
    def _strip_one_bracket_pair(key: str) -> str:
        """Remove EXACTLY one surrounding [..] pair (the context-display syntax) if present. No
        whitespace stripping, no lowercasing, no repair — `[[finding:F1]]`, `[ finding:F1 ]`, and
        partial brackets fall through to the strict checks above and are rejected as malformed."""
        if len(key) >= 2 and key[0] == "[" and key[-1] == "]":
            return key[1:-1]
        return key

    def _resolve(self, ref: CitationReference, index: CitationIndex) -> None:
        if ref.key in index.valid_keys:
            return
        if ref.namespace == CitationNamespace.FINDING and ref.identifier in index.omitted_finding_ids:
            raise CitationError("cited a budget-omitted finding", code="omitted_finding_cited")
        raise CitationError("citation not present in current context", code="citation_not_in_context")


def grounding_confidence(*, unable_to_answer: bool, verified_citation_count: int,
                         has_citable_grounding: bool, truncated: bool) -> GroundingConfidence:
    """Deterministic, application-computed grounding STATUS (v1: UNAVAILABLE | MEDIUM | HIGH).

    This measures GROUNDING CONDITIONS only. It is NOT model self-confidence and does NOT prove
    semantic entailment or factual correctness. Invalid or unverified answers must never reach this
    function in the normal flow (validation + verification run first)."""
    if unable_to_answer:
        return GroundingConfidence.UNAVAILABLE
    if not has_citable_grounding or verified_citation_count == 0:
        return GroundingConfidence.UNAVAILABLE
    return GroundingConfidence.MEDIUM if truncated else GroundingConfidence.HIGH


def assemble_ai_answer(*, validated: ValidatedResponse,
                       citations: Tuple[CitationReference, ...],
                       provider: str, model: str,
                       schema_version: str, prompt_version: str, masking_policy_version: str,
                       has_citable_grounding: bool, truncated: bool) -> AiAnswer:
    """Pure factory: pack an ALREADY-validated + ALREADY-verified result into an immutable AiAnswer,
    computing grounding confidence. It performs NO validation, verification, provider call, retry,
    persistence, logging, authorization, grounding, masking, or prompt building — it is NOT an
    orchestrator. Final assembly may alternatively be done by the future AskFinService."""
    confidence = grounding_confidence(
        unable_to_answer=validated.unable_to_answer,
        verified_citation_count=len(citations),
        has_citable_grounding=has_citable_grounding,
        truncated=truncated,
    )
    return AiAnswer(
        answer_text=validated.answer_text,
        unable_to_answer=validated.unable_to_answer,
        citations=citations,
        grounding_confidence=confidence,
        provider=provider,
        model=model,
        schema_version=schema_version,
        prompt_version=prompt_version,
        masking_policy_version=masking_policy_version,
        citation_format_version=CITATION_FORMAT_VERSION,
    )
