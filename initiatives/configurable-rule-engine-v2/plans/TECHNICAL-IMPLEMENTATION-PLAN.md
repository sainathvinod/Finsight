# FinSight Configurable Rule Engine V2 — Technical Implementation Plan

- **Status:** Draft — Architecture-stage review and explicit Project Owner approval required
- **Date:** 2026-07-27
- **Implementation authorization:** None
- **Plan type:** Stage-based, workflow-vertical delivery plan for the existing FinSight repository and application
- **Inputs:** Independently reviewed V2 Requirements; Draft Application Architecture, Rule Engine Design, Persistence Model, and UX/UI Design; Proposed ADR-V2-001 through ADR-V2-007

## 1. Outcome and boundary

Extend the existing FinSight Python/PySide6 modular monolith into a department-neutral configurable financial-validation platform whose deterministic, versioned rule engine is the sole source of validation truth.

The MVP must:

- read the supplied real Budget and GED layouts without modifying source files;
- preserve and expose Original Extracted, User-Reviewed, and Current Validation Values;
- execute the five protected baseline controls and future configured rules through one engine;
- preserve one stable Validation Run identity from validation start and atomically persist its complete result ledger;
- support Reviewer, Rule Administrator, and Financial Control Approver roles;
- enforce different-person protected-change request and approval;
- open the Review Summary first after validation;
- preserve immutable review, rule, run, result, audit, and Derived Record history;
- support replacement-machine backup/restore and governed whole-scope disposal;
- restrict Ask Fin to an approved, consent-gated when external, read-only, engine-bound context; and
- ship as a signed, offline-capable Windows installer.

This plan does not authorize application code, test, migration, dependency, package, or installer changes. Architecture approval is the only authorization needed to enter Workflow Phase Implementation; no separate implementation-approval gate is introduced.

## 2. Stage-based SDD delivery model

FinSight uses exactly these approval gates:

| Stage gate | Entry | Required completion evidence | Approval effect |
|---|---|---|---|
| **Requirements** | Product direction and source evidence available | Complete requirements package and independent PASS | Completed; authorizes Architecture |
| **Architecture** | Requirements PASS | Complete Architecture package, internal consistency checks, one independent package review with material defects resolved, explicit Project Owner approval | Authorizes workflow implementation |
| **Workflow Phase Implementation** | Architecture approved | All seven workflows completed in order, each independently verified end to end, integrated regression green | Authorizes Final Product evaluation |
| **Final Product** | Workflow phase complete | Full-system functional, financial, security, accessibility, recovery, performance, and user-acceptance evidence; no unresolved material defect | Authorizes production packaging/release qualification |
| **Windows Packaging and Release** | Final Product approved | Signed executable/MSI, clean-machine qualification, provenance/SBOM/checksums, upgrade/uninstall/recovery evidence, release authorization | Authorizes distribution |

No additional approval gate is planned. A security, architecture, or business-policy issue may stop work only when it materially invalidates an approved contract; it then follows normal change control at the affected gate.

Within a stage, related artifacts and findings are handled as one batch: complete the required work, run internal consistency checks, perform one independent review, repair material defects together, and present the stage. Editorial-only churn does not reopen a completed review.

Implementation and remediation work inside these gates uses the two routes
defined in [FinSight Delivery Execution Lanes](EXECUTION-LANES.md):

- the **Governed Lane** for architecture, business logic, persistence, security,
  rule-engine, data-model, workflow, dependency, packaging, or governed-artifact
  changes; and
- the **Rapid UX Lane** only for purely visual changes that preserve architecture,
  persistence, security, business rules, workflow semantics, dependencies, and
  data behavior.

Rapid UX work runs only the impacted UI, accessibility, and launch checks,
produces screenshots, and stops for Project Owner review. It does not run the
full regression suite, regenerate unchanged specifications, or reopen
architecture/governance review unless a material governed impact is discovered.
Discovery of such an impact stops the Rapid UX change and reclassifies it to the
Governed Lane.

## 3. Delivery principles

1. **One product, repository, and application.** Extend `src/finsight`; do not create a sibling product or duplicate the specification system.
2. **Strict workflow order.** Complete one workflow end to end before beginning product work in the next workflow.
3. **Vertical completion.** Every workflow includes backend, frontend, persistence, audit, accessibility, tests, documentation, and independent verification.
4. **Parallelism stays inside the active workflow.** Independent components may be developed concurrently only when their contracts are already fixed and the next workflow has not begun.
5. **No shadow validation.** UI, analytics, reports, exports, and Ask Fin consume the persisted engine ledger and never recompute pass/fail.
6. **Immutable evidence.** Used versions, run basis, completed ledgers, audit facts, and Derived Records are append-only; correction creates a successor fact.
7. **Fail closed.** Unknown identity, authorization, source layout, rule schema, evaluator, reconstruction basis, encryption state, or AI egress condition cannot become a financial PASS.
8. **Exact arithmetic and canonical data.** Financial values use exact `Decimal`/fixed-scale storage and versioned canonical serialization; binary float is prohibited.
9. **Source minimization.** Source workbook bytes and complete normalized, Working, or Verified row stores never enter authoritative persistence or backup.
10. **Traceability.** Tasks, code, migrations, tests, findings, and evidence reference FR/NFR, ADR, Architecture Contract, workflow, and commit/build identity.

