# FinSight SDD Closeout and Next-Stage Review

**Review date:** 2026-07-29
**Review type:** Specification-Driven Development closeout, reconciliation, and recommendation
**Source branch / reviewed HEAD:** `codex/configurable-rule-engine-v2` / `a298040a8408c04342818a65a186a0d72c87956a`
**Production-code changes made by this review:** None
**Packaging-readiness decision:** **Not ready for packaging**
**Recommended next governed stage:** **Option C — Stabilization and Regression**
**Final product gate:** **NO-GO**

## Executive Summary

FinSight is no longer a prototype. It has a substantial, coherent desktop product:
the guided Budget/GED review workflow works; source workbooks are read without being
modified; reviewed values, audit history, rule versions, validation runs, Findings,
evidence, and historical reviews persist; the five baseline controls and configurable
optional rules run through a deterministic engine; Stage 1 delivered a canonical
financial dataset and source-linked analysis; and Stage 2 delivered the modern
five-section Financial Review, deterministic **Explain This**, and local-only Ask Fin.

That progress is real, but the current repository is **not a release candidate**.
Closeout verification found defects that prior fixture-based evidence did not reveal:

1. the current full suite is red: **4 failed, 1,212 passed, 2 subtests passed**;
2. the protected CORE-04 implementation silently includes 71 Budget/formula scopes
   that are outside the approved GED-only protected contract;
3. optional-rule failures can change Overall Review Status, contrary to the approved
   core-only status policy;
4. RAG, Budget Health, Data Quality, reconciliation, duplicate, and missing-data
   projections do not all follow the exact approved policy;
5. duplicate groups larger than two understate exposure and duplicate count;
6. valid GED rows after the selected reporting month are included in CORE-01/CORE-05;
7. protected rule IDs in persisted results use `CORE-*` aliases instead of the
   approved permanent `R-VAL-*` IDs;
8. successor reanalysis is automatically published instead of requiring explicit
   Reviewer promotion and reason;
9. post-validation source/edit successor handling and advisory-rule execution remain
   incomplete;
10. the modern PDF/spreadsheet export obligations and managed backup/restore are not
    delivered;
11. the current V2 implementation is not captured in an immutable source revision:
    29 tracked files are modified and 809 files are untracked; and
12. no Windows MSI, signed build, clean-machine evidence, automatic local-AI runtime
    provisioning, model provisioning, repair, upgrade, or uninstall evidence exists.

The May 2026 synthetic workbook arithmetic still reconciles under the current encoded
oracle: BGT `$10,372,000.00`, ATD/parseable GED `$3,500,095.00`, ETC
`$5,882,000.00`, EAC `$9,382,095.00`, and DELTA `$989,905.00`. The oracle is not,
however, sufficient release proof because it was changed to expect the unapproved
CORE-04 scope expansion.

The immediate next stage must therefore be **Stabilization and Regression**. Packaging,
new analytics, additional source types, and new AI features must not start yet.

## Original Product Objective

The original project-understanding document described an Amerisure/Application
Engineering financial-review assistant spanning Budget, GED, invoices, contracts,
resources, and eventual forecasting. Its enduring principles were:

- financial truth is deterministic;
- AI explains but never decides;
- FinSight is read-only with respect to external financial systems;
- every conclusion is auditable and attributable; and
- humans remain responsible for every financial action.

The later approved V2 initiative intentionally narrowed and generalized the MVP:

- one FinSight product, repository, and application;
- usable by any department with the approved Budget/GED layouts;
- two source roles only: Budget Report and GED Report;
- a configurable, versioned deterministic rule engine as the single source of
  validation truth;
- five protected baseline controls plus governed optional/advisory extensibility;
- a guided review workflow rather than a generic validation utility;
- private local Ask Fin for explanation only; and
- a governed Windows installer as the eventual release deliverable.

The V2 direction is the current product contract. Root requirements that describe
Application Engineering, invoice/resource phases, public-provider consent, a
three-sheet tracker, or a nine-tab/summary-first result experience are historical,
superseded, or deferred where the V2 matrix says so. They must not silently re-enter
the MVP.

## Completed Work

The status below assesses implemented behavior against the latest approved direction,
not merely whether an artifact exists.

### Foundation, product definition, and SDD

| Area | Original objective | Implemented behavior | Verification evidence | Known limitation | Status |
|---|---|---|---|---|---|
| Foundation | Understand the repository, source reports, business process, and deterministic/AI boundary before implementation. | Root project understanding, requirements, epics, features, rule catalog, architecture, UX, decision log, AI plan, methodology, readiness runbook, and walking skeleton were created. | `docs/00-project-understanding.md` through `docs/13-walking-skeleton-plan.md`. | Root documents still contain historic customer/department, external-provider, invoice/resource, and Release 1 language. | **Partially Complete** |
| Product vision | Evolve, rather than fork, FinSight into a department-neutral configurable financial-validation platform. | V2 is organized under one initiative in the existing repository and reuses the existing application. | V2 `README.md`, Product Direction Source, implementation brief, requirements completion. | Product-wide baseline has not been formally reconciled; several superseded root statements remain prominent. | **Partially Complete** |
| Requirements | Define auditable functional/non-functional requirements for workflow, rules, persistence, identity, results, Ask Fin, and packaging. | Root FR-001–122/NFR-001–080, V2 FR-123–203/NFR-081–110, and remediation deltas exist and are traced. | Updated traceability matrix; requirements review and generated spec audits. | Several approved files still say Draft; permanent rule IDs, CORE-04, successor publication, exports, backup, and packaging do not align with implementation. | **Partially Complete** |
| Architecture | Specify the application, rule engine, persistence, audit, identity, results, AI, and Windows packaging. | Modular-monolith design, SQLCipher store, audit streams, role governance, protected-rule lifecycle, local Ask Fin, and WiX/PyInstaller target architecture are documented. | Architecture package, ADR-V2-001–007, independent architecture review. | ADR headers remain Proposed; parts of the approved architecture (backup, Windows delivery, advisory execution) are plans only. | **Partially Complete** |
| SDD process | Use requirements and architecture gates, stage packages, one independent review, evidence, and explicit stop points. | Product-owner, requirements, architecture, Workflow 1/2, remediation, Stage 1, Stage 2, follow-up, and Rapid UX evidence exists. | Readiness, review, verification, task, and screenshot directories. | Gate state is not reconciled: Stage 1/2 records still say hands-on approval pending, and there is no final-product approval record. | **Partially Complete** |
| Execution lanes | Separate governed logic/data work from presentation-only Rapid UX work. | `EXECUTION-LANES.md` is present; landing, scale, and source-details changes used focused UI/accessibility/launch verification. | Rapid UX verification records and Stage 1/2 governed plans. | The latest governed Ask Fin changes received focused tests only; a later full run now exposes regressions. | **Complete as a process; current baseline fails its release gate** |

