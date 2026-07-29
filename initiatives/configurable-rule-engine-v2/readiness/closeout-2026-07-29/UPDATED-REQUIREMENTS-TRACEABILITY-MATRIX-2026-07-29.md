# FinSight Updated Requirements Traceability Matrix

**Review date:** 2026-07-29
**Scope:** Approved root FinSight baseline, Configurable Rule Engine V2 requirements, and the approved MVP remediation delta
**Review type:** Closeout reconciliation; implementation was inspected but not changed
**Overall finding:** The financial-review core is substantially implemented and well tested, but the approved specification and the implementation are not yet release-aligned. Protected-rule identity/semantics, successor publication, successor source re-verification, advisory rules, validation progress, modern exports/backup, accessibility qualification, and Windows packaging remain material gaps.

## 1. Status definitions

| Status | Meaning in this review |
|---|---|
| Complete | Implemented, exercised by relevant automated or independent evidence, and materially aligned with the latest approved direction. |
| Partially Complete | A useful implementation exists, but a required behavior, qualification, identity field, workflow, or governed semantic is missing or inconsistent. |
| Not Started | No production implementation or release qualification was found. |
| Superseded | A later approved product decision intentionally replaced the earlier requirement. The source requirement still needs formal baseline reconciliation where noted. |
| Deferred | Explicitly outside the current MVP or intentionally retained for a later governed phase. |

## 2. Evidence-key index

### Implementation keys

| Key | Exact implementation area |
|---|---|
| I-RM | `src/finsight/domain/review_management.py`; `src/finsight/application/review_management.py`; `src/finsight/infrastructure/review_management_repository.py`; `src/finsight/delivery/desktop/views/review_management_view.py`; `reviews_view.py`; `workflow_view.py` |
| I-SI | `src/finsight/domain/source_intake.py`; `src/finsight/application/source_intake.py`; `src/finsight/infrastructure/slv001_extractor.py`; `workbook_safety.py`; `source_intake_repository.py`; `src/finsight/delivery/desktop/views/source_intake_view.py` |
| I-VD | `src/finsight/application/reconstruction.py`; `review_session.py`; `review_working_set.py`; `verification.py`; `src/finsight/delivery/desktop/views/steps/verify_steps.py`; correction/source-lineage repositories and migrations |
| I-RE | `src/finsight/domain/financial_validation.py`; `src/finsight/application/rule_management.py`; `financial_review.py`; rule/governance repositories; `src/finsight/delivery/desktop/views/rules_repository_view.py` |
| I-RS | `src/finsight/domain/finding_explanations.py`; `src/finsight/application/financial_review.py`; `reporting.py`; `export.py`; `src/finsight/delivery/desktop/views/financial_review_view.py`; `findings_view.py` |
| I-AI | `src/finsight/application/ai/private_ask_fin.py`; `src/finsight/infrastructure/ai/providers/ollama.py`; AI grounding/citation/persistence modules; `src/finsight/delivery/desktop/views/private_ask_fin_dialog.py` |
| I-SEC | `src/finsight/application/security.py`; `src/finsight/infrastructure/identity.py`; `authorization_manifest.py`; `authorization_source.py`; secure-store, audit-stream, runtime-path, single-instance and migration infrastructure |
| I-DSP | `src/finsight/application/review_disposal.py`; disposal registry and repository infrastructure; review-delete UI |
| I-LC | `src/finsight/application/transition_engine.py`; lifecycle, generation, publication and reconstruction repositories |
| I-PKG | Architecture and packaging plans plus `tests/ui/test_packaging.py`; no MSI, signed executable, provisioning, or release implementation |

### Test and verification keys

| Key | Exact tests / verification evidence |
|---|---|
| T-RM | `tests/unit/test_review_management.py`; `tests/application/test_review_management.py`; `test_lifecycle_*`; `tests/ui/test_review_management.py`; `tests/accessibility/test_review_management_accessibility.py` |
| T-SI | `tests/unit/test_source_intake.py`; `tests/application/test_source_intake.py`; `tests/infrastructure/test_slv001_extractor.py`; `test_workbook_safety.py`; `tests/ui/test_source_intake.py` |
| T-VD | `tests/application/test_reconstruction*.py`; `test_verification_basis.py`; `tests/ui/test_working_set.py`; `test_verification_readiness.py`; source-details UI tests |
| T-RE | `tests/unit/test_financial_validation.py`; `tests/application/test_rule_management.py`; `test_protected_rule_governance.py`; `tests/security/test_workspace_baseline_upgrade_security.py`; `tests/integration/test_stage1_financial_oracle.py` |
| T-RS | `tests/application/test_financial_review.py`; `test_finding_explanations.py`; `tests/ui/test_integrated_financial_review.py`; `test_findings_workspace.py`; `tests/accessibility/test_financial_results_accessibility.py` |
| T-AI | `tests/ai/*`; `tests/integration/test_private_ask_fin_v2_grounding.py`; `tests/ui/test_ask_fin_setup_and_drawer.py`; `test_stage2_private_ask_fin_dialog.py` |
| T-SEC | `tests/application/test_authorization.py`; `tests/security/*`; secure-store, identity, audit-stream, manifest, single-instance and migration tests |
| T-DSP | `tests/application/test_review_disposal.py`; `tests/infrastructure/test_disposal_registry.py`; `tests/ui/test_review_deletion.py` |
| T-FIT | `tests/fitness/test_integrated_financial_review_architecture.py`; `test_boundaries.py`; `test_traceability.py` |
| E-W1 | `verification/WORKFLOW-01-VERIFICATION-2026-07-27.md` — 861 passed |
| E-W2 | `verification/WORKFLOW-02-VERIFICATION-2026-07-27.md` — 926 passed |
| E-MVP | `verification/MVP-END-TO-END-VERIFICATION-2026-07-27.md` — 940 passed |
| E-REM | `verification/MVP-FINAL-REMEDIATION-VERIFICATION-2026-07-28.md` — 1,019 passed; native screen-reader check pending |
| E-S1 | `verification/STAGE-1-FINANCIAL-CORRECTNESS-VERIFICATION-2026-07-29.md` — 1,042 passed and independent Decimal/OOXML oracle PASS |
| E-S2 | `verification/STAGE-2-CONSOLIDATED-VERIFICATION-2026-07-29.md` — 1,190 passed; independent financial, visual, privacy reviews PASS |
| E-S2F | `verification/STAGE-2-FOLLOWUP-ASK-FIN-NAVIGATION-RULES-2026-07-29.md` — focused 261 and 59 tests |
| E-AFS | `verification/STAGE-2-ASK-FIN-SIMPLIFICATION-2026-07-29.md` — focused 200 + 2 subtests, then 56 + 2 subtests; no full regression |
| E-UX | `verification/FINAL-LANDING-PAGE-VERIFICATION-2026-07-28.md`; `RAPID-UX-LANDING-SCALE-2026-07-28.md`; `RAPID-UX-VERIFY-DATA-SOURCE-DETAILS-2026-07-28.md` |
| E-CLOSE | `readiness/closeout-2026-07-29/CONSOLIDATED-TEST-INVENTORY-2026-07-29.md` — current full suite **4 failed, 1,212 passed, 2 subtests** plus independent boundary probes |

## 3. Material traceability findings

1. **Permanent protected Rule ID mismatch — material defect.** Approved requirements and architecture define permanent IDs `R-VAL-01` through `R-VAL-05`. Production rule manifests, results, findings, UI mappings, and tests use `CORE-01` through `CORE-05` as `rule_id` (`financial_validation.py:24-35`, `rule_management.py:35-39`). `CORE-*` is the approved control alias, not the permanent Rule ID. Historical/replay governance cannot be called aligned until the baseline is formally rebaselined to `CORE-*` or the implementation and retained data are migrated to `R-VAL-*`.
2. **CORE-04 protected semantics changed without governed version reconciliation — material defect.** FR-162 defines one scope per GED transaction and exactly six required GED fields. `financial_validation.py:1030-1189` also evaluates Budget BGT/ATD/ETC/EAC/DELTA consistency, producing 329 scopes instead of the 258 GED scopes in the supplied fixture. REM-FR-007 introduced “Complete and Correct Data,” but the protected-rule baseline was not formally versioned/reconciled.
3. **Successor reanalysis is silently published — material defect.** FR-202 requires a successor to remain Working/Unpublished until a Reviewer explicitly promotes it with a reason. `financial_review.py:607-627` records supersession and calls `set_published_generation` for reanalysis completion.
4. **Source/edit successor versions are deferred — material defect.** FR-196 requires post-validation source or reviewed-value changes to create a successor candidate/version with fresh confirmation. `transition_engine.py:134-145` explicitly defers `SOURCE_REVERIFICATION` and `EXTRACTOR_REVERIFICATION`.
5. **Informational/Advisory rules are modeled but not executable — product gap.** `financial_validation.py:260-309` accepts only `CORE_MANDATORY` and `OPTIONAL_CONFIGURABLE`; OBSERVATION/NO_OBSERVATION behavior is absent.
6. **Validation progress is staged presentation, not engine progress — UX/requirements gap.** `financial_review_view.py:5674`, `5738`, and `5781` discard engine stages with `lambda _stage: None`; the screen uses timer-driven steps rather than current rule/record/NOT_EVALUATED counts.
7. **The current full regression is red — release test gap.** E-AFS deliberately ran focused suites. E-CLOSE then ran the complete current repository and found 4 failures after the prior clean 1,190-test Stage 2 baseline.
8. **Requirements and Architecture artifacts still say Draft after their approval gates.** The approval/readiness records prove passage, but the normative headers and product-wide baseline were not reconciled. This is documentation/governance debt, not evidence that implementation lacked authorization.

