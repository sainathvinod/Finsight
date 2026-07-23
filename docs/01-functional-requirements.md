# FinSight — Functional Requirements

**Document:** 01-functional-requirements.md
**Status:** Approved Baseline
**Date:** 2026-07-20
**Scope:** WHAT FinSight must do. Contains no architecture, technology, framework, database, or implementation decisions.
**Companion documents:** 00-project-understanding.md · 02-non-functional-requirements.md · 09-decision-log.md

---

## 1. Conventions

- **ID:** `FR-nnn`, unique and permanent. Retired requirements are marked superseded, never renumbered.
- **Priority (MoSCoW):** Must / Should / Could — priority for the *product*, independent of build order.
- **Phase:** 1–4 per the agreed delivery sequence (DEC-009). Phase ≠ priority: Invoice Review is a Must, delivered in Phase 3.
- **Tags:**
  - `ASSUMPTION (A-nn)` — rests on an entry in the Assumptions Register (§2).
  - `PENDING VALIDATION` — cannot be finalized until stakeholders provide information.
  - `OPEN QUESTION (OQ-n)` — blocked on a decision-log open question.
  - `PROPOSED` — not requested by any source document or discussion; added with justification for team accept/reject.
- **Personas used in this document** *(per A-09)*: **Operator** — performs ingestion, verification, reconciliation; **Leader** — consumes summaries, findings, Q&A, and makes decisions. These may be the same person in different modes.

## 2. Assumptions Register

Any FR citing an assumption becomes invalid if that assumption fails, and must be revisited.

| ID | Assumption | Risk if wrong | Validation owner |
|----|------------|---------------|------------------|
| A-01 | GED = General Expense Detail report (team-confirmed; not yet Amerisure-document-confirmed) | Terminology/scope confusion | Aditi → Amerisure |
| A-02 | MVP analysis dimensions are department + GL account + vendor; project/workstream/funding-category data does not exist | Missing dimensions expected by stakeholders | Aditi → stakeholders (OQ-4) |
| A-03 | Monthly review cadence governs all workflows; one reporting month per review cycle | Workflow redesign | Aditi → finance |
| A-04 | ~~Budget granularity unknown~~ **RESOLVED 2026-07-09: budget phasing is monthly** (team-confirmed) | — | Closed |
| A-05 | Invoices, POs, SOWs, rate cards arrive as PDF and/or Excel in stable formats. **PARTIALLY VALIDATED 2026-07-09:** one real invoice sample received (HCL America format: summary page + line-item annexure). Other vendors' invoice formats, and all PO/SOW/rate-card documents, remain unseen | Phase 3 extraction rework for unseen formats | Aditi → stakeholders (OQ-2) |
| A-06 | An Amerisure-approved enterprise AI endpoint will exist for production use | AI features restricted to other consented providers | Aditi → stakeholders (OQ-3) |
| A-07 | ≥3 months of historical data importable at go-live; pattern rules degrade gracefully below that | Cold-start noise; weakened anomaly detection | Aditi → finance |
| A-08 | Volumes are single-department scale (hundreds to low thousands of GED lines/month) | Performance targets revised | Aditi → finance |
| A-09 | Two personas exist (Operator, Leader), possibly embodied by one person | Workflow requirements consolidated or split | **Team — answerable internally (OQ-6)** |
| A-10 | FinSight coexists with the Budget Tracker workbook initially (export-back supported), with replacement as the goal once trust is established | Export requirements change; double-bookkeeping risk | **Team — answerable internally** |
| A-11 | MVP serves one department per user; data model must not preclude multi-department later | Rollup/filter requirements added | **Team — answerable internally** |
| A-12 | Sanitized samples are structurally faithful to production files (including credits/negative amounts/reversals) | Extraction rework | Aditi → stakeholders |
| A-13 | Consent-based AI data-sharing model stands (DEC-006) | AI transmission features re-gated | Amerisure security (OQ-1) |

---

## 3. Functional Requirements

### 3.1 File Ingestion

