# FinSight — Rules Catalog

**Document:** 05-rules-catalog.md
**Status:** Draft for team review and design-review board (spec-driven `design` panel; deterministic-logic focus)
**Date:** 2026-07-15
**Scope:** The authoritative definition of **deterministic financial truth** in FinSight — how rules operate, how evidence is generated, how findings are produced, and how deterministic decisions are made. This document defines **rule structure and business logic**; it is not implementation, code, database, or technical architecture, and it is **not a repository of configuration values**. Where a value is business-controlled, unknown, or pending, this catalog defines the *configurable parameter* the rule depends on — never a hard-coded number — unless the value is explicitly approved in a source document.
**Governing methodology:** Spec-driven development (DEC-010, NFR-073). This is a derived artifact; its source of truth is the approved artifact set below. It introduces no scope beyond approved requirements, epics, features, decisions, or the baselined architecture.
**Sources of truth:** 00-project-understanding.md · 01-functional-requirements.md · 02-non-functional-requirements.md · 03-epics.md (LOCKED, DEC-021) · 04-features.md (LOCKED, DEC-023) · **06-architecture.md (approved architecture baseline)** · 09-decision-log.md
**Companion / downstream documents:** 06-architecture.md (components & ports) · 07-ux-design · 08-ai-and-agents · 10-dev-methodology (09 remains the decision log)
**Provenance:** AI-drafted from the approved artifacts, for human review and design-board sign-off before any status change (sdd:ai-provenance). Rules not requested by a source document are tagged `PROPOSED` with justification; parameter defaults are never asserted where a source leaves them to the business — they are marked pending against the controlling open question. Nothing here is `Baselined` until the team approves it.

---

## 1. Purpose

The Rules Catalog is where FinSight's central promise becomes concrete: **financial truth is deterministic** (00 §1; DEC-005; AP-01). Every finding, variance, severity, status, reconciliation outcome, and readiness verdict the product ever shows a user is produced by a rule defined here — repeatably, auditably, and identically for the same verified inputs and configuration version (NFR-021). This document exists to:

1. **Define the business logic of every deterministic rule** — what it detects, on what evidence, with what exclusions — at a fidelity a Finance Governance Lead and an Auditor can validate against real-world accounting behavior, and a Rules Engine Designer can implement without inventing business meaning.
2. **Separate durable rule logic from volatile values.** The logic ("flag a GED amount that deviates materially from its trailing baseline") is stable; the value ("materially = X%") is business-owned and will change. This catalog fixes the former and *parameterizes* the latter (§4), so tuning a threshold is a governed configuration change (FR-107), never a code or spec change.
3. **Make every rule traceable** — to the requirement(s) it implements, the feature(s) that ship it, the architecture component(s) that run it, and the open question(s) that gate its parameters — in both directions (§20).
4. **Give the Rules Engine (C-07/E-02) its contract set** — each rule declares inputs, parameters, evidence, findings, severity method, and minimum-history need (F-02-01), so a new rule is an addition, never a redesign (NFR-044).

### 1.1 What this document is NOT

- **Not implementation or code.** No algorithms-as-code, data structures, or pseudo-code beyond the minimum needed to state business logic unambiguously.
- **Not database or technical architecture.** Storage, ports, layering, and technology live in 06-architecture.md and its ADRs.
- **Not a configuration-values repository.** It names parameters and their meaning; the *values* are held in the governed Configuration & Reference Data store (C-18) and versioned there (FR-107, NFR-022). Where a source document *has* approved a value or an enumeration, it is stated as approved; nowhere else is a number invented.
- **Not UX.** How a finding is displayed is 07-ux-design; this catalog defines what the finding *is*.

### 1.2 Design bias (explicit)

Per the directive and DEC-019: **favor configurable rule design over fixed rule design.** When in doubt whether something is logic or a value, it is treated as a parameter. Thresholds, tolerances, severity bands, dollar/percentage limits, anomaly sensitivities, cutoff calendars, materiality values, and match tolerances are **always** parameters (§4), each tied to its controlling open question and owner. This maximizes future flexibility and minimizes rework when finance supplies real values (OQ-5/7/8) or samples arrive (OQ-2).

---

## 2. Conventions

### 2.1 ID grammar (namespaces distinct from FR/NFR/E/F/DEC/ADR and from the architecture's AP/ASR/C/… IDs)

| Prefix | Meaning |
|---|---|
| `R-<FAM>-##` | A rule. `<FAM>` ∈ {BUD, GED, REC, FND, RPT, HST, RDY, INV, RES, FOR}. IDs are permanent; retired rules are marked superseded, never renumbered or reused. |
| `CP-<slug>` | A configurable parameter defined in the Parameter Register (§4) and referenced by rules. |
| `EV-<FAM>-##` | An evidence type a rule produces (defined inline per rule; the register in §19 lists them). |

### 2.2 Status & lifecycle tags (mirroring the requirements documents)

- **Approved** — traces to an approved FR/feature and is buildable now (subject only to its parameters).
- **`ASSUMPTION (A-##)`** — rests on an entry in the project Assumptions Register (01 §2) or a rules-specific assumption (§17).
- **`OPEN QUESTION (OQ-#)`** — a parameter or baseline is blocked on a decision-log open question; the *rule logic* stands, the *value* is pending.
- **`PENDING VALIDATION`** — cannot be finalized until stakeholders provide documents/data (e.g., invoice/PO/SOW/rate-card samples — OQ-2).
- **`PROPOSED`** — not requested by a source document; added with justification for team accept/reject.
- **Future / Deferred** — belongs to a later release/phase (E-11 Phase 2, E-12 Phase 3, E-13 Phase 4); specified at provisional fidelity and re-verified before build.
- **Release tag** — `R1` / `R2` per DEC-022/DEC-023, matching the owning feature.

### 2.3 Per-rule template (every rule uses these 18 fields)

Rule ID · Rule Name · **Purpose** · **Business Context** · **Related Requirements** · **Related Features** · **Related Architecture Components** · **Inputs** · **Preconditions** · **Configurable Parameters** · **Rule Logic** · **Exceptions and Exclusions** · **Evidence Produced** · **Findings Produced** · **Severity Determination Method** · **Minimum History Requirements** · **Outputs** · **Related Open Questions** · **Notes**.

### 2.4 Approved enumerations (the only fixed vocabularies — from source documents, not invented here)

| Vocabulary | Approved values | Source |
|---|---|---|
| Severity | **Critical / High / Medium / Low** | FR-070 |
| Report RAG status | **Green / Yellow / Red** | FR-077 |
| Reconciliation match tier | **Exact / Probable / Unmatched** | FR-045 |
| Invoice status recommendation | **Ready for approval / Needs clarification / Hold for review / Recommend rejection / Partial approval candidate** | FR-059 |
| Finding lifecycle state | **New → Acknowledged → In review → Resolved / Dismissed** | FR-072 |
| Analysis dimensions (MVP) | **Department / GL account / Vendor** | DEC-002; invoice-level **Project** added Phase 3 (FR-122) |
| Budget granularity | **Monthly** | DEC-017 (A-04 resolved) |

These are enumerations, not thresholds; the *boundaries between them* (e.g., which variance is Critical vs. High) are configurable (§4, §5).

### 2.5 Binding acceptance criterion (from 04-features §2.1 — the rule-pack pattern)

Every detection rule ships with **golden-dataset validation**: a seeded synthetic month produces exactly the expected findings, with correct severities and evidence traceable to source lines (NFR-036). Determinism and provider-swap regressions (NFR-037) apply to every rule. Golden datasets use sanitized/synthetic data only (NFR-018, NFR-038). This criterion is stated once here and is implied by every "Approved" rule below.

---

## 3. Cross-Cutting Deterministic Design Principles

These principles constrain every rule and every family. They are the catalog-level expression of the architecture's principles (06 §3).

1. **Deterministic by construction (AP-01, NFR-021).** A rule reads only verified data and versioned configuration; it uses exact decimal arithmetic (NFR-059), no wall-clock, no locale-dependent parsing/sorting, and explicit ordering — so identical inputs+config yield byte-identical findings across platforms and AI providers.
2. **AI is absent from this catalog (AP-02, DEC-005).** No rule invokes, consults, or is influenced by AI. AI may later *explain* a rule's finding (FR-091); it can never produce, alter, or suppress one. Rules emit findings only through the deterministic `FindingsCommandPort` (06 §7.1), which the AI layer cannot reach — this is what makes "Trust > AI" structural, not aspirational.
3. **Evidence or it did not happen (AP-06, FR-071, NFR-067).** Every finding carries its rule reference, the exact input values used, and lineage to the source rows/cells. A rule that cannot show its evidence cannot raise a finding.
4. **Configuration over fixed values (AP-07, DEC-019).** Thresholds/tolerances/bands/cutoffs are parameters (§4), versioned (FR-107) and recorded against each run (NFR-022). A finding is always explainable by the parameter values in force when it was produced (F-08-03).
5. **Change ≠ exception (AP-12, FR-041, §16.2 of 06).** Rules distinguish *what is new* (surfaced for attention) from *what is wrong* (a finding). Routine accounting events (payroll, reclass, accrual reversals) are recognized and given correct treatment so they do not become false findings (FR-041).
6. **Honest at cold start (AP-11, FR-111).** Every rule declares its minimum-history need; below it, the rule reports "insufficient history" rather than firing unreliable findings, and the report discloses which rules ran with limited baselines.
7. **Idempotent and replayable (NFR-008, F-02-06).** Re-running a rule on the same verified inputs and configuration version produces the same findings with no duplication; any historical cycle can be replayed exactly.
8. **Rules are additive (NFR-044, XP-01).** A new rule declares its own inputs/parameters/outputs/min-history and is registered without modifying unrelated rules — the extension seam, not a redesign.

---

## 4. Configurable Parameter Register

The single list of business-owned values the rules depend on. **No value is asserted here** unless a source document approved it; every pending value names its controlling open question and validation owner. Values live in C-18 (governed, versioned); this register defines their *meaning and dependency*, satisfying the directive to identify each configurable parameter with its related open question, requirement(s), feature(s), and how the rule depends on it.

