# FinSight — Walking Skeleton Plan

**Document:** 13-walking-skeleton-plan.md
**Status:** Draft for team review and design-review board (build-planning)
**Date:** 2026-07-16
**Scope:** The **first implementation slice** of FinSight — the smallest end-to-end thread that proves the approved architecture, workflow, boundaries, verification gate, audit trail, traceability, determinism, export path, and the minimal AI read-path work together. This is a **build plan**, not a design; it introduces no product scope, features, workflows, or AI capabilities beyond the approved set. Where the skeleton must choose, it defers to the approved UX (07), Architecture (06), Rules (05), Decision Log (09/DEC-001–034), Constitution, and Build-Readiness Runbook (12).
**Governing methodology:** Spec-Driven Development (DEC-010, NFR-073); the Constitution governs.
**Sources of truth:** Constitution · 00–12 · Final Specification Review · Build-Readiness Review · DEC-001–DEC-034.
**Relationship to the framework:** this document is the skeleton's *overarching* plan. Its actual implementation is driven, at Build-Readiness **Gate 5**, by a proper `specs/plans/PLAN-F-##-##.md` + `specs/tasks/TASKS-F-##-##.md` for the scoped feature slice, design-panel-reviewed, per 11 §3. This plan defines *what the skeleton must be*; the PLAN/TASKS define *how it is built task by task*.
**Prerequisites:** this plan assumes Build-Readiness **Gates 1–4** are in progress/complete (DEC-024–034 ratified; `specs/` operationalized + constitution + baseline; skeleton-critical ADRs raised; environment + CI + trace gate + golden-dataset framework ready). It does not begin until the skeleton-critical ADRs are Accepted (§9).

> **One governed deviation to record (P-1 spec-first, not a silent change):** Architecture §21 defined the walking skeleton with **no AI in the path** (proving AI-off completeness by construction). This plan, per explicit direction, adds a **minimal, stubbed** Explain This and Ask Fin to also prove the AI *read-path architecture* early. This is a deliberate, small scope expansion of §21's skeleton. It preserves every approved AI principle (grounded, cited, optional, single-persona, no agents, AI-off complete) and depends on **no production provider** (it uses a pluggable stub/local provider — OQ-1/OQ-3 gate *production* AI, not an architecture proof on synthetic data). **Action:** record this as a minor decision/CR against §21 when specs are baselined, so the deviation is governed, not assumed.

---

## 1. Purpose

To define the single smallest slice of FinSight that, when built, **proves the approved architecture and user experience work together end-to-end** — before any feature breadth. If this one thread cannot run through FinSight's load-bearing boundaries (the verification gate, the deterministic core, the audit port, the DAL, the findings contract, the export path, and the minimal AI read-path), those boundaries are wrong, and that is discovered on day one rather than at integration (06 §21, DEC-022).

The skeleton is **the first thing Claude will implement**. It exists to de-risk the architecture, not to deliver value; feature breadth (the first-wave epics E-14, E-01, E-02, E-08, E-06 and beyond) follows only after the skeleton walks.

## 2. Walking Skeleton Objectives

The skeleton must prove, with one thread of real behavior:

1. **The guided review workflow** — the approved wizard flow (07 §5), Review Setup → … → Export, feels like a very small version of the real product.
2. **The Review-Cycle architecture** — one month/year cycle owns the thread's state, resumable and audited (AP-04, FR-006).
3. **The verification gate (the trust boundary)** — no analysis runs on unverified data; the `VerifiedDataset` is constructible only on human approval (P-9, FR-026, TB-02).
4. **The deterministic core** — one rule produces one finding, byte-identical across runs and platforms, with exact decimal arithmetic (P-7/P-8, NFR-021/029/059).
5. **The findings contract** — one first-class finding with severity, evidence, and one-hop source lineage (AP-12, FR-069/071, R-FND-01/02).
6. **The audit trail** — every material step emits an attributable event through the audit port, from story one (P-14, E-08).
7. **The export path** — one self-describing, labeled export (FR-116/120).
8. **The minimal AI read-path** — Explain This and Ask Fin, grounded and cited via the read-only findings port, visibly labeled, and **removable without loss** (P-8/P-11, FR-091/094/095/099, C-15/TB-03).
9. **Traceability & determinism as gates** — `Implements:`/`Verifies:` annotations, `TRACEABILITY: PASS`, and the golden-dataset/provider-swap/cross-platform tests, all green (P-5/P-7, NFR-036/037/048).

