# Recipe — Backend Implementation: 04 Review (independent)

**Layer:** recipe (workflow engine). Delegates to the shared review engine. References recipes/standards; does not invoke agents.
**Phase:** Review.

## Purpose
Independently review the backend implementation for plan compliance, scope, determinism, layering, and traceability.

## Required inputs
The implementation diff + Implementation Summary; the approved Plan and allowed-files list.

## Ordered steps
1. Invoke [`review/run-independent-review`](../../review/run-independent-review.recipe.md) with `mode = code`, the diff+summary as `artifact`, the Plan as `governing_specs`, and [coding](../../../standards/coding.md) + [architecture](../../../standards/architecture.md) + [financial-determinism](../../../standards/financial-determinism.md) as `standards`.
2. Run read-only, fresh context, separate from implementation.
3. Record the verdict.

## Outputs
An Independent Review Report (code mode).

## Gate
`PASS` → verification/testing. `FAIL`/conditions → `05-remediate`.

## Prohibited behaviors
Implementer issuing the verdict; editing code during review.
