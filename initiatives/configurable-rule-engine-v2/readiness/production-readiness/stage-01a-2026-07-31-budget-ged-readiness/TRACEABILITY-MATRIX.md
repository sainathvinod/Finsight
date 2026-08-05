# Stage 01A Requirements Traceability Matrix

**Prepared:** 2026-07-31  
**Status:** Draft; complete for decision presentation, not approved  
**Implementation fields:** Intentionally `TBD` until Requirements and
Architecture approval  
**Scope:** Complete 2026-07-31 Budget/GED production-readiness directive

## 1. Constitutional coverage

The governing principles are parent P-1/P-2 (spec-first/human approval), P-4
(visible failure), P-7 (financial determinism), P-8 (deterministic system of
record), P-11 (AI optionality), P-12 (change is not an exception), P-14
(auditability), P-15 (versioned configuration), and P-16 (monthly Review
Cycle). V2 principles 2, 4, 7, 8, 9, 12, 20, and 24 apply directly.

The directive proposes changes to V2 principles 13 and 17: the first
post-validation page and persistence of the complete working/verified row
projection. Those changes remain blocked by S1A-D09 and S1A-D02 and require a
successor approved specification/ADR; this package does not silently amend the
constitution.

## 2. Source-to-requirement coverage

| Source clause | Normalized outcome | Requirement / decision | Planned verification | State |
|---|---|---|---|---|
| §§1–2 | One department-neutral Budget/GED product; deterministic engine is truth; no invoice or packaging work | Parent P-7/P-8/P-11/P-12/P-16; V2 principles 2/4/7/8/12; FR-126, FR-165; S1A-D01 | scope/navigation inventory; engine-consumer architecture check | Existing authority plus pending source-precedence decision |
| §3 | Durable encrypted SQLite state, including exact source/reviewed row projections | FR-225; NFR-127; S1A-D02 | migration, restart, integrity, Decimal, backup/restore, disposal | Draft / blocked; reverses current reconstruction profile |
| §3 | Provider credentials never stored as plaintext governed data | NFR-128; S1A-D04 | database/backup/log/crash/support-bundle secret scan | Draft / blocked |
| §4 | Review identity, lifecycle, immediate resumable Draft | FR-240; existing FR-124/FR-195/FR-201 | create/close/reopen/resume/dispose workflow | Draft |
| §5 | Exact duplicate review blocked early and before validation | FR-228; NFR-129 | creation, prevalidation, archived/deleted, and concurrent writer matrix | Draft |
| §5 | Deterministic likely-duplicate warning with compare/open/continue/cancel | FR-229; S1A-D06 | predicate/signals/actions/reason/audit boundary matrix | Draft / blocked |
| §5 | Same period but different department permitted; deleted review ignored | FR-228/FR-229; existing FR-201 | negative duplicate and disposal/tombstone controls | Draft |
| §6 | Revalidation creates immutable successor history, not a duplicate review | existing FR-173/FR-196/FR-207; FR-230 | prior/current run replay and publication-state controls | Existing authority clarified |
| §6 | Ask Fin rolls to exact run/provider context | FR-224 | working versus published and provider-version conversation matrix | Draft |
| §§7–9 | Five protected rules plus review-local optional rules; unused deletion versus used retirement | existing FR-143–FR-150; FR-226/FR-227; S1A-D05 | two-review isolation, reference check, deletion/retirement/replay | Draft / blocked |
| §10 | Clear deterministic validation readiness | existing FR-205/FR-207 | disabled-reason and selected-rule-set matrix | Existing candidate; implementation recheck required |
| §11 | Versioned approved provider profiles, discovery, connection test, safe reset | FR-219/FR-220/FR-244; S1A-D03/D04 | provider-contract and no-review-data discovery/connection tests | Draft / blocked |
| §11 | External warning, enforceable authorization, field-level transmission policy | FR-245/FR-246; NFR-124/NFR-125/NFR-128; S1A-D04 | signed-policy, revocation, packet-capture, masking, audit, secret tests | Draft / blocked |
| §11 | Provider changes cannot change financial truth | FR-221; parent P-7/P-8/P-11 | cross-provider authoritative-state equality | Draft |
| §12 | Durable conversation bound to review/version/run/provider | FR-222–FR-224, FR-241; NFR-126; S1A-D08 | restart, pending/terminal outcomes, rollover, isolation, retention | Draft / blocked |
| §13 | Grounded natural-language Ask Fin with citations/refusals | existing FR-167–FR-170; FR-221/FR-222/FR-233/FR-241 | summary/account/vendor/evidence/comparison/refusal/cross-review suite | Existing plus Draft clarification |
| §14 | Modern embedded right-side Ask Fin conversation | FR-242; NFR-131 | bubbles, suggestions, loading, scrolling, multiline keyboard, citations/evidence | Draft normative requirement |
| §15 | Exact June fixture and independent oracle | `JUNE-FIXTURE-AND-ORACLE-CONTRACT.md`; `FIX-JUN-001`; `ORACLE-JUN-001`; S1A-D07/D10 | independent XLSX/XML Decimal oracle with exact cells | Draft / blocked |
| §16 | Prior-review eligibility, YTD/current-period basis, exact identities and tie-break | FR-231; S1A-D10; root FR-032/FR-078/FR-108 | comparable/incompatible/tie/period-basis matrix | Draft / blocked |
| §16 | Recurrence and trend classifications | FR-232; NFR-130; S1A-D07/D10 | `VER-MOM-001`, including New/Resolved/Continuing and trend values | Draft / blocked |
| §16 | Both-period evidence and no unsupported causation | FR-233; parent P-8/P-12 | May/June citation validation and causation-refusal cases | Draft / blocked |
| §17 | Exactly five primary results areas | FR-234; S1A-D09 | navigation inventory and displaced-detail reachability | Draft / blocked |
| §18 | Decision-oriented Overview | FR-235; S1A-D09 | recorded-projection equality and drill-down | Draft / blocked |
| §19 | Financial Analysis with accessible exact tables/visuals/drill-down | FR-236; NFR-131 | account/vendor/period oracle, keyboard and evidence navigation | Draft |
| §20 | Consolidated GED Review and filters | FR-237; root FR-037/FR-038/FR-039/FR-040/FR-042; S1A-D07 | transaction/filter/quality/finding-source matrix | Draft / blocked |
| §21 | Findings, deterministic Explain This, evidence and audited status | FR-238 | evidence completeness, source navigation, status nonmutation | Draft |
| §22 | Deterministic published-run Leadership Summary | FR-239; root FR-076/FR-078 | exact section/value/evidence equality and Ask Fin nonmutation | Draft |
| §23 | Complete attributable audit history | existing FR-208/FR-209; candidate NFR-112 | event coverage, restart, integrity/tamper/order tests | Existing candidate; approval pending |
| §24 | Confidentiality, isolation, fail-closed provider security | FR-245/FR-246; NFR-124–NFR-128; S1A-D03/D04/D08 | endpoint/transport/credential/policy/cross-context security suite | Draft / blocked |
| §25 | UI states only permissions actually enforced | existing §2.8; NFR-107/NFR-108 | permission and product-claim inventory | Existing candidate |
| §26 | Integrated themed accessible dialogs | FR-243; NFR-131 | focus/Escape/modality/theme/assistive-technology matrix | Draft normative requirement |
| §27 | Named acceptance scenarios | §3 of this matrix | one evidence record per `ACC-PR-*` | Draft |
| §28 | Full affected verification twice and three independent reviews | NFR-132 | two clean-revision manifests and independent verdicts | Draft |
| §29 | 23 exact deliverables | §5 `DEL-PR-*` register | artifact existence/hash/content review | Planned; no implementation artifacts authorized |
| §30 | Stop for hands-on acceptance; no packaging | NFR-132; README gate | gate audit | Binding stop condition |

