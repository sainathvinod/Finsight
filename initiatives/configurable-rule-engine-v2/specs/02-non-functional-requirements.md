# 02 — Non-Functional Requirements: FinSight Configurable Rule Engine V2

- **Purpose:** Define the V2 quality constraints added to or made more specific than the existing approved FinSight NFRs. This is a delta register for the same product.
- **Sources:** HD-01–HD-27; WF-01–WF-11; AR-01–AR-04; the human-approved Product Owner brief; the governed V2 delta record; existing approved FinSight NFR-001–NFR-080; parent FinSight Constitution.
- **Status legend:** Draft → Approved → Baselined → Implemented → Verified. Implementation may start only after row-level approval and baselining.
- **ID policy:** Root FinSight currently uses NFR-001 through NFR-080. This delta continues the same stable namespace at NFR-081.
- **Scope boundary:** Every item below is `Draft` pending the independent Requirements review. Architecture-specific profiles named below must be approved before implementation but do not reopen the Requirements business contract.

## Requirements

### NFR-081 — V2 validation performance envelope
- **Statement (EARS):** WHILE processing the approved compatible single-department Budget/GED benchmark with the five protected core rules active, THE SYSTEM SHALL make the completed Review Summary available within 2 minutes on the root NFR-001 target hardware.
- **Category:** Performance & responsiveness
- **Rationale:** The configurable engine must preserve the existing monthly-review turnaround promise before optional-rule scale is added; interactive responsiveness and non-blocking long-operation behavior remain separately governed by root NFR-002 and NFR-003.
- **Source:** stakeholder-approved root NFR-001; HD-02, HD-12; AR-04.
- **Priority:** Must
- **Dependencies:** Approved root NFR-001 target hardware and 10,000-GED-line workload; Architecture-approved benchmark fixture and workbook-complexity profile; root NFR-002 and NFR-003 remain independent release checks.
- **Fit criterion (measurable):** On an 8–16 GB target corporate laptop, the approved fixture contains no more than 10,000 GED detail lines, one compatible Budget report, and no optional rules. A scripted Reviewer selects the fixture, confirms the unchanged extracted data as soon as confirmation is enabled, and starts validation as soon as that action is enabled. One monotonic wall-clock timer starts when FinSight accepts both files for ingestion and stops only when the completed Rule Result ledger and Rule Executions are persisted and the Review Summary is render-ready. The measured interval is no more than 120,000 milliseconds.
- **Acceptance criteria:**
  - Given the approved benchmark fixture and target hardware, When the scripted procedure runs, Then the measured ingest-to-Review-Summary interval is no more than 120,000 milliseconds.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-082 — Atomic rule and result persistence
- **Statement (EARS):** IF interruption occurs during rule-version creation, protected activation, workspace binding, ReviewGeneration creation, validation completion, Rule Result persistence, Rule Execution persistence, or generation promotion/supersession, THEN THE SYSTEM SHALL recover to either the prior consistent state or one complete successor state.
- **Category:** Reliability & data safety
- **Rationale:** Partial rule versions or mixed-version results would make a financial review unreproducible.
- **Source:** stakeholder (HD-04; Product Owner P-04); extends root NFR-005 and NFR-057.
- **Priority:** Must
- **Dependencies:** FR-144, FR-145, FR-149, FR-153; persistence boundaries defined in architecture later.
- **Fit criterion (measurable):** Fault injection at every declared persistence boundary produces zero partially activated rule versions, zero partial Protected Baseline Versions, zero partial workspace Rule Set Versions, zero partial ReviewGenerations, zero mixed-version runs, zero falsely complete Rule Result ledgers, zero inconsistent Rule Execution counts, zero orphan Findings, and zero half-moved published pointers; restart exposes the prior state or one complete successor with its predecessor, creation reason, verification basis, one-run relationship, publication state, and supersession record reconciled.
- **Acceptance criteria:**
  - Given fault injection at each boundary, When the application restarts, Then the consistency assertions in the fit criterion all pass.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-083 — No false pass from unavailable evidence
- **Statement (EARS):** IF a rule-and-scope pair cannot evaluate because required evidence is missing, invalid, unmapped, or scope-inconsistent, THEN THE SYSTEM SHALL record NOT_EVALUATED rather than PASS.
- **Category:** Reliability & data safety
- **Rationale:** Lack of evidence is not proof that a control passed.
- **Source:** stakeholder (HD-05, HD-09, HD-10; WF-07, WF-08); extends root NFR-062.
- **Priority:** Must
- **Dependencies:** FR-155, FR-164; per-rule dependency maps.
- **Fit criterion (measurable):** Across the approved dependency-failure fixture matrix, dependent rules produce zero PASS outcomes, 100% identify the failed dependency, and zero downstream views present those controls as satisfied.
- **Acceptance criteria:**
  - Given each approved missing/invalid/unmapped/mismatched fixture, When validation completes, Then all three fit-criterion assertions pass.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-084 — Non-executable rule definitions
- **Statement (EARS):** IF a configurable rule contains user-provided Python, SQL, scripts, macros, system commands, or unrestricted expressions, THEN THE SYSTEM SHALL reject the definition before testing or activation.
- **Category:** Security
- **Rationale:** Business configurability must not become arbitrary code execution.
- **Source:** stakeholder-approved Product Owner P-06; HD-02, HD-03; AR-02.
- **Priority:** Must
- **Dependencies:** FR-147; controlled rule model in functional requirements §2.11.
- **Fit criterion (measurable):** The security suite submits every prohibited construct through every supported create/import/edit/test/activate path; 100% are rejected, zero execute, and zero produce a partially persisted active definition.
- **Acceptance criteria:**
  - Given each prohibited construct/path pair, When attempted, Then all fit-criterion assertions pass.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-085 — Least-privilege protection of core rules
