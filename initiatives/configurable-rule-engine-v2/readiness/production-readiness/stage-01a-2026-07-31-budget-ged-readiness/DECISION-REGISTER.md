# Stage 01A Decision Register

**Status:** Open  
**Rule:** A blank decision is not implied consent  
**Gate:** Every blocking decision must be approved or explicitly deferred

## S1A-D01 — Governing source and truncated-draft disposition

**Question:** Is the complete 1,073-line attachment the governing new change
source, with the two shorter physically truncated files retained only as
supporting provenance?

**Recommended option:** Yes. This yields one complete Budget/GED-only source
and removes the truncated draft's conflicting `GED & Invoice Review` wording.

**Authority:** Product Owner.  
**Blocking:** Yes.  
**Decision:** Pending.

## S1A-D02 — Durable financial-data persistence profile

**Question:** What durable data replaces or preserves the accepted
reconstruction/minimization contract?

- **A — Preserve reconstruction.** Persist bindings, fingerprints,
  corrections, verified fingerprints, results, and evidence references; do
  not persist complete normalized Budget/GED rows. Restart reconstruction
  still depends on matching source files.
- **B — Managed normalized-row store.** Persist encrypted normalized source
  rows, reviewed values, verification snapshots, and cell lineage in a
  governed SQLite-backed store; do not persist raw workbook bytes. Supersede
  ADR-012/NFR-110 through a new ADR and migration.
- **C — Managed raw-source copies plus rows.** Store encrypted workbook bytes
  and normalized rows under a complete retention/disposal policy.

**Recommended option:** **B.** It meets the new requirement that a review
survive restart without depending on a user-managed source path, while avoiding
duplicate raw workbook storage. It requires approved at-rest encryption,
backup, retention, migration, and secure-disposal designs.

**Authorities:** Product Owner, Data/Architecture, Security/Privacy, Data
Governance.  
**Blocking:** Yes.  
**Decision:** Pending.

## S1A-D03 — Executable provider scope

**Question:** Which provider profiles may actually receive Ask Fin prompts in
this release stage?

- **A — Local-only executable.** Ollama and Deterministic-Only operate now;
  external profiles are deferred and not presented as usable.
- **B — Approved-private executable.** Ollama, Deterministic-Only, Azure
  OpenAI, private OpenAI-compatible, and private Anthropic-compatible adapters
  may operate only under an approved policy bundle, endpoint allowlist, OS
  credential reference, and pre-prompt authorization check.
- **C — Local acknowledgement.** Any desktop user can acknowledge a warning
  and enable an arbitrary remote endpoint.

**Recommended option:** **B only if S1A-D04 is approved by Security/Privacy;
otherwise A.** Option C is rejected because the desktop MVP does not enforce an
enterprise administrator role.

**Authorities:** Product Owner decides release scope; Technical Lead/Software
Architect owns the successor architecture; Security/Privacy, Data Governance,
AI Governance/Safety, and Financial Control review the applicable boundary.  
**Blocking:** Yes.  
**Decision:** Pending.

## S1A-D04 — External-provider data and authorization policy

**Question:** For each nonlocal provider, which exact data classes may leave
the device, which masking/tokenization is mandatory, who authorizes the
profile, and how endpoint trust is established?

The approval must classify at least: review identity, department, account
number/name, vendor, amounts, findings, evidence excerpts, workbook/worksheet,
row/cell references, free-text descriptions, conversation history, and audit
metadata. It must define certificate/TLS requirements, redirect/proxy rules,
credential storage, prompt minimization, logging, retention, revocation, and
incident handling.

**Recommended authorization model:** Ordinary Reviewers may select only an
immutable, enabled Provider Profile that is delivered through a signed
administrator-controlled organization policy. The application does not expose
arbitrary external endpoint creation as ordinary review work. An in-product
warning acknowledgement informs the user but is not authorization. Profile
creation/revocation is attributable to the signed policy authority until an
enforced enterprise AI Provider Administrator role exists.

**Recommended default if unanswered:** No nonlocal prompt execution.  
**Authorities:** Product Owner and Technical Lead/Software Architect, with
Security/Privacy, Data Governance, AI Governance/Safety, and Financial Control
approval for transmitted financial classes.  
**Blocking:** Yes for external execution; no for local-only work.  
**Decision:** Pending.

## S1A-D05 — Physical deletion of never-used optional rules

**Question:** May a never-used Tested optional Rule Version be physically
deleted, or does Tested remain immutable and retire-only?

- **A — Draft-only physical deletion.** Never-used Draft objects may be
  physically deleted with an audit tombstone; Tested and later versions retire.
- **B — Draft and never-used Tested deletion.** Both may be deleted if no
  retained Rule Set or Validation Run references them, with transactional
  reference checks and a content-free audit tombstone.
- **C — Retirement only.** No rule definition is physically deleted.

**Recommended option:** **A.** It preserves the accepted meaning of Tested as
immutable evidence while still removing abandoned drafts. If the stakeholder
requires B, FR-145 and the rule-lifecycle ADR need an explicit successor.

