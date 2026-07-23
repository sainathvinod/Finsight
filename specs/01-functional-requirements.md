# FinSight — Functional Requirements

**Document:** 01-functional-requirements.md
**Status:** Approved
**Date:** 2026-07-09
**Scope:** WHAT FinSight must do. Contains no architecture, technology, framework, database, or implementation decisions.
**Companion documents:** 00-project-understanding.md · 02-non-functional-requirements.md · 09-decision-log.md

---

## 1. Conventions

- **ID:** `FR-nnn`, unique and permanent. Retired requirements are marked superseded, never renumbered.
- **Priority (MoSCoW):** Must / Should / Could — priority for the *product*, independent of build order.
- **Phase:** 1–4 per the agreed delivery sequence (DEC-009). Phase ≠ priority: Invoice Review is a Must, delivered in Phase 3.
- **Tags** *(historical; all resolved and Approved in the current baseline)*:
  - *Assumption tags* rested on the Assumptions Register (§2); confirmed under the approved baseline.
  - *Validation tags* are resolved; all such items are Approved in the current baseline.
  - *Open-question tags* are resolved by the approved baseline.
  - *Proposed tags* were accepted into the approved baseline.
- **Personas used in this document** *(per A-09)*: **Operator** — performs ingestion, verification, reconciliation; **Leader** — consumes summaries, findings, Q&A, and makes decisions. These may be the same person in different modes.

## 2. Assumptions Register

Any FR citing an assumption becomes invalid if that assumption fails, and must be revisited.

All assumptions in this register are accepted as the approved basis of the current baseline (project-owner approval; documentary date not recorded in repository).

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

### FR-001 — Ingest Excel workbooks
- **Classification:** Must, Phase 1 · **Status:** Approved
Accept Excel files provided by the user, including multi-sheet workbooks (GED reports, Budget Tracker with Details/Actuals/Original Budget sheets).

### FR-002 — Ingest PDF documents
- **Classification:** Must, Phase 3 · **Status:** Approved
Accept PDF documents (invoices, POs, SOWs, rate cards, contracts). Formats assumed until samples are provided.

### FR-003 — Read-only source handling
- **Classification:** Must, Phase 1 · **Status:** Approved
Never modify, move, or delete a user's source file. All processing operates on ingested copies.

### FR-004 — Document type classification with user confirmation
- **Classification:** Must, Phase 1 · **Status:** Approved
Automatically classify each ingested file (GED report, budget tracker, invoice, PO, SOW, rate card, resource sheet, unknown) and require the user to confirm or correct the classification before processing. Classification may be AI-assisted, but the user's confirmation is authoritative.

### FR-005 — Reporting-period assignment
- **Classification:** Must, Phase 1 · **Status:** Approved
Every ingested file is assigned to a reporting month/year, proposed automatically where detectable (e.g., "Year-To-Date for Period May") and confirmed by the user.

### FR-006 — Review-cycle grouping
- **Classification:** Must, Phase 1 · **Status:** Approved
Group a month's ingested files into a named review cycle that progresses through the pipeline as a unit (ingest → verify → analyze → report).

### FR-007 — File-level validation with clear rejection
- **Classification:** Must, Phase 1 · **Status:** Approved
Reject unreadable, corrupt, password-protected, or unsupported files with a message stating exactly what is wrong and what the user can do.

### FR-008 — Duplicate file detection
- **Classification:** Should, Phase 1 · **Status:** Approved
Detect when an identical or near-identical file (by content) has already been ingested for the same cycle and warn before proceeding. *Justification: re-uploading last month's file by mistake is the most likely user error and would silently poison every downstream result.*

### FR-009 — File replacement with versioning
- **Classification:** Should, Phase 1 · **Status:** Approved
Allow a corrected file to replace a previously ingested one within a cycle; retain the superseded version and re-run affected downstream steps. *Justification: corrected re-exports are routine in month-end processes; without versioning, lineage breaks.*

### FR-010 — File provenance record
- **Classification:** Must, Phase 1 · **Status:** Approved
For every ingested file record: original filename, content fingerprint, ingestion timestamp, ingesting user, assigned period, and classification.

### 3.2 Data Extraction

