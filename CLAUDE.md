# CLAUDE.md — FinSight Operating Rules

Concise, shared rulebook for every Claude Code session in this repository.
Follow it without re-reading the whole repo.

## FinSight Development Organization

- Before undertaking governed project work, follow the bootstrap protocol: @.ai-dev/bootstrap.md
- The **approved specifications remain the source of product and architecture authority.**
- **`.claude/` is the canonical executable layer.** The **three orchestration agents** are `.claude/agents/finsight-po-ai-agent.md`, `finsight-architect-ai-agent.md`, and `finsight-developer-ai-agent.md`. They select and authorize **recipes** (`.claude/recipes/`), which own sequencing and compose **skills** (`.claude/skills/`); rules, scaffolds, and examples live in `.claude/standards/`, `.claude/templates/`, `.claude/patterns/`, and `.claude/tech-stacks/`. See `.claude/README.md`.
- **`.ai-dev/` is the AI Engineering Organization layer** (governance, philosophy, workflow, memory, bootstrap, history) — not an executable layer.
- **Dependency direction is downward only:** Agent → Recipe → Skill / Standard / Template / Pattern / Tech-stack. Lower layers never reference agents; recipes never invoke agents; skills never sequence work.
- **No generation may approve itself.** Every generation stage passes an **independent review** run as a separate, read-only, fresh-context execution of the review skill (`.claude/recipes/review/run-independent-review.recipe.md`), returning PASS / PASS WITH CONDITIONS / FAIL / BLOCKED.
- Missing authority, requirements, thresholds, or decisions must produce a **RED CARD** rather than an invented answer.
- **Do not broadly inspect the repository** unless the assigned agent and current artifact authorize it.

## Source of truth
- **`specs/` is the authoritative source of truth.** Everything else is derived or historical.
- Use the **`spec-driven/` framework**; do **not** invent another process.
- Follow **Specification-Driven Development (SDD)**: spec first, then plan/tasks, then implementation, then verification.

## FinSight philosophy
- **Trust > AI.** Deterministic logic decides; **AI explains only.**
- AI may explain deterministic outputs. AI may **not** create findings, severity, financial truth, approvals, rejections, or financial actions.

## Never invent
- Never invent **requirements, thresholds, business rules, financial logic, architecture, or assumptions.**
- If information needed for the task is **missing or ambiguous: issue a Red Card and stop.**
  - **Red Card** = state plainly what is missing, why it blocks the task, and what input is needed. Do not guess, do not proceed, do not fill gaps with invented values.

## Scope discipline
- **Least-privilege context:** read only the files needed for the assigned task.
- **No opportunistic changes.** Do not modify unrelated files.
- Do **not** change requirements, ADRs, plans, tasks, or governance **unless explicitly instructed.**
- Keep every change **small, traceable, and reviewable.**

## Architecture & determinism (preserve)
- Preserve the **domain → application → infrastructure → delivery** layering; dependencies point inward.
- Preserve **Decimal-only deterministic financial logic** (no floats; exact decimal; explicit ordering; deterministic output).
- **Synthetic thresholds are demonstration-only, not production values.** Never treat them as production configuration.

## No autonomous financial action
- No approval, no rejection, no payment, no budget update, no GED change, no vendor communication.
- FinSight is read-only and human-controlled; a human owns every decision.

## Traceability
- Every implementation must **trace to approved specs, requirements, features, rules, ADRs, plans, or tasks** (e.g., `# Implements:` / `# Verifies:` annotations).
- If work cannot be traced to an approved item, raise a **Red Card** instead of proceeding.
