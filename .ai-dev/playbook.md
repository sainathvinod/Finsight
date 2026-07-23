# FinSight Development Organization — Playbook

This document describes how work moves through the organization: the three orchestration agents, the recipes that sequence their work, the independent review between generation and advancement, and the human-approval gates. It is operational. It does not restate the rules — those are in the [Constitution](constitution.md) — and it does not restate the purpose — that is in the [Manifesto](manifesto.md).

The executable assets referenced here live under [`.claude/`](../.claude/). Every session operates under least-privilege context, communicates through artifacts, and stops on any Red Card trigger defined in the Constitution.

---

## The three orchestration agents

Work is owned by **three** lightweight orchestration agents. They **select and authorize recipes**; recipes own the ordered steps and compose skills (**Agent → Recipe → Skill**). No agent sequences work itself, and no agent issues its own review verdict.

```
FinSight PO AI Agent
  → requirements recipes → independent review → HUMAN APPROVAL
        ↓
FinSight Architect AI Agent
  → architecture/design recipes → independent review → HUMAN APPROVAL
        ↓
FinSight Developer AI Agent
  → implementation, testing, financial-review, data-verification,
    governance, and remediation recipes → independent review
    → full-chain verification → HUMAN ACKNOWLEDGMENT
```

- [`finsight-po-ai-agent`](../.claude/agents/finsight-po-ai-agent.md) — approved specifications → a reviewed, traceable Implementation Brief.
- [`finsight-architect-ai-agent`](../.claude/agents/finsight-architect-ai-agent.md) — approved Brief → a reviewed Technical Implementation Plan (with an allowed-files list).
- [`finsight-developer-ai-agent`](../.claude/agents/finsight-developer-ai-agent.md) — approved Plan → implementation, tests, remediation, and delivery preparation.

## Recipes are the workflow engine

Each phase runs through recipes under [`.claude/recipes/`](../.claude/recipes/), following the spine **Plan → Generate → Validate → Review → Remediate**. Recipes compose the reusable skills in [`.claude/skills/`](../.claude/skills/) and reference the standards, templates, and patterns in [`.claude/`](../.claude/).

## Independent review (self-approval is not verification)

The rigor formerly held by five dedicated reviewer roles and a governance reviewer is preserved as a reusable capability: the [review skill](../.claude/skills/review/SKILL.md) executed via [`recipes/review/run-independent-review.recipe.md`](../.claude/recipes/review/run-independent-review.recipe.md).

- Review runs in a **separate, read-only, fresh-context** execution (tools limited to Read/Grep/Glob).
- The generating execution hands over the artifact and **does not** author the verdict.
- Every review returns exactly one of: **PASS · PASS WITH CONDITIONS · FAIL · BLOCKED**, with structured evidence.
- No stage advances without a PASS (or resolved conditions). A FAIL routes to the remediation recipe for the owning phase; the corrected work re-enters verification so the **full chain** — not only the fragment — is re-validated. A BLOCKED (or any Red Card) routes to a human.

## Human-approval gates

Human approval is required between the PO and Architect agents, between the Architect and Developer agents, and before any output is acknowledged as complete. Completion is marked **VERIFIED — READY FOR HUMAN ACKNOWLEDGMENT** (see the [Constitution](constitution.md)); it is not an AI approval. Business scope, requirements, architecture decisions, finance thresholds, governance, and Red Card resolution remain human-only.

## Failure routing

- A generation review **FAIL** routes to the remediation recipe for that phase; the corrected artifact is independently re-reviewed and then re-verified end to end.
- A **BLOCKED** verdict, or any **Red Card**, routes to a **human**.
