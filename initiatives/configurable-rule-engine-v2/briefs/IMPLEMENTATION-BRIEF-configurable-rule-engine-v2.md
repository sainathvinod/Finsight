# FinSight Configurable Rule Engine — Product Definition and Implementation Brief

- **Status:** Human-approved Product Owner baseline; requirements refinements recorded through HD-27
- **Source:** Human-approved product direction and refinements supplied 2026-07-27
- **Prepared under:** `finsight-po-ai-agent`
- **Milestone:** Configurable financial validation platform evolution
- **Implementation authorization:** None — this brief authorizes no architecture or code changes
- **Pre-change reference:** `../readiness/CONFIGURABLE-RULE-ENGINE-PRECHANGE-INVENTORY.md`
- **Decision-source record:** `PRODUCT-DIRECTION-SOURCE-configurable-rule-engine-v2.md`
- **Independent review:** `../reviews/REVIEW-2026-07-27-configurable-rule-engine-product-definition.md`
- **Amendment review:** `../reviews/REVIEW-2026-07-27-product-owner-amendments.md`
- **Approved workflow:** `../docs/FINANCIAL-REVIEW-WORKFLOW.md`

## 1. Product vision

FinSight will evolve from a financial-review application with a fixed set of checks into a configurable financial validation platform whose foundation is a deterministic, versioned rule engine.

The engine is the single source of financial validation truth. The initial five mandatory controls are protected baseline rule definitions loaded through the same engine used by future organization-specific, optional, and informational rules. Adding rule 6, rule 20, or rule 100 must not require redesigning the application or creating a separate validation path.

The supplied Budget and GED reports are the V1/MVP reference model. Their agreed structures and sample conventions are the first-release business contract; broader enterprise accounting semantics and organization-specific conventions extend the engine later through governed configuration rather than delaying the MVP.

After validation, the first user destination is a Review Summary Dashboard that turns recorded engine results into an immediate executive overview before users drill into detailed findings.

## 2. Business problem

Finance users need reliable controls that are understandable, reproducible, and traceable to source data. They also need validation policy to evolve without losing the ability to reproduce prior results.

A fixed set of one-off checks would create several risks:

- new controls would require repeated application redesign;
- dashboards and reports could calculate conflicting versions of financial truth;
- editing a rule could silently change the meaning of historical validation runs;
- core controls could be accidentally disabled or deleted;
- user-authored logic could introduce unsafe or non-deterministic execution.

FinSight must solve these risks with one governed rule library, one deterministic execution path, immutable rule versions used by historical runs, and evidence-backed outputs consumed consistently throughout the product.

## 3. Target users and roles

### MVP roles

- **Reviewer:** uploads files, reviews extracted data, makes and confirms review-local corrections, runs validation, reviews findings, uses Ask Fin, generates reports, and advances the review lifecycle.
- **Rule Administrator:** creates, edits through new versions, tests, enables, disables, and retires configurable rules; may author and test a protected candidate and request its activation but cannot approve it or make a financial approval decision.
- **Financial Control Approver:** approves or rejects protected-baseline change requests, authorizes application of an approved protected baseline to an existing workspace, and governs the protected baseline lifecycle.

A protected-baseline request and approval must be performed by two different authenticated actors. The role model may gain additional roles without changing deterministic rule definitions or the rule engine.

Department or business-unit budget owners, leaders, auditors, and governance reviewers consume the views and evidence permitted by one of these MVP roles.

### Future users

- organization-specific rule authors operating through controlled forms;
- security, compliance, and release reviewers;
- consumers of approved AI explanations grounded exclusively in deterministic results.

The authenticated Windows user account is the default MVP actor identity. Identity resolution and authorization remain outside the deterministic rule engine so enterprise identity providers can replace the Windows source later.

The supplied Application Engineering reports are sample inputs, not a product boundary. FinSight must apply the same approved validation rules to any department or business unit using the compatible Budget and GED structures. Department names, numbers, reporting periods, or lists of departments must not be hard-coded into rules, readers, workspace identity, UI text, reports, or analytics.

## 4. Governing product principles

