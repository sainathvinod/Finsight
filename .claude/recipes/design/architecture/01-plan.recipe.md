# Recipe — Architecture Design: 01 Plan

**Layer:** recipe (workflow engine). Composes the [architecture-design skill](../../../skills/architecture-design/SKILL.md). References skills/standards; does not invoke agents.
**Phase:** Plan.

## Purpose
Frame the design approach for an approved Brief, identifying components, boundaries, and the ADRs that govern them — without making a new architecture decision.

## Required inputs
The reviewed, human-approved Implementation Brief; relevant `specs/06-architecture.md` sections and `specs/adr/`.

## Standards
[architecture](../../../standards/architecture.md), [financial-determinism](../../../standards/financial-determinism.md), [specification-authority](../../../standards/specification-authority.md).

## Ordered steps
1. Identify components, layers, and ports the scope touches.
2. Map each to governing ADRs and architecture sections.
3. Note determinism/AI and source-system boundaries that constrain the design.
4. Flag any needed decision that does not yet exist.

## Outputs
A design framing note feeding `02-generate`.

## Stop conditions / escalation
A required architecture decision is missing → **Red Card** (new decisions are human-only).

## Prohibited behaviors
Deciding architecture; moving financial calculation toward AI; inventing integration.
