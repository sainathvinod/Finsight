# FinSight SDD Closeout — Exact Evidence Index

**Review date:** 2026-07-29
**Repository:** `FinSight-AIConsulting`
**Observed Git HEAD:** `a298040a8408c04342818a65a186a0d72c87956a`
**Purpose:** Identify the exact evidence used for the SDD closeout, state its
authority and time relevance, and prevent a historical PASS or a rendered
screenshot from being mistaken for current release-readiness proof.

This index is evidence navigation, not a new product specification. A link to a
file means the closeout considered it; it does not imply that every claim in the
file remains correct.

## 1. Evidence classifications and interpretation

| Code | Evidence class | How it is used | What it does **not** prove |
|---|---|---|---|
| **N** | Normative/governing | Defines approved intent, requirements, principles, architecture, or a governed delivery decision. | That the current implementation conforms. |
| **H** | Historical stage evidence | Records a test, screenshot, review, approval, inventory, or result at a named earlier snapshot. | Current release readiness after later changes. |
| **C** | Current closeout evidence | Re-performed or generated during the 2026-07-29 closeout against the present working tree. | Clean-machine, Windows, production-scale, or external-security behavior unless explicitly exercised. |
| **I** | Current implementation evidence | Shows where behavior is presently implemented. | That behavior is correct merely because code exists. Tests and/or inspection are still required. |
| **E** | External authoritative reference | Establishes a platform, tool, runtime, or licensing fact from its official publisher. | That FinSight has implemented or qualified that capability. |

### Evidence-strength rules

1. Human decisions and the adopted Constitution govern product intent.
2. `specs/` is the authoritative root baseline. The similarly named files in
   `docs/` are useful project-history and understanding evidence, but they are
   not a substitute for the later approved `specs/` versions.
3. The V2 initiative is a governed delta to the same product. A later explicit
   V2 human decision may refine an inherited root requirement, but code never
   silently supersedes either source.
4. Package-level Requirements and Architecture approval records govern the
   reviewed hashes even where individual V2 requirement rows still say
   `Draft`. That wording mismatch is documentation debt, not permission to
   ignore the package-level gate.
5. Historical review PASS records are scoped to their frozen snapshot.
   Subsequent Stage 1, Stage 2, follow-up, Ask Fin simplification, and current
   working-tree changes require new evidence.
6. Screenshots prove rendered appearance on the capture host and fixture. They
   do not prove financial correctness, accessibility semantics, persistence,
   security, or Windows compatibility.
7. The current full-suite result supersedes earlier passing focused or full
   counts for packaging readiness.

## 2. Governing source hierarchy

| Priority | Evidence | Class | What it establishes | What it does not establish |
|---:|---|---|---|---|
| 1 | [Root FinSight Constitution](../../../../specs/constitution.md) | N | Adopted principles, decision rights, `specs/` authority, deterministic-core boundary, accessibility and release quality bars. | Current conformance or V2-specific details. |
| 2 | [V2 product-direction source](../../briefs/PRODUCT-DIRECTION-SOURCE-configurable-rule-engine-v2.md) | N | Durable human decisions HD-01–HD-27 and approved corrections to V2 direction. | Implementation completion. |
| 3 | [V2 implementation brief](../../briefs/IMPLEMENTATION-BRIEF-configurable-rule-engine-v2.md) | N | Approved product-owner scope: one product, configurable engine, protected baseline rules, department-neutral workflow, Review Summary, identity and governance. | Technical realization. |
| 4 | [V2 Constitution](../../specs/constitution.md) | N | Inheritance and precedence rules for the initiative; binding V2 terminology and invariants. | That root specifications were formally rewritten. |
| 5 | [Governed V2 delta](../../requirements/GOVERNED-V2-DELTA-2026-07-27.md) | N | Reconciles V2 rule-set, lifecycle, verification, immutability, publication, and disposal semantics with the root baseline. | Current code compliance. |
| 6 | [V2 Requirements completion](../../requirements/REQUIREMENTS-PHASE-COMPLETION-2026-07-27.md) | N/H | Records the Requirements gate PASS and the exact reviewed FR/NFR hashes. | Final Product or packaging approval. |
| 7 | [Architecture approval](../ARCHITECTURE-APPROVAL-2026-07-27.md) and [frozen package](../ARCHITECTURE-STAGE-PACKAGE-2026-07-27.md) | N/H | Records the independently reviewed Architecture gate and frozen artifact hashes. | Approval of later implementation or architecture drift. |
| 8 | [Execution lanes](../../plans/EXECUTION-LANES.md) | N | Defines Governed Lane and Rapid UX Lane boundaries and the focused-test exception for presentation-only work. | That a particular change was correctly classified. |
| 9 | Implementation, tests, current closeout evidence | I/C | Shows actual behavior and current verification state. | Authority to change approved intent. |

### Governing-source cautions

- [Root baseline approval package](../../../../specs/readiness/BASELINE-APPROVAL-PACKAGE.md)
  states that `specs/` is authoritative, but its human signature checklist and
  immutable generated baseline manifest remain visibly incomplete. This is
  relevant SDD documentation debt; it does not erase the explicit approval
  status recorded in the root specifications.
- The V2 FR/NFR files retain row-level `Draft` text while
  [Requirements completion](../../requirements/REQUIREMENTS-PHASE-COMPLETION-2026-07-27.md)
  records package-level completion and pinned hashes. Consumers must read these
  together.
- The initiative [README](../../README.md) contains a historical “current gate”
  narrative that stops at final MVP remediation. It is not a current closeout
  status source after Stage 1 and Stage 2.

### Conversation-supplied governed direction

The following attached source texts were read as original stakeholder direction. They
are external to the repository and should be preserved or summarized into the governed
baseline before attachment retention expires:

