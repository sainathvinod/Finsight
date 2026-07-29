# 01 — Functional Requirements: FinSight Configurable Rule Engine V2

- **Purpose:** Define the V2 behavior added to or made more specific than the existing FinSight functional requirements. This is a delta register for the same product, not a duplicate application specification.
- **Sources:** HD-01 through HD-27; WF-01 through WF-11; AR-01 through AR-04; the human-approved Product Owner brief; the supplied real-layout Budget/GED structures; existing approved FinSight FR-001–FR-122.
- **Status legend:** Draft (unreviewed) → Approved (named, row-level stakeholder decision in a workbook) → Baselined → Implemented → Verified.
- **ID policy:** Root FinSight currently uses FR-001 through FR-122. This delta continues the same stable namespace at FR-123. IDs are never reused.
- **Scope boundary:** Every item below is `Draft`. Product Owner approval authorized drafting; it did not approve these detailed statements.

## 1. Source relationships

| Source | Relationship to this delta |
|---|---|
| `../../../specs/01-functional-requirements.md` | Existing approved FinSight behavior remains in force unless an explicit V2 item states a narrower or changed behavior. |
| `../briefs/PRODUCT-DIRECTION-SOURCE-configurable-rule-engine-v2.md` | Durable human decisions HD-01–HD-27 and inherited project outcomes AR-01–AR-04. |
| `../docs/FINANCIAL-REVIEW-WORKFLOW.md` | Binding workflow steps WF-01–WF-11. |
| `../briefs/IMPLEMENTATION-BRIEF-configurable-rule-engine-v2.md` | Human-approved Product Owner scope, governance, classifications, resolved decisions, and downstream routing. |
| `../../../specs/05-rules-catalog.md` | Existing approved rule catalog; no existing rule is silently reclassified or repurposed. |
| `../../../specs/adr/ADR-011-review-lifecycle-and-generation-model.md` | Inherited ReviewCycle/ReviewGeneration, one-run lineage, working/published, promotion, and supersession contract. |
| `../../../specs/adr/ADR-012-source-binding-and-working-set-reconstruction.md` | Inherited source-binding, fingerprint-verified reconstruction, and non-persistence contract for normalized/verified row stores. |
| `../../../specs/adr/ADR-014-review-abandonment-and-retention.md` | Inherited orthogonal Active/Abandoned disposition, no-auto-expiry, and non-destructive ordinary-retention contract. |
| `../../../specs/adr/ADR-015-immutable-export-and-report-identity.md` | Inherited immutable export manifest, generation visibility, and working/published/historical artifact-labeling contract. |
| `03-existing-rule-disposition.md` | Complete 57-rule preservation register; future migration of a legacy rule requires an explicit successor decision. |
| `clarifications/CLARIFICATION-PACKET-2026-07-27.md` | Closed Requirements clarification record and routing of implementation-specific choices to Architecture or release governance. |
| `../requirements/GOVERNED-V2-DELTA-2026-07-27.md` | Explicit consistency record for V2 refinements of the inherited rule-set, authority, workflow, status, verification, immutability, and disposal contracts. |
| `../fixtures/SYNTHETIC-VALIDATION-EXPECTATIONS.md` | Complete cross-rule oracle for the four intentional Stage 2 source-data scenarios. |

## 2. Defined records

### 2.1 Validation Workspace metadata summary

The metadata summary referenced below contains:

- Review ID, Review Status, and either the active Working Candidate ID or the created Review Version;
- working/published Review Version identity when either exists;
- resolved Department Name and Department Number;
- selected reporting month/year;
- each file's extracted department and period evidence;
- Budget filename and GED filename;
- Budget detail-record count and GED transaction count;
- upload, compatibility, extraction, verification, and mismatch status for each file.

Unknown or conflicting metadata remains visibly unknown or conflicting; it is never silently defaulted.

### 2.2 Rule Result record

Each rule definition declares one deterministic evaluation grain, such as workspace, Department Number + Account Number, GED transaction, or duplicate-fingerprint group. The engine enumerates the expected scopes at that grain. The Rule Result record represents one selected rule version evaluated against one expected scope and contains:

- validation Run ID;
- Rule Execution ID and stable evaluation-scope key;
- selected Rule ID, immutable rule version, classification, and configuration version;
- input-file fingerprints;
- confirmed correction-basis/edit version and verified-data fingerprint;
- execution timestamp and deterministic execution order;
- PASS, FAIL, NOT_EVALUATED, OBSERVATION, or NO_OBSERVATION status as permitted by the rule classification and versioned status policy;
- evaluated scope, calculation/evaluation evidence, and source references;
- blocking dependency when status is NOT_EVALUATED;
- exactly one linked Finding ID when a control status is FAIL.

A result ledger is complete only when every expected rule-and-scope pair has exactly one persisted status. An intake failure that prevents scope enumeration blocks the run before a false complete ledger can be created.

### 2.3 Rule Execution record

Each selected rule version has exactly one Rule Execution record per validation run. It contains:

- validation Run ID and Rule Execution ID;
- Rule ID, immutable rule version, classification, and configuration version;
- declared evaluation grain;
- expected-scope count and persisted Rule Result counts by status;
- one rule-level display status derived exclusively from its Rule Results under the versioned roll-up policy;
- linked Finding IDs and execution/audit provenance.

The Rule Execution record is a deterministic roll-up; it is not an independent financial calculation. The V1 roll-up precedence is defined in §2.7 and remains versioned with the run.

### 2.4 Rule classifications

Each rule version has exactly one classification:

- Core Mandatory;
- Optional Configurable;
- Informational/Advisory.

Classification governs lifecycle and status policy but never creates a separate financial-calculation path.

Core Mandatory and Optional Configurable control scopes use PASS, FAIL, or NOT_EVALUATED and create exactly one Finding for each FAIL scope. Informational/Advisory scopes use OBSERVATION, NO_OBSERVATION, or NOT_EVALUATED and never create a control-failure Finding.

### 2.5 Required results and analytics views

The WF-08 Review Summary is the first view presented after validation. It contains the §2.7 executive summary and drill-down access to:

- Findings;
- Rule Results;
- Analytics;
- Reports;
- Ask Fin.

The Findings and Rule Results views contain:

- selected and executed rule counts;
- Rule Execution counts by derived status;
- Rule Result counts by PASS, FAIL, NOT_EVALUATED, OBSERVATION, and NO_OBSERVATION status;
- total Findings;
- Findings grouped by severity, rule, department, and account;
- budget-versus-actual and reconciliation status;
- duplicate, missing-data, and invalid-reference exceptions;
- evidence access and recommended human follow-up for every Finding.

The WF-09 analytics workspace contains:

- budget versus actual by account;
- over-budget accounts and largest variances;
- Findings by severity and rule;
- GED completeness;
- reconciliation results;
- validation-run summary;
- leadership-ready summary.

Every validation conclusion in these views is obtained from persisted Rule Executions and Rule Results. Non-validation descriptive aggregates are labeled as descriptive and cannot override a recorded result.

### 2.6 Deterministic comparison projection

Deterministic replay compares the ordered business-result projection: rule/configuration versions, stable evaluation-scope keys, statuses, calculations, normalized evidence references, severities, and Finding content. Run IDs, execution timestamps, actor IDs, correlation IDs, and other volatile audit metadata remain retained for provenance but are excluded from equality comparison. Any later change to this projection is versioned and requires human approval of regenerated expected outputs.

### 2.7 Review Summary and V1 status policy

The Review Summary contains:

- Department Name;
- Department Number;
- Reporting Period;
- Validation Run ID;
- Rule Set Version;
- Review Version;
- Review Lifecycle Status;
- Publication State;
- Source File Names;
- Validation Timestamp;
- Overall Review Status;
- RAG Status;
- Budget Health;
- Data Quality;
- Number of Rules Executed;
- Number of Rules Passed;
- Number of Rules Failed;
- Number of Rules Not Evaluated;
- Advisory Rules With Observations;
- Advisory Rules With No Observations;
- Budget Overruns;
- Duplicate Transactions;
- Missing Required Data;
- Reconciliation Status;
- Top Findings;
- Recommended Next Actions.

Every validation value on the Review Summary is a projection of persisted engine records:

| Summary item | V1 deterministic source |
|---|---|
| Department Name, Department Number, Reporting Period | Confirmed Validation Workspace metadata |
| Validation Run ID, Rule Set Version, Review Version, Review Lifecycle Status, Publication State, Source File Names, Validation Timestamp | Persisted identity, generation, publication, and provenance records of the selected Validation Run and Review Version |
| Overall Review Status and RAG Status | The V1 status policy and one-to-one mapping below |
| Budget Health | `Incomplete`, `Attention Required`, or `Healthy` from the CORE-01 Rule Execution status |
| Budget Overruns | Number of CORE-01 failed Department Number + Account Number scopes |
| Data Quality | `Incomplete` when CORE-02 or CORE-04 is `NOT_EVALUATED`; otherwise `Attention Required` when either fails; otherwise `Healthy` |
| Duplicate Transactions | Sum of `group member count - 1` across CORE-03 failed duplicate groups |
| Missing Required Data | Number of distinct GED transaction scopes that fail CORE-04 |
| Reconciliation Status | `Incomplete`, `Attention Required`, or `Healthy` from the CORE-05 Rule Execution status |
| Rules Executed, Passed, Failed, Not Evaluated | Persisted Rule Execution records; only control-rule `PASS` and `FAIL` executions are counted as passed or failed, and every `NOT_EVALUATED` execution remains separately visible |
| Advisory Rules With Observations / No Observations | Informational/Advisory Rule Executions with `OBSERVATION` / `NO_OBSERVATION`; neither status is counted as passed or failed |
| Top Findings | At most five control Findings for the run, ordered by severity Critical → High → Medium → Low, then Core Mandatory before Optional Configurable, then stable Rule ID and evaluation-scope key |
| Recommended Next Actions | Configured recommended-human-follow-up text for displayed Findings; when none exist, `Resolve cited NOT_EVALUATED dependencies and rerun` for `Incomplete`, or `No core-rule follow-up identified` for `Healthy` |

The default trusted Review Summary, dashboard, analytics, reports, exports, and Ask Fin context use the published Review Version. Immediately after a successor validation completes, the run-specific Review Summary may display that working Review Version before promotion only with a prominent `Working — Unpublished` label and simultaneous identification of the still-published Review Version; no working value silently replaces a published metric. An explicitly selected historical run is labeled historical and carries its own identity.

For a control rule, the V1 Rule Execution roll-up is `NOT_EVALUATED` when any expected scope is `NOT_EVALUATED`; otherwise it is `FAIL` when any expected scope is `FAIL`; otherwise it is `PASS` when every expected scope is `PASS`. For an Informational/Advisory rule, the roll-up is `NOT_EVALUATED` when any expected scope is `NOT_EVALUATED`; otherwise it is `OBSERVATION` when at least one scope is `OBSERVATION`; otherwise it is `NO_OBSERVATION` when every expected scope is `NO_OBSERVATION`. A disabled rule is not selected, is not executed, and is not counted as executed.

A successfully enumerated empty scope population rolls up to `PASS` for a control rule or `NO_OBSERVATION` for an Informational/Advisory rule whose declared grain permits zero scopes. Failure to enumerate expected scopes is not an empty population and blocks run completion.

The V1 Overall Review Status is:

- `Incomplete` when any selected Core Mandatory rule lacks a complete Rule Execution or has a `NOT_EVALUATED` Rule Execution;
- `Attention Required` when every selected Core Mandatory rule is complete and at least one has a `FAIL` Rule Execution;
- `Healthy` when all five Core Mandatory Rule Executions are `PASS`.

Optional Configurable and Informational/Advisory outcomes remain visible but do not change the V1 Overall Review Status. A future versioned status policy may change that behavior without changing or bypassing the rule engine.

The V2 Review Summary exposes both the textual Overall Review Status and the inherited deterministic RAG presentation from the same engine-derived status, with no second calculation:

| Overall Review Status | RAG label | RAG color term |
|---|---|---|
| `Healthy` | `On Track` | `Green` |
| `Attention Required` | `Needs Attention` | `Yellow` |
| `Incomplete` | `At Risk` | `Red` |

This mapping is the V2 realization of root FR-077 for the Review Summary. Text and icon/shape accompany color under the inherited accessibility requirements.

### 2.8 MVP authorization and actor identity

The MVP authorization policy contains three roles. `Yes` means the role grants the action within the actor's separately authorized data scope; `Bound read` means only the stated evidence is visible:

| MVP action | Reviewer | Rule Administrator | Financial Control Approver |
|---|---|---|---|
| Read authorized review data, source evidence, results, and derived records | Yes | No, unless also Reviewer | No, unless also Reviewer |
| Read active rule/version evidence bound to an authorized review | Bound read | Yes | Bound read for protected rules and requests |
| Create/advance a review; upload; correct/revert/confirm data; validate; review results; use Ask Fin; generate reports/exports; close/archive | Yes | No, unless also Reviewer | No, unless also Reviewer |
| Request confirmed whole-scope disposal under §2.13 | Yes | No, unless also Reviewer | No, unless also Reviewer |
| Create/edit/test an Optional Configurable or Informational/Advisory Draft; advance it to Tested | No | Yes | No |
| Approve activation, activate, bind, enable, disable, or retire an Optional Configurable or Informational/Advisory version | No | Yes | No |
| Create/edit/test a protected successor Draft; advance it to immutable Tested; submit a request referencing it | No | Yes | Read only |
| Request application of an effective Protected Baseline Version to an existing workspace | No | Yes | Read only |
| Approve/reject a protected request; authorize an existing-workspace protected-baseline upgrade | No | No | Yes, subject to distinct-actor controls |
| Assign an MVP role through FinSight | No | No | No; role assignment remains outside the MVP application |

For the Windows MVP, the stable Actor ID is the authenticated Windows security identifier, retained with its domain-qualified account name and identity-source identifier. Display-name equality never substitutes for stable Actor ID equality. If FinSight cannot resolve a stable Actor ID, it permits access only to non-sensitive application-shell and product-help content that discloses no review, source, rule, request, result, Derived Record, or audit data; it denies every such data-access request and every action that creates or mutates application or audit state. After a stable Actor ID resolves, every authorized application-data access is audited with that Actor ID, identity source, and timestamp under root FR-084.

On a supported non-Windows platform required by inherited NFR-028, the authenticated platform account maps through the replaceable identity-provider boundary to the same stable Actor contract and failure behavior. Windows account identity remains the default V2 actor source and the required Windows release-qualification case; platform substitution cannot change rule, authorization, audit, or deterministic-result semantics.

Authorization is evaluated before a protected operation enters the rule library or review workflow. The rule engine receives immutable rule/configuration versions and data, not operating-system credentials or role-assignment logic.

A Role Assignment records stable Actor ID, role, effective-from timestamp, optional effective-through timestamp, assigning Actor ID, assignment timestamp, and assignment version. A Protected Change Request records request ID, protected Rule ID/version, exact Tested candidate Rule Version, requested action, before/after definition, reason, proposed effective date, requester Actor ID/time, decision status, and approver Actor ID/time/reason when decided. It links immutably to a separate activation event carrying the activated Rule Version and resulting Protected Baseline Version only if and when an approved request takes effect; a pending or rejected request has no fabricated activation values.

Role assignments originate from a protected administrative authorization source. No actor may grant itself a role or approve its own role assignment. The role-provisioning mechanism is selected and approved during Architecture.

One Actor ID may hold more than one MVP role, and ordinary permissions are the union of assignments effective at the action's persisted evaluation timestamp. Explicit separation and protection denials take precedence over that union: an actor cannot approve or reject its own protected request, approve its own role assignment, bypass lifecycle state, or alter historical records even when it holds every role. A role assignment is effective when `effective-from <= evaluation timestamp < effective-through`, or from `effective-from` onward when no effective-through value exists.

A protected requester and decision maker must each hold the required effective role when their respective action is committed. A scheduled protected activation relies on the immutable approved decision and exact Tested candidate recorded at decision time; later role expiry does not rewrite that decision. An existing workspace adopts a newer protected baseline only through an explicit upgrade authorized by a Financial Control Approver, followed by a new Review Version and Validation Run. FinSight roles grant no approval authority for spending, invoices, journal entries, or other financial business decisions.

### 2.9 Working Dataset value provenance

The Working Dataset is a deterministic, in-process reconstruction for one Working Candidate. FinSight reconstructs normalized Budget/GED rows from source bytes whose fingerprints match the persisted source bindings, using the recorded extractor version, then replays the persisted correction/reversion ledger. FinSight does not persist source workbook bytes, the complete normalized row store, the complete Working Dataset, or the complete `VerifiedDataset`.

Each editable extracted field presents:

- **Original Extracted Value:** the immutable normalized value created from the uploaded source cell, with raw-cell lineage;
- **User-Reviewed Value:** the latest saved review-local replacement with `Pending confirmation` or `Confirmed` state, or `Not set` when no replacement exists;
- **Current Validation Value:** `Unavailable — confirmation required` for a Working Candidate; for a sealed Review Version it is the reconstructed confirmed User-Reviewed Value when one exists, otherwise the reconstructed Original Extracted Value.

A Reviewer may edit any extracted Budget or GED row-level business-data value, including account, department, date, description, BGT, ATD, ETC, EAC, DELTA, Invoice Amount, and GED Amount. Report-title metadata, source-level department/period evidence, row identity, source location, source file bytes, file fingerprint, formula text, row classification, audit history, and system-generated IDs are provenance rather than editable extracted fields. A correction never inserts or deletes a source row.

