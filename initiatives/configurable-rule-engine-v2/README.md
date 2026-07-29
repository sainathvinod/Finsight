# FinSight Configurable Rule Engine V2 Initiative

## Purpose

This initiative evolves FinSight into a department-neutral, configurable financial validation platform centered on one deterministic, versioned rule engine.

The five protected baseline rules are the initial governed configuration. Additional optional and advisory rules will use the same engine, result contract, evidence model, versioning, audit history, reporting path, and historical replay mechanism.

For V1/MVP, the supplied Budget and GED reports and their agreed sample conventions are the business contract. Broader enterprise accounting semantics, duplicate normalization beyond those reports, additional layouts, and department-specific conventions are future governed, configurable extensions rather than MVP blockers.

After validation, the approved Stage 2 experience opens a decision-oriented
Overview derived entirely from recorded deterministic rule-engine results.
Review Summary remains a primary destination alongside Financial Analysis, GED
Detail, Findings, and Ask Fin.

## Relationship to FinSight

- This is the next evolution of the existing FinSight product.
- It remains one product, one repository, and one application.
- It will extend the existing codebase after requirements and architecture receive their required approvals.
- It does not create a sibling application, duplicate the full existing specification set, or replace the current Git history.
- Existing FinSight specifications under `/specs`, application code, tests, generated workbooks, and artifacts remain in place.
- Application Engineering is represented only by the supplied sample files. The product and rules apply to any department or business unit using compatible Budget and GED reports.

## Authority and stage

The Project Owner approved the Product Owner direction subject to the amendments recorded on 2026-07-27. Those amendments are incorporated in the initiative brief and source record.

Detailed V2 requirements are developed as a delta to the existing FinSight specifications. HD-27 conditionally authorizes Requirements completion after the clarifications are incorporated, internal consistency is confirmed, and an independent full review returns PASS. Architecture is authorized only after that gate; implementation additionally requires reviewed and approved Architecture, rule-engine, persistence, UX/UI, and technical-plan artifacts.

## Directory map

| Path | Purpose |
|---|---|
| `briefs/` | Product Owner direction and durable human-decision sources |
| `requirements/` | Requirements-stage navigation and clarification guidance |
| `specs/` | SDD-controlled V2 delta FR/NFR, decomposition, workbooks, reviews, and baselines |
| `reviews/` | Initiative-level and Product Owner independent-review records |
| `readiness/` | Pre-change inventories and later stage-readiness evidence |
| `docs/` | Approved workflow and other initiative-specific explanatory material |
| `adr/` | V2 architecture decisions after requirements approval |
| `plans/` | Approved implementation plans after architecture approval |
| `tasks/` | Traceable delivery tasks derived from approved plans |
| `verification/` | V2 verification records and release evidence |
| `fixtures/` | Approved V2 test-fixture references or initiative-owned fixtures |

## Approved product invariants

- The configurable deterministic rule engine is the heart of FinSight.
- Every financial validation result originates from that engine.
- Dashboards, analytics, reports, exports, KPIs, summaries, and Ask Fin consume recorded engine results rather than independently determining financial validity.
- The five baseline rules are protected from ordinary modification, disablement, or deletion but may evolve through a governed, versioned administrative workflow.
- Source Budget and GED files remain unchanged.
- AI may explain recorded results but never determines financial validation.
- A distributable Windows executable and installer remain required release outputs.
- The guided FinSight financial-review workflow is preserved.
- The supplied Budget/GED reference model defines deterministic V1 behavior without claiming to define organization-wide accounting policy.
- Overview, Review Summary, reports, exports, and Ask Fin consume the same
  recorded validation projections and do not independently recalculate
  validation logic.

## Current gate

As of 2026-07-29, the initiative is in
[Production-Readiness Stage 1 — Baseline Freeze and SDD Reconciliation](readiness/production-readiness/README.md).
The product and release decision are **NO-GO**. Financial stabilization,
later-stage implementation, packaging, and release are blocked until the Stage
1 decision package is independently reviewed and approved.

The history below records how the initiative reached this point. Historical
PASS records remain valid only for their named snapshots and do not override
the current closeout defects or production-readiness gate.

The Product Owner direction through HD-27 is incorporated, the clarification packet is closed, and FR-123–FR-203/NFR-081–NFR-110 received a fresh independent full PASS. The Requirements gate is complete.

The complete Architecture package passed independent review and received explicit Project Owner approval
on 2026-07-27:

