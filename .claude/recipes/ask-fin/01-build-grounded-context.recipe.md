# Recipe — Ask Fin: 01 Build Grounded Context (DESIGN-ONLY, Release 2)

**Layer:** recipe (workflow engine). Composes the [ask-fin skill](../../skills/ask-fin/SKILL.md). References skills/standards; does not invoke agents.
**Status:** DESIGN-ONLY — the AI layer is not implemented (`E-09`). No endpoints/models are asserted.

## Purpose
Describe how Fin assembles a grounded context from already-computed verified data, approved findings, evidence, and history for the current review.

## Required inputs
The current review's verified data, approved findings, evidence, and history (as produced by the deterministic core).

## Specification references
`specs/10-ai-and-agents.md §4`; `FR-094`, `FR-099`, `NFR-050`.

## Standards
[ai-governance](../../standards/ai-governance.md), [security](../../standards/security.md), [financial-determinism](../../standards/financial-determinism.md).

## Ordered steps (design)
1. Gather only grounded materials for the current review.
2. Apply data minimization/masking per policy before any provider transmission.
3. Assemble the context; mark absent evidence explicitly.

## Outputs
A design-level grounded-context definition (no runtime call).

## Stop conditions / escalation
Grounding materials absent, or a task assumes a live provider → **Red Card** / mark "evidence not found".

## Prohibited behaviors
Fabricating endpoints/models; sending data to an unapproved provider; including ungrounded material.
