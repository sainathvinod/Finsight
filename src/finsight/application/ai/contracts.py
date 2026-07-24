# AI execution-seam contracts (application layer). These are orchestration contracts — the request a
# provider is asked to complete, and the raw completion it returns — not domain concepts, so they
# live with the application AI services rather than in domain/ai (moved in Phase 4C.2).
# Framework-independent; immutable; no I/O.
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, Optional, Tuple

DEFAULT_PROMPT_VERSION = "v1"
DEFAULT_SCHEMA_VERSION = "v1"


@dataclass(frozen=True)
class PromptRequest:
    """Provider-independent execution request. The PromptBuilder owns HOW each section is composed
    from masked grounding/history; provider adapters serialize this into their own wire format.
    Sections are already-composed, provider-neutral text."""
    system_prompt: str
    context_block: str
    conversation_block: str
    question: str
    output_schema: str
    prompt_version: str = DEFAULT_PROMPT_VERSION
    schema_version: str = DEFAULT_SCHEMA_VERSION


@dataclass(frozen=True)
class RawProviderResponse:
    """Raw, transient provider output. NEVER persisted (ADR-009). Carries the raw text plus
    non-sensitive execution metadata (provider, model, timing/finish reason)."""
    text: str
    provider: str
    model: str
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderStatus:
    """Two orthogonal facts about a provider. `operational` = the adapter is callable. `generation
    _available` = a real generative model will actually answer. NullProvider is operational but NOT
    generation-available. UI generation status and provider selection MUST use `generation_available`
    — never adapter callability alone."""
    operational: bool
    generation_available: bool
    reason: str = ""


# ============================================================================================
# Phase 4C.4 — Response-validation & citation-verification contracts. Data only: no I/O, no provider,
# no persistence, no logging. These are validated application EXECUTION OUTPUTS, not financial-domain
# concepts (Trust > AI: provider output is untrusted until validated here).
# ============================================================================================

CITATION_FORMAT_VERSION = "v1"


def _nonneg_int_or_none(name: str, value) -> None:
    """None = unlimited; 0 and positive ints valid; negatives, booleans, and non-integers raise.
    (bool is rejected explicitly because bool subclasses int in Python.) Mirrors ContextBudget."""
    if value is None:
        return
    if isinstance(value, bool):
        raise ValueError("%s must be an int >= 0 or None, not bool" % name)
    if not isinstance(value, int):
        raise ValueError("%s must be an int >= 0 or None" % name)
    if value < 0:
        raise ValueError("%s must be >= 0 or None" % name)


@dataclass(frozen=True)
class ResponseValidationLimits:
    """Injected response size limits. None = unlimited; 0 and positive ints valid. Production defaults
    are deferred to future composition — nothing is hardcoded here."""
    max_answer_chars: Optional[int] = None
    max_citations: Optional[int] = None
    max_citation_key_chars: Optional[int] = None

    def __post_init__(self):
        _nonneg_int_or_none("max_answer_chars", self.max_answer_chars)
        _nonneg_int_or_none("max_citations", self.max_citations)
        _nonneg_int_or_none("max_citation_key_chars", self.max_citation_key_chars)


@dataclass(frozen=True)
class ValidatedResponse:
    """Structurally + semantically validated provider output. Carries NO raw provider text. The
    citation_keys are verbatim model strings, not yet resolved against grounding."""
    answer_text: str
    unable_to_answer: bool
    citation_keys: Tuple[str, ...]


class CitationNamespace(str, Enum):
    """The five supported citable namespaces. Definition order IS the approved canonical rank
    (finding, run, prov, audit, memory). 'omitted-finding' is intentionally NOT a member — it is
    never a valid citation namespace."""
    FINDING = "finding"
    RUN = "run"
    PROV = "prov"
    AUDIT = "audit"
    MEMORY = "memory"


@dataclass(frozen=True)
class CitationReference:
    """A verified citation: identity only. NO copied evidence, NO snippet, NO masked value — so it
    stays re-resolvable against current deterministic data and is safe for future metadata-only
    journaling (ADR-009/ADR-010)."""
    namespace: CitationNamespace
    identifier: str          # e.g. "F1"; for AUDIT "<action>@<timestamp>"; for PROV the fingerprint
    key: str                 # canonical unbracketed key, e.g. "finding:F1"


@dataclass(frozen=True)
class CitationIndex:
    """The sole authority for what was citable in ONE built turn. Produced by the PromptBuilder from
    the constructed prompt; the verifier consumes it and never re-parses prompt text or re-runs
    context budgeting. valid_keys holds only canonical keys actually present as citable context."""
    valid_keys: FrozenSet[str]
    omitted_finding_ids: FrozenSet[str]
    format_version: str = CITATION_FORMAT_VERSION


class GroundingConfidence(str, Enum):
    """Application-computed grounding STATUS. NOT model self-confidence; does NOT prove factual
    correctness or semantic entailment. v1 has exactly three values — no LOW."""
    UNAVAILABLE = "unavailable"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class AiAnswer:
    """Validated + citation-verified AI output. Contains NO raw provider response, NO prompts, NO
    copied evidence, and NO original masked values. provider/model and the *_version fields are
    non-sensitive metadata, not model-authored financial facts."""
    answer_text: str
    unable_to_answer: bool
    citations: Tuple[CitationReference, ...]
    grounding_confidence: GroundingConfidence
    provider: str
    model: str
    schema_version: str
    prompt_version: str
    masking_policy_version: str
    citation_format_version: str
