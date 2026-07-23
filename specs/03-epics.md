# FinSight — Epics

**Document:** 03-epics.md
**Status:** LOCKED baseline (DEC-021, 2026-07-10) — amended per DEC-022 (release-based delivery, AI epic merge, E-13 deferral)
**Guiding principle:** *"Monthly Review in a Box"* is the lens for evaluating every feature, story, and priority. **Trust > AI.**
**Scope:** The epic-level decomposition of FinSight. Features and user stories will be derived per epic in subsequent documents. No architecture or technology content.
**Companion documents:** 01-functional-requirements.md · 02-non-functional-requirements.md · 09-decision-log.md

---

## 1. How this structure was derived

Epics are sliced by **business capability** (with two explicitly labeled **enabler** epics), because FinSight's requirements already group naturally into capabilities stakeholders recognize, and capability epics stay outcome-oriented. Cross-cutting behaviors (audit, lineage, determinism, testing) are deliberately **not** epics — they are Definition of Done clauses (§4) applied to every story. Configuration was deliberately dissolved as a standalone epic: configuration belongs with the capability it configures; configuration-versioning infrastructure lives in E-08.

**Conventions:** `E-nn` IDs are permanent. Type = Capability or Enabler. Phase = delivery phase per DEC-009. Every epic carries an outcome statement ("When this epic is complete…"), at least one measurable success signal, FR/NFR traceability, and dependencies. Numeric targets are calibration starting points set under the approved baseline.

## 2. Epic overview

| ID | Epic | Type | Phase | Depends on |
|----|------|------|-------|-----------|
| Epic E-01 | Data Intake, Extraction & Verification | Capability | 1 | E-14 |
| Epic E-02 | Deterministic Rules Engine | Enabler | 1 | E-14 |
| Epic E-03 | Budget Review & Analysis | Capability | 1 | E-01, E-02, E-06 |
| Epic E-04 | GED Analysis & Exception Detection | Capability | 1 | E-01, E-02, E-06 |
| Epic E-05 | Reconciliation Automation | Capability | 1 | E-01, E-02, E-06 |
| Epic E-06 | Findings & Exception Management | Capability | 1 | E-02 |
| Epic E-07 | Executive Reporting & Export | Capability | 1 | E-03–E-06 |
| Epic E-08 | Audit & Compliance | Capability | 1 | E-14 |
| Epic E-09 | AI Assistance (Optional) | Capability (optional at runtime) | 1 · Release 2 | E-06, E-08, E-14 |
| Epic E-10 | *(merged into E-09 — DEC-022; ID retired)* | — | — | — |
| Epic E-11 | Resource & Contract Management | Capability | 2 | E-01, E-02, E-06 |
| Epic E-12 | Invoice Review & Validation | Capability | 3 | E-01, E-02, E-06; sample documents (OQ-2) |
| Epic E-13 | Forecasting & What-If Analysis | Capability | Deferred (visible on roadmap; re-justify before activation) | E-03, E-11 |
| Epic E-14 | Desktop Application Foundation & Experience | Enabler | 1 | — |

**First wave (nothing works without them):** E-14, E-01, E-02, E-08, E-06.
**WIP guidance:** small team + coding agents — actively work 2–3 epics at a time; this list is a map, not a parallel to-do list.

### Release plan (DEC-022) — epics are the map; releases are the value slices

**Release 1 — "Monthly Review in a Box" (MVP):** a user completes an end-to-end monthly review inside FinSight without manual spreadsheet analysis for the core workflow: upload GED + Budget Tracker → verify extracted data → budget review, GED analysis, reconciliation → findings management → executive summary → export — with a complete audit trail throughout. Delivered as MVP slices of E-14, E-01, E-02, E-03, E-04, E-05, E-06, E-07, E-08. Build order starts with a **walking skeleton** (one file → one rule → one finding with lineage → one summary line, audit on from story one).
**Release 2 — depth & AI:** history-dependent anomaly rules and historical onboarding import; AI Assistance (E-09: narratives, explanations, recommendations, optional Q&A); workbook-compatible export polish; wrong-file replacement re-run machinery; recurrence linkage and false-positive feedback; masking/multi-provider trust controls as needed.
**Release 3+:** E-11 (Phase 2), E-12 (Phase 3 — samples resolved under the approved baseline, OQ-2), E-13 (deferred; re-justify before activation).
**Priority order of value drivers:** reconciliation automation · exception detection · auditability & traceability · executive reporting · invoice validation (when samples arrive). AI enhances these; it never defines them.

---

## 3. Epics

### E-01 — Data Intake, Extraction & Verification (Capability, Phase 1)
- **Status:** Approved