## 4. V2 functional requirements traceability

| ID / source | Requirement | Implementation | Tests / verification | Status | Gap or disposition |
|---|---|---|---|---|---|
| FR-123 | Review entry actions | I-RM | T-RM; E-W1/E-S2 | Complete | Create and Past Reviews routes work; past action disables when empty. |
| FR-124 | Reporting-period selection | I-RM | T-RM; E-W1 | Complete | Month/year is persisted and validated. |
| FR-125 | Guided workflow progression | I-RM/I-SI/I-VD/I-RS | workflow/UI tests; E-MVP/E-S2 | Complete | Seven visible steps implement the approved simplified presentation over the logical workflow. |
| FR-126 | Two-source-role MVP intake | I-SI | T-SI; E-W2 | Complete | Exactly Budget and GED slots. |
| FR-127 | Source processing status | I-SI | T-SI; E-W2 | Complete | File, structure, extraction, metadata, and error states shown. |
| FR-128 | Paired-source validation prerequisite | I-SI/I-VD | source/verification tests; E-W2/E-S1 | Complete | Validation is blocked until both compatible sources and confirmation exist. |
| FR-129 | Department-evidence extraction | I-SI | extractor tests; E-W2 | Complete | Budget Grand Total and GED total evidence resolved. |
| FR-130 | Reporting-period-evidence extraction | I-SI | extractor/intake tests; E-W2 | Complete | Approved GED evidence and selected Budget workspace period used. |
| FR-131 | Pre-validation metadata summary | I-SI | UI intake tests; E-W2 | Complete | Department, period, filenames, counts, status and fingerprints shown. |
| FR-132 | Workbook-structure blocking diagnostics | I-SI | safety/extractor tests; E-W2 | Complete | Sheet/header/boundary failures block with location-aware messages. |
| FR-133 | Department-neutral execution | I-SI/I-RE | parameterization/oracle tests; E-S1 | Complete | No sample department constant controls results. |
| FR-134 | Department-mismatch gate | I-SI | source-intake tests; E-W2 | Complete | Cross-report report-level mismatch blocks. |
| FR-135 | Reporting-period-mismatch gate | I-SI | source-intake tests; E-W2 | Complete | Selected/extracted mismatch blocks. |
| FR-136 | Budget and GED review views | I-VD | T-VD; E-REM/E-S2 | Complete | Separate searchable/sortable review tables and source detail. |
| FR-137 | Review-local correction and reversion | I-VD | correction/reconstruction tests; E-REM | Complete | Source is immutable; reviewed copy is auditable/reversible. |
| FR-138 | Correction audit detail | I-VD/I-SEC | correction/audit tests; E-REM | Complete | Prior/new value, actor, time, source and reason retained. |
| FR-139 | Edit-confirmation gate | I-VD | verification-basis/UI tests; E-REM | Complete | Pending edits block validation and require the governed affirmation. |
| FR-140 | Confirmation without artificial edits | I-VD | verification tests; E-REM | Complete | No-edit confirmation creates no fabricated correction. |
| FR-141 | Governed rule classification | I-RE | rule-management tests; E-S1 | Partially Complete | Core and Optional work; Informational/Advisory execution is rejected. |
| FR-142 | One deterministic execution path | I-RE | T-RE/T-FIT; E-S1 | Partially Complete | Core/Optional share the engine; advisory class is not implemented. |
| FR-143 | Protected core binding | I-RE | T-RE; E-S1 | Partially Complete | Five controls are protected, but permanent IDs conflict with `R-VAL-*`. |
| FR-144 | Governed core-rule change | I-RE/I-SEC | governance/security tests; E-S1 | Complete | Different-person request/approval, version and audit mechanisms exist. |
| FR-145 | Optional-rule lifecycle | I-RE | rule-management/UI tests; E-S1/E-S2F | Complete | Create, test, activate, enable/disable, retire and logical delete are versioned. |
| FR-146 | Advisory-result distinction | I-RE | none for advisory result statuses | Not Started | OBSERVATION/NO_OBSERVATION and non-control treatment are absent. |
| FR-147 | Controlled rule-definition validation | I-RE | schema/injection tests; E-S1 | Complete | Closed declarative threshold family; unsafe definitions rejected. |
| FR-148 | Rule activation tests | I-RE | positive/negative/boundary tests; E-S1 | Complete | Activation requires governed test evidence. |
| FR-149 | Used rule-version retention | I-RE | replay/immutability tests; E-S1 | Complete | Prior versions/results remain addressable. |
| FR-150 | Rule-library visibility | I-RE | rules UI tests; E-S2F | Partially Complete | Core/Optional lifecycle visible; advisory inventory semantics are not realized. |
| FR-151 | Rule-change impact comparison | I-RE/I-RS | revalidation/comparison tests; E-S1 | Complete | Added/removed/changed results/findings compare across generations. |
| FR-152 | Confirmed-data rule execution | I-VD/I-RE | verification-gate/engine tests; E-S1 | Complete | Engine accepts sealed verified datasets. |
| FR-153 | Complete Rule Result ledger | I-RE | cardinality/ledger/oracle tests; E-S1 | Complete | PASS/FAIL/NOT_EVALUATED scopes retained with seals. |
| FR-154 | Rule Result provenance | I-RE | lineage/oracle tests; E-S1 | Partially Complete | Rich provenance exists; permanent protected Rule IDs are wrong. |
| FR-155 | Dependency-aware not-evaluated result | I-RE | engine/oracle tests; E-S1 | Complete | Missing Amount creates scoped NOT_EVALUATED, never false PASS. |
| FR-156 | Failed-result Finding | I-RE | finding cardinality tests; E-S1 | Complete | Exactly one Finding per failed control scope. |
| FR-157 | Complete validation-results presentation | I-RS | integrated-results tests; E-S2 | Complete | Current five-section experience exposes ledger-derived results and findings. |
| FR-158 | Overall validation-status derivation | I-RE/I-RS | oracle/results tests; E-S1/E-S2; E-CLOSE | Partially Complete | Persisted results are used, but optional failures/NOT_EVALUATED outcomes incorrectly affect Overall Review Status and RAG is separately derived. |
| FR-159 | CORE-01 spend versus BGT | I-RE | core/oracle tests; E-S1; E-CLOSE | Partially Complete | Exact Decimal comparison works for the fixture, but permanent Rule ID is not `R-VAL-01` and valid rows after the selected review month are wrongly included. |
| FR-160 | CORE-02 GED maps to Budget | I-RE | core/oracle tests; E-S1 | Partially Complete | Exact mapping behavior passes; permanent Rule ID drift remains. |
| FR-161 | CORE-03 exact duplicate | I-RE | duplicate/oracle tests; E-S1; E-CLOSE | Partially Complete | Fixture pair detection works, but permanent Rule ID drift, incomplete typed-scalar canonicalization, and undercounted 3+ member exposure/count remain. |
| FR-162 | CORE-04 required GED fields | I-RE | required-field/oracle tests; E-S1 | Partially Complete | Six GED checks work, but unapproved Budget formula scopes changed protected semantics. |
| FR-163 | CORE-05 Budget ATD equals GED sum | I-RE | reconciliation/oracle tests; E-S1; E-CLOSE | Partially Complete | Exact Decimal fixture behavior passes, but permanent Rule ID drift and missing selected-period eligibility remain. |
| FR-164 | Dependency-aware core outcomes | I-RE | cross-rule oracle; E-S1 | Partially Complete | Correct effects are observed, but CORE-04 scope and ID contract drift. |
| FR-165 | Validation-derived consumer source | I-RS/T-FIT | fitness and projection tests; E-S1/E-S2 | Complete | UI/AI consume recorded engine results; no evaluator import in consumers. |
| FR-166 | Results-based analytics set | I-RS | financial-results tests; E-S2 | Complete | Overview/Financial Analysis/GED/Findings/Summary use recorded review data. |
| FR-167 | Ask Fin evidence boundary | I-AI | T-AI; E-S2/E-S2F/E-AFS | Complete | One selected review/run corpus; no command ports. |
| FR-168 | Ask Fin citations and edit distinction | I-AI | citation/grounding tests; E-S2 | Complete | Structured citations and original/current distinction are enforced. |
| FR-169 | Ask Fin non-authority | I-AI | refusal/claim tests; E-S2 | Complete | Model cannot create findings, decisions or authoritative calculations. |
| FR-170 | Ask Fin before completed results | I-AI | mode/UI tests; E-S2F | Complete | Product-help mode is separated from financial-review mode. |
| FR-171 | Completed-review authoritative history | I-LC/I-RE | lifecycle/reconstruction tests; E-S1 | Complete | Sealed results and run identities persist. |
| FR-172 | Past-review read-only default | I-RM/I-LC | past-review/lifecycle tests; E-W1/E-S2 | Complete | Sealed review data opens read-only with separate governed actions. |
| FR-173 | Historical rerun isolation | I-RE/I-LC | revalidation/replay tests; E-S1 | Partially Complete | Runs/results are preserved, but successor completion auto-publishes contrary to isolation intent. |
| FR-174 | Existing-rule V2 disposition | rule disposition register/I-RE | catalog collision tests; E-S1 | Complete | 57 legacy rules preserved/inactive; no silent activation. |
| FR-175 | Windows executable and installer | I-PKG | only packaging UI/planning tests | Not Started | No executable/MSI or bundled runtime/model. |
| FR-176 | Windows clean-machine qualification | I-PKG | none on target matrix | Not Started | No clean Windows 11 8/16GB evidence. |
| FR-177 | Windows upgrade and uninstall behavior | I-PKG | no installer lifecycle tests | Not Started | Repair/upgrade/uninstall are plans only. |
| FR-178 | Windows release provenance and integrity | I-PKG | dependency checks only | Not Started | No signing, SBOM release manifest, checksum, malware or tamper qualification. |
| FR-179 | Validation progress visibility | I-RS | UI responsiveness tests; E-S2 | Partially Complete | Timer stages show activity; real rule/scope/NOT_EVALUATED progress is discarded. |
| FR-180 | Budget SLV-001 mapping | I-SI | extractor/oracle tests; E-W2/E-S1 | Complete | Columns A:H and financial fields map correctly. |
| FR-181 | Budget SLV-001 row classification | I-SI | extractor tests; E-W2 | Complete | Detail/group/separator/Grand Total retained correctly. |
| FR-182 | GED SLV-001 mapping | I-SI | extractor/oracle tests; E-W2/E-S1 | Complete | Header row 7, details from row 8, all A:O fields retained. |
| FR-183 | GED SLV-001 row classification | I-SI | extractor tests; E-W2 | Complete | Transaction/total/blank/header rows classified; totals excluded from scopes. |
| FR-184 | One Rule Execution per selected rule | I-RE | cardinality/oracle tests; E-S1 | Complete | Five core plus enabled optional rules have one execution each. |
| FR-185 | Review Summary landing page | I-RS | Stage 2 UI tests; E-S2 | Superseded | Later approved Stage 2 navigation intentionally opens Overview first; Summary remains accessible. Baseline text needs reconciliation. |
| FR-186 | Review Summary content | I-RS | integrated-results tests; E-S2; E-CLOSE | Partially Complete | Required sections exist, but several status/count values do not follow the exact §2.7 source policy and advisory counters are absent. |
| FR-187 | Engine-derived Review Summary | I-RE/I-RS | fitness/oracle tests; E-S1/E-S2; E-CLOSE | Partially Complete | Values come from a sealed engine projection, but that projection currently implements incorrect status/RAG/health/count semantics. |
| FR-188 | Review Summary drill-down navigation | I-RS | UI navigation tests; E-S2 | Complete | Summary/Overview drill into Findings, evidence and source records. |
| FR-189 | Windows actor identity | I-SEC | identity unit/security tests; E-W1 | Partially Complete | Replaceable OS identity adapter exists; native Windows SID/packaged qualification is absent. |
| FR-190 | MVP role-policy enforcement | I-SEC/I-RE | authorization/governance tests; E-W1/E-S1 | Complete | Reviewer, Rule Administrator and Approver boundaries enforced at services. |
| FR-191 | Three-value field presentation | I-VD | working-set/accessibility tests; E-REM/E-UX | Complete | Original, reviewed and current values are available; source details are progressive disclosure. |
| FR-192 | Confirmed current-value validation binding | I-VD/I-RE | verification/reconstruction/oracle tests; E-S1 | Complete | Run fingerprints bind the exact confirmed basis. |
| FR-193 | Review Summary identity block | I-RS | results UI tests; E-S2 | Partially Complete | Department, period, run, rule set, review and files are shown; publication state is not consistently displayed. |
| FR-194 | Downstream review-context identity | I-RS/I-AI | export identity/AI context tests; E-S2 | Partially Complete | Ask Fin is bound; modern report/export delivery and complete publication labeling are unfinished. |
| FR-195 | Review lifecycle transition enforcement | I-LC | lifecycle tests; E-W1/E-S1 | Complete | Seven statuses and valid transition gates exist. |
| FR-196 | Successor version after reviewed-data change | I-LC | transition tests expose deferral | Partially Complete | Rule-set successors exist; source/edit/extractor successor flow is explicitly deferred. |
| FR-197 | Past-review lifecycle visibility | I-RM/I-LC | past-review UI tests; E-W1 | Complete | Status filters and saved reviews persist across restart. |
| FR-198 | Protected change request submission | I-RE/I-SEC | governance tests; E-S1 | Complete | Exact tested candidate, reason, actor and evidence retained. |
| FR-199 | Protected change rejection | I-RE/I-SEC | governance tests; E-S1 | Complete | Terminal rejection preserves active baseline/history. |
| FR-200 | Ask Fin private-provider prerequisite | I-AI | Ollama/security tests; E-S2/E-AFS | Complete | Only loopback Ollama; unavailable state is non-blocking with Retry. |
| FR-201 | Governed whole-scope disposal | I-DSP | T-DSP; E-REM | Partially Complete | One-review live-store disposal exists; period/all-data and managed-backup revocation do not. |
| FR-202 | Working-generation publication | I-LC/I-RE | generation tests | Partially Complete | First generation auto-publish works; successors are also auto-published without explicit promotion/reason. |
| FR-203 | Fingerprint-verified dataset reconstruction | I-VD | reconstruction tests; E-S1 | Complete | Matching source/extractor/correction basis is required; divergence withholds data. |

