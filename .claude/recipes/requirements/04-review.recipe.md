# Recipe — Requirements: 04 Review (independent)

**Layer:** recipe (workflow engine). Delegates to the shared review engine. References recipes/skills/standards; does not invoke agents.
**Phase:** Review.

## Purpose
Independently review the Implementation Brief before any design work begins.

## Required inputs
The Implementation Brief; the approved task and referenced `specs/` items.

## Ordered steps
1. Invoke [`review/run-independent-review`](../review/run-independent-review.recipe.md) with `mode = requirements`, the Brief as `artifact`, the referenced specs as `governing_specs`, and [specification-authority](../../standards/specification-authority.md) + [ai-governance](../../standards/ai-governance.md) as `standards`.
2. Ensure it runs read-only, in a fresh context, separate from Brief generation.
3. Record the verdict.

## Outputs
An Independent Review Report (requirements mode) with `PASS / PASS WITH CONDITIONS / FAIL / BLOCKED`.

## Gate
Only a `PASS` (or resolved conditions) permits handoff to architecture design — and only after human approval.

## Prohibited behaviors
The Brief's author issuing the verdict; editing the Brief during review.
