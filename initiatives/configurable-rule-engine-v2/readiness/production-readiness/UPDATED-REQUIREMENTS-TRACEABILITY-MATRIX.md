# Updated Requirements Traceability Matrix — Production Readiness

**Initiative:** FinSight Configurable Rule Engine V2<br>
**Program stage:** Stage 1 — Baseline Freeze and SDD Reconciliation<br>
**Matrix type:** Additive status and successor-requirement overlay<br>
**Status:** Pending Stage 1 Product Owner approval<br>
**Prepared:** 2026-07-29<br>
**Implementation changes reviewed in this matrix:** None

## 1. Scope and continuity

This matrix updates, but does not rewrite, the [2026-07-29 Closeout Requirements Traceability Matrix](../closeout-2026-07-29/UPDATED-REQUIREMENTS-TRACEABILITY-MATRIX-2026-07-29.md). The closeout matrix remains the detailed implementation/test disposition for root `FR-001`–`FR-122`, V2 `FR-123`–`FR-203`, root `NFR-001`–`NFR-080`, V2 `NFR-081`–`NFR-110`, and the MVP remediation delta at the source state that closeout reviewed.

This overlay adds:

- the nine-stage production-readiness program;
- every Section 15.1–15.17 clause;
- proposed successor requirements `FR-204`–`FR-218`;
- proposed successor requirements `NFR-111`–`NFR-123`;
- explicit Stage 1 decisions and stage gates; and
- current normative status without modifying frozen reviewed files.

Approval of this matrix would not imply that any proposed requirement is implemented. It establishes what must be traced and verified in later governed stages.

## 2. Governing source keys

| Key | Source | Exact identity |
|---|---|---|
| PRP | FinSight Production-Readiness and Governed Release Program | SHA-256 `6653b87ba7d23fa83bba14450f1abb69479661e9550c03ef9b1154e16998bc53` |
| S15 | Section 15 — Enterprise Rule Governance, Complete Reporting, Audit History, and Final Distribution | SHA-256 `1275c7dee199b1f08d76a7bdcedb1185b645e04039f0a16d417a6ac05accf92d` |
| ROOT-FR | [Root Functional Requirements](../../../../specs/01-functional-requirements.md) | Existing approved working baseline; exact release seal pending Stage 1. |
| ROOT-NFR | [Root Non-Functional Requirements](../../../../specs/02-non-functional-requirements.md) | Existing approved working baseline; exact release seal pending Stage 1. |
| V2-FR | [V2 Functional Requirements](../../specs/01-functional-requirements.md) | Accepted SHA-256 `0fe666b42290d6c12ac679a787f347155f8d2eb2fd6b03ab0957164984eb3297`. |
| V2-NFR | [V2 Non-Functional Requirements](../../specs/02-non-functional-requirements.md) | Accepted SHA-256 `a49212a6c2bd9bd185831d4422d99018e99629afc4dd2c51ab622d8c52ce9a8b`. |
| ARCH | [Architecture Stage Package](../ARCHITECTURE-STAGE-PACKAGE-2026-07-27.md) | Accepted architecture/ADR hashes listed in the package and repeated in the [Stage 1 hierarchy](STAGE-01-NORMATIVE-SOURCE-HIERARCHY.md). |
| CLOSE | [Closeout report](../closeout-2026-07-29/FIN-SIGHT-SDD-CLOSEOUT-AND-NEXT-STAGE-REVIEW-2026-07-29.md), [matrix](../closeout-2026-07-29/UPDATED-REQUIREMENTS-TRACEABILITY-MATRIX-2026-07-29.md), [test inventory](../closeout-2026-07-29/CONSOLIDATED-TEST-INVENTORY-2026-07-29.md), and [evidence index](../closeout-2026-07-29/EXACT-EVIDENCE-INDEX-2026-07-29.md) | Current implementation/test evidence for the reviewed closeout state; overall release disposition NO-GO. |
| DELTA | [Production-Readiness Requirements Delta](PRODUCTION-READINESS-REQUIREMENTS-DELTA.md) | Proposed; final hash to be recorded at Stage 1 approval. |

## 3. Status definitions