| Evidence | Class | What it establishes | Limit |
|---|---|---|---|
| [Initial FinSight project briefing](/Users/lakshminarayanana/.codex/attachments/f40af6c5-2f48-4e0a-af7c-ff0e8259dd4a/pasted-text.txt) | N/H | Repository-understanding and product-context request that initiated the work. | Conversation attachment, not a version-controlled specification. |
| [Configurable validation product direction](/Users/lakshminarayanana/.codex/attachments/b9d7f7f4-7afe-4512-a9a1-6be6aa4736d9/pasted-text.txt) | N/H | One-product configurable-rule-engine evolution and initial baseline controls. | Later clarifications and V2 specs govern conflicts. |
| [Preserved FinSight review workflow](/Users/lakshminarayanana/.codex/attachments/7874e21e-38bb-4a5f-8e0d-e0581a6300ff/pasted-text.txt) | N/H | Guided review experience, two-file MVP, evidence, rule-engine, Ask Fin, and history expectations. | Later seven-stage and Stage 2 presentation decisions refine the visible workflow. |
| [End-to-end workflow alignment](/Users/lakshminarayanana/.codex/attachments/d4bbd92f-6f61-4c99-89ea-8f9b3a2f5233/pasted-text.txt) | N/H | Continuous Create→Upload→Verify→Validate→Results→Complete journey and full result/evidence expectations. | Later remediation and Stage 2 navigation supersede some tab/presentation details. |
| [MVP final remediation source](/Users/lakshminarayanana/.codex/attachments/2ea78e14-64f6-458b-8a77-bae130758b78/pasted-text.txt) | N/H | Editable Verify Data, Rules Repository, evidence, analytics, deletion, themes, and release-evidence requirements. | Stage 1/2 sources later simplify analytics/navigation and Ask Fin. |
| [Stage 1 financial-correctness source](/Users/lakshminarayanana/.codex/attachments/02224699-d4a7-4ef1-b6ad-6ab1f6aabd67/pasted-text.txt) | N/H | Canonical financial dataset, hierarchy, exact controls, independent oracle, five-rule evidence, and full field coverage. | Its remediation-era Budget-formula wording does not by itself authorize changing the approved permanent CORE-04 contract. |
| [Stage 2 modern UX and private Ask Fin source](/Users/lakshminarayanana/.codex/attachments/0c212c86-5bf5-4ffb-a93c-ca311cb7e138/pasted-text.txt) | N/H | Five-section Financial Review, deterministic Explain This, local grounded Ask Fin, decision boundary, privacy, and accessibility. | Follow-up and simplification sources refine setup/readiness behavior. |
| [Stage 2 Ask Fin/navigation/rules follow-up](/Users/lakshminarayanana/.codex/attachments/ed36855a-4d3f-4a57-9cbe-aaab8688bac2/pasted-text.txt) | N/H | Right-side assistant, operational local setup, global Back, and simplified Rules Repository. | The later Ask Fin simplification removes ordinary identity/setup approval friction. |

## 3. Original product understanding and root product specifications

### 3.1 Understanding and product vision

| Evidence | Class | What it proves | Limit |
|---|---|---|---|
| [Project Understanding — authoritative root version](../../../../specs/00-project-understanding.md) | N | Original product objective, business problems, users, monthly workflow, data sources, scope, assumptions, constraints, and success criteria. | Predates later V2 department-neutral and local-only AI decisions unless read with V2 deltas. |
| [Project Understanding — earlier `docs/` version](../../../../docs/00-project-understanding.md) | H | Earlier discovery record and rationale, including Application Engineering sample context. | Not the current authoritative baseline; contains language later generalized by V2. |
| [V2 initiative README](../../README.md) | N/H | V2 relationship to the same FinSight product and directory map; records stage chronology. | Its “current gate” section is historical rather than current closeout evidence. |
| [Financial Review workflow](../../docs/FINANCIAL-REVIEW-WORKFLOW.md) | N | Approved WF-01–WF-11 guided review and the relationship among upload, verify, rules, validation, summary, findings, Ask Fin, and history. | Rendered UX quality or implementation completeness. |

### 3.2 Authoritative root baseline

These files are **normative** and must be included in any product-wide
traceability review:

| Evidence | What it governs |
|---|---|
| [Functional requirements](../../../../specs/01-functional-requirements.md) | Root FR-001–FR-122. |
| [Non-functional requirements](../../../../specs/02-non-functional-requirements.md) | Root NFR-001–NFR-080 and measurable quality bars. |
| [Epics](../../../../specs/03-epics.md) | Approved product decomposition. |
| [Features](../../../../specs/04-features.md) | Feature-level acceptance framing. |
| [Rules catalog](../../../../specs/05-rules-catalog.md) | Inherited rule inventory and finance-control semantics. |
| [Application architecture](../../../../specs/06-architecture.md) | Root component and dependency architecture. |
| [UX design](../../../../specs/07-ux-design.md) | Root workflows, task model, and accessibility intent. |
| [UI design system](../../../../specs/08-ui-design-system.md) | Root visual and interaction standards. |
| [Decision log](../../../../specs/09-decision-log.md) | Approved product and delivery decisions. |
| [AI and agents](../../../../specs/10-ai-and-agents.md) | Deterministic/AI boundary, provider and consent model inherited unless refined. |
| [Development methodology](../../../../specs/11-development-methodology.md) | SDD gates, reviews, Definition of Done, traceability, and release evidence. |

### 3.3 Earlier `docs/` specification set

The files [docs/01–11](../../../../docs/) are all different from their
same-named `specs/` counterparts. They remain useful historical evidence for
why the product evolved, but are **not** the authority when they conflict with
`specs/`. The closeout specifically reviewed:

- [Functional requirements](../../../../docs/01-functional-requirements.md)
- [Non-functional requirements](../../../../docs/02-non-functional-requirements.md)
- [Epics](../../../../docs/03-epics.md)
- [Features](../../../../docs/04-features.md)
- [Rules catalog](../../../../docs/05-rules-catalog.md)
- [Architecture](../../../../docs/06-architecture.md)
- [UX design](../../../../docs/07-ux-design.md)
- [UI design system](../../../../docs/08-ui-design-system.md)
- [Decision log](../../../../docs/09-decision-log.md)
- [AI and agents](../../../../docs/10-ai-and-agents.md)
- [Development methodology](../../../../docs/11-development-methodology.md)
- [Build-readiness runbook](../../../../docs/12-build-readiness-runbook.md)
- [Walking-skeleton plan](../../../../docs/13-walking-skeleton-plan.md)

These prove earlier intent and planning. They do not prove that the later V2
application implements every inherited Phase 2–4 capability.

### 3.4 Root ADRs and readiness records

| Evidence group | Class | What it proves | Limit |
|---|---|---|---|
| [ADR-001 through ADR-010](../../../../specs/adr/) | N | Stack, layers, Decimal, SQLite, audit, review aggregate, findings, PySide6, and AI persistence/masking decisions. | Some were refined by ADR-011–015 and V2 ADRs. |
| [ADR-011 lifecycle](../../../../specs/adr/ADR-011-review-lifecycle-and-generation-model.md) | N | Working/published generation and validation-run lineage. | Actual persistence integrity. |
| [ADR-012 reconstruction](../../../../specs/adr/ADR-012-source-binding-and-working-set-reconstruction.md) | N | Fingerprint-bound reconstruction instead of silently persisted normalized truth. | Reader correctness or source availability. |
| [ADR-013 desktop scope](../../../../specs/adr/ADR-013-single-user-single-instance-desktop-scope.md) | N | Single-user/single-instance MVP assumptions. | Enterprise deployment readiness. |
| [ADR-014 retention](../../../../specs/adr/ADR-014-review-abandonment-and-retention.md) | N | Non-destructive ordinary retention and abandonment semantics. | Backup or enterprise retention policy. |
| [ADR-015 export identity](../../../../specs/adr/ADR-015-immutable-export-and-report-identity.md) | N | Immutable derived-artifact identity requirements. | That all exports/reports exist. |
| [Gate-4 implementation package](../../../../specs/readiness/GATE-4-IMPLEMENTATION-PACKAGE.md) | H | Root implementation-entry evidence. | V2 final-product or packaging approval. |
| [Root readiness folder](../../../../specs/readiness/) | H | Constitution adoption, ratification, gate and authorization records. | Current working-tree status. |

## 4. V2 requirements, architecture, plans, and workflows

### 4.1 Requirements and requirement-review evidence

