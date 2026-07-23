# Recipe — Governance: 01 End-to-End Validation

**Layer:** recipe (workflow engine). Composes the [governance skill](../../skills/governance/SKILL.md). References skills/standards/templates; does not invoke agents.
**Phase:** Validate.

## Purpose
Confirm the finished work matches the approved original requirements, every gate passed, and no human-only decision was made by an AI role.

## Required inputs
The original approved specs/task; the complete artifact chain (Brief, Plan, implementation, Verification Report, all review verdicts).

## Standards / templates
[specification-authority](../../standards/specification-authority.md), [ai-governance](../../standards/ai-governance.md), [architecture](../../standards/architecture.md), [financial-determinism](../../standards/financial-determinism.md), [data-verification](../../standards/data-verification.md), [audit-traceability](../../standards/audit-traceability.md), [security](../../standards/security.md); [review-report-template](../../templates/review-report-template.md).

## Ordered steps
1. Compare final output to the approved originals for drift.
2. Confirm each prior gate returned PASS.
3. Confirm no autonomous financial action and no human-only decision by AI.
4. Confirm Ask Fin/provider boundaries and honest audit status.
5. Assemble a Governance Validation Report.

## Outputs
A Governance Validation Report.

## Stop conditions / escalation
Output diverges from approved originals, or a human-only decision is needed → **Red Card** to a human.

## Prohibited behaviors
Fixing findings here (that is remediation); granting final approval (a human act).