| Status | Meaning |
|---|---|
| Pending Stage 1 approval | Proposed requirement or disposition; no implementation authority yet. |
| Stage 1 in progress | Baseline reconciliation activity is authorized, but exit evidence and decisions are incomplete. |
| Blocked by Stage 1 | A later stage cannot start because the sequential predecessor gate has not passed. |
| Existing coverage — complete/partial/not started | Current implementation status inherited from CLOSE; it does not change the proposed requirement's approval status. |
| Provisional Product Owner direction | S15 indicates the intended answer, but the decision must be recorded in the Stage 1 gate package. |

## 4. Production-readiness program traceability

| Source | Program obligation | Existing coverage and evidence | Successor requirement(s) / decision(s) | Required stage | Required verification | Current status |
|---|---|---|---|---|---|---|
| PRP §1–2 | Deliver a financially correct, private, reliable, accessible, supportable, one-click Windows application through nine sequential governed stages; prohibit source mutation, AI decisions/facts, public AI, concealed incompleteness, and false gate claims. | Root/V2 requirements cover major boundaries; CLOSE reports substantial implementation but release NO-GO, red full regression, no Windows release, and unresolved policy conflicts. | NFR-111, NFR-116–NFR-123; FR-215–FR-217 | All stages | Full trace audit; financial oracle; privacy/egress tests; accessibility; clean-machine qualification; final independent reviews | Pending Stage 1 approval |
| PRP §3 | Preserve repository/evidence, classify all files, establish clean baseline, reconcile status/traceability, freeze scope. | CLOSE recorded 29 modified tracked and 809 untracked items; no clean immutable release baseline. This three-document overlay covers hierarchy/delta/trace only. | NFR-123; S1-D01–S1-D13 | Stage 1 | Clean Git/snapshot evidence; classified inventory; hashes; approved gate record | **Stage 1 in progress** |
| PRP §3 decisions | Decide permanent IDs, CORE-04, advisory, backup/restore, exports, Ask Fin, layout scope, hardware, and local-AI topology. | CLOSE identifies ID/CORE-04 as material defects and advisory/backup/packaging as gaps. S15 provisionally answers exports and Ask Fin. | S1-D01–S1-D09 | Stage 1 | Attributable Product Owner/control/security/architecture decision record | Open; blocks Stage 1 exit |
| PRP §4 | Stabilize protected rule identity, deterministic finance, periods, duplicates, formula/reconciliation logic, result status, summaries, evidence, optional rules, history, and oracle behavior. | V2 FR-159–FR-164 and Stage 1 financial oracle exist; CLOSE documents protected-ID, CORE-04, period, duplicate, overall-status, and publication defects. | FR-204–FR-207; NFR-113; S1-D01–S1-D03 | Stage 2 | Independent Decimal/OOXML oracle; positive/negative/boundary/metamorphic tests; full rule-result cardinality/replay | Blocked by Stage 1 |
| PRP §5 | Stabilize lifecycle, architecture, persistence, publication, successor versions, audit, retention, backup/restore, disposal, and authoritative reconstruction. | Accepted Architecture is detailed; CLOSE marks source/edit successors, publication, backup/restore, and disposal partial/not started. | FR-207–FR-209, FR-211, FR-218; NFR-112, NFR-114, NFR-122; S1-D04/S1-D11 | Stage 3 | Migration/fault/race/tamper/recovery tests; lifecycle state machine; architecture/security review | Blocked by Stage 1 |
| PRP §6 | Stabilize UX, accessibility, diagnostics, reliability, keyboard/screen-reader/zoom, and large-review behavior. | Stage 2 UI work is substantial; CLOSE full suite had focus and 200% appearance failures; native screen-reader evidence pending. | NFR-115; inherited NFR-092/remediation accessibility NFRs | Stage 4 | Impacted UI tests plus governed full accessibility suite; native Windows AT; resizing/performance; independent UX/accessibility PASS | Blocked by Stage 1 |
| PRP §7 | Deliver decision-oriented Leadership Summary, complete PDF/XLSX, deterministic report equality, export identity, confidentiality, and approved recovery. | Current summary exists; modern complete PDF/XLSX and production recovery are incomplete/not started per CLOSE. | FR-209–FR-214, FR-218; NFR-113–NFR-115, NFR-122; S1-D04/S1-D05/S1-D11–S1-D13 | Stage 5 | PDF semantic/golden review; OOXML oracle; audit equality; confidentiality/accessibility; backup/restore oracle | Blocked by Stage 1 |
| PRP §8 | Production-harden Ask Fin: local only, grounded, isolated, refusal-safe, audited, automatically ready. | Current loopback Ollama grounding/refusal coverage is strong; automatic runtime/model provisioning is absent; topology/licensing/hardware undecided. | FR-215; NFR-111, NFR-116; S1-D06/S1-D08/S1-D09 | Stage 6 | Egress/proxy/redirect tests; model verification; prompt-injection/context isolation; refusal suite; repair/unavailable recovery | Blocked by Stage 1 |
| PRP §9 | Build signed Windows installer with automatic application/runtime/model provisioning, update/repair/uninstall, provenance, and license controls. | FR-175–FR-178/ADR-V2-004 define outcome; CLOSE says production packaging not started. | FR-215–FR-217; NFR-117; S1-D08/S1-D09 | Stage 7 | Controlled build; SBOM/license/model-rights review; signing/timestamp/hash/malware tests; installer lifecycle | Blocked by Stage 1 |
| PRP §10 | Qualify clean machines, enterprise deployment, constrained hardware, first run, reports, Ask Fin, persistence, recovery, upgrade/uninstall. | No target-machine matrix evidence. | FR-216; NFR-118; S1-D08/S1-D09 | Stage 8 | Approved VM/physical clean-machine matrix with exact manifests and PASS artifacts | Blocked by Stage 1 |
| PRP §11–14 | Run final full validation, independent reviewers, hands-on gate, exact rebuild, and an exact GO or NO-GO decision without publishing early. | Existing closeout independent PASS applies to the review package, not the product; full regression was red. | FR-217; NFR-119–NFR-121, NFR-123 | Stage 9 | Two full governed evidence runs; reviewer separation; Product Owner hands-on; signature/hash/download verification | Blocked by Stage 1 |