| Evidence | Class | What it establishes | Limit |
|---|---|---|---|
| [V2 functional requirements](../../specs/01-functional-requirements.md) | N | FR-123–FR-203: configurable rule model, protected baseline, review versions, department/period extraction, review summary, evidence, editing, reporting, Ask Fin linkage, lifecycle. | Rows still display `Draft`; use with package approval/hashes. |
| [V2 non-functional requirements](../../specs/02-non-functional-requirements.md) | N | NFR-081–NFR-110: atomicity, no false PASS, determinism, performance, accessibility, security, replay, privacy and Windows quality constraints. | Passing unit tests alone do not satisfy hardware/clean-machine criteria. |
| [Existing-rule disposition](../../specs/03-existing-rule-disposition.md) | N | Prevents silent deletion/reclassification of the inherited rule catalog. | Does not mean all 57 inherited rules are implemented in the MVP. |
| [Closed clarification packet](../../specs/clarifications/CLARIFICATION-PACKET-2026-07-27.md) | N/H | Resolved roles, separation of duties, identity, editable data, review context and lifecycle questions. | Later implementation conformance. |
| [Full Requirements review](../../specs/generated/SPEC-AUDIT-2026-07-27-FULL-REVIEW.md) | H | Independent review of the then-current package. | Superseded by the recheck after repairs. |
| [Requirements recheck PASS](../../specs/generated/SPEC-AUDIT-2026-07-27-RECHECK.md) | H | Fresh 111/111 package PASS for the pinned requirements snapshot. | Later implementation or post-review requirement drift. |
| [Cross-check](../../specs/generated/SPEC-CROSSCHECK-2026-07-27.md) | H | Cross-artifact consistency repair evidence. | Current code conformance. |
| [Current closeout traceability matrix](UPDATED-REQUIREMENTS-TRACEABILITY-MATRIX-2026-07-29.md) | C | Current implementation/test/evidence status for approved requirements, including gaps and supersessions. | Formal stakeholder approval of any proposed disposition. |

### 4.2 Approved V2 architecture package

| Evidence | Class | What it governs |
|---|---|---|
| [Application Architecture](../../docs/APPLICATION-ARCHITECTURE.md) | N | Layering, composition, services, lifecycle, security, audit, packaging and platform boundaries. |
| [Rule Engine Design](../../docs/RULE-ENGINE-DESIGN.md) | N | Versioned definitions, immutable rule sets, execution ledger, findings, revalidation and replay. |
| [Persistence Model](../../docs/PERSISTENCE-MODEL.md) | N | Encrypted authoritative store, append-only records, migration/recovery and lineage. |
| [UX/UI Design](../../docs/UX-UI-DESIGN.md) | N | Approved desktop shell, workflow, summary, evidence, accessibility and status presentation. |
| [Technical Implementation Plan](../../plans/TECHNICAL-IMPLEMENTATION-PLAN.md) | N | Delivery order, boundaries, testing and Windows release intent. |
| [Architecture independent review](../../reviews/REVIEW-2026-07-27-architecture-stage.md) | H | PASS on the frozen architecture package. |
| [Architecture package hashes](../ARCHITECTURE-STAGE-PACKAGE-2026-07-27.md) | H | Identifies exactly what the architecture review covered. |

### 4.3 V2 ADRs

| Evidence | Class | Decision |
|---|---|---|
| [ADR-V2-001](../../adr/ADR-V2-001-configurable-deterministic-rule-engine.md) | N | One configurable deterministic engine and result contract. |
| [ADR-V2-002](../../adr/ADR-V2-002-sequential-multi-actor-local-governance.md) | N | Local multi-role governance and two-person protected changes. |
| [ADR-V2-003](../../adr/ADR-V2-003-encrypted-authoritative-persistence-and-recovery.md) | N | Encrypted store and recovery strategy. |
| [ADR-V2-004](../../adr/ADR-V2-004-windows-packaging-and-support.md) | N | Windows executable/installer, identity, support and release architecture. |
| [ADR-V2-005](../../adr/ADR-V2-005-private-engine-bound-ai.md) | N | Private, read-only, engine-grounded AI boundary. |
| [ADR-V2-006](../../adr/ADR-V2-006-slv001-workbook-safety-profile.md) | N | Approved workbook safety and parser profile. |
| [ADR-V2-007](../../adr/ADR-V2-007-ledger-consumers-and-derived-records.md) | N | Dashboards, analytics, reports and AI consume recorded results. |

### 4.4 Delivery plans and stage deltas

| Evidence | Class | What it covers | Limit |
|---|---|---|---|
| [Workflow 1 plan](../../tasks/WORKFLOW-01-IMPLEMENTATION-PLAN.md) | N/H | Review-management increment. | Later product behavior. |
| [Workflow 2 plan](../../tasks/WORKFLOW-02-IMPLEMENTATION-PLAN.md) | N/H | Upload and extraction increment. | Verify, validation and results behavior. |
| [Integrated MVP plan](../../tasks/MVP-END-TO-END-IMPLEMENTATION-PLAN.md) | N/H | Authorized end-to-end primary journey. | Later remediation and Stage 1/2 changes. |
| [MVP remediation delta](../../requirements/MVP-REMEDIATION-DELTA-2026-07-28.md) | N | Final remediation requirements for editable data, rules, evidence, analytics, deletion, appearance and UX. | Implementation proof. |
| [MVP remediation architecture](../../docs/MVP-REMEDIATION-ARCHITECTURE-2026-07-28.md) | N | Architecture impact of that remediation. | Current conformance. |
| [MVP remediation plan](../../tasks/MVP-FINAL-REMEDIATION-IMPLEMENTATION-PLAN-2026-07-28.md) | N/H | Remediation implementation and verification steps. | Stage 1/2 scope. |
| [Stage 1 governed plan](../../tasks/STAGE-1-GOVERNED-IMPLEMENTATION-PLAN-2026-07-29.md) | N/H | Canonical financial dataset, hierarchy, protected rules, configurable rules, replay, evidence and financial correctness. | Stage 2 UX/Ask Fin behavior. |
| [Stage 2 governed plan](../../tasks/STAGE-2-GOVERNED-IMPLEMENTATION-PLAN-2026-07-29.md) | N/H | Modern results UX, deterministic explanations, private Ask Fin, navigation and simplified rules UX. | Packaging qualification. |
| [Stage 1 financial hierarchy design](../../docs/STAGE-1-FINANCIAL-HIERARCHY-AND-CANONICAL-DATASET.md) | N | Canonical account/department/vendor/transaction relationships and recorded projections. | That each calculation is correctly implemented. |
| [Stage 2 product design](../../docs/STAGE-2-MODERN-UX-AND-PRODUCT-DESIGN-2026-07-29.md) | N | Current results navigation and decision-oriented interaction model. | Pixel-level current appearance. |

## 5. Historical verification and independent reviews

Every item in this section is **historical**. Its date and scoped file inventory
must be checked before using its PASS.

### 5.1 Workflow and integrated MVP

