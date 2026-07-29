# Stage 1 Normative Source Hierarchy and Baseline Status Overlay

**Initiative:** FinSight Configurable Rule Engine V2<br>
**Program:** Production-Readiness and Governed Release Program<br>
**Stage:** 1 — Baseline Freeze and SDD Reconciliation<br>
**Document type:** Additive governance/status overlay; no historical artifact is rewritten<br>
**Status:** Pending Stage 1 Product Owner approval<br>
**Prepared:** 2026-07-29<br>
**Implementation authorization:** None. Stages 2–9 remain blocked.

## 1. Purpose

This document reconciles which FinSight artifacts are authoritative, approved, historical, superseded in part, or still awaiting a governed decision. It does not change production behavior and does not silently promote a `Draft` or `Proposed` document.

The repository contains valid evidence from several generations of the same FinSight product. A package-level approval sometimes froze an exact file while the file's own header still said `Draft` or an ADR still said `Proposed`. Rewriting those reviewed files would invalidate their recorded hashes. This overlay therefore records the effective status while preserving the reviewed bytes and history.

## 2. New governing-source fingerprints

The two Product Owner sources initiating this production-readiness program are preserved outside the repository attachment area and identified here by exact content hash:

| Source | Attachment path | SHA-256 | Stage 1 treatment |
|---|---|---|---|
| FinSight Production-Readiness and Governed Release Program | `/Users/lakshminarayanana/.codex/attachments/8a5a1e10-6c8a-44d0-932f-b9af580ec704/pasted-text.txt` | `6653b87ba7d23fa83bba14450f1abb69479661e9550c03ef9b1154e16998bc53` | Current Product Owner direction governing stage order, release objective, and Stage 1 decisions. Pending incorporation into the approved baseline through this Stage 1 gate. |
| Section 15 — Enterprise Rule Governance, Complete Reporting, Audit History, and Final Distribution | `/Users/lakshminarayanana/.codex/attachments/816cbd88-afc7-4714-b051-3a9dc7c3abc8/pasted-text.txt` | `1275c7dee199b1f08d76a7bdcedb1185b645e04039f0a16d417a6ac05accf92d` | Current Product Owner requirements delta. Proposed successor requirements are enumerated in `PRODUCTION-READINESS-REQUIREMENTS-DELTA.md`; each remains Pending Stage 1 approval. |

Hash verification command:

```text
shasum -a 256 <source-file>
```

## 3. Normative precedence

When two artifacts conflict, use the first applicable level below. A lower-level artifact cannot override a higher-level source merely because it is newer or implemented.

| Rank | Authority | Effective treatment |
|---:|---|---|
| 1 | [Root FinSight Constitution](../../../../specs/constitution.md), including its amendment and precedence rules | Highest existing repository authority until amended through its governed process. |
| 2 | Explicit, current Product Owner decisions recorded in an approved gate package | May amend or supersede lower-level requirements within the approved scope. The two sources fingerprinted in §2 direct Stage 1 work now; their proposed baseline changes become fully adopted when the Stage 1 gate records approval and required financial-control decisions. |
| 3 | Approved root specifications under [`/specs`](../../../../specs/) | Existing product baseline. The baseline approval checklist was not fully sealed, so the exact release baseline still requires Stage 1 freeze evidence. |
| 4 | V2 Requirements package accepted by the Requirements gate | Functional and non-functional files are authoritative at their accepted hashes even though their internal headers retain `Draft`. Package approval is the effective status; the stale header is preserved as historical metadata. |
| 5 | V2 Architecture package accepted by the Architecture gate | Architecture, plan, and ADR files are authoritative at their accepted hashes even though document headers retain `Draft` or `Proposed`. The acceptance package controls their effective status. |
| 6 | Approved execution-lane and workflow/stage directions | Governs how authorized work is performed. The nine-stage production-readiness sequence supersedes the earlier five-gate sequence for release stabilization once Stage 1 is approved; it does not erase earlier workflow evidence. |
| 7 | Verification, independent-review, closeout, screenshot, test, and oracle evidence | Proves or disproves claims about a particular source state. Evidence does not itself change a requirement. A PASS for a report package is not a PASS for the product. |
| 8 | Root [`/docs`](../../../../docs/) and obsolete Release 1 or walking-skeleton artifacts | Historical or explanatory reference unless an approved requirement explicitly incorporates a statement. These artifacts do not override `/specs`, V2 packages, or current Product Owner decisions. |
| 9 | Implementation, tests, generated artifacts, and current UI behavior | Evidence of what exists, not authority to change business policy. Implementation convenience never resolves a requirement conflict. |