## 5. Section 15 clause traceability

| Source | Required outcome | Existing requirement/architecture coverage | Known implementation/evidence gap | Proposed successor mapping | Required stage | Verification | Status |
|---|---|---|---|---|---|---|---|
| S15 §15.1 | Five visible protected controls; review metadata/history; ordinary disable/delete warning; governed changes only | FR-143, FR-144, FR-150, FR-198, FR-199; NFR-085/NFR-090 | Five controls exist, but permanent ID and CORE-04 semantics conflict with accepted contracts. | FR-204; S1-D01/S1-D02 | 2–3 | Manifest/UI/auth matrix; governance replay; finance/security review | Pending Stage 1 approval |
| S15 §15.2 | User inspects and confirms exact active Rule Set; no hidden/draft/disabled/retired/stale rules | FR-141, FR-145, FR-150, FR-152, FR-184 | Active-set machinery exists; complete confirmation metadata and advisory scope need reconciliation. | FR-205; S1-D03 | 2–3 | Active-set positive/negative matrix; confirmation audit; accessibility | Pending Stage 1 approval |
| S15 §15.3 | Every consumer uses active-rule recorded results only, with full provenance | FR-142, FR-153–FR-169, FR-184, FR-187, FR-194; ADR-V2-007 | Strong architecture/tests exist; CLOSE identifies incorrect status/RAG semantics and unfinished exports. | FR-206; NFR-113 | 2, 4–6 | Consumer fitness, equality oracle, optional-rule metamorphic test, historical replay | Pending Stage 1 approval |
| S15 §15.4 | Immutable rule/version/set change; new run; added/removed/changed/unchanged comparison; reproducibility | FR-145, FR-147–FR-151, FR-171, FR-173, FR-196, FR-202; NFR-089 | History/comparison exists; successor auto-publication and source successor flow conflict with accepted lifecycle. | FR-207 | 2–3 | Version/revalidation/race tests; predecessor replay; comparison oracle | Pending Stage 1 approval |
| S15 §15.5 | Full append-only lifecycle audit catalog, immutable/ordered/attributable/tamper-evident/retained | Root FR-084–FR-090; FR-138/144/154/198–202; NFR-090/091/101/109 | Audit foundations exist; complete catalog, packaged paths, backup/restore, retention policy, and full cleanup provenance are incomplete. | FR-208; NFR-112/NFR-122; S1-D04/S1-D11 | 3, 5–8 | Event-catalog oracle; tamper/fault/access/retention tests | Pending Stage 1 approval |
| S15 §15.6 | Concise Leadership Summary audit block and complete ordered Audit History appendix | FR-186, FR-193, FR-194; root FR-089/090 | Summary exists; complete audit section/appendix export is absent. | FR-209 | 5 | Audit-ledger equality; appendix completeness/redaction/accessibility | Pending Stage 1 approval |
| S15 §15.7 | Complete exact-run enterprise PDF with all named financial/evidence/audit sections and no recalculation | Root FR-116/117/120; V2 §2.13; FR-165/186/187/193/194 | Legacy/generic export support does not satisfy the complete current financial-review report. | FR-210; NFR-113/NFR-115; S1-D05/S1-D12 | 5 | PDF parser/golden review; Decimal equality; section/row-count oracle | Pending Stage 1 approval |
| S15 §15.8 | Pre-export confirmation and exact Working/Published/Historical/Superseded label | FR-171/172/193/194/202; ADR-V2-007 | Publication model exists; successor publication defect and complete report UI remain. | FR-211 | 3, 5 | State/race matrix; confirmation UI/a11y; artifact metadata | Pending Stage 1 approval |
| S15 §15.9 | Three PDF profiles; pagination/appendices; clear completeness; no silent omission | Generic root PDF requirements and V2 reporting | No approved profile/size-limit contract or complete report generator. | FR-212; NFR-115; S1-D12 | 5 | Profile/limit boundary matrix; count/disclosure/accessibility checks | Pending Stage 1 approval |
| S15 §15.10 | XLSX with 15 named sheets and exact authoritative values | Root FR-118–FR-120; V2 §2.13/FR-194 | Modern evidence workbook is absent/incomplete; format discretion is too broad. | FR-213; NFR-113; S1-D05 | 5 | OOXML sheet/value/formula oracle; reporting review | Pending Stage 1 approval |
| S15 §15.11 | Enterprise confidentiality across data, audit, AI, reports, exports, temp files, logs, destinations, labels | Root NFR-009–020; NFR-086/088/100/103–105; security architecture | Strong local/privacy controls exist; packaged Windows security, report workspace, destination policy, label governance, recovery, and provisioning remain. | FR-218; NFR-111/NFR-114/NFR-116/NFR-122; S1-D09/S1-D11/S1-D13 | 3, 5–8 | Filesystem/ACL/encryption/log/egress/destination/security review | Pending Stage 1 approval |
| S15 §15.12 | Every export includes complete review/run/rules/source identity and integrity verification | Root FR-120; FR-193/194; NFR-095 | Identity exists in UI/legacy export pieces; complete final artifact hash/manifest and modern exports are absent. | FR-214; NFR-113/NFR-117 | 5, 7 | Metadata resolution; hash/tamper; application-export equality | Pending Stage 1 approval |
| S15 §15.13 | Eleven independent reviewer PASS decisions against implementation/evidence | NFR-099; established independent-review practice | No final product reviewer package; closeout PASS is report-package-only. | NFR-119 | 9 | Independence manifest; verdict/evidence completeness | Pending Stage 1 approval |
| S15 §15.14 | Stop after reviewers; exact build/test data/checklist; Product Owner hands-on approval | Prior workflow hands-on gates; NFR-099 | No final release candidate or final hands-on evidence. | NFR-120 | 9 | Gate-state negative tests; exact build/hash/approval record | Pending Stage 1 approval |
| S15 §15.15 | Signed installer; one-click use; no repository/Python/Terminal/manual Ollama/model/startup | FR-175–FR-178; NFR-094/095; ADR-V2-004 | Windows packaging and automatic local-AI provisioning not implemented. | FR-215/FR-216; NFR-116–NFR-118; S1-D08/S1-D09 | 6–8 | Clean-machine moderated install; runtime/model readiness; installer lifecycle | Pending Stage 1 approval |
| S15 §15.16 | Exact approved commit rebuilt, signed, hashed, scanned, clean-tested; working Ask Fin/reports/uninstall; safe synthetic content; release manifest | FR-178; NFR-095/099 | No controlled final pipeline/artifact, signed manifest, clean-machine evidence, or model/license qualification. | FR-217; NFR-117/NFR-118/NFR-121/NFR-123 | 7–9 | Supply-chain attestation; clean-machine rerun; content scan; download hash match | Pending Stage 1 approval |
| S15 §15.17 | No manager download until every gate/oracle/reviewer/hands-on/report/AI/install/signing check passes and release authority records GO | Existing SDD gates and no-false-pass principles | Current state is NO-GO and Stage 1 decisions remain open. | FR-217; NFR-120/NFR-121/NFR-123 | 9 | Release state machine; mandatory-evidence audit; final authority record | Pending Stage 1 approval |