| Param ID | Name / what it controls | Value status | Controlling OQ / owner | Used by (rules) | How the rule depends on it |
|---|---|---|---|---|---|
| **CP-FISCAL-CALENDAR** | Fiscal calendar: period definitions, month boundaries, YTD span | Pending finance definition | OQ-7 (cutoff) · finance | R-BUD-01, R-GED-*, R-REC-*, R-RPT-*, R-HST-* | Defines "the reporting month" and "YTD"; every period-scoped rule reads it |
| **CP-ACCOUNT-LIST** | Master GL account list, names, and categories (~31 accounts observed) | Pending finance reference | finance | R-RDY-01/02, R-GED-05, R-BUD-*, R-REC-01 | Validates account numbers; groups spend; defines expected account/dept combinations |
| **CP-VENDOR-EXPECTATIONS** | Expected vendor↔account/department associations | Pending finance reference | OQ-5-adjacent · finance | R-GED-05 | Defines which vendor-on-account combinations are "expected" vs. flagged |
| **CP-VAR-MATERIALITY** | Variance materiality thresholds (% and/or $) per account/vendor | **Pending — no default** | **OQ-8** · finance | R-BUD-02, R-RPT-01 | Sets the boundary at which a variance becomes a finding |
| **CP-VAR-SEVERITY-BANDS** | Severity bands for over/under-budget findings | **Pending — no default** | **OQ-8** · finance | R-BUD-02 (via R-FND-02) | Maps variance magnitude → Critical/High/Medium/Low |
| **CP-MOM-THRESHOLD** | Month-over-month change threshold (% and/or $) per account/vendor | Pending | OQ-8-adjacent · finance | R-BUD-03 | Sets the boundary at which a MoM swing is flagged |
| **CP-TREND-N** | Number of consecutive months defining a sustained adverse trend | Pending | finance | R-BUD-06 | Defines "sustained"; also sets this rule's minimum history |
| **CP-RUNRATE-METHOD** | Run-rate projection method (e.g., YTD-average × remaining periods) | **Pending — method needs finance agreement** | finance (F-03-04 note) | R-BUD-05, R-FOR-01 | Defines the deterministic projection formula; without agreement the rule stays R2/unshipped |
| **CP-DUP-KEYS** | Duplicate GED match key fields (e.g., account, vendor, amount, period) | Pending | finance | R-GED-02 | Defines what "candidate duplicate" means |
| **CP-DUP-WINDOW** | Time window over which duplicates are considered | Pending | finance | R-GED-02 | Bounds duplicate search (e.g., within/around a period) |
| **CP-CUTOFF-CALENDAR** | Official monthly posting cutoff dates | **Pending — no default** | **OQ-7** · finance | R-GED-04 | Defines "delayed" (posted after cutoff) |
| **CP-ANOMALY-BASELINE** | Trailing window for amount-anomaly baseline (e.g., N-month average) | Pending | OQ-5-adjacent · finance | R-GED-06, R-HST-01 | Defines the expected-amount baseline; sets minimum history |
| **CP-ANOMALY-SENSITIVITY** | Deviation threshold from baseline that constitutes an anomaly | **Pending — no default** | finance | R-GED-06 | Sets the boundary at which an amount is "materially" off pattern |
| **CP-EXPECTED-ENTRIES-SOURCE** | Missing-entry baseline mode: history-derived vs. finance-maintained expected list | **Pending — determines rule variant** | **OQ-5** · finance | R-GED-03 | Selects which detection variant runs; gates R1 vs. R2 shipping |
| **CP-EXPECTED-ENTRIES-REF** | The finance-maintained expected-entries reference data (if OQ-5 = reference mode) | Pending | OQ-5 · finance | R-GED-03 | Supplies the expected set to compare the month against |
| **CP-CODING-EXPECTATIONS** | Expected account↔department and vendor↔account combinations | Pending | finance | R-GED-05 | Defines "unexpected coding" |
| **CP-EVENT-MARKERS** | Observable markers classifying journal-line event type (payroll interface, "RECLAS", accrual/reversal) | Partially observed in sample; pending finance confirmation | finance (FR-041) | R-GED-07 (and consumed by R-GED-02/06) | Defines which lines are exempt from duplicate/anomaly treatment |
| **CP-MATCH-KEYS** | Reconciliation match key fields (GED line ↔ tracker entry) | Pending | finance | R-REC-02 | Defines how a match candidate is identified |
| **CP-MATCH-TOLERANCE** | Amount/date tolerances distinguishing exact vs. probable matches | **Pending — no default** | finance | R-REC-02 | Sets exact/probable/unmatched tier boundaries |
| **CP-CLRD-SEMANTICS** | Meaning of the cleared/`clrd` status and its transitions | Pending finance definition | A-10 · finance | R-REC-03 | Defines when an item counts as cleared |
| **CP-RECON-ELIGIBLE-ACCOUNTS** | Account ranges eligible for reconciliation (excludes payroll/benefits/non-invoiced) | **Pending finance validation** | finance (FR-050) | R-REC-01 | Scopes which GED lines are reconciled at all |
| **CP-CARRYFWD-AGING-BANDS** | Aging buckets for carried-forward unreconciled items (e.g., 30/60/90) | Pending | finance | R-REC-05 | Defines aging categories for reporting |
| **CP-SEVERITY-CRITERIA** | Per-rule severity criteria mapping evidence → Critical/High/Medium/Low | **Pending — no defaults** | **OQ-8** · finance | R-FND-02 (referenced by all detection rules) | The canonical severity method's inputs |
| **CP-RAG-CRITERIA** | Deterministic criteria mapping the month's findings/variances → Green/Yellow/Red | **Pending — no default** | OQ-8-adjacent · finance | R-RPT-01 | Sets the overall status thresholds |
| **CP-MINHISTORY** | Per-rule minimum-history months required before a history-based rule fires | Rule-declared; values pending | finance | R-GED-06, R-BUD-03/06, R-HST-*, R-FND-04 | Below this, the rule reports "insufficient history" (FR-111) |
| **CP-RECURRENCE-KEY** | Identity key linking the "same" finding across months (rule + entities) | Pending | finance | R-FND-04, R-HST-03 | Defines what counts as a recurrence |
| **CP-READINESS-REQUIREMENTS** | Per-capability prerequisites: required document types, reference data, verification state | Derived from FRs; pending confirmation | AA-07 · team | R-RDY-07 | Determines Available/Partial/Unavailable per capability |
| **CP-QUALITY-CAVEAT-THRESHOLD** | Quarantine ratio above which a capability is "Partially available" | Pending | team | R-RDY-04/05/07 | Sets when data-quality degrades a capability's readiness |
| **CP-RATE-TOLERANCE** | Billed-rate tolerance vs. rate card (labor lines) | **Pending — sample-gated** | **OQ-2** · finance | R-INV-04 | Sets acceptable rate deviation |
| **CP-HOURS-TOLERANCE** | Billed-hours tolerance vs. estimate/timesheet | **Pending — sample-gated** | **OQ-2** · finance | R-INV-05 | Sets acceptable hours deviation |
| **CP-INV-STATUS-CRITERIA** | Mapping from invoice line-findings → one of the five statuses | Pending — sample-gated | OQ-2 · finance | R-INV-10 | Determines the single status recommendation |
| **CP-RESOURCE-COST-METHOD** | Resource cost formula (rate × allocation × period) conventions | Pending — Phase 2 | DEC-012 · finance | R-RES-01 | Defines deterministic cost computation |

> **Parameter governance:** every parameter is versioned with before/after values and user/timestamp (FR-107), owned by C-08 (definition/read model) and C-18 (persistence/versioning/validation), and recorded against every analysis run (NFR-022). Changing a value never changes rule *logic* and never requires a spec or code change (AP-07). False-positive feedback (R-FND-05) builds the human evidence base for tuning these values; it never auto-tunes them (NFR-021 integrity).

---

## 5. Severity & Materiality Model (shared method)

Severity is computed by **one canonical rule, R-FND-02**, invoked by every detection rule — the architectural split of FR-070 into *computation* (F-02-04, core) and *presentation* (F-06-01, C-09b). No detection rule embeds its own severity numbers; each contributes its evidence and its severity parameters, and R-FND-02 maps them to the approved enumeration **Critical / High / Medium / Low** (§2.4).

- **Inputs to severity:** the finding's evidence values (e.g., variance magnitude, deviation from baseline, age, count), plus the rule's severity parameters (`CP-SEVERITY-CRITERIA`, and rule-specific bands such as `CP-VAR-SEVERITY-BANDS`).
- **Materiality is a parameter, not a constant.** Whether a variance/anomaly is "material" is set by finance per account/vendor (OQ-8). Until finance supplies values, severity criteria are **pending — no default**; the rule logic is complete, the boundaries are not.
- **Determinism:** given the same evidence and the same severity-parameter version, severity is identical (NFR-021). Severity carries non-color encoding so meaning survives without color (NFR-025, ASR-14).
- **AI exclusion:** severity is never assigned, adjusted, or suggested by AI (DEC-005, NFR-047).

Each rule's "Severity Determination Method" field below reads, in effect: *"via R-FND-02 using [named parameters]."*

---

## 6. Family 1 — Budget Review Rules (R-BUD)

**Family purpose.** Turn the month's verified budget and actuals into plan-vs-actual position, variances, their drivers, and projected risk — by department, GL account, and vendor, for the reporting month and YTD (E-03, FR-030–036). Output is interpretation-ready evidence, not just numbers.

**Trust > AI.** All variance math, flagging, and projection are deterministic and reproducible; AI may later narrate "why it matters," never compute the variance or decide it is a problem (DEC-005, DEC-022 value driver "exception detection").

**Monthly Review in a Box.** This family answers the Leader's first question — *"are we over or under budget, and where?"* — inside FinSight without opening a spreadsheet (E-03 success signal), a core slice of Release 1.

**Architecture fit.** Rule packs in C-11 executing on the deterministic engine C-07; findings emitted via C-09a's `FindingsCommandPort`; parameters from C-08/C-18; period semantics from `CP-FISCAL-CALENDAR`; consumes only `VerifiedDataset` inputs (06 §11).

---

**R-BUD-01 — Planned-vs-Actual Variance Computation** *(Approved · R1 · Must)*
- **Purpose:** Compute variance (amount and %) between planned budget and actual spend for the reporting month and YTD.
- **Business context:** The foundation of budget review; every downstream budget finding cites its variance evidence. Budget granularity is monthly (DEC-017).
- **Related requirements:** FR-030, FR-031 (uses bgt/atd/etc/eac/delta where present).
- **Related features:** F-03-01, F-03-02.
- **Related architecture components:** C-11 (budget pack), C-07, C-09a, C-08.
- **Inputs:** verified budget figures per account (budget, actuals-to-date, estimate-to-complete, estimate-at-completion, delta); verified GED actuals aggregated by dimension.
- **Preconditions:** verified budget + GED datasets for the cycle (`VerifiedDataset`); fiscal calendar available.
- **Configurable parameters:** `CP-FISCAL-CALENDAR`, `CP-ACCOUNT-LIST`.
- **Rule logic:** for each (department, account, vendor) dimension and for month and YTD, variance_amount = actual − planned; variance_pct = variance_amount ÷ planned (exact decimal; percentage undefined/flagged when planned = 0). Prefer workbook-provided figures where present (FR-031); otherwise derive from aggregated actuals.
- **Exceptions and exclusions:** dimensions with no plan and no actual are omitted; planned = 0 with actual > 0 yields an explicit "unbudgeted spend" evidence marker rather than a divide-by-zero.
- **Evidence produced:** `EV-BUD-VARIANCE` (planned, actual, variance amount, variance %, dimension, period scope, source lineage).
- **Findings produced:** none directly — this is the computation feeding R-BUD-02/03/05/06 and R-RPT-*.
- **Severity determination method:** n/a (pure computation).
- **Minimum history requirements:** 0 for month; YTD requires the current fiscal year's prior months present (reports partial-YTD honestly if not).
- **Outputs:** variance evidence records keyed to the cycle and dimensions.
- **Related open questions:** —.
- **Notes:** "unbudgeted spend" (planned = 0, actual > 0) is a legitimate governance signal; it becomes a finding via R-BUD-02 only if configured material.

**R-BUD-02 — Over/Under-Budget Flagging & Severity** *(Approved · R1 · Must)*
- **Purpose:** Flag over-budget and materially under-budget positions and classify their severity.
- **Business context:** "Materially under" matters as much as "over" — unspent budget signals mis-forecast or stalled work.
- **Related requirements:** FR-033, FR-070 (severity).
- **Related features:** F-03-03 (rule pack), F-06-01 (presentation).
- **Related architecture components:** C-11, C-07, C-09a, R-FND-02.
- **Inputs:** `EV-BUD-VARIANCE` from R-BUD-01.
- **Preconditions:** R-BUD-01 evidence present.
- **Configurable parameters:** `CP-VAR-MATERIALITY` (flag boundary), `CP-VAR-SEVERITY-BANDS` (severity bands) — **both pending OQ-8**.
- **Rule logic:** compare each variance against its materiality parameter (per account/vendor); if |variance| ≥ materiality, raise a finding; classify severity via R-FND-02 using the severity bands.
- **Exceptions and exclusions:** dimensions marked out of scope by configuration; positions explained by known timing (informational, not a finding) where such reference exists.
- **Evidence produced:** references `EV-BUD-VARIANCE`; adds the materiality parameter version and comparison result.
- **Findings produced:** `Budget over-spend` / `Budget under-spend` finding per breaching dimension.
- **Severity determination method:** via R-FND-02 using `CP-VAR-SEVERITY-BANDS`, `CP-SEVERITY-CRITERIA`.
- **Minimum history requirements:** 0 (single-month judgment).
- **Outputs:** budget findings into the Findings Hub.
- **Related open questions:** **OQ-8** (materiality/severity values).
- **Notes:** logic is complete and buildable now; only the boundaries await finance. Golden-dataset tests use synthetic materiality values.

