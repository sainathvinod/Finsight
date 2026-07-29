# MVP Final Remediation Requirements Delta — 2026-07-28

- **Initiative:** FinSight Configurable Rule Engine V2
- **Increment:** Consolidated MVP UX, rules, evidence, analytics, appearance, and disposal remediation
- **Status:** Approved remediation scope; implementation verification pending
- **Authority:** Project Owner remediation direction dated 2026-07-28
- **Parent baseline:** Approved V2 Requirements and Architecture remain in force
- **Packaging:** Explicitly excluded until a later gate

## 1. Purpose and precedence

This delta records only decisions that materially change the current MVP presentation or workflow. It does not replace the deterministic rule engine, source readers, persistence model, audit model, identity boundary, or application shell.

Where this delta conflicts with the prior six-stage integrated-MVP presentation, this delta controls the remediation increment. Prior verification remains historical evidence for the state that existed before remediation and must not be relabeled as evidence for this increment.

## 2. Seven-step primary workflow

The visible review workflow is:

1. **Create**
2. **Upload**
3. **Verify Data**
4. **Review Rules**
5. **Validate**
6. **Review Results**
7. **Complete**

Welcome, Past Reviews, Settings, Ask Fin, and saved-review reopening are shell destinations rather than numbered financial-review steps.

Validation shall not begin until the Reviewer has:

- uploaded compatible Budget and GED reports;
- resolved department and reporting-period gates;
- reviewed and, where necessary, edited the review-local working copy;
- saved or cancelled all pending edits;
- affirmed that the Budget and GED data are ready for validation; and
- reviewed the exact immutable Rule Set Version that will execute.

## 3. User-experience requirements

### REM-FR-001 — Welcome hierarchy

The Welcome page shall center the primary hierarchy in the available workspace:

- `Welcome to FinSight`
- `Your personal financial review assistant`
- `Create a monthly review or return to saved work. FinSight keeps every review identifiable, attributable, and ready to continue after a restart.`;
- compact side-by-side **Create New Review** and **Open Past Review** actions; and
- a horizontally useful Recent Reviews section below.

The existing sidebar and top header remain. The page shall not resemble a narrow form or place the main welcome message as an ordinary upper-left page title.

### REM-FR-002 — Plain-language errors with optional diagnostics

Primary errors shall state what is wrong and what the user should do next. They shall not lead with internal codes, correlation IDs, state-transition internals, diagnostic taxonomy, impact headings, or repeated text.

Technical identifiers may be available through a secondary **View technical details** disclosure for authorized troubleshooting and audit use. The disclosure shall not duplicate the primary message and shall not expose workbook financial content that the actor is not authorized to view.

Required examples include:

- missing review period: `Please enter the required month and year.`
- period mismatch: `The GED reporting period does not match the selected review period. Select the correct file or update the review period.`
- department mismatch: `The Budget and GED reports belong to different departments. Please select matching reports.`

### REM-FR-003 — Business-first upload metadata

Primary Budget and GED cards shall show:

- file name;
- compatibility;
- extraction status;
- department name and number;
- reporting period;
- accepted record count; and
- Replace File and Remove File actions.

Raw SHA-256 values, internal actor identifiers, internal timestamps, and persistence terminology shall move to a secondary **File details** view. The fingerprint remains authoritative source evidence and audit data.

### REM-FR-004 — Resolved Budget department display

When Budget supplies a department number, GED supplies the matching department number and name, and the report-level department gate passes, FinSight shall display the confirmed department name consistently on both upload cards and the review context.

The Budget card shall distinguish resolved context from native Budget evidence where necessary. FinSight shall preserve the exact original evidence and shall never infer a name when report-level identifiers do not match.

## 4. Reviewed working-copy requirements

### REM-FR-005 — Editable Verify Data

Verify Data shall provide Budget Data and GED Data tabs with:

- search, filter, and sorting;
- explicit Edit Mode;
- Save Changes and Cancel Changes;
- individual reversion;
- Original Extracted Value versus User-Reviewed/Current Value comparison;
- Change History;
- source workbook, worksheet, row, and cell reference; and
- a non-color-only edited-value indicator.

Edits affect only the review-local working copy. Original workbook bytes shall never be modified.

### REM-FR-006 — Governed edit confirmation

Saving changes shall require a modal confirmation:

> **Save these changes?**
>
> Validation results will be calculated using the edited values. The original
> values will remain preserved, and all changes will be recorded in the audit
> history.

The modal shall contain this unchecked affirmation:

> I understand that validation will use these edited values.

Cancel shall make no working-copy change. Save Changes shall append attributable correction evidence retaining the original, prior, and new values, actor, and timestamp. The page shall display the approved audit-history note after save.

> Changes are recorded in the audit history with the original value, edited
> value, user, and timestamp.

Before leaving Verify Data, the Reviewer shall affirm:

> I have reviewed the Budget and GED data and confirm it is ready for validation.

## 5. Rules Repository requirements

### REM-FR-007 — Review Rules step

