# FinSight — Features Baseline

**Document:** 04-features.md
**Status:** LOCKED baseline — feature sets agreed and locked per epic in team brainstorming, 2026-07-10 (DEC-023). Changes go through the decision log.
**Guiding lens:** *"Monthly Review in a Box"* (Release 1) · **Trust > AI** (DEC-022)
**Companion documents:** 03-epics.md (locked epic baseline) · 01/02 requirements baselines · 09-decision-log.md
**Downstream numbering:** 05-rules-catalog · 06-architecture · 07-ux-design · 10-ai-and-agents · 11-development-methodology (09 remains the decision log)

---

## 1. Conventions

- **ID:** `F-ee-nn` = feature *nn* of epic *ee*. IDs are permanent; retired IDs are never reused.
- **Type:** Capability (stakeholder-demoable) or **Enabler** (fails the demo test but is a contract another epic's plan or the Definition of Done explicitly depends on — the only admissible justification).
- **Release:** R1 = required for "Monthly Review in a Box"; R2 = deepens it; some features split (R1 core / R2 scope noted inline).
- **Feature test applied throughout:** (1) demoable value a stakeholder recognizes; (2) named for what the user gets, not what the code does; (3) decomposes into multiple stories without being the whole epic. Enablers substitute test (1) with the dependency test above.
- Stories and acceptance criteria will be derived per feature in the next phase; acceptance criteria noted here are *binding feature-level criteria* agreed during brainstorming.

## 2. Cross-cutting patterns (binding)

### 2.1 The Rule-Pack pattern
Capability epics ship their business rules as **rule-pack features**: catalog entries implemented on E-02's engine. E-02 owns *how* rules execute (pipeline, versioning, determinism); the capability epic owns *that these rules exist and are correct*. Rule parameters, thresholds, tolerances, and match semantics are defined in the Rules Catalog (05) — the rule-pack feature is their implementation as working detection.
**Binding acceptance criterion for every rule pack:** *golden-dataset validation* — a seeded synthetic month produces exactly the expected findings, with correct severities and evidence traceable to source lines.

### 2.2 Enabler-feature criteria
An enabler feature is legitimate only when (a) another epic's plan or the DoD names it as a dependency, and (b) it is honestly labeled. "Enabler" is never a euphemism for architecture: storage design, frameworks, and engines-for-their-own-sake belong in 06-architecture. Current enablers: F-01-05, F-02-01–06 (whole epic), F-08-01, F-14-03, F-14-04.

### 2.3 The Workspace/Finding boundary principle
*A workspace row is work-in-progress; a finding is what survives the workflow.* During an active process (reconciliation now; invoice review in Phase 3), unresolved items are workspace tasks — not exceptions — and must not flood the findings inbox. When the cycle closes or the Operator explicitly escalates, residual unresolved items become findings with full lifecycle, severity, and Leader visibility. One underlying record, two presentations, one state machine — divergent statuses between surfaces are a trust defect.

### 2.4 Not-Features register (do not re-invent these as features)
- **Cross-platform identical results (NFR-029)** — a standing CI test on both platforms, not a buildable capability.
- **Error-handling quality (NFR-055/062/064)** — DoD clause 7.
- **Per-epic audit logging** — DoD clause 1, satisfied via F-08-01's contract.
- **Storage/DAL setup** — architecture (06); arrives with the walking skeleton; belongs to no feature.
- **"Report generation engine," "PDF renderer," "parsing engine," "normalization service"** — implementation internals of the features that need them.
- **RAG status as a standalone feature** — one deterministic aggregation rule (catalog entry on E-02) plus a display element in F-07-01.
- **Rule testing & validation framework** — development methodology (10) and DoD clauses 3–4.
- **Rule dependency management** — no requirement traces to it; deliberately rejected (YAGNI). Returns only via the decision log if the Rules Catalog proves a need.
- **Custom report builder** — unrequested; any future request goes through the decision log.

## 3. Feature overview

| Epic | R1 | R2 | Total |
|------|----|----|-------|
| E-01 Data Intake, Extraction & Verification | 9 (incl. F-01-04 warning scope) | 3 (incl. F-01-04 replacement scope) | 11 |
| E-02 Deterministic Rules Engine | 6 (F-02-05 R1 scope) | (F-02-05 R2 scope) | 6 |
| E-03 Budget Review & Analysis | 3 | 2 | 5 |
| E-04 GED Analysis & Exception Detection | 2 | 1 | 3 |
| E-05 Reconciliation Automation | 2 | 1 | 3 |
| E-06 Findings & Exception Management | 4 | 2 | 6 |
| E-07 Executive Reporting & Export | 3 (F-07-04 R1 core) | 1 (+ workbook export scope) | 4 |
| E-08 Audit & Compliance | 3 | 1 | 4 |
| E-14 Desktop Application Foundation & Experience | 6 | 1 | 7 |
| **Total (decomposed epics)** | | | **49** |

E-09 (AI Assistance, R2) and E-11/E-12/E-13 (future releases) are deliberately **not yet decomposed** — features are defined just-in-time when their release approaches (§13).

---

## 4. E-01 — Data Intake, Extraction & Verification

### F-01-01 — Monthly Review Cycle Workspace
- **Classification:** Capability, R1 · **Status:** Approved
Create/name a monthly review cycle; see its status at all times (loaded → verified → analyzed → reported) with outstanding items; pause and resume across days and restarts. **Scope extended (DEC-035, R1):** explicit, audited, non-destructive, reversible **abandonment** (`Active | Abandoned` disposition, orthogonal to analytical state) and deterministic **30/60-day inactivity reminders** (informational, non-blocking; no automatic expiry/archival/state change). *Traces:* FR-006, FR-081; NFR-006; ADR-014, DEC-035; FR-108 (non-destructive retention).

### F-01-02 — File Upload & Acceptance
- **Classification:** Capability, R1 · **Status:** Approved
Add Excel files (PDF in Phase 3 per FR-002); unreadable/corrupt/password-protected files rejected with plain-language reasons; source files never modified; full provenance recorded (name, fingerprint, user, timestamp). Hostile/malformed input cannot crash or corrupt. *Traces:* FR-001–003, FR-007, FR-010; NFR-012.

### F-01-03 — Document Recognition & Period Assignment
- **Classification:** Capability, R1 · **Status:** Approved
FinSight proposes each file's type and reporting month; the user confirms or corrects — user confirmation is authoritative. *Traces:* FR-004, FR-005.

### F-01-04 — Wrong-File Protection
- **Classification:** Capability, split release · **Status:** Approved
**R1:** duplicate-upload warning (content-identical file already in cycle). **R2:** versioned replacement with downstream re-run; MVP fallback is "discard cycle and redo." *Traces:* FR-008 (R1), FR-009 (R2).

### F-01-05 — Document Extraction Framework
- **Classification:** **Enabler**, R1 · **Status:** Approved
The contract for onboarding document types: type registration, extraction template interface, shared normalization and lineage services, confidence assignment. *Depended on by:* F-01-06/07 now; E-11 (resource sheets) and E-12 (invoices, POs, SOWs, rate cards) by explicit epic note. *Traces:* FR-013–016 (shared machinery).

### F-01-06 — GED Report Extraction
- **Classification:** Capability, R1 · **Status:** Approved
GED journal lines become verified structured data: all observed fields, structural noise handled (headers, subtotals, blanks), values normalized with raw originals preserved to cell level. **Includes accounting-event tagging** (payroll interface / reclass / accrual-reversal classification per FR-041) so tags are visible, reviewable, and correctable at verification — consumed by F-04-02 and F-05-01. *Traces:* FR-011, FR-013–015, FR-041 (classification half).

### F-01-07 — Budget Tracker Extraction
- **Classification:** Capability, R1 · **Status:** Approved
All three sheets (Details; Actuals incl. cleared markers; Original Budget bgt/atd/etc/eac) become structured data with lineage. *Traces:* FR-012, FR-014, FR-015.

### F-01-08 — Data Quality Gate & Quarantine
- **Classification:** Capability, R1 · **Status:** Approved
Schema and row-level checks; failing rows quarantined visibly — never blocking the month; subtotal self-check against the report's own totals; per-cycle data quality summary before verification. *Traces:* FR-021–025.

### F-01-09 — Verification Workspace
- **Classification:** Capability, R1 · **Status:** Approved
The mandatory human gate: review extracted data with one-click trace to source cell; low-confidence and quarantined items highlighted; correct values with original preserved and audit recorded; approve / approve-with-corrections / reject per document. Bulk approval of high-confidence data keeps the gate fast. **No analysis runs on unverified data.** *Traces:* FR-016 (display), FR-026–029; NFR-069.

### F-01-10 — Historical Onboarding Import
- **Classification:** Capability, R2 · **Status:** Approved
Bulk-load prior months at onboarding to establish baselines. *Traces:* FR-110. *R2 per DEC-022 — the first successful monthly review does not require it.*

### F-01-11 — Extraction Template Configuration
- **Classification:** Capability, R2 / Phase 2 · **Status:** Approved
Authorized users adjust extraction templates without code changes; changes versioned and audited. *Traces:* FR-017.

## 5. E-02 — Deterministic Rules Engine *(all features Enabler-class; users: rule authors, auditors, other epics, and end users where behavior is visible)*

### F-02-01 — Rule Definition & Registration Contract
- **Classification:** R1 · **Status:** Approved
How a rule exists: declared inputs, parameters, outputs, Rules-Catalog ID traceability, minimum-history declaration, per-rule test declaration. New rules are additions, never redesigns. *Traces:* NFR-044, NFR-076, NFR-033.

### F-02-02 — Deterministic Execution Pipeline
- **Classification:** R1 · **Status:** Approved
Fixed, predictable rule sequence per DEC-005; run records carry rule-set version, configuration version, and input fingerprints; emits rule-execution audit events (FR-086 — stored by E-08). Agents and AI can never select, skip, or alter rules.

### F-02-03 — Governed Rule & Parameter Management
- **Classification:** R1 · **Status:** Approved
Thresholds, tolerances, cutoffs, and reference data (account lists, vendor expectations, fiscal calendar, reconciliation-eligible accounts per FR-050, expected-entries reference for F-04-02) — all configurable without code changes; enable/disable as versioned, logged change only. *Traces:* FR-103, FR-105, FR-106.

### F-02-04 — Rule Output & Findings Contract
- **Classification:** R1 · **Status:** Approved
The schema of a finding: evidence values, affected entities, source references, and **severity computed per rule-defined configurable criteria** (FR-070's computation half). E-06 consumes; capability epics emit through it. *Traces:* FR-069 (creation), FR-070 (computation).

### F-02-05 — Historical Baselines & Cold-Start Honesty
- **Classification:** R1 core / R2 scope · **Status:** Approved
**R1:** minimum-history declarations enforced; below-minimum rules report "insufficient history" rather than firing; reports disclose which rules ran with limited baselines (FR-111). **R2:** history-derived baseline computation (trailing averages etc.) supporting F-04-03 and F-03-05.

### F-02-06 — Deterministic Replay & Reproducibility
- **Classification:** R1 · **Status:** Approved
Re-run any historical cycle against its recorded inputs and configuration with identical results. *Depended on by:* F-07-03 (report reproducibility, R1) and auditors. *Traces:* NFR-021.

## 6. E-03 — Budget Review & Analysis

### F-03-01 — Budget Position Dashboard
- **Classification:** Capability, R1 · **Status:** Approved
Plan vs. actual by department, account, vendor — month and YTD — using bgt/atd/etc/eac figures. One dashboard, dimension lenses (not separate per-dimension features). Answers: *"are we on plan?"* *Traces:* FR-030, FR-031.

### F-03-02 — Variance Analysis & Drivers
- **Classification:** Capability, R1 · **Status:** Approved
From any variance to its decomposition: ranked contributing accounts/vendors, drill-through to journal lines. Answers: *"what's driving this?"* Links to findings in E-06; does not duplicate them. **Guardrail:** every element answers a variance question, or it's out. *Traces:* FR-035.

### F-03-03 — Budget Exception Rule Pack
- **Classification:** Capability, R1 · **Status:** Approved
Over/under-budget severity checks and month-over-month change detection as catalog entries on E-02. Golden-dataset acceptance per §2.1. *Traces:* FR-032, FR-033.

### F-03-04 — Run-Rate Projection & Overrun Alerts
- **Classification:** Capability, **R2** · **Status:** Approved
Deterministic projection from YTD actuals; overrun trajectory flags. Demoted from R1 under the MVP lens (DEC-023): the monthly review completes without it, and the projection *method* needs finance agreement. *Traces:* FR-034.

### F-03-05 — Multi-Month Spend Trends
- **Classification:** Capability, R2 · **Status:** Approved
Sustained-trend risk rules and trend views; history-dependent. *Traces:* FR-036, FR-109 (budget portion).

## 7. E-04 — GED Analysis & Exception Detection

### F-04-01 — GED Activity Summarization
- **Classification:** Capability, R1 · **Status:** Approved
GED spend summarized by department, account, vendor, period, with prior-period comparison and drill-through. Answers: *"where did the money go?"* (Boundaries: F-03-01 answers "on plan?"; F-06-04 answers "find this specific thing" — one view answering two questions triggers consolidation.) *Traces:* FR-043, FR-109 (GED portion).

### F-04-02 — GED Exception Rule Pack
- **Classification:** Capability, R1 · **Status:** Approved
History-free detection as catalog entries: duplicates (consuming F-01-06's verified event tags — reclass/accrual reversals are not false duplicates), delayed postings vs. configured cutoff (OQ-7), coding and vendor-expectation checks vs. configured reference, and **missing-entry detection against a finance-maintained expected-entries reference where OQ-5 permits** — keeping a canonical leadership question ("are entries missing?") in Release 1. Golden-dataset acceptance per §2.1. *Traces:* FR-037 (reference-based), FR-038, FR-039, FR-042, FR-041 (consumption half).

### F-04-03 — History-Based Anomaly Detection
- **Classification:** Capability, R2 · **Status:** Approved
History-derived expectations and amount-anomaly detection vs. trailing baselines (via F-02-05 R2 scope). Deterministic only; deliberately renamed from "pattern intelligence" to stay boring and honest. *Traces:* FR-037 (history-based), FR-040.

## 8. E-05 — Reconciliation Automation *(pure Operator epic; the Leader consumes outcomes via E-06/E-07)*

### F-05-01 — Automated Matching Rule Pack
- **Classification:** Capability, R1 · **Status:** Approved
The product's highest-ROI capability: GED lines matched against tracker entries as catalog-parameterized rules producing exact / probable / unmatched classifications with confidence tiers. Match keys, tolerances, and `clrd` semantics come from the Rules Catalog; eligible-account scope from F-02-03 (FR-050). Consumes F-01-06 event tags. Golden-dataset acceptance per §2.1. *Traces:* FR-044, FR-045.

### F-05-02 — Reconciliation Workspace
- **Classification:** Capability, R1 · **Status:** Approved
The Operator's single reconciliation surface: all match states; probable matches confirmed or rejected; manual match/unmatch/override with reasons and audit; cleared-status tracking equivalent to today's `clrd`; unmatched items always visible; progress display; **carry-forward mechanism** — unresolved items persist across cycles with age display. Residual unresolved items become findings at cycle close per §2.3. *Traces:* FR-046–FR-049.

### F-05-03 — Aging Analytics & Carry-Forward Reporting
- **Classification:** Capability, R2 · **Status:** Approved
Aging metrics, cross-period reporting and trends over the carry-forward data. *Traces:* FR-049 (analytics scope).

## 9. E-06 — Findings & Exception Management

### F-06-01 — Findings Inbox & Triage
- **Classification:** Capability, R1 · **Status:** Approved
The single findings experience: severity presentation, critical-first surfacing on analysis completion, progressive disclosure, filter/sort/group. **Explicit dual lens:** Operator work queue and Leader decision view ("items needing my decision"). **Binding criterion:** Budget, GED, Reconciliation — and later Invoice — findings all render through the same components; no per-capability forks. *Traces:* FR-069/070 (display), FR-074, FR-082; NFR-066.

### F-06-02 — Finding Investigation & Explainability
- **Classification:** Capability, R1 · **Status:** Approved
From any finding: the rule, the input values, the source rows/cells — one interaction. The product's single strongest trust feature. *Traces:* FR-071; NFR-067.

### F-06-03 — Finding Lifecycle & Resolution
- **Classification:** Capability, R1 · **Status:** Approved
New → Acknowledged → In review → Resolved/Dismissed; dismissal requires a reason; all transitions logged. **Includes false-positive capture in R1** (a dismissal reason category) — pilot-critical evidence at near-zero cost. *Traces:* FR-072, FR-075 (capture half).

### F-06-04 — Data & Findings Search
- **Classification:** Capability, R1 · **Status:** Approved
Search across underlying verified data and findings (vendor, account, amount range, period, status) — no AI required. *Traces:* FR-102.

### F-06-05 — Recurring Findings Intelligence
- **Classification:** Capability, R2 · **Status:** Approved
Cross-month finding linkage and recurrence counts; history-dependent by definition. *Traces:* FR-073.

### F-06-06 — False-Positive Analytics
- **Classification:** Capability, R2 · **Status:** Approved
Analysis over captured false-positive evidence to support human threshold tuning; never silently alters rule behavior. *Traces:* FR-075 (analytics half).

## 10. E-07 — Executive Reporting & Export

### F-07-01 — Monthly Leadership Summary
- **Classification:** Capability, R1 · **Status:** Approved
The flagship artifact: deterministic RAG status (a catalog rule surfaced here — FR-077), budget health, GED status, key risks, recommended actions, and the absorbed **"What Changed" section** (thin month-over-month deltas per FR-078). AI-narrative slots exist, labeled (FR-080), and remain empty until E-09 — the summary must read as complete without them (FR-095 acceptance criterion). **Guardrail:** the source spec's section structure, nothing more. *Traces:* FR-076–078 (thin), FR-080.

### F-07-02 — Interactive Month-over-Month Comparison
- **Classification:** Capability, **R2** · **Status:** Approved
The exploratory comparison view; joins the history-dependent capabilities. Anything needing cross-month finding identity belongs to F-06-05, not here. *Traces:* FR-078 (interactive scope).

### F-07-03 — Report History & Reproducibility
- **Classification:** Capability, R1 · **Status:** Approved
Every generated report retained and re-displayable exactly; regeneration is identical — the visible payoff of F-02-06. *Traces:* FR-079.

### F-07-04 — Export & Distribution
- **Classification:** Capability, R1 core / R2 scope · **Status:** Approved
The **shared, uniformly-labeled export capability** — one implementation of formats and FR-120 labeling (timestamp, period, config version, AI marking), serving E-07 reports *and* E-06 findings/data exports (FR-117); per-surface export buttons are stories in consuming features. **R1:** summary print/PDF; findings and data spreadsheet exports. **R2:** workbook-compatible export (FR-118) — promotable if A-10 resolves toward coexistence. *Traces:* FR-116, FR-117, FR-118 (R2), FR-120. FR-083 (no external notifications) stands as an epic boundary statement.

## 11. E-08 — Audit & Compliance

### F-08-01 — Audit Event Capture Contract
- **Classification:** **Enabler**, R1 · **Status:** Approved
The event taxonomy and interface every component uses: ingestion, verification, corrections, rule runs, config changes, AI interactions, consents, reports, exports — attributed, timestamped, fingerprinted; multi-month retention (FR-108) lives in its storage behavior. **Taxonomy extended (DEC-035, R1):** `review_abandoned` / `review_resumed` lifecycle events (append-only, attributed, timestamped) per ADR-014. *Depended on by:* DoD clause 1 across every epic. **Guardrail:** event schema versioned from day one (v1, evolvable); taxonomy derived strictly from FR-084–089 (plus ADR-014/DEC-035 for the abandonment lifecycle events), nothing speculative. In the walking skeleton from story one.

### F-08-02 — Audit Trail Explorer
- **Classification:** Capability, R1 · **Status:** Approved
Searchable, filterable audit view with a **cycle timeline lens** ("show me June's review, start to finish") delivering the epic's reconstruction signal. Audit export (FR-119) is a story here, not a feature. *Traces:* FR-090, FR-119.

### F-08-03 — Configuration & Rule Change History
- **Classification:** Capability, R1 · **Status:** Approved
Versioned history of every configuration and rule-set change; answers "which thresholds were in force for this finding?" — where E-02's per-run version references resolve. *Traces:* FR-107; NFR-022.

### F-08-04 — Tamper-Evident Audit Records
- **Classification:** Capability, R2 · **Status:** Approved
Alteration/deletion detectability. R2. NFR-020 is Approved in the current baseline. *Traces:* NFR-020.

## 12. E-14 — Desktop Application Foundation & Experience *(standing constraint: intentionally thin — enough foundation for "Monthly Review in a Box" and no more)*

### F-14-01 — Application Shell & Navigation
- **Classification:** Capability, R1 · **Status:** Approved
Installs and runs on enterprise Windows and macOS in restricted environments; navigation frame; responsive layout; settings surface including view-active-configuration transparency. **Guardrail:** the R1 shell is navigation between R1 surfaces plus one settings screen; any screen not traceable to a locked feature is rejected by definition. *Traces:* NFR-028, NFR-030, NFR-039–041, NFR-065.

### F-14-02 — Never Lose Work
- **Classification:** Capability, R1 · **Status:** Approved
Crash-safe, resumable, all-or-nothing operations; force-kill mid-analysis loses nothing. *Traces:* NFR-005, NFR-006, NFR-008, NFR-057.

### F-14-03 — Background Processing & Progress
- **Classification:** **Enabler**, R1 · **Status:** Approved
Long operations run off the UI thread with progress reporting; every epic's long-running work uses this contract. **Guardrail:** no generic job framework until two features demonstrably need the same machinery; the word "framework" in a story here is the tripwire. *Traces:* NFR-002–004.

### F-14-04 — Data Protection & Secrets
- **Classification:** **Enabler**, R1 · **Status:** Approved
Protection at rest for all stored data (financial, findings, audit); platform-secure credential storage. R1 without debate: the pilot puts real data on a laptop on day one. *Traces:* NFR-009, NFR-010.

### F-14-05 — Accessible Experience & Display Modes
- **Classification:** Capability, R1 · **Status:** Approved
Accessible by default: no meaning by color alone (severity, RAG), OS light/dark following, contrast, keyboard reachability, text scaling. Theme picker with color-blind palettes: R2 story within this feature. *Traces:* NFR-024–027.

### F-14-06 — Backup & Restore
- **Classification:** Capability, R1 minimal · **Status:** Approved
Back up all FinSight data to a file; restore on a fresh install — because a lost laptop must not mean a lost audit trail. Polish (scheduling, guided flows): R2. *Traces:* NFR-060, NFR-061.

### F-14-07 — Health, Diagnostics & Data Disposal
- **Classification:** Capability, R2 · **Status:** Approved
Self-diagnosis, separated technical logs (no sensitive values), permanent data deletion with logged fact-of-deletion. *Traces:* NFR-017, NFR-053, NFR-054.

---

## 13. Not yet decomposed (deliberate)

| Epic | Status | Decomposition trigger |
|------|--------|----------------------|
| E-09 AI Assistance (Optional) | Locked epic, R2 | Feature brainstorm at R2 planning; MVP AI scope per DEC-022 (single provider, consent, labeling, citations, audit) |
| E-11 Resource & Contract Management | Locked epic, Phase 2 | Schema validation (DEC-012) + Phase 2 planning |
| E-12 Invoice Review & Validation | Locked epic, Phase 3 | Sample documents received (OQ-2) |
| E-13 Forecasting & What-If | Deferred | Re-justification through the decision log |

## 14. Cross-epic shared assignments (the complete list — anything not here is single-owner)

| Item | Split |
|------|-------|
| FR-041 accounting-event awareness | Classification/tagging: F-01-06 (visible at verification) · Consumption: F-04-02, F-05-01 |
| FR-070 severity | Computation: F-02-04 · Presentation: F-06-01 |
| FR-050 reconciliation scope | Configuration: F-02-03 · Consumption: F-05-01 |
| FR-078 what-changed | Thin section: F-07-01 (R1) · Interactive view: F-07-02 (R2) |
| FR-075 false positives | Capture: F-06-03 (R1) · Analytics: F-06-06 (R2) |
| FR-086 rule-execution audit | Emission: F-02-02 · Storage/serving: F-08-01/02 |
| FR-119 audit export | Story in F-08-02, machinery via F-07-04 |
| Export machinery & FR-120 labeling | Owned once by F-07-04; consuming surfaces add buttons as stories |
| FR-095 AI-off completeness | R1: satisfied by construction · From E-09 onward: standing regression |

## 15. Watch items (carried from brainstorm reviews)

1. **F-14-01** — highest scope-creep risk in the product ("just polish" accretion).
2. **F-08-01** — decided earliest, most expensive to change; schema versioning is the mitigation.
3. **F-14-03** — highest architecture-in-disguise risk; the "framework" tripwire applies.
4. **F-07-01** — executive-report chart accretion; section structure is fixed.
5. **F-03-02** — analysis-view growth; the variance-question rule applies.
6. **E-01 size** — 11 features; pre-agreed split line (Intake & Extraction vs. Quality & Verification) if it dominates the board.
7. **OQ-5** — determines whether missing-entry detection ships R1 (reference-based) or waits for R2 (history-based); chase it explicitly.
