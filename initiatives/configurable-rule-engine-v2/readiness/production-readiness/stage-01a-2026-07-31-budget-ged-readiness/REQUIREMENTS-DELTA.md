# Stage 01A Requirements Delta

**Prepared:** 2026-07-31  
**Status:** Draft; not approved or baselined  
**ID continuity:** Follows candidate FR-218 and NFR-123; proposed additions end at FR-246 and NFR-132  
**Source:** Complete 1,073-line stakeholder directive dated 2026-07-31

## 1. Adoption rules

- These items are proposed changes to the working specification; they do not
  edit approved text in place.
- Existing requirements remain in force unless an approved item explicitly
  supersedes them.
- Items marked `Blocked` cannot be approved until their named S1A decision is
  recorded.
- June workbooks and oracles are verification artifacts (`FIX-JUN-001`,
  `ORACLE-JUN-001`, and `VER-MOM-001`), not production functional
  requirements.
- Product behavior remains department-neutral and Budget/GED-only.

## 2. Proposed functional requirements

### FR-219 — Versioned AI provider profiles

- **Statement (EARS):** WHEN an authorized actor saves an Ask Fin provider profile, THE SYSTEM SHALL create a versioned profile containing exactly one registered class from `Ollama`, `Azure OpenAI`, `Private OpenAI-Compatible`, `Private Anthropic-Compatible`, or `Deterministic-Only`, plus endpoint class, discovered or entered model identity where applicable, data-handling mode, credential reference, authorization reference, and enabled state; only the executable subset approved by S1A-D03 may be enabled.
- **Rationale:** Provider flexibility must be configurable without allowing arbitrary or unaudited data transmission.
- **Source:** Stakeholder directive §§11 and 24.
- **Priority:** Must.
- **Dependencies:** S1A-D03 and S1A-D04; successor provider-security ADR.
- **Acceptance:** Saving each approved profile produces a new immutable configuration version; unknown provider classes, missing policy fields, and plaintext credentials are rejected.
- **Status:** Draft — blocked by S1A-D03/D04.

### FR-220 — Provider connection test and safe reset

- **Statement (EARS):** WHEN a user tests or resets an Ask Fin provider profile, THE SYSTEM SHALL verify the configured endpoint and model under that profile's approved transport policy without transmitting review financial content and SHALL report the exact success or actionable failure state.
- **Rationale:** Configuration must be testable without using confidential workbook data as a connectivity probe.
- **Source:** Stakeholder directive §11.
- **Priority:** Must.
- **Dependencies:** FR-219.
- **Acceptance:** Connection tests contain no Budget/GED values; reset creates or selects the approved Ollama loopback default and never triggers cloud fallback.
- **Status:** Draft — blocked by S1A-D03/D04.

### FR-221 — Provider-independent financial truth

- **Statement (EARS):** WHEN the active Ask Fin provider profile changes, THE SYSTEM SHALL leave every recorded Budget total, GED total, Rule Result, Finding, severity, source-evidence record, Leadership Summary figure, comparison classification, and Overall Review Status unchanged.
- **Rationale:** An explanation provider cannot become a second financial engine.
- **Source:** Stakeholder directive §§1, 11, and final implementation principle.
- **Priority:** Must.
- **Dependencies:** FR-165, FR-167–FR-170, NFR-103.
- **Acceptance:** Repeating the same grounded question through every approved provider changes zero authoritative persisted financial/result fields.
- **Status:** Draft.

### FR-222 — Ask Fin conversation identity

- **Statement (EARS):** WHEN Ask Fin starts a review conversation, THE SYSTEM SHALL bind one Conversation ID to exactly one Review ID, Review Version, Validation Run ID, Provider Configuration Version, and conversation state.
- **Rationale:** Grounding and history must never cross reviews, runs, or provider policies.
- **Source:** Stakeholder directive §§12 and 24.
- **Priority:** Must.
- **Dependencies:** FR-167–FR-173, FR-194, FR-219.
- **Acceptance:** Attempts to attach one message or citation to a different review or run fail transactionally; the UI identifies the selected review/run context.
- **Status:** Draft.