### Core workflow

| Area | Original objective | Implemented behavior | Verification evidence | Known limitation | Status |
|---|---|---|---|---|---|
| Review creation | Create a monthly review with period, persistence, lifecycle, and audit. | Welcome, Create Review, month/year selection, saved reviews, lifecycle status, restart restoration, creation/reopen audit. | Workflow 1 verification and tests. | Production first-run depends on a provisioned identity/authorization source and machine store. | **Complete for development/pilot workflow** |
| File upload | Accept exactly one Budget and one GED report and preserve original files. | Two role-specific upload cards, safe replacement/removal, byte fingerprints, read-only extraction, counts, and metadata. | Workflow 2 verification; extractor/safety tests. | Only the approved `SLV-001` layouts are supported; source bytes are not managed copies. | **Complete for approved layouts** |
| Extraction | Validate workbook, worksheet, headers, row types, department, period, and file safety. | Budget and GED layouts, row 7 GED header, total/subtotal exclusion, department/period mismatch gates, resource ceilings, safe failures. | Workflow 2 and Stage 1 extractor/oracle evidence. | No alternative layouts or user-created mapping profiles. | **Complete for approved layouts** |
| Data verification | Review, search, sort, edit, revert, confirm, and preserve original/current values. | Separate Budget/GED tables, working-copy corrections, confirmation, history, source details, reversible audit, unchanged source files. | MVP remediation verification and correction tests. | Post-validation source/edit successor flow is explicitly deferred in legacy transition code and not fully aligned with FR-196. | **Partially Complete** |
| Rule selection | Show the active five protected rules and configurable optional rules before validation. | Simplified Rules Repository, core badges/details, optional create/edit/test/activate/disable/retire, advanced governance on demand. | Remediation and Stage 2 follow-up verification. | Advisory rules are modeled but not executable; protected permanent IDs and CORE-04 semantics drift. | **Partially Complete** |
| Validation | Execute deterministic rules against confirmed reviewed data and retain a sealed ledger. | Confirmed-basis execution, rule/scope results, Findings, rule-set/run/review identities, append-only run history. | Stage 1 tests/oracle and persisted-run tests. | Material rule/status/period/duplicate defects remain; progress UI is timer-driven rather than actual engine progress. | **Partially Complete — release blocking** |
| Review results | Present decision-oriented results and drill-downs without reopening Excel. | Overview, Financial Analysis, GED Detail, Findings, and Review Summary consume recorded review data. | Stage 2 verification and current screenshot audit. | Status projections are wrong in boundary cases; modern PDF/spreadsheet exports are absent. | **Partially Complete** |
| Past reviews | Preserve, reopen, compare, close/archive, and dispose of reviews. | Saved reviews reopen with retained results; run comparison and review disposal exist. | Workflow 1, Stage 1, remediation tests/screenshots. | Reanalysis auto-publishes; managed backup copies and broad period/all-data disposal are absent. | **Partially Complete** |
| Persistence | Keep financial/audit/governance state encrypted, attributable, and replayable. | SQLCipher store, migrations through 0014, OS identity, signed-role source support, audit streams, source bindings, retained versions/results. | Persistence, security, migration, restart, and disposal tests. | No implemented managed backup/restore/replacement-machine recovery; Windows DPAPI/ACL behavior is not natively qualified. | **Partially Complete** |

### Stage 1 — Financial correctness and hierarchy

| Area | Original objective | Implemented behavior | Verification evidence | Known limitation | Status |
|---|---|---|---|---|---|
| Canonical financial dataset | One deterministic dataset for validation, charts, tables, evidence, exports, and future AI. | Review → Department → Account → Budget summary → GED transaction hierarchy with source lineage and recorded projections. | Stage 1 hierarchy spec, financial review service, oracle, screenshots. | Some reusable vendor/descriptive counts are still assembled in the UI; approved period eligibility is not enforced in aggregate logic. | **Partially Complete** |
| Budget/GED reconciliation | Exact Department + Account matching with Decimal arithmetic and explicit incompleteness. | Exact two-decimal totals, mapped/unmapped GED, no account-only join, missing Amount produces NOT_EVALUATED. | Current oracle/core tests and Stage 1 records. | A valid row after the selected reporting month is wrongly included; CORE-04 oracle encodes unapproved Budget scopes. | **Partially Complete — release blocking** |
| Financial hierarchy | Drill from review to department/account/transactions/source evidence. | Account, vendor, department, Budget-vs-Actual, reconciliation, GED, finding, and source drill-downs. | Stage 1/2 UI tests and screenshots. | Only source-supported hierarchy is available; no invented expense-type/project layer. | **Complete for approved data** |
| Five protected rules | Always run the baseline budget-overrun, mapping, exact-duplicate, required-field, and ATD-reconciliation controls. | Five seeded controls run and produce the known synthetic findings. | Stage 1 oracle and result ledger. | Permanent IDs, CORE-04 scope, status projection, duplicate 3+ boundary, period eligibility, and fingerprint canonicalization require correction. | **Partially Complete — release blocking** |
| Optional rules | Add rules without redesigning the application; version, activate, disable, rerun, compare, and retain history. | A closed deterministic amount-threshold rule family supports governed lifecycle and rerun comparison. | Rule-management tests and Stage 1 screenshots. | Optional failures improperly affect Overall Status; the extensibility family is intentionally narrow. | **Partially Complete** |
| Rule versioning/revalidation/replay | Preserve old definitions, rule sets, runs, results, and comparisons. | Immutable versions and successor rule sets/runs are retained; added/removed/changed outcomes can be compared. | Rule governance/replay tests. | Reanalysis is auto-published; protected ID/semantic drift weakens historical contract identity. | **Partially Complete** |
| Findings/evidence | Explain each failure with exact inputs, source rows/cells, values, and follow-up. | Structured Finding evidence, source navigation, contributing transactions, expected/actual, original/current, rule/run/version. | Stage 1 and Stage 2 evidence tests/screenshots. | Explain This can overload users with long raw row lists; current rule identity is not the approved permanent ID. | **Partially Complete** |
| Financial correctness verification | Independently reproduce totals and intentional cases outside FinSight. | A stdlib OOXML/Decimal verifier reproduces the supplied fixture and five current findings. | Independent oracle JSON/script and current 29-test focused run. | Oracle expectations were changed to match unapproved CORE-04 behavior; boundary cases exposed by closeout are missing. | **Partially Complete — release blocking** |

