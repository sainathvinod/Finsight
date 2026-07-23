# PLAN-F-02-02 — Deterministic Walking Skeleton (anchored on F-02-02 Deterministic Execution Pipeline)

- **Feature:** F-02-02 — Deterministic Execution Pipeline (specs/04-features.md) — *anchor*
- **Epic:** E-02 — Deterministic Rules Engine (enabler); slice spans E-14, E-01, E-02, E-08, E-06, E-07
- **Author:** AI-drafted for human review · **Date:** 2026-07-16
- **Status:** Approved — Executable (project-owner-approved baseline; documentary date not recorded in repository)
- **Realizes:** docs/13-walking-skeleton-plan.md (the deterministic thread, steps 1–9); Build-Readiness Gate 5

> **Scope of this plan:** the **deterministic walking skeleton only.** It **excludes Ask Fin, Explain This, and all production AI** (steps 10–11 of 13 §18). Those are a later AI slice, planned separately after **ADC-03 (AI provider adapter/grounding), ADC-07 (egress/consent), and ADC-04 (orchestration)** are formalized (consistency finding A-1). With AI excluded, **AI-off completeness (FR-095) is satisfied by construction** — there is no AI in this build; the deterministic output produced here becomes the baseline the future AI slice's provider-swap regression must preserve unchanged.

> **Cross-feature note:** the walking skeleton is a deliberately cross-cutting vertical slice (DEC-022; 04-features §2.2 "storage/DAL … belongs to no feature"). This plan is anchored on **F-02-02** (the pipeline it exists to prove) and **co-delivers minimal slices** of: F-14-01/02/04 (shell, never-lose-work, data protection), F-01-01/02/03/05/06/07/08/09 (cycle, upload, recognition, **document-extraction framework seam**, GED+Budget extraction, quality gate, verification), F-02-01/04/06 (rule contract, findings contract, replay), F-03-03 (budget exception rule pack — the one rule), F-06-01/02 (findings inbox/investigation, deterministic parts only), F-07-01/04 (summary, export), F-08-01 (audit capture). The team may re-file per-feature if preferred; a single skeleton plan is the pragmatic convention.

## Context

FinSight's design set (00–13), Constitution, and seven skeleton-critical ADRs are complete. Before any feature breadth, one thin thread must prove the architecture and UX work together end-to-end: **Review Setup → Upload → Validation → Processing (extraction + lineage + readiness) → Verification (the gate) → Analysis (one rule) → Findings (one finding) → Leadership Summary (one section) → Export**, with **audit and transactional persistence from story one** and the **cross-platform determinism test running on the first rule** (06 §21, 13). If this thread cannot run through the verification gate, the deterministic core, the audit port, the DAL, the findings contract, and the export path, those boundaries are wrong — and that is discovered on day one.

The two forces that most shape this build: **(1) verification-before-analysis must be structural** (the engine consumes only a `VerifiedDataset`, constructible solely at approval — ADR-006), and **(2) determinism must be byte-identical across repeated runs and both platforms** (ADR-003). This plan deliberately does *not* cover: any other rule/capability, any AI, wrong-file replacement, historical/comparison, Review Health, What's New, quarantine breadth, or production polish (13 §5).

### Preconditions (satisfied under the approved baseline — P-1, Build-Readiness §16)

All preconditions below are satisfied under the project-owner-approved baseline; this plan is Approved — Executable.

1. **Gate 1:** DEC-024–034 ratified (✅).
2. **Gate 2:** `docs/00–13` migrated + normalized into `specs/`; Constitution adopted; baseline established; hooks active. The requirements this plan's FR/NFR traces resolve to are Approved.
3. **Gate 3:** **ADR-001…ADR-007 Accepted** (approved architecture baseline). ADC-08 (at-rest/secrets) not required — skeleton uses synthetic data only; **no AI ADRs needed** (AI excluded).
4. **Gate 4:** repository stood up; **both-OS CI** (Windows + macOS) green on a trivial change; **`/sdd:trace --fail-on-orphans` gate wired**; pytest + import-linter harness scaffolded; ≥1 synthetic golden dataset; dev-data-hygiene guard active.
5. This plan is approved under the current baseline; its review record is referenced below.