**R-BUD-03 — Month-over-Month Change Detection** *(Approved · R1 · Must)*
- **Purpose:** Detect unusual month-over-month spend increases/decreases per account and vendor.
- **Business context:** Sudden swings surface issues a static plan-vs-actual view misses.
- **Related requirements:** FR-032. `ASSUMPTION (A-07)`.
- **Related features:** F-03-03.
- **Related architecture components:** C-11, C-07, C-09a, C-13 (prior-month actuals), R-FND-02.
- **Inputs:** current-month actuals by dimension; immediately prior month's verified actuals (from C-13).
- **Preconditions:** at least one prior verified month retained.
- **Configurable parameters:** `CP-MOM-THRESHOLD`, `CP-MINHISTORY` (=1 prior month).
- **Rule logic:** delta = current − prior (amount and %); flag where |delta| ≥ threshold.
- **Exceptions and exclusions:** event-tagged lines (R-GED-07) that legitimately cause swings (e.g., accrual reversals) are treated per their event type; first month of operation → "insufficient history."
- **Evidence produced:** `EV-BUD-MOM` (current, prior, delta amount/%, dimension).
- **Findings produced:** `Unusual month-over-month change` finding.
- **Severity determination method:** via R-FND-02 using `CP-SEVERITY-CRITERIA`.
- **Minimum history requirements:** 1 prior month (else "insufficient history," FR-111).
- **Outputs:** MoM findings; MoM evidence reused by R-RPT-03/R-HST-02.
- **Related open questions:** OQ-8-adjacent (threshold).
- **Notes:** shares delta computation with R-HST-02 (single source of MoM truth).

**R-BUD-04 — Variance Contributor Ranking** *(Approved · R1 · Should)*
- **Purpose:** Rank the top contributors (accounts, vendors) to overall variance so attention goes where it matters.
- **Business context:** Directs the scarcest resource — leadership attention (NFR-066).
- **Related requirements:** FR-035.
- **Related features:** F-03-02.
- **Related architecture components:** C-11, C-07, C-09b (drives drill-through), C-13.
- **Inputs:** `EV-BUD-VARIANCE` across all dimensions.
- **Preconditions:** R-BUD-01 evidence present.
- **Configurable parameters:** `CP-FISCAL-CALENDAR`; (ranking depth is a display concern, not a rule value).
- **Rule logic:** order dimensions by contribution to total variance (absolute and signed); produce a deterministic, tie-broken ranking (explicit tie-break on dimension identity to keep ordering stable — NFR-021).
- **Exceptions and exclusions:** out-of-scope dimensions excluded.
- **Evidence produced:** `EV-BUD-RANK` (ordered contributions with amounts/percent-of-total).
- **Findings produced:** none (analytical evidence; not an exception).
- **Severity determination method:** n/a.
- **Minimum history requirements:** 0.
- **Outputs:** ranked contributor evidence for F-03-02 and the summary.
- **Related open questions:** —.
- **Notes:** ranking is not a finding — it is navigation. Keeps the "change ≠ exception" line (Principle 5).

**R-BUD-05 — Run-Rate Projection & Overrun Flag** *(Approved · R2 · Should)*
- **Purpose:** Project period-end position from YTD actuals and flag accounts/vendors trending toward overrun.
- **Business context:** Demoted to R2 (F-03-04, DEC-023) — the monthly review completes without it, and the projection *method* needs finance agreement.
- **Related requirements:** FR-034.
- **Related features:** F-03-04.
- **Related architecture components:** C-11, C-07, C-13, R-FND-02.
- **Inputs:** YTD actuals; plan; fiscal calendar (remaining periods).
- **Preconditions:** sufficient YTD history per `CP-MINHISTORY`.
- **Configurable parameters:** `CP-RUNRATE-METHOD` (**pending finance agreement**), `CP-MINHISTORY`, `CP-VAR-MATERIALITY` (overrun boundary).
- **Rule logic:** project year-end position using the agreed deterministic method; flag where projected position breaches materiality. All projection math is deterministic; AI may only narrate it (FR-034).
- **Exceptions and exclusions:** accounts with insufficient YTD → "insufficient history."
- **Evidence produced:** `EV-BUD-RUNRATE` (method, inputs, projected position, gap to plan).
- **Findings produced:** `Projected overrun risk` finding.
- **Severity determination method:** via R-FND-02.
- **Minimum history requirements:** per `CP-MINHISTORY` (method-dependent).
- **Outputs:** projection evidence and overrun findings.
- **Related open questions:** OQ-8 (materiality); method agreement (finance).
- **Notes:** does not ship until `CP-RUNRATE-METHOD` is agreed — an honest gate, not a guess.

**R-BUD-06 — Multi-Month Trend Risk** *(Approved · R2 · Should)*
- **Purpose:** Detect sustained adverse trends (e.g., N consecutive months of growth) per account/vendor.
- **Business context:** History-dependent; "third month rising" is different information than one bad month.
- **Related requirements:** FR-036, FR-109 (budget portion). `ASSUMPTION (A-07)`.
- **Related features:** F-03-05.
- **Related architecture components:** C-11, C-07, C-13, R-HST-01 (baselines), R-FND-02.
- **Inputs:** trailing monthly actuals by dimension (from C-13).
- **Preconditions:** ≥ `CP-TREND-N` months of verified history.
- **Configurable parameters:** `CP-TREND-N`, `CP-MINHISTORY`, `CP-SEVERITY-CRITERIA`.
- **Rule logic:** detect monotonic/adverse movement over `CP-TREND-N` consecutive months per configured trend definition; flag qualifying dimensions.
- **Exceptions and exclusions:** trends explained by event-tagged one-offs; below-minimum history → "insufficient history."
- **Evidence produced:** `EV-BUD-TREND` (series, direction, span).
- **Findings produced:** `Sustained adverse trend` finding.
- **Severity determination method:** via R-FND-02.
- **Minimum history requirements:** `CP-TREND-N` months.
- **Outputs:** trend findings and evidence.
- **Related open questions:** OQ-8-adjacent.
- **Notes:** degrades gracefully at cold start (E-03 note).

---

## 7. Family 2 — GED Analysis Rules (R-GED)

**Family purpose.** Surface missing, duplicate, delayed, unusually sized, and miscoded GED (General Expense Detail, DEC-001) entries each month, and summarize GED activity — with routine accounting events recognized so they are not false alarms (E-04, FR-037–043).

**Trust > AI.** Every exception is a deterministic rule outcome with evidence to the journal line; AI never decides an entry is missing/duplicate/anomalous. Exception detection is the second-named value driver (DEC-022).

**Monthly Review in a Box.** Replaces the manual, chance-based catching of GED problems with systematic detection each month (E-04 success signal), a Release-1 core.

**Architecture fit.** C-11 GED rule pack on C-07; consumes verified GED data and the accounting-event tags produced at extraction (F-01-06, FR-041); findings via C-09a; history-based members draw baselines from C-13.

---

**R-GED-01 — GED Activity Summarization** *(Approved · R1 · Must)*
- **Purpose:** Summarize GED spend by department, account, vendor, and fiscal period with counts, totals, and prior-period comparison.
- **Business context:** Answers "where did the money go?"; the substrate other GED rules and the summary read.
- **Related requirements:** FR-043, FR-109 (GED portion).
- **Related features:** F-04-01.
- **Related architecture components:** C-11, C-07, C-13 (prior periods), C-09b (drill-through).
- **Inputs:** verified GED lines with normalized amounts and event tags.
- **Preconditions:** verified GED dataset.
- **Configurable parameters:** `CP-FISCAL-CALENDAR`, `CP-ACCOUNT-LIST`.
- **Rule logic:** aggregate amounts and counts by each dimension and period; compute prior-period comparisons via C-13.
- **Exceptions and exclusions:** subtotal/structural rows excluded from data (handled at extraction, FR-013) but retained for the self-check (R-RDY-03).
- **Evidence produced:** `EV-GED-SUMMARY` (grouped totals/counts, comparisons, lineage).
- **Findings produced:** none (analytical).
- **Severity determination method:** n/a.
- **Minimum history requirements:** 0 (prior-period comparison shown only where history exists).
- **Outputs:** summarization evidence for F-04-01 and R-RPT-02.
- **Related open questions:** —.
- **Notes:** boundary — this answers "where money went," not "on plan?" (R-BUD-01) nor "find this" (R-FND search).

**R-GED-02 — Duplicate Entry Detection** *(Approved · R1 · Must)*
- **Purpose:** Detect candidate duplicate GED entries.
- **Business context:** Duplicate postings are a classic overpayment/mis-statement risk; must not falsely flag legitimate repeats.
- **Related requirements:** FR-038, FR-041 (consumption).
- **Related features:** F-04-02.
- **Related architecture components:** C-11, C-07, C-09a, R-GED-07 (event guard), R-FND-02.
- **Inputs:** verified GED lines with event tags.
- **Preconditions:** verified GED dataset.
- **Configurable parameters:** `CP-DUP-KEYS`, `CP-DUP-WINDOW`, `CP-EVENT-MARKERS` (via R-GED-07).
- **Rule logic:** group lines by the configured key fields within the configured window; where >1 line shares the key, mark candidates as potential duplicates.
- **Exceptions and exclusions:** lines classified by R-GED-07 as reclass ("RECLAS"), accrual, accrual-reversal, or payroll-interface events are excluded from duplicate treatment per event type (FR-041) — the single most important false-positive guard.
- **Evidence produced:** `EV-GED-DUP` (matched key, member line references, amounts, event tags).
- **Findings produced:** `Candidate duplicate GED entry` finding.
- **Severity determination method:** via R-FND-02.
- **Minimum history requirements:** 0 (within-cycle detection).
- **Outputs:** duplicate findings.
- **Related open questions:** —.
- **Notes:** true-duplicate vs. legitimate repeat distinction is the whole point (FR-041); the guard is not optional.

**R-GED-03 — Missing Entry Detection** *(Approved · R1 or R2 by OQ-5 · Must)*
- **Purpose:** Detect expected-but-absent GED entries for the reporting month.
- **Business context:** A canonical leadership question ("are entries missing?"). The baseline source is undecided (OQ-5): a finance-maintained expected list, or a history-derived pattern.
- **Related requirements:** FR-037. `OPEN QUESTION (OQ-5)` `ASSUMPTION (A-07)`.
- **Related features:** F-04-02 (reference-based, R1 where OQ-5 permits) · F-04-03 (history-based, R2).
- **Related architecture components:** C-11, C-07, C-09a, C-08 (`CP-EXPECTED-ENTRIES-REF`), C-13 (history mode), R-FND-02.
- **Inputs:** verified GED lines; **either** the finance-maintained expected-entries reference **or** trailing-history-derived expectations.
- **Preconditions:** an expected baseline exists in the configured mode.
- **Configurable parameters:** `CP-EXPECTED-ENTRIES-SOURCE` (**mode selector — OQ-5**), `CP-EXPECTED-ENTRIES-REF`, `CP-ANOMALY-BASELINE` (history mode), `CP-MINHISTORY` (history mode).
- **Rule logic:** compare the month's present entries against the expected set for the mode; any expected entry with no matching activity is flagged missing. In reference mode this ships in R1; in history mode it is R2 (needs baselines).
- **Exceptions and exclusions:** entries legitimately absent per calendar/timing where such reference exists; below-minimum history (history mode) → "insufficient history."
- **Evidence produced:** `EV-GED-MISSING` (expected item, expected-source, absence confirmation).
- **Findings produced:** `Missing GED entry` finding.
- **Severity determination method:** via R-FND-02.
- **Minimum history requirements:** 0 (reference mode); per `CP-MINHISTORY` (history mode).
- **Outputs:** missing-entry findings.
- **Related open questions:** **OQ-5** (baseline source — determines R1 vs. R2 shipping and which variant runs).
- **Notes:** the rule's *logic* is defined under both modes now; OQ-5 selects the variant. This is the design that keeps the question from blocking (DEC-019).

