# Stage 01 — Product and Financial Control Decisions

**Program:** FinSight Production-Readiness and Governed Release Program
**Stage:** 01 — Baseline Freeze and SDD Reconciliation
**Document status:** Candidate decision package
**Approval status:** **Pending Product Owner approval**
**Effective status:** **Not effective**
**Gate:** Stage 02 must not begin until every blocking decision in this
document is approved or given an explicit approved deferral.

## 1. Purpose and decision discipline

This register presents the product, financial-control, recovery, reporting,
platform, privacy, and deployment decisions that must be frozen before
production behavior changes.

The recommended options are analyst recommendations. They are not approvals and
do not change the current requirements, architecture, implementation, rule
catalog, release scope, or historical evidence.

For every decision:

- the Product Owner records the product-scope decision;
- the additional approvers named for that decision record their own decision;
- two roles listed as distinct approvers must be performed by different people;
- protected-rule decisions require the requester and Financial Control Approver
  to have different stable Actor IDs;
- a rejected recommendation must identify the selected alternative and its
  rationale;
- an approval is valid only when the actor, role, date/time, decision text, and
  governing evidence are recorded; and
- no blank field below may be interpreted as implied approval.

## 2. Resolution terminology

| Term | Meaning |
|---|---|
| Resolved by Section 15 | The latest stakeholder directive supplies a clear product direction, but a Stage 01 approval record is still required. |
| Constrained by Section 15 | The directive eliminates or constrains options but does not select one complete implementation baseline. |
| Not resolved by Section 15 | An explicit Product Owner and specialist-authority decision remains necessary. |
| Blocking | The sequential program may not enter Stage 02 while the item remains pending. |

## 3. Decision register

### S1-D01 — Permanent protected Rule IDs

**Decision question:** Which identifiers are the permanent identities of the
five protected baseline controls?

**Options**

- **A — Retain `R-VAL-01` through `R-VAL-05`.** Treat `CORE-01` through
  `CORE-05` only as human-readable control aliases.
- **B — Rebaseline `CORE-01` through `CORE-05` as permanent Rule IDs.**
  Formally supersede the existing identity contract and migrate every
  downstream reference.
- **C — Assign a new third identifier family.** Migrate both current identifier
  families to new permanent identities.

**Recommended default:** **Option A.**

**Rationale and impacts**

- The approved requirements assign `R-VAL-01` through `R-VAL-05` as
  collision-free permanent identities and explicitly define the `CORE-*`
  values as aliases.
- Retaining those identities avoids silently repurposing any of the 57 preserved
  legacy Rule IDs.
- Current `CORE-*` persistence must be corrected through a governed migration or
  compatibility alias; historical evidence must not be rewritten in place.
- Seeds, migrations, Rule Sets, Rule Results, Findings, UI, reports, exports,
  citations, Ask Fin, replay, and the independent oracle must resolve the same
  identity.
- Option B is possible only as an explicit protected-baseline rebaseline with
  historical compatibility. Option C adds ambiguity without business value.

**Section 15 effect:** **Not resolved by Section 15.** Section 15 names the five
controls but does not assign numeric Rule IDs.

**Required distinct approvers**

1. Product Owner — selects the permanent product identity.
2. Financial Control Approver — approves the protected-control identity with a
   stable Actor ID different from the requester.
3. Data/Architecture reviewer — attests that the migration and replay strategy
   preserves history; this reviewer must not be the migration implementer.

**Blocking status:** **Blocks Stage 02.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Product Owner name / Actor ID |  |
| Product Owner decision timestamp |  |
| Financial Control Approver name / Actor ID |  |
| Financial Control approval timestamp |  |
| Independent Data/Architecture reviewer |  |
| Rationale or conditions |  |
| Superseded decision/reference, if any |  |

### S1-D02 — CORE-04 scope and Budget formula checks

**Decision question:** Do Budget formula/arithmetic checks belong inside the
protected CORE-04 required-GED-field rule?

**Options**

- **A — Restore the six-field GED-only CORE-04 contract.** Keep structural
  formula/cached-value safety in workbook compatibility. If financial Budget
  arithmetic checks are required, define them as a separately identified,
  versioned, governed rule.
