# Migration Record — AI Engineering Architecture (2026-07-23)

This is the organizational-history record of the migration from the original eleven-role
agent architecture to the layered, Claude-native AI engineering architecture. The full
technical deliverables live in [`docs/ai-architecture/`](../../docs/ai-architecture/).

## What changed

- **Executable AI assets became canonical under [`.claude/`](../../.claude/)**: three orchestration
  agents, reusable skills, workflow recipes, standards, templates, patterns, and a tech-stack profile.
- **`.ai-dev/` was repurposed** as the permanent **AI Engineering Organization layer** — governance,
  philosophy, migration history, and organizational documentation. It is no longer an executable layer.
- **The eleven role contracts were retired** as active executable agents. Their expertise was migrated:
  - product-owner → PO agent + `requirements` skill
  - architect → Architect agent + `architecture-design` skill
  - coding → Developer agent + `backend-implementation` / `ui-shell-implementation` skills
  - verification-testing → `testing` skill
  - governance-reviewer → `governance` skill + `review` (governance mode)
  - remediation → `remediation` skill
  - product-owner-reviewer / architecture-reviewer / code-reviewer / testing-reviewer / remediation-reviewer
    → `review` skill modes + `recipes/review/run-independent-review.recipe.md`
- **Independent review** is preserved as a first-class capability executed in a separate, read-only,
  fresh context (no dedicated reviewer agent). A generating execution can never issue its own verdict.

## Preservation

The eleven original contracts are archived verbatim in
[`legacy-role-contracts/`](legacy-role-contracts/) and in Git history. No product code,
prototype behavior, or approved specification was changed by this migration.

## Authority for this change

The migration was explicitly requested and human-approved through a plan-first, gated process.
Updating the AI-development governance workflow documents was in scope for that reason.
`specs/` (including `specs/constitution.md`) remained authoritative and untouched.
