# FinSight V2 — Configurable Rule-Engine Design

- **Status:** Draft — AI-PROPOSED for named human review
- **Initiative:** Configurable Rule Engine V2
- **Product relationship:** Evolution of the existing FinSight product and codebase
- **Decision state:** Proposed architecture design; no new or amended ADR is accepted by this document
- **Implementation authorization:** None. Application implementation remains blocked until all required Architecture artifacts are reviewed and approved.
- **Primary requirements:** FR-141–FR-165, FR-174, FR-180–FR-184, FR-192, FR-198–FR-199; NFR-081–NFR-085, NFR-089–NFR-091, NFR-093, NFR-096–NFR-099
- **Governing sources:** [V2 Functional Requirements](../specs/01-functional-requirements.md), [V2 Non-Functional Requirements](../specs/02-non-functional-requirements.md), [V2 Constitution](../specs/constitution.md), and [approved review workflow](FINANCIAL-REVIEW-WORKFLOW.md)
- **Inherited architecture:** [ADR-002](../../../specs/adr/ADR-002-layering-ports-and-dependency-rules.md), [ADR-003](../../../specs/adr/ADR-003-exact-decimal-and-determinism.md), [ADR-007](../../../specs/adr/ADR-007-findings-domain-model.md), [ADR-011](../../../specs/adr/ADR-011-review-lifecycle-and-generation-model.md), and [ADR-012](../../../specs/adr/ADR-012-source-binding-and-working-set-reconstruction.md)

## 1. Decision summary

FinSight V2 has one pure, headless, deterministic rule engine. Every Core Mandatory, Optional Configurable, and Informational/Advisory rule executes through that engine and produces the same versioned result contract.

The engine accepts exactly two immutable domain inputs:

1. one fingerprint-verified reconstructed `VerifiedDataset`; and
2. one immutable workspace-scoped `RuleSetVersion`.

It returns a deterministic `EngineEvaluation` containing the complete ordered scope-result ledger, one execution roll-up per selected rule, control Finding drafts derived only from failed control results, and the engine-owned status projections. It performs no file, database, network, UI, identity-provider, audit-store, AI-provider, clock, or random-number access.

Rule definitions are data, not executable extensions. They use a versioned canonical JSON schema, allowlisted fields and enums, exact decimal strings, and evaluator types registered in trusted application code. A rule cannot contain Python, SQL, scripts, macros, commands, loops, recursion, unrestricted expressions, or a class/module name supplied by a user.

This design makes the rule engine—not five individual UI checks—the source of every validation conclusion. The five protected controls are the first protected configuration loaded into the same engine.

## 2. Scope

This document defines:

- the deterministic engine boundary and dependency direction;
- immutable input and output contracts;
- canonical rule-definition, configuration, and rule-set serialization;
- controlled evaluator and operator allowlists;
- scope enumeration, dependency resolution, evaluation, ordering, and roll-up;
- Rule Execution, Rule Result, Finding, and status-projection behavior;
- the exact first-release CORE-01 through CORE-05 realization;
- rule lifecycle and protected-baseline governance as they constrain engine inputs;
- replay and deterministic comparison behavior;
- integration contracts for persistence and downstream consumers;
- failure semantics, test strategy, traceability, risks, and approval gates.

## 3. Non-goals

This design does not:

- define UI layouts, database tables, installer technology, or an AI provider;
- make the engine responsible for authentication, authorization, workflow navigation, source extraction, persistence, or promotion;
- permit user-authored executable logic or arbitrary expressions;
- migrate, reclassify, or activate any of the 57 preserved legacy rules in [the disposition register](../specs/03-existing-rule-disposition.md);
- add fuzzy duplicate matching, alternate source layouts, enterprise accounting policy, or department-specific logic;
- make an AI system part of rule evaluation, Finding creation, severity, status, or financial calculation;
- authorize implementation or mark any proposed architecture decision Accepted.

## 4. Architectural boundaries

### 4.1 Dependency rule

The design preserves ADR-002:

```text
Delivery/UI/Ask Fin
        |
        v
Application orchestration and governed rule services
        |
        v
Domain core: pure Rules Engine, result model, status projections
        ^
        |
Infrastructure implements core-owned persistence/audit ports
```

The domain core imports no delivery, persistence, workbook, operating-system identity, provider, or AI types. A composition root supplies infrastructure implementations to application services. The engine itself needs no port because evaluation is a pure function:

```text
evaluate(VerifiedDataset, RuleSetVersion) -> EngineEvaluation
```

Application orchestration performs authorization and preflight, calls the engine, assigns volatile run/audit metadata at the edge, and commits the authoritative records atomically. Downstream consumers query persisted engine records; they do not call evaluators independently.

