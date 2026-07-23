# Recipe — Architecture Design: 03 Review (independent)

**Layer:** recipe (workflow engine). Delegates to the shared review engine. References recipes/standards; does not invoke agents.
**Phase:** Review.

## Purpose
Independently review the Technical Implementation Plan before coding.

## Required inputs
The Plan; the approved Brief; architecture specs and ADRs.

## Ordered steps
1. Invoke [`review/run-independent-review`](../../review/run-independent-review.recipe.md) with `mode = architecture`, the Plan as `artifact`, the architecture specs/ADRs as `governing_specs`, and [architecture](../../../standards/architecture.md) + [financial-determinism](../../../standards/financial-determinism.md) as `standards`.
2. Run read-only, fresh context, separate from plan generation.
3. Record the verdict.

## Outputs
An Independent Review Report (architecture mode).

## Gate
Only `PASS` (or resolved conditions), then human approval, permits implementation.

## Prohibited behaviors
Plan author issuing the verdict; editing the Plan during review.
