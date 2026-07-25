# ADR-015 — Immutable Export and Report Identity

- **Status:** Accepted · **Date:** 2026-07-25 · records the export-identity architecture (Phase 6.3)
- **Deciders:** Technical Lead / Software Architect (decided); product owner (approved report immutability and generation visibility)
- **Feature/plan:** Review lifecycle / reporting. Defines the immutable export manifest and how generation identity appears across the product. Preserves ADR-003 (determinism), ADR-005 (audit). Implements ADR-011; consumes ADR-012 fingerprints.

## 1. Status
Accepted. Establishes that every export is an immutable, fully-identified artifact and that generation identity is consistently visible across screens.

## 2. Context
Exports and leadership summaries may be shared outside FinSight. A distributed financial artifact must forever mean what it said when generated; a later generation must never retroactively change it. Reviewers must always know **which generation** grounds what they see.

## 3. Decision
- **Exports are immutable** (decision 11). Each export is a snapshot of one generation, recorded in an `export_artifacts` record and never overwritten. A later generation produces a **new** export that **supersedes** the prior one; the prior export remains valid history, labeled superseded (never mutated or deleted).
- **Export manifest — every export must identify:** review/cycle id; human-readable review period; **generation id + sequence_number**; **verified-source fingerprint**; rule **run id**; **ruleset version**; **configuration version**; **extractor version**; export **timestamp**; export **fingerprint** (content hash of the package); and **current/superseded status at creation**. The manifest is embedded in the export content and its identity persisted in `export_artifacts`.
- **Report philosophy (facts only, ADR-011/6.2):** reports state what was analyzed, against which fingerprint, under which versions, whether the current bound source matches, and whether the findings belong to the current or a superseded generation. Reports never speculate, assign blame, or infer causality; a superseded report is labeled with a reference to its successor.
- **Generation visibility (restrained):** Overview identifies the **current** generation; Findings identifies the generation being displayed and labels superseded ones; Ask Fin states which generation grounds its answer (grounding is generation-scoped); Audit events identify generation-changing actions; exports carry the full manifest. **Raw fingerprints stay secondary** (details/tooltips), surfaced prominently only for recovery/divergence — screens are not overloaded with hashes.

## 4. Consequences
**Positive:** shared artifacts are permanent, self-describing, and reproducible; every screen agrees on which generation is authoritative; supersession is transparent and non-destructive.
**Negative / limitation:** export artifacts and superseded generations accumulate (retention by design); the UI must consistently render generation identity (a modest, shared presentation concern).

## 5. Verification
Verified by the Phase 6.3 test matrix: export-manifest consistency; prior-export immutability across supersession; generation visibility on Overview/Findings/Ask Fin/Audit/exports; no later generation overwrites a prior export.

## 6. Traceability
Implements ADR-011; consumes ADR-012 (fingerprints/generation). Preserves ADR-003 (determinism) and ADR-005 (audit). Records product decisions 11–14. Export retention aligns with ADR-014.

## 7. Amendment — Currentness Derivation (Phase 6.3A, 2026-07-25)
Per ADR-011 §7, an export belongs to a generation whose analytical_state is EXPORTED. The manifest's "current/superseded status at creation" is a snapshot; **live** currentness is derived from the append-only supersession relation (not by rewriting the export artifact). When a later generation supersedes, the prior `export_artifacts` row is marked superseded via the supersession record and the cycle's current-generation pointer — the export **file/manifest is never rewritten**. The review-level status shown alongside an export is derived from the current generation (ADR-011 §7). Legacy exports lacking full version/fingerprint metadata are labeled honestly ("legacy metadata incomplete"), never fabricated.

Per ADR-011 §8, "current" for reports/exports means the **published** generation. An export produced from a **working** (not-yet-promoted) generation is labeled "working — unpublished" and does not supersede the published export; supersession of the prior published export occurs **atomically at promotion** (never at verification or at working-generation export). The manifest additionally records the generation's `creation_reason` and, for a re-analysis generation, both the **original verification** (actor/time/fingerprint, inherited) and the **re-analysis initiator** (`created_by`/`created_at`) — the report must not present a re-analysis as a fresh verification.