## 3. Acceptance-scenario map

| Scenario ID | Scenario | Requirements | Required evidence |
|---|---|---|---|
| `ACC-PR-01` | May review survives restart with rows, rules, run, findings, conversation, preferences, and audit | FR-223/FR-225/FR-226/FR-241; NFR-126/127 | committed-table inventory and UI restart transcript |
| `ACC-PR-02` | May optional rule is absent from June/unrelated review | FR-226 | two-review scope query and UI evidence before/after restart |
| `ACC-PR-03` | Eligible never-used optional rule is removed under the approved lifecycle | FR-227; S1A-D05 | transactional reference check, tombstone/disposition, restart |
| `ACC-PR-04` | Used optional rule can only retire and historical replay remains exact | FR-227 | retained Rule Set/run/version oracle |
| `ACC-PR-05` | Exact duplicate is blocked at create and prevalidation | FR-228; NFR-129 | early/prevalidation/concurrent attempt tests |
| `ACC-PR-06` | Likely duplicate supports Compare/Open/Continue/Cancel and audits override reason | FR-229; S1A-D06 | predicate boundary, action, reason, and audit evidence |
| `ACC-PR-07` | Governed-deleted review no longer blocks; archived review remains a warning candidate | FR-228/FR-229; FR-201 | query/tombstone lifecycle controls |
| `ACC-PR-08` | Same month with Department 00-0245 and 00-0999 is allowed | FR-228/FR-229 | negative duplicate fixture |
| `ACC-PR-09` | Same-review revalidation preserves prior run/conversation and opens new scopes | FR-224/FR-230 | old/new run, rule set, publication, conversation, citations |
| `ACC-PR-10` | May-to-June results match YTD/current-period and recurrence/trend oracle | FR-231–FR-233; NFR-130 | `FIX-JUN-001`, `ORACLE-JUN-001`, `VER-MOM-001` |
| `ACC-PR-11` | Overview/analysis/finding/comparison drills to exact workbook evidence | FR-235–FR-238 | navigation transcript and identity-preserving source links |
| `ACC-PR-12` | Approved provider switch preserves all financial truth and never falls back | FR-219–FR-221/FR-244–FR-246; NFR-124/125/128 | packet capture, audit, credential scan, state equality |
| `ACC-PR-13` | Ask Fin handles greeting, review/account/vendor/missing/duplicate/evidence/comparison/follow-up/refusal/unsupported/cross-review/restart | existing FR-167–FR-170; FR-222–FR-224/FR-241/FR-242 | grounded response/citation/refusal/persistence suite |
| `ACC-PR-14` | Five result areas retain all detail in Light/Dark and accessible navigation | FR-234–FR-239/FR-243; NFR-131 | UI inventory, keyboard/screen-reader/zoom and screenshots |

