# FinSight Configurable Rule Engine V2 — UX/UI Design

- **Status:** Draft — architecture review and explicit Project Owner approval required
- **Date:** 2026-07-27
- **Initiative:** Configurable Rule Engine V2
- **Product boundary:** One FinSight product, repository, and desktop application
- **Implementation authority:** None. This document does not authorize application implementation.

## 1. Purpose and authority

This document defines the V2 user experience and interface contract for:

- the eleven-step Budget/GED financial-review workflow;
- the first post-validation Review Summary;
- review-local data correction and three-value provenance;
- configurable-rule authoring, testing, activation, binding, and retirement;
- two-person governance of the five protected baseline rules;
- findings, Rule Results, analytics, reports, exports, audit, and Ask Fin;
- the seven-state Review Status lifecycle; and
- role-aware, accessible Windows desktop interaction.

It is a V2 delta to the approved root [UX design](../../../specs/07-ux-design.md) and [UI design system](../../../specs/08-ui-design-system.md), not a replacement product. The root visual tokens, calm finance-grade presentation, accessibility rules, and guided-review identity remain in force. Where the root UX uses an eight-step sequence or assumes a single user, this document supersedes those details with WF-01 through WF-11 and the approved three-role model.

The binding sources are:

- [V2 functional requirements](../specs/01-functional-requirements.md);
- [V2 non-functional requirements](../specs/02-non-functional-requirements.md);
- [approved financial-review workflow](FINANCIAL-REVIEW-WORKFLOW.md);
- [V2 constitution](../specs/constitution.md); and
- the root approved FinSight specifications and ADRs except where an explicit V2 artifact supersedes them.

## 2. Experience outcome

FinSight remains a guided financial-review assistant. It does not become a generic rule-builder, spreadsheet editor, or analytics portal.

The Reviewer should always be able to answer:

1. Which department, period, review, and version am I viewing?
2. Am I viewing original source evidence, a pending reviewed value, or the value validation used?
3. Which workflow step and Review Status am I in?
4. Is this result working, published, or historical?
5. Which immutable rule and evidence produced this conclusion?
6. What is blocked, why is it blocked, and what can I do next?

The Rule Administrator should always be able to answer:

1. Which rule version am I editing or inspecting?
2. Is it Core Mandatory, Optional Configurable, or Informational/Advisory?
3. Which lifecycle state and workspace bindings apply?
4. Which positive, negative, and boundary tests ran?
5. Does the next action require independent approval?

The Financial Control Approver should always be able to answer:

1. Who requested the protected change?
2. What exact Tested candidate is being considered?
3. What changes before and after?
4. Which tests and evidence support the request?
5. Can I approve this request without violating separation of duties?

## 3. Binding UX principles

| ID | Principle | UX consequence |
|---|---|---|
| V2-UX-01 | Guided review remains the product spine | The Reviewer advances through WF-01–WF-11 with one clear next action and visible prerequisites. |
| V2-UX-02 | Engine results are the single validation truth | Summary cards, findings, analytics, reports, exports, and Ask Fin link to persisted Rule Executions and Rule Results; none calculates a competing result. |
| V2-UX-03 | Identity is always visible | Department, period, Review Version, Run ID, Rule Set Version, publication state, and source filenames stay available in context. |
| V2-UX-04 | Original, reviewed, and validation values never blur | Every editable financial field has an explicit three-value presentation and complete edit/reversion history. |
| V2-UX-05 | Working never impersonates published | Working results carry a persistent `Working — Unpublished` banner and name the still-published version. |
| V2-UX-06 | No false “all clear” | `NOT_EVALUATED`, blocked scope enumeration, missing inputs, and incomplete ledgers are prominent and cannot render as PASS or Healthy. |
| V2-UX-07 | Governance is visible and attributable | Rule lifecycle, requests, approvals, denials, activation, bindings, and role checks expose actor and time evidence. |
| V2-UX-08 | Protected controls require deliberate separation | Request and approval are separate interactions; self-approval is unavailable and denied even for a multi-role actor. |
| V2-UX-09 | AI explains only selected engine evidence | Ask Fin is optional, private-provider-gated, generation-bound, cited, and visibly non-authoritative. |
| V2-UX-10 | Department-neutral by construction | No screen, workflow, label, rule, or empty state assumes Application Engineering or any other named department. |
| V2-UX-11 | Accessible by default | Meaning never depends on color; all workflows are keyboard and screen-reader operable and survive text scaling/high contrast. |
| V2-UX-12 | Destructive actions are separate and explicit | Whole-scope disposal is never presented as ordinary edit, archive, uninstall, or cleanup. |

