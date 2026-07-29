# FinSight V2 Clarification Packet — 2026-07-27

- **Status:** Closed — no unresolved Requirements question remains
- **Purpose:** Preserve the decisions that converted Draft ambiguities into deterministic MVP requirements and distinguish them from downstream Architecture/release choices.
- **Requirement status effect:** Closing this packet does not by itself approve a requirement row; HD-27 permits Requirements completion only after incorporation, consistency checks, and an independent PASS.
- **Source registers:** Functional CQ-01–CQ-31 and non-functional CQ-10/CQ-11/CQ-22/CQ-23/CQ-25–CQ-27.

## 1. Human-provided decisions

The stakeholder explicitly established:

- the supplied Budget/GED reports and agreed sample conventions as the V1 business contract;
- Review Summary as the first post-validation view;
- Reviewer, Rule Administrator, and Financial Control Approver as the three MVP roles;
- different requester and approver people for every protected-baseline change;
- the authenticated Windows account as the default actor identity through a replaceable identity layer;
- editable review-local financial/business fields with immutable source files and visible Original Extracted, User-Reviewed, and Current Validation values;
- exact Review Summary identity fields;
- the seven-state Review Lifecycle Status;
- conditional Requirements completion after incorporation and an independent PASS, with no implementation before approved Architecture and design artifacts.

These decisions are recorded as HD-19 through HD-27 and implemented in functional requirements §2.7–§2.10 and FR-185–FR-202.

## 2. Sample-reference financial decisions

The supplied reports close the V1 finance and reader questions:

- CQ-01/CQ-02: sample department normalization and GED display-name precedence;
- CQ-03/CQ-04: selected period, GED title-period authority, Budget workspace assignment, and no-override mismatch behavior;
- CQ-09: Rule Execution and Overall Review Status roll-up;
- CQ-15–CQ-17: BGT/ATD meaning, eligible GED population, and `SLV-001` scope;
- CQ-18/CQ-19: all-15-field exact duplicate fingerprint and no accounting-event exceptions;
- CQ-20/CQ-21: V1 parse domains and exact two-decimal reconciliation;
- CQ-28: duplicate canonical Budget keys block validation;
- CQ-31: stored formula-result policy.

Enterprise accounting meanings, alternate layouts, fuzzy matching, broader normalization, and department-specific conventions remain future configurable extensions rather than MVP blockers.

## 3. Governance and configurable-engine decisions

The remaining Requirements questions are closed as follows:

| Items | Resolution |
|---|---|
| CQ-05, CQ-06, CQ-10 | Apply the three MVP roles, Windows stable Actor ID, two-person protected approval, and broad audited Working Dataset correction contract in functional requirements §2.8–§2.10. |
| CQ-07 | Every protected change creates a tested successor; requester and approver Actor IDs differ; activation occurs atomically at an approved effective time; all historical bindings remain replayable; no action may leave fewer than five active protected controls. |
| CQ-11, CQ-30 | Apply the controlled evaluators and separate Rule Definition Version and Rule Binding lifecycles in functional requirements §2.11. |
| CQ-12 | Require Review Summary print/PDF and spreadsheet-compatible Findings, Rule Results, and summarized-data exports. Audit export and on-screen run comparison are Should; comparison export is not required and tracker workbook remains R2. |
| CQ-13, CQ-29 | Preserve all 57 legacy rules unchanged outside the initial V2 active set. Use new permanent protected IDs `R-VAL-01` through `R-VAL-05`; future legacy migration requires its own governed mapping. |
| CQ-14 | Seed CORE-01 through CORE-05 as High, High, Medium, High, High. Severity is versioned run evidence and protected severity changes use two-person governance. |
| Independent scope cross-check | Distinguish a globally effective Protected Baseline Version from the workspace-scoped Rule Set Version shown in run identity. Protected activation creates the former; new-workspace creation, authorized workspace upgrade, or workspace binding change creates the latter. |

## 4. Quality and release-boundary decisions