**Outcome:** When this epic is complete, users can load their monthly files into FinSight and trust the extracted data — every file recognized and assigned to the right period, real-world file structure handled correctly, quality problems quarantined visibly, and nothing analyzed until a human has verified and approved it.
**Success signals:** A pilot user completes intake and verification of a real month's files without support. Extraction of the sample GED/Budget Tracker files reproduces the files' own subtotals exactly. No analysis can be started on unverified data (verified by test).
**Traces to:** FR-001–FR-029, FR-081, FR-110 · NFR-012, NFR-062, NFR-064, NFR-069
**Notes:** Largest epic (~30 FRs). Pre-agreed split line if it bloats: *Intake & Extraction* vs. *Quality & Verification*. Document-type-specific extraction templates are built under their capability epics on this epic's infrastructure: invoice/reference documents (FR-018/019) under E-12, resource loading sheets (FR-020) under E-11.

### E-02 — Deterministic Rules Engine (Enabler, Phase 1)
- **Status:** Approved

**Outcome:** When this epic is complete, all financial findings, validations, classifications, and rule-derived recommendations are generated through a consistent, auditable, reproducible rules framework that produces the same results given the same inputs — and new rules can be added cheaply without touching unrelated modules.
**Success signals:** Running the same review cycle repeatedly with the same verified data produces identical findings, severities, statuses, and outputs regardless of AI provider, user session, or execution date (standing regression test). A new rule can be added, tested, and versioned without modifying any unrelated module. Rules below their declared minimum history report "insufficient history" rather than firing (FR-111).
**Traces to:** FR-086 *(shared with E-08: this epic emits rule-execution audit events; E-08 owns the audit infrastructure that stores them)*, FR-103, FR-105, FR-106, FR-111 · NFR-021, NFR-022, NFR-036, NFR-037, NFR-044, NFR-047, NFR-048, NFR-059
**Notes:** Individual business rules belong to their capability epics; this epic owns the engine, rule versioning, parameterization, and the determinism guarantee. Enabler risk: protect its capacity — E-03/04/05 are all blocked without it. Rule parameter values arrive via the Rules Catalog (04).

### E-03 — Budget Review & Analysis (Capability, Phase 1)
- **Status:** Approved

**Outcome:** When this epic is complete, a Leader can see plan-vs-actual position, variances, their drivers, and projected risk for their department — by account and vendor, for the month and year-to-date — without opening a spreadsheet.
**Success signals:** A pilot user completes their monthly budget review without opening the source Excel files. Variance findings match a hand-checked control month exactly. Monthly review effort trends toward the NFR-068 target *(≤50% of manual baseline, per the approved baseline)*.
**Traces to:** FR-030–FR-036, FR-109 · budget-rule entries in the Rules Catalog
**Notes:** Budget granularity is monthly (DEC-017). Trend/anomaly rules degrade gracefully at cold start (E-02 / FR-111).

### E-04 — GED Analysis & Exception Detection (Capability, Phase 1)
- **Status:** Approved

**Outcome:** When this epic is complete, missing, duplicate, delayed, unusually sized, and miscoded GED entries are surfaced systematically each month — with routine accounting events (payroll, reclasses, accruals) recognized so they don't become false alarms.
**Success signals:** Seeded synthetic exceptions (missing/duplicate/anomalous entries) are detected at 100% on the golden dataset. Reclass and accrual-reversal entries in the sample data produce zero duplicate/anomaly false positives *(FR-041)*. False-positive rate in pilot months trends down via FR-075 feedback.
**Traces to:** FR-037–FR-043 · GED-rule entries in the Rules Catalog · OQ-5, OQ-7 (baseline & cutoff semantics)
**Notes:** Missing-entry baseline design (history-derived vs. finance-maintained) resolves in the Rules Catalog phase.

### E-05 — Reconciliation Automation (Capability, Phase 1)
- **Status:** Approved

**Outcome:** When this epic is complete, GED activity reconciles against tracking records automatically, and the Operator reviews only exceptions — with full manual override and nothing falling through the cracks across months.
**Success signals:** ≥70% of reconciliation-eligible GED lines auto-match as exact *(pilot-calibrated, per the approved baseline)*. The Operator manually touches only flagged/probable items. Unreconciled items persist visibly across cycles with aging until resolved.
**Traces to:** FR-044–FR-050 · match-rule entries in the Rules Catalog · A-10 (workbook coexistence), `clrd` semantics (Rules Catalog)
**Notes:** Directly replaces today's paste-and-clear process — the single largest manual effort in the current workflow.

### E-06 — Findings & Exception Management (Capability, Phase 1)
- **Status:** Approved