### P-01 — Rule engine as the source of financial validation truth

Every financial validation result in FinSight must originate from the deterministic rule engine.

Dashboards, analytics, reports, exports, KPIs, summaries, and future AI-generated explanations must consume recorded rule-engine results rather than independently recalculating financial validation logic. This ensures one reproducible source of truth.

File-ingestion status, data-preview screens, operational health, and other non-validation application state may originate from their owning application services. They must not be presented as independent financial validation conclusions.

### P-02 — Deterministic decisions; AI explanation only

Rule execution, calculations, result status, findings, evidence, and severity are deterministic. AI may later explain recorded results but cannot select rules, execute rule logic, change results, suppress findings, or create financial truth.

### P-03 — Same engine, governed classifications

Core mandatory, optional configurable, and informational/advisory rules use the same rule library, versioning system, controlled evaluator model, execution lifecycle, audit mechanism, and source-evidence contract. Rule classification changes governance behavior; it does not create a separate hard-coded execution path.

### P-04 — Historical meaning is preserved

Changing a rule creates a new immutable version. Historical validation runs continue to reference and replay the exact rule versions and configuration used at execution time.

### P-05 — Source financial files remain read-only

The platform may store its own rules, configuration, run records, findings, comments, reports, and audit history. It must never modify a source Budget or GED workbook or take an autonomous financial action.

### P-06 — Controlled configuration, not arbitrary code

Rule authors use validated fields, operators, keys, thresholds, messages, and other controlled options. The application must not execute user-provided Python, SQL, scripts, macros, or unrestricted expressions.

### P-07 — Department-neutral operation with automatic identification

Each review represents one department or business unit, but the product supports any compatible department. FinSight extracts available Department Name and Department Number metadata from the uploaded Budget and GED reports and displays the resolved workspace identity. The same rules execute regardless of department.

If the two reports identify different departments, validation is blocked and the inconsistency is explained before rule execution. Missing, conflicting, truncated, or differently formatted department metadata must remain explicit; detailed requirements must define its deterministic resolution and normalization rather than relying on a hard-coded department.

### P-08 — Period-bound review identity and pre-validation consistency

The user selects a reporting month and year when creating a review. FinSight extracts available period evidence from both reports and compares it with the selected period before validation. Under the V1 sample-reference contract, a mismatch is displayed and blocks validation until the report is replaced or the review selection is corrected; V1 has no user-confirmed period override. Period evidence and resolution are audited.

### P-09 — Supplied reports define the V1/MVP contract

The first release implements deterministic behavior against the supplied Budget and GED structures and the sample conventions already agreed for them. Requirements must state those V1 interpretations precisely and label them as reference-model decisions, not universal Amerisure accounting policy.

Production-wide accounting semantics, duplicate normalization beyond the supplied reports, additional layouts, and department-specific conventions are future governed, configurable extensions. They do not block V1 requirements, architecture, or implementation once the sample-reference contract is explicit and testable.

### P-10 — Summary first, detail on demand

After validation completes, FinSight opens the run-specific Review Summary Dashboard before the detailed findings view. A successor result is prominently `Working — Unpublished` until explicit promotion and never silently replaces the published trusted summary. The summary, its KPIs, its top findings, and its recommended next actions consume recorded deterministic rule-engine results and never create a second calculation path. Users can then navigate to Findings, Rule Results, Analytics, Reports, and Ask Fin.

### P-11 — Reviewed working data with immutable source provenance

A Reviewer may correct any extracted field in FinSight's reconstructed Working Dataset, including BGT, ATD, GED Amount, department, account, dates, and descriptions. Source workbooks never change. The product distinguishes the original extracted value, user-reviewed value, and current value used for validation; every change and reversion is visible, attributed, timestamped, audited, and retained as correction-basis events. Confirmation creates and seals the Review Version/ReviewGeneration at `Data Reviewed`; later data changes create a successor Working Candidate. Source bytes and complete normalized/working/verified row stores are not persisted, consistent with inherited ADR-012.

### P-12 — Replaceable identity and extensible authorization

