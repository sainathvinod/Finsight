# DRAFT — Gate 3 Design-Panel Review Record (Template)

> **DRAFT TEMPLATE — AI-prepared. No ADR is accepted and no plan is approved here.** Reviewer agents may generate the findings; **humans decide** the acceptances/approval below. AI must never accept an ADR or approve a plan (Constitution §5, §4; DEC-034). Copy to `specs/reviews/REVIEW-<yyyy-mm-dd>-adrs-and-skeleton.md` and complete.

> **This single record fulfils three requested artifacts:** (5) ADR acceptance review, (6) plan approval review, (7) design-panel review record — because the design panel reviews the ADRs and the plan together.

- **Purpose:** convene the design panel on the seven ADRs and PLAN-F-02-02, record findings and dissent, and capture the human acceptance/approval decisions that close Gate 3.
- **Required human approvers:** **Technical Lead / Software Architect** (ADR acceptance); **+ Project Owner** for the AI-boundary ADRs (layering/ports and findings model) and for **plan approval** (Constitution §4).
- **Evidence required:** this record completed; each ADR `Status: Accepted` (deciders + date); `PLAN-F-02-02` `Status: Approved` + link to this record; the shell packaging spike outcome recorded.
- **Acceptance criteria:** all seven ADRs Accepted; no open BLOCKER/CRITICAL finding; plan Approved with open conditions closed or owned; shell decision recorded.

## Panel
- **Preset:** design — `software-architect, data-architect, integration-architect, security-engineer, qa-engineer` (augment: `ai-governance-reviewer` for the AI boundary; `accessibility-engineer` for the UI slice).
- **Reviewers present / mode:** {human panel | AI reviewer-agents assisting, human deciders}

## Findings (standard format — `[SEVERITY] file:line — finding — grounded in <canon/spec-ID> — Fix:`)
{one per line; preserve dissent; findings without evidence are not findings}

## ADR acceptance decisions *(artifact 5 — human completes)*
| ADR | Panel verdict | Decision (Accept / Revise) | Deciders (name, role) | Date |
|---|---|---|---|---|
| ADR-001 Application Stack & Shell | {…} | {…} | {…} | {…} |
| ADR-002 Layering, Ports & Dependency Rules | {…} | {…} | {…} | {…} |
| ADR-003 Exact Decimal & Determinism | {…} | {…} | {…} | {…} |
| ADR-004 Persistence (SQLite) | {…} | {…} | {…} | {…} |
| ADR-005 Audit Event Architecture | {…} | {…} | {…} | {…} |
| ADR-006 Review Cycle & VerifiedDataset | {…} | {…} | {…} | {…} |
| ADR-007 Findings Domain Model | {…} | {…} | {…} | {…} |

## Shell packaging spike outcome (the stack ADR's required condition)
- **Result:** {Tauri + bundled-Python packaging + loopback IPC + code-signing validated in the restricted target env | fall back to Electron (no core change)} · **By:** {…} · **Date:** {…}

## Plan approval decision *(artifact 6 — human completes)*
| Plan | Panel verdict | Decision (Approve / Revise) | Approver (Project Owner) | Date |
|---|---|---|---|---|
| PLAN-F-02-02 Deterministic Walking Skeleton | {…} | {…} | {…} | {…} |

## Open conditions to close before / at approval
- [ ] Shell packaging spike outcome recorded (above).
- [ ] Synthetic materiality default confirmed (PLAN §Implementation Assumptions / R-BUD-02).
- [ ] Synthetic fixture layouts confirmed; real-sanitized-sample validation scheduled as a pre-pilot condition.

## Overall verdict *(human)*
{approved | approved with conditions (list + owners) | revise and resubmit} · **Recorded by:** {…} · **Date:** {…}

**On completion:** set each Accepted ADR → `Status: Accepted` (deciders + date); set `PLAN-F-02-02` → `Status: Approved` and link this record in its Review-board outcome + Status history.