## 3. Architecture Being Proven

The skeleton exercises a minimal slice of each load-bearing boundary from 06:

| Boundary (06) | What the skeleton proves |
|---|---|
| Clean layering & dependency rule (§7, ADC-02) | domain core imports no UI/storage/provider/AI types; core is drivable headless |
| Command/Query segregation (§7.1, TB-03) | AI reaches the core only via read-only `FindingsQueryPort`; findings are written only via `FindingsCommandPort` (rules only); the AI write path is unwired and blocked by the CI architecture-fitness test (enforced by construction, not the compiler — Python) |
| Verification gate (§11, TB-02, ADC-10) | Rules Engine consumes only a `VerifiedDataset`, constructible solely by the verification step — analyzed-but-unverified is unrepresentable |
| Deterministic Rules Engine (§12, ADC-05) | one rule, versioned run (rule-set + config + input fingerprint), exact decimal, byte-identical |
| Findings model/experience split (§13, ADC-11) | finding contract in the core (C-09a); minimal experience in delivery (C-09b) via query port |
| Audit port (§14, §7.2, ADC-09) | core emits audit events through `AuditEventPort`; C-14 stores them; core stays headless-testable |
| Persistence/DAL (§17, ADC-06) | only the DAL touches storage; transactional, crash-safe, resumable |
| Consented egress chokepoint (§17, TB-04, ADC-07) | the AI stub's I/O passes one governed path; no second outbound path; consent-gated (stubbed) |
| Cycle state model (§6, ADC-10) | the wizard is a projection of the cycle state machine; resumable; per-artifact verification |

## 4. Scope Included

Exactly **one of everything**, following the approved 9-step flow (§6):

- **one Review Cycle** (month + year);
- **one upload flow** accepting the **GED report and the Budget Tracker** (the two Phase-1 documents with real samples — 00 §6, FR-001);
- **one upload-validation** step (required-files/completeness check — FR-007);
- **one processing** step: extraction + cell-level lineage + a minimal readiness check + data preparation (FR-011/012/013/015, R-RDY subset);
- **one verification** step producing the `VerifiedDataset` on explicit human approval (FR-026–029);
- **one deterministic rule**: **R-BUD-02 Over/Under-Budget Flagging & Severity**, composing R-BUD-01 (variance computation) and R-FND-02 (severity) — chosen because it uses *both* uploaded documents and feeds the summary's Budget Health (§10);
- **one finding** with severity, evidence, and source lineage (FR-069/070/071, R-FND-01);
- **one leadership-summary section** (Budget Health) with deterministic data and one executive-ready narrative slot (FR-076, R-RPT-02);
- **one export** (self-describing, labeled — FR-116/120);
- **minimal Explain This** on the finding (deterministic explanation + optional stubbed AI narration — FR-091/095);
- **minimal Ask Fin** from the summary (grounded, cited, stubbed — FR-100/094/099);
- **cross-cutting from story one:** audit on every step (E-08), transactional persistence (NFR-005/057), config-versioned run (FR-107), cross-platform determinism test (NFR-029).

## 5. Scope Explicitly Excluded

To keep the skeleton minimal (P-6; 12 §11):

- **All other rules and capabilities:** GED analysis breadth, reconciliation, invoice review, resource/contract, historical comparison, forecasting, Review Health, What's New (only R-BUD-02 runs).
- **All other document types:** invoices/POs/SOWs/rate cards/resource sheets (only GED + Budget Tracker).
- **Findings breadth:** full triage/filter/sort, dual-lens work-queue/decision toggle, full lifecycle beyond a single state, recurrence (one finding, minimal state).
- **Summary breadth:** RAG aggregation across capabilities, MoM/"what changed," all sections beyond Budget Health.
- **AI breadth & production:** Investigation Guidance, question library breadth, masking, multi-provider registry, and any **real/production AI provider** (stub/local only; production gated on OQ-1/OQ-3). No autonomous agents (P-8, DEC-034).
- **Wizard breadth:** Recent Reviews home, compare/history, settings/config depth, accessibility theme picker, onboarding/import — only the minimal screens for the nine steps.
- **Polish:** production UI, visual design-system fidelity beyond meaning-carrying essentials (color-independent severity is kept — P-13), performance tuning beyond correctness.
- **Wrong-file replacement/versioning, quarantine breadth, historical import** (R2/later features).

