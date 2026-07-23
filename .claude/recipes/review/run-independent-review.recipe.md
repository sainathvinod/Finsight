# Recipe — Run Independent Review (shared review engine)

**Layer:** recipe (workflow engine). Composes the [review skill](../../skills/review/SKILL.md). References skills and standards; does not invoke orchestration agents. This is the single mechanism that enforces generation ≠ approval.

## Purpose
Execute an independent review of a generated artifact and return a structured verdict, in a way a generating execution cannot self-satisfy.

## Parameters
- `mode`: one of `requirements | architecture | code | test | governance | remediation`
- `artifact`: path(s)/id of the artifact under review
- `governing_specs`: the approved `specs/` items the artifact must satisfy
- `standards`: the applicable [`standards/`](../../standards/) for the mode

## Required inputs
The artifact, its governing specs, the applicable standards, and the mode. Nothing else is loaded (least privilege).

## Independence controls (mandatory)
1. Executed in a **separate, fresh context** from the generation that produced the artifact.
2. **Read-only tools only** (Read, Grep, Glob). The review may not edit, create, or delete any file.
3. The generating execution **hands over** the artifact and does **not** author the verdict.

## Ordered steps
1. **Load** the artifact, governing specs, and mode-specific standards — only these.
2. **Check** the artifact against each governing item and standard for the mode (scope, traceability, determinism, architecture, accessibility, audit honesty, acceptance-criteria coverage — as the mode dictates).
3. **Collect evidence** for each finding (spec ID / file:line / standard clause).
4. **Decide** exactly one verdict: `PASS` · `PASS WITH CONDITIONS` · `FAIL` · `BLOCKED`.
5. **Emit** an Independent Review Report using [review-report-template](../../templates/review-report-template.md).

## Outputs
An Independent Review Report with the verdict, findings, evidence, required remediation, unresolved assumptions, and any human decision required.

## Stop conditions
Governing material needed to review is missing → verdict `BLOCKED`.

## Escalation
`BLOCKED` or a required human-only decision → route to a human (Red Card).

## Prohibited behaviors
- Editing the reviewed artifact or any file.
- Being run by the same execution that generated the artifact.
- Returning a verdict outside the four allowed values.
- Inventing acceptance criteria or expected values.
