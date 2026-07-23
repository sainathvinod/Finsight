# ADR-009 — AI Platform Persistence, Retention, and Data Classification

- **Status:** Accepted · **Date:** 2026-07-23 · accepted as part of the authorized AI Platform build (Phase 4B)
- **Deciders:** Technical Lead / Software Architect (decided); product owner (approved the AI Platform roadmap)
- **Feature/plan:** AI Platform (Phase 4). Governs the persistence introduced by migration `0002_ai_platform`. Preserves ADR-002 layering, ADR-005 audit, and the deterministic engine as the sole source of truth.

## 1. Status
Accepted. Establishes how AI conversations, review memory, preferences, and the AI interaction journal are persisted and retained, and records a hard limitation until encryption-at-rest exists.

## 2. Context
The AI Platform explains what the deterministic engine decided. It persists conversations and human-controlled review memory to support a multi-turn assistant. Conversation content and review memory may quote verified financial facts and are therefore **potentially sensitive**. FinSight has no encryption-at-rest yet (ADR-004 requires it before real data).

## 3. Decision
- **Data classification:** persisted conversation content and review memory are treated as potentially sensitive financial data.
- **Retention:** conversations persist until explicitly deleted (default `retention_policy = "keep"`; no automatic expiry in this phase). Message persistence is gated by a per-user `conversation_persistence` preference (default enabled); when disabled, message **content is not stored**. Deleting a conversation removes its messages transactionally (FK `ON DELETE CASCADE`); clearing removes only messages and preserves the conversation record; forgetting review memory removes only the exact `(user_id, cycle_id)` scope.
- **Human-controlled memory:** durable review memory is **never** written from model output. Entries are created only via explicit application commands and carry provenance — `human_authored` (actor + timestamp) or `system_derived` (must reference a deterministic `source_type`/`source_id`). No model-authored or model-selected memory; no automatic summarization.
- **AI interaction journal (`ai_interactions`):** operational traceability — append + read only, no update/delete in the application port. It is **distinct** from the deterministic financial audit trail (ADR-005) and from application diagnostic logs. It stores approved non-sensitive metadata only: **no full prompts, no raw messages, no raw financial rows.** It is **not** cryptographically tamper-evident.
- **No secrets in SQLite:** no provider credentials, secrets, raw workbook rows, or source workbooks are stored.
- **Scope isolation:** every AI record is keyed by `user_id` (and `cycle_id` where applicable); all reads/writes filter by scope. No leakage across reviews, users, or future workspaces.

## 4. Consequences
**Positive:** a real, scoped, retention-aware persistence foundation for Ask Fin; human accountability for durable memory; clean separation from the financial audit trail.
**Negative / limitation (accepted, and enforced in code comments + this ADR):** **AI persistence must NOT be used with real sensitive data until encryption-at-rest is implemented.** Until then, synthetic/demo use only. Encryption-at-rest and identity/authorization are deferred to their own phases.

## 5. Verification
Migration `0002` is additive/idempotent (tests: fresh, upgrade-from-0001, repeat, FK cascade, deterministic tables unchanged). Isolation, retention, provenance, and non-mutation are covered by tests. `application/ai` imports no `sqlite3`/PySide6/deterministic-command modules; the deterministic engine does not depend on AI.

## 6. Traceability
Extends the persistence architecture (ADR-004); distinct from ADR-005 (financial audit). Provider abstraction, prompt construction, grounding retrieval, masking, and the response contract are **out of scope** here and deferred to Phase 4C+.