### FR-223 — Submitted Ask Fin message persistence

- **Statement (EARS):** WHEN a user submits an Ask Fin message, THE SYSTEM SHALL append the immutable ordered user message and one `Pending` request-attempt record to its Conversation ID before invoking any provider.
- **Rationale:** A submitted question must survive a crash or provider failure rather than disappear.
- **Source:** Stakeholder directive §12.
- **Priority:** Must.
- **Dependencies:** S1A-D08; FR-222; NFR-126.
- **Acceptance:** Failure immediately before/during provider invocation leaves the submitted message and interrupted/pending state visible after restart; resubmission appends rather than overwrites.
- **Status:** Draft — blocked by S1A-D08.

### FR-224 — Conversation rollover across run or provider context

- **Statement (EARS):** WHEN a user opens Ask Fin for a different Validation Run or Provider Configuration Version, THE SYSTEM SHALL create or resume a distinct Conversation ID and SHALL prevent messages or citations from the previously selected context from entering that conversation.
- **Rationale:** Historical conversations are evidence, but stale run/provider context must not ground a new conversation.
- **Source:** Stakeholder directive §§6 and 12.
- **Priority:** Must.
- **Dependencies:** FR-173, FR-222, FR-223.
- **Acceptance:** A Working — Unpublished run has a separately labeled conversation; the published run/conversation remains the trusted default until promotion; promotion changes the default; historical conversations are read-only; a provider-version change creates a new conversation and no conversation mixes provider versions.
- **Status:** Draft.

### FR-225 — Durable committed review state

- **Statement (EARS):** WHEN FinSight restarts after a successful committed state transition, THE SYSTEM SHALL restore every retained review, lifecycle state, source identity, approved immutable normalized Budget/GED source-row snapshot and cell lineage, original/reviewed/current validation value, verification snapshot, rule scope/version, Validation Run, result, finding, evidence link, deterministic summary/comparison, preference, workflow position, audit event, and generated-artifact metadata required by the approved persistence profile, without requiring the original user-managed workbook path when S1A-D02 option B or C is approved.
- **Rationale:** Application memory cannot be the sole source of committed work.
- **Source:** Stakeholder directive §§3, 4, 6, 12, and 23.
- **Priority:** Must.
- **Dependencies:** S1A-D02 and S1A-D08; NFR-127; successor persistence ADR.
- **Acceptance:** The complete restart scenario in directive §27 reproduces each seeded retained value and relationship exactly, with zero orphan records.
- **Status:** Draft — blocked by S1A-D02/D08.

### FR-226 — Review-scoped optional rule default

- **Statement (EARS):** WHEN a user creates an Optional Configurable rule inside a review, THE SYSTEM SHALL assign `Current Review Only` scope and prevent that Rule ID and every version from appearing in any unrelated review's proposed or active Rule Set.
- **Rationale:** A local experiment must not silently become organization-wide financial policy.
- **Source:** Stakeholder directive §8.
- **Priority:** Must.
- **Dependencies:** FR-145, FR-149–FR-151, FR-207.
- **Acceptance:** A May rule is absent from June and from a different department before and after restart; its exact used version remains visible only in historical May runs.
- **Status:** Draft.

### FR-227 — Optional rule deletion or retirement

- **Statement (EARS):** WHEN an authorized user requests removal of a review-scoped Optional rule, THE SYSTEM SHALL apply the approved S1A-D05 deletion policy after a transactional retained-reference check and SHALL preserve every Rule Set and Validation Run that used the rule.
- **Rationale:** Users need cleanup without breaking historical truth.
- **Source:** Stakeholder directive §9.
- **Priority:** Must.
- **Dependencies:** S1A-D05; FR-145 and FR-149.
- **Acceptance:** An eligible unused rule follows the approved physical/logical disposition and remains absent after restart; a used rule offers retirement and historical replay remains exact.
- **Status:** Draft — blocked by S1A-D05.

