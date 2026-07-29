# FinSight Configurable Rule Engine — Product-Direction Source Record

- **Recorded:** 2026-07-27
- **Purpose:** Preserve durable traceability from the Product Owner brief to the human directives that govern this product evolution.
- **Status:** Source record only. It does not approve the Product Owner brief, detailed requirements, architecture, implementation, or release.
- **Related brief:** `IMPLEMENTATION-BRIEF-configurable-rule-engine-v2.md`

## Source authority

Later explicit human instructions supersede conflicting earlier instructions. The entries below record the operative decisions and distinguish the approved V1 sample-reference contract from future enterprise extensions and downstream design choices.

| Decision ID | Human decision | Operative direction |
|---|---|---|
| HD-01 | Same-product evolution | Keep this work in the existing FinSight ecosystem and repository as the next evolution of FinSight. Do not create or maintain a duplicate sibling product or duplicate the full specification-driven framework. Preserve everything built so far. This supersedes the earlier separate-project-directory direction in the attached project request. |
| HD-02 | Configurable engine is the product core | Design FinSight around a configurable deterministic rule engine, not five one-off checks. Adding rule 6, rule 20, or rule 100 must not require application redesign. |
| HD-03 | Three governed classifications | Distinguish core mandatory rules, optional configurable rules, and informational/advisory rules while running them through the same configurable, versioned engine. |
| HD-04 | Protected baseline governance | The five core rules cannot be modified, disabled, or deleted through normal user actions. A change requires a governed administrative workflow that creates a new version, preserves the original for historical replay, records the reason, and retains full audit history. |
| HD-05 | Single source of validation truth | Every FinSight financial validation result originates from the deterministic rule engine. Dashboards, analytics, reports, exports, KPIs, summaries, and future AI explanations consume rule-engine results rather than independently recalculating validation logic. |
| HD-06 | Baseline rule 1 | Actual spend must not exceed BGT for the same Department Number + Account Number. |
| HD-07 | Baseline rule 2 | Every GED transaction must map to a valid Budget Department Number + Account Number. |
| HD-08 | Baseline rule 3 | Exact duplicate GED transactions must be flagged using all material transaction fields, not Journal Number alone. |
| HD-09 | Baseline rule 4 | Required GED fields must be present and parseable: Department Number, Account Number, Fiscal Period, Journal Number, Journal Date, and Amount. |
| HD-10 | Baseline rule 5 | Budget ATD must equal the summed GED Amount for the same Department Number + Account Number. |
| HD-11 | Baseline availability and evidence | The five core rules are included by default, enabled in every new validation workspace, versioned and auditable, tested with positive/negative/boundary cases, represented in reports and analytics, and produce clear findings with source evidence. |
| HD-12 | Department-neutral product scope | The supplied Application Engineering reports are sample input data. FinSight must support any department or business unit using compatible Budget and GED structures, with the same validation rules regardless of department. |
| HD-13 | Automatic department identification | Extract and display Department Name and Department Number from uploaded reports whenever available. Detect inconsistent Budget/GED department identities before validation rather than asking users to enter metadata manually by default. |
| HD-14 | Reporting-period consistency | Extract available reporting-period evidence, compare it across the selected review period and uploaded files, and identify a mismatch before validation. |
| HD-15 | Preserve the FinSight review workflow | Retain the guided eleven-step experience from welcome and period selection through upload, metadata extraction, data review/correction, deterministic validation, results, analytics, Ask Fin, and saved past reviews. |
| HD-16 | V2 initiative organization | Keep V2-only artifacts under `initiatives/configurable-rule-engine-v2/`; preserve existing FinSight specifications and implementation in place and extend the same product/codebase. |
| HD-17 | Product Owner approval | After the audience, metadata, initiative-organization, and workflow amendments are incorporated, the Product Owner stage is approved and detailed requirements plus financial-semantic clarification may begin. |
| HD-18 | Preserved decisions | One product/repository/application, configurable deterministic engine, five protected baseline rules, additional configurable rules, engine-result single source, Windows installer, and AI-explains-only remain approved. |
| HD-19 | Supplied reports are the V1/MVP business contract | Use the supplied Budget and GED report structures and the previously agreed sample conventions as the reference model for the first release. Do not delay the MVP while defining organization-wide or production Amerisure accounting policy. Broader enterprise financial semantics, duplicate normalization beyond the supplied reports, additional layouts, and department-specific conventions are future governed, configurable extensions. Requirements must document the deterministic V1 interpretation clearly without presenting it as universal enterprise policy. |
| HD-20 | Review Summary is the first post-validation landing | After validation completes, show a Review Summary Dashboard before detailed findings. It displays Department Name, Department Number, Reporting Period, Overall Review Status, Budget Health, Data Quality, rules executed/passed/failed, Budget Overruns, Duplicate Transactions, Missing Required Data, Reconciliation Status, Top Findings, and Recommended Next Actions. Users can then navigate to Findings, Rule Results, Analytics, Reports, and Ask Fin. Every financial status, count, finding, and recommendation shown there is derived from recorded deterministic rule-engine results. |
| HD-21 | Three MVP roles | Use Reviewer, Rule Administrator, and Financial Control Approver for the MVP. Reviewer operates financial reviews; Rule Administrator governs configurable rules without making financial approval decisions; Financial Control Approver approves protected-baseline changes and governs their lifecycle. The authorization model must permit additional roles later without changing the rule engine. |
| HD-22 | Two-person protected-core governance | A protected-baseline change requires one authorized requester and a different authorized Financial Control Approver. Every request and decision is attributed, audited, versioned, and historically reproducible; a protected rule is never silently modified. |
| HD-23 | Replaceable actor identity | Use the authenticated Windows user account as the default MVP actor identity. Keep identity resolution outside the rule engine so Azure AD, Active Directory, SSO, or another enterprise provider can replace the MVP identity source later without changing deterministic rule behavior. |
| HD-24 | Review-local editing with three-value provenance | Permit a Reviewer to edit any extracted financial field, including BGT, ATD, GED Amount, department, account, dates, and descriptions. Source workbooks remain immutable. Validation uses the current reviewed Working Dataset. Every edit is visible, attributed, timestamped, audited, reversible, compared with the extracted original, retained in review history, and presented with an explicit original extracted value, user-reviewed value, and current validation value. |
| HD-25 | Review Summary identity block | The Review Summary must display Department Name, Department Number, Reporting Period, Validation Run ID, Rule Set Version, Review Version, Source File Names, and Validation Timestamp so reports, screenshots, exports, and Ask Fin responses identify the exact review context. |
| HD-26 | Review lifecycle | Use the review statuses Draft, Data Uploaded, Data Reviewed, Validation Complete, Reviewed, Closed, and Archived. Past-review browsing and lifecycle actions must use these states rather than an inferred complete/incomplete flag. |
| HD-27 | Requirements completion and architecture gate | Once these clarifications are incorporated, the requirements are internally consistent, and an independent requirements review returns PASS, the Requirements phase is complete and Architecture may begin. Application implementation remains prohibited until the architecture, rule-engine design, persistence model, UX/UI, and technical implementation plan are reviewed and approved. |

