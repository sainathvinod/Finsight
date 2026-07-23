# Recipe — Remediation: 01 Triage

**Layer:** recipe (workflow engine). Composes the [remediation skill](../../skills/remediation/SKILL.md). References skills/standards; does not invoke agents.
**Phase:** Plan.

## Purpose
Interpret a review's cited defects, confirm each is in scope, and order them for repair.

## Required inputs
The originating Independent Review Report (FAIL or conditions) and the artifacts it cites.

## Standards
[specification-authority](../../standards/specification-authority.md).

## Ordered steps
1. List each cited defect with its evidence and the file/artifact it lives in.
2. Confirm each is addressable within the cited scope.
3. Flag any defect that needs a decision beyond the role's authority.

## Outputs
A triaged defect list feeding `02-remediate`.

## Stop conditions / escalation
A defect cannot be fixed without scope expansion or a human-only decision → **Red Card**.

## Prohibited behaviors
Adding defects not cited; broadening scope.