**R-GED-04 — Delayed Posting Detection** *(Approved · R1 · Should)*
- **Purpose:** Flag entries posted after the expected monthly cutoff.
- **Business context:** Late postings distort month-end completeness and reconciliation.
- **Related requirements:** FR-039. `OPEN QUESTION (OQ-7)`.
- **Related features:** F-04-02.
- **Related architecture components:** C-11, C-07, C-09a, C-08 (`CP-CUTOFF-CALENDAR`), R-FND-02.
- **Inputs:** verified GED lines with journal/posting and invoice dates; fiscal calendar; cutoff calendar.
- **Preconditions:** cutoff calendar configured (interim configurable until OQ-7).
- **Configurable parameters:** `CP-CUTOFF-CALENDAR` (**OQ-7**), `CP-FISCAL-CALENDAR`.
- **Rule logic:** compare posting date against the period's cutoff; flag lines posted after cutoff for the period they belong to.
- **Exceptions and exclusions:** entries whose late posting is expected by policy (e.g., specific accrual timing) where configured.
- **Evidence produced:** `EV-GED-DELAY` (posting date, cutoff, days late, period).
- **Findings produced:** `Delayed GED posting` finding.
- **Severity determination method:** via R-FND-02 (age/days-late as an input).
- **Minimum history requirements:** 0.
- **Outputs:** delayed-posting findings.
- **Related open questions:** **OQ-7** (official cutoff calendar).
- **Notes:** service-period-to-invoice-date lag observed (~6 weeks, DEC-018) means "late posting" and "timing difference" differ — the latter is a reconciliation carry-forward (R-REC-05), not necessarily a finding.

**R-GED-05 — Coding & Vendor-Expectation Checks** *(Approved · R1 · Should)*
- **Purpose:** Flag entries under unexpected account/department combinations, or from vendors not previously associated with an account.
- **Business context:** Miscoding and unexpected vendors are common governance issues.
- **Related requirements:** FR-042.
- **Related features:** F-04-02.
- **Related architecture components:** C-11, C-07, C-09a, C-08 (`CP-CODING-EXPECTATIONS`, `CP-VENDOR-EXPECTATIONS`), R-FND-02.
- **Inputs:** verified GED lines; configured expectation reference data.
- **Preconditions:** expectation reference configured.
- **Configurable parameters:** `CP-CODING-EXPECTATIONS`, `CP-VENDOR-EXPECTATIONS`, `CP-ACCOUNT-LIST`.
- **Rule logic:** for each line, check account↔department and vendor↔account against configured expectations; flag lines outside expected combinations.
- **Exceptions and exclusions:** newly onboarded vendors/accounts flagged as *new* (change, via R-HST-04) rather than *wrong* where configuration marks them provisional — new ≠ wrong (Principle 5).
- **Evidence produced:** `EV-GED-CODING` (combination observed vs. expected).
- **Findings produced:** `Unexpected coding` / `Unexpected vendor-on-account` finding.
- **Severity determination method:** via R-FND-02.
- **Minimum history requirements:** 0 (reference-based).
- **Outputs:** coding/vendor findings.
- **Related open questions:** —.
- **Notes:** without reference data this rule reports "capability unavailable — no coding expectations configured" (R-RDY-07), not silence.

**R-GED-06 — Amount Anomaly Detection** *(Approved · R2 · Must)*
- **Purpose:** Flag GED amounts materially above/below the historical pattern for an account/vendor combination.
- **Business context:** History-derived; deliberately "boring and honest" (F-04-03) — deterministic statistics, not AI pattern-guessing.
- **Related requirements:** FR-040, FR-037 (history-based portion). `ASSUMPTION (A-07)`.
- **Related features:** F-04-03.
- **Related architecture components:** C-11, C-07, C-13/R-HST-01 (baselines), C-09a, R-FND-02.
- **Inputs:** current-month amounts by account/vendor; trailing baseline (e.g., N-month average) from R-HST-01.
- **Preconditions:** ≥ minimum-history baseline available.
- **Configurable parameters:** `CP-ANOMALY-BASELINE` (window), `CP-ANOMALY-SENSITIVITY` (deviation boundary), `CP-MINHISTORY`.
- **Rule logic:** compute deviation of the current amount from its trailing baseline; flag where deviation ≥ sensitivity.
- **Exceptions and exclusions:** event-tagged lines (R-GED-07) treated per event type; below-minimum history → "insufficient history."
- **Evidence produced:** `EV-GED-ANOMALY` (baseline, observed, deviation, window).
- **Findings produced:** `Amount anomaly` finding.
- **Severity determination method:** via R-FND-02 (deviation magnitude as input).
- **Minimum history requirements:** per `CP-ANOMALY-BASELINE` (e.g., 3 months) — declared, not assumed.
- **Outputs:** anomaly findings.
- **Related open questions:** OQ-5-adjacent (baseline definition).
- **Notes:** the baseline is deterministic and versioned; the same history+config yields the same anomalies (NFR-021).

**R-GED-07 — Accounting-Event Treatment (guard)** *(Approved · R1 · Should · `PROPOSED` consumption logic per FR-041)*
- **Purpose:** Apply correct rule treatment to journal lines by event type so routine events are not false exceptions.
- **Business context:** Payroll-interface entries, reclassifications ("RECLAS"), and accrual entries/reversals are routine; treating them as duplicates or anomalies is the fastest path to alert fatigue (FR-041 justification).
- **Related requirements:** FR-041 (consumption half; tagging half is F-01-06 at extraction).
- **Related features:** F-04-02, F-05-01 (consumers).
- **Related architecture components:** C-04 (produces tags), C-11 (consumes), C-07.
- **Inputs:** verified GED lines carrying event tags from extraction; event-marker configuration.
- **Preconditions:** event tags present and reviewable at verification (F-01-06).
- **Configurable parameters:** `CP-EVENT-MARKERS`.
- **Rule logic:** for each event type, define the treatment other rules must apply (e.g., accrual reversals excluded from duplicate/anomaly detection; payroll-interface lines excluded from reconciliation scope where configured).
- **Exceptions and exclusions:** this rule *is* the exclusion policy; it produces no findings of its own.
- **Evidence produced:** `EV-GED-EVENT` (event classification and applied treatment) attached to affected findings' evidence for auditability.
- **Findings produced:** none directly.
- **Severity determination method:** n/a.
- **Minimum history requirements:** 0.
- **Outputs:** treatment decisions consumed by R-GED-02/06 and R-REC-01/02.
- **Related open questions:** finance confirmation of markers.
- **Notes:** tags are visible and correctable at verification (F-01-06); a human can fix a mis-tag before rules run.

---

## 8. Family 3 — Reconciliation Rules (R-REC)

**Family purpose.** Reconcile GED activity against tracking records automatically, so the Operator reviews only exceptions, with full manual override and nothing lost across months (E-05, FR-044–050). This directly replaces today's manual paste-and-clear — the single largest manual effort (E-05 note) and the top value driver (DEC-022).

**Trust > AI.** Match classification is a deterministic tiering with evidence; AI plays no role. Human override is a governed, audited action, never an AI action.

**Monthly Review in a Box.** Automated matching + an exception-only Operator workspace is the Release-1 reconciliation slice.

**Architecture fit.** Match rules in C-11 on C-07; the Operator surface is C-10, which applies the **workspace/finding boundary** (06 §13, 04 §2.3) — in-progress items are workspace tasks, not findings, until cycle close or escalation. Findings (residual unreconciled) emit via C-09a.

---

**R-REC-01 — Reconciliation Scope Determination** *(Approved · R1 · Must)*
- **Purpose:** Restrict reconciliation to eligible account ranges, excluding non-invoiced spend (payroll, benefits).
- **Business context:** Reconciling payroll against an invoice tracker is meaningless; scope must be finance-defined.
- **Related requirements:** FR-050. `ASSUMPTION`.
- **Related features:** F-02-03 (config), F-05-01 (consumption).
- **Related architecture components:** C-08 (`CP-RECON-ELIGIBLE-ACCOUNTS`), C-11, C-07, R-GED-07.
- **Inputs:** verified GED lines; eligible-account configuration; event tags.
- **Preconditions:** eligible-account scope configured.
- **Configurable parameters:** `CP-RECON-ELIGIBLE-ACCOUNTS` (**pending finance validation**), `CP-EVENT-MARKERS`.
- **Rule logic:** select GED lines whose account is in the eligible set and whose event type is reconciliation-relevant; the remainder is out of reconciliation scope (not an exception).
- **Exceptions and exclusions:** payroll/benefits/non-invoiced accounts excluded by scope; event-excluded lines per R-GED-07.
- **Evidence produced:** `EV-REC-SCOPE` (in-scope/out-of-scope classification with reason).
- **Findings produced:** none.
- **Severity determination method:** n/a.
- **Minimum history requirements:** 0.
- **Outputs:** the reconciliation candidate set for R-REC-02.
- **Related open questions:** eligible-account list (finance).
- **Notes:** getting scope right is what makes the auto-match rate meaningful (E-05 ≥70% signal).

**R-REC-02 — GED-to-Tracker Match Classification** *(Approved · R1 · Must)*
- **Purpose:** Match in-scope GED lines against tracker entries and classify each as Exact / Probable / Unmatched.
- **Business context:** The product's highest-ROI capability (F-05-01). Only exact or user-confirmed matches count as reconciled (FR-045).
- **Related requirements:** FR-044, FR-045.
- **Related features:** F-05-01.
- **Related architecture components:** C-11, C-07, C-10 (workspace), C-09a (residual findings).
- **Inputs:** in-scope GED lines (R-REC-01); verified tracker entries.
- **Preconditions:** both datasets verified; scope determined.
- **Configurable parameters:** `CP-MATCH-KEYS`, `CP-MATCH-TOLERANCE` (**pending — tier boundaries**).
- **Rule logic:** attempt to match each GED line to a tracker entry on the configured keys; classify Exact (within exact tolerance), Probable (within probable tolerance — requires user confirmation), or Unmatched. Only Exact or user-confirmed Probable count as reconciled (FR-045).
- **Exceptions and exclusions:** out-of-scope lines never enter matching; event-excluded lines excluded.
- **Evidence produced:** `EV-REC-MATCH` (candidate pair, matched keys, tolerance result, tier).
- **Findings produced:** none while in the workspace (workspace tasks, §2.3 of 04); residual Unmatched become findings at cycle close/escalation via R-REC-04.
- **Severity determination method:** n/a at match time; residual findings via R-FND-02.
- **Minimum history requirements:** 0.
- **Outputs:** classified matches into C-10; reconciled set.
- **Related open questions:** tolerance values (finance).
- **Notes:** manual match/unmatch/override (FR-046) is a human action captured with reason and audit (C-10); the *reclassification result* of an override is deterministic and re-derivable.

**R-REC-03 — Cleared-Status Derivation** *(Approved · R1 · Must)*
- **Purpose:** Maintain a cleared/uncleared status per tracker entry equivalent to today's `clrd` column, with comments.
- **Business context:** Preserves the existing workbook mental model during coexistence (A-10).
- **Related requirements:** FR-047. `ASSUMPTION (A-10)`.
- **Related features:** F-05-02.
- **Related architecture components:** C-10, C-07, C-08 (`CP-CLRD-SEMANTICS`).
- **Inputs:** match results (R-REC-02); manual clear/override actions.
- **Preconditions:** match classification available.
- **Configurable parameters:** `CP-CLRD-SEMANTICS` (**pending finance definition**).
- **Rule logic:** derive cleared status from reconciliation state per configured semantics (e.g., cleared when Exact or user-confirmed); record comments.
- **Exceptions and exclusions:** entries out of reconciliation scope carry no cleared status.
- **Evidence produced:** `EV-REC-CLRD` (status, basis, comment lineage).
- **Findings produced:** none.
- **Severity determination method:** n/a.
- **Minimum history requirements:** 0.
- **Outputs:** cleared status per tracker entry; feeds workbook-compatible export (F-07-04 R2).
- **Related open questions:** `clrd` semantics (finance, per DEC-019).
- **Notes:** semantics are a Rules-Catalog input, not a requirements blocker (DEC-019).