## 6. Proposed functional-requirement traceability

| ID | Source | Existing coverage | Required implementation stage | Required verification | Approval/implementation status |
|---|---|---|---|---|---|
| FR-204 | S15 §15.1 | FR-143/144/150/198/199; protected repository/governance currently partial due ID/CORE-04 conflict | 2–3 | Five-control repository manifest, mutation-denial/accessibility, protected successor integration | Pending Stage 1 approval / Not authorized |
| FR-205 | S15 §15.2 | FR-141/145/150/152/184; active sets exist, complete confirmation/advisory scope partial | 2–3 | Exact selection/exclusion/version/count/actor/time tests | Pending Stage 1 approval / Not authorized |
| FR-206 | S15 §15.3 | FR-142/153–169/184/186/187/194; consumer architecture strong, some semantics/export consumers incomplete | 2, 4–6 | Consumer fitness + Decimal equality + rule-change propagation | Pending Stage 1 approval / Not authorized |
| FR-207 | S15 §15.4 | FR-145/147–151/171/173/196/202; replay/comparison partial, publication/source-successor defects known | 2–3 | Immutable version chain, new run, four-way comparison, replay/race | Pending Stage 1 approval / Not authorized |
| FR-208 | S15 §15.5 | Root FR-084–090; V2 audit/persistence pieces; catalog/retention/packaged coverage partial | 3 | Complete event-catalog, schema/order/tamper/fault/privacy | Pending Stage 1 approval / Not authorized |
| FR-209 | S15 §15.6 | FR-186/193/194; summary exists, audit block/appendix incomplete | 5 | Audit-to-summary equality, appendix count/order/redaction/isolation | Pending Stage 1 approval / Not authorized |
| FR-210 | S15 §15.7 | Root FR-116/117, V2 generic reports; complete modern PDF not started | 5 | Required-section parser, app-to-PDF oracle, finance/reporting review | Pending Stage 1 approval / Not authorized |
| FR-211 | S15 §15.8 | Lifecycle/publication model partial; report confirmation absent | 3, 5 | Publication-state and concurrency matrix; confirmation a11y | Pending Stage 1 approval / Not authorized |
| FR-212 | S15 §15.9 | No approved three-profile/full disclosure implementation | 5 | Profile/size-boundary/row-count/pagination/accessibility | Pending Stage 1 approval / Not authorized |
| FR-213 | S15 §15.10 | Generic spreadsheet export only; exact evidence workbook absent | 5 | OOXML sheet/value/formula/identity oracle | Pending Stage 1 approval / Not authorized |
| FR-214 | S15 §15.12 | Identity foundations partial; immutable export hash/manifest absent | 5, 7 | Metadata resolution, final SHA-256, tamper and privacy | Pending Stage 1 approval / Not authorized |
| FR-215 | PRP §8–10; S15 §15.15 | Local Ollama integration exists; automatic runtime/model provisioning not started | 6–8 | Clean install/repair/upgrade/uninstall; model identity; egress; license/SBOM | Pending Stage 1 approval / Not authorized |
| FR-216 | S15 §15.15 | Architecture/plans only; no signed one-click Windows distribution | 7–8 | Moderated clean-machine manager workflow; one-click launch | Pending Stage 1 approval / Not authorized |
| FR-217 | PRP §11–14; S15 §15.13–17 | No final product gate/build/distribution; closeout is NO-GO | 9 | Gate negative matrix; exact rebuild/sign/hash/scan/download verification | Pending Stage 1 approval / Not authorized |
| FR-218 | S15 §15.11 | Theme/security config patterns exist; report label/destination workflow absent | 3, 5, 7–8 | Role/config, label, destination-protection warning/block, audit | Pending Stage 1 approval / Not authorized |

