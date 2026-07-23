# FinSight — Build Readiness Runbook

**Document:** 12-build-readiness-runbook.md
**Status:** Draft for team review and design-review board
**Date:** 2026-07-16
**Scope:** Everything that must occur **before implementation begins** — the path from **Design Complete → Build Ready → Claude-Led Implementation**. This is an operational transition plan, not a design document. It introduces no product scope, no features, no AI capabilities, and revisits no decision except where implementation readiness strictly requires it.
**Governing methodology:** Spec-Driven Development (DEC-010, NFR-073). This runbook operationalizes the SDD framework (the `sdd` and `engineering-standards` plugins) for FinSight's transition to build.
**Sources of truth:** 00–11 (the complete design set) · the Final Specification Consistency Review · the Build-Readiness Review · DEC-001–DEC-034 · the architecture's ADC candidates (06 §26) and open questions (06 §25).
**Implementation intent (context):** the long-term intention is for **Claude to implement FinSight under human accountability**; there is currently **no dedicated development team**. This runbook therefore treats "readiness" as *readiness for a capable implementer (human or Claude) to build with minimal ambiguity, under the same governance, traceability, quality, accessibility, and auditability that governed design* (11-development-methodology.md).
**Numbering note:** produced as `12-build-readiness-runbook.md`, following `11-development-methodology.md` (per the proposed DEC-031 renumbering). Pending ratification with the DEC-024–034 batch.

---

## 1. Purpose

To answer one question honestly: **"Are we truly ready to start building FinSight?"** — and, where the answer is "not yet," to define every prerequisite, its owner, and its exit criteria so the gap is closable. The runbook exists because implementation quality, traceability, governance, maintainability, accessibility, and auditability must remain exactly as strong during build as they were during design; readiness is what makes that guarantee real rather than hoped-for.

It does **not** design anything. It sequences the transition activities the Build-Readiness Review identified: (1) ratify DEC-024–034; (2) operationalize the framework; (3) create the constitution; (4) cut the first baseline; (5) raise ADRs; (6) generate the traceability matrix; (7) prepare the walking skeleton; (8) resolve open-question ownership.

## 2. Current State Assessment

**Design: complete and coherent.** Eleven approved design documents (00–11) fully specify the product; the Final Consistency Review found no Critical or Major *contradictions* and scored the set Health 8.5 / Consistency 8.5 / Traceability 8.

**Build: not yet started, and not yet enforced.** Verified project state:

| Asset | State | Implication |
|---|---|---|
| `docs/00–11` | Present, approved *design* baseline | Source content is ready |
| `specs/` tree (framework-enforced) | **Absent** | SDD guarantees not yet operative for FinSight |
| `constitution.md` | **Absent** | No encoded principles / decision rights / quality bars / glossary |
| `specs/baselines/` (immutable baseline) | **Absent** | No sealed, hashed scope; nothing to trace against |
| ADRs (`specs/adr/`) | **Absent** | Technology unbound; ADC-01–11 are candidates only (06 §26) |
| `specs/plans/`, `tasks/`, `verification/` | **Absent** | No feature planned/tasked/verified yet |
| `specs/traceability.md` | **Absent** | Traceability asserted (manual §27/§20), not tooling-proven |
| Source code / tests / golden datasets | **Absent** | No implementation exists |
| DEC-024–034 | **Proposed 🔶 (pending ratification)** | Foundations provisional |
| Open questions | OQ-1..8 open (OQ-9 closed); AOQ-01..07 open | Parameter values + technology + AI-production gates outstanding |

**Conclusion:** FinSight is at the boundary between an approved *design* baseline and an enforced *build* baseline. Crossing that boundary is the entire content of this runbook.

## 3. Build Readiness Overview

Readiness is organized as **five sequential gates**, each with a clear exit criterion. Later gates depend on earlier ones; the walking skeleton (Gate 5) is the first implementation slice and passing it is the **GO** point.

```
Design Complete
   │
   ▼
G1  Decision Ratification ──▶ G2  Framework Operationalization ──▶ G3  Architecture Binding (ADRs)
   (DEC-024–034 ✅)            (specs/ + constitution + baseline)      (skeleton ADRs Accepted)
                                                                              │
   Build Ready  ◀── G5  Walking Skeleton Ready ◀── G4  Implementation Readiness
   (GO)             (plan+tasks approved, thread runs)   (CI, trace gate, both-OS runners, golden framework)
   │
   ▼
Claude-Led Implementation (walking skeleton first, then first-wave epics)
```