## 4. Existing-code strategy

### 4.1 Reuse and extend

- `src/finsight/domain` for immutable records, invariants, evaluator registry, and projections;
- `src/finsight/application` for workflow orchestration, reconstruction, governance, authorization, validation, and query services;
- `src/finsight/infrastructure` for workbook readers, encrypted repositories, migrations, identity, backup, exports, and private AI adapters;
- `src/finsight/delivery/desktop` for the PySide6 shell and accessible views;
- `src/finsight/app.py` as composition root;
- import-linter dependency rules;
- exact financial parsing/formatting in `domain/money.py`;
- additive migration runner and existing source-fingerprint/lifecycle concepts where their contracts remain valid.

### 4.2 Replace or supersede

V2 must not preserve these V1 behaviors as product truth:

- GED header row 4/data row 5 or shifted Budget amount mapping;
- normalized records that discard department, transaction, or source-cell evidence;
- account-only verified aggregation;
- quarantine of missing required values before CORE-04 can evaluate them;
- Budget-key iteration that drops unmapped GED transactions;
- a single hard-coded variance rule or 20% threshold;
- run IDs derived only from truncated input fingerprints;
- `INSERT OR REPLACE` for immutable history;
- literal actor `local-user`;
- eight/nine-step lifecycle presentation;
- report health inferred independently from Finding presence;
- unencrypted production SQLite;
- external AI without approved provider plus active informed consent; or
- wheel/zipapp-only Windows distribution.

## 5. Common Definition of Workflow Done

A workflow may advance to the next workflow only when all rows below are satisfied for its scope.

| Dimension | Required evidence |
|---|---|
| Backend | Domain/application contracts implemented without outward dependency violations |
| Frontend | Complete role-appropriate journey with loading, empty, error, recovery, and prohibited-action states |
| Persistence | Forward migration, repository contracts, integrity constraints, recovery behavior, and no unauthorized overwrite |
| Audit | Attributable success, denial, failure, and material read events with privacy-safe payloads |
| Accessibility | Keyboard completion, accessible names/states, focus restoration, 200% scaling, high contrast, reduced motion, and no color-only meaning |
| Testing | Unit/property, contract, persistence/fault, integration, UI journey, security, and regression coverage proportional to risk |
| Determinism | Same approved inputs/configuration produce the same business-result projection where the workflow touches validation truth |
| Security/privacy | Threat cases and sensitive-data scans pass; source files remain unchanged; no unapproved egress |
| Documentation | User/admin/developer behavior, errors, migration/recovery, and requirement traces updated |
| Independent verification | A reviewer who did not author the change inspects the integrated workflow; blocker/critical/major findings are repaired and rechecked before progression |

Independent workflow verification is an engineering exit condition, not an extra Project Owner approval gate. Minor editorial findings may be scheduled without delaying progression when they cannot change behavior, security, auditability, or implementation.

## 6. Workflow implementation sequence

### Workflow 1 — Review Management

**User outcome:** An authenticated user can create, resume, identify, govern, and navigate the correct review without exposing unauthorized data.

**Backend**

- establish immutable domain types for Actor, permissions, ReviewCycle, Working Candidate, Review Version/Generation, seven Review Status values, disposition, analytical/publication state, and Derived Record identity;
- establish `DisposalRegistryPort`, registry lineage/token-epoch, committed/pending protected-head, journal-event, and fail-closed startup-admission types before protected store open; Workflow 7 completes backup/disposal operations over this boundary;
- implement replaceable `IdentityProvider`, Windows SID identity, and permission policy with explicit-denial precedence;
- implement signed, versioned external role-assignment manifest validation;
- implement review create/resume, working/published pointers, status transitions, abandon/resume, close/archive, and read-only historical access;
- establish Architecture Contracts AC-01 through AC-07 and import/forbidden-dependency fitness checks.

**Frontend**

- implement permission-aware shell, Welcome/Create/Open Review, workspace identity header, lifecycle/status display, and safe empty/error states;
- expose actor/role context without allowing in-app role assignment;
- keep financial status separate from lifecycle and publication status.