**R-REC-04 — Unreconciled Items Determination** *(Approved · R1 · Must)*
- **Purpose:** Report all unreconciled items: GED lines without tracker matches and tracker entries without GED activity.
- **Business context:** Nothing may fall through the cracks (E-05 outcome).
- **Related requirements:** FR-048.
- **Related features:** F-05-02.
- **Related architecture components:** C-10, C-07, C-09a (at close/escalation).
- **Inputs:** match results; scope; cleared status.
- **Preconditions:** matching complete for the cycle.
- **Configurable parameters:** — (definitional; uses match outputs).
- **Rule logic:** identify in-scope GED lines with no Exact/confirmed match and tracker entries with no matching GED activity; present as workspace tasks; on cycle close or escalation, materialize residual items as findings (workspace/finding boundary).
- **Exceptions and exclusions:** items within tolerance and confirmed are reconciled, not unreconciled.
- **Evidence produced:** `EV-REC-UNMATCHED` (side, entity, amount, reason).
- **Findings produced:** `Unreconciled item` finding (at close/escalation only).
- **Severity determination method:** via R-FND-02 (age/amount as inputs).
- **Minimum history requirements:** 0.
- **Outputs:** unreconciled lists; residual findings.
- **Related open questions:** —.
- **Notes:** the surface (workspace) and the finding are one record in two presentations, one state machine (04 §2.3) — divergent statuses are a trust defect.

**R-REC-05 — Carry-Forward & Aging** *(Approved · R1 workspace / R2 analytics · Should)*
- **Purpose:** Carry unreconciled items forward into subsequent cycles until resolved, with aging.
- **Business context:** Timing differences are normal (June service invoiced in July, DEC-018); without carry-forward every timing difference becomes a permanent loose end.
- **Related requirements:** FR-049. `PROPOSED`.
- **Related features:** F-05-02 (carry-forward, R1) · F-05-03 (aging analytics, R2).
- **Related architecture components:** C-10, C-13, C-07.
- **Inputs:** prior cycles' unreconciled items; current cycle activity.
- **Preconditions:** at least one prior cycle with unresolved items.
- **Configurable parameters:** `CP-CARRYFWD-AGING-BANDS`.
- **Rule logic:** persist unresolved items across cycles; on each cycle, attempt resolution against new activity; compute age since first appearance and assign aging bands.
- **Exceptions and exclusions:** resolved items exit carry-forward.
- **Evidence produced:** `EV-REC-AGING` (first-seen period, age, band).
- **Findings produced:** aged unreconciled items escalate per configuration (via R-REC-04).
- **Severity determination method:** via R-FND-02 (age as an input).
- **Minimum history requirements:** 1 prior cycle.
- **Outputs:** carried-forward items with aging; R2 trends (F-05-03).
- **Related open questions:** —.
- **Notes:** aging turns "unmatched forever" into a governed, visible, escalating queue.

---

## 9. Family 4 — Findings Management Rules (R-FND)

**Family purpose.** Define how any rule's exception becomes a first-class, severity-classified, fully traceable finding with a managed lifecycle — one consistent findings experience for every capability (E-06, FR-069–075).

**Trust > AI.** Findings are the deterministic substrate AI later explains; the finding contract, severity, and lifecycle are AI-free (DEC-005). Grounding for any future AI answer resolves to finding IDs (FR-099).

**Monthly Review in a Box.** A single findings inbox with severity, explainability, and lifecycle is a Release-1 core; it unifies Budget/GED/Reconciliation output.

**Architecture fit.** R-FND-01/02/03 are the **Findings Domain Model (C-09a)** contract in the core; presentation is C-09b (06 §7.3). Producers emit via `FindingsCommandPort`; readers (including future AI) use `FindingsQueryPort` only.

---

**R-FND-01 — Finding Construction & Evidence Binding** *(Approved · R1 · Must)*
- **Purpose:** Define the invariant structure every finding must have and bind it to its evidence and lineage.
- **Business context:** A finding no one can trace is not trustworthy; traceability is the product's single strongest trust feature (F-06-02).
- **Related requirements:** FR-069, FR-071.
- **Related features:** F-02-04 (contract), F-06-02 (investigation).
- **Related architecture components:** C-09a, C-07, C-11.
- **Inputs:** the emitting rule's evidence record(s); rule reference; period; affected entities.
- **Preconditions:** produced only by a deterministic rule via `FindingsCommandPort`.
- **Configurable parameters:** — (structural contract).
- **Rule logic:** construct a finding with unique ID, rule reference, severity (from R-FND-02), reporting period, affected entities (account/vendor/document/row), and computed evidence values, each linked to source rows/cells and to the rule-set/config versions in force.
- **Exceptions and exclusions:** no finding may exist without a rule reference and evidence (Principle 3).
- **Evidence produced:** the bound evidence set is part of the finding.
- **Findings produced:** the finding record itself (the contract all producers use).
- **Severity determination method:** delegates to R-FND-02.
- **Minimum history requirements:** 0.
- **Outputs:** persisted, traceable findings.
- **Related open questions:** —.
- **Notes:** one-interaction traceability to rule → inputs → source (NFR-067) is a construction guarantee, not a UI afterthought.

**R-FND-02 — Severity Classification** *(Approved · R1 · Must)*
- **Purpose:** The canonical method mapping a finding's evidence to Critical / High / Medium / Low.
- **Business context:** Consistent, configurable severity across all capabilities; never AI-assigned (FR-077 spirit; FR-070).
- **Related requirements:** FR-070. `OPEN QUESTION (OQ-8)`.
- **Related features:** F-02-04 (computation), F-06-01 (presentation).
- **Related architecture components:** C-09a, C-07, C-08/C-18 (criteria).
- **Inputs:** finding evidence values; the emitting rule's severity parameters.
- **Preconditions:** finding evidence present.
- **Configurable parameters:** `CP-SEVERITY-CRITERIA`, plus rule-specific bands (`CP-VAR-SEVERITY-BANDS`, etc.) — **pending OQ-8**.
- **Rule logic:** apply the configured, rule-defined criteria to the evidence to select exactly one severity; deterministic and versioned.
- **Exceptions and exclusions:** where no criteria are configured, the finding carries a defined "severity unconfigured" state rather than a guessed level (honesty over fabrication).
- **Evidence produced:** the severity decision with the criteria version used.
- **Findings produced:** enriches findings; produces none itself.
- **Severity determination method:** this *is* the method.
- **Minimum history requirements:** 0.
- **Outputs:** severity on every finding.
- **Related open questions:** **OQ-8** (severity/materiality values).
- **Notes:** the shared method (see §5); every detection rule references it. Values pending; method complete.

**R-FND-03 — Finding Lifecycle State Transitions** *(Approved · R1 · Must)*
- **Purpose:** Enforce the legal lifecycle of a finding.
- **Business context:** Without a lifecycle, the same finding nags forever and audit cannot show how exceptions were handled (FR-072 justification).
- **Related requirements:** FR-072.
- **Related features:** F-06-03.
- **Related architecture components:** C-09a (state machine), C-14 (audit of transitions).
- **Inputs:** finding; user action; reason (for dismissal).
- **Preconditions:** finding exists.
- **Configurable parameters:** — (state model is fixed by FR-072).
- **Rule logic:** permit only legal transitions New → Acknowledged → In review → Resolved/Dismissed; dismissal requires a reason; every transition is logged with user and timestamp (audited via `AuditEventPort`).
- **Exceptions and exclusions:** illegal transitions are rejected; dismissal without reason is impossible.
- **Evidence produced:** transition history (state, user, timestamp, reason).
- **Findings produced:** — (governs existing findings).
- **Severity determination method:** n/a.
- **Minimum history requirements:** 0.
- **Outputs:** lifecycle state and history per finding.
- **Related open questions:** —.
- **Notes:** false-positive capture is a dismissal-reason category (R-FND-05), pilot-critical evidence at near-zero cost (F-06-03).

**R-FND-04 — Recurrence Linkage** *(Approved · R2 · Should)*
- **Purpose:** Link findings recurring across months and display recurrence count.
- **Business context:** "Third month in a row" is materially different information than "new this month" (FR-073 justification).
- **Related requirements:** FR-073.
- **Related features:** F-06-05.
- **Related architecture components:** C-09a, C-13 (cross-month identity), R-HST-03.
- **Inputs:** current findings; prior cycles' findings.
- **Preconditions:** ≥1 prior cycle with findings.
- **Configurable parameters:** `CP-RECURRENCE-KEY`, `CP-MINHISTORY` (=1).
- **Rule logic:** match current findings to prior findings on the recurrence key (rule + entities); maintain and display a recurrence count.
- **Exceptions and exclusions:** dismissed-as-false-positive findings do not resurrect as recurrences (respect human dismissal).
- **Evidence produced:** `EV-FND-RECUR` (linked finding IDs, count, span).
- **Findings produced:** enriches findings with recurrence; produces none new.
- **Severity determination method:** recurrence may be a severity input via `CP-SEVERITY-CRITERIA`.
- **Minimum history requirements:** 1 prior cycle.
- **Outputs:** recurrence linkage and counts.
- **Related open questions:** —.
- **Notes:** shares identity logic with R-HST-03; one definition of "the same finding."

**R-FND-05 — False-Positive Capture → Configuration Feedback** *(Approved · R1 capture / R2 analytics · Should)*
- **Purpose:** Capture findings marked false positive, with reason, as evidence for human threshold tuning.
- **Business context:** Threshold tuning without recorded evidence is guesswork; silent self-tuning would break determinism (FR-075 justification).
- **Related requirements:** FR-075.
- **Related features:** F-06-03 (capture, R1), F-06-06 (analytics, R2).
- **Related architecture components:** C-09a, C-14, C-18 (informs governed config change).
- **Inputs:** dismissal with false-positive reason category.
- **Preconditions:** finding dismissed as false positive.
- **Configurable parameters:** — (feeds parameter tuning; never alters rules automatically).
- **Rule logic:** record the false-positive event and its context; aggregate (R2) to support humans deciding parameter changes. **Never** silently alters rule behavior or a parameter.
- **Exceptions and exclusions:** feedback informs; it does not act (NFR-021 integrity).
- **Evidence produced:** `EV-FND-FP` (finding, reason, rule, parameters in force).
- **Findings produced:** —.
- **Severity determination method:** n/a.
- **Minimum history requirements:** 0.
- **Outputs:** false-positive evidence base for governed tuning (via decision log / config versioning).
- **Related open questions:** OQ-8 (tuning targets).
- **Notes:** the one place "learning" is allowed — human-in-the-loop, audited, deterministic-preserving.

---

## 10. Family 5 — Executive Reporting Rules (R-RPT)

**Family purpose.** Compute the deterministic content of the monthly leadership summary: overall RAG status, budget health, GED status, risks, recommended actions, and a thin "what changed" — reproducible forever (E-07, FR-076–080).

**Trust > AI.** RAG status and every number are deterministic (FR-077); AI-narrative slots exist, labeled, and empty until E-09, and the summary reads complete without them (FR-095).

**Monthly Review in a Box.** The leadership summary is the flagship Release-1 artifact — the Leader answers "are we okay this month, and what changed?" from it alone (E-07 signal).

**Architecture fit.** C-12 composes the summary from deterministic evidence and findings (read via `FindingsQueryPort`); reproducibility is guaranteed by replay (F-02-06); export machinery and FR-120 labeling are owned once by C-12.

---

**R-RPT-01 — Deterministic RAG Status Computation** *(Approved · R1 · Must)*
- **Purpose:** Compute the overall Green / Yellow / Red status of the month by deterministic, configurable criteria.
- **Business context:** The single most visible signal; must never be AI-assigned (FR-077).
- **Related requirements:** FR-077.
- **Related features:** F-07-01 (surfaced here).
- **Related architecture components:** C-12, C-07, C-09a (findings), C-08/C-18 (criteria).
- **Inputs:** the cycle's findings (counts by severity), key variance/exception evidence.
- **Preconditions:** analysis complete; findings available.
- **Configurable parameters:** `CP-RAG-CRITERIA` (**pending — no default**).
- **Rule logic:** apply configured criteria (e.g., presence of Critical findings, count/threshold of High findings, materiality breaches) to select exactly one status; deterministic and versioned.
- **Exceptions and exclusions:** where criteria unconfigured, report a defined "status unconfigured" state rather than a guessed color.
- **Evidence produced:** `EV-RPT-RAG` (inputs, criteria version, resulting status).
- **Findings produced:** — (a status, not a finding).
- **Severity determination method:** n/a (consumes severities).
- **Minimum history requirements:** 0.
- **Outputs:** the month's RAG status.
- **Related open questions:** OQ-8-adjacent (criteria).
- **Notes:** RAG is one deterministic aggregation rule surfaced in F-07-01 (04 §2.4 "not a standalone feature").