**FR-001 — Ingest Excel workbooks** (Must, Phase 1)
Accept Excel files provided by the user, including multi-sheet workbooks (GED reports, Budget Tracker with Details/Actuals/Original Budget sheets).

**FR-002 — Ingest PDF documents** (Must, Phase 3) `ASSUMPTION (A-05)` `PENDING VALIDATION`
Accept PDF documents (invoices, POs, SOWs, rate cards, contracts). Formats assumed until samples are provided.

**FR-003 — Read-only source handling** (Must, Phase 1)
Never modify, move, or delete a user's source file. All processing operates on ingested copies.

**FR-004 — Document type classification with user confirmation** (Must, Phase 1)
Automatically classify each ingested file (GED report, budget tracker, invoice, PO, SOW, rate card, resource sheet, unknown) and require the user to confirm or correct the classification before processing. Classification may be AI-assisted, but the user's confirmation is authoritative.

**FR-005 — Reporting-period assignment** (Must, Phase 1) `ASSUMPTION (A-03)`
Every ingested file is assigned to a reporting month/year, proposed automatically where detectable (e.g., "Year-To-Date for Period May") and confirmed by the user.

**FR-006 — Review-cycle grouping** (Must, Phase 1)
Group a month's ingested files into a named review cycle that progresses through the pipeline as a unit (ingest → verify → analyze → report).

**FR-007 — File-level validation with clear rejection** (Must, Phase 1)
Reject unreadable, corrupt, password-protected, or unsupported files with a message stating exactly what is wrong and what the user can do.

**FR-008 — Duplicate file detection** (Should, Phase 1) `PROPOSED`
Detect when an identical or near-identical file (by content) has already been ingested for the same cycle and warn before proceeding. *Justification: re-uploading last month's file by mistake is the most likely user error and would silently poison every downstream result.*

**FR-009 — File replacement with versioning** (Should, Phase 1) `PROPOSED`
Allow a corrected file to replace a previously ingested one within a cycle; retain the superseded version and re-run affected downstream steps. *Justification: corrected re-exports are routine in month-end processes; without versioning, lineage breaks.*

**FR-010 — File provenance record** (Must, Phase 1)
For every ingested file record: original filename, content fingerprint, ingestion timestamp, ingesting user, assigned period, and classification.

### 3.2 Data Extraction

**FR-011 — GED extraction** (Must, Phase 1)
Extract from GED reports the observed fields: department number/name, account number/name, fiscal period, journal number/date, invoice amount, check number, invoice date, vendor name, agency, journal description, journal line description, amount.

**FR-012 — Budget Tracker extraction** (Must, Phase 1)
Extract: invoice-detail rows (account, vendor, description, date, invoice number, status, comment, owner, approver); actuals rows including reconciliation markers (cleared status, comments); per-account budget figures (budget, actuals-to-date, estimate-to-complete, estimate-at-completion, delta, notes).

**FR-013 — Structural noise handling** (Must, Phase 1)
Correctly handle real-world report structure: title/header preamble rows, subtotal rows ("TOTAL FOR ACCOUNT…"), blank rows, merged cells, and repeated headers — excluding them from data rows while retaining subtotals for cross-checks (FR-023).

**FR-014 — Value normalization** (Must, Phase 1) `ASSUMPTION (A-12)`
Normalize dates, fiscal periods, currency amounts, and identifiers into consistent internal representations, including negative amounts, credits, and placeholder values (".", blanks).

**FR-015 — Raw value preservation (data lineage)** (Must, Phase 1) `PROPOSED`
Retain the original raw value alongside every normalized value, traceable to file/sheet/row/column. *Justification: audit and trust demand that any number on screen can be traced to the exact cell it came from.*

**FR-016 — Extraction confidence indication** (Should, Phase 1)
Assign a confidence level to extracted rows/fields and surface low-confidence items prominently during verification.

**FR-017 — Configurable extraction templates** (Should, Phase 2)
Support per-document-type extraction templates that authorized users can adjust (e.g., column mappings) without code changes, with changes versioned and audited.