- **Statement (EARS):** WHEN an actor uses an ordinary rule-management action against a Core Mandatory rule, THE SYSTEM SHALL deny modification, disablement, deletion, replacement, and bypass.
- **Category:** Security
- **Rationale:** Mandatory controls must be protected from routine or accidental mutation.
- **Source:** stakeholder (HD-04, HD-11); extends root FR-106 and NFR-019.
- **Priority:** Must
- **Dependencies:** MVP role and identity policy in functional requirements §2.8; protected baseline governance §2.12; FR-143, FR-144.
- **Fit criterion (measurable):** Authorization tests cover every supported ordinary mutation path and deny 100% of them without changing the protected version or workspace binding; governed administrative paths require every human-approved authorization element.
- **Acceptance criteria:**
  - Given each ordinary user role and mutation path, When the mutation is attempted, Then the request is denied and the baseline state is byte-identical.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-086 — Approved processing boundary
- **Statement (EARS):** WHILE processing financial source data, Working Dataset values, Rule Results, Findings, prompts, or responses, THE SYSTEM SHALL route that content only within the local application or an explicitly approved private environment.
- **Category:** Security
- **Rationale:** The V2 source explicitly requires no public-model exposure for financial information.
- **Source:** stakeholder (AR-02; attached project request lines 385–410 and 583–603); HD-18.
- **Priority:** Must
- **Dependencies:** Architecture-approved on-device or organization-private provider/egress profile; root NFR-009–NFR-016.
- **Fit criterion (measurable):** Deny-by-default proxy capture across deterministic and AI workflows observes zero outbound destinations outside the approved allowlist and zero financial payloads transmitted to a public model.
- **Acceptance criteria:**
  - Given every supported workflow with network observation enabled, When the workflow completes, Then the fit criterion reports zero violations.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-087 — Workbook resource-exhaustion limits
- **Statement (EARS):** IF an uploaded workbook exceeds any approved byte, decompressed-content, worksheet, row, column, formula/merge-complexity, or processing-duration limit, THEN THE SYSTEM SHALL block its processing before any partial review persistence.
- **Category:** Security
- **Rationale:** Hostile or accidental workbook complexity must not exhaust resources or corrupt the review.
- **Source:** stakeholder (AR-02, AR-04); extends root NFR-012 and NFR-064.
- **Priority:** Must
- **Dependencies:** Architecture-approved workbook byte, decompression, dimension, formula/merge-complexity, and processing-duration limits; inherited NFR-001 workload; NFR-106 for the diagnostic identity, detected cause, and permitted remedy.
- **Fit criterion (measurable):** For each limit in the approved Architecture resource profile, an otherwise compatible fixture exactly at that limit is accepted for compatibility evaluation, while the corresponding fixture exceeding that limit by one unit is rejected before any ReviewCycle, Working Candidate, Review Version, source-binding, extraction-audit, or correction-basis record is persisted. Every limit-plus-one case produces zero crash, and its surfaced diagnostic satisfies NFR-106.
- **Acceptance criteria:**
  - Given an otherwise compatible fixture exactly at each approved limit, When ingestion runs, Then the fixture proceeds to compatibility evaluation.
  - Given the paired fixture exceeds that limit by one unit, When ingestion runs, Then processing is rejected with zero crash, zero partial review records, and an NFR-106-compliant diagnostic.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-088 — Protected temporary-data lifecycle
- **Statement (EARS):** WHILE temporary source copies, extraction intermediates, generated previews, or artifacts from canceled or superseded processing exist, THE SYSTEM SHALL protect them to the root NFR-009 confidentiality level required for retained financial data.
- **Category:** Privacy & consent
- **Rationale:** Temporary files can expose the same sensitive information as the retained review.
- **Source:** stakeholder (AR-02); extends root NFR-009, NFR-017, and NFR-056.
- **Priority:** Must
- **Dependencies:** Approved storage-protection policy; security architecture later.
- **Fit criterion (measurable):** During successful processing, cancellation, failed import, and crash/restart recovery, an approved disk/permission scan finds zero temporary financial artifacts outside approved protected storage and zero artifacts with weaker access controls than retained review data.
- **Acceptance criteria:**
  - Given each lifecycle scenario while temporary data exists, When storage protection is scanned, Then both zero-count assertions pass.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-089 — Immutable used rule versions
- **Statement (EARS):** WHEN a completed validation run references a rule version, THE SYSTEM SHALL prevent ordinary mutation or direct object-level physical deletion of that version.
- **Category:** Auditability & provenance
- **Rationale:** Past results must retain the exact policy that produced them.
- **Source:** stakeholder (HD-04, HD-11; Product Owner P-04); extends root NFR-021 and NFR-022.
- **Priority:** Must
- **Dependencies:** FR-144, FR-149, FR-171; governed whole-scope disposal under FR-201 and NFR-102.

An ordinary or direct rule-version deletion is a rule-library lifecycle action aimed at that version. It excludes the separately initiated, explicitly confirmed FR-201/NFR-102 whole-scope disposal workflow. A review- or period-scoped disposal cannot remove a shared rule version while any retained run outside the selected scope references it; an all-data disposal may remove it with the rest of the complete selected scope and retain only the permitted content-free tombstone.