- **B — Expand CORE-04 through an approved protected successor.** Change its
  purpose, dataset, scope population, and historical comparison contract.
- **C — Remove all Budget formula checks.** Retain only workbook safety and the
  five existing protected controls.

**Recommended default:** **Option A.**

**Rationale and impacts**

- CORE-04 evaluates one GED transaction for six fields: Department Number,
  Account Number, Fiscal Period, Journal Number, Journal Date, and Amount.
- Section 15 prohibits hidden rules and results that cannot be linked to an
  active Rule ID and Rule Version.
- Reader-level checks that determine whether formula cells and cached values can
  be read safely are intake compatibility, not a financial pass/fail rule.
- A Budget arithmetic control, if retained, needs its own stable ID,
  classification, immutable version, configuration, active Rule Set binding,
  result/evidence contract, positive/negative/boundary tests, and reporting.
- Restoring the original CORE-04 meaning requires regeneration of scope counts,
  fixtures, oracle results, summaries, and replay/migration evidence.

**Section 15 effect:** **Direction resolved; formal approval still required.**
The named baseline control is “Required GED field completeness,” and hidden
financial checks are prohibited. Budget financial checks therefore cannot
remain silently embedded in CORE-04.

**Required distinct approvers**

1. Product Owner — confirms the control purpose and first-release treatment of
   Budget arithmetic checks.
2. Financial Control Approver — approves the protected CORE-04 contract with a
   stable Actor ID different from the requester.
3. Requirements reviewer — independently verifies that no financial check
   remains undocumented or hidden.

**Blocking status:** **Blocks Stage 02.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Product Owner name / Actor ID |  |
| Product Owner decision timestamp |  |
| Financial Control Approver name / Actor ID |  |
| Financial Control approval timestamp |  |
| Independent Requirements reviewer |  |
| Separate Budget-rule disposition, if applicable |  |
| Rationale or conditions |  |

### S1-D03 — Advisory rules in the first release

**Decision question:** Are executable Informational/Advisory rules part of the
first production release?

**Options**

- **A — Include Advisory execution.** Complete the common engine, lifecycle,
  active-set, `OBSERVATION`/`NO_OBSERVATION`, reporting, export, audit, replay,
  and test paths for at least one approved Advisory rule.
- **B — Formally defer Advisory execution.** Preserve the governed
  classification and future architecture, but ship no active Advisory rule and
  make no UI or report claim that the class executes in release 1.
- **C — Remove the Advisory classification.** Delete it from the product model
  and future extension contract.

**Recommended default:** **Option B.**

**Rationale and impacts**

- No first-release business Advisory rule has an approved definition or
  acceptance oracle.
- Deferral keeps the release focused on protected and optional deterministic
  controls without discarding the planned extensibility model.
- The pre-validation summary must truthfully show `0 advisory rules`.
- Advisory counts, observations, filters, exports, and report sections must be
  absent or explicitly “not included,” never presented as executable.
- Option A materially expands engine, lifecycle, UI, audit, export, and
  qualification scope. Option C creates avoidable architectural churn.

**Section 15 effect:** **Not resolved by Section 15.** It applies Advisory
requirements only “if included in the governed release scope.”

**Required distinct approvers**

1. Product Owner — decides include or defer.
2. Financial Control Approver — confirms that a deferral does not weaken the
   five mandatory controls and that Advisory outcomes do not affect core status.
3. Rule Governance/Architecture reviewer — verifies the UI, engine, and
   documentation accurately reflect the chosen scope.

**Blocking status:** **Blocks Stage 02 until included or explicitly deferred.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Product Owner name / Actor ID |  |
| Product Owner decision timestamp |  |
| Financial Control Approver |  |
| Financial Control approval timestamp |  |
| Rule Governance/Architecture reviewer |  |
| Rationale or conditions |  |

### S1-D04 — Managed backup and replacement-machine restore

**Decision question:** Does release 1 include complete governed backup and
replacement-machine restore?

**Options**

- **A — Retain complete governed recovery.** Deliver encrypted backup,
  replacement-machine restore, review/rule/run/result/finding/evidence/audit
  continuity, permitted Ask Fin history, managed-copy lifecycle, and
  disposed-scope revocation.
