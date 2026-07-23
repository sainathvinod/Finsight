# Recipe — UI Shell Implementation: 03 Validate

**Layer:** recipe (workflow engine). Composes the [ui-shell-implementation](../../../skills/ui-shell-implementation/SKILL.md) and [testing](../../../skills/testing/SKILL.md) skills. References skills/standards; does not invoke agents.
**Phase:** Validate.

## Purpose
Run repository-native checks, including accessibility, against the shell change.

## Required inputs
The delivery-shell diff; expected tests.

## Standards
[accessibility](../../../standards/accessibility.md), [coding](../../../standards/coding.md), [testing](../../../standards/testing.md).

## Ordered steps
1. Run `ruff check .` and `lint-imports`.
2. Run `pytest -m accessibility` and other relevant markers.
3. Record results.

## Outputs
Validation evidence attached to the Implementation Summary.

## Stop conditions / escalation
A check fails and cannot be fixed within scope without inventing behavior → **Red Card** / route to remediation.

## Prohibited behaviors
Weakening an accessibility test to pass; reporting a pass when a check failed.
