# FinSight Configurable Rule Engine V2 — Specification Constitution

- **Status:** Inherits the adopted FinSight Constitution; V2 direction is human-approved through HD-01–HD-27
- **Purpose:** Provide the local SDD authority and terminology needed to draft V2 delta requirements without duplicating or silently rewriting the existing FinSight specification set.
- **Parent authority:** `../../../specs/constitution.md`
- **Product Owner baseline:** `../briefs/IMPLEMENTATION-BRIEF-configurable-rule-engine-v2.md`
- **Decision sources:** `../briefs/PRODUCT-DIRECTION-SOURCE-configurable-rule-engine-v2.md`
- **Approved workflow:** `../docs/FINANCIAL-REVIEW-WORKFLOW.md`
- **Governed V2 delta:** `../requirements/GOVERNED-V2-DELTA-2026-07-27.md`

## 1. Inheritance and precedence

This initiative is part of the existing FinSight product. Every principle, decision right, quality bar, and glossary term in the parent FinSight Constitution remains in force unless an explicit, later human decision in HD-01 through HD-27 defines a V2 delta.

The initiative's `specs/` directory contains only V2 delta specifications. It does not copy the full parent specification set. Requirements cite existing approved FinSight IDs where behavior is reused and create new IDs only for added or changed V2 behavior.

No V2 artifact changes a root specification in place. After V2 requirements complete clarification, row-level approval, and baselining, their integration into the product-wide specification set must follow the governed change process.

## 2. Binding V2 principles

1. FinSight remains one product, repository, application, and codebase.
2. The product supports any single department or business unit represented by compatible Budget and GED reports; the supplied department is sample data only.
3. The same validation rules apply regardless of department.
4. The deterministic, versioned configurable rule engine is the sole source of financial validation truth.
5. Core mandatory, optional configurable, and informational/advisory rules use the same engine and result contract.
6. The five named core rules are protected baseline controls and evolve only through governed, versioned administrative change.
7. Dashboards, analytics, reports, exports, KPIs, summaries, and Ask Fin consume recorded rule results rather than independently deciding financial validity.
8. AI explains recorded results but never creates or changes financial values, rule outcomes, findings, severity, approvals, or financial actions.
9. Source Budget and GED files remain unchanged; corrections are review-local, additive, confirmed, and auditable.
10. The eleven-step workflow WF-01 through WF-11 is the V2 Guided Review Wizard. It refines the parent constitution's earlier eight-step count without removing the Monthly Review in a Box principle.
11. A distributable Windows executable and installer remain mandatory release outputs. This added Windows gate does not waive the parent NFR-028/NFR-029 macOS parity and deterministic-equivalence obligations.
12. The supplied Budget/GED structures and agreed sample conventions are the V1 financial contract; broader enterprise accounting policy and department-specific conventions are future configurable extensions rather than MVP stop gates.
13. The Review Summary is the first post-validation view and derives every validation conclusion from recorded rule-engine results.
14. The MVP uses Reviewer, Rule Administrator, and Financial Control Approver roles through a versioned authorization model that can add roles without changing the rule engine. Multiple active role assignments combine by permission union, except that an explicit separation-of-duties denial always takes precedence.
15. A Rule Administrator may author and test a protected successor, but a protected-baseline change requires that administrator's request and approval by a different Financial Control Approver; activation creates a new immutable Protected Baseline Version and preserves replayable history. Applying an approved protected baseline to an existing workspace also requires Financial Control Approver authorization and a successor workspace Rule Set Version.
16. The authenticated Windows account supplies the default MVP actor identity through a replaceable identity boundary.
17. Every editable extracted financial field visibly retains Original Extracted Value, User-Reviewed Value, and Current Validation Value. Draft and Data Uploaded work belongs to a mutable Working Candidate. Confirmation creates and seals a Review Version/ReviewGeneration at `Data Reviewed`; the complete Current Validation Value projection is reconstructed under inherited ADR-012 and is the V2 realization of the inherited `VerifiedDataset` input contract.
18. Review Lifecycle Status follows Draft → Data Uploaded on a Working Candidate and Data Reviewed → Validation Complete → Reviewed → Closed → Archived on its resulting Review Version. It is distinct from deterministic Overall Review Status and from the generation's analytical and publication states.
19. Every Review Summary, report, export, screenshot context, and review-specific Ask Fin response identifies its Department, Period, Validation Run, Rule Set Version, Review Version/ReviewGeneration, publication state, source files, and validation timestamp.
20. Architecture, rule-engine design, persistence, UX/UI, and the technical implementation plan require review and approval before application implementation begins.
21. The V2 Overall Review Status maps one-to-one to the inherited RAG presentation: `Healthy` = `On Track (Green)`, `Attention Required` = `Needs Attention (Yellow)`, and `Incomplete` = `At Risk (Red)`.
22. Reports, exports, and Ask Fin responses created after a Review Version is sealed are separately audited derived artifacts linked to that immutable Review Version and its Validation Run; they never mutate authoritative generation or review history.
23. Ordinary review actions never erase retained evidence. The separately initiated, explicitly confirmed whole-scope disposal promised by parent NFR-017 may remove a Review Cycle, a period, or all stored data and leaves only the content-free deletion audit record required by that inherited policy.
24. Every ReviewCycle distinguishes a working Review Version from its published trusted Review Version. New successor results never replace trusted dashboard, analytics, report, export, or Ask Fin defaults until the inherited explicit-promotion contract succeeds.

