# FinSight Development Organization — `.ai-dev/`

## What this folder is

`.ai-dev/` is the **AI Engineering Organization layer** for FinSight: the governed, specification-driven structure through which AI tools and human contributors implement FinSight. It holds **governance, philosophy, migration history, and organizational documentation** — the *why* and *how the organization works*.

It is **not** the executable layer. The executable AI assets — the three orchestration agents, skills, recipes, standards, templates, patterns, and the tech-stack profile — are **canonical under [`.claude/`](../.claude/)**.

This folder does not contain FinSight requirements or code. The authoritative FinSight specifications live in [`specs/`](../specs/), and the repository-wide operating rules live in [`CLAUDE.md`](../CLAUDE.md).

## Why it exists

FinSight is a financial-governance product, and the people who rely on it must be able to trust its outputs. Unconstrained AI assistance tends to drift — inventing scope, eroding architecture, bypassing review, and wasting effort. This layer prevents that drift by defining a single, shared way of working: AI assists, humans remain the final business authority, and every contribution is traceable, reviewed, and deterministic where financial truth is involved.

## How the documents relate

- **Manifesto** (`manifesto.md`) — *why* the organization exists and the culture it enforces.
- **Constitution** (`constitution.md`) — the *rules* and *authority*. Its engineering standards are operationalized in [`.claude/standards/`](../.claude/standards/).
- **Playbook** (`playbook.md`) — *how* work moves through the three orchestration agents, with independent review and human approval.
- **Memory** (`memory.md`) — *what the organization remembers* so each session starts with minimal context.
- **Bootstrap** (`bootstrap.md`) — the *startup protocol* every AI session follows.
- **History** ([`history/`](history/)) — migration records and archived legacy assets.

## Reading order

1. **Manifesto** — purpose and philosophy.
2. **Constitution** — governing rules and chain of authority.
3. **Playbook** — the three-agent workflow and review discipline.
4. **Memory** — the static and operational context to load before starting.
5. **Executable layer** — [`.claude/README.md`](../.claude/README.md): the agents, skills, recipes, standards, templates, patterns, and tech-stack you will actually use.

If any information needed to proceed is missing or ambiguous, do not guess. Raise a Red Card as defined in the Constitution and stop.