| Items | Resolution |
|---|---|
| CQ-22, CQ-23 | A supported Windows upgrade retains all user data. Uninstall retains it by default and removes it only through a separate explicit confirmed choice. Exact OS builds, installer technology, certificate, and timestamp mechanism are Architecture/release-profile decisions. |
| CQ-25 | Retain root NFR-001: at most 10,000 GED rows on an 8–16 GB Windows corporate laptop within two minutes. Architecture adds workbook-complexity ceilings and an optional-rule stress profile; no unapproved 100-rule timing promise is made. |
| CQ-26 | Ask Fin is deny-by-default and may use only on-device or explicitly organization-approved private processing. Public/retail models are prohibited even with consent. Without an approved provider, Ask Fin is unavailable and deterministic validation remains complete. |
| CQ-27 | Reviews have no automatic expiry or ordinary-workflow deletion; archive is explicit and non-destructive; referenced rule/audit/output history remains replayable; Ask Fin retention is user-controlled; temporary artifacts are disposed at lifecycle end. The separately initiated and explicitly confirmed whole-scope disposal required by root NFR-017 remains available and leaves only its content-free deletion audit record. Architecture selects storage and recovery mechanisms. |

## 5. Independent pre-audit consistency resolutions

The strict functional and non-functional pre-audits identified the following analyst-resolvable specification gaps. These resolutions make existing stakeholder and parent-specification decisions testable; they do not introduce new organization-wide finance policy.

| Topic | Deterministic MVP resolution | Decision basis |
|---|---|---|
| GED report-level department evidence | Under `SLV-001`, the GED `TOTAL FOR DEPARTMENT` row is authoritative for report-level Department Number. GED detail-row department values remain transaction-level rule inputs, so the deliberately unmapped synthetic row does not block the file-level metadata gate. | Supplied-report structure; HD-19; TEST-04 intent |
| Advisory predicate with no match | Use `NO_OBSERVATION`; advisory rules never emit control PASS/FAIL solely to fill the complete result ledger. | HD-03 and single-engine complete-ledger principle |
| Protected candidate preparation | A Rule Administrator may author and test a protected Draft candidate but cannot activate it. A request references an immutable Tested candidate; a different Financial Control Approver alone approves activation. | HD-21/HD-22 two-person roles |
| Multiple roles and workspace upgrade | Active role permissions combine by union, explicit separation-of-duties denial overrides allow, and a Financial Control Approver authorizes applying an approved protected baseline to an existing workspace. | HD-21/HD-22; protected-baseline governance |
| Executive status terminology | V2 and inherited RAG are one status, not two calculations: `Healthy` = `On Track (Green)`, `Attention Required` = `Needs Attention (Yellow)`, and `Incomplete` = `At Risk (Red)`. | HD-20 plus inherited FR-076/FR-077 |
| ReviewCycle/generation mapping | Draft and Data Uploaded belong to a Working Candidate. Confirmation creates Review Version N as inherited ReviewGeneration sequence N at Data Reviewed/VERIFIED; each owns exactly one authoritative Validation Run/result lineage. | HD-24/HD-26; inherited ADR-011 |
| Verified data boundary and reconstruction | Confirmation records the verification/reconstruction basis and verified fingerprint. Normalized rows, Working Dataset, and complete `VerifiedDataset` are reconstructed from fingerprint-matching source bytes, extractor version, and correction events rather than persisted as complete row stores. | HD-24; inherited ADR-011/ADR-012 |
| Working versus published results | A successor is working/unpublished until an authorized Reviewer explicitly promotes it after ANALYZED; trusted outputs default to the published generation, while the immediate working summary is prominently labeled. | HD-05/HD-21/HD-26; inherited ADR-011 |
| Reason-specific rerun behavior | Data/extractor changes require fresh confirmation; rule/configuration reanalysis inherits the exact verification basis; exact replay creates a comparison event but no second authoritative generation/run. | Inherited ADR-011/ADR-012 |
| Later artifacts for sealed reviews | Reports, exports, and Ask Fin responses generated later are append-only derived records linked to the sealed Review Version and Validation Run, with their own generation audit data. | HD-24/HD-25; historical reproducibility |
| Unmapped GED effect on reconciliation | Matching always uses the complete Department Number + Account Number key. An unmapped GED row produces CORE-02 failure and is not assigned to a Budget scope by Account Number alone; unrelated valid Budget scopes remain evaluable. | HD-07/HD-10; TEST-04 intent |
| Closed-review disposal | Closed/Archived review content is read-only in ordinary workflows. Explicit confirmed whole-scope disposal under root NFR-017 is a distinct end-of-life operation, not a partial mutation. | Inherited NFR-017 and CQ-27 |