### 3.1 Tie-breaking rules

1. A current explicit Product Owner decision wins over an older product direction only within the decision's stated scope.
2. Financial-control semantics, protected-rule identity, protected-rule replacement, retention, and publication require the designated approval authority in addition to Product Owner approval where the baseline requires it.
3. An exact reviewed hash wins over a mutable working copy for claims about what was approved.
4. A later verification report supersedes an earlier verification status only for the source state and tests it actually evaluated.
5. A focused Rapid UX test run cannot establish governed full-regression or release readiness.
6. Missing evidence is not a PASS, and an unresolved policy choice is not an implementation default.

## 4. Accepted baseline fingerprints

The exact snapshots below remain the approval identities. This overlay does not alter any of them. A current-workspace hash check performed on 2026-07-29 matched every listed Requirements, Architecture, and ADR file except the Technical Implementation Plan; that divergence is called out explicitly rather than silently treating the current bytes as approved.

### 4.1 Requirements package

| Artifact | Accepted SHA-256 | Effective status |
|---|---|---|
| [V2 Functional Requirements](../../specs/01-functional-requirements.md) | `0fe666b42290d6c12ac679a787f347155f8d2eb2fd6b03ab0957164984eb3297` | Requirements-gate accepted; internal `Draft` label retained as frozen historical metadata. |
| [V2 Non-Functional Requirements](../../specs/02-non-functional-requirements.md) | `a49212a6c2bd9bd185831d4422d99018e99629afc4dd2c51ab622d8c52ce9a8b` | Requirements-gate accepted; internal `Draft` label retained as frozen historical metadata. |

The approval evidence is [Requirements Phase Completion](../../requirements/REQUIREMENTS-PHASE-COMPLETION-2026-07-27.md) and the hashes repeated in the [Architecture Stage Package](../ARCHITECTURE-STAGE-PACKAGE-2026-07-27.md). If a local link moves, the hashes above remain the identity of the accepted files.

### 4.2 Architecture package

| Artifact | Accepted SHA-256 | Effective status |
|---|---|---|
| [Application Architecture](../../docs/APPLICATION-ARCHITECTURE.md) | `996a05a014514e08260c3511513f72446f7800a66b806d7f201cbab2afd17b7e` | Architecture-gate accepted; internal `Draft` label retained. |
| [Configurable Rule Engine Design](../../docs/RULE-ENGINE-DESIGN.md) | `0aa9faf5a5485e6ca38a8002d74053688dc75ef8ba2da930bccb619b7ccb604d` | Architecture-gate accepted; internal `Draft` label retained. |
| [Persistence Model](../../docs/PERSISTENCE-MODEL.md) | `6ce833bc8c21dd42ba6a86099bd6a7bf1153cd3a2a0fd942f72291cdb394c14a` | Architecture-gate accepted; internal `Draft` label retained. |
| [UX/UI Design](../../docs/UX-UI-DESIGN.md) | `e5805a8ec48f3dc16ac4d493b327ce86b34c5881490e48f285a6ecf8d2dc9264` | Architecture-gate accepted; internal `Draft` label retained. |
| [Technical Implementation Plan](../../plans/TECHNICAL-IMPLEMENTATION-PLAN.md) | `93bca498e0e2a4605a1a778548640debccea1485a68e5bc3e4401a074cb68845` | Architecture-gate accepted snapshot. The current workspace file hashes to `8df4ae8e0f94995f010c0203465c777c0d14326d5ec6b72aab38f0e5eb9ad477` and is therefore **not byte-equivalent to the accepted snapshot**. Its current additions must be classified and either approved as a successor or separated before the clean baseline is frozen. The old five-gate sequence is superseded for this release program only. |
| [ADR-V2-001](../../adr/ADR-V2-001-configurable-deterministic-rule-engine.md) | `f1d548ad2886122f7ee62c7c5bd913b5814702f31e3d3825b5a07ba323a433e6` | Architecture-gate accepted; `Proposed` metadata retained. |
| [ADR-V2-002](../../adr/ADR-V2-002-sequential-multi-actor-local-governance.md) | `f2648307d6394e01813cf5bbe55cb7caff7a70c33077130b4187b916a09f7bcb` | Architecture-gate accepted; `Proposed` metadata retained. |
| [ADR-V2-003](../../adr/ADR-V2-003-encrypted-authoritative-persistence-and-recovery.md) | `5ca87f8e5f5a0dd975117c9ec2acc952317e57473ad1843b8fb7110a5f7c2020` | Architecture-gate accepted; `Proposed` metadata retained. |
| [ADR-V2-004](../../adr/ADR-V2-004-windows-packaging-and-support.md) | `01620967465b211623f806a7aa894ead702b6af954d729705ae89601489a0812` | Architecture-gate accepted; `Proposed` metadata retained. |
| [ADR-V2-005](../../adr/ADR-V2-005-private-engine-bound-ai.md) | `2c1fa98e3548e9d8643b283e14b60d16fd954ea27a12c816e05b39625ab46736` | Architecture-gate accepted, subject to the current local-only/no-cloud production-readiness delta. |
| [ADR-V2-006](../../adr/ADR-V2-006-slv001-workbook-safety-profile.md) | `0e8388db98260b450836a9de8049396b53b7289ddd52c5fd8c48cb2fcc22fde4` | Architecture-gate accepted. |
| [ADR-V2-007](../../adr/ADR-V2-007-ledger-consumers-and-derived-records.md) | `f9b7cc45cb2d0d54f26c05e9d79dab68c4224020ad1f66aae53c483010acf5f8` | Architecture-gate accepted. |