## 7. Proposed non-functional-requirement traceability

| ID | Source | Existing coverage | Required implementation stage | Required verification | Approval/implementation status |
|---|---|---|---|---|---|
| NFR-111 | PRP §1; S15 §15.11 | Strong local/privacy foundations; packaged/report/recovery boundary incomplete | 3, 5–8 | Encryption/ACL/log/crash/support/egress/cross-review security review | Pending Stage 1 approval / Not authorized |
| NFR-112 | S15 §15.5 | HMAC/audit design and tests exist; complete event scope/fault/retention proof incomplete | 3, 8 | Tamper/reorder/delete/fault/recovery/authorization tests | Pending Stage 1 approval / Not authorized |
| NFR-113 | S15 §15.3/7/10/12 | Engine/result projection architecture exists; modern exports and some summary semantics incomplete | 2, 5 | Independent Decimal, PDF, OOXML equality and boundary oracle | Pending Stage 1 approval / Not authorized |
| NFR-114 | S15 §15.11 | Temp lifecycle foundations exist; report/export packaged workspace not complete | 3, 5, 8 | Success/failure/cancel/crash/restart filesystem forensics and audit | Pending Stage 1 approval / Not authorized |
| NFR-115 | PRP §6–7; S15 §15.9 | Automated accessibility exists; native AT and current zoom/focus failures remain; report scale unqualified | 4, 5, 8 | Native Windows AT, PDF accessibility, max-size performance/memory | Pending Stage 1 approval / Not authorized |
| NFR-116 | PRP §8–10; S15 §15.11/15 | Loopback provider/security strong; automatic readiness/topology absent | 6–8 | Network interception, model/runtime identity, repair/offline/unavailable | Pending Stage 1 approval / Not authorized |
| NFR-117 | PRP §9/11; S15 §15.16 | Signing/SBOM/provenance are Architecture only | 7, 9 | License/model rights, SBOM, controlled build, signature/hash/scan | Pending Stage 1 approval / Not authorized |
| NFR-118 | PRP §10; S15 §15.16 | No target clean-machine matrix | 8 | All approved OS/RAM/rights/offline/online installer and workflow cells | Pending Stage 1 approval / Not authorized |
| NFR-119 | S15 §15.13 | Independent reviews used historically; no final multidisciplinary product gate | 9 | Eleven scoped verdicts and reviewer-implementer separation | Pending Stage 1 approval / Not authorized |
| NFR-120 | S15 §15.14–17 | Workflow approvals used historically; final gate state absent | 9 | Out-of-order transition denial; exact build/hands-on/release authority | Pending Stage 1 approval / Not authorized |
| NFR-121 | PRP §11; S15 §15.16–17 | Prior suites extensive; latest full closeout suite red | 9 | Full governed suite and independent oracle twice; order-varied run; zero mandatory failures | Pending Stage 1 approval / Not authorized |
| NFR-122 | PRP §3/7; S15 §15.5/11 | Recovery Architecture detailed; production backup/restore/retention policy incomplete | 3, 5 | Retention boundaries, backup/restore manifest, disposal non-restoration | Pending Stage 1 approval / Not authorized |
| NFR-123 | PRP §3/11–14; S15 §15.13–17 | Closeout exposed dirty baseline and test truth; this overlay starts reconciliation | 1 and every gate | Clean inventory, exact hashes, link/evidence audit, independent reproducibility check | Pending Stage 1 approval / Stage 1 work in progress |