- **B — Use an approved enterprise-managed recovery dependency.** Defer the
  FinSight-owned workflow only if one governed enterprise mechanism satisfies
  the complete recovery, continuity, authorization, and disposal contract.
- **C — Provide same-machine copy or no managed recovery.** Treat loss of a
  machine as loss of local review history.

**Recommended default:** **Option A.**

**Rationale and impacts**

- A production financial-review product must preserve its audit and replay
  evidence after device loss or replacement.
- A DPAPI-only database copy or ordinary filesystem copy is not
  replacement-machine recovery.
- Backup must not contain source workbook bytes or complete normalized Working
  or Verified datasets when the approved minimization contract excludes them.
- Restore must preserve exact identities, hashes, ordering, relationships,
  publication state, and historical replay, and must fail closed for disposed
  content.
- This is a substantial Stage 05 implementation and clean-replacement-machine
  qualification obligation.

**Section 15 effect:** **Strongly constrained but not fully resolved.** Section
15 requires encrypted backups and backup/restore/disposal auditability, but the
Product Owner must still explicitly retain or replace the complete
replacement-machine NFR-101 obligation.

**Required distinct approvers**

1. Product Owner — selects the recovery obligation.
2. Security/Data Governance approver — approves encryption, key recovery,
   retention, disposal, and external-copy boundaries.
3. Financial Control Approver — confirms that restored evidence remains
   complete and historically reproducible.
4. Architecture/Release reviewer — attests that the selected path is
   qualification-ready and independent of its implementer.

**Blocking status:** **Blocks Stage 02 while undecided and blocks packaging if
retained but not delivered.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Product Owner name / Actor ID |  |
| Security/Data Governance approver |  |
| Financial Control Approver |  |
| Independent Architecture/Release reviewer |  |
| Approval timestamps |  |
| Rationale or conditions |  |

### S1-D05 — Mandatory PDF and spreadsheet exports

**Decision question:** Which user-facing reports and exports are mandatory in
release 1?

**Options**

- **A — Adopt the complete Section 15 package.** Provide the three PDF detail
  levels and the fifteen-sheet XLSX evidence workbook defined by Section 15.
- **B — Retain the earlier minimum.** Provide a printable Review Summary/PDF and
  spreadsheet-compatible Findings, Rule Results, and summarized financial data.
- **C — Defer downloadable reports and exports.**

**Recommended default:** **Option A.**

**Rationale and impacts**

- Section 15 is the latest explicit reporting direction and supersedes the
  earlier minimum if approved.
- Every output must bind one exact Review Version, Validation Run, Rule Set,
  source fingerprint set, generation actor/time, and publication state.
- Reports and spreadsheets consume recorded deterministic projections and must
  never calculate financial truth independently.
- The complete package adds an audit appendix, evidence references,
  confidentiality labels, export integrity metadata, charts/tables, accessible
  output checks, pagination, size/detail controls, and a generation
  confirmation screen.
- Option A materially expands Stage 05 and final qualification but matches the
  enterprise report objective.

**Section 15 effect:** **Resolved by Section 15, subject to formal baseline
approval.**

**Required distinct approvers**

1. Product Owner — approves release scope and report levels.
2. Financial Control Approver — approves the financial contents, labels, and
   deterministic source-of-truth contract.
3. Security/Confidentiality approver — approves exported data, destination
   warning, labeling, temporary workspace, and cleanup controls.
4. Reporting/Accessibility reviewer — independently verifies output completeness
   and accessibility.

**Blocking status:** **Blocks Stage 02 until recorded and blocks packaging until
delivered.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Product Owner name / Actor ID |  |
| Financial Control Approver |  |
| Security/Confidentiality approver |  |
| Independent Reporting/Accessibility reviewer |  |
| Approval timestamps |  |
| Rationale or conditions |  |

### S1-D06 — Ask Fin release inclusion

**Decision question:** Is private Ask Fin enabled in the first production
release?

**Options**

- **A — Include and automatically enable it.** Ask Fin is ready whenever the
  approved managed local runtime/model is healthy; otherwise one clear
  unavailable message and Retry action is shown.
