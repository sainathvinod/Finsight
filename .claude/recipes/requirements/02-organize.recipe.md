# Recipe — Requirements: 02 Organize

**Layer:** recipe (workflow engine). Composes the [requirements skill](../../skills/requirements/SKILL.md). References skills/standards; does not invoke agents.
**Phase:** Generate.

## Purpose
Organize analyzed requirements into a scoped structure (epics/features/stories as the approved FinSight model uses), preserving acceptance criteria.

## Required inputs
The analysis note from `01-analyze`; the approved epics/features (`specs/03-epics.md`, `specs/04-features.md`).

## Standards
[specification-authority](../../standards/specification-authority.md).

## Ordered steps
1. Group in-scope items under their approved epic/feature.
2. Preserve acceptance criteria verbatim from specs.
3. Mark in-scope vs. out-of-scope explicitly.

## Outputs
A structured scope outline feeding `03-refine`.

## Stop conditions / escalation
An item cannot be tied to an approved epic/feature → **Red Card**.

## Prohibited behaviors
Reorganizing or rewriting approved requirements; introducing new structure not in the spec model.