**R-RPT-02 — Monthly Summary Composition** *(Approved · R1 · Must)*
- **Purpose:** Assemble the deterministic monthly summary sections.
- **Business context:** The source spec's section structure, nothing more (F-07-01 guardrail).
- **Related requirements:** FR-076, FR-079 (reproducibility).
- **Related features:** F-07-01, F-07-03.
- **Related architecture components:** C-12, C-13, C-09b, C-07.
- **Inputs:** RAG status (R-RPT-01); budget health (R-BUD-*); GED status (R-GED-*); reconciliation status (R-REC-*); risks (findings); recommended actions (deterministic references to findings); MoM deltas (R-RPT-03).
- **Preconditions:** contributing rules complete.
- **Configurable parameters:** `CP-FISCAL-CALENDAR`.
- **Rule logic:** compose the fixed section set (RAG; Budget Health; GED Status; Invoice Exceptions [Phase 3]; Key Risks; Recommended Actions; What Changed) from deterministic evidence; leave labeled AI-narrative slots empty until E-09.
- **Exceptions and exclusions:** no section is fabricated; unavailable capabilities are shown as "unavailable — [reason]" per R-RDY-07, not omitted silently.
- **Evidence produced:** `EV-RPT-SUMMARY` (composed section content with sources).
- **Findings produced:** —.
- **Severity determination method:** n/a.
- **Minimum history requirements:** 0 (MoM section shown where history exists).
- **Outputs:** the monthly summary; retained and re-displayable exactly (FR-079).
- **Related open questions:** —.
- **Notes:** regeneration against the same verified inputs+config is identical (F-02-06); this is the visible payoff of replay.

**R-RPT-03 — "What Changed" Delta Section** *(Approved · R1 thin / R2 interactive · Must)*
- **Purpose:** Provide the month-over-month "what changed" content: spend deltas, new/resolved/recurring findings, status changes.
- **Business context:** Absorbed into the summary as a thin section for R1 (F-07-01); the interactive exploration is F-07-02 (R2).
- **Related requirements:** FR-078.
- **Related features:** F-07-01 (thin, R1), F-07-02 (interactive, R2).
- **Related architecture components:** C-12, C-13, R-HST-02, R-FND-04.
- **Inputs:** current vs. prior cycle deltas (R-HST-02); finding status changes (R-FND-03/04).
- **Preconditions:** ≥1 prior cycle.
- **Configurable parameters:** — (uses history deltas).
- **Rule logic:** summarize spend deltas and new/resolved/recurring findings and status changes since last month.
- **Exceptions and exclusions:** first month → "no prior month to compare."
- **Evidence produced:** `EV-RPT-CHANGE` (delta set with references).
- **Findings produced:** —.
- **Severity determination method:** n/a.
- **Minimum history requirements:** 1 prior cycle.
- **Outputs:** the "what changed" section.
- **Related open questions:** —.
- **Notes:** cross-month finding identity belongs to R-FND-04/R-HST-03, not here (F-07-02 boundary).

---

## 11. Family 6 — Historical Comparison Rules (R-HST)

**Family purpose.** Make history a first-class deterministic capability: trailing baselines, month-over-month deltas, recurring-finding identity, and change ("what's new") detection across cycles (06 §16; FR-078/108/109; F-06-05/F-07-02).

**Trust > AI.** All comparison and baseline math is deterministic and reproducible; "what's new" surfaces *change* for human attention and never manufactures findings (Principle 5).

**Monthly Review in a Box.** MoM deltas feed the Release-1 summary; deeper history capabilities deepen it in R2.

**Architecture fit.** C-13 owns retention and comparison; it supplies baselines to C-11 history-based rules and deltas to C-12; recurrence identity is shared with C-09a (R-FND-04).

---

**R-HST-01 — Trailing Baseline Computation** *(Approved · R2 · Should)*
- **Purpose:** Compute deterministic trailing baselines (e.g., N-month averages) for history-based rules.
- **Business context:** The shared, boring, deterministic baseline behind anomaly/trend detection (F-02-05 R2).
- **Related requirements:** FR-040/036 support; F-02-05.
- **Related features:** F-02-05, F-04-03, F-03-05.
- **Related architecture components:** C-13, C-07.
- **Inputs:** trailing verified monthly data by dimension.
- **Preconditions:** ≥ minimum-history months retained.
- **Configurable parameters:** `CP-ANOMALY-BASELINE`, `CP-MINHISTORY`.
- **Rule logic:** compute the configured trailing statistic per dimension deterministically.
- **Exceptions and exclusions:** below-minimum history → baseline unavailable; dependent rules report "insufficient history."
- **Evidence produced:** `EV-HST-BASELINE` (window, statistic, inputs).
- **Findings produced:** — (feeds other rules).
- **Severity determination method:** n/a.
- **Minimum history requirements:** per `CP-ANOMALY-BASELINE`.
- **Outputs:** baselines consumed by R-GED-06, R-BUD-06.
- **Related open questions:** OQ-5-adjacent.
- **Notes:** one baseline definition; reused, never re-derived per consumer.

**R-HST-02 — Month-over-Month Delta Computation** *(Approved · R1 · Must)*
- **Purpose:** Compute spend and finding deltas between consecutive cycles.
- **Business context:** The single source of MoM truth feeding budget MoM (R-BUD-03) and the summary (R-RPT-03).
- **Related requirements:** FR-078, FR-109.
- **Related features:** F-07-01 (thin), F-07-02 (interactive R2).
- **Related architecture components:** C-13, C-12, C-07.
- **Inputs:** current and prior cycle verified data and findings.
- **Preconditions:** ≥1 prior cycle.
- **Configurable parameters:** — (deltas), `CP-FISCAL-CALENDAR`.
- **Rule logic:** compute deltas (amount/%) by dimension and finding-set changes (new/resolved/recurring) deterministically.
- **Exceptions and exclusions:** first month → no comparison.
- **Evidence produced:** `EV-HST-MOM` (deltas, finding-set changes).
- **Findings produced:** — (R-BUD-03 may raise MoM findings using these deltas).
- **Severity determination method:** n/a.
- **Minimum history requirements:** 1 prior cycle.
- **Outputs:** MoM deltas.
- **Related open questions:** —.
- **Notes:** consumed by, not duplicated in, R-BUD-03 and R-RPT-03.

**R-HST-03 — Recurring-Finding Identity** *(Approved · R2 · Should)*
- **Purpose:** Define what makes a finding "the same" across months.
- **Business context:** The identity behind recurrence counts (R-FND-04) and recurring-risk views.
- **Related requirements:** FR-073.
- **Related features:** F-06-05.
- **Related architecture components:** C-13, C-09a.
- **Inputs:** findings across cycles.
- **Preconditions:** ≥1 prior cycle with findings.
- **Configurable parameters:** `CP-RECURRENCE-KEY`.
- **Rule logic:** match findings on the configured recurrence key (rule + entities) to establish identity across cycles.
- **Exceptions and exclusions:** human-dismissed false positives are not re-linked.
- **Evidence produced:** `EV-HST-RECUR` (identity links).
- **Findings produced:** —.
- **Severity determination method:** n/a.
- **Minimum history requirements:** 1 prior cycle.
- **Outputs:** identity used by R-FND-04.
- **Related open questions:** —.
- **Notes:** one identity definition shared with findings management.

**R-HST-04 — "What's New" Change Detection** *(Future / Deferred · `PROPOSED`)*
- **Purpose:** Identify new vendors, accounts, department activity, and spending patterns appearing for the first time.
- **Business context:** Approved architectural guidance concept 10 (06 §16.2). **New ≠ wrong** — this surfaces change for attention, not exceptions.
- **Related requirements:** grounded in FR-078/FR-032 and FR-041 philosophy (no new requirement).
- **Related features:** future; extension via XP-04 (06 §19).
- **Related architecture components:** C-13, C-07 (deterministic), R-GED-05 (feeds coding-context).
- **Inputs:** current-cycle entities vs. historical entity set.
- **Preconditions:** sufficient history to define "previously seen."
- **Configurable parameters:** `CP-MINHISTORY`; entity-scope configuration.
- **Rule logic:** compute the set difference between current entities and the historical set; surface *new* entities as change (not findings).
- **Exceptions and exclusions:** does **not** manufacture findings (Principle 5); a new entity is flagged as *wrong* only if a *separate* exception rule (e.g., R-GED-05) independently fires.
- **Evidence produced:** `EV-HST-NEW` (new entities with first-seen context).
- **Findings produced:** none (change surface).
- **Severity determination method:** n/a.
- **Minimum history requirements:** declared when activated.
- **Outputs:** "what's new this month" change list.
- **Related open questions:** OQ-4 (project/workstream dimensions may expand entity scope).
- **Notes:** deferred; carried as an extension seam so it fits later without redesign. Keeps change detection and exception detection architecturally separate.

---

## 12. Family 7 — Capability Readiness Rules (R-RDY)

**Family purpose.** Before analysis, assess data quality and determine which capabilities are Available / Partially available / Unavailable, and why (06 §10; FR-004/007/021–025/081/111). Users upload only what they have; the system never assumes every document exists.

**Trust > AI.** Readiness and data-quality verdicts are deterministic and evidence-based; they tell the user honestly what can and cannot be analyzed rather than producing unreliable results silently.

**Monthly Review in a Box.** Readiness is part of cycle status (FR-081) and lets the review proceed on the available subset — essential to a review that "just works" with whatever files a user has that month.

**Architecture fit.** C-05 computes readiness and data quality; readiness composes document presence (C-03), quality outcomes, reference-data presence (C-08), verification state (C-06), and minimum-history satisfaction (F-02-05). Deterministic and auditable like the rest of the core.

---

**R-RDY-01 — Schema Validation** *(Approved · R1 · Must)*
- **Purpose:** Validate extracted data against the expected structure per document type.
- **Related requirements:** FR-021. **Related features:** F-01-08. **Components:** C-05, C-04.
- **Inputs:** extracted dataset; expected schema per document type. **Preconditions:** extraction complete.
- **Configurable parameters:** `CP-ACCOUNT-LIST` (valid accounts); document-type schema definitions.
- **Rule logic:** report missing columns, unexpected columns, and type mismatches against the expected structure.
- **Exceptions and exclusions:** known-optional columns configured as such.
- **Evidence produced:** `EV-RDY-SCHEMA` (deviations). **Findings produced:** data-quality findings (pre-verification, quality class). **Severity:** via R-FND-02 (quality severity). **Min history:** 0.
- **Outputs:** schema validation result. **Open questions:** —. **Notes:** feeds readiness (R-RDY-07).

**R-RDY-02 — Row-Level Quality Checks** *(Approved · R1 · Must)*
- **Purpose:** Flag rows with missing required fields, invalid account numbers, malformed dates/periods, or non-numeric amounts.
- **Related requirements:** FR-022. **Related features:** F-01-08. **Components:** C-05.
- **Inputs:** extracted rows; `CP-ACCOUNT-LIST`; fiscal calendar. **Preconditions:** extraction complete.
- **Configurable parameters:** `CP-ACCOUNT-LIST`, `CP-FISCAL-CALENDAR`.
- **Rule logic:** validate each row's required fields/formats; mark failing rows.
- **Exceptions and exclusions:** placeholder values (".", blanks) normalized at extraction are not failures (FR-014).
- **Evidence produced:** `EV-RDY-ROW` (per-row issues). **Findings produced:** quality findings. **Severity:** via R-FND-02. **Min history:** 0.
- **Outputs:** row-quality result. **Open questions:** —. **Notes:** feeds quarantine (R-RDY-04).

