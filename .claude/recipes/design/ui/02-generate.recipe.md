# Recipe — UI Design: 02 Generate

**Layer:** recipe (workflow engine). Composes the [ui-design skill](../../../skills/ui-design/SKILL.md). References skills/standards/templates/patterns; does not invoke agents.
**Phase:** Generate.

## Purpose
Produce the UI/UX design for the slice: navigation, states, presentation, and accessibility, faithful to the approved workflow.

## Required inputs
The UI framing note from `01-plan`.

## Standards / templates / patterns
[accessibility](../../../standards/accessibility.md), [ai-governance](../../../standards/ai-governance.md); [leadership-summary-template](../../../templates/leadership-summary-template.md), [finding-template](../../../templates/finding-template.md); [ui/eight-step-wizard](../../../patterns/ui/eight-step-wizard.md), [ui/review-before-analysis](../../../patterns/ui/review-before-analysis.md), [ui/severity-non-color-encoding](../../../patterns/ui/severity-non-color-encoding.md).

## Ordered steps
1. Define navigation and states for the slice within the 8-step workflow.
2. Specify findings/summary presentation with non-color severity encoding.
3. Specify keyboard operability.
4. Keep Ask Fin explanatory only (not the financial source of truth).

## Outputs
A UI/UX design artifact.

## Stop conditions / escalation
Design would reorder the workflow or contradict specs → **Red Card**.

## Prohibited behaviors
Issuing a review verdict here; introducing an unapproved stack.
