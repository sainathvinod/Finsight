# Recipe — Remediation: 02 Remediate

**Layer:** recipe (workflow engine). Composes the [remediation skill](../../skills/remediation/SKILL.md). References skills/standards; does not invoke agents.
**Phase:** Generate / Execute.

## Purpose
Apply minimal, in-scope corrections for exactly the triaged defects.

## Required inputs
The triaged defect list; the cited artifacts/files.

## Standards
[specification-authority](../../standards/specification-authority.md), [coding](../../standards/coding.md), [financial-determinism](../../standards/financial-determinism.md), [architecture](../../standards/architecture.md).

## Ordered steps
1. Fix each cited defect with the smallest correct change.
2. Preserve determinism, layering, and traceability.
3. Record residual risk and write the Remediation Summary.

## Outputs
Corrected artifacts + Remediation Summary.

## Stop conditions / escalation
A fix would weaken a control, expand scope, or need a human-only decision → **Red Card**, stop.

## Prohibited behaviors
Weakening a standard/test/requirement to pass; fixing uncited items.