## 4. Roles, identity, and authorization presentation

### 4.1 MVP roles

| Role | Primary surfaces | Explicitly absent authority |
|---|---|---|
| Reviewer | Reviews, source intake, extracted-data review, corrections/reversions, validation, summary, findings, analytics, reports, exports, Ask Fin, close/archive, governed disposal | Cannot administer rules or approve protected changes unless separately assigned another role |
| Rule Administrator | Rule Library, rule-version editor, test workbench, optional/advisory activation and bindings, protected change requests, baseline-upgrade requests | Cannot make financial approval decisions or approve a protected request |
| Financial Control Approver | Protected Change Queue, before/after comparison, approval/rejection, protected-baseline upgrade authorization | Cannot review financial data unless separately assigned Reviewer |

Active role grants combine, but explicit separation-of-duties denial wins. The UI must not imply that a person with all three roles can approve their own request.

### 4.2 Actor identity

The application shell displays the resolved actor’s domain-qualified Windows account and effective roles. Stable Actor ID remains available in the identity detail, audit, and governance evidence. The Windows security identifier is the MVP identity key; display-name equality is never used for authorization.

If stable identity resolution fails:

- no review, rule, request, result, audit, or derived-record data is disclosed;
- all state-changing controls are unavailable;
- a blocking identity message explains the impact and the organization support path; and
- only non-sensitive product help and shell information remain accessible.

Role assignment is not editable in the MVP application. A read-only Roles & Access view may show effective assignments, source version, validity interval, and who assigned them without offering a self-service grant action.

### 4.3 Authorization feedback

Authorization is checked before sensitive content is loaded and again when a privileged action is committed. A denial states:

- the requested action;
- the permission or separation-of-duties condition that failed;
- that no state changed;
- the actor and correlation reference recorded for the attempt; and
- the appropriate role or administrative path, without revealing unauthorized data.

## 5. Information architecture

```text
FinSight
├── Home
│   ├── Create New Review
│   └── View Past Reviews
├── Review Workspace
│   ├── WF-01 through WF-11 guided review
│   ├── Review Summary
│   ├── Findings
│   ├── Rule Results
│   ├── Analytics
│   ├── Reports
│   └── Ask Fin
├── Rule Library
│   ├── Catalog and versions
│   ├── Rule builder
│   ├── Test workbench
│   └── Workspace bindings
├── Governance
│   ├── Protected Change Queue
│   ├── Protected Baseline Versions
│   └── Workspace Baseline Upgrades
├── Audit
├── Settings
│   ├── Identity and effective roles
│   ├── Approved private AI provider selection
│   ├── AI privacy, masking, and consent
│   └── Accessibility preferences
└── Help
```

The navigation is permission-aware:

- users see destinations for which they have at least one read permission;
- disabled workflow actions remain visible when seeing the prerequisite helps the user;
- unauthorized datasets and governance evidence are not represented by enticing-but-denied previews;
- a dual-role user sees a union of destinations, but protected approval remains subject to distinct-actor denial.

## 6. The eleven-step guided review

The in-review header shows `Step X of 11`, the Review ID, selected period, Review Status, publication context, and a compact department identity. On narrower windows, the full stepper becomes a current-step label plus accessible progress list; it does not wrap into an unreadable strip.

| Step | Workflow | Primary user goal | Primary action or gate | Review Status effect |
|---|---|---|---|---|
| 1 | Welcome and review selection | Start or resume the correct review | Create New Review or open a retained review | New candidate is not created until the create action succeeds |
| 2 | Reporting-period selection | Choose one month and year | Continue after both are present | Prospective `Draft` intake state; still volatile |
| 3 | Budget and GED upload | Bind exactly one Budget and one GED source | Continue after both pass safety, compatibility, and extraction processing | Atomically persist `Draft` then `Data Uploaded`; failed intake leaves no authoritative review |
| 4 | Metadata and workspace identity | Verify department, period, filenames, structure, and counts | Continue only when department/period/structure gates pass | Remains `Data Uploaded` |
| 5 | Extracted-data review | Inspect Budget and GED Working Dataset views | Review, search, edit, revert, and inspect source | Remains `Data Uploaded` |
| 6 | Edit confirmation and audit | Confirm the exact correction basis | Use the required affirmation when edits exist; confirm reviewed data when none exist | Candidate is consumed; Review Version is created at `Data Reviewed` |
| 7 | Deterministic validation | Run the selected immutable Rule Set | Start Validation; optional safe cancel before atomic completion | `Data Reviewed` → `Validation Complete` only after complete ledger and Review Summary commit |
| 8 | Review Summary and results | Understand overall financial health first | Review Summary, then drill into evidence; explicitly mark reviewed | `Validation Complete` → `Reviewed`; successor promotion may be part of this action |
| 9 | Analytics and reporting | Explore and generate self-identifying outputs | Open analytics; generate PDF/spreadsheet-compatible output | No Review Status change; first completed report/export advances analytical state to `EXPORTED` |
| 10 | Ask Fin | Ask cited questions about one selected run | Ask when an approved private provider exists; otherwise continue | Optional and never blocks completion |
| 11 | Completion and history | Deliberately complete or archive the review | Complete Review; later Archive | `Reviewed` → `Closed` → `Archived` |

