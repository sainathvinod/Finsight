# Implements: ADR-011 (review lifecycle & generation model), ADR-012 (source binding), ADR-014
# (abandonment/retention), ADR-015 (export identity), Phase 6.3A/6.3B corrections.
#
# Framework-independent lifecycle VALUE TYPES: immutable persistence records + enums. Pure data only.
# No PySide6, no sqlite3, no I/O, no financial logic, no reconstruction. These are the authoritative
# (persisted) lifecycle tier of ADR-011 — the reconstructed/transient tiers are NOT modeled here.
#
# Cross-ROW invariants (same-cycle parent/basis, increasing supersession sequence, one-run-per-
# generation) are enforced at the database/repository layer, which can see other rows; these records
# enforce only pure, SELF-CONTAINED invariants (self-reference, verification-basis honesty).
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CreationReason(str, Enum):
    """Why a generation (one immutable result lineage) was created (ADR-011 §8)."""
    INITIAL_VERIFICATION = "INITIAL_VERIFICATION"          # first human verification of a source
    SOURCE_REVERIFICATION = "SOURCE_REVERIFICATION"        # source changed; NEW human verification
    EXTRACTOR_REVERIFICATION = "EXTRACTOR_REVERIFICATION"  # extractor changed; NEW human verification
    RULESET_REANALYSIS = "RULESET_REANALYSIS"              # same source, new ruleset; NO new verification
    CONFIG_REANALYSIS = "CONFIG_REANALYSIS"                # same source, new config; NO new verification


# Fresh-verification reasons carry their OWN verification metadata (basis = NULL). Re-analysis reasons
# INHERIT the verification basis (basis is required) and must never claim a new verification occurred.
FRESH_VERIFICATION_REASONS = frozenset({
    CreationReason.INITIAL_VERIFICATION,
    CreationReason.SOURCE_REVERIFICATION,
    CreationReason.EXTRACTOR_REVERIFICATION,
})
REANALYSIS_REASONS = frozenset({
    CreationReason.RULESET_REANALYSIS,
    CreationReason.CONFIG_REANALYSIS,
})


class AnalyticalState(str, Enum):
    """A generation's analytical stage (ADR-011 §7). A generation begins at VERIFIED. Mutable only
    while the generation is current (forward progress); frozen at supersession."""
    VERIFIED = "VERIFIED"
    ANALYZED = "ANALYZED"
    SUMMARIZED = "SUMMARIZED"
    EXPORTED = "EXPORTED"


class GenerationDisposition(str, Enum):
    """A working generation may be abandoned before promotion without affecting the published one."""
    ACTIVE = "active"
    ABANDONED = "abandoned"


class IntakeStage(str, Enum):
    """Cycle-level, generation-independent progression of the currently bound+extracted CANDIDATE
    source (ADR-011 §7). Advances forward for a new candidate; never a backward move of a generation."""
    CREATED = "CREATED"
    SOURCE_BOUND = "SOURCE_BOUND"
    PROCESSED = "PROCESSED"


class CycleDisposition(str, Enum):
    """Orthogonal to analytical state (ADR-014). Abandonment is non-destructive and reversible."""
    ACTIVE = "Active"
    ABANDONED = "Abandoned"


# Explicit legacy markers — used by backfill so legacy generations are labeled honestly and NEVER
# carry an invented human name or a fabricated precise timestamp (ADR-011 §7 / Phase 6.3A).
LEGACY_VERIFICATION_ACTOR = "legacy-unknown"
LEGACY_BACKFILL_ACTOR = "legacy-backfill"


def _as_enum(enum_cls, value):
    return value if isinstance(value, enum_cls) else enum_cls(value)


@dataclass(frozen=True)
class SourceBinding:
    """Persisted reconstruction HINT for one authoritative document of a cycle (ADR-012 §3). The
    path is a hint only; the FINGERPRINT is the source identity. Source bytes and normalized rows are
    NEVER stored. One binding per (cycle_id, document_type)."""
    cycle_id: str
    document_type: str
    last_known_path: str
    source_fingerprint: str
    selected_at: str
    actor: str


@dataclass(frozen=True)
class ReviewGeneration:
    """One immutable RESULT LINEAGE (ADR-011 §8): exactly one rule run, its findings, its exports.
    `verified_fingerprint` + `extractor_version` are verification-basis properties (inherited for
    re-analysis); `ruleset_version`/`config_version`/`input_fingerprint` live on the rule run, never
    duplicated here."""
    generation_id: str
    cycle_id: str
    sequence_number: int
    analytical_state: AnalyticalState
    creation_reason: CreationReason
    based_on_generation_id: Optional[str]              # lineage parent
    verification_basis_generation_id: Optional[str]    # inherited-verification source (re-analysis)
    verified_fingerprint: Optional[str]
    extractor_version: Optional[str]
    verification_actor: Optional[str]
    verified_at: Optional[str]
    created_by: str
    created_at: str
    generation_disposition: GenerationDisposition = GenerationDisposition.ACTIVE
    legacy_metadata_incomplete: bool = False

    def __post_init__(self):
        object.__setattr__(self, "analytical_state", _as_enum(AnalyticalState, self.analytical_state))
        object.__setattr__(self, "creation_reason", _as_enum(CreationReason, self.creation_reason))
        object.__setattr__(self, "generation_disposition",
                           _as_enum(GenerationDisposition, self.generation_disposition))
        object.__setattr__(self, "legacy_metadata_incomplete", bool(self.legacy_metadata_incomplete))
        if int(self.sequence_number) < 1:
            raise ValueError("sequence_number must be >= 1")
        gid = self.generation_id
        if self.based_on_generation_id == gid:
            raise ValueError("generation cannot be its own lineage parent")
        if self.verification_basis_generation_id == gid:
            raise ValueError("generation cannot be its own verification basis")
        # Verification-basis honesty (ADR-011 §8): fresh verification carries its own metadata (no
        # basis); re-analysis inherits and MUST identify a basis.
        if self.creation_reason in FRESH_VERIFICATION_REASONS:
            if self.verification_basis_generation_id is not None:
                raise ValueError("fresh-verification generation must not carry a verification basis")
        else:  # re-analysis
            if self.verification_basis_generation_id is None:
                raise ValueError("re-analysis generation must identify a verification basis")


@dataclass(frozen=True)
class GenerationSupersession:
    """Append-only supersession fact (ADR-011 §8): a prior generation is superseded by a successor,
    only inside a successful human promotion. Nothing in the prior generation is mutated or deleted."""
    prior_generation_id: str
    successor_generation_id: str
    superseded_at: str
    actor: str
    reason: str

    def __post_init__(self):
        if self.prior_generation_id == self.successor_generation_id:
            raise ValueError("a generation cannot supersede itself")


@dataclass(frozen=True)
class ExportArtifact:
    """Immutable export identity (ADR-015). The export file/manifest is never rewritten; currentness
    is DERIVED from the cycle's published generation + supersession relation, not a mutable field."""
    export_id: str
    cycle_id: str
    generation_id: str
    run_id: str
    export_path: str
    export_fingerprint: str
    created_at: str
    actor: str
