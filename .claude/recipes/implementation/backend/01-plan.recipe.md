# Recipe — Backend Implementation: 01 Plan

**Layer:** recipe (workflow engine). Composes the [backend-implementation skill](../../../skills/backend-implementation/SKILL.md). References skills/standards/tech-stack; does not invoke agents.
**Phase:** Plan.

## Purpose
Confirm the approved Technical Implementation Plan is sufficient to implement the backend slice within its allowed-files list.

## Required inputs
The architecture-reviewed, human-approved Plan and its allowed-files list; [tech-stacks/finsight.yml](../../../tech-stacks/finsight.yml).

## Standards
[coding](../../../standards/coding.md), [architecture](../../../standards/architecture.md), [financial-determinism](../../../standards/financial-determinism.md).

## Ordered steps
1. Confirm each task is traceable and within the allowed-files list.
2. Confirm no new dependency, layer, or float is required.
3. Note the tests the plan expects.

## Outputs
An implementation readiness note.

## Stop conditions / escalation
Plan insufficient without inventing behavior, or requires files/deps outside scope → **Red Card**.

## Prohibited behaviors
Expanding the allowed-files list; deciding architecture.
