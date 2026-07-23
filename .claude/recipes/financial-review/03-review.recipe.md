# Recipe — Financial Review: 03 Review (independent)

**Layer:** recipe (workflow engine). Delegates to the shared review engine. References recipes/standards; does not invoke agents.
**Phase:** Review.

## Purpose
Independently review the financial-review presentation for fidelity to deterministic results and rules.

## Required inputs
The findings presentation and leadership summary; the deterministic results; the rules catalog.

## Ordered steps
1. Invoke [`review/run-independent-review`](../review/run-independent-review.recipe.md) with `mode = governance`, the presentation as `artifact`, `specs/05` + the results as `governing_specs`, and [financial-determinism](../../standards/financial-determinism.md) + [ai-governance](../../standards/ai-governance.md) as `standards`.
2. Confirm no value/severity was created or altered outside the engine.
3. Record the verdict.

## Outputs
An Independent Review Report (financial-review).

## Gate
`PASS` (or resolved conditions) before the summary is used with humans.

## Prohibited behaviors
Presenter issuing the verdict; editing the presentation during review.