**FR-018 — Invoice-document extraction** (Must, Phase 3) `ASSUMPTION (A-05, partially validated)`
Extract from invoices, per the validated real sample (HCL America format — summary page plus line-item annexure): invoice number, invoice date, vendor, bill-to entity, attention/contact, goods-and-services type, segment, PO number (**may be absent**), vendor project ID and name, account manager, currency, payment terms; line items: description/resource name, item type, service period (from/to dates), units with unit-of-measure (e.g., MHR, EA), rate, amount; delivery-location subtotals (onshore/offshore) and totals. Other vendors' formats pending validation.

**FR-019 — Reference-document extraction** (Must, Phase 3) `ASSUMPTION (A-05)` `PENDING VALIDATION`
Extract from POs (number, vendor, value, balance, period), SOWs (reference, vendor, period, scope, approved resources/categories), rate cards (resource/role rates, effective dates), and approved estimates.

**FR-020 — Resource loading extraction** (Must, Phase 2)
Extract resource loading data per the designed schema (DEC-012): resource ID/name/type, vendor, contract/SOW reference, department, account, bill rate, cost rate, allocation %, start/end dates, status, manager/owner, fiscal period, comments.

### 3.3 Data Validation (quality of ingested data)

**FR-021 — Schema validation** (Must, Phase 1)
Validate extracted data against the expected structure per document type; report missing columns, unexpected columns, and type mismatches.

**FR-022 — Row-level quality checks** (Must, Phase 1)
Flag rows with missing required fields, invalid account numbers, malformed dates/periods, or non-numeric amounts.

**FR-023 — Internal consistency checks** (Should, Phase 1) `PROPOSED`
Cross-check extracted detail rows against the report's own subtotal/total rows and flag discrepancies. *Justification: the cheapest possible detection of extraction errors — the file audits itself.*

**FR-024 — Quarantine, not abort** (Should, Phase 1) `PROPOSED`
When some rows fail validation, quarantine those rows for user attention and proceed with the valid remainder, clearly reporting what was excluded. *Justification: one bad row must not block a month-end review.*

**FR-025 — Data quality summary per cycle** (Should, Phase 1) `PROPOSED`
Produce a per-cycle data quality summary (rows ingested, rows quarantined, confidence distribution, consistency check results) visible before verification. *Justification: the Operator needs to judge "is this data fit to analyze?" at a glance.*

### 3.4 User Verification

**FR-026 — Mandatory verification gate** (Must, Phase 1)
No analysis runs on unverified data. Each document's extraction must be explicitly approved by the user before the rules engine may consume it.

**FR-027 — Verification view with source traceability** (Must, Phase 1)
Present extracted data for review such that any row can be traced to its source file/sheet/row. Low-confidence and quarantined items are highlighted.

**FR-028 — User corrections with full audit** (Must, Phase 1)
Allow the user to correct extracted values before approval. Corrections preserve the original extracted value, the corrected value, the user, and the timestamp, and are visible in lineage thereafter.

**FR-029 — Verification decisions per document** (Must, Phase 1)
The user may approve, approve-with-corrections, or reject (triggering re-extraction or file replacement) each document. Decisions are logged.

### 3.5 Budget Analysis

**FR-030 — Planned vs. actual variance** (Must, Phase 1)
Compute variance (amount and %) between planned budget and actual spend per department, GL account, and vendor for the reporting month and year-to-date. Budget granularity is monthly (A-04 resolved 2026-07-09).

**FR-031 — Budget workbook figures support** (Must, Phase 1)
Ingest and use existing budget-management figures where present: budget, actuals-to-date, estimate-to-complete, estimate-at-completion, delta.

**FR-032 — Month-over-month change detection** (Must, Phase 1) `ASSUMPTION (A-07)`
Detect unusual month-over-month spend increases/decreases per account and vendor against configurable thresholds.

**FR-033 — Over/underspend flagging with severity** (Must, Phase 1) `OPEN QUESTION (OQ-8)`
Flag over-budget and materially under-budget positions, classified by severity against configurable materiality thresholds (defaults pending OQ-8).

**FR-034 — Run-rate projection** (Should, Phase 1)
Compute deterministic run-rate projections (e.g., projected year-end position from YTD actuals) and flag accounts/vendors trending toward overrun. All projection math is deterministic; AI may only narrate it.

