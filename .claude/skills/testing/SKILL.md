---
name: testing
description: Expertise for validating the full FinSight chain — spec, plan, implementation, and results — with pytest across unit/golden/determinism/fitness/accessibility markers and traceability to acceptance criteria. Expertise only — recipes own sequencing.
---

# Skill — Testing

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Validate that the specification, plan, implementation, and results form one consistent chain — not the code alone — with recorded, repeatable evidence.

## When to use
- Designing and executing tests that cover acceptance criteria and the full chain.
- Adding golden/determinism/fitness/accessibility coverage when authorized by the plan.

## When not to use
- Marking work complete when tests fail, or inventing expected values.

## Required inputs
- Acceptance criteria and upstream artifacts (Brief, Plan, implementation); existing tests.

## Authoritative sources
`pyproject.toml` markers; `.importlinter`; existing `tests/`; the feature's acceptance criteria.

## Capabilities (expertise)
- Build unit, golden, determinism, fitness, and accessibility tests; negative/edge cases.
- Verify domain behavior: original vs. corrected data, source unchanged, certified-value analysis, audit-event creation, verification-gate consistency, findings-after-selection, deterministic reruns; (R2) Fin explains but does not recompute.
- Record repeatable evidence and coverage against acceptance criteria.

## Standards referenced
[testing](../../standards/testing.md), [financial-determinism](../../standards/financial-determinism.md), [data-verification](../../standards/data-verification.md), [audit-traceability](../../standards/audit-traceability.md), [accessibility](../../standards/accessibility.md).

## Templates referenced
[test-plan-template](../../templates/test-plan-template.md).

## Patterns referenced
[financial-domain/deterministic-calculation](../../patterns/financial-domain/deterministic-calculation.md), [data-verification/original-vs-corrected](../../patterns/data-verification/original-vs-corrected.md), [audit/audit-event](../../patterns/audit/audit-event.md).

## Recipes that orchestrate this skill
[`recipes/testing/`](../../recipes/testing/) — `01-plan`, `02-execute`, `03-validate`, `04-review`.

## Outputs
A Verification Report with recorded, repeatable, full-chain evidence.

## Validation
Every acceptance criterion is covered; evidence is reproducible; no gate weakened.

## Escalation
Acceptance criteria missing/ambiguous, or evidence unobtainable without inventing expected values → **Red Card**, stop.

## Traceability
Tests annotate `# Verifies: <ID>`; the report maps evidence to acceptance criteria.
