# Target Architecture

The canonical AI engineering architecture for FinSight, Claude-native, layered, with downward-only dependencies.

## Layers and why each exists

| Layer | Home | Why |
|---|---|---|
| Specifications | `specs/` | Authoritative product/architecture truth. Everything defers to it. |
| Organization | `.ai-dev/` | Governance, philosophy, workflow, memory, bootstrap, migration history. |
| Agents | `.claude/agents/` | Three lightweight orchestrators that select/authorize workflows and enforce human gates. |
| Recipes | `.claude/recipes/` | The workflow engine: ordered `Plan → Generate → Validate → Review → Remediate`; compose skills. |
| Skills | `.claude/skills/` | Reusable, composable expertise. No sequencing. |
| Standards | `.claude/standards/` | Normative rules, referenced not duplicated. |
| Templates | `.claude/templates/` | Artifact scaffolds. |
| Patterns | `.claude/patterns/` | Implementation conventions grounded in specs. |
| Tech-stack | `.claude/tech-stacks/` | The confirmed FinSight stack. |

## Dependency flow (downward only)

```
specs/ → .ai-dev/ → agents/ → recipes/ → skills/ + standards/ + templates/ + patterns/ + tech-stacks/ → generated artifacts
```
Enforced rules: lower layers never reference agents; recipes never invoke agents; skills never sequence work; no circular skill/recipe dependencies.

## Agents (what each owns)

- **`finsight-po-ai-agent`** — approved specs → reviewed Implementation Brief. Skills: requirements, review, governance, audit-traceability.
- **`finsight-architect-ai-agent`** — approved Brief → reviewed Technical Plan. Skills: architecture-design, ui-design, financial-analysis, data-verification, ai-provider-integration, review, governance.
- **`finsight-developer-ai-agent`** — approved Plan → implementation, tests, remediation, delivery prep. Skills: backend-/ui-shell-implementation, testing, remediation, financial-analysis, data-verification, audit-traceability, ask-fin (R2), ai-provider-integration (R2), review, governance.

## Skills (14)

requirements · architecture-design · ui-design · financial-analysis · data-verification · audit-traceability · backend-implementation · ui-shell-implementation · testing · governance · remediation · review · ask-fin (R2) · ai-provider-integration (R2). *(No `api-design`; no Ollama-specific skill.)*

## Context flow, human approval, traceability

- **Context:** an agent loads only the recipe(s) for a task; recipes load only the skills/standards/templates/patterns they name (progressive disclosure, least privilege).
- **Human approval:** required between PO→Architect, Architect→Developer, and before completion. Completion is marked *VERIFIED — READY FOR HUMAN ACKNOWLEDGMENT*, never an AI approval.
- **Independent review:** [`recipes/review/run-independent-review.recipe.md`](../../.claude/recipes/review/run-independent-review.recipe.md) runs as a separate, read-only, fresh-context execution; a generating execution can never issue its own verdict.
- **Traceability:** artifacts and code cite approved IDs (`# Implements:` / `# Verifies:`); the audit-traceability skill/standard maintain requirement→spec→design→implementation→test→review.

## Grounded deviations from the generic model

- **No `api-design`** — FinSight has no API scope (`DEC-003`).
- **`ai-provider-integration`, not `ollama-integration`** — provider abstraction is specified; Ollama is a documented future local option only.
- **`ui-shell-implementation`** scoped to the delivery shell — no web/GUI framework exists (deferred, `ADC-01`).
- **AI recipes/skills are design-only (Release 2)** — no fabricated endpoints or models.
- **Wizard step drift** (spec 8 steps `DEC-024` vs code 9 labels) recorded, not repaired — product behavior is out of scope.
