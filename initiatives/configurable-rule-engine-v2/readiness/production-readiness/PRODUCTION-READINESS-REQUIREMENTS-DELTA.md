# Production-Readiness Requirements Delta

**Initiative:** FinSight Configurable Rule Engine V2<br>
**Program stage:** Stage 1 — Baseline Freeze and SDD Reconciliation<br>
**Delta scope:** Production-readiness program and Section 15 successor requirements<br>
**Status:** Pending Stage 1 Product Owner approval<br>
**Prepared:** 2026-07-29<br>
**Normative effect before approval:** None; this is a proposed additive overlay<br>
**Implementation authorization:** None

## 1. Source identity and adoption model

This delta translates two exact Product Owner sources into successor requirement IDs without modifying the frozen Requirements package:

| Source | SHA-256 |
|---|---|
| FinSight Production-Readiness and Governed Release Program | `6653b87ba7d23fa83bba14450f1abb69479661e9550c03ef9b1154e16998bc53` |
| Section 15 — Enterprise Rule Governance, Complete Reporting, Audit History, and Final Distribution | `1275c7dee199b1f08d76a7bdcedb1185b645e04039f0a16d417a6ac05accf92d` |

The accepted predecessor snapshots remain:

- V2 Functional Requirements SHA-256 `0fe666b42290d6c12ac679a787f347155f8d2eb2fd6b03ab0957164984eb3297`;
- V2 Non-Functional Requirements SHA-256 `a49212a6c2bd9bd185831d4422d99018e99629afc4dd2c51ab622d8c52ce9a8b`.

Successor numbering begins at `FR-204` and `NFR-111`. These proposed requirements supplement or narrow predecessor requirements only where explicitly stated. They do not decide the open permanent-rule-ID or CORE-04 policy questions.

## 2. Requirement-state rules

| State | Meaning |
|---|---|
| Pending Stage 1 approval | Proposed from the current Product Owner sources, traceable and implementation-ready only after the Stage 1 gate approves it. |
| Approved | May be assigned only by the authorized Stage 1 approval record. |
| Deferred | Requires an explicit Product Owner disposition; absence from implementation is not silent deletion. |
| Superseded in part | A named predecessor clause remains historical, but this delta governs the specifically identified behavior after approval. |

Every requirement below is **Pending Stage 1 approval**. No code, migration, test baseline, packaging artifact, or user data may treat it as implemented merely because the current UI resembles it.

## 3. Proposed functional requirements

### FR-204 — Protected baseline repository visibility and ordinary-action protection

- **Statement:** BEFORE a validation run can be confirmed, THE SYSTEM SHALL display all five protected baseline controls in the Rules Repository with control purpose, classification, fields, configuration or thresholds, current version, prior versions, lifecycle state, activation evidence, and supporting documentation; WHEN an ordinary user attempts to disable, retire, replace, logically delete, or delete one, THE SYSTEM SHALL deny the action and explain that a governed protected-rule workflow is required.
- **Source:** Section 15.1.
- **Extends:** FR-143, FR-144, FR-150, FR-198, FR-199; NFR-085 and NFR-090.
- **Acceptance:** A five-control baseline fixture is completely visible; every ordinary mutation path is denied with an accessible warning; an authorized governed successor remains possible without loss of prior versions.
- **Required stage:** Stage 2 for identity/financial-control alignment; Stage 3 for governance persistence and authorization.
- **Verification:** Repository UI/accessibility tests; service authorization tests; five-control manifest comparison; protected-change integration tests; independent financial-control and security review.
- **Status:** Pending Stage 1 approval.

### FR-205 — Exact active Rule Set inspection and confirmation