Parallelizable, non-blocking work (runs alongside the gates): assign OQ owners/dates; author the constitution draft; prepare synthetic golden datasets; apply the deferred documentation cleanups (numbering, Fin naming, FR-093 annotation) as change-controlled edits post-ratification.

## 4. Build Readiness Gates

### Gate 1 — Decision Ratification
- **Purpose:** make the design's foundations official; the design documents currently rest on proposed (🔶) decisions.
- **Activities:** team review and ratification of **DEC-024–DEC-034**; flip 🔶 → ✅ with approval date; record ratification evidence.
- **Dependencies:** none (internal decision).
- **Owner:** Project owner (Aditi) + design-review board.
- **Deliverables:** ratified DEC-024–034 in `09-decision-log.md`.
- **Success criteria:** every DEC-024–034 is ✅ Decided with a date; no proposed entry remains that a design document depends on.
- **Exit criteria:** decision log shows no 🔶 entries in the load-bearing set; the wizard, Fin, no-agents, reconciliation-in-findings, readiness step, and UI foundations are ratified.

### Gate 2 — Framework Operationalization
- **Purpose:** convert the approved `docs/` design into the framework's **enforced `specs/`** source of truth, so the SDD guarantees (baseline immutability, gated flow, trace gate) become operative.
- **Activities:** `/sdd:init` scaffold; author and commit the **constitution** (§7); **migrate `docs/00–11` into `specs/`, normalized to the framework's greppable shapes** (item headings like `### FR-042 — …`, zero-padded IDs, explicit `Status:` fields, checkbox tasks) per the spec-templates skill; run `/sdd:analyze` to confirm cross-artifact consistency; `/sdd:workbook` to capture per-requirement approval decisions; `/sdd:baseline` to cut the **first immutable baseline** (§8); confirm the three hooks are active (session-status, baseline-immutability, spec-lint).
- **Dependencies:** Gate 1.
- **Owner:** Project owner + design-review board; stakeholder sign-off where the constitution encodes Amerisure principles.
- **Deliverables:** `specs/constitution.md`; `specs/` tree populated (00–11 normalized); `specs/workbooks/WORKBOOK-<date>.md`; `specs/baselines/v1.0/BASELINE.md` (SHA-256 manifest + approval record).
- **Success criteria:** `/sdd:analyze` reports no blocking inconsistencies; `/sdd:baseline` produces a valid manifest; the baseline-immutability hook blocks a test write under `specs/baselines/` (exit 2).
- **Exit criteria:** requirements are `Baselined`; downstream commands (`/sdd:plan` etc.) accept the baselined scope; a write to a baseline is hook-blocked.

