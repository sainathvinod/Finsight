# Recipe — Prototype: 01 Walking Skeleton

**Layer:** recipe (workflow engine). Composes the [ui-shell-implementation](../../skills/ui-shell-implementation/SKILL.md) and [backend-implementation](../../skills/backend-implementation/SKILL.md) skills. References skills/standards; does not invoke agents.
**Phase:** Plan → Generate → Validate → Review.

## Purpose
Produce or extend a disposable walking-skeleton slice that proves an end-to-end path (e.g. wizard frame + non-color severity render) without committing production architecture.

## Required inputs
The approved walking-skeleton plan; the target thin slice.

## Specification references
`specs/plans/PLAN-F-02-02.md`, `specs/tasks/TASKS-F-02-02.md`; `docs/13-walking-skeleton-plan.md` (reference).

## Standards
[accessibility](../../standards/accessibility.md), [coding](../../standards/coding.md), [architecture](../../standards/architecture.md), [ai-governance](../../standards/ai-governance.md).

## Ordered steps
1. Confirm the slice is explicitly walking-skeleton scope (disposable, minimal).
2. Implement the thin path (e.g. text-mode wizard frame) with non-color severity and keyboard operability.
3. Validate (`ruff`, `lint-imports`, `pytest` relevant markers).
4. Obtain an independent review via [`review/run-independent-review`](../review/run-independent-review.recipe.md) (`mode = code`).

## Outputs
A validated walking-skeleton slice + review verdict.

## Stop conditions / escalation
The slice would harden into production architecture, add AI (no Ask Fin/Explain in the skeleton), or introduce a framework → **Red Card**.

## Prohibited behaviors
Treating the prototype as final architecture; adding Ask Fin/Explain to the skeleton; expanding beyond the thin slice.