The Review Rules step shall identify the exact Rule Set Version that will execute and present these protected baseline definitions consistently across UI, engine manifest, tests, findings, analytics, and reports:

| Rule | Plain-language purpose |
|---|---|
| Budget-to-GED Reconciliation | Summed GED Amount must equal Budget ATD for each Department Number + Account Number. |
| Budget Overrun | Total GED actual spending must not exceed BGT for the same Department Number + Account Number. |
| Valid Account Coding | Every GED Department Number + Account Number combination must exist in the Budget report. |
| Complete and Correct Data | Required values must be present and parseable, and approved Budget EAC/DELTA calculations must be internally consistent. |
| Duplicate Transactions | Flag GED rows with the same approved duplicate fingerprint, including department, account, journal information, date, descriptions, and financial amount fields. |

For every rule, the user can inspect purpose, required fields, grouping/matching keys, severity, version, classification, lifecycle status, and approved parameters.

### REM-FR-008 — Optional-rule lifecycle

An authorized Rule Administrator can:

- add an optional Draft rule;
- edit a Draft by creating or replacing its unactivated working definition;
- test a Draft rule against an authorized review dataset;
- save an immutable new rule version;
- enable or disable an optional rule through a new Rule Set Version;
- retire or delete an optional rule only as permitted by the governed lifecycle; and
- request revalidation after a Rule Set Version changes.

Historical Rule Definition Versions, Rule Set Versions, Validation Runs, and findings remain reproducible.

### REM-FR-009 — Protected baseline governance

The five core rules shall display **Protected Core Rule** status. Ordinary Reviewer or Rule Administrator actions shall not delete, silently disable, replace, or semantically edit them.

Approved parameter changes shall create a governed version. Disablement, replacement, or semantic changes require the existing request/different-person approval process and preserve the prior version for replay.

### REM-FR-010 — Revalidation

When an authorized rule-set change occurs after validation:

- the previous run remains immutable;
- a successor Rule Set Version is created;
- validation creates a new run over the unchanged verified basis or a newly confirmed basis, as applicable; and
- users can compare previous and successor outcomes without mixing them.

## 6. Results, evidence, and data-quality requirements

### REM-FR-011 — Business-first result identity

Executive Overview shall prominently show Department Name, Department Number, Reporting Period, source filenames, validation timestamp, and Review Status.

Validation Run ID, Review Version, Rule Set Version, fingerprints, and other internal identifiers remain available under Review Details or Audit Details but shall not dominate the executive view. Every export, screenshot context, and Ask Fin explanation must still resolve to the exact persisted run.

### REM-FR-012 — Deterministic visual analytics

All charts consume sealed deterministic engine projections. A chart or UI consumer shall not independently sum financial data, calculate pass/fail, determine risk, or silently coerce missing amounts to zero.

Required visual projections are:

- Executive Overview: Budget versus GED/actual; findings by severity; rule PASS/FAIL/NOT_EVALUATED; budget utilization; over-budget versus within-budget accounts; reconciliation status.
- Budget Data: BGT, ATD, EAC where available, and remaining budget or overrun by account.
- GED Data: spend by account, spend by fiscal period where available, highest-spend accounts, and transaction counts by account.
- Budget vs GED Comparison: grouped BGT, Budget ATD, summed GED Amount, variance, over-budget amount, and reconciliation difference by Department Number + Account Number.

Each visual shall have labels, a text/status counterpart, and an accessible exact-data table alternative. Partial totals shall be explicitly labeled when missing or unparseable values prevent complete evaluation.

### REM-FR-013 — Rule-oriented Validation Results

Validation Results answers which rules ran and how they performed. Each rule row shall show:

- rule name and plain-language purpose;
- overall outcome;
- records evaluated, passed, failed, and not evaluated;
- number of findings;
- severity; and
- View Evidence.

Opening a rule reveals its scope evaluations and affected records. Failed or not-evaluated evidence includes department, account, workbook, worksheet, row/cell where applicable, Original and User-Reviewed/Current values, expected condition, actual condition, explanation, and recommended action.

### REM-FR-014 — Record-oriented Findings

Findings answers which exceptions require attention and shall not duplicate the rule roll-up table. Every finding includes:

- severity and rule;
- department and account;
- source workbook, worksheet, row, and cell;
- material record details;
- expected and actual values or conditions;
- Original/User-Reviewed/Current provenance;
- explanation and recommended action; and
- Open Source Evidence.

Duplicate evidence shows both records side by side. Reconciliation evidence shows Budget ATD with summed GED Amount and contributing records. Budget overrun evidence shows BGT, GED spend, overrun amount, and overrun percentage.

### REM-FR-015 — Data Quality & Coverage

Data Quality & Coverage summarizes dataset reliability rather than repeating findings. It shall show and link to affected records for:

- Budget detail rows;
- GED transaction rows;
- excluded subtotal, total, separator, and blank rows;
- missing required values;
- unparseable values;
- duplicate candidates;
- unmapped transactions;
- department mismatches;
- period mismatches;
- reconciliation scopes not evaluated; and
- counts of Original versus edited/current values.

