# FinSight Production-Readiness Master Plan

**Version:** 1.0-stage-1-candidate
**Date:** 2026-07-29
**Status:** Pending Stage 1 approval
**Product:** FinSight
**Release state:** **NO-GO**

## 1. Objective

Deliver one financially correct, private, reliable, accessible, supportable
Windows desktop application that a supported user can install and use without
Python, Terminal, VS Code, manual Ollama installation, a manual model download,
environment-variable editing, or developer intervention.

FinSight shall:

- create and preserve monthly financial reviews;
- ingest the approved Budget and GED layouts without modifying the source files;
- expose original, reviewed, and current validation values;
- run only the exact confirmed deterministic Rule Set;
- preserve versioned rules, Rule Sets, runs, results, findings, evidence, audit,
  publication state, and history;
- explain every finding and navigate to its source evidence;
- provide deterministic leadership reporting and approved exports;
- keep Ask Fin local, grounded, cited, fail-closed, and non-authoritative; and
- install, launch, repair, upgrade, and uninstall through a supported Windows
  distribution.

FinSight shall never invent financial facts, substitute missing values silently,
make an approval or payment decision, hide incomplete validation, expose an
unsupported Ask Fin claim, send confidential financial data to a public or
unapproved AI service, fall back to cloud AI, or pass a release gate without its
mandatory evidence.

## 2. Governing sources

The program is directed by the two 2026-07-29 Product Owner sources recorded in
[the Governing Directive Record](STAGE-01-GOVERNING-DIRECTIVE-RECORD.md).
Their combined requirements supersede conflicting release sequencing and output
minimums, but do not silently resolve the protected Rule ID, CORE-04, Advisory,
recovery, layout, hardware, or local-runtime choices listed in the Stage 1
decision register.

The source hierarchy and frozen-snapshot rules are defined in
[Stage 1 Normative Source Hierarchy](STAGE-01-NORMATIVE-SOURCE-HIERARCHY.md).

## 3. Program controls

1. Stages execute in the order below.
2. A failed or incomplete gate stops progression.
3. Product policy is changed only through an approved successor requirement,
   ADR, migration, and traceability update.
4. An implementation agent cannot approve its own work.
5. Each stage requires planning, traceability, implementation where authorized,
   testing, independent review, evidence, and a human gate decision.
6. Tests and implementation verify the approved contract; they do not redefine it.
7. Historical evidence is immutable and remains labelled with its exact scope.
8. Every release claim identifies one immutable commit and exact artifacts.
9. The Governed Lane controls architecture, financial behavior, persistence,
   security, rules, workflows, packaging, and release.
10. The Rapid UX Lane may be used only inside an approved stage for purely visual
    corrections that preserve behavior. It cannot bypass that stage's gate.

## 4. Sequential stages

| Stage | Purpose | Current state | Required independent review | Gate authority |
|---|---|---|---|---|
| 1. Baseline Freeze and SDD Reconciliation | Preserve the current state, establish reproducible source, reconcile authority/status, and freeze decisions/scope. | **In progress — approval pending** | Requirements, Financial Control, repository/governance | Product Owner; Financial Control for protected controls |
| 2. Financial Correctness Stabilization | Correct protected identity/contract, status/RAG, summaries, duplicates, period eligibility, Decimal boundaries, and oracle. | **Blocked by Stage 1** | Financial Control and independent oracle | Product Owner and Financial Control |
| 3. Lifecycle, Architecture, and Persistence Stabilization | Correct successor publication, post-validation versions, obsolete paths, dependency direction, ordering, recovery, and migrations. | **Blocked** | Architecture and persistence | Architecture gate |
| 4. UX, Accessibility, and Reliability Stabilization | Fix current UI/accessibility defects without redesign; qualify native Windows accessibility. | **Blocked** | Accessibility and UX | Workflow stabilization gate |
| 5. Leadership Summary, Reports, Exports, and Recovery | Deliver deterministic summary, PDF/XLSX evidence outputs, audit appendix, and approved backup/restore. | **Blocked** | Finance, reporting/export, recovery/security | Output/recovery gate |
| 6. Ask Fin Production Hardening | Enforce verified claims, citations, refusal, injection resistance, managed identity, resource limits, and no egress. | **Blocked** | AI safety, privacy, security | Ask Fin safety gate |
| 7. Windows Packaging and Local-AI Provisioning | Produce signed executable/installer, automatically provision local AI, and implement lifecycle/provenance/licensing. | **Blocked** | Release engineering, security, legal/license | Windows Packaging and Release gate |
| 8. Clean-Machine and Enterprise Qualification | Qualify the exact signed candidate across Windows, users, hardware, connectivity, display, accessibility, lifecycle, data, performance, and security. | **Blocked** | Enterprise qualification panel | Qualification gate |
| 9. Final Product Validation and Release Authorization | Run every final gate against one immutable signed candidate and obtain hands-on and release approval. | **Blocked** | Independent final-product panel | Product Owner, Financial Control, Security, Release Authority |