**R-RDY-03 — Internal Consistency / Subtotal Self-Check** *(Approved · R1 · Should · `PROPOSED`)*
- **Purpose:** Cross-check extracted detail against the report's own subtotal/total rows.
- **Business context:** The cheapest extraction-error detection — the file audits itself (FR-023 justification).
- **Related requirements:** FR-023. **Related features:** F-01-08. **Components:** C-05, C-04.
- **Inputs:** extracted detail rows; retained subtotal/total rows. **Preconditions:** subtotals retained (FR-013).
- **Configurable parameters:** tolerance for rounding (exact by default; configurable).
- **Rule logic:** sum detail per group and compare to the report's stated subtotal/total; flag discrepancies.
- **Exceptions and exclusions:** documented rounding conventions.
- **Evidence produced:** `EV-RDY-CONSISTENCY` (group, computed vs. stated). **Findings produced:** consistency findings. **Severity:** via R-FND-02. **Min history:** 0.
- **Outputs:** self-check result. **Open questions:** —. **Notes:** a failing self-check is a strong signal the extraction is wrong — surfaced before verification.

**R-RDY-04 — Row Quarantine Determination** *(Approved · R1 · Should · `PROPOSED`)*
- **Purpose:** Quarantine failing rows for user attention and proceed with the valid remainder.
- **Business context:** One bad row must not block a month-end review (FR-024 justification).
- **Related requirements:** FR-024. **Related features:** F-01-08. **Components:** C-05.
- **Inputs:** row-quality/schema/consistency results. **Preconditions:** quality checks run.
- **Configurable parameters:** `CP-QUALITY-CAVEAT-THRESHOLD` (ratio degrading readiness).
- **Rule logic:** move failing rows to quarantine; retain valid rows for analysis; record what was excluded.
- **Exceptions and exclusions:** none — quarantine never silently drops data (NFR-062).
- **Evidence produced:** `EV-RDY-QUARANTINE` (excluded rows and reasons). **Findings produced:** — (quality summary, not exceptions). **Severity:** n/a. **Min history:** 0.
- **Outputs:** clean set + quarantine list. **Open questions:** —. **Notes:** quarantine volume feeds "Partially available" readiness (R-RDY-07).

**R-RDY-05 — Data-Quality Summary** *(Approved · R1 · Should · `PROPOSED`)*
- **Purpose:** Produce a per-cycle data-quality summary before verification.
- **Business context:** The Operator needs "is this data fit to analyze?" at a glance (FR-025 justification).
- **Related requirements:** FR-025. **Related features:** F-01-08. **Components:** C-05.
- **Inputs:** results of R-RDY-01..04; confidence distribution (from extraction). **Preconditions:** quality checks run.
- **Configurable parameters:** `CP-QUALITY-CAVEAT-THRESHOLD`.
- **Rule logic:** aggregate rows ingested, quarantined, confidence distribution, and consistency results into one summary.
- **Exceptions and exclusions:** —.
- **Evidence produced:** `EV-RDY-SUMMARY`. **Findings produced:** —. **Severity:** n/a. **Min history:** 0.
- **Outputs:** the data-quality summary shown before the verification gate. **Open questions:** —. **Notes:** informs the human before they approve (F-01-09).

**R-RDY-06 — Minimum-History Gate** *(Approved · R1 · Must)*
- **Purpose:** Enforce each rule's declared minimum-history requirement.
- **Business context:** Cold-start honesty; the first months are when FinSight is judged (FR-111 justification).
- **Related requirements:** FR-111. **Related features:** F-02-05. **Components:** C-05, C-07, C-13.
- **Inputs:** available history depth; each rule's `CP-MINHISTORY` declaration. **Preconditions:** —.
- **Configurable parameters:** `CP-MINHISTORY` (per rule).
- **Rule logic:** for each history-based rule, compare available history to its minimum; below it, the rule reports "insufficient history" and does not fire; the report discloses which rules ran with limited baselines.
- **Exceptions and exclusions:** history-free rules always run.
- **Evidence produced:** `EV-RDY-HISTORY` (per-rule sufficiency). **Findings produced:** —. **Severity:** n/a. **Min history:** 0 (this rule governs others).
- **Outputs:** per-rule run/skip decisions with disclosure. **Open questions:** —. **Notes:** the structural expression of AP-11.

**R-RDY-07 — Capability-Readiness Assessment** *(Approved · R1 · Should · `PROPOSED` model, 06 §10)*
- **Purpose:** Compute the capability-readiness map: for each capability, Available / Partially available / Unavailable with a reason.
- **Business context:** Approved architectural guidance concept 3; users are informed of missing prerequisites (06 §10).
- **Related requirements:** grounded in FR-004/007/021–025/081/111 (no new requirement — AA-07).
- **Related features:** F-01-08, F-01-01 (status), F-06-01 (surfacing).
- **Related architecture components:** C-05, C-03, C-06, C-08, C-13.
- **Inputs:** document presence/classification (C-03); data-quality outcomes (R-RDY-01..05); reference-data presence (C-08); verification state (C-06); minimum-history satisfaction (R-RDY-06).
- **Preconditions:** intake and quality checks run.
- **Configurable parameters:** `CP-READINESS-REQUIREMENTS`, `CP-QUALITY-CAVEAT-THRESHOLD`.
- **Rule logic:** for each capability, evaluate its configured prerequisites; assign Available (all met), Partially available (met with a stated caveat, e.g., high quarantine or limited history), or Unavailable (a hard prerequisite missing) with a machine- and human-readable reason.
- **Exceptions and exclusions:** readiness gates *capabilities*, not the whole review; available capabilities run.
- **Evidence produced:** `EV-RDY-CAPABILITY` (per-capability status and reason).
- **Findings produced:** — (readiness is status, not a finding).
- **Severity determination method:** n/a.
- **Minimum history requirements:** 0 (reads R-RDY-06 outputs).
- **Outputs:** the readiness map, part of cycle status (FR-081) and the summary (R-RPT-02).
- **Related open questions:** AA-07 (readiness derivable from existing FRs).
- **Notes:** deterministic and auditable; "why unavailable" is always a concrete, named reason with a next step (NFR-055/064).

---

## 13. Family 8 — Future Invoice Review Rules (R-INV) — Deferred (E-12, Phase 3, gated on OQ-2)

**Family purpose.** Validate each invoice line-by-line against POs, SOWs, rate cards, estimates, and staffing plans, and arrive at a single status recommendation with reasons — never an action (E-12, FR-051–060, FR-121/122). FinSight recommends; humans decide (00 §1).

**Trust > AI.** Every check and the final status are deterministic with per-line evidence; AI may later narrate the recommendation, never make it. Invoice validation is a named value driver "when samples arrive" (DEC-022).

**Monthly Review in a Box.** Extends the same intake → verify → analyze → findings → summary spine to invoices, using the same Findings Hub and export — one review platform, one more document type.

**Architecture fit.** New document types and rule packs added via extension points XP-02 (templates) and XP-01 (rules) with no core redesign (06 §19); findings via C-09a; the five-status recommendation is a deterministic rule.

**Gate & fidelity.** `PENDING VALIDATION` — one real invoice validated the set (DEC-018); other vendors' invoices, POs, SOWs, and rate cards are unseen (A-05, OQ-2). These rules are specified at **provisional fidelity** and must be re-verified against samples before build (DEC-011). Parameters (`CP-RATE-TOLERANCE`, `CP-HOURS-TOLERANCE`, `CP-INV-STATUS-CRITERIA`) are pending OQ-2/finance.

| Rule | Name / purpose | Key requirement(s) | Key parameter(s) | Evidence / finding | Notes (provisional) |
|---|---|---|---|---|---|
| **R-INV-01** | Line-item type differentiation — classify labor / tax / expense / other and route each to appropriate checks | FR-121 | (type-marker config) | `EV-INV-TYPE` / mis-typed-line | Validated by real sample (BEAT tax line); non-labor lines exempt from rate/hours checks — prevents false rate-mismatch findings |
| **R-INV-02** | PO matching — validate amount vs. PO remaining balance; missing-PO is itself a finding | FR-051 | (balance tolerance) | `EV-INV-PO` / over-balance, missing-PO | PO field can be blank (DEC-018) → finding, not error/skip |
| **R-INV-03** | SOW period & scope validation | FR-052 | (period/scope refs) | `EV-INV-SOW` / out-of-period, out-of-scope | Sample-gated (POs/SOWs unseen) |
| **R-INV-04** | Rate-card validation — labor lines only | FR-053 | `CP-RATE-TOLERANCE` | `EV-INV-RATE` / rate mismatch | Applies to labor lines only (R-INV-01) |
| **R-INV-05** | Hours validation vs. estimate/timesheet | FR-054 | `CP-HOURS-TOLERANCE` | `EV-INV-HOURS` / hours mismatch | Estimate/timesheet references unconfirmed |
| **R-INV-06** | Resource authorization vs. staffing plan | FR-055 | (staffing ref) | `EV-INV-RESOURCE` / unauthorized resource | Depends on resource plan (E-11 data) |
| **R-INV-07** | Code & category validation | FR-056 | `CP-CODING-EXPECTATIONS` | `EV-INV-CODE` / bad code/category | Reuses coding-expectation reference |
| **R-INV-08** | Duplicate invoice detection | FR-057 | (dup keys/window) | `EV-INV-DUP` / duplicate invoice | Same number, or vendor+period+amount pattern |
| **R-INV-09** | Deliverable confirmation | FR-058 | (deliverable ref) | `EV-INV-DELIV` / unconfirmed delivery | Only where deliverable records exist |
| **R-INV-10** | Invoice status recommendation — exactly one of five statuses with reasons | FR-059, FR-060 | `CP-INV-STATUS-CRITERIA` | status + per-line findings | Recommendation only; never an action (00 §1) |
| **R-INV-11** | Vendor project reference mapping | FR-122 | (project→dept/account map) | `EV-INV-PROJECT` | Introduces invoice-level Project dimension; GED stays dept/account/vendor (A-02) |

**Severity/min-history:** all via R-FND-02; history-free unless a rule uses trailing references. **Open questions:** **OQ-2** (samples), OQ-4 (project dimension), OQ-8 (severity).

---

## 14. Family 9 — Future Resource & Contract Rules (R-RES) — Deferred (E-11, Phase 2)

**Family purpose.** Connect resources, contracts, vendors, departments, accounts, and budget allocations, compute resource cost, attribute budget to resources, and flag contract-governance gaps (E-11, FR-061–068).

**Trust > AI.** Cost, attribution, and governance-gap checks are deterministic; the data model supports attrition analysis from day one (DEC-014) with all computation deterministic.

**Monthly Review in a Box.** Adds a resource/contract lens on the same cycle and Findings Hub; answers "which contracts fund which people, and what does each cost?" (E-11 signal) inside the platform.

**Architecture fit.** New document type (resource loading sheet) via XP-02 on the designed schema (DEC-012); rules via XP-01; contract-mappings view is a C-11/C-13 derivation; governance findings via C-09a.

**Gate & fidelity.** Phase 2; resource schema designed but not sampled (DEC-012, pending business validation). Provisional fidelity.

| Rule | Name / purpose | Key requirement(s) | Key parameter(s) | Evidence / finding | Notes (provisional) |
|---|---|---|---|---|---|
| **R-RES-01** | Resource cost computation — rate × allocation × period by resource/vendor/dept/account | FR-063 | `CP-RESOURCE-COST-METHOD` | `EV-RES-COST` | Deterministic; conventions pending (DEC-012) |
| **R-RES-02** | Budget-to-resource attribution — portion of an account's budget/actuals attributable to resources | FR-064 | (attribution method) | `EV-RES-ATTRIB` | Connects resource cost to budget lines |
| **R-RES-03** | Resource status & change history — dated, auditable status/allocation/rate transitions | FR-062, FR-065 | — | `EV-RES-HISTORY` | Supports future attrition analysis (DEC-014) from day one |
| **R-RES-04** | Contract coverage governance checks — active resources with no contract; expired contracts with active resources; billing inconsistent with mapping | FR-068 (`PROPOSED`) | (coverage refs) | `EV-RES-COVERAGE` / governance-gap finding | The three most common contract-governance failure modes |
| **R-RES-05** | Contract mappings derivation — Resources↔Contracts/SOWs↔Vendors↔Depts↔Accounts↔Budget | FR-066, FR-067 | (mapping refs) | `EV-RES-MAP` | Navigable relationship view (DEC-013) |

**Severity/min-history:** via R-FND-02; R-RES-03 history accumulates from onboarding. **Open questions:** DEC-012 schema validation; A-11 (multi-department).