### 4.2 Responsibilities

| Component | Owns | Must not own |
|---|---|---|
| Source/reconstruction service | `SLV-001` extraction, correction replay, verified-fingerprint check, immutable `VerifiedDataset` construction | Rule pass/fail decisions |
| Rule governance service | Authorization, lifecycle transitions, tests, activation, bindings, protected requests and approvals | Financial evaluation |
| Rule-set assembler | Canonical immutable workspace manifest and global-baseline reference | Ad hoc per-run selection |
| Rules Engine | Scope enumeration, dependency resolution, evaluator dispatch, results, roll-ups, Finding drafts, status projections | I/O, identity, authorization, persistence, AI |
| Validation application service | One-run gate, engine invocation, IDs/timestamps, atomic persistence, lifecycle transition | Recalculation of engine outcomes |
| Result query services | Read-only projections for summary, findings, analytics, reports, exports, and AI grounding | Independent validation logic |

## 5. Immutable engine inputs

### 5.1 `VerifiedDataset`

`VerifiedDataset` is the V2 realization of the inherited verified-data input contract. It is reconstructed under ADR-012 and FR-203 from fingerprint-matching source bindings, the recorded extractor version, and the persisted correction/confirmation basis. The complete row store is never persisted.

Before engine invocation, the application layer must prove:

- the candidate was explicitly confirmed or the Review Version validly inherits an unchanged verification basis;
- Budget and GED sources satisfy the approved compatibility, department, and period gates;
- the reconstructed fingerprint equals the Review Version's recorded verified fingerprint;
- the dataset contains immutable typed Budget detail rows, GED transaction rows, report metadata, row classifications, Current Validation Values, and raw/source lineage;
- no unconfirmed Working Candidate value or partial reconstruction is present.

The engine rejects any object not carrying the verified contract marker, fingerprint, extractor version, correction-basis version, schema/layout version, and immutable collections. It never accepts a Working Candidate.

### 5.2 `RuleSetVersion`

`RuleSetVersion` is an immutable workspace-scoped ordered manifest. It contains:

- its stable version ID, workspace ID, creation provenance, and content hash;
- one exact global `ProtectedBaselineVersion` reference;
- the status-policy version;
- ordered selected entries containing manifest ordinal, Rule ID/version/hash, configuration version/hash, binding version, enabled state, and classification;
- exactly the protected `R-VAL-01` through `R-VAL-05` entries, enabled and matching the referenced Protected Baseline Version;
- any enabled Optional Configurable or Informational/Advisory entries approved for that workspace.

Disabled bindings remain in governed history but are not selected for execution. The Validation Run pins the existing `RuleSetVersion`; users and AI cannot add, skip, reorder, or replace rules for one run.

### 5.3 Volatile execution envelope

Run ID, initiating Actor ID, start/completion timestamps, attempt identity, and correlation ID are authoritative orchestration metadata, not engine inputs. Before evaluation, the application layer persists the one stable run envelope and first attempt under the one-run constraint. After evaluation, it adds completion/ledger metadata without changing any engine outcome. These values are retained for provenance but excluded from the deterministic comparison projection in functional requirements §2.6.

## 6. Controlled canonical rule model

### 6.1 Versioned records

A governed rule is represented by three independently immutable records:

- `RuleDefinitionVersion`: evaluator semantics, inputs, grain, dependencies, status/evidence behavior;
- `RuleConfigurationVersion`: governed operand values, severity policy, and other approved parameters;
- `RuleBindingVersion`: workspace applicability and enabled/disabled state.

`RuleSetVersion` pins all three. Editing Tested or Active content creates a successor Draft; it never edits a referenced version in place.

### 6.2 Canonical JSON profile

The first schema identifiers are:

- `finsight.rule-definition/1`;
- `finsight.rule-configuration/1`;
- `finsight.rule-set/1`.

Only schema-valid canonical JSON may enter testing, activation, assembly, or execution. Canonicalization is:

1. parse UTF-8 JSON while rejecting duplicate object keys;
2. reject unknown properties through `additionalProperties: false`;
3. require Unicode strings in NFC and line endings normalized to LF;
4. validate every identifier, enum, reference, and decimal string;
5. sort set-like arrays by their defined locale-independent key while preserving explicitly ordered manifest arrays;
6. serialize with RFC 8785 JSON Canonicalization Scheme;
7. calculate SHA-256 over the canonical bytes.

The submitted representation may be retained as request evidence, but only the canonical bytes and hash are tested, approved, activated, pinned, and executed. A content hash is stored in the immutable record envelope beside the canonical payload and is computed over that payload; no payload contains or hashes its own hash field.