### FR-228 — Exact duplicate ReviewCycle block

- **Statement (EARS):** IF another nondeleted ReviewCycle has the same department identity, reporting period, Budget source fingerprint, and GED source fingerprint, THEN THE SYSTEM SHALL block validation of the new ReviewCycle and offer `Open Existing Review`, `Return to Upload`, and `Cancel New Review`.
- **Rationale:** Exact duplicate financial reviews waste effort and create conflicting histories.
- **Source:** Stakeholder directive §5.
- **Priority:** Must.
- **Dependencies:** FR-124, FR-129–FR-135; NFR-129.
- **Acceptance:** The exact-duplicate scenario is blocked both at source binding and immediately before validation; a deleted review does not block; an archived review does.
- **Status:** Draft.

### FR-229 — Likely duplicate warning and override

- **Statement (EARS):** IF a distinct nondeleted ReviewCycle satisfies the approved S1A-D06 likely-duplicate predicate without satisfying FR-228, THEN THE SYSTEM SHALL display the matching and differing signals and offer `Compare Reviews`, `Open Existing Review`, `Continue as a New Review`, and `Cancel`, requiring a nonblank reason before the continue action commits.
- **Rationale:** Similar scopes need review without falsely blocking legitimate work.
- **Source:** Stakeholder directive §5.
- **Priority:** Must.
- **Dependencies:** S1A-D06; FR-228.
- **Acceptance:** The exact approved predicate triggers a warning, its inverse does not, same month with a different department proceeds, all four actions perform their labeled behavior, and an override audit records both Review IDs, predicate/hash-policy versions, signals/differences, actor, reason, and time.
- **Status:** Draft — blocked by S1A-D06.

### FR-230 — Same-review revalidation exclusion

- **Statement (EARS):** WHEN a Reviewer requests governed revalidation inside the same ReviewCycle, THE SYSTEM SHALL evaluate revalidation eligibility under the immutable successor-version contract and SHALL NOT classify the request as a duplicate ReviewCycle.
- **Rationale:** Duplicate prevention must not disable legitimate immutable reanalysis.
- **Source:** Stakeholder directive §§5 and 6; clarification derived from FR-173/FR-196.
- **Priority:** Must.
- **Dependencies:** FR-173, FR-196, FR-207, FR-228.
- **Acceptance:** Same-review revalidation creates one successor Review Version/run and preserves the prior run; creating a second ReviewCycle from the same scope remains blocked.
- **Status:** Draft.

### FR-231 — Deterministic prior-review selection

- **Statement (EARS):** WHEN a published current review requests default prior-period comparison, THE SYSTEM SHALL select the eligible same-department, compatible-layout published review with the greatest earlier year-month, then latest publication timestamp, then ascending Review ID, or SHALL record the first failed eligibility condition when none exists.
- **Rationale:** Comparison must not mix departments, incompatible layouts, or unpublished data.
- **Source:** Stakeholder directive §16.
- **Priority:** Must.
- **Dependencies:** S1A-D10; FR-171–FR-173, FR-194.
- **Acceptance:** Same-department compatible May is selected for June; tie fixtures follow the stated ordering; a different department, incompatible layout, or unpublished run yields the required unavailable explanation; explicitly selecting another eligible candidate records a distinct comparison projection.
- **Status:** Draft — blocked by S1A-D10.

### FR-232 — Versioned comparison classification

