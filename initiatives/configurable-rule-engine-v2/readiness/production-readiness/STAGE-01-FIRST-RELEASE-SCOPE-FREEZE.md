# Stage 01 — Candidate First-Release Scope Freeze

**Program:** FinSight Production-Readiness and Governed Release Program
**Stage:** 01 — Baseline Freeze and SDD Reconciliation
**Document status:** Candidate scope freeze based on recommended defaults
**Approval status:** **Pending Product Owner approval**
**Effective status:** **Not effective**
**Decision source:** `STAGE-01-PRODUCT-AND-FINANCIAL-CONTROL-DECISIONS.md`

## 1. Non-effective declaration

This document describes the recommended first-release boundary if the Product
Owner and every required specialist authority approve S1-D01 through S1-D13.

It does not:

- approve any recommendation;
- change a protected rule;
- supersede a requirement or ADR;
- authorize a migration;
- authorize Stage 02 implementation;
- authorize packaging, pilot use, or distribution; or
- convert a known limitation into an accepted release risk.

If any decision is rejected or changed, this candidate freeze must be updated
and independently reconciled before it can become effective.

## 2. Candidate product outcome

Release 1 is a financially correct, deterministic, private, accessible,
supportable Windows desktop application that:

- installs and launches without Python, a developer environment, Terminal, or
  manual dependency setup;
- accepts the approved Budget and GED source layouts;
- preserves original workbooks unchanged;
- provides an audited reviewed working copy;
- executes one confirmed active Rule Set through one versioned deterministic
  engine;
- finds, explains, and evidences financial-control issues;
- preserves review, rule, validation, publication, audit, report, export, and
  recovery history;
- provides deterministic leadership reporting and evidence exports;
- offers explanatory, private, local-only Ask Fin; and
- installs, repairs, upgrades, and uninstalls through a governed signed Windows
  distribution.

No component outside the deterministic rule engine creates PASS, FAIL,
NOT_EVALUATED, a Finding, a financial value, Overall Review Status, or RAG.

## 3. Candidate in-scope release boundary

### 3.1 Protected baseline and deterministic validation

Release 1 includes exactly these mandatory protected controls in every new
workspace:

| Permanent Rule ID | Human-readable alias | Control |
|---|---|---|
| `R-VAL-01` | CORE-01 | Actual spend must not exceed BGT for the same Department Number + Account Number |
| `R-VAL-02` | CORE-02 | Every GED transaction must map to a valid Budget Department Number + Account Number |
| `R-VAL-03` | CORE-03 | Exact duplicate GED transactions must be flagged using every governed material field |
| `R-VAL-04` | CORE-04 | Required GED fields must be present and parseable |
| `R-VAL-05` | CORE-05 | Budget ATD must equal eligible summed GED Amount for the same Department Number + Account Number |

CORE-04 is limited to Department Number, Account Number, Fiscal Period, Journal
Number, Journal Date, and Amount on one GED transaction.

Budget financial formula/arithmetic validation is not hidden inside CORE-04. If
retained, it is a separately identified governed rule with its own version,
classification, active binding, results, evidence, tests, and history. Workbook
formula/cached-value safety remains part of source compatibility.

Protected changes require a Tested immutable successor, a reason, before/after
evidence, a requester, and a different Financial Control Approver. Prior
versions, Rule Sets, runs, results, approvals, and replay evidence remain
immutable.

### 3.2 Configurable rules

Release 1 includes the approved controlled evaluator family for Optional
Configurable control rules. Optional rules:

- follow the common versioned engine and result contract;
- can be created, tested, activated, bound, enabled, disabled, and retired only
  through the governed lifecycle;
- affect only future confirmed Rule Sets and runs;
- never overwrite historical results; and
- do not change the core-only Overall Review Status under the release-1 status
  policy.

Executable Informational/Advisory rules are **deferred**. Their future
classification and architecture may remain documented, but the released
product exposes no active Advisory rule, observation count, false execution
claim, or unsupported Advisory report section.

### 3.3 Source layouts and workbook safety

The only supported source contract is exact `SLV-001` under `WRL-001`:

- Budget worksheet `Original Budget`;
- Budget header row 1;
- Budget columns A:H, with Account Name in B, BGT in C, ATD in D, ETC in E, EAC
  in F, DELTA in G, and Notes in H;
- GED worksheet `GED`;
- GED header row 7;
- GED body beginning row 8;
- GED fields A:O;
- exact detail, total, separator, repeated-header, and Grand/Department Total
  classification;
- total rows retained as evidence but excluded from transaction and rule scopes;
  and
- malformed non-total GED rows retained for CORE-04 evaluation.

Worksheet-name compatibility alone is insufficient. The exact header, field,
row-boundary, metadata, formula/cached-value, safety, and resource profile must
pass.

Unsupported layouts fail safely with expected/observed evidence. No alias,
fuzzy, position-guessing, or permissive fallback is in scope.

### 3.4 Review and publication lifecycle

The release includes:

- review creation and reporting-period selection;
- Budget and GED upload/extraction;
- source fingerprint and metadata reconciliation;
- department and period mismatch gates;
- reviewed working values with original/current comparison;
- audited correction, reason, reversion, and confirmation;
- active Rule Set inspection and confirmation;
- deterministic validation;
- complete Rule Executions, Rule Results, Findings, evidence, and projections;
- one working generation and one explicit published generation;
- explicit Reviewer promotion of a successor with a reason;
- immutable prior published results;
- run-to-run comparison for rule/configuration reanalysis;
- Past Reviews and historical replay; and
- append-only, attributable, ordered, tamper-evident audit.

A successor reanalysis is Working — Unpublished until an authorized Reviewer
explicitly promotes it. It never silently replaces the trusted published run.

### 3.5 Results and evidence

Release 1 includes the simplified five-section financial-review experience:

- Overview;
- Financial Analysis;
- GED Detail;
- Findings; and
- Review Summary/Leadership Summary.

Findings remain the primary exception-review experience. Every Finding provides
deterministic Explain This/Show Evidence access to:

- rule, version, Rule Set, and Validation Run;
- why the result occurred;
- expected and actual values;
- calculation basis and variance/exposure;
- affected Budget and GED records;
- exact file, worksheet, row, and relevant fields/cells;
- contributing transactions; and
- non-binding human follow-up phrased as review, verify, investigate, confirm,
  or consider.

Charts, summaries, reports, exports, and Ask Fin consume recorded engine results
and recorded projections. They do not independently recalculate financial
truth.

### 3.6 Leadership Summary, PDF, and XLSX

Release 1 includes a deterministic one-page Leadership Summary and three PDF
detail choices:

1. Leadership Summary Only;
2. Standard Financial Review; and
3. Complete Evidence Report.

**Standard Financial Review is the candidate default.**

Before generation, FinSight displays and requires confirmation of Review,
reporting period, Review Version, Validation Run, Rule Set, publication state,
included sections, detail level, and generated-by actor.

The PDF includes the Section 15 content appropriate to the selected detail
level. Complete Evidence includes full supported GED and audit evidence,
paginated or placed in appendices as necessary. Required content is never
silently omitted. Every explicit exclusion is disclosed in the report.

The XLSX evidence workbook includes separate sheets for:

1. Review Overview;
2. Leadership Summary;
3. Budget Data;
4. GED Data;
5. Budget vs GED;
6. Account Analysis;
7. Vendor Analysis;
8. Department Analysis;
9. Rule Results;
10. Findings;
11. Evidence;
12. Rule Set;
13. Audit History;
14. Source Files; and
15. Report Metadata.

The release baseline follows the complete fifteen-sheet list above.

PDF and XLSX:

- bind one exact selected Review Version and Validation Run;
- show Working Draft, Published Review, Historical Review, or Superseded Review;
- include application/review/run/rule-set/rule-version identity;
- include source fingerprints, generated actor/time, and integrity hash;
- use only persisted authoritative values and projections;
- include no authoritative recalculating formulas;
- carry an export audit event; and
- meet the approved accessibility and confidentiality requirements.

### 3.7 Confidentiality and export label

All Budget, GED, vendor, account, transaction, Finding, evidence, audit, Ask Fin,
report, and export content is confidential enterprise financial information.

Every PDF and XLSX displays the nonempty default:

> Confidential — Internal Financial Review

An authorized organization administrator may configure a stronger approved
label through a versioned policy. Ordinary users cannot remove, blank, or weaken
the label at export time. The exact label and policy version are recorded with
each export and remain unchanged historically.

Export generation uses protected temporary storage, automatic cleanup,
least-privilege permissions, destination warnings, and no confidential ordinary
logs, crash data, or support bundles.

### 3.8 Backup, restore, retention, and disposal

Release 1 includes complete encrypted governed backup and replacement-machine
restore for:

- review and candidate metadata;
- source bindings and fingerprints;
- correction/confirmation basis;
- generations and working/published pointers;
- promotion/supersession;
- immutable rule/configuration/baseline/Rule Set versions;
- runs, Rule Executions, Rule Results, Findings, evidence, and comparisons;
- retained reports and spreadsheet exports;
- audit and authorization history; and
- policy-permitted Ask Fin history.

The backup excludes source workbook bytes and complete normalized, Working, or
Verified row stores under the approved minimization contract.

Restore verifies identity, integrity, ordering, relationships, publication
state, audit continuity, and replay. Missing source files leave stored results
viewable but make row reconstruction explicitly unavailable.

Retention is controlled by an administrator-approved, versioned organization
policy. Until such a schedule is approved, FinSight performs no automatic
age-based deletion. Ordinary users cannot shorten retention or edit/delete
audit history.

Governed whole-scope disposal remains separately authorized and prevents
FinSight-managed backup/recovery paths from restoring disposed content.
External copies outside FinSight control are disclosed and governed by
organization policy.

### 3.9 Ask Fin

Ask Fin is in scope and automatically available when the approved managed local
runtime/model is healthy.

Ask Fin:

- uses only the selected review/run and approved help documentation;
- uses local loopback only;
- has no cloud fallback, internet retrieval, public API, external embeddings, or
  unapproved files;
- treats workbook text as untrusted data;
- verifies exact runtime/model identity before every prompt;
- returns only allowlisted structured claims backed by exact navigable FinSight
  citations;
- fails closed before display when a claim, value, citation, scope, decision
  boundary, or audit persistence check fails;
- keeps reviews isolated;
- refuses financial decisions and governed mutations;
- cannot create values, Rule Results, Findings, status, publication, or actions;
  and
- remains non-blocking when unavailable.

The unavailable state contains one clear message and Retry. There is no ordinary
user workflow for approving local model identity, installing Ollama, choosing
an endpoint/digest, downloading a model, or starting a daemon.

### 3.10 Windows platform and distribution

The supported candidate platform is:

- x86-64 Windows 11 Enterprise 24H2 and 25H2;
- 8 GB RAM minimum class;
- 16 GB RAM standard class;
- CPU-only operation required;
- no required GPU;
- enterprise/admin installation; and
- standard-user runtime.

The release uses:

- one Python/PySide6 codebase with a headless deterministic core;
- a PyInstaller one-directory application;
- a WiX Toolset v4 per-machine MSI or an equivalently approved governed
  implementation of that architecture;
- Authenticode-signed and timestamped executable content and installer;
- pinned deterministic build inputs;
- SBOM, third-party notices, checksums, build manifest, provenance, malware
  scan, vulnerability scan, and exact source/runtime/model versions; and
- install, launch, same-version repair, upgrade, failed-upgrade rollback,
  reinstall, uninstall, retained-data, removed-data, and replacement-machine
  restore qualification.

No installer-time network download, self-updater, telemetry, or implicit network
dependency is in scope.

### 3.11 Local-AI provisioning

The candidate release uses a FinSight-owned local-AI topology:

- the offline governed distribution provisions the exact approved runtime and
  model without user action;
- runtime binary, model identity, profile, and digest are administrator
  controlled and recorded;
- the service is restricted to loopback and deployment policy blocks
  non-loopback egress;
- startup, health, readiness, cancellation, timeout, queueing, response size,
  concurrency, memory, repair, update, rollback, and uninstall are controlled;
- the application opens without Terminal or manual service startup; and
- licensing/redistribution approval and required notices are release blockers.