## 8. Open decision-to-requirement traceability

| Decision | Requirements affected | Why implementation cannot decide it | Required decision evidence | Current state |
|---|---|---|---|---|
| S1-D01 permanent protected IDs | FR-204–FR-207; FR-143/154/159–164; NFR-089/090/113 | Rule identity controls replay, migration, evidence, reports, and governance. | Product Owner + Financial Control + Architecture decision with compatibility/migration plan | Open — Stage 1 exit blocker |
| S1-D02 CORE-04 boundary | FR-204/206; FR-162/164; NFR-113 | It changes protected control scope, result cardinality, and findings. | Product Owner + Financial Control approved rule contract/version strategy | Open — Stage 1 exit blocker |
| S1-D03 advisory release scope | FR-205–FR-207; FR-141/146/150; NFR-119/121 | Current model and execution coverage differ. | Include-with-contract or explicit deferral | Open — first-release scope blocker |
| S1-D04 managed backup/restore | FR-208/209; NFR-112/122 | Recovery authority, installer lifecycle, disposal, and report audit depend on it. | Include/defer decision with accepted recovery scope | Open — first-release scope blocker |
| S1-D05 mandatory exports | FR-210–FR-214; NFR-113–NFR-115 | Format/content determine Stage 5 scope and release evidence. | Approve PDF + XLSX or explicit alternative | **Provisional from S15: PDF + XLSX mandatory** |
| S1-D06 Ask Fin in first release | FR-215; NFR-111/116/117 | Packaging, model licensing, hardware, privacy, and installer size depend on it. | Include/defer decision | **Provisional from S15: included** |
| S1-D07 supported workbook layouts | Existing FR-180–183; NFR-118/121 | Intake/oracle qualification is layout-specific. | Exact release layout/version list and fixtures | Open — Stage 1 exit blocker |
| S1-D08 Windows hardware baseline | FR-215/216; NFR-115–NFR-118 | Local model and workbook/report performance cannot be qualified without targets. | OS/CPU/RAM/storage/GPU/rights/support matrix | Open — Stage 1 exit blocker |
| S1-D09 local-AI topology | FR-215; NFR-111/116/117/118 | Per-user/per-machine runtime ownership changes security, updates, repair, uninstall, and licensing. | Approved architecture/security/legal topology decision | Open — Stage 1 exit blocker |
| S1-D10 macOS parity | NFR-118 and first-release scope | Existing direction and new Windows objective conflict. | Retain or formally defer, with future trace preserved | Open |
| S1-D11 retention/disposal policy | FR-208/209/214/218; NFR-111/112/122 | Required durations and deletion authority are business/security policy. | Versioned enterprise retention matrix and owners | Open |
| S1-D12 report detail/size policy | FR-210/212/213; NFR-115 | Completeness, usability, performance, and omission disclosures depend on limits. | Default profile, thresholds, hard limits, appendix/companion rules | Open |
| S1-D13 confidentiality label/config owner | FR-218; NFR-111 | Legal/organizational marking cannot be inferred from sample data. | Default label, permitted values, authorization owner | Open |

