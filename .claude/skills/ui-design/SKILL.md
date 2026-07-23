---
name: ui-design
description: Reusable expertise for FinSight review-workflow UX and information architecture — the Guided Review Wizard, verification interactions, findings and leadership-summary presentation, and accessibility. Expertise only — recipes own sequencing.
---

# Skill — UI Design

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Design the review workflow, navigation, and presentation so that verification, findings, and the leadership summary are clear, accessible, and faithful to the approved UX.

## When to use
- Designing review navigation, validation/verification states, findings presentation, or the leadership summary.
- Ensuring accessibility and enterprise conventions in a UI slice.

## When not to use
- Implementing UI components (use ui-shell-implementation).
- Encoding financial truth in the UI (the deterministic core owns truth).

## Required inputs
- The approved UX and design-system specs and the feature's Brief.

## Authoritative sources
`specs/07-ux-design.md`, `specs/08-ui-design-system.md`; `DEC-024` (Guided Review Wizard).

## Capabilities (expertise)
- Preserve the approved workflow sequence: **Create → Upload → Validate → Verify → Analyze → Findings → Summary → Complete** (8 steps, `DEC-024`).
- Enforce: no financial dashboard before a review is selected; full financial review precedes findings; Ask Fin is explanatory, not the financial source of truth; prototype UX is disposable, not final architecture.
- Design non-color severity encoding and keyboard-operable flows.

## Standards referenced
[accessibility](../../standards/accessibility.md), [ai-governance](../../standards/ai-governance.md), [data-verification](../../standards/data-verification.md), [specification-authority](../../standards/specification-authority.md).

## Templates referenced
[leadership-summary-template](../../templates/leadership-summary-template.md), [finding-template](../../templates/finding-template.md).

## Patterns referenced
[ui/eight-step-wizard](../../patterns/ui/eight-step-wizard.md), [ui/review-before-analysis](../../patterns/ui/review-before-analysis.md), [ui/severity-non-color-encoding](../../patterns/ui/severity-non-color-encoding.md).

## Recipes that orchestrate this skill
[`recipes/design/ui/`](../../recipes/design/ui/) — `01-plan`, `02-generate`, `03-review`.

## Outputs
UX/UI design artifacts consistent with the approved workflow and design system.

## Validation
Workflow order preserved; accessibility rules honored; no financial truth encoded in UI.

## Escalation
A UI element's behavior or accessible form is undefined in `specs/07`/`08`, or the design would reorder the approved workflow → **Red Card** (record wizard step drift for a human; do not silently change it).

## Traceability
Design elements cite UX/UI spec sections and feature IDs.