**Outcome:** When this epic is complete, every issue FinSight detects is a first-class, severity-classified, fully traceable record with a managed lifecycle — one consistent findings experience shared by every analysis capability.
**Success signals:** From any finding, a user reaches rule + inputs + source rows in one interaction (NFR-067). No finding can be dismissed without a reason, and audit shows the full lifecycle of every finding in a closed month. Budget, GED, and reconciliation findings all render through the same components (no per-capability forks).
**Traces to:** FR-069–FR-075, FR-082, FR-102 · NFR-066, NFR-067
**Notes:** Dependency magnet — must land in the first wave or E-03/04/05 build inconsistent workarounds. Severity threshold defaults arrive via the Rules Catalog (OQ-8).

### E-07 — Executive Reporting & Export (Capability, Phase 1)
- **Status:** Approved

**Outcome:** When this epic is complete, FinSight produces the monthly leadership summary — deterministic RAG status, budget health, GED status, risks, recommended actions, and month-over-month change — reproducible forever, and exportable in shareable, self-describing form.
**Success signals:** A Leader answers "are we okay this month, and what changed?" from the summary alone in a pilot review. Any historical report re-displays exactly as originally produced. Every export carries timestamp, period, configuration version, and AI-content labeling (verified by test).
**Traces to:** FR-076–FR-080, FR-083, FR-116–FR-120
**Notes:** Smallest Phase 1 capability epic — kept separate because ownership of the product's most visible artifact must never be ambiguous.

### E-08 — Audit & Compliance (Capability, Phase 1)
- **Status:** Approved
*(Renamed from "Audit Trail & Governance Infrastructure" for stakeholder clarity, 2026-07-10. Scope unchanged: this epic owns audit infrastructure; regulatory-compliance features beyond audit readiness are not in scope.)*

**Outcome:** When this epic is complete, every material action in FinSight — intake, verification, corrections, rule runs, configuration changes, AI interactions, consents, reports, exports — is recorded attributably and searchably, so any month's review can be reconstructed after the fact.
**Success signals:** For a completed pilot month, a reviewer reconstructs the full review (who did what, which rules/config versions ran, what was produced) using only the audit trail. Audit-record tampering is detectable *(NFR-020)*. Configuration history explains every threshold in force for any historical finding.
**Traces to:** FR-084–FR-090, FR-107, FR-108 · NFR-019, NFR-020, NFR-022, NFR-023, NFR-058
**Notes:** This epic owns audit *infrastructure* (storage, viewer, search, export). Audit *behavior* — every feature logging its actions — is Definition of Done (§4), enforced story by story.

### E-09 — AI Assistance (Optional) (Capability — optional at runtime, Phase 1 · Release 2)
- **Status:** Approved