## Requirement constraints

Every NFR that constrains this design, with its fit criterion (verbatim intent from 02) and the constraint it imposes.

| ID | Fit criterion (measurable) | Design constraint it imposes |
|---|---|---|
| NFR-021 | Same verified inputs + config version ⇒ identical findings/statuses/severities/variances | No wall-clock/locale/RNG on compute paths; versioned+fingerprinted run (ADR-003/006) |
| NFR-029 | Byte-identical deterministic results on Windows **and** macOS | Both-OS CI matrix; exact decimal; explicit ordering (ADR-001/003) |
| NFR-059 | Monetary math exact; no cent-level float error | `decimal.Decimal` pinned context; amounts as integer minor units / decimal text, never `REAL` (ADR-003/004) |
| NFR-005 / NFR-057 | Crash never loses verified data; multi-step persistence all-or-nothing | Transactional DAL; persist at each cycle transition (ADR-004/006) |
| NFR-006 | Cycle pauses/resumes across restarts without rework | State persisted per transition; resume from last consistent state (ADR-006) |
| NFR-008 | Re-analysis idempotent; no duplicate findings/reports | Re-run keyed to VerifiedDataset + config version (ADR-006) |
| NFR-019 | Every material action attributable & reconstructable | Emit an AuditEvent through the port on every step (ADR-005) |
| FR-026 | No analysis on unverified data | Engine accepts only `VerifiedDataset`; only C-06 constructs it (ADR-006) |
| FR-071 / NFR-067 | From any finding: rule → inputs → source in one interaction | Finding carries evidence + cell-level source refs (ADR-007; extraction lineage) |
| NFR-025 | No meaning by color alone (severity/RAG) | Severity rendered as icon/shape + label + color (ADR-007; C-09b) |
| NFR-026 | Primary workflow keyboard- & screen-reader-operable | Wizard steps keyboard-traversable; accessible names (C-01) |
| NFR-036 / NFR-048 | Golden-dataset determinism passes; determinism is a release gate | One golden dataset → exactly the expected finding; gate in CI |
| NFR-062 | No silent failure; partial results never shown as complete | Validation/readiness surface reasons; errors actionable (C-03/C-05) |
| FR-120 | Exports self-describing & labeled | Export carries period, data-as-of, config version, AI-content labeling (empty) (C-12) |
| FR-086 / NFR-022 | Run records rule-set + config versions + input fingerprint | RuleRun record; ConfigVersion bound to the run (ADR-003/005) |
| NFR-045 | Adding a document type is a new reader + template, not a redesign | Read/normalize/validate behind a `DocumentReader` interface + extraction pipeline (minimal F-01-05); Excel only now |
| NFR-031 | Composable, replaceable modules behind interfaces | Reader/normalization/validation are separable services behind the pipeline (ADR-002) |

## Proposed design

A single deterministic vertical thread across minimal slices of the approved components (06 §7–§8), wired at a composition root (ADR-002). Dependencies point inward; the domain core imports no UI/storage/AI types.