Windows account identity and the three MVP roles define the first-release authorization boundary. Multiple active roles combine by permission union, with explicit separation-of-duties denials taking precedence. The identity provider and role policy are replaceable application services; neither becomes part of financial rule definitions or deterministic rule execution.

### P-13 — Explicit review identity and lifecycle

Every Review Summary and downstream artifact identifies the exact department, period, review version/generation, validation run, rule-set version, publication state, source files, and validation timestamp. Reviews move through Draft and Data Uploaded on a Working Candidate, then Data Reviewed, Validation Complete, Reviewed, Closed, and Archived on the created Review Version. Review lifecycle status is operational metadata and remains distinct from generation analytical/publication state and Overall Review Status, which is a financial validation result. The status maps to the inherited RAG presentation as `Healthy` = `On Track (Green)`, `Attention Required` = `Needs Attention (Yellow)`, and `Incomplete` = `At Risk (Red)`; RAG is not independently recalculated.

## 5. Rule classifications

Rule classification and lifecycle state are independent.

### 5.1 Core mandatory rules

Core mandatory rules are protected baseline controls included by default and enabled in every new validation workspace.

They cannot be modified, disabled, or deleted through normal user actions. Any change must occur through a governed administrative workflow that:

- creates a new rule version;
- preserves the original version for historical replay;
- records the requester, authorizer, reason, date, and before/after definition;
- records whether the change modifies, disables, deletes, replaces, or supersedes the rule;
- retains complete audit history;
- prevents the change from altering completed validation runs;
- makes the changed baseline visible to users and reports.

The Rule Administrator may create, edit, and test a protected Draft candidate without activating it. The protected workflow then requires the administrator's request to reference that immutable Tested candidate, approval by a different Financial Control Approver, an approved effective time, atomic activation, and immutable historical bindings. Applying the approved baseline to an existing workspace also requires Financial Control Approver authorization. The ordinary rule-management workflow is insufficient authorization.

### 5.2 Optional configurable rules

Authorized users may create, test, activate, edit through new versions, disable, retire, or logically delete optional rules under the configurable-rule lifecycle.

A version already used by a validation run is retained. “Delete” removes the rule from ordinary future selection; it does not erase historical rule definitions, execution evidence, or audit history.

### 5.3 Informational or advisory rules

Informational/advisory rules produce evidence-backed observations without determining a financial control pass/fail unless a later governed version explicitly changes their classification and behavior.

Their results must be visibly distinguishable from validation failures in findings, dashboards, analytics, reports, and exports.

## 6. Mandatory baseline controls

The following five controls form the protected baseline for every FinSight deployment and validation workspace.

For V1, the detailed requirements derive each control's eligible rows, fields, parsing, matching, comparison, and evidence behavior from the supplied Budget and GED reference reports and previously agreed sample conventions. Those deterministic V1 definitions are testable product behavior, while broader enterprise or department-specific policies remain future configurable extensions.

### Core rule A — Actual spend must not exceed BGT

For each valid Department Number + Account Number, compare validated actual spend derived from GED Amount with the matching Budget BGT. A breach produces a finding with the planned amount, actual amount, overrun, key, calculation, and contributing source rows.

### Core rule B — Every GED transaction must map to Budget

Every GED transaction must map to a valid Budget Department Number + Account Number combination. An unmapped transaction produces a finding with the GED row, identifiers, journal evidence, amount where available, and matching failure.

### Core rule C — Exact duplicate GED transactions must be flagged

GED transactions with the same governed material-field fingerprint must be flagged as duplicate candidates. The fingerprint must use all approved material transaction fields, not Journal Number alone. The finding identifies every member row and the potential duplicate exposure. No row is automatically deleted or excluded.

### Core rule D — Required GED fields must be present and parseable

Department Number, Account Number, Fiscal Period, Journal Number, Journal Date, and Amount must be present and parseable on every GED transaction. Blank Amount is not zero. Zero and signed amounts remain valid unless a separate approved rule states otherwise.

### Core rule E — Budget ATD must equal summed GED Amount

For each Department Number + Account Number, Budget ATD must equal the exact-decimal sum of eligible GED Amount values for the same review cycle. Missing, invalid, or unmapped inputs must produce an explicit not-evaluated/blocked outcome rather than a false pass.

