# Pattern — Append-Only Provenance (not tamper-evident yet)

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [audit-traceability.md](../../standards/audit-traceability.md); `06 §14`; `NFR-020`; `F-08-04`.

## Convention
The audit trail is written **append-only**: events are added, never edited or deleted in place. Provenance (who/when/what version/what input fingerprint) travels with each event.

## Truthful status
Cryptographic **tamper-evidence is specified but deferred to Release 2** (`06 §14` "tamper-evidence (R2)"). Describe the trail as *append-only by construction*, **not** as immutable or tamper-proof. Do not claim guarantees the code does not provide.

## Checks
- No update/delete paths against audit records.
- Documentation and UI language say "append-only", never "immutable/tamper-proof", until R2 lands.
