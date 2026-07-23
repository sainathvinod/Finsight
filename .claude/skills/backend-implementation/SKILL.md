---
name: backend-implementation
description: Expertise for implementing FinSight's Python backend (domain/application/infrastructure) from an approved plan — deterministic services, ports, data access, validation, and tests — within the approved stack. Expertise only — recipes own sequencing.
---

# Skill — Backend Implementation

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Implement exactly an approved Technical Implementation Plan in the Python backend, preserving layering and determinism, within the plan's allowed-files list.

## When to use
- Implementing domain/application/infrastructure logic, ports, data access, deterministic calculation services, validation, error handling, and their tests.

## When not to use
- Implementing without an approved, architecture-reviewed plan.
- Changing architecture, adding dependencies, or touching files outside the allowed-files list (raise a Red Card).

## Required inputs
- The approved plan + its allowed-files list; the FinSight tech-stack profile.

## Authoritative sources
[tech-stacks/finsight.yml](../../tech-stacks/finsight.yml); the approved plan; `src/finsight-V1/` conventions.

## Capabilities (expertise)
- Implement deterministic services with exact `Decimal` and injected `Clock`.
- Reach side effects through `domain/ports.py`; keep `sqlite3` in infrastructure.
- Add `# Implements:` annotations; make minimal, in-scope changes.

## Standards referenced
[coding](../../standards/coding.md), [architecture](../../standards/architecture.md), [financial-determinism](../../standards/financial-determinism.md), [security](../../standards/security.md), [testing](../../standards/testing.md), [audit-traceability](../../standards/audit-traceability.md).

## Templates referenced
[implementation-plan-template](../../templates/implementation-plan-template.md) (Implementation Summary scaffold).

## Patterns referenced
[backend/layering-ports](../../patterns/backend/layering-ports.md), [backend/decimal-money](../../patterns/backend/decimal-money.md), [backend/clock-injection](../../patterns/backend/clock-injection.md), [backend/verified-dataset-factory](../../patterns/backend/verified-dataset-factory.md), [financial-domain/deterministic-calculation](../../patterns/financial-domain/deterministic-calculation.md).

## Recipes that orchestrate this skill
[`recipes/implementation/backend/`](../../recipes/implementation/backend/) — `01-plan`, `02-implement`, `03-validate`, `04-review`, `05-remediate`.

## Outputs
An implementation diff limited to the allowed-files list plus an Implementation Summary.

## Validation
`ruff`, `lint-imports`, and relevant `pytest` markers pass; determinism preserved; no out-of-scope files.

## Escalation
Plan insufficient without inventing behavior, or change requires a file/dependency outside scope → **Red Card**, stop.

## Traceability
Code annotates the approved IDs it implements.
