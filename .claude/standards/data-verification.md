# Standard — Data Verification (review-local correction)

**Layer:** standard (normative, leaf). Referenced by skills and recipes. References no agents.
**Origin / authority:** `specs/adr/ADR-006-review-cycle-and-verified-dataset.md`; `specs/06-architecture.md §11`; `FR-003`, `FR-026`, `FR-028`, `FR-029`, `NFR-008`, `NFR-056`; `TB-01`, `TB-02`, `P-9`, `P-10`, `ADC-10`.

## Rule

1. **Original value is immutable.** The extracted source value is never overwritten. A correction is an **additive** layer that preserves original value, corrected value, actor, timestamp, and reason in lineage (`AP-05`, `06 §11.2`, `FR-028`, `NFR-056`, `TB-01`).
2. **Corrections are review-local.** A corrected value applies **only** within the FinSight review that created it. There is **no source-system write-back** — FinSight never updates, moves, or deletes source data (`FR-003`, `TB-01`, `P-10`).
3. **The UI must state the boundary.** The interface makes clear that a correction does not update the source system, and that re-importing unchanged source data may reproduce the original issue (`06 §6.2`, `06 §11.2`, `NFR-008`).
4. **Certification precedes analysis.** No analysis runs on unverified data. Verification is gated per document (approve / approve-with-corrections / reject) with an explicit "I have reviewed this information" confirmation (`FR-026`, `FR-029`, `DEC-027`, `P-9`, `TB-02`, `ASR-03`).
5. **Certified data is the only analysis input.** The `VerifiedDataset` — constructible only via verification — is the sole input to the rules engine (`glossary`, `06 §11.1`, `ADC-10`; enforced by `tests/fitness/`).
6. **Re-import is idempotent.** Replacing a document or re-running returns the affected artifact to its earliest affected state and re-runs forward without duplicate findings (`06 §6.2`, `NFR-008`).
7. **Every correction is audited.** Each verification/correction action emits an audit event (see [audit-traceability.md](audit-traceability.md); `FR-028`, `FR-085`).

## Escalation

Do not introduce source-system write-back, update events, or correction notifications. If a task appears to require them, raise a **Red Card** — that is deferred/unapproved scope.