The Review Status is never used as a financial assessment. It remains visually and semantically distinct from:

- Overall Review Status: `Healthy`, `Attention Required`, or `Incomplete`;
- RAG label: `On Track`, `Needs Attention`, or `At Risk`;
- publication state: working, published, historical, or superseded;
- analytical state; and
- ReviewCycle disposition: `Active` or `Abandoned`.

Analytical state is shown in history/detail, not used as the main guided-workflow label. Fresh confirmation creates `VERIFIED`; reanalysis shows `Verified basis inherited from <generation>` and never presents its initiator as a new verifier. Successful validation atomically advances through `ANALYZED` to `SUMMARIZED`; the first eligible completed PDF report or XLSX export advances to `EXPORTED`. A migrated snapshot is labeled `Legacy state — transition history incomplete`. Failed/blocked generation, Ask Fin output, viewing, and later regeneration do not change that state. Publication remains a separate explicit concept.

## 7. Screen and surface inventory

| ID | Surface | Responsibility | Primary evidence/actions |
|---|---|---|---|
| V2-S01 | Home | Create or find reviews | Create New Review; conditionally enabled View Past Reviews; recent active reviews |
| V2-S02 | Period | Establish user-selected period | Month, year, duplicate-review warning |
| V2-S03 | Source Intake | Bind and process two required reports | Budget/GED slots, fingerprints, file roles, compatibility/extraction status |
| V2-S04 | Workspace Identity | Present pre-validation metadata | Department, selected/extracted periods, source names, counts, mismatches, lineage |
| V2-S05 | Budget Review | Inspect and edit reconstructed Budget data | Search/filter/sort, three-value inspector, source trace, correction/revert |
| V2-S06 | GED Review | Inspect and edit reconstructed GED transactions | Same controls, optimized for large tables and required-field exceptions |
| V2-S07 | Confirmation & Audit | Confirm exact review-local basis | Edit diff, audit preview, affirmation, confirmation |
| V2-S08 | Validation Progress | Show deterministic execution safely | Rule/order progress, expected/evaluated scopes, completed/not-evaluated counts, cancel state |
| V2-S09 | Review Summary | First post-validation executive view | Full identity block, Overall/RAG, health cards, rule counts, top findings, actions |
| V2-S10 | Findings | Triage control failures | Severity/rule/department/account filters, evidence, follow-up, lifecycle |
| V2-S11 | Rule Results | Display the complete ledger | Every Rule Execution and Rule Result, including PASS and NOT_EVALUATED |
| V2-S12 | Analytics | Visualize persisted result projections | Budget/actual, variance, completeness, reconciliation, findings by rule/severity |
| V2-S13 | Reports & Exports | Create append-only Derived Records | Printable summary, PDF, spreadsheet-compatible outputs, identity manifest |
| V2-S14 | Ask Fin | Explain one exact selected run | Context identity, cited Claim Records, sources, provider status |
| V2-S15 | Past Reviews | Find retained candidates and versions | Seven-status filters, candidate/working/published/historical label, Active/Abandoned |
| V2-S16 | Review History | Reconstruct lifecycle and evidence | Timeline, version/run/rule-set links, recovery state, derived records |
| V2-S17 | Rule Library | Manage versioned deterministic rules | Classification, lifecycle, versions, tests, bindings, audit |
| V2-S18 | Rule Builder | Author constrained non-executable definitions | Allowlisted evaluator, typed operands, scope, evidence template, severity, follow-up |
| V2-S19 | Rule Test Workbench | Prove rule behavior before Tested | Positive, negative, boundary cases; deterministic expected/actual diff |
| V2-S20 | Protected Change Queue | Enforce two-person governance | Request, exact Tested version, before/after, tests, requester, approve/reject |
| V2-S21 | Audit | Search attributable history | Actor, source, time, action, object/version, outcome, correlation ID |
| V2-S22 | Governed Disposal | Remove one complete authorized scope | Scope preview, managed-backup impact, explicit confirmation, terminal outcome |
| V2-S23 | Identity Failure | Fail closed without leaking data | Resolution problem, non-sensitive help, exit/retry |
| V2-S24 | AI Privacy & Consent | Control external AI disclosure | Approved-provider selection, masking state, consent scope/history, revoke |
| V2-S25 | Backup & Restore | Create or admit a complete managed recovery set | Backup plus current registry-continuity state, replacement-machine recovery, revocation/rollback checks |