### FR-011 — GED extraction
- **Classification:** Must, Phase 1 · **Status:** Approved
Extract from GED reports the observed fields: department number/name, account number/name, fiscal period, journal number/date, invoice amount, check number, invoice date, vendor name, agency, journal description, journal line description, amount.

### FR-012 — Budget Tracker extraction
- **Classification:** Must, Phase 1 · **Status:** Approved
Extract: invoice-detail rows (account, vendor, description, date, invoice number, status, comment, owner, approver); actuals rows including reconciliation markers (cleared status, comments); per-account budget figures (budget, actuals-to-date, estimate-to-complete, estimate-at-completion, delta, notes).

### FR-013 — Structural noise handling
- **Classification:** Must, Phase 1 · **Status:** Approved
Correctly handle real-world report structure: title/header preamble rows, subtotal rows ("TOTAL FOR ACCOUNT…"), blank rows, merged cells, and repeated headers — excluding them from data rows while retaining subtotals for cross-checks (FR-023).

### FR-014 — Value normalization
- **Classification:** Must, Phase 1 · **Status:** Approved
Normalize dates, fiscal periods, currency amounts, and identifiers into consistent internal representations, including negative amounts, credits, and placeholder values (".", blanks).

### FR-015 — Raw value preservation (data lineage)
- **Classification:** Must, Phase 1 · **Status:** Approved
Retain the original raw value alongside every normalized value, traceable to file/sheet/row/column. *Justification: audit and trust demand that any number on screen can be traced to the exact cell it came from.*

### FR-016 — Extraction confidence indication
- **Classification:** Should, Phase 1 · **Status:** Approved
Assign a confidence level to extracted rows/fields and surface low-confidence items prominently during verification.

### FR-017 — Configurable extraction templates
- **Classification:** Should, Phase 2 · **Status:** Approved
Support per-document-type extraction templates that authorized users can adjust (e.g., column mappings) without code changes, with changes versioned and audited.

### FR-018 — Invoice-document extraction
- **Classification:** Must, Phase 3 · **Status:** Approved
Extract from invoices, per the validated real sample (HCL America format — summary page plus line-item annexure): invoice number, invoice date, vendor, bill-to entity, attention/contact, goods-and-services type, segment, PO number (**may be absent**), vendor project ID and name, account manager, currency, payment terms; line items: description/resource name, item type, service period (from/to dates), units with unit-of-measure (e.g., MHR, EA), rate, amount; delivery-location subtotals (onshore/offshore) and totals. Other vendors' formats are Approved in the current baseline.

### FR-019 — Reference-document extraction
- **Classification:** Must, Phase 3 · **Status:** Approved
Extract from POs (number, vendor, value, balance, period), SOWs (reference, vendor, period, scope, approved resources/categories), rate cards (resource/role rates, effective dates), and approved estimates.

### FR-020 — Resource loading extraction
- **Classification:** Must, Phase 2 · **Status:** Approved
Extract resource loading data per the designed schema (DEC-012): resource ID/name/type, vendor, contract/SOW reference, department, account, bill rate, cost rate, allocation %, start/end dates, status, manager/owner, fiscal period, comments.

### 3.3 Data Validation (quality of ingested data)

### FR-021 — Schema validation
- **Classification:** Must, Phase 1 · **Status:** Approved
Validate extracted data against the expected structure per document type; report missing columns, unexpected columns, and type mismatches.

### FR-022 — Row-level quality checks
- **Classification:** Must, Phase 1 · **Status:** Approved
Flag rows with missing required fields, invalid account numbers, malformed dates/periods, or non-numeric amounts.

### FR-023 — Internal consistency checks
- **Classification:** Should, Phase 1 · **Status:** Approved
Cross-check extracted detail rows against the report's own subtotal/total rows and flag discrepancies. *Justification: the cheapest possible detection of extraction errors — the file audits itself.*

### FR-024 — Quarantine, not abort
- **Classification:** Should, Phase 1 · **Status:** Approved
When some rows fail validation, quarantine those rows for user attention and proceed with the valid remainder, clearly reporting what was excluded. *Justification: one bad row must not block a month-end review.*

### FR-025 — Data quality summary per cycle
- **Classification:** Should, Phase 1 · **Status:** Approved
Produce a per-cycle data quality summary (rows ingested, rows quarantined, confidence distribution, consistency check results) visible before verification. *Justification: the Operator needs to judge "is this data fit to analyze?" at a glance.*

