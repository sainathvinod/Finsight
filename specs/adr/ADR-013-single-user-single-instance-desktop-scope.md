# ADR-013 — Single-User / Single-Instance Desktop Scope

- **Status:** Accepted · **Date:** 2026-07-25 · records the authoritative product scope decisions (Phase 6.3)
- **Deciders:** product owner (decided scope); Technical Lead / Software Architect (accepted the technical consequences)
- **Feature/plan:** Application scope. Bounds identity, concurrency, persistence, and AI-availability assumptions for the current FinSight scope. Preserves ADR-004 (SQLite persistence) and ADR-009 (AI persistence/retention limits).

## 1. Status
Accepted. Fixes the operating envelope so lifecycle, persistence, and AI designs are not over-built for capabilities that are explicitly out of scope.

## 2. Context
Prior ADRs left identity/concurrency implicit. The lifecycle work (ADR-011/012) and AI work (ADR-009) need a definite scope: who uses FinSight, how many at once, and whether Ask Fin is required for core review.

## 3. Decision
- **Single-user, local desktop application.** One reviewer per installation. The single-user convention is `local-user`; no login.
- **Out of scope (do not build, do not claim):** multi-user identity, authentication, authorization/permissions, collaboration, and shared-database use. FinSight makes **no** claim of production authentication, multi-user authorization, encryption-at-rest, or shared-database support.
- **SQLite remains the authoritative local persistence store** (ADR-004). Potentially-sensitive data remains synthetic/demo-only until encryption-at-rest exists (ADR-009 limitation, unchanged).
- **Single-instance per database:** only one FinSight application instance may use a given database at a time, enforced by an **advisory single-instance lock** on the database/app-support directory acquired at startup. A second instance targeting the same database is refused with a clear, non-destructive message and does not open or modify the database. The lock is advisory (best-effort OS file lock), scoped to this single-user assumption — not a distributed/multi-writer guarantee.
- **Ollama is required only for Ask Fin.** Core deterministic review (create, upload, process, verify, analyze, findings, summary, export, audit, dashboard) MUST be fully usable with **no** Ollama and **no** AI provider. Ask Fin degrades to a clear "AI unavailable" state (NullProvider) and never blocks or alters deterministic behavior; provider availability is independent of authorization (see ADR-009 and the demo-authorization gate).

## 4. Consequences
**Positive:** a coherent, defensible scope; no speculative auth/multi-user surface; deterministic core independent of AI; safe concurrency posture for a single-writer SQLite store.
**Negative / limitation:** no concurrent/multi-user use; the single-instance lock is advisory (a forced/stale lock may need manual clearing); real sensitive data remains disallowed until encryption-at-rest (ADR-009).

## 5. Verification
Verified by the Phase 6.3 test matrix: second-instance rejection; Ollama-unavailable-while-deterministic-workflow-operational; startup without any AI provider. No new claims of auth/multi-user/encryption are made anywhere in the codebase or docs.

## 6. Traceability
Bounds ADR-011/ADR-012 (lifecycle) and ADR-009/ADR-010 (AI). Preserves ADR-004 (SQLite). Records product decisions 1–5.