### Stage 2 — Modern review and private Ask Fin

| Area | Original objective | Implemented behavior | Verification evidence | Known limitation | Status |
|---|---|---|---|---|---|
| Modern UI | Replace the older cream-heavy/technical experience with a modern, minimal financial workspace. | Neutral cards, semantic colors, Light/Dark/System, responsive desktop shell, back navigation, simplified technical disclosure. | Stage 2 screenshots, accessibility tests, current visual audit. | Current 200% appearance control and Settings keyboard-focus tests fail. | **Partially Complete** |
| Results navigation | Reduce result navigation to five primary sections with focused secondary analysis. | Overview; Financial Analysis; GED Detail; Findings; Review Summary. | Stage 2 verification and current screenshots. | A complete legacy result shell is still instantiated and reachable by internal navigation. | **Partially Complete** |
| Overview | Answer status, Budget, Actual, EAC, variances, and priorities quickly. | KPI cards, account comparison, findings/severity, incompleteness disclosure, priority actions. | Current Light/Dark `01-overview` screenshots and Stage 2 tests. | Boundary status/RAG values are wrong because the domain projector is wrong. | **Partially Complete** |
| Financial Analysis | Provide account, vendor, department, Budget-vs-Actual, and reconciliation analysis from recorded data. | All five secondary views and direct values/drill-downs are present. | Stage 2 screenshots/tests. | No authoritative prior-period vendor comparison; correctly disclosed instead of fabricated. | **Complete for available source data** |
| GED Detail | Search/filter/drill into transactions and source evidence. | Transaction table, filters, details, related account/findings, source location. | Stage 2 GED screenshots/tests. | No approved source confidence or transaction-type field is invented. | **Complete for approved data** |
| Findings workflow | Make Findings the primary exception-review surface with status and evidence. | Severity/status filters, plain-language finding rows, audited status updates, Explain This and Ask Fin actions. | Stage 2 findings screenshots/tests. | The current table is dense and some content is ellipsized at supported widths. | **Partially Complete (UX debt)** |
| Explain This | Deterministically explain findings without an LLM. | What happened, why flagged, why it matters, expected/actual, evidence, contributing transactions, follow-up, collapsed technical details. | Finding-explanation tests and Stage 2 screenshots. | Long contributing-row citations dominate the panel for large account findings. | **Complete functionally; UX refinement should follow stabilization** |
| Private Ask Fin | Explain only authorized recorded FinSight facts through local Ollama. | Local Help/Financial Review modes, closed supported claims, citations, review isolation, pre/post prompt verification, refusals, audit, fail-closed output verifier. | Stage 2 privacy/security tests and real local-Ollama evidence. | Runtime/model are external unmanaged prerequisites; enterprise distribution, license, resource, update, repair, and uninstall plans are absent. | **Partially Complete** |
| Ollama integration | Use loopback only, no public API or cloud fallback, and recover with Retry. | Loopback/DNS/peer enforcement, proxies/redirects disabled, cloud-style aliases rejected, model profile/digest verification, automatic readiness, one-message Retry state. | Provider/private-AI tests, simplification verification, current unavailable-state capture. | No installer-managed service/model, firewall/cloud-feature hardening, fixed managed digest, response-byte cap, or concurrency qualification. | **Partially Complete** |
| Decision boundary | AI may explain, summarize, cite, and refuse; it may not decide or mutate. | Direct and subtle decision prompts are refused before/after generation; no command ports are exposed. | Private Ask Fin decision-boundary and response-verifier tests. | A local model remains probabilistic; safety depends on the closed claim/citation verifier and must remain fail-closed. | **Complete for implemented path** |
| Global Back navigation | Preserve logical history across workflow, drill-down, Settings, and evidence. | A global history layer and view-specific fallbacks exist. | Stage 2 follow-up tests/screenshots. | Settings Back currently has `NoFocus` in the fresh full suite. | **Partially Complete** |
| Simplified Rules Repository | Hide hashes/approval machinery from ordinary review while retaining governance. | Human-readable rule list/details and contextual advanced governance. | Follow-up screenshots/tests and current Rules screenshot. | Advisory class missing; advanced legacy/governance paths and duplicate shells increase maintenance risk. | **Partially Complete** |

## Requirements Traceability

The complete matrix is:

[Updated Requirements Traceability Matrix](UPDATED-REQUIREMENTS-TRACEABILITY-MATRIX-2026-07-29.md).

It covers every approved identifier in:

- root FR-001–FR-122;
- root NFR-001–NFR-080;
- V2 FR-123–FR-203;
- V2 NFR-081–NFR-110; and
- REM-FR-001–REM-FR-020 / REM-NFR-001–REM-NFR-005.

The most important traceability conclusions are:

- **Complete:** the guided two-file workflow, source preservation, approved-layout
  extraction, review-local corrections, optional-rule lifecycle, structured evidence,
  local Ask Fin grounding/refusal, and historical result retention have strong
  implementation/test evidence.
- **Partially Complete:** protected rule identity/semantics, status policy, review
  successor publication, post-validation correction flow, validation progress,
  native accessibility, modern exports, disposal breadth, and secure release
  provisioning.
- **Not Started:** advisory-rule execution, managed backup/restore, current PDF/XLSX
  deliverables, Windows MSI lifecycle, signing/provenance, automatic Ollama/model
  provisioning, clean-machine qualification, and measured finance-user efficiency.
- **Superseded:** generic multi-document upload, public-provider consent for the local
  MVP, Review Summary as the first results page, Recent Reviews on the landing page,
  and several older source/layout assumptions.
- **Deferred:** invoices, resource/contract analysis, forecasting, what-if analysis,
  multi-period trends without authoritative data, broader source layouts, and
  additional AI providers.

Implemented but unreconciled behavior includes the five-section Stage 2 navigation,
local-only automatic Ask Fin readiness, and remediation-era Budget checks placed inside
CORE-04. The first two should be formally captured as supersessions/deltas. The last is
a protected-rule defect and must not be normalized by documentation after the fact.

## SDD Compliance Assessment

### What complied

