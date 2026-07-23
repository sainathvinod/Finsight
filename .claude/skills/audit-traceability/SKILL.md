---
name: audit-traceability
description: Expertise for FinSight audit events and end-to-end traceability from requirement to test to review result, including correction-event metadata. Describes audit as append-only, never falsely as immutable. Expertise only — recipes own sequencing.
---

# Skill — Audit & Traceability

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Ensure meaningful actions are audited with the required metadata and that work is traceable across the full chain — while describing audit guarantees truthfully.

## When to use
- Designing/verifying audit event emission and its metadata.
- Establishing or checking the requirement → spec → design → implementation → test → review trace.

## When not to use
- Claiming cryptographic tamper-evidence/immutability (deferred to R2 — do not assert it).

## Required inputs
- The action being audited and its context; the approved audit-field definitions.

## Authoritative sources
`specs/adr/ADR-005-audit-event-architecture.md`, `specs/adr/ADR-007-findings-domain-model.md`, `specs/06-architecture.md §14`; `FR-084`–`FR-090`, `NFR-019`–`NFR-023`.

## Capabilities (expertise)
- Specify per-event metadata (actor, timestamp, fingerprint, event-specific detail; rule-run versions; correction lineage; AI-interaction fields in R2).
- Maintain the traceability chain and code/test annotations (`# Implements:` / `# Verifies:`).
- State audit status accurately: append-only by construction, tamper-evidence deferred.

## Standards referenced
[audit-traceability](../../standards/audit-traceability.md), [data-verification](../../standards/data-verification.md), [specification-authority](../../standards/specification-authority.md).

## Templates referenced
[audit-event-template](../../templates/audit-event-template.md).

## Patterns referenced
[audit/audit-event](../../patterns/audit/audit-event.md), [audit/append-only-provenance](../../patterns/audit/append-only-provenance.md).

## Recipes that orchestrate this skill
Composed within [`recipes/data-verification/04-audit-review`](../../recipes/data-verification/) and referenced by governance and testing recipes.

## Outputs
Audit-event specifications and traceability mappings.

## Validation
Required metadata present; trace links resolve; no false immutability claim.

## Escalation
A required audit field or trace link is undefined in `specs/` → **Red Card**, stop.

## Traceability
This skill *is* the traceability discipline; it cites the ADRs/FRs that define each field.