## 6. User Journey

The skeleton implements a minimal version of the approved guided wizard (07 §5, DEC-024). Each step maps to a real wizard step, an architecture component, and the "one of everything" principle. The user always sees **"Step X of 9"** with a clear next action (UXP-01, wayfinding guarantees).

| # | Step (as approved) | User action | System responsibility | Maps to wizard / component |
|---|---|---|---|---|
| 1 | **Review Setup** | selects Month + Year | creates the Review Cycle | Create · C-02 / FR-005/006 |
| 2 | **Data Upload** | uploads GED + Budget Tracker | accepts read-only; records provenance | Upload · C-03 / FR-001/003/010 |
| 3 | **Upload Validation** | reviews what's present | checks required files exist / completeness; names anything missing | Validate · C-03/C-05 / FR-007 |
| 4 | **Processing** | waits, informed (plain-language stages) | extraction + lineage + minimal readiness + prep; **no analysis** | Processing · C-04/C-05 / FR-011–015 |
| 5 | **Verification (gate)** | reviews extracted data; may edit; **confirms "I have reviewed the extracted data and confirm it is correct"** | presents data w/ source trace; captures corrections + approval; **constructs the `VerifiedDataset`** | Verify · C-06 / FR-026–029 |
| 6 | **Analysis** | waits, informed | runs **one rule** (R-BUD-02) on the `VerifiedDataset`; versioned run | Analyze · C-07/C-11 / FR-030/033 |
| 7 | **Findings** | views the one finding; opens Explain This | renders one finding: severity, evidence, one-hop source | Findings · C-09a/C-09b / FR-069–071 |
| 8 | **Leadership Summary** | reads Budget Health; opens Ask Fin | composes one deterministic summary section + narrative slot | Summary · C-12 / FR-076 |
| 9 | **Export** | exports | produces one labeled, self-describing export | Export · C-12 / FR-116/120 |

**Editing note (Step 5):** editing extracted values is supported but expected to be rare (per the approved flow); a correction preserves the original value, records user + timestamp, and remains in lineage (FR-028) — proving the correction path even if the golden run needs no edit.

## 7. Review Cycle Flow

The nine steps are the user-facing projection of the approved cycle state model (06 §6.2, ADC-10). The skeleton proves the model's invariants:

```
Created ─▶ Intake ─▶ Readiness ─▶ Extraction ─▶ VERIFY (gate) ─▶ Analysis ─▶ Findings ─▶ Summary ─▶ Export
   │           │          │            │             │(VerifiedDataset)                                    │
   └── resumable at every step (NFR-006) · every transition emitted through AuditEventPort (P-14) ─────────┘
```

- **The gate is structural:** the transition into Analysis is impossible without a `VerifiedDataset`, whose only constructor is the verification step (TB-02, ADC-10). The skeleton's integration test asserts this by construction, not by a runtime flag.
- **Resumable & crash-safe:** the cycle persists at each transition through the DAL; a force-kill mid-thread loses no verified data and resumes from the last consistent state (NFR-005/006, ADC-06).
- **Idempotent re-run:** re-running analysis on the same `VerifiedDataset` + config version yields the identical finding, no duplicates (NFR-008, F-02-06).

## 8. Required Components (minimal slices)

Per 06 §7–§8; each is the thinnest slice that carries its boundary:

| Component | Minimal role in the skeleton |
|---|---|
| **C-01 Application Shell** | the nine-step wizard frame, "Step X of 9", minimal screens; keyboard-operable; color-independent severity |
| **C-02 Review-Cycle Orchestrator** | create the cycle; sequence the fixed steps; enforce the verify gate; report status |
| **C-03 Document Intake** | accept GED + Budget Tracker read-only; provenance; required-file/completeness validation |
| **C-04 Extraction & Normalization** | extract observed fields; exact-decimal normalization; raw + cell-level lineage |
| **C-05 Data Quality & Readiness** | minimal schema/row check; a single-capability readiness verdict (Budget analysis Available/Unavailable + reason) |
| **C-06 Verification Workspace** | present data + source trace; capture correction + approval; **construct `VerifiedDataset`** |
| **C-07 Deterministic Rules Engine** | execute one rule; versioned, fingerprinted run; emit finding via `FindingsCommandPort` |
| **C-08 Rules & Config Registry** | hold R-BUD-02's parameters (materiality default) as versioned config |
| **C-09a Findings Domain Model** | the finding contract + severity (R-FND-02) + `FindingsQueryPort`/`FindingsCommandPort` |
| **C-09b Findings Experience** | render the one finding via the query port; Explain This affordance |
| **C-12 Executive Reporting & Export** | compose one summary section; produce one labeled export |
| **C-14 Audit & Provenance** | implement `AuditEventPort`; store an event for every step |
| **C-15 AI Assistance (minimal, stubbed)** | Explain This narration + Ask Fin, via `FindingsQueryPort` only; grounded/cited/labeled; pluggable stub provider (XP-03) |
| **C-16 Consent (minimal)** | a consent gate before any (stubbed) AI transmission; logged (proves the gate, not production consent) |
| **C-17 Persistence & DAL** | the only storage touch; transactional, crash-safe, resumable |

*(C-10 Reconciliation, C-11 breadth, C-13 Historical, C-18 Config UI are not exercised beyond what C-08 needs.)*

## 9. Required ADRs

From the skeleton-critical set (12 §9). **These must be Accepted before coding begins.**

| ADR (from ADC) | Why the skeleton needs it |
|---|---|
| **ADC-01** shell + core stack & separation | nothing can be coded without the stack decided |
| **ADC-02** layering, dependency rule, core-owned ports | defines module structure + the AI/deterministic boundary the skeleton proves |
| **ADC-05** exact-decimal + cross-platform determinism harness | the one rule + the both-OS determinism test depend on it |
| **ADC-06** persistence: repository interfaces & substitution | the DAL, crash-safety, resumability |
| **ADC-10** cycle state model + `VerifiedDataset` | the verification gate |
| **ADC-09** audit event schema + core-owned port | audit-from-story-one |
| **ADC-11** findings model/experience split | the one finding |

**Needed for the minimal AI slice (thin versions; full versions deferred to E-09/OQ):**

| ADR | Thin scope for the skeleton |
|---|---|
| **ADC-03** AI provider adapter + grounding/citation | the adapter interface + a **stub/local provider**; grounding-via-query-port + citation contract (no real endpoint — OQ-3 deferred) |
| **ADC-07** single consented-egress chokepoint | establish the invariant + the consent gate even though the stub performs no real egress (production consent gated on OQ-1) |
| **ADC-04** workflow orchestration (minimal) | a simple deterministic step sequencer; full orchestration ADR deferred (AOQ-03) |

*(ADC-08 at-rest/secrets is recommended before any real data but not strictly required for a synthetic-data skeleton; raise it before pilot.)*

## 10. Required Rules

**One detection rule** (05, Family 1 — Budget Review):

- **R-BUD-02 — Over/Under-Budget Flagging & Severity** (Approved · R1 · Must; FR-033, FR-070).
  - **Composes** (necessary infrastructure, not additional detection rules): **R-BUD-01** (Planned-vs-Actual Variance Computation, FR-030/031) as its input, and **R-FND-02** (Severity Classification, FR-070) as its shared severity method.
  - **Inputs:** the `VerifiedDataset` (verified budget figures + verified GED actuals aggregated by dimension).
  - **Configurable parameter:** `CP-VAR-MATERIALITY` (and `CP-VAR-SEVERITY-BANDS`) — **value pending OQ-8**; the skeleton uses a **synthetic default in versioned config** (DEC-019: value is configuration, not code) so the golden dataset produces a known finding. No real materiality value is invented or asserted.
  - **Output:** one finding — `Budget over-spend` (or under-spend) for the seeded dimension — with variance evidence and severity.
  - **Minimum history:** 0 (single-month judgment) — no cold-start dependency, ideal for a skeleton.