- **Statement (EARS):** WHEN current and prior projections are compared, THE SYSTEM SHALL assign each governed comparison identity one recurrence value from `New`, `Resolved`, `Continuing`, `Not Comparable`, or `Missing Prior Evidence` and, where recurrence is `Continuing`, one trend value from `Worsened`, `Improved`, `Unchanged`, or neutral `Changed`, using one recorded comparison-policy version.
- **Rationale:** Month-over-month conclusions must be reproducible rather than inferred in presentation or AI code.
- **Source:** Stakeholder directive §16.
- **Priority:** Must.
- **Dependencies:** S1A-D07 and S1A-D10; FR-231; NFR-130.
- **Acceptance:** The first matching S1A-D10 recurrence row and, when applicable, trend row determine the values using the approved Department, Account, Vendor, Finding, or Data-quality identity; results display both values (for example `Continuing · Improved`); `VER-MOM-001` matches every identity/value/classification and reruns byte-equivalently for the same two run identities and policy version.
- **Status:** Draft — blocked by S1A-D07/D10.

### FR-233 — Two-period comparison evidence

- **Statement (EARS):** WHEN FinSight displays or Ask Fin explains a comparative claim, THE SYSTEM SHALL identify and link the exact current and prior Review Versions, Validation Runs, deterministic values, and source-evidence records supporting that claim.
- **Rationale:** A leadership comparison must be auditable back to both months.
- **Source:** Stakeholder directive §16.
- **Priority:** Must.
- **Dependencies:** S1A-D10; FR-168, FR-231, FR-232.
- **Acceptance:** Every supported May-to-June claim has valid citations from both runs; unsupported causation is omitted or labeled unsupported.
- **Status:** Draft — blocked by S1A-D10.

### FR-234 — Five-area results information architecture

- **Statement (EARS):** WHEN recorded results open, THE SYSTEM SHALL expose only `Overview`, `Financial Analysis`, `GED Review`, `Findings`, and `Leadership Summary` as primary result areas while retaining rules, reconciliation mechanics, data quality, audit, and technical provenance through secondary drill-downs.
- **Rationale:** The product must remain detailed without presenting internal diagnostics as competing destinations.
- **Source:** Stakeholder directive §17.
- **Priority:** Must.
- **Dependencies:** S1A-D09; FR-157, FR-166, FR-185–FR-188.
- **Acceptance:** Navigation contains exactly the five primary areas; every displaced detail remains reachable and retains its original evidence identity.
- **Status:** Draft — blocked by S1A-D09.

### FR-235 — Decision-oriented Overview

- **Statement (EARS):** WHEN Overview renders a completed run, THE SYSTEM SHALL present recorded completion, Budget, parseable GED spend, EAC availability/value, variance availability/value, findings by severity, GED completeness, top account/vendor drivers, prior-period changes, and permitted human follow-up with drill-down links.
- **Rationale:** A reviewer must understand the current financial state before opening details.
- **Source:** Stakeholder directive §18.
- **Priority:** Must.
- **Dependencies:** FR-165, FR-186–FR-188, FR-232, S1A-D09.
- **Acceptance:** Every displayed figure equals the selected run's recorded projection; unavailable partial values are labeled and no UI calculation creates a new financial conclusion.
- **Status:** Draft — blocked by S1A-D09.

### FR-236 — Financial Analysis drill-down

- **Statement (EARS):** WHEN a user selects a supported Financial Analysis amount or visual, THE SYSTEM SHALL navigate through its available Department, Account, Vendor, GED transaction, and source-evidence identities without changing the selected Review Version or Validation Run.
- **Rationale:** Summary values must be explainable without reopening Excel.
- **Source:** Stakeholder directive §19.
- **Priority:** Must.
- **Dependencies:** FR-165, FR-166, FR-188.
- **Acceptance:** Budget-versus-GED, variance, account, vendor, and month-change views reproduce the exact financial table and reach the supporting source rows/cells.
- **Status:** Draft.

### FR-237 — Consolidated GED Review