## 5. V2 non-functional requirements traceability

| ID | Requirement | Implementation | Tests / verification | Status | Gap or disposition |
|---|---|---|---|---|---|
| NFR-081 | V2 validation performance envelope | I-SI/I-RE | resource-limit/unit tests | Partially Complete | 10,000-line limits exist; no ≤120-second benchmark on approved Windows 8/16GB targets. |
| NFR-082 | Atomic rule and result persistence | I-RE/I-LC | migration/fault/cardinality tests; E-S1 | Complete | Completion seals and transactional repositories prevent partial authoritative ledgers. |
| NFR-083 | No false pass from unavailable evidence | I-RE | oracle/dependency tests; E-S1 | Complete | Missing required evidence produces NOT_EVALUATED or blocks scope enumeration. |
| NFR-084 | Non-executable rule definitions | I-RE | schema/injection tests; E-S1 | Complete | Closed declarative threshold model; code/SQL/scripts rejected. |
| NFR-085 | Least-privilege protection of core rules | I-RE/I-SEC | governance/security tests; E-S1 | Complete | Service authorization and different-person approval enforced. |
| NFR-086 | Approved processing boundary | I-AI/I-SEC | loopback/egress tests; E-S2/E-AFS | Complete | Ask Fin is loopback-only with no cloud fallback. |
| NFR-087 | Workbook resource-exhaustion limits | I-SI | workbook-safety boundary tests; E-W2 | Complete | ZIP/XML/sheet/cell/row/formula limits and cleanup paths exist. |
| NFR-088 | Protected temporary-data lifecycle | I-SI/I-SEC | secure-store/safety tests | Partially Complete | Protected temp behavior exists; packaged Windows ACL/runtime qualification is absent. |
| NFR-089 | Immutable used rule versions | I-RE | immutability/replay tests; E-S1 | Partially Complete | History is retained, but permanent protected IDs and CORE-04 governed semantics drift. |
| NFR-090 | Protected-rule change provenance | I-RE/I-SEC | governance/audit tests; E-S1 | Partially Complete | Workflow evidence exists; current seed identity/CORE-04 semantics were not governed to the approved baseline. |
| NFR-091 | End-to-end validation lineage | I-RE/I-RS | oracle/evidence/fitness tests; E-S1/E-S2 | Partially Complete | Strong lineage exists, but permanent Rule IDs/publication labeling are inconsistent. |
| NFR-092 | Accessibility coverage for V2 surfaces | desktop views | accessibility/UI tests; E-REM/E-S2; E-CLOSE | Partially Complete | Native screen-reader validation remains pending, and current 200% appearance clipping plus Settings Back focus tests fail. |
| NFR-093 | Evidence-first rule explainability | I-RS | evidence/dialog tests; E-S2 | Complete | One-interaction explanations identify values, rows, rule, outcome and follow-up. |
| NFR-094 | Windows installer qualification | I-PKG | none | Not Started | No clean-machine MSI/install/repair/uninstall qualification. |
| NFR-095 | Signed-package integrity and release provenance | I-PKG | none | Not Started | No signed release candidate, SBOM, provenance or tamper evidence. |
| NFR-096 | Department- and period-neutral implementation | I-SI/I-RE | parameterized tests; E-S1 | Complete | No sample department/month drives rules. |
| NFR-097 | Controlled rule extension without source-code change | I-RE | optional-rule tests; E-S1 | Complete | Supported threshold-family rules can be added/versioned/configured without code. |
| NFR-098 | Common engine contract across classifications | I-RE | core/optional tests | Partially Complete | Advisory execution/result contract is absent. |
| NFR-099 | Complete V2 delivery traceability | SDD artifacts/tests | fitness tests and this matrix | Partially Complete | Code/test evidence is extensive; formal product-wide rebaseline and exact protected IDs remain unresolved. |
| NFR-100 | Privacy-safe validation diagnostics | I-SEC/I-AI | logging/privacy tests; E-S2 | Complete | Diagnostics omit financial content/prompts/secrets and use correlation IDs. |
| NFR-101 | Complete governed backup and restore | architecture only | no production backup/restore tests | Not Started | Portable replacement-machine backup, restore, registry continuity and repair are absent. |
| NFR-102 | Closed-review immutability | I-LC/I-RM | lifecycle/immutability tests | Complete | Closed/Archived data is read-only; new facts append. |
| NFR-103 | Engine-bound AI explanation | I-AI | grounding/claim/fitness tests; E-S2 | Complete | AI consumes one result corpus and has no validation/write path. |
| NFR-104 | Public-model transmission prohibition | I-AI | loopback/proxy/redirect tests; E-S2/E-AFS | Complete | Public, non-loopback, proxy and redirect paths are rejected. |
| NFR-105 | Lifecycle-bound temporary-data disposal | I-SI/I-SEC | safety/secure-store tests | Partially Complete | Cleanup exists; complete operation-bound packaged proof and failure blocking need release qualification. |
| NFR-106 | Actionable diagnostic identity | I-SI/I-RE/I-AI | failure-contract/UI tests | Complete | Stable codes, safe cause, remedy and correlation IDs are surfaced. |
| NFR-107 | Role-model extensibility | I-SEC | authorization-manifest tests | Complete | Roles map to permissions through replaceable signed manifests. |
| NFR-108 | Replaceable identity-provider boundary | I-SEC | identity contract tests | Complete | Engine is identity-agnostic; OS adapter is replaceable. |
| NFR-109 | Temporary-data disposal provenance | I-SEC | limited cleanup tests | Partially Complete | No complete audit catalog proving every cleanup trigger/outcome across crash/recovery/packaged paths. |
| NFR-110 | Authoritative-only review persistence | I-VD/I-RE | reconstruction/storage-inventory tests; E-S1 | Complete | Sources/full normalized/verified datasets are not persisted; authoritative facts are reconstructed. |

