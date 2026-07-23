# Recipe — Data Verification: 03 Certify

**Layer:** recipe (workflow engine). Composes the [data-verification skill](../../skills/data-verification/SKILL.md). References skills/standards/patterns; does not invoke agents.
**Phase:** Validate.

## Purpose
Have the user certify the review-local data so analysis may proceed on certified values only.

## Required inputs
The reviewed values (original + any review-local corrections).

## Specification references
`FR-029`, `DEC-027`, `ADR-006` (`VerifiedDataset` factory).

## Standards / patterns
[data-verification](../../standards/data-verification.md); [backend/verified-dataset-factory](../../patterns/backend/verified-dataset-factory.md).

## Ordered steps
1. Present the per-document decision: approve / approve-with-corrections / reject.
2. Capture the explicit "I have reviewed this information" confirmation.
3. Construct the `VerifiedDataset` via the verification factory only.
4. Emit an audit event for certification.

## Outputs
A certified `VerifiedDataset` ready for analysis.

## Stop conditions / escalation
User has not certified → analysis must not run (stop).

## Prohibited behaviors
Constructing a `VerifiedDataset` outside the verification factory; auto-certifying on the user's behalf.
