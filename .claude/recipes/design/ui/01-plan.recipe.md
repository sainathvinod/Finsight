# Recipe — UI Design: 01 Plan

**Layer:** recipe (workflow engine). Composes the [ui-design skill](../../../skills/ui-design/SKILL.md). References skills/standards; does not invoke agents.
**Phase:** Plan.

## Purpose
Frame a UI/UX slice against the approved workflow and design system.

## Required inputs
The approved Brief for a UI feature; `specs/07-ux-design.md`, `specs/08-ui-design-system.md`.

## Standards
[accessibility](../../../standards/accessibility.md), [ai-governance](../../../standards/ai-governance.md), [data-verification](../../../standards/data-verification.md).

## Ordered steps
1. Locate the slice within the 8-step Guided Review Wizard (`DEC-024`).
2. Identify validation/verification states, findings, and summary presentation involved.
3. Note accessibility (non-color severity, keyboard) and "no dashboard before review selected".

## Outputs
A UI framing note feeding `02-generate`.

## Stop conditions / escalation
Element behavior/accessible form undefined in specs, or slice implies reordering the workflow → **Red Card** (record wizard step drift; do not change behavior).

## Prohibited behaviors
Assuming a web/GUI framework; encoding financial truth in UI.
