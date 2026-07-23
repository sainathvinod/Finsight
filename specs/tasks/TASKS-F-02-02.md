# TASKS-F-02-02 — Deterministic Walking Skeleton

- **Plan:** specs/plans/PLAN-F-02-02.md · **Feature:** F-02-02 (anchor); walking-skeleton slice (DEC-022, docs/13)
- **Status:** Approved — Executable (project-owner-approved baseline; documentary date not recorded in repository)
- **Scope:** deterministic thread only. **Excludes Ask Fin, Explain This, production AI** (later AI slice, after ADC-03/04/07).

**How to work these tasks (per 11-development-methodology §3 and Constitution §7):**
- Ordered; respect `Depends`. Each task is ~half a day and individually testable.
- **Test-first:** write the failing test → minimal code → quality gates green → annotate `Implements:`/`Verifies:` → tick the box → commit `[F-02-02]`.
- A task is done only when its slice satisfies the plan's **Definition of Done / Acceptance Criteria** (PLAN §Acceptance) and CI is green (both-OS, `TRACEABILITY: PASS`).
- Run via `/sdd:implement` (one task per invocation); refusals name the missing gate.

---

## Phase A — Environment & spine (audit + persistence from story one)

- [ ] **T-001 — Repository & environment scaffold.** Package layout (`finsight/domain`, `application`, `infrastructure`, `delivery`) + composition root (ADR-002); both-OS CI matrix (Windows + macOS); `pytest` + import-linter; golden-dataset framework (synthetic only); dev-data-hygiene guard (rejects real-data-shaped fixtures); wire `/sdd:trace --fail-on-orphans` as a merge gate. *Verifies:* NFR-018, NFR-029 (harness), NFR-031, NFR-033 (gate). *Depends:* — (needs ADR-001/002 Accepted).
- [ ] **T-002 — Architecture/import-contract tests.** Enforce: domain core imports no UI/storage/provider/AI types; `FindingsCommandPort` reachable only from C-07/C-11; only the DAL touches storage; **format-specific readers (`ExcelReader`) live in infrastructure behind the core-defined `DocumentReader` interface** (the core imports no reader/format types). *Verifies:* NFR-047, NFR-031, NFR-045 (ADR-002). *Depends:* T-001.
- [ ] **T-003 — Persistence & DAL (SQLite) + crash-safety + backup/restore.** Repository interfaces + SQLite implementation behind the DAL; transactions (all-or-nothing); amounts as integer minor units (never `REAL`); crash-safe/resumable state; single-file backup + restore. *Verifies:* NFR-005, NFR-057, NFR-060, NFR-072 (ADR-004). *Depends:* T-001, T-002.
- [ ] **T-004 — Audit event architecture.** Core-owned `AuditEventPort`; append-only, versioned (v1) event store via the DAL; taxonomy for the skeleton's steps; reconstruction query. *Verifies:* NFR-019, FR-086 (ADR-005). *Depends:* T-003.
- [ ] **T-005 — Config registry & ConfigVersion.** Versioned configuration holding R-BUD-02's synthetic materiality default + severity bands; bound to each analysis run. *Verifies:* FR-107, NFR-022 (ADR-003/004). *Depends:* T-003.

## Phase B — Domain core, cycle & the gate

- [ ] **T-006 — Review Cycle aggregate + state model + Step 1 (Review Setup).** (Month, Year) aggregate; two-region state model (per-artifact + cycle projection); resumable + transactional persistence; create-cycle on Month/Year selection; audit the creation; wizard "Step 1 of 9". *Verifies:* FR-005, FR-006, NFR-006 (ADR-006). *Depends:* T-003, T-004.
- [ ] **T-007 — Step 2 (Data Upload) + provenance.** Ingest GED report + Budget Tracker (Excel) read-only; record provenance (name, fingerprint, timestamp, user, period, type); audit per file; source files never modified. *Verifies:* FR-001, FR-003, FR-010, NFR-012 (safe rejection). *Depends:* T-006.
- [ ] **T-008 — Step 3 (Upload Validation).** Required-file/completeness check; unreadable/corrupt/missing files rejected with plain-language reason + next step; nothing silent. *Verifies:* FR-007, NFR-055, NFR-062. *Depends:* T-007.

## Phase C — Processing (extraction, lineage, readiness)

- [ ] **T-009 — Step 4a (Document Extraction Framework seam — minimal F-01-05).** Build the thinnest seam serving GED + Budget: a **core-defined `DocumentReader` interface**; a single **`ExcelReader`** implementation (infrastructure) reading `.xlsx` and emitting raw cell values with source references (file/sheet/row/col); a small **type registry** (GED report, Budget Tracker → reader + expected schema); and the **extraction-pipeline skeleton** (read → normalize → validate → lineage/confidence — a plain deterministic function chain, **no agent/orchestrator/planner**). Handle structural noise (preamble rows, `TOTAL FOR ACCOUNT…` subtotals, blanks, merged/repeated headers). **Excel only.** *Verifies:* FR-011, FR-012, FR-013, NFR-045; F-01-05. *Depends:* T-008.
- [ ] **T-010 — Step 4a (Normalization service + lineage + confidence).** A **reusable Normalization service** invoked by the pipeline: exact-decimal amounts (`Decimal`, pinned context; no float), dates, periods, identifiers, placeholders/credits/negatives; preserve raw value + source cell reference per value; assign confidence. *Verifies:* FR-014, FR-015, FR-016, NFR-059 (ADR-003); F-01-05. *Depends:* T-009.
- [ ] **T-011 — Step 4b (Validation service + readiness verdict).** A **reusable Validation service** invoked by the pipeline: schema checks per registered type + row-level quality (missing required fields, invalid accounts, malformed dates/periods, non-numeric amounts); then a single-capability readiness verdict (Budget analysis Available/Unavailable + reason); no analysis yet. *Verifies:* FR-021, FR-022, FR-081 (subset); F-01-05. *Depends:* T-010.

