# Baseline v1.0 Approval Package (Gate 2)

> **Baseline approved under explicit project-owner approval.** `specs/` is the authoritative approved baseline. The immutable `/sdd:baseline` cut at `specs/baselines/v1.0/BASELINE.md` (hook-protected; a human runs the command) remains a human-run step; its SHA-256 manifest and signatures are not fabricated here (documentary date not recorded in repository).

- **Purpose:** assemble the preconditions and the human approval needed to cut baseline v1.0 (the sealed, hashed, approved scope the build implements and traces against).
- **Required human approvers:** **Project Owner + Technical Lead** (baseline approval, Constitution §4).
- **Evidence required:** (1) Gate-1 ratification complete; (2) Constitution adopted; (3) signed workbook; (4) `/sdd:analyze` clean; (5) the generated `specs/baselines/v1.0/BASELINE.md` containing a **per-file SHA-256 manifest** + this approval record referenced.
- **Acceptance criteria:** manifest hashes match the migrated `specs/` files; every in-scope requirement is `Status: Baselined`; the baseline-immutability hook is proven (exit 2 on a test write).

**Preconditions checklist** *(human confirms each before running `/sdd:baseline`):*
- [ ] DEC-024–034 ratified (Gate 1 record complete).
- [ ] `specs/constitution.md` Approved (adoption record complete).
- [ ] `docs/00–13` migrated + normalized into `specs/`; items `Status: Baselined`-ready.
- [ ] `specs/workbooks/WORKBOOK-<date>.md` signed.
- [ ] `/sdd:analyze` reports no blocking cross-artifact defects.

**Scope to be sealed in v1.0** *(the migrated set):* constitution; requirements (01/02); epics/features (03/04); rules catalog (05); architecture (06); UX (07); UI (08); decision log (09); AI & agents (10); dev methodology (11); readiness/skeleton planning (12/13); ADR-001–007; PLAN-F-02-02; TASKS-F-02-02.

**Approval decision** *(human completes):*
| Confirmation | Approver (name, role) | Date |
|---|---|---|
| Manifest generated; hashes verified against files | {…} | {…} |
| Baseline v1.0 approved and cut | {Project Owner} | {…} |
| Baseline v1.0 approved and cut | {Technical Lead} | {…} |

**Statement:** "Baseline v1.0 represents the approved FinSight scope as of this date; all future scope changes flow through `/sdd:change` (CR-###)."
