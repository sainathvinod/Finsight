# Recipe — Data Verification: 04 Audit Review (independent)

**Layer:** recipe (workflow engine). Composes the [audit-traceability skill](../../skills/audit-traceability/SKILL.md) and delegates the verdict to the shared review engine. References skills/recipes/standards; does not invoke agents.
**Phase:** Review.

## Purpose
Confirm every correction and certification produced a complete audit event and that originals were preserved — then obtain an independent verdict.

## Required inputs
The correction/certification actions and their audit events; the retained originals.

## Standards
[audit-traceability](../../standards/audit-traceability.md), [data-verification](../../standards/data-verification.md).

## Ordered steps
1. Check each correction/certification emitted an audit event with the required metadata.
2. Confirm originals are unchanged and no source write-back occurred.
3. Invoke [`review/run-independent-review`](../review/run-independent-review.recipe.md) with `mode = governance` over the audit evidence.
4. Record the verdict.

## Outputs
An audit-review verdict (Independent Review Report).

## Stop conditions / escalation
A required audit field is missing → **Red Card**.

## Prohibited behaviors
Claiming tamper-evidence/immutability (append-only only); self-issuing the verdict.