- **B — Include the code but ship it disabled or administrator opt-in.**
- **C — Defer Ask Fin from release 1.**

**Recommended default:** **Option A.**

**Rationale and impacts**

- Ask Fin remains explanatory, local-only, citation-bound, fail-closed,
  review/run-scoped, and unable to create authoritative values or actions.
- Automatic readiness removes manual identity approval, Ollama installation,
  model download, endpoint configuration, Terminal use, and daemon startup.
- Inclusion makes production model/runtime identity, hostile-input testing,
  prompt/citation verification, network capture, resource limits, retention,
  automatic provisioning, repair, upgrade, rollback, uninstall, and license
  review mandatory.
- Provider failure must never block deterministic review, reports, or exports.

**Section 15 effect:** **Resolved by Section 15, subject to formal baseline
approval.** Ask Fin is part of the audit/report contract and the final installer
must automatically provide or configure its private runtime and model.

**Required distinct approvers**

1. Product Owner — approves first-release inclusion.
2. Security/Privacy approver — approves local-only enforcement, retention,
   network controls, and fail-closed behavior.
3. AI Governance/Safety approver — approves the model profile, closed claim
   protocol, citations, refusals, and prompt-injection controls.
4. Financial Control Approver — confirms Ask Fin cannot determine financial
   truth or decisions.

**Blocking status:** **Blocks Stage 02 until recorded and blocks release unless
the complete safety/provisioning scope passes.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Product Owner name / Actor ID |  |
| Security/Privacy approver |  |
| AI Governance/Safety approver |  |
| Financial Control Approver |  |
| Approval timestamps |  |
| Rationale or conditions |  |

### S1-D07 — Supported Budget and GED layout scope

**Decision question:** Which source workbook layouts are supported in release 1?

**Options**

- **A — Exact `SLV-001` under `WRL-001`.** Support only the supplied Budget and
  GED structures and their approved safety/resource profile.
- **B — Add tolerant aliases or permissive fallback behavior to `SLV-001`.**
- **C — Add multiple versioned source layouts before release.**

**Recommended default:** **Option A.**

**Rationale and impacts**

- Budget: worksheet `Original Budget`, row-1 header, columns A:H, Account Name in
  B and BGT in C.
- GED: worksheet `GED`, header row 7, body from row 8, fields A:O.
- Total rows remain evidence but are excluded from detail rule scopes; malformed
  non-total GED rows remain transaction candidates for CORE-04.
- Worksheet-name compatibility alone is insufficient.
- Unsupported structures fail with evidence rather than being guessed.
- Every future layout or enlarged resource profile requires a versioned reader
  contract and security/performance review.

**Section 15 effect:** **Not resolved by Section 15.**

**Required distinct approvers**

1. Product Owner — selects the business source scope.
2. Financial Control/Data Owner — confirms the exact row/field meanings.
3. Software/Security/Performance Architecture reviewer — approves the reader and
   resource boundary independently of implementation.

**Blocking status:** **Blocks Stage 02.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Product Owner name / Actor ID |  |
| Financial Control/Data Owner |  |
| Independent Architecture reviewer |  |
| Approval timestamps |  |
| Rationale or conditions |  |

### S1-D08 — Supported Windows hardware baseline

**Decision question:** What Windows platform and hardware class must the first
release support?

**Options**

- **A — Retain the existing enterprise baseline.** x86-64 Windows 11 Enterprise
  24H2 and 25H2; 8 GB RAM minimum class; 16 GB RAM standard class; CPU-only
  operation required; GPU acceleration optional and not required.
- **B — Raise the supported minimum to 16 GB RAM.**
- **C — Broaden the first release to additional Windows editions, versions,
  architectures, or required GPU paths.**

**Recommended default:** **Option A.**

**Rationale and impacts**

- Both 8 GB and 16 GB clean-machine images must pass the approved workbook,
  deterministic review, accessibility, packaging, and Ask Fin qualification
  matrix.
- No supported workflow may depend on a GPU.
- If the 8 GB class cannot satisfy the approved performance and stability
  criteria, the program must return for a governed baseline change rather than
  weakening evidence or silently treating it as unsupported.
