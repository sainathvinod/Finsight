# FinSight AI Engineering — Executable Layer (`.claude/`)

`.claude/` is the **canonical, executable** AI engineering architecture for FinSight. It holds the orchestration agents, reusable skills, workflow recipes, standards, templates, patterns, and the technology profile that AI sessions use to do governed work.

- **Product & architecture source of truth:** [`specs/`](../specs/) (authoritative).
- **AI Engineering Organization layer** (governance, philosophy, history): [`.ai-dev/`](../.ai-dev/).
- **Repository operating contract:** [`CLAUDE.md`](../CLAUDE.md).

If anything here conflicts with an approved specification, **the specification wins.**

## Layout

| Path | Layer | Purpose |
|---|---|---|
| `agents/` | orchestration | The **three** canonical agents. Select and authorize workflows; enforce human gates. |
| `skills/` | expertise | Reusable, composable know-how. **No workflow sequencing.** |
| `recipes/` | workflow engine | Ordered `Plan → Generate → Validate → Review → Remediate`. **Compose skills.** |
| `standards/` | normative (leaf) | Rules referenced by skills/recipes. Reference no agents. |
| `templates/` | scaffolding (leaf) | Artifact shapes. Reference no agents. |
| `patterns/` | examples (leaf) | Implementation conventions grounded in specs. Reference no agents. |
| `tech-stacks/` | profile (leaf) | The confirmed FinSight stack. References no agents. |

## Dependency direction (downward only)

```
specs/  →  .ai-dev/ (organization)  →  agents/  →  recipes/  →  skills/ + standards/ + templates/ + patterns/ + tech-stacks/
```

**Agent → Recipe → Skill.** Agents select and authorize; recipes own sequencing and review gates; skills provide expertise. Lower layers never reference agents; recipes never invoke agents; skills never sequence work.

## The three agents

1. [`finsight-po-ai-agent`](agents/finsight-po-ai-agent.md) — business intent → reviewed, human-approved Implementation Brief.
2. [`finsight-architect-ai-agent`](agents/finsight-architect-ai-agent.md) — approved Brief → reviewed, human-approved Technical Implementation Plan.
3. [`finsight-developer-ai-agent`](agents/finsight-developer-ai-agent.md) — approved Plan → implementation, tests, remediation, delivery prep.

## Workflow & human approval

```
PO agent ─(independent review PASS)─▶ HUMAN APPROVAL ─▶
Architect agent ─(independent review PASS)─▶ HUMAN APPROVAL ─▶
Developer agent ─(independent review PASS + full-chain verification)─▶ HUMAN ACKNOWLEDGMENT
```
Completion is marked **VERIFIED — READY FOR HUMAN ACKNOWLEDGMENT**; it is never an AI approval.

## Independent review (generation ≠ approval)

Every generation recipe ends by dispatching [`recipes/review/run-independent-review.recipe.md`](recipes/review/run-independent-review.recipe.md) — executed as a **separate, read-only, fresh-context** run (tools limited to Read/Grep/Glob) using the [review skill](skills/review/SKILL.md). It returns exactly one of **PASS · PASS WITH CONDITIONS · FAIL · BLOCKED** with structured evidence. A generating execution can never issue its own verdict. There is no dedicated reviewer agent — independence is enforced by the recipe + read-only separate execution.

## Using the architecture

- **Full governed workflow:** invoke one of the three agents; it authorizes the relevant recipes.
- **Direct skill use:** a skill may be used directly for its expertise (e.g. `financial-analysis`), but any multi-step governed work — especially anything with a review gate — runs through a recipe.

## Preserved FinSight guarantees

Deterministic core owns financial truth; AI explains only. Findings are rule-produced (`ADR-007`). Corrections are review-local with **no source-system write-back**; originals are immutable. Audit is **append-only** (tamper-evidence deferred to R2 — never claimed as immutable). Ask Fin and AI providers are **specified-only (Release 2)**; Ollama is not a selected provider. Invoice Review is **deferred** (`DEC-009`). GED = General Expense Detail.
