# FinSight Development Organization — Bootstrap Protocol

This is the entrypoint for every AI session working on FinSight. Before doing anything else, a session follows this protocol. It binds the [Constitution](constitution.md), the [Playbook](playbook.md), and the executable architecture in [`.claude/`](../.claude/) to actual behavior.

## Startup sequence

Every AI session must, in order:

1. **Read [`CLAUDE.md`](../CLAUDE.md)** — the repository operating contract.
2. **Read [`.ai-dev/README.md`](README.md)** — the map of the organization (governance, philosophy, history) and its reading order.
3. **Read [`.claude/README.md`](../.claude/README.md)** — the executable architecture: the three agents, skills, recipes, standards, templates, patterns, and tech-stack.
4. **Identify the orchestration agent** for the task — one of `finsight-po-ai-agent`, `finsight-architect-ai-agent`, `finsight-developer-ai-agent`. If none is assigned and it cannot be inferred from the task, stop and request one.
5. **Read that agent's definition** in [`.claude/agents/`](../.claude/agents/), then the **recipes** it authorizes for the task.
6. **Load only the skills, standards, templates, and patterns those recipes reference** — least-privilege context. Do not load the repository broadly.
7. **Read the current task artifact or prompt** — the specific input to act on.
8. **If required information is missing or ambiguous, issue a RED CARD and stop** — state what is missing, why it blocks the task, and what input is needed. Do not search the repository broadly to fill the gap.
9. **Produce only the expected artifact or output** — nothing more — and route generation through a recipe whose review step is an independent, read-only, separate execution.

## Binding rules

- **No session begins work without completing the startup sequence above.**
- **`specs/` is authoritative**; `.claude/` is the canonical executable layer; `.ai-dev/` is the organization layer. If any AI instruction conflicts with an approved specification, the specification wins.
- **No agent may skip the independent review gate**, and no generating execution may issue its own review verdict.
- **No role may inspect unrelated files "just in case."** Curiosity is not authorization; least-privilege context is mandatory.
- **Human approval is required** at the gates defined in the [Playbook](playbook.md); human-only decisions are never made by an AI role.

Operational state — the current milestone, task, and open Red Cards — is read from [`memory.md`](memory.md). The governing rules live in the [Constitution](constitution.md); the workflow lives in the [Playbook](playbook.md).