### 3.4 User Verification

### FR-026 — Mandatory verification gate
- **Classification:** Must, Phase 1 · **Status:** Approved
No analysis runs on unverified data. Each document's extraction must be explicitly approved by the user before the rules engine may consume it.

### FR-027 — Verification view with source traceability
- **Classification:** Must, Phase 1 · **Status:** Approved
Present extracted data for review such that any row can be traced to its source file/sheet/row. Low-confidence and quarantined items are highlighted.

### FR-028 — User corrections with full audit
- **Classification:** Must, Phase 1 · **Status:** Approved
Allow the user to correct extracted values before approval. Corrections preserve the original extracted value, the corrected value, the user, and the timestamp, and are visible in lineage thereafter.

### FR-029 — Verification decisions per document
- **Classification:** Must, Phase 1 · **Status:** Approved
The user may approve, approve-with-corrections, or reject (triggering re-extraction or file replacement) each document. Decisions are logged.

### 3.5 Budget Analysis

### FR-030 — Planned vs. actual variance
- **Classification:** Must, Phase 1 · **Status:** Approved
Compute variance (amount and %) between planned budget and actual spend per department, GL account, and vendor for the reporting month and year-to-date. Budget granularity is monthly (A-04 resolved 2026-07-09).

### FR-031 — Budget workbook figures support
- **Classification:** Must, Phase 1 · **Status:** Approved
Ingest and use existing budget-management figures where present: budget, actuals-to-date, estimate-to-complete, estimate-at-completion, delta.

### FR-032 — Month-over-month change detection
- **Classification:** Must, Phase 1 · **Status:** Approved
Detect unusual month-over-month spend increases/decreases per account and vendor against configurable thresholds.

### FR-033 — Over/underspend flagging with severity
- **Classification:** Must, Phase 1 · **Status:** Approved
Flag over-budget and materially under-budget positions, classified by severity against configurable materiality thresholds (defaults set in configuration under the approved baseline).

### FR-034 — Run-rate projection
- **Classification:** Should, Phase 1 · **Status:** Approved
Compute deterministic run-rate projections (e.g., projected year-end position from YTD actuals) and flag accounts/vendors trending toward overrun. All projection math is deterministic; AI may only narrate it.

### FR-035 — Variance contributor ranking
- **Classification:** Should, Phase 1 · **Status:** Approved
Rank the top contributors (accounts, vendors) to overall variance so attention goes to what matters most.

### FR-036 — Multi-month trend risk
- **Classification:** Should, Phase 1 · **Status:** Approved
Detect sustained adverse trends (e.g., N consecutive months of growth in an account/vendor) per configurable rules.

### 3.6 GED Analysis

### FR-037 — Missing entry detection
- **Classification:** Must, Phase 1 · **Status:** Approved
Detect expected-but-absent GED entries for the reporting month. Baseline source (historical pattern vs. finance-maintained expected list) is resolved under the approved baseline; requirement stands under either.

### FR-038 — Duplicate entry detection
- **Classification:** Must, Phase 1 · **Status:** Approved
Detect candidate duplicate GED entries (matching on configurable key fields such as account, vendor, amount, period). Must distinguish true duplicates from legitimate accounting events (see FR-041).

### FR-039 — Delayed posting detection
- **Classification:** Should, Phase 1 · **Status:** Approved
Flag entries posted after the expected monthly cutoff. Cutoff calendar resolved under the approved baseline; configurable.

### FR-040 — Amount anomaly detection
- **Classification:** Must, Phase 1 · **Status:** Approved
Flag GED amounts materially above/below the historical pattern for that account/vendor combination (e.g., vs. trailing three-month average; parameters in the Rules Catalog).

### FR-041 — Accounting-event awareness
- **Classification:** Should, Phase 1 · **Status:** Approved
Classify journal lines by event type using observable markers (payroll interface entries, reclassification journals such as "RECLAS", accrual entries and reversals) and apply appropriate rule treatment, so reclasses and accrual reversals are not falsely flagged as duplicates or anomalies. *Justification: without this, the most routine accounting events become monthly false positives — the fastest path to alert fatigue and lost trust.*