**Persistence and audit**

- qualify and introduce SQLCipher production access with DPAPI machine protection, restrictive ACLs, exclusive local-store lock, and no plaintext fallback;
- append forward-only V2 migrations while preserving migrations 0001–0003;
- add review, identity, authorization, status, audit-stream, HMAC-chain, and pointer entities;
- add append-only generation analytical-state events with native/legacy origin and the separate platform-protected recovery-control journal/head foundation outside the SQLCipher store;
- replace V2 overwrite paths with immutable inserts or explicit compare-and-swap;
- audit sensitive reads, authorized/denied actions, lifecycle transitions, and manifest decisions.

**Accessibility and tests**

- three-role action matrix, unresolved identity, multi-role union, self-approval denial, manifest tamper/rollback/expiry, second-instance, ACL, encryption, migration-fault, registry genesis/head/pending crash behavior, lifecycle, keyboard, scaling, and assistive-name tests;
- dependency qualifications for SQLCipher, DPAPI/SID, signed manifest, PySide6, and macOS Keychain adapter occur as implementation tasks here, not as a new approval gate.

**Exit evidence:** A stable authenticated actor can create/resume and navigate an encrypted, attributable review shell; unauthorized or unverifiable actors see only non-sensitive shell/help. Independent Workflow 1 verification PASS.

### Workflow 2 — Upload & Extraction

**User outcome:** A Reviewer selects one Budget and one GED source, and FinSight safely extracts the real supplied structures and identifies department/period without mutating either file.

**Backend**

- implement exact Budget/GED `SLV-001` readers and `WRL-001` safety/resource limits;
- Budget uses Account Number A, Account Name B, BGT C, and approved ATD/ETC/EAC/DELTA/Notes columns;
- GED uses report metadata rows, header row 7, body from row 8, all fields A–O, and exact row classification;
- preserve transaction candidates with missing/malformed required values for CORE-04;
- reject workbook macros/external links/executable content, hostile archives, unsupported protection, and ambiguous total/header shapes;
- extract and reconcile department, reporting-period, filename, worksheet, count, formula, and source-lineage evidence.

**Frontend**

- provide exactly two role-labeled upload slots, preflight progress/cancel, file/structure evidence, metadata summary, and actionable mismatch/resource errors;
- keep reporting-period/source selection volatile until both sources pass, then display the authoritative `Data Uploaded` review.

**Persistence and audit**

- atomically create a new review/candidate, adjacent Draft/Data Uploaded events, two source bindings, metadata evidence, initial Rule Set reference, and audit only after both sources pass;
- persist filename/path hint/fingerprint/provenance but never workbook bytes or complete extracted rows;
- make failed or canceled new intake leave zero authoritative partial review.

**Accessibility and tests**

- supplied synthetic files; headers, totals, blanks, formulas, moved/missing files, department/period mismatch; ZIP-bomb/resource/path/TOCTOU cases; progress/cancel; keyboard file selection; clear non-color-only state;
- prove source fingerprints and bytes are unchanged.

**Exit evidence:** The supplied Budget/GED pair yields the approved row classifications, counts, metadata, and lineage within `WRL-001`, and unsafe/mismatched input fails closed. Independent Workflow 2 verification PASS.

### Workflow 3 — Extraction Review

**User outcome:** A Reviewer can inspect, correct, revert, compare, and confirm a review-local working copy while the source remains immutable.

**Backend**

- reconstruct typed Working Dataset views from matching sources plus correction/reversion basis;
- allow corrections to every approved extracted business field without row insertion/deletion or provenance mutation;
- implement Original Extracted, User-Reviewed, and Current Validation Value semantics;
- confirm one exact basis, calculate the verified fingerprint, and create a sealed Review Version at `Data Reviewed`;
- enforce fresh verification for changed source/extractor/data and exact inherited basis only for governed reanalysis.

**Frontend**

- virtualized Budget/GED tables, search/filter/sort, field inspector, source lineage, edit/revert history, pending/confirmed labels, diff preview, and exact confirmation affirmation;
- block validation while corrections/source basis are unconfirmed;
- show reconstruction-unavailable recovery without hiding retained authoritative results.

**Persistence and audit**

- persist only source bindings, correction/reversion events, correction bases, confirmation, verification fingerprint, counts, metadata, actor/time/reason, and lineage;
- never persist a complete normalized, Working, or Verified row store;
- atomically consume the candidate and create the immutable Review Version.

**Accessibility and tests**

- all editable fields, original/prior/resulting/reversion history, no-edit confirmation, source mismatch, extractor divergence, restart reconstruction, virtual-grid keyboard navigation, focus, scaling, and large-table responsiveness;
- storage inventory proves prohibited full-row/source-byte stores are absent.

