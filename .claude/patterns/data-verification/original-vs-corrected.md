# Pattern — Original vs. Corrected Value

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [data-verification.md](../../standards/data-verification.md); `AP-05`, `NFR-056`, `TB-01`.

## Convention
Store both values, never replace. A field under review keeps its original extracted value immutable and records the corrected value alongside it with full lineage.

## Shape
```
field:
  original:   <immutable extracted value>
  corrected:  <review-local value or null>
  reason:     <required when corrected present>
  actor:      <user>
  timestamp:  <when>
  certified:  <true/false>
```

## Guidelines
- Analysis consumes `corrected ?? original` **only after certification**.
- The original remains available for display and audit at all times.

## Checks
- Reading a corrected field still exposes the original.
- Uncertified corrections are not fed to analysis.
