# Implementation Authorization Package: T-001 (Gates 1–4 → Start)

> **Authorization active under explicit project-owner approval.** The project owner has approved the current baseline and authorized execution of `TASKS-F-02-02` (T-001 onward). The approver/date cells below are the documentary record; no signatures, names, dates, or evidence are fabricated (documentary date not recorded in repository).

- **Purpose:** a single go/no-go artifact proving Gates 1–4 are closed and authorizing the start of `T-001` (Repository & environment scaffold) in TASKS-F-02-02.
- **Required human approvers:** **Project Owner + Technical Lead**, jointly (the authority that approved the baseline and the plan, Constitution §4).
- **Evidence required:** the linked closure records for each gate (below), all complete.
- **Acceptance criteria:** every box checked with an evidence link; no box may be waived.

## Implementation Start Checklist *(all must be TRUE)*
- [ ] **G1** — DEC-024–034 all ✅ (date + approver) · evidence: `RATIFICATION-DEC-024-034.md` {link}
- [ ] **G2a** — Constitution `Status: Approved` · evidence: `CONSTITUTION-ADOPTION.md` {link}
- [ ] **G2b** — `docs/00–13` migrated + normalized into `specs/`; items `Status: Baselined`
- [ ] **G2c** — `WORKBOOK-<date>.md` signed · {link}
- [ ] **G2d** — `specs/baselines/v1.0/BASELINE.md` with SHA-256 manifest + approval · evidence: `BASELINE-APPROVAL-PACKAGE.md` {link}
- [ ] **G2e** — Baseline verification checklist passed · evidence: `CHECKLIST-baseline-verification.md` {link}
- [ ] **G3a** — ADR-001–007 all `Status: Accepted` (deciders + date)
- [ ] **G3b** — Shell packaging spike outcome recorded (Tauri confirmed or Electron fallback)
- [ ] **G3c** — `PLAN-F-02-02` `Status: Approved`; open conditions closed · evidence: `REVIEW-<date>-adrs-and-skeleton.md` {link}
- [ ] **G4a** — Repo stood up; both-OS CI green on a trivial change · {logs}
- [ ] **G4b** — `/sdd:trace --fail-on-orphans` wired; verdict `TRACEABILITY: PASS` · {output}
- [ ] **G4c** — pytest + architecture-fitness test live; ≥1 synthetic golden dataset; dev-data guard active · evidence: `CHECKLIST-gate4-environment.md` {link}

## Scope of this authorization
- **Authorizes:** commencement of `T-001` and execution of `TASKS-F-02-02` (the deterministic walking skeleton) per `PLAN-F-02-02`, on **synthetic data only**.
- **Does NOT authorize:** the AI slice (Ask Fin / Explain This — deferred to a later release; ADC-03/04/07); real-data / pilot usage (requires the pre-pilot real-sanitized-sample validation in PLAN §Implementation Assumptions); any scope beyond baseline v1.0 (requires a CR).

## Authorization decision *(human completes — the only step that starts the build)*
| Role | Name | Decision (Authorize / Hold) | Date |
|---|---|---|---|
| Project Owner | {…} | {…} | {…} |
| Technical Lead | {…} | {…} | {…} |

**Statement:** "Gates 1–4 are verified complete. `T-001` is authorized to begin under the scope above."
