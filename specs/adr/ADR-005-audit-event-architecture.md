# ADR-005 — Audit Event Architecture

- **Status:** Accepted · **Date:** 2026-07-16 · accepted as part of the project-owner-approved architecture baseline
- **Deciders:** Software Architect + data-architect (decided); design-review board (consulted) — Constitution §4
- **Feature/plan:** cross-cutting; enables the Walking Skeleton (13); realizes ADC-09

## 1. Status
Accepted as part of the project-owner-approved architecture baseline. Binds how auditability-by-construction (P-14, E-08) is realized so any month's review is reconstructable from the trail alone (NFR-019).

## 2. Context
Every material action must be recorded attributably and reconstructably (NFR-019); findings must be explainable by the rule-set and configuration versions in force (NFR-022); AI interactions and consents must be logged (FR-087/088); diagnostic logs must be separate and carry no sensitive values (NFR-053). Audit is **infrastructure**, and per-feature logging is a **Definition-of-Done** clause (03 §4). The core must stay headless-testable, so it cannot depend outward on the audit store (ADR-002).

## 3. Decision
- **Core-owned `AuditEventPort`.** The domain/application code **emits events through the port** (defined in the core); the **audit store (C-14) implements it in infrastructure** and persists to SQLite via the DAL (ADR-004). The core imports no audit-store type (dependency inversion, ADR-002); a test supplies a no-op/in-memory port.
- **Append-only, versioned event schema (v1, evolvable).** Every event carries: event type, actor (the local OS user — DEC-008), timestamp (recorded at the edge, ADR-003), a content fingerprint where applicable (NFR-058), the schema version, and event-specific detail. Events are **append-only** — never updated or deleted.
- **Event taxonomy (derived strictly from FR-084–089; nothing speculative):** ingestion/access/classification/period-assignment; extraction/quarantine; corrections (original + corrected); verification decisions; **rule runs** (rule-set version + configuration version + input fingerprint); configuration/rule changes; **AI interactions** (provider/model/version, data transmitted, masking applied, consent reference, prompt category, output); **consent** grants/revocations; report generation; exports.
- **Provenance of truth:** each finding/report references the rule-set and configuration versions in force (NFR-022, ADR-006/007), so any historical output is explainable.
- **Separation from diagnostics (NFR-053):** operational/technical logs are a **distinct channel** and **never contain sensitive financial values**; they are not the audit trail.
- **Reconstruction surface:** a **cycle-timeline** query over the audit store reconstructs "who did what, which rules/config ran, what was produced" for a review (E-08 / F-08-02).
- **Tamper-evidence: deferred (R2).** Detectability of alteration/deletion (NFR-020) is a later feature (ADC-09 full / F-08-04); the append-only v1 schema is designed so tamper-evidence can be added without reshaping events.

## 4. Alternatives Considered
| Alternative | Why not |
|---|---|
| Components write to the audit store directly | Core would depend outward on infrastructure — breaks headless-core independence (ADR-002/NFR-070). |
| Reuse the diagnostic logger for audit | Conflates governance audit with technical logs; risks sensitive values in diagnostics (NFR-053). |
| Derive audit from DB triggers only | Opaque, technology-coupled, and misses non-DB actions (AI interactions, consents, exports). |
| Unversioned event schema | The earliest-decided, most-expensive-to-change artifact (06 AR-06); versioning from v1 is the mitigation. |

## 5. Consequences
**Positive:** the core stays headless-testable; every material action is captured uniformly; provenance makes findings explainable; the schema can evolve and later gain tamper-evidence.
**Negative (accepted):** every action must emit through the port (a DoD discipline, enforced per story); an append-only store grows over time (bounded by single-department volumes and multi-month retention — acceptable, A-08/FR-108).

## 6. Dependencies
- **ADR-002** (the port; dependency inversion) · **ADR-004** (SQLite store; retention) · **ADR-003** (edge timestamps, fingerprints) · **ADR-006/007** (run/config versions referenced by events).

## 7. Verification Strategy
- **Audit-completeness test:** every skeleton step (setup, upload, validation, extraction, verification, analysis, finding, summary, export, each AI interaction) emits an event.
- **Reconstruction test:** the cycle-timeline query reproduces the full review from events alone (E-08 signal).
- **Headless test:** the core runs with a no-op `AuditEventPort` (proves inversion).
- **Separation test:** diagnostic logs contain no sensitive financial values (NFR-053).

## 8. Traceability
- **Serves:** E-08, P-14. **FRs:** FR-084–089, FR-107 (config history). **NFRs:** NFR-019/022/023/052/053/058; NFR-020 (deferred). Realizes **ADC-09**.

## 9. Risks
- **A step that forgets to emit** — mitigated by the DoD clause + audit-completeness test as a merge gate.
- **Sensitive values leaking into diagnostics** — mitigated by the separation test and review.

## 10. Open Questions (resolved under the approved baseline)
- **NFR-020 tamper-evidence** approach (hash-chain / signing) — deferred to ADC-09 full / R2 (AOQ-06); the v1 schema must not preclude it.