## 8. Source intake and metadata behavior

### 8.1 Two-source intake

Only Budget Report and GED Report upload slots appear in the V2 MVP. Each slot shows:

- selected filename and assigned role;
- source fingerprint;
- selecting actor and time;
- workbook sheet/header/layout compatibility;
- extraction progress and result;
- department and period evidence when available;
- detected structural issues with source location; and
- replace/remove behavior before confirmation.

FinSight must say that source files are read-only references and are not copied into the application database. A moved source can later be rebound only when its bytes match the retained fingerprint.

### 8.2 Metadata summary

The metadata summary shows selected values and extracted evidence side by side. It never fills an absent Department Name, period, or structural value with sample data.

Blocking mismatches use an evidence comparison:

| Check | Left evidence | Right evidence | Outcome |
|---|---|---|---|
| Department | Budget report-level number and source cell | GED department-total number and source cell | Match or blocking conflict |
| Period | User-selected month/year | GED approved period evidence; Budget workspace-assigned/no-source-period marker | Match or blocking conflict |
| Structure | Expected `SLV-001` contract | Observed sheet/header/boundary/row classification | Compatible or exact blocking issues |

A different Department Number on an individual GED transaction does not change report metadata; it remains transaction input for CORE-02.

## 9. Working-data review and three-value editing

### 9.1 Grid behavior

Budget and GED have separate, virtualized tables. The default columns match the supplied report structures and retain source order. Search, filters, and sorting alter only presentation, never row identity or stored evidence.

Every editable cell opens a field inspector with:

| Label | Meaning |
|---|---|
| Original Extracted Value | Immutable normalized value reconstructed from the source cell, with raw-cell lineage |
| User-Reviewed Value | Latest review-local replacement, labeled `Not set`, `Pending confirmation`, or `Confirmed` |
| Current Validation Value | `Unavailable — confirmation required` for a mutable candidate; after confirmation, the reviewed value when present or the original value |

The inspector also shows source file, worksheet, row/cell reference, extractor version, correction event, actor, timestamp, reason/comment, and linked reversion.

### 9.2 Edit behavior

- Any extracted business field may be edited, including identifiers, dates, descriptions, BGT, ATD, ETC, EAC, DELTA, Invoice Amount, and GED Amount.
- Source bytes, source fingerprints, row identity, and lineage are not editable.
- Saving a change creates a correction event; it does not mutate the workbook or overwrite the original value.
- Revert creates a linked reversion event; it does not erase prior history.
- Unsaved and saved-pending edits are visually distinct.
- Validation remains unavailable while any edit or source basis is unconfirmed.

When edits exist, the exact confirmation text is:

> I confirm that I have reviewed these edits. I understand that all changes will be recorded in the audit history and that validation results will be based on the edited values.

The user can inspect the complete edit diff and audit projection before confirming. With no edits, the user confirms the extracted data without artificial correction events.

## 10. Validation progress and completion

The validation screen displays:

- selected Review Version and Rule Set Version;
- initiating actor and start time;
- total selected rules;
- current stable execution position;
- expected and evaluated scope counts;
- rules completed;
- rules not evaluated;
- records evaluated; and
- plain-language processing state.

The UI thread remains responsive. Starting validation immediately displays the stable Validation Run ID. Before the atomic completion boundary, Cancel requests a safe cancellation and explains that the Run ID and attempt history will remain, no partial financial results will be retained, and the same run can be retried. During the final atomic commit, the primary state becomes `Finishing safely`; the application does not imply that interruption can partially cancel a commit.

Only a complete persisted Rule Result ledger and its Rule Executions advances the Review Status to `Validation Complete`. A failed or cancelled attempt returns to a retryable state under the same Run ID without showing partial results as authoritative.

## 11. Review Summary — first post-validation landing page

### 11.1 Persistent identity block

The top of the Review Summary displays, without opening a drawer:

- Department Name;
- Department Number;
- Reporting Period;
- Validation Run ID;
- Rule Set Version;
- Review Version;
- Review Lifecycle Status;
- Publication State;
- Budget and GED source filenames; and
- Validation Timestamp.

The same identity block appears in reports, exports, and the context detail for every review-specific Ask Fin response.