- **Statement (EARS):** WHEN GED Review opens, THE SYSTEM SHALL present the selected run's transaction count, parseable spend, account/vendor/fiscal-period distributions, largest and signed activity, governed data-quality results, and source-row detail with filters for account, vendor, department, amount range, finding status, severity, and fiscal period.
- **Rationale:** GED financial detail and quality evidence belong in one understandable review area.
- **Source:** Stakeholder directive §20.
- **Priority:** Must.
- **Dependencies:** FR-157, FR-165, FR-166.
- **Acceptance:** Filters change only the displayed projection; each quality label traces to an active Rule Result or is explicitly labeled as a non-finding deterministic observation.
- **Status:** Draft — observation/finding distinction blocked by S1A-D07.

### FR-238 — Finding explanation and evidence

- **Statement (EARS):** WHEN a user opens a Finding, THE SYSTEM SHALL show its severity, plain-language title, affected identities, recorded impact, condition/expected/actual/difference, Rule ID/version, status, source rows/cells, review scope, and permitted human follow-up, with `Explain This`, `Ask Fin`, and `Open Evidence` actions.
- **Rationale:** A finding is useful only when the reviewer can understand and verify it.
- **Source:** Stakeholder directive §21.
- **Priority:** Must.
- **Dependencies:** FR-156, FR-157, NFR-093.
- **Acceptance:** Every field is derived from the selected recorded result/evidence; status changes append audit and never alter the underlying financial finding.
- **Status:** Draft.

### FR-239 — Deterministic Leadership Summary

- **Statement (EARS):** WHEN an authorized user generates or regenerates a Leadership Summary for the exact published completed Validation Run, THE SYSTEM SHALL append a recorded summary containing Overall Status, reporting month, department, Budget Health, GED Status, Key Findings, Account and Vendor Drivers, prior-period change, Key Risks, permitted human actions, Data Limitations, Rules Used, and Audit/Evidence Reference.
- **Rationale:** Leadership needs a complete monthly deliverable sourced from the same recorded truth.
- **Source:** Stakeholder directive §22.
- **Priority:** Must.
- **Dependencies:** FR-165, FR-187, FR-193, FR-231–FR-233.
- **Acceptance:** Summary values exactly equal the published run and comparison projections; Ask Fin can explain but cannot mutate the summary.
- **Status:** Draft.

### FR-240 — Immediate Draft persistence

- **Statement (EARS):** WHEN a user creates a review or commits its reporting month and year, THE SYSTEM SHALL persist a `Draft` ReviewCycle immediately and SHALL make that draft resumable or governably disposable after restart.
- **Rationale:** Work must not disappear merely because files have not yet been uploaded or validated.
- **Source:** Stakeholder directive §4.
- **Priority:** Must.
- **Dependencies:** FR-123, FR-124, FR-195, FR-201, FR-225.
- **Acceptance:** Closing immediately after period selection leaves one resumable Draft; explicit disposal removes it from active duplicate checks and retains only the approved tombstone.
- **Status:** Draft.

### FR-241 — Terminal Ask Fin outcome persistence

- **Statement (EARS):** WHEN an Ask Fin request reaches a displayed response, refusal, blocked outcome, or terminal failure, THE SYSTEM SHALL append the immutable terminal outcome, provider/model and prompt-policy versions, grounding/refusal status, timestamp, and only the validated citations supporting that outcome to the originating user message.
- **Rationale:** Every submitted question needs an attributable terminal history without rewriting its earlier message.
- **Source:** Stakeholder directive §12.
- **Priority:** Must.
- **Dependencies:** S1A-D08; FR-222–FR-224; NFR-126.
- **Acceptance:** Success, refusal, blocked, timeout, and crash-recovery cases retain one ordered user message plus the correct terminal/pending state; citations never attach to a different response or run.
- **Status:** Draft — blocked by S1A-D08.

### FR-242 — Modern embedded Ask Fin conversation