## 4. Existing approved requirement disposition

| Existing requirement / principle | Disposition in this proposed change | Approval needed |
|---|---|---|
| Root FR-032 month-over-month detection | Retained; S1A-D07 must approve exact configuration before the June rule is active | Product Owner + Financial Control |
| Root FR-037 missing expected entry | Retained in finance-reference mode; `NOT_EVALUATED` without `EXPECTED-GED-REF-v1` or successor | Product Owner + Financial Control/reference owner |
| Root FR-038 duplicate entry | Retained and refined by protected CORE-03's exact 15-field contract | Existing protected-rule governance |
| Root FR-039 delayed posting | Retained; `NOT_EVALUATED` without approved cutoff calendar/posting field | Product Owner + Financial Control/calendar owner |
| Root FR-040 amount anomaly | Retained but deferred for May/June because minimum trailing history is absent; no Finding may be fabricated | No scope removal; later configuration/history gate |
| Root FR-042 coding/vendor expectation | Budget mapping retained through CORE-02; vendor expectation conditional on governed reference data | Financial Control for optional mode/reference |
| Root FR-078 month-over-month view | Retained and clarified by FR-231–FR-233/S1A-D10 | Product Owner + Financial Control |
| Root FR-108 multi-month retention | Retained; storage mechanics and record-class retention remain blocked by S1A-D02/S1A-D08/predecessor S1-D11 | Product Owner + Architecture + Records/Security |
| V2 principle 13 first Review Summary | Proposed successor: Overview becomes first and absorbs the cards; Leadership Summary remains separate | S1A-D09 and successor approved constitution/UX wording |
| V2 principle 17 reconstructed complete row projection | Proposed successor: encrypted normalized row snapshots, no workbook bytes | S1A-D02 and successor persistence ADR |
| V2 principle 24 publication default | Retained; comparisons, summaries, and Ask Fin default to published results | No change |