**FR-035 — Variance contributor ranking** (Should, Phase 1)
Rank the top contributors (accounts, vendors) to overall variance so attention goes to what matters most.

**FR-036 — Multi-month trend risk** (Should, Phase 1) `ASSUMPTION (A-07)`
Detect sustained adverse trends (e.g., N consecutive months of growth in an account/vendor) per configurable rules.

### 3.6 GED Analysis

**FR-037 — Missing entry detection** (Must, Phase 1) `OPEN QUESTION (OQ-5)` `ASSUMPTION (A-07)`
Detect expected-but-absent GED entries for the reporting month. Baseline source (historical pattern vs. finance-maintained expected list) is pending OQ-5; requirement stands under either.

**FR-038 — Duplicate entry detection** (Must, Phase 1)
Detect candidate duplicate GED entries (matching on configurable key fields such as account, vendor, amount, period). Must distinguish true duplicates from legitimate accounting events (see FR-041).

**FR-039 — Delayed posting detection** (Should, Phase 1) `OPEN QUESTION (OQ-7)`
Flag entries posted after the expected monthly cutoff. Cutoff calendar pending OQ-7; configurable in the interim.

**FR-040 — Amount anomaly detection** (Must, Phase 1) `ASSUMPTION (A-07)`
Flag GED amounts materially above/below the historical pattern for that account/vendor combination (e.g., vs. trailing three-month average; parameters in the Rules Catalog).

**FR-041 — Accounting-event awareness** (Should, Phase 1) `PROPOSED`
Classify journal lines by event type using observable markers (payroll interface entries, reclassification journals such as "RECLAS", accrual entries and reversals) and apply appropriate rule treatment, so reclasses and accrual reversals are not falsely flagged as duplicates or anomalies. *Justification: without this, the most routine accounting events become monthly false positives — the fastest path to alert fatigue and lost trust.*

**FR-042 — Coding and vendor-expectation checks** (Should, Phase 1)
Flag entries under unexpected account/department combinations or from vendors not previously associated with that account, per configurable reference expectations.

**FR-043 — GED summarization** (Must, Phase 1)
Summarize GED spend by department, account, vendor, and fiscal period, including counts, totals, and comparisons to prior periods.

### 3.7 Reconciliation

**FR-044 — Automated GED-to-tracker matching** (Must, Phase 1)
Automatically match GED journal lines against invoice-tracker entries, replacing today's manual paste-and-clear process. Match key semantics and tolerances are defined in the Rules Catalog.

**FR-045 — Match confidence tiers** (Must, Phase 1)
Classify each match as exact, probable, or unmatched. Probable matches require user confirmation; only user-confirmed or exact matches count as reconciled.

**FR-046 — Manual match and unmatch** (Must, Phase 1)
Allow the Operator to manually match, unmatch, or override proposed matches, with reason capture and full audit.

**FR-047 — Cleared-status tracking** (Must, Phase 1) `ASSUMPTION (A-10)`
Maintain a cleared/uncleared status per tracker entry equivalent to today's `clrd` column, including comments.

**FR-048 — Unreconciled items reporting** (Must, Phase 1)
Report all unreconciled items at any time: GED lines without tracker matches and tracker entries without GED activity.

**FR-049 — Cross-month carry-forward** (Should, Phase 1) `PROPOSED`
Carry unreconciled items forward into subsequent cycles until resolved, with aging (e.g., "unmatched for 2 months"). *Justification: timing differences are normal (invoice posted in July for June service); without carry-forward every timing difference becomes a permanent loose end.*

**FR-050 — Reconciliation scope configuration** (Must, Phase 1) `ASSUMPTION`
Restrict reconciliation to configured account ranges (e.g., vendor/expense accounts), excluding non-invoiced spend such as payroll and benefits. Eligible account list pending finance validation.

### 3.8 Invoice Review *(Phase 3. Invoice format partially validated by real sample 2026-07-09; PO/SOW/rate-card documents still `PENDING VALIDATION` (A-05))*