- The product remained in one repository and initiative.
- Requirements and Architecture each had consolidated independent reviews and recorded
  approval gates.
- Workflow 1 and Workflow 2 were implemented end-to-end rather than screen-by-screen.
- Governed Lane work included requirements/architecture/test/evidence updates.
- Rapid UX work used scoped tests and screenshots as explicitly authorized.
- Stage 1 used an external OOXML/Decimal oracle rather than trusting the application
  alone.
- Stage 2 separated deterministic Explain This from probabilistic Ask Fin and performed
  independent financial, visual/accessibility, and privacy reviews.
- Important source, run, rule-set, and evidence identities are recorded.

### What did not fully comply

- Approved requirements/ADRs still carry Draft/Proposed headers, so approval records and
  normative artifacts disagree.
- The approved permanent protected IDs and CORE-04 contract were not preserved.
- A successor run is published automatically despite the explicit promotion contract.
- Later focused Stage 2 changes were not followed by a governed full regression; the
  fresh closeout run is now red.
- The current implementation is largely uncommitted, so independent evidence cannot be
  tied to an immutable V2 revision.
- Stage 1 and Stage 2 records still say Project Owner hands-on review is pending. No
  evidence closes the Final Product gate.

**SDD conclusion:** The process produced unusually strong evidence, but the current
baseline is **Partially Compliant**, not release-complete. Specification conformance
must be restored before the Packaging and Release gate.

The [independent closeout review](INDEPENDENT-CLOSEOUT-REVIEW-2026-07-29.md)
returned **PASS** after a focused recheck closed one traceability-consistency defect.
That PASS validates this review package; it does not change the product's current red
regression, **Not ready for packaging** decision, or Option C recommendation.

## Specification Drift

| Issue | Classification | Evidence | Assessment / correction |
|---|---|---|---|
| Root docs still define an Amerisure/Application Engineering, multi-artifact, external-provider product. | **Documentation debt** | `docs/00-project-understanding.md`, root FR/NFR/architecture/AI docs. | Preserve as historical foundation, but add an explicit current-baseline/supersession map pointing to V2. |
| Approved permanent IDs are `R-VAL-01..05`, while persisted definitions/results use `CORE-01..05`. | **Material defect** | V2 FR §2.12/§12; `financial_validation.py`; rule management and tests. | Govern a baseline/migration decision; aliases and permanent identities must not be conflated. |
| CORE-04 includes Budget financial/formula scopes outside its approved GED-only contract. | **Material defect** | V2 FR-162/§12; rule design §10; `financial_validation.py:1083-1188`; oracle scope count. | Remove the extra scopes or create a separately governed rule; regenerate oracle and replay evidence. |
| Optional outcomes alter overall status and RAG/status projections differ from §2.7. | **Material defect** | `financial_validation.py:689-750`; direct closeout probes. | Implement one core-only persisted status projector and exact summary sources. |
| A May review includes valid June GED in CORE-01/05 aggregates. | **Material defect** | FR §11.3–11.5; closeout boundary probe. | Enforce selected-year/month eligibility before aggregation. |
| Reanalysis completion auto-publishes the successor. | **Material defect** | FR-202; `financial_review.py:607-627`. | Keep successor Working/Unpublished until explicit Reviewer promotion with reason. |
| Advisory rules are declared but not executable. | **Product misalignment** | FR-141/146 and rule design; engine rejects classification. | Implement OBSERVATION/NO_OBSERVATION through the common engine or formally defer the class. |
| Validation progress is timer presentation, not engine progress. | **UX debt** | FR-179; `financial_review_view.py` discards stages. | Wire real rule/scope progress and NOT_EVALUATED counts after financial stabilization. |
| Overview remains decision-oriented and Findings remains the exception workflow. | **Acceptable limitation** | Current Stage 2 screenshots and navigation. | No BI-style expansion is recommended. Keep existing five-section structure. |
| Explain This is deterministic but exposes very long row lists. | **UX debt** | Current `09-explain-this-open` screenshots. | Summarize key contributors and collapse the exhaustive source list without hiding evidence. |
| Ask Fin remains explanatory/non-authoritative. | **Acceptable limitation** | Closed-claim verifier, refusals, citations, no command ports. | Retain strict fail-closed boundary; do not expand authority. |
| Rules Repository default is simplified. | **Acceptable limitation** | Current Rules screenshot and follow-up tests. | Advanced governance may remain behind role/context disclosure. |
| Legacy result shell and legacy AI/engine composition remain packaged beside V2 paths. | **Technical debt** | `main_window.py:61-109`; `app.py` legacy and V2 builders. | Remove or prove compile/package-time exclusion before packaging. |
| Review Summary first-screen requirement conflicts with approved Stage 2 Overview-first navigation. | **Documentation debt** | FR-185 versus approved Stage 2 source/implementation. | Mark FR-185 superseded; do not regress Stage 2 navigation. |

## Financial Correctness Assessment

### Reconfirmed fixture controls

| Control | Closeout result |
|---|---:|
| Budget detail records | 71 |
| GED transaction rows | 258 |
| Total BGT | `$10,372,000.00` |
| Total ATD | `$3,500,095.00` |
| Total ETC | `$5,882,000.00` |
| Total EAC | `$9,382,095.00` |
| Total DELTA | `$989,905.00` |
| Parseable GED Amount | `$3,500,095.00` |
| Mapped GED Amount | `$3,498,245.00` |
| Unmapped GED Amount | `$1,850.00` |
| Known overrun | Account `555035`, `$150,000.00` |
| Known duplicate | GED rows `65–66`, `$82.50` duplicate-copy exposure |
| Known missing value | `GED!O87` |
| Known invalid mapping | GED row `43`, `00-0999 + 527015`, `$1,850.00` |
| Known reconciliation effect | `00-0245 + 527015`, `$1,850.00` difference |

### Strengths

- Financial parsing and core arithmetic use `Decimal`, reject non-finite and
  over-precision inputs, and retain exact two-decimal labels/cents.
- Missing amounts are not silently converted to zero.
- Exact Department + Account joins are used; the unmapped synthetic row does not join
  by Account alone.
- Charts use recorded exact labels/tables; conversion to float is limited to visual
  coordinates.
- Ask Fin and presentation code do not create authoritative pass/fail values.
- Original source row/cell evidence and original/current reviewed values are retained.

### Release-blocking correctness defects

1. **CORE-04 contract drift.** The current 986-scope oracle includes 71 unapproved
   Budget scopes. The approved five-rule scope count is 915 for this fixture.
