# Recipe — Testing: 03 Validate (full chain)

**Layer:** recipe (workflow engine). Composes the [testing skill](../../skills/testing/SKILL.md). References skills/standards; does not invoke agents.
**Phase:** Validate.

## Purpose
Confirm the specification → plan → implementation → results chain is consistent, and that release gates hold.

## Required inputs
Test results; Brief, Plan, implementation, review records.

## Standards
[testing](../../standards/testing.md), [financial-determinism](../../standards/financial-determinism.md), [audit-traceability](../../standards/audit-traceability.md).

## Ordered steps
1. Verify each acceptance criterion has passing evidence.
2. Confirm golden, determinism, and fitness gates pass (and provider-swap when the AI layer exists).
3. Confirm every chain link resolves (no orphan requirement, code, or test).

## Outputs
A completed Verification Report.

## Stop conditions / escalation
A chain link is broken or a gate fails → report accurately; route to remediation (do not mark complete).

## Prohibited behaviors
Weakening a gate to pass; validating code only rather than the full chain.