## 6. MVP remediation-delta traceability

| ID | Requirement | Implementation | Tests / verification | Status | Gap or disposition |
|---|---|---|---|---|---|
| REM-FR-001 | Welcome hierarchy | I-RM | landing UI tests; E-REM/E-UX | Superseded | Later approved landing direction removed Recent Reviews from Home and retained only the two primary actions. Current UI follows the later direction. |
| REM-FR-002 | Plain-language errors with optional diagnostics | all delivery views | failure/UI tests; E-REM | Complete | Business-first text and progressive technical details exist. |
| REM-FR-003 | Business-first upload metadata | I-SI | source-intake UI tests; E-REM | Complete | File role, name, status, department/period and counts precede technical evidence. |
| REM-FR-004 | Resolved Budget department display | I-SI | extractor/intake tests; E-REM | Complete | Budget department resolves from Grand Total/workspace evidence. |
| REM-FR-005 | Editable Verify Data | I-VD | working-set UI tests; E-REM/E-UX | Complete | Budget/GED edits, revert and reviewed-copy behavior are implemented. |
| REM-FR-006 | Governed edit confirmation | I-VD | verification-basis tests; E-REM | Complete | Exact affirmation, diff, actor/time and audit gate validation. |
| REM-FR-007 | Review Rules step | I-RE/I-RS | rule/results UI tests; E-REM/E-S1 | Partially Complete | User experience exists, but its expanded CORE-04 Budget formula checks conflict with FR-162 without a governed protected-rule version. |
| REM-FR-008 | Optional-rule lifecycle | I-RE | rule-management tests; E-S1/E-S2F | Complete | Optional create/edit/version/test/enable/disable/retire/delete/revalidate works. |
| REM-FR-009 | Protected baseline governance | I-RE/I-SEC | governance/security tests; E-S1 | Partially Complete | Controls are protected, but seed permanent IDs/CORE-04 baseline semantics do not match the approved contract. |
| REM-FR-010 | Revalidation | I-RE/I-LC | comparison/revalidation tests; E-S1 | Partially Complete | New run/history/deltas are preserved, but successor completion auto-publishes instead of awaiting explicit promotion. |
| REM-FR-011 | Business-first result identity | I-RS | results UI tests; E-REM/E-S2 | Complete | Department, period and files lead; technical IDs are secondary/reachable. |
| REM-FR-012 | Deterministic visual analytics | I-RS | chart/projection tests; E-S1/E-S2 | Complete | Charts/tables use recorded Decimal-based review projections. |
| REM-FR-013 | Rule-oriented Validation Results | I-RS | integrated-results tests; E-REM/E-S2 | Complete | Results are grouped by rule with counts/outcomes/evidence. |
| REM-FR-014 | Record-oriented Findings | I-RS | findings tests; E-REM/E-S2 | Complete | Findings expose affected entity, rule, status, evidence and follow-up. |
| REM-FR-015 | Data Quality & Coverage | I-RS | data-quality UI tests; E-REM/E-S2 | Complete | Missing, invalid, duplicate, mapping and reconciliation coverage shown. |
| REM-FR-016 | Affected-row and cell navigation | I-RS/I-VD | evidence-navigation tests; E-REM/E-UX | Complete | Evidence opens exact Budget/GED source row/cell context. |
| REM-FR-017 | Governed whole-review disposal | I-DSP | T-DSP; E-REM | Partially Complete | Review-scoped live-store disposal works; period/all-data/managed backup scope from FR-201 remains absent. |
| REM-FR-018 | Financial application visual system | desktop theme/views | product-experience tests; E-REM/E-S2 | Complete | Warm cream/navy, cards, tables, semantic colors and hierarchy implemented. |
| REM-FR-019 | Light, Dark, System Default | appearance infrastructure | appearance/UI tests; E-REM/E-S2 | Complete | Preference persists and major surfaces are theme-aware. |
| REM-FR-020 | Bounded Ask Fin | I-AI | T-AI; E-S2/E-S2F/E-AFS | Complete | Review/help modes, one-review grounding, refusal boundary and local-only Ollama implemented. |
| REM-NFR-001 | Keyboard and focus | desktop views | accessibility tests; E-REM/E-S2/E-CLOSE | Partially Complete | Most automated keyboard coverage passes, but the current full suite proves the Settings Back control has `NoFocus`; native assistive-technology validation also remains pending. |
| REM-NFR-002 | Perceivability | themes/accessibility | accessibility/appearance tests; E-REM/E-S2 | Partially Complete | Contrast/text/icon semantics are tested; native screen-reader announcement quality remains pending. |
| REM-NFR-003 | Resizing and zoom | desktop layouts | responsive/200% tests; E-REM/E-S2/E-CLOSE | Partially Complete | Wide layouts generally work, but the current 200% test proves the appearance selector clips because its measured height is below the required scaled minimum. |
| REM-NFR-004 | Evidence integrity | I-RS/I-VD | oracle/evidence tests; E-S1/E-S2 | Complete | Financial evidence resolves to source records without UI recomputation. |
| REM-NFR-005 | Consolidated verification | verification package | E-REM/E-S1/E-S2/E-CLOSE | Partially Complete | A current full governed regression has now run and is red: 4 failed, 1,212 passed, and 2 subtests passed. The four failures must be corrected and the full suite rerun before release qualification. |

## 7. Inherited root functional-requirement disposition

The root functional baseline remains formally Approved and was inherited unless a V2 or later approved product decision narrowed or replaced it. This table records each root requirement individually. “Deferred” means the requirement remains a valid future product item, not that it was silently deleted.