### FR-042 — Coding and vendor-expectation checks
- **Classification:** Should, Phase 1 · **Status:** Approved
Flag entries under unexpected account/department combinations or from vendors not previously associated with that account, per configurable reference expectations.

### FR-043 — GED summarization
- **Classification:** Must, Phase 1 · **Status:** Approved
Summarize GED spend by department, account, vendor, and fiscal period, including counts, totals, and comparisons to prior periods.

### 3.7 Reconciliation

### FR-044 — Automated GED-to-tracker matching
- **Classification:** Must, Phase 1 · **Status:** Approved
Automatically match GED journal lines against invoice-tracker entries, replacing today's manual paste-and-clear process. Match key semantics and tolerances are defined in the Rules Catalog.

### FR-045 — Match confidence tiers
- **Classification:** Must, Phase 1 · **Status:** Approved
Classify each match as exact, probable, or unmatched. Probable matches require user confirmation; only user-confirmed or exact matches count as reconciled.

### FR-046 — Manual match and unmatch
- **Classification:** Must, Phase 1 · **Status:** Approved
Allow the Operator to manually match, unmatch, or override proposed matches, with reason capture and full audit.

### FR-047 — Cleared-status tracking
- **Classification:** Must, Phase 1 · **Status:** Approved
Maintain a cleared/uncleared status per tracker entry equivalent to today's `clrd` column, including comments.

### FR-048 — Unreconciled items reporting
- **Classification:** Must, Phase 1 · **Status:** Approved
Report all unreconciled items at any time: GED lines without tracker matches and tracker entries without GED activity.

### FR-049 — Cross-month carry-forward
- **Classification:** Should, Phase 1 · **Status:** Approved
Carry unreconciled items forward into subsequent cycles until resolved, with aging (e.g., "unmatched for 2 months"). *Justification: timing differences are normal (invoice posted in July for June service); without carry-forward every timing difference becomes a permanent loose end.*

### FR-050 — Reconciliation scope configuration
- **Classification:** Must, Phase 1 · **Status:** Approved
Restrict reconciliation to configured account ranges (e.g., vendor/expense accounts), excluding non-invoiced spend such as payroll and benefits. Eligible account list resolved under the approved baseline; configurable.

### 3.8 Invoice Review *(Phase 3. Invoice format validated by real sample 2026-07-09; PO/SOW/rate-card documents Approved in the current baseline)*

### FR-051 — PO matching
- **Classification:** Must, Phase 3 · **Status:** Approved
Validate invoice amounts against PO remaining balance; flag invoices exceeding available balance. Invoices carrying no PO reference (observed in the real sample) are themselves flagged as a finding ("missing PO reference"), not treated as errors or skipped.

### FR-052 — SOW period and scope validation
- **Classification:** Must, Phase 3 · **Status:** Approved
Validate invoice billing periods fall within SOW start/end dates and billed work is within SOW scope/categories.

### FR-053 — Rate card validation
- **Classification:** Must, Phase 3 · **Status:** Approved
Validate billed rates against the approved rate card per resource/role, within configurable tolerance.

### FR-054 — Hours validation
- **Classification:** Must, Phase 3 · **Status:** Approved
Validate billed hours against approved estimates or timesheet references, within configurable tolerance.

### FR-055 — Resource authorization validation
- **Classification:** Must, Phase 3 · **Status:** Approved
Validate billed resources appear in the approved staffing/resource plan for that engagement.

### FR-056 — Code and category validation
- **Classification:** Must, Phase 3 · **Status:** Approved
Validate project/account codes, cost centers, and billing categories against approved references.

### FR-057 — Duplicate invoice detection
- **Classification:** Must, Phase 3 · **Status:** Approved
Detect resubmitted or duplicate invoices (same number, or same vendor+period+amount pattern).

### FR-058 — Deliverable confirmation check
- **Classification:** Should, Phase 3 · **Status:** Approved
Where deliverable records exist, flag invoices billing for work not confirmed as delivered.

### FR-059 — Invoice status recommendation
- **Classification:** Must, Phase 3 · **Status:** Approved
Classify every reviewed invoice as exactly one of: Ready for approval · Needs clarification · Hold for review · Recommend rejection · Partial approval candidate — each with the specific rule findings that produced the status. FinSight recommends; it never approves, rejects, or communicates with vendors.