**Exit evidence:** A confirmed Review Version reconstructs byte-identically from its recorded basis, owns exactly one initial `VERIFIED` analytical-state event, and makes every changed value attributable and reversible. Independent Workflow 3 verification PASS.

### Workflow 4 — Validation Engine

**User outcome:** Authorized users can govern safe configurable rules, and a Reviewer can run one immutable Rule Set against one confirmed Review Version to produce one complete deterministic ledger.

**Backend — rule model and governance**

- implement closed canonical JSON schemas, RFC 8785 profile, exact decimals, controlled fields/grains/operators/aggregates/composition/dependencies, and trusted evaluator registry;
- implement Rule Definition, Configuration, and Binding Versions;
- implement Draft → Tested → Active → Retired and separate Enabled/Disabled bindings;
- require positive, negative, and boundary tests;
- implement Optional/Advisory activation, disablement, retirement, and workspace binding;
- implement five protected IDs `R-VAL-01` through `R-VAL-05`, global Protected Baseline Version, workspace Rule Set Version, request/decision/effective activation, different-person approval, and explicit existing-workspace upgrade;
- implement durable future-activation due jobs, in-process timing, signed Windows Task Scheduler/macOS `launchd` wake adapters, and fail-closed overdue-startup reconciliation;
- prohibit user code, SQL, scripts, macros, unrestricted expressions, unknown fields, or a protected manifest with fewer than five controls.

**Backend — deterministic execution**

- implement required-field, exact-reference, duplicate-group, scalar-compare, aggregate-compare/reconciliation, and finite ALL/ANY evaluators;
- implement deterministic scope enumeration, dependency handling, ordering, Rule Results, Rule Executions, Findings, status/severity policy, summary projection, and exact replay comparison;
- accept exactly `VerifiedDataset` and `RuleSetVersion` as pure engine inputs;
- create one stable run envelope at validation start, append attempts under it, evaluate off the UI thread, and atomically commit the complete ledger/seal;
- append ordered `ANALYZED` and `SUMMARIZED` generation events in that completion transaction because the ledger and engine-produced Review Summary projection commit together;
- insert the completion seal last under deferred transaction assertions and test that no dependent lifecycle/publication fact survives a seal/count failure;
- retry canceled/failed/interrupted attempts only under the same Run ID; changed basis creates the required successor Review Version.

**Frontend**

- validation preflight, stable Run ID, progress/cancel/finishing/retry states;
- Rule Library, constrained rule builder, test workbench, versions/bindings, protected request queue, before/after evidence, approval/rejection, and baseline-upgrade surfaces;
- role-gated views with commit-time authorization regardless of UI state.

**Persistence and audit**

- persist immutable rule/config/binding revisions, tests, lifecycle, manifests, requests, decisions, activations, run envelope/attempts, complete ledger, Findings, evidence, seals, lifecycle/publication, and replay events;
- persist the exact analytical-state event sequence and advance any compatibility mirror only with its authoritative event;
- HMAC-chain all material governance and run events; preserve historical definitions and bindings for replay;
- completion transaction is all-or-nothing; consumers query sealed runs only.

**Accessibility and tests**

- evaluator positive/negative/boundary/property/permutation/mutation suites;
- Stage 2 synthetic oracle: overrun, duplicate, missing Amount, unmapped department/account, secondary `NOT_EVALUATED` and reconciliation effects;
- injection/resource/canonicalization/Decimal/cross-platform determinism tests;
- all three roles, same-actor denial, terminal decisions, scheduled activation with open/closed/offline-machine/lock/tamper/missed-wake cases, inherited-basis verification honesty, immutable used versions, cancellation/retry, completion-seal fault injection, and full keyboard/governance journey.

**Exit evidence:** Rule 6 can be configured without code; all five protected controls execute through the same pure engine; one run owns one complete, replayable ledger with no partial or shadow result. Independent Workflow 4 verification PASS plus finance-owner golden-oracle sign-off.

### Workflow 5 — Results & Analytics

**User outcome:** After validation, a user first sees a self-identifying executive Review Summary and can trace every conclusion to the exact persisted result.

**Backend**

- expose read-only result-query ports for summary, Findings, complete Rule Results, and analytics;
- implement only ledger-derived validation metrics; label allowed non-validation aggregates `Descriptive`;
- enforce published-by-default and explicit isolated working/historical context.

**Frontend**

