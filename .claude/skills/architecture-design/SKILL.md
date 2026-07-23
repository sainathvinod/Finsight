---
name: architecture-design
description: Reusable expertise for turning approved requirements into FinSight technical design and Technical Implementation Plans while preserving layering, determinism, and the deterministic/AI boundary. Expertise only — recipes own sequencing.
---

# Skill — Architecture Design

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Convert an approved Implementation Brief into a technical design and plan that preserve the approved architecture without introducing new architecture decisions (which are human-only).

## When to use
- An approved Brief needs a Technical Implementation Plan with components, ports, ordered tasks, and an allowed-files list.
- A design must be checked for feasibility against layering and determinism.

## When not to use
- Writing production code (use backend-/ui-shell-implementation).
- Making a new architecture decision or ADR change (human-only; raise a Red Card, or use the SDD ADR flow).

## Required inputs
- The approved Brief; relevant `specs/06-architecture.md` sections and `specs/adr/ADR-###`.

## Authoritative sources
`specs/06-architecture.md`, `specs/adr/` (ADR-001…007), `specs/09-decision-log.md`.

## Capabilities (expertise)
- Define system boundaries, component responsibilities, data flow, and integration boundaries.
- Enforce separation between deterministic financial logic, AI explanation, source-system data, review-local corrected data, audit evidence, and UI presentation.
- Produce an allowed-files list that scopes implementation.

## Standards referenced
[architecture](../../standards/architecture.md), [financial-determinism](../../standards/financial-determinism.md), [data-verification](../../standards/data-verification.md), [audit-traceability](../../standards/audit-traceability.md), [ai-governance](../../standards/ai-governance.md), [specification-authority](../../standards/specification-authority.md).

## Templates referenced
[architecture-decision-template](../../templates/architecture-decision-template.md) (Technical Implementation Plan scaffold).

## Patterns referenced
[backend/layering-ports](../../patterns/backend/layering-ports.md), [backend/clock-injection](../../patterns/backend/clock-injection.md), [backend/verified-dataset-factory](../../patterns/backend/verified-dataset-factory.md), [ai-provider/provider-adapter](../../patterns/ai-provider/provider-adapter.md).

## Recipes that orchestrate this skill
[`recipes/design/architecture/`](../../recipes/design/architecture/) — `01-plan`, `02-generate`, `03-review`.

## Outputs
A Technical Implementation Plan with traceable tasks and an allowed-files list.

## Validation
Plan preserves layering, determinism, and the deterministic/AI boundary; every task traces to an approved item; no new architecture decision is assumed.

## Escalation
Design would require a missing/undecided architecture decision, or inventing architecture → **Red Card**, stop.

## Traceability
Plan tasks cite approved requirement/feature/ADR IDs.
