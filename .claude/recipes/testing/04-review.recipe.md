# Recipe — Testing: 04 Review (independent)

**Layer:** recipe (workflow engine). Delegates to the shared review engine. References recipes/standards; does not invoke agents.
**Phase:** Review.

## Purpose
Independently review the Verification Report: evidence soundness, acceptance-criteria coverage, and full-chain (not code-only) validation.

## Required inputs
The Verification Report and its evidence; the acceptance criteria and upstream artifacts.

## Ordered steps
1. Invoke [`review/run-independent-review`](../review/run-independent-review.recipe.md) with `mode = test`, the Report as `artifact`, the acceptance criteria as `governing_specs`, and [testing](../../standards/testing.md) as `standards`.
2. Run read-only, fresh context, separate from test execution.
3. Record the verdict.

## Outputs
An Independent Review Report (test mode).

## Gate
`PASS` (or resolved conditions) before governance validation.

## Prohibited behaviors
Test author issuing the verdict; editing the report during review.