- open Review Summary first and display Department Name/Number, period, Run ID, Rule Set Version, Review Version, lifecycle, publication state, source filenames, and validation timestamp;
- show Overall Status/RAG, Budget Health, Data Quality, Reconciliation, rules executed/passed/failed/not evaluated, overrun/duplicate/missing counts, observations, Top Findings, and next actions;
- implement Findings, Rule Results, Analytics, evidence/source navigation, working-versus-published comparison, and promotion;
- use text/icon/shape plus color and accessible dense-table patterns.

**Persistence and audit**

- query only the completion-sealed ledger and stored projection/lineage;
- append finding-review and promotion/supersession events without changing originating results;
- audit sensitive result access and promotion.

**Accessibility and tests**

- ledger-to-view reconciliation, no-false-all-clear, `Incomplete`, empty population, working/published/historical isolation, deep links, virtual tables, keyboard, screen-reader semantics, high contrast, scaling, and performance;
- architecture test forbids evaluator imports or independent result calculations in consumers.

**Exit evidence:** Every displayed financial-validation conclusion resolves to one selected sealed Run/Execution/Result record and no context mixes generations. Independent Workflow 5 verification PASS.

### Workflow 6 — Ask Fin

**User outcome:** A user can request a plain-language, cited explanation of one selected run without allowing AI to create validation truth or change state.

**Backend**

- support only on-device or signed organization-approved private provider profiles;
- construct one finite allowlisted grounding corpus from a single selected run;
- implement a single external egress chokepoint with provider approval, explicit informed active consent, deterministic masking, context minimization, and immediate revocation;
- expose no command/write/validation ports to AI;
- verify structured candidate claims against exact corpus fields before rendering;
- remain fully functional with AI absent or disabled.

**Frontend**

- show exact review/run/publication/provider context;
- for external requests, show provider, exact data categories/payload preview, masking, privacy/retention implications, unselected consent, decline, and revoke;
- label AI output, citations, unsupported claims, on-device/no-transmission state, and unavailable/blocked/provider-failure states.

**Persistence and audit**

- append consent grants/revocations, interaction events, corpus/prompt/masking/provider versions, payload fingerprint, Claim/Citation/Blocked Claim records, and Derived Record outcome;
- retain policy-permitted encrypted content only; never store hidden reasoning, secrets, whole files, or complete datasets.

**Accessibility and tests**

- zero egress before consent, after revocation, for stale/mismatched consent, public/unapproved endpoints, or chokepoint bypass;
- context-minimization equality, prompt injection, cross-generation, unsupported/malformed claims, provider failure, zero write capability, accessible consent, and AI-off/provider-swap deterministic equality.

**Exit evidence:** Removing or replacing Ask Fin changes zero deterministic result or required workflow, and no external financial context leaves without approved provider plus active consent. Independent Workflow 6 verification PASS.

### Workflow 7 — Reports & Review History

**User outcome:** Users can generate self-identifying immutable outputs, inspect historical reviews, recover protected data, and perform separately governed disposal.

**Backend**

- generate PDF and spreadsheet-compatible reports/exports exclusively from result-query projections;
- implement append-only Derived Record attempts, manifests, content fingerprints, regeneration, and external-delivery evidence;
- implement Past Reviews/history, close/archive, reconstruction availability, audit timeline, and exact run/generation selection;
- implement transactionally consistent portable encrypted backup using required passphrase profile and optional approved organization-certificate profile, with mandatory `STORE_LINEAGE` plus review/period tokens, immutable token epoch, recovery-wrapped registry secret bundle, and one signed current capsule per custody-controlled managed recovery root;
- restore into quarantine, validate fully, and on replacement machines create an idempotent protected local registry segment anchored to the admitted signed-capsule checkpoint with a `RECOVERY_ADOPTION` successor before atomic store activation;
- implement `DisposalRegistryPort` over a separate HMAC-chained journal, two-phase committed/pending protected head, opaque scope tokens, authoritative `BACKUP_PREPARED`/`ACTIVE`/`RETIRED`/`REVOKED` lifecycle, and signed current capsules;
- implement protected temporary lifecycle and confirmed whole-review, whole-period, or all-data disposal using durable `DISPOSAL_PREPARED`/`DISPOSAL_COMMITTED`/safe-`DISPOSAL_ABORTED`, retained-graph rebuild, one-way tombstone linkage, managed-copy reconciliation, and crash recovery.

**Frontend**

- report/export destination and identity preview; generation/working/published/historical labels;
- show native fresh/inherited and legacy-snapshot `VERIFIED`/`ANALYZED`/`SUMMARIZED`/`EXPORTED` history; first eligible completed PDF/XLSX export advances only analytical state, while regeneration and Ask Fin do not;
- Past Reviews filters for all seven statuses plus Active/Abandoned distinction;
- backup/restore progress and clear passphrase-loss/provider limitations;
- require the current continuity capsule for managed replacement-machine restore and expose stale/rollback/revoked/prepared failures without a bypass or “restore anyway”;
- disclose the custody-controlled currentness boundary for offline replacement restores;
- disposal impact inventory, exact scope, external-copy limitation, retained content-free registry/key-envelope/capsule residue after all-data removal, separate confirmation, failure/recovery state, and no ordinary-delete affordance.