- Additional Windows versions or hardware paths require a separately approved
  qualification change.

**Section 15 effect:** **Not resolved by Section 15.**

**Required distinct approvers**

1. Product Owner — approves the supported user population.
2. Enterprise Desktop/Release Engineering approver — approves the support
   matrix and installation context.
3. Performance Engineer — independently approves workload and Ask Fin evidence
   on both RAM classes.
4. Architecture reviewer — confirms no unsupported platform assumption remains.

**Blocking status:** **Blocks Stage 02 while undecided and blocks clean-machine
qualification.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Product Owner name / Actor ID |  |
| Enterprise Desktop/Release approver |  |
| Independent Performance Engineer |  |
| Independent Architecture reviewer |  |
| Approval timestamps |  |
| Rationale or conditions |  |

### S1-D09 — Approved local-AI deployment topology

**Decision question:** Who owns installation and lifecycle of the approved local
AI runtime and model?

**Options**

- **A — FinSight-owned local runtime.** The governed offline distribution
  provisions and controls the exact approved runtime and model.
- **B — Coordinated enterprise-managed dependency.** One enterprise deployment
  automatically provisions FinSight, runtime, model, policies, and service
  configuration without end-user action.
- **C — User-managed prerequisite.** Require the user to install/start Ollama or
  download/configure a model.

**Recommended default:** **Option A** for the manager-shareable production
distribution.

**Rationale and impacts**

- The expected experience is installer download, install, open, and use; no
  Terminal, manual Ollama, manual model pull, endpoint, digest, or environment
  configuration is permitted.
- The signed offline package must pin and verify exact binary/model identity,
  bind the service to loopback, disable cloud behavior, control start/health,
  implement repair/update/rollback/uninstall, and record versions/digests.
- Redistribution and required notices must receive legal approval.
- Option B remains a valid later enterprise channel only if it produces the same
  zero-user-action, offline, governed outcome. Option C is prohibited.

**Section 15 effect:** **Constrained but not selected.** Section 15 rules out
Option C and requires automatic provisioning, but either a complete A or B
topology could satisfy the experience.

**Required distinct approvers**

1. Product Owner — selects the deployment topology.
2. Software Architect — approves runtime ownership and integration boundaries.
3. Security/Privacy approver — approves binary/model identity, loopback,
   egress, service account, ACL, and lifecycle controls.
4. Release Engineering/Enterprise IT approver — approves install, repair,
   update, rollback, and uninstall operations.
5. Legal/License authority — approves runtime/model redistribution and notices.

**Blocking status:** **Blocks Stage 02 while undecided and blocks packaging and
Ask Fin release.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Product Owner name / Actor ID |  |
| Software Architect |  |
| Security/Privacy approver |  |
| Release Engineering/Enterprise IT approver |  |
| Legal/License authority |  |
| Approval timestamps |  |
| Rationale or conditions |  |

### S1-D10 — macOS release obligation

**Decision question:** Does the first production release require a distributable
macOS application in addition to the governed Windows product?

**Options**

- **A — Require simultaneous Windows and macOS production distributions.**
- **B — Defer macOS distribution.** Preserve platform-neutral deterministic-core
  behavior and developer regression coverage where practical, but qualify and
  release only Windows.
- **C — Permanently remove macOS compatibility and parity obligations.**

**Recommended default:** **Option B.**

**Rationale and impacts**

- The latest governing objective is a one-click Windows desktop application and
  Section 15 defines a signed Windows installer as the final distribution.
- Existing architecture retains macOS parity language, creating a scope
  contradiction that must be resolved rather than ignored.
- Deferral avoids duplicating signing, packaging, local-runtime provisioning,
  accessibility, clean-machine, upgrade, repair, and uninstall qualification.
- The deterministic core, fixtures, and financial oracle should remain
  platform-neutral; no release claim is made for macOS.
- Option C would create unnecessary product lock-in and requires a broader
  architectural supersession.

**Section 15 effect:** **Strongly constrained but not formally resolved.**
Section 15 specifies Windows distribution but does not explicitly supersede the
existing macOS parity obligation.

**Required distinct approvers**