Financial and other decimal operands are JSON strings, never JSON numbers. A fixed-scale currency operand uses `-?(0|[1-9][0-9]*)\.[0-9]{2}`; leading `+`, commas, exponent notation, leading integer zeroes, and negative zero are rejected. `-0.00` must be submitted as `0.00`. COUNT thresholds use canonical nonnegative integer strings `0|[1-9][0-9]*`. A future non-currency decimal type must declare a fixed scale in a successor schema; the scale is never inferred from platform locale.

### 6.3 Definition shape

The canonical executable payload contains only:

```json
{
  "schema_version": "finsight.rule-definition/1",
  "rule_id": "R-VAL-01",
  "rule_version": "1",
  "name": "Actual spend must not exceed BGT",
  "classification": "CORE_MANDATORY",
  "evaluation_grain": "DEPARTMENT_ACCOUNT",
  "input_fields": [
    "budget.account_number",
    "budget.bgt",
    "budget.department_number",
    "ged.account_number",
    "ged.amount",
    "ged.department_number",
    "ged.fiscal_period",
    "workspace.reporting_period"
  ],
  "dependencies": [
    "REPORTS_COMPATIBLE",
    "EXACT_BUDGET_KEY_UNIQUE",
    "BGT_VALID",
    "EXACT_KEY_GED_AMOUNT_AND_PERIOD_VALID"
  ],
  "evaluator": {
    "type": "AGGREGATE_COMPARE",
    "version": "1",
    "aggregate": "SUM",
    "population": "GED_ELIGIBLE_EXACT_KEY_YTD",
    "value_field": "ged.amount",
    "operator": "LTE",
    "comparison_field": "budget.bgt"
  },
  "status_policy_version": "control-v1",
  "evidence_template_version": "core-01-evidence/1",
  "recommended_human_follow_up": "Review the planned amount and cited actual transactions with the responsible budget owner."
}
```

The immutable governance envelope binds that canonical payload/hash and separately records lifecycle state, author Actor ID/timestamps, test-suite version and outcome, configuration and severity-policy references, predecessor, approval/request evidence where applicable, and record hashes. It cannot override the payload's classification or semantics. The engine trusts neither free-form name nor follow-up text as executable input.

The other canonical records have these closed top-level shapes:

| Record | Required canonical fields |
|---|---|
| `RuleConfigurationVersion` | schema version; Rule ID/version; configuration version; evaluator-typed operand object; fixed or criteria-based severity-policy version; status-policy reference; predecessor |
| `RuleBindingVersion` | workspace ID; Rule ID/version; binding version; `ENABLED` or `DISABLED`; effective provenance; predecessor |
| `ProtectedBaselineVersion` | schema version; global baseline ID; exactly five protected Rule/configuration hashes; severity/status-policy versions; effective timestamp; activation-event ID |
| `RuleSetVersion` | schema version; workspace ID; rule-set version ID; Protected Baseline Version ID/hash; status-policy version; ordered rule entries with manifest ordinal and pinned definition/configuration/binding hashes; creation provenance |

Evaluator schemas define the only permitted operand keys for `RuleConfigurationVersion`. A configuration cannot introduce a field, operator, population, evaluator, or dependency absent from its pinned definition and schema.

A criteria-based severity policy uses the same closed field, decimal, operator, and finite-composition types. It cannot contain code or an unrestricted expression, and its resolved severity and policy version are recorded with each failed result.

### 6.4 Allowlists

The first-release evaluation grains are:

- `WORKSPACE`;
- `DEPARTMENT_ACCOUNT`;
- `GED_TRANSACTION`;
- `DUPLICATE_FINGERPRINT_GROUP`.

The first-release evaluator types are:

- `REQUIRED_FIELDS`;
- `REFERENCE_MEMBERSHIP`;
- `DUPLICATE_GROUP`;
- `DECIMAL_COMPARE`;
- `AGGREGATE_COMPARE`;
- `LOGICAL_COMPOSITION`.

The operator enums are `EQ`, `NE`, `LT`, `LTE`, `GT`, and `GTE`. Aggregate enums are `SUM` and `COUNT`. Composition enums are finite `ALL` and `ANY`; nested depth and child count are bounded by the Architecture-approved resource profile. Composition references typed allowlisted predicates, not strings containing expressions.

The field allowlist is:

- workspace: `workspace.department_number`, `workspace.reporting_period`;
- Budget: `budget.department_number`, `budget.account_number`, `budget.account_name`, `budget.bgt`, `budget.atd`, `budget.etc`, `budget.eac`, `budget.delta`, `budget.notes`;
- GED: `ged.department_number`, `ged.department_name`, `ged.account_number`, `ged.account_name`, `ged.fiscal_period`, `ged.journal_number`, `ged.journal_date`, `ged.invoice_amount`, `ged.check_number`, `ged.invoice_date`, `ged.vendor_name`, `ged.agency`, `ged.journal_description`, `ged.journal_line_description`, `ged.amount`.

Source row/cell references, raw values, formula text, record IDs, fingerprints, and row classifications are evidence/provenance properties. They are available to the engine's trusted evidence builder but cannot be selected as user-authored operands.

Adding an evaluator, operator, grain, population selector, or field requires a reviewed schema/registry version and governed product change. A user cannot expand an allowlist through configuration.

## 7. Evaluator registry

The registry is trusted domain-core code keyed only by `(evaluator_type, evaluator_version)`. Each entry supplies:

- a schema validator for its exact typed operands;
- a pure scope enumerator or a reference to the grain's shared enumerator;
- a declared dependency resolver contract;
- one pure evaluator;
- a deterministic evidence builder;
- supported classification/status combinations.

The canonical definition stores the registry key, never a Python import, module, class, SQL fragment, callback, script, or expression. Unknown or retired registry keys cannot be tested or activated. Historical versions needed by retained runs remain available until governed whole-scope disposal permits their removal.

Registry implementations are stateless. They receive immutable typed values, use the centrally pinned decimal context, and return typed outcomes. They cannot call one another by dynamic name, inspect the filesystem, import user content, or perform I/O.

## 8. Deterministic execution pipeline

For one invocation, the engine performs these steps:

1. **Validate input identities.** Verify immutable-contract markers and hashes for the `VerifiedDataset` and `RuleSetVersion`.
2. **Validate the manifest.** Confirm canonical hashes, supported schema/registry versions, unique entries, enabled bindings, and all five protected rules.
3. **Freeze selection.** Use the ordered enabled entries already captured by `RuleSetVersion`; never query a live catalog during execution.
4. **Enumerate expected scopes.** Use the declared grain and dataset indexes before evaluating the rule.
5. **Resolve dependencies.** Resolve each named prerequisite for each scope to `AVAILABLE(value/evidence)` or `UNAVAILABLE(code/evidence)`.
6. **Evaluate.** Dispatch to the allowlisted registry entry only when required dependencies are available.
7. **Create one Rule Result draft per expected scope.** Unavailable dependencies create `NOT_EVALUATED`; they never create PASS.
8. **Build one Rule Execution draft per selected rule.** Reconcile expected count and result counts, then apply the versioned roll-up policy.
9. **Create Finding drafts.** Create exactly one for each failed Core Mandatory or Optional Configurable scope and none for any other result.
10. **Project overall status and summary facts.** Apply only the Rule Set's pinned status-policy version.
11. **Return one immutable `EngineEvaluation`.** The application either persists its complete authoritative form or persists no completed ledger.

### 8.1 Scope enumeration

| Grain | Expected scopes | Stable scope key |
|---|---|---|
| `WORKSPACE` | Exactly one selected Review Version | `workspace` |
| `DEPARTMENT_ACCOUNT` | Every valid unique Budget detail key | canonical `Department Number|Account Number` |
| `GED_TRANSACTION` | Every `SLV-001` GED transaction candidate | stable source-record ID, ordered by source row then ID |
| `DUPLICATE_FINGERPRINT_GROUP` | Every distinct governed 15-field fingerprint in GED detail | lowercase SHA-256 fingerprint |

An allowed empty population produces a complete control execution with PASS or advisory execution with NO_OBSERVATION. Failure to enumerate scopes is not an empty population: it blocks completion of the run.

V1 dependencies are named data prerequisites, not arbitrary cross-rule expressions. No V1 rule consumes another rule's status. A future inter-rule dependency feature requires a successor schema and explicit cycle/order design.

### 8.2 Dependency behavior

A dependency failure is local to the narrowest resolvable scope. Another scope for the same rule continues when its evidence is complete. The resolver records a stable dependency code, affected fields/records, and source evidence.

- Missing, invalid, unmapped, or scope-inconsistent required evidence produces `NOT_EVALUATED`.
- A false or exceptional financial condition with complete evidence produces FAIL.
- An application/evaluator defect is not financial unavailability and does not become `NOT_EVALUATED`; it fails the run.
- Intake failure before reliable scope enumeration blocks engine invocation or run completion.

### 8.3 Stable total ordering

The `RuleSetVersion.rules` array is ordered by immutable manifest ordinal. The rule-set assembler assigns the protected controls first in permanent Rule ID order, followed by enabled optional/advisory rules in stable Rule ID, Rule Version, configuration-version order. The canonical manifest records the resulting ordinals.