**FR-051 — PO matching** (Must, Phase 3)
Validate invoice amounts against PO remaining balance; flag invoices exceeding available balance. Invoices carrying no PO reference (observed in the real sample) are themselves flagged as a finding ("missing PO reference"), not treated as errors or skipped.

**FR-052 — SOW period and scope validation** (Must, Phase 3)
Validate invoice billing periods fall within SOW start/end dates and billed work is within SOW scope/categories.

**FR-053 — Rate card validation** (Must, Phase 3)
Validate billed rates against the approved rate card per resource/role, within configurable tolerance.

**FR-054 — Hours validation** (Must, Phase 3)
Validate billed hours against approved estimates or timesheet references, within configurable tolerance.

**FR-055 — Resource authorization validation** (Must, Phase 3)
Validate billed resources appear in the approved staffing/resource plan for that engagement.

**FR-056 — Code and category validation** (Must, Phase 3)
Validate project/account codes, cost centers, and billing categories against approved references.

**FR-057 — Duplicate invoice detection** (Must, Phase 3)
Detect resubmitted or duplicate invoices (same number, or same vendor+period+amount pattern).

**FR-058 — Deliverable confirmation check** (Should, Phase 3)
Where deliverable records exist, flag invoices billing for work not confirmed as delivered.

**FR-059 — Invoice status recommendation** (Must, Phase 3)
Classify every reviewed invoice as exactly one of: Ready for approval · Needs clarification · Hold for review · Recommend rejection · Partial approval candidate — each with the specific rule findings that produced the status. FinSight recommends; it never approves, rejects, or communicates with vendors.

**FR-060 — Line-item level findings** (Should, Phase 3)
Attribute findings to specific invoice line items so partial-approval candidates identify exactly which lines are clean and which are not.

**FR-121 — Line-item type differentiation** (Must, Phase 3) *(ID appended after initial issue; validated by real sample)*
Classify invoice line items by type — labor (resource/hours/rate), tax (e.g., BEAT tax), expense, other — and apply validation appropriate to each type. Rate-card and hours checks apply to labor lines only; non-labor lines are validated against their own references where they exist, and surfaced for review where they do not.

**FR-122 — Vendor project reference capture** (Should, Phase 3) *(ID appended after initial issue; validated by real sample)*
Capture vendor-side project identifiers from invoices (project ID, project name, segment — e.g., `C/314993`, "Amerisure – CDX Staffing", "APPS") and support mapping them to departments/accounts/contracts via reference data. This introduces a project dimension at the invoice level (GED data remains dept/account/vendor — A-02 unchanged) and directly supports the Contract Mappings view (FR-067).

### 3.9 Resource Management *(Phase 2)*

**FR-061 — Resource registry** (Must, Phase 2)
Maintain resource records per the designed schema (DEC-012), populated from ingested resource loading sheets.

**FR-062 — Status and period tracking** (Must, Phase 2)
Track active/inactive status with effective dates and allocation periods; status changes are recorded, dated, and auditable from day one (supports future attrition analysis, DEC-014).

**FR-063 — Resource cost visibility** (Must, Phase 2)
Compute and display resource cost (rate × allocation × period) by resource, vendor, department, and account.

**FR-064 — Budget-to-resource analysis** (Must, Phase 2)
Show what portion of an account's budget/actuals is attributable to which resources, connecting resource costs to budget lines.

**FR-065 — Resource change history** (Should, Phase 2)
Show a resource's history over time: rate changes, allocation changes, status transitions.

### 3.10 Contract Mapping *(Phase 2; contract document details `PENDING VALIDATION`)*

**FR-066 — Contract/SOW registry** (Must, Phase 2)
Maintain basic contract/SOW records (reference, vendor, period, value where known) from ingested data or manual entry.

**FR-067 — Contract mappings view** (Must, Phase 2)
Provide a navigable view of relationships: Resources ↔ Contracts/SOWs ↔ Vendors ↔ Departments ↔ Accounts ↔ Budget allocations — answering: which resources are funded by which contracts, which vendors bill where, and the budget impact of each contract.