*Rationale for this choice over alternatives (e.g., R-GED-02 duplicate detection): R-BUD-02 exercises **both** uploaded documents (proving multi-document extraction, readiness, and verification of two files) and feeds the leadership summary's Budget Health section directly — the tightest fit to the approved 9-step flow. If the team prefers a single-document, parameter-free rule, R-GED-02 (duplicate detection, configurable match keys) is an equally valid skeleton rule; this plan recommends R-BUD-02.*

## 11. Required Data Structures (logical only — schema is bound by ADRs)

Logical shapes the skeleton needs; **not** database or code design (that is ADC-06/implementation):

- **ReviewCycle** — month, year, name, state, user.
- **IngestedFile** — original name, content fingerprint, ingest timestamp, user, assigned period, document type (provenance — FR-010).
- **ExtractedRecord** — normalized value + **raw value** + source reference (file/sheet/row/cell) + confidence (lineage — FR-015).
- **ReadinessResult** — per-capability status (Available/Unavailable) + reason.
- **VerificationDecision** — per-document approve/approve-with-corrections/reject + user + timestamp + corrections (original→corrected).
- **VerifiedDataset** — the immutable, approved input to the engine; constructible only by C-06.
- **RuleRun** — rule-set version + configuration version + input fingerprint (reproducibility — FR-086, NFR-022).
- **Finding** — id, rule reference, severity, period, affected entities, evidence values, source references, lifecycle state (FR-069).
- **SummarySection** — Budget Health deterministic content + a labeled (empty-by-default) AI-narrative slot.
- **Export** — content + labels (period, data-as-of, config version, AI-content labeling — FR-120).
- **AuditEvent** — action, actor, timestamp, fingerprint, versioned schema (E-08, ADC-09).
- **ConfigVersion** — the versioned parameter set in force for the run (FR-107).
- **AIInteraction** (stubbed) — provider/model (stub), data transmitted, consent reference, prompt category, output, citations (FR-087).

## 12. Required Tests

Test-first (P-3/P-7; 11 §11). Minimum suites for the skeleton:

- **Unit:** extraction of the observed GED/Budget fields; R-BUD-01 variance math (edge: planned = 0 → "unbudgeted" marker); R-BUD-02 flag + R-FND-02 severity.
- **Golden-dataset (one):** a seeded **synthetic** month (GED + Budget Tracker with a known variance) → **exactly one expected finding** with the expected severity and evidence traceable to source lines (NFR-036/038; 04 §2.1). Synthetic data only (P-3, NFR-018).
- **Determinism:** repeat-run byte-identical findings for the same `VerifiedDataset` + config version (NFR-021).
- **Cross-platform:** identical results on **Windows and macOS** in CI (NFR-029).
- **Provider-swap / AI-off completeness:** with the AI stub **disabled**, the finding, summary, and export are complete and identical; enabling/swapping the stub changes **no** deterministic output (NFR-037/048; FR-095; P-11).
- **Verification-gate integration:** analysis cannot run without a `VerifiedDataset` — asserted structurally (the engine has no other entry).
- **Audit assertion:** every step (setup, upload, validation, extraction, verification, analysis, finding, summary, export, each AI interaction) emits an `AuditEvent` through the port.
- **Crash-safety:** force-kill mid-analysis loses no verified data; the cycle resumes (NFR-005/006).
- **AI grounding/citation:** Explain This and Ask Fin answers cite the finding/evidence they are grounded in and **decline** an unsupported question ("evidence not found") (FR-094/099; 10 §4.3).
- **Accessibility smoke:** the nine steps are keyboard-traversable; severity is conveyed with icon/label, not color alone (NFR-025/026).
- **Traceability:** every unit carries `Implements: FR-###, F-##-##, R-BUD-02`; tests carry `Verifies:`; `/sdd:trace` returns **PASS** for the skeleton feature.

## 13. Verification Criteria

The skeleton is verified (per 06 §21 + Constitution quality bars) when **all** hold:

