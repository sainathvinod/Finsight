# Recipe — UI Shell Implementation: 04 Review (independent)

**Layer:** recipe (workflow engine). Delegates to the shared review engine. References recipes/standards; does not invoke agents.
**Phase:** Review.

## Purpose
Independently review the shell implementation for plan compliance, accessibility, workflow fidelity, scope, and traceability.

## Required inputs
The delivery-shell diff + Implementation Summary; the approved Plan and allowed-files list.

## Ordered steps
1. Invoke [`review/run-independent-review`](../../review/run-independent-review.recipe.md) with `mode = code`, the diff+summary as `artifact`, the Plan + `specs/07`/`08` as `governing_specs`, and [accessibility](../../../standards/accessibility.md) + [coding](../../../standards/coding.md) + [architecture](../../../standards/architecture.md) as `standards`.
2. Run read-only, fresh context, separate from implementation.
3. Record the verdict.

## Outputs
An Independent Review Report (code mode, UI lens).

## Gate
`PASS` → verification/testing. `FAIL`/conditions → `05-remediate`.

## Prohibited behaviors
Implementer issuing the verdict; editing code during review.