## 6. Downstream decisions that do not reopen Requirements

Architecture, UX, security, or release governance must select and review:

- controlled-rule serialization and evaluator classes within the approved semantic model;
- concrete spreadsheet-compatible export representation;
- workbook byte/decompression/complexity ceilings and optional-rule stress fixtures;
- supported Windows editions/builds, installer technology, signing certificate, and timestamp service;
- authorization provisioning, enterprise identity adapter, storage paths, backup/recovery, and temporary cleanup mechanisms;
- versioned error-taxonomy representation;
- an approved on-device or organization-private Ask Fin adapter and endpoint policy.

These choices cannot weaken the requirements. Application implementation remains blocked until the Architecture, rule-engine design, persistence model, UX/UI, and technical implementation plan are reviewed and approved.

## 7. Answer log

| Date | Item(s) | Decision basis | Applied artifacts |
|---|---|---|---|
| 2026-07-27 | CQ-01–CQ-04, CQ-09, CQ-15–CQ-21, CQ-28, CQ-31 | Product stakeholder HD-19/HD-20; supplied-report V1 contract | Functional §2.7, §10–§12; FR-124, FR-129–FR-135, FR-159–FR-164, FR-180–FR-188 |
| 2026-07-27 | CQ-05, CQ-06, CQ-10 | Product stakeholder HD-21–HD-26 | Functional §2.8–§2.10; FR-137–FR-145, FR-189–FR-197; NFR-085, NFR-090, NFR-107, NFR-108 |
| 2026-07-27 | CQ-07, CQ-11, CQ-30 | Product direction HD-02–HD-04, HD-21, HD-22, HD-27 | Functional §2.11–§2.12; FR-142–FR-150 |
| 2026-07-27 | CQ-08, CQ-14 | Product direction HD-03–HD-05, HD-11; sample-manifest evidence | Functional §2.4, §2.7, §2.12; FR-146, FR-156; CORE-01–CORE-05 |
| 2026-07-27 | CQ-12 | Inherited approved root FR-116–FR-120 and HD-20 | Functional §2.13; FR-151, FR-165, FR-166 |
| 2026-07-27 | CQ-13, CQ-29 | HD-01, HD-17, HD-18, HD-27; collision review | Functional §2.12; FR-143, FR-174; `03-existing-rule-disposition.md` |
| 2026-07-27 | CQ-22, CQ-23, CQ-25–CQ-27 | Inherited approved root requirements/ADRs and HD-18/HD-27 | Functional §2.13; FR-175–FR-178; NFR-081, NFR-086, NFR-087, NFR-094, NFR-095, NFR-101, NFR-103–NFR-105, NFR-109 |
| 2026-07-27 | CQ-24 | Product stakeholder HD-20 | FR-167–FR-170, FR-188 |
| 2026-07-27 | Pre-audit consistency set | Existing HD-03, HD-07, HD-10, HD-19–HD-25; supplied-report structure; inherited FR-076/FR-077, NFR-017, and `VerifiedDataset` contract | Functional §2.2–§2.13 and §11–§12; V2 Constitution; NFR-089–NFR-103; workflow WF-04, WF-06, WF-08, WF-11 |
| 2026-07-27 | Post-PASS independent cross-check reconciliation | Inherited ADR-011/ADR-012, root FR-084, HD-21–HD-26 | Functional §2.1–§2.12, FR-137–FR-173, FR-185–FR-202; NFR-082, NFR-090, NFR-091, NFR-101, NFR-102; workflow WF-02–WF-11; Governed V2 Delta items 1 and 6–13 |