- **Statement (EARS):** WHEN the Ask Fin drawer is open, THE SYSTEM SHALL present user messages as right-aligned bubbles, Fin messages as left-aligned bubbles, first-message-only suggestions, loading/interrupted states, smooth end-of-conversation scrolling, multiline keyboard submission, and expandable validated citations/evidence in one accessible embedded conversation.
- **Rationale:** Ask Fin must behave as a professional assistant rather than a setup form or separate application window.
- **Source:** Stakeholder directive §14.
- **Priority:** Must.
- **Dependencies:** FR-222–FR-224, FR-241, NFR-131.
- **Acceptance:** Suggestions disappear/reduce after the first message; loading/interrupted states are announced; keyboard and pointer flows reach each citation/evidence item; no artificial child-window controls appear.
- **Status:** Draft.

### FR-243 — Integrated FinSight dialogs

- **Statement (EARS):** WHEN FinSight requires product confirmation, warning, comparison, or error interaction, THE SYSTEM SHALL use an in-application themed modal card or contextual drawer with plain-language title/body, explicit primary/secondary actions, initial/trapped/restored focus, Escape behavior, accessible labels, and Light/Dark support unless the operating system requires a native file/credential dialog.
- **Rationale:** Product dialogs must remain consistent and accessible without imitating operating-system window chrome.
- **Source:** Stakeholder directive §26.
- **Priority:** Must.
- **Dependencies:** NFR-131.
- **Acceptance:** Duplicate, optional-rule, provider-warning, and error-dialog fixtures pass keyboard/focus/theme/accessibility tests and show no artificial red/yellow/green window controls.
- **Status:** Draft.

### FR-244 — Provider model discovery and controlled entry

- **Statement (EARS):** WHEN an authorized actor configures a Provider Profile, THE SYSTEM SHALL discover model/deployment identities from that provider without review content when supported, or SHALL require an exact manually entered identity when discovery is unavailable, without presenting hard-coded consumer model names as guaranteed options.
- **Rationale:** Model identity must reflect the selected approved environment.
- **Source:** Stakeholder directive §11.
- **Priority:** Must.
- **Dependencies:** S1A-D03/D04; FR-219/FR-220.
- **Acceptance:** Discovery requests contain no financial context; a discovered/manual identity is bound to the profile version; an empty/unknown identity cannot be enabled.
- **Status:** Draft — blocked by S1A-D03/D04.

### FR-245 — External-processing warning and enforceable authorization

- **Statement (EARS):** IF a nonlocal Provider Profile is selected, THEN THE SYSTEM SHALL display the approved confidentiality/data-class warning and SHALL deny Test/Save/Use unless the profile carries a valid signed administrator-controlled authorization policy and the actor has permission to select that approved profile.
- **Rationale:** A checkbox cannot substitute for enforceable financial-data egress authorization.
- **Source:** Stakeholder directive §§11, 24, and 25.
- **Priority:** Must.
- **Dependencies:** S1A-D03/D04; FR-219; NFR-124/NFR-128.
- **Acceptance:** An ordinary Reviewer cannot create or authorize an arbitrary endpoint; warning acknowledgement alone never enables transmission; revoked/invalid policy fails closed.
- **Status:** Draft — blocked by S1A-D03/D04.

### FR-246 — External-provider data-policy enforcement and audit

- **Statement (EARS):** WHEN an authorized nonlocal provider request is attempted, THE SYSTEM SHALL construct the prompt only from data classes permitted by the exact profile policy, enforce required minimization/masking/tokenization/metadata-only transforms, block raw workbook bytes and source rows by default, and append provider, endpoint class, model, policy version, actor, prompt type, timestamp, and outcome audit without secrets or prohibited financial content.
- **Rationale:** Technical provider compatibility must not broaden the approved confidentiality boundary.
- **Source:** Stakeholder directive §§11 and 24.
- **Priority:** Must.
- **Dependencies:** S1A-D04; FR-219, FR-245; NFR-124/125/128.
- **Acceptance:** Field-level policy fixtures prove only allowed classes leave the device; raw workbook/source-row attempts are blocked by default; profile revocation blocks the next prompt; audit contains all required metadata and zero credentials/prohibited content.
- **Status:** Draft — blocked by S1A-D04.

