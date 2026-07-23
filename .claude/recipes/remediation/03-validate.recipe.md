# Recipe — Remediation: 03 Validate

**Layer:** recipe (workflow engine). Composes the [remediation](../../skills/remediation/SKILL.md) and [testing](../../skills/testing/SKILL.md) skills. References skills/standards; does not invoke agents.
**Phase:** Validate.

## Purpose
Re-run the checks the defect touched to confirm the fix holds and introduces no regression.

## Required inputs
The corrected artifacts; the originating defects.

## Standards
[testing](../../standards/testing.md), [coding](../../standards/coding.md), [financial-determinism](../../standards/financial-determinism.md).

## Ordered steps
1. Re-run the relevant checks (`ruff`, `lint-imports`, `pytest` markers).
2. Confirm each cited defect is resolved.
3. Confirm no new failure was introduced.

## Outputs
Re-validation evidence appended to the Remediation Summary.

## Stop conditions / escalation
A defect remains or a regression appears → report accurately; do not mark resolved.

## Prohibited behaviors
Weakening a gate to pass; claiming resolution without evidence.