## 9. Required verification evidence by stage

| Stage | Minimum evidence package before PASS |
|---|---|
| 1 | Clean starting commit/snapshot; classified tracked/untracked inventory; approved hierarchy, delta, and matrix hashes; S1-D01–S1-D09 decisions plus relevant S1-D10–S1-D13; frozen scope; Product Owner/control approvals. |
| 2 | Correct protected identity/semantics; independent Decimal/OOXML oracle; positive, negative, missing, reversal, boundary, 3+ duplicate, period, optional-rule, and replay cases; full stage regression; independent financial-control PASS. |
| 3 | Approved successor ADRs; lifecycle/publication state tests; migrations; audit catalog/tamper/fault tests; retention/backup/restore/disposal evidence; independent architecture/security PASS. |
| 4 | Corrected full UI/accessibility suite; native Windows screen-reader/keyboard/zoom evidence; large-review responsiveness; UX/accessibility PASS. |
| 5 | Leadership Summary equality; complete PDF/XLSX oracles; audit appendix; export confirmation/labels/hash; report accessibility/confidentiality; recovery evidence; finance/reporting/security PASS. |
| 6 | Ask Fin local-only topology; pre-prompt model/runtime verification; grounded citations; context isolation; prompt-injection/refusal/egress/recovery; independent AI safety/privacy PASS. |
| 7 | Controlled Windows build; signed/timestamped installer; SBOM/licenses/model rights; automatic runtime/model provisioning; repair/upgrade/uninstall; release-engineering/security PASS. |
| 8 | Approved clean-machine matrix with first run, workflows, reports, Ask Fin, restart, recovery, upgrade/uninstall, performance, no developer steps; enterprise qualification PASS. |
| 9 | Exact full regression and oracle twice; eleven independent PASS verdicts; exact hands-on build and Product Owner approval; controlled final rebuild; signature/hash/scan/download match; final authority GO. |

## 10. Traceability completeness and next action

Coverage check:

- PRP governing objective and all nine stages: mapped.
- PRP Stage 1 explicit decisions: mapped as S1-D01–S1-D09.
- Additional ambiguity found during source reconciliation: mapped as S1-D10–S1-D13.
- S15 §15.1 through §15.17: each mapped.
- Successor functional requirements: continuous `FR-204` through `FR-218`, each mapped.
- Successor non-functional requirements: continuous `NFR-111` through `NFR-123`, each mapped.
- Existing requirement implementation disposition: incorporated by reference to CLOSE, not overwritten.

Current gate conclusion:

> **Stage 1 remains IN PROGRESS. Stages 2–9 are BLOCKED.**

The next action is Product Owner/control-authority resolution of the decision register and creation of a clean, classified source baseline. No production implementation is authorized by this matrix.