- **Statement:** BEFORE validation, THE SYSTEM SHALL construct and show the complete proposed active Rule Set, including protected successor versions, enabled optional rules, and approved advisory rules only when in release scope; THE SYSTEM SHALL require confirmation of the exact Rule Set ID, Rule IDs, immutable Rule Versions, classifications, lifecycle states, configurations, thresholds, scopes, activation evidence, confirming Actor ID, and confirmation timestamp.
- **Source:** Section 15.2.
- **Extends:** FR-141, FR-145, FR-146, FR-150, FR-152, FR-184, FR-193.
- **Acceptance:** The pre-run summary gives counts by classification and total, permits inspection of each exact selected version, excludes draft/disabled/retired/unselected versions, and seals confirmation evidence before execution.
- **Required stage:** Stage 2 and Stage 3.
- **Verification:** Positive/negative active-set matrix; stale-version selection test; disabled/draft/retired exclusion tests; confirmation-audit persistence test; keyboard/screen-reader test.
- **Status:** Pending Stage 1 approval.

### FR-206 — Active-rule-only result and consumer derivation

- **Statement:** WHEN validation completes, THE SYSTEM SHALL derive every Rule Result, Finding, status, count, chart, analysis, Leadership Summary fact, report/export value, Explain This statement, Ask Fin grounding fact, and run-comparison fact exclusively from recorded results created by the confirmed active Rule Set; THE SYSTEM SHALL NOT execute or expose a financial conclusion that lacks Rule ID, Rule Version, Rule Set ID, Validation Run ID, affected scope, outcome, evidence, calculation basis, and source-record lineage.
- **Source:** Section 15.3.
- **Extends:** FR-142, FR-153 through FR-158, FR-165 through FR-169, FR-184, FR-186, FR-187, FR-194; ADR-V2-007.
- **Acceptance:** Adding, changing, disabling, or retiring an optional rule changes only the next run's recorded projections and all consumers update from those projections; consumer-boundary fitness tests reject direct evaluator imports or UI-only financial checks.
- **Required stage:** Stage 2, Stage 4, Stage 5, and Stage 6.
- **Verification:** Full consumer provenance test; architecture fitness test; optional-rule metamorphic test; historical-run replay; report/UI/Ask Fin equality check.
- **Status:** Pending Stage 1 approval.

### FR-207 — Governed rule change, revalidation, and complete comparison

- **Statement:** WHEN an authorized rule mutation is proposed, THE SYSTEM SHALL validate it, create an immutable Rule Version and successor Rule Set Version, preserve every predecessor, require confirmation of the successor active set, create a new Validation Run, and compare the new run with the selected predecessor as `added`, `removed`, `changed`, or `unchanged` for both Rule Results and Findings without overwriting history.
- **Source:** Section 15.4.
- **Extends:** FR-144, FR-145, FR-147 through FR-151, FR-171, FR-173, FR-196, FR-198, FR-199, FR-202; NFR-089 and NFR-090.
- **Acceptance:** Create/edit/enable/disable/retire/protected-successor fixtures each produce an immutable successor and exact comparison; unchanged facts are explicitly classified; replay of the predecessor reproduces its original ordered projection.
- **Required stage:** Stage 2 and Stage 3.
- **Verification:** Version-chain tests; comparison oracle; immutable-history test; concurrent activation/revalidation test; predecessor replay.
- **Status:** Pending Stage 1 approval.

### FR-208 — Complete review-lifecycle audit capture

- **Statement:** WHEN a governed review, source, extraction, reviewed-data, verification, rule, validation, finding, explanation, Ask Fin, evidence, report/export, publication, comparison, backup/restore, disposal, runtime/model, or application-version event occurs, THE SYSTEM SHALL append a typed audit event containing the required subject identifiers, before/after facts where applicable, Actor ID, timestamp, correlation ID, outcome, and safe reason or diagnostic identity.
- **Source:** Section 15.5.
- **Extends:** Root FR-084 through FR-090; FR-138, FR-144, FR-149, FR-154, FR-171, FR-193, FR-194, FR-198 through FR-202; NFR-090, NFR-091, NFR-101, NFR-109.
- **Acceptance:** A canonical end-to-end fixture produces one ordered event for every applicable event type in the Section 15.5 catalog; denied/failed/refused events remain attributable; secrets, hidden reasoning, and raw financial content prohibited by policy are absent.
- **Required stage:** Stage 3, with consumer checks in Stages 5–7.
- **Verification:** Event-catalog completeness test; schema/ordering/tamper tests; fault-injection recovery; correlation trace; privacy-log inspection.
- **Status:** Pending Stage 1 approval.