| ID | Root requirement | Implementation / tests / evidence | Status | Reconciliation note |
|---|---|---|---|---|
| FR-001 | Ingest Excel workbooks | I-SI; T-SI; E-W2 | Complete | Approved Budget/GED `.xlsx` layouts only. |
| FR-002 | Ingest PDF documents | No current product path | Deferred | Invoice/reference-document phases are outside the Budget/GED MVP. |
| FR-003 | Read-only source handling | I-SI/I-VD; source immutability tests | Complete | Sources are fingerprinted references and never modified. |
| FR-004 | Document type classification with confirmation | I-SI | Superseded | Later MVP uses two explicit Budget/GED slots rather than generic classification. |
| FR-005 | Reporting-period assignment | I-RM/I-SI; E-W1/W2 | Complete | Month/year selected and cross-checked. |
| FR-006 | Review-cycle grouping | I-RM; T-RM | Complete | Stable review identity groups versions/runs. |
| FR-007 | File-level validation with clear rejection | I-SI; safety tests | Complete | Format, structure and resource gates are actionable. |
| FR-008 | Duplicate file detection | Fingerprints exist; no duplicate-content warning workflow found | Not Started | Duplicate review-period warning is not duplicate source-content detection. |
| FR-009 | File replacement with versioning | I-SI/I-LC | Partially Complete | Pre-confirmation binding replacement works; post-validation source successor is deferred. |
| FR-010 | File provenance record | I-SI/I-VD | Complete | Role, filename, path hint, hash, actor/time and source lineage retained. |
| FR-011 | GED extraction | I-SI; extractor/oracle tests | Complete | Real row-7 header/A:O layout. |
| FR-012 | Budget Tracker extraction | I-SI | Superseded | V2 approved one-sheet `Original Budget` layout replaces the old three-sheet model. |
| FR-013 | Structural noise handling | I-SI | Complete | Blank, subtotal, total and repeated-header rows classified. |
| FR-014 | Value normalization | I-SI/I-VD | Complete | Typed deterministic normalizers are used. |
| FR-015 | Raw value preservation | I-SI/I-VD | Complete | Raw/source value and lineage are preserved or reconstructable. |
| FR-016 | Extraction confidence indication | Current product intentionally avoids fabricated confidence | Superseded | Stage 2 uses deterministic validity/coverage states instead of invented confidence scores. |
| FR-017 | Configurable extraction templates | Versioned `SLV-001` contract only | Deferred | Additional layouts require a governed reader version. |
| FR-018 | Invoice-document extraction | None | Deferred | Future document type. |
| FR-019 | Reference-document extraction | None | Deferred | Future document type. |
| FR-020 | Resource loading extraction | None | Deferred | Future document type. |
| FR-021 | Schema validation | I-SI/I-RE | Complete | Source and rule schemas are validated. |
| FR-022 | Row-level quality checks | I-SI/I-RE/I-RS | Complete | Required values, mapping, duplicate and source-shape checks. |
| FR-023 | Internal consistency checks | I-RE | Complete | Decimal formulas/reconciliation and ledger cardinality. |
| FR-024 | Quarantine, not abort | I-SI/I-RE | Superseded | V2 retains malformed GED transaction candidates for CORE-04 but blocks ambiguous/unsafe source structure. |
| FR-025 | Data quality summary per cycle | I-RS | Complete | Overview/Data Quality surfaces aggregate recorded results. |
| FR-026 | Mandatory verification gate | I-VD | Complete | Confirmation is required before validation. |
| FR-027 | Verification view with source traceability | I-VD | Complete | Budget/GED grids and progressive Source Details. |
| FR-028 | User corrections with full audit | I-VD/I-SEC | Complete | Append-only corrections/reversions. |
| FR-029 | Verification decisions per document | I-VD | Superseded | Later approved pair-level confirmation seals the combined reviewed basis. |
| FR-030 | Planned versus actual variance | I-RE/I-RS | Complete | Exact BGT versus GED Actual by department/account. |
| FR-031 | Budget workbook figures support | I-SI/I-RS | Complete | BGT/ATD/ETC/EAC/DELTA/Notes retained. |
| FR-032 | Month-over-month change detection | No multi-period comparison engine | Deferred | One-period MVP. |
| FR-033 | Over/underspend severity | I-RE/I-RS | Complete | Overrun control and favorable/unfavorable visuals. |
| FR-034 | Run-rate projection | No forecasting implementation | Deferred | Future analysis. |
| FR-035 | Variance contributor ranking | Account/vendor descriptive analysis exists | Partially Complete | Current-period ranking exists; formal root contributor rule semantics are not fully specified/tested. |
| FR-036 | Multi-month trend risk | None | Deferred | Needs multiple periods. |
| FR-037 | Missing entry detection | I-RE | Complete | Required-field rule covers missing/invalid GED values. |
| FR-038 | Duplicate entry detection | I-RE | Complete | Exact all-material-field duplicate rule. |
| FR-039 | Delayed posting detection | None | Deferred | Not one of the protected/optional MVP rule families. |
| FR-040 | Amount anomaly detection | Optional threshold family supports bounded comparisons | Partially Complete | No dedicated statistical/anomaly rule. |
| FR-041 | Accounting-event awareness | GED fields retained; no event-policy evaluator | Deferred | Future configured finance semantics. |
| FR-042 | Coding and vendor-expectation checks | CORE-02 exact Budget mapping | Partially Complete | Coding exists; vendor expectation policy does not. |
| FR-043 | GED summarization | I-RS | Complete | Account/vendor/department and transaction views. |
| FR-044 | Automated GED-to-tracker matching | CORE-02/05 exact joins | Partially Complete | Exact Budget/GED mapping exists; generic tracker reconciliation workflow does not. |
| FR-045 | Match confidence tiers | None | Deferred | Exact deterministic mapping used. |
| FR-046 | Manual match and unmatch | Corrections can edit identifiers | Partially Complete | No dedicated match/unmatch lifecycle. |
| FR-047 | Cleared-status tracking | Finding lifecycle exists | Partially Complete | No item-level reconciliation cleared status. |
| FR-048 | Unreconciled items reporting | CORE-02/05 findings | Complete | Unmapped and ATD mismatch evidence shown. |
| FR-049 | Cross-month carry-forward | None | Deferred | Multi-period feature. |
| FR-050 | Reconciliation scope configuration | Rule configuration framework | Partially Complete | Current mapping/reconciliation scope is fixed to approved dataset; broader scope configuration deferred. |
| FR-051 | PO matching | None | Deferred | Future invoice control. |
| FR-052 | SOW period and scope validation | None | Deferred | Future invoice/contract control. |
| FR-053 | Rate card validation | None | Deferred | Future resource/invoice control. |
| FR-054 | Hours validation | None | Deferred | Future resource/invoice control. |
| FR-055 | Resource authorization validation | None | Deferred | Future resource control. |
| FR-056 | Code and category validation | CORE-02 only | Partially Complete | Budget code mapping exists; invoice category policy deferred. |
| FR-057 | Duplicate invoice detection | CORE-03 transaction duplicate | Partially Complete | Exact GED duplicate exists; document-level invoice duplicate deferred. |
| FR-058 | Deliverable confirmation check | None | Deferred | Future contract/invoice workflow. |
| FR-059 | Invoice status recommendation | AI refuses financial decisions; no deterministic workflow | Superseded | Current product provides evidence, not approval recommendation. |
| FR-060 | Line-item findings | I-RS | Complete | Transaction/account findings with source evidence. |
| FR-061 | Resource registry | None | Deferred | Future resource module. |
| FR-062 | Resource status and period | None | Deferred | Future resource module. |
| FR-063 | Resource cost visibility | None | Deferred | Future resource module. |
| FR-064 | Budget-to-resource analysis | None | Deferred | Future resource module. |
| FR-065 | Resource change history | None | Deferred | Future resource module. |
| FR-066 | Contract/SOW registry | None | Deferred | Future contract module. |
| FR-067 | Contract mappings view | None | Deferred | Future contract module. |
| FR-068 | Contract coverage checks | None | Deferred | Future contract module. |
| FR-069 | Findings as first-class records | I-RE/I-RS | Complete | Immutable result-linked Findings. |
| FR-070 | Severity classification | I-RE/I-RS | Complete | Deterministic fixed/configured severity. |
| FR-071 | Full traceability per finding | I-RS | Complete | Rule/version/scope/calculation/source evidence. |
| FR-072 | Finding lifecycle | I-RS/I-LC | Complete | New/acknowledged/in-review/resolved/dismissed events. |
| FR-073 | Recurrence linkage | No multi-period recurrence model | Deferred | Historical runs compare, but recurrence entity is absent. |
| FR-074 | Findings browsing | I-RS | Complete | Filters, drill-down and evidence. |
| FR-075 | False-positive feedback | Dismissed/status history only | Partially Complete | Feedback does not tune deterministic rules automatically. |
| FR-076 | Monthly leadership summary | I-RS | Complete | Deterministic Leadership Summary tab. |
| FR-077 | Deterministic RAG status | I-RE/I-RS; T-RE/T-RS; E-S2/E-CLOSE | Partially Complete | Status and RAG are both deterministic, but they are derived independently and can produce the prohibited `Attention Required / At Risk (Red)` pair instead of the approved one-to-one mapping. |
| FR-078 | Month-over-month comparison | None | Deferred | Multiple periods required. |
| FR-079 | Report reproducibility and history | Runs/history persist | Partially Complete | UI/history reproducible; modern PDF/XLSX Derived Records unfinished. |
| FR-080 | AI narrative sections separated | I-AI/I-RS | Complete | Deterministic summary and AI explanation are visibly distinct. |
| FR-081 | Review-cycle status tracking | I-RM/I-LC | Complete | Seven-state lifecycle. |
| FR-082 | Critical findings surfaced | I-RS | Complete | Findings/severity/priorities are prominent after validation. |
| FR-083 | No external notifications in MVP | No notification subsystem | Complete | No notification egress. |
| FR-084 | Ingestion and access audit | I-SEC/I-SI | Complete | Source/action events are attributable. |
| FR-085 | Extraction and verification audit | I-SEC/I-VD | Complete | Extraction/confirmation/corrections audited. |
| FR-086 | Rule execution audit | I-RE/I-SEC | Complete | Run/rule-set/result provenance retained. |
| FR-087 | AI interaction audit | I-AI | Complete | Provider/context/claims/outcome journaled without hidden reasoning. |
| FR-088 | Consent audit | Local Ollama needs no external consent | Superseded | Current approved local-only boundary eliminates external transmission consent. |
| FR-089 | Reporting and export audit | Legacy export identities exist | Partially Complete | Modern report/export experience and Derived Record lifecycle unfinished. |
| FR-090 | Audit trail review | Audit persistence exists | Partially Complete | No complete normal-user audit browser found in the current simplified product. |
| FR-091 | AI narrative explanation of findings | I-AI | Complete | Cited grounded explanations. |
| FR-092 | AI-generated summary narrative | Deterministic summary plus optional Ask Fin | Superseded | AI no longer creates the authoritative leadership summary. |
| FR-093 | AI recommendations from deterministic outputs | Decision refusals/nonbinding next actions | Superseded | Ask Fin explains; it does not recommend approvals or financial decisions. |
| FR-094 | AI grounding constraint | I-AI | Complete | One-review allowlisted corpus and verified claims. |
| FR-095 | AI-off completeness | I-AI/I-RS | Complete | Deterministic product works without Ollama. |
| FR-096 | Consent before transmission | No external AI path | Superseded | Local-only processing sends no financial data externally. |
| FR-097 | Provider selection and warnings | Ollama-only approved profile | Superseded | User-selectable provider registry narrowed to local Ollama. |
| FR-098 | Masking option | Legacy masking modules exist; not part of local-only normal path | Deferred | Needed only if a governed external-private provider returns later. |
| FR-099 | AI answer citation | I-AI | Complete | Valid FinSight citation syntax/records enforced. |
| FR-100 | Natural-language Q&A | I-AI | Complete | Pre/post-validation Ask Fin modes. |
| FR-101 | Question library | Suggested prompts exist | Partially Complete | No governed reusable question-library management. |
| FR-102 | Non-AI structured search | I-RS/I-VD | Complete | Tables, filters and drill-down work with AI off. |
| FR-103 | Configurable analysis parameters | I-RE | Complete | Versioned optional threshold configuration within approved family. |
| FR-104 | AI provider configuration | Ollama setup/config infrastructure | Partially Complete | Local endpoint/model config exists; deployment provisioning is absent. |
| FR-105 | Reference data management | None | Deferred | Future organization-specific reference data. |
| FR-106 | Rule enable/disable governed | I-RE | Complete | Optional binding versions; protected rules require governance. |
| FR-107 | Configuration versioning | I-RE | Complete | Rule-set/config versions preserved. |
| FR-108 | Multi-month retention | I-RM/I-LC | Complete | Reviews persist indefinitely unless governed disposal occurs. |
| FR-109 | Trend views | Current fixture has no prior-period source | Deferred | UI avoids fabricated trends. |
| FR-110 | Historical import | None | Deferred | Existing legacy records are viewable, but no user import workflow. |
| FR-111 | Cold-start graceful degradation | I-AI/I-RM | Complete | Missing Ollama is non-blocking; Retry is available. |
| FR-112 | Deterministic forecasting | None | Deferred | Future phase. |
| FR-113 | Resource departure impact | None | Deferred | Future phase. |
| FR-114 | Backfill scenario estimation | None | Deferred | Future phase. |
| FR-115 | What-if scenario framework | None | Deferred | Future phase. |
| FR-116 | Leadership summary export | I-RS legacy reporting | Partially Complete | On-screen summary exists; polished current PDF export is not delivered. |
| FR-117 | Data and findings export | `application/export.py` legacy JSON | Partially Complete | Backend artifacts exist; current modern UI/export scope is incomplete. |
| FR-118 | Workbook-compatible export | Architecture only | Not Started | No completed XLSX evidence workbook. |
| FR-119 | Audit export | No current user route | Not Started | Audit persistence is not an export deliverable. |
| FR-120 | Export labeling | Legacy manifests/tests | Partially Complete | Identity manifests exist in legacy path; modern artifacts/publication label incomplete. |
| FR-121 | Line-item type differentiation | GED row fields/classification | Partially Complete | Transaction/total/header distinctions exist; invoice/resource line-type model deferred. |
| FR-122 | Vendor project reference capture | GED fields retained | Partially Complete | Vendor/descriptions retained; dedicated project-reference field/workflow absent. |