2. **Status-policy drift.** Optional failures can change Overall Review Status. RAG is
   separately calculated, permitting an invalid `Attention Required / At Risk (Red)`
   pair.
3. **Summary-source drift.** Budget Health, Data Quality, reconciliation label,
   duplicate count, and missing-data count are not all derived exactly as §2.7 requires.
4. **Duplicate boundary defect.** A three-member `$100` group reports `$100` exposure
   and one duplicate instead of `$200` and two.
5. **Period-eligibility defect.** A valid June row is counted in a May YTD review.
6. **Fingerprint canonicalization risk.** Optional scalar types and canonical
   equivalents are not fully distinguished/tested.
7. **Historical contract risk.** Alias/ID and CORE-04 changes undermine strict replay
   semantics even though stored rows remain reproducible under current code.

**Assessment:** the supplied fixture remains internally arithmetically consistent, but
FinSight's deterministic financial policy is **not release-correct across approved
boundary cases**.

## Ask Fin Privacy and Safety Assessment

### Verified controls

- The active Stage 2 path uses local Ollama only; no OpenAI, Anthropic, Gemini, search,
  external embedding, or cloud fallback is composed into the V2 assistant.
- Endpoint normalization permits loopback HTTP only.
- DNS resolution and the connected peer must remain loopback.
- Environment proxies and HTTP redirects are disabled.
- Cloud-style model aliases are rejected.
- The model name, SHA-256 digest, and approved GGUF profile are checked; the provider is
  rechecked immediately before each prompt.
- Automatic readiness removes normal setup friction when the local runtime/model is
  available.
- The unavailable state leaves deterministic FinSight usable and offers a single Retry.
- Pre-validation Help Mode and post-validation Financial Review Mode are separated.
- Grounding uses application-authored claims over one authorized review/run; unsupported
  prose and citations fail closed.
- Citations resolve to FinSight evidence; review context is isolated.
- Decision/state-change prompts are refused before provider use, and decision language
  in model output is withheld.
- Ask Fin cannot invoke source, rule, finding, budget, or financial-system mutation
  ports.
- Prompt/model/records/response/citations/latency/refusal/failure are retained locally;
  audit failure withholds the response.

### Remaining privacy, security, and audit risks

| Risk | Classification | Required action |
|---|---|---|
| Ollama and `llama3.2:3b` are external prerequisites, not governed installed components. | **Must fix before packaging** | Define installer-managed runtime/model provisioning, version/digest pinning, health, start/stop, repair, upgrade, rollback, and uninstall. |
| Automatic observed-digest pinning is trust-on-first-use unless a managed digest is supplied. | **Must fix before packaging** | Ship an approved managed model digest/profile and verify it before first prompt. |
| Local Ollama cloud features/egress are not independently disabled by installer/firewall policy. | **Must fix before packaging** | Enforce and test a no-cloud runtime configuration and offline execution with all non-loopback egress blocked. |
| Provider response-byte and concurrent-request ceilings are not proven at the boundary. | **Must fix before pilot** | Add bounded response/stream, concurrency, cancellation, and resource-exhaustion tests. |
| Local daemon compromise or a malicious model remains outside FinSight's Python process. | **Must fix before pilot** | Threat-model service ownership/ACL, fixed binaries/models, least privilege, and runtime integrity monitoring. |
| Prompt injection in source descriptions can influence model wording. | **Should fix** | Preserve source-as-data delimiters and add hostile workbook-text tests; continue exact claim/citation validation. |
| Ask Fin interaction retention contains financial questions/answers. | **Must fix before pilot** | Approve retention, access, backup, disposal, and diagnostic-redaction policy. |
| Runtime/model licensing and redistribution notices are unresolved. | **Must fix before packaging** | Complete legal review and ship required notices/attribution or choose a permitted enterprise deployment method. |

### Production deployment assessment

Ollama has an official Windows installer and standalone CLI/service options, but FinSight
does not currently provision or manage either. The selected `llama3.2:3b` artifact is
approximately 2 GB and is distributed under the Llama 3.2 Community License, not the
Ollama repository's MIT license. Redistribution therefore requires separate legal and
notice review. Hardware, cold-start time, model-response latency, first-run download,
offline provisioning, updates, repair, and removal have not been qualified on the
required 8 GB/16 GB Windows matrix.

**Ask Fin conclusion:** the application-level boundary is strong and appropriately
conservative; the release/deployment boundary is incomplete.

## UX Assessment

This assessment used the approved Stage 2 screenshots, the walking-skeleton references,
and a new Light/Dark current-state capture from the actual application.

1. **Landing and Create Review — Healthy.** Strong hierarchy, side-by-side primary
   actions, modern shell, clear workflow rail, and compact period form. Sparse lower
   space is acceptable at large sizes.
2. **Upload — Healthy.** Two clear cards, business-first metadata, compatibility/count
   status, and source-preservation disclosure.
3. **Verify Data — Healthy.** The duplicate internal row header is hidden; Source Row is
   authoritative; source details are progressive; table height is reclaimed.
4. **Rules — Healthy with product debt.** Default view is understandable and
   human-readable. Advisory support and rule-contract drift are not UI problems.
5. **Validate — Needs correction.** The progress presentation is clear but not tied to
   real engine stages/counts.
6. **Overview/Financial Analysis — Healthy visually.** The current information
   architecture is focused and avoids the earlier BI-style sprawl. Financial labels are
   direct and table alternatives are present.
7. **GED Detail — Healthy.** Filters, direct amounts, and transaction/source drill-down
   are usable.
8. **Findings — UX debt.** It is the primary exception-review surface, but row density,
   truncation, and competing filters/actions make scanning harder than necessary.
9. **Explain This — UX debt.** Deterministic explanation is excellent; exhaustive raw
   source citations can dominate the panel. Progressive disclosure should be improved.
10. **Ask Fin drawer — Functional but brittle.** The simplified unavailable state is
    correct. In the full suite, drawer width collapses to 169 px; current capture also
    could not complete the post-validation live-model state because Ollama was absent.
11. **Accessibility — not release-qualified.** Keyboard labels and semantic text are
    broad, but 200% appearance clipping and Settings Back focus currently fail, and
    native NVDA verification is pending.

No recommendation is made to add more analytics or redesign the Stage 2 navigation.
After stabilization, refinement should focus on Findings, evidence density, and robust
resizing/accessibility.

## Test and Verification Assessment

The detailed inventory is:

[Consolidated Test Inventory](CONSOLIDATED-TEST-INVENTORY-2026-07-29.md).

### Current closeout results

| Check | Result |
|---|---|
| Test collection | 1,216 tests across 127 files |
| Full suite | **FAIL — 4 failed, 1,212 passed, 2 subtests passed in 81.98s** |
| Financial/oracle/rule/history focused set | PASS — 29 |
| Independent OOXML/Decimal oracle | PASS for its encoded expectations |
| Import-linter | PASS — 235 files, 1,008 dependencies, 3/3 contracts |
| Focused Ruff over financial modules | PASS |
| `git diff --check` | PASS |
| Integrated offscreen launch smoke | PASS |

### Current failures

- appearance control clips at 200% text scale;
- Settings Back has `NoFocus`;
- Ask Fin drawer width is order-dependent and can collapse below minimum;
- delivery imports Ask Fin infrastructure directly.

### Coverage strengths

The suite has strong unit, application, infrastructure, migration, security, AI,
workflow, UI, accessibility, oracle, and architecture coverage. It covers fixture
totals, corrections, retained versions/runs, governance, source evidence, local AI,
decision refusals, and launch.

### Missing high-risk coverage

- exact core-only status and three-state RAG mapping;
- exact CORE-04 scope contract;
- duplicate groups of 3+;
- review-period boundaries;
- typed duplicate fingerprint boundaries;
- exact §2.7 summary sources;
- advisory statuses;
- explicit successor promotion;
- clean supported Windows execution and ACL/DPAPI equivalents;
- NVDA/manual assistive technology;
- large-workbook performance/responsiveness;
- installer clean/upgrade/repair/uninstall;
- managed Ollama/model lifecycle and offline egress proof.

Three POSIX permission tests will skip on Windows and do not prove their Windows
equivalents. No xfails exist. One 865-line integrated financial UI test provides broad
coverage but is brittle and should be complemented by focused contract tests.

**Full-regression decision:** A full governed regression is mandatory before packaging,
but rerunning the unchanged code is not enough. The material financial, lifecycle,
architecture, and accessibility defects must be corrected first; then the complete
suite, oracle, static/architecture checks, and native Windows qualification must run
from one clean immutable revision.

## Architecture and Code Quality Assessment

### Strengths

- The V2 domain/application/infrastructure/delivery split is explicit.
- Exact financial logic is kept out of Ask Fin and largely out of the UI.
- Rule/run/source identities, corrections, findings, and audits are persisted.
- SQLCipher, audit HMACs, signed authorization sources, single-instance control, and
  workbook safety show serious security engineering.
- Migrations are explicit and tested through schema 14.
- Local AI has a strong closed-claims and fail-closed response boundary.

### Defects and debt

| Issue | Classification | Evidence / action |
|---|---|---|
| Delivery imports AI infrastructure. | **Must fix before packaging** | Move preference/config storage behind an application port; strengthen import-linter so it cannot disagree with the UI fitness test. |
| Legacy and V2 engines/shells are both composed. | **Must fix before packaging** | Remove packaged reachability or quarantine behind an explicit non-production composition root. |
| `financial_review_view.py` is about 5,996 lines. | **Should fix** | Split navigation, read models, tables, evidence drawers, and section widgets after behavior is locked. |
| UI rebuilds some descriptive vendor/count aggregates. | **Should fix** | Move reusable aggregates into recorded analytics projections. |
| Run ordering uses SQLite `rowid`. | **Should fix** | Add an explicit immutable sequence/timestamp + stable tie-breaker. |
| Error/audit and persistence design is stronger than release operations. | **Must fix before packaging** | Implement backup/restore, release provisioning, recovery, and installer lifecycle. |
| Repository-wide Ruff is not a clean release gate. | **Should fix** | Establish a scoped debt baseline, then make release-owned source clean. |
| Current source state is not reviewable/reproducible. | **Must fix before packaging** | Separate generated evidence, remove accidental artifacts through an approved cleanup, commit/tag the reviewed source, and rerun from that revision. |

The current branch has 29 modified tracked files and 809 untracked files. The accidental
root `--help/` screenshot directory and old July 25 Release 1 artifacts are not a valid
V2 release payload. The only CI workflow checks dependency versions; it does not run the
full suite, build a Windows artifact, verify signatures, or publish release provenance.

## Known Limitations

- Only the approved `SLV-001` Budget and GED layouts are supported.
- Budget has no authoritative source-period field; it is bound to the workspace period.
- The original workbook is not copied into the encrypted store. If the external file is
  removed, stored results/evidence remain but raw row reconstruction can become
  unavailable.
- Vendor prior-period comparison is unavailable without authoritative historical data.
- Invoice, PO, SOW, rate-card, resource, project, forecast, and what-if capabilities are
  deferred.
- Informational/Advisory rules are not executable.
- Optional rule types are limited to the approved deterministic family.
- Current PDF/XLSX outputs are not delivered.
- Managed backup, replacement-machine restore, and final key/backup disposal are absent.
- Native Windows, NVDA, large-workbook, and 8 GB/16 GB performance qualification are
  absent.
- Ollama/model installation, startup, repair, updates, and uninstall are external.
- No signed V2 installer, code-signing plan execution, SBOM, malware scan, or
  clean-machine evidence exists.
- Project Owner hands-on approval for Stage 1/2/Final Product is not recorded.

## Risk Register

The complete register is:

[Consolidated Risk Register](CONSOLIDATED-RISK-REGISTER-2026-07-29.md).

Highest risks are:

- incorrect protected-rule/status behavior;
- an oracle that validates drift;
- uncommitted, non-reproducible source state;
- absent Windows/runtime/model provisioning;
- absent backup/restore and incomplete disposal continuity;
- missing current exports;
- unqualified Windows security/identity/ACL behavior;
- accessibility and large-workbook performance not natively qualified;
- model redistribution/license obligations;
- duplicate legacy production paths;
- incomplete audit-retention and enterprise operations policy.

No high/critical risk should be accepted implicitly. The risk register names the owner,
mitigation, packaging/pilot effect, and verification for each item.

## Packaging Readiness

The detailed checklist is:

[Packaging Readiness Checklist](PACKAGING-READINESS-CHECKLIST-2026-07-29.md).

### Decision: Not ready for packaging