**FR-068 — Contract coverage checks** (Should, Phase 2) `PROPOSED`
Flag governance gaps: active resources with no contract reference, contracts past end date with active resources, and resources billing to accounts inconsistent with their mapping. *Justification: contract governance is a stated goal; these are its three most common failure modes.*

### 3.11 Findings Management

**FR-069 — Findings as first-class records** (Must, Phase 1)
Every rule violation/exception is a persistent finding: unique ID, rule reference, severity, reporting period, affected entities (account/vendor/document/row), and computed evidence values.

**FR-070 — Severity classification** (Must, Phase 1) `OPEN QUESTION (OQ-8)`
Classify findings Critical / High / Medium / Low per rule-defined, configurable criteria. Defaults pending OQ-8.

**FR-071 — Full traceability per finding** (Must, Phase 1)
From any finding, the user can navigate to: the rule that produced it, the input values used, and the source rows/files those values came from.

**FR-072 — Finding lifecycle** (Must, Phase 1) `PROPOSED`
Findings carry a workflow state: New → Acknowledged → In review → Resolved / Dismissed. Dismissal requires a reason. All transitions are logged with user and timestamp. *Justification: the source spec generates findings but says nothing about what happens to them; without a lifecycle, the same finding nags forever and audit cannot show how exceptions were handled.*

**FR-073 — Recurrence linkage** (Should, Phase 1) `PROPOSED`
Link findings recurring across months (same rule, same entities) and display recurrence count. *Justification: "third month in a row" is materially different information than "new this month."*

**FR-074 — Findings browsing** (Must, Phase 1)
Filter, sort, and group findings by severity, status, rule, category, account, vendor, and period.

**FR-075 — False-positive feedback** (Should, Phase 1) `PROPOSED`
Allow users to mark findings as false positives with a reason, building an evidence base for threshold tuning. Feedback informs configuration changes made by humans; it never silently alters rule behavior. *Justification: threshold tuning without recorded evidence is guesswork; silent self-tuning would break determinism.*

### 3.12 Executive Reporting

**FR-076 — Monthly leadership summary** (Must, Phase 1)
Generate the monthly summary: overall RAG status; Budget Health (plan, actual, variance, top over-budget accounts/vendors, MoM change, YTD risk); GED Status (expected vs. received, missing, duplicates, delayed, unusual); Invoice Exceptions (Phase 3); Key Risks; Recommended Actions.

**FR-077 — Deterministic RAG status** (Must, Phase 1)
The Green/Yellow/Red status is computed by deterministic, configurable criteria — never assigned by AI.

**FR-078 — Month-over-month comparison view** (Must, Phase 1)
Provide a "what changed since last month" view: spend deltas, new/resolved/recurring findings, status changes.

**FR-079 — Report reproducibility and history** (Must, Phase 1)
Retain every generated report; any historical report can be re-displayed exactly as produced. Regeneration against the same verified inputs and configuration yields identical deterministic content.

**FR-080 — AI narrative sections clearly separated** (Must, Phase 1)
Where AI narrative is included in reports, it is visually and structurally distinct from deterministic content and labeled as AI-generated, including provider/model attribution.

### 3.13 Notifications & Alerts

**FR-081 — Review-cycle status tracking** (Should, Phase 1) `PROPOSED`
Show the state of the current cycle at all times: files ingested, awaiting verification, analysis complete, report generated — with outstanding items. *Justification: month-end is a checklist process; users need to know "where am I and what's left."*

**FR-082 — Critical findings surfaced on completion** (Should, Phase 1)
When analysis completes, present Critical/High findings prominently before anything else.

**FR-083 — No external notifications in MVP** (Must, Phase 1)
The MVP sends no emails or external messages of any kind (consistent with read-only, no-vendor-communication boundaries). External notification is a future-phase consideration.

### 3.14 Audit Logging

**FR-084 — Ingestion and access audit** (Must, Phase 1)
Log every file ingestion, classification, period assignment, and data access with user identity and timestamp.

**FR-085 — Extraction and verification audit** (Must, Phase 1)
Log extraction runs, quarantines, user corrections (original and corrected values), and verification decisions.