## 8. Inherited root non-functional-requirement disposition

| ID | Root requirement | Implementation / tests / evidence | Status | Reconciliation note |
|---|---|---|---|---|
| NFR-001 | Analysis turnaround | I-SI/I-RE | Partially Complete | Small fixture is fast; no approved max-volume hardware benchmark. |
| NFR-002 | Interactive responsiveness | Worker-thread UI; E-S2 | Partially Complete | No formal 200ms interaction benchmark. |
| NFR-003 | Long operations never block | background workers/UI tests | Complete | Extraction/validation/AI use worker paths. |
| NFR-004 | AI latency independence | I-AI/I-RS | Complete | Deterministic results are available without waiting for AI. |
| NFR-005 | No data loss on failure | repositories/migrations/crash tests | Complete | Transactional/append-only behavior is broadly tested. |
| NFR-006 | Resumable cycles | I-RM/I-LC | Complete | Saved reviews resume after restart. |
| NFR-007 | Graceful degradation without connectivity | local desktop/Null AI | Complete | Core product is offline. |
| NFR-008 | Idempotent re-analysis | replay/version tests | Complete | Historical results remain preserved. |
| NFR-009 | Protection of data at rest | secure-store implementation/tests | Partially Complete | Encrypted store tests exist; packaged Windows DPAPI/ACL qualification absent. |
| NFR-010 | Protection of secrets | secure-store/AI config tests | Partially Complete | Code avoids plaintext secrets; release provisioning/key custody not qualified. |
| NFR-011 | No unconsented egress | I-AI | Complete | Local loopback only, no cloud fallback. |
| NFR-012 | Malicious/malformed input safety | workbook/rule/provider security tests | Complete | Archive/XML/rule/endpoint attacks covered. |
| NFR-013 | Administrator-managed provider registry | Ollama-only config | Superseded | Approved product narrowed to one local runtime. |
| NFR-014 | Informed consent quality | no external transmission | Superseded | Not applicable to local Ollama. |
| NFR-015 | Data minimization | I-VD/I-AI | Complete | No full source/dataset persistence; Ask Fin corpus minimized. |
| NFR-016 | Masking effectiveness | masking unit tests | Deferred | External-private provider path is outside current local-only product. |
| NFR-017 | Local data disposal | I-DSP | Partially Complete | One-review scope exists; period/all/managed backups absent. |
| NFR-018 | Development data hygiene | synthetic fixtures/docs | Complete | Verification uses synthetic workbooks. |
| NFR-019 | Complete attributable trail | I-SEC | Complete | Actors/actions/versions are broadly audited. |
| NFR-020 | Tamper-evidence | audit HMAC tests | Complete | Audit-stream integrity checks exist. |
| NFR-021 | Reproducibility guarantee | Decimal/oracle/replay tests; E-CLOSE | Partially Complete | Current code is repeatable, but the oracle encodes unapproved CORE-04 scopes and the protected ID/period/status contracts are not yet reproducible against the approved specification. |
| NFR-022 | Versioned rule/config provenance | I-RE | Partially Complete | Versions persist; permanent core IDs and CORE-04 baseline drift. |
| NFR-023 | AI provenance | I-AI | Complete | Provider/model/context/citations recorded. |
| NFR-024 | OS display mode support | appearance subsystem | Complete | Light/Dark/System modes persist. |
| NFR-025 | Color-independent meaning | UI/accessibility tests | Complete | Text/icon/shape accompany status colors. |
| NFR-026 | Keyboard and assistive access | accessibility tests | Partially Complete | Automated keyboard coverage passes; native screen reader pending. |
| NFR-027 | Text scaling | accessibility tests; E-CLOSE | Partially Complete | Most scaling coverage exists, but the current 200% header appearance control test fails because the label clips. |
| NFR-028 | Windows and macOS parity | cross-platform architecture | Partially Complete | macOS development works; Windows runtime not qualified. |
| NFR-029 | Identical results across platforms | canonical/Decimal tests | Partially Complete | No native Windows-versus-macOS byte-comparison evidence. |
| NFR-030 | Restricted-environment compatibility | offline/local design | Partially Complete | No enterprise clean-machine/GPO/standard-user qualification. |
| NFR-031 | Composable modules | ports/layers/fitness tests | Complete | Modular-monolith boundaries are enforced. |
| NFR-032 | No shortcuts | SDD/governance evidence | Partially Complete | Tactical ID/CORE-04/publication drift violates the approved contract. |
| NFR-033 | Requirement-traceable implementation | annotations/tests/this matrix | Partially Complete | Extensive traces exist, but formal baseline remains unreconciled. |
| NFR-034 | Documented behavior | docs/verification | Partially Complete | Strong documentation; several approved docs still say Draft and latest Ask Fin behavior lacks a delta. |
| NFR-035 | Unit testing built along the way | 1,190-test full suite evidence | Complete | Broad unit/integration/UI coverage. |
| NFR-036 | Deterministic core fully verifiable | T-RE/E-S1/E-CLOSE | Partially Complete | An independent oracle runs, but it validates the unapproved CORE-04 scope expansion and omits newly exposed status, period, duplicate-group and fingerprint boundaries. |
| NFR-037 | Provider-swap regression | Null/Ollama contract tests | Partially Complete | Current product intentionally supports local Ollama/Null only. |
| NFR-038 | Synthetic test fixtures | fixture/oracle | Complete | Approved synthetic Budget/GED and expected outcomes used. |
| NFR-039 | Parameterized operation | period/department/rule tests | Complete | No sample hard-coding in deterministic logic. |
| NFR-040 | Safe configuration handling | rule/AI config validation | Complete | Typed/validated configuration with safe defaults. |
| NFR-041 | Configuration transparency | Rules Repository/identity UI | Complete | Active rules/versions and local AI state are visible. |
| NFR-042 | Data growth headroom | pagination/limits | Partially Complete | No long-retention/large-ledger load qualification. |
| NFR-043 | Dimensional headroom | neutral keys/models | Partially Complete | Architecture supports departments; fixture validates only one report-level department. |
| NFR-044 | New rules without core change | optional rule family | Complete | Within approved evaluator family. |
| NFR-045 | New document types | versioned reader seam | Deferred | Only SLV-001 Budget/GED are implemented. |
| NFR-046 | New AI providers | provider port exists | Deferred | Product policy currently allows local Ollama only. |
| NFR-047 | Deterministic/AI boundary enforcement | fitness/AI tests | Complete | AI cannot affect results. |
| NFR-048 | Determinism as release criterion | oracle/verification; E-CLOSE | Partially Complete | The oracle is an explicit gate, but it must be regenerated from the approved contract before it can authorize a release. |
| NFR-049 | Visible AI distinction | Ask Fin labels | Complete | AI/private/local/non-authoritative labels shown. |
| NFR-050 | Grounded-output policy | I-AI | Complete | Unsupported claims are rejected/qualified. |
| NFR-051 | Model change management | digest/profile verification | Partially Complete | Runtime/model update/provisioning/release policy is absent. |
| NFR-052 | Prompt/response privacy balance | AI retention/audit policies | Complete | Hidden reasoning excluded; governed interaction evidence retained. |
| NFR-053 | Operational logging separate from audit | logging/audit modules | Complete | Separate privacy-safe diagnostics and audit. |
| NFR-054 | Self-diagnosis | health/errors/correlation IDs | Partially Complete | App-level diagnostics exist; installer/runtime/model repair diagnostics not delivered. |
| NFR-055 | Actionable error surfaces | delivery/error contracts | Complete | Plain-language remediation and optional details. |
| NFR-056 | Source immutability | I-SI/I-VD | Complete | Read-only handling and fingerprints verified. |
| NFR-057 | Transactional consistency | repositories/migrations | Complete | Result/lifecycle commits are transactional. |
| NFR-058 | Content fingerprinting | source/run/artifact hashes | Complete | SHA-256 identities broadly used. |
| NFR-059 | Financial arithmetic precision | Decimal/money/oracle tests | Complete | No binary-float financial core. |
| NFR-060 | User backup and restore | Architecture only | Not Started | No product backup/restore workflow. |
| NFR-061 | Storage failure containment | transaction/failure tests | Complete | Prior committed state is retained. |
| NFR-062 | No silent failure | failure contracts/UI | Complete | Failures surface codes/remedies. |
| NFR-063 | Safe AI failure | I-AI | Complete | Ollama unavailable leaves deterministic features intact. |
| NFR-064 | Input error recovery | I-SI/I-VD | Complete | Replace/retry/revert paths exist. |
| NFR-065 | Responsive layout | UI tests/screenshots; E-S2/E-CLOSE | Partially Complete | Wide desktop behavior is strong, but the current suite proves a 200% appearance-control clipping failure and an order-dependent Ask Fin drawer collapse below its required width. |
| NFR-066 | Progressive disclosure by severity | Overview/Findings/evidence | Complete | Executive summary drills into details. |
| NFR-067 | Explainability in one click | Explain This/Show Evidence | Complete | Direct finding evidence is available. |
| NFR-068 | Workflow efficiency versus manual baseline | no measured study | Not Started | No timed finance-user comparison. |
| NFR-069 | Low-friction verification | Verify Data UX | Complete | Compact tables, source details on demand and confirmation gate. |
| NFR-070 | Core independence from desktop | ports/fitness tests | Complete | Headless domain/application tests. |
| NFR-071 | Multi-user readiness in data design | actor/role/version model | Complete | Sequential machine actors and attributable history supported. |
| NFR-072 | Storage substitutability | repository ports | Partially Complete | Ports exist; only local encrypted SQLite implementation is qualified in tests. |
| NFR-073 | Specification-driven development | extensive SDD package | Partially Complete | Process followed, but approved normative artifacts/baseline were not fully reconciled. |
| NFR-074 | Agent assistance with human accountability | approvals/reviews | Complete | Human approvals and independent reviews are recorded. |
| NFR-075 | Quality gates apply to all code | verification suites; E-CLOSE | Partially Complete | A current full regression now exists and is red: 4 failed, 1,212 passed, 2 subtests. |
| NFR-076 | Verifiable financial logic | oracle/Decimal/rule tests | Complete | Independent oracle matches. |
| NFR-077 | Consistent standards | code/test/docs | Partially Complete | Generally strong; protected ID and lifecycle drift are exceptions. |
| NFR-078 | Static analysis | changed-scope checks | Partially Complete | Verification notes legacy repository-wide Ruff debt; no clean full static-analysis release evidence. |
| NFR-079 | Dependency hygiene | dependency checks | Partially Complete | Checks pass with documented nonblocking drift; license/release review still required. |
| NFR-080 | Reviewability of changes | changed-file inventories/reviews | Complete | Stage evidence includes inventories, screenshots and independent verdicts. |

