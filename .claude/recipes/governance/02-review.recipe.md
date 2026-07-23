# Recipe — Governance: 02 Review (independent)

**Layer:** recipe (workflow engine). Delegates to the shared review engine. References recipes/standards; does not invoke agents.
**Phase:** Review.

## Purpose
Obtain the final independent governance verdict on the end-to-end validation.

## Required inputs
The Governance Validation Report; the original approved specs; the full artifact chain.

## Ordered steps
1. Invoke [`review/run-independent-review`](../review/run-independent-review.recipe.md) with `mode = governance`, the Report as `artifact`, the approved originals as `governing_specs`, and the full [`standards/`](../../standards/) set as `standards`.
2. Run read-only, fresh context, separate from the validation that produced the Report.
3. Record the verdict.

## Outputs
A final Independent Review Report (governance mode).

## Gate
On `PASS`, the work is marked **VERIFIED — READY FOR HUMAN ACKNOWLEDGMENT** (completion is not approval; a human acknowledges).

## Prohibited behaviors
The validating execution issuing its own verdict; treating PASS as human approval.