The protected catalog IDs are `R-VAL-01` through `R-VAL-05` for CORE-01 through CORE-05. No existing identifier is silently repurposed.

This brief changes no existing catalog rule's identifier, approved meaning, status, classification, or release disposition. All 57 existing rules are preserved unchanged outside the initial V2 active set. A future migration requires an explicit successor, controlled-evaluator mapping, V2 classification, and lifecycle decision; omission from the five-rule protected baseline never demotes or retires a legacy rule.

## 7. Rule lifecycle

The Rule Definition Version lifecycle is:

`Draft → Tested → Active → Retired`

Workspace applicability is a separate versioned Rule Binding with `Enabled` or `Disabled` state.

Required lifecycle behavior:

- activation requires successful rule-definition validation and approved tests;
- editing creates a new version rather than mutating an active version;
- completed runs retain the exact version they used;
- disabled bindings and retired versions remain available for audit and replay;
- ordinary deletion is logical rather than historical erasure;
- core-rule transitions use the stronger administrative workflow in §5.1;
- rule changes can be tested before activation;
- governed rule/configuration reanalysis discloses which findings were added, removed, or changed while preserving the original verification basis and published result until promotion.

## 8. Preserved financial-review workflow

The detailed, approved workflow is recorded in `../docs/FINANCIAL-REVIEW-WORKFLOW.md` and is a binding input to requirements, UX, UI, architecture, acceptance criteria, tests, and traceability.

1. **Welcome:** offer Create New Review and View Past Reviews; disable the past-review action with an explanation when no prior review exists.
2. **Select review period:** choose reporting month and year; make the selection part of the review identity.
3. **Upload source files:** show exactly two required MVP upload slots—Budget Report and GED Report—with file, compatibility, metadata, and extraction status.
4. **Extract and identify metadata:** display department name/number, reporting period, filenames, record counts, mismatches, and workbook-structure problems.
5. **Review extracted data:** provide separate searchable, filterable, sortable Budget and GED views with values and source lineage.
6. **Confirm and save edits:** permit a Reviewer to correct any extracted field in the reconstructed review-local Working Dataset, preserve source files and original extracted values, distinguish original/reviewed/current values, require explicit confirmation, audit every edit/reversion, and create the Review Version/ReviewGeneration only at confirmation.
7. **Validate:** after both datasets are compatible and the working data is confirmed, execute all protected core rules plus active optional/advisory rules through the deterministic engine.
8. **Review Summary and results:** land first on an executive Review Summary containing Department Name/Number, Reporting Period, Validation Run ID, Rule Set Version, Review Version, Publication State, Source File Names, Validation Timestamp, Overall Review Status and its mapped RAG presentation, Budget Health, Data Quality, rule execution/pass/fail/not-evaluated counts, advisory observation/no-observation counts, Budget Overruns, Duplicate Transactions, Missing Required Data, Reconciliation Status, Top Findings, and Recommended Next Actions; label a successor `Working — Unpublished` until promotion, then let users navigate to Findings, Rule Results, Analytics, Reports, and Ask Fin.
9. **Analyze and report:** present views derived from recorded rule-engine results without independently recalculating financial validation logic; trusted defaults use the published generation.
10. **Ask Fin:** explain and cite one identified published, historical, or explicitly selected analyzed-working generation without creating, changing, mixing, or approving financial conclusions.
11. **Complete and save:** explicitly promote a completed successor before it becomes Reviewed, then advance to Closed and optionally Archived without erasing history; retain authoritative reconstruction, generation, run, result, promotion, and derived-artifact records while reconstructing row data when fingerprint-matching sources are available.

## 9. MVP boundaries

### In scope