## 5. Required-deliverable register

These IDs enumerate directive §29. An ID is a planned artifact, not evidence
that implementation has started.

| ID | Required deliverable | Earliest legal stage |
|---|---|---|
| `DEL-PR-01` | Implementation summary | post-implementation verification |
| `DEL-PR-02` | Architecture decision record | successor Architecture |
| `DEL-PR-03` | SQLite schema and migration report | Architecture, completed after implementation |
| `DEL-PR-04` | Persistence verification | governed verification |
| `DEL-PR-05` | Duplicate-review design and test report | Architecture plus governed verification |
| `DEL-PR-06` | Source-fingerprint design | Architecture |
| `DEL-PR-07` | Deletion and retention behavior report | Requirements/Architecture decision, completed after verification |
| `DEL-PR-08` | Review-scoped rule lifecycle report | Architecture plus governed verification |
| `DEL-PR-09` | Provider-security design | Architecture/Security review |
| `DEL-PR-10` | Ask Fin grounding report | governed verification |
| `DEL-PR-11` | May synthetic oracle | existing sealed oracle; re-identified in final evidence manifest |
| `DEL-PR-12` | June synthetic oracle | post-Architecture fixture/oracle work |
| `DEL-PR-13` | May-versus-June comparison oracle | post-Architecture fixture/oracle work |
| `DEL-PR-14` | Results information-architecture report | Architecture/UX design, finalized after verification |
| `DEL-PR-15` | Accessibility report | governed verification |
| `DEL-PR-16` | Light and Dark screenshots | governed verification |
| `DEL-PR-17` | Exact changed-file inventory | governed verification |
| `DEL-PR-18` | Full test inventory | governed verification |
| `DEL-PR-19` | Known limitations | governed verification |
| `DEL-PR-20` | Independent Financial Control review | final stage verification |
| `DEL-PR-21` | Independent Privacy/Security review | final stage verification |
| `DEL-PR-22` | Independent UX review | final stage verification |
| `DEL-PR-23` | Hands-on acceptance checklist | final stage handoff |

## 6. Existing artifact impacts

| Artifact / item | Impact | Required post-approval action |
|---|---|---|
| Root functional requirements | Clarify FR-032/037/038/039/040/042/078/108 without overwriting history | approved successor change/baseline |
| V2 FR-145, FR-171–FR-173, FR-185–FR-188, FR-200, FR-203 | material successor wording or clarification | apply only recorded human decisions |
| Root/V2 NFR-101, NFR-103/104, NFR-110 and candidate NFR-116/NFR-122 | persistence/provider/retention conflict | reconcile exact successor requirements |
| ADR-012 and current reconstruction ADR | potential supersession by encrypted canonical rows | new ADR; never rewrite accepted history |
| ADR-V2-005 and local-only release freeze | potential provider-profile successor/split | new security ADR after S1A-D03/D04 |
| Rule lifecycle architecture | physical-deletion policy change | successor ADR after S1A-D05 |
| Persistence schema/migrations | large governed change | schema, migration, rollback, recovery, disposal plan |
| Results UX/walking skeleton | five-area IA and landing change | updated UX flow and independent UX review |
| Ask Fin implementation | conversation/provider persistence extension | grounding/security design and focused verification |
| May fixture/oracle | immutable comparison reference | retain hashes and never mutate |

## 7. Implementation traceability state

Implementation, test-file, technical-plan, and task links are intentionally
`TBD`. Assigning them now would imply decomposition before the Requirements
gate. After approval, the successor ADRs, Technical Implementation Plan, task
decomposition, and implementation must populate both forward and reverse
links.

## 8. Coverage conclusion

Every clause in the complete directive is represented by an existing
authority, a proposed Draft requirement, an enumerated verification/deliverable
artifact, or an explicit blocking decision. The two physically truncated
attachments are retained as provenance and add no independent governing
clause.

This is **complete coverage for stakeholder decision presentation only**. It
is not a Requirements PASS: S1A-D01 through S1A-D10, applicable predecessor
S1-D decisions, the exact optional-rule parameters/severities, human approval,
and a successor Architecture review remain open.