## 3. Proposed non-functional requirements

### NFR-124 — Provider transmission fail-closed boundary

- **Statement (EARS):** IF the active provider's authorization, endpoint class, transport verification, data-handling policy, credential reference, or model identity cannot be verified immediately before a prompt, THEN THE SYSTEM SHALL send zero prompt bytes and SHALL expose one actionable non-confidential failure.
- **Category:** Security and confidentiality.
- **Fit criterion:** Across the approved provider fault matrix, packet capture records zero outbound prompt bytes for 100% of invalid cases and the audit records one blocked attempt without financial content.
- **Source:** Stakeholder directive §§11 and 24.
- **Status:** Draft — blocked by S1A-D03/D04.

### NFR-125 — No silent provider fallback

- **Statement (EARS):** WHILE an Ask Fin request uses one Provider Configuration Version, THE SYSTEM SHALL send the request only to that exact approved provider/endpoint/model or fail without selecting another provider.
- **Category:** Security and determinism.
- **Fit criterion:** Failure injection for endpoint, model, authentication, timeout, redirect, proxy, and TLS errors produces zero calls to every nonselected endpoint in packet capture.
- **Source:** Stakeholder directive §§11 and 24.
- **Status:** Draft.

### NFR-126 — Conversation isolation and content minimization

- **Statement (EARS):** WHILE Ask Fin conversation content is retained or retrieved, THE SYSTEM SHALL enforce exact Review ID, Review Version, Validation Run ID, Conversation ID, and Provider Configuration Version isolation and SHALL store no hidden chain-of-thought.
- **Category:** Privacy and auditability.
- **Fit criterion:** A cross-product matrix of two reviews, three runs, two providers, and restart/backup/restore paths returns zero cross-context message or citation records and storage search finds zero seeded hidden-reasoning markers.
- **Source:** Stakeholder directive §§12, 13, and 24.
- **Status:** Draft — retention duration blocked by S1A-D08.

### NFR-127 — Encrypted SQLite integrity and exactness

- **Statement (EARS):** WHILE committed FinSight state is stored in SQLite, THE SYSTEM SHALL enforce approved encryption at rest/key management, schema migrations, foreign keys, transactional state transitions, versioned decimal-safe monetary storage, integrity checks, and indexed identity/audit lookups under the approved persistence profile.
- **Category:** Reliability and data integrity.
- **Fit criterion:** Migration, encryption/key failure, interruption, foreign-key, integrity, and exact-decimal boundary suites produce zero unencrypted governed stores, zero partial transitions, zero orphan records, and zero binary-floating financial drift; query-plan inspection confirms index use for Review ID, department+period, Budget/GED fingerprint, Validation Run, Rule ID/version/scope, Conversation+Run, audit stream/correlation/time, publication, and lifecycle lookups on the approved maximum fixture.
- **Source:** Stakeholder directive §3.
- **Status:** Draft — storage population blocked by S1A-D02.

### NFR-128 — Secret isolation

- **Statement (EARS):** WHILE provider credentials exist, THE SYSTEM SHALL persist only an opaque credential reference in SQLite and SHALL store secret material exclusively in the approved operating-system or enterprise credential facility.
- **Category:** Security.
- **Fit criterion:** Database, backup, logs, crash data, audit, exports, and support-bundle scans find zero seeded secret values; credential revocation makes the profile unusable without deleting historical provider metadata.
- **Source:** Stakeholder directive §§3, 11, and 24.
- **Status:** Draft — credential facility blocked by S1A-D04.

### NFR-129 — Concurrent duplicate prevention