Every saved correction or reversion appends a persisted edit event and advances the Working Candidate's correction-basis version. Each event retains the source cell/row identity and the original, prior reviewed, resulting reviewed, actor, time, reason, and reversal linkage required by FR-138. A pending User-Reviewed Value is visible but is never a Current Validation Value.

On explicit confirmation, FinSight computes the complete Current Validation Value projection, persists its verified fingerprint, source fingerprints, extractor version, correction-basis version, row/schema counts, confirming Actor ID/time, and verification reason, and creates the sealed Review Version described in §2.10. It does not persist the complete projection. Before validation or evidence display, it reconstructs the projection from the same basis and requires the recomputed fingerprint to equal the recorded verified fingerprint.

A `RULESET_REANALYSIS` or `CONFIG_REANALYSIS` Review Version inherits the exact verified fingerprint, original confirming Actor/time, extractor version, source fingerprints, and correction basis from its verification-basis Review Version while separately recording the reanalysis initiator/time. Any changed or unavailable basis prohibits inheritance. The deterministic rule engine accepts only a successfully fingerprint-verified reconstructed `VerifiedDataset`; it accepts no Working Candidate or partial reconstruction.

### 2.10 Review identity and lifecycle

Review ID is the stable inherited ReviewCycle identity. Before verification, mutable intake belongs to one Working Candidate identified independently of Review Version. A new Review starts with a Working Candidate at `Draft`; after both source roles are bound it advances to `Data Uploaded`. Source binding persists a last-known path hint, source fingerprint, filename/provenance, selecting Actor ID/time, and document role, never source workbook bytes.

Explicit confirmation of a compatible Working Candidate creates and seals the next monotonically increasing Review Version as the user-facing identity of exactly one inherited ReviewGeneration with the same sequence number. Its `creation_reason` is `INITIAL_VERIFICATION` for the first confirmed basis, `SOURCE_REVERIFICATION` when source bytes or reviewed Current Validation Values change, or `EXTRACTOR_REVERIFICATION` when the extractor basis changes. It records fresh verification Actor/time, verified fingerprint, extractor version, source fingerprints, correction basis, creator Actor/time, and predecessor when applicable.

A governed rule-set or configuration change over an unchanged verified basis creates a working successor Review Version/ReviewGeneration with `RULESET_REANALYSIS` or `CONFIG_REANALYSIS`. It inherits the original verification Actor/time, verified fingerprint, extractor version, source fingerprints, and correction basis; records the verification-basis and predecessor generations plus its separate creator/time; and never claims that a new human verification occurred. Exact replay with unchanged data, rules, and configuration recomputes and compares the §2.6 projection, appends a Replay Verification Event, and creates neither a Review Version nor another authoritative Validation Run. Promotion creates neither.

A Review Version/ReviewGeneration owns zero authoritative Validation Runs before validation starts and exactly one thereafter; a second authoritative run is prohibited. Validation Run ID uniquely identifies that execution and binds Review ID/version/generation, Rule Set Version, initiating Actor ID, input/verified fingerprint, start timestamp, completion timestamp, and terminal persistence status. Protected Baseline Version is the immutable globally effective manifest containing exactly one governed rule/configuration version for each protected Rule ID plus severity/status-policy versions and effective timestamp. Rule Set Version is the immutable workspace-scoped ordered manifest of one Protected Baseline Version and the exact selected Rule IDs, rule versions, configuration versions, binding versions, enabled states, classifications, and status-policy version. A Validation Run pins one existing Rule Set Version; multiple generations may reference it while configuration is unchanged. Validation Timestamp is the persisted Validation Run completion timestamp.

Review Status is the user-facing operational progression across the candidate/generation boundary. Every status event records Actor ID, timestamp, and reason:

| Owner | Review Status | Entry condition |
|---|---|---|
| Working Candidate | `Draft` | New review or fresh changed-data work begins |
| Working Candidate | `Data Uploaded` | Both required source roles are bound |
| Review Version | `Data Reviewed` | Candidate confirmation creates a verification generation, or governed reanalysis creates an inherited-basis generation |
| Review Version | `Validation Complete` | Its one complete Rule Result ledger and all Rule Executions persist; generation analytical state is at least `ANALYZED` |
| Review Version | `Reviewed` | Reviewer explicitly confirms the summary/details and, for an unpublished successor, promotion succeeds |
| Review Version | `Closed` | Reviewer explicitly completes a `Reviewed` Review Version |
| Review Version | `Archived` | Reviewer archives a `Closed` Review Version |

Review Lifecycle Status is operational workflow state. Overall Review Status is a deterministic financial-validation conclusion and never changes Review Lifecycle Status by itself.

The inherited ReviewCycle disposition `Active` or `Abandoned` remains orthogonal to Review Status, analytical state, publication state, and Overall Review Status. An explicit abandon/resume event records actor/time and changes no candidate, generation, verification, run, result, publication, or lifecycle history; age causes informational reminders only and never an automatic transition or expiry.

A complete run containing `FAIL` or `NOT_EVALUATED` results still enters `Validation Complete`; the lifecycle state means execution completed, not that the financial review passed.

Forward user workflow follows the adjacent statuses in the table, while the candidate-to-generation boundary atomically consumes the confirmed candidate and creates the sealed version at `Data Reviewed`. A source, reviewed-value, or extractor-basis change after `Data Reviewed` creates a linked Working Candidate at `Data Uploaded` when both prior source bindings are inherited, or `Draft` otherwise; fresh confirmation is required before the next Review Version exists. A rule-set/configuration reanalysis may create a version directly at `Data Reviewed` only under the inherited-basis contract above. These are new work/generation creation events, not backward transitions of a prior generation. Every sealed version is read-only; `Closed` and `Archived` add no broader mutation permission.

The ReviewCycle records `working_generation_id` and `published_generation_id`. A new Review Version becomes working. The first generation auto-publishes only after its run reaches `Validation Complete`/`ANALYZED`. A successor remains `Working — Unpublished` until an authorized Reviewer explicitly promotes it at `ANALYZED` or later. Promotion atomically appends a prior-to-successor supersession record, moves the published pointer, records actor/time/reason, and leaves both generations immutable; failure or abandonment leaves the prior published pointer unchanged.

Trusted dashboard, analytics, report, export, and Ask Fin defaults resolve the published generation. The immediate post-validation Review Summary may show the working run under §2.7; historical and explicitly selected analyzed-working contexts are labeled and never mixed with the published context. Reports, exports, and Ask Fin interactions generated for an allowed context are separate append-only Derived Records, not mutations of the Review Version. Each appends a Derived Record Generation Event with Derived Record ID/type, Review ID/version/generation, Validation Run ID, Rule Set Version, publication state, initiating Actor ID, request timestamp, completion timestamp when terminal, terminal status `Completed`, `Failed`, or `Blocked`, and content fingerprint when content exists. Regeneration creates another linked record; it never overwrites an earlier record.

Every export also carries the immutable ADR-015 manifest: Review/period identity; generation ID/sequence and creation reason; verified-dataset fingerprint; Validation Run, Rule Set, configuration, and extractor versions; export timestamp/fingerprint; and working/published/historical or superseded status at creation. A reanalysis export distinguishes inherited original verification Actor/time from reanalysis initiator/time. Live supersession is derived from append-only promotion/supersession records and never rewrites a prior export.

### 2.11 Controlled rule model and optional-rule lifecycle

Every Rule Definition Version records a stable Rule ID, immutable version, name, classification, evaluation grain, allowlisted input fields, controlled evaluator and operands, dependency references, status policy, severity policy, evidence template, recommended human follow-up, test-suite version, lifecycle state, author Actor ID, and timestamps.

The first-release controlled evaluator types are:

- required-field presence and approved-domain parseability;
- exact reference-key membership;
- exact uniqueness or duplicate grouping;
- two-decimal scalar comparison using `=`, `!=`, `<`, `<=`, `>`, or `>=`;
- grouped `SUM` or `COUNT` aggregate comparison and reconciliation;
- finite `ALL` or `ANY` composition of the preceding allowlisted predicates.

Rule definitions cannot contain user-authored code, SQL, scripts, macros, system commands, loops, recursion, unrestricted expressions, fuzzy matching, or fields outside the approved Budget/GED schema. Architecture defines the versioned serialization and safe evaluator implementation without expanding these approved semantics.

A Rule Definition Version has the forward lifecycle `Draft` → `Tested` → `Active` → `Retired`. Creation produces Draft; only Draft may be edited or execute its required test suite. Passing tests permits an authorized actor to advance it to immutable Tested, but does not activate it. A Tested or Active version is immutable; editing it creates a successor Draft version. An ordinary delete request for an Optional Configurable or Informational/Advisory rule is a logical retirement, never physical erasure. Retired versions cannot receive new workspace bindings but remain available to historical runs and replay.

Workspace applicability is a separate versioned Rule Binding with `Enabled` or `Disabled` state. Disabling a binding affects only future Validation Runs for that workspace and never changes a Rule Definition Version or a prior Rule Set Version. After FR-148 tests pass and the version reaches Tested, a Rule Administrator explicitly approves activation of an Optional Configurable or Informational/Advisory version and may then manage its bindings. Protected core versions and bindings follow §2.12 instead.

### 2.12 Protected baseline catalog, severity, and change governance

The first-release protected baseline has these permanent Rule IDs and seed severities:

| Control key | Rule ID | Seed severity |
|---|---|---|
| CORE-01 | `R-VAL-01` | High |
| CORE-02 | `R-VAL-02` | High |
| CORE-03 | `R-VAL-03` | Medium |
| CORE-04 | `R-VAL-04` | High |
| CORE-05 | `R-VAL-05` | High |

Every control rule version declares either a fixed severity or deterministic versioned severity criteria. A Validation Run records the resolved severity policy and result severity. Changing severity criteria creates a governed configuration version; changing evaluation logic creates a successor Rule Definition Version. Every protected-baseline severity change follows the same two-person workflow as a protected logic change.

Every protected-baseline change:

1. begins when a Rule Administrator creates and edits a protected successor while it is Draft, completes its positive/negative/boundary tests, and advances it to immutable Tested;
2. is submitted as a request that references that exact Tested candidate and states its reason, before/after evidence, proposed effective timestamp, and binding effects;
3. is decided by a Financial Control Approver with a different stable Actor ID;
4. becomes effective only by atomically activating the approved Tested candidate and creating its new Protected Baseline Version at the approved timestamp;
5. preserves prior definitions, configurations, Protected Baseline Versions, Rule Set Versions, approvals, and Validation Runs for audit and replay.

A submitted Protected Change Request enters `Pending Approval` and then reaches exactly one terminal decision, `Approved` or `Rejected`. A terminal request cannot be reopened; a revised proposal uses a new request ID linked to the prior request.

A protected action cannot leave a new workspace or upgraded workspace with fewer than all five protected baseline controls active. Disablement, retirement, logical deletion, or replacement of a protected version is therefore permitted only as an atomic governed replacement with an approved active successor for the same protected Rule ID and control purpose. Ordinary or direct object-level physical deletion of protected history is prohibited; the separately confirmed §2.13/FR-201 all-data disposal may remove it only as part of the complete local FinSight data scope and retains the permitted content-free tombstone.

Global protected activation creates one new Protected Baseline Version and changes zero existing workspace Rule Set Versions. A new workspace derives its initial Rule Set Version from the Protected Baseline Version effective at creation. An optional/advisory binding change creates a successor Rule Set Version only for the affected workspace and creates no Protected Baseline Version. Applying a newer Protected Baseline Version to an existing workspace requires explicit Financial Control Approver authorization and atomically creates a successor Rule Set Version for only that workspace; other workspaces and all historical runs remain unchanged. Each resulting validation requires a new Review Version and Validation Run.

### 2.13 First-release reporting and Windows data-lifecycle outcomes

The first release requires:

- a printable Review Summary and PDF report;
- spreadsheet-compatible exports of Findings, Rule Results, and summarized financial data;
- the on-screen rule-change comparison in FR-151 as a Should-priority capability.

An audit-history export is Should priority. A workbook-compatible tracker export remains release 2 scope. A rule-change comparison export is not required in the first release. Architecture and UX may select CSV, XLSX, or another spreadsheet-compatible representation provided the required content, identity block, evidence links, and deterministic-result lineage are preserved.

A supported Windows upgrade retains all FinSight user data. Uninstall retains user data by default and may remove it only after a separate, explicit, confirmed user choice that identifies the affected data. Upgrade or uninstall never silently deletes review, rule, approval, audit, or replay evidence.

Root NFR-017 remains the narrow exception to ordinary read-only retention: a Reviewer may request permanent disposal of one complete authorized review, one complete authorized reporting period, or all locally stored FinSight data. FinSight presents the exact scope and impact, requires a separate explicit confirmation, removes the complete selected scope rather than individual records, and retains only an audit tombstone recording actor, time, scope category, reason, confirmation, and outcome without retaining deleted financial content. The selected scope includes FinSight-managed backup and recovery copies, which cannot later resurrect disposed content. Separately exported backup files outside FinSight's control are identified in the confirmation impact and remain subject to the organization's external-copy policy. This governed whole-scope disposal is not an edit to a `Closed` or `Archived` Review Version and cannot be used to rewrite only unfavorable evidence.

### 2.14 Ask Fin grounding contract

For one review-specific response, the Approved Grounding Corpus is the finite, immutable set of identity fields, Rule Executions, Rule Results, Findings, confirmed `VerifiedDataset` values/provenance, and source-evidence excerpts explicitly selected from one Validation Run. Records from another run, unconfirmed Working Dataset values, general model knowledge, and unapproved external content are outside that corpus. Product-help guidance uses a separate finite, versioned, human-approved product-help corpus and cannot be presented as review evidence.

The default selected run is the published Review Version's run. A Reviewer may explicitly select one analyzed working or historical run; the response identifies `Working — Unpublished` or `Historical` as applicable. One response uses exactly one ReviewVersion/ReviewGeneration and never combines records from working, published, or historical generations.

Every review-specific response is represented as atomic Claim Records. Each Claim Record has a stable Claim ID, structured subject/predicate/value, the exact supporting corpus record/field IDs, and rendered text. Before presentation, the system verifies that every structured value equals or is a deterministic projection of its cited corpus values. A claim that does not satisfy that check is omitted or explicitly labeled `Unsupported by selected review evidence`; it is never rendered as a supported financial fact. The persisted response audit records the corpus version, every displayed Claim ID/citation, and every blocked claim without retaining hidden model reasoning.

## 3. Guided review, intake, and metadata

### FR-123 — Review entry actions
- **Statement (EARS):** WHEN FinSight opens, THE SYSTEM SHALL present the WF-01 welcome action set with Create New Review available and View Past Reviews enabled only when at least one prior review exists.
- **Rationale:** The approved workflow begins with one clear choice while avoiding a dead action for first-time users.
- **Source:** stakeholder (HD-15; WF-01); extends root FR-081.
- **Priority:** Must
- **Dependencies:** Review-history availability; WF-01.
- **Acceptance criteria:**
  - Given no saved review exists, When FinSight opens, Then Create New Review is available and View Past Reviews is disabled with an explanation.
  - Given at least one saved review exists, When FinSight opens, Then both actions are available.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-124 — Reporting-period selection
- **Statement (EARS):** WHEN a user starts a new review, THE SYSTEM SHALL require selection of one reporting month and one reporting year before source upload.
- **Rationale:** The selected period is part of review identity and provides the user-owned value against which file evidence is checked.
- **Source:** stakeholder (HD-14, HD-15; WF-02); extends root FR-005 and FR-006.
- **Priority:** Must
- **Dependencies:** V1 reporting-period contract §11.3.
- **Acceptance criteria:**
  - Given a valid month and year are selected, When the user continues, Then the new review records that selection.
  - Given either value is absent, When the user attempts to continue, Then source upload is not entered and the missing selection is identified.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-125 — Guided workflow progression
- **Statement (EARS):** WHEN a review attempts to advance, THE SYSTEM SHALL allow only the next workflow and Review Lifecycle Status transition permitted by WF-01 through WF-11 and §2.10.
- **Rationale:** FinSight remains a guided review assistant rather than a collection of independent tools.
- **Source:** stakeholder (HD-15, HD-26; WF-01–WF-11); extends root FR-006 and FR-081.
- **Priority:** Must
- **Dependencies:** FR-123, FR-124, FR-128, FR-134, FR-135, FR-139, FR-152; §2.10.
- **Acceptance criteria:**
  - Given every prerequisite for a workflow step is satisfied, When the user advances, Then the review enters only the next permitted state.
  - Given any prerequisite is not satisfied, When the user attempts to advance, Then the review remains in its current state and identifies each blocking prerequisite.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-126 — Two-source-role MVP intake
- **Statement (EARS):** WHILE FinSight operates the first configurable-rule-engine MVP, THE SYSTEM SHALL present exactly two required source roles: Budget Report and GED Report.
- **Rationale:** The approved MVP focuses on the paired financial sources used by the five baseline controls.
- **Source:** stakeholder (HD-15; WF-03); narrows root FR-004 presentation for this MVP without deleting future document support.
- **Priority:** Must
- **Dependencies:** Root FR-001, FR-003, FR-004, FR-007.
- **Acceptance criteria:**
  - Given a new V2 review, When its upload step opens, Then one Budget Report slot and one GED Report slot are shown.
  - Given the same step, When the available upload roles are inspected, Then invoice, PO, SOW, rate-card, resource-sheet, and other source roles are absent.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-127 — Source processing status