1. A user completes all nine steps end-to-end on synthetic data and obtains one finding, one summary section, and one export.
2. **The gate holds by construction:** there is no code path that analyzes an unverified document.
3. **AI-off is complete:** disabling the AI stub removes only narration; every number, the finding, the summary, and the export remain (FR-095).
4. **Determinism:** byte-identical results across repeated runs and across Windows + macOS (NFR-021/029).
5. **Crash-safety:** a mid-thread force-kill loses no verified data (NFR-005).
6. **Audit completeness:** every step is reconstructable from audit events alone (P-14).
7. **One-hop explainability:** from the finding, the user reaches rule → inputs → source in one interaction (NFR-067).
8. **Export is self-describing:** carries period, data-as-of, config version, and AI-content labeling (FR-120).
9. **AI is grounded, cited, labeled, consent-gated, and declines the unsupported** (FR-094/096/099; NFR-049).
10. **Traceability PASS** with zero orphans for the skeleton feature; golden/determinism/provider-swap/accessibility suites green.

Passing these is the proof the architecture and UX work together; feature breadth may then begin.

## 14. AI Validation Strategy

The skeleton proves the **AI architecture**, not AI feature breadth (10 §1/§18). Strictly within the approved Fin strategy:

- **One persona, two minimal surfaces:** **Explain This** (on the finding) and **Ask Fin** (from the summary). No Investigation breadth, no agents (DEC-032/034).
- **Explain This** narrates the *existing* finding grounded in its deterministic evidence (rule, inputs, threshold comparison, source); it explains, never generates (FR-091; P-8). The deterministic explanation is present with AI off.
- **Ask Fin** answers grounded questions over the review's verified data and findings, with **Sources Used**; it opens with the approved welcome and honors the approved rules — grounded only in review data, explain-only, **no decision-making, no recommendations on the user's behalf**, supporting evidence, source references; if evidence is absent it says so (10 §4). It degrades to the deterministic question library when AI is off (FR-101/102).
- **Read-only boundary:** both reach the core **only** through `FindingsQueryPort` (C-15/TB-03) — structurally unable to write a finding or take an action.
- **Provider-stubbed:** a pluggable stub/local provider behind the adapter (XP-03) proves retrieval → grounded prompt → cited answer → labeled render → consent gate → audit, **without a production endpoint** (OQ-3) or the ratified production consent model (OQ-1). Those gate *production* AI; the skeleton proves *plumbing* on synthetic data.
- **Consent + labeling + audit:** every (stubbed) transmission passes the consent gate (C-16, FR-096), is visibly labeled and attributed (NFR-049), and is logged (FR-087).
- **Validation:** the AI grounding/citation and AI-off-completeness tests (§12) are the acceptance evidence.

## 15. Traceability Strategy

- The skeleton is scoped as a **single feature slice** planned via `specs/plans/PLAN-F-…` + `specs/tasks/TASKS-F-…` at Gate 5; tasks are half-day and test-mapped up front.
- **Annotations:** every implementing unit carries `Implements: FR-###, F-##-##` (and `R-BUD-02` for rule code); every test carries `Verifies: FR-###/NFR-###`.
- **FRs the skeleton touches (its trace surface):** FR-001/003/005/006/007/010 (intake); FR-011/012/013/015 (extraction/lineage); FR-021/022 + readiness (quality); FR-026/027/028/029 (verification); FR-030/031/033 (budget rule); FR-069/070/071 (finding); FR-076 (summary); FR-116/120 (export); FR-086/107 (run/config versioning); FR-084–089 (audit); FR-091/094/095/099/100/096 (minimal AI). NFRs: NFR-005/006/008/019/021/025/026/029/036/037/048/049/057/059/062/067.
- **Gate:** CI runs `/sdd:trace --fail-on-orphans`; merge requires `TRACEABILITY: PASS` and green golden/determinism/cross-platform/accessibility suites.
- **No orphans:** every skeleton unit traces to a baselined requirement; any untraceable code is a defect fixed at the spec or the annotation.

## 16. Definition of Success

The walking skeleton succeeds when it satisfies §13 **and** the Constitution's Definition-of-Done clauses applicable to it (11 §15): functional (nine steps + one finding/summary/export), quality (tests green), accessibility (keyboard + color-independent), traceability (PASS), determinism + audit (non-negotiable), AI-labeled + optional, config-governed, honest-under-failure, reviewed (design-panel), real-data-free.