### 11.2 Summary hierarchy

The first viewport contains:

1. Overall Review Status and its one-to-one RAG label;
2. Budget Health, Data Quality, and Reconciliation Status;
3. Rules Executed, Passed, Failed, and Not Evaluated;
4. Budget Overruns, Duplicate Transactions, and Missing Required Data;
5. advisory observation counts;
6. Top Findings; and
7. Recommended Next Actions.

Each metric carries a `View source results` link to the persisted Rule Execution/Rule Result projection that produced it. Descriptive information is labeled `Descriptive` and cannot look like an engine conclusion.

### 11.3 Working, published, and historical context

For the default trusted summary, the published version is selected.

Immediately after a successor validation, its summary shows:

- a persistent `Working — Unpublished` banner;
- the working Review Version and Run ID;
- the still-published Review Version and a direct comparison/open action; and
- an explicit statement that trusted defaults have not changed.

Historical selection displays `Historical` with its immutable identity. No screen combines counts, findings, charts, or Ask Fin evidence from different generations.

### 11.4 Status semantics

| Engine-derived status | Accessible presentation |
|---|---|
| `Healthy` | `On Track` + success icon/shape + Green token |
| `Attention Required` | `Needs Attention` + warning icon/shape + Yellow token |
| `Incomplete` | `At Risk` + stop/error icon/shape + Red token |

`Incomplete` is not a pass and never uses a reassuring empty-state message. The summary names the `NOT_EVALUATED` dependencies and the next corrective action.

## 12. Findings, Rule Results, analytics, and reports

### 12.1 Findings

Findings contain only failed control Rule Results. Each row shows:

- severity with text, shape/icon, and color;
- stable Finding ID;
- Rule ID, name, immutable version, and classification;
- evaluation scope and affected department/account/transaction;
- what failed and why;
- calculation and comparison evidence;
- Original/User-Reviewed/Current values when a corrected field contributed;
- source references;
- recommended human follow-up; and
- finding-review status and history.

### 12.2 Rule Results

The Rule Results view is the complete ledger, not a failures-only list. It supports:

- Rule Execution roll-ups;
- scope-level PASS, FAIL, NOT_EVALUATED, OBSERVATION, and NO_OBSERVATION;
- expected-versus-persisted scope counts;
- selected rule/configuration/status-policy versions;
- blocking dependency evidence;
- stable deterministic order; and
- one-click source trace.

A disabled rule is shown in the applicable Rule Set manifest, not represented as an execution result.

### 12.3 Analytics

Analytics consume persisted engine records and labeled descriptive projections. Each chart/table exposes its selected Review Version and Run ID and has a non-visual tabular alternative. Required views include:

- budget versus actual by account;
- over-budget accounts and largest variances;
- findings by severity and rule;
- GED completeness;
- reconciliation status; and
- validation-run summary.

### 12.4 Reports and exports

The first release provides:

- printable Review Summary;
- PDF report;
- spreadsheet-compatible Findings export;
- spreadsheet-compatible Rule Results export; and
- spreadsheet-compatible summarized-financial-data export.

Generation is an append-only Derived Record action. The progress/result view shows actor, selected run context, requested time, terminal outcome, created time, fingerprint, destination, creation-time publication/supersession label, and generation analytical state. The first successful PDF/XLSX completion moves a `SUMMARIZED` generation to `EXPORTED` without changing Review Status or publication, including when an authorized Closed, Archived, historical, or superseded context has no prior artifact. If promotion happened first, the artifact is labeled `Historical — Superseded`; it is not blocked merely because of supersession. Concurrent first exports may both complete but history shows one transition. Failed/blocked attempts for other causes and Ask Fin do not move state. Regeneration creates a new record, leaves `EXPORTED` unchanged, and never overwrites application history.

## 13. Rule Library and governance

### 13.1 Catalog

The catalog can be filtered by classification, Rule ID/name, lifecycle state, evaluator type, and workspace binding. Each row distinguishes:

- Rule Definition Version lifecycle: `Draft`, `Tested`, `Active`, or `Retired`;
- workspace binding: `Enabled` or `Disabled`;
- classification: Core Mandatory, Optional Configurable, or Informational/Advisory; and
- protected status and current Protected Baseline membership.

### 13.2 Constrained rule builder

The builder offers only architecture-approved evaluator families and typed configuration controls. It does not expose raw code, SQL, spreadsheet macros, scripts, unrestricted expressions, or plugin execution.

The definition review shows:

- rule identity, version, classification, purpose, and owner;
- declared evaluation grain and scope enumeration;
- typed field operands and comparison/aggregation;
- dependency behavior and NOT_EVALUATED policy;
- evidence template and source-reference requirements;
- fixed or deterministic severity policy;
- recommended human follow-up;
- configuration/status-policy version; and
- deterministic preview using approved test fixtures.

Only Draft may be edited. Editing Tested or Active starts a successor Draft and leaves the earlier version unchanged.

### 13.3 Test workbench

Before a version can become Tested, the workbench displays positive, negative, and boundary cases with:

- fixture/test ID and fingerprint;
- expected scopes and ordered results;
- expected and actual statuses/evidence;
- deterministic replay comparison;
- pass/fail outcome; and
- actor and timestamp.

`Advance to Tested` remains unavailable until all required tests pass. Tested is visibly immutable and does not imply Active.

### 13.4 Optional and advisory lifecycle

A Rule Administrator may activate a Tested Optional Configurable or Informational/Advisory version and manage workspace bindings. The confirmation explains:

- the affected workspace;
- whether a successor Rule Set Version will be created;
- that only future runs change; and
- that historical runs remain unchanged.

Delete is presented as `Retire version`; physical historical deletion is not offered.

### 13.5 Protected change workflow

A protected successor follows:

```text
Rule Administrator authors Draft
  → required tests pass
  → immutable Tested
  → submit Protected Change Request
  → Pending Approval
  → different Financial Control Approver approves or rejects
  → approved candidate activates at effective time
  → new Protected Baseline Version
```

The request view requires exact Tested candidate, requested action, reason, before/after definition, proposed effective time, binding effects, and test evidence.

The Approver view shows requester Actor ID/time, approver identity, a side-by-side semantic diff, all required test results, current and proposed baselines, and affected future behavior. Approve and Reject require an explicit reason. If requester and approver stable Actor IDs match, approval controls are unavailable and commit-time authorization denies the action.

A future-dated approval shows `Scheduled`, the approved effective time, local time-zone rendering plus UTC, scheduler registration health, and later the actual activation time. If a due activation was delayed because the machine was off, the store was locked, or scheduling failed, the next launch shows a blocking governance recovery state before new baseline-dependent work; it never presents the prior baseline as silently current.

Approval does not silently update existing workspaces. A separate workspace baseline-upgrade view requires Financial Control Approver authorization and shows the successor Rule Set Version and required new Review Version/run.

## 14. Past reviews, publication, and lifecycle

Past Reviews supports every Review Status:

- Draft;
- Data Uploaded;
- Data Reviewed;
- Validation Complete;
- Reviewed;
- Closed; and
- Archived.

Each row separately identifies:

- Working Candidate or Review Version;
- working, published, historical, or superseded context;
- latest valid analytical state and its triggering confirmation/run/report/export;
- Active or Abandoned ReviewCycle disposition;
- department and period;
- last actor/time; and
- reconstruction availability.

Closed and Archived versions open with their authoritative data read-only. Authorized report, export, Ask Fin, lifecycle, successor, and disposal commands remain separate append-only or governed actions; they never edit that sealed record set. Missing, moved, mismatched, or extractor-divergent source state is shown as a recovery condition without hiding retained runs, results, findings, audit, or Derived Records.

Promotion of a successor working generation is a deliberate Reviewer action with a reason. The comparison view makes the prior published and candidate working identities explicit. A failed or declined promotion leaves the published version unchanged.

### 14.1 Backup, restore, and disposal continuity

Backup presents one FinSight-managed recovery set: the encrypted backup package plus its managed root's current signed recovery-control continuity state. The user sees Backup ID, registry lineage/version, creation time, recovery profile, authoritative `Active`/`Retired`/`Revoked` state, managed/external-copy classification, and replacement-machine readiness without exposing financial content or keys.

Replacement-machine restore requires a selected package and the current continuity capsule from the same custody-controlled managed recovery root. Before decrypting review content, the UI reports package/capsule lineage, admission status, and any `FS-BAK`/`FS-DSP` reason. Missing, stale, rolled-back, tampered, revoked, or unresolved-prepared continuity fails closed; the UI never offers “restore anyway.” Help states that an independently copied stale package/capsule pair is an external copy and that the offline MVP can prove currentness only for artifacts still under FinSight-managed-root custody.

After admission on an empty replacement machine, progress shows `Adopting signed recovery checkpoint` while FinSight anchors the protected local registry segment and appends its recovery-adoption successor. There is no option to create a fresh lineage, reset sequence, or bypass an interrupted adoption; restart returns to the blocking recovery surface until that idempotent step is reconciled.