- [Application Architecture](docs/APPLICATION-ARCHITECTURE.md)
- [Rule Engine Design](docs/RULE-ENGINE-DESIGN.md)
- [Persistence Model](docs/PERSISTENCE-MODEL.md)
- [UX/UI Design](docs/UX-UI-DESIGN.md)
- [Technical Implementation Plan](plans/TECHNICAL-IMPLEMENTATION-PLAN.md)
- [Proposed V2 ADR catalog](adr/README.md)
- [Frozen stage package and hashes](readiness/ARCHITECTURE-STAGE-PACKAGE-2026-07-27.md)
- [Independent Architecture review — PASS](reviews/REVIEW-2026-07-27-architecture-stage.md)
- [Project Owner Architecture approval](readiness/ARCHITECTURE-APPROVAL-2026-07-27.md)

Workflow 1 passed hands-on approval. The Project Owner then authorized Workflow 2 and,
after identifying cross-workflow journey fragmentation, explicitly authorized one
integrated increment to complete and align the remaining MVP primary journey. That
frozen 2026-07-27 increment passed its consolidated internal verification,
same-viewport design QA, and independent review:

- [Integrated MVP implementation plan](tasks/MVP-END-TO-END-IMPLEMENTATION-PLAN.md)
- [Integrated MVP verification and acceptance evidence](verification/MVP-END-TO-END-VERIFICATION-2026-07-27.md)
- [Independent integrated MVP review — PASS](reviews/REVIEW-2026-07-27-mvp-end-to-end.md)
- [Design QA — PASS](../../design-qa.md)

The Project Owner subsequently withheld final hands-on acceptance and directed a
material final MVP remediation covering the seven-step journey, Rules Repository,
editable-data presentation, evidence drilldown, deterministic analytics, review
disposal, polished financial visual design, and Light/Dark/System appearance modes.
That later scope supersedes the acceptance status, but not the historical evidence,
for the earlier frozen snapshot.

The consolidated remediation package is:

- [Remediation stage package and traceability](readiness/MVP-FINAL-REMEDIATION-STAGE-PACKAGE-2026-07-28.md)
- [Requirements delta](requirements/MVP-REMEDIATION-DELTA-2026-07-28.md)
- [Architecture delta](docs/MVP-REMEDIATION-ARCHITECTURE-2026-07-28.md)
- [Implementation plan](tasks/MVP-FINAL-REMEDIATION-IMPLEMENTATION-PLAN-2026-07-28.md)
- [Synthetic expected-versus-actual matrix](fixtures/MVP-REMEDIATION-SYNTHETIC-TEST-MATRIX-2026-07-28.md)
- [Verification record — historical PASS with native screen-reader limitation](verification/MVP-FINAL-REMEDIATION-VERIFICATION-2026-07-28.md)
- [Independent review record — historical PASS](reviews/REVIEW-2026-07-28-mvp-final-remediation.md)

The later Stage 1/Stage 2 implementation and closeout evidence supersede that
remediation-era gate state. Product Owner hands-on Final Product approval and
Windows Packaging/Release remain incomplete.

## Historical stage-based delivery

The initiative previously used five approval gates:

1. Requirements — complete;
2. Architecture — complete;
3. Workflow Phase Implementation — final MVP remediation in progress and pending verification/review;
4. Final Product;
5. Windows Packaging and Release.

That sequencing is historical. The 2026-07-29 Production-Readiness directive
supersedes it with nine sequential release stages. Architecture was completed
and reviewed as one package. The primary workflow
integrates Review Management, Upload & Extraction, Extraction Review, Rules
Repository review, Validation Engine, Results & Analytics, limited engine-bound Ask
Fin, and saved Review History without creating a second product or repository. The
current remediation is a delta within that approved architecture. Final-product
work outside this approved primary journey and all Windows packaging remain subject
to their existing gates.

### Execution lanes retained

Work within the new governed stages continues to use the
[FinSight Delivery Execution Lanes](plans/EXECUTION-LANES.md):

- **Governed Lane:** architecture, business logic, persistence, security,
  deterministic rules, data models, workflow semantics, dependencies, packaging,
  and governed specifications.
- **Rapid UX Lane:** presentation-only changes that leave those concerns and all
  user-task outcomes unchanged.

Rapid UX changes use only impacted UI, accessibility, and launch checks, include
screenshots, and stop for Project Owner hands-on review. They do not trigger the
full regression suite, unchanged-specification regeneration, or architecture and
governance re-review unless a material governed impact is discovered.
The lane cannot bypass a production-readiness stage gate.