### FR-209 — Human-readable audit summary and complete report appendix

- **Statement:** WHEN a Leadership Summary is displayed or a complete report is generated, THE SYSTEM SHALL show the review creator, data verifier, Rule Set confirmer, validation time, Rule Set and Validation Run identity, rule/data change indicators, publication state, Ask Fin-use indicator, export indicator, and review status; the complete report SHALL include the selected review's full ordered audit timeline with secrets and prohibited internals excluded.
- **Source:** Section 15.6.
- **Extends:** FR-186, FR-193, FR-194; root FR-089 and FR-090.
- **Acceptance:** Summary facts match the audit ledger for the selected review/run; the full appendix has complete ordered events with explicit redaction/exclusion labels and no cross-review content.
- **Required stage:** Stage 5.
- **Verification:** Audit-to-summary equality test; appendix event-count/order oracle; redaction/privacy test; selected-review isolation test; accessibility review.
- **Status:** Pending Stage 1 approval.

### FR-210 — Complete deterministic enterprise PDF

- **Statement:** WHEN an authorized user requests a PDF for one exact Review Version and Validation Run, THE SYSTEM SHALL create a leadership-ready report containing the Section 15.7 content set—identity, status, summaries, financial detail, GED detail subject to approved limits, comparisons, analyses, reconciliation, Rule Results, Findings, deterministic explanations, evidence references, charts, data quality, Rule Set/version appendix, source fingerprints, limitations, human-review requirements, audit appendix, and generation metadata—using recorded deterministic projections only.
- **Source:** Section 15.7.
- **Extends and narrows:** Root FR-116, FR-117, FR-120; V2 §2.13, FR-165, FR-186, FR-187, FR-193, FR-194.
- **Acceptance:** Every financial value and status equals the selected recorded projection; no report-side evaluator exists; every required section is present or explicitly marked excluded under FR-212; source/run identity is unambiguous.
- **Required stage:** Stage 5.
- **Verification:** Golden-PDF semantic inspection; application-to-report equality oracle; required-section parser; Decimal/string equality; independent reporting and financial-control review.
- **Status:** Pending Stage 1 approval.

### FR-211 — Export confirmation and publication labeling

- **Statement:** BEFORE creating a PDF, THE SYSTEM SHALL display and require confirmation of Review ID, period, Review Version, Validation Run ID, Rule Set ID, publication state, included sections, detail profile, and generating Actor ID; WHEN generated, THE PDF SHALL display exactly one valid state label: `Working Draft`, `Published Review`, `Historical Review`, or `Superseded Review`.
- **Source:** Section 15.8.
- **Extends:** FR-171, FR-172, FR-193, FR-194, FR-202.
- **Acceptance:** A user cannot generate without confirmation; concurrent publication/supersession uses the creation-time state contract; no draft can appear published; the label matches retained lifecycle facts.
- **Required stage:** Stage 3 for lifecycle contract; Stage 5 for UI/reporting.
- **Verification:** State-transition matrix; confirmation UI/accessibility test; concurrent promotion/export test; retained-artifact metadata check.
- **Status:** Pending Stage 1 approval.

### FR-212 — PDF detail profiles and explicit completeness declaration

- **Statement:** WHEN a user exports a PDF, THE SYSTEM SHALL offer `Leadership Summary only`, `Standard Financial Review`, and `Complete Evidence Report`; THE SYSTEM MAY paginate or move large tables to appendices or the companion XLSX, but SHALL state the selected profile, included sections, excluded sections and approved reason, row counts, and whether the selected output is complete for that profile, and SHALL never silently omit required data.
- **Source:** Section 15.9.
- **Extends:** FR-210; root FR-116 and FR-117.
- **Acceptance:** Boundary fixtures around approved size limits produce complete disclosures and stable pagination; the Complete Evidence Report contains all in-scope GED/audit rows or an explicit, approved companion-workbook reference with exact counts.
- **Required stage:** Stage 5 after S1-D12 is approved.
- **Verification:** Detail-profile matrix; limit-minus-one/equal/plus-one tests; row-count reconciliation; visual pagination review; accessible reading-order test.
- **Status:** Pending Stage 1 approval.