| Required packaging condition | Current state |
|---|---|
| Clean immutable release source | **Fail** — V2 largely uncommitted; 29 modified tracked / 809 untracked files |
| Full regression evidence | **Fail** — 4 current failures plus material uncovered finance defects |
| Clean-machine installation plan implemented | **Fail** — ADR only |
| Windows build viability | **Not proven** — no current V2 Windows artifact/VM run |
| One-click launch, no terminal | **Fail** — developer launch script/environment/provisioning required |
| Automatic local AI runtime provisioning | **Fail** |
| Automatic model provisioning | **Fail** |
| No manual Ollama startup | **Fail** |
| Local-only data handling | **Application path passes; deployment egress hardening unproven** |
| Installer/uninstall behavior | **Fail** — no MSI lifecycle |
| Upgrade path | **Fail** — architecture only |
| Repair path | **Fail** |
| Code signing | **Fail** — plan only |
| License review/notices | **Fail** |
| SBOM/provenance/malware scan | **Fail** |
| Backup/restore/recovery | **Fail** |
| Standard-user role/store provisioning | **Fail** |
| Native accessibility/performance | **Fail** |

Existing `dist/FinSight.dmg`, wheel, zipapp, and `1.0.0` metadata are Release 1 artifacts
that predate V2. They must not be treated as closeout evidence or shipped as the V2
product.

## Recommended Next Stage

### Option C — Stabilization and Regression

**Recommendation classification: Must fix before packaging.**

This is the only appropriate immediate stage. Option A is premature because there is no
stable release candidate or installer path. Option B would add output work before
financial and lifecycle semantics are trustworthy. Option D is premature because the
manager should review a corrected, green baseline rather than approve known material
defects.

### Why

- Deterministic financial behavior does not fully match the approved contract.
- Current automated regression is red.
- Historical oracle evidence masks one protected-rule drift.
- Source/release provenance is not reproducible.
- Architecture boundaries and obsolete production paths need cleanup.
- Packaging prerequisites are still unimplemented.

### Entry criteria

- Project Owner accepts this closeout finding and Option C scope.
- The approved requirements/architecture source hierarchy is frozen for stabilization.
- No packaging, new analytics, new source types, or new AI capabilities begin.
- A controlled backup or branch snapshot preserves the current evidence before cleanup.

### Work that must be completed

1. Reconcile permanent protected IDs and CORE-04 through a governed requirements/data
   migration decision.
2. Correct core-only status/RAG/summary projections, reporting-period eligibility,
   duplicate 3+ behavior, and fingerprint canonicalization.
3. Correct explicit successor publication and source/edit successor semantics.
4. Decide and implement or formally defer advisory execution without pretending the
   common three-class engine is complete.
5. Fix all four current regression failures.
6. Remove/quarantine legacy engine/UI/AI paths and repair the delivery dependency.
7. Reconcile approved/superseded documentation and Stage gate state.
8. Separate source from generated evidence, establish a clean immutable revision, and
   strengthen CI/static/architecture gates.
9. Regenerate the independent oracle and Stage 1/2 evidence from the corrected contract.
10. Run the complete suite, oracle, import/static checks, launch, and targeted
    order/isolation tests twice from that exact revision.

### Work that must not start

- MSI/PyInstaller release build or code signing;
- Ollama/model redistribution;
- new analytics, invoice/resource source types, forecasting, or AI authority;
- final branding/cosmetic polish unrelated to defects;
- release announcements or pilot deployment with real financial data.

### Exit criteria

- zero unresolved Material defects;
- approved protected Rule IDs and contracts are identical across specifications,
  seeds, persisted results, UI, oracle, and tests;
- exact §2.7 status/RAG/summary policy passes positive, negative, and boundary tests;
- review-period, duplicate 3+, and fingerprint boundary tests pass;
- explicit publication/history behavior passes;
- all current full-suite failures are closed;
- full suite is green twice in clean/order-varied execution;
- independent oracle is regenerated independently and passes;
- import/static/architecture checks are green and legacy release paths are absent or
  provably excluded;
- repository is clean and evidence is tied to an immutable commit/tag;
- documentation/gate state is reconciled;
- one independent stabilization review returns PASS.

### Estimated implementation risk

**Medium–High.** Most defects are localized, but changing permanent rule identities,
protected scope contracts, retained run semantics, and publication state may require
migrations and expected-result updates. The very large uncommitted change set increases
review and recovery risk.

### Dependencies

- Product Owner decision on CORE-04 and permanent Rule ID baseline;
- Financial Control Approver participation if a protected baseline is changed rather
  than corrected to the approved contract;
- test/fixture regeneration independent of application assumptions;
- security/architecture review of legacy-path removal and publication changes.

## Mandatory Actions