**FR-086 — Rule execution audit** (Must, Phase 1)
Log every analysis run: rule set version, configuration/threshold values in effect, input data fingerprint, rules executed, findings produced.

**FR-087 — AI interaction audit** (Must, Phase 1)
Log every AI interaction: provider, model and version, what data was transmitted, masking applied (if any), the consent reference authorizing it, the prompt category, and the output received.

**FR-088 — Consent audit** (Must, Phase 1)
Log every consent grant, scope, and revocation: who, when, provider, operation type.

**FR-089 — Reporting and export audit** (Must, Phase 1)
Log every report generation and every export (what content left the application, in what format, when, by whom).

**FR-090 — Audit trail review** (Should, Phase 1)
Provide an in-application, searchable, filterable view of the audit trail, and support export of audit records.

### 3.15 AI Insights *(all AI features are optional; the application is fully functional with AI disabled — FR-095)*

**FR-091 — AI narrative explanation of findings** (Should, Phase 1)
Generate plain-language explanations of rule-engine findings ("what happened, why it matters, what to do"), derived exclusively from rule outputs and their evidence.

**FR-092 — AI-generated summary narrative** (Should, Phase 1)
Generate the narrative portions of the monthly summary from deterministic results, in leadership-appropriate language.

**FR-093 — AI recommendations from deterministic outputs** (Should, Phase 1)
Generate recommended-action suggestions based solely on findings and their evidence, clearly labeled as AI-generated suggestions for human judgment.

**FR-094 — AI grounding constraint** (Must, Phase 1)
AI-generated content must be grounded in rule-engine outputs and verified data. The AI layer must not introduce financial figures, findings, or conclusions absent from deterministic results. AI responses must decline questions whose answers are not supported by available data.

**FR-095 — AI-off completeness** (Must, Phase 1)
Every number, finding, status, reconciliation result, and report section (except AI narrative) is available with no AI provider configured or consented.

**FR-096 — Consent flow before transmission** (Must, Phase 1) `ASSUMPTION (A-13)`
Before any data transmission to an AI provider: disclose the provider, the specific data to be transmitted, and privacy implications; require explicit consent; log it (FR-088). Consent is revocable in settings; revocation stops future transmissions immediately.

**FR-097 — Provider selection and warnings** (Must, Phase 1)
The user selects the AI provider from configured options. Providers outside the organization-recommended list trigger an explicit warning state before consent can be given.

**FR-098 — Masking/tokenization option** (Should, Phase 1)
Support masking or tokenizing sensitive values (vendor names, resource names, amounts, identifiers) before AI transmission, per configuration; the UI shows whether masking is active. Token-to-real mapping never leaves the application.

**FR-099 — AI answer citation** (Should, Phase 1) `PROPOSED`
AI-generated answers and narratives cite the finding IDs / data points they are based on, so users can verify any claim in one click. *Justification: cited answers are checkable answers; this is the single strongest defense against silent hallucination eroding trust.*

### 3.16 Search & Q&A

**FR-100 — Natural-language Q&A** (Should, Phase 1)
Answer natural-language questions over the current cycle's verified data and findings (e.g., the five canonical questions: vendors trending over budget; invoices needing attention; what changed; projects at overrun risk; missing GED entries). Answers obey FR-094 grounding and FR-099 citation.

**FR-101 — Question library** (Should, Phase 1)
Offer predefined, one-click questions covering the canonical leadership questions, usable with or without AI (backed by deterministic views where possible).

**FR-102 — Non-AI structured search** (Must, Phase 1) `PROPOSED`
Provide full browse/search/filter across data and findings (by vendor, account, amount range, period, status) requiring no AI. *Justification: search is a core function that must not depend on an optional, consent-gated feature.*

### 3.17 Configuration

**FR-103 — Configurable analysis parameters** (Must, Phase 1)
All thresholds, tolerances, and rule parameters are configurable without code changes: variance materiality, anomaly sensitivity, duplicate match keys, cutoff dates, reconciliation scope.