### FR-213 — Deterministic XLSX evidence workbook

- **Statement:** WHEN an authorized user requests spreadsheet evidence for an exact Review Version and Validation Run, THE SYSTEM SHALL create an XLSX with separate sheets named `Review Overview`, `Leadership Summary`, `Budget Data`, `GED Data`, `Budget vs GED`, `Account Analysis`, `Vendor Analysis`, `Department Analysis`, `Rule Results`, `Findings`, `Evidence`, `Rule Set`, `Audit History`, `Source Files`, and `Report Metadata`, preserving exact displayed values, identifiers, evidence references, and selected-run identity.
- **Source:** Section 15.10.
- **Extends and narrows:** Root FR-118 through FR-120; V2 §2.13, FR-165, FR-194.
- **Acceptance:** All 15 sheets exist in order or by exact name; authoritative cells are literal retained values; formulas, if any, are explicitly marked non-authoritative display aids and cannot change exported authoritative facts.
- **Required stage:** Stage 5.
- **Verification:** OOXML structural inspection; sheet/value/identifier oracle; formula inventory; application-to-XLSX equality; independent reporting review.
- **Status:** Pending Stage 1 approval.

### FR-214 — Export identity and integrity verification

- **Statement:** WHEN a PDF or XLSX export completes, THE SYSTEM SHALL retain and expose the application version, Review ID/version, Validation Run ID, Rule Set ID, included Rule Versions, generation time, generating Actor ID, publication state, source fingerprints, export ID, and final artifact SHA-256 or equivalent non-self-referential integrity identifier so an authorized reviewer can match the artifact to retained FinSight facts.
- **Source:** Section 15.12.
- **Extends:** Root FR-120; FR-171, FR-193, FR-194; NFR-095.
- **Acceptance:** Rehashing the immutable completed file equals the retained/sidecar manifest hash; any byte modification fails verification; every identifier resolves to the retained review without exposing secrets.
- **Required stage:** Stage 5 and Stage 7.
- **Verification:** Hash/manifest verification; tamper test; metadata resolution test; access-control and privacy test.
- **Status:** Pending Stage 1 approval.

### FR-215 — Automatic private local-AI dependency provisioning

- **Statement:** WHEN FinSight is installed or repaired on a supported clean Windows machine, THE INSTALLER SHALL automatically provide or configure the approved private local-AI runtime and exact approved model, establish the governed local-only connection, and make Ask Fin ready without Python, Terminal, manual runtime installation, manual model download, or manual service startup.
- **Source:** Production-readiness program objective and Stages 6–8; Section 15.15.
- **Supersedes in first-release scope:** Any earlier statement that FinSight must never automatically obtain or provision its model.
- **Extends:** FR-175 through FR-178, FR-200; NFR-094, NFR-095, NFR-104.
- **Acceptance:** An offline/online acquisition policy-approved clean-machine fixture reaches Ask Fin ready state through the signed installer alone; missing/corrupt runtime/model supports deterministic repair; uninstall follows the approved retention/removal choice.
- **Required stage:** Stage 6 architecture/security hardening; Stage 7 implementation; Stage 8 qualification.
- **Verification:** Clean-machine install/repair/upgrade/uninstall tests; exact runtime/model identity check; no-terminal observation; egress capture; licensing/SBOM review.
- **Status:** Pending Stage 1 approval and decisions S1-D06, S1-D08, S1-D09.

### FR-216 — One-click Windows distribution workflow

- **Statement:** WHEN the release is authorized, FinSight SHALL be distributed as a signed Windows installer or approved equivalent through an enterprise-approved download such that the manager workflow is `download installer → run installer → open FinSight → use the application`, with every required dependency included or automatically configured.
- **Source:** Section 15.15.
- **Extends:** FR-175 through FR-178; NFR-094 and NFR-095.
- **Acceptance:** A supported non-developer can install and launch on a clean target without repository/ZIP source, VS Code, Python, commands, or developer intervention; a raw executable ZIP cannot satisfy this requirement.
- **Required stage:** Stage 7 and Stage 8.
- **Verification:** Moderated clean-machine usability test; installer telemetry/evidence; dependency inventory; one-click launch smoke test.
- **Status:** Pending Stage 1 approval.