- **Statement (EARS):** WHEN a required source is selected, THE SYSTEM SHALL display its filename, assigned source role, upload status, workbook-compatibility status, extraction status, and detected structural issues.
- **Rationale:** Users need to know whether a file is usable and what must be corrected before validation.
- **Source:** stakeholder (HD-15; WF-03); extends root FR-007, FR-010, FR-021, and FR-025.
- **Priority:** Must
- **Dependencies:** Approved Budget/GED compatibility contracts; FR-126.
- **Acceptance criteria:**
  - Given a compatible source, When processing completes, Then each status is shown as successful with the selected filename and source role.
  - Given a source has a missing required sheet or column, When processing completes, Then compatibility is unsuccessful and the exact structural issue is shown.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-128 — Paired-source validation prerequisite
- **Statement (EARS):** WHEN deterministic cross-file validation is requested, THE SYSTEM SHALL require one compatible, extracted, and user-confirmed Budget Report and one compatible, extracted, and user-confirmed GED Report.
- **Rationale:** Cross-file controls cannot produce trustworthy results from an absent, incompatible, or unverified side of the comparison.
- **Source:** stakeholder (HD-15; WF-03, WF-05–WF-07); extends root FR-007, FR-021, FR-026, and FR-029.
- **Priority:** Must
- **Dependencies:** FR-126, FR-127, FR-134, FR-135, FR-139, FR-141.
- **Acceptance criteria:**
  - Given both required sources satisfy every prerequisite, When validation is requested, Then the request may enter the deterministic engine.
  - Given either source fails one prerequisite, When validation is requested, Then execution does not begin and every failed prerequisite is identified.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-129 — Department-evidence extraction
- **Statement (EARS):** WHEN a required report contains department evidence, THE SYSTEM SHALL resolve its report-level Department Number and display Department Name under §11.2 while preserving every raw value and source-cell lineage.
- **Rationale:** The workspace must identify the department automatically from evidence whenever the source provides it.
- **Source:** stakeholder (HD-12, HD-13; WF-03, WF-04); extends root FR-011, FR-014, and FR-015.
- **Priority:** Must
- **Dependencies:** `SLV-001`; V1 identity contract §11.2.
- **Acceptance criteria:**
  - Given the Budget Grand Total and GED department-total rows contain valid department identifiers, When extraction completes, Then their normalized report-level identifiers, raw values, and lineage are retained.
  - Given exactly one distinct nonblank GED Department Name occurs among detail rows matching the GED report-level Department Number, When extraction completes, Then that raw name is displayed with its lineage.
  - Given no matching nonblank name or more than one distinct matching name exists, When extraction completes, Then Department Name is visibly absent or conflicting under §11.2 and no sample name is inferred.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-130 — Reporting-period-evidence extraction
- **Statement (EARS):** WHEN a required report contains approved reporting-period evidence, THE SYSTEM SHALL extract a normalized reporting month/year while preserving the raw value and source-cell lineage.
- **Rationale:** Selected and source-reported periods must be compared from evidence rather than filenames or transaction maxima unless expressly approved.
- **Source:** stakeholder (HD-14; WF-02–WF-04); extends root FR-005, FR-010, FR-014, and FR-015.
- **Priority:** Must
- **Dependencies:** `SLV-001`; V1 reporting-period contract §11.3.
- **Acceptance criteria:**
  - Given GED row 3 matches the exact §11.3 `Year-To-Date for Period {Full English Month Name} {four-digit year}` grammar, When extraction completes, Then its normalized month/year, raw text, and lineage are retained.
  - Given GED row 3 does not match that grammar, When extraction completes, Then period evidence is recorded as malformed with cell lineage and the period gate remains unsatisfied.
  - Given no approved report-period source is present, When extraction completes, Then the period is recorded as absent and no transaction maximum or run date is silently substituted.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-131 — Pre-validation metadata summary
- **Statement (EARS):** WHEN a review reaches its pre-validation metadata step, THE SYSTEM SHALL display the Validation Workspace metadata summary defined in §2.1.
- **Rationale:** The user must see the department, period, sources, record population, and inconsistencies before trusting a run.
- **Source:** stakeholder (HD-13–HD-15; WF-03, WF-04); extends root FR-010, FR-025, and FR-027.
- **Priority:** Must
- **Dependencies:** FR-127, FR-129, FR-130, FR-134, FR-135.
- **Acceptance criteria:**
  - Given both files completed extraction, When the metadata step opens, Then every defined field is displayed with its evidence status.
  - Given any metadata field is absent or conflicting, When the summary is displayed, Then the field is visibly absent or conflicting and is not replaced with sample data.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-132 — Workbook-structure blocking diagnostics
- **Statement (EARS):** IF a required workbook cannot be classified into the approved Budget or GED structure, THEN THE SYSTEM SHALL block dependent validation and identify each missing or ambiguous structural element.
- **Rationale:** Incorrect row or column interpretation can create silent financial misstatements.
- **Source:** stakeholder (WF-03, WF-04); root FR-007, FR-013, FR-021, and NFR-062.
- **Priority:** Must
- **Dependencies:** Approved real-layout reader contracts.
- **Acceptance criteria:**
  - Given every required structural element is unambiguous, When compatibility is assessed, Then the workbook may proceed to extraction.
  - Given a required header, detail-row boundary, or row-type rule is missing or ambiguous, When compatibility is assessed, Then dependent validation is blocked with the affected element and source location.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-133 — Department-neutral execution
- **Statement (EARS):** WHEN compatible reports identify any department or business unit, THE SYSTEM SHALL apply the same active rule definitions without a department allow-list or department-specific logic path.
- **Rationale:** The supplied department is a sample; the product must work for every compatible department.
- **Source:** stakeholder (HD-12, HD-18; workflow contract); extends root FR-030, FR-043, and NFR-043.
- **Priority:** Must
- **Dependencies:** FR-129, FR-134; rule definitions.
- **Acceptance criteria:**
  - Given two equivalent fixtures differing only in valid department identity, When the same rule versions execute, Then the ordered rule behaviors differ only in the identity/evidence carried by results.
  - Given the sample department is absent from configuration, When another compatible department is reviewed, Then no rule or workflow becomes unavailable because of its name or number.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-134 — Department-mismatch gate
- **Statement (EARS):** IF the resolved Budget and GED department identities conflict, THEN THE SYSTEM SHALL block cross-file validation and display the conflicting values with their source evidence.
- **Rationale:** Joining different departments would make every cross-file financial conclusion untrustworthy.
- **Source:** stakeholder (HD-13; WF-04); extends root FR-021, FR-022, and FR-026.
- **Priority:** Must
- **Dependencies:** V1 identity contract §11.2.
- **Acceptance criteria:**
  - Given the two reports resolve to the same identity under the approved policy, When consistency is checked, Then no department mismatch is recorded.
  - Given they resolve to different identities, When consistency is checked, Then validation remains blocked and both source references are shown.
  - Given the canonical Department Numbers agree but one source lacks a name or supplies a truncated name, When consistency is checked, Then the reports remain compatible and the raw GED name is displayed as source-provided evidence without invented expansion.
  - Given one GED detail transaction contains a different but parseable Department Number while the authoritative GED department-total number matches Budget, When consistency is checked, Then intake is not blocked by that row and CORE-02 evaluates its exact transaction key.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-135 — Reporting-period-mismatch gate
- **Statement (EARS):** IF the selected reporting period conflicts with resolved period evidence from either required report, THEN THE SYSTEM SHALL block cross-file validation and display the conflicting values with their source evidence.
- **Rationale:** Files from different review periods cannot safely feed the same validation run.
- **Source:** stakeholder (HD-14; WF-02, WF-04); extends root FR-005 and FR-026.
- **Priority:** Must
- **Dependencies:** V1 reporting-period contract §11.3.
- **Acceptance criteria:**
  - Given selected and extracted periods agree, When consistency is checked, Then no period mismatch is recorded.
  - Given any resolved period conflicts, When consistency is checked, Then validation remains blocked and all conflicting evidence is shown.
  - Given the Budget source has no reporting-period field under `SLV-001`, When consistency is checked, Then it is explicitly bound to the selected workspace period with `workspace-assigned/no source period` evidence.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

## 4. Working-data review and confirmation

### FR-136 — Budget and GED review views
- **Statement (EARS):** WHEN both reports complete extraction, THE SYSTEM SHALL present separate Budget and GED working-data views with the browse, search, filter, sort, and source-lineage behavior already approved by root FR-027 and FR-102.
- **Rationale:** Users must inspect what the engine will consume before confirmation.
- **Source:** stakeholder (HD-15; WF-05); root FR-027, FR-074, and FR-102.
- **Priority:** Must
- **Dependencies:** FR-127, FR-132; extracted records.
- **Acceptance criteria:**
  - Given extracted records exist, When either view opens, Then the user can inspect normalized values and navigate to original source locations.
  - Given a filter or sort is applied, When the view changes, Then stored data and source lineage remain unchanged.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-137 — Review-local correction and reversion
- **Statement (EARS):** WHEN a Reviewer saves or reverts an extracted-field correction on a Working Candidate, THE SYSTEM SHALL append only the review-local correction-basis event under §2.9 while preserving the Original Extracted Value and source workbook unchanged.
- **Rationale:** Users may correct extraction without destroying evidence or writing back to the report.
- **Source:** stakeholder (HD-15, HD-24; WF-05); root FR-003, FR-015, and FR-028.
- **Priority:** Must
- **Dependencies:** Working Dataset value-provenance contract §2.9; FR-136.
- **Acceptance criteria:**
  - Given any extracted Budget or GED row-level business field, When a Reviewer saves a replacement scalar—including blank or text that a rule may later find unparseable—Then a new pending edit version carries that exact reviewed value while the original/source remain available.
  - Given a saved correction, When it is reverted, Then the working value returns to the extracted value without deleting the audit history.
  - Given system provenance or a row insertion/deletion request, When mutation is attempted, Then the Working Dataset structure, lineage, audit history, and source remain unchanged.
  - Given a Review Version is already Data Reviewed or later, When a Reviewer starts a correction or reversion, Then FR-196 creates a successor Working Candidate rather than mutating the sealed version.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-138 — Correction audit detail
- **Statement (EARS):** WHEN a review-local correction is saved or reverted, THE SYSTEM SHALL append an audit record containing event ID, Review ID, Working Candidate ID, stable Actor ID, identity source, domain-qualified account, timestamp, dataset, source reference, field, Original Extracted Value, prior User-Reviewed Value, resulting User-Reviewed Value, confirmation state, supplied reason/comment, correction-basis version, and linked reversal-event ID when applicable.
- **Rationale:** Every value used for validation must be attributable and reconstructable.
- **Source:** stakeholder (HD-15, HD-23, HD-24; WF-06); extends root FR-028 and FR-085.
- **Priority:** Must
- **Dependencies:** MVP actor-identity contract §2.8; FR-137.
- **Acceptance criteria:**
  - Given a correction is saved, When its audit entry is inspected, Then every defined field is present and linked to the Working Candidate and correction-basis version.
  - Given that Working Candidate is later confirmed, When its audit is inspected, Then an immutable confirmation record links the candidate's exact correction-basis version and included correction event IDs to the created Review Version without rewriting any event.
  - Given a correction is reverted, When history is inspected, Then both the original correction and the reversion remain present.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-139 — Edit-confirmation gate
- **Statement (EARS):** WHILE any review-local correction in the current Working Candidate is unconfirmed by a Reviewer, THE SYSTEM SHALL prevent creation of its Review Version and entry into validation.
- **Rationale:** Validation must never use edits the user has not explicitly reviewed and accepted.
- **Source:** stakeholder (HD-15, HD-21, HD-24; WF-06, WF-07); extends root FR-026, FR-028, and FR-029.
- **Priority:** Must
- **Dependencies:** FR-137, FR-138; exact confirmation text from WF-06.
- **Acceptance criteria:**
  - Given at least one unconfirmed correction, When validation is requested, Then execution is blocked and confirmation is requested.
  - Given the user selects the required confirmation and saves, When the candidate-to-generation transition succeeds, Then the created sealed Review Version may satisfy this gate.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-140 — Confirmation without artificial edits
- **Statement (EARS):** WHEN a Reviewer confirms a Working Candidate containing no corrections, THE SYSTEM SHALL create its sealed Review Version and verification record without creating a correction record.
- **Rationale:** Audit history should reflect real actions rather than synthetic edits.
- **Source:** stakeholder (HD-15, HD-21; WF-06); extends root FR-026 and FR-029.
- **Priority:** Must
- **Dependencies:** FR-136; root verification decision contract.
- **Acceptance criteria:**
  - Given no correction exists, When the user confirms the data, Then one Review Version/ReviewGeneration and verification record are created and the correction count remains zero.
  - Given a correction exists, When confirmation occurs, Then FR-138 and FR-139 apply.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

## 5. Configurable rule governance

### FR-141 — Governed rule classification
- **Statement (EARS):** WHEN a rule version is created, THE SYSTEM SHALL assign exactly one classification defined in §2.4.
- **Rationale:** Governance, lifecycle, and reporting behavior depend on an explicit classification.
- **Source:** stakeholder (HD-03; WF-07); extends root FR-103, FR-106, and FR-107.
- **Priority:** Must
- **Dependencies:** Classification definitions; MVP role policy §2.8.
- **Acceptance criteria:**
  - Given one valid classification, When a version is saved, Then that classification is retained with the version.
  - Given zero or multiple classifications, When save is attempted, Then the version is rejected with an actionable message.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-142 — One deterministic execution path
- **Statement (EARS):** WHEN any active rule executes, THE SYSTEM SHALL execute it through the common deterministic, versioned rule-engine contract regardless of classification.
- **Rationale:** A single path prevents hard-coded core checks and conflicting versions of financial truth.
- **Source:** stakeholder (HD-02, HD-03, HD-05; WF-07); extends root FR-086 and NFR-044.
- **Priority:** Must
- **Dependencies:** FR-141, FR-153; controlled rule model §2.11.
- **Acceptance criteria:**
  - Given one active rule of each classification, When a run executes, Then each produces the same Rule Result contract.
  - Given a consumer requests a financial validation outcome, When the source is traced, Then no classification-specific calculation path exists outside the engine.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-143 — Protected core binding
- **Statement (EARS):** WHEN a Validation Workspace is created, THE SYSTEM SHALL bind the five protected core-rule versions as active and unavailable to ordinary modification, disablement, deletion, or replacement.
- **Rationale:** Every new workspace starts with the mandatory baseline controls intact.
- **Source:** stakeholder (HD-04, HD-11, HD-18; WF-07); refines root FR-106.
- **Priority:** Must
- **Dependencies:** FR-141; protected baseline contract §2.12; MVP role policy §2.8.
- **Acceptance criteria:**
  - Given a new workspace, When its active rule set is inspected, Then all five core rules and versions are present.
  - Given a new workspace, When its initial Rule Set Version is created, Then it references the Protected Baseline Version effective at workspace creation.
  - Given an ordinary user action, When it attempts any protected mutation, Then the request is denied and the baseline remains unchanged.
  - Given a protected successor has become effective, When a new workspace is created, Then its Rule Set Version references the new Protected Baseline Version while every earlier workspace retains its prior Rule Set Version until explicitly upgraded.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-144 — Governed core-rule change
- **Statement (EARS):** WHEN a Financial Control Approver with a different stable Actor ID approves a Pending Approval request that references an immutable Tested protected candidate, THE SYSTEM SHALL record the approval and schedule or atomically activate that exact candidate under §2.12 while retaining the prior version and complete decision evidence.
- **Rationale:** Core policy must evolve without erasing historical meaning or bypassing governance.
- **Source:** stakeholder (HD-04, HD-11, HD-18, HD-21, HD-22); extends root FR-086, FR-106, and FR-107.
- **Priority:** Must
- **Dependencies:** MVP role policy §2.8; protected baseline contract §2.12.
- **Acceptance criteria:**
  - Given a Rule Administrator-authored Tested candidate and approval by a different Financial Control Approver Actor ID, When the effective timestamp is reached, Then that exact candidate becomes Active and the old version remains replayable.
  - Given requester and approver resolve to the same stable Actor ID, either required role was not effective for its action, or the referenced candidate is not immutable Tested, When approval is attempted, Then no approval, activation, or baseline binding is created.
  - Given a completed historical run, When the successor activates, Then the historical run still resolves the prior rule version.
  - Given a requested protected disablement, retirement, logical deletion, or replacement lacks a tested active successor for the same protected control, When approval or activation is attempted, Then the request is denied.
  - Given all approved conditions are satisfied, When the effective timestamp is reached, Then successor activation, prior-version retirement, and one new Protected Baseline Version are persisted atomically or none takes effect, and zero existing workspace Rule Set Versions change.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-145 — Optional-rule lifecycle
- **Statement (EARS):** WHEN a Rule Administrator changes an Optional Configurable or Informational/Advisory rule, THE SYSTEM SHALL apply the Rule Definition Version lifecycle and separate Rule Binding state defined in §2.11.
- **Rationale:** Business users need controlled evolution while historical evidence remains reproducible.
- **Source:** stakeholder (HD-02, HD-03, HD-21; AR-01; WF-07, WF-11); extends root FR-103, FR-106, and FR-107.
- **Priority:** Must
- **Dependencies:** Controlled rule model §2.11; MVP role policy §2.8.
- **Acceptance criteria:**
  - Given a Draft version passes its required tests, When an authorized Rule Administrator advances it, Then it becomes immutable Tested but remains non-active.
  - Given an Optional Configurable or Informational/Advisory version is Tested, When a Rule Administrator explicitly approves activation, Then it becomes Active and may receive a workspace binding without creating a Protected Baseline Version.
  - Given a Tested or Active version is edited, When the change is saved, Then a successor Draft is created and the prior version remains unchanged.
  - Given an enabled workspace binding is disabled, When a later run starts, Then the rule is not selected for that run while prior Rule Set Versions remain unchanged.
  - Given an optional or advisory binding changes in one workspace, When the change commits, Then a successor Rule Set Version is created only for that workspace and no Protected Baseline Version is created.
  - Given a version is Retired, When a new binding is attempted, Then the binding is rejected while historical replay remains available.
  - Given a prohibited transition or unauthorized actor, When attempted, Then no version or binding behavior changes.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-146 — Advisory-result distinction
