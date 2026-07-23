# Recipe — Data Verification: 01 Inspect Extraction

**Layer:** recipe (workflow engine). Composes the [data-verification skill](../../skills/data-verification/SKILL.md). References skills/standards; does not invoke agents.
**Phase:** Plan / Execute.

## Purpose
Present extracted source values for user review before any correction or analysis.

## Required inputs
Intake/extracted values for the review.

## Specification references
`specs/06-architecture.md §11`; `FR-026`, `ADR-006`.

## Standards
[data-verification](../../standards/data-verification.md), [audit-traceability](../../standards/audit-traceability.md).

## Ordered steps
1. Display each extracted value with its source reference.
2. Mark values as unverified (not yet usable for analysis).
3. Identify values needing user attention.

## Outputs
An inspection view feeding `02-apply-review-local-correction`.

## Stop conditions / escalation
Source reference missing for a value → **Red Card**.

## Prohibited behaviors
Running analysis on unverified data; altering original values.
