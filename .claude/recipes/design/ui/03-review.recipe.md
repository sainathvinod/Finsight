# Recipe — UI Design: 03 Review (independent)

**Layer:** recipe (workflow engine). Delegates to the shared review engine. References recipes/standards; does not invoke agents.
**Phase:** Review.

## Purpose
Independently review the UI/UX design against the approved workflow, design system, and accessibility.

## Required inputs
The UI/UX design artifact; `specs/07`, `specs/08`; the approved Brief.

## Ordered steps
1. Invoke [`review/run-independent-review`](../../review/run-independent-review.recipe.md) with `mode = architecture` (UI design lens), the design as `artifact`, `specs/07`/`08` as `governing_specs`, and [accessibility](../../../standards/accessibility.md) + [ai-governance](../../../standards/ai-governance.md) as `standards`.
2. Run read-only, fresh context, separate from design generation.
3. Record the verdict.

## Outputs
An Independent Review Report (UI design).

## Gate
Only `PASS` (or resolved conditions), then human approval, permits implementation.

## Prohibited behaviors
Design author issuing the verdict; editing the design during review.