- **Statement (EARS):** WHEN an Informational/Advisory rule produces OBSERVATION or NO_OBSERVATION, THE SYSTEM SHALL present and export that outcome distinctly from PASS, FAIL, and a financial-control Finding.
- **Rationale:** Advice must not be mistaken for a failed control.
- **Source:** stakeholder (HD-03; WF-07–WF-09).
- **Priority:** Must
- **Dependencies:** Rule classifications §2.4; V1 status policy §2.7.
- **Acceptance criteria:**
  - Given an advisory observation, When results are viewed or exported, Then it is labeled advisory and is not rendered as a failed core control.
  - Given an advisory scope has no configured observation, When results are viewed or exported, Then it is labeled NO_OBSERVATION rather than PASS or omitted.
  - Given a control failure, When displayed beside an advisory observation, Then users can distinguish status and governance meaning without relying on color alone.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-147 — Controlled rule-definition validation
- **Statement (EARS):** IF a proposed rule definition uses a field, operator, evaluator type, or expression outside the approved controlled rule model, THEN THE SYSTEM SHALL reject it before testing or activation.
- **Rationale:** Configurability must not become arbitrary code execution or undefined financial behavior.
- **Source:** stakeholder (HD-02, HD-03; Product Owner principle P-06; AR-02).
- **Priority:** Must
- **Dependencies:** Controlled rule model §2.11.
- **Acceptance criteria:**
  - Given a definition using only approved elements, When it is validated, Then it may proceed to testing.
  - Given Python, SQL, scripts, macros, system commands, or unrestricted expressions, When validation is attempted, Then the definition is rejected and none executes.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-148 — Rule activation tests
- **Statement (EARS):** WHEN activation of a rule version is requested, THE SYSTEM SHALL require successful definition validation and approved positive, negative, and boundary test results for that version.
- **Rationale:** A rule should not affect financial results before its expected behavior is demonstrated.
- **Source:** stakeholder (HD-11; AR-04; WF-07); extends root FR-086 and NFR-036.
- **Priority:** Must
- **Dependencies:** FR-147; MVP role policy §2.8; test fixtures.
- **Acceptance criteria:**
  - Given every required test passes and the applicable activation approval is present, When activation is requested, Then the Tested version may become Active.
  - Given any required test fails or is absent, When activation is requested, Then the version remains non-active with the blocking tests identified.
  - Given an Optional Configurable or Informational/Advisory Draft passes its tests, When a Rule Administrator advances it, Then it becomes Tested and requires a separate Rule Administrator activation approval.
  - Given a protected-baseline successor, When tests pass, Then activation still requires the two-person approval and effective-time contract in §2.12.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-149 — Used rule-version retention
- **Statement (EARS):** WHEN a validation run first references a rule version, THE SYSTEM SHALL retain that exact version and configuration for audit and deterministic replay.
- **Rationale:** Editing current policy must not change what a past result meant.
- **Source:** stakeholder (HD-04, HD-11; WF-11); extends root FR-079, FR-086, and FR-107.
- **Priority:** Must
- **Dependencies:** Rule/version storage; retention policy.
- **Acceptance criteria:**
  - Given a completed run and a successor rule version, When the run is replayed, Then it uses the original referenced version.
  - Given a used version, When ordinary deletion is requested, Then historical definition and evidence remain retained.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-150 — Rule-library visibility
- **Statement (EARS):** WHEN an authorized user opens the Rule Library, THE SYSTEM SHALL display each rule's ID, name, classification, lifecycle state, active version, dependencies, last change, and workspace applicability.
- **Rationale:** Users must understand which governed rules exist and what will execute.
- **Source:** stakeholder (HD-02–HD-04; AR-01); extends root FR-103, FR-106, and FR-107.
- **Priority:** Must
- **Dependencies:** MVP role policy §2.8; rule metadata model.
- **Acceptance criteria:**
  - Given rules across all classifications and states, When the library opens, Then every defined metadata field is visible.
  - Given an unauthorized user, When protected administration detail is requested, Then visibility follows the approved authorization policy without hiding the active controls used by their review.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-151 — Rule-change impact comparison
- **Statement (EARS):** WHEN a user creates a governed `RULESET_REANALYSIS` or `CONFIG_REANALYSIS` over an unchanged verified basis, THE SYSTEM SHALL identify which Rule Results and Findings were added, removed, or changed between the predecessor and successor runs.
- **Rationale:** Users need to see the consequence of a rule change without overwriting either result set.
- **Source:** stakeholder (AR-01; Product Owner brief §7); extends root FR-079 and FR-107.
- **Priority:** Should
- **Dependencies:** First-release reporting contract §2.13; FR-149, FR-153, FR-171.
- **Acceptance criteria:**
  - Given two runs differing only by rule-set version, When compared, Then added, removed, and changed outcomes are identified with both versions.
  - Given the successor is created, When its provenance is inspected, Then it inherits the predecessor's original verification basis, records the reanalysis initiator separately, and remains working/unpublished until FR-202 succeeds.
  - Given either run is missing, When comparison is requested, Then no inferred comparison is shown.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

## 6. Deterministic execution and result ledger

### FR-152 — Confirmed-data rule execution
- **Statement (EARS):** WHEN validation starts, THE SYSTEM SHALL execute the five protected core rules and every other active workspace rule against one immutable confirmed Review Version and one immutable Rule Set Version.
- **Rationale:** Users need a transparent run over the exact data and rule set they confirmed.
- **Source:** stakeholder (HD-03, HD-11, HD-15, HD-24, HD-25; WF-07); extends root FR-026, FR-081, and FR-086.
- **Priority:** Must
- **Dependencies:** FR-128, FR-139, FR-142, FR-143.
- **Acceptance criteria:**
  - Given all gates pass, When validation starts, Then the Validation Run binds the selected Review Version, Rule Set Version, initiating Actor ID, and Current Validation Values.
  - Given a selected Review Version, When validation is requested after its authoritative run already exists, Then no second authoritative run is created; exact replay follows FR-173.
  - Given the Working Dataset or rule set changes during a run, When the run completes, Then its records still reference the immutable versions captured at start.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-153 — Complete Rule Result ledger
- **Statement (EARS):** WHEN a validation run reaches terminal result persistence, THE SYSTEM SHALL persist exactly one ordered Rule Result for every enumerated expected rule-and-scope pair under the §2.2 contract.
- **Rationale:** Findings alone omit successful and blocked controls; the complete ledger is the source of validation truth.
- **Source:** stakeholder (HD-05, HD-11; WF-07, WF-08); extends root FR-069 and FR-086.
- **Priority:** Must
- **Dependencies:** Rule Result contract §2.2; FR-142, FR-152.
- **Acceptance criteria:**
  - Given N expected rule-and-scope pairs, When a run completes normally, Then exactly N ordered Rule Results exist with no duplicate pair.
  - Given one expected scope cannot evaluate, When the run completes, Then that pair has one NOT_EVALUATED result rather than no record or PASS.
  - Given an advisory expected scope evaluates without producing an observation, When the run completes, Then that pair has one NO_OBSERVATION result rather than PASS or omission.
  - Given intake cannot enumerate expected scopes, When validation is requested, Then the run is blocked before a complete ledger is represented.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-154 — Rule Result provenance
- **Statement (EARS):** WHEN a Rule Result is persisted, THE SYSTEM SHALL populate every provenance field defined in §2.2 that applies to its status.
- **Rationale:** Auditors must reconstruct the inputs, rule version, calculation, and source evidence behind every outcome.
- **Source:** stakeholder (HD-05, HD-11; WF-07, WF-08, WF-11); extends root FR-010, FR-015, FR-071, FR-086, and FR-107.
- **Priority:** Must
- **Dependencies:** FR-138, FR-149, FR-153; actor/time policy.
- **Acceptance criteria:**
  - Given a PASS or FAIL, When its result is opened, Then the run, versions, inputs, evaluated scope, calculation/evaluation evidence, and source references are present.
  - Given NOT_EVALUATED, When opened, Then the blocking dependency and affected scope are present instead of fabricated calculation evidence.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-155 — Dependency-aware not-evaluated result
- **Statement (EARS):** IF a rule-and-scope pair cannot evaluate because a required dependency is missing, invalid, unmapped, or unresolved, THEN THE SYSTEM SHALL persist NOT_EVALUATED with the failed dependency and affected scope.
- **Rationale:** Unavailable evidence must never become a false pass.
- **Source:** stakeholder (HD-05, HD-10, HD-11; WF-07, WF-08); extends root FR-022, FR-024, NFR-062, and FR-086.
- **Priority:** Must
- **Dependencies:** Per-rule dependency contracts; FR-153.
- **Acceptance criteria:**
  - Given a required dependency is unavailable for one expected scope, When the rule executes, Then that scope's status is NOT_EVALUATED and the dependency is named.
  - Given all dependencies are available for one expected scope, When the rule executes, Then that scope returns the status permitted by its classification and versioned logic.
  - Given another scope for the same rule has complete evidence, When the rule executes, Then the unresolved scope does not prevent the complete scope from being evaluated.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-156 — Failed-result Finding
- **Statement (EARS):** WHEN a control rule returns FAIL, THE SYSTEM SHALL create a Finding linked to that Rule Result, rule version, evaluated scope, calculation/evaluation evidence, affected entities, and source evidence.
- **Rationale:** A failed control needs a persistent, investigable exception without replacing the result ledger.
- **Source:** stakeholder (HD-05, HD-11; WF-08); extends root FR-069–FR-071.
- **Priority:** Must
- **Dependencies:** FR-153, FR-154; severity policy §2.12.
- **Acceptance criteria:**
  - Given one control Rule Result returns FAIL, When persistence completes, Then exactly one linked Finding carries the specified evidence for that failed scope.
  - Given a PASS, When persistence completes, Then no failure Finding is fabricated for that result.
  - Given two scopes fail the same rule, When persistence completes, Then each failed scope remains independently traceable even if the UI groups their Findings.
  - Given a rule uses versioned severity criteria, When a Finding is persisted, Then its resolved severity and the exact policy/configuration version are recorded.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-157 — Complete validation-results presentation
- **Statement (EARS):** WHEN a validation run completes, THE SYSTEM SHALL present every selected Rule Execution with its derived status and access to every persisted scope-level Rule Result in the WF-08 results workspace.
- **Rationale:** Users must see control coverage, not only exceptions.
- **Source:** stakeholder (HD-05, HD-11, HD-15; WF-08); extends root FR-074, FR-082, and FR-086.
- **Priority:** Must
- **Dependencies:** FR-153, FR-154, FR-156.
- **Acceptance criteria:**
  - Given a run containing PASS, FAIL, NOT_EVALUATED, OBSERVATION, and NO_OBSERVATION scope results, When results open, Then every selected rule appears exactly once as a Rule Execution and exposes all of its scope results.
  - Given findings exist, When their count is compared with failed scope results, Then each Finding remains linked and does not conceal successful, blocked, or advisory scope results.
  - Given a rule has mixed scope outcomes, When it is displayed, Then its counts and derived status follow the V1 versioned roll-up policy in §2.7.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-158 — Overall validation-status derivation
- **Statement (EARS):** WHEN a run's overall validation status is displayed, THE SYSTEM SHALL derive it exclusively from persisted Rule Executions and Rule Results under the versioned status policy used by that run.
- **Rationale:** Overall status must not be independently recalculated by a dashboard or AI layer.
- **Source:** stakeholder (HD-05; WF-08, WF-09); extends root FR-077 and FR-086.
- **Priority:** Must
- **Dependencies:** FR-153; the V1 status policy in §2.7.
- **Acceptance criteria:**
  - Given a versioned status policy and result set, When overall status is produced repeatedly, Then it is identical and traces to that policy, the Rule Executions, and their Rule Results.
  - Given an advisory OBSERVATION or NO_OBSERVATION outcome or a disabled rule, When V1 status is derived, Then the outcome remains visible but does not change Overall Review Status.
  - Given one Core Mandatory rule has both evaluated and NOT_EVALUATED scopes, When V1 status is derived, Then Overall Review Status is `Incomplete`.
  - Given any Overall Review Status, When Review Summary renders, Then its RAG label/color term follows the one-to-one §2.7 mapping from the same persisted engine status.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

## 7. Five protected baseline controls

### FR-159 — CORE-01 actual spend must not exceed BGT
- **Statement (EARS):** WHEN CORE-01 evaluates a valid Department Number + Account Number scope, THE SYSTEM SHALL assign its terminal status according to the CORE-01 comparison contract in §12.
- **Rationale:** Budget owners need immediate evidence of actual spend beyond the approved planned amount.
- **Source:** stakeholder (HD-06, HD-11); extends root FR-030, FR-031, and FR-033.
- **Priority:** Must
- **Dependencies:** V1 sample-reference contract §11; FR-133–FR-135, FR-155.
- **Acceptance criteria:**
  - Given eligible actual spend is less than BGT, When CORE-01 executes, Then the scope returns PASS.
  - Given eligible actual spend exceeds BGT, When CORE-01 executes, Then the scope returns FAIL with BGT, actual spend, overrun, contributing rows, and source evidence.
  - Given eligible actual spend equals BGT exactly, When CORE-01 executes, Then the scope returns PASS.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-160 — CORE-02 GED transaction must map to Budget
- **Statement (EARS):** WHEN CORE-02 evaluates a GED detail transaction, THE SYSTEM SHALL assign its terminal status according to the CORE-02 mapping contract in §12.
- **Rationale:** Unmapped actual spend cannot be reconciled to an approved budget account.
- **Source:** stakeholder (HD-07, HD-11); extends root FR-022 and FR-042.
- **Priority:** Must
- **Dependencies:** V1 sample-reference contract §11; FR-133–FR-135.
- **Acceptance criteria:**
  - Given a transaction key matches one Budget detail key, When CORE-02 executes, Then the transaction returns PASS.
  - Given no Budget detail key matches, When CORE-02 executes, Then the transaction returns FAIL with its key, journal evidence, amount when available, and source row.
  - Given a key matches only a row classified as a group, subtotal, separator, or Grand Total under the approved layout contract, When CORE-02 executes, Then that row is not treated as a valid detail mapping.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-161 — CORE-03 exact duplicate GED transaction
- **Statement (EARS):** WHEN CORE-03 evaluates each distinct governed material-field fingerprint present in GED detail, THE SYSTEM SHALL assign its complete member set a PASS or FAIL status according to the CORE-03 duplicate contract in §12.
- **Rationale:** Duplicate postings can overstate actual spend, but evidence must remain intact for human review.
- **Source:** stakeholder (HD-08, HD-11); refines root FR-038 and FR-041.
- **Priority:** Must
- **Dependencies:** V1 sample-reference contract §11.
- **Acceptance criteria:**
  - Given a fingerprint has exactly one member, When CORE-03 executes, Then that fingerprint-group scope returns PASS.
  - Given two transactions differ on at least one approved material field, When CORE-03 executes, Then each belongs to its own independently evaluated fingerprint group.
  - Given two or more transactions match every approved material field, When CORE-03 executes, Then one FAIL result identifies every member row and the deterministically calculated exposure or `Unavailable`.
  - Given an equal-and-opposite or event-tagged pair differs on at least one fingerprint field, When CORE-03 executes, Then it is not an exact duplicate based on Journal Number alone.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-162 — CORE-04 required GED fields
- **Statement (EARS):** WHEN CORE-04 evaluates a GED detail transaction, THE SYSTEM SHALL assign its PASS or FAIL status according to the CORE-04 required-field contract in §12.
- **Rationale:** The core validations cannot trust or trace a transaction whose essential identity, period, journal, date, or amount is unavailable.
- **Source:** stakeholder (HD-09, HD-11); extends root FR-013, FR-014, and FR-022.
- **Priority:** Must
- **Dependencies:** V1 sample-reference contract §11.
- **Acceptance criteria:**
  - Given all six fields are present and parseable, When CORE-04 executes, Then the transaction returns PASS.
  - Given any one field is blank, When CORE-04 executes, Then the transaction returns FAIL naming that field and source cell.
  - Given Amount is zero or signed but otherwise valid, When CORE-04 executes, Then Amount passes this rule; value-domain policy belongs to a separate governed rule.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-163 — CORE-05 Budget ATD must equal GED sum
- **Statement (EARS):** WHEN CORE-05 evaluates a valid Department Number + Account Number scope, THE SYSTEM SHALL assign its terminal status according to the CORE-05 reconciliation contract in §12.
- **Rationale:** Budget-reported actuals and source transaction detail must reconcile before downstream budget conclusions are trusted.
- **Source:** stakeholder (HD-10, HD-11); extends root FR-023, FR-030, and FR-031.
- **Priority:** Must
- **Dependencies:** V1 sample-reference contract §11; FR-133–FR-135.
- **Acceptance criteria:**
  - Given Budget ATD equals the eligible GED sum under the approved policy, When CORE-05 executes, Then the scope returns PASS.
  - Given the values differ, When CORE-05 executes, Then the scope returns FAIL with ATD, GED sum, difference, contributing rows, and source evidence.
  - Given a GED row has the same exact valid key as a Budget scope but its Amount or Fiscal Period is missing or invalid, When CORE-05 executes, Then only that Budget scope returns NOT_EVALUATED.
  - Given a GED row has no exact Budget key, When CORE-05 executes, Then the row never joins by Account Number alone, CORE-02 owns its mapping outcome, and every valid Budget scope remains independently evaluable.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-164 — Dependency-aware core outcomes