### REM-FR-016 — Affected-row and cell navigation

Budget and GED tables shall show textual status, rule badges, severity, non-color-only affected-cell highlighting, an accessible description or details panel, and View Finding.

Evidence navigation shall select and focus the exact record/cell where available and preserve keyboard focus on return. When source reconstruction is unavailable, persisted evidence remains viewable and the unavailable raw-context action is plainly explained.

## 7. Review-disposal requirements

### REM-FR-017 — Governed whole-review disposal

An authorized user may request disposal of Draft, in-progress, completed, Closed, or Archived reviews from Past Reviews, Review Details, or Financial Review Results.

The confirmation dialog shall state:

> **Permanently delete this review?**
>
> This will permanently delete the review, its working data, edits, validation
> runs, findings, and audit history from this FinSight installation. This action
> cannot be undone.

It shall require either:

- `I understand this action cannot be undone`; or
- entry of the reporting period/review label.

Cancel shall perform no disposal. Confirm shall require `review.disposal.request`, re-resolve identity and authorization at commit, bind the confirmation to one review and actor, and reject a stale or reused token.

The actions shall be labeled **Cancel** and **Permanently Delete**.

The disposal operation shall:

- remove the selected review's working data, corrections, rule sets scoped to that review, runs, results, findings, Ask Fin review content, and review-scoped audit stream;
- retain only a content-free, attributable disposal tombstone/receipt required for integrity;
- be atomic for the authoritative live store;
- preserve unrelated reviews and shared/global rule definitions;
- retire the removed review audit anchor without invalidating startup verification; and
- never open, alter, or delete original external workbook files.

The UI shall not claim forensic media erasure or managed-backup revocation unless the retained-store/key-destruction and backup-revocation architecture has been executed and verified.

## 8. Appearance and visual-quality requirements

### REM-FR-018 — Financial application visual system

The desktop UI shall use a calm, trustworthy, modern financial design:

- warm cream/off-white application background;
- white or subtly warm cards;
- deep navy navigation and primary actions;
- muted secondary blues and blue-gray text;
- soft neutral borders;
- consistent spacing and deliberate rounded cards;
- professional typography, clear hierarchy, readable tables, and refined charts; and
- green, amber, and red reserved for status, always paired with text or iconography.

The application shall avoid large empty gray areas, default-widget harshness, dense unstructured tables, random color, inconsistent cards, and mobile-style desktop layouts.

### REM-FR-019 — Light, Dark, and System Default

Settings shall provide Light, Dark, and System Default appearance modes. System Default follows the operating-system preference. The user's preference persists after restart.

The whole shell, pages, charts, tables, dialogs, tooltips, technical disclosures, focus indicators, warnings, and errors shall update consistently. Dark mode uses deep navy/charcoal surfaces, lighter navy panels, off-white primary text, muted blue-gray secondary text, and accessible status colors. Large surfaces shall avoid pure black and pure white where practical.

## 9. Ask Fin boundary

### REM-FR-020 — Bounded Ask Fin

Ask Fin remains visible but is not a remediation critical path. It may provide product help and explanations of persisted rule results, selected findings, and charts. It shall not calculate validation truth, edit data/rules, approve actions, or block deterministic review completion.

## 10. Accessibility and quality requirements

### REM-NFR-001 — Keyboard and focus

All new actions, tabs, tables, disclosures, dialogs, chart alternatives, Settings controls, evidence navigation, and delete confirmation are operable by keyboard with visible focus. Modal focus is trapped and restored to the invoking control.

### REM-NFR-002 — Perceivability

Color is never the sole carrier of status, edit state, severity, or selection. Text and controls remain visible in Light, Dark, and System modes. Charts have accessible names, summaries, labels, and table alternatives.

### REM-NFR-003 — Resizing and zoom

Key pages remain usable at qualified desktop window sizes and supported zoom/scaling. Content shall not clip, overlap, hide actions, or introduce unnecessary horizontal scrolling. Wide financial tables may scroll while preserving row context and evidence actions.

### REM-NFR-004 — Evidence integrity

Every displayed validation conclusion and chart value traces to one sealed Validation Run projection. Evidence retains source role, worksheet, row, field/cell, record identity, value provenance, expected/actual condition, and contributing records as applicable.

### REM-NFR-005 — Consolidated verification

The remediation exits only after:

- automated positive, negative, and boundary coverage;
- exact synthetic-oracle comparison;
- review-edit/audit verification;
- optional-rule add/edit/test/version/revalidate verification;
- disposal authorization, cancellation, isolation, restart-integrity, and external-file-preservation verification;
- keyboard, focus, contrast, Light/Dark/System, resizing, and chart-alternative verification;
- same-screen Light and Dark screenshots for the required key states; and
- one independent end-to-end review with no unresolved material defect.

Results and review verdicts shall be recorded only after execution.