The engine evaluates or at least emits results in:

1. manifest ordinal;
2. canonical scope key;
3. stable source-record ID as the final tie-breaker.

Parallel computation is permitted only when output is buffered and restored to that total order. Hash-map, set, database-return, locale, and thread-completion order can never affect results, evidence, findings, or serialization.

## 9. Result, execution, Finding, and status contracts

### 9.1 Rule Results and Rule Executions

Each selected rule yields exactly one `RuleExecutionDraft`. Each enumerated expected scope yields exactly one `RuleResultDraft`. The result contains the deterministic fields required by functional requirements §2.2; the application adds Run ID, IDs, Actor/time, and persistence metadata without changing its business outcome.

Permitted statuses are:

| Classification | Scope statuses | Rule Execution roll-up precedence |
|---|---|---|
| Core Mandatory | PASS, FAIL, NOT_EVALUATED | NOT_EVALUATED, then FAIL, then PASS |
| Optional Configurable | PASS, FAIL, NOT_EVALUATED | NOT_EVALUATED, then FAIL, then PASS |
| Informational/Advisory | OBSERVATION, NO_OBSERVATION, NOT_EVALUATED | NOT_EVALUATED, then OBSERVATION, then NO_OBSERVATION |

Counts on the Rule Execution must reconcile exactly to its expected-scope count. A missing or duplicate result prevents the execution and run from being represented as complete.

### 9.2 Findings

A deterministic Finding factory in the domain core consumes only a failed control `RuleResultDraft`. It produces one frozen `FindingDraft` with rule/configuration/severity versions, evaluated scope, affected entities, calculation/evaluation evidence, source lineage, and recommended human follow-up.

No Finding is created for PASS, NOT_EVALUATED, OBSERVATION, or NO_OBSERVATION. Advisory rules never create control-failure Findings. AI and delivery code receive only read-only result/finding query capabilities and are never wired to the Finding factory or command port.

### 9.3 Overall status

The engine-owned V1 status projector derives:

- `Incomplete` if any selected Core Mandatory execution is absent/incomplete or `NOT_EVALUATED`;
- `Attention Required` if all five core executions are complete and at least one is FAIL;
- `Healthy` if all five are PASS.

Optional and advisory rules remain visible but do not affect V1 Overall Review Status. RAG is a one-to-one rendering of that persisted status: Healthy → On Track/Green; Attention Required → Needs Attention/Yellow; Incomplete → At Risk/Red.

Budget Health, Data Quality, exception counts, Reconciliation Status, Top Findings, and recommended next actions use the exact projections in functional requirements §2.7. They are domain result projections, not dashboard calculations.

## 10. Exact protected baseline controls

All five definitions use the common engine and permanent protected IDs. Exact signed two-decimal arithmetic has no tolerance. Negative GED transactions reduce sums; exact duplicates remain included until the reviewed data changes.

| Control | Registry realization and scope | Deterministic outcome |
|---|---|---|
| CORE-01 / `R-VAL-01` | `AGGREGATE_COMPARE@1`, `DEPARTMENT_ACCOUNT`; sum `GED_ELIGIBLE_EXACT_KEY_YTD`, `LTE budget.bgt` | PASS when eligible GED sum ≤ BGT; FAIL when greater; NOT_EVALUATED only for invalid BGT or invalid exact-key GED Amount/Fiscal Period. Empty eligible population is `0.00`; unmatched GED rows affect no Budget scope. |
| CORE-02 / `R-VAL-02` | `REFERENCE_MEMBERSHIP@1`, `GED_TRANSACTION`; exact canonical department/account key in unique Budget detail-key index | PASS for exactly one match; FAIL for no match; NOT_EVALUATED when required identifiers cannot parse. Group/subtotal/total rows never satisfy membership. Missing Amount is irrelevant. |
| CORE-03 / `R-VAL-03` | `DUPLICATE_GROUP@1`, `DUPLICATE_FINGERPRINT_GROUP`; all 15 `SLV-001` GED fields | PASS for one member; FAIL for two or more; no NOT_EVALUATED after compatible scope enumeration. Malformed fields use deterministic typed raw/null tokens. Evidence cites every member. Exposure sums duplicate-copy Amounts after the lowest-row reference member, or is `Unavailable` if a copy Amount is nonnumeric. |
| CORE-04 / `R-VAL-04` | `REQUIRED_FIELDS@1`, `GED_TRANSACTION`; Department Number, Account Number, Fiscal Period, Journal Number, Journal Date, Amount | PASS only when all six fields are present and parseable under §11.4; otherwise FAIL naming every failed field and cell. Zero and negative Amounts are valid. Row-classification ambiguity blocks intake rather than becoming a result. |
| CORE-05 / `R-VAL-05` | `AGGREGATE_COMPARE@1`, `DEPARTMENT_ACCOUNT`; `budget.atd EQ SUM(GED_ELIGIBLE_EXACT_KEY_YTD)` | PASS for exact equality; FAIL for any difference; NOT_EVALUATED only for invalid ATD or invalid exact-key GED Amount/Fiscal Period. Empty population is `0.00`; no account-only join is permitted. |