- **Statement (EARS):** IF an enumerated core-control scope's required data, mapping, department, or period dependency is unresolved, THEN THE SYSTEM SHALL return NOT_EVALUATED for that dependent scope rather than PASS.
- **Rationale:** A control is not satisfied merely because evidence needed to test it is unavailable.
- **Source:** stakeholder (HD-05, HD-10, HD-11); WF-07, WF-08.
- **Priority:** Must
- **Dependencies:** FR-155; per-core dependency map.
- **Acceptance criteria:**
  - Given a prerequisite fails, When a dependent core rule executes, Then its result is NOT_EVALUATED and cites the prerequisite.
  - Given every prerequisite passes, When the core rule executes, Then it returns PASS or FAIL under its own logic.
  - Given an unmapped GED transaction has no corresponding Budget-key scope, When dependency handling runs, Then CORE-02 evaluates that transaction and no phantom or account-only CORE-01/CORE-05 scope is created.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

## 8. Results consumers, Ask Fin, and saved reviews

### FR-165 — Validation-derived consumer source
- **Statement (EARS):** WHEN FinSight displays or exports a pass/fail, risk, exception, reconciliation, or validation conclusion, THE SYSTEM SHALL obtain that conclusion from persisted Rule Executions and Rule Results.
- **Rationale:** The engine must remain the single source of validation truth across every product surface.
- **Source:** stakeholder (HD-05, HD-18; WF-09); extends root FR-030, FR-043, FR-076, FR-077, FR-117, and FR-120.
- **Priority:** Must
- **Dependencies:** FR-153, FR-154.
- **Acceptance criteria:**
  - Given any validation conclusion on a dashboard, report, export, KPI, or summary, When its lineage is followed, Then it resolves to one or more persisted Rule Executions and Rule Results.
  - Given no Rule Execution or Rule Result supports a conclusion, When a consumer renders, Then the conclusion is absent or explicitly unavailable rather than independently calculated.
  - Given a descriptive aggregate is displayed, When its classification is inspected, Then it is labeled non-validation and cannot replace or override a Rule Result.
  - Given working and published Review Versions differ, When a trusted consumer opens without an explicit historical or analyzed-working selection, Then its validation conclusions resolve only to the published Validation Run.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-166 — Results-based analytics set
- **Statement (EARS):** WHEN validation results exist, THE SYSTEM SHALL provide every WF-09 view defined in §2.5 from recorded Rule Executions, Rule Results, linked evidence, and approved non-validation descriptive aggregates.
- **Rationale:** Users need usable analysis without creating parallel control logic.
- **Source:** stakeholder (HD-05, HD-15; WF-09); extends root FR-030, FR-035, FR-043, FR-076, and FR-078.
- **Priority:** Must
- **Dependencies:** First-release reporting contract §2.13; FR-165.
- **Acceptance criteria:**
  - Given a completed run, When the WF-09 workspace opens, Then all seven views defined in §2.5 are available.
  - Given any required WF-09 view opens, When a validation conclusion is inspected, Then it traces through FR-165.
  - Given a descriptive aggregate is not itself a pass/fail conclusion, When shown, Then it is labeled and does not override a Rule Result.
  - Given a working successor is unpublished, When analytics opens by default, Then it remains scoped to the published Review Version and visibly identifies that a newer working result exists.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-167 — Ask Fin evidence boundary
- **Statement (EARS):** WHEN Ask Fin prepares a review-specific response, THE SYSTEM SHALL permit only atomic Claim Records supported by the finite Approved Grounding Corpus under §2.14.
- **Rationale:** AI explanation must remain downstream of deterministic truth.
- **Source:** stakeholder (HD-05, HD-15, HD-18; WF-10); extends root FR-091, FR-094, and FR-100.
- **Priority:** Must
- **Dependencies:** Approved AI security boundary; FR-153, FR-154.
- **Acceptance criteria:**
  - Given a finite fixture corpus and a response, When every displayed atomic claim is inspected, Then each structured subject/predicate/value resolves exactly to cited fields in that selected run's approved corpus and the unsupported-claim count is zero.
  - Given a candidate claim cites another run, an unconfirmed value, an absent field, or a value not deterministically projected from its citations, When the grounding gate runs, Then the claim is blocked or labeled `Unsupported by selected review evidence` and is not presented as a supported financial fact.
  - Given evidence is absent, When asked, Then Ask Fin identifies that evidence was not found and makes no supported financial claim.
  - Given working and published versions differ, When no explicit analyzed-working selection exists, Then the corpus contains only the published run; when analyzed working is explicitly selected, Then the response identifies it as `Working — Unpublished` and contains no record from the published or another generation.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-168 — Ask Fin citations and edit distinction
- **Statement (EARS):** WHEN Ask Fin returns a review-specific answer, THE SYSTEM SHALL attach citations that identify supporting rules, results, findings, records, source evidence, Original Extracted Values, User-Reviewed Values, and Current Validation Values.
- **Rationale:** Users must verify explanations and understand which value version drove validation.
- **Source:** stakeholder (HD-05, HD-15, HD-24; WF-10); extends root FR-099.
- **Priority:** Must
- **Dependencies:** FR-138, FR-154, FR-167.
- **Acceptance criteria:**
  - Given an answer uses an unedited field, When its citation opens, Then Original Extracted Value, `Not set` User-Reviewed Value, Current Validation Value, and source location are shown.
  - Given an answer uses a confirmed correction, When its citation opens, Then all three value states plus edit/audit evidence are shown.
  - Given a review-specific answer contains multiple financial assertions, When response evidence is inspected, Then each assertion is a separate Claim Record with its own supporting corpus references.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-169 — Ask Fin non-authority
- **Statement (EARS):** THE SYSTEM SHALL deny Ask Fin any capability to create or change source data, Working Dataset values, rules, Rule Results, Findings, severities, approvals, or financial actions.
- **Rationale:** AI explains; deterministic logic and humans retain all financial and governance authority.
- **Source:** stakeholder (HD-05, HD-18; WF-10); root FR-091, FR-093–FR-095.
- **Priority:** Must
- **Dependencies:** Parent Constitution P-8–P-11; security architecture later.
- **Acceptance criteria:**
  - Given any prompt requesting a prohibited change or decision, When Ask Fin responds, Then no product state or deterministic record changes.
  - Given AI is disabled or unavailable, When validation runs, Then all deterministic results and non-AI reports remain complete.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-170 — Ask Fin before completed results
- **Statement (EARS):** WHILE no completed validation result exists for the selected published, historical, or explicitly selected analyzed-working context, THE SYSTEM SHALL limit Ask Fin to product-help guidance and make no review-specific financial claim.
- **Rationale:** There is no deterministic evidence to explain before a run completes.
- **Source:** stakeholder (HD-15; WF-10); extends root FR-094, FR-095, and FR-101.
- **Priority:** Must
- **Dependencies:** Review-state model FR-125.
- **Acceptance criteria:**
  - Given no completed run, When a product-help question is asked, Then Ask Fin may explain how to use FinSight.
  - Given no completed run, When a financial question is asked, Then Ask Fin states that completed validation evidence is unavailable.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-171 — Completed-review authoritative history
- **Statement (EARS):** WHEN a Review Version enters `Closed`, THE SYSTEM SHALL retain its authoritative generation, verification/reconstruction basis, source binding/fingerprints, correction/confirmation records, one Validation Run, Rule Executions, Rule Results, Findings, promotion/supersession and audit evidence, and every separately linked Derived Record under §2.10 as reproducible append-only history.
- **Rationale:** A completed review must remain reconstructable and explainable after rules or files change.
- **Source:** stakeholder (HD-04, HD-05, HD-11, HD-15, HD-25, HD-26; WF-11); extends root FR-079, FR-086, FR-087, and FR-108.
- **Priority:** Must
- **Dependencies:** Retention policy; FR-149, FR-153, FR-154.
- **Acceptance criteria:**
  - Given a Closed Review Version and fingerprint-matching sources, When its data is reopened, Then the `VerifiedDataset` is reconstructed from the recorded extractor/correction basis, its fingerprint matches, and every authoritative record resolves to the exact version recorded at closure.
  - Given its source is missing, mismatched, or extractor-divergent, When the Closed Review Version opens, Then reconstruction is withheld and the recovery state is shown while retained runs, results, findings, audit, and Derived Records remain viewable and unchanged.
  - Given a Closed Review Version becomes Archived or receives a later report, export, or Ask Fin interaction, When its authoritative record set is compared, Then every prior record is unchanged and the new lifecycle or Derived Record Generation Event is separately appended.
  - Given AI history is not permitted by policy, When the authoritative record set is retained, Then its absence is explicit and does not affect deterministic replay.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-172 — Past-review read-only default
- **Statement (EARS):** WHEN a user opens a sealed `Data Reviewed` or later Review Version, THE SYSTEM SHALL present its fingerprint-verified reconstructed business data read-only when available and otherwise preserve access to retained authoritative results under the §2.10 recovery contract.
- **Rationale:** Historical evidence must not be edited in place.
- **Source:** stakeholder (HD-15, HD-26; WF-01, WF-11); extends root FR-079 and FR-108.
- **Priority:** Must
- **Dependencies:** FR-171; user authorization.
- **Acceptance criteria:**
  - Given a Data Reviewed, Validation Complete, Reviewed, Closed, or Archived Review Version, When opened, Then no source, Working Dataset, rule version, result, Finding, prior Derived Record, or audit mutation is available in that version.
  - Given a Draft or Data Uploaded Working Candidate, When resumed by a Reviewer, Then only the mutable actions permitted by §2.9–§2.10 are available.
  - Given matching source bytes are unavailable, When the Review Version opens, Then no data is fabricated, the recovery state is shown, and retained result/evidence records remain read-only.
  - Given an authorized report, export, Ask Fin, rerun, lifecycle transition, or whole-scope disposal action, When it completes, Then it follows its append-only or successor/disposal contract without editing the sealed authoritative record set.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-173 — Historical rerun isolation
- **Statement (EARS):** WHEN a Reviewer requests re-evaluation of a retained Review Version, THE SYSTEM SHALL apply the reason-specific generation or exact-replay behavior in §2.10 while preserving every prior authoritative record unchanged.
- **Rationale:** Re-evaluation should be comparable without rewriting history.
- **Source:** stakeholder (HD-04, HD-11, HD-15, HD-21, HD-26; WF-11); extends root FR-079, FR-086, and FR-107.
- **Priority:** Must
- **Dependencies:** FR-149, FR-151, FR-171, FR-172.
- **Acceptance criteria:**
  - Given the Rule Set Version or governed configuration changes while the verified basis is identical, When reanalysis starts, Then one working successor at `Data Reviewed` records `RULESET_REANALYSIS` or `CONFIG_REANALYSIS`, inherits the exact original verification basis, and separately records the initiator.
  - Given source bytes, reviewed Current Validation Values, or extractor basis changes, When re-evaluation starts, Then a Working Candidate is created under FR-196 and fresh confirmation is required before a successor generation exists.
  - Given data, rules, and configuration are all unchanged, When exact replay is requested, Then the system recomputes and compares the §2.6 projection, appends one Replay Verification Event with actor/time/outcome, and creates no Review Version or authoritative Validation Run.
  - Given the rerun completes with different results, When the original opens, Then its original versions and outputs remain unchanged.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

## 9. Catalog preservation and Windows distribution

### FR-174 — Existing-rule V2 disposition
- **Statement (EARS):** WHEN migration or activation of an existing approved FinSight rule in the V2 engine is requested without an approved successor version, V2 classification, controlled-evaluator mapping, and lifecycle disposition, THE SYSTEM SHALL reject that migration or activation.
- **Rationale:** Selecting five protected controls must not silently demote, repurpose, or delete the existing catalog.
- **Source:** stakeholder-approved Product Owner brief §6; HD-01, HD-17, HD-18; clarification resolution CQ-13/CQ-29.
- **Priority:** Must
- **Dependencies:** `03-existing-rule-disposition.md`; controlled rule model §2.11.
- **Acceptance criteria:**
  - Given the existing catalog inventory, When preservation is reviewed, Then all 57 existing Rule IDs appear exactly once and remain unchanged outside the initial V2 active set.
  - Given a preserved legacy rule has no V2 mapping, When V2 Requirements or the five-rule baseline is approved, Then that absence does not block approval and the legacy rule is not activated.
  - Given future migration of a legacy rule is requested, When its required mapping or disposition is absent, Then only that migration remains blocked.
  - Given a successor or retirement disposition is approved, When it takes effect, Then the original version remains retained for historical replay.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-175 — Windows executable and installer
- **Statement (EARS):** WHEN a V2 product version enters release qualification, THE RELEASE PROCESS SHALL produce a Windows-compatible executable and installer that do not require a developer-run source environment.
- **Rationale:** Authorized users need a distributable desktop application rather than a development script.
- **Source:** stakeholder (HD-18; AR-03); extends root NFR-028 and NFR-030.
- **Priority:** Must
- **Dependencies:** Approved Windows version matrix and packaging ADR in a later stage.
- **Acceptance criteria:**
  - Given a release candidate, When the release process completes, Then the executable and installer are present and version-matched.
  - Given only source scripts exist, When release readiness is assessed, Then Windows distribution remains incomplete.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-176 — Windows clean-machine qualification
- **Statement (EARS):** WHEN a V2 build is assessed for distribution, THE RELEASE PROCESS SHALL require successful clean-machine Windows installation and first-launch evidence for that exact build.
- **Rationale:** A package is not distributable merely because it works on a developer machine.
- **Source:** stakeholder (HD-18; AR-03, AR-04).
- **Priority:** Must
- **Dependencies:** FR-175; approved Windows test matrix.
- **Acceptance criteria:**
  - Given a clean target Windows machine, When the released installer is used, Then installation and first launch pass without a developer runtime.
  - Given either test fails or evidence refers to another build, When readiness is assessed, Then distribution approval remains blocked.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-177 — Windows upgrade and uninstall behavior
- **Statement (EARS):** WHEN a Windows installer release is qualified, THE RELEASE PROCESS SHALL verify its upgrade and uninstall behavior against the Windows data-lifecycle contract in §2.13.
- **Rationale:** Enterprise users need predictable lifecycle behavior and no accidental loss or retention of financial data.
- **Source:** stakeholder (AR-03).
- **Priority:** Must
- **Dependencies:** Windows data-lifecycle contract §2.13; FR-175.
- **Acceptance criteria:**
  - Given an installed prior supported version, When upgrade is tested, Then all FinSight user data remains available and unchanged after the upgrade.
  - Given an installed release, When default uninstall is tested, Then user data is retained.
  - Given the user explicitly selects and confirms data removal during uninstall, When removal completes, Then the identified data is removed and the choice and outcome are recorded without affecting data outside that scope.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-178 — Windows release provenance and integrity
- **Statement (EARS):** WHEN a Windows package is assessed for distribution, THE RELEASE PROCESS SHALL require a checksum, build manifest, exact source commit, application version, dependency manifest, release notes, and approved code-signing/security evidence bound to that package.
- **Rationale:** Users and auditors must verify what was built, from which source, and whether the package changed.
- **Source:** stakeholder (HD-18; AR-03, AR-04); extends root NFR-033, NFR-073, and NFR-079.
- **Priority:** Must
- **Dependencies:** Architecture-approved Windows matrix, packaging, and signing profile; FR-175, FR-176.
- **Acceptance criteria:**
  - Given a release package, When provenance is verified, Then every defined artifact resolves to that exact package and source commit.
  - Given the package is modified or any required evidence is absent, When verification runs, Then the package is rejected as non-distributable.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-179 — Validation progress visibility
- **Statement (EARS):** WHILE deterministic validation is running, THE SYSTEM SHALL display the current processing status, rules executing, records evaluated, rules completed, and rules unable to evaluate.
- **Rationale:** The guided workflow must remain transparent during work that is not instantaneous.
- **Source:** stakeholder (HD-15; WF-07); extends root FR-081 and NFR-003.
- **Priority:** Must
- **Dependencies:** FR-152, FR-153.
- **Acceptance criteria:**
  - Given a validation run is active, When progress is viewed, Then the defined progress fields reflect that run.
  - Given a rule becomes NOT_EVALUATED, When progress updates, Then the rule is counted as unable to evaluate rather than silently omitted.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

## 10. Supplied real-layout source contract

The first Draft compatible-layout identifier is `SLV-001`. It describes the supplied master reports without adding compatibility sheets or restructuring either workbook. Worksheet-name matching is necessary but not sufficient; all applicable header, column, boundary, and row-type checks below must pass.

Root FR-013–FR-015 continue to govern preamble/blank/repeated/merged-cell handling, normalization, and raw cell lineage. Formula-backed financial cells follow §11.7.

### 10.1 Budget `SLV-001`

| Element | Required supplied layout |
|---|---|
| Worksheet | `Original Budget` |
| Header | Row 1 |
| Body boundary | Row 2 through the one `Grand Total` row, which is the final populated report row |
| Columns A:H | `Account #`, `Account Name`, `bgt`, `atd`, `etc`, `eac`, `delta`, `Notes` |
| Financial mapping | BGT=C; ATD=D; ETC=E; EAC=F; DELTA=G |
| Supplied row types | Six-digit numeric account detail; three-digit numeric account group; blank separator; `Grand Total` department total |
| Department evidence | A Grand Total row has `Grand Total` in A and `Department NNNN` in B; its raw department text is authoritative Budget report-level evidence and is normalized under §11.2 |
| BGT/ATD domain | Detail-row C and D values follow the finite signed, at-most-two-decimal financial parse in §11.4 and formula handling in §11.7 |

