# Recipe — Backend Implementation: 03 Validate

**Layer:** recipe (workflow engine). Composes the [backend-implementation](../../../skills/backend-implementation/SKILL.md) and [testing](../../../skills/testing/SKILL.md) skills. References skills/standards; does not invoke agents.
**Phase:** Validate.

## Purpose
Run repository-native checks against the change before independent review.

## Required inputs
The implementation diff; the plan's expected tests.

## Standards
[coding](../../../standards/coding.md), [testing](../../../standards/testing.md), [financial-determinism](../../../standards/financial-determinism.md).

## Ordered steps
1. Run `ruff check .`.
2. Run `lint-imports` (layering + storage contracts).
3. Run `pytest` for the relevant markers (incl. golden/determinism where touched).
4. Record results.

## Outputs
Validation evidence attached to the Implementation Summary.

## Stop conditions / escalation
A check fails and cannot be fixed within the allowed-files list without inventing behavior → **Red Card** / route to remediation.

## Prohibited behaviors
Weakening a test or contract to pass; reporting a pass when a check failed.