CORE-03 canonicalizes its 15-field fingerprint exactly as functional requirements §11.6: parseable required fields use canonical parsed values; malformed required fields use deterministic type-tagged raw/null tokens; optional fields use type-tagged spreadsheet scalars; text preserves case, punctuation, and internal spaces after only outer-whitespace and line-ending normalization.

The seed severities are High, High, Medium, High, and High respectively. A run pins the exact severity-policy/configuration version. A protected severity change follows the same governed workflow as protected logic.

The [synthetic fixture oracle](../fixtures/SYNTHETIC-VALIDATION-EXPECTATIONS.md) is normative test input for cross-rule effects: one overrun, one duplicate group, one missing Amount causing two scope-level NOT_EVALUATED results, one unmapped transaction, one consequential reconciliation failure, five Findings, and Overall Review Status `Incomplete`.

## 11. Governance and version scopes

### 11.1 Ordinary lifecycle

Rule Definition Versions move only:

```text
Draft -> Tested -> Active -> Retired
```

Only Draft is editable. Passing the required tests permits advancement to immutable Tested but is not activation. Editing Tested or Active content creates a successor Draft. Rule Binding state is versioned separately. Retirement is logical; a used version remains resolvable for replay.

### 11.2 Protected baseline

`ProtectedBaselineVersion` is global and contains exactly one governed definition/configuration for each protected Rule ID plus severity/status-policy versions and effective time. It is not a workspace Rule Set Version.

A protected change requires:

1. a Rule Administrator-authored Draft;
2. successful positive, negative, and boundary tests;
3. advancement of the exact canonical hash to immutable Tested;
4. a protected request referencing that exact hash and recording reason, before/after evidence, proposed effective time, and binding effects;
5. approval by a different effective Financial Control Approver Actor ID;
6. atomic activation and creation of a successor Protected Baseline Version at the approved time.

Rejection is terminal and creates no activation. Protected disablement, retirement, deletion, or replacement cannot leave fewer than all five controls; it requires an approved active successor for the same protected Rule ID. Prior definitions, decisions, baselines, rule sets, and runs remain immutable and replayable.

Global activation changes no existing workspace. A new workspace uses the then-effective Protected Baseline Version. Applying a newer baseline to an existing workspace requires explicit Financial Control Approver authorization and creates one successor workspace Rule Set Version. Optional/advisory binding changes create a successor Rule Set Version only for that workspace and never create a Protected Baseline Version.

Authorization and two-person separation are application/governance concerns outside the pure evaluator. The engine nevertheless fails manifest preflight if the pinned workspace Rule Set omits, duplicates, disables, or mismatches any protected entry.

## 12. Replay, reanalysis, and comparison

- **Exact replay:** unchanged verified data, Rule Set Version, configurations, registry versions, and status policy are evaluated again in memory. The ordered §2.6 business-result projection is compared with the retained projection. No Review Version or second authoritative Validation Run is created; the application appends one Replay Verification Event.
- **Rule-set reanalysis:** changed governed Rule Set over the same verified basis creates a `RULESET_REANALYSIS` generation with a new authoritative run.
- **Configuration reanalysis:** changed governed configuration over the same verified basis creates a `CONFIG_REANALYSIS` generation with a new authoritative run.
- **Source or extractor change:** requires a successor Working Candidate, fresh confirmation, and `SOURCE_REVERIFICATION` or `EXTRACTOR_REVERIFICATION`.

The comparison projection includes ordered rule/configuration versions, scope keys, statuses, calculations, normalized evidence references, severities, and Finding content. It excludes volatile IDs, timestamps, actor IDs, and correlation IDs. Comparison reports added, removed, and changed results/findings without altering either generation.

Canonical JSON, exact decimals, explicit formats, injected edge timestamps, and total ordering make the projection value- and byte-identical across repeated runs and supported platforms.

## 13. Failure semantics