| Evidence | What it proves at that snapshot | What it does not prove now |
|---|---|---|
| [Workflow 1 verification](../../verification/WORKFLOW-01-VERIFICATION-2026-07-27.md) and [independent review](../../reviews/REVIEW-2026-07-27-workflow-01.md) | Review creation, persistence, lifecycle, audit and then-current tests. | Current end-to-end regression. |
| [Workflow 1 UX review](../../reviews/REVIEW-2026-07-27-workflow-01-ux-remediation.md) | The remediated desktop shell met that focused review. | Current Stage 2 layout at all scales. |
| [Workflow 2 verification](../../verification/WORKFLOW-02-VERIFICATION-2026-07-27.md) and [independent review](../../reviews/REVIEW-2026-07-27-workflow-02.md) | Approved-layout ingestion/extraction, metadata and safety behavior at the Workflow 2 snapshot. | Later reader changes or large-workbook performance. |
| [Integrated MVP verification](../../verification/MVP-END-TO-END-VERIFICATION-2026-07-27.md) and [independent review](../../reviews/REVIEW-2026-07-27-mvp-end-to-end.md) | Then-current complete journey and test evidence. | Later remediation, Stage 1/2, or packaging readiness. |
| [MVP remediation stage package](../MVP-FINAL-REMEDIATION-STAGE-PACKAGE-2026-07-28.md) | Exact remediation scope and traceability. | Completion by itself. |
| [MVP remediation verification](../../verification/MVP-FINAL-REMEDIATION-VERIFICATION-2026-07-28.md), [changed-file inventory](../../verification/MVP-FINAL-REMEDIATION-CHANGED-FILES-2026-07-28.md), and [review](../../reviews/REVIEW-2026-07-28-mvp-final-remediation.md) | Verification/review of the named remediation snapshot and its changed files. | Stage 1/2 and Ask Fin simplification changes. |

### 5.2 Rapid UX Lane

| Evidence | Scope proved | Exclusion |
|---|---|---|
| [Final landing page verification](../../verification/FINAL-LANDING-PAGE-VERIFICATION-2026-07-28.md) and [review](../../reviews/REVIEW-2026-07-28-final-landing-page.md) | Focused landing-page layout/theme behavior. | Governed logic and full regression. |
| [Landing scale verification](../../verification/RAPID-UX-LANDING-SCALE-2026-07-28.md) | Focused proportional scale adjustment. | Non-UI behavior. |
| [Verify Data source-details verification](../../verification/RAPID-UX-VERIFY-DATA-SOURCE-DETAILS-2026-07-28.md) | Focused source-row/evidence-panel UX. | Source-lineage correctness beyond the tested fixture. |

### 5.3 Stage 1 financial correctness

| Evidence | Scope proved then | Current caution |
|---|---|---|
| [Stage 1 verification](../../verification/STAGE-1-FINANCIAL-CORRECTNESS-VERIFICATION-2026-07-29.md) | Canonical dataset, Decimal results, five core rules, optional rules, replay, recorded projections, evidence and Stage 1 tests for its snapshot. | The closeout identified rule-contract deviations not detected by the Stage 1 oracle; see current test inventory. |
| [Stage 1 independent review](../../reviews/REVIEW-2026-07-29-stage-1-financial-correctness.md) | Independent review verdict on the frozen Stage 1 evidence. | It is not a waiver for newly detected CORE-03/CORE-04/period/status defects. |
| [Stage 1 independent-oracle JSON](../../verification/STAGE-1-INDEPENDENT-ORACLE-2026-07-29.json) | Machine-readable expected/actual ledger at that snapshot. | Correctness of expectations not independently encoded outside the repository. |

### 5.4 Stage 2 and follow-up

| Evidence | Scope proved then | Current caution |
|---|---|---|
| [Stage 2 consolidated verification](../../verification/STAGE-2-CONSOLIDATED-VERIFICATION-2026-07-29.md) | Modern results UI, deterministic Explain This, private Ollama design and then-current tests/screenshots. | Follow-up and simplification changes occurred later. |
| [Stage 2 follow-up verification](../../verification/STAGE-2-FOLLOWUP-ASK-FIN-NAVIGATION-RULES-2026-07-29.md) | Ask Fin panel, back navigation and simplified Rules Repository at that follow-up snapshot. | Automatic-readiness simplification and present full-suite status. |
| [Ask Fin simplification verification](../../verification/STAGE-2-ASK-FIN-SIMPLIFICATION-2026-07-29.md) | Reports 200 focused tests plus 2 subtests for automatic readiness, local protections and simplified unavailable state. | The current full suite is not clean; focused PASS is not packaging evidence. |
| [Stage 2 grounding and decision boundary](../../docs/STAGE-2-ASK-FIN-GROUNDING-AND-DECISION-BOUNDARY-2026-07-29.md) | Normative grounding, citation, refusal and authority boundary. | Model behavior outside tested prompts or production hardware. |
| [Stage 2 private AI architecture delta](../../docs/STAGE-2-PRIVATE-ASK-FIN-ARCHITECTURE-DELTA-2026-07-29.md) | Local-only composition and security architecture. | Bundling, provisioning, update, repair or licensing completion. |
| [Stage 2 threat model](../../docs/STAGE-2-LOCAL-INFERENCE-THREAT-MODEL-2026-07-29.md) | Identified local inference threats and controls. | Independent penetration/security assessment. |
| [Ask Fin prompt pack 1.0.0](../../docs/STAGE-2-ASK-FIN-PROMPT-PACK-1.0.0.md) | Versioned prompt/refusal policy used as design input. | That a model always obeys it. |

## 6. Fixtures, manual oracle, and financial-source evidence

| Evidence | Class | Exact role | Important limit |
|---|---|---|---|
| [Sample Budget workbook](../../fixtures/Sample_Budget_Report.xlsx) | N/H | Approved-layout synthetic Budget fixture used by ingestion, validation and screenshot tests. SHA-256 `bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14`. | One department/layout, not enterprise-format coverage. |
| [Sample GED workbook](../../fixtures/Sample_GED_Report.xlsx) | N/H | Approved-layout synthetic GED fixture with intentional test cases. SHA-256 `2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c`. | Does not represent production volume, all row variants, or confidential data. |
| [Synthetic validation expectations](../../fixtures/SYNTHETIC-VALIDATION-EXPECTATIONS.md) | N/H | Expected four intentional source-data findings and fixture interpretation. | Not a complete independent oracle for all core/optional/boundary semantics. |
| [MVP remediation test matrix](../../fixtures/MVP-REMEDIATION-SYNTHETIC-TEST-MATRIX-2026-07-28.md) | H | Expected-vs-actual matrix for remediation scenarios. | Predates Stage 1/2 behavior. |
| [Stage 1 manual oracle](../../fixtures/STAGE-1-MANUAL-VALIDATION-ORACLE-2026-07-29.md) | H | Human-readable Decimal totals, per-account expectations and rule outcomes. SHA-256 `f2aad7efe3450b591f42ca2c6938dd1d19097554cee4847f0e70f7b281696a86`. | It bakes the expanded CORE-04 scope total and therefore cannot independently detect that spec drift. |
| [Oracle verification script](../../../../scripts/verify_stage1_financial_oracle.py) | I | Recomputes OOXML fixture expectations without importing the production validation engine. | Still shares repository-authored expectations and fixture assumptions. |
| [Oracle integration test](../../../../tests/integration/test_stage1_financial_oracle.py) | C/I | Runs the independent script and validates production results against the encoded oracle. | Does not establish that every encoded expectation matches the approved rule contract. |