## Inherited project outcomes not superseded

The attached project request remains authoritative where later instructions did not replace it:

- **Source:** `New FinSight Project — Configurable Financial Validation Application I want to …`
- **Captured attachment:** `b9d7f7f4-7afe-4512-a9a1-6be6aa4736d9/pasted-text.txt`
- **SHA-256:** `e06d485e2695af3b3883fb2079143bc798a2943003866d013cf6cab07c9b3bd1`

| Source ID | Attachment lines | Inherited outcome |
|---|---:|---|
| AR-01 | 17–29, 124–169 | Users can govern controlled rule definitions and the platform is extensible beyond the initial five rules. Historical evidence retains the exact rule version used. |
| AR-02 | 350–410 | Requirements cover deterministic execution, rule governance, auditability, security, portability, installation, and release controls. |
| AR-03 | 604–633 | A distributable Windows executable and installer are mandatory product outputs. Release requires a Windows-compatible build, clean-machine installation and launch evidence, upgrade/uninstall behavior, integrity evidence, exact source provenance, and appropriate security/signing gates. Packaging technology remains an architecture decision. |
| AR-04 | 635–670 | Testing covers the rule engine, workbook layouts, exact decimals, the five core cases, versioning, reproducibility, audit, UI/accessibility, cross-platform behavior, packaging, clean machines, performance, and security. |

## Approved workflow source

- **Source:** `4. Preserve the FinSight review workflow The configurable-rule-engine evolution…`
- **Captured attachment:** `7874e21e-38bb-4a5f-8e0d-e0581a6300ff/pasted-text.txt`
- **SHA-256:** `b27870013c8147efd7ec26f7ecd36c1166d69b4459bec7974f59ca1b0788fa60`
- **Durable workflow record:** `../docs/FINANCIAL-REVIEW-WORKFLOW.md`

The workflow record assigns WF-01 through WF-11 to the approved steps so downstream requirements, UX, architecture, acceptance criteria, tests, and traceability can reference them without relying on chat history.

## V1/MVP reference-model boundary

HD-19 authorizes the Requirements stage to resolve first-release financial behavior from the supplied Budget and GED reports and the sample conventions already approved for those reports. Those documented V1 decisions are the business contract for the MVP; they are not claims about organization-wide Amerisure accounting policy.

The following topics are future governed, configurable extensions and do not block the MVP:

- production or organization-wide meanings that differ from the supplied Budget/GED reference model;
- transaction-eligibility policies for additional report layouts or accounting conventions;
- fuzzy, organization-specific, or event-specific duplicate normalization beyond the supplied GED structure;
- department-specific identifier, naming, period, or accounting conventions not represented by the supplied reports.

## Requirements resolutions and downstream approval boundaries

HD-21 through HD-27 close the remaining human role, identity, editing, protected-approval, review-identity, lifecycle, and Requirements-gate questions. The detailed requirements also apply bounded analyst resolutions anchored in the approved root specifications: controlled evaluator families, separate rule-version and workspace-binding lifecycles, legacy-rule preservation, new core IDs, seed severities, first-release exports, the inherited performance envelope, private/on-device AI only, and non-destructive retention.

Architecture and release governance still select the exact serialization/evaluator classes, export representation, resource ceilings beyond the inherited envelope, Windows matrix and packaging/signing mechanisms, authorization provisioning, identity adapter, storage/recovery mechanisms, error taxonomy, and approved private/on-device Ask Fin adapter. These implementation-specific choices may not weaken the Requirements contract and require their own reviews before implementation.