The six-digit/three-digit pattern is the approved first-release contract for every V1-compatible department. Supporting another layout requires a separately versioned, approved reader contract as a future extension.

### 10.2 GED `SLV-001`

| Element | Required supplied layout |
|---|---|
| Worksheet | `GED` |
| Report title | Row 1 |
| Reporting-period evidence | Row 3 |
| Run-date evidence | Row 4 |
| Header | Row 7 |
| First possible detail row | Row 8 |
| Body boundary | Row 8 through the one department-total row, which is the final nonblank row; later worksheet rows must be blank in A:O |
| Columns A:O | `DEPT. #`, `DEPT NAME`, `ACCOUNT NUMBER`, `ACCOUNT NAME`, `FISCAL PERIOD`, `JOURNAL #`, `JOURNAL DATE`, `INVOICE AMT`, `CHECK #`, `INVOICE DATE`, `VENDOR NAME`, `AGENCY`, `JOURNAL DESCRIPTION`, `JOURNAL LINE DESCRIPTION`, `AMOUNT` |
| Account-total recognition | After outer-whitespace removal, A equals `TOTAL FOR ACCOUNT -  ` followed by exactly six digits; B:N are blank; O contains the retained total value/formula |
| Department-total recognition | After outer-whitespace removal, A equals `TOTAL FOR DEPARTMENT -  ` followed by canonical `NN-NNNN`; B:N are blank; O contains the retained total value/formula |
| Supplied row types | Transaction candidate; exact account-total row; exact department-total row; blank row; exact repeated row-7 header |
| Report-level department evidence | The canonical number on the exact department-total row is authoritative for GED report identity; detail-row Department Number remains transaction input |

Header comparison for `SLV-001` may normalize embedded line breaks and outer whitespace only. A row whose A value begins with `TOTAL FOR ACCOUNT` or `TOTAL FOR DEPARTMENT` but fails its exact total-row shape is a structural ambiguity rather than a transaction. Every other nonblank, non-header body row is retained as a GED transaction candidate even when a required transaction field is blank or malformed, so CORE-04 can evaluate it. V1 field parse domains are defined in §11.2 and §11.4; broader aliases are future versioned reader extensions.

### FR-180 — Budget `SLV-001` field mapping
- **Statement (EARS):** WHEN an `Original Budget` worksheet is assessed under `SLV-001`, THE SYSTEM SHALL map its row-1 columns A through H exactly as defined in §10.1.
- **Rationale:** The current reader shifts every financial value left because it treats Account Name in column B as Budget.
- **Source:** stakeholder-supplied master layout and synthetic manifest reader-gap record; extends root FR-012–FR-015 and FR-021.
- **Priority:** Must
- **Dependencies:** `SLV-001`; FR-127, FR-132.
- **Acceptance criteria:**
  - Given the supplied Budget header, When mapping completes, Then column B is Account Name and column C is BGT.
  - Given the worksheet name matches but one required header is absent or occupies another column, When compatibility is assessed, Then extraction is blocked with the expected and observed cell evidence.
  - Given BGT is zero in column C, When the row is extracted, Then zero is retained as BGT and is not treated as blank.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-181 — Budget `SLV-001` row classification
- **Statement (EARS):** WHEN Budget body rows are classified under `SLV-001`, THE SYSTEM SHALL assign each row exactly one §10.1 row type and retain that type with source-cell lineage.
- **Rationale:** Group, separator, and department-total rows must not become account-detail records used by the core controls.
- **Source:** stakeholder-supplied master layout and synthetic manifest; extends root FR-013 and FR-015.
- **Priority:** Must
- **Dependencies:** `SLV-001`; §11.2.
- **Acceptance criteria:**
  - Given a supplied six-digit numeric Account # row, When classified under `SLV-001`, Then it is a Budget detail record eligible for account-key evaluation.
  - Given a supplied three-digit group, blank separator, or `Grand Total` row, When classified, Then it is excluded from the Budget detail population and retained in its own row type.
  - Given a nonblank row matches more than one or no `SLV-001` row type, When classified, Then compatibility is blocked with its sheet/row evidence.
  - Given a Budget detail BGT or ATD contains a finite signed value with no more than two fractional digits, When parsed, Then the exact two-decimal financial value and source lineage are retained; blank, non-finite, or over-precision input remains invalid for its dependent control.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-182 — GED `SLV-001` field mapping
- **Statement (EARS):** WHEN a `GED` worksheet is assessed under `SLV-001`, THE SYSTEM SHALL map its row-7 columns A through O exactly as defined in §10.2 and begin body classification at row 8.
- **Rationale:** The current reader assumes a row-4 header and row-5 detail start, which misreads the supplied report.
- **Source:** stakeholder-supplied master layout and synthetic manifest reader-gap record; extends root FR-011–FR-015 and FR-021.
- **Priority:** Must
- **Dependencies:** `SLV-001`; FR-127, FR-132.
- **Acceptance criteria:**
  - Given the supplied GED layout, When mapping completes, Then row 7 supplies all 15 fields and row 8 is the first body row considered.
  - Given the worksheet name matches but the header is on row 4 or a required field occupies a different column, When `SLV-001` compatibility is assessed, Then extraction is blocked with expected and observed locations.
  - Given embedded line breaks or outer whitespace occur in a supplied header, When comparison runs, Then only those approved formatting differences are normalized and the raw header remains in lineage.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-183 — GED `SLV-001` row classification
- **Statement (EARS):** WHEN GED body rows are classified under `SLV-001`, THE SYSTEM SHALL assign each row exactly one §10.2 row type and retain that type with source-cell lineage.
- **Rationale:** Account totals, the department total, blanks, and repeated headers are evidence but are not GED transactions.
- **Source:** stakeholder-supplied master layout and synthetic manifest reader-gap record; extends root FR-013 and FR-015.
- **Priority:** Must
- **Dependencies:** `SLV-001`; FR-182.
- **Acceptance criteria:**
  - Given a transaction row with a blank Amount, When classified, Then it remains a GED transaction so CORE-04 can evaluate the missing field.
  - Given a body row exactly matches an account-total, department-total, blank, or repeated-row-7-header shape in §10.2, When classified, Then it is excluded from the GED transaction population and retained under its source row type.
  - Given a nonblank body row is not a header or total-like row, When required transaction values are missing or malformed, Then it remains a transaction candidate with raw lineage for CORE-04.
  - Given A begins with a total-row label but the row fails the exact label, blank-column, or value-column shape, When classified, Then compatibility is blocked with its sheet/row evidence.
  - Given the exact department-total row is reached, When body classification completes, Then it is the final nonblank body row and any later nonblank A:O cell blocks compatibility.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-184 — One Rule Execution per selected rule
- **Statement (EARS):** WHEN all expected Rule Results for one selected rule version reach a terminal persisted state, THE SYSTEM SHALL persist exactly one Rule Execution record under the §2.3 contract.
- **Rationale:** One per-rule execution summary and many per-scope results are both required for auditable counts without losing account/transaction-level outcomes.
- **Source:** stakeholder (HD-05, HD-11; WF-07, WF-08); clarification of FR-153 and FR-157.
- **Priority:** Must
- **Dependencies:** FR-153–FR-158; V1 roll-up policy §2.7.
- **Acceptance criteria:**
  - Given one selected rule with N complete scope results, When execution closes, Then one Rule Execution records N results and status counts that reconcile to N.
  - Given any expected scope lacks a terminal Rule Result, When execution closure is attempted, Then no complete Rule Execution is represented.
  - Given a selected workspace-grain rule, When it completes, Then one Rule Execution and one scope-level Rule Result exist.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-185 — Review Summary landing page
- **Statement (EARS):** WHEN a validation run completes, THE SYSTEM SHALL open the Review Summary as the first post-validation view for that run.
- **Rationale:** Leaders need immediate business context and review health before they inspect individual exceptions.
- **Source:** stakeholder (HD-20, HD-25, HD-26; WF-08).
- **Priority:** Must
- **Dependencies:** FR-157, FR-158, FR-184.
- **Acceptance criteria:**
  - Given a completed run, When the post-validation workspace opens, Then Review Summary is the active view.
  - Given a completed run has no failed core rules, When the post-validation workspace opens, Then Review Summary remains the active view rather than skipping directly to an empty Findings view.
  - Given the completed run belongs to an unpublished working successor, When Review Summary opens, Then `Working — Unpublished` and the still-published Review Version are prominent and no working metric is represented as the published default.
  - Given a run is still executing or cannot produce a complete result ledger, When its workspace is viewed, Then the final Review Summary is not represented as complete.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-186 — Review Summary content
- **Statement (EARS):** WHEN the Review Summary is displayed, THE SYSTEM SHALL present every summary item defined in §2.7 for the selected validation run.
- **Rationale:** A stable executive summary makes review outcomes understandable without hiding their evidence.
- **Source:** stakeholder (HD-20, HD-25, HD-26; WF-08).
- **Priority:** Must
- **Dependencies:** FR-129–FR-131, FR-153–FR-158, FR-184, FR-193; §2.10.
- **Acceptance criteria:**
  - Given a completed run with failures, When Review Summary opens, Then all §2.7 metadata, health, count, exception, top-finding, and next-action items are present.
  - Given one summary category has zero findings, When Review Summary opens, Then that category displays zero or its deterministic healthy status rather than being omitted.
  - Given a selected rule is `NOT_EVALUATED`, When counts are displayed, Then it is included in Rules Not Evaluated and is not counted as passed or failed.
  - Given advisory rules produce OBSERVATION and NO_OBSERVATION, When counts are displayed, Then each appears in the corresponding advisory count and neither is counted as passed or failed.
  - Given any selected run, When its summary opens, Then its publication state is displayed with the other §2.7 identity fields.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-187 — Engine-derived Review Summary
- **Statement (EARS):** WHEN a Review Summary value represents a validation conclusion, THE SYSTEM SHALL derive it from the persisted engine records mapped in §2.7.
- **Rationale:** The executive view must consume the same validation truth as Findings, reports, analytics, and Ask Fin.
- **Source:** stakeholder (HD-05, HD-20; WF-08).
- **Priority:** Must
- **Dependencies:** FR-153–FR-165; §2.7.
- **Acceptance criteria:**
  - Given unchanged persisted engine records, When Review Summary is regenerated, Then every validation value and count is identical.
  - Given a dashboard query would produce a value that conflicts with persisted Rule Results, When Review Summary renders, Then the persisted engine outcome controls and no independent validation value is shown.
  - Given a descriptive value has no rule-engine origin, When it is displayed, Then it is labeled descriptive and cannot affect Overall Review Status.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-188 — Review Summary drill-down navigation
- **Statement (EARS):** WHEN a user selects a Review Summary destination, THE SYSTEM SHALL navigate to Findings, Rule Results, Analytics, Reports, or Ask Fin for the same validation run.
- **Rationale:** The summary is an entry point into evidence and analysis, not a replacement for them.
- **Source:** stakeholder (HD-20; WF-08–WF-10).
- **Priority:** Must
- **Dependencies:** FR-157, FR-166–FR-170, FR-185.
- **Acceptance criteria:**
  - Given a destination is available, When the user selects it, Then the destination opens scoped to the same Run ID.
  - Given the user selects a Top Finding, When navigation completes, Then the linked Finding and source evidence are in context.
  - Given the approved Ask Fin provider is temporarily unavailable, When the user opens Ask Fin, Then the same-run destination identifies the outage and produces no fabricated answer.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-189 — Windows actor identity
- **Statement (EARS):** WHEN an actor attempts an audited MVP action on Windows, THE SYSTEM SHALL resolve the stable Actor ID, domain-qualified account name, and `WINDOWS_ACCOUNT` identity-source identifier under §2.8.
- **Rationale:** Corrections, rule changes, approvals, runs, reports, and Ask Fin interactions must be attributable to an authenticated person.
- **Source:** stakeholder (HD-23).
- **Priority:** Must
- **Dependencies:** Windows-authenticated session; root FR-084; §2.8.
- **Acceptance criteria:**
  - Given an authenticated Windows account, When an audited action begins, Then its stable security identifier, domain-qualified account, and identity source are available to authorization and audit.
  - Given an account display name changes while its security identifier remains the same, When identity is compared, Then it remains the same Actor ID.
  - Given no stable Windows Actor ID can be resolved, When the actor requests review, source, rule, request, result, Derived Record, or audit data, or attempts another audited action, Then the request is denied, no protected data is disclosed, and only non-sensitive application-shell or product-help content remains available.
  - Given a previously resolved identity becomes unresolved while protected content is open or cached, When the next access boundary is evaluated, Then protected content is locked or cleared before further access and no unattributed data-access event occurs.
  - Given a stable Windows Actor ID resolves, When the actor accesses authorized application data, Then exactly one access-audit event records that Actor ID, identity source, and timestamp under root FR-084.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-190 — MVP role-policy enforcement
- **Statement (EARS):** WHEN an authenticated actor requests an MVP action, THE SYSTEM SHALL permit or deny it according to the Reviewer, Rule Administrator, and Financial Control Approver policy in §2.8.
- **Rationale:** The three roles separate financial review work, configurable-rule administration, and protected-control approval.
- **Source:** stakeholder (HD-21, HD-22).
- **Priority:** Must
- **Dependencies:** FR-189; §2.8.
- **Acceptance criteria:**
  - Given each single-role actor, When every action row in §2.8 is attempted at a time its assignment is effective, Then only the permissions in that role's column are granted.
  - Given one actor holds multiple effective roles, When ordinary actions are attempted, Then permissions are the union of those role columns.
  - Given a combined-role actor attempts to decide its own protected request or role assignment, When authorization is evaluated, Then the explicit separation denial takes precedence and the action is denied.
  - Given a role assignment is not yet effective or has reached effective-through, When its permission is requested, Then that assignment grants no permission.
  - Given an existing workspace upgrade to a newer protected baseline, When authorization is evaluated, Then a Financial Control Approver's explicit authorization is required even if a Rule Administrator requested the upgrade.
  - Given an authorized upgrade for Workspace A, When it commits, Then Workspace A receives one successor Rule Set Version referencing the target Protected Baseline Version while Workspace B and every historical Validation Run remain unchanged.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-191 — Three-value field presentation
- **Statement (EARS):** WHEN an extracted Budget or GED field is displayed in review data, evidence, a Finding, or edit history, THE SYSTEM SHALL distinguish its Original Extracted Value, User-Reviewed Value, and Current Validation Value under §2.9.
- **Rationale:** Users must always know what came from the source, what a person reviewed, and what validation consumed.
- **Source:** stakeholder (HD-24).
- **Priority:** Must
- **Dependencies:** FR-137, FR-138; §2.9.
- **Acceptance criteria:**
  - Given no saved correction in a confirmed Review Version, When the field is displayed, Then User-Reviewed Value is `Not set` and Current Validation Value equals Original Extracted Value.
  - Given a saved but unconfirmed correction, When the field is displayed, Then User-Reviewed Value is labeled `Pending confirmation`, Current Validation Value is `Unavailable — confirmation required` for that Working Candidate, and no Review Version exists yet.
  - Given a confirmed correction, When the field is displayed, Then all three labeled values are visible and Current Validation Value equals User-Reviewed Value.
  - Given a correction is reverted and the reversion confirmed, When history and current data are displayed, Then the prior reviewed value remains in history while Current Validation Value again equals Original Extracted Value.
  - Given a sealed Review Version cannot be reconstructed because its source is missing, mismatched, or extractor-divergent, When field data is requested, Then the three values are marked unavailable with the recovery reason and retained audit/result evidence is not altered.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-192 — Confirmed current-value validation binding
- **Statement (EARS):** WHEN validation starts, THE SYSTEM SHALL bind every rule input to the confirmed Current Validation Values and provenance of the selected Review Version.
- **Rationale:** The engine must consume exactly the values the Reviewer confirmed without losing their original evidence.
- **Source:** stakeholder (HD-24).
- **Priority:** Must
- **Dependencies:** FR-139, FR-152; §2.9.
- **Acceptance criteria:**
  - Given a confirmed corrected field, When validation starts, Then rules receive its Current Validation Value and retain links to the reviewed and original values.
  - Given an unedited field, When validation starts, Then rules receive its Original Extracted Value as Current Validation Value.
  - Given any unconfirmed edit exists, When validation is requested, Then FR-139 blocks execution and no mixed-version input binding is created.
  - Given a Reviewer confirms the Working Candidate and its Review Version is created at Data Reviewed, When the engine input is constructed, Then it is the fingerprint-verified reconstructed V2 VerifiedDataset projection defined in §2.9.
  - Given a `RULESET_REANALYSIS` or `CONFIG_REANALYSIS` successor satisfies §2.10, When validation starts, Then the engine input is fingerprint-equivalent to the predecessor's VerifiedDataset, retains the predecessor's original verification provenance, and separately identifies the reanalysis initiator.
  - Given reconstruction cannot reproduce the recorded verified fingerprint, When validation is requested, Then execution is blocked and no partial input reaches the engine.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-193 — Review Summary identity block
