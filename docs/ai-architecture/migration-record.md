# Migration Record

Record of files created, modified, relocated, and removed in the 2026-07-23 AI engineering architecture migration. Executed on branch `migration/ai-engineering-architecture`.

## Created

- **Agents (3):** `.claude/agents/finsight-{po,architect,developer}-ai-agent.md`
- **Skills (14):** `.claude/skills/*/SKILL.md`
- **Recipes (43):** `.claude/recipes/**` (requirements 4, design/architecture 3, design/ui 3, financial-review 3, data-verification 4, implementation/backend 5, implementation/ui-shell 5, testing 4, governance 2, review 1, remediation 4, ask-fin 4, prototype 1)
- **Patterns (16):** `.claude/patterns/**` (backend 4, financial-domain 3, audit 2, data-verification 2, ui 3, ai-provider 2)
- **Standards (10):** `.claude/standards/*.md`
- **Templates (8):** `.claude/templates/*.md`
- **Tech-stack:** `.claude/tech-stacks/finsight.yml`
- **Index:** `.claude/README.md`
- **Org history:** `.ai-dev/history/migration-2026-07-23.md` (+ `legacy-role-contracts/` populated at finalization)
- **Deliverables:** `docs/ai-architecture/{current-state-inventory,responsibility-map,target-architecture,migration-record}.md`

## Modified

- `CLAUDE.md` — `.claude/` declared canonical executable layer; 3-agent model; downward-only dependency rule; independent-review rule.
- `.ai-dev/README.md`, `playbook.md`, `bootstrap.md` — rewritten to the 3-agent workflow; `.ai-dev/` reframed as the organization layer.
- `.ai-dev/constitution.md` — §4 chain of authority and §5/§11 review/completion updated to the 3-agent + review-skill model; §3 principles preserved; pointer added to `.claude/standards/`.
- `.ai-dev/manifesto.md` — role-named bullets reframed as capabilities; pointer to `.claude/`.
- `.ai-dev/memory.md` — repository layout + executable-roles note updated.

## Relocated (at finalization, post-validation)

- `.ai-dev/agents/*.md` (11) → `.ai-dev/history/legacy-role-contracts/` (verbatim; Git history preserved).

## Removed (at finalization, post-validation only)

- `.claude/agents/*.md` (11 legacy wrappers) — replaced by the 3 orchestration agents.
- `.ai-dev/prompts/*.md` (6 empty stubs) and `.ai-dev/templates/*.md` (8 empty stubs).

## Intentionally retained / untouched

`specs/`, `docs/` numbered files, `spec-driven/` (externally managed), `src/`, `tests/`, `build/`, `.github/`, `pyproject.toml`, `requirements*.txt`, `.importlinter`.

## Unresolved gaps / assumptions

- **Wizard step drift** (spec 8 vs code 9) — recorded in `.claude/patterns/ui/eight-step-wizard.md`; needs a separate governed change (not made here).
- **AI layer (Ask Fin, providers)** — design-only; no implementation created.
- `.ai-dev/memory.md` operational state remains placeholder (as before — filled by the responsible role/human).

## Human decisions still required

- Whether/when to build the Release-2 AI layer (Ask Fin + provider), and provider selection (`ADC-03`) — human-only.
- Resolution of the wizard step-count drift — human-only.
- Adoption of this architecture into the default branch (currently on the migration branch).