The authoritative acceptance record is the [Architecture Stage Package](../ARCHITECTURE-STAGE-PACKAGE-2026-07-27.md) and its recorded Project Owner approval.

Current-workspace verification found matching accepted hashes for both V2 Requirements files, all four Architecture design files, and ADR-V2-001 through ADR-V2-007. The Technical Implementation Plan mismatch is a Stage 1 baseline-classification item, not an approval failure retroactively applied to the accepted historical snapshot.

## 5. Status overlay register

| Artifact or family | Embedded/current label | Effective Stage 1 status | Required action |
|---|---|---|---|
| Root `/specs` | Approved baseline | **Approved working baseline; not yet reproducibly sealed for release** | Preserve; create clean starting commit, inventory, and release-baseline manifest before Stage 1 exits. |
| Root `/docs` | Mixed historical descriptions | **Historical reference** | Do not use to override `/specs`; identify obsolete Release 1 material during source classification. |
| V2 functional and non-functional requirements | `Draft` | **Accepted requirements snapshot at hashes in §4.1** | Preserve bytes; apply this additive successor delta after Stage 1 approval. |
| V2 architecture, persistence, UX, rule-engine, and plan files | `Draft` | **Accepted architecture snapshot at hashes in §4.2** | Preserve bytes; create later architecture deltas only for approved production-readiness changes. |
| ADR-V2-001 through ADR-V2-007 | `Proposed` | **Accepted as part of the approved Architecture package** | Preserve bytes; use successor ADRs or status overlays for changed decisions. |
| [Execution Lanes](../../plans/EXECUTION-LANES.md) | Approved | **Approved and current** | Continue Governed Lane for semantics, persistence, security, packaging, and release; Rapid UX remains limited to presentation-only work. |
| Old five-gate stage sequence in the technical plan | Approved Architecture content | **Superseded for release-program sequencing only** | Use the new nine sequential governed stages. Preserve prior workflow approvals and evidence. |
| V2 README and root project summaries | Mixed/stale | **Informational; not normative for current completion state** | Refresh only after the baseline decision package is approved; do not use stale text as release evidence. |
| Remediation deltas that still say verification is pending | Pending | **Historical status metadata superseded by later verification for the tested snapshot** | Preserve; cite later verification and its scope. |
| Stage 2 Ask Fin contracts that say approval or verification is pending | Pending | **Historical contract metadata; implementation evidence is later** | Preserve; local-only production changes require an approved successor delta, not a rewrite. |
| [Closeout package](../closeout-2026-07-29/FIN-SIGHT-SDD-CLOSEOUT-AND-NEXT-STAGE-REVIEW-2026-07-29.md) | NO-GO / Stabilization recommended | **Current closeout evidence for the reviewed repository state** | Preserve. Its independent PASS covers the report package, not product release readiness. |
| Generated screenshots | Evidence | **Non-normative visual evidence** | Retain only governed evidence; separate duplicates and temporary captures during baseline classification. |
| Current source, tests, migrations, and untracked files | Mixed working state | **Unfrozen** | Classify and commit or exclude each item before the Stage 1 source-baseline gate. |