## 7. Current closeout evidence

### 7.1 Current documents produced by this review

| Evidence | Class | What it proves |
|---|---|---|
| [Consolidated closeout report](FIN-SIGHT-SDD-CLOSEOUT-AND-NEXT-STAGE-REVIEW-2026-07-29.md) | C | Integrated product, requirements, financial, safety, UX, architecture, risk, packaging and next-stage assessment. |
| [Consolidated test inventory](CONSOLIDATED-TEST-INVENTORY-2026-07-29.md) | C | Exact current test commands/results, category inventory, skips, focused financial probes, architecture checks, gaps and release interpretation. |
| [Updated requirements traceability matrix](UPDATED-REQUIREMENTS-TRACEABILITY-MATRIX-2026-07-29.md) | C | Current mapping from approved requirements to implementation, tests, evidence and completion state. |
| [Consolidated risk register](CONSOLIDATED-RISK-REGISTER-2026-07-29.md) | C | Current product, finance, security, UX, deployment and operational risks with severity, ownership and gate impact. |
| [Packaging-readiness checklist](PACKAGING-READINESS-CHECKLIST-2026-07-29.md) | C | Gate-by-gate evidence for the current **Not ready for packaging** decision. |
| [One-page manager summary](ONE-PAGE-MANAGER-SUMMARY-2026-07-29.md) | C | Decision-focused synopsis of status, blockers and the single recommended next stage. |
| This exact evidence index | C | Evidence provenance, authority and limitations. |
| [Independent closeout review](INDEPENDENT-CLOSEOUT-REVIEW-2026-07-29.md) | C | Independent consistency review, reproduced full-suite result, resolved ICR-01 recheck, and final PASS on the closeout package—not on product release readiness. |

Current evidence hashes at the time this index was prepared:

- Test inventory:
  `1549d13c05f906eac351b90b92b4de8a0afd41b630009ad184a9543e3fa20c44`
- Traceability matrix:
  `bcd7d6b9829ff6f16a64c4499acacd35bbb0b3789bfdfbfe0943273dff3a9667`

Hashes will change if the closeout team corrects these documents before the
final package is frozen.

### 7.2 Current test and repository observations

| Observation | Evidence | Interpretation |
|---|---|---|
| Full suite: **4 failed, 1212 passed, 2 subtests passed** | [Test inventory §3](CONSOLIDATED-TEST-INVENTORY-2026-07-29.md) | Current tree is not at a clean packaging regression gate. |
| 1216 collected tests across 127 test files | [Test inventory §2](CONSOLIDATED-TEST-INVENTORY-2026-07-29.md) | Broad automated coverage exists; count alone is not risk coverage. |
| Financial/oracle focused selection: 29 passed | [Test inventory §5](CONSOLIDATED-TEST-INVENTORY-2026-07-29.md) | Existing oracle and focused financial tests pass their encoded expectations. |
| Architecture contracts: 3/3 kept | [Test inventory §7](CONSOLIDATED-TEST-INVENTORY-2026-07-29.md) | Declared import-linter contracts pass, but one ungoverned delivery→infrastructure dependency remains outside those contracts. |
| Launch smoke passed offscreen | [Test inventory §4](CONSOLIDATED-TEST-INVENTORY-2026-07-29.md) | Application composes and starts on this macOS development host. It is not a Windows clean-machine test. |
| Git HEAD `a298040…`; observed dirty working tree with 29 modified and 135 untracked status entries during evidence collection | Shell observation recorded in this index and test inventory context | The reviewed product state is not a clean, reproducible release commit. Counts may rise while closeout documents are created. |

The current failures and current financial probes supersede earlier PASS claims
for packaging decisions. They do not retroactively invalidate the historical
stage work; they establish that stabilization is now required.

## 8. Current-run screenshot evidence

The closeout captured a same-fixture, same-host light/dark walkthrough under
[the current closeout screenshot root](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/).
There are 21 light and 21 dark captures.

### 8.1 Light mode

| Workflow area | Current screenshot |
|---|---|
| Home | [00-home.png](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/00-home.png) |
| Create Review | [00a-create-review.png](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/00a-create-review.png) |
| Upload empty / complete | [empty](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/00b-upload-empty.png) · [complete](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/00c-upload-complete.png) |
| Verify Budget / GED | [Budget](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/00e-verify-budget.png) · [GED](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/00f-verify-ged.png) |
| Ask Fin help mode | [00g-private-ask-fin-help-mode.png](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/00g-private-ask-fin-help-mode.png) |
| Rules / validation | [Rules](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/00h-review-rules.png) · [Validation](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/00i-validation-progress.png) |
| Overview | [01-overview.png](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/01-overview.png) |
| Account / vendor / department analysis | [Account](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/02-financial-analysis-account.png) · [Vendor](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/03-financial-analysis-vendor.png) · [Department](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/04-financial-analysis-department.png) |
| Budget-vs-actual / reconciliation | [Budget vs Actual](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/05-financial-analysis-budget-vs-actual.png) · [Reconciliation](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/06-financial-analysis-reconciliation.png) |
| GED detail / transaction details | [GED](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/07-ged-detail.png) · [Transaction](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/07a-ged-transaction-details.png) |
| Findings / Explain This | [Findings](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/08-findings.png) · [Explain](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/09-explain-this-open.png) · [transactions/actions](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/09a-explain-transactions-and-actions.png) |
| Review Summary | [10-review-summary.png](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/light/10-review-summary.png) |

### 8.2 Dark mode

The matching dark-mode set is indexed at
[stage2/dark](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/dark/).
Representative captures:

- [Home](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/dark/00-home.png)
- [Upload complete](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/dark/00c-upload-complete.png)
- [Verify Budget](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/dark/00e-verify-budget.png)
- [Overview](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/dark/01-overview.png)
- [Financial Analysis](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/dark/05-financial-analysis-budget-vs-actual.png)
- [GED Detail](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/dark/07-ged-detail.png)
- [Findings](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/dark/08-findings.png)
- [Explain This](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/dark/09-explain-this-open.png)
- [Review Summary](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2/dark/10-review-summary.png)

These captures prove the current screens render coherently on the capture host.
They do not prove native screen-reader operation, 200% layout integrity,
keyboard order, Windows typography, or live Ollama success.

## 9. Historical screenshot evidence

| Screenshot set | Class | Count | Scope and limitation |
|---|---:|---:|---|
| [Workflow 1](../../verification/screenshots/workflow-01/) | H | 5 | Historical Review Management screens only. |
| [Workflow 2](../../verification/screenshots/workflow-02/) | H | 8 | Historical upload/extraction screens only. |
| [Integrated MVP light/dark](../../verification/screenshots/mvp-end-to-end/) | H | 96 | Earlier full journey before later remediation and Stage 1/2. |
| [Stage 1 financial correctness](../../verification/screenshots/stage-1-financial-correctness/) | H | 130 | Stage 1 hierarchy/evidence/financial views at that snapshot. |
| [Stage 2 standard viewport](../../verification/screenshots/stage2/) | H | 48 | Initial Stage 2 redesign. |
| [Stage 2 1100×720](../../verification/screenshots/stage2-responsive-1100x720/) | H | 48 | Focused responsive evidence; not 200% or all Windows DPI modes. |
| [Stage 2 follow-up](../../verification/screenshots/stage2-followup/) | H | 10 | Ask Fin/navigation/rules follow-up. |
| [Ask Fin simplified](../../verification/screenshots/ask-fin-simplified/) | H | 6 | Automatic-readiness/unavailable-state UX. |

