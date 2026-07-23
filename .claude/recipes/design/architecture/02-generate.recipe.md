# Recipe — Architecture Design: 02 Generate (Technical Implementation Plan)

**Layer:** recipe (workflow engine). Composes the [architecture-design skill](../../../skills/architecture-design/SKILL.md). References skills/standards/templates/patterns; does not invoke agents.
**Phase:** Generate.

## Purpose
Produce the Technical Implementation Plan: components, ports, ordered traceable tasks, an allowed-files list, and a test strategy.

## Required inputs
The design framing note from `01-plan`.

## Standards / templates / patterns
[architecture](../../../standards/architecture.md), [financial-determinism](../../../standards/financial-determinism.md), [data-verification](../../../standards/data-verification.md), [audit-traceability](../../../standards/audit-traceability.md); [architecture-decision-template](../../../templates/architecture-decision-template.md); [backend/layering-ports](../../../patterns/backend/layering-ports.md), [backend/clock-injection](../../../patterns/backend/clock-injection.md).

## Ordered steps
1. Fill the plan template: components, responsibilities, ports.
2. Record determinism and data boundaries preserved.
3. Write ordered tasks, each traced to an approved ID.
4. Define the allowed-files list that scopes implementation.
5. State the test strategy (unit/golden/determinism/fitness/accessibility as applicable).

## Outputs
A Technical Implementation Plan.

## Stop conditions / escalation
Scope cannot be met without violating layering/determinism, or requires a missing decision → **Red Card**.

## Prohibited behaviors
Issuing a review verdict here; authorizing files beyond what the scope needs.