**Persistence and audit**

- retain report/export/Ask Fin Derived Records inside SQLCipher per policy;
- append `EXPORTED` in the first eligible PDF/XLSX terminal transaction even for an authorized Closed/Archived historical or superseded `SUMMARIZED` generation, serialize request-label/promotion and concurrent-export races, preserve all prior superseded facts, and never duplicate the event on regeneration;
- store managed-backup catalog/provider metadata only as evidence/projections; external registry lifecycle is authoritative and no passphrase/private key is stored in plaintext;
- append backup/restore/disposal events and content-free tombstones linked to operation plus prepared entry; committed registry event references the resulting tombstone/store hash;
- ensure disposed data cannot return through any registered managed copy.

**Accessibility and tests**

- report/manifest identity; fresh/inherited/legacy analytical origins; Closed superseded `SUMMARIZED` first historical artifact; request-label/promotion and concurrent-first-export races; regeneration/failed/Ask-Fin transitions; print/PDF visual regression; spreadsheet structure; history filters; missing-source view; replacement-machine restore and signed-checkpoint adoption interruption; wrong passphrase; missing/stale/rolled-back continuity capsule; revoked/prepared scope; catalog rollback; token epoch and `STORE_LINEAGE`; journal-only/pending-head crash cases; tamper/partial/incompatible bundle; scoped/all-data disposal; retained registry residue; reinstall; external-copy warning; keyboard/focus/scaling;
- NFR-101 seeded authoritative-graph manifest equality and out-of-scope byte-for-byte preservation.

**Exit evidence:** Historical evidence is self-identifying and immutable; replacement-machine recovery is proven; managed disposal cannot resurrect selected scope. Independent Workflow 7 verification PASS.

## 7. Workflow Phase Implementation gate

After all seven workflow exits:

- run the complete unit/property/contract/migration/integration/UI/security/accessibility/determinism suite;
- run the supplied `SLV-001` ≤10,000-GED benchmark and meet the 120-second ingest-to-summary target;
- reconcile every FR/NFR/ADR/Architecture Contract with implementation and test evidence;
- verify no unresolved blocker, critical, or major defect;
- produce one integrated independent verification report.

The Project Owner approves the **Workflow Phase Implementation** gate once. Individual workflow verification records support that decision but do not create seven additional approval gates.

## 8. Final Product gate

The Final Product stage is an integrated product evaluation, not a redesign cycle. It includes:

- complete Reviewer, Rule Administrator, and Financial Control Approver journeys;
- finance-owner acceptance of the five core rules and synthetic oracle;
- end-to-end review from creation through history/reporting with AI off and with an approved private provider;
- security threat verification, sensitive-value scans, backup/restore/disposal drills, audit-chain verification, and dependency vulnerability/license review;
- WCAG-oriented desktop accessibility review;
- Windows/macOS deterministic projection comparison;
- performance, reliability, crash/restart, corruption, and data-retention tests;
- user/admin/developer documentation review; and
- independent full-product verification.

Final Product approval authorizes packaging/release qualification. It does not itself authorize distribution.

## 9. Windows Packaging and Release gate

### Packaging architecture

- reproducible PyInstaller one-directory executable;
- WiX v4 per-machine MSI under Program Files;
- machine-scoped protected data/key directories with approved ACL;
- signed least-privilege Task Scheduler helper for already-approved future-dated activation;
- SHA-256 Authenticode signing with RFC 3161 timestamp;
- dependency lock, SBOM, hashes, build provenance, and release manifest;
- default uninstall retains encrypted data, the Disposal Registry/key envelope, and managed-recovery continuity state; any all-data removal invokes the separately governed disposal component and cannot be enabled by an unverified MSI property;
- offline operation and no telemetry/user-data update egress.

### Qualification matrix

- Windows 11 Enterprise x64 24H2 and 25H2;
- 8 GB and 16 GB target laptops;
- clean install, standard-user launch, sequential multi-actor use, scheduled-activation helper/recovery, repair, upgrade, failed-migration rollback, registry preservation/rollback detection, default-retain uninstall, separately authorized disposal, and reinstall/recovery;
- signature/timestamp/SBOM/malware verification;
- SQLCipher/PySide6/native dependency presence and wrong-build fail-closed behavior;
- NFR-081 performance fixture;
- source-file immutability, zero unintended egress, crash recovery, and replacement-machine backup restore.