- real-layout Budget and GED workbook ingestion;
- the supplied Budget and GED structures and agreed sample conventions as the deterministic V1/MVP business contract;
- department-neutral operation for any single department or business unit represented by compatible reports;
- automatic extraction and display of department name, department number, reporting period, filenames, and record counts whenever the source provides them;
- pre-validation department and reporting-period consistency checks;
- the approved guided review workflow in §8;
- extracted-data review before validation;
- the Reviewer, Rule Administrator, and Financial Control Approver roles with two-person protected-core approval;
- authenticated Windows-account actor identity behind a replaceable identity-provider boundary;
- any-field review-local correction with immutable source files and explicit original/reviewed/current values;
- controlled, versioned rule definitions;
- the three rule classifications;
- the five protected core controls;
- optional and informational rule lifecycle;
- deterministic execution using exact decimal arithmetic;
- pass, fail, and not-evaluated outcomes;
- findings with calculation and source evidence;
- rule testing before activation;
- reason-specific source/extractor reverification, rule/configuration reanalysis, exact replay comparison, and explicit generation promotion;
- rule, configuration, run, finding, and authorization audit history;
- validation-derived dashboard, analytics, reports, and approved exports;
- a Review Summary Dashboard as the first post-validation landing page, with every financial status, metric, finding, and next action derived from recorded rule-engine results;
- Review Summary and downstream-artifact identity using department, period, Validation Run ID, Rule Set Version, Review Version, publication state, source filenames, and validation timestamp;
- the Draft, Data Uploaded, Data Reviewed, Validation Complete, Reviewed, Closed, and Archived review lifecycle;
- a distributable Windows executable and installer as mandatory release outputs;
- Windows clean-machine installation and launch evidence, upgrade and uninstall behavior, integrity checks, build manifest, exact source-commit provenance, release notes, and the approved security/code-signing gates required before distribution;
- inherited macOS functional parity and packaging support, while V2 adds the explicit Windows installer and Windows qualification gates;
- synthetic fixtures only until the security operating boundary is approved.

### Out of scope for this Product Owner stage

- technology-stack selection;
- database, schema, class, API, or UI-component design;
- application-code changes;
- source-workbook modification;
- a fixed department list, department-specific rule variants, or hard-coded sample department identifiers;
- organization-wide accounting-policy definition, additional source-layout semantics, fuzzy duplicate matching, or department-specific conventions beyond the supplied V1 reference model;
- invoice, purchase-order, statement-of-work, rate-card, resource-sheet, or other upload slots in the first configurable-rule-engine MVP;
- arbitrary script or expression execution;
- autonomous financial decisions or actions;
- production use with confidential data;
- AI-generated pass/fail decisions;
- approval of security, packaging, or deployment architecture.

## 10. Success measures

Candidate measures requiring requirements-stage fit criteria:

- identical files plus identical rule/configuration versions produce identical ordered results;
- all five core rules are present and enabled in a newly created workspace;
- the same compatible files produce the same rule behavior regardless of department name or number;
- a workspace displays extracted/resolved department identity, reporting period, source filenames, and record counts before validation;
- conflicting department identities block validation with source evidence;
- conflicting selected/file reporting periods block V1 validation until the report is replaced or the review selection is corrected;
- neither required source file can be omitted or bypassed before cross-file validation;
- every core rule has passing positive, negative, and boundary tests;
- every finding identifies its rule version, calculation, input values, and source rows/cells;
- completing validation opens the Review Summary before detailed findings and displays every HD-20 summary field;
- every Review Summary financial status, count, top finding, and recommended next action traces to recorded rule-engine results;
- users can navigate from the Review Summary to Findings, Rule Results, Analytics, Reports, and Ask Fin;
- a completed run remains reproducible after a rule receives a new version;
- normal user actions cannot disable, modify, or delete a core rule;
- an authorized core-rule change preserves the prior version and records the complete reason and authorization history;
- downstream validation views contain no independent financial-validation calculation;
- an optional rule can be added through a supported controlled rule type without redesigning unrelated modules;
- disabling AI changes no deterministic result;
- every existing approved catalog rule has an explicit, human-governed V2 preservation or disposition decision;
- a Windows installation package is traceable to its exact source commit and passes the approved clean-machine, integrity, security, signing, upgrade, and uninstall release gates before it is represented as distributable.

This brief adds no new numeric performance or scale target; the inherited root NFR-001 baseline of at most 10,000 GED rows on an 8–16 GB target laptop within two minutes remains binding.