## 5. Stage requirements

### Stage 1 — Baseline Freeze and SDD Reconciliation

Allowed work:

- external preservation archive and complete Git bundle;
- a controlled stabilization branch;
- exact file/source/artifact inventory and classification;
- baseline-only repository mechanics needed for reconstruction;
- normative-source and status overlays;
- production-readiness requirement delta and traceability;
- Product Owner/Financial Control decision packet;
- candidate first-release scope freeze; and
- independent reconciliation review.

Exit criteria:

- source/evidence snapshot hashes verified;
- clean, reviewable source commit candidate established;
- generated, temporary, accidental, obsolete, and confidential runtime artifacts
  excluded from release source without destroying preservation evidence;
- requirement/architecture status and source precedence reconciled;
- every Stage 1 decision has one approved option, rationale, actor, timestamp,
  and authority;
- protected identity and CORE-04 have different-person Financial Control
  approval where required;
- no ambiguity affects deterministic Stage 2 behavior;
- updated traceability and first-release scope are approved; and
- independent Requirements/Financial Control review and Product Owner gate PASS.

### Stage 2 — Financial Correctness Stabilization

Required outcomes:

- governed permanent protected Rule identity and migration;
- approved CORE-04 contract and any separate Budget-formula control;
- one persisted core-only Overall Status projector and exact RAG mapping;
- recorded downstream summary projections;
- exact duplicate-copy count/exposure for groups of 2, 3, 5, and more;
- approved reporting-period eligibility before CORE-01/CORE-05 aggregation;
- explicit Decimal/invalid-number boundary behavior;
- historical replay compatibility; and
- an independently rebuilt specification-derived oracle.

Exit requires no unresolved material financial defect and independent Financial
Control PASS.

### Stage 3 — Lifecycle, Architecture, and Persistence Stabilization

Required outcomes:

- Working/Unpublished successor creation and explicit Reviewer promotion;
- reason, audit, atomic publication pointer, rollback, and retained prior result;
- governed source/edit/extractor/rule-set successor behavior;
- one authoritative engine, result shell, and Ask Fin path;
- no delivery-to-infrastructure dependency;
- explicit immutable sequence/order rather than SQLite `rowid`; and
- migration, restart, corruption, partial-failure, rollback, and replay evidence.

### Stage 4 — UX, Accessibility, and Reliability Stabilization

Required outcomes:

- current 200% scaling, focus, and drawer-order failures fixed;
- 100/125/150/200% qualification;
- keyboard-only, focus restoration, high contrast, Light/Dark/System;
- long labels/text/evidence and unavailable/loading states;
- supported desktop sizes; and
- native Windows NVDA or approved screen-reader PASS.

No feature redesign or new analytics are authorized.

### Stage 5 — Leadership Summary, Reports, Exports, and Recovery

Required outcomes:

- one-page recorded-results-only Leadership Summary;
- selected-run PDF profiles with confirmation, publication label, full required
  content, limitations, evidence, and Audit History appendix;
- the specified multi-sheet XLSX evidence workbook;
- no report/export-side financial recalculation;
- confidentiality label, secure temporary workspace/destination, hashes, and
  exact run/rule/source metadata; and
- the approved encrypted backup/restore/disposal scope on a replacement
  environment.

### Stage 6 — Ask Fin Production Hardening

Required outcomes:

- closed verified claim protocol with valid selected-run citations;
- fail-closed unsupported-claim handling;
- direct/indirect financial-decision refusals;
- hostile workbook/prompt-injection isolation;
- administrator-controlled runtime binary/model digest, reverified per prompt;
- prompt/retrieval/output/response-byte/concurrency/memory/timeout/cancellation
  controls; and
- loopback-only, proxy/redirect-resistant, deployment-enforced no-cloud behavior
  proven by network capture.

### Stage 7 — Windows Packaging and Local-AI Provisioning

