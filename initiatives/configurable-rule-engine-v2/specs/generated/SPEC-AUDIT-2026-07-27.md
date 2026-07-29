# Independent Specification Audit — FinSight Configurable Rule Engine V2

- **Date:** 2026-07-27
- **Mode:** Separate read-only requirements audit
- **Reviewed:** V2 constitution, FR/NFR drafts, Product Owner sources, WF-01–WF-11, parent requirements/rules catalog, and local SDD quality standards
- **Initial verdict:** **FAIL**
- **Gate meaning:** The draft may enter `/sdd:clarify`; it may not enter `/sdd:decompose`, `/sdd:workbook`, architecture, or implementation.

`FAIL` here means that identifiable requirement defects and unresolved human decisions prevent approval. It does not reject the approved product direction.

## Initial score bands

| Range | Score band | Principal failed characteristics |
|---|---:|---|
| FR-123–FR-140 | 2–3 | Missing reader contract; unresolved metadata semantics; incomplete boundary criteria |
| FR-141–FR-152 | 2–3 | Unresolved governance/rule-type decisions; lifecycle ambiguity |
| FR-153–FR-164 | 1–2 | Contradictory result grain; unresolved financial semantics |
| FR-165–FR-179 | 2–3 | Incomplete workflow presentation, catalog disposition, release-policy decisions |
| NFR-081–NFR-104 | 2–3 | Unapproved profiles/policies, incomplete measurement conditions, criteria/statement mismatches |

The local spec-quality standard requires every item to score at least 4 before workbook entry.

## Evidence-backed findings

1. **Critical — Rule Result cardinality contradicted scope-level core behavior.** FR-153 required one result per selected rule while CORE-01 through CORE-05 evaluate accounts, transactions, or fingerprint groups.
2. **Blocker — Real-layout ingestion was named but not specified.** The supplied source uses GED header row 7/detail row 8 and Budget Account Name in B/BGT in C, while the current reader assumes GED header row 4 and Budget in B.
3. **Major — Sample account-shape assumptions appeared universal before approval.**
4. **Major — OQ-14 lacked a complete existing-rule disposition artifact.**
5. **Major — WF-08/WF-09 required outputs were referenced but not enumerated as testable results.**
6. **Major — NFR fit criteria added obligations absent from their statements, and byte-identical replay conflicted with volatile timestamps/IDs.**
7. **Major — Clarification questions were substantively appropriate but lacked quoted ambiguity, impact, ownership, and safe-default/no-safe-default treatment; some questions were missing.**
8. **Major — Acceptance design is incomplete.** Most FRs still require a distinct boundary case and verification approach; deterministic replay still requires a fully approved golden-dataset policy.

## Post-audit analyst remediation

The following defects were corrected without resolving a human policy decision:

- Functional §2.2–§2.3 and FR-153/FR-157/FR-184 now distinguish one Rule Execution per selected rule from one Rule Result per expected evaluation scope.
- Functional §10 and FR-180–FR-183 now define versioned source layout `SLV-001`, including worksheet names, header/detail rows, field-to-column mappings, and non-transaction row exclusion.
- Six-digit detail and three-digit group behavior is limited to the versioned `SLV-001` reader contract.
- `03-existing-rule-disposition.md` inventories all 57 existing Rule IDs with a preservation stop gate and pending human disposition.
- Functional §2.5 and FR-157/FR-166 enumerate the required WF-08/WF-09 results and analytics views.
- Functional §2.6 defines a deterministic business-result comparison projection that excludes volatile audit metadata.
- NFR-088/NFR-100 were narrowed to their statements; disposal and actionable-diagnostic obligations were split into NFR-105/NFR-106.
- `clarifications/CLARIFICATION-PACKET-2026-07-27.md` supplies quoted ambiguities, impact, accountable decisions, and safe-default/no-safe-default treatment.

These changes require a follow-up audit after stakeholder answers. They do not convert any item from Draft or change the initial independent verdict.

## Subsequent stakeholder clarification

HD-19 and HD-20 resolved the sample-level finance questions without asserting enterprise-wide accounting policy:

- the supplied Budget/GED structures and agreed synthetic conventions are the V1 business contract;
- functional §11 now defines V1 identity, period, parsing, eligible-population, exact-duplicate, precision, and formula-result behavior;
- broader accounting semantics, alternate layouts, broader normalization, and department-specific conventions are future configurable extensions;
- functional §2.7 and FR-185–FR-188 define a deterministic Review Summary as the first post-validation view;
- CQ-01–CQ-04, CQ-08, CQ-09, CQ-15–CQ-21, CQ-24, CQ-28, and CQ-31 are resolved for V1 and logged.

Governance, authorization, catalog, lifecycle, release, retention, scale, severity, reporting, and AI-boundary questions remain open. The requirements remain Draft, and the initial independent verdict remains unchanged pending a new audit after those decisions.

## Focused HD-19/HD-20 follow-up

- **Scope:** Incorporation of the supplied-report V1 contract and Review Summary-first requirement.
- **Verdict:** **PASS**
- **Confirmed:** V1 semantics are explicitly sample-scoped; resolved finance questions are absent from the active stop-gate table and are logged; every requested Review Summary field and destination is specified; summary values have deterministic engine-record mappings; WF-01–WF-11 remains intact; all 66 FRs and 26 NFRs remain sequential and Draft; explicit requirement references and local Markdown links resolve.
- **Limitation:** This focused PASS does not supersede the initial full-audit FAIL or authorize decomposition. Remaining governance, lifecycle, severity, catalog, release, scale, retention, reporting, and AI-boundary decisions still require clarification and a later full audit.

## Post-remediation mechanical check

- 66 functional requirements are sequential from FR-123 through FR-188.
- 26 non-functional requirements are sequential from NFR-081 through NFR-106.
- Every requirement has exactly one EARS `SHALL`, all required template fields, and Draft status.
- All explicit FR/NFR references resolve to either the parent or V2 register.
- The 57-rule disposition register matches the 57 unique IDs in the root Rules Catalog with zero missing, extra, or duplicate rows.
- Local spec lint, relative-link checks, trailing-whitespace checks, and patch-integrity checks pass.

This mechanical check is not a substitute for the required independent follow-up audit.

## Checked and sound

- Requirement IDs were unique and sequential at the time of the initial audit.
- Every EARS statement contained exactly one `SHALL`.
- All requirements were Draft.
- All 13 NFR categories were represented.
- HD-01–HD-20, WF-01–WF-11, protected-core governance, deterministic-engine single-source truth, source immutability, department neutrality, Windows distribution, summary-first review, sample-contract V1 scope, and AI-explains-only were materially preserved.
- No existing root rule was silently removed or reclassified.

## Remaining stop gates

- Apply named human answers from the clarification packet.
- Complete happy, negative, and boundary acceptance design for every FR.
- Assign a justified verification approach to every FR/NFR.
- Define and approve the deterministic golden-dataset corpus, expected-output regeneration policy, comparison rules, and storage.
- Re-run the independent audit and achieve score 4 or 5 for every item.
- Record row-level human approval before baselining or decomposition.