## 6. Reconciled contradictions and scoped supersessions

| Conflict | Governing disposition in this overlay | Status |
|---|---|---|
| Root `/docs` and `/specs` disagree | `/specs` governs; `/docs` is historical unless incorporated by an approved requirement. | Resolved for interpretation. |
| V2 requirement files say `Draft`, but Requirements passed | The accepted hashes are requirements-gate approved. Do not edit their headers; this overlay records the package status. | Resolved without hash invalidation. |
| V2 architecture/ADRs say `Draft`/`Proposed`, but Architecture passed | The exact hashes in §4.2 are architecture-gate accepted. Do not edit in place. | Resolved without hash invalidation. |
| Earlier plan defines five stage gates; current program defines nine sequential stages | Nine-stage production-readiness order governs the stabilization/release program. Earlier approvals and workflow evidence remain historical facts. | Pending formal Stage 1 approval of this overlay. |
| Root product understanding is sample-department specific | Department-neutral V2 requirements govern product behavior; Application Engineering remains sample data only. | Resolved by later approved V2 scope. |
| Eight-step, eleven-step, and seven-visible-step workflow descriptions coexist | Logical controls remain traceable; the approved seven-visible-step remediation presentation governs current UX. The production-readiness stages are delivery gates, not end-user steps. | Resolved for scope; preserve trace. |
| Root AI plan deferred AI, while V2 includes Ask Fin | Later V2 requirements include Ask Fin. Current production direction requires first-release, local-only Ask Fin with automatic provisioning, pending Stage 1 scope approval. | Pending gate record for first-release scope. |
| ADR-V2-005 permits an organization-private external provider, while current direction forbids cloud fallback | First-release release target is loopback/local-only with no external/cloud fallback. The ADR remains historical Architecture authority outside this narrower release profile until a successor ADR is approved. | Pending successor Architecture delta in Stage 3/6. |
| Stage 2 says the application never automatically downloads a model; production direction requires automatic runtime/model provisioning | The current implementation contract is historical. First-release distribution must automatically provide or configure the approved local runtime and model. | Pending topology/licensing/hardware decision and successor Architecture delta. |
| Generic reporting requirements allow format discretion; Section 15 mandates complete PDF and XLSX | PDF and XLSX are provisionally mandatory first-release outputs, with exact content and identity requirements in the successor delta. | Pending Stage 1 approval. |
| FR-162 defines CORE-04 as GED required fields; remediation added Budget formula checks to CORE-04 | No implementation behavior may decide this policy. Financial-control and Product Owner decision required. | **Unresolved blocker.** |
| Specifications use permanent IDs `R-VAL-01`–`R-VAL-05`; implementation/evidence often uses `CORE-01`–`CORE-05` | Aliases and permanent identities cannot remain ambiguous. A governed identity and migration decision is required. | **Unresolved blocker.** |
| V2 requires macOS parity while the production objective is Windows | Windows is the release target. macOS parity must be retained or formally deferred; it is not silently deleted. | Unresolved scope decision. |
| Backup/restore is `Should` or unimplemented in some artifacts, but Architecture defines managed recovery | Product Owner must decide whether governed managed backup/restore remains first-release mandatory. | **Unresolved blocker.** |

## 7. Product Owner and control-authority decision register

No item below may be decided implicitly in code. “Provisional direction” means the new source strongly indicates an answer, but the Stage 1 approval record must confirm it.

