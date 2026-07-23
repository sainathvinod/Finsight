# Recipe — Backend Implementation: 05 Remediate

**Layer:** recipe (workflow engine). Composes the [remediation skill](../../../skills/remediation/SKILL.md). References skills/standards/recipes; does not invoke agents.
**Phase:** Remediate.

## Purpose
Correct exactly the defects cited by the code review, then re-validate and re-review.

## Required inputs
The code-review report's cited defects; the affected authorized files.

## Standards
[specification-authority](../../../standards/specification-authority.md), [coding](../../../standards/coding.md), [financial-determinism](../../../standards/financial-determinism.md).

## Ordered steps
1. Map each cited defect to a minimal, in-scope fix.
2. Apply fixes in the authorized files only; add/adjust annotations.
3. Re-run [`03-validate`](03-validate.recipe.md).
4. Return to [`04-review`](04-review.recipe.md) for an independent re-check.

## Outputs
A Remediation Summary + updated diff + re-review verdict.

## Stop conditions / escalation
A fix needs scope expansion, a weakened control, or a human-only decision → **Red Card**, stop. Remediation cannot close its own review.

## Prohibited behaviors
Fixing unrelated code; weakening a test/standard to pass.