### FR-217 — Exact authorized final distribution

- **Statement:** WHEN and only when every governed stage, independent reviewer gate, Product Owner hands-on gate, release qualification, and final release-authority decision has passed, THE RELEASE PROCESS SHALL rebuild from the exact hands-on-approved source commit, produce and verify the signed artifact and release manifest, and publish a download that resolves to that exact artifact; otherwise the distribution action SHALL remain blocked.
- **Source:** Section 15.13 through 15.17; production-readiness program Stages 8–9 and release-decision rules.
- **Extends:** FR-178; NFR-095 and NFR-099.
- **Acceptance:** Any missing/failed/stale gate prevents publication; the distributed artifact hash equals the release manifest and qualified artifact; final decision is exactly `GO`, `CONDITIONAL GO`, or `NO-GO` under the approved policy.
- **Required stage:** Stage 9 after Stages 1–8.
- **Verification:** Release-gate negative matrix; controlled pipeline rebuild reproducibility; signature/timestamp/hash/malware checks; clean-machine rerun; download-target verification.
- **Status:** Pending Stage 1 approval.

### FR-218 — Configurable confidentiality marking and unprotected-destination warning

- **Statement:** WHEN a PDF or XLSX is generated, THE SYSTEM SHALL apply the approved organization confidentiality label, defaulting to `Confidential — Internal Financial Review` unless governance configures another approved label; BEFORE export to a location that fails the approved protection policy, THE SYSTEM SHALL warn the user, record the decision, and apply the authorized block-or-confirm behavior.
- **Source:** Section 15.11.
- **Extends:** FR-190, FR-194, FR-214; NFR-086, NFR-100.
- **Acceptance:** Both formats display the configured label; only authorized configuration changes are accepted and audited; protected/unprotected destination fixtures follow policy with no silent export.
- **Required stage:** Stage 3 for configuration/authorization; Stage 5 for reports; Stage 7/8 for Windows destination policy.
- **Verification:** Role/configuration tests; label inspection; destination ACL/policy matrix; audit-event test; accessibility review.
- **Status:** Pending Stage 1 approval and S1-D13.

## 4. Proposed non-functional requirements

### NFR-111 — Confidential enterprise-financial processing boundary

- **Statement:** FinSight SHALL treat Budget, GED, vendor, account, transaction, finding, evidence, audit, Ask Fin, report, export, and backup content as confidential enterprise financial information and SHALL enforce encryption at rest, encrypted backup, least privilege, role authorization, safe logging/crash/support behavior, and no public or unapproved external transmission.
- **Source:** Section 15.11; governing program prohibitions.
- **Extends:** Root NFR-009 through NFR-020; NFR-086, NFR-088, NFR-100, NFR-103 through NFR-105.
- **Fit criterion:** Security inspection finds zero confidential values in ordinary logs, crash reports, support bundles without approved inclusion, public API traffic, unrelated review contexts, or unencrypted governed stores.
- **Required stage:** Stage 3, Stage 5, Stage 6, Stage 7, and Stage 8.
- **Verification:** Static/dataflow review; filesystem/ACL/encryption inspection; log/crash/support tests; packet capture; cross-review isolation; independent security/privacy PASS.
- **Status:** Pending Stage 1 approval.

### NFR-112 — Immutable, ordered, attributable, tamper-evident audit

- **Statement:** Every FR-208 audit event SHALL be append-only, attributable, totally ordered within its governed stream, correlation-linked, tamper-evident, authorized for least-privilege access, and retained or disposed only under the approved enterprise policy.
- **Source:** Section 15.5.
- **Extends:** Root NFR-019 and NFR-020; NFR-082, NFR-090, NFR-091, NFR-102, NFR-109.
- **Fit criterion:** Mutation/deletion/reorder/insertion attempts are denied or detected; crash/fault recovery yields one valid ordered history without duplicate or lost committed events.
- **Required stage:** Stage 3 and Stage 8.
- **Verification:** Cryptographic-chain tests; database tamper probes; power-loss/fault injection; actor/time/order oracle; authorization tests.
- **Status:** Pending Stage 1 approval.