- **Fit criterion (measurable):** A completed-run fixture references one Core Mandatory, one Optional Configurable, and one Informational/Advisory rule version. Every supported definition, configuration, status, binding, and persistence mutation path and every direct object-level physical-deletion path is attempted against each used version; 100% are denied and the retained content hashes remain unchanged. After successors activate, replay of every retained completed fixture run resolves each original definition, configuration, classification, and binding and reproduces an identical ordered [functional requirements §2.6](01-functional-requirements.md#26-deterministic-comparison-projection) projection with zero changed business-result fields. Separate FR-201/NFR-102 fixtures prove that a review/period disposal retains a shared used version while any out-of-scope run references it, and that confirmed all-data disposal removes the complete local scope without leaving a partial rule object.
- **Acceptance criteria:**
  - Given a completed run has used a version from each rule classification, When every ordinary mutation and direct object-level deletion path is attempted, Then every attempt is denied and each used version's content hash is unchanged.
  - Given successors for those versions become active, When every completed fixture run is replayed, Then the original versions resolve and the functional-requirements §2.6 projection is identical while new run/audit metadata remains separately retained.
  - Given a confirmed review- or period-scoped FR-201 disposal and an out-of-scope retained run references the same rule version, When disposal completes, Then the shared version remains resolvable for the out-of-scope run while disposed review content does not.
  - Given confirmed all-data disposal, When it completes under FR-201/NFR-102, Then the complete local rule-version scope is absent and only the permitted content-free tombstone remains.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-090 — Protected-rule change provenance
- **Statement (EARS):** WHEN a protected-rule request submission, terminal decision, effective activation, existing-workspace baseline upgrade, or denied protected-rule attempt occurs, THE SYSTEM SHALL append exactly one immutable audit event using the applicable event schema below.
- **Category:** Auditability & provenance
- **Rationale:** Governance must show who changed a mandatory control, why, and exactly what changed.
- **Source:** stakeholder (HD-04; Product Owner §5.1); extends root NFR-019–NFR-022.
- **Priority:** Must
- **Dependencies:** FR-144; functional requirements §2.8 and §2.12.

Every event contains an Event ID, event type, event timestamp, stable Actor ID of the person or system performing that transition or attempt, requested action, protected Rule ID or protected Rule ID set, outcome, and reason. The following matrix defines the remaining required fields and fields that carry the literal `N/A`; an empty value never substitutes for `N/A`.

| Event schema | Required fields in addition to the common fields | Fields recorded as explicit `N/A` |
|---|---|---|
| Request submitted | Request ID; requester stable Actor ID and request timestamp; before definition/configuration/binding and old Rule Version; proposed after definition/configuration/binding and proposed successor Rule Version; proposed effective time | Approver Actor ID; decision timestamp and decision reason; activation timestamp; prior and resulting Protected Baseline Version; activation outcome |
| Terminal decision — approved or rejected | Request ID; requester stable Actor ID and request timestamp; approver stable Actor ID; decision timestamp and decision reason; before definition/configuration/binding and old Rule Version; proposed after definition/configuration/binding and proposed successor Rule Version; proposed effective time; decision outcome | Activation timestamp; prior and resulting Protected Baseline Version; activation outcome |
| Effective activation | Request ID; requester stable Actor ID and request timestamp; approver stable Actor ID; approval timestamp and approval reason; before and activated after definition/configuration/binding; old and new Rule Version; approved effective time; activation timestamp; prior and resulting Protected Baseline Version; activation outcome | None |
| Existing-workspace baseline upgrade | Workspace ID; protected Rule ID set; target Protected Baseline Version; prior and resulting workspace Rule Set Version; requester Actor ID/time; authorizing Financial Control Approver Actor ID/time; activation timestamp; activation outcome | Before/after Rule Definition when definitions are unchanged; proposed successor Rule Version |
| Denied attempt outside a governed transition | attempted target definition/configuration/binding and old Rule Version; supplied proposed after definition/configuration/binding when present | Request ID when no request exists; requester Actor ID and request timestamp; approver Actor ID; decision timestamp and decision reason; proposed after definition/configuration/binding when none was supplied; proposed successor Rule Version; proposed effective time; activation timestamp; prior and resulting Protected Baseline Version; activation outcome |

A rejected request ends with its terminal-decision event and has no activation event. An approved request has one request event, one approved-decision event, and one activation event if and when its effective transition occurs.

- **Fit criterion (measurable):** For every protected action in functional requirements §2.12, the suite exercises request submission, approval, rejection, effective global activation, existing-workspace baseline upgrade, and denied ordinary attempt outcomes. Event reconciliation finds exactly one event at every exercised transition or attempt, zero missing/blank schema fields, explicit `N/A` in every field designated by the matrix, zero extra activation events for rejected requests, zero unintended workspace Rule Set Version changes, and zero mutable events; root NFR-020 mutation testing detects every attempted alteration.
- **Acceptance criteria:**
  - Given an approved request reaches activation, When its audit is reconciled, Then exactly one request event, one approved-decision event, and one activation event satisfy their schemas.
  - Given a request is rejected, When its audit is reconciled, Then exactly one request event and one rejected-decision event satisfy their schemas and no activation event exists.
  - Given an existing workspace upgrade is authorized, When its audit is reconciled, Then exactly one upgrade event identifies the workspace, target Protected Baseline Version, prior/resulting Rule Set Versions, requester, distinct authorizer, timestamps, and outcome while all other workspace manifests remain unchanged.
  - Given a protected action is denied outside a governed transition, When its audit is reconciled, Then exactly one denied-attempt event satisfies its schema.
  - Given any protected-rule audit event, When alteration is attempted, Then root NFR-020 detects the mutation and the retained event remains unchanged.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-091 — End-to-end validation lineage
- **Statement (EARS):** WHEN a validation-derived dashboard item, KPI, analytic, report value, export value, summary statement, or AI explanation is displayed, THE SYSTEM SHALL expose lineage to its Review Version/ReviewGeneration, publication state, Validation Run, persisted Rule Execution, Rule Result, and immutable rule version.
- **Category:** Auditability & provenance
- **Rationale:** Every validation conclusion must be reproducible from the engine's source-of-truth record.
- **Source:** stakeholder (HD-05, HD-11; Product Owner P-01); extends root NFR-019 and NFR-021–NFR-023.
- **Priority:** Must
- **Dependencies:** FR-154, FR-165–FR-168.
- **Fit criterion (measurable):** A lineage test traverses every V2 validation consumer to a stored Review ID/version/generation, working/published/historical state, Run ID, Rule Execution ID, Result ID, Rule Version ID, verified/input fingerprints, reconstruction basis, and source evidence; static/architecture conformance tests detect zero independent financial-validation calculations in consumers and zero mixed-generation consumers.
- **Acceptance criteria:**
  - Given every validation-derived consumer type, When its lineage is traversed, Then every required identifier/evidence link resolves and the independent-calculation count is zero.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-092 — Accessibility coverage for V2 surfaces
- **Statement (EARS):** WHEN a V2 user-facing surface is added or changed, THE DELIVERY PROCESS SHALL include that surface in the approved accessibility verification matrix.
- **Category:** Accessibility
- **Rationale:** Metadata resolution, rule governance, and complete rule results must be as accessible as the existing workflow.
- **Source:** stakeholder (HD-15; AR-04); extends root NFR-024–NFR-027, NFR-065, and parent Constitution P-13.
- **Priority:** Must
- **Dependencies:** Approved UX/UI specifications in a later stage.
- **Fit criterion (measurable):** Every V2 surface has recorded pass/fail evidence for applicable WCAG 2.2 AA, keyboard-only operation, accessible names, color-independent meaning, OS display modes, 200% text scaling, and responsive layout; the matrix contains zero omitted V2 surfaces.
- **Acceptance criteria:**
  - Given the release surface inventory, When accessibility evidence is reconciled, Then every surface has all applicable results and the omission count is zero.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-093 — Evidence-first rule explainability
- **Statement (EARS):** WHEN a user views a persisted rule outcome or Finding, THE SYSTEM SHALL provide access within one interaction to the governing rule classification and version, applicable calculation/evaluation or blocking dependency, inputs, and source rows/cells.
- **Category:** Usability & explainability
- **Rationale:** Trust requires one-step access to why each control produced its outcome.
- **Source:** stakeholder (HD-11; WF-08); extends root NFR-067.
- **Priority:** Must
- **Dependencies:** FR-154, FR-156, FR-157; UX design later.
- **Fit criterion (measurable):** A scripted matrix covers Core Mandatory and Optional Configurable results in PASS, FAIL, and NOT_EVALUATED states, plus Informational/Advisory results in OBSERVATION, NO_OBSERVATION, and NOT_EVALUATED states. It also covers one Finding linked to each applicable failing control result. From every displayed outcome or Finding, the walkthrough reaches all applicable governing-version, evaluation/dependency, input, and source-row/cell evidence with one user interaction in 100% of cases.
- **Acceptance criteria:**
  - Given each classification/status combination in the fit-criterion matrix, When its displayed outcome is selected once, Then every applicable evidence element is available.
  - Given a Finding for a failed Core Mandatory or Optional Configurable result, When the Finding is selected once, Then the linked rule version, calculation/evaluation, inputs, and source rows/cells are available.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-094 — Windows installer qualification
- **Statement (EARS):** WHEN a V2 Windows release is qualified, THE RELEASE PROCESS SHALL verify install, first launch, core offline workflow, upgrade, retained-user-data behavior, uninstall, and post-uninstall state on each approved target environment.
- **Category:** Portability & platform parity
- **Rationale:** The Windows deliverable must work on authorized users' clean machines, not only development systems.
- **Source:** stakeholder (HD-18; AR-03, AR-04); extends root NFR-028–NFR-030.
- **Priority:** Must
- **Dependencies:** Architecture/release-approved Windows environment matrix; functional requirements §2.13; FR-175–FR-177.
- **Fit criterion (measurable):** On every OS/version/permission profile in the approved release matrix, a clean standard-user machine passes every listed lifecycle test with the released package and no developer runtime; upgrade retains all user data and default uninstall retains it.
- **Acceptance criteria:**
  - Given the approved environment matrix, When release qualification completes, Then every environment/test pair has a passing evidence record.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-095 — Signed-package integrity and release provenance
- **Statement (EARS):** WHEN a distributable package is verified, THE RELEASE PROCESS SHALL prove its approved signature, checksum, exact source commit, dependency/build manifest, application version, and release-note identity.
- **Category:** Portability & platform parity
- **Rationale:** Authorized users must be able to verify what they are installing and detect tampering.
- **Source:** stakeholder (HD-18; AR-03); extends root NFR-079.
- **Priority:** Must
- **Dependencies:** Architecture/release-approved package-signing and timestamp profile; FR-178.
- **Fit criterion (measurable):** The release verifier resolves every defined provenance field for the package, accepts the approved signature/checksum, and rejects a package changed by one byte.
- **Acceptance criteria:**
  - Given an authentic package and a one-byte-mutated copy, When verified, Then the authentic package passes and the mutated package fails.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-096 — Department- and period-neutral implementation
- **Statement (EARS):** WHEN compatible reports contain any valid department identity and reporting period, THE SYSTEM SHALL derive identity and period behavior from source/workspace evidence rather than sample constants.
- **Category:** Extensibility & configurability
- **Rationale:** Application Engineering and May 2026 are fixture values, not product configuration.
- **Source:** stakeholder (HD-12–HD-14; Product Owner P-07/P-08).
- **Priority:** Must
- **Dependencies:** FR-129–FR-135; approved normalization policies.
- **Fit criterion (measurable):** A parameterized fixture suite changes only compatible department identity and review-period evidence; the same rule versions produce the same ordered behavior with only identity/evidence values changing, and an approved code/config scan finds zero sample identifier used as business logic.
- **Acceptance criteria:**
  - Given at least two non-sample compatible department/period fixtures, When the suite runs, Then all behavioral-equivalence and scan assertions pass.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-097 — Controlled rule extension without source-code change
- **Statement (EARS):** WHERE a controlled rule type is approved for V2, THE SYSTEM SHALL permit its approved Optional Configurable rule lifecycle through supported product interfaces without changing executable application source.
- **Category:** Extensibility & configurability
- **Rationale:** Adding rule 6, 20, or 100 must be an ordinary governed extension rather than an application redesign.
- **Source:** stakeholder (HD-02, HD-03; AR-01); extends root NFR-039–NFR-045.
- **Priority:** Must
- **Dependencies:** Functional requirements §2.8 and §2.11; FR-145, FR-147, FR-148.
- **Fit criterion (measurable):** One conformance rule of every approved type completes the full lifecycle through supported product interfaces with zero executable-application-source diff; invalid definitions are rejected without partial activation.
- **Acceptance criteria:**
  - Given each approved rule type, When its conformance rule completes the lifecycle, Then the source-diff count is zero and every lifecycle assertion passes.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-098 — Common engine contract across classifications
- **Statement (EARS):** WHEN any rule classification executes, THE SYSTEM SHALL use the same versioning, evaluator, run lifecycle, Rule Execution, Rule Result, evidence, persistence, and audit contracts.
- **Category:** Extensibility & configurability
- **Rationale:** Classification may change governance behavior but cannot create parallel sources of financial truth.
- **Source:** stakeholder (HD-03; Product Owner P-03).
- **Priority:** Must
- **Dependencies:** FR-141, FR-142, FR-153, FR-154.
- **Fit criterion (measurable):** A conformance suite executes one approved rule of each classification through the same engine interfaces and reports zero classification-specific financial-calculation paths; only approved lifecycle/status/reporting policy varies.
- **Acceptance criteria:**
  - Given one rule per classification, When the conformance suite runs, Then every common-contract assertion passes and the parallel-calculation-path count is zero.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-099 — Complete V2 delivery traceability
- **Statement (EARS):** WHEN a V2 behavior or release artifact is proposed for shipment, THE DELIVERY PROCESS SHALL require traceability through business objective, requirement, epic, feature, acceptance criterion, architecture decision, source, test, review, and release evidence.
- **Category:** Maintainability & development process
- **Rationale:** Same-product evolution must remain auditable and must not strand approved or legacy rule behavior.
- **Source:** stakeholder (AR-04; attached project request traceability section); extends root NFR-033 and NFR-073–NFR-076.
- **Priority:** Must
- **Dependencies:** FR-174; later decomposition, architecture, plans, tasks, tests, and verification.

For this requirement, `source` means the exact version-controlled artifact and revision that realizes or governs the traced item—for example executable code, configuration, schema/migration, build definition, or the approved specification/disposition record. It never means an uploaded Budget/GED source file. `R` below means the link is required. `C` means an Architecture Decision Record is required when an architecture decision constrains the item; otherwise the trace contains explicit `N/A`, its rationale, and the approving reviewer.

| Shipped trace subject | Business objective | Requirement | Epic/feature | Acceptance criterion | Architecture decision | Source | Test | Review | Release evidence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V2 requirement | R | R | R | R | C | R | R | R | R |
| Existing-rule disposition | R | R | R | R | C | R | R | R | R |
| Implementation unit | R | R | R | R | R | R | R | R | R |
| Test or verification item | R | R | R | R | C | R | R | R | R |
| Release artifact | R | R | R | R | R | R | R | R | R |

- **Fit criterion (measurable):** The release traceability gate applies the matrix to every shipped V2 requirement, existing-rule disposition, implementation unit, test/verification item, and release artifact. It reports zero missing `R` links, zero conditional links lacking either an ADR or approved explicit `N/A`, zero unresolved identifiers/revisions, and zero trace subjects omitted from the inventory.
- **Acceptance criteria:**
  - Given a release candidate, When traceability is audited against the applicability matrix, Then all fit-criterion zero-count assertions pass.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-100 — Privacy-safe validation diagnostics
- **Statement (EARS):** WHEN FinSight emits a diagnostic log or support bundle, THE SYSTEM SHALL exclude workbook content, financial values, vendor/employee data, credentials, prompts, and retained AI responses.
- **Category:** Observability & diagnosability
- **Rationale:** Troubleshooting evidence must not become a second uncontrolled financial-data store.
- **Source:** stakeholder (AR-02); extends root NFR-053–NFR-055 and NFR-061–NFR-064.
- **Priority:** Must
- **Dependencies:** Approved sensitive-data taxonomy; Architecture/UX versioned error taxonomy.
- **Fit criterion (measurable):** Across a fault matrix covering intake, metadata resolution, rule loading/execution, persistence, export, and AI, seeded-sensitive-data scanning finds zero prohibited workbook values, financial values, vendor/employee data, credentials, prompts, or retained AI responses in logs and support bundles.
- **Acceptance criteria:**
  - Given every fault-matrix case with seeded prohibited values, When diagnostics are collected, Then the prohibited-value count is zero.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-101 — Complete governed backup and restore
- **Statement (EARS):** WHEN a V2 backup is created, THE SYSTEM SHALL include authoritative ReviewCycle/Working-Candidate metadata, source bindings/fingerprints, correction/confirmation and verification-basis records, ReviewGenerations, working/published pointers, promotion/supersession records, immutable rule/configuration versions, Protected Baseline Versions, workspace Rule Set Versions and bindings, runs, Rule Executions, Rule Results, Findings, every retained Derived Record and its Generation Event—including reports, spreadsheet-compatible exports, and policy-permitted Ask Fin interactions—authorization/audit history, and permitted AI history.
- **Category:** Data lifecycle & scale
- **Rationale:** Restoring only transaction data would leave historical validation unreproducible.
- **Source:** stakeholder (WF-11; AR-02); extends root NFR-060.
- **Priority:** Should
- **Dependencies:** Retention and AI-history policy; FR-149, FR-171.
- **Fit criterion (measurable):** With AI-history retention permitted for the fixture, the backup seed contains at least one record in every artifact class named in the Statement, a working/published divergence followed by promotion, at least two completed runs, one completed report, one completed spreadsheet-compatible export, one permitted completed Ask Fin Derived Record, one failed or blocked Generation Event with no content, and two append-only Derived Records created by regenerating the same artifact type. It contains no source workbook bytes, complete normalized-row store, complete Working Dataset, or complete `VerifiedDataset`. A pre-backup manifest records exact record counts; identifiers; content and source fingerprints; relationship edges; audit-event ordering; completed-run comparison projections; and, for every Derived Record and Generation Event, its ID, type, Review ID/version/generation, Validation Run ID, Rule Set Version, publication state, initiating Actor ID, request/completion timestamps, terminal status, content fingerprint, or explicit no-content state. Restore to a replacement machine matches every manifested count, identifier, fingerprint, content value, relationship, authorization/audit event, Generation Event, Derived Record, publication pointer, supersession edge, and permitted AI-history record; produces zero orphan references; preserves both regeneration records independently; and reproduces an identical [functional requirements §2.6](01-functional-requirements.md#26-deterministic-comparison-projection) projection for every completed run when matching sources are available. A missing-source restore proves authoritative results remain viewable while dataset reconstruction is unavailable. A policy-prohibited AI-history fixture retains only required non-content audit/Generation Event evidence and an explicit exclusion record. A separate disposed-scope fixture proves that an NFR-102/FR-201 tombstone prevents every FinSight-managed backup or recovery path from restoring the disposed content.
- **Acceptance criteria:**
  - Given the complete seeded authoritative record set, When the backup manifest is created, Then every artifact class named in the Statement is represented and the counts of source workbook bytes and complete normalized/Working/Verified row stores are zero.
  - Given the seeded completed report, completed export, permitted completed Ask Fin Derived Record, failed or blocked no-content Generation Event, and regenerated artifact pair, When the backup manifest is created, Then every retained Derived Record and Generation Event is independently manifested with every field required by the fit criterion.
  - Given that backup is restored to a replacement test machine, When the restored manifest is compared, Then exact counts, identifiers, fingerprints, content, relationships, audit ordering, terminal statuses, explicit no-content states, and permitted AI history match, the regenerated records remain distinct, the orphan count is zero, and every completed run has an identical functional-requirements §2.6 projection.
  - Given the restored machine lacks matching source bytes, When a Closed review opens, Then retained authoritative results remain viewable, reconstructed datasets are explicitly unavailable, and no verification or publication state changes.
  - Given policy prohibits Ask Fin response-content retention, When backup and restore complete, Then response content is absent while the required non-content audit and Generation Event evidence and explicit policy exclusion remain.
  - Given a scope was permanently disposed after an earlier FinSight-managed backup, When restore or recovery is attempted, Then the disposed content is not reintroduced and only its permitted content-free tombstone remains.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-102 — Closed-review immutability
- **Statement (EARS):** WHEN an ordinary in-place mutation of a `Closed` or `Archived` Review Version's authoritative source-binding, correction/confirmation, verification-basis, generation, run, result, finding, promotion/supersession, Derived Record, or audit record is requested, THE SYSTEM SHALL reject that mutation.
- **Category:** Data lifecycle & scale
- **Rationale:** Past reviews are evidence and must not be edited in place.
- **Source:** stakeholder (HD-04; WF-11); extends root NFR-005, NFR-006, NFR-021, and NFR-022; narrows its relationship to whole-scope disposal under root NFR-017.
- **Priority:** Must
- **Dependencies:** FR-171, FR-172; root NFR-017 confirmed data-disposal workflow.

`Ordinary in-place mutation` includes field editing, replacing retained content, object-level deletion, and partial removal from one authoritative record set. The complete normalized row store, Working Dataset, and `VerifiedDataset` are reconstructed and are not retained snapshot artifacts. A separately initiated, explicitly confirmed whole-scope disposal of a cycle, a period, or all data under root NFR-017 is not an ordinary mutation: it may dispose of the selected complete scope, including FinSight-managed backup/recovery copies, and leaves only the deletion audit evidence permitted by NFR-017, never a partially rewritten Closed or Archived record set.

- **Fit criterion (measurable):** Every supported ordinary mutation and partial-deletion attempt against each retained authoritative artifact class of a Closed and an Archived Review Version is rejected and leaves the authoritative-record manifest hash unchanged. In a separate root NFR-017 test, a whole-scope disposal request is blocked before confirmation; after explicit confirmation it removes exactly the selected complete cycle, period, or all-data scope from active storage and every FinSight-managed backup/recovery path, leaves zero residual or recoverable partial authoritative records, preserves only the permitted content-free deletion audit record, and does not affect data outside the selected scope.
- **Acceptance criteria:**
  - Given the Closed/Archived mutation matrix, When each action is attempted, Then every mutation is rejected and the original authoritative-record manifest hash is unchanged.
  - Given a whole-scope disposal request under root NFR-017 has not been confirmed, When disposal is attempted, Then no retained data changes.
  - Given that request is explicitly confirmed, When disposal completes, Then exactly the selected whole scope is absent, no partially rewritten authoritative record set remains, out-of-scope data is unchanged, and only the permitted content-free deletion audit evidence remains.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-103 — Engine-bound AI explanation
- **Statement (EARS):** WHEN the AI layer receives financial context, THE SYSTEM SHALL provide only recorded deterministic Rule Results and approved minimized evidence through a read-only explanation boundary.
- **Category:** AI governance
- **Rationale:** Ask Fin must remain a consumer of financial truth and cannot become another rule engine.
- **Source:** stakeholder (HD-05, HD-18; Product Owner P-01/P-02; WF-10); extends root NFR-037 and NFR-047–NFR-052.
- **Priority:** Must
- **Dependencies:** FR-165, FR-167–FR-170; approved AI processing boundary; Architecture-approved, versioned AI-context field and evidence allowlist.
- **Fit criterion (measurable):** A context-minimization fixture offers the AI boundary selected and unrelated Rule Results, raw source files, full Working Datasets, credentials, mutable object handles, approval capabilities, and write-capable tools. Captured AI context contains exactly the allowlisted fields from the selected recorded Rule Results and the minimum cited evidence rows/cells, with zero unrelated rows, prohibited fields, credentials, mutable handles, or non-allowlisted capabilities. Capability tests request create, update, delete, validation, approval, and financial actions through direct invocation, malicious prompts, and substituted/malformed providers; the boundary exposes zero write-capable operations and all deterministic-data, rule, result, approval, and audit content hashes remain unchanged. With AI disabled, unavailable, or substituted, the [functional requirements §2.6](01-functional-requirements.md#26-deterministic-comparison-projection) has zero changed business-result fields. Every retained financial explanation cites its selected Run ID, Result ID, Rule Version ID, and source evidence.
- **Acceptance criteria:**
  - Given a superset of selected, unrelated, and prohibited context, When AI context is assembled, Then its exact field/row set equals the approved allowlist and contains no mutable handle or write-capable operation.
  - Given every prohibited create, update, delete, validation, approval, or financial-action request, When it is attempted through the AI boundary, Then no write capability is available and every governed content hash is unchanged.
  - Given AI is disabled, unavailable, maliciously prompted, substituted, or returns malformed output, When deterministic regression and explanation tests run, Then the functional-requirements §2.6 projection has zero changed business-result fields and every retained financial explanation satisfies all citation fields.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-104 — Public-model transmission prohibition
- **Statement (EARS):** IF a requested AI operation targets a public model or a provider outside the approved private boundary, THEN THE SYSTEM SHALL block transmission of financial and review content.
- **Category:** AI governance
- **Rationale:** The V2 source explicitly requires no public-model exposure.
- **Source:** stakeholder (AR-02; attached project request lines 385–410 and 583–603); HD-18.
- **Priority:** Must
- **Dependencies:** Architecture-approved on-device or organization-private provider/egress profile; NFR-086, NFR-103.
- **Fit criterion (measurable):** Across every supported AI action and provider configuration, proxy capture records zero financial/review payload bytes transmitted to a public or unapproved endpoint, and every prohibited request returns a visible blocked status.
- **Acceptance criteria:**
  - Given each public/unapproved provider configuration, When an AI action is requested, Then transmission is blocked, zero payload bytes leave the boundary, and the user sees the blocked status.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-105 — Lifecycle-bound temporary-data disposal
- **Statement (EARS):** WHEN a temporary financial artifact reaches the end of its processing lifecycle, THE SYSTEM SHALL dispose of it before that lifecycle operation reports completion.
- **Category:** Privacy & consent
- **Rationale:** Protected temporary data must not persist indefinitely after it is no longer required.
- **Source:** stakeholder (AR-02); extends root NFR-017 and NFR-056; split from NFR-088 audit finding.
- **Priority:** Must
- **Dependencies:** Architecture-defined protected temporary locations and crash-recovery cleanup mechanism; ADR-014 retention boundary.
- **Fit criterion (measurable):** For successful completion, cancellation, failed import, and explicit removal, a disk scan before the operation reports completion finds zero lifecycle-ended temporary financial artifacts; after a crash, the same assertion passes during recovery before new review work is allowed.
- **Acceptance criteria:**
  - Given each lifecycle scenario, When completion or crash recovery is reported, Then the expired-artifact count is zero.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-106 — Actionable diagnostic identity
- **Statement (EARS):** WHEN FinSight reports a failed intake, metadata, rule, persistence, export, or AI operation, THE SYSTEM SHALL provide a stable correlation ID plus the detected cause and permitted user remedy.
- **Category:** Observability & diagnosability
- **Rationale:** Privacy-safe diagnostics must still let users and authorized support personnel identify and resolve a failure.
- **Source:** stakeholder (AR-02, AR-04); extends root NFR-053–NFR-055 and NFR-061–NFR-064; split from NFR-100 audit finding.
- **Priority:** Must
- **Dependencies:** Architecture/UX versioned error taxonomy completed before implementation verification.
- **Fit criterion (measurable):** Across the approved fault matrix for intake, metadata, rule loading/execution, persistence, export, and AI, 100% of surfaced failures contain one stable correlation ID, one cataloged cause, and at least one permitted remedy; repeated lookup by correlation ID resolves the same diagnostic event.
- **Acceptance criteria:**
  - Given every approved fault-matrix case, When the failure is surfaced and looked up, Then all required diagnostic fields exist and the repeated lookup resolves the same event.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-107 — Role-model extensibility
- **Statement (EARS):** WHERE an additional authorized role is introduced, THE SYSTEM SHALL represent its versioned permission mapping without changing deterministic rule definitions, evaluator behavior, or historical authorization evidence.
- **Category:** Extensibility & configurability
- **Rationale:** The three MVP roles must not become a hard-coded ceiling on future enterprise governance.
- **Source:** stakeholder (HD-21, HD-27).
- **Priority:** Must
- **Dependencies:** Functional requirements §2.8; authorization architecture.
- **Fit criterion (measurable):** An authorization conformance fixture adds one test role and maps only existing allowlisted permissions with zero deterministic-engine source or contract changes; prior Role Assignments and audit outcomes remain byte-identical.
- **Acceptance criteria:**
  - Given a newly configured role with a subset of existing permissions, When its authorized and prohibited action matrix runs, Then every permission decision matches the versioned mapping and the rule-engine contract is unchanged.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-108 — Replaceable identity-provider boundary
- **Statement (EARS):** WHERE an approved platform or enterprise authentication source replaces Windows-account authentication, THE SYSTEM SHALL map the authenticated subject to the canonical stable Actor ID contract without changing role policy, audit schemas, protected-rule governance, or deterministic rule-engine behavior.
- **Category:** Extensibility & configurability
- **Rationale:** A parent-required supported platform and later Azure AD, Active Directory, SSO, or another enterprise provider must be adoptable without redesigning the validation engine.
- **Source:** stakeholder (HD-23, HD-27).
- **Priority:** Must
- **Dependencies:** Functional requirements §2.8; identity architecture.
- **Fit criterion (measurable):** A provider-substitution conformance test supplies equivalent Windows, parent-required non-Windows platform, and enterprise identity assertions for the same authorization matrix; every permission and separation-of-duties outcome is identical, audit records retain the correct provider-qualified Actor ID, and the deterministic comparison projection changes in zero business-result fields.
- **Acceptance criteria:**
  - Given an approved substitute identity adapter, When the authorization and deterministic regression suites run, Then all identity, role, audit, separation-of-duties, and unchanged-business-result assertions pass.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-109 — Temporary-data disposal provenance
- **Statement (EARS):** WHEN a temporary financial artifact set is disposed, THE SYSTEM SHALL append one audit event identifying its artifact category, lifecycle trigger, disposal outcome, Actor ID or system actor, and timestamp without retaining the disposed financial content.
- **Category:** Auditability & provenance
- **Rationale:** Disposal must be provable without copying sensitive temporary content into the audit trail.
- **Source:** stakeholder (AR-02); extends root NFR-017, NFR-019, and NFR-053; split from NFR-105 for atomicity.
- **Priority:** Must
- **Dependencies:** NFR-100, NFR-105; Architecture-defined temporary artifact categories.
- **Fit criterion (measurable):** Across the NFR-105 lifecycle fixture matrix, the audit query returns exactly one complete disposal event per disposed artifact set, zero missing or duplicate events, and zero seeded financial-content values.
- **Acceptance criteria:**
  - Given each artifact set disposed under NFR-105, When disposal audit is reconciled, Then one event contains every defined field and no seeded financial content.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

### NFR-110 — Authoritative-only review persistence
- **Statement (EARS):** WHILE V2 review data is retained or backed up, THE SYSTEM SHALL persist authoritative source-binding/fingerprint, correction/confirmation, verification-basis, generation, run/result, promotion/supersession, Derived Record, authorization, and audit records without persisting source workbook bytes or complete normalized, Working Dataset, or `VerifiedDataset` row stores.
- **Category:** Data lifecycle & scale
- **Rationale:** The reviewed-copy experience must preserve the inherited ADR-011/ADR-012 reconstruction and trust model.
- **Source:** inherited ADR-011 and ADR-012; resolves independent Requirements cross-check blocker 1.
- **Priority:** Must
- **Dependencies:** FR-171, FR-172, FR-203; NFR-101, NFR-102.
- **Fit criterion (measurable):** After exercising initial confirmation, corrections/reversions, source reverification, extractor reverification, rule-set reanalysis, configuration reanalysis, exact replay, promotion, report/export generation, application restart, backup, and restore, a storage inventory finds every authoritative record class named in the Statement and zero source workbook byte copies, zero complete normalized-row stores, zero complete Working Dataset row stores, and zero complete `VerifiedDataset` row stores; fingerprint-verified reconstruction from matching sources still reproduces the expected values and §2.6 projection.
- **Acceptance criteria:**
  - Given the full lifecycle fixture, When active storage and a backup are inventoried, Then every prohibited complete byte/row-store count is zero and every required authoritative class is present.
  - Given matching source bytes remain available after restart or restore, When FR-203 reconstructs the dataset, Then its values, lineage, counts, and fingerprint match the pre-restart expectation.
  - Given matching source bytes are unavailable, When retained history opens, Then authoritative results remain viewable and reconstructed row data is explicitly unavailable.
- **Traces to:** TBD at `/sdd:decompose`
- **Status:** Draft

## Category coverage checklist

No category is waived. Existing root requirements remain in force; V2 items add the initiative-specific constraint.

| Category (nfr-catalog) | Addressed by | Waived — reason |
|---|---|---|
| Performance & responsiveness | Root NFR-001–NFR-004; NFR-081 | — |
| Reliability & data safety | Root NFR-005–NFR-008, NFR-057, NFR-062, NFR-064; NFR-082, NFR-083 | — |
| Security | Root NFR-009–NFR-013, NFR-018, NFR-030, NFR-079; NFR-084–NFR-087 | — |
| Privacy & consent | Root NFR-014–NFR-018; NFR-088, NFR-105 | — |
| Auditability & provenance | Root NFR-019–NFR-023, NFR-058; NFR-089–NFR-091, NFR-109 | — |
| Accessibility | Root NFR-024–NFR-027, NFR-065; NFR-092 | — |
| Usability & explainability | Root NFR-055, NFR-065–NFR-069; NFR-093 | — |
| Portability & platform parity | Root NFR-007, NFR-028–NFR-030, NFR-070; NFR-094, NFR-095 | — |
| Extensibility & configurability | Root NFR-039–NFR-046, NFR-072; NFR-096–NFR-098, NFR-107, NFR-108 | — |
| Maintainability & development process | Root NFR-031–NFR-038, NFR-073–NFR-080; NFR-099 | — |
| Observability & diagnosability | Root NFR-053–NFR-055, NFR-061–NFR-064; NFR-100, NFR-106 | — |
| Data lifecycle & scale | Root NFR-042, NFR-043, NFR-056–NFR-061, NFR-071, NFR-072; NFR-101, NFR-102, NFR-110 | — |
| AI governance | Root NFR-004, NFR-023, NFR-037, NFR-046–NFR-052, NFR-063; NFR-103, NFR-104 | — |

## Requirements clarification status

No open clarification blocks Requirements approval. Exact resource-limit values, Windows environments and signing mechanisms, storage/backup implementation, error taxonomy representation, and private AI adapter details are Architecture or release-profile decisions constrained by these NFRs.

## Clarifications log

The following resolutions close the NFR clarification register without inventing enterprise accounting policy or implementation technology.

| Date | Item(s) | Question | Resolution | Raised by | Answered by |
|---|---|---|---|---|---|
| 2026-07-27 | CQ-10 | Which MVP roles and actor identity govern privileged actions? | Apply functional requirements §2.8: Reviewer, Rule Administrator, and Financial Control Approver; stable Windows Actor ID for MVP; two different actors for protected request/approval; provider and role models remain replaceable/extensible under NFR-107/NFR-108. | Requirements clarification | Product stakeholder (HD-21–HD-23) |
| 2026-07-27 | CQ-11 | Which controlled rule types are permitted? | Apply functional requirements §2.11 and NFR-084/NFR-097: bounded deterministic presence/parse, key membership, exact duplicate, decimal comparison, grouped SUM/COUNT, and finite ALL/ANY composition only. | Requirements analysis | Product stakeholder direction (HD-02, HD-03, HD-27) |
| 2026-07-27 | CQ-22, CQ-23 | Which Windows lifecycle and release outcomes apply? | Upgrades retain all user data; uninstall retains by default and removes only by explicit confirmed choice. A signed, traceable package must qualify on clean standard-user environments; Architecture/release governance selects the exact matrix and signing/timestamp mechanisms. | Requirements analysis | Inherited Windows requirements and product direction |
| 2026-07-27 | CQ-25 | Which scale baseline applies? | Retain root NFR-001: no more than 10,000 GED lines on an 8–16 GB corporate laptop within two minutes. Architecture must approve safe workbook-complexity limits and optional-rule stress profiles before implementation. | Requirements analysis | Inherited approved root NFR-001 |
| 2026-07-27 | CQ-26 | Which AI boundary applies? | Only on-device or explicitly organization-approved private processing is permitted. Public/retail models are prohibited even with user consent; without an approved provider Ask Fin is unavailable and deterministic validation remains complete. | Requirements analysis | Product direction (HD-05, HD-18, HD-27) |
| 2026-07-27 | CQ-27 | Which retention boundary applies? | No automatic review expiry or deletion; archive is explicit and non-destructive; referenced rules, audit, and deterministic outputs remain replayable; Ask Fin history remains user-controlled; lifecycle-ended temporary artifacts are disposed under NFR-105. Root NFR-017 separately preserves an explicitly confirmed whole-cycle, period, or all-data disposal workflow under NFR-102/FR-201. Exact storage and recovery mechanisms belong to Architecture. | Requirements analysis | Inherited ADR-009, ADR-014, and NFR-017 |
