# ADR-006 — Review Cycle & VerifiedDataset Model

- **Status:** Accepted · **Date:** 2026-07-16 · accepted as part of the project-owner-approved architecture baseline
- **Deciders:** Software Architect (decided); design-review board (consulted) — Constitution §4
- **Feature/plan:** cross-cutting; enables the Walking Skeleton (13); realizes ADC-10

## 1. Status
Accepted as part of the project-owner-approved architecture baseline. Binds the Review-Cycle aggregate and the `VerifiedDataset` so **verification-before-analysis is enforced by construction** (P-9, FR-026, TB-02), realizing 06 §6/§11.

## 2. Context
The Review Cycle is FinSight's organizing aggregate (AP-04, P-16): a month/year cycle owns the review's state and artifacts, is resumable across restarts (NFR-006), and must make "analyzed-but-unverified" **impossible** (FR-026). A review runs on a *set* of documents that are individually intaken, verified, and analyzed while the cycle is in progress, so the state model cannot be a single flat track (06 §6.2). The guided wizard (07) is the user-facing projection of this model.

## 3. Decision
- **Review-Cycle aggregate**, identified by **(Month, Year)** for the single-department scope (A-11), owns: identity/metadata, pipeline state, and all cycle-keyed artifacts (files, extracted data + lineage, readiness, verification decisions, `VerifiedDataset`, rule runs, findings, summary, exports, audit). Persisted transactionally via the DAL (ADR-004).
- **Two orthogonal state regions (Harel-style), not one flat FSM:**
  - **Per-artifact:** `Ingested → Extracted → (Quarantined | Ready) → Verified → Analyzed`.
  - **Cycle (a projection over artifacts):** `Open → In progress → Summarized → Exported → Closed`, plus the continuously-recomputed readiness map (06 §10).
- **`VerifiedDataset` — the gate, by construction.** The Rules Engine (C-07) accepts **only** a `VerifiedDataset` value. Because the core is Python (no compile-time access control), "only C-06 can produce one" is enforced concretely: `VerifiedDataset` is a **frozen type with no public constructor**, created by a **single module-private factory owned by C-06** on recording a per-document human approval, with a **runtime guard** that raises if construction is attempted elsewhere, and a **CI test** asserting no other module can obtain one. So "run a rule on unverified data" is not a guarded path but an **effectively absent** one — enforced by construction + CI, not by discipline and not by the compiler. Verification is **per document/dataset**, so available capabilities analyze verified inputs while other documents are still being verified (aligns with readiness proceeding on a subset).
- **Corrections are additive:** a correction preserves the original value, the corrected value, and user + timestamp in lineage (FR-028, ADR-007/ADR-004); the raw source is never mutated (P-5-adjacent, NFR-056).
- **Resumable & crash-safe:** the cycle persists at each transition; a force-kill loses no verified data and resumes from the last consistent state (NFR-005/006).
- **Idempotent re-run:** re-analyzing the same `VerifiedDataset` + configuration version yields the identical result set, no duplicates (NFR-008); re-entry (corrected file) returns the affected artifact to the earliest affected state and re-runs forward.
- **Verified runs are versioned & fingerprinted** (ADR-003/005) for replay (F-02-06).

## 4. Alternatives Considered
| Alternative | Why not |
|---|---|
| A boolean `is_verified` flag checked at analysis time | A guarded path is bypassable and after-the-fact; the type-level constructor makes the illegal state unrepresentable (stronger, per NFR-047). |
| A single flat cycle FSM | Cannot represent "GED verified & analyzed while Budget still unverified" — contradicts per-document verification and readiness-on-a-subset (06 §6.2). |
| Mutate source/extracted values on correction | Destroys lineage/evidence (NFR-056); corrections must be additive layers. |
| No cycle aggregate (loose state) | Loses the review-cycle organizing model (AP-04/P-16) and resumability guarantees. |

## 5. Consequences
**Positive:** the verification gate is enforced by construction + CI (frozen `VerifiedDataset`, module-private C-06 factory, runtime guard, fitness test) rather than by discipline — as strong as Python allows; the model matches the multi-document reality and the wizard; resumable and idempotent; replayable.
**Negative (accepted):** a `VerifiedDataset` type + per-artifact state machine is more up-front modeling than a flag; orthogonal regions require care (mitigated by explicit state tests).

## 6. Dependencies
- **ADR-002** (`VerifiedDataset` as the engine's only input; core independence) · **ADR-004** (transactional persistence, resumability) · **ADR-005** (transition events) · **ADR-003** (versioned/fingerprinted runs) · **ADR-007** (findings produced from the run).

## 7. Verification Strategy
- **Gate-by-construction test:** the Rules Engine has no entry accepting anything but a `VerifiedDataset`; a test asserts a `VerifiedDataset` cannot be constructed outside C-06's factory (the runtime guard raises), so there is no path from unverified data to a rule (integration + guard test).
- **State-machine tests:** illegal states/transitions are unrepresentable; per-artifact verification while the cycle is in progress works.
- **Crash/resume test:** force-kill mid-thread → no lost verified data, resume (NFR-005/006).
- **Idempotency test:** re-run yields identical results, no duplicate findings (NFR-008).
- **Correction-lineage test:** a correction preserves the original and is visible in lineage (FR-028).

## 8. Traceability
- **Serves:** FR-006 (cycle), FR-026–029 (verification), AP-03/04, TB-02, P-9/P-16. **NFRs:** NFR-005/006/008/056; NFR-022 (versioning). Realizes **ADC-10**.

## 9. Risks
- **Gate implemented as a flag by mistake** — mitigated by the gate-by-construction test (WS-8 in 13).
- **Orthogonal-region complexity** — mitigated by explicit state tests and keeping the skeleton to two documents.

## 10. Open Questions (resolved under the approved baseline)
- **OQ-6** (personas: leader/delegate/both) shapes verification UX detail, not the model — non-blocking. Multi-department scope (A-11) is future; the aggregate key allows it without redesign.