Governed Disposal shows affected active reviews, Derived Records, managed Backup IDs, provider envelopes, and the external-copy limitation before separate confirmation. During execution it shows non-sensitive `Preparing revocation`, `Rebuilding retained data`, `Reconciling managed copies`, and `Committed` states. After a crash, an unresolved prepared operation opens a blocking recovery surface; result access and restore remain unavailable until FinSight proves safe abort or completes the operation. Default uninstall is clearly labeled as retaining the registry and data. `Remove all FinSight data` discloses that the minimal content-free registry, protected registry-key envelope, and current continuity capsule remain solely to prevent old managed recovery from returning; only administrator device decommission removes that final residue.

## 15. Ask Fin

Ask Fin is downstream of a complete Validation Run and uses the published run by default. An explicitly selected working run displays `Working — Unpublished`; a past run displays `Historical`.

Before each review-specific response, the context panel identifies one:

- Review Version;
- Validation Run ID;
- Rule Set Version;
- publication state;
- department and period; and
- approved private provider profile.

For an organization-private external provider, the same panel shows the exact data categories/payload preview, masking state, privacy and retention implications, and active-consent status. If no matching active consent exists, Ask Fin presents an unselected explicit consent action; declining leaves the request unsent. Every transmission references the logged consent. Revoking consent in Settings blocks subsequent external requests immediately. Consent never permits a public or otherwise unapproved provider. An on-device provider is labeled `On device — no external transmission`.

The response:

- is visibly labeled AI-generated;
- contains only verified Claim Records or an explicit unsupported label;
- cites exact Rule Execution, Rule Result, Finding, field, and source-evidence IDs;
- distinguishes Original, User-Reviewed, and Current values;
- never mixes generations;
- never creates a finding, status, recommendation to approve financial activity, or data/rule change; and
- is unavailable when no on-device or organization-approved private provider is configured.

Product help remains available without validation evidence, but it is labeled separately and cannot make review-specific financial claims.

## 16. Errors, empty states, and recovery

Every actionable error contains:

1. a stable category/code;
2. what failed;
3. impact on the review or action;
4. the exact next step;
5. whether any state changed; and
6. a correlation ID suitable for privacy-safe support.

The version-1 category prefixes are:

- `FS-IDN` — identity resolution;
- `FS-AUT` — authorization or separation of duties;
- `FS-SRC` — source access or fingerprint;
- `FS-WRK` — workbook safety or resource limit;
- `FS-STR` — workbook structure;
- `FS-MET` — department or period metadata;
- `FS-REC` — source/extractor/correction reconstruction;
- `FS-RUL` — rule definition, test, dependency, or lifecycle;
- `FS-GOV` — protected-rule governance;
- `FS-RUN` — validation invocation/execution;
- `FS-LED` — atomic ledger persistence;
- `FS-LIF` — review lifecycle;
- `FS-PUB` — publication or promotion;
- `FS-DRV` — report/export/Derived Record generation;
- `FS-AI` — provider, corpus, citation, or claim verification;
- `FS-BAK` — backup or restore;
- `FS-DSP` — governed disposal; and
- `FS-SYS` — runtime, package, lock, or migration health.

Error views never expose workbook values, paths, credentials, prompts, or sensitive row content in diagnostic payloads by default.

Required empty states include:

- no past reviews: disabled action plus explanation;
- no findings: state exactly which rules/scopes ran and whether any were NOT_EVALUATED;
- no optional rules: explain that the five protected baseline controls still run;
- no pending approvals: neutral queue state;
- no approved AI provider: deterministic product remains complete;
- source unavailable for reconstruction: retained evidence remains viewable; and
- no advisory observations: not presented as a control PASS.

## 17. Visual system

The approved root FinSight UI tokens remain the baseline:

- light-first neutral workspace;
- restrained Trust Blue primary action;
- semantic success/warning/danger/info tokens;
- severity encoded with label, shape/icon, and color;
- system fonts with tabular numerals;
- 4px spacing grid;
- calm cards, tables, and drawers;
- reduced motion; and
- WCAG 2.2 AA minimum.

V2 changes the signature progress component from eight to eleven steps and adds these visual patterns:

- persistent review/run identity block;
- `Working — Unpublished`, `Published`, and `Historical` context banners;
- three-value field inspector;
- Rule Execution/Result ledger;
- lifecycle timeline for rule versions and reviews;
- protected-change before/after comparison;
- distinct `Review Status`, `Overall Review Status`, publication state, and disposition badges.

Application Engineering and Amerisure-specific labels are sample or deployment context only; the product experience is department-neutral and brand tokens remain replaceable.

## 18. Accessibility and interaction requirements