**Authorities:** Product Owner, Financial Control, Data Governance.  
**Blocking:** Yes.  
**Decision:** Pending.

## S1A-D06 — Deterministic likely-duplicate predicate

**Question:** Which signal set and threshold creates a likely-duplicate
warning?

**Recommended MVP policy:** For two distinct nondeleted ReviewCycles, classify
same canonical department + same reporting month/year as a likely duplicate
unless the exact fingerprint rule makes it an exact duplicate. This is a
warning, not a block. It deliberately avoids an unjustified fuzzy percentage.

The comparison displays, but does not use as hidden pass/fail factors:

- normalized Budget and GED filenames;
- raw SHA-256 fingerprints;
- approved layout-version and worksheet-structure fingerprints;
- extracted department and period;
- detail-row counts;
- exact normalized Budget, ATD, and parseable GED totals;
- versioned normalized-content fingerprints; and
- the other review's lifecycle/publication state.

The normalized-content fingerprint uses the approved layout version and every
typed material row field in source order, excluding filename and physical
workbook container metadata. Architecture records the hash-policy version; it
may not choose a similarity threshold.

An exact duplicate remains same department, period, raw Budget fingerprint,
and raw GED fingerprint and is blocked. A Reviewer may continue after a likely
warning only by selecting `Continue as a New Review` and providing a nonblank
reason. Audit records candidate Review IDs, predicate version, every displayed
signal/difference, actor, reason, and time. Revalidation in the same
ReviewCycle bypasses cross-review duplicate classification.

**Authorities:** Product Owner and Data/Architecture.  
**Blocking:** Yes.  
**Decision:** Pending.

## S1A-D07 — June governed rule/check disposition

**Question:** Which already-approved root rules are activated as review-scoped
Optional rules for the June oracle, with which exact configuration?

The existing catalog—not presentation code—defines the candidate semantics:

| Case | Existing authority | Recommended stage disposition | Required approved configuration/evidence |
|---|---|---|---|
| Unusual month-over-month increase | FR-032 / `R-BUD-03` | Include as Optional | `CP-MOM-THRESHOLD` amount/percentage logic, zero-prior behavior, severity bands; both periods and exact delta |
| Missing expected GED entry | FR-037 / `R-GED-03` reference mode | Include only if a finance-maintained expected-entry reference is approved | Expected-entry stable key, expected period, reference version, exclusions, severity; absence evidence |
| Delayed posting | FR-039 / `R-GED-04` | Include only if a cutoff calendar is approved | Fiscal/cutoff calendar version, posting-date field, days-late bands/exclusions; posting/cutoff evidence |
| Amount anomaly | FR-040 / `R-GED-06` | Exclude from the June Rule Set because the approved trailing-history minimum is unavailable | Retain root requirement for a later history-qualified release; create no June Rule Execution, Rule Result, observation, or Finding |
| Coding/vendor expectation | FR-042 / `R-GED-05`, plus CORE-02 for Budget mapping | Include Budget mapping through CORE-02; exclude optional `R-GED-05` from the June Rule Set unless approved vendor reference data is supplied | CORE-02 uses the exact Budget key set; if R-GED-05 is later included, record vendor/account reference version, provisional-new handling, severity, and observed/expected evidence |
| Duplicate GED | FR-038 / protected CORE-03 | Include through protected core | Existing exact 15-field duplicate contract and evidence |
| Budget-to-GED mismatch | protected CORE-05 | Include through protected core | Existing Budget ATD versus eligible GED sum contract |

For every included Optional rule, the approval record must supply its exact
Rule ID/version, parameter values, scope, severity policy, evidence template,
and positive/negative/boundary oracle. A selected rule whose enumerated scope
lacks a required dependency returns `NOT_EVALUATED`. A deferred or excluded
rule is not selected and creates no Rule Execution, Rule Result, observation,
or Finding. Neither state may be inferred as a hidden presentation finding.

**Recommended option:** Approve the table's dispositions; provide the named
configuration values before FIX-JUN-001 is generated. No presentation-only
financial detection is permitted.

**Authorities:** Product Owner and Financial Control.  
**Blocking:** Yes for the June oracle, comparison, and finding counts.  
**Decision:** Pending.

## S1A-D08 — Ask Fin transcript retention

**Question:** What are the retention, backup, archival, legal-hold, deletion,
and disposal periods for Ask Fin messages and citations?

**Recommended policy:** Retain conversations with their exact Review Version
and Validation Run for the review's approved retention period; make prior-run
conversations read-only; include content only in encrypted governed backups;
remove it during authorized whole-review disposal; never store hidden
chain-of-thought.

**Authorities:** Product Owner, Security/Privacy, Data Governance/Records.  
**Blocking:** Yes. This supplies only the Ask Fin record-class subpolicy and
depends on predecessor S1-D11; it does not resolve that broader enterprise
retention decision.  
**Decision:** Pending.

## S1A-D09 — First post-validation view

**Question:** Does `Overview` replace the current Review Summary landing view,
or is the current Review Summary retained as a separate first page?

**Recommended option:** `Overview` becomes the first post-validation page and
absorbs the current Review Summary executive cards. `Leadership Summary`
remains a separate deterministic printable narrative. This avoids duplicate
top-level views while preserving all FR-185/FR-186 content.