- **Statement (EARS):** WHILE two operations attempt to establish the same exact nondeleted review identity, THE SYSTEM SHALL commit at most one ReviewCycle eligible for validation.
- **Category:** Concurrency and integrity.
- **Fit criterion:** At least 100 synchronized two-writer attempts per supported SQLite journaling mode produce exactly one eligible review and one deterministic duplicate outcome, with zero lock-corruption or orphan records.
- **Source:** Stakeholder directive §5.
- **Status:** Draft.

### NFR-130 — Reproducible comparison

- **Statement (EARS):** WHILE the same two Validation Runs and comparison-policy version are selected, THE SYSTEM SHALL produce identical comparison identities, classifications, exact Decimal values, and evidence references independent of UI, Ask Fin provider, locale, or execution order.
- **Category:** Determinism and financial correctness.
- **Fit criterion:** Ten order/locale/provider permutations and two clean reruns match `VER-MOM-001` exactly in 100% of fields.
- **Source:** Stakeholder directive §16.
- **Status:** Draft.

### NFR-131 — Accessible results and dialogs

- **Statement (EARS):** WHILE the five result areas, Ask Fin drawer, or FinSight dialogs are used in Light or Dark mode, THE SYSTEM SHALL expose keyboard-operable controls, visible focus, programmatic labels, non-color status text, and readable evidence at the approved zoom/resizing matrix.
- **Category:** Accessibility and UX.
- **Fit criterion:** Automated accessibility/UI checks plus the approved keyboard, screen-reader, 100/125/150/200% zoom, and minimum-window matrix report zero blocker or critical defects.
- **Source:** Stakeholder directive §§14, 19, 26, and 28.
- **Status:** Draft.

### NFR-132 — Governed stage verification

- **Statement (EARS):** BEFORE this production-readiness increment is offered for hands-on acceptance, THE SYSTEM and evidence package SHALL pass the complete affected migration, integrity, persistence, duplicate, isolation, immutable-run, rule-lifecycle, May/June oracle, comparison, Ask Fin, provider-security, citation, accessibility, launch, architecture, and full-regression suites twice from the same identified clean revision with no unresolved affected material failure.
- **Category:** Verification and release governance.
- **Fit criterion:** Two evidence manifests identify the same source revision, environments, exact commands, test counts, skips, failures, artifact hashes, and independent Financial Control, Security/Privacy, and UX PASS verdicts; neither run is a filtered subset labeled as full regression.
- **Source:** Stakeholder directive §§28–30.
- **Status:** Draft.

## 4. Verification artifacts

| ID | Artifact | Required contents | Gate |
|---|---|---|---|
| `FIX-JUN-001` | June 2026 synthetic Budget/GED package | Same approved layout/department family, changed synthetic values, documented controlled cases, no invented unsupported fields | S1A-D07/D10 and oracle definitions approved |
| `ORACLE-JUN-001` | Independent June oracle | Exact totals, account/vendor values, core/optional results, findings, severities, and source locations | S1A-D07/D10 and independent Financial Control approval |
| `VER-MOM-001` | May-versus-June oracle | Separately labeled YTD/current-period measures, comparable identities, exact changes, classifications, and both-period evidence | S1A-D07/D10 and comparison ADR approved |

## 5. Requirements not created by this delta

The following remain governed by existing requirements and are not duplicated:

- five protected baseline rules and two-person protected change governance;
- source-layout mappings and row classifications for `SLV-001`;
- verified-data editing, provenance, and confirmation;
- immutable Rule Results/Findings and engine-derived consumers;
- finding status audit without changing financial truth;
- department/period mismatch gates;
- theme persistence and ordinary application navigation;
- whole-review disposal and content-free tombstones;
- Windows packaging, which remains a later prohibited stage.

## 6. Approval status

All items remain **Draft**. The Requirements stage cannot pass until:

1. S1A-D01 through S1A-D10 and applicable predecessor S1-D decisions are
   recorded by the named authorities;
2. blocked wording is updated to the selected policies;
3. one independent Requirements review returns PASS; and
4. the Product Owner explicitly approves the resulting exact package.
