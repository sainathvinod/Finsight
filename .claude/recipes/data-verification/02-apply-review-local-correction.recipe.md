# Recipe — Data Verification: 02 Apply Review-Local Correction

**Layer:** recipe (workflow engine). Composes the [data-verification skill](../../skills/data-verification/SKILL.md). References skills/standards/patterns; does not invoke agents.
**Phase:** Execute.

## Purpose
Record a user correction as a review-local, additive change — preserving the original and capturing the reason — with no source-system write-back.

## Required inputs
The value to correct; the corrected value and user-supplied reason.

## Standards / patterns
[data-verification](../../standards/data-verification.md), [audit-traceability](../../standards/audit-traceability.md); [data-verification/review-local-correction](../../patterns/data-verification/review-local-correction.md), [data-verification/original-vs-corrected](../../patterns/data-verification/original-vs-corrected.md).

## Ordered steps
1. Retain the original value immutably.
2. Record the corrected value with actor, timestamp, and reason.
3. Emit an audit event for the correction.
4. Show the UI notice: this does not update the source system; re-import may reproduce the issue.

## Outputs
A review-local correction plus its audit event.

## Stop conditions / escalation
A task appears to require source-system write-back → **Red Card**, stop.

## Prohibited behaviors
Overwriting the original; writing back to the source; skipping the audit event.