A coordinated enterprise-managed topology is not the candidate manager
distribution. It may be introduced later only through a governed architecture
and qualification decision that preserves the same zero-user-action and
local-only outcome.

### 3.12 Accessibility and reliability

Release 1 includes qualification at:

- 100%, 125%, 150%, and 200% scale;
- approved desktop sizes;
- keyboard-only operation;
- visible focus and focus restoration;
- Light, Dark, and System modes;
- high contrast;
- NVDA or the approved native Windows screen reader;
- long text, vendor names, evidence lists, and unavailable/loading states; and
- 8 GB and 16 GB supported hardware.

No order-dependent UI test, critical clipping, inaccessible report, unsupported
status-by-color-only presentation, or known material keyboard defect may remain.

### 3.13 macOS disposition

macOS production distribution is deferred from release 1.

The headless deterministic core, rule contracts, fixtures, and independent
financial oracle remain platform-neutral and may retain development regression
coverage where practical. FinSight makes no macOS installation, accessibility,
support, signing, packaging, local-AI provisioning, or production-readiness
claim for release 1.

## 4. Explicitly out of scope or deferred

The candidate release excludes:

- executable Informational/Advisory rules;
- Budget/GED layouts beyond exact `SLV-001`/`WRL-001`;
- permissive reader aliases or structure guessing;
- invoices, purchase orders, statements of work, rate cards, contracts,
  resources, projects, and other source types;
- forecasting, what-if analysis, payment decisions, approvals, rejection,
  budget decisions, or autonomous actions;
- BI-style analytics not required to find, explain, evidence, or review the
  supported financial issues;
- cloud AI, public AI APIs, internet retrieval, unapproved private providers, or
  cloud fallback;
- user-managed Ollama/model setup;
- macOS production packaging and support;
- Windows versions, architectures, and hardware outside the approved matrix;
- tracker workbook export;
- rule-change comparison export;
- final manager download before every governed stage, independent review,
  hands-on approval, and release-authorization gate passes; and
- real-data pilot use before the pilot blockers in the production-readiness
  program are closed.

## 5. Conditions that remain release blockers

Approval of this scope does not mean the product is ready. At minimum, later
stages must close:

- financial-rule identity, CORE-04, period, duplicate, status/RAG, and oracle
  defects;
- lifecycle publication, persistence ordering, legacy-path, and architecture
  defects;
- all regression and accessibility failures;
- report, export, audit appendix, backup, restore, retention, and disposal
  implementation;
- Ask Fin adversarial, identity, network, resource, privacy, and retention
  controls;
- runtime/model licensing and redistribution;
- Windows executable/MSI, signatures, SBOM, scans, provenance, first-run,
  upgrade, repair, rollback, uninstall, and recovery;
- clean-machine, offline, standard-user, two-user, performance, accessibility,
  network, corruption, and installer-lifecycle qualification;
- full regression twice against the same immutable signed candidate;
- independent specialist PASS decisions;
- Product Owner hands-on acceptance; and
- final release authority GO.

## 6. Change control

Once approved, this freeze changes only through an attributable governed
decision that:

1. identifies the affected S1 decision and requirement/ADR;
2. records requester, approver, reason, before/after text, impact, and effective
   version;
3. preserves the prior freeze for historical evidence;
4. updates traceability, tests, plans, and migration requirements;
5. receives Financial Control approval for protected financial behavior;
6. receives the applicable Security, Privacy, Data Governance, Architecture,
   Accessibility, Reporting, or Release approval; and
7. does not silently reinterpret an implementation defect as a scope change.

## 7. Approval record

| Field | Recorded value |
|---|---|
| Freeze status | **Pending Product Owner approval** |
| Effective | **No** |
| Approved decision-register version/hash |  |
| Product Owner name / Actor ID |  |
| Product Owner approval timestamp |  |
| Financial Control Approver |  |
| Financial Control approval timestamp |  |
| Security/Data Governance approval reference |  |
| Architecture/Release approval reference |  |
| Independent Stage 01 review reference |  |
| Conditions |  |
| Effective baseline version |  |

Until every required approval is recorded, this document remains a candidate,
Stage 01 remains open, and Stage 02 is not authorized.