**FR-104 — AI provider configuration** (Must, Phase 1)
AI providers are configurable: add/select providers, mark the organization-recommended set (administrator-managed), set masking behavior. Per DEC-006/DEC-007 the recommended list is advisory; consent (FR-096) remains the final gate.

**FR-105 — Reference data management** (Should, Phase 1)
Maintain reference data used by rules: account list and categories, vendor expectations, fiscal calendar, reconciliation-eligible accounts, (Phase 2+) resource and contract references.

**FR-106 — Rule enable/disable as governed change** (Should, Phase 1)
Authorized users may enable/disable individual rules or rule groups. Changes are versioned, logged, and visible in analysis audit records (FR-086). Rule sets cannot vary per-run or be altered by agents.

**FR-107 — Configuration versioning** (Must, Phase 1) `PROPOSED`
Every configuration change is versioned with user/timestamp/before-after values, and every analysis run records the configuration version used. *Justification: reproducibility (a finding must be explainable by the thresholds in force at the time) — without this, determinism is unverifiable in practice.*

### 3.18 Historical Analysis

**FR-108 — Multi-month retention** (Must, Phase 1)
Retain verified data, findings, reconciliation results, reports, and configurations across months as the basis for trends, baselines, and comparisons.

**FR-109 — Trend views** (Should, Phase 1)
Display spend trends over time by account and vendor, with findings-count and exception-value trends.

**FR-110 — Historical import** (Should, Phase 1) `ASSUMPTION (A-07)`
Support importing prior months' files at onboarding to establish baselines before the first live cycle.

**FR-111 — Cold-start graceful degradation** (Must, Phase 1) `PROPOSED`
Pattern-based rules declare their minimum history requirement; below it they report "insufficient history" rather than firing unreliable findings, and the report states which rules ran with limited baselines. *Justification: the first months are when FinSight is judged; noisy or silent-but-unexplained behavior at cold start is an adoption killer.*

### 3.19 Forecasting & What-If *(Phase 4; all computation deterministic, AI narrates only)*

**FR-112 — Deterministic forecasting** (Must, Phase 4)
Project year-end / period-end positions from actuals, run rates, and (Phase 2+) resource allocation data, with stated calculation methods.

**FR-113 — Resource departure impact analysis** (Must, Phase 4)
Given a resource's departure date, compute the budget impact: remaining planned cost released, by account and period (data model support exists from Phase 2 — FR-062).

**FR-114 — Backfill scenario estimation** (Should, Phase 4)
Model replacement scenarios (rate, start date, allocation) and compute net budget effect deterministically.

**FR-115 — What-if scenario framework** (Should, Phase 4)
Allow parameterized what-if questions (spend change, vendor change, resource change) computed deterministically, with AI narration of results clearly labeled and scenario results clearly marked as hypothetical — never mixed with actuals.

### 3.20 Export & Reporting Output

**FR-116 — Leadership summary export** (Must, Phase 1)
Export the monthly summary in shareable, print-ready form suitable for distribution to stakeholders who do not use FinSight.

**FR-117 — Data and findings export** (Must, Phase 1)
Export findings, reconciliation results, and summarized data in spreadsheet-compatible form.

**FR-118 — Workbook-compatible export** (Should, Phase 1) `ASSUMPTION (A-10)`
Export reconciliation results in a form compatible with the existing Budget Tracker workbook process, supporting coexistence during the trust-building period.

**FR-119 — Audit export** (Should, Phase 1)
Export audit trail records for external review (see FR-090).

**FR-120 — Export labeling** (Must, Phase 1) `PROPOSED`
All exports carry: generation timestamp, reporting period, data-as-of information, configuration version, and AI-content labeling identical to the in-app presentation. *Justification: exported documents live forever in email; unlabeled AI content or undated data in circulation is a governance failure waiting to happen.*

---

## 4. Traceability note

Every FR above traces to: the two source specification documents, the GED/Budget Tracker sample analysis, the real invoice sample (DEC-018), team decisions DEC-001–DEC-019, or is marked `PROPOSED` with justification. The Rules Catalog (04) will trace each rule to the FRs it implements; the architecture (05) must satisfy these FRs without weakening any Must.