The Windows Packaging and Release gate requires independent release qualification and explicit Project Owner release authorization.

## 10. Test architecture

| Level | Purpose |
|---|---|
| Pure unit/property | Decimal, canonicalization, evaluator, scope, status, lifecycle, permissions |
| Contract | Repositories, identity/provider ports, rule registry, queries, renderers, backup key providers |
| Migration/persistence | Atomicity, constraints, encryption, analytical-state sequence, append-only behavior, audit/registry chains, recovery |
| Fixture integration | Real `SLV-001` Budget/GED, corrections, five controls, cross-rule effects |
| Desktop journey | Eleven review steps, three roles, governance, accessibility, errors/recovery |
| Security/adversarial | Workbook abuse, rule injection, manifest tamper, path/egress/log leakage |
| Determinism/replay | Repeat/platform/locale/timezone/order comparisons |
| System/release | Clean-machine install, upgrade, uninstall, signing, offline, performance |

Every Rule Definition Version requires:

- positive PASS or NO_OBSERVATION;
- negative FAIL or OBSERVATION;
- threshold and valid-empty-population boundaries;
- malformed/unavailable evidence behavior;
- expected scope count and stable keys;
- evidence/source references;
- replay projection; and
- mutation sensitivity.

Critical financial branches and authorization/separation paths require complete branch coverage. Repository-wide thresholds remain binding; a numeric coverage target never substitutes for the required scenario matrix.

## 11. Migration, compatibility, and rollback

- Existing migrations 0001–0003 remain unchanged; new migrations are forward-only, transactional, checksummed, and fault-tested.
- Fresh V2 installation creates external registry genesis, protected committed/pending head, signing/token profile, and `STORE_LINEAGE` before the first SQLCipher store. Replacement recovery instead anchors a local segment to the verified managed-root capsule hash/sequence/tail and appends `RECOVERY_ADOPTION`; it never creates a replacement genesis.
- Legacy cutover inventories trustworthy catalog/tombstone/object evidence and appends an attestation; pre-registry packages are `Legacy — unmanaged`, migration-quarantine-only, and must be re-backed up under the registry before production activation.
- Registry-format migration is append-only and independently attested. Binary/schema rollback never lowers the external head; an incompatible older binary enters recovery-only mode.
- Native analytical-state migration preserves exact adjacency; a legacy generation receives one `LEGACY_SNAPSHOT` event only for its recorded state, with no fabricated transitions/actor/time.
- Existing V1 records remain readable as explicitly labeled legacy history; V2 never fabricates Rule Results or missing provenance.
- A V1 review becomes V2 only through compatible retained sources, reconstruction, confirmation, a new Review Version, and one V2 Validation Run.
- Existing root rule catalog entries remain preserved and inactive unless each passes governed migration.
- `SLV-001` is the only initial layout; another layout requires a new versioned reader contract.
- Normal production startup never opens plaintext after encrypted-open failure.
- Schema downgrade is unsupported; failed upgrade restores the verified recovery point and prior executable only when that executable supports the already accepted registry format/head.
- Every workflow leaves the application in a releasable migration state; rollback means binary rollback with compatible schema or verified restore, never destructive schema rewriting.

## 12. Security, privacy, and support controls

- Treat workbooks, rule definitions, paths, manifests, backup bundles, AI output, and destinations as untrusted input.
- Prevent archive/XML/formula abuse, traversal, symlink/junction surprise, device paths, TOCTOU replacement, executable definitions, and dependency tampering.
- Keep temporary storage ACL-restricted, operation-scoped, encrypted when disk spooling is unavoidable, and synchronously lifecycle-cleaned.
- Refuse plaintext production storage, invalid keys/ACLs, unresolved identity, stale/tampered role manifests, unapproved providers, missing external-AI consent, and disposed-scope restore.
- Use one network egress adapter; no telemetry or update path carries user data.
- Keep diagnostics to correlation IDs, versions, codes, counts, duration buckets, and remedies—never workbook values, people/vendor names, raw paths, prompts, responses, credentials, or decrypted artifacts.
- Recheck authorization and different-person constraints at commit.
- Keep source files read-only and fingerprint-verified.
- Keep whole-scope disposal distinct from edit, archive, uninstall, and ordinary retention.

Support bundles are allowlist-generated and contain application/build/schema versions, dependency/SBOM hash, sanitized diagnostics, migration state, and invariant checks. Sensitive-value scans run in workflow verification and release qualification.

## 13. Requirements coverage by workflow