---

## 15. Family 10 — Future Forecasting & Scenario Rules (R-FOR) — Deferred (E-13, Phase 4)

**Family purpose.** Project period-end positions and explore hypothetical scenarios — including resource-departure impact and backfill costs — all computed deterministically, with hypotheticals never mixed with actuals (E-13, FR-112–115).

**Trust > AI.** Every number is deterministic; AI narrates scenario results only, clearly labeled; scenario outputs are visibly marked hypothetical (FR-115).

**Monthly Review in a Box.** A forward-looking lens layered on the same cycle data once the platform and history exist; enhances, never redefines, the monthly review.

**Architecture fit.** Aggregate/scenario computation via the extension hook XP-05 and C-11/C-13; data prerequisites land with E-11 (DEC-014). Deferred and re-justified before activation (DEC-022).

**Gate & fidelity.** Phase 4, deferred; provisional fidelity; re-justify through the decision log before build.

| Rule | Name / purpose | Key requirement(s) | Key parameter(s) | Notes (provisional) |
|---|---|---|---|---|
| **R-FOR-01** | Deterministic forecast projection — year/period-end position from actuals, run rates, (Phase 2) resource allocation | FR-112 | `CP-RUNRATE-METHOD` | Stated calculation methods; deterministic (shares method with R-BUD-05) |
| **R-FOR-02** | Resource departure impact — given a departure date, remaining planned cost released by account/period | FR-113 | (cost method) | Data-model support from Phase 2 (FR-062, DEC-014) |
| **R-FOR-03** | Backfill scenario estimation — replacement rate/start/allocation → net budget effect | FR-114 | (scenario params) | Deterministic scenario math |
| **R-FOR-04** | What-if scenario framework — parameterized hypotheticals computed deterministically, AI narrates | FR-115 | (scenario params) | Results always marked hypothetical, never mixed with actuals |

**Severity/min-history:** forecasts are projections, not findings (no severity); history per method. **Open questions:** E-13 re-justification; depends on E-11 data.

---

## 16. Approved Rules (summary index)

Buildable now subject only to parameter values (which are governed configuration, not blockers — DEC-019):

- **Budget:** R-BUD-01, R-BUD-02 (OQ-8 values), R-BUD-03, R-BUD-04 (R1); R-BUD-05, R-BUD-06 (R2).
- **GED:** R-GED-01, R-GED-02, R-GED-04, R-GED-05, R-GED-07 (R1); R-GED-03 (R1 reference-mode / R2 history-mode per OQ-5); R-GED-06 (R2).
- **Reconciliation:** R-REC-01, R-REC-02, R-REC-03, R-REC-04, R-REC-05 (carry-forward R1 / analytics R2).
- **Findings:** R-FND-01, R-FND-02 (OQ-8 values), R-FND-03, R-FND-05 (capture R1) (R1); R-FND-04 (R2).
- **Reporting:** R-RPT-01, R-RPT-02, R-RPT-03 (thin R1 / interactive R2).
- **Historical:** R-HST-02 (R1); R-HST-01, R-HST-03 (R2).
- **Readiness:** R-RDY-01..07 (R1).

## 17. Assumptions (rules-specific)

Building on the project Assumptions Register (A-01..A-13, 01 §2), which remains in force:

| ID | Assumption | If wrong | Owner |
|---|---|---|---|
| **RA-01** | Accounting-event markers (payroll/reclass/accrual-reversal) are reliably observable in GED data (partially seen in sample) | R-GED-07 guard weakens; duplicate/anomaly false positives rise | finance (FR-041) |
| **RA-02** | Reconciliation match keys and tolerances can distinguish exact/probable/unmatched at useful rates on real data | R-REC-02 auto-match rate below target (E-05 ≥70% signal) | finance |
| **RA-03** | A finance-maintained expected-entries reference *or* sufficient history will exist for missing-entry detection | R-GED-03 variant selection blocked; capability Unavailable until resolved | finance (OQ-5) |
| **RA-04** | Severity/materiality can be expressed as per-account/vendor configurable criteria | R-FND-02/R-BUD-02 need a richer criteria model | finance (OQ-8) |
| **RA-05** | Deterministic run-rate/forecast methods can be agreed with finance | R-BUD-05/R-FOR-01 do not ship until agreed | finance |
| **RA-06** | Invoice/PO/SOW/rate-card structures are stable enough for template-based extraction once sampled | R-INV-* rework for unseen formats | stakeholders (OQ-2) |
| **RA-07** | The capability-readiness model introduces no new requirement (it composes existing FRs) | Readiness becomes a requirements-level change via the decision log | team (AA-07) |

## 18. Open Questions (affecting rules)

Per DEC-019, Rules-Catalog open questions do not block the requirements or this catalog's *logic*; they gate *parameter values* and *variant selection*.

| # | Question | Rules affected | Effect | Status |
|---|---|---|---|---|
| **OQ-5** | Missing-entry baseline: history-derived or finance-maintained expected list? | R-GED-03 (and R-GED-06 baseline) | Selects the R1 reference variant vs. R2 history variant | Open (RC class) |
| **OQ-7** | Official monthly posting cutoff calendar | R-GED-04 (`CP-CUTOFF-CALENDAR`) | Defines "delayed"; interim configurable | Open (RC class) |
| **OQ-8** | Materiality thresholds and severity bands per account/vendor (% / $) | R-BUD-02, R-FND-02, R-RPT-01 (and all severity) | Sets finding boundaries and severity/RAG bands | Open (RC class) |
| **OQ-2** | Samples: other vendors' invoices, POs, SOWs, rate cards | R-INV-* (whole family) | Build gate for E-12; parameters pending | Partially closed (one invoice, DEC-018) |
| **OQ-4** | Project/workstream/funding-category mapping files | R-INV-11, R-HST-04, dimensional scope | May expand entity/dimension scope | Open (FP; invoice project IDs available, FR-122) |
| **clrd semantics / eligible accounts** | Cleared-status meaning; reconciliation-eligible account ranges | R-REC-03, R-REC-01 | Define cleared derivation and reconciliation scope | RC inputs (finance) |

## 19. Future / Deferred Rules (summary)

Specified at provisional fidelity; re-verified before build against their gates:

- **R-INV-01..11** — Invoice Review (E-12, Phase 3) — **gated on OQ-2 samples** (DEC-011); parameters pending.
- **R-RES-01..05** — Resource & Contract (E-11, Phase 2) — schema designed not sampled (DEC-012).
- **R-FOR-01..04** — Forecasting & Scenario (E-13, Phase 4) — deferred; re-justify before activation (DEC-022); depends on E-11 data.
- **R-HST-04** — "What's New" change detection — deferred extension (XP-04); change ≠ exception.
- **R-BUD-06, R-GED-06, R-HST-01, R-FND-04, R-RPT-03 (interactive)** — history-dependent R2 members; logic approved, ship in Release 2.

No future rule may introduce scope beyond its approved requirement; each carries its `PENDING VALIDATION` / gate and re-verification obligation.

---

## 20. Traceability

Per the traceability skill: this catalog is the "how deterministic truth is produced" layer between features (04) and implementation. Implementing units will carry `Implements: FR-###, R-<FAM>-##`; tests carry `Verifies: FR-###/NFR-###` and the rule ID; `/sdd:trace` assembles the full matrix.

**20.1 Rule family → epic / feature / architecture component**

| Family | Epic | Primary feature(s) | Architecture component(s) |
|---|---|---|---|
| R-BUD Budget | E-03 | F-03-01..05 | C-11 (budget pack), C-07, C-09a |
| R-GED GED | E-04 | F-04-01..03 | C-11 (GED pack), C-07, C-04 (tags), C-09a |
| R-REC Reconciliation | E-05 | F-05-01..03 | C-11 (match pack), C-10, C-07, C-09a |
| R-FND Findings | E-06 / E-02 | F-02-04, F-06-01..06 | C-09a (contract), C-09b (presentation), C-07 |
| R-RPT Reporting | E-07 | F-07-01..04 | C-12, C-07, C-13 |
| R-HST Historical | E-07 / C-13 | F-02-05, F-06-05, F-07-02 | C-13, C-07, C-09a |
| R-RDY Readiness | E-01 | F-01-08/09, F-01-01 | C-05, C-03, C-06, C-08 |
| R-INV Invoice *(future)* | E-12 | (undecomposed) | C-04/C-11 via XP-02/XP-01, C-09a |
| R-RES Resource *(future)* | E-11 | (undecomposed) | C-04/C-11 via XP-02, C-13, C-09a |
| R-FOR Forecasting *(future)* | E-13 | (undecomposed) | C-11/C-13 via XP-05 |

**20.2 Requirement → rule (analysis/detection FRs)**

| FR | Rule(s) | FR | Rule(s) |
|---|---|---|---|
| FR-021 | R-RDY-01 | FR-044 / FR-045 | R-REC-02 |
| FR-022 | R-RDY-02 | FR-047 | R-REC-03 |
| FR-023 | R-RDY-03 | FR-048 | R-REC-04 |
| FR-024 | R-RDY-04 | FR-049 | R-REC-05 |
| FR-025 | R-RDY-05 | FR-050 | R-REC-01 |
| FR-030 / FR-031 | R-BUD-01 | FR-069 / FR-071 | R-FND-01 |
| FR-032 | R-BUD-03 | FR-070 | R-FND-02 |
| FR-033 | R-BUD-02 | FR-072 | R-FND-03 |
| FR-034 | R-BUD-05 | FR-073 | R-FND-04 / R-HST-03 |
| FR-035 | R-BUD-04 | FR-075 | R-FND-05 |
| FR-036 | R-BUD-06 | FR-076 | R-RPT-02 |
| FR-037 | R-GED-03 | FR-077 | R-RPT-01 |
| FR-038 | R-GED-02 | FR-078 | R-RPT-03 / R-HST-02 |
| FR-039 | R-GED-04 | FR-079 | R-RPT-02 (replay F-02-06) |
| FR-040 | R-GED-06 | FR-108 / FR-109 | R-HST-01/02, R-GED-01 |
| FR-041 | R-GED-07 (consumption) | FR-111 | R-RDY-06 |
| FR-042 | R-GED-05 | FR-051..060 / 121 / 122 | R-INV-01..11 |
| FR-043 | R-GED-01 | FR-061..068 | R-RES-01..05 |
| FR-004/007/081 | R-RDY-07 | FR-112..115 | R-FOR-01..04 |

**20.3 Coverage statements**

- Every Release-1 analysis/detection FR (Budget, GED, Reconciliation, Findings, Reporting, Readiness) has ≥1 owning rule (§20.2); none is orphaned.
- Every rule traces to an approved requirement and an architecture component (§20.1); no rule invents scope. New framings (readiness R-RDY-07, "what's new" R-HST-04) are `PROPOSED`/deferred and grounded in existing FRs (AA-07, §16.2 of 06) — no R1 requirement scope is created.
- Every parameter in §4 names its controlling open question/owner and the rules depending on it; no threshold, tolerance, band, cutoff, or materiality value is asserted where a source leaves it to the business.
- No conflict with logged decisions: DEC-005 (deterministic core / AI boundary), DEC-002 (dimensions), DEC-017 (monthly), DEC-018 (invoice findings), DEC-019 (catalog/architecture split), DEC-022/023 (release plan / locks) are all respected; no Must is weakened.

**20.4 Downstream obligation**

Rule parameter *values* are set and versioned in C-18 (FR-107); each analysis run records the rule-set and configuration versions in force (NFR-022) so any historical finding is reproducible and explainable (F-02-06, F-08-03). Feature plans (`specs/plans/`) elaborate these rules into tasks; golden datasets (§2.5) prove each rule; the provider-swap regression (NFR-037) proves AI changes nothing here.

---

*End of 05-rules-catalog.md — deterministic business logic and rule structure only. No hard-coded thresholds, tolerances, severities, or materiality values are asserted beyond those explicitly approved in source documents; all such values are configurable parameters (§4) tied to their controlling open questions. Submit to the team and the design-review board (deterministic-logic focus: software-architect, data-architect, qa-engineer, plus a Finance Governance reviewer for rule correctness) before any status change beyond Draft.*