1. Product Owner — approves Windows-only release scope and macOS deferral.
2. Software Architect — approves the retained platform-neutral core boundary.
3. Release Engineering approver — confirms no macOS artifact is represented as
   a release deliverable.
4. Financial Control reviewer — verifies deterministic rule/oracle behavior is
   not made Windows-specific.

**Blocking status:** **Blocks the Stage 01 scope freeze.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Product Owner name / Actor ID |  |
| Software Architect |  |
| Release Engineering approver |  |
| Financial Control reviewer |  |
| Approval timestamps |  |
| Rationale or conditions |  |

### S1-D11 — Enterprise retention policy

**Decision question:** How long are authoritative reviews, rules, results,
evidence, audits, exports, backups, and policy-permitted Ask Fin content
retained?

**Options**

- **A — Hard-code one universal product retention period.**
- **B — Use an administrator-controlled, versioned organization retention
  policy.** In the absence of an approved policy, retain authoritative records
  and allow only separately confirmed governed whole-scope disposal; never
  silently age-delete evidence.
- **C — Allow ordinary users to delete records or select retention periods.**

**Recommended default:** **Option B.**

**Rationale and impacts**

- FinSight should not invent an organization-wide legal retention duration.
- The policy must define each record class, minimum duration, legal hold,
  archive/backup behavior, Ask Fin content treatment, export responsibility,
  disposal authorization, and audit tombstone treatment.
- Every run/report must retain the policy ID/version in force when it was
  created.
- No automatic age-based deletion occurs until an authorized organization
  policy is approved, configured, tested, and auditable.
- Ordinary users cannot shorten retention or remove audit evidence.

**Section 15 effect:** **Constrained but not resolved.** Section 15 requires
enterprise retention and immutable audit but provides no duration or
record-class schedule.

**Required distinct approvers**

1. Product Owner — approves the product behavior.
2. Data Governance/Records Management authority — approves the schedule and
   legal-hold behavior.
3. Security/Privacy approver — approves Ask Fin, backup, export, log, and
   disposal treatment.
4. Financial Control Approver — approves retention of financial-control and
   historical-replay evidence.

**Blocking status:** **Blocks the Stage 01 scope freeze; the exact organization
schedule must be approved before pilot use.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Retention policy ID / version |  |
| Product Owner name / Actor ID |  |
| Data Governance/Records authority |  |
| Security/Privacy approver |  |
| Financial Control Approver |  |
| Approval timestamps |  |
| Approved schedule or conditions |  |

### S1-D12 — Report size and default detail level

**Decision question:** Which PDF detail level is the default, and how are large
reports handled?

**Options**

- **A — Default to Standard Financial Review.** Offer Leadership Summary Only
  and Complete Evidence Report as explicit alternatives. Support the full
  approved `SLV-001`/`WRL-001` population without silently dropping required
  data; paginate or move complete GED/audit evidence to appendices and the XLSX
  evidence workbook.
- **B — Default to Leadership Summary Only.**
- **C — Default to Complete Evidence Report.**

**Recommended default:** **Option A.**

**Rationale and impacts**

- Standard is useful for routine leadership and financial review without making
  the first export unnecessarily large.
- The confirmation screen must identify selected detail level, included
  sections, explicit exclusions, review/run/rule-set identity, publication
  state, and generating actor.
- Complete Evidence must include all required rows and audit history for every
  supported workbook within the approved resource profile. It may paginate and
  use an accompanying XLSX but may not silently downgrade or omit data.
- A failed size/resource check must stop generation with a clear remedy; it must
  not create an apparently complete truncated report.
- No arbitrary row threshold is approved in this candidate. Performance and
  output-size qualification may establish a versioned technical ceiling only
  if it still covers the approved `SLV-001`/`WRL-001` release scope.

**Section 15 effect:** **Partially resolved.** Section 15 defines the three
levels and permits pagination/appendices, but it does not select the default or
an omission policy.

**Required distinct approvers**

1. Product Owner — selects the default level and user choice.
2. Financial Control Approver — approves section completeness and explicit
   exclusion language.
3. Reporting/Accessibility approver — approves pagination, table alternatives,
   bookmarks, reading order, and large-report behavior.