| Classification | Specific issue | Evidence / affected component | Proposed action and rationale | Verification method |
|---|---|---|---|---|
| **Must fix before packaging** | Protected IDs and CORE-04 do not match the approved baseline. | V2 FR §12; `financial_validation.py`; seeds, oracle, retained results. | Govern the identity/scope correction; do not rewrite the specification to bless an unapproved implementation. Historical replay depends on stable identity. | Migration/replay tests, independent oracle, exact seed/result/UI identity checks. |
| **Must fix before packaging** | Status, RAG, summary counters, duplicate, and period-boundary results are wrong. | `financial_validation.py:689-750`, duplicate/period closeout probes. | Implement exact §2.7 and §11 policies in the domain projector/engine. | Table-driven boundary suite plus regenerated fixture evidence. |
| **Must fix before packaging** | Current suite has four failures. | Appearance, Settings, drawer, and architecture fitness tests. | Fix behavior/test isolation and delivery dependency; no waiver. | Full suite twice plus order-varied UI run. |
| **Must fix before packaging** | Successor reanalysis auto-publishes. | FR-202; `financial_review.py`. | Require explicit Reviewer promotion and reason; preserve published/working labels. | Publication/history/restart/audit tests. |
| **Must fix before packaging** | V2 source is not in a reproducible revision. | 29 modified tracked, 809 untracked files, old HEAD. | Review, classify, commit, and tag exact source/evidence; exclude generated/accidental artifacts. | Clean `git status`, signed/tagged source identity, fresh verification logs. |
| **Must fix before packaging** | Legacy engines/shells and legacy AI composition remain present. | `app.py`, `main_window.py`, legacy views. | Remove packaged reachability or create explicit non-production composition. This protects the single-source-of-truth boundary. | Reachability/import/package inspection and end-to-end regression. |
| **Must fix before packaging** | Managed backup/restore and current PDF/spreadsheet exports are absent. | NFR-101/root NFR-060; FR §2.13; no current implementation route. | Deliver governed recovery and approved first-release outputs before release packaging. | Backup/restore/disaster/disposal tests; PDF/XLSX content/identity/accessibility tests. |
| **Must fix before packaging** | Windows installer/runtime/model lifecycle is absent. | ADR-V2-004; no WiX/PyInstaller release source; Ask Fin limitation. | After stabilization, implement signed MSI, standard-user provisioning, runtime/model lifecycle, offline local-only operation, upgrade/repair/uninstall. | Clean 8/16 GB Windows 11 VM matrix, hashes, signatures, SBOM, malware scan. |
| **Must fix before packaging** | Runtime/model/legal boundary is unresolved. | Ollama/model official licenses and current external setup. | Approve redistribution/deployment method, exact versions/digests, notices, resource envelope, and update policy. | Legal sign-off, license inventory, offline install/repair/uninstall evidence. |
| **Must fix before pilot** | Native accessibility and large-workbook behavior are unqualified. | NVDA pending; 200% regression; no representative load benchmark. | Complete NVDA/keyboard/contrast/zoom and realistic performance/responsiveness qualification. | Recorded assistive-tech script and approved hardware/load results. |
| **Must fix before pilot** | Retention, backup, disposal, and Ask Fin interaction policies are incomplete. | Local financial/audit/AI content; no operational policy. | Approve retention/access/backup/disposal/recovery responsibility and test it. | Policy review plus lifecycle/authorization/restore/disposal tests. |
| **Should fix** | Findings and Explain This are dense. | Current Light/Dark visual audit. | Improve responsive columns and progressive evidence disclosure without changing semantics. | Focused visual/accessibility review at supported sizes. |
| **Should fix** | Large view modules and UI-derived descriptive aggregates increase drift risk. | `financial_review_view.py`; vendor/count assembly. | Refactor behind recorded read models after stabilization behavior is locked. | Characterization tests, import contracts, result equality. |
| **Should fix** | Run ordering uses SQLite internals. | financial review repository `rowid` ordering. | Add explicit immutable sequence/timestamp ordering. | Migration and deterministic-selection tests. |
| **Optional** | Additional visual polish and animation refinement. | Current UI is already coherent. | Defer until correctness/accessibility gates are green. | Product-owner visual review. |
| **Deferred** | Invoice/resource/contract/forecasting/what-if and broader layouts. | Root future phases; no approved source samples/contracts. | Keep out of stabilization and packaging. | Future governed requirements/architecture stages. |

## Optional Improvements

- Split the integrated 865-line workflow UI test into focused contract tests while
  retaining it as an end-to-end journey.
- Add a concise current-baseline index at repository root.
- Add build-time package reachability and forbidden-module scans.
- Improve contributor pagination/summarization in Explain This.
- Add a stable user-facing diagnostics bundle that excludes financial content.
- Add a deterministic developer fixture for Ollama-ready/unavailable UI states.

## Deferred Work

- Invoices, purchase orders, SOWs, rate cards, contracts, and resources.
- Project/workstream/funding-category analysis without approved mappings.
- Forecasting, run-rate, what-if, resource departure, and backfill scenarios.
- Portfolio/web/multi-user deployment.
- Additional source layout versions.
- Additional AI providers or public/cloud inference.
- Multi-period trends until authoritative history exists.
- Advisory rule expansion beyond the approved deterministic model.

## Final Go/No-Go Recommendation

**NO-GO for Packaging and NO-GO for a real-data pilot.**

FinSight's implemented workflow and product direction are strong enough to preserve.
They should not be replaced or expanded. The correct move is a bounded governed
stabilization stage that restores the protected financial contract, lifecycle
publication semantics, green regression, architecture boundaries, and reproducible
source state. Only after that PASS should the Product Owner choose the next gate—most
likely completing the still-mandatory output/recovery obligations before beginning the
Windows Packaging and Release stage.

## Exact Evidence and File References

The complete source-by-source index is:

[Exact Evidence Index](EXACT-EVIDENCE-INDEX-2026-07-29.md).

Primary evidence groups:

- [Project understanding](../../../../docs/00-project-understanding.md)
- [V2 Product Direction Source](../../briefs/PRODUCT-DIRECTION-SOURCE-configurable-rule-engine-v2.md)
- [V2 functional requirements](../../specs/01-functional-requirements.md)
- [V2 non-functional requirements](../../specs/02-non-functional-requirements.md)
- [Financial Review workflow](../../docs/FINANCIAL-REVIEW-WORKFLOW.md)
- [Application architecture](../../docs/APPLICATION-ARCHITECTURE.md)
- [Rule-engine design](../../docs/RULE-ENGINE-DESIGN.md)
- [Persistence model](../../docs/PERSISTENCE-MODEL.md)
- [Technical implementation plan](../../plans/TECHNICAL-IMPLEMENTATION-PLAN.md)
- [Execution lanes](../../plans/EXECUTION-LANES.md)
- [Stage 1 verification](../../verification/STAGE-1-FINANCIAL-CORRECTNESS-VERIFICATION-2026-07-29.md)
- [Stage 2 verification](../../verification/STAGE-2-CONSOLIDATED-VERIFICATION-2026-07-29.md)
- [Stage 2 follow-up](../../verification/STAGE-2-FOLLOWUP-ASK-FIN-NAVIGATION-RULES-2026-07-29.md)
- [Ask Fin simplification](../../verification/STAGE-2-ASK-FIN-SIMPLIFICATION-2026-07-29.md)
- [Independent oracle](../../verification/STAGE-1-INDEPENDENT-ORACLE-2026-07-29.json)
- [Independent closeout review](INDEPENDENT-CLOSEOUT-REVIEW-2026-07-29.md)
- [Current test inventory](CONSOLIDATED-TEST-INVENTORY-2026-07-29.md)
- [Current UX screenshots](../../../../artifacts/closeout-ux-audit-2026-07-29/stage2)
- [Windows packaging ADR](../../adr/ADR-V2-004-windows-packaging-and-support.md)

External release facts were checked against official sources:

- [Ollama Windows documentation](https://github.com/ollama/ollama/blob/main/docs/windows.mdx)
- [Ollama repository and MIT license](https://github.com/ollama/ollama)
- [Ollama `llama3.2:3b` model record](https://ollama.com/library/llama3.2:3b)
- [Llama 3.2 Community License text](https://ollama.com/library/llama3.2:latest/blobs/fcc5a6bec9da)
- [`sqlcipher3` distribution record](https://pypi.org/project/sqlcipher3/)
