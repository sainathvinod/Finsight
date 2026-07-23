# Standard — Architecture

**Layer:** standard (normative, leaf). Referenced by skills and recipes. References no agents.
**Origin / authority:** `specs/06-architecture.md`; `specs/adr/ADR-002-layering-ports-and-dependency-rules.md`; `.importlinter`; `specs/constitution.md`.

## Layering and dependency direction

1. Preserve the **domain → application → infrastructure → delivery** layering. Dependencies point **inward**; the domain imports nothing outward (`ADR-002`, enforced by `.importlinter` contract *Layered dependency direction* and *C-DOMAIN-INDEP*).
2. Storage details stay in infrastructure: `sqlite3` is forbidden to `finsight.domain`, `finsight.application`, and `finsight.delivery` (`.importlinter` contract *C-DAL-ONLY-STORAGE*). Domain state crosses layers only through **ports** (`domain/ports.py`).

## Deterministic core vs. AI boundary

3. The **deterministic rules engine (C-07) is the system of record** for every financial value, finding, severity, RAG, variance, and reconciliation outcome. AI **explains** results; it never computes, creates, or alters them (see [financial-determinism.md](financial-determinism.md), [ai-governance.md](ai-governance.md)).
4. Findings and financial values are created **only** through the command ports wired to the rules engine (`FindingsCommandPort`); the AI/delivery side holds read-only query ports (`ADR-007`, `06 §7.1`).

## Source-system boundary

5. FinSight is **read-only** with respect to source systems. It never modifies, moves, or deletes source data and performs **no source-system write-back** (`FR-003`, `06 §11.2`, constitution "no GED change"). See [data-verification.md](data-verification.md).

## Provider abstraction

6. AI inference sits behind a **provider adapter interface** — "providers are configuration, not code" (`XP-03`, `FR-104`, `NFR-046`, `06 §19`). Adding or swapping a provider must not change any deterministic component. Concrete provider/model binding is **specified-only and deferred** (`DEC-016`, `ADC-03`); do not assume a concrete provider is present.

## Human approval gates

7. New or changed architecture decisions are **human-only** (constitution §9). Design advances to implementation only after human approval. Delivery/UI technology binding (e.g. desktop shell) is deferred to an ADR (`ADC-01`) and must not be assumed.

## Escalation

If a task cannot be satisfied without violating layering, determinism, the source-system boundary, or provider abstraction — or requires a missing architecture decision — raise a **Red Card** and stop.