| Workflow | Primary V2 coverage |
|---|---|
| Review Management | FR-123–FR-125, FR-171–FR-173, FR-189–FR-190, FR-195–FR-197; NFR-082, NFR-085, NFR-089–NFR-092, NFR-102, NFR-107–NFR-109 |
| Upload & Extraction | FR-126–FR-137, FR-175, FR-180–FR-183, FR-191–FR-192; NFR-081, NFR-086–NFR-088, NFR-093–NFR-096, NFR-105–NFR-106, NFR-109–NFR-110 |
| Extraction Review | FR-138–FR-140, FR-171–FR-173, FR-191–FR-196, FR-203; NFR-082–NFR-083, NFR-091–NFR-093, NFR-101–NFR-102, NFR-110 |
| Validation Engine | FR-141–FR-164, FR-174, FR-184, FR-198–FR-199, FR-202–FR-203; NFR-081–NFR-085, NFR-089–NFR-091, NFR-097–NFR-099 |
| Results & Analytics | FR-157–FR-170, FR-185–FR-188, FR-193, FR-197, FR-202; NFR-082–NFR-083, NFR-091–NFR-093, NFR-098, NFR-102–NFR-103, NFR-106 |
| Ask Fin | FR-165, FR-168–FR-170, FR-193–FR-194, FR-200 plus root FR-091–FR-100; NFR-086, NFR-100, NFR-103–NFR-104, NFR-106 plus root NFR-011, NFR-013–NFR-016 |
| Reports & Review History | FR-165–FR-173, FR-185–FR-197, FR-200–FR-203; NFR-088, NFR-091–NFR-093, NFR-100–NFR-106, NFR-109–NFR-110 |
| Windows Packaging and Release | FR-175–FR-179; NFR-081, NFR-086–NFR-088, NFR-094–NFR-096, NFR-100–NFR-101, NFR-105–NFR-106 |

The implementation traceability matrix must include inherited root requirements and ADRs in addition to this primary V2 routing.

## 14. Documentation deliverables

- Reviewer guided-workflow and three-value editing guide;
- Rule Administrator rule schema/test/lifecycle/binding guide;
- Financial Control Approver request/decision/baseline-upgrade guide;
- administrator install, signed-role-manifest, signing, backup, restore, disposal, upgrade, and uninstall guide;
- source-layout/resource-limit and error-catalog reference;
- rule schema/evaluator and deterministic-result contract reference;
- data dictionary, audit-event catalog, migration/recovery runbook, and support guide;
- Ask Fin provider/consent/masking/context/citation/privacy guide;
- Windows support matrix, SBOM/provenance, and release notes; and
- requirement-to-code-to-test traceability plus final verification reports.

## 15. Risks and controls

| Risk | Control |
|---|---|
| Workflow delivery drifts back to layer- or screen-based work | Strict workflow order and Common Definition of Workflow Done |
| V1 conveniences leak into V2 truth | Explicit supersession list, architecture fitness tests, source golden fixtures |
| SQLCipher/PyInstaller/WiX incompatibility | Early time-boxed qualification inside Workflow 1; material failure returns through Architecture change control |
| Complete ledger size harms performance | Indexed result schema, bounded transaction, virtualized queries, 10,000-line benchmark |
| Configurable rules become code execution | Closed schemas, allowlists, trusted registry, injection suite |
| Two-person control is cosmetic | Stable Actor IDs, signed roles, commit-time different-person denial |
| Published results are silently replaced | Separate working/published pointers, atomic promotion, published-default queries |
| Backup resurrects disposed content | External recovery-control lifecycle, `STORE_LINEAGE`/scope-token admission, current signed capsule, provider-envelope reconciliation, and database catalogs/tombstones treated only as evidence |
| Ask Fin leaks or creates financial truth | Approved profile, explicit external consent, one egress chokepoint, minimal corpus, Claim verification, no command ports |
| Accessibility degrades in dense grids | Accessible Qt model/view contracts and verification in every workflow |
| Documentation consumes cycles without changing quality | Batch stage artifacts/reviews and defer editorial-only findings that do not affect behavior |

## 16. Architecture approval effect

Approval of the complete Architecture package:

- accepts the application, engine, persistence, UX/UI, security, identity, AI, backup, Windows, and ADR decisions;
- accepts this strict seven-workflow delivery sequence and five stage gates;
- authorizes implementation to begin with Workflow 1; and
- does not authorize release, protected-rule changes outside the governed workflow, use of real confidential test data, or bypass of workflow-independent verification.

Any later change that alters a requirement outcome, deterministic rule semantics, protected authority, encryption/egress boundary, authoritative persistence, or stage-gate contract returns to the appropriate SDD change-control stage. Ordinary implementation detail within the approved architecture does not reopen Architecture.