| Decision ID | Required decision | Current evidence or provisional direction | Decision authority | Stage 1 state |
|---|---|---|---|---|
| S1-D01 | Permanent protected Rule IDs | Existing accepted requirements use `R-VAL-01`–`R-VAL-05`; current implementation commonly uses `CORE-01`–`CORE-05`. Choose retention plus migration, or formal rebaseline with compatibility mapping. | Product Owner + Financial Control Approver + Architecture | **Open — exit blocker** |
| S1-D02 | CORE-04 boundary | Accepted FR-162 is GED required-field completeness. Budget formula checks were later placed into CORE-04 without an approved protected successor. Choose CORE-04-only or a separate governed rule. | Product Owner + Financial Control Approver | **Open — exit blocker** |
| S1-D03 | Advisory rules in first release | Model and requirements describe advisory rules; execution coverage is incomplete. Include with full contract or formally defer. | Product Owner | **Open — first-release scope blocker** |
| S1-D04 | Managed backup and restore in first release | Accepted Architecture defines governed recovery; implementation/readiness evidence is incomplete. | Product Owner + Security/Architecture | **Open — first-release scope blocker** |
| S1-D05 | Mandatory exports | Section 15 requires complete PDF plus XLSX evidence workbook. | Product Owner | **Provisional: both mandatory; confirmation required** |
| S1-D06 | Ask Fin in first release | Section 15 and the program require automatic local-AI provisioning and no manual setup. | Product Owner + Security/Privacy | **Provisional: included; confirmation required** |
| S1-D07 | Supported Budget/GED layout scope | Current implemented contract is `SLV-001`; no other approved layout is release-qualified. | Product Owner + Finance + Architecture | **Open — exit blocker** |
| S1-D08 | Supported Windows hardware baseline | No approved CPU/RAM/storage/GPU/OS matrix exists for application plus local model. | Product Owner + Release Engineering + Architecture | **Open — exit blocker** |
| S1-D09 | Approved local-AI deployment topology | Decide per-user versus per-machine runtime/model ownership, process lifecycle, update/repair/uninstall behavior, offline acquisition, and model identity. | Product Owner + Security + Architecture + Legal/Release | **Open — exit blocker** |
| S1-D10 | macOS parity | Retain as a release requirement, or formally defer it while preserving future scope. | Product Owner | Open; must be recorded before first-release scope freeze. |
| S1-D11 | Enterprise retention and disposal policy | Define retention periods and disposal authority for reviews, results, audit, Ask Fin content, reports, exports, backups, and content-free tombstones. | Product Owner + Financial Control + Security/Records | Open; blocks final persistence/report design. |
| S1-D12 | PDF detail defaults and size limits | Define default profile, transaction/audit thresholds, pagination/appendix behavior, and any hard limits. No silent omission is allowed. | Product Owner + Finance + UX/Accessibility | Open; required before Stage 5 implementation. |
| S1-D13 | Confidentiality label and configuration owner | Section 15 proposes `Confidential — Internal Financial Review`; confirm default, allowed customization, and authorized administrator. | Product Owner + Security/Legal | Open; required before Stage 5 implementation. |

## 8. Frozen stabilization scope

Subject to Stage 1 approval, the governed stabilization scope is:

1. reconcile protected-rule identity and deterministic contracts;
2. correct financial computation, eligibility, duplicate, reconciliation, result-status, and evidence defects;
3. complete lifecycle, publication, persistence, audit, retention, backup/restore, and source-reverification contracts selected for release;
4. stabilize UX, accessibility, diagnostics, and reliability without adding unrelated BI functionality;
5. implement the approved Leadership Summary, complete PDF, XLSX evidence export, and recovery scope;
6. production-harden local-only Ask Fin;
7. build signed Windows packaging with automatic local runtime/model provisioning;
8. qualify clean-machine and enterprise-operational behavior; and
9. run full regression, independent reviews, hands-on approval, and final GO/NO-GO authorization.

Out of scope until separately approved:

- new source-document types beyond Budget and GED;
- new workbook layouts beyond the approved release profile;
- cloud/public AI or automatic cloud fallback;
- AI-created financial facts, findings, calculations, or decisions;
- unrelated BI, forecasting, payment approval, vendor approval, or accounting-policy automation;
- implementation of Stage 2 or later before Stage 1 exits.

## 9. Stage 1 gate and approval record

Stage 1 may pass only when all of the following are evidenced:

- a clean controlled starting commit or immutable snapshot;
- a classified source inventory covering tracked modifications and untracked files;
- acceptance of this hierarchy/status overlay;
- approval of the successor requirements delta and updated traceability matrix;
- recorded decisions S1-D01 through S1-D09, plus any S1-D10 through S1-D13 item needed by the frozen first-release scope;
- no ambiguity affecting deterministic financial behavior;
- an exact approved stabilization scope; and
- Product Owner approval, with Financial Control, Security, Architecture, or Legal approval where identified above.

Until then:

> **Stage 1 status: IN PROGRESS / NO-GO for Stage 2.**

Approval record to be appended by the authorized gate owner without modifying any frozen predecessor:

| Field | Value |
|---|---|
| Product Owner decision | Pending |
| Financial-control decisions | Pending |
| Security/Architecture decisions | Pending |
| Approved starting commit/snapshot | Pending |
| Approved successor-requirements hash | Pending |
| Approved traceability-matrix hash | Pending |
| Stage 1 gate result | Pending |
| Decision timestamp and actor | Pending |
