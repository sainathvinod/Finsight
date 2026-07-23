# Baseline Verification Checklist (Gate 2 exit)

> **Baseline verification is confirmed under the project-owner-approved baseline.** AI may run the commands and attach outputs; command outputs and results are not fabricated here.

- **Purpose:** prove Gate 2 is genuinely closed before Gate 3 begins.
- **Required human approvers:** **Project Owner + Technical Lead** (confirm exit).
- **Evidence required:** command outputs / logs attached per row.
- **Acceptance criteria:** every row checked with evidence; any failure re-opens Gate 2.

| # | Check | How to verify | Evidence attached | Pass? |
|---|---|---|---|---|
| 1 | Requirements are `Status: Baselined` in `specs/` | grep the migrated files / `/sdd:status` | {link} | {☐} |
| 2 | `specs/baselines/v1.0/BASELINE.md` exists with a per-file SHA-256 manifest | open file; recompute a sample hash | {link} | {☐} |
| 3 | Manifest hashes match the on-disk files | recompute + diff | {log} | {☐} |
| 4 | Signed `WORKBOOK-<date>.md` present as approval evidence | open workbook sign-off block | {link} | {☐} |
| 5 | Constitution `Status: Approved` + amendment history row filled | open `specs/constitution.md` | {link} | {☐} |
| 6 | `/sdd:analyze` reports no blocking defects | run `/sdd:analyze`; attach report | {report} | {☐} |
| 7 | Baseline-immutability hook blocks a write under `specs/baselines/` | `echo '{"tool_input":{"file_path":"specs/baselines/v1.0/BASELINE.md"}}' | <hook>; echo $?` → **exit 2 + block message** | {log} | {☐} |
| 8 | Spec-lint active on `specs/` edits (no duplicate item IDs) | trigger a test edit; observe lint | {log} | {☐} |

**Exit confirmation** *(human):* {name, role} · {date} — "Gate 2 verified; proceed to Gate 3."