## 10. Key current implementation evidence

### 10.1 Composition, review lifecycle and persistence

| Component | Implementation evidence | Tests/evidence |
|---|---|---|
| Application composition | [src/finsight/app.py](../../../../src/finsight/app.py) | `tests/application/test_composition.py`, `tests/ai/test_ai_composition.py`, launch smoke in the test inventory. |
| Review management | [application/review_management.py](../../../../src/finsight/application/review_management.py), [domain/review_management.py](../../../../src/finsight/domain/review_management.py) | `tests/application/test_review_management.py`, `tests/ui/test_review_management.py`, `tests/infrastructure/test_review_management_repository.py`. |
| Lifecycle/generations | [domain/lifecycle.py](../../../../src/finsight/domain/lifecycle.py), [application/transition_engine.py](../../../../src/finsight/application/transition_engine.py), [application/financial_review.py](../../../../src/finsight/application/financial_review.py) | Lifecycle, generation-lineage, crash-safety and migration tests listed in the test inventory. |
| Authoritative persistence | [infrastructure/persistence.py](../../../../src/finsight/infrastructure/persistence.py), [secure_store.py](../../../../src/finsight/infrastructure/secure_store.py), [financial_review_repository.py](../../../../src/finsight/infrastructure/financial_review_repository.py) | Infrastructure, migration, integrity and audit tests. |
| Audit | [infrastructure/audit.py](../../../../src/finsight/infrastructure/audit.py), [audit_stream.py](../../../../src/finsight/infrastructure/audit_stream.py) | `tests/test_audit.py`, `tests/infrastructure/test_audit_stream.py`, application logging tests. |
| Disposal/retention | [application/review_disposal.py](../../../../src/finsight/application/review_disposal.py), [infrastructure/review_disposal.py](../../../../src/finsight/infrastructure/review_disposal.py) | Application/UI disposal tests. |

### 10.2 Ingestion, extraction and reviewed data

| Component | Implementation evidence | Tests/evidence |
|---|---|---|
| Workbook safety | [infrastructure/workbook_safety.py](../../../../src/finsight/infrastructure/workbook_safety.py) | `tests/infrastructure/test_workbook_safety.py`. |
| Approved-layout extraction | [infrastructure/slv001_extractor.py](../../../../src/finsight/infrastructure/slv001_extractor.py), [application/source_intake.py](../../../../src/finsight/application/source_intake.py) | Extractor/source-intake tests and Workflow 2 evidence. |
| Source preservation/bindings | [infrastructure/files.py](../../../../src/finsight/infrastructure/files.py), [source_intake_repository.py](../../../../src/finsight/infrastructure/source_intake_repository.py) | Binding protection, reconstruction and source repository tests. |
| Review-local corrections | [application/reconstruction.py](../../../../src/finsight/application/reconstruction.py), [application/review_working_set.py](../../../../src/finsight/application/review_working_set.py), [infrastructure/source_intake_repository.py](../../../../src/finsight/infrastructure/source_intake_repository.py) | Reconstruction, working-set and verification-basis tests. |

### 10.3 Deterministic rule engine and recorded projections

| Component | Implementation evidence | Tests/evidence |
|---|---|---|
| Current V2 financial engine | [domain/financial_validation.py](../../../../src/finsight/domain/financial_validation.py) | `tests/unit/test_financial_validation.py`, `tests/application/test_financial_review.py`, independent oracle test. |
| Rule model/governance | [domain/rules.py](../../../../src/finsight/domain/rules.py), [application/rule_management.py](../../../../src/finsight/application/rule_management.py) | Rule, rule-management, protected-governance and workspace-upgrade tests. |
| Immutable run/result store | [infrastructure/financial_review_repository.py](../../../../src/finsight/infrastructure/financial_review_repository.py) and migrations [m0006–m0014](../../../../src/finsight/infrastructure/migrations/) | Migration, replay, audit and generation-lineage tests. |
| Read models | [application/read_models](../../../../src/finsight/application/read_models/) | `tests/integration/test_read_models.py`, dashboard and integrated financial-review tests. |
| Deterministic explanations | [domain/finding_explanations.py](../../../../src/finsight/domain/finding_explanations.py), [application/financial_review.py](../../../../src/finsight/application/financial_review.py) | `tests/application/test_finding_explanations.py`, findings workspace tests. |
| Legacy parallel validation path | [application/validation.py](../../../../src/finsight/application/validation.py), [application/pipeline.py](../../../../src/finsight/application/pipeline.py), [domain/findings.py](../../../../src/finsight/domain/findings.py) | Root/legacy tests. Presence alongside the V2 path is architecture/maintenance debt, not proof of a defect by itself. |

Current inspection identified these exact high-risk code locations:

- CORE-03 duplicate-copy exposure uses only `rows[1]` in
  [financial_validation.py lines 981–1028](../../../../src/finsight/domain/financial_validation.py).
- CORE-04 begins with the approved six GED fields, then adds Budget scopes and
  formula checks in
  [financial_validation.py lines 1030–1189](../../../../src/finsight/domain/financial_validation.py).
- The canonical account join and Decimal fields begin in
  [financial_validation.py lines 64–180](../../../../src/finsight/domain/financial_validation.py).

The [current test inventory](CONSOLIDATED-TEST-INVENTORY-2026-07-29.md)
documents direct probes for the duplicate-exposure, reporting-period and
overall-status issues. These probes are stronger current evidence than the
earlier oracle PASS for those exact semantics.

### 10.4 Desktop UX

| Component | Implementation evidence | Tests/evidence |
|---|---|---|
| Main shell/navigation | [delivery/desktop/main_window.py](../../../../src/finsight/delivery/desktop/main_window.py), [controllers/app_controller.py](../../../../src/finsight/delivery/desktop/controllers/app_controller.py) | Desktop, product-experience, global-back and walkthrough tests. |
| Home/review creation | [views/review_management_view.py](../../../../src/finsight/delivery/desktop/views/review_management_view.py) | Review-management and accessibility tests; current screenshots. |
| Upload/verify workflow | [views/source_intake_view.py](../../../../src/finsight/delivery/desktop/views/source_intake_view.py), [views/workflow_view.py](../../../../src/finsight/delivery/desktop/views/workflow_view.py) | Source-intake, working-set and accessibility tests. |
| Results experience | [views/financial_review_view.py](../../../../src/finsight/delivery/desktop/views/financial_review_view.py), [views/findings_view.py](../../../../src/finsight/delivery/desktop/views/findings_view.py) | Integrated-results/findings tests and current screenshots. |
| Rules Repository | [views/rules_repository_view.py](../../../../src/finsight/delivery/desktop/views/rules_repository_view.py) | Protected-governance and integrated-results tests. |
| Appearance/themes | [theme](../../../../src/finsight/delivery/desktop/theme/), [components/appearance_control.py](../../../../src/finsight/delivery/desktop/components/appearance_control.py) | Appearance tests; one current 200% clipping failure remains. |
| Charts | [components/charts.py](../../../../src/finsight/delivery/desktop/components/charts.py) | UI tests and screenshots. Financial aggregates must continue to come from recorded read models, not chart calculations. |

