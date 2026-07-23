# Recipe — Testing: 02 Execute

**Layer:** recipe (workflow engine). Composes the [testing skill](../../skills/testing/SKILL.md). References skills/standards; does not invoke agents.
**Phase:** Execute.

## Purpose
Write/run the planned tests and record repeatable evidence covering the full chain.

## Required inputs
The Test Plan; authorized test files.

## Standards
[testing](../../standards/testing.md), [determinism/financial-determinism](../../standards/financial-determinism.md), [data-verification](../../standards/data-verification.md), [accessibility](../../standards/accessibility.md).

## Ordered steps
1. Implement tests (only in authorized test files), annotated `# Verifies: <ID>`.
2. Run `pytest` (relevant markers), `lint-imports`, and `ruff` as applicable.
3. Record evidence and reproduction commands.

## Outputs
Test results + a Verification Report draft.

## Stop conditions / escalation
Evidence cannot be produced without inventing expected values → **Red Card**.

## Prohibited behaviors
Marking work complete when tests fail; editing product code to make a test pass (that is remediation, separately reviewed).
