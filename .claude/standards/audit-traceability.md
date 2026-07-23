# Standard — Audit & Traceability

**Layer:** standard (normative, leaf). Referenced by skills and recipes. References no agents.
**Origin / authority:** `specs/adr/ADR-005-audit-event-architecture.md`; `specs/adr/ADR-007-findings-domain-model.md`; `specs/06-architecture.md §14`; `FR-084`–`FR-090`, `NFR-019`, `NFR-020`, `NFR-022`, `NFR-023`; `F-08-01`, `F-08-04`.

## Audit event metadata

Every audited action records at minimum: **actor identity, timestamp, and an input fingerprint**, plus event-specific detail. In particular:

- **Rule runs** record rule-set version, config version, and input fingerprint.
- **Review-local corrections** record: review identifier, source file, source record/row/transaction identifier (when available), field name, original value, corrected value, correction reason, actor, timestamp, certification status, the governing specification/rule reference, and downstream analysis usage (see [data-verification.md](data-verification.md); `FR-028`, `FR-085`).
- **AI-interaction events** (when the AI layer is built) record provider, model + version, data transmitted, masking applied, consent reference, prompt category, and output (`06 §14`, `NFR-019`, `NFR-022`, `NFR-023`).

The audit taxonomy is **append-only** and versioned from day one (`F-08-01`). The port is `AuditEventPort.emit(cycle_id, action, actor, detail)` (`domain/ports.py`, `infrastructure/audit.py`).

## Truthful status of immutability

**Do not claim cryptographic tamper-evidence or immutability that is not implemented.** Today the audit trail is **append-only by construction**; cryptographic tamper-evidence is **specified but deferred to Release 2** (`06 §14` "tamper-evidence (R2)", `NFR-020`, `F-08-04`, `ADC-09`). Describe it accurately as append-only, not tamper-proof.

## Artifact traceability chain

Maintain the chain: **business requirement → specification → design → implementation → test → review result.** Code annotates `# Implements: <ID>` and tests annotate `# Verifies: <ID>` (see [coding.md](coding.md), [testing.md](testing.md)).

## Escalation

If a required audit field or trace link is undefined in `specs/`, raise a **Red Card** rather than inventing it.