### 10.5 Ask Fin

| Control | Implementation evidence | Tests/evidence |
|---|---|---|
| Private service and authority boundary | [application/ai/private_ask_fin.py](../../../../src/finsight/application/ai/private_ask_fin.py), [private_contracts.py](../../../../src/finsight/application/ai/private_contracts.py) | Private Ask Fin unit/integration tests. |
| Grounding and review isolation | [application/ai/private_grounding.py](../../../../src/finsight/application/ai/private_grounding.py) | `tests/integration/test_private_ask_fin_v2_grounding.py`, Stage 2 tests. |
| Prompt/refusal boundary | [application/ai/private_prompt.py](../../../../src/finsight/application/ai/private_prompt.py) | Private Ask Fin prompt, decision-refusal and response-validation tests. |
| Loopback-only config | [infrastructure/ai/private_config.py](../../../../src/finsight/infrastructure/ai/private_config.py), [domain/ai/local_endpoint.py](../../../../src/finsight/domain/ai/local_endpoint.py) | Non-loopback/cloud-alias rejection tests. |
| Proxy/redirect/DNS/peer/model verification | [infrastructure/ai/providers/ollama.py](../../../../src/finsight/infrastructure/ai/providers/ollama.py) | Ollama provider, setup-status and Stage 2 security tests. |
| Local audit | [infrastructure/ai/private_audit.py](../../../../src/finsight/infrastructure/ai/private_audit.py) | Stage 2 audit and integration tests. |
| Composition and OS-actor authorization | [app.py lines 401–753](../../../../src/finsight/app.py) | AI composition, authorization and worker-thread tests. |
| Drawer and unavailable-state UX | [views/private_ask_fin_dialog.py](../../../../src/finsight/delivery/desktop/views/private_ask_fin_dialog.py) | Drawer/setup/accessibility tests and historical simplification screenshots. |

Implementation inspection plus the focused Stage 2 tests supports “local
Ollama only, no cloud fallback” for the application path. It does **not**
establish automatic runtime/model provisioning, redistribution rights,
hardware qualification, repair/update behavior, or clean-machine readiness.

## 11. Consolidated current test evidence

The authoritative closeout inventory is
[CONSOLIDATED-TEST-INVENTORY-2026-07-29.md](CONSOLIDATED-TEST-INVENTORY-2026-07-29.md).
Key test locations are:

| Test area | Exact locations |
|---|---|
| Financial engine/rules | [tests/unit/test_financial_validation.py](../../../../tests/unit/test_financial_validation.py), [tests/unit/test_rules.py](../../../../tests/unit/test_rules.py), [tests/application/test_financial_review.py](../../../../tests/application/test_financial_review.py), [tests/application/test_rule_management.py](../../../../tests/application/test_rule_management.py) |
| Oracle/read models | [tests/integration/test_stage1_financial_oracle.py](../../../../tests/integration/test_stage1_financial_oracle.py), [tests/integration/test_read_models.py](../../../../tests/integration/test_read_models.py) |
| Replay/history/lifecycle | [tests/application/test_generation_lineage.py](../../../../tests/application/test_generation_lineage.py), [test_lifecycle_integrity.py](../../../../tests/application/test_lifecycle_integrity.py), [test_transition_engine.py](../../../../tests/application/test_transition_engine.py), [tests/migrations](../../../../tests/migrations/) |
| Ingestion/extraction/safety | [tests/application/test_source_intake.py](../../../../tests/application/test_source_intake.py), [tests/infrastructure/test_slv001_extractor.py](../../../../tests/infrastructure/test_slv001_extractor.py), [test_workbook_safety.py](../../../../tests/infrastructure/test_workbook_safety.py) |
| Ask Fin/privacy | [tests/ai](../../../../tests/ai/), [private grounding integration test](../../../../tests/integration/test_private_ask_fin_v2_grounding.py) |
| UI/workflows | [tests/ui](../../../../tests/ui/) |
| Accessibility | [tests/accessibility](../../../../tests/accessibility/) |
| Security | [tests/security](../../../../tests/security/) |
| Architecture fitness | [tests/fitness](../../../../tests/fitness/), [.importlinter](../../../../.importlinter) |
| Determinism/golden/crash safety | [tests/determinism](../../../../tests/determinism/), [tests/golden](../../../../tests/golden/), [tests/crashsafety](../../../../tests/crashsafety/) |
| Launch entry point | [scripts/launch_mvp_demo.py](../../../../scripts/launch_mvp_demo.py) |

The root [test-results.txt](../../../../test-results.txt) is stale, narrow
historical output and must not be cited as the current regression result.

## 12. Packaging and deployment evidence

### 12.1 Normative plans

| Evidence | Class | What it establishes | Gap it does not close |
|---|---|---|---|
| [ADR-V2-004 Windows packaging](../../adr/ADR-V2-004-windows-packaging-and-support.md) | N | Intended Windows installer, identity, update/support and qualification architecture. | No built or tested Windows artifact. |
| [Application Architecture — packaging sections](../../docs/APPLICATION-ARCHITECTURE.md) | N | Separation of application, encrypted data, local AI runtime and release responsibilities. | Clean-machine evidence. |
| [Technical Implementation Plan](../../plans/TECHNICAL-IMPLEMENTATION-PLAN.md) | N | Planned Windows build/test/release tasks. | Completion. |
| [Dependency qualification](../../verification/DEPENDENCY-QUALIFICATION-2026-07-27.md) | H | Dependency analysis at architecture/workflow entry. | Current SBOM, current vulnerability scan, model licensing, or Windows smoke. |
| [Root distribution guide](../../../../docs/DISTRIBUTION.md) | H/N | Existing macOS/Python distribution approaches and operator commands. | One-click Windows installation. |
| [Build-readiness runbook](../../../../docs/12-build-readiness-runbook.md) | H | Earlier readiness procedure. | V2 runtime/model installer integration. |

### 12.2 Existing artifacts

| Artifact | Class | What it proves | What it does not prove |
|---|---|---|---|
| [dist/FinSight.app](../../../../dist/FinSight.app/) | H | A macOS application bundle was previously produced. | Current V2 content, signing/notarization, or Windows behavior. |
| [dist/FinSight.dmg](../../../../dist/FinSight.dmg) | H | A macOS disk image was previously produced. | Windows installer or current working-tree reproducibility. |
| [dist/FinSight/FinSight](../../../../dist/FinSight/FinSight) | H | A prior PyInstaller-style macOS executable exists. | Current release qualification. |
| [dist/finsight.pyz](../../../../dist/finsight.pyz) and [wheel](../../../../dist/finsight-1.0.0-py3-none-any.whl) | H | Python distribution experiments exist. | No-Python/no-terminal end-user experience. |
| [build/pyinstaller/finsight/FinSight.pkg](../../../../build/pyinstaller/finsight/FinSight.pkg) | H | macOS PyInstaller intermediate exists. | Signed installer, Windows artifact, update or repair. |
| [build/versions.json](../../../../build/versions.json), [build/validate_deps.py](../../../../build/validate_deps.py) | I/H | Dependency version/check tooling exists. | Complete SBOM or vulnerability/license approval. |
| [dependency validation workflow](../../../../.github/workflows/dependency-validation.yml) | I | CI definition for dependency checks. | Evidence that it ran against this uncommitted tree. |