### FR-060 — Line-item level findings
- **Classification:** Should, Phase 3 · **Status:** Approved
Attribute findings to specific invoice line items so partial-approval candidates identify exactly which lines are clean and which are not.

### FR-121 — Line-item type differentiation
- **Classification:** Must, Phase 3 · **Status:** Approved *(ID appended after initial issue; validated by real sample)*
Classify invoice line items by type — labor (resource/hours/rate), tax (e.g., BEAT tax), expense, other — and apply validation appropriate to each type. Rate-card and hours checks apply to labor lines only; non-labor lines are validated against their own references where they exist, and surfaced for review where they do not.

### FR-122 — Vendor project reference capture
- **Classification:** Should, Phase 3 · **Status:** Approved *(ID appended after initial issue; validated by real sample)*
Capture vendor-side project identifiers from invoices (project ID, project name, segment — e.g., `C/314993`, "Amerisure – CDX Staffing", "APPS") and support mapping them to departments/accounts/contracts via reference data. This introduces a project dimension at the invoice level (GED data remains dept/account/vendor — A-02 unchanged) and directly supports the Contract Mappings view (FR-067).

### 3.9 Resource Management *(Phase 2)*

### FR-061 — Resource registry
- **Classification:** Must, Phase 2 · **Status:** Approved
Maintain resource records per the designed schema (DEC-012), populated from ingested resource loading sheets.

### FR-062 — Status and period tracking
- **Classification:** Must, Phase 2 · **Status:** Approved
Track active/inactive status with effective dates and allocation periods; status changes are recorded, dated, and auditable from day one (supports future attrition analysis, DEC-014).

### FR-063 — Resource cost visibility
- **Classification:** Must, Phase 2 · **Status:** Approved
Compute and display resource cost (rate × allocation × period) by resource, vendor, department, and account.

### FR-064 — Budget-to-resource analysis
- **Classification:** Must, Phase 2 · **Status:** Approved
Show what portion of an account's budget/actuals is attributable to which resources, connecting resource costs to budget lines.

### FR-065 — Resource change history
- **Classification:** Should, Phase 2 · **Status:** Approved
Show a resource's history over time: rate changes, allocation changes, status transitions.

### 3.10 Contract Mapping *(Phase 2; contract-document details Approved in the current baseline)*

### FR-066 — Contract/SOW registry
- **Classification:** Must, Phase 2 · **Status:** Approved
Maintain basic contract/SOW records (reference, vendor, period, value where known) from ingested data or manual entry.

### FR-067 — Contract mappings view
- **Classification:** Must, Phase 2 · **Status:** Approved
Provide a navigable view of relationships: Resources ↔ Contracts/SOWs ↔ Vendors ↔ Departments ↔ Accounts ↔ Budget allocations — answering: which resources are funded by which contracts, which vendors bill where, and the budget impact of each contract.

### FR-068 — Contract coverage checks
- **Classification:** Should, Phase 2 · **Status:** Approved
Flag governance gaps: active resources with no contract reference, contracts past end date with active resources, and resources billing to accounts inconsistent with their mapping. *Justification: contract governance is a stated goal; these are its three most common failure modes.*

### 3.11 Findings Management

### FR-069 — Findings as first-class records
- **Classification:** Must, Phase 1 · **Status:** Approved
Every rule violation/exception is a persistent finding: unique ID, rule reference, severity, reporting period, affected entities (account/vendor/document/row), and computed evidence values.

### FR-070 — Severity classification
- **Classification:** Must, Phase 1 · **Status:** Approved
Classify findings Critical / High / Medium / Low per rule-defined, configurable criteria. Defaults set in configuration under the approved baseline.

### FR-071 — Full traceability per finding
- **Classification:** Must, Phase 1 · **Status:** Approved
From any finding, the user can navigate to: the rule that produced it, the input values used, and the source rows/files those values came from.

### FR-072 — Finding lifecycle
- **Classification:** Must, Phase 1 · **Status:** Approved
Findings carry a workflow state: New → Acknowledged → In review → Resolved / Dismissed. Dismissal requires a reason. All transitions are logged with user and timestamp. *Justification: the source spec generates findings but says nothing about what happens to them; without a lifecycle, the same finding nags forever and audit cannot show how exceptions were handled.*

