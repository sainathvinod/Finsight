# ADR-012 — Source Binding and Working-Set Reconstruction

- **Status:** Accepted · **Date:** 2026-07-25 · accepted as the review-lifecycle architecture (Phase 6.1–6.3)
- **Deciders:** Technical Lead / Software Architect (decided); product owner (approved the Phase 6.1 lifecycle and product decisions 13–15)
- **Feature/plan:** Review lifecycle. Defines how intake working data is reconstructed rather than persisted, and how source identity is bound. Preserves ADR-002 (layering), ADR-003 (determinism), ADR-006 (verified dataset). Implements ADR-011.

## 1. Status
Accepted. Replaces the transient, single-copy `ReviewSession.ctx` ownership of intake artifacts with a **cycle-keyed working-set manager** plus a minimal persisted **source binding**. The objective is explicitly **not** to persist the session; it is to make derived data re-derivable and trust anchored to fingerprints.

## 2. Context
Intake artifacts (selected file paths, normalized rows, verified dataset) lived only in a transient `ReviewSession` owned as one mutable slot by the desktop controller. Switching reviews or restarting discarded them, and the workflow then dead-ended (verify/analyze require the in-memory `ctx`). Normalized/verified data is a **deterministic function** of the source bytes (identified by fingerprint) + versioned extractor/rules, so it need not be stored — only re-derived and verified.

## 3. Decision
**Source binding (persist; authoritative for *reconstruction*, not for bytes):** per `(cycle_id, document_type)` record `last_known_path`, `source_fingerprint`, `selected_at`, `actor`. The **path is a reconstruction hint only**; the **fingerprint is the source identity** (decision 14). FinSight never copies or modifies source bytes (immutability) and never persists normalized workbook rows.

**ReviewWorkingSetManager (application layer), keyed by cycle_id:** owns the reconstructed working set (normalized rows, verified dataset, readiness detail, representative preview) in an in-memory cache keyed by cycle. The desktop controller holds only the transient active-review pointer and requests the working set; switching reviews no longer destroys another review's data.

**Reconstruction algorithm (deterministic, fingerprint-verified):** to obtain the working set for a review whose `state ≥ INTAKE`:
1. If cached in-memory → return it.
2. Else, if `state ≥ ANALYZED` and only persisted results are needed (findings/run/summary/export) → no reconstruction required.
3. Else, read the source binding, open `last_known_path`, and **compare the file's fingerprint to the recorded provenance/verified fingerprint**:
   - **Match** → re-extract deterministically; if `state ≥ VERIFIED`, rebuild the verified dataset (approval already recorded). The recomputed verified fingerprint MUST equal the recorded one; if it does not (e.g. extractor-version drift), treat as **divergence** (never silently proceed).
   - **Mismatch / missing / moved-unlocatable** → do not reconstruct; surface a non-destructive recovery (ADR-011 §invariants; recovery states below). Never alter state, verification, or findings.
Reconstruction runs off the UI thread (existing worker pattern); the result is cached for the process lifetime and invalidated on fingerprint mismatch or explicit re-bind.

**Recovery states (surfaced, never auto-reconciled):** *matches* (seamless resume) · *moved with matching fingerprint* (re-bind path, fingerprint unchanged) · *changed / mismatched fingerprint* (source-divergent → require human re-verification) · *missing/deleted* (results viewable as history; re-select to continue) · *legacy review without binding* (prompt re-selection). Extractor-version change is handled as divergence when the recomputed fingerprint no longer matches; ruleset-version change leaves prior findings valid and offers explicit re-analysis (ADR-011).

## 4. Consequences
**Positive:** resumable reviews without persisting runtime state; trust anchored to fingerprints; immutability preserved (only a path + hash are stored). One in-memory copy per cycle, reconstructable on demand.
**Negative / limitation:** reconstruction needs the source; a missing/changed source blocks re-derivation and requires a human decision; a large source re-extracts on resume (mitigated by off-thread reconstruction + caching). Paths may go stale — by design they are hints, not identity.

## 5. Verification
Verified by the Phase 6.3 test matrix: switch-with-active-intake, restart at every state, moved-unchanged, changed, missing, legacy-without-binding, extractor-version mismatch, no normalized-row duplication. Migration is additive (see the Phase 6.3 plan).

## 6. Traceability
Implements ADR-011; preserves ADR-003 (determinism) and ADR-006 (verified dataset). Source binding + working-set are additive to the ADR-004 SQLite store; no deterministic tables change. Anchors decisions 13–15.

## 7. Amendment — Candidate vs Generation (Phase 6.3A, 2026-07-25)
Per ADR-011 §7, reconstruction operates at two levels: (a) the **current candidate** for the cycle's `intake_stage` (re-extract the currently bound source to reach PROCESSED, awaiting verification), and (b) a **generation's verified dataset** (rebuild from the source whose fingerprint equals that generation's `verified_fingerprint`). The "verified fingerprint" referenced in §3 is the **current generation's**. A source change while a generation is EXPORTED puts the review into `source-divergent`; re-verification of the re-processed candidate creates the next generation (never mutates the prior). Legacy cycles whose generation metadata is incomplete (no usable rule-run fingerprint) cannot be reconstructed/re-verified confidently and are labeled "legacy metadata incomplete" (findings retained as history).

Per ADR-011 §8, a **re-analysis** generation (RULESET/CONFIG) **inherits** the verification basis (same `verified_fingerprint` + `extractor_version`): its working set is the **same verified dataset**, reconstructed from the same source@fingerprint — **no re-extraction under a different basis and no re-verification**. Re-analysis re-runs the rules on that verified dataset only. Reconstruction is thus keyed by the generation's (inherited or fresh) `verified_fingerprint`.