**In one line:** *a user completes a minimal but real monthly review — setup → upload → validate → verify → analyze → finding → summary → export, with Explain This and a grounded Ask Fin — on synthetic data, byte-identically on both platforms, with a full audit trail, complete traceability, and the AI fully removable.* When that is true, the architecture is proven and first-wave breadth (E-14, E-01, E-02, E-08, E-06) may begin.

## 17. Risks

| ID | Risk | Mitigation |
|---|---|---|
| **WS-1** | AI-in-skeleton expands scope beyond §21's "no-AI" skeleton | Keep AI minimal + stubbed; record the governed deviation (banner above); AI-off-completeness is a hard test |
| **WS-2** | AI slice pulls in production-provider dependency (OQ-1/OQ-3) | Stub/local provider behind the adapter; no real endpoint; production AI explicitly out of skeleton scope |
| **WS-3** | Materiality value (OQ-8) not available | Use a synthetic default in versioned config (DEC-019); golden dataset defines the expected finding; real value plugs in later |
| **WS-4** | Cross-platform determinism gaps found late | ADC-05 + both-OS CI from the first rule; determinism test on R-BUD-02 day one |
| **WS-5** | Doing too much ("just one more rule/screen") | §5 exclusions are binding; one of everything, nothing more (P-6) |
| **WS-6** | Coding starts before skeleton-critical ADRs Accepted | Hard prerequisite (§9); Gate 5 blocks until Gate 3 done |
| **WS-7** | Confidential/real data used in the skeleton | Synthetic only (P-3/NFR-018); dev-data-hygiene guard (12 Gate 4) |
| **WS-8** | Verification gate implemented as a flag, not by construction | `VerifiedDataset` is the only engine input type (ADC-10); integration test asserts unrepresentability |

## 18. Recommended Build Order

Cross-cutting spine first (audit + persistence from story one — 06 §21), then the linear thread, then the optional AI. Test-first at every step.

0. **Prerequisites:** skeleton-critical ADRs Accepted (§9); repo + both-OS CI + trace gate + golden-dataset framework ready (Gate 4); PLAN/TASKS for the slice approved (Gate 5).
1. **Spine:** ReviewCycle + DAL (transactional, crash-safe) + `AuditEventPort` + ConfigVersion — prove persistence and audit on a trivial state transition first.
2. **Step 1 Setup:** create the cycle; audit it.
3. **Step 2–3 Upload + Validation:** intake GED + Budget with provenance; required-file/completeness check.
4. **Step 4 Processing:** extraction + cell-level lineage + minimal readiness verdict (exact decimal).
5. **Step 5 Verification (gate):** verification workspace + correction path + **`VerifiedDataset` construction**; assert the gate by construction.
6. **Step 6–7 Analysis + Finding:** R-BUD-02 (with R-BUD-01, R-FND-02); versioned run; one finding via `FindingsCommandPort`; golden + determinism + cross-platform tests green.
7. **Step 8 Summary:** one Budget Health section (deterministic) + empty labeled narrative slot.
8. **Step 9 Export:** one labeled, self-describing export; AI-off-completeness test green here.
9. **Minimal Explain This:** deterministic explanation first; then optional stubbed narration via query port; grounding/citation test.
10. **Minimal Ask Fin:** grounded, cited, consent-gated (stubbed), declines-unsupported; degrades to deterministic library with AI off.
11. **Verify the skeleton:** run §13 criteria; `/sdd:verify` the feature; confirm `TRACEABILITY: PASS`.

At each step: `Implements:`/`Verifies:` annotations, audit events, and a commit `[F-##-##]`. Refusals from the gated flow name the missing gate — treat them as navigation.

---

*End of 13-walking-skeleton-plan.md — the smallest end-to-end slice that proves the approved FinSight architecture and UX work together: one review cycle, one upload, one validation, one verification (the gate), one rule, one finding, one summary, one export, plus minimal grounded Explain This and Ask Fin — all deterministic, audited, traceable, accessible, and AI-optional. It introduces no new scope; it follows the approved 9-step flow and the approved Fin strategy. Implement via a Gate-5 `PLAN-F-…`/`TASKS-F-…` once the skeleton-critical ADRs are Accepted.*