### Gate 3 — Architecture Binding (ADRs)
- **Purpose:** bind the technology the architecture deliberately deferred, so code is unambiguous.
- **Activities:** raise the **skeleton-critical ADRs** from ADC-01–11 via `/sdd:adr` (§9), each design-panel-reviewed; resolve the corresponding architecture open questions (AOQ-01..07) as those ADRs are decided; confirm DEC-003/DEC-004 directional stack (Python core / desktop shell / embedded store behind DAL) as Accepted ADRs or supersede with reasons.
- **Dependencies:** Gate 2 (ADRs trace to baselined requirements; the constitution's decision rights govern who accepts them).
- **Owner:** Software-architect (lead) + design panel (`software-architect, data-architect, integration-architect, security-engineer, qa-engineer`); project owner accepts.
- **Deliverables:** Accepted `specs/adr/ADR-001…` for at least the skeleton-critical set; review records.
- **Success criteria:** every skeleton-critical ADR is **Accepted** with Traces-to and a Verification method; no skeleton component depends on an undecided technology.
- **Exit criteria:** the walking skeleton can be planned and coded against decided technology; deferred ADRs are explicitly listed with their trigger.

### Gate 4 — Implementation Readiness
- **Purpose:** make the environment and the quality machinery ready so the first line of code is born gated.
- **Activities:** stand up the repository (single repo, §6 of 11); install and pin the plugin toolchain; configure **CI running on both Windows and macOS** (NFR-029); wire the **traceability CI gate** (`/sdd:trace --fail-on-orphans`, grep `^TRACEABILITY: PASS$`); scaffold the **test harness** (unit / golden-dataset / determinism / provider-swap / accessibility / security categories) per 11 §11; build the **synthetic golden-dataset framework** (seeded exceptions; no real data — NFR-018); establish dev-data-hygiene controls (implementer, incl. Claude, sees synthetic/sanitized data only); prepare the **Claude implementation inputs** (§14).
- **Dependencies:** Gate 2 (parseable `specs/`), Gate 3 (stack decided).
- **Owner:** Project owner + (build lead once assigned) + design-review board for gate config.
- **Deliverables:** repo skeleton; CI config (both OS + trace gate); test harness scaffolding; at least one synthetic golden dataset; dev-data-hygiene guard.
- **Success criteria:** CI runs green on a trivial change on both OSes; `/sdd:trace` executes and emits a verdict; the golden-dataset framework can express "expected findings for a seeded month."
- **Exit criteria:** a change cannot merge without green both-OS CI and `TRACEABILITY: PASS`; the environment is ready to run the skeleton.

### Gate 5 — Walking Skeleton Ready
- **Purpose:** confirm the first implementation slice is fully specified, planned, and runnable — the immediate pre-build state.
- **Activities:** `/sdd:plan` the first feature (a minimal slice of E-01/E-02, e.g., GED extraction + one rule) with acceptance criteria (acceptance-designer); design-panel review; `/sdd:tasks` decompose into `T-###`; confirm the skeleton's ADRs are Accepted (Gate 3) and the environment is ready (Gate 4); define the skeleton's validation criteria (§11).
- **Dependencies:** Gates 1–4.
- **Owner:** Project owner + design panel; Claude (supervised) as implementer at start.
- **Deliverables:** `specs/plans/PLAN-F-…`, `specs/tasks/TASKS-F-…`, an approved review record, the skeleton validation checklist.
- **Success criteria:** the skeleton plan is **Approved** by the design panel; tasks are half-day and test-mapped; every skeleton-critical ADR is Accepted.
- **Exit criteria (= GO):** implementation of the walking skeleton may begin; passing the skeleton's validation criteria (§11) is the proof the architecture holds.

## 5. Decision Ratification Plan (DEC-024–DEC-034)

**Why it matters:** every design document (06–11) asserts concepts whose decisions are still 🔶 proposed. Until ratified, the foundations are provisional and Gate 2's baseline would seal *un-ratified* scope. Ratification is therefore the first gate.

**Recommended order (lowest-dependency → highest, all fast/internal):**

| Order | DECs | Group | Build impact |
|---|---|---|---|
| 1 | **DEC-034, DEC-033, DEC-032** | AI guardrails + Fin persona | Confirm the AI layer's shape and boundary; R2, but ratifying now prevents rework in the Fin surfaces |
| 2 | **DEC-026, DEC-028, DEC-027** | Findings/reconciliation, readiness step, verification ritual | Directly shape first-wave epics (E-01/E-05/E-06); needed before planning those features |
| 3 | **DEC-024, DEC-025** | Guided wizard, Recent Reviews | Shape the shell/navigation (E-14) and cycle model |
| 4 | **DEC-029, DEC-030** | Review Health FUTURE-only, UI foundations | Confirm R1 exclusion (Review Health) and UI system; guards scope |
| 5 | **DEC-031** | Document renumbering | Enables the deferred cross-reference cleanups |

**Dependencies:** none external; all are internal team decisions. **Sequencing note:** ratify as a single batch if the board prefers; the order above only matters if ratification is incremental. On ratification, execute the deferred cleanups (numbering, Fin naming in 07/08, FR-093 annotation in 01) as change-controlled edits — *after* Gate 2 exists, these go through `/sdd:change`.

## 6. Framework Operationalization Plan (`docs/` → `specs/`)

The transition, in order:

1. **Scaffold** (`/sdd:init`): create the `specs/` tree and the CLAUDE.md contract; install/pin plugins.
2. **Constitution** (`/sdd:constitution`): author and commit `specs/constitution.md` (§7) — governance is activated here.
3. **Migrate & normalize:** move `docs/00–11` into `specs/`, reshaping to the framework's greppable conventions so the lint, `/sdd:trace`, and `/sdd:status` can parse them:
   - requirement items as headings with zero-padded IDs and explicit `Status:` fields (the current bold-prefix style must be normalized);
   - features/epics/rules keep their `F-##-##` / `E-##` / `R-<FAM>-##` IDs;
   - preserve every traceability table (they become the seed for the generated matrix).
   *This is mechanical but non-trivial; treat it as a reviewed activity, not a copy-paste.*
4. **Analyze** (`/sdd:analyze`): cross-artifact consistency check before approval; fix any drift the review already flagged (numbering, FR-093) here.
5. **Governance activation:** confirm the three hooks fire (session-status inject, baseline-immutability hard block, spec-lint on edit).
6. **Approve** (`/sdd:workbook`): capture per-requirement Approve/Disapprove decisions with a signed workbook.
7. **Baseline** (`/sdd:baseline`): cut `v1.0` (§8).
8. **Traceability readiness** (`/sdd:trace`): generate the first matrix (pre-code, so code/test columns are empty but the FR→feature→plan chain is proven) and wire the CI gate (§10).

**Review readiness:** confirm the engineering-standards review board is installed and the design panel preset resolves, so `/sdd:plan` reviews can run at Gate 5.

## 7. Constitution Readiness

*(Do not generate the constitution here — this defines readiness to create it later.)*

- **Purpose:** the project's governing, versioned contract — the non-negotiable principles, the shared vocabulary, who may decide what, and the quality bars every artifact must clear. It is the root the baseline and all ADRs trace up to.
- **Ownership:** authored by the project owner + design-review board; **stakeholder (Amerisure) sign-off** where it encodes Amerisure principles/decision rights; amended only under an approved change request.
- **Expected contents:**
  - **Principles (non-negotiable):** Trust > AI; deterministic core is the system of record; verification before analysis; AI explains/never decides; human decision ownership; accessibility first (meaning never by color alone); no real data in development; auditable by construction. *(These are restatements of already-approved principles — no new scope.)*
  - **Glossary (ubiquitous language):** GED, RAG status, readiness, cleared/`clrd`, reconciliation-eligible, workspace vs. finding, `VerifiedDataset`, Review Cycle, Fin / Ask Fin / Explain This, materiality, cold start — one definition source to end terminology drift (closes review gap G-2).
  - **Decision rights:** who approves baselines, CRs, ADRs, and panel conditions; how OQ resolutions are recorded; the human-accountability rule for AI-assisted/agent-built code.
  - **Quality bars:** determinism + provider-swap as release gates; test-first; golden-dataset acceptance; accessibility per story; `TRACEABILITY: PASS`; the full Definition of Done (11 §15).
- **Acceptance criteria:** covers all four content areas above; every principle traces to an existing source (no invented scope); ratified by the board and stakeholders; committed at `specs/constitution.md`; referenced by the first baseline.

## 8. Baseline Readiness

- **What becomes baselined:** the complete, normalized, approved spec set (00–11 in `specs/`) plus the constitution — the sealed scope the build implements and traces against.
- **Approval requirements:** a completed `/sdd:workbook` with a per-requirement Approve decision and a signed approval record; no in-scope item left `Draft`; DEC-024–034 ratified (Gate 1).
- **Evidence requirements:** a **per-file SHA-256 manifest** and the recorded approval evidence (who approved, when) — the audit artifact proving "this exact scope was sealed."
- **Versioning strategy:** semantic `v<major>.<minor>` — the first baseline is **v1.0**; scope changes after v1.0 flow through `/sdd:change` (CR-###) and are re-baselined in batches at the boundary (11 §17); the sealed baseline is never edited.
- **Baseline protection:** the PreToolUse hook hard-blocks all writes under `specs/baselines/` (no prompt, however persuasive, can edit a sealed baseline); verified by the test write returning exit 2.
- **Success criteria:** `v1.0/BASELINE.md` exists with a valid manifest and approval record; `/sdd:plan` and downstream commands accept the baselined requirements; an attempted baseline edit is blocked.

## 9. ADR Readiness

The architecture enumerated **ADC-01–ADC-11** (06 §26) as decision candidates and the architecture open questions **AOQ-01..07** (06 §25) as their inputs. None is yet an ADR. Recommended sequence and priority:

**Must exist before any coding (skeleton-critical):**

| Priority | ADR (from ADC) | Binds | Resolves | Why before code |
|---|---|---|---|---|
| 1 | **ADC-01** — shell + application-core stack & core/shell/storage separation | the whole stack | AOQ-01/02 | nothing can be coded without the language/runtime/shell |
| 1 | **ADC-02** — layering, dependency rule, core-owned ports (Findings query/command, audit) | module structure & the AI/deterministic boundary | — | defines where every unit lives and the AI/deterministic boundary (enforced by construction + a CI architecture-fitness test; Python — not the compiler) |
| 1 | **ADC-05** — exact-decimal arithmetic + cross-platform determinism harness | all financial math & the both-OS gate | AOQ-04 | determinism is unretrofittable; the skeleton's rule needs it day one |
| 1 | **ADC-06** — persistence: repository interfaces & substitution | the DAL | AOQ-01 | the skeleton persists and must survive force-kill |
| 2 | **ADC-10** — Review-Cycle state model & `VerifiedDataset` | the verification gate | — | the skeleton's hard gate is this type |
| 2 | **ADC-09** — audit event schema + core-owned port | audit-from-story-one | AOQ-06 (tamper-evidence R2) | audit is a DoD clause from the first story |
| 2 | **ADC-11** — findings model/experience split | the one finding | — | the skeleton produces one finding through this contract |

**Recommended before real/pilot data (not required for a synthetic-data skeleton):**

| Priority | ADR | Binds | Note |
|---|---|---|---|
| 3 | **ADC-08** — at-rest protection & secrets storage | data protection (TB-05) | needed before any real data lands on a machine |
| 3 | **ADC-07** — single consented-egress chokepoint | the "no second outbound path" invariant | set the invariant early even if AI is R2 |

**Deferrable to their phase (with explicit trigger):**

| ADR | Trigger to raise |
|---|---|
| **ADC-04** — workflow orchestration mechanism (full) | the skeleton may use a minimal deterministic sequencer; full ADR when orchestration grows (AOQ-03) |
| **ADC-03** — AI provider adapter & grounding enforcement | E-09 / Release 2, gated on OQ-3 |

**Success criteria:** the seven skeleton-critical ADRs are Accepted (design-panel reviewed) before Gate 5 exit; deferred ADRs are listed with triggers so nothing is silently forgotten.

## 10. Traceability Readiness

- **Matrix generation:** `/sdd:trace` scans `specs/` for IDs and the codebase for `Implements:`/`Verifies:` annotations, generating `specs/traceability.md` — **never hand-edited**. Runs first at Gate 2 (pre-code: proves FR→feature→plan) and continuously thereafter.
- **Required annotations:** implementing units carry `Implements: FR-###, F-##-##` (rules add `R-<FAM>-##`); tests carry `Verifies: FR-###/NFR-###`. These arrive with code, starting at the skeleton.
- **CI integration:** CI runs `/sdd:trace --fail-on-orphans` and gates the merge on `grep -q "^TRACEABILITY: PASS$"`.
- **PASS criteria:** every Must-priority FR/NFR has a verified chain (requirement → feature → plan → tasks → `Implements:` code → `Verifies:` test / VERIFY record), every hop evidenced; **zero orphans** in both directions.
- **Orphan detection:** spec→nothing (declared but not delivered) and code→nothing (delivered but not declared) are both defects, fixed at the spec or annotation — never by editing the matrix.
- **Merge readiness impact:** no merge lands with unimplemented Must scope or unannotated/unapproved code.
- **Implementation readiness impact:** trace **cannot run until Gate 2** (specs must be in `specs/` with parseable IDs) — so Gate 2 is a hard prerequisite for the trace gate, and thus for merge-gating any code.

## 11. Walking Skeleton Readiness

*(Source of truth: DEC-022 and 06 §21. Do not generate implementation code.)*

- **Goal:** prove the architecture's load-bearing boundaries end-to-end **before** any capability breadth — if one thread cannot run through the boundaries, they are wrong, and that is discovered on day one.
- **Scope (one of everything):** **one upload → one extraction (with lineage) → one verification approval (the gate) → one deterministic rule → one finding (severity + evidence + trace) → one summary line → one export**, with **audit and transactional persistence on from story one** and the **cross-platform determinism test** running day one.
- **Boundaries (deliberately excluded):** no capability breadth (only one rule), no AI/Fin (proves AI-off completeness by construction — FR-095), no historical/comparison, minimal shell/navigation, synthetic data only.
- **Required architecture components (minimal slices):** C-01 (shell), C-02 (cycle orchestrator — minimal sequencer), C-03 (intake), C-04 (extraction+lineage), C-05 (minimal quality/readiness), C-06 (verification gate), C-07 (engine, one rule), C-08 (config, minimal), C-09a/C-09b (finding model + minimal experience), C-12 (summary/export line), C-14 (audit via port), C-17 (DAL).
- **Required ADRs:** the seven skeleton-critical ADRs (§9) — ADC-01/02/05/06/09/10/11 (plus a minimal orchestration approach pending full ADC-04).
- **Required tests:** unit (the one rule, the extraction); **one golden dataset** (seeded synthetic month → the one expected finding); **determinism** (repeat-run byte-identical); **cross-platform** (same result Windows + macOS); **verification-gate integration** (analysis cannot run without approval — `VerifiedDataset` unconstructible otherwise); **audit assertion** (every step emits an event); **crash-safety** (force-kill mid-run loses no verified data).
- **Validation criteria (proof the architecture holds):** the gate blocks unverified analysis by construction; the AI-off path is complete; force-kill loses nothing (NFR-005); results are byte-identical on both OSes (NFR-029); audit records exist for every step; the finding traces to its rule/inputs/source in one hop.
- **Success criteria:** the single thread runs end-to-end; all skeleton tests green on both OSes; `/sdd:verify` passes the skeleton feature; `/sdd:trace` returns PASS for it. Passing this = the architecture is proven and breadth can begin (first wave: E-14, E-01, E-02, E-08, E-06).

## 12. Open Question Review

All open questions across the set, categorized by build impact. *(OQ-9 is closed — DEC-017.)*

**Blockers (must resolve before the dependent build activity):**

| ID | Question | Owner | Impact | Timing | Implementation risk |
|---|---|---|---|---|---|
| **AOQ-01/02/04/06** (→ ADRs ADC-01/02/05/06/09) | Persistence tech + at-rest; shell + core stack; exact-decimal + determinism harness; audit schema | Software-architect + design panel | Blocks all coding — technology unbound | **Gate 3** | **High** if skipped: ambiguous/incoherent code |

**Build-time decisions (resolve during build; land as configuration or minor decisions, not code blockers):**

| ID | Question | Owner | Impact | Timing | Implementation risk |
|---|---|---|---|---|---|
| **OQ-5** | Missing-entry baseline: history-derived vs. finance-maintained | Aditi → finance | Selects R-GED-03 variant; **value/config**, logic exists both ways | Before the GED rule pack ships (R1) / before pilot | Low-Med: build logic now with configurable mode |
| **OQ-7** | Official monthly cutoff calendar | Aditi → finance | R-GED-04 parameter value (`CP-CUTOFF-CALENDAR`) | Before pilot | Low: configurable interim; real value plugs in |
| **OQ-8** | Materiality thresholds / severity bands | Aditi → finance | Rule severity/RAG **values** (DEC-019: config, not logic) | Before a trustworthy pilot | Low-Med: golden datasets use synthetic values |
| **OQ-6** | Personas (leader/delegate/both) | Team (internal) | Workflow/verification UX detail | Early, non-blocking | Low: answerable internally |
| **AOQ-03/05/07** (→ ADRs ADC-04/07/08) | Orchestration mechanism; egress chokepoint; backup/disposal | Software-architect | Needed before their features/pilot data | Gate 3 (partial) / before pilot | Med: skeleton uses minimal versions |

**Future decisions (do not affect R1 build / walking skeleton):**

| ID | Question | Owner | Impact | Timing | Implementation risk |
|---|---|---|---|---|---|
| **OQ-1** | Amerisure security validation of consent model | Aditi → Amerisure security | **AI-layer production gate (E-09, R2)** | Before AI ships | None for R1 (AI off, FR-095) |
| **OQ-3** | Approved managed AI endpoint | Aditi → stakeholders | AI provider binding (ADC-03, R2) | Before AI ships | None for R1 |
| **OQ-2** | Invoice/PO/SOW/rate-card samples | Aditi → stakeholders | Gates E-12 (Phase 3) | Before invoice build | None for R1/R2 |
| **OQ-4** | Project/workstream mapping files | Aditi → stakeholders | Future analysis dimension | Future | None now |

**Key readiness insight:** the only build blockers are the **architecture ADRs** (AOQ→ADC). Rule parameter values (OQ-5/7/8) are **configuration**, not code blockers (DEC-019) — the walking skeleton and first-wave logic can be built with synthetic/configurable defaults and golden datasets. The AI open questions (OQ-1/3) gate **Release 2 only** and must not delay R1.

## 13. Risk Assessment

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **BR-1** | Coding begins before ADRs (technology unbound) | Med | High | Gate 3 is a hard prerequisite for Gate 5; skeleton-critical ADRs Accepted first |
| **BR-2** | Claude-led build with no dev team → ambiguity/quality risk | Med | High | Strong specs + tight gates + human acceptance of every merge; walking-skeleton-first; §14 inputs complete before start |
| **BR-3** | `docs/`→`specs/` migration loses ID/shape fidelity, breaking trace/lint | Med | Med | Treat migration as a reviewed activity; run `/sdd:analyze` + a trial `/sdd:trace` before baseline |
| **BR-4** | Cross-platform determinism gaps found late | Med | High | ADC-05 + both-OS CI from Gate 4; determinism/golden tests on the skeleton's single rule |
| **BR-5** | Parameter-value vacuum (OQ-5/7/8) delays or produces an untrustworthy pilot | Med | Med | Build with configurable defaults + golden datasets now; chase finance owners with dates; real values plug in pre-pilot |
| **BR-6** | Confidential/real data reaches the implementer (incl. Claude) or an external tool | Low | High | Synthetic/sanitized only (NFR-018); dev-data-hygiene guard at Gate 4; treat external AI tools as governed egress |
| **BR-7** | Scope creep during build (features added without a CR) | Med | Med | SDD gates + DoD + YAGNI; `/sdd:change` is the only path to new scope |
| **BR-8** | E-02 (Rules Engine) enabler starvation stalls the first wave | Med | High | Protect enabler capacity; skeleton exercises the engine day one (AR-04) |
| **BR-9** | AI open questions (OQ-1/3) mistaken as R1 blockers, delaying build | Low | Med | Runbook classifies them as R2-only; R1 ships AI-off (FR-095) |

## 14. Claude Implementation Readiness Assessment

**Question:** *What is still missing before Claude could begin implementation with minimal ambiguity?* The specs are strong; the gaps are almost entirely **technology binding, environment, and test fixtures** — not product understanding.

**Missing implementation inputs (required before Claude starts):**
1. **Confirmed technology stack (ADRs ADC-01/02/05/06)** — *the single biggest gap.* Claude cannot write coherent code without the language/runtime, shell, module/port structure, decimal/determinism approach, and persistence interface decided. DEC-003/004 are directional, not binding.
2. **A runnable environment** — repository, pinned plugin toolchain, and **both-OS CI** (NFR-029). Claude needs somewhere to build, test, and gate.
3. **Synthetic golden datasets** — seeded synthetic month(s) encoding *expected findings* for the rule(s) being built; TDD and rule packs depend on them (NFR-036/038). The real GED/Budget Tracker samples exist but development must use synthetic/sanitized data only (NFR-018).
4. **The first feature planned and tasked** — `PLAN-F-…` + `TASKS-F-…` (with acceptance criteria) for the walking-skeleton slice; Claude implements *against tasks*, not against prose.
5. **The traceability + CI gate wired** — so Claude's `Implements:`/`Verifies:` annotations are checked and `TRACEABILITY: PASS` gates merges.

**Missing decisions:** the architecture open questions behind the skeleton-critical ADRs (AOQ-01/02/04/06); a minimal orchestration approach (light ADC-04). *(Rule parameter values OQ-5/7/8 are NOT required to start — configurable defaults + golden datasets suffice; real values pre-pilot.)*

**Missing ADRs:** ADC-01, 02, 05, 06, 09, 10, 11 (skeleton-critical); ADC-08 before real data; ADC-03/04/07 deferrable.

**Missing governance artifacts:** the constitution (principles, decision rights, quality bars, glossary — Claude's guardrails and ubiquitous language); the first baseline (the sealed scope to build against); a signed workbook.

**Missing traceability artifacts:** `specs/` in parseable shape; `specs/traceability.md` (generated); the CI gate.

**What is NOT missing (ready now):** the product understanding, requirements, rules logic, architecture structure, UX flows, UI system, and AI boundary are fully specified and internally consistent — Claude has an unusually complete design to build from. The DoD, testing expectations, and review triggers are defined (11). **Conclusion:** close the technology/environment/fixture gaps (Gates 3–4) and produce the first plan+tasks (Gate 5), and Claude can implement the walking skeleton with minimal ambiguity under full governance.

## 15. Build Readiness Checklist

- [ ] **G1** DEC-024–034 ratified (🔶 → ✅) with dates
- [ ] **G2** `/sdd:init` run; plugins installed and pinned
- [ ] **G2** Constitution authored, ratified, committed (`specs/constitution.md`)
- [ ] **G2** `docs/00–11` migrated + normalized into `specs/` (IDs/shapes parseable)
- [ ] **G2** `/sdd:analyze` clean; deferred cleanups (numbering, Fin naming, FR-093) applied
- [ ] **G2** Workbook completed + signed; **first baseline `v1.0` cut** (SHA-256 manifest + approval)
- [ ] **G2** Baseline-immutability hook verified (test write → exit 2)
- [ ] **G3** Skeleton-critical ADRs Accepted: ADC-01, 02, 05, 06, 09, 10, 11
- [ ] **G3** AOQ-01/02/04/06 resolved via those ADRs; deferred ADRs listed with triggers
- [ ] **G4** Repository stood up; both-OS CI green on a trivial change
- [ ] **G4** Traceability CI gate wired (`/sdd:trace --fail-on-orphans` → `TRACEABILITY: PASS`)
- [ ] **G4** Test harness scaffolded (unit/golden/determinism/provider-swap/accessibility/security)
- [ ] **G4** ≥1 synthetic golden dataset built; dev-data-hygiene guard active (synthetic only)
- [ ] **G4** Claude implementation inputs (§14) assembled
- [ ] **G5** First feature planned (`PLAN-F-…`) + design-panel approved
- [ ] **G5** Tasks decomposed (`TASKS-F-…`), half-day, test-mapped
- [ ] **G5** Walking-skeleton validation criteria (§11) agreed
- [ ] **OQ** Owners + due dates assigned to OQ-1/2/3/5/6/7/8 (R1-relevant: 5/6/7/8)

## 16. Go / No-Go Criteria

**GO — implementation of the walking skeleton may begin when ALL hold:**
- Gates 1–5 exit criteria met (checklist §15 complete).
- Skeleton-critical ADRs **Accepted**; stack unambiguous.
- `specs/` **baselined v1.0**; baseline hook enforcing.
- Both-OS CI green; **`TRACEABILITY: PASS`** gate live; golden-dataset framework ready.
- First feature **planned + tasked + panel-approved**; validation criteria agreed.
- Dev-data-hygiene (synthetic only) enforced.

**NO-GO — do not start coding if ANY is true:**
- Any skeleton-critical ADR is unaccepted (technology ambiguous) — **hard stop**.
- `specs/` not baselined, or the baseline hook not enforcing.
- Trace gate cannot run, or CI is not running on both OSes.
- DEC-024–034 unratified (foundations provisional).
- No synthetic golden dataset (nothing to TDD against).
- Real/confidential data present in the build environment.

**Risk indicators (proceed with caution / escalate):**
- Rule parameter values (OQ-5/7/8) unowned or undated — build logic with defaults but flag pilot risk (BR-5).
- Migration fidelity unverified (no trial `/sdd:trace`) — risk BR-3.
- AI open questions (OQ-1/3) being treated as R1 blockers — correct the misconception (BR-9), do not delay R1.

**Escalation paths:**
- Technology/architecture ambiguity → **design-review board** (software-architect lead).
- Requirement/scope ambiguity discovered in build → **`/sdd:change` (CR)** → project owner decides.
- OQ-1/OQ-2/OQ-3 (external) → **Aditi → Amerisure/finance stakeholders**; these gate R2/Phase-3/pilot, not R1 start.
- Governance/quality-gate conflict → **project owner + board**; gates are not waived to hit a date (NFR-032/048).

## 17. Recommended Next Actions

1. **Convene the ratification review** and approve DEC-024–034 (Gate 1) — fast, internal, unblocks everything.
2. **Operationalize the framework** (Gate 2): `/sdd:init` → author the **constitution** (§7) → migrate & normalize `docs/`→`specs/` → `/sdd:analyze` → `/sdd:workbook` → **baseline v1.0**. *(I can draft the constitution ready for `/sdd:constitution` on request.)*
3. **Raise the seven skeleton-critical ADRs** (Gate 3), design-panel-reviewed, resolving AOQ-01/02/04/06.
4. **Stand up the environment** (Gate 4): repo, both-OS CI, trace gate, test harness, first synthetic golden dataset, dev-data-hygiene guard.
5. **Plan + task the walking skeleton** (Gate 5); agree its validation criteria (§11).
6. **In parallel:** assign owners + due dates to OQ-5/6/7/8 (finance/internal); leave OQ-1/2/3 as R2/Phase-3 gates.
7. **Then declare GO** against §16 and begin the walking skeleton — the first proof the architecture holds.

---

*End of 12-build-readiness-runbook.md — the path from Design Complete → Build Ready → Claude-Led Implementation. No product scope, features, AI capabilities, or design decisions are introduced; the runbook only prepares the approved FinSight design for implementation. The only hard build blockers are the architecture ADRs; rule parameter values are configuration (DEC-019) and the AI open questions gate Release 2, not the Release-1 walking skeleton. Adopt on completion of Gate 1; declare GO on completion of Gates 1–5.*