- **Statement (EARS):** WHEN the Review Summary is displayed, THE SYSTEM SHALL present Department Name, Department Number, Reporting Period, Validation Run ID, Rule Set Version, Review Version, Review Lifecycle Status, Publication State, Source File Names, and Validation Timestamp for the selected run.
- **Rationale:** The visible summary must identify the exact review context captured by reports and screenshots.
- **Source:** stakeholder (HD-25; WF-08).
- **Priority:** Must
- **Dependencies:** FR-129–FR-131, FR-152–FR-154, FR-186; §2.10.
- **Acceptance criteria:**
  - Given a completed run, When Review Summary opens, Then all ten identity fields are visible without opening a secondary details view.
  - Given two runs differ by Review Version or Rule Set Version, When their summaries are compared, Then the differing identifiers are visible.
  - Given no Review Version or complete run exists for a Working Candidate, When a provisional workspace view is shown, Then no fabricated Review Version, Validation Run ID, Rule Set Version, Publication State, or Validation Timestamp is presented.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-194 — Downstream review-context identity
- **Statement (EARS):** WHEN FinSight generates a report, export, or review-specific Ask Fin response, THE SYSTEM SHALL include the §2.10 identity of the selected Review Version and Validation Run.
- **Rationale:** Every shared or conversational artifact must make its exact financial context independently identifiable.
- **Source:** stakeholder (HD-25).
- **Priority:** Must
- **Dependencies:** FR-167, FR-168, FR-171, FR-193.
- **Acceptance criteria:**
  - Given a report or export, When its identity block is inspected, Then it contains Department Name/Number, Reporting Period, Validation Run ID, Rule Set Version, Review Version, Review Lifecycle Status, Publication State, Source File Names, and Validation Timestamp.
  - Given a review-specific Ask Fin response, When its context is inspected, Then it identifies the same selected Review Version and Validation Run.
  - Given a past run is selected, When a new artifact is generated, Then the artifact carries the past run's identity rather than the latest run's identity.
  - Given an export is generated for a published, analyzed-working, or historical generation, When its manifest is inspected, Then every inherited ADR-015 field is present and the artifact's creation-time publication/supersession label is unambiguous.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-195 — Review lifecycle transition enforcement
- **Statement (EARS):** WHEN a Working Candidate or Review Version satisfies one §2.10 workflow entry condition, THE SYSTEM SHALL advance only through the corresponding candidate-to-generation Review Status progression.
- **Rationale:** Explicit lifecycle state makes active and past reviews understandable without inferring progress from partial records.
- **Source:** stakeholder (HD-26; WF-01–WF-11).
- **Priority:** Must
- **Dependencies:** FR-125; §2.10.
- **Acceptance criteria:**
  - Given each adjacent lifecycle pair, When its entry condition is satisfied, Then exactly that next status is recorded with actor and timestamp.
  - Given a Working Candidate is confirmed, When history is inspected, Then the candidate-to-generation event and created Review Version at Data Reviewed are both recorded without representing a prior generation as moving backward.
  - Given a governed reanalysis inherits an unchanged verification basis, When its history is inspected, Then the successor begins at Data Reviewed with its exact creation reason and no fabricated Draft, upload, or new-verification event.
  - Given a prerequisite is absent, When advancement is requested, Then status remains unchanged and each missing prerequisite is identified.
  - Given a request skips an intermediate status, When it is evaluated, Then the transition is denied.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-196 — Successor version after reviewed-data change
- **Statement (EARS):** IF source data, a reviewed Current Validation Value, or extractor basis changes after a Review Version reaches `Data Reviewed`, THEN THE SYSTEM SHALL create a linked Working Candidate requiring fresh confirmation while preserving the prior Review Version unchanged.
- **Rationale:** A reviewed or validated basis must never be silently rewritten.
- **Source:** stakeholder (HD-24, HD-26).
- **Priority:** Must
- **Dependencies:** FR-137–FR-140, FR-171–FR-173; §2.10.
- **Acceptance criteria:**
  - Given both prior source bindings are inherited, When changed-data work begins, Then one linked Working Candidate starts at Data Uploaded; otherwise it starts at Draft.
  - Given the candidate opens, When its provenance is inspected, Then its inherited source/evidence, triggering change type, and predecessor Review Version are visible.
  - Given the candidate is not freshly confirmed, When validation is requested, Then no successor Review Version exists and validation is blocked.
  - Given the candidate is confirmed, When the candidate-to-generation transition succeeds, Then the next Review Version is created with `SOURCE_REVERIFICATION` or `EXTRACTOR_REVERIFICATION` and fresh verifier/time.
  - Given the candidate is modified, When the prior Review Version is reopened, Then its generation, status, run, results, and evidence remain unchanged.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-197 — Past-review lifecycle visibility
- **Statement (EARS):** WHEN View Past Reviews is opened, THE SYSTEM SHALL display each retained Working Candidate or Review Version's Review Status and permit filtering by every §2.10 status.
- **Rationale:** Users need to distinguish unfinished, validated, closed, and archived work in review history.
- **Source:** stakeholder (HD-26; WF-01, WF-11).
- **Priority:** Must
- **Dependencies:** FR-123, FR-171–FR-173, FR-195.
- **Acceptance criteria:**
  - Given retained candidates and versions across all seven statuses, When View Past Reviews opens, Then each row displays its Review Status and identifies whether it is candidate, working, published, or historical.
  - Given one or more status filters, When applied, Then only matching Working Candidates or Review Versions appear without changing stored reviews.
  - Given Archived reviews exist, When the default recent list opens, Then they are excluded; selecting the Archived filter reveals them read-only.
  - Given an Active or Abandoned ReviewCycle, When View Past Reviews opens, Then its orthogonal disposition is visible without replacing or recalculating Review Status.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-198 — Protected change request submission
- **Statement (EARS):** WHEN a Rule Administrator submits a complete protected-baseline change request that references an exact immutable Tested candidate authored and tested through the protected Draft lifecycle, THE SYSTEM SHALL persist it with `Pending Approval` status under the §2.8 Protected Change Request contract while leaving the active baseline unchanged.
- **Rationale:** Requesting a policy change must create reviewable evidence without changing the control before independent approval.
- **Source:** stakeholder (HD-22).
- **Priority:** Must
- **Dependencies:** FR-147, FR-148, FR-189, FR-190; §2.8 and §2.12.
- **Acceptance criteria:**
  - Given a protected successor was created and edited while Draft, passed its required tests, reached immutable Tested, and supplies every §2.8 request field, When a Rule Administrator submits the request, Then one Pending Approval record references that exact version and the active Protected Baseline Version is unchanged.
  - Given a requester lacks the Rule Administrator permission, When submission is attempted, Then FR-190 denies the action and no request or baseline change is created.
  - Given a required request field or test result is absent, the referenced candidate is Draft/Active/Retired, or its definition changed after testing, When submission is attempted, Then no Pending Approval record is created and every blocking element is identified.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-199 — Protected change rejection
- **Statement (EARS):** WHEN a Financial Control Approver rejects a Pending Approval protected-baseline change request, THE SYSTEM SHALL persist the `Rejected` decision, approver Actor ID, timestamp, and reason while leaving the active baseline unchanged.
- **Rationale:** A rejection is a governed, attributable decision and must never disappear or partially activate policy.
- **Source:** stakeholder (HD-22).
- **Priority:** Must
- **Dependencies:** FR-144, FR-189, FR-190, FR-198; §2.8 and §2.12.
- **Acceptance criteria:**
  - Given a Pending Approval request from a different Actor ID, When a Financial Control Approver rejects it with a reason, Then the decision evidence is retained and no successor, Protected Baseline Version, or workspace Rule Set Version activates.
  - Given the requester attempts to reject the same request, When authorization is evaluated, Then the action is denied and the request remains Pending Approval.
  - Given a previously rejected request, When a later approval is attempted against that same request ID, Then the transition is denied; a new change requires a new request ID.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-200 — Ask Fin private-provider prerequisite
- **Statement (EARS):** WHILE no on-device or explicitly organization-approved private Ask Fin provider is configured, THE SYSTEM SHALL present Ask Fin as unavailable while keeping deterministic validation, findings, analytics, reports, and exports complete and usable.
- **Rationale:** The financial review cannot depend on an unapproved AI data path, and AI availability must never become a validation prerequisite.
- **Source:** stakeholder (HD-05, HD-18, HD-27); clarification resolution CQ-24/CQ-26.
- **Priority:** Must
- **Dependencies:** Approved AI security boundary; FR-165, FR-169; §2.14.
- **Acceptance criteria:**
  - Given no approved private provider is configured, When Ask Fin is opened, Then it identifies the configuration prerequisite and sends no review data to an AI provider.
  - Given the same configuration state, When validation and deterministic reporting run, Then their complete outputs remain available without Ask Fin.
  - Given an approved private provider is configured but temporarily unavailable, When Ask Fin is opened, Then the outage is identified and no unsupported answer is produced.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-201 — Governed whole-scope disposal
- **Statement (EARS):** WHEN an authorized Reviewer separately confirms permanent disposal of one complete review, one complete reporting period, or all locally stored FinSight data, THE SYSTEM SHALL dispose the exact selected scope and append only the non-content audit tombstone defined in §2.13.
- **Rationale:** Confidential local financial data needs a deliberate removal path without permitting selective rewriting of retained review evidence.
- **Source:** inherited root NFR-017; stakeholder retention clarification (HD-27; CQ-27).
- **Priority:** Must
- **Dependencies:** FR-189, FR-190; first-release data-lifecycle contract §2.13.
- **Acceptance criteria:**
  - Given an authorized Reviewer selects one permitted scope, When the confirmation view opens, Then every review and Derived Record that will be removed is summarized before confirmation.
  - Given the Reviewer cancels or the selected scope is ambiguous, When disposal is evaluated, Then no data or evidence is removed.
  - Given a complete review or period is confirmed, When disposal completes, Then no record within that scope remains recoverable through FinSight or its managed backup/recovery paths and no record outside that scope changes.
  - Given disposal succeeds or fails, When audit history is inspected, Then one tombstone records actor, time, scope category, reason, confirmation, and outcome without the deleted financial content.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-202 — Working-generation publication
- **Statement (EARS):** WHEN a working Review Version becomes publication-eligible, THE SYSTEM SHALL atomically apply the §2.10 first-generation auto-publication or successor explicit-promotion contract.
- **Rationale:** A rerun must not silently replace the financial results that dashboards, reports, and Ask Fin treat as trusted.
- **Source:** inherited ADR-011 §§8–9; stakeholder trust, review, and actor requirements (HD-05, HD-21, HD-23, HD-26).
- **Priority:** Must
- **Dependencies:** FR-152–FR-154, FR-165–FR-173, FR-185–FR-195; §2.10.
- **Acceptance criteria:**
  - Given the first Review Version has no prior published generation, When its complete run reaches Validation Complete/ANALYZED, Then it auto-publishes once and one attributable system audit event records the transition.
  - Given a successor working generation is Validation Complete/ANALYZED or later and a Reviewer confirms promotion with a reason, When the transaction commits, Then one supersession record links prior to successor, the published pointer moves to the successor, and actor/time/reason are retained.
  - Given promotion persistence fails at any boundary, When recovery completes, Then the prior published pointer and trusted outputs remain unchanged and no partial supersession exists.
  - Given a working generation lacks a complete run or the actor lacks Reviewer permission, When promotion is requested, Then it is denied and the published pointer remains unchanged.
  - Given promotion succeeds, When trusted Review Summary, dashboard, analytics, reports, exports, or Ask Fin open by default, Then they resolve the successor; every historical generation remains explicitly selectable and immutable.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### FR-203 — Fingerprint-verified dataset reconstruction
- **Statement (EARS):** WHEN a Working Dataset or `VerifiedDataset` is requested, THE SYSTEM SHALL reconstruct it from fingerprint-matching source bindings, the recorded extractor version, and the applicable persisted correction/confirmation basis under §2.9–§2.10.
- **Rationale:** Review-local corrections and historical evidence must remain reproducible without contradicting the inherited prohibition on persisted normalized/verified row stores.
- **Source:** inherited ADR-011/ADR-012; stakeholder immutable-source, reviewed-copy, and historical-reproducibility requirements (HD-04, HD-15, HD-24–HD-26).
- **Priority:** Must
- **Dependencies:** FR-127, FR-136–FR-140, FR-171, FR-172, FR-192; §2.9–§2.10.
- **Acceptance criteria:**
  - Given matching sources and the recorded extractor/correction basis, When reconstruction runs twice, Then normalized values, Current Validation Values, lineage, row/schema counts, and verified fingerprint are identical.
  - Given a sealed Review Version, When the recomputed verified fingerprint differs from its recorded fingerprint, Then no reconstructed dataset is released to validation or evidence consumers and no retained generation/result/publication record changes.
  - Given a source path moved but selected bytes match the recorded fingerprint, When an authorized actor rebinds the path, Then reconstruction succeeds without new verification or result mutation and the path-change audit is appended.
  - Given a source is missing, mismatched, or extractor-divergent, When reconstruction is requested, Then the exact recovery state is displayed while retained runs, results, findings, audit, and Derived Records remain viewable.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

## 11. V1 sample-reference financial contract

The supplied Budget and GED report pair is the business contract for the first configurable-rule-engine release. The definitions below are V1 product semantics, not a declaration of enterprise-wide Amerisure accounting policy. Broader accounting bases, alternative layouts, department-specific conventions, fuzzy duplicate matching, and organization-specific row inclusion policies are future versioned configurations or rule extensions and do not block this MVP.

### 11.1 Budget meanings and arithmetic

For V1:

- BGT means planned budget.
- ATD means actual-to-date and is reconciled to the eligible GED Amount sum.
- ETC means estimate to complete.
- EAC means ATD plus ETC.
- DELTA means BGT minus EAC.

The five protected controls consume Budget detail BGT and ATD values and GED detail Amount values. Budget group, subtotal, and department-total values remain evidence and are not substituted for detail values.

### 11.2 Department and account identity

- A GED Department Number is canonical when it matches `NN-NNNN` after outer whitespace is removed.
- A Budget Grand Total label `Department NNNN` resolves to canonical Department Number `00-NNNN`.
- The Budget Grand Total row and GED department-total row supply the authoritative report-level Department Numbers. The canonical numbers are the cross-file report-identity comparison; a different Department Number on an individual GED transaction remains row-level input for CORE-02 and does not by itself block intake.
- For the displayed Department Name, consider only GED transaction candidates whose canonical Department Number equals the authoritative GED report-level number, remove outer whitespace from their Department Name values, and retain first-source-row order. Exactly one distinct nonblank value is displayed as the raw source name. No value produces `Absent`; more than one produces `Conflicting` plus the ordered distinct raw values. `Absent`, `Conflicting`, or a truncated value is visible but does not change an otherwise matching report-level number or trigger invented expansion.
- A V1 Budget or GED detail Account Number is a six-digit digit string after spreadsheet numeric-to-text canonicalization and outer-whitespace removal.
- More than one Budget detail row with the same canonical Department Number + Account Number is an ambiguous source structure and blocks validation; V1 never silently aggregates duplicate Budget keys.

### 11.3 Reporting period and eligible GED population

- The user-selected month/year is the Validation Workspace reporting period.
- GED row 3 is authoritative source-period evidence only when its outer-whitespace-trimmed text matches exactly `Year-To-Date for Period {Full English Month Name} {four-digit year}` with the supplied capitalization and one internal space between tokens. Its parsed month/year must match the selected month/year. GED row 4 is run-date evidence only.
- `SLV-001` Budget contains no source-period field, so V1 binds it to the selected workspace period and records `workspace-assigned/no source period`.
- A GED transaction is period-eligible when its Fiscal Period is in the selected year and is no later than the selected month, reflecting the supplied year-to-date report.
- A conflicting GED title period blocks validation. V1 provides no period override; the user must replace the report or start/correct the review before validation.

### 11.4 Required-field parsing

For CORE-04:

- Department Number uses §11.2.
- Account Number uses §11.2.
- Fiscal Period is `YYYY-MM` with month `01` through `12`.
- Journal Number is a nonblank scalar text value after outer-whitespace removal.
- Journal Date is an Excel date or ISO `YYYY-MM-DD` value resolving to a valid calendar date.
- Amount is a finite signed spreadsheet numeric value or signed decimal text with optional thousands separators and no more than two fractional digits.

Zero and negative Amount values are valid for field presence and parsing. Blank, non-finite, and more-than-two-decimal Amount values fail CORE-04.

For CORE-01 and CORE-05, Budget BGT and ATD use the same finite signed spreadsheet-numeric or signed-decimal-text domain, optional thousands separators, and no more than two fractional digits. Valid values are represented at exactly two decimal places for comparison; blank, non-finite, and more-than-two-decimal values invalidate only the dependent Budget key scope.

### 11.5 Eligible actual-spend and reconciliation sum

The V1 GED aggregate for one Budget key includes every row classified as a GED transaction under `SLV-001` whose valid canonical Department Number + Account Number exactly equals that Budget detail key, is period-eligible, and has a valid signed Amount. Account-total, department-total, blank, preamble, and repeated-header rows are excluded. Account Number alone never supplies a join.

Negative transactions reduce the sum. Exact duplicates remain included until a user corrects the review-local dataset and reruns; CORE-03 flags them but never deletes them. An empty eligible population for a valid Budget key sums to exact zero.

If any transaction with an exact valid Budget key has a missing or invalid Amount or Fiscal Period, CORE-01 and CORE-05 return `NOT_EVALUATED` for that key rather than treating the value as zero or using a partial sum. The issue does not prevent any other Budget key from evaluating. A GED row with no exact Budget key fails CORE-02 when its identifiers are parseable, never joins a Budget scope by Account Number alone, and does not make any valid Budget scope `NOT_EVALUATED`.

BGT, ATD, and GED Amount comparisons use exact decimal arithmetic at two currency decimal places with no tolerance.

### 11.6 Exact-duplicate fingerprint