### FR-073 — Recurrence linkage
- **Classification:** Should, Phase 1 · **Status:** Approved
Link findings recurring across months (same rule, same entities) and display recurrence count. *Justification: "third month in a row" is materially different information than "new this month."*

### FR-074 — Findings browsing
- **Classification:** Must, Phase 1 · **Status:** Approved
Filter, sort, and group findings by severity, status, rule, category, account, vendor, and period.

### FR-075 — False-positive feedback
- **Classification:** Should, Phase 1 · **Status:** Approved
Allow users to mark findings as false positives with a reason, building an evidence base for threshold tuning. Feedback informs configuration changes made by humans; it never silently alters rule behavior. *Justification: threshold tuning without recorded evidence is guesswork; silent self-tuning would break determinism.*

### 3.12 Executive Reporting

### FR-076 — Monthly leadership summary
- **Classification:** Must, Phase 1 · **Status:** Approved
Generate the monthly summary: overall RAG status; Budget Health (plan, actual, variance, top over-budget accounts/vendors, MoM change, YTD risk); GED Status (expected vs. received, missing, duplicates, delayed, unusual); Invoice Exceptions (Phase 3); Key Risks; Recommended Actions.

### FR-077 — Deterministic RAG status
- **Classification:** Must, Phase 1 · **Status:** Approved
The Green/Yellow/Red status is computed by deterministic, configurable criteria — never assigned by AI.

### FR-078 — Month-over-month comparison view
- **Classification:** Must, Phase 1 · **Status:** Approved
Provide a "what changed since last month" view: spend deltas, new/resolved/recurring findings, status changes.

### FR-079 — Report reproducibility and history
- **Classification:** Must, Phase 1 · **Status:** Approved
Retain every generated report; any historical report can be re-displayed exactly as produced. Regeneration against the same verified inputs and configuration yields identical deterministic content.

### FR-080 — AI narrative sections clearly separated
- **Classification:** Must, Phase 1 · **Status:** Approved
Where AI narrative is included in reports, it is visually and structurally distinct from deterministic content and labeled as AI-generated, including provider/model attribution.

### 3.13 Notifications & Alerts

### FR-081 — Review-cycle status tracking
- **Classification:** Should, Phase 1 · **Status:** Approved
Show the state of the current cycle at all times: files ingested, awaiting verification, analysis complete, report generated — with outstanding items. *Justification: month-end is a checklist process; users need to know "where am I and what's left."*

### FR-082 — Critical findings surfaced on completion
- **Classification:** Should, Phase 1 · **Status:** Approved
When analysis completes, present Critical/High findings prominently before anything else.

### FR-083 — No external notifications in MVP
- **Classification:** Must, Phase 1 · **Status:** Approved
The MVP sends no emails or external messages of any kind (consistent with read-only, no-vendor-communication boundaries). External notification is a future-phase consideration.

### 3.14 Audit Logging

### FR-084 — Ingestion and access audit
- **Classification:** Must, Phase 1 · **Status:** Approved
Log every file ingestion, classification, period assignment, and data access with user identity and timestamp.

### FR-085 — Extraction and verification audit
- **Classification:** Must, Phase 1 · **Status:** Approved
Log extraction runs, quarantines, user corrections (original and corrected values), and verification decisions.

### FR-086 — Rule execution audit
- **Classification:** Must, Phase 1 · **Status:** Approved
Log every analysis run: rule set version, configuration/threshold values in effect, input data fingerprint, rules executed, findings produced.

### FR-087 — AI interaction audit
- **Classification:** Must, Phase 1 · **Status:** Approved
Log every AI interaction: provider, model and version, what data was transmitted, masking applied (if any), the consent reference authorizing it, the prompt category, and the output received.

### FR-088 — Consent audit
- **Classification:** Must, Phase 1 · **Status:** Approved
Log every consent grant, scope, and revocation: who, when, provider, operation type.

### FR-089 — Reporting and export audit
- **Classification:** Must, Phase 1 · **Status:** Approved
Log every report generation and every export (what content left the application, in what format, when, by whom).

### FR-090 — Audit trail review
- **Classification:** Should, Phase 1 · **Status:** Approved
Provide an in-application, searchable, filterable view of the audit trail, and support export of audit records.