Required outcomes:

- exactly one approved automatic deployment topology;
- frozen Windows executable, signed installer, shortcuts, Start Menu entry, and
  uninstaller;
- automatic local runtime/model provisioning, health, verification, startup,
  repair, update, rollback, and uninstall;
- SQLCipher and migrations;
- Authenticode/timestamp, SBOM, notices, checksums, manifest, scans, provenance;
- approved redistribution and attribution; and
- a clean build from an immutable commit.

### Stage 8 — Clean-Machine and Enterprise Qualification

Required outcomes:

- the exact signed candidate passes the approved Windows/hardware/user/network/
  display/accessibility/lifecycle/data/performance/security matrix;
- automatic Ask Fin readiness without developer tools;
- financial results match the independent oracle;
- no confidential data egress or plaintext leakage; and
- install, repair, upgrade, rollback, uninstall, and replacement restore pass.

### Stage 9 — Final Product Validation and Release Authorization

Required outcomes:

- one immutable tagged signed candidate;
- full deterministic and order-varied regressions green;
- oracle, replay, Ask Fin adversarial/network, accessibility, Windows,
  performance, recovery, security, license, SBOM, scan, and artifact evidence;
- independent reviewer matrix PASS;
- Product Owner hands-on PASS;
- Financial Control, Security, and Release Authority approval.

The only permitted final decision is **GO — Production-ready release** or
**NO-GO — Release blocked**.

## 6. Required deliverable register

| Deliverable | Planned stage | Current status |
|---|---:|---|
| `PRODUCTION-READINESS-MASTER-PLAN.md` | 1 | Candidate produced |
| `CURRENT-GOVERNED-BASELINE.md` | 1 | Candidate produced |
| `UPDATED-REQUIREMENTS-TRACEABILITY-MATRIX.md` | 1 and maintained | Candidate produced |
| `FINANCIAL-CORRECTNESS-STABILIZATION-REPORT.md` | 2 | Not Started |
| `INDEPENDENT-FINANCIAL-ORACLE-REPORT.md` | 2 | Not Started |
| `RULE-IDENTITY-AND-MIGRATION-REPORT.md` | 2 | Not Started |
| `LIFECYCLE-AND-PUBLICATION-VERIFICATION.md` | 3 | Not Started |
| `ARCHITECTURE-STABILIZATION-REPORT.md` | 3 | Not Started |
| `ACCESSIBILITY-QUALIFICATION-REPORT.md` | 4 | Not Started |
| `LEADERSHIP-SUMMARY-AND-EXPORT-VERIFICATION.md` | 5 | Not Started |
| `BACKUP-RESTORE-AND-DISPOSAL-REPORT.md` | 5 | Not Started |
| `ASK-FIN-PRODUCTION-SAFETY-REPORT.md` | 6 | Not Started |
| `ASK-FIN-ADVERSARIAL-TEST-REPORT.md` | 6 | Not Started |
| `LOCAL-AI-NETWORK-BOUNDARY-REPORT.md` | 6 | Not Started |
| `WINDOWS-PACKAGING-ARCHITECTURE-DECISION.md` | 7 | Not Started |
| `WINDOWS-CLEAN-MACHINE-QUALIFICATION.md` | 8 | Not Started |
| `INSTALL-UPGRADE-REPAIR-UNINSTALL-REPORT.md` | 8 | Not Started |
| `PERFORMANCE-QUALIFICATION-REPORT.md` | 8 | Not Started |
| `SBOM.json` or approved equivalent | 7/9 | Not Started |
| `THIRD-PARTY-NOTICES.md` | 7/9 | Not Started |
| `RELEASE-MANIFEST.json` | 9 | Not Started |
| `FINAL-PRODUCT-VERIFICATION.md` | 9 | Not Started |
| `INDEPENDENT-FINAL-REVIEW.md` | 9 | Not Started |
| `ONE-PAGE-MANAGER-RELEASE-SUMMARY.md` | 9 | Not Started |
| Exact changed-file and artifact inventory | Every stage | Stage 1 candidate in progress |

Each final report must record the exact commit, artifact hashes, versions, test
commands/results/skips, limitations, reviewer, review scope, and approval state.

## 7. Release rule

The program remains **NO-GO** until all nine stages have passed. Packaging may
not begin before Stages 1 through 6 pass. A raw executable, source ZIP, unsigned
artifact, manual Ollama prerequisite, or developer-assisted launch is not a
release.