- All eleven workflow steps, data editing, rule authoring/testing, protected approval, reporting, and disposal are keyboard operable.
- A screen reader receives the current step, Review Status, publication context, and blockers after every transition.
- Data grids support accessible headers, row identity, cell editing, error association, and source/evidence navigation.
- Original/User-Reviewed/Current state is expressed in text, not only style.
- `PASS`, `FAIL`, `NOT_EVALUATED`, `OBSERVATION`, and `NO_OBSERVATION` are full text labels.
- Approve and Reject controls have distinct accessible names and confirmation content.
- Status, severity, RAG, and publication meaning use text plus icon/shape; color is supplemental.
- Focus returns to the invoking cell/row after closing editors, evidence drawers, or dialogs.
- At 200% text scaling, primary actions and identity information remain visible without page-level horizontal scrolling; tables may scroll inside their region.
- Long operations expose determinate or staged progress through accessible live regions without repeatedly announcing noisy row-level changes.
- Motion is unnecessary for meaning and respects reduced-motion preferences.
- High-contrast mode uses borders and labels rather than relying on tints or shadows.

## 19. Performance and large-data UX

- Budget and GED grids use virtualized/paged models; the application never constructs one visual widget per row.
- Sorting/filtering is cancellable and does not mutate source order or evidence.
- Validation and export run off the UI thread.
- Progress updates are throttled so rendering does not dominate engine execution.
- Evidence drawers load only the selected scope and nearby source context.
- The UI reports resource-limit rejection before expensive extraction whenever possible.
- Large result ledgers use stable server/model-side paging over the local data-access boundary while preserving deterministic order.
- The Review Summary becomes interactive only after its complete persisted run is available; no partial summary flashes as authoritative.

## 20. Cross-artifact contracts

This design consumes the shared Architecture contracts:

| Contract | UX/UI dependency |
|---|---|
| AC-01 — Source and reconstruction | Source intake, three-value presentation, evidence trace, recovery states |
| AC-02 — Identity, authorization, and audit | Actor display, role-aware actions, separation of duties, attributable events |
| AC-03 — Protected Baseline and Rule Set manifests | Rule catalog, baseline version, workspace bindings, summary identity |
| AC-04 — Engine invocation and result ledger | Validation progress, Rule Results, findings, summary, analytics |
| AC-05 — Lifecycle, rerun, and publication | Seven statuses, working/published/historical labels, promotion, replay |
| AC-06 — Consumers and Derived Records | Dashboard/report/export/Ask Fin identity and append-only generation |
| AC-07 — Retention, backup, and disposal | Past reviews, recovery, archive, whole-scope disposal |

## 21. Requirements traceability

| UX/UI area | Primary V2 requirements |
|---|---|
| Entry, period, two-file intake, metadata | FR-123–FR-135 |
| Working review, edits, confirmation, provenance | FR-136–FR-140, FR-191–FR-192, FR-203 |
| Rule classifications, protected baseline, lifecycle | FR-141–FR-151, FR-198–FR-199 |
| Validation, executions, result ledger, findings | FR-152–FR-164, FR-184 |
| Summary, analytics, reporting, Ask Fin | FR-165–FR-170, FR-185–FR-188, FR-193–FR-194, FR-200 |
| Versions, publication, replay, history | FR-171–FR-173, FR-195–FR-197, FR-202 |
| Windows delivery-visible behavior | FR-174–FR-179 |
| Source-layout and core-rule evidence | FR-180–FR-183; CORE-01–CORE-05 |
| Roles and actor identity | FR-189–FR-190; NFR-085, NFR-090, NFR-107–NFR-108 |
| Disposal | FR-201; NFR-101, NFR-102, NFR-105, NFR-109–NFR-110 |
| Accessibility and evidence-first explanation | NFR-092–NFR-093 |
| Performance, security, diagnostics | NFR-081, NFR-083–NFR-088, NFR-100, NFR-106 |
| Rule-engine uniformity and extension | NFR-084, NFR-089, NFR-097–NFR-099 |
| Private, engine-bound AI | NFR-103–NFR-104 |

## 22. Review and approval checklist

The single independent package-level Architecture review must examine this artifact through UX, accessibility, finance-workflow, security/privacy, rule-governance, and software-architecture lenses. It must confirm WF-01–WF-11; keyboard/screen-reader/high-contrast/dense-grid/200% behavior; metadata/correction/summary/publication language; fail-closed disclosure and disposal; rule lifecycle/two-person controls; AC-01 through AC-07; and the absence of UI-side validation logic.

Until that package review passes and the Project Owner explicitly approves the Architecture stage, this document remains Draft and application implementation remains blocked.