4. Performance/Release reviewer — independently qualifies supported maximum
   output generation.

**Blocking status:** **Blocks the Stage 01 reporting scope freeze.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Default detail level |  |
| Product Owner name / Actor ID |  |
| Financial Control Approver |  |
| Reporting/Accessibility approver |  |
| Independent Performance/Release reviewer |  |
| Approval timestamps |  |
| Approved limits or conditions |  |

### S1-D13 — Configurable enterprise confidentiality label

**Decision question:** How is the confidentiality label on PDF and XLSX exports
controlled?

**Options**

- **A — Use only a fixed product label:** `Confidential — Internal Financial
  Review`.
- **B — Use an administrator-controlled, versioned organization label with the
  fixed phrase as the nonempty default.** Ordinary users cannot remove or
  weaken it at export time.
- **C — Allow each exporting user to enter or omit free-form label text.**

**Recommended default:** **Option B.**

**Rationale and impacts**

- The default is `Confidential — Internal Financial Review`.
- An authorized organization administrator may configure a stronger approved
  label through a versioned policy, not through the ordinary export dialog.
- The label value and policy version are captured in export metadata and audit.
- PDF and XLSX display the same label consistently; blank output is rejected.
- Historical exports retain their original label and are not retroactively
  changed when policy changes.
- Option C permits accidental downgrading and inconsistent records.

**Section 15 effect:** **Partially resolved.** Section 15 requires a
confidentiality label and allows an approved organization label, but it does not
define who controls changes or the fallback behavior.

**Required distinct approvers**

1. Product Owner — approves configurability and default text.
2. Security/Confidentiality approver — approves control, placement, and
   downgrade prevention.
3. Data Governance/Records authority — approves organization labeling policy
   and audit retention.
4. Reporting reviewer — independently verifies consistent PDF/XLSX rendering.

**Blocking status:** **Blocks the Stage 01 reporting/confidentiality scope
freeze.**

**Decision record**

| Field | Recorded value |
|---|---|
| Status | **Pending Product Owner approval** |
| Selected option |  |
| Default label |  |
| Product Owner name / Actor ID |  |
| Security/Confidentiality approver |  |
| Data Governance/Records authority |  |
| Independent Reporting reviewer |  |
| Approval timestamps |  |
| Rationale or conditions |  |

## 4. Candidate consolidated recommendation

The candidate first-release decision set is:

| Decision | Candidate option |
|---|---|
| S1-D01 | A — permanent `R-VAL-01` through `R-VAL-05` |
| S1-D02 | A — GED-only CORE-04; separately govern Budget financial checks |
| S1-D03 | B — defer executable Advisory rules |
| S1-D04 | A — complete governed backup and replacement-machine restore |
| S1-D05 | A — complete Section 15 PDF and XLSX outputs |
| S1-D06 | A — include automatically ready private Ask Fin |
| S1-D07 | A — exact `SLV-001`/`WRL-001` only |
| S1-D08 | A — Windows 11 x86-64, 8 GB minimum/16 GB standard, CPU-only |
| S1-D09 | A — FinSight-owned bundled offline runtime/model |
| S1-D10 | B — defer macOS distribution; preserve platform-neutral core |
| S1-D11 | B — versioned organization retention policy; no silent age deletion |
| S1-D12 | A — Standard report default; explicit Summary/Complete choices |
| S1-D13 | B — administrator-controlled label; nonempty default |

This table is a recommendation only. It becomes effective only after the
decision records above and the final approval record below are complete.

## 5. Package approval record

| Field | Recorded value |
|---|---|
| Package status | **Pending Product Owner approval** |
| Decisions approved |  |
| Decisions rejected or returned |  |
| Conditions |  |
| Product Owner name / Actor ID |  |
| Product Owner approval timestamp |  |
| Financial Control Approver name / Actor ID |  |
| Financial Control approval timestamp |  |
| Security/Data Governance approval reference |  |
| Architecture/Release approval reference |  |
| Independent Stage 01 review reference |  |
| Stage 01 gate result |  |

Until this record and every applicable decision record are complete, the
candidate defaults are not authorized and Stage 02 remains blocked.
