# Current-State Inventory (pre-migration)

Inventory of FinSight AI engineering assets as they existed before the 2026-07-23 migration. Product specs, code, and the vendored SDD framework are out of scope and unchanged.

## AI assets

| Path | Type | Purpose | Disposition |
|---|---|---|---|
| `.ai-dev/constitution.md` | governance | Rules & authority of the AI dev org | Repurposed (org layer); principles → `.claude/standards/` |
| `.ai-dev/manifesto.md` | philosophy | Why the org exists | Repurposed (org layer) |
| `.ai-dev/playbook.md` | workflow | 11-role stage flow | Rewritten to 3-agent flow |
| `.ai-dev/README.md` | org map | Reading order | Rewritten |
| `.ai-dev/bootstrap.md` | protocol | Session startup | Rewritten |
| `.ai-dev/memory.md` | state | Static/operational memory | Updated (layout + roles) |
| `.ai-dev/agents/*.md` (11) | executable role contracts | PO, Architect, Coding, V&T, Governance-Reviewer, Remediation + 5 reviewers | Expertise migrated to skills/review; archived to `.ai-dev/history/legacy-role-contracts/` |
| `.claude/agents/*.md` (11) | native wrappers | Thin pointers to `.ai-dev/agents/` contracts | Removed after validation (replaced by 3 agents) |
| `.ai-dev/prompts/*.md` (6) | prompt stubs | **Empty (0 bytes)** | Removed after validation |
| `.ai-dev/templates/*.md` (8) | template stubs | **Empty (0 bytes)** | Removed after validation (templates now in `.claude/templates/`) |

## Grounded technical facts (preserved)

- **Stack:** Python ≥3.10 (target 3.12); runtime dep `openpyxl` only; `pytest`, `ruff`, `import-linter`, `coverage`; SQLite confined to infrastructure. No API, no web/GUI framework — delivery is a text-mode wizard.
- **Layering:** `domain → application → infrastructure → delivery` (enforced by `.importlinter`).
- **Determinism:** exact `Decimal`, injected `Clock`; findings created only by the rules engine (`ADR-007`).
- **Data verification:** review-local corrections, immutable originals, **no source-system write-back**; `VerifiedDataset` is the only analysis input.
- **Audit:** append-only; tamper-evidence deferred to R2 (not immutable).
- **AI layer:** Ask Fin + providers are **specified-only (Release 2)**; **Ollama not selected**; provider abstraction required.
- **Deferred:** Invoice Review (`DEC-009`). **GED** = General Expense Detail.

## Reference surface (pre-migration)

Live references to `.ai-dev/` paths / the 11 role names existed only in: `CLAUDE.md` (3 lines), the 11 `.claude/agents/` wrappers (self-referential), and `.ai-dev/` internal docs. The vendored `spec-driven/` framework and `specs/`/`docs/` design-panel agent names are a **different** agent set and were not affected.
