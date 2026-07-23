# Audit Event — <event id>

<!-- Template (leaf). Scaffolding only — no normative rules, no agent references.
     Field set grounded in ADR-005 / 06 §14 / FR-084–090. The trail is append-only by
     construction; do NOT label it tamper-evident/immutable (deferred to R2, NFR-020). -->

- **Event ID:** <id>
- **Review (cycle) ID:** <cycle_id>
- **Action:** <taxonomy action name>
- **Actor:** <user identity>
- **Timestamp:** <recorded time>
- **Input fingerprint:** <fingerprint>

## Event-specific detail
<!-- Include the block relevant to the action. -->

### If rule run
- Rule-set version: <v> · Config version: <v> · Input fingerprint: <hash>

### If review-local correction
- Source file: <name> · Record/row/txn id: <id or n/a> · Field: <name>
- Original value: <value> · Corrected value: <value>
- Correction reason: <text> · Certification status: <status>
- Governing rule/spec: <ID> · Downstream usage: <where the corrected value is used>

### If AI interaction (Release 2)
- Provider: <name> · Model + version: <v> · Data transmitted: <summary>
- Masking applied: <yes/no + method> · Consent reference: <id> · Prompt category: <cat> · Output: <summary>
