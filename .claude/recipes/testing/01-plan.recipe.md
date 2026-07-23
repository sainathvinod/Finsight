# Recipe — Testing: 01 Plan

**Layer:** recipe (workflow engine). Composes the [testing skill](../../skills/testing/SKILL.md). References skills/standards/templates; does not invoke agents.
**Phase:** Plan.

## Purpose
Plan verification of a feature: which acceptance criteria and chain links are covered, and by which test types.

## Required inputs
Acceptance criteria; the approved plan and implementation; existing `tests/`.

## Standards / templates
[testing](../../standards/testing.md), [financial-determinism](../../standards/financial-determinism.md); [test-plan-template](../../templates/test-plan-template.md).

## Ordered steps
1. List acceptance criteria and map each to a planned test.
2. Choose markers (unit/golden/determinism/fitness/accessibility/audit/security).
3. Identify domain cases (original-vs-corrected, source-unchanged, certified-value analysis, audit events, findings-after-selection, deterministic reruns).

## Outputs
A Test Plan.

## Stop conditions / escalation
An acceptance criterion is missing/ambiguous → **Red Card**.

## Prohibited behaviors
Inventing expected values; inventing new marker categories.
