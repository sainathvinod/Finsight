---
name: review
description: First-class independent-review capability with six modes (requirements, architecture, code, test, governance, remediation). Runs read-only in a separate fresh context and returns PASS / PASS WITH CONDITIONS / FAIL / BLOCKED with evidence. A generating execution can never issue its own verdict. Expertise only — the review recipe owns sequencing.
---

# Skill — Review

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Provide reusable, independent review that is separate from the generation it judges — the mechanism that preserves the rigor formerly held by dedicated reviewer roles, without a dedicated reviewer agent.

## Independence requirement (mandatory)
Review must be executed as a **separate, read-only, fresh-context** run — never by the same execution that produced the artifact. The generating execution hands the artifact over and does not write the verdict. Enforced by [`recipes/review/run-independent-review.recipe.md`](../../recipes/review/run-independent-review.recipe.md), which requires a read-only tool set (Read/Grep/Glob), forbids editing the reviewed artifact, and returns a structured result. See [ai-governance](../../standards/ai-governance.md).

## Review modes
`requirements` · `architecture` · `code` · `test` · `governance` · `remediation`. Each mode names the governing specs and standards it checks against.

## When to use
- Any generated artifact reaches its review gate (Brief, Plan, implementation, tests, governance package, remediation).

## When not to use
- To generate or fix artifacts (that is generation/remediation, a different execution).

## Required inputs
- The artifact(s) under review; the governing `specs/` items; the applicable `.claude/standards/`; the review mode.

## Authoritative sources
The governing specs for the mode; the relevant standards; the approved acceptance criteria.

## Capabilities (expertise)
- Judge scope, traceability, determinism, architecture, accessibility, audit honesty, and acceptance-criteria coverage per mode.
- Produce structured evidence and one verdict: **PASS / PASS WITH CONDITIONS / FAIL / BLOCKED**.
- Cite reviewed artifacts, governing specs, standards applied, findings, severity, evidence, required remediation, unresolved assumptions, and any human decision required.

## Standards referenced
All of [`standards/`](../../standards/), selected by mode.

## Templates referenced
[review-report-template](../../templates/review-report-template.md).

## Patterns referenced
As relevant to the mode.

## Recipes that orchestrate this skill
[`recipes/review/run-independent-review.recipe.md`](../../recipes/review/run-independent-review.recipe.md) — the shared review engine, called by every generation recipe's review step.

## Outputs
An Independent Review Report with a single verdict.

## Validation
Executed read-only, in a separate context; verdict is one of the four values; every finding cites evidence.

## Escalation
Governing material needed to review is missing, or resolution requires a human-only decision → verdict **BLOCKED** (and Red Card to a human).

## Traceability
Each finding cites a spec ID, standard, or file:line.