## 9. Implemented behavior without a reconciled formal requirement

| Behavior | Evidence | Classification | Required documentation action |
|---|---|---|---|
| Ask Fin automatically becomes ready when an observed loopback Ollama model is available; manual local-identity approval is removed | `private_ask_fin.py`; `ollama.py`; E-AFS | Implemented after the governing V2/Stage 2 text | Add a governed requirement/architecture delta describing automatic per-provider-session pinning, managed digest override, pre-prompt re-verification, unavailable message and Retry. |
| Landing page intentionally omits Recent Reviews and the actor/profile block | Home view; E-UX | Later explicitly approved UX direction | Mark REM-FR-001 and the older V2 Home inventory as superseded in the normative baseline. |
| Results navigation opens Overview and uses exactly Overview, Financial Analysis, GED Detail, Findings, Review Summary | `financial_review_view.py`; E-S2 | Later governed Stage 2 UX contract | Reconcile FR-185 “Summary first” and older nine-tab UX text with the approved five-section experience. |
| Verify Data hides the internal table index and makes source evidence on-demand | working-set/source-detail views; E-UX | Approved Rapid UX Lane change | Add a compact UX amendment to the current product specification; no business semantic change. |
| Seven visible workflow steps present the eleven logical workflow activities | desktop stepper; E-MVP/E-REM | Approved simplification, but terminology remains split | Document “seven visible stages / eleven logical activities” once and remove conflicting eight/nine/eleven-step presentation language. |
| CORE-04 checks Budget EAC/DELTA/financial completeness in addition to GED required fields | `financial_validation.py:1030-1189`; REM-FR-007; E-S1 | Implemented with material protected-rule impact | This cannot be cured by documentation alone. Govern it as a new protected version or remove it from CORE-04 and create a separate optional/core control through approval. |
| Production rule identities are `CORE-01` through `CORE-05` | `financial_validation.py:24-35`; rule/result persistence and UI | Implemented contrary to permanent-ID contract | Governed product decision required: rebaseline permanent IDs to `CORE-*` or migrate implementation/history to `R-VAL-*`. |

## 10. Documented requirements no longer aligned with the current product direction

| Source requirement / artifact | Current direction | Classification | Action |
|---|---|---|---|
| Root FR-004 generic document classification | Two explicit Budget/GED upload roles | Superseded | Mark root requirement superseded by FR-126. |
| Root FR-012 three-sheet Budget Tracker | Supplied `Original Budget` worksheet and columns A:H | Superseded | Mark root requirement superseded by FR-180/181. |
| Root FR-016 confidence indication | Deterministic extraction/data-quality states; no invented confidence | Superseded | Replace confidence-scoring language with validity/coverage evidence. |
| Root FR-024 quarantine every malformed item | Preserve malformed GED transaction candidates, but reject unsafe/ambiguous source structures | Superseded | Cross-reference FR-132/183 and CORE-04. |
| Root FR-029 per-document verification decision | One paired reviewed-basis confirmation | Superseded | Cross-reference FR-139/140/192. |
| Root FR-088/096/097 external-provider consent/selection | Local loopback Ollama only, no external transmission | Superseded for current MVP | Retain as deferred requirements for any future organization-private external provider. |
| FR-185 and UX/UI §11 “Review Summary first” | Approved Stage 2 opens Overview first and keeps Summary as a primary tab/action | Superseded | Formally amend FR-185; do not revert the approved Stage 2 UI. |
| REM-FR-001 Recent Reviews on Home | Approved landing intentionally removes Recent Reviews | Superseded | Update remediation delta or append an explicit supersession note. |
| Architecture/UX/Implementation Plan headers still say Draft | Architecture and Requirements approval records show PASS and implementation authorization | Documentation debt | Update status metadata without rewriting decision history; link approval record and effective date. |
| Architecture Ask Fin profile/setup/consent language | Automatic local Ollama readiness and no setup approval in normal case | Documentation debt | Add the Ask Fin simplification delta and update operational/deployment sections. |
| Architecture/plan promise of PDF/XLSX, backup/restore, full disposal, Windows installer | These capabilities are not implemented in the current product | Valid but incomplete | Keep active and classify as pre-packaging work, not as completed architecture. |