| Failure | Required behavior |
|---|---|
| Invalid/unknown schema, enum, evaluator, operator, grain, field, or decimal | Reject the definition before testing or activation; execute nothing |
| User code, SQL, macro, script, command, or expression | Reject on every create/import/edit/test/activate path; execute nothing |
| Invalid Rule Set manifest or missing/mismatched protected entry | Block validation before engine evaluation |
| Unverified, partial, missing, mismatched, or extractor-divergent dataset | Block invocation; expose reconstruction recovery without changing retained results |
| Scope enumeration impossible | Block run completion; do not fabricate an empty population or complete ledger |
| Required evidence unavailable for one enumerated scope | Persist `NOT_EVALUATED` for that scope with dependency evidence |
| Evaluator defect, unsupported historical registry implementation, or invariant violation | Fail the run with a stable diagnostic; do not translate the defect into PASS, FAIL, or NOT_EVALUATED |
| Cancellation or process interruption | Persist no partial complete ledger; recovery exposes the prior state or one complete successor |
| Result, execution, Finding, or lifecycle persistence failure | Roll back the completion transaction; no orphan Finding or `Validation Complete` status |
| Consumer lacks supporting persisted engine records | Display unavailable; never recalculate or infer a conclusion |

Diagnostics receive correlation IDs and actionable remedies at the application edge. Logs and support bundles contain no workbook content, financial values, vendor/employee data, credentials, prompts, or retained AI responses.

## 14. Persistence and consumer integration

The application first persists one immutable Validation Run envelope and attempt record in a validation-start transaction. It then persists in one completion transaction:

- the terminal completion status/seal for that same authoritative Validation Run;
- one Rule Execution per selected rule;
- one Rule Result per expected scope;
- exactly one Finding per failed control result;
- pinned Rule Set/configuration/status/severity/registry versions and hashes;
- evidence and source-lineage references;
- engine-derived Overall Review Status and summary projection;
- lifecycle and audit events required to enter `Validation Complete`.

The complete `VerifiedDataset` and source workbook bytes are not part of that transaction. Consumers can render a retained run without reconstruction; reconstruction is needed only for row-level reviewed-data display or additional source evidence.

Review Summary, Findings, Analytics, Reports, Exports, and Ask Fin read persisted results through query ports. Trusted defaults resolve the published generation. An explicitly selected analyzed working or historical generation remains isolated and labeled. No consumer may import evaluator implementations or reconstruct pass/fail logic.

## 15. Verification strategy

### 15.1 Schema and security

- Positive canonical-schema fixtures for every evaluator, grain, operator, classification, and field family.
- Negative fixtures for duplicate keys, unknown properties/enums, noncanonical decimals, overprecision, non-NFC text, invalid references, and unsupported schema versions.
- Injection fixtures for Python, SQL, expressions, scripts, macros, commands, imports, callbacks, deep composition, and resource-limit breaches.
- Canonical-byte/hash equivalence across key-order and harmless formatting variants.

### 15.2 Evaluator and contract tests

- Unit tests for every evaluator with positive, negative, and boundary cases.
- Contract tests proving all classifications use one invocation/result/evidence contract.
- Cardinality properties: one execution per selected rule; one result per expected scope; no missing or duplicate pairs; one Finding per failed control scope only.
- Dependency properties: unavailable evidence never becomes PASS; an unavailable scope does not suppress complete sibling scopes.
- Permutation/property tests proving input row order, map order, set order, and parallel completion order do not change the deterministic projection.
- Exact-decimal boundaries including equality, `0.00`, negative values, `0.01` differences, large valid values, non-finite values, and overprecision rejection.

### 15.3 Core and golden tests

- Human-readable positive, negative, and boundary tests for CORE-01 through CORE-05.
- The Stage 2 synthetic oracle as a golden cross-rule run, including all passing scopes and the stated secondary effects.
- Mutation tests that intentionally alter joins, duplicate fields, roll-up precedence, exclusions, decimal behavior, and Finding creation and require the golden suite to fail.
- Department/period parameterization proving no sample department or May 2026 constant affects behavior.

### 15.4 Determinism and platform tests

- Repeated evaluation of identical canonical inputs produces byte-identical §2.6 projections.
- Windows and macOS produce byte-identical projections.
- Locale, timezone, hash seed, row iteration, and supported concurrency variations produce no changes.
- AI disabled, unavailable, malicious, or provider-swapped changes zero deterministic fields.
- Exact replay matches retained projections; governed rule/config changes produce only explainable comparison deltas.

### 15.5 Governance, atomicity, and performance

