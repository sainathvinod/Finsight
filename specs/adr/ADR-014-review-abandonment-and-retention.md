# ADR-014 — Review Abandonment and Retention

- **Status:** Accepted · **Date:** 2026-07-25 · records the approved abandonment/retention policy (Phase 6.3)
- **Deciders:** product owner (decided policy); Technical Lead / Software Architect (accepted the model)
- **Feature/plan:** Review lifecycle. Defines how reviews end, age, and are retained. Preserves ADR-003 (determinism), ADR-005 (append-only audit), ADR-006 (review cycle). Implements ADR-011.

## 1. Status
Accepted. Establishes non-destructive abandonment, age-based reminders (no expiry), and deletion restrictions.

## 2. Context
Reviews may sit incomplete for long periods. Enterprise correctness forbids automatic state changes, silent expiry, or data loss. A review must be endable by an explicit human choice, auditable and reversible-as-history.

## 3. Decision
- **Abandonment is a separate lifecycle status, NOT a linear analytical state.** The CREATED→…→EXPORTED progression (ADR-006) is analytical and must retain valid semantics; abandonment is an orthogonal disposition (e.g. `Active | Abandoned`) applied to a cycle at any point, recorded via an **append-only lifecycle audit event** ("review abandoned", actor + timestamp). It does not alter the analytical state, verification, findings, or generations.
- **Non-destructive:** abandonment deletes nothing. All authoritative data (state, provenance, generations, findings, audit, exports) is retained. A reviewer may **resume** an abandoned review (an audited "review resumed" event restores `Active`); nothing was lost.
- **No automatic expiry:** reviews never expire, change state, invalidate verification, or lose data because of age (decisions 6–8). Age drives **informational reminders only**.
- **Inactivity is derived, deterministic, informational.** Computed from the latest **meaningful** audit event (see below) versus the current wall clock: `< 30 days` — no message; `30–59 days` — a secondary "Inactive for N days" indicator; `≥ 60 days` — a non-blocking "This review has been inactive for N days. Continue or mark it abandoned." with explicit choices. No automatic transition, deletion, or verification change.
- **Meaningful activity** = analytical/lifecycle audit events (created, source bound/re-bound, verification performed, analysis performed, summary generated, export generated, abandoned, resumed). It **excludes** operational/diagnostic events (review resumed-as-reconstruction, navigation, provider status, Ask Fin questions) so a divergence check or a glance does not reset the clock.
- **Deletion restrictions:** meaningful reviews (those past CREATED, or carrying findings/exports/generations) are **archived/abandoned, not permanently deleted** through the ordinary UI. Hard deletion is not an ordinary-UI operation. (An empty, never-progressed CREATED review with no artifacts may be discarded; that is not a "meaningful" review.)
- **Reports/exports are immutable** and are retained regardless of abandonment (ADR-015).

## 4. Consequences
**Positive:** no silent data loss or expiry; explicit, audited, reversible end-of-life; deterministic, honest age signalling; complete history preserved.
**Negative / limitation:** abandoned reviews accumulate (retention by design); there is no ordinary-UI hard-delete (deliberate — protects meaningful financial records).

## 5. Verification
Verified by the Phase 6.3 test matrix: abandon/resume (audited, non-destructive); long-running reminder at 30/60-day thresholds with deterministic activity calculation; delete-meaningful-review restriction; abandonment does not alter analytical state/verification/findings.

## 6. Traceability
Implements ADR-011; preserves ADR-005 (append-only audit) and ADR-006 (review cycle). Records product decisions 6–10. Export retention per ADR-015.
