# Pattern — Review-Local Correction

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [data-verification.md](../../standards/data-verification.md); `ADR-006`; `FR-003`, `FR-028`, `TB-01`, `P-10`.

## Convention
A user correction applies **only** within the current FinSight review. It never writes back to the source system. The corrected value is an additive layer; the original extracted value is retained unchanged.

## Flow
```
extracted value → user reviews → user edits (with reason) →
system retains {original, corrected, actor, timestamp, reason} →
user certifies → analysis uses the certified corrected value
```

## Guidelines
- No source-system write-back, update event, or vendor notification.
- UI states plainly that the correction does not change the source system, and that re-importing unchanged source data may reproduce the original issue.

## Checks
- Source data is byte-unchanged after a correction.
- Analysis reads the certified value; audit event records the correction.
