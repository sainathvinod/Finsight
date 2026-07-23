# Recipe — Requirements: 01 Analyze

**Layer:** recipe (workflow engine). Composes the [requirements skill](../../skills/requirements/SKILL.md). References skills/standards; does not invoke agents.
**Phase:** Plan.

## Purpose
Analyze an approved task against `specs/` to identify the requirements in scope and any ambiguity or contradiction.

## Required inputs
The approved task; referenced `FR-###`/`NFR-###`/`F-##-##`/rule IDs; current milestone from `.ai-dev/memory.md`.

## Specification references
`specs/01-functional-requirements.md`, `specs/02-non-functional-requirements.md`, `specs/04-features.md`, `specs/05-rules-catalog.md`.

## Standards
[specification-authority](../../standards/specification-authority.md), [ai-governance](../../standards/ai-governance.md).

## Ordered steps
1. Read only the referenced approved items.
2. List each in-scope requirement with its approved ID.
3. Flag ambiguities, contradictions, or missing acceptance criteria.
4. Note deferred/out-of-scope items (e.g. Invoice Review — `DEC-009`).

## Outputs
An analysis note feeding `02-organize`.

## Stop conditions / escalation
Referenced item missing or ambiguous → **Red Card**, stop.

## Prohibited behaviors
Inventing requirements/thresholds; reading `src/`/`tests/` for this analysis; broad repository reads.