## 3. Decision rights

The parent Constitution's human decision rights remain unchanged.

- The Project Owner approves scope and requirement decisions.
- Financial Domain and Financial Control owners decide production financial semantics, rule parameters, and control policy.
- Reviewers govern review-local source inspection, correction, validation, findings review, reporting, and lifecycle actions permitted by the requirements.
- Rule Administrators govern the runtime lifecycle of Optional Configurable and Informational/Advisory rules and may author, test, and request activation of protected successors, but do not make financial approval decisions or amend product specifications and the approved legacy catalog.
- Financial Control Approvers decide protected-baseline requests made by a different actor and authorize an approved protected baseline's application to an existing workspace.
- Product-specification and legacy-catalog changes remain governed by the Project Owner and the parent Constitution's change process; runtime rule administration is not authority to rewrite those artifacts.
- Security/Governance owners decide role provisioning, enterprise identity, and authorization deployment policy.
- The Technical Lead/Architect decides architecture only after requirements approval.
- AI agents draft and review but do not approve.

## 4. V2 glossary

| Term | Definition |
|---|---|
| **Validation Workspace** | The active FinSight ReviewCycle for one selected reporting month/year and one resolved department or business unit, containing source bindings, its current Working Candidate or working Review Version, published Review Version, rule configuration, results, findings, derived artifacts, and audit evidence. |
| **Compatible Budget Report** | A workbook whose approved V2 reader can identify the required real-layout Budget structure, detail rows, financial fields, source lineage, and available department/period evidence. Exact layout acceptance belongs to the detailed requirements. |
| **Compatible GED Report** | A workbook whose approved V2 reader can identify the required real-layout GED structure, transaction rows, financial fields, source lineage, and available department/period evidence. Exact layout acceptance belongs to the detailed requirements. |
| **Department Identity** | The resolved Department Number plus the Department Name retained for display/evidence. V1 normalization and source precedence follow the supplied-report contract; broader conventions require a future versioned extension. |
| **Reporting-Period Evidence** | A source value that identifies the report's applicable month/year. V1 uses the selected workspace period and GED title period under the supplied-report contract; run date and transaction maxima are not substitutes. |
| **Actor** | An authenticated person represented by a stable, provider-qualified Actor ID. The MVP derives it from the Windows account; later identity providers map to the same contract. |
| **Role** | A versioned set of permitted application actions assigned to an Actor independently of deterministic rule logic. Multiple active assignments combine by permission union; an explicit separation-of-duties denial overrides an allow. |
| **Working Candidate** | Mutable pre-confirmation work owned by a ReviewCycle. It has `Draft` or `Data Uploaded` Review Status, source bindings, extractor/correction state, and a reconstructed Working Dataset, but is not yet a Review Version or ReviewGeneration. |
| **Working Dataset** | The reconstructed normalized Budget/GED rows plus replayed review-local corrections for one Working Candidate. Its original, pending/reviewed, and prospective validation values and source lineage remain available in the active process, but the complete row store is not persisted. |
| **Original Extracted Value** | The immutable normalized value and raw-cell lineage created from the uploaded source. |
| **User-Reviewed Value** | The latest saved review-local replacement, visibly Pending confirmation or Confirmed. |
| **Current Validation Value** | The immutable value used by one Review Version's Validation Run: the confirmed reviewed value when one exists, otherwise the original extracted value. It is reconstructed from a matching source/extractor basis plus persisted correction and confirmation records. |
| **VerifiedDataset (V2 realization)** | The complete reconstructed Current Validation Value projection and lineage of one sealed Review Version/ReviewGeneration. It is established by explicit Reviewer confirmation or inherited without change by a `RULESET_REANALYSIS`/`CONFIG_REANALYSIS`, verified against its recorded fingerprint, and is the only V2 data object accepted by the deterministic Rules Engine. |
| **Rule Definition** | A controlled, versioned declaration of deterministic inputs, parameters, matching/aggregation behavior, result behavior, evidence, and lifecycle metadata. It is not arbitrary executable code. |
| **Core Mandatory Rule** | One of the five protected baseline controls enabled in every new workspace and unavailable to ordinary modification, disablement, or deletion. |
| **Optional Configurable Rule** | A controlled rule that authorized users may govern through the ordinary versioned lifecycle. |
| **Informational/Advisory Rule** | A controlled rule that records an evidence-backed observation and is visibly distinct from a financial-control failure. |
| **Rule Result Ledger** | The ordered, persisted record of every selected rule-and-scope deterministic PASS, FAIL, NOT_EVALUATED, or permitted advisory OBSERVATION or NO_OBSERVATION outcome and its rule/input/configuration/evidence provenance. |
| **Protected Baseline Version** | An immutable globally effective manifest containing exactly one governed rule/configuration version for each of the five protected Rule IDs, their severity/status-policy versions, and effective timestamp. Global protected activation creates this object; it does not create or rewrite a workspace Rule Set Version. |
| **Rule Set Version** | The user-facing name for an immutable workspace-scoped ordered manifest of the exact Protected Baseline Version and selected rule, configuration, binding, classification, enabled-state, and status-policy versions. A Validation Run pins one existing Rule Set Version; multiple runs may reference it while that workspace configuration is unchanged. |
| **Review Version / ReviewGeneration** | The user-facing Review Version is the identity of exactly one inherited immutable ReviewGeneration with the same positive sequence number. It begins only at verification (`Data Reviewed`/`VERIFIED`), permits zero authoritative runs before validation and exactly one thereafter, and is never a Draft or Data Uploaded candidate. |
| **Working Review Version** | The latest explicitly initiated Review Version/ReviewGeneration for a ReviewCycle. It may be in progress or completed and may differ from the published version. |
| **Published Review Version** | The Review Version/ReviewGeneration selected by the inherited promotion contract as the default trusted result for dashboards, analytics, reports, exports, and Ask Fin. |
| **Validation Run** | The one authoritative deterministic execution owned by a Review Version/ReviewGeneration and bound to its immutable verified basis, Rule Set Version, initiating Actor, timestamps, and complete result ledger. |
| **Review Lifecycle Status** | Operational workflow state: `Draft` and `Data Uploaded` apply to a Working Candidate; `Data Reviewed`, `Validation Complete`, `Reviewed`, `Closed`, and `Archived` apply to a Review Version. It is not a pass/fail financial conclusion, a generation analytical state, or a publication state. |
| **Review Disposition** | The inherited orthogonal ReviewCycle state `Active` or `Abandoned`. It changes only by explicit audited abandon/resume action and never changes Review Status, analytical state, verification, results, publication, or retention by itself. |
| **Overall Review Status** | The deterministic V2 financial-validation conclusion: `Healthy`, `Attention Required`, or `Incomplete`, derived only from the selected run's persisted core-rule results. |
| **RAG status** | The accessible inherited presentation of Overall Review Status: `Healthy` maps to `On Track (Green)`, `Attention Required` maps to `Needs Attention (Yellow)`, and `Incomplete` maps to `At Risk (Red)`. It is not a separate calculation. |
| **Derived Review Artifact** | A report, export, or Ask Fin response generated as an append-only record linked to a sealed Review Version and Validation Run, with its own actor, generation timestamp, and outcome; it is not part of and cannot mutate the sealed snapshot. |
| **Review Summary** | The first post-validation view, containing exact review/run identity, deterministic review health, rule counts, exception counts, top findings, recommended human actions, and drill-down navigation for one recorded Validation Run. |
| **Finding** | The evidence-backed exception record created from a failed control result; a finding never substitutes for the complete rule-result ledger. |
| **Protected Baseline** | The five mandatory rule definitions and governance status loaded into every new workspace, with changes possible only by governed administrative versioning and full audit history. |

## 5. Requirements-stage boundary

Before the independent Requirements review passes, this stage may create Draft FR/NFR delta registers, audit reports, and clarification records. It may not:

- mark the Requirements phase complete unless the HD-27 conditions are satisfied and the independent review returns PASS;
- invent or override a human financial or governance decision;
- decompose while blocking clarification questions remain;
- create code, tests, packages, or production-readiness claims;
- alter root specifications, source code, tests, generated workbooks, or existing artifacts.

After those conditions pass, Architecture may begin. Application implementation remains prohibited until the Architecture, rule-engine design, persistence model, UX/UI, and technical implementation plan have each been reviewed and approved.