CORE-03 fingerprints all 15 GED transaction fields mapped from columns A through O in `SLV-001`. A CORE-04 required field uses its canonical parsed representation when parseable; otherwise it uses a deterministic type-tagged raw scalar or explicit null token, so a malformed field does not suppress duplicate evaluation. Every optional field uses a type-tagged spreadsheet scalar: numeric cells use exact decimal text, date-typed cells use ISO `YYYY-MM-DD`, text cells preserve their text subject only to outer-whitespace and line-ending normalization, and blanks use an explicit null token. Case, punctuation, internal spaces, literal dots, and blank values remain distinct.

Every distinct fingerprint present in the GED detail population is one expected CORE-03 scope. A singleton fingerprint returns PASS; a fingerprint with two or more members returns FAIL. Journal Number alone is never sufficient. Payroll, journal-entry, accrual, reclass, reversal, and internal-allocation rows receive no automatic exception. An opposite-sign pair is not exact because Amount differs.

For a failed fingerprint, the deterministic reference row is the member with the lowest source-row number, with stable source-record ID as the tie-breaker. Potential duplicate exposure is the exact signed sum of Amount for every member after that one reference row only when every duplicate-copy Amount is numeric; otherwise exposure is `Unavailable`. Exposure availability never changes the PASS/FAIL result.

### 11.7 Formula-backed financial cells

When a required financial cell contains a formula, V1 uses its stored finite numeric result when one is present and retains both formula text and stored result as lineage. If no usable stored numeric result exists, the field is invalid and the dependent rule is `NOT_EVALUATED`. V1 does not execute macros, external links, or an unapproved workbook recalculation engine.

## 12. Protected baseline rule contracts

The control keys below are human-readable aliases for the permanent protected Rule IDs assigned in §2.12. None of the 57 preserved legacy Rule IDs is silently repurposed for these controls.

### CORE-01 contract — Actual spend must not exceed BGT

| Attribute | Draft contract |
|---|---|
| Purpose | Identify a Department Number + Account Number whose eligible GED actual spend is greater than Budget BGT. |
| Datasets | Confirmed Budget and GED Working Dataset for one workspace. |
| Required fields | Budget department/account identity and BGT; GED department/account identity and Amount; review-period evidence. |
| Matching grain | Canonical Department Number + Account Number from a Budget detail row under `SLV-001`, as defined in §11.2. |
| Calculation | The §11.5 eligible GED Amount sum by key compared with BGT using exact two-decimal arithmetic. |
| PASS | Eligible actual spend is less than or equal to BGT. |
| FAIL | Eligible actual spend is greater than BGT. |
| NOT_EVALUATED | An input assigned to this exact Budget key is unresolved: BGT is invalid, or an exact-key GED transaction has an invalid Amount or Fiscal Period. A failed report-level intake dependency blocks the run before scope evaluation; an unmatched GED row is owned by CORE-02 and affects no Budget-key scope. |
| Severity | High under protected seed policy `R-VAL-01`; the resolved severity and configuration version are recorded with each run. |
| Finding | Key, BGT, actual spend, overrun, rule/version, contributing rows, source evidence. |
| Recommended human follow-up | Review the planned amount and contributing actual transactions with the responsible budget owner; FinSight takes no financial action. |
| Positive/negative/boundary | Synthetic TEST-01 supplies one deliberate FAIL; TEST-03 makes only key `00-0245 + 537035` NOT_EVALUATED; TEST-04 remains outside every Budget-key aggregate; add passing below-budget and exact-equality fixtures. |

### CORE-02 contract — GED transaction must map to Budget

| Attribute | Draft contract |
|---|---|
| Purpose | Identify each GED detail transaction whose resolved department/account key is absent from valid Budget detail rows. |
| Datasets | Confirmed Budget detail records and GED detail transactions. |
| Required fields | Department Number and Account Number from both sources; GED journal/source evidence. |
| Matching grain | One GED transaction to the canonical Department Number + Account Number of exactly one `SLV-001` Budget detail row. |
| PASS | Exactly one valid Budget detail key covers the GED transaction key. |
| FAIL | No valid Budget detail key covers the GED transaction key. |
| NOT_EVALUATED | Required identifier evidence cannot be parsed or resolved. |
| Severity | High under protected seed policy `R-VAL-02`; the resolved severity and configuration version are recorded with each run. |
| Finding | GED row, department/account values, journal identity, amount when available, attempted normalized key, and source evidence. |
| Recommended human follow-up | Review coding and source data; correct the review-local extraction or replace/correct the source through the approved process. |
| Positive/negative/boundary | Synthetic TEST-04 supplies one FAIL for `00-0999 + 527015`; TEST-03 still maps because missing Amount is irrelevant to this exact-key rule; add a valid mapping and a group-total-only non-match boundary. |

### CORE-03 contract — Exact duplicate GED transaction

| Attribute | Draft contract |
|---|---|
| Purpose | Identify transaction sets equal on every approved material field without deleting or suppressing source evidence. |
| Datasets | Confirmed GED detail transactions only; subtotal/total rows excluded by the reader contract. |
| Required fields | All 15 GED transaction fields mapped from columns A through O under `SLV-001`, using canonical values or deterministic raw/null fallback tokens under §11.6. |
| Matching grain | Every distinct fingerprint group present in GED detail, including member count one. |
| PASS | The fingerprint group contains exactly one transaction. |
| FAIL | A fingerprint occurs more than once. |
| NOT_EVALUATED | Not used after compatible GED detail scopes are enumerated; malformed values use §11.6 fallback tokens and CORE-04 owns parseability. |
| Severity | Medium under protected seed policy `R-VAL-03`; the resolved severity and configuration version are recorded with each run. |
| Finding | Fingerprint definition/version, every member row, values, event tags, and potential duplicate exposure calculated under §11.6 or labeled `Unavailable`. |
| Recommended human follow-up | Determine whether the repeated entries are legitimate or duplicate postings; FinSight does not delete or exclude them automatically. |
| Positive/negative/boundary | Synthetic TEST-02 supplies one failed group; every other distinct fingerprint is a singleton PASS, including one-field-different and opposite-sign groups; malformed identical rows remain evaluable while exposure may be unavailable. |

### CORE-04 contract — Required GED fields

| Attribute | Draft contract |
|---|---|
| Purpose | Ensure each GED detail transaction has parseable identity, period, journal, date, and amount evidence. |
| Datasets | Confirmed GED detail transactions. |
| Required fields | Department Number, Account Number, Fiscal Period, Journal Number, Journal Date, Amount. |
| Matching grain | One GED detail transaction. |
| PASS | All six fields are present and parseable under §11.4. |
| FAIL | At least one field is absent or not parseable. |
| NOT_EVALUATED | Not used for the field-presence/type decision itself; row classification ambiguity is an intake-compatibility blocker. |
| Severity | High under protected seed policy `R-VAL-04`; the resolved severity and configuration version are recorded with each run. |
| Finding | GED row, each failed field, raw value, expected schema, rule/version, and source cell. |
| Recommended human follow-up | Correct a permitted review-local extraction or replace/correct the source report, then reconfirm and rerun. |
| Positive/negative/boundary | Synthetic TEST-03 supplies one FAIL; TEST-04's parseable `00-0999` Department Number passes this field rule; add all-fields-valid PASS, zero Amount PASS, negative Amount PASS, and invalid-date/period cases. |

### CORE-05 contract — Budget ATD must equal GED sum

| Attribute | Draft contract |
|---|---|
| Purpose | Reconcile Budget ATD to the eligible GED Amount aggregate for the same department/account and review cycle. |
| Datasets | Confirmed Budget and GED Working Dataset. |
| Required fields | Budget department/account identity and ATD; GED department/account identity and Amount; review-cycle evidence. |
| Matching grain | Canonical Department Number + Account Number from a Budget detail row under `SLV-001`, as defined in §11.2. |
| Calculation | Budget ATD compared with the §11.5 exact-key GED Amount sum using exact two-decimal arithmetic and no tolerance; no account-only join is permitted. |
| PASS | Budget ATD equals the eligible GED sum under the approved comparison policy. |
| FAIL | Budget ATD differs from the eligible GED sum under that policy. |
| NOT_EVALUATED | An input assigned to this exact Budget key is unresolved: Budget ATD is invalid, or an exact-key GED transaction has an invalid Amount or Fiscal Period. A failed report-level intake dependency blocks the run before scope evaluation; an unmatched GED row is owned by CORE-02 and affects no Budget-key scope. |
| Severity | High under protected seed policy `R-VAL-05`; the resolved severity and configuration version are recorded with each run. |
| Finding | Key, Budget ATD, GED sum, difference, inclusion/exclusion evidence, rule/version, contributing rows, and source cells. |
| Recommended human follow-up | Review Budget ATD and the contributing GED population; correct/replace source or review-local extraction as authorized, then rerun. |
| Positive/negative/boundary | Synthetic TEST-04 produces a consequential FAIL for Budget key `00-0245 + 527015` because its GED exact-key sum is zero while ATD is 1,850.00; TEST-03 makes only `00-0245 + 537035` NOT_EVALUATED; other intended scopes, including TEST-01 and TEST-02 scopes, reconcile. Add a $0.01 difference FAIL, exact-equality PASS, and no-transaction/zero-ATD PASS. |

## 13. Requirements clarification status

No open clarification blocks Requirements approval. The implementation-specific choices below are deliberately routed forward and cannot expand or weaken the approved outcome without a governed requirements change:

- Architecture selects the controlled-rule serialization and evaluator classes within §2.11.
- Architecture and UX select the concrete spreadsheet-compatible export format within §2.13.
- Architecture and release governance select the Windows version matrix, installer technology, signing certificate, and timestamp service while preserving FR-175–FR-178.
- Architecture and security select local storage paths, backup/recovery mechanisms, temporary-data cleanup implementation, and an approved on-device or organization-private Ask Fin adapter.
- Architecture defines workbook byte, decompression, and complexity ceilings and optional-rule stress profiles in addition to the inherited 10,000-GED-row, 8–16 GB Windows-laptop, two-minute baseline.

## Clarifications log

The following decisions close the clarification register. Architecture-routed implementation choices remain approval gates for their own phase, not unresolved Requirements questions.

| Date | Item(s) | Question | Resolution | Raised by | Answered by |
|---|---|---|---|---|---|
| 2026-07-27 | CQ-05, CQ-06, CQ-10 | Which data may be edited, which roles act, and how is the actor identified? | Apply §2.8–§2.10: three extensible MVP roles; Windows stable Actor ID; two different people for protected requests and approvals; any extracted row-level business field may be corrected in an immutable-source, audited, reversible working copy with Original, User-Reviewed, and Current Validation values. | Requirements clarification | Product stakeholder (HD-21–HD-26) |
| 2026-07-27 | CQ-07 | How may protected baseline policy evolve? | Apply §2.12: tested successor, different requester/approver Actor IDs, explicit effective timestamp, atomic activation, no fewer than five active protected controls, immutable historical bindings, and explicit upgrade/rerun for existing work. | Requirements analysis | Product stakeholder direction (HD-04, HD-22, HD-27) |
| 2026-07-27 | CQ-11, CQ-30 | Which configurable evaluator and lifecycle model applies? | Apply §2.11: six bounded deterministic evaluator families; no executable/unrestricted expressions; Rule Definition Version lifecycle is Draft → Tested → Active → Retired and workspace binding is separately Enabled/Disabled. | Requirements analysis | Product stakeholder direction (HD-02, HD-03, HD-21, HD-27) |
| 2026-07-27 | CQ-12 | Which result outputs and comparison capabilities are first-release scope? | Apply §2.13: Review Summary print/PDF and spreadsheet-compatible Findings, Rule Results, and summarized-data exports are Must; audit export and on-screen rule-change comparison are Should; comparison export is not required and tracker workbook remains R2. | Requirements analysis | Inherited approved root FR-116–FR-120 and product direction |
| 2026-07-27 | CQ-13, CQ-29 | How do legacy rules and the five core controls receive IDs? | Preserve all 57 legacy rules unchanged outside the V1 active set. Assign new collision-free protected IDs `R-VAL-01` through `R-VAL-05`. Future migration of a legacy rule requires an explicit FR-174 disposition and does not block the five-rule MVP. | Requirements analysis | Product stakeholder direction (HD-01, HD-17, HD-18, HD-27) |
| 2026-07-27 | CQ-14 | Which severity policy applies? | Apply §2.12: severity is versioned run evidence; protected seed severities are High, High, Medium, High, High for CORE-01 through CORE-05, and protected severity changes require two-person governance. | Requirements analysis | Product stakeholder direction and synthetic-manifest evidence |
| 2026-07-27 | CQ-22, CQ-23 | What Windows lifecycle outcome is required? | Apply §2.13 and FR-175–FR-178: upgrades retain all user data; uninstall retains it by default and removes only through explicit confirmed choice; exact Windows builds, packaging, certificates, and timestamping are Architecture/release decisions. | Requirements analysis | Inherited approved Windows delivery requirements and product direction |
| 2026-07-27 | CQ-25 | What performance envelope blocks the MVP? | Retain the approved root baseline of 10,000 GED detail rows on an 8–16 GB Windows laptop within two minutes. Architecture adds safe workbook-complexity ceilings and optional-rule stress profiles before implementation; no unsupported 100-rule timing promise is introduced. | Requirements analysis | Inherited root NFR-001 and product direction (HD-19, HD-27) |
| 2026-07-27 | CQ-26, CQ-27 | Which AI and retention boundaries apply? | Ask Fin is deny-by-default and may use only on-device or explicitly organization-approved private processing; if none exists it is unavailable while deterministic validation remains complete. Reviews have no automatic expiry, archive is explicit, referenced rules/audit remain replayable, and temporary artifacts are removed at lifecycle end; mechanisms are Architecture decisions. | Requirements analysis | Inherited ADR-009/ADR-014 and product direction (HD-05, HD-18, HD-27) |
| 2026-07-27 | CQ-08 | What distinguishes an Informational/Advisory observation from a Low-severity control Finding? | An advisory rule produces `OBSERVATION`, `NO_OBSERVATION`, or `NOT_EVALUATED` and never a control FAIL or failure Finding. A Low-severity Finding is still created only from a control rule's FAIL result; severity does not convert it into advice. | Spec audit | Product stakeholder direction (HD-03, HD-05) |
| 2026-07-27 | CQ-24 | Is Ask Fin part of the first V2 release? | Yes. HD-20 requires Review Summary navigation to Ask Fin. Ask Fin remains explanation-only, same-run scoped, and subject to the separately approved provider/network boundary. | Product definition | Product stakeholder (HD-20) |
| 2026-07-27 | CQ-28, CQ-31 | How should duplicate Budget keys and formula-backed financial cells behave? | For the V1 sample contract, duplicate canonical Budget detail keys block validation. A formula uses its stored finite numeric result with formula/result lineage; absent usable result makes the field invalid and dependent rules `NOT_EVALUATED`. Broader formula evaluation is a future extension. | Spec audit | Product stakeholder (HD-19) |
| 2026-07-27 | CQ-20, CQ-21 | Which V1 parse domains and reconciliation precision apply? | Apply the sample-driven domains in §11.2/§11.4 and exact two-decimal comparison with no tolerance in §11.5. Broader organization formats and tolerance policies are future versioned configurations. | Spec audit | Product stakeholder (HD-19) |
| 2026-07-27 | CQ-18, CQ-19 | Which fields and exceptions define an exact duplicate in V1? | Fingerprint all 15 GED A:O fields under §11.6, with typed canonical values and minimal whitespace/line-ending normalization. No event-class exception applies; a pair must match every field. Broader normalization and event policy are future configurable extensions. | Spec audit | Product stakeholder (HD-19) |
| 2026-07-27 | CQ-15, CQ-16, CQ-17 | What financial basis, transaction population, and layout scope govern V1? | The supplied reports are the V1 business contract. Apply BGT/ATD meanings and eligible GED behavior in §11.1/§11.5, and use `SLV-001` for V1-compatible departments. Enterprise accounting policy and additional layouts do not block the MVP. | Spec audit | Product stakeholder (HD-19) |
| 2026-07-27 | CQ-09 | How do scope results roll up and affect the V1 executive status? | Apply the deterministic Rule Execution, Overall Review Status, and RAG mapping policy in §2.7. Optional and advisory outcomes remain visible but do not change V1 Overall Review Status; future policy changes require a versioned configuration. | Spec audit | Product stakeholder (HD-20) |
| 2026-07-27 | CQ-03, CQ-04 | Which period evidence and mismatch behavior apply to the supplied reports? | Apply §11.3: selected month/year is workspace identity, GED row 3 must match, GED row 4 is run date only, Budget is visibly workspace-assigned, and V1 has no period override. | Spec audit | Product stakeholder (HD-19) |
| 2026-07-27 | CQ-01, CQ-02 | How do the supplied reports resolve department identity and display name? | Apply §11.2: the Budget Grand Total and GED department-total numbers are authoritative report identities; detail-row numbers remain CORE-02 inputs; display the one distinct matching GED detail name or an explicit Absent/Conflicting state without invented expansion. Broader identity conventions are future extensions. | Spec audit | Product stakeholder (HD-19) |

## 14. Future configurable-extension backlog

These items are intentionally outside the V1 clarification gate:

- enterprise-specific alternatives to the V1 meanings of BGT, ATD, ETC, EAC, and DELTA;
- additional Budget/GED layouts, department-code patterns, account-code patterns, period calendars, and currency scales;
- organization-specific GED inclusion/exclusion, reversal, accrual, allocation, and duplicate-normalization policies;
- fuzzy or semantic duplicate detection;
- trusted formula recalculation beyond stored numeric results.