## Phase D — Verification (the hard gate)

- [ ] **T-012 — Step 5a (Verification workspace).** Present extracted data with one-click source trace; support optional correction preserving the original value + user + timestamp in lineage; per-document approve / approve-with-corrections / reject; audit each decision. *Verifies:* FR-016, FR-027, FR-028, FR-029, NFR-069. *Depends:* T-011.
- [ ] **T-013 — Step 5b (VerifiedDataset by construction).** Construct the `VerifiedDataset` only on explicit approval; make it the Rules Engine's sole input type so unverified data cannot reach a rule (gate integration test). *Verifies:* FR-026, NFR-047 (TB-02, ADR-006). *Depends:* T-012.

## Phase E — Analysis, finding, summary, export

- [ ] **T-014 — Step 6a (R-BUD-01 variance) + versioned RuleRun.** Compute planned-vs-actual variance (amount + %) by dimension on the `VerifiedDataset`, exact decimal; record the RuleRun (rule-set + config version + input fingerprint). *Verifies:* FR-030, FR-031, FR-086, NFR-021, NFR-022 (R-BUD-01). *Depends:* T-013, T-005.
- [ ] **T-015 — Step 6b (R-BUD-02 flag + R-FND-02 severity) + author golden dataset.** Flag over/under-budget against the synthetic materiality config; classify severity via R-FND-02; emit the finding via `FindingsCommandPort` (rules-only write path); author the seeded synthetic golden month that yields exactly one expected finding. *Verifies:* FR-033, FR-070, NFR-036 (R-BUD-02, R-FND-02). *Depends:* T-014.
- [ ] **T-016 — Step 7a (Finding domain model).** The finding contract in the core (id, rule ref, severity, period, entities, evidence values, source refs, `New` state); persisted; readable via `FindingsQueryPort`. *Verifies:* FR-069, FR-071 (ADR-007, R-FND-01). *Depends:* T-015.
- [ ] **T-017 — Step 7b (Findings render) + minimal wizard shell.** C-09b renders the one finding via the query port — severity as icon/shape + label (not color alone), evidence, one-hop source trace; minimal 9-step wizard frame ("Step X of 9"), keyboard-operable. **No Explain This.** *Verifies:* FR-070 (presentation), FR-074/082 (minimal), NFR-025, NFR-026, NFR-065, NFR-067. *Depends:* T-016.
- [ ] **T-018 — Step 8 (Leadership Summary).** Compose one deterministic Budget Health section; include an AI-narrative slot that is present, labeled, and **empty**; summary reads complete without AI. *Verifies:* FR-076, FR-095. *Depends:* T-017.
- [ ] **T-019 — Step 9 (Export).** Produce one self-describing, labeled export (period, data-as-of, config version, AI-content labeling). *Verifies:* FR-116, FR-120. *Depends:* T-018.

## Phase F — Cross-cutting verification & closure

- [ ] **T-020 — Determinism test.** Repeat-run on the same `VerifiedDataset` + ConfigVersion → byte-identical finding/severity/evidence; re-run produces no duplicate. *Verifies:* NFR-008, NFR-021. *Depends:* T-019.
- [ ] **T-021 — Cross-platform test.** Run the golden dataset on Windows and macOS in CI → identical results (release gate). *Verifies:* NFR-029, NFR-048. *Depends:* T-020.
- [ ] **T-022 — Boundary, extensibility-seam & audit-completeness assertions.** Harden the architecture/import tests as breadth landed; **assert the F-01-05 extensibility seam — a second stub `DocumentReader` registers and runs without modifying the Normalization service, the Validation service, or the pipeline**; assert every step emitted an audit event and the cycle timeline reconstructs the review from events alone. *Verifies:* NFR-047, NFR-045, NFR-019, FR-084 through FR-089. *Depends:* T-004, T-009, T-019.
- [ ] **T-023 — Traceability closure + verify the feature.** Confirm `Implements:`/`Verifies:` annotations on every unit/test; run `/sdd:trace --fail-on-orphans` → `TRACEABILITY: PASS`, zero orphans; run `/sdd:verify F-02-02`, recording per-criterion evidence in `specs/verification/VERIFY-F-02-02.md` (see PLAN §Verification Evidence Requirements). *Verifies:* NFR-033, and all Acceptance Criteria AC-1…AC-15. *Depends:* T-001 through T-022.

---

**Task count:** 23 (unchanged — no new tasks required). The minimal **F-01-05 Document Extraction Framework seam** — `DocumentReader` interface, `ExcelReader`, Normalization service, Validation service, extraction pipeline — is realized in **T-009–T-011** and asserted in **T-002 / T-022** (AC-16); it introduces no new product scope and no AI. **No autonomous agents, multi-agent systems, orchestration frameworks, agent memory, or agent planning** (DEC-034; Constitution §6). **Golden dataset** authored in T-015 (synthetic only, NFR-018). **Verification** (`/sdd:verify`) is T-023 and flips statuses to Verified only on a full pass — no partial credit (NFR-048). All work is real-data-free (Constitution P-3/§7).