- **Components (minimal slices):**
  - **C-17 DAL (SQLite, ADR-004)** — the only storage touch; repository interfaces; transactions; single-file backup-capable. Amounts stored as integer minor units.
  - **C-14 Audit (ADR-005)** — core-owned `AuditEventPort`; append-only, versioned v1 events; SQLite-backed via the DAL.
  - **C-08 Config Registry** — holds R-BUD-02's parameters (a **synthetic `CP-VAR-MATERIALITY` default** + severity bands) as a **versioned `ConfigVersion`**; bound to each run.
  - **C-02 Orchestrator** — a **trivial, deterministic fixed-sequence step runner** (resolves consistency finding A-5: no ADC-04 needed for a fixed deterministic sequence; documented here per ADR-002 §10). Enforces the verification gate; reports "Step X of 9".
  - **C-03 Intake** — accept **GED report + Budget Tracker** (Excel) read-only; record provenance; required-file/completeness validation.
  - **C-04 Extraction & Normalization — minimal F-01-05 Document Extraction Framework seam.** The thinnest version that serves the GED + Budget Tracker files and no more, realizing the approved R1 enabler F-01-05 and the XP-02 seam:
    - a **core-defined `DocumentReader` interface** (the contract), with a **single `ExcelReader` implementation in infrastructure** (per ADR-002 dependency rule) that reads `.xlsx` and emits raw cell values with source references (file/sheet/row/col);
    - a tiny **type registry** mapping the two document types (GED report, Budget Tracker) → reader + expected schema;
    - a deterministic **extraction pipeline** (a plain function chain: read → normalize → validate → lineage/confidence) — **not** an agent, orchestrator, or planner;
    - a reusable **Normalization service** — exact-decimal amounts (ADR-003), dates, periods, identifiers, placeholders/credits/negatives — preserving raw value + cell-level lineage and assigning confidence.
    Structural noise (title/preamble rows, `TOTAL FOR ACCOUNT…` subtotals, blanks, merged/repeated headers) is handled here (FR-013). **Excel only — no PDF/DOCX/CSV readers** (later phases; PDF is Phase 3, FR-002).
  - **C-05 Quality & Readiness — reusable Validation service.** A **Validation service** (schema checks per registered type + row-level quality: missing required fields, invalid accounts, malformed dates/periods, non-numeric amounts) invoked by the pipeline; and a single-capability readiness verdict (**Budget analysis: Available / Unavailable + reason**).
  - **C-06 Verification** — present extracted data with source trace; capture optional correction (original preserved); capture explicit approval; **construct the `VerifiedDataset`**.
  - **C-07 Rules Engine (ADR-002/003)** — execute one rule over the `VerifiedDataset`; versioned+fingerprinted `RuleRun`; emit the finding via `FindingsCommandPort`.
  - **C-09a Findings Domain Model (ADR-007)** — finding contract + severity (R-FND-02) + `FindingsCommandPort`/`FindingsQueryPort`; minimal lifecycle (`New`).
  - **C-09b Findings Experience** — render the one finding via `FindingsQueryPort` (severity icon+label, evidence, one-hop source trace). **No Explain This.**
  - **C-12 Reporting & Export** — compose one **Budget Health** summary section (deterministic) with an **empty, labeled AI-narrative slot**; produce one **labeled export**.
  - **C-01 Shell** — minimal 9-step wizard frame ("Step X of 9"), keyboard-operable, color-independent severity. **No Ask Fin.**
  - *(Excluded: C-15 AI Assistance, C-16 Consent — AI slice.)*
- **The one rule:** **R-BUD-02 — Over/Under-Budget Flagging & Severity**, composing **R-BUD-01** (variance) as input and **R-FND-02** (severity) as method. Materiality value is a **synthetic default in the `ConfigVersion`** (OQ-8 resolved under the approved baseline; DEC-019: value is configuration, not code) so the golden dataset yields a known finding. No real materiality value is invented.
- **Data & contracts (logical; schema bound by ADR-004):** `ReviewCycle`, `IngestedFile` (name, fingerprint, ts, user, period, type), `ExtractedRecord` (raw + normalized + source cell ref + confidence), `ReadinessResult`, `VerificationDecision` (approve/approve-with-corrections/reject; corrections original→corrected), **`VerifiedDataset`** (constructible only by C-06), `RuleRun` (rule-set + config version + input fingerprint), `Finding` (id, rule ref, severity, period, entities, evidence, source refs, state), `SummarySection`, `Export`, `AuditEvent`, `ConfigVersion`. *(No `AIInteraction` — AI excluded.)*
- **Failure & degradation behavior:** unreadable/missing files → plain-language rejection + named missing item (NFR-062); a validation/quality failure quarantines without blocking; a crash mid-run loses no verified data and resumes (NFR-005/006); errors are actionable, never raw traces (NFR-055).
- **Traceability:** each implementing unit carries `Implements: FR-###, F-02-02` (rule code adds `R-BUD-02`); each test carries `Verifies: FR-###/NFR-###`.

