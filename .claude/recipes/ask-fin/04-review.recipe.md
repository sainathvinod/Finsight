# Recipe — Ask Fin: 04 Review (independent, DESIGN-ONLY, Release 2)

**Layer:** recipe (workflow engine). Delegates to the shared review engine. References recipes/standards; does not invoke agents.
**Status:** DESIGN-ONLY — not implemented.

## Purpose
Independently review a Fin explanation design/behavior for grounding, boundary compliance, and audit completeness.

## Required inputs
The explanation and its grounding-validation result; `specs/10-ai-and-agents.md`.

## Ordered steps
1. Invoke [`review/run-independent-review`](../review/run-independent-review.recipe.md) with `mode = governance`, the explanation as `artifact`, `specs/10` as `governing_specs`, and [ai-governance](../../standards/ai-governance.md) + [security](../../standards/security.md) as `standards`.
2. Run read-only, fresh context, separate from generation.
3. Record the verdict.

## Outputs
An Independent Review Report (Ask Fin design).

## Gate
`PASS` before any Fin behavior is considered ready (implementation itself remains Release 2).

## Prohibited behaviors
Generator issuing the verdict; treating design review as authorization to ship AI in Release 1.