### NFR-113 — Deterministic export equality and no report-side financial logic

- **Statement:** PDF, XLSX, Leadership Summary, charts, and exported appendices SHALL reproduce retained deterministic projections for one exact Review Version and Validation Run without recomputing, rounding into a different financial result, or deriving new failures in presentation or export code.
- **Source:** Section 15.3, 15.7, 15.10, and 15.12.
- **Extends:** FR-165, FR-187, FR-194; NFR-091 and NFR-093.
- **Fit criterion:** A canonical Decimal oracle compares every exported monetary/status/count field to the recorded projection with exact approved-format equivalence and zero business-result mismatch.
- **Required stage:** Stage 2 and Stage 5.
- **Verification:** Independent Decimal/OOXML/PDF oracle; consumer dependency fitness tests; formatting/rounding boundary matrix.
- **Status:** Pending Stage 1 approval.

### NFR-114 — Secure report/export workspace and lifecycle cleanup

- **Statement:** Report and export generation SHALL use a protected workspace with least-privilege filesystem permissions, deterministic cleanup on success/failure/cancel/crash/restart, no confidential plaintext remanence under the approved threat model, and safe destination handling.
- **Source:** Section 15.11.
- **Extends:** NFR-088, NFR-105, NFR-109.
- **Fit criterion:** All operation outcomes leave zero prohibited temporary artifact; cleanup events are audited; a cleanup failure blocks unsafe completion and exposes an actionable non-confidential diagnostic.
- **Required stage:** Stage 3, Stage 5, and Stage 8.
- **Verification:** Failure/cancel/crash matrix; filesystem forensics; ACL tests; disposal audit check; destination-policy tests.
- **Status:** Pending Stage 1 approval.

### NFR-115 — Accessible and scalable report generation

- **Statement:** PDF/XLSX export and confirmation UI SHALL remain keyboard accessible, screen-reader meaningful, and operational for the approved maximum review size; large tables SHALL have stable pagination/appendix behavior and explicit completeness disclosures.
- **Source:** Section 15.9 and the program's accessibility/reliability objective.
- **Extends:** NFR-081, NFR-092, NFR-094; remediation accessibility and resizing requirements.
- **Fit criterion:** Approved maximum-size fixtures complete within the approved hardware/time/memory envelope; PDF tagging/reading order and confirmation controls pass the approved assistive-technology matrix.
- **Required stage:** Stage 4, Stage 5, and Stage 8.
- **Verification:** Performance benchmark; memory profile; PDF accessibility inspection; native Windows screen-reader/keyboard/zoom tests.
- **Status:** Pending Stage 1 approval and decisions S1-D08 and S1-D12.

### NFR-116 — Local-only Ask Fin runtime, model, and egress assurance

- **Statement:** First-release Ask Fin SHALL use only the approved local runtime/model identity, enforce loopback/no-proxy/no-redirect/no-cloud-fallback behavior before every prompt, remain unable to execute financial or product mutations, and recover to an automatic ready state through approved installer/repair paths.
- **Source:** Production-readiness program Stages 6–8; Section 15.11 and 15.15.
- **Extends and narrows:** NFR-086, NFR-103, NFR-104; ADR-V2-005 for the first-release deployment profile.
- **Fit criterion:** Network interception and hostile configuration tests observe zero non-loopback model traffic; model/runtime identity is verified pre-prompt; unavailable/corrupt fixtures recover without manual developer steps.
- **Required stage:** Stage 6, Stage 7, and Stage 8.
- **Verification:** Packet capture; proxy/redirect/DNS/IPv6 tests; pre-prompt identity tests; repair/offline tests; independent Ask Fin safety/privacy review.
- **Status:** Pending Stage 1 approval and S1-D09.

### NFR-117 — Signed and reproducible software/model supply chain

