---
name: data-verification
description: Expertise for the review-local data verification workflow — inspecting extracted values, applying review-local corrections with reasons, preserving originals, certifying, and auditing. No source-system write-back. Expertise only — recipes own sequencing.
---

# Skill — Data Verification

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Guide the user workflow that reviews and corrects extracted data before analysis, keeping every correction review-local and fully audited.

## When to use
- Designing or presenting the inspect → correct → certify flow over extracted GED data.
- Ensuring analysis consumes only certified values.

## When not to use
- Writing corrections back to the source system (prohibited).
- Running analysis on unverified data (prohibited).

## Required inputs
- Extracted/intake values for the review; the correction reason from the user.

## Authoritative sources
`specs/adr/ADR-006-review-cycle-and-verified-dataset.md`, `specs/06-architecture.md §11`; `FR-003`, `FR-026`, `FR-028`, `FR-029`, `DEC-027`.

## Capabilities (expertise)
Enforce the approved behavior:
- Original source value stays immutable; corrected value applies only to the current review.
- The source system is never changed; the UI states this and that re-import may reproduce the original issue.
- The user certifies review-local data; analysis then uses the certified value; the user owns certification.
- Every correction creates an auditable event.

## Standards referenced
[data-verification](../../standards/data-verification.md), [audit-traceability](../../standards/audit-traceability.md), [ai-governance](../../standards/ai-governance.md).

## Templates referenced
[audit-event-template](../../templates/audit-event-template.md).

## Patterns referenced
[data-verification/review-local-correction](../../patterns/data-verification/review-local-correction.md), [data-verification/original-vs-corrected](../../patterns/data-verification/original-vs-corrected.md), [backend/verified-dataset-factory](../../patterns/backend/verified-dataset-factory.md).

## Recipes that orchestrate this skill
[`recipes/data-verification/`](../../recipes/data-verification/) — `01-inspect-extraction`, `02-apply-review-local-correction`, `03-certify`, `04-audit-review`.

## Outputs
A certified review-local dataset plus audit events for each correction.

## Validation
Originals immutable; no source write-back; analysis uses certified values; one audit event per correction.

## Escalation
A task appears to require source-system write-back or analysis on unverified data → **Red Card**, stop.

## Traceability
Each correction records the governing rule/spec reference and downstream usage.
