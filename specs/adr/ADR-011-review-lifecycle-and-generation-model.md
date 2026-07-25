# ADR-011 — Review Lifecycle and Generation Model

- **Status:** Accepted · **Date:** 2026-07-25 · accepted as the review-lifecycle architecture (Phase 6.1–6.3)
- **Deciders:** Technical Lead / Software Architect (decided); product owner (approved the Phase 6.0–6.2 reviews and the 15 authoritative product decisions)
- **Feature/plan:** Review lifecycle. Governs how a review's information exists, is trusted, and changes over its lifetime. Preserves ADR-002 (layering), ADR-003 (determinism), ADR-005 (append-only audit), ADR-006 (review cycle / verified dataset), ADR-007 (findings). Records Phase 6.2 invariants as the stable contract.

## 1. Status
Accepted. Establishes the permanent lifecycle invariants and the **generation** concept for reviews. Constrains all future persistence/reconstruction work (ADR-012), export identity (ADR-015), and abandonment/retention (ADR-014).

## 2. Context
FinSight reviews progress CREATED → INTAKE → PROCESSED → VERIFIED → ANALYZED → SUMMARIZED → EXPORTED. The interactive intake artifacts (selected paths, normalized rows, verified dataset) were transient session-only state, making reviews non-resumable and conflating three distinct kinds of information. Phase 6.0/6.1/6.2 established that trust must be bound to *what was certified* (a fingerprint), not to a live file, and that recorded results are immutable historical facts.

## 3. Decision
**Data tiers (single classification for every lifecycle item):**
- **Authoritative (persist):** cycle identity + workflow state; provenance (name, **fingerprint**, period, size, doc_type); rule run (run_id, input fingerprint, ruleset/config/extractor versions); findings; audit (append-only); export artifacts (ADR-015); source binding (ADR-012); generation records.
- **Reconstructed (do not persist; re-derive, fingerprint-verified):** normalized rows; verified dataset; representative preview; readiness detail.
- **Transient (never persist):** UI view/filter/selection, active-review pointer, background workers, caches.

**Generation** is a first-class domain concept: one `verify → analyze → summarize → export` chain, identified by the **verified-source fingerprint** and a per-cycle `sequence_number`. Findings, runs, and exports belong to exactly one generation. Only one generation is *current* per review; others are *superseded*.

**Trust anchor:** trust is bound to the verified-source fingerprint + generation, never to a live path (product decisions 12–14). A finding is trustworthy as a fact about the fingerprint it was analyzed against.

**Invariants (permanent):**
- A finding never exists without a rule run; a rule run never exists without provenance + a fingerprint + versions.
- VERIFIED requires an explicit **human** approval event (actor + timestamp) bound to a verified fingerprint; analysis is gated on VERIFIED.
- AI **explains only** — it never creates or modifies findings, severity, verification, summaries, or exports (Trust > AI); an AI citation requires the finding to exist.
- **No automatic re-verification, re-analysis, supersession, or source mutation** (decision 15). Every consequential transition is human-initiated and audited.
- Supersession is **additive**: a new generation supersedes a prior one; nothing in a prior generation is mutated or deleted. Audit is append-only (ADR-005); "invalidation" is a new superseding event, never an edit.
- Source bytes are never modified by FinSight (immutability).

## 4. Consequences
**Positive:** resumability and correctness rest on reproducibility, not on persisting runtime state; every result is permanently attributable (fingerprint + versions + human actor); shared, immutable history across screens and exports.
**Negative / limitation:** reconstructing derived data requires the source (or a matching fingerprint); when the source diverges, the review is *source-divergent* and a human must act (ADR-012). Introducing generations adds a modest domain concept that all screens must render consistently (ADR-015 §Generation visibility).

## 5. Verification
Enforced by the Phase 6.3 test matrix (illegal-state rejection, generation immutability, no-auto-transition, audit completeness) and by the deterministic engine's existing gating. Implementation is deferred to later phases; this ADR is the contract they are verified against.

## 6. Traceability
Records Phase 6.0–6.2 reviews and product decisions 5–15. Extends ADR-006 (review cycle / verified dataset) with the generation model; anchored by ADR-003 (determinism) and ADR-005 (audit). Implemented by ADR-012 (binding/reconstruction), ADR-014 (abandonment/retention), ADR-015 (export identity). Does not claim authentication, multi-user authorization, encryption-at-rest, or shared-database support (ADR-013).

## 7. Amendment — Generation-State Ownership (Phase 6.3A, 2026-07-25)
The original §3 left analytical progression ambiguous: a cycle at EXPORTED could not truthfully hold a *current* generation at VERIFIED. Corrected model (authoritative):

- **Ownership of analytical state is split (Option C, distinct semantics):**
  - **ReviewGeneration owns the analytical stage** `analytical_state ∈ {VERIFIED, ANALYZED, SUMMARIZED, EXPORTED}`. The forward-gated transition engine (ADR-006) drives the **current** generation's analytical_state. A generation begins **at verification**.
  - **ReviewCycle owns** stable identity (cycle_id, period), `disposition` (Active/Abandoned, ADR-014), `current_generation_id`, and the **pre-generation intake progression of the current candidate source** `intake_stage ∈ {CREATED, SOURCE_BOUND, PROCESSED}` (generation-independent; describes the currently bound+extracted candidate).
  - **`cycles.state` becomes a DERIVED MIRROR** (denormalized, non-authoritative, recomputed): the current generation's analytical_state when a current generation exists, else the intake_stage. Retained only for backward-compatible reads/queries.
- **Product review status is derived** from the current generation (else the intake stage). Historical generations retain their own final analytical_state permanently.
- **Pre-generation intake (Model 1):** CREATED/INTAKE(SOURCE_BOUND)/PROCESSED remain review-level until verification creates a generation. Re-binding a new source after export advances the cycle's intake_stage again for the **new candidate** — this is explicit, audited **forward intake of a new candidate**, not a backward move of any generation.
- **Supersession is append-only, not a rewrite:** modeled as an append-only supersession **relation/event** (prior→successor, actor, timestamp) plus an update of the cycle's `current_generation_id` pointer (a denormalized current-pointer, not a historical fact of the generation). A superseded generation's `analytical_state`, verified_fingerprint, verification metadata, run relationships, findings, and exports are **immutable**; `analytical_state` is mutable **only while the generation is current** (forward progress) and frozen at supersession. Currentness is derivable from the append-only relation.
- **Re-verification-after-export sequence** (canonical; no hidden backward transition): Gen1 EXPORTED/current → source changes (divergent banner; Gen1 still current) → re-bind (intake_stage SOURCE_BOUND) → re-process (PROCESSED) → **re-verify creates Gen2 (VERIFIED, current); Gen1 → EXPORTED, superseded (frozen)** → analyze/summarize/export Gen2. The derived `cycles.state` re-points from "Exported (Gen1)" to "Verified (Gen2)" at re-verification — a consequence of an explicit, audited generation-creation + supersession, with **no** generation moving backward.

Impact: §3 "Generation" and the tier for `cycles.state` are refined as above; all other invariants (human-owned transitions, no auto-supersession, AI explains only, findings⇒run⇒fingerprint) are unchanged. ADR-012 (reconstruction per candidate + per generation), ADR-015 (export currentness derived from the supersession relation) are amended accordingly.