- **Statement:** Every release installer, executable, bundled runtime, model, migration, dependency, and update SHALL be license-approved, version-pinned, provenance-recorded, checksum-verified, malware-scanned, SBOM-listed, built from the controlled approved commit, and signed/timestamped where the artifact type supports it.
- **Source:** Program Stage 7 and Section 15.16.
- **Extends:** NFR-095 and NFR-099; FR-178.
- **Fit criterion:** The release manifest resolves every shipped byte to approved source/provenance/license; clean rebuild output is reproducible to the approved level; tampered or unapproved assets are rejected.
- **Required stage:** Stage 7 and Stage 9.
- **Verification:** SBOM/license review; controlled pipeline attestation; checksum/signature/timestamp verification; malware scan; model redistribution approval.
- **Status:** Pending Stage 1 approval.

### NFR-118 — Clean-machine and enterprise qualification matrix

- **Statement:** The release candidate SHALL pass install, first run, extraction, validation, reports, Ask Fin, persistence, restart, repair, upgrade, uninstall, and failure recovery on every approved clean Windows hardware/OS/user-rights profile, including constrained supported hardware.
- **Source:** Program Stage 8 and Section 15.16.
- **Extends:** FR-176 and FR-177; NFR-094.
- **Fit criterion:** Every mandatory matrix cell has reproducible PASS evidence from an isolated clean environment; any mandatory failure holds the gate at NO-GO.
- **Required stage:** Stage 8.
- **Verification:** VM/physical-machine matrix; standard-user/admin variants; 8/16GB or approved replacement profiles; offline/online install; signed evidence bundle.
- **Status:** Pending Stage 1 approval and S1-D08.

### NFR-119 — Independent multidisciplinary release review

- **Statement:** After implementation stages complete, independent reviewers who did not approve their own work SHALL inspect implementation and evidence and return PASS for Product, Finance, Requirements, Architecture, Security/Confidentiality, Ask Fin Grounding/Safety, Accessibility, UX, Reporting/Export, Test/Regression, and Release Engineering; any material defect SHALL keep the release NO-GO.
- **Source:** Section 15.13.
- **Extends:** NFR-099 and the established independent-review process.
- **Fit criterion:** The release evidence index contains an attributable, scoped verdict from every required discipline and proves reviewer/implementer separation.
- **Required stage:** Stage 9.
- **Verification:** Reviewer independence manifest; evidence-to-implementation sampling; verdict completeness check.
- **Status:** Pending Stage 1 approval.

### NFR-120 — Ordered hands-on and final-distribution authorization

- **Statement:** Product Owner hands-on review SHALL occur only after all independent PASS verdicts, and final distribution SHALL occur only after explicit hands-on approval and final release-authority GO; no downstream action may reinterpret missing approval as consent.
- **Source:** Section 15.14 through 15.17.
- **Extends:** NFR-099; FR-217.
- **Fit criterion:** Gate-state tests block out-of-order transition; all approvals contain actor, timestamp, exact build/source/artifact identity, scope, and result.
- **Required stage:** Stage 9.
- **Verification:** Release-state-machine test; negative transition matrix; approval artifact/hash linkage.
- **Status:** Pending Stage 1 approval.

### NFR-121 — Full regression and financial-oracle release gate

- **Statement:** Before hands-on acceptance and again for the exact final rebuilt artifact, the complete governed regression, independent financial oracle, security/privacy suite, accessibility suite, Ask Fin grounding/refusal suite, report/export equality suite, and installer qualification suite SHALL pass with zero unresolved mandatory failures.
- **Source:** Program Stage 9; Section 15.16 and 15.17.
- **Extends:** Remediation consolidated-verification NFR; NFR-083, NFR-092, NFR-095, NFR-099.
- **Fit criterion:** Two exact evidence runs identify commit/build/artifact, environment, tests, counts, skips, quarantines, and outcomes; order-varied execution exposes no state leakage.
- **Required stage:** Stage 9.
- **Verification:** Governed full-suite commands; independent oracle; randomized/order-varied run; exact test inventory and machine manifests.
- **Status:** Pending Stage 1 approval.

### NFR-122 — Approved retention, backup, recovery, and disposal policy conformance