**Authority:** Product Owner; independent UX reviewer verifies the result.  
**Blocking:** Yes for results IA.  
**Decision:** Pending.

## S1A-D10 — Prior-period financial and recurrence semantics

**Question:** Is the following complete deterministic comparison policy
approved for May-to-June and future adjacent-period comparisons?

### Eligible prior review and tie-break

Eligible candidates have the same canonical Department Number, an earlier
reporting period, compatible approved Budget/GED layout versions, and a
published completed Validation Run. Choose the greatest earlier year-month. If
more than one candidate exists for that month, choose the one with the latest
publication timestamp; break an exact timestamp tie by ascending Review ID.
Record the selected Review ID/run and policy version. A user may explicitly
choose another eligible candidate, but that creates and records a new
comparison projection rather than silently changing the default.

### Financial period bases

- `YTD GED Spend` is the eligible GED sum in the selected YTD report through
  the report period.
- `Current Fiscal-Period GED Activity` is the eligible GED sum whose Fiscal
  Period equals the review period.
- `YTD Movement` is current YTD spend minus prior YTD spend and is never labeled
  monthly spend.
- Budget/ATD/ETC/EAC/DELTA are compared as source-report snapshots and labeled
  accordingly.
- All money uses the existing exact Decimal/sign conventions.

### Comparison identities

| Type | Stable identity |
|---|---|
| Department | canonical Department Number |
| Account | Department Number + Account Number |
| Vendor | Department Number + extractor-normalized vendor name (Unicode normalize, trim, collapse whitespace, casefold); blank is an explicit `No vendor` bucket |
| Finding | permanent Rule ID + governed finding type + deterministic rule scope key |
| Data quality/result | permanent Rule ID + deterministic rule scope key |

An Account Name change does not change an account identity; it is recorded as
an attribute change on the same Department+Account key. An Account Number
change or vendor-name change creates a new identity unless an approved
versioned mapping links the old and new keys. A Finding whose
rule/configuration versions are not declared comparison-compatible is
`Not Comparable`.

### Classification precedence

Comparison records use two explicit axes so `Continuing` is not confused with
whether the continuing condition improved or worsened.

Apply this recurrence precedence first:

1. incompatible layout/rule/configuration/identity → recurrence
   `Not Comparable`, trend `Not Comparable`;
2. required prior evidence absent → recurrence `Missing Prior Evidence`,
   trend `Missing Prior Evidence`;
3. current only → recurrence `New`, trend `Not Applicable`;
4. prior only → recurrence `Resolved`, trend `Not Applicable`
   (deterministic detection ended; reviewer-managed status does not control
   this classification);
5. present in both → recurrence `Continuing`, then calculate trend.

For a `Continuing` record, apply this trend precedence:

1. exact comparison values equal → `Unchanged`;
2. unfavorable metric or severity rank increases → `Worsened`;
3. unfavorable metric or severity rank decreases → `Improved`;
4. neither favorable direction is defined → `Changed`, with neutral
   `Increased`, `Decreased`, or `Changed` detail.

For account Budget health, the unfavorable metric is `GED spend - BGT`; a
lower value is improved and a higher value is worsened. For missing/duplicate/
coding/reconciliation results, FAIL severity rank then exact financial/count
impact is the unfavorable metric. GED completeness uses missing required value
count, where lower is improved. Vendor spend alone has no favorable/unfavorable
meaning and therefore uses `Continuing` plus increased/decreased detail unless
a recorded rule result establishes an unfavorable association.

Every difference is significant at the exact stored cent/count/severity level;
rule-specific materiality affects whether the active rule emits a Finding, not
whether the recorded comparison changed. Results may filter by recurrence or
trend, and must display both when both exist (for example,
`Continuing · Improved`).

### Evidence and causation

Every comparison cites both runs and both source projections. FinSight may say
a vendor is associated with spend in an over-budget account. It may claim the
vendor caused pressure only when a governed source record/rule establishes
causation. Delay and missing-expectation claims require the approved
calendar/reference from S1A-D07.

**Recommended option:** Approve this policy as written. Any altered identity,
precedence, or metric must be recorded in this decision before Requirements
approval; Architecture implements but does not choose it.

**Authorities:** Product Owner and Financial Control; Data/Architecture
attests implementability.  
**Blocking:** Yes for FR-231–FR-233, FIX-JUN-001, ORACLE-JUN-001, and
VER-MOM-001.  
**Decision:** Pending.

## Approval record

| Decision | Selection | Approver name/role | Timestamp | Conditions |
|---|---|---|---|---|
| S1A-D01 |  |  |  |  |
| S1A-D02 |  |  |  |  |
| S1A-D03 |  |  |  |  |
| S1A-D04 |  |  |  |  |
| S1A-D05 |  |  |  |  |
| S1A-D06 |  |  |  |  |
| S1A-D07 |  |  |  |  |
| S1A-D08 |  |  |  |  |
| S1A-D09 |  |  |  |  |
| S1A-D10 |  |  |  |  |
