# Recipe — Ask Fin: 03 Validate Grounding (DESIGN-ONLY, Release 2)

**Layer:** recipe (workflow engine). Composes the [ask-fin skill](../../skills/ask-fin/SKILL.md). References skills/standards; does not invoke agents.
**Status:** DESIGN-ONLY — not implemented.

## Purpose
Describe how an explanation is checked to be fully grounded and cited before it reaches a user.

## Required inputs
The generated explanation and the grounded context it claims to draw on.

## Standards
[ai-governance](../../standards/ai-governance.md), [audit-traceability](../../standards/audit-traceability.md).

## Ordered steps (design)
1. Verify every claim maps to grounded evidence.
2. Confirm absent evidence is reported as "evidence not found", never guessed.
3. Confirm no financial value/finding was created or altered.
4. Confirm the AI-interaction audit fields are recorded.

## Outputs
A design-level grounding-validation definition.

## Stop conditions / escalation
An ungrounded claim is present → reject the explanation (do not surface it).

## Prohibited behaviors
Passing ungrounded output; suppressing the "evidence not found" state.