*(Merged from "AI Platform & Trust Controls" and E-10 "AI Insights & Q&A" per DEC-022. Trust controls remain fully in scope as this epic's foundational features; if security review (OQ-1) expands their scope, re-split via the decision log.)*

**Outcome:** When this epic is complete, users can read plain-language explanations, narratives, and recommendations derived strictly from deterministic results — and optionally ask natural-language questions — with every AI statement grounded, cited, visually distinct, and safe to ignore, and every data transmission consent-gated, transparent, and auditable.
**Success signals:** Zero AI transmissions occur without a logged consent record — provable from the audit trail. For any historical AI interaction, a reviewer can reconstruct what was sent, to which provider/model, under which consent, in under a minute. Every AI claim carries citations resolvable to finding IDs/data points in one click. AI declines questions unsupported by available data (adversarial test set). Disabling AI removes narratives only — every number, finding, and report section remains (FR-095 regression).
**Traces to:** FR-091–FR-101, FR-104 · NFR-011, NFR-013–NFR-016, NFR-046, NFR-049–NFR-052 · DEC-006 (consent model — Amerisure security validation resolved under the approved baseline, OQ-1)
**Notes:** AI enhances the deterministic value drivers; it never defines them (Trust > AI, DEC-022). MVP AI scope: single approved provider, consent flow, labeling, citation, audit. Masking/tokenization, multi-provider registry, and non-recommended-provider warning states are later features within this epic. Builds on E-08 (audit) and E-06 (findings are the grounding substrate). The application is fully functional with this epic entirely unconfigured (FR-095).

### E-10 — *(retired)*
- **Status:** Retired

Merged into E-09 per DEC-022 (2026-07-10). The ID is retired and will not be reused.

### E-11 — Resource & Contract Management (Capability, Phase 2)
- **Status:** Approved

**Outcome:** When this epic is complete, users can see who is working under what terms and what they cost — resources, contracts, vendors, departments, accounts, and budget allocations connected in one navigable view, with status history recorded from day one.
**Success signals:** A user answers "which contracts fund which people, and what does each cost per month?" from the mappings view alone. Every resource status change is dated and auditable. Governance gap checks (no-contract resources, expired contracts) fire correctly on seeded test data *(FR-068)*.
**Traces to:** FR-020, FR-061–FR-068 · DEC-012 (schema — resolved under the approved baseline), DEC-013
**Notes:** Data model must support attrition analysis from day one (DEC-014) even though the what-if UI is E-13.

### E-12 — Invoice Review & Validation (Capability, Phase 3)
- **Status:** Approved

**Outcome:** When this epic is complete, every invoice is automatically checked against POs, SOWs, rate cards, estimates, and staffing plans — line-item by line-item, with line types handled correctly — and arrives at the Leader as a single status recommendation with reasons, never an action.
**Success signals:** Seeded invoice exceptions (rate/hours/period/duplicate/missing-PO) are detected at 100% on the golden dataset. Every reviewed invoice receives exactly one of the five statuses with rule-level reasons attached. Non-labor lines (e.g., tax) produce zero false rate-mismatch findings (FR-121).
**Traces to:** FR-002, FR-018, FR-019, FR-051–FR-060, FR-121, FR-122 · A-05 (partially validated), OQ-2
**Notes:** Sample documents (other vendors' invoices, POs, SOWs, rate cards) and formerly assumed formats are Approved in the current baseline.

### E-13 — Forecasting & What-If Analysis (Capability, Phase 4)
- **Status:** Approved

**Outcome:** When this epic is complete, leadership can see where budgets are heading and explore hypothetical scenarios — including resource-departure impact and backfill costs — with all numbers computed deterministically, AI narrating only, and hypotheticals never mixed with actuals.
**Success signals:** Forecast math reproduces hand-calculated control scenarios exactly. A "resource X departs on date Y" query returns account-and-period-level impact computed from Phase 2 data. Every scenario output is visibly marked hypothetical.
**Traces to:** FR-112–FR-115 · DEC-014
**Notes:** Parked until Phase 4; data model prerequisites land with E-11.

### E-14 — Desktop Application Foundation & Experience (Enabler, Phase 1)
- **Status:** Approved

**Outcome:** When this epic is complete, FinSight exists as a trustworthy desktop application: installs and runs identically on enterprise Windows and macOS, never freezes or loses work, protects data at rest, respects OS display modes and accessibility needs, and can be backed up and restored.
**Success signals:** The same golden dataset produces byte-identical deterministic results on Windows and macOS (NFR-029). A mid-analysis force-kill loses no verified data or audit records (NFR-005). Full backup/restore succeeds on a replacement machine. All severity/RAG information is distinguishable without color (NFR-025).
**Traces to:** NFR-002–NFR-010, NFR-017, NFR-024–NFR-030, NFR-039–NFR-041, NFR-053, NFR-054, NFR-057, NFR-060–NFR-062, NFR-065
**Notes:** Enabler; almost entirely NFR-driven. First-wave — everything else runs inside it. Technology choices belong to the architecture phase (05), not this document.

---

## 4. Definition of Done (cross-cutting — applies to every story in every epic)

A story in any epic is not done until:

1. **Audited:** every material action the story introduces writes appropriate audit records (per E-08 infrastructure).
2. **Traceable:** any data the story displays or computes preserves lineage to source (file/sheet/row) and to the rule/configuration version that produced it.
3. **Deterministic:** any computation the story introduces is covered by determinism tests; the provider-swap regression (NFR-037) still passes.
4. **Tested:** unit tests written with the code (NFR-035); golden-dataset tests updated where behavior changed.
5. **AI-labeled:** any AI-generated content the story surfaces is visually distinct, labeled, and attributed (NFR-049) — including in exports.
6. **Config-governed:** any new parameter is configurable (not hard-coded), versioned, and recorded in analysis audit records (FR-107).
7. **Honest under failure:** errors are visible, actionable, and never present partial results as complete (NFR-062).
8. **Accessible:** no information conveyed by color alone; keyboard-reachable (NFR-025/026).
9. **Reviewed:** human-reviewed regardless of whether code was agent-generated (NFR-074/075); traceable to the FR/NFR it implements (NFR-033).
10. **Real-data-free:** all fixtures and tests use sanitized/synthetic data only (NFR-018).

## 5. Open items affecting epics

| Item | Affects | Status |
|------|---------|--------|
| OQ-1 — Amerisure security validation of consent model | E-09 (production gate) | Open |
| OQ-2 — PO/SOW/rate-card samples | E-12 (build gate) | Open; one real invoice received |
| OQ-5 / OQ-7 / OQ-8 — baselines, cutoffs, thresholds | E-02, E-04, E-06 rule parameters | Rules Catalog phase |
| A-09/A-10/A-11 — personas, workbook fate, department scope | E-01, E-05, E-07 workflow detail | Team — answerable internally |
| DEC-012 schema validation | E-11 | Resolved under the approved baseline |
