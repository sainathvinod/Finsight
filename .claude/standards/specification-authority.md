# Standard — Specification Authority

**Layer:** standard (normative, leaf). Referenced by skills and recipes. References no agents.
**Origin:** `.ai-dev/constitution.md` §3.1, §3.4–§3.6, §3.8, §7, §8; `CLAUDE.md`.
**Authority above this standard:** `specs/` (product source of truth) and `specs/constitution.md`.

## Rule

1. **`specs/` is authoritative.** The approved specifications in `specs/` are the single source of product and architecture truth. AI implements what a specification has already decided; it never decides for the specification.
2. **Conflict resolution.** If any agent, skill, recipe, standard, template, or pattern conflicts with an approved specification, **the specification wins** and work stops until the conflict is resolved by a human.
3. **No invention.** Never invent requirements, thresholds, business rules, financial logic, architecture, or assumptions. Missing or ambiguous information is a stop condition, not a gap to fill.
4. **Traceability obligation.** Every produced artifact and code change must trace to an approved item — `FR-###`, `NFR-###`, `E-##`, `F-##-##`, a rule ID, an `ADR-###`, a plan, or a task. Untraceable work does not proceed. Code carries `# Implements:` / `# Verifies:` annotations (see [coding.md](coding.md), [audit-traceability.md](audit-traceability.md)).
5. **Least privilege.** Read only the files the assigned task requires. Do not load the repository broadly "just in case."
6. **Minimal change.** Keep every change small, traceable, and reviewable. No opportunistic edits to unrelated files.
7. **Scope protection.** Do not change requirements, ADRs, plans, tasks, or governance unless a task explicitly and traceably authorizes it.

## Approval requirement

Changes to approved scope, requirements, architecture decisions, finance thresholds, or governance are **human-only decisions**. See [ai-governance.md](ai-governance.md).

## Escalation

When required information is missing or ambiguous, or work cannot be traced to an approved item, raise a **Red Card** and stop: state what is missing, why it blocks the task, and what input is needed. A Red Card is resolved only by a human.