## 11. Existing specification alignment

The direction aligns with:

- `specs/00-project-understanding.md` — deterministic truth and AI explanation boundary;
- FR-103 — configurable rule parameters;
- FR-106 — governed rule enable/disable;
- FR-107 — configuration versioning;
- FR-086 — rule-execution audit;
- NFR-021/NFR-022 — reproducibility and rule/configuration provenance;
- NFR-039–041 — safe, transparent configuration;
- NFR-044 — new rules without core redesign;
- F-02-01 through F-02-06 — rule definition, execution, management, findings, and replay;
- `specs/05-rules-catalog.md` — deterministic rules and evidence;
- `specs/06-architecture.md` XP-01 — rule registration extension point.

Detailed requirements must close the gaps identified in the pre-change inventory. This brief does not edit or reinterpret the cited approved items.

## 12. Risks

- an overly expressive rule language could become arbitrary code execution;
- an overly narrow rule model could make “configurable” nominal rather than useful;
- separately calculated dashboard metrics could diverge from rule results;
- core-rule governance could be so weak that controls are bypassed, or so rigid that policy evolution becomes impractical;
- a future duplicate-normalization policy could create false positives if it is not introduced as an explicit, versioned configuration that preserves the V1 exact-match behavior for historical replay;
- incomplete or unmapped data could create misleading downstream passes without dependency-aware execution;
- historical reproducibility could fail if definitions are edited in place or files/configurations are not fingerprinted;
- desktop rule administration and future enterprise role-based authorization may require different operating models;
- confidential-data use remains unsafe until the security boundary is approved and evidenced.

## 13. Product assumptions and boundaries

- the five named controls are the only mandatory baseline rules for the first configurable-rule release;
- one review operates on one department or business unit, while any compatible department may create its own review;
- all 57 existing catalog rules remain preserved unchanged and outside the initial V2 active set until any future per-rule migration receives an explicit governed disposition;
- V1 financial semantics, eligible rows, duplicate matching, department identity, and period handling are derived from the supplied Budget/GED reports and their previously agreed sample conventions;
- those V1 reference-model decisions do not claim to define organization-wide Amerisure accounting policy;
- broader financial semantics, additional normalization, new report layouts, and department-specific conventions enter later as governed, configurable extensions;
- core-rule modification authority is an administrative responsibility distinct from ordinary rule editing;
- validation-derived dashboards and reports consume persisted/recorded rule results, while file-status and operational screens may use non-validation application state;
- the Review Summary is the first screen shown after validation and does not independently calculate financial truth.
- the authenticated Windows account supplies the MVP Actor ID while identity-provider replacement and additional role definitions do not change rule-engine behavior;
- lifecycle Review Status is operational and never substitutes for deterministic Overall Review Status.

## 14. Resolved Requirements decisions and downstream design gates

The Requirements clarification register is closed:

- a protected core version cannot be ordinarily disabled; governed retirement, disablement, logical deletion, or replacement activates a tested successor atomically and never leaves fewer than five protected controls;
- the first-release configurable evaluator supports bounded presence/parseability, exact reference membership, exact duplicates, decimal comparison, grouped SUM/COUNT, and finite ALL/ANY composition, with no executable or unrestricted expressions;
- Review Summary print/PDF and spreadsheet-compatible Findings, Rule Results, and summarized-data exports are required; audit export and on-screen run comparison are Should priority;
- the inherited scale baseline remains 10,000 GED rows on an 8–16 GB laptop within two minutes; Architecture must add safe workbook-complexity and optional-rule stress profiles;
- all 57 legacy rules are preserved unchanged outside the initial V2 active set; the new baseline IDs are `R-VAL-01` through `R-VAL-05`;
- protected seed severities are High, High, Medium, High, and High for CORE-01 through CORE-05, with every severity change versioned and governed.

Architecture and release governance must still select the exact rule serialization/evaluator classes, export representation, resource ceilings, Windows matrix/packaging/signing mechanisms, local storage and recovery mechanisms, versioned error taxonomy, and approved private/on-device Ask Fin adapter. Those choices cannot weaken the requirements and must be reviewed before implementation.

