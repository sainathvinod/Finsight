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

## 8. Amendment — Generation Basis & Promotion Model (Phase 6.3B, 2026-07-25)
§7 still conflated two concepts (a *verified source version* and an *analysis/result set*), and superseded the prior generation at verification (before results existed). Corrected model (authoritative):

**Generation = one immutable RESULT LINEAGE** (exactly one rule run, its findings, its exports). A generation is created explicitly and human-triggered, by one `creation_reason`:
- `INITIAL_VERIFICATION` — first human verification of a source.
- `SOURCE_REVERIFICATION` — the verified source changed; a **new human verification** occurred.
- `EXTRACTOR_REVERIFICATION` — the extractor changed such that the verified dataset must be re-certified; a **new human verification** occurred.
- `RULESET_REANALYSIS` / `CONFIG_REANALYSIS` — the **same** verified source is re-analyzed under a new ruleset/config; **no new human verification occurs**.

**Verification-basis (honesty rule).** Every generation records its verification basis:
`verified_fingerprint`, `verification_actor`, `verified_at`, `verification_basis_generation_id` (nullable), `based_on_generation_id` (lineage parent, nullable), `creation_reason`, `created_by`, `created_at`, `extractor_version`.
- Re-verification reasons: verification metadata is **fresh** (new actor/time); `verification_basis_generation_id = NULL`.
- Re-analysis reasons: verification metadata is **inherited** from the basis generation (same `verified_fingerprint`, **original** actor/time, same `extractor_version`); `verification_basis_generation_id` = the basis. The generation **must never claim a new verification occurred**; audit records "re-analysis initiated (R1→R2 / cfg-1→cfg-2)", not "verification performed". UI/reports show the original verifier + a distinct "re-analyzed by `created_by` on `created_at`" line.
- **Version-field placement:** `verified_fingerprint` + `extractor_version` are **verification-basis** properties → on the **generation** (inherited for re-analysis). `ruleset_version` + `config_version` + `input_fingerprint` are **analysis** properties → on the **rule_run** (each generation has exactly one run). They are not duplicated onto the generation.

**Working vs Published (trust rule).** The cycle carries two pointers:
- `published_generation_id` — the latest **promoted, trusted** result (Dashboard, reports, Ask Fin default).
- `working_generation_id` — the latest **explicitly initiated** work (may equal published, or be a newer in-progress generation).
A newly created generation is **working, not published**. **The prior published generation remains current until an explicit human PROMOTION** succeeds. Promotion is **eligible only once the working generation is `ANALYZED`** (has a rule run + findings) — never a `VERIFIED`-only generation. **Promotion point = explicit human promotion gated ≥ ANALYZED**, justified by financial-review practice: a published result must be (1) trustworthy — deterministic findings must exist; and (2) replaced only by a human decision — you never silently swap the numbers leadership relies on; export is a downstream artifact, not the definition of "current trusted results". **Exception:** the **first** generation of a review (no prior published) **auto-publishes at ANALYZED** — there is no prior trusted result to protect and a promotion step would be empty ceremony.

**Supersession is atomic at promotion.** Superseding the prior published generation happens **only inside the successful promotion transaction** (append-only supersession record `prior→successor` with `reason`; move `published_generation_id`; audit). If generation creation, reconstruction, analysis, findings persistence, or export fail, **promotion never runs and the prior published generation is untouched**. This removes the §7 hazard of a completed generation being superseded before its replacement is complete. A working generation may be **abandoned** (generation-level disposition) before promotion without ever affecting the published one.

**Ask Fin grounding.** Ask Fin grounds on the **published** generation by default; if none exists, it states there are no analyzed results to explain (never grounds a `VERIFIED`-only generation). The user may explicitly ground on the **working** generation only when it is `ANALYZED+`. One answer grounds on exactly one generation, stated in the answer — never mixed generations.

This supersedes §7 where they differ (single "current" pointer → split working/published; supersession-at-verification → supersession-at-promotion). All other §7 invariants stand.

## 9. Amendment — Derived-Mirror vs Trusted-Output Resolution (Phase 6.4cB clarification, authoritative)
Phase 6.4cB surfaced a genuine §7-vs-§8 ambiguity (independent architect RED CARD): §7's canonical example re-points `cycles.state` to "Verified (Gen2)" at re-verification (mirror → **working**), while §8/ADR-015 §7 make "current" for reports/exports the **published** generation; §8's "supersedes §7 where they differ" enumerated only two items and never restated what the derived mirror reflects. The following product+architecture decision is **authoritative and closes the ambiguity**:

**When `working_generation_id` and `published_generation_id` differ:**
- **`cycles.state` reflects the WORKING generation's workflow progress** (the reviewer's in-progress activity).
- **Trusted product outputs — Dashboard trusted metrics, reports, exports, and Ask Fin — use the PUBLISHED generation until explicit promotion.**
- **Workflow progress and trusted-output status are distinct concepts.** A working generation may show that review work is in progress while published financial results remain unchanged.
- **UI surfaces must clearly distinguish "work in progress" (working) from "published trusted results."**
- **No working data may silently replace or contaminate published output.**
- **Promotion is the only operation that changes the trusted published generation.**

This **supersedes** §7's canonical example where it re-points the mirror to the working generation for the trusted-output surfaces, and **clarifies** §8's working/published split. All other §7/§8 invariants stand. For a **single-generation** review (the R1 common case — second-generation source replacement / re-verification is **R2**, DEC-023) `working == published` after the first-generation auto-publish at ANALYZED, so the mirror and trusted output coincide and this amendment is a no-op. This decision must not be reopened or reinterpreted during implementation.