- Full lifecycle tests for Core, Optional, and Advisory versions and bindings.
- Two-person protected request/approval, rejection, scheduled activation, workspace upgrade, denied bypass, and immutable-history tests.
- Fault injection at rule creation, activation, Rule Set assembly, generation/run/result/Finding persistence, and publication boundaries.
- NFR-081 benchmark: compatible single-department Budget/GED, at most 10,000 GED detail lines, five protected rules, no optional rules, completed Review Summary within 120 seconds on approved 8–16 GB target hardware.
- Traceability annotations from every implementation and test back to the exact FR/NFR and protected Rule ID.

## 16. Architecture fitness rules

The later implementation plan must include automated checks that:

- the domain engine imports no UI, infrastructure, workbook, identity, provider, or AI modules;
- delivery/AI code cannot reference a Finding command/factory capability;
- no financial path uses binary float, locale-dependent parsing, implicit database ordering, wall-clock reads, or randomness;
- no consumer imports evaluator implementations or computes validation statuses independently;
- only registry implementations can execute evaluator semantics;
- protected Rule IDs cannot be absent or disabled in an executable Rule Set Version;
- used canonical definitions, configurations, registry versions, and status policies remain resolvable;
- implementation and tests carry `Implements:` and `Verifies:` traceability.

## 17. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Configurability becomes an unsafe scripting surface | Closed schemas, `additionalProperties: false`, fixed enums, trusted registry, injection tests |
| A missing dependency becomes a false PASS | Typed resolver, mandatory NOT_EVALUATED, dependency-failure matrix |
| Result counts drift from scope counts | Pre-enumeration, unique `(run, rule, scope)` contract, atomic completeness check |
| Cross-platform decimal or ordering drift | Exact strings/Decimal, canonical JSON, explicit scope order, both-OS golden tests |
| Core rules become one-off code paths | Same registry, invocation, result, evidence, persistence, and audit contracts for all classifications |
| A UI/report recreates financial logic | Read-only persisted-result projections and architecture fitness tests |
| Rule history becomes unreplayable | Immutable versions/hashes, retained registry implementations, pinned manifests, replay gates |
| Global and workspace version scopes are conflated | Separate `ProtectedBaselineVersion` and `RuleSetVersion` types, repositories, and transaction tests |
| A protected change bypasses two-person governance | Distinct stable Actor IDs, exact Tested hash, terminal request state, atomic activation audit |
| Scope volume degrades performance | Prebuilt immutable indexes, one enumeration pass per grain, bounded composition, NFR-081 benchmark |
| Legacy rules are silently activated or repurposed | Preserve all 57 unchanged; FR-174 migration gate and collision checks |

## 18. Traceability

| Design area | Requirements |
|---|---|
| Common configurable engine and classifications | FR-141–FR-142, FR-145–FR-148; NFR-084, NFR-097–NFR-098 |
| Protected baseline and governance | FR-143–FR-144, FR-149–FR-151, FR-174, FR-189–FR-190, FR-198–FR-199; NFR-085, NFR-089–NFR-090, NFR-107–NFR-108 |
| Immutable verified inputs and one-run binding | FR-128, FR-139–FR-140, FR-152, FR-171–FR-173, FR-192, FR-196, FR-203; NFR-082, NFR-110 |
| Scope/result/execution/Finding contracts | FR-153–FR-157, FR-164, FR-184; NFR-082–NFR-083, NFR-091, NFR-093 |
| Engine-owned status and downstream truth | FR-158, FR-165–FR-170, FR-185–FR-188; NFR-091, NFR-093, NFR-103 |
| Published/working result isolation and identity | FR-165, FR-167, FR-171–FR-173, FR-185–FR-194, FR-202; NFR-082, NFR-089, NFR-091, NFR-101–NFR-103 |
| Five protected rules and source semantics | FR-159–FR-164, FR-180–FR-183; NFR-083, NFR-096 |
| Determinism, security, extensibility, and delivery quality | NFR-081, NFR-084–NFR-086, NFR-089–NFR-091, NFR-096–NFR-100, NFR-103–NFR-104 |
| Synthetic golden expectations | FR-148, FR-159–FR-164; NFR-036 inherited, NFR-083, NFR-098 |

## 19. Review and approval gate

This Draft should not be treated as accepted architecture. The single independent package-level Architecture review must cover the pure-engine boundary, canonical schema and registry, dependency/order model, exact CORE-01 through CORE-05 contracts and severities, non-executable rule surface, protected governance, persistence cardinality/immutability/version/atomicity, historical resolution, and fixture/property/golden/fault/performance/cross-platform verification strategy.

Any review change that alters approved financial semantics, role authority, protected governance, result status, or lifecycle behavior must return through governed Requirements change control. Architecture may refine implementation mechanisms only within the approved contracts.

Until the complete Architecture package passes that independent review and receives Project Owner approval, no application implementation is authorized.
