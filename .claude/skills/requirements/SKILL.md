---
name: requirements
description: Reusable expertise for analyzing FinSight requirements and producing scoped, traceable Implementation Briefs from approved specs. Use when converting an approved task into a work definition. Expertise only — recipes own sequencing.
---

# Skill — Requirements

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Interpret what the approved specifications already decided and express it as a clearly scoped, traceable unit of work — without inventing requirements.

## When to use
- An approved task must become an Implementation Brief with scope, acceptance criteria, and traceability.
- Requirement ambiguity or contradiction must be identified for human resolution.

## When not to use
- Designing implementation or architecture (use architecture-design).
- Creating or changing requirements/thresholds (human-only; raise a Red Card).

## Required inputs
- The approved task and the `specs/` items it references (`FR-###`, `NFR-###`, `E-##`, `F-##-##`, rule IDs).
- Current milestone/task from `.ai-dev/memory.md`.

## Authoritative sources
`specs/01-functional-requirements.md`, `specs/02-non-functional-requirements.md`, `specs/03-epics.md`, `specs/04-features.md`, `specs/05-rules-catalog.md`.

## Capabilities (expertise)
- Decompose a task into scoped items each tied to an approved ID.
- Detect ambiguity, contradiction, and missing acceptance criteria.
- Preserve acceptance criteria verbatim from specs; never invent them.
- Distinguish in-scope from deferred scope (e.g. Invoice Review — `DEC-009`).

## Standards referenced
[specification-authority](../../standards/specification-authority.md), [ai-governance](../../standards/ai-governance.md).

## Templates referenced
[requirement-analysis-template](../../templates/requirement-analysis-template.md).

## Patterns referenced
_None (analysis skill)._

## Recipes that orchestrate this skill
[`recipes/requirements/`](../../recipes/requirements/) — `01-analyze`, `02-organize`, `03-refine`, `04-review`.

## Outputs
A completed Implementation Brief with traceability references and acceptance criteria.

## Validation
Every scoped item maps to an approved ID; no requirement absent from `specs/` is introduced.

## Escalation
Missing/ambiguous requirement, untraceable scope, or need to invent a requirement → **Red Card**, stop.

## Traceability
Brief cites the approved IDs it derives from; downstream design/tests trace back to them.
