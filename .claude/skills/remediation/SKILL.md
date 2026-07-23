---
name: remediation
description: Expertise for correcting exactly the defects cited in a review's required-remediation list, without scope expansion, and rerunning validation. Never weakens a standard, test, or requirement to pass. Expertise only — recipes own sequencing.
---

# Skill — Remediation

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Interpret review findings, prioritize defects, repair exactly what was cited, rerun validation, and document residual risk — without touching anything else.

## When to use
- A review returned FAIL (or PASS WITH CONDITIONS) with specific cited defects to correct.

## When not to use
- Broadening scope, refactoring unrelated code, or "fixing" a failure by weakening a standard, test, or requirement (prohibited without explicit human approval).

## Required inputs
- The review report's cited defects and the specific artifacts/files they reference.

## Authoritative sources
The originating review report; the plan and specs the cited artifacts trace to.

## Capabilities (expertise)
- Map each cited defect to a minimal, in-scope correction.
- Preserve determinism, layering, and traceability while fixing.
- Record residual risk and any defect that cannot be fixed without a human decision.

## Standards referenced
[specification-authority](../../standards/specification-authority.md), [coding](../../standards/coding.md), [financial-determinism](../../standards/financial-determinism.md), [architecture](../../standards/architecture.md), [testing](../../standards/testing.md).

## Templates referenced
[implementation-plan-template](../../templates/implementation-plan-template.md) (Remediation Summary reuses the summary shape).

## Patterns referenced
As relevant to the defect (e.g. [backend/*](../../patterns/backend/), [financial-domain/*](../../patterns/financial-domain/)).

## Recipes that orchestrate this skill
[`recipes/remediation/`](../../recipes/remediation/) — `01-triage`, `02-remediate`, `03-validate`, `04-review`.

## Outputs
A Remediation Summary limited to the cited defects, with rerun validation evidence.

## Validation
Only cited defects changed; no new drift/regression; gates re-pass without being weakened.

## Escalation
A fix would require inventing a requirement/decision, weakening a control, or a human-only decision → **Red Card**, stop. Remediation never closes its own review.

## Traceability
Summary references the originating review and the cited defect items.