### 14.1 Future configurable extensions, not V1 stop gates

HD-19 removes the following from the V1 clarification stop gate:

- organization-wide or production Amerisure meanings that differ from the supplied sample conventions;
- GED eligibility policies for accounting conventions or layouts not represented by the supplied reports;
- broader, fuzzy, case-specific, or event-specific duplicate normalization;
- department identifier/name conventions beyond the supplied reference structure;
- review-period conventions for additional source-report variants.
- status-policy versions in which optional or advisory rules affect Overall Review Status differently from the V1 baseline.

The Requirements stage must still document one precise, deterministic, testable interpretation for the supplied V1 reference reports. It does not need enterprise-wide policy answers to do so.

## 15. Definition of done for the Product Owner stage

- [x] The product vision and rule-engine-first principle are accepted by HD-17/HD-18.
- [x] The three rule classifications and protected-core governance wording are accepted by HD-17/HD-18.
- [x] The five mandatory controls are accepted as the baseline rule set by HD-06 through HD-11 and reaffirmed by HD-18.
- [x] The amended in-scope and out-of-scope boundaries are accepted by HD-12 through HD-20.
- [x] The supplied-report V1 contract and Review Summary-first experience are recorded by HD-19/HD-20.
- [x] Requirements ambiguities are resolved or explicitly routed to the correct downstream design/release gate.
- [x] Candidate requirements and acceptance criteria are drafted and remain Draft until the independent Requirements review confirms the HD-27 completion conditions.
- [x] The pre-amendment brief received an independent read-only requirements review with a final PASS.
- [x] The HD-12 through HD-18 amendment set received a final independent read-only re-review with PASS.
- [x] The Project Owner explicitly approved the amended direction and authorized the Requirements stage after incorporation (HD-17).

## 16. Traceability and handoff

The durable decision-source record identifies the operative human decisions as HD-01 through HD-27 and the inherited outcomes as AR-01 through AR-04.

| Brief content | Decision/specification source |
|---|---|
| Same-repository FinSight evolution | HD-01 |
| Department-neutral audience and automatic department identification | HD-12; HD-13 |
| Period selection, extraction, and mismatch gate | HD-14; HD-19; WF-02; WF-04 |
| Preserved eleven-step review workflow | HD-15; WF-01 through WF-11 |
| Supplied Budget/GED reports as the V1/MVP business contract | HD-19; P-09 |
| Review Summary as the first post-validation landing | HD-20; P-10; WF-08 |
| Three roles, Windows identity, and two-person protected-core approval | HD-21–HD-23; P-12 |
| Any-field Working Dataset corrections and three-value provenance | HD-24; P-11; WF-05–WF-07 |
| Review identity block and seven-state lifecycle | HD-25; HD-26; P-13; WF-08; WF-11 |
| Configurable rule engine as product core | HD-02; AR-01; FR-103; NFR-044; F-02-01 |
| Three rule classifications | HD-03 |
| Protected baseline governance and historical replay | HD-04; HD-11; FR-106; FR-107; F-02-03; F-02-06 |
| Single source of financial validation truth | HD-05; FR-086; NFR-021; NFR-022 |
| Core rules A–E | HD-06 through HD-10 |
| Default enablement, testing, evidence, reporting, and analytics | HD-11; AR-04 |
| Existing-rule preservation and future migration gate | HD-01; HD-17; HD-18; `specs/05-rules-catalog.md`; clarification CQ-13/CQ-29 |
| Windows distribution and release evidence | AR-03 |
| Security, portability, testing, and production-readiness boundaries | AR-02; AR-04; existing NFR catalog |
| Product Owner amendment approval and Requirements/Architecture gates | HD-17 through HD-27 |

The Project Owner explicitly approved the direction, including the refinements recorded through HD-27. Requirements complete only after these decisions are incorporated and the independent requirements review returns PASS. Architecture may then begin; application implementation remains blocked until the architecture, rule-engine design, persistence model, UX/UI, and technical implementation plan are reviewed and approved.
