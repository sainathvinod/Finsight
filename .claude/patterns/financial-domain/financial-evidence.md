# Pattern — Financial Evidence

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [audit-traceability.md](../../standards/audit-traceability.md); `06 §13`; `FR-069`.

## Convention
Every finding carries the evidence that produced it: the rule reference, the values used, and the source references — so a human can trace a finding back to the underlying GED data. Evidence is a set of deterministic facts, not a narrative.

## Record shape (from spec)
- Finding ID · rule reference · severity · period · affected entities (department / GL account / vendor) · evidence values · source references.

## Guidelines
- Store the values that drove the rule, not a summary of them.
- Explanations (Ask Fin, R2) cite this evidence; they do not add or alter it.

## Checks
- Each emitted finding has non-empty evidence and a resolvable source reference.