- **Statement:** Review, source-reference, result, rule, audit, Ask Fin, report/export, backup, recovery-control, and content-free tombstone records SHALL be retained, backed up, restored, archived, or disposed only according to one approved enterprise policy whose version is recorded with every applicable action.
- **Source:** Section 15.5 and 15.11; program Stage 1 decision and Stage 5 recovery scope.
- **Extends:** NFR-089, NFR-101, NFR-102, NFR-105, NFR-109; FR-201.
- **Fit criterion:** Policy-boundary fixtures prove no early deletion, no restoration after governed disposal, no orphan history, and exact recovery or explicit non-recoverability for every governed record class.
- **Required stage:** Stage 3 and Stage 5.
- **Verification:** Retention clock/boundary tests; backup/restore manifest oracle; disposal-revocation tests; policy migration tests.
- **Status:** Pending Stage 1 approval and S1-D04/S1-D11.

### NFR-123 — Reproducible baseline and honest release evidence

- **Statement:** Every stabilization and release claim SHALL identify the exact source commit/snapshot, classified source inventory, requirement/architecture overlays, migrations, generated artifacts, test environment, test selection, skips, failures, independent reviews, and artifact hashes; missing mandatory evidence SHALL be reported as incomplete or NO-GO rather than PASS.
- **Source:** Program Stage 1, Stage 9, and governing prohibitions; Section 15.13 through 15.17.
- **Extends:** NFR-099 and NFR-095.
- **Fit criterion:** An independent reviewer can reconstruct the claimed source state and evidence chain; modified/untracked or generated files are classified; no focused test run is labeled a full regression.
- **Required stage:** Stage 1 and every subsequent gate.
- **Verification:** Clean Git/source inventory; evidence-index link/hash audit; independent release audit; negative missing-evidence scenarios.
- **Status:** Pending Stage 1 approval.

## 5. Explicit predecessor impacts

Approval of this delta would make only the following scoped changes; all other predecessor requirements remain in force:

| Predecessor | Proposed impact |
|---|---|
| Old five-gate sequencing in the Technical Implementation Plan | Superseded only by the nine-stage production-readiness delivery sequence. Earlier gate outcomes remain historical. |
| Generic PDF/XLSX format discretion in root/V2 reporting requirements | Narrowed by FR-210 through FR-214 to mandatory PDF and XLSX content and identity. |
| External organization-private provider option in ADR-V2-005 | Narrowed for this first-release profile to local-only/no-cloud under NFR-116; a successor Architecture decision is required. |
| Stage 2 “never auto-download model” direction | Superseded for supported Windows distribution by FR-215, subject to approved topology, licensing, and security design. |
| Mac-first or macOS parity statements | Not deleted. S1-D10 must formally retain or defer them relative to the Windows release target. |
| `R-VAL-*` versus `CORE-*` identities | Not resolved by this delta. S1-D01 remains a Stage 1 exit blocker. |
| CORE-04 GED completeness versus Budget formula checks | Not resolved by this delta. S1-D02 remains a Stage 1 exit blocker. |

## 6. Gate dependencies

| Requirement group | Cannot become implementation-ready until |
|---|---|
| FR-204 through FR-207 | S1-D01 and S1-D02 are approved; S1-D03 is approved if advisory rules are included. |
| FR-208, FR-209, NFR-112, NFR-122 | S1-D04 and S1-D11 define backup/retention/disposal scope and policy. |
| FR-210 through FR-214, FR-218, NFR-113 through NFR-115 | S1-D05, S1-D12, and S1-D13 are approved. |
| FR-215, NFR-116, NFR-117 | S1-D06, S1-D08, S1-D09, license/redistribution, and local-AI security decisions are approved. |
| FR-216, FR-217, NFR-118 through NFR-121, NFR-123 | The preceding stages pass and the exact release baseline/build is identified. |

## 7. Approval record

Approval must reference this file's final SHA-256 and the exact two source hashes in §1.

| Field | Value |
|---|---|
| Product Owner approval | Pending |
| Financial Control approval for protected-rule scope | Pending |
| Security/Privacy approval for confidentiality/local AI | Pending |
| Architecture acceptance of required deltas | Pending |
| Approved effective date | Pending |
| Approved file SHA-256 | Pending |
| Exceptions or deferrals | Pending |
