# Recipe — Remediation: 04 Review (independent)

**Layer:** recipe (workflow engine). Delegates to the shared review engine. References recipes/standards; does not invoke agents.
**Phase:** Review.

## Purpose
Independently confirm the remediation resolved exactly the cited defects with no scope expansion or regression.

## Required inputs
The Remediation Summary + corrected diff; the originating review report.

## Ordered steps
1. Invoke [`review/run-independent-review`](../review/run-independent-review.recipe.md) with `mode = remediation`, the Summary+diff as `artifact`, the originating report as `governing_specs`, and the relevant [`standards/`](../../standards/) as `standards`.
2. Run read-only, fresh context, separate from the remediation.
3. Record the verdict.

## Outputs
An Independent Review Report (remediation mode).

## Gate
`PASS` → re-enter verification/testing for full-chain re-validation. Remediation may never close its own review.

## Prohibited behaviors
Remediator issuing the verdict; editing artifacts during review.