### 3.15 AI Insights *(all AI features are optional; the application is fully functional with AI disabled — FR-095)*

### FR-091 — AI narrative explanation of findings
- **Classification:** Should, Phase 1 · **Status:** Approved
Generate plain-language explanations of rule-engine findings ("what happened, why it matters, what to do"), derived exclusively from rule outputs and their evidence.

### FR-092 — AI-generated summary narrative
- **Classification:** Should, Phase 1 · **Status:** Approved
Generate the narrative portions of the monthly summary from deterministic results, in leadership-appropriate language.

### FR-093 — AI recommendations from deterministic outputs
- **Classification:** Should, Phase 1 · **Status:** Approved
- *Scope note (DEC-033): narrowed to investigation-only guidance — Fin may suggest where to look/what evidence to consult, never business/financial-action recommendations; the deterministic "Recommended Actions" in FR-076 are unaffected.*
Generate recommended-action suggestions based solely on findings and their evidence, clearly labeled as AI-generated suggestions for human judgment.

### FR-094 — AI grounding constraint
- **Classification:** Must, Phase 1 · **Status:** Approved
AI-generated content must be grounded in rule-engine outputs and verified data. The AI layer must not introduce financial figures, findings, or conclusions absent from deterministic results. AI responses must decline questions whose answers are not supported by available data.

### FR-095 — AI-off completeness
- **Classification:** Must, Phase 1 · **Status:** Approved
Every number, finding, status, reconciliation result, and report section (except AI narrative) is available with no AI provider configured or consented.

### FR-096 — Consent flow before transmission
- **Classification:** Must, Phase 1 · **Status:** Approved
Before any data transmission to an AI provider: disclose the provider, the specific data to be transmitted, and privacy implications; require explicit consent; log it (FR-088). Consent is revocable in settings; revocation stops future transmissions immediately.

### FR-097 — Provider selection and warnings
- **Classification:** Must, Phase 1 · **Status:** Approved
The user selects the AI provider from configured options. Providers outside the organization-recommended list trigger an explicit warning state before consent can be given.

### FR-098 — Masking/tokenization option
- **Classification:** Should, Phase 1 · **Status:** Approved
Support masking or tokenizing sensitive values (vendor names, resource names, amounts, identifiers) before AI transmission, per configuration; the UI shows whether masking is active. Token-to-real mapping never leaves the application.

### FR-099 — AI answer citation
- **Classification:** Should, Phase 1 · **Status:** Approved
AI-generated answers and narratives cite the finding IDs / data points they are based on, so users can verify any claim in one click. *Justification: cited answers are checkable answers; this is the single strongest defense against silent hallucination eroding trust.*

### 3.16 Search & Q&A

### FR-100 — Natural-language Q&A
- **Classification:** Should, Phase 1 · **Status:** Approved
Answer natural-language questions over the current cycle's verified data and findings (e.g., the five canonical questions: vendors trending over budget; invoices needing attention; what changed; projects at overrun risk; missing GED entries). Answers obey FR-094 grounding and FR-099 citation.

### FR-101 — Question library
- **Classification:** Should, Phase 1 · **Status:** Approved
Offer predefined, one-click questions covering the canonical leadership questions, usable with or without AI (backed by deterministic views where possible).

### FR-102 — Non-AI structured search
- **Classification:** Must, Phase 1 · **Status:** Approved
Provide full browse/search/filter across data and findings (by vendor, account, amount range, period, status) requiring no AI. *Justification: search is a core function that must not depend on an optional, consent-gated feature.*

### 3.17 Configuration

### FR-103 — Configurable analysis parameters
- **Classification:** Must, Phase 1 · **Status:** Approved
All thresholds, tolerances, and rule parameters are configurable without code changes: variance materiality, anomaly sensitivity, duplicate match keys, cutoff dates, reconciliation scope.

### FR-104 — AI provider configuration
- **Classification:** Must, Phase 1 · **Status:** Approved
AI providers are configurable: add/select providers, mark the organization-recommended set (administrator-managed), set masking behavior. Per DEC-006/DEC-007 the recommended list is advisory; consent (FR-096) remains the final gate.

### FR-105 — Reference data management
- **Classification:** Should, Phase 1 · **Status:** Approved
Maintain reference data used by rules: account list and categories, vendor expectations, fiscal calendar, reconciliation-eligible accounts, (Phase 2+) resource and contract references.