## Implementation Assumptions (synthetic fixtures)

The skeleton is built and tested on **synthetic data only** (NFR-018, Constitution P-3); no real customer data enters development. The synthetic GED and Budget Tracker fixtures below are the **thinnest structures** that (a) carry the observed fields (FR-011/012), (b) exercise the real-world quirks the pipeline must handle (FR-013; NFR-038), and (c) are **structurally faithful approximations** of the real samples "in hand" (00 §6; assumption A-12). They **stand in for the real files** for the skeleton; they add no scope and change no requirement.

- **Synthetic GED layout — one Excel sheet.** Columns for the FR-011 observed fields: department #/name, account #/name, fiscal period, journal #/date, invoice amount, check #, invoice date, vendor name, agency, journal description, journal-line description, amount. To exercise FR-013/NFR-038 it includes: a title/preamble block above the header row, at least one `TOTAL FOR ACCOUNT …` subtotal row per account group, blank and merged/repeated-header rows, and at least one credit/negative amount and one placeholder (`.`) value. Populated with ≥2 accounts × ≥2 vendors whose amounts produce a known variance against the budget fixture.
- **Synthetic Budget Tracker layout — one Excel workbook, three sheets (FR-012).** *Original Budget* (the sheet the rule reads): per account — budget, actuals-to-date, estimate-to-complete, estimate-at-completion, delta, notes. *Details*: minimal invoice-detail rows (account, vendor, description, date, invoice #, status, comment, owner, approver). *Actuals*: a minimal GED-extract-plus-cleared/comment structure. Figures are set so **exactly one** account/vendor breaches the synthetic materiality default.
- **Expected result.** The two fixtures together yield **exactly one** deterministic finding (the golden-dataset assertion, AC-7/AC-8), byte-identical across runs and platforms. R-BUD-01 reads `planned = budget` and `actual = actuals-to-date` from the Original Budget sheet (per 05 R-BUD-01 "prefer workbook figures").
- **Validation against real files — pre-pilot condition, not a skeleton task.** The synthetic layouts *approximate* the real samples. Before any **pilot / real-data usage**, extraction and the golden fixtures are validated against a **real sanitized GED + Budget Tracker sample** (or an equivalent extraction-template spec) to confirm structural fidelity (A-12; readiness-review IMP-1). This validation is a **precondition to pilot**, deliberately **out of scope for the skeleton build**, which proves the pipeline on synthetic data.

---

## Acceptance Criteria *(Deliverable 3 — binding; Given/When/Then per the acceptance-designer method)*

**AC-1 — Review Setup creates a cycle.** *Given* the app is open, *when* the user selects a Month and Year and confirms, *then* a Review Cycle is created, shown as "Step 1 of 9", and an audit event records its creation. *(FR-005/006)*

**AC-2 — Upload accepts the two documents read-only with provenance.** *Given* a new cycle, *when* the user uploads a GED report and a Budget Tracker, *then* each is ingested without modifying the source file, provenance is recorded (name, fingerprint, timestamp, user, period, type), and an audit event is written per file. *(FR-001/003/010)*

**AC-3 — Validation names missing/unreadable inputs; nothing silent.** *Given* uploads, *when* the user runs Upload Validation, *then* the system confirms required files are present or states, in plain language, exactly what is missing or unreadable and the next step; an unreadable/corrupt file is rejected with a reason and never crashes the app. *(FR-007; NFR-012/062)*

**AC-4 — Processing extracts with cell-level lineage and exact decimals; no analysis.** *Given* validated uploads, *when* processing runs, *then* GED/Budget fields are extracted, each value carries its raw original and a source cell reference, amounts are exact decimals (no float), a Budget-analysis readiness verdict (Available/Unavailable + reason) is produced, and **no rule has executed.** *(FR-011/012/013/015; NFR-059; readiness R-RDY-07 subset)*

**AC-5 — Verification is a hard gate that constructs the VerifiedDataset.** *Given* extracted data, *when* the user reviews it (with one-click source trace), optionally corrects a value (original preserved with user+timestamp), and confirms "I have reviewed the extracted data and confirm it is correct," *then* a `VerifiedDataset` is constructed and the "Analyze" step becomes available; **until confirmation, there is no code path that runs a rule.** *(FR-026/027/028/029; TB-02)*

**AC-6 — Analysis runs one rule on verified data, versioned.** *Given* a `VerifiedDataset`, *when* analysis runs, *then* R-BUD-02 executes (via R-BUD-01 variance + R-FND-02 severity) using the synthetic materiality `ConfigVersion`, and the run records the rule-set version, configuration version, and input fingerprint. *(FR-030/033/086; NFR-022)*

**AC-7 — One finding with severity, evidence, and one-hop source.** *Given* analysis on the golden dataset, *when* it completes, *then* exactly one finding is produced with a computed severity (icon/shape + label, not color alone), its variance evidence, and a source reference reachable in one interaction. *(FR-069/070/071; NFR-025/067; R-FND-01/02)*

**AC-8 — Deterministic & byte-identical across runs and platforms.** *Given* the same `VerifiedDataset` and `ConfigVersion`, *when* analysis is re-run and run on Windows and macOS, *then* the finding/severity/evidence are byte-identical; re-run produces no duplicate finding. *(NFR-021/029/008/036/048)*

**AC-9 — Leadership Summary composes one deterministic section.** *Given* the finding, *when* the summary is generated, *then* a Budget Health section presents the deterministic figures, with an AI-narrative slot present, labeled, and **empty**; the summary reads complete without AI. *(FR-076/095; F-07-01)*

**AC-10 — Export is self-describing and labeled.** *Given* the summary, *when* the user exports, *then* one export is produced carrying period, data-as-of, configuration version, and AI-content labeling. *(FR-116/120)*

**AC-11 — Audit reconstructs the whole thread.** *Given* a completed run, *when* the audit trail is inspected, *then* every step (setup, upload, validation, extraction, verification, analysis, finding, summary, export) is present with actor + timestamp, sufficient to reconstruct the review from events alone. *(FR-084–089; NFR-019)*

**AC-12 — Crash-safe & resumable.** *Given* an analysis in progress, *when* the process is force-killed and restarted, *then* no verified data or audit records are lost and the cycle resumes from the last consistent state. *(NFR-005/006/057)*

**AC-13 — Accessible & color-independent.** *Given* the nine steps, *when* navigated by keyboard, *then* each step and control is reachable and labeled, and severity/status meaning is conveyed without relying on color. *(NFR-025/026)*

**AC-14 — Structural boundaries hold.** *Given* the codebase, *when* the architecture/import test runs, *then* the domain core imports no UI/storage/AI types, `FindingsCommandPort` is reachable only from C-07/C-11, and only the DAL touches storage. *(NFR-047; ADR-002/004; P-8)*

**AC-15 — Fully traceable.** *Given* the implementation, *when* `/sdd:trace --fail-on-orphans` runs, *then* every unit/test carries its `Implements:`/`Verifies:` annotation, the verdict is `TRACEABILITY: PASS`, and there are zero orphans. *(NFR-033; P-5)*

**AC-16 — Extraction runs through the F-01-05 seam and is extensible.** *Given* the extraction framework, *when* GED and Budget Tracker are processed, *then* both flow through the `DocumentReader` interface via the `ExcelReader`, the Normalization and Validation services, and the extraction pipeline; *and* a second stub `DocumentReader` can be registered and run **without modifying** the Normalization service, the Validation service, or the pipeline. Format-specific reading lives in infrastructure; the domain core imports no reader/format types. *(FR-013/014/016; NFR-045/031; F-01-05; ADR-002; XP-02)*

## Alternatives considered

| Alternative | Why rejected for the skeleton |
|---|---|
| A different single rule (e.g., R-GED-02 duplicate detection) | Valid and parameter-free, but uses one document; R-BUD-02 exercises **both** uploads and feeds Budget Health — tighter fit to the 9-step flow (13 §10). Recorded as the accepted alternative. |
| Include the AI slice now | Excluded by instruction and finding A-1; needs ADC-03/07/04; deterministic thread must prove out first (13 §18). |
| Backend-only skeleton | 13 §UI requires a minimal version of the approved wizard UX — a backend-only slice would not prove the UX/architecture together. |
| Real materiality value | None is approved (OQ-8 open); a synthetic configurable default + golden dataset is the DEC-019-correct approach. |
| One-off Excel parser (no `DocumentReader` interface) | Faster to write, but misses the approved F-01-05 seam and XP-02 extensibility; a second document type would force a rewrite, and the domain core would couple to a format. Rejected in favor of the minimal seam. |

## Risks and mitigations

| Risk | L | I | Mitigation | Owner |
|---|---|---|---|---|
| Verification gate built as a flag, not by construction | Med | High | `VerifiedDataset` is the engine's only input type; AC-5/AC-14 assert unrepresentability (ADR-006) | Implementer |
| Cross-platform determinism gap found late | Med | High | Determinism + both-OS CI on the one rule from the first analysis task (ADR-003) | Implementer |
| Accidental `float`/`REAL` for money | Med | High | Lint rule + review + golden test catch divergence (ADR-003) | Implementer |
| Scope creep ("one more rule/screen") | Med | Med | §Scope exclusions binding; one of everything (P-6) | Reviewer |
| Tauri + Python-sidecar packaging friction | Med | Med | ADR-001 spike; Electron fallback (no core change) | Architect |
| Executing before gates clear | Low | High | Preconditions satisfied under the approved baseline; gates recorded above | Project Owner |

## Test strategy

Suites follow the golden-testing skill; every suite names the IDs it verifies (`Verifies:`). Test-first per task.

- **Unit** — extraction of observed GED/Budget fields; R-BUD-01 variance (edge: planned=0 → "unbudgeted" marker); R-BUD-02 flag + R-FND-02 severity — *Verifies:* FR-011/012, FR-030/033, FR-070.
- **Golden-dataset (one)** — seeded synthetic month (GED + Budget with a known variance) → **exactly one** expected finding, severity, and evidence traceable to source lines; synthetic data only — *Verifies:* NFR-036, FR-069.
- **Determinism** — repeat-run byte-identical on the same VerifiedDataset+ConfigVersion — *Verifies:* NFR-021/008.
- **Cross-platform** — identical results on Windows and macOS in CI — *Verifies:* NFR-029.
- **Verification-gate integration** — the engine has no entry but a `VerifiedDataset`; unverified data cannot reach a rule — *Verifies:* FR-026, NFR-047.
- **Audit-completeness** — every step emits an AuditEvent; the trail reconstructs the review — *Verifies:* NFR-019, FR-084–089.
- **Crash-safety** — force-kill mid-analysis loses nothing; resumes — *Verifies:* NFR-005/006/057.
- **Architecture/import** — core imports no UI/storage/AI; command port isolation; DAL-only storage — *Verifies:* NFR-047/031, ADR-002/004.
- **Accessibility smoke** — keyboard traversal; color-independent severity — *Verifies:* NFR-025/026.
- **Backup/restore** — back up the SQLite store and restore on a fresh install; data + audit intact — *Verifies:* NFR-060.
- *(Provider-swap/AI-off: N/A now — no AI; the deterministic output here is the baseline the future AI slice must not change — NFR-037/FR-095.)*

## ADRs

| ADR | Decision (one line) | Status |
|---|---|---|
| ADR-001 | Python headless core; Tauri shell (Electron fallback); loopback-only boundary | Accepted |
| ADR-002 | Layering, dependency rule, core-owned ports (command/query segregation) | Accepted |
| ADR-003 | Exact decimal + determinism strategy | Accepted |
| ADR-004 | SQLite behind the DAL | Accepted |
| ADR-005 | Audit event architecture (core-owned port) | Accepted |
| ADR-006 | Review Cycle + `VerifiedDataset` by construction | Accepted |
| ADR-007 | Findings domain model + command/query ports | Accepted |

*All seven are Accepted (approved architecture baseline). No AI ADR is required for this slice. Orchestration for the deterministic thread is a trivial fixed sequence documented in this plan (no ADC-04).*

## Traceability Matrix *(Deliverable 4 — plan-scoped; the generated `specs/traceability.md` is produced by `/sdd:trace` after implementation)*

*(First column leads with the concern, not a bare requirement ID, so this matrix references — not re-defines — items; the single leading-ID definition list is the Requirement-constraints table above.)*

| Concern / anchor | Task(s) | Intended code annotation | Verifying test |
|---|---|---|---|
| Cycle setup (cycle FR-005/006) | T-006 | `Implements: FR-006, F-02-02` | AC-1 unit/integration |
| Upload & provenance (FR-001/003/010) | T-007 | `Implements: FR-001/003/010` | AC-2 |
| Upload validation (FR-007; NFR-012/062) | T-008 | `Implements: FR-007` | AC-3 |
| Extraction, lineage, decimals (FR-011/012/013/015; NFR-059) | T-009, T-010 | `Implements: FR-011/012/015` | AC-4; unit; golden |
| Document-extraction framework seam (F-01-05; FR-013/014/016; NFR-045/031) | T-009, T-010, T-011 | `Implements: F-01-05, FR-013/014/016` | AC-4/16; unit; extensibility test |
| Readiness verdict (R-RDY-07 subset) | T-011 | `Implements: FR-081 subset` | AC-4 |
| Verification gate (FR-026/027/028/029; TB-02) | T-012, T-013 | `Implements: FR-026/029` | AC-5; gate integration |
| Variance computation (R-BUD-01; FR-030) | T-014 | `Implements: FR-030, R-BUD-01` | AC-6; unit |
| Flag & severity (R-BUD-02, R-FND-02; FR-033/070) | T-015 | `Implements: FR-033/070, R-BUD-02, R-FND-02` | AC-6/7; unit; golden |
| Versioned run (FR-086/NFR-022) | T-014–T-015 | `Implements: FR-086` | AC-6 |
| Finding & lineage (FR-069/071; NFR-067) | T-016 | `Implements: FR-069/071, R-FND-01` | AC-7 |
| Color-independent severity (NFR-025) | T-017 | `Implements: NFR-025` | AC-7/13 |
| Leadership summary (FR-076/095) | T-018 | `Implements: FR-076` | AC-9 |
| Export labeling (FR-116/120) | T-019 | `Implements: FR-116/120` | AC-10 |
| Audit capture (E-08; FR-084–089; NFR-019) | T-004 (+ every step) | `Implements: FR-086 series` | AC-11; audit-completeness |
| Crash-safety & DAL (NFR-005/006/057) | T-003 | `Implements: NFR-005/057` | AC-12; crash test |
| Determinism (NFR-021/029/008/036) | T-020, T-021 | test-only | AC-8 |
| Structural boundaries + reader seam (NFR-047/045; ADR-002/004) | T-002, T-022 | test-only | AC-14/16 |
| Keyboard access (NFR-026) | T-017 | `Implements: NFR-026` | AC-13 |
| Traceability (NFR-033) | T-023 | annotations across all | AC-15; trace PASS |

## Verification Evidence Requirements *(Deliverable 5 — what `/sdd:verify` must capture in specs/verification/VERIFY-F-02-02.md)*

Verification passes only on a **full pass** (no partial credit); statuses flip to Verified only then. For each acceptance criterion, the recorded evidence:

| AC | Required evidence |
|---|---|
| AC-1–AC-3 | Test run output (pass) + a screenshot/log of the setup/upload/validation steps showing "Step X of 9" and a plain-language missing-file message |
| AC-4 | Extraction test output; a sample `ExtractedRecord` showing raw + normalized (decimal) + cell reference; readiness verdict with reason; proof no rule ran (no `RuleRun` yet) |
| AC-5 | Gate-integration test output proving the engine cannot be invoked without a `VerifiedDataset`; a correction record showing original preserved + user/timestamp; the approval event |
| AC-6 | `RuleRun` record showing rule-set version + `ConfigVersion` + input fingerprint; unit-test output for R-BUD-01/R-BUD-02/R-FND-02 |
| AC-7 | The one finding with severity (icon/label), evidence values, and a resolved one-hop source reference; golden-dataset assertion output |
| AC-8 | Repeat-run diff = empty (byte-identical); **both-OS CI logs** (Windows + macOS) showing identical golden output; no-duplicate assertion |
| AC-9 | The rendered Budget Health section; proof the AI-narrative slot is present, labeled, and empty; summary complete with no AI present |
| AC-10 | The export artifact showing period, data-as-of, config version, and AI-content labeling |
| AC-11 | The reconstructed cycle timeline from audit events alone; audit-completeness test output |
| AC-12 | Force-kill/restart demonstration or test showing no lost verified data + resume; transaction test output |
| AC-13 | Keyboard-traversal record for all nine steps; grayscale render proving severity meaning survives without color |
| AC-14 | Architecture/import-test output (core clean; command-port isolation; DAL-only storage) |
| AC-15 | `/sdd:trace` output showing `TRACEABILITY: PASS` and zero orphans; the plan-scoped matrix reconciled to the generated matrix |
| AC-16 | Evidence that GED + Budget flow through the `DocumentReader`/`ExcelReader` + Normalization + Validation + pipeline; architecture-test output showing the core imports no reader/format types; **extensibility-test output**: a second stub `DocumentReader` registers and runs with **no change** to normalization/validation/pipeline |

**Release-gate note:** golden-dataset determinism (NFR-036) and cross-platform (NFR-029) evidence are mandatory; a skeleton that is functionally complete but not byte-identical across platforms **does not pass** (NFR-048).

## Review-board outcome

- **Review record:** not recorded in repository; executability authorized by project-owner approval of the current baseline.
- **Panel:** design (software-architect, data-architect, integration-architect, security-engineer, qa-engineer)
- **Outcome:** Approved under the project-owner-approved baseline; formal panel details not recorded.
- **Open conditions:** none outstanding under the approved baseline (the pre-pilot real-sanitized-sample validation remains a pre-pilot step per Implementation Assumptions).

## Status history

| Date | Status | By | Note |
|---|---|---|---|
| 2026-07-16 | Draft | AI-drafted | Initial Gate-5 plan for the deterministic walking skeleton; AI slice excluded (finding A-1); pending Gates 1–4 + ADR acceptance + design-panel review |
| 2026-07-17 | Draft | AI-drafted | Added minimal F-01-05 Document Extraction Framework seam (DocumentReader interface, ExcelReader, Normalization service, Validation service, extraction pipeline) per the Final Implementation Readiness Review; realizes an approved R1 enabler (no new scope); no agents/AI; AC-16 added; T-009/010/011 re-decomposed, asserted in T-002/T-022 |
| 2026-07-17 | Draft | AI-drafted | Added "Implementation Assumptions (synthetic fixtures)" documenting the synthetic GED + Budget Tracker layouts (grounded in FR-011/012/013; A-12; NFR-018/038) and the pre-pilot validation against real sanitized files (IMP-1); no new scope, no requirement or acceptance-criteria change |
| Date not recorded in repository | Approved — Executable | Project owner | Administrative status synchronization to the project-owner-approved baseline; preconditions/gates recorded as satisfied; plan content, scope, and acceptance criteria unchanged. |