No `.msi`, `.msix`, signed Windows `.exe` installer, Windows clean-machine
result, uninstall/repair result, or automated Ollama/model provisioning artifact
was found. Existing `dist/` content therefore does not satisfy the Windows
Packaging and Release gate.

## 13. Repository-state evidence

| Evidence | Class | Observation | Release implication |
|---|---|---|---|
| `git rev-parse HEAD` | C | `a298040a8408c04342818a65a186a0d72c87956a` | Identifies the last committed base, not the full reviewed state. |
| `git status --short` during collection | C | 29 modified and 135 untracked status entries before this index was added. | The actual product under review is not reproducible from HEAD alone. |
| [MVP remediation changed-file inventory](../../verification/MVP-FINAL-REMEDIATION-CHANGED-FILES-2026-07-28.md) | H | Exact historical remediation file list. | Omits later Stage 1/2 and closeout changes. |
| [Prechange inventory](../CONFIGURABLE-RULE-ENGINE-PRECHANGE-INVENTORY.md) | H | State before the V2 implementation evolution. | Current code or dependencies. |
| [Current test inventory](CONSOLIDATED-TEST-INVENTORY-2026-07-29.md) | C | Current test-file counts, commands and failures. | A release commit or signed artifact. |

A final stabilization stage must freeze a clean commit and regenerate exact
hashes, changed-file inventory, dependency lock/SBOM, test logs and build
provenance. This index should then be retained as the pre-stabilization
closeout record rather than silently rewritten.

## 14. External authoritative evidence

These references establish platform/runtime constraints used in the packaging
readiness assessment. They are **not** evidence that FinSight has fulfilled
them.

| External source | Class | Authoritative fact used | FinSight implication |
|---|---|---|---|
| [PyInstaller Manual](https://pyinstaller.org/en/stable/index.html) | E | PyInstaller is not a cross-compiler; a Windows application must be built on Windows. | Existing macOS artifacts cannot qualify the Windows release. |
| [Ollama on Windows](https://docs.ollama.com/windows) | E | Official installer, standalone CLI/service option, filesystem locations and registered uninstaller; binary install needs at least 4 GB and models require additional space that may reach tens/hundreds of GB. | A governed decision is still required for bundled vs. provisioned runtime, service lifecycle, storage, update, repair and uninstall. |
| [Ollama hardware support](https://docs.ollama.com/gpu) | E | GPU support depends on vendor/model/drivers; CPU fallback and platform-specific support exist but performance varies. | Target corporate-laptop qualification and supported-hardware matrix are mandatory. |
| [Ollama llama3.2 model page](https://ollama.com/library/llama3.2%3Alatest) | E | The selected family has explicit size/digest metadata and a Llama 3.2 Community License/AUP. | Legal must approve the exact model/version, redistribution and update mechanism; “available in Ollama” is not redistribution approval. |
| [Microsoft: MSIX signing overview](https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview) | E | Windows requires a deployable MSIX to be signed with a valid, trusted certificate; production signing and timestamping need an approved path. | Code-signing identity, certificate/service, key custody and timestamping are unresolved release dependencies. |
| [Microsoft: SignTool package signing](https://learn.microsoft.com/en-us/windows/msix/package/sign-app-package-using-signtool) | E | Shows signature verification prerequisites and signing mechanism. | CI signing and verification evidence must be produced on the Windows artifact. |
| [Microsoft: deploy MSIX with Intune](https://learn.microsoft.com/en-us/windows/msix/desktop/managing-your-msix-deployment-intune) | E | Signed MSIX packages can be assigned for install/uninstall through enterprise deployment. | Enterprise deployment is feasible but not implemented or piloted. |
| [Microsoft: What is MSIX?](https://learn.microsoft.com/en-us/windows/msix/overview) | E | Package manifest/signature support deployment, update and integrity behavior. | Installer format must be selected and tested; the architecture decision alone is insufficient. |

## 15. Evidence conflicts and closeout cautions

| Conflict/caution | Stronger evidence | Closeout treatment |
|---|---|---|
| Root `docs/` and `specs/` files differ. | Constitution says `specs/` is authoritative. | Treat `docs/` as historical/supporting only. |
| V2 requirement rows say `Draft`; package says Requirements complete. | Pinned-hash completion record plus independent recheck PASS. | Use package-level approval, but repair row-status/baseline documentation before release. |
| Earlier full/focused suites passed. | Current full run has 4 failures. | Full governed regression is not clean; packaging blocked. |
| Stage 1 oracle passes. | Current direct probes expose approved-contract gaps the oracle encodes or omits. | Correct code and strengthen the oracle; do not waive defects. |
| Historical screenshots look complete. | Current screenshots and current implementation/test inspection. | Use historical sets only for progression, not current acceptance. |
| Ask Fin focused simplification suite passed. | Current full suite includes an order-dependent Ask Fin drawer failure; runtime provisioning remains absent. | Stabilize tests and qualify deployment separately. |
| macOS `.app`/`.dmg` exist. | PyInstaller is not cross-platform and no Windows installer evidence exists. | No Windows packaging readiness. |
| “Local Ollama only” is implemented. | No clean-machine runtime/model provisioning, license decision or hardware matrix exists. | Security boundary is promising; deployment is incomplete. |
| Rule/result architecture says ledger is sole truth. | Current UI/read-model inspection and direct probes show status-policy and duplicated-path risks. | Reconcile before packaging and add tests at consumer boundaries. |

## 16. Minimum evidence required to supersede this index

The next governed stage should not claim packaging readiness until it produces:

1. a clean, reviewed release commit with an exact manifest;
2. corrected core-rule/status semantics and an independent oracle that detects
   those corrections;
3. a clean full regression on the frozen commit;
4. Windows-native build output and dependency/SBOM provenance;
5. signed installer plus clean-install, one-click launch, upgrade, repair and
   uninstall evidence;
6. automated Ollama/runtime/model provisioning with no terminal/manual service
   startup, or an explicitly approved alternative;
7. exact model license/redistribution approval and runtime/model version pins;
8. supported Windows hardware/latency/storage matrix;
9. local-only/network-boundary verification on the installed product;
10. native Windows keyboard, 200% zoom, contrast and screen-reader evidence;
11. large-workbook performance evidence against the approved NFR fixture;
12. final independent security/release review and Project Owner Final Product
    approval before the Windows Packaging and Release gate.

Until then, this index supports a **Stabilization and Regression** next-stage
recommendation and a **Not ready for packaging** decision.