### FR-106 — Rule enable/disable as governed change
- **Classification:** Should, Phase 1 · **Status:** Approved
Authorized users may enable/disable individual rules or rule groups. Changes are versioned, logged, and visible in analysis audit records (FR-086). Rule sets cannot vary per-run or be altered by agents.

### FR-107 — Configuration versioning
- **Classification:** Must, Phase 1 · **Status:** Approved
Every configuration change is versioned with user/timestamp/before-after values, and every analysis run records the configuration version used. *Justification: reproducibility (a finding must be explainable by the thresholds in force at the time) — without this, determinism is unverifiable in practice.*

### 3.18 Historical Analysis

### FR-108 — Multi-month retention
- **Classification:** Must, Phase 1 · **Status:** Approved
Retain verified data, findings, reconciliation results, reports, and configurations across months as the basis for trends, baselines, and comparisons.

### FR-109 — Trend views
- **Classification:** Should, Phase 1 · **Status:** Approved
Display spend trends over time by account and vendor, with findings-count and exception-value trends.

### FR-110 — Historical import
- **Classification:** Should, Phase 1 · **Status:** Approved
Support importing prior months' files at onboarding to establish baselines before the first live cycle.

### FR-111 — Cold-start graceful degradation
- **Classification:** Must, Phase 1 · **Status:** Approved
Pattern-based rules declare their minimum history requirement; below it they report "insufficient history" rather than firing unreliable findings, and the report states which rules ran with limited baselines. *Justification: the first months are when FinSight is judged; noisy or silent-but-unexplained behavior at cold start is an adoption killer.*

### 3.19 Forecasting & What-If *(Phase 4; all computation deterministic, AI narrates only)*

### FR-112 — Deterministic forecasting
- **Classification:** Must, Phase 4 · **Status:** Approved
Project year-end / period-end positions from actuals, run rates, and (Phase 2+) resource allocation data, with stated calculation methods.

### FR-113 — Resource departure impact analysis
- **Classification:** Must, Phase 4 · **Status:** Approved
Given a resource's departure date, compute the budget impact: remaining planned cost released, by account and period (data model support exists from Phase 2 — FR-062).

### FR-114 — Backfill scenario estimation
- **Classification:** Should, Phase 4 · **Status:** Approved
Model replacement scenarios (rate, start date, allocation) and compute net budget effect deterministically.

### FR-115 — What-if scenario framework
- **Classification:** Should, Phase 4 · **Status:** Approved
Allow parameterized what-if questions (spend change, vendor change, resource change) computed deterministically, with AI narration of results clearly labeled and scenario results clearly marked as hypothetical — never mixed with actuals.

### 3.20 Export & Reporting Output

### FR-116 — Leadership summary export
- **Classification:** Must, Phase 1 · **Status:** Approved
Export the monthly summary in shareable, print-ready form suitable for distribution to stakeholders who do not use FinSight.

### FR-117 — Data and findings export
- **Classification:** Must, Phase 1 · **Status:** Approved
Export findings, reconciliation results, and summarized data in spreadsheet-compatible form.

### FR-118 — Workbook-compatible export
- **Classification:** Should, Phase 1 · **Status:** Approved
Export reconciliation results in a form compatible with the existing Budget Tracker workbook process, supporting coexistence during the trust-building period.

### FR-119 — Audit export
- **Classification:** Should, Phase 1 · **Status:** Approved
Export audit trail records for external review (see FR-090).

### FR-120 — Export labeling
- **Classification:** Must, Phase 1 · **Status:** Approved
All exports carry: generation timestamp, reporting period, data-as-of information, configuration version, and AI-content labeling identical to the in-app presentation. *Justification: exported documents live forever in email; unlabeled AI content or undated data in circulation is a governance failure waiting to happen.*

---

## 4. Traceability note

Every FR above traces to: the two source specification documents, the GED/Budget Tracker sample analysis, the real invoice sample (DEC-018), team decisions DEC-001–DEC-019, or was a proposed addition (with justification) since accepted into the approved baseline. The Rules Catalog (04) will trace each rule to the FRs it implements; the architecture (05) must satisfy these FRs without weakening any Must.
