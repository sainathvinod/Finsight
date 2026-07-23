---
name: governance
description: Reusable expertise for end-to-end governance validation — specification/architecture compliance, human-approval gates, AI-usage boundaries, traceability, and release readiness. Usable by all three orchestration agents. Expertise only — recipes own sequencing.
---

# Skill — Governance

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Confirm that finished work matches the approved original requirements, that every gate passed, and that no human-only decision was made by an AI role. This skill replaces a standalone governance orchestrator; it is reusable by every agent.

## When to use
- Final end-to-end validation before human acknowledgment.
- Checking specification/architecture compliance, AI boundaries, and release readiness at any gate.

## When not to use
- Fixing findings (use remediation) or granting final approval (a human act).

## Required inputs
- The original approved specs/task and the complete artifact chain (Brief, Plan, implementation, Verification Report, review records).

## Authoritative sources
`specs/`; `.ai-dev/constitution.md` (principles); `specs/09-decision-log.md`.

## Capabilities (expertise)
- Verify spec compliance, architecture compliance, privacy/security posture, and traceability.
- Confirm human-approval gates were honored and no autonomous financial action occurred.
- Confirm Ask Fin/provider boundaries and audit-status honesty.
- Assess release readiness.

## Standards referenced
[specification-authority](../../standards/specification-authority.md), [ai-governance](../../standards/ai-governance.md), [architecture](../../standards/architecture.md), [financial-determinism](../../standards/financial-determinism.md), [data-verification](../../standards/data-verification.md), [audit-traceability](../../standards/audit-traceability.md), [security](../../standards/security.md).

## Templates referenced
[review-report-template](../../templates/review-report-template.md) (governance-review mode).

## Patterns referenced
_None (cross-cutting validation)._

## Recipes that orchestrate this skill
[`recipes/governance/`](../../recipes/governance/) — `01-end-to-end-validation`, `02-review`. The independent verdict comes from [`recipes/review/run-independent-review`](../../recipes/review/) in governance-review mode.

## Outputs
A Governance Validation Report feeding an independent review verdict.

## Validation
Output matches approved originals; all gates passed; no human-only decision made by AI.

## Escalation
Output diverges from approved requirements, a control was weakened, or a human-only decision is required → **Red Card** to a human.

## Traceability
Report maps each conclusion to an approved ID and the corresponding gate.
