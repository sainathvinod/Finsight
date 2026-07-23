# ADR-004 — Persistence Strategy (SQLite behind the DAL)

- **Status:** Accepted · **Date:** 2026-07-16 · accepted as part of the project-owner-approved architecture baseline
- **Deciders:** Technical Lead / Software Architect (decided — a technology-binding architecture decision, Constitution §4); Project Owner + data-architect + design-review board (consulted)
- **Feature/plan:** cross-cutting; enables the Walking Skeleton (13); realizes ADC-06

## 1. Status
Accepted as part of the project-owner-approved architecture baseline. **SQLite is a LOCKED decision** (DEC-004, reaffirmed): this ADR records *why* and *how*, not *whether*. It is not reopened absent a material conflict with an approved requirement.

## 2. Context
FinSight is a **single-user, local-first, offline-capable desktop app** on **restricted 8–16 GB corporate laptops** (DEC-008/016, NFR-030). "No database" was always understood as **no database server/infrastructure dependency** (DEC-004). It must never lose verified data, findings, or audit records on crash (NFR-005), must be **transactionally consistent** (NFR-057), must protect data at rest (NFR-009), must be **backed up and restored** on a replacement machine (NFR-060), and must keep **persistence replaceable** so a future web deployment can move to a server database without changing business logic (NFR-072). Only the DAL may touch storage (06 C-17).

## 3. Decision
- **Persistence technology: SQLite (embedded, serverless, single-file), accessed exclusively through a Data Access Layer (DAL) exposing repository interfaces** (the ports of ADR-002). No component other than the DAL touches storage.
- **What SQLite stores:** the Review-Cycle state and artifacts, ingested-file provenance, extracted records + lineage, verification decisions/corrections, the `VerifiedDataset`, rule runs (versions + fingerprints), findings, summary/report history, the **audit event store** (ADR-005), and configuration/version history — all keyed to the review cycle.
- **Amounts are stored as integer minor units or exact-decimal text, never `REAL`** (ADR-003) — the storage-boundary rule that protects determinism.
- **Transactions:** multi-step persistence (completing verification, finishing an analysis) is **all-or-nothing** via SQLite transactions (NFR-057); interrupted operations never leave partial state; the cycle resumes from the last consistent state (NFR-005/006).
- **At-rest protection:** SQLite is not encrypted by default; protection is provided via **SQLCipher (encrypted SQLite) or OS-level protection** — the mechanism is decided in **ADC-08** (deferred; required before real/pilot data, not for a synthetic-data skeleton). Secrets/API keys are **never** stored in the SQLite file; they use platform-secure storage (NFR-010, ADC-08).
- **Backup/restore:** because the store is a **single file**, backup is a consistent copy of the database (e.g., the SQLite backup API / a checkpointed copy) to a user-chosen location, and restore replaces it on the same or a replacement machine (NFR-060/061). Content fingerprints (ADR-005) make "the same data" provable.
- **Future migration:** moving to **PostgreSQL / SQL Server** for the future web deployment is a **new DAL implementation behind the same repository interfaces** — no change to domain/application logic (NFR-072, DEC-004). Schemas and queries live only in the DAL.

## 4. Alternatives Considered
| Alternative | Why not (for the single-user MVP) |
|---|---|
| **Server database now (PostgreSQL/SQL Server)** | Requires infrastructure/install and admin rights — violates DEC-004 (no server dependency) and NFR-030 (restricted env); overkill for single-user. It is the *future web* target, reachable via the DAL. |
| **Plain files (JSON/CSV/Parquet)** | No transactions/ACID → risks partial writes and data loss on crash (fails NFR-005/057); ad-hoc querying for audit/history is weak. |
| **Embedded document store / other embedded engines** | Adds a less-ubiquitous dependency without benefit at this scale; SQLite is the most portable, best-supported, install-free embedded engine and is already in the Python stdlib. |
| **In-memory only** | Loses data on exit — incompatible with multi-month retention (FR-108) and no-data-loss (NFR-005). |

## 5. Consequences
**Positive:** zero-install, offline, single-file store ideal for single-user restricted laptops; ACID transactions give crash-safety and consistency; single-file makes backup/restore trivial; ubiquitous and battle-tested; strong audit/history query support; the DAL keeps it replaceable.
**Negative / limitations (accepted):**
- **Single-writer concurrency** — fine for a single-user desktop; not for multi-user server load (the future web deployment migrates off SQLite via the DAL).
- **No native decimal type** — handled by the integer-minor-units/decimal-text rule (ADR-003); `REAL` is forbidden for money.
- **No encryption by default** — addressed by ADC-08 (SQLCipher or OS-level); not a skeleton blocker on synthetic data.
- **File-level portability caveats** — mitigated by using the SQLite backup API for consistent copies rather than copying a live file.

## 6. Dependencies
- **ADR-002** (repository ports; only the DAL touches storage) · **ADR-003** (no `REAL` for money) · **ADR-005** (audit store persists here) · **ADR-006** (cycle/`VerifiedDataset` persisted transactionally) · **ADC-08** (at-rest/secrets — deferred, pre-pilot).

## 7. Verification Strategy
- **Crash-safety test:** force-kill mid-analysis loses no verified data; the cycle resumes (NFR-005/006).
- **Transaction test:** an interrupted multi-step write leaves no partial state (NFR-057).
- **DAL-only test:** an architecture/import test proves no component outside the DAL imports SQLite/storage types (ADR-002).
- **Backup/restore test:** back up and restore on a fresh install; data and audit intact (NFR-060).
- **Interface-swap test:** a second repository implementation (e.g., in-memory) satisfies the same interfaces — proves substitutability (NFR-072).

## 8. Traceability
- **Serves:** DEC-004 (locked), DEC-008/016. **NFRs:** NFR-005/006/009/010/057/058/060/061/072. **Constitution:** P-14 (auditability persists here), P-15 (config versioning). Realizes **ADC-06**; depends on **ADC-08**.

## 9. Risks
- **At-rest gap until ADC-08** — mitigated by using synthetic data only until ADC-08 is decided (before pilot).
- **Accidental `REAL` for amounts** — mitigated by the ADR-003 lint rule and review.
- **Concurrency assumptions leaking into logic** (blocking future migration) — mitigated by keeping all storage semantics inside the DAL.

## 10. Open Questions (resolved under the approved baseline)
- **ADC-08:** SQLCipher vs. OS-level at-rest protection, and the secrets-storage mechanism (deferred; required before real data). *(AOQ-01)*
- Backup granularity/scheduling beyond manual (R2 polish, F-14-06/07) — not a skeleton concern.
