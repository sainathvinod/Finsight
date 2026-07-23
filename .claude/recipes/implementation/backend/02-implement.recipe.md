# Recipe — Backend Implementation: 02 Implement

**Layer:** recipe (workflow engine). Composes the [backend-implementation skill](../../../skills/backend-implementation/SKILL.md). References skills/standards/patterns; does not invoke agents.
**Phase:** Generate / Execute.

## Purpose
Implement exactly the approved plan in the Python backend, minimal changes, within the allowed-files list.

## Required inputs
The Plan; the allowed-files list.

## Standards / patterns
[coding](../../../standards/coding.md), [architecture](../../../standards/architecture.md), [financial-determinism](../../../standards/financial-determinism.md), [audit-traceability](../../../standards/audit-traceability.md); [backend/layering-ports](../../../patterns/backend/layering-ports.md), [backend/decimal-money](../../../patterns/backend/decimal-money.md), [backend/clock-injection](../../../patterns/backend/clock-injection.md), [financial-domain/deterministic-calculation](../../../patterns/financial-domain/deterministic-calculation.md).

## Ordered steps
1. Implement each task in the authorized files only.
2. Use exact `Decimal`, injected `Clock`, and ports for side effects.
3. Add `# Implements: <ID>` annotations.
4. Write the Implementation Summary.

## Outputs
An implementation diff (authorized files only) + Implementation Summary.

## Stop conditions / escalation
A change would touch a file outside the list or require inventing logic → **Red Card**, stop.

## Prohibited behaviors
Opportunistic refactors; floats on the compute path; source-system write-back; issuing a review verdict.