## 11. Traceability-based mandatory corrections

| Classification | Specific issue | Affected requirements | Proposed action | Verification method |
|---|---|---|---|---|
| Must fix before packaging | Permanent protected Rule IDs conflict with approved `R-VAL-*` contract | FR-143, FR-154, FR-159–164; NFR-089–091, NFR-099 | Make one governed ID decision; migrate code/data/tests/evidence or formally rebaseline with historical replay preservation. | Seed-baseline migration tests; old/new run replay; traceability and independent finance-governance review. |
| Must fix before packaging | CORE-04 protected semantics expanded without governed version | FR-144, FR-162, FR-164; NFR-089–091 | Restore exact six-field GED scope or approve/version a successor and place Budget formula checks in a distinct governed rule. | Positive/negative/boundary suite; exact expected scope count; synthetic oracle and two-person approval evidence. |
| Must fix before packaging | Successor run auto-publishes | FR-173, FR-202; NFR-082, NFR-091 | Keep successor Working/Unpublished; add explicit Reviewer promotion with reason and atomic pointer move. | Integration/fault/race tests proving trusted defaults remain on prior published run until promotion. |
| Must fix before packaging | Current full governed regression is red | REM-NFR-005; root NFR-075 | Correct the four failures and all material stabilization defects, then rerun the complete suite plus static/dependency checks and independent full-product review. | One timestamped clean full-suite report from the immutable release-candidate commit. |
| Must fix before packaging | Windows installer/runtime/model provisioning and clean-machine qualification absent | FR-175–178; NFR-094–095; root NFR-028–030 | Complete a stabilization gate first, then implement/qualify signed Windows packaging, automatic Ollama/model provisioning, repair/upgrade/uninstall. | Clean Windows 11 matrix, standard user, no terminal, offline one-click launch, signature/SBOM/license/tamper evidence. |
| Must fix before pilot | Post-validation source/edit re-verification successors are deferred | FR-196, FR-203 | Implement reason-specific successor candidates with fresh confirmation and retained prior trusted result. | Source/edit/extractor-change E2E and reconstruction tests. |
| Must fix before pilot | Advisory classification is promised but not executable | FR-141/142/146/150; NFR-098 | Implement advisory lifecycle/statuses/evidence in the same engine or formally defer it from the MVP baseline. | Advisory positive/negative/boundary, ledger, UI and historical-replay tests. |
| Must fix before pilot | Validation progress is not actual engine progress | FR-179 | Wire bounded engine progress events to current rule/scopes/completed/not-evaluated values. | UI/accessibility tests with deterministic event fixtures and cancellation. |
| Must fix before pilot | Native assistive-technology verification remains pending | NFR-092; REM-NFR-001/002 | Run Windows Narrator and one approved additional screen-reader keyboard journey; fix material issues. | Signed manual accessibility script/results and screenshots/video where policy permits. |
| Must fix before packaging | Backup/restore and complete disposal are absent | FR-201; NFR-101; root NFR-017/060 | Implement or explicitly remove from first release scope through requirements change control. If retained, complete review/period/all-data, managed backup and replacement restore. | Crash/fault/restore/disposal drills on clean machines. |
| Should fix | Publication state missing from some identity surfaces | FR-193/194 | Add one consistent identity component sourced from selected generation/run. | UI/export/Ask Fin identity tests. |
| Should fix | Approved artifacts still carry Draft metadata and conflicting workflow counts | NFR-034/073/099 | Reconcile normative status, supersession and presentation terminology without rewriting history. | Documentation cross-check and requirements review PASS. |
| Deferred | Multi-period trends, invoice/resource/contract controls and broader source layouts | Root FR-002, FR-017–020, FR-032/036, FR-051–068, FR-073/078/109/110/112–115 | Retain as governed future scope; do not imply MVP completion. | Future requirements/architecture gates. |

## 12. Matrix conclusion

The current product is **not traceability-ready for packaging**. It is suitable for continued synthetic-data stabilization and manager review, but the mandatory protected-rule and publication defects affect the trust contract, and the Windows/runtime/model/recovery release obligations have not started.

The immediate governed stage supported by this matrix is **Stabilization and Regression**. It should:

1. resolve protected Rule ID and CORE-04 semantic governance;
2. correct successor publication and implement or formally scope the source/edit successor gap;
3. reconcile advisory-rule and progress requirements;
4. reconcile the normative requirement/architecture baseline with later approved UX and Ask Fin decisions;
5. run the complete regression, independent financial oracle, security/privacy tests, accessibility qualification, and static/dependency checks from one release-candidate commit.

Packaging, model redistribution/provisioning, exports, and broad new product capabilities must not begin until that stabilization gate exits with no unresolved material requirement defect.

## 13. Exact governing and verification sources read for this matrix

### Root product baseline

- `docs/00-project-understanding.md`
- `docs/01-functional-requirements.md`
- `docs/02-non-functional-requirements.md`
- `docs/03-epics.md`
- `docs/04-features.md`
- `docs/07-ux-design.md`
- `docs/08-ui-design-system.md`
- `docs/11-development-methodology.md`
- `specs/01-functional-requirements.md`
- `specs/02-non-functional-requirements.md`

### V2 requirements, architecture, workflow, and governance

- `initiatives/configurable-rule-engine-v2/README.md`
- `briefs/PRODUCT-DIRECTION-SOURCE-configurable-rule-engine-v2.md`
- `briefs/IMPLEMENTATION-BRIEF-configurable-rule-engine-v2.md`
- `requirements/README.md`
- `requirements/GOVERNED-V2-DELTA-2026-07-27.md`
- `requirements/REQUIREMENTS-PHASE-COMPLETION-2026-07-27.md`
- `requirements/MVP-REMEDIATION-DELTA-2026-07-28.md`
- `specs/constitution.md`
- `specs/01-functional-requirements.md`
- `specs/02-non-functional-requirements.md`
- `specs/03-existing-rule-disposition.md`
- `specs/clarifications/CLARIFICATION-PACKET-2026-07-27.md`
- `specs/generated/SPEC-AUDIT-2026-07-27.md`
- `SPEC-AUDIT-2026-07-27-FULL-REVIEW.md`
- `SPEC-CROSSCHECK-2026-07-27.md`
- `SPEC-AUDIT-2026-07-27-RECHECK.md`
- `docs/FINANCIAL-REVIEW-WORKFLOW.md`
- `docs/APPLICATION-ARCHITECTURE.md`
- `docs/RULE-ENGINE-DESIGN.md`
- `docs/PERSISTENCE-MODEL.md`
- `docs/UX-UI-DESIGN.md`
- `docs/STAGE-2-MODERN-UX-AND-PRODUCT-DESIGN-2026-07-29.md`
- `plans/EXECUTION-LANES.md`
- `plans/TECHNICAL-IMPLEMENTATION-PLAN.md`
- `readiness/ARCHITECTURE-APPROVAL-2026-07-27.md`
- `readiness/ARCHITECTURE-STAGE-PACKAGE-2026-07-27.md`
- `reviews/REVIEW-2026-07-27-configurable-rule-engine-product-definition.md`
- `reviews/REVIEW-2026-07-27-product-owner-amendments.md`
- `reviews/REVIEW-2026-07-27-architecture-stage.md`

### Verification evidence

- `verification/WORKFLOW-01-VERIFICATION-2026-07-27.md`
- `verification/WORKFLOW-02-VERIFICATION-2026-07-27.md`
- `verification/MVP-END-TO-END-VERIFICATION-2026-07-27.md`
- `verification/MVP-FINAL-REMEDIATION-VERIFICATION-2026-07-28.md`
- `verification/STAGE-1-FINANCIAL-CORRECTNESS-VERIFICATION-2026-07-29.md`
- `verification/STAGE-2-CONSOLIDATED-VERIFICATION-2026-07-29.md`
- `verification/STAGE-2-FOLLOWUP-ASK-FIN-NAVIGATION-RULES-2026-07-29.md`
- `verification/STAGE-2-ASK-FIN-SIMPLIFICATION-2026-07-29.md`
- `verification/FINAL-LANDING-PAGE-VERIFICATION-2026-07-28.md`
- `verification/RAPID-UX-LANDING-SCALE-2026-07-28.md`
- `verification/RAPID-UX-VERIFY-DATA-SOURCE-DETAILS-2026-07-28.md`

### Implementation/test sampling

The implementation keys in §2 were inspected directly. The complete test-file inventory under `tests/` was reviewed by area, with detailed inspection focused on financial validation, source extraction, reconstruction, rule lifecycle/governance, result projection, Ask Fin/Ollama privacy, lifecycle/publication, disposal, migrations, accessibility, UI journeys, and architecture fitness. No production code or test code was modified for this review.
