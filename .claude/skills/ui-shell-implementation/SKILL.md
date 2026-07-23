---
name: ui-shell-implementation
description: Expertise for implementing FinSight's delivery/UI shell (currently the text-mode wizard) from an approved plan, honoring accessibility and workflow order. No web framework is assumed — GUI binding is deferred. Expertise only — recipes own sequencing.
---

# Skill — UI Shell Implementation

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Implement the delivery/presentation shell for a review workflow slice, faithful to the approved UX, accessibility rules, and the deterministic/AI boundary.

## When to use
- Implementing the delivery-ring shell (today: text-mode wizard in `delivery/wizard.py`), presentation of validation/verification states, findings, and the leadership summary.

## When not to use
- Assuming a web/React/Electron stack — none is approved; GUI binding is deferred (`ADR-001`/`ADC-01`). Raise a Red Card if a task assumes one.
- Encoding financial truth in the shell (the deterministic core owns truth).

## Required inputs
- The approved plan + allowed-files list; the UX/design-system specs.

## Authoritative sources
[tech-stacks/finsight.yml](../../tech-stacks/finsight.yml); `specs/07-ux-design.md`, `specs/08-ui-design-system.md`; `src/finsight-V1/delivery/`.

## Capabilities (expertise)
- Implement keyboard-operable, non-color severity presentation.
- Preserve the 8-step review workflow and "no dashboard before review selected".
- Keep the shell replaceable (delivery ring) and free of business truth.

## Standards referenced
[accessibility](../../standards/accessibility.md), [coding](../../standards/coding.md), [architecture](../../standards/architecture.md), [ai-governance](../../standards/ai-governance.md), [testing](../../standards/testing.md).

## Templates referenced
[implementation-plan-template](../../templates/implementation-plan-template.md).

## Patterns referenced
[ui/severity-non-color-encoding](../../patterns/ui/severity-non-color-encoding.md), [ui/review-before-analysis](../../patterns/ui/review-before-analysis.md), [ui/eight-step-wizard](../../patterns/ui/eight-step-wizard.md).

## Recipes that orchestrate this skill
[`recipes/implementation/ui-shell/`](../../recipes/implementation/ui-shell/) — `01-plan`, `02-implement`, `03-validate`, `04-review`, `05-remediate`.

## Outputs
A delivery-shell implementation diff plus an Implementation Summary.

## Validation
Accessibility tests pass; workflow order preserved; no financial truth in the shell; no unapproved framework introduced.

## Escalation
Task assumes an unapproved UI technology, or reorders the approved workflow → **Red Card** (record wizard step drift; do not silently change it).

## Traceability
Shell code annotates the UX/UI spec items and feature IDs it implements.
