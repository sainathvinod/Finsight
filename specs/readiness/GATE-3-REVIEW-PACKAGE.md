# Gate 3 Review Package (design-panel briefing)

> **ADR-001–007 are Accepted and PLAN-F-02-02 is Approved under the project-owner-approved architecture baseline.** This package is the briefing that supported that approval. Formal design-panel meeting details are not recorded in the repository and are not fabricated.

## 1. Gate 3 Executive Summary
The seven ADRs and PLAN-F-02-02 are **acceptance-ready**: every cross-reference resolves against the migrated `specs/`, deciders match Constitution §4, the deterministic/AI boundary is stated accurately (enforced by construction + CI, not "compile-time"), and no content defects remain. **Two human gates govern Gate 3:** (a) the **shell packaging spike** (Tauri vs Electron) — ADR-001's one open condition; and (b) sequencing — **baseline v1.0 (Gate 2) should be cut first**, since ADR acceptance and plan approval expect baselined requirements. This package gives the panel, per ADR: an executive summary, the decision, benefits, costs, risks, open conditions, supporting evidence, and the explicit questions to answer — plus the plan package, the shell decision matrix, and the meeting agenda.

## 2. ADR Acceptance Package

### ADR-001 — Application Stack & Shell
- **Executive summary:** Adopt a **Python headless core** with a **web-technology UI in a desktop shell** (Tauri recommended, Electron accepted fallback), a **loopback-only** shell↔core boundary, and the AI layer as a **thin provider adapter** (no agent framework). Validates the DEC-003 direction.
- **Key decision:** Python core + shell choice (per the ADR-001 spike; Electron fallback) + loopback IPC + bundled Python runtime.
- **Benefits:** strongest finance/AI/decimal/Excel/SQLite ecosystem; headless-testable core; web-tech UI eases future web migration; Tauri is light on 8–16 GB restricted laptops.
- **Costs/tradeoffs:** Tauri adds a Rust toolchain + Python-sidecar packaging; two-process IPC boundary; larger installer (bundled Python).
- **Risks:** sidecar packaging/code-signing in restricted corporate environments; IPC complexity.
- **Open conditions:** **the shell spike must resolve** before final acceptance (§4).
- **Evidence supporting acceptance:** consistent with DEC-003/DEC-016; satisfies NFR-028 (parity), NFR-030 (restricted env), NFR-070 (web migration); loopback satisfies NFR-011 (no egress); the headless core enables ADR-002/003.
- **Panel must answer:** (1) Tauri or Electron, on the spike evidence? (2) Is Python-sidecar packaging + code-signing acceptable in the target environment? (3) Confirm the boundary is loopback-only (no external listener)?

### ADR-002 — Layering, Ports & Dependency Rules
- **Executive summary:** Adopt four inward-pointing layers with **core-owned ports** (`FindingsQueryPort`/`FindingsCommandPort`/`AuditEventPort`/repositories); command/query segregation makes the AI/deterministic boundary **structural — enforced by construction + a mandatory CI architecture-fitness test** (corrected from the earlier, inaccurate "compile-time" wording, since the core is Python). Realizes ADC-02.
- **Key decision:** the layered structure + ports + the enforcement mechanism (composition-root wiring, frozen types/no-public-constructor, runtime guard, CI import test).
- **Benefits:** AI structurally cannot author findings; headless, web-migratable core; replaceable modules.
- **Costs/tradeoffs:** more interfaces + a composition root; a small discipline cost (enforced by CI so it doesn't decay).
- **Risks:** boundary erosion over time — mitigated by treating the architecture-fitness test as a mandatory, non-removable merge gate.
- **Open conditions:** none.
- **Evidence:** resolves Trust > AI enforcement honestly in Python; import test specified; consistent with DEC-005, NFR-047, Constitution §6.
- **Panel must answer:** (1) Is the CI architecture-fitness test **mandated as a merge gate**? (2) Are the in-language hardening measures (frozen `Finding`/`VerifiedDataset`, runtime guard) **required, not optional**?

### ADR-003 — Exact Decimal & Determinism
- **Executive summary:** Adopt `decimal.Decimal` with a pinned context (no float on money), **integer minor units in SQLite (never `REAL`)**, injected clock, locale-free parsing/ordering, and an **operational reading of NFR-029** (finding set value-identical across runs/providers/OS; serialized finding output byte-identical; Excel date-system + encoding pinned). Realizes ADC-05.
- **Key decision:** the determinism strategy + the operational NFR-029 reading (which interprets, not changes, NFR-029).
- **Benefits:** reproducible, cent-accurate, cross-platform-identical findings; exact replay.
- **Costs/tradeoffs:** `Decimal` is slower than float (irrelevant at single-department scale); all money must route through the decimal boundary.
- **Risks:** a stray `float`/locale call silently breaks determinism — mitigated by a lint rule, both-OS CI, and golden tests.
- **Open conditions:** confirm the rounding-mode/precision default (a configuration matter, not blocking).
- **Evidence:** the golden-dataset, determinism, provider-swap, and both-OS CI gates (NFR-036/037/048); NFR-021/029/059.
- **Panel must answer:** (1) Accept the operational NFR-029 reading (value-identical findings + byte-identical serialized output)? (2) Confirm the default rounding mode/precision?

### ADR-004 — Persistence (SQLite behind the DAL)
- **Executive summary:** Confirm **embedded single-file SQLite accessed only through the DAL** — transactions, crash-safety, single-file backup/restore; amounts as integer minor units; at-rest protection via ADC-08 (deferred, pre-pilot); future migration to a server DB is a new DAL implementation. SQLite is **locked (DEC-004)**.
- **Key decision:** confirm SQLite-behind-DAL for the single-user MVP.
- **Benefits:** zero-install, offline, single-file, ACID, ubiquitous, replaceable behind repository interfaces.
- **Costs/limitations:** single-writer (fine for single-user); no native decimal (handled by ADR-003); no default encryption (→ ADC-08); backup via the SQLite backup API.
- **Risks:** at-rest gap until ADC-08 — mitigated by synthetic-data-only development.
- **Open conditions:** **ADC-08** (at-rest/secrets) before real/pilot data — **not** a skeleton blocker.
- **Evidence:** DEC-004; NFR-005/006/009/010/057/060/072.
- **Panel must answer:** (1) Confirm SQLite (no re-open)? (2) Accept ADC-08 as a pre-pilot follow-up, not a skeleton blocker?

### ADR-005 — Audit Event Architecture
- **Executive summary:** Adopt a **core-owned `AuditEventPort`** (dependency-inverted; implemented by the audit store), an **append-only, versioned v1 event schema**, and the taxonomy drawn strictly from FR-084–089; tamper-evidence deferred to R2. Realizes ADC-09; satisfies NFR-019.
- **Key decision:** the audit port + v1 event schema + append-only store.
- **Benefits:** auditability by construction; headless-testable core; provenance of every material action.
- **Costs/tradeoffs:** every step must emit an event (a DoD discipline); the append-only store grows (bounded at single-department scale).
- **Risks:** a step forgets to emit — mitigated by the audit-completeness test (merge gate).
- **Open conditions:** NFR-020 tamper-evidence approach (R2).
- **Evidence:** E-08; NFR-019/022/023; the reconstruct-a-month test.
- **Panel must answer:** (1) Accept append-only v1 now with **tamper-evidence deferred to R2** for the walking skeleton? (2) Is the v1 event schema versioned from day one?

### ADR-006 — Review Cycle & VerifiedDataset
- **Executive summary:** Adopt the **(Month, Year) cycle aggregate** with **two orthogonal state regions**, and a **`VerifiedDataset` constructible only by the verification component** (frozen type, module-private factory, runtime guard, CI test) so "analyzed-but-unverified" is **unrepresentable by construction**; resumable and idempotent. Realizes ADC-10; enforces FR-026/TB-02.
- **Key decision:** the cycle state model + the verification gate as a type-level construction guarantee.
- **Benefits:** the verification gate is structural (not a flag); resumable; replayable; matches the multi-document reality.
- **Costs/tradeoffs:** more up-front modeling than a boolean flag; orthogonal regions require care.
- **Risks:** the gate implemented as a flag by mistake — mitigated by the gate-by-construction test.
- **Open conditions:** none.
- **Evidence:** FR-026; NFR-005/006/008; the gate-by-construction + resume tests.
- **Panel must answer:** (1) Confirm `VerifiedDataset`-by-construction (no boolean-flag alternative)? (2) Accept the two-region (per-artifact + cycle) state model?

### ADR-007 — Findings Domain Model
- **Executive summary:** Adopt the **core finding contract** (record + severity via R-FND-02 + lifecycle) with **command/query ports** and the **model (core) / experience (delivery) split**; `Finding` is a frozen type created only via the command port; **one findings experience, no per-capability forks**; severity is deterministic and color-independent. Realizes ADC-11; satisfies FR-069/070/071.
- **Key decision:** the findings model + ports + the model/experience split.
- **Benefits:** uniform, traceable findings across capabilities; AI-explains-never-creates is structural; headless core; color-independent severity (NFR-025).
- **Costs/tradeoffs:** the split + two ports; severity criteria are configuration (synthetic default for the skeleton, OQ-8 for real values).
- **Risks:** a per-capability findings fork under delivery pressure — mitigated by the binding no-fork criterion + review.
- **Open conditions:** severity/materiality **values** (OQ-8 — configuration, not logic).
- **Evidence:** E-06; AP-12; FR-069/070/071; NFR-025/067; the boundary + traceability tests.
- **Panel must answer:** (1) Confirm the model/experience split and the no-fork binding criterion? (2) Accept severity values as configuration deferred to OQ-8?

## 3. PLAN Approval Package (PLAN-F-02-02)
- **Executive summary:** The deterministic walking skeleton — one thread (Setup → Upload → Validate → Process → **Verify** → Analyze → Finding → Summary → Export) on synthetic data, proving the architecture end-to-end before breadth; AI slice excluded. Anchored on F-02-02, co-delivering minimal slices of E-14/E-01/E-02/E-06/E-07/E-08 and the F-01-05 extraction seam.
- **Scope:** one review cycle · one upload (GED + Budget Tracker) · one validation · extraction+lineage+readiness · verification gate (`VerifiedDataset`) · one rule (R-BUD-02) · one finding · one Budget-Health summary section · one labeled export · audit + transactional persistence + cross-platform determinism from story one.
- **Exclusions:** Ask Fin / Explain This / production AI (later slice); all other rules/capabilities; other document types; wrong-file replacement, history, Review Health, What's New; production polish.
- **Acceptance-criteria summary:** 16 binding criteria (AC-1…16) — setup/upload/validation; verification-gate-by-construction; one finding with color-independent severity + one-hop lineage; byte-identical determinism on both OS; audit reconstruction; crash-safety; accessibility; structural boundaries; traceability PASS; and the F-01-05 extensibility seam.
- **Key implementation risks:** verification gate built as a flag (mitigated by ADR-006 construction guarantee); cross-platform determinism found late (mitigated by both-OS CI + golden on the one rule); scope creep (binding exclusions); Tauri packaging (spike + Electron fallback).
- **Open conditions:** (1) shell spike outcome; (2) synthetic materiality default confirmed; (3) synthetic fixture layouts confirmed + real-sample validation scheduled pre-pilot.
- **Evidence supporting approval:** all references resolve in migrated specs; test strategy + verification-evidence requirements defined; F-01-05 seam specified; consistent with the Constitution and all seven ADRs.
- **Panel must answer:** (1) Approve the skeleton scope and its exclusions? (2) Confirm R-BUD-02 (with a synthetic materiality default) as the single skeleton rule? (3) Are the 16 acceptance criteria sufficient proof the architecture holds? (4) Close the three open conditions or assign owners?

## 4. Shell Spike Decision Package (Tauri vs Electron) — no winner chosen

**Decision matrix** (criteria from approved requirements only):

| # | Criterion (approved source) | Tauri | Electron |
|---|---|---|---|
| 1 | Memory/footprint on 8–16 GB (DEC-016) | Small (system webview) | Large (bundled Chromium) |
| 2 | Restricted-env install, no admin, proxy-friendly (NFR-030) | Small signed binary; newer to enterprise allow-lists | Ubiquitous, widely enterprise-approved |
| 3 | Python-core bundling + loopback IPC (ADR-001, NFR-011) | Sidecar (Rust host + bundled Python) — less-trodden | Child process + localhost — well-trodden |
| 4 | Code-signing, Windows + macOS (NFR-030) | Supported; smaller artifact | Mature signing tooling |
| 5 | Cross-platform parity (NFR-028) | Yes | Yes |
| 6 | Offline / no external egress (NFR-007/011) | Meets | Meets |
| 7 | Accessible web UI (NFR-024–027) | Hosts it | Hosts it |
| 8 | Web-migration reuse (NFR-070) | Yes | Yes |
| 9 | Build/distribution complexity for a no-team build (12 §14) | Adds Rust + sidecar packaging | Node-based, familiar |

- **Required evidence:** install logs on both OS; launch screenshot/log; loopback-only proof (127.0.0.1 only); memory measurement on 8 GB; code-signed installer result; enterprise/security-review posture note.
- **Success criteria (spike passes for the chosen option when ALL hold):** on **both** Windows and macOS, in the **restricted target environment under standard user rights**, a **code-signed** installer installs and launches the shell with a **bundled Python core**; the shell↔core channel is **loopback-only**; memory footprint is acceptable on **8 GB**; a minimal "Step 1 of 9" screen renders and is **keyboard-operable**.
- **Failure criteria (spike fails for an option if ANY):** cannot install under standard user rights; requires a non-loopback listener; cannot be code-signed for an OS; unacceptable 8 GB footprint; Python bundling unreliable in the restricted env.
- **Recommended review procedure:** run the spike for **Tauri first** (the recommended option); if it meets all success criteria → adopt Tauri; if any failure criterion triggers → run the spike for **Electron** and adopt it (ADR-002's boundary keeps the core unchanged either way); record the outcome + evidence in the review record.

## 5. Design-Panel Agenda
- **Panel:** software-architect, data-architect, integration-architect, security-engineer, qa-engineer (+ ai-governance-reviewer, accessibility-engineer). Reviewer agents may assist; humans decide.
- **Prerequisite confirmed at open:** baseline v1.0 cut (Gate 2). If not, defer accept/approve decisions (review may still proceed).
- **Review order & expected outputs:**
  1. **Shell spike** → decision (Tauri or Electron) + evidence recorded → unblocks ADR-001.
  2. **ADR-001** → Accept/Revise (with the spike outcome).
  3. **ADR-002 → ADR-007** in order → Accept/Revise each (record findings + dissent).
  4. **PLAN-F-02-02** → Approve/Revise; close the three open conditions or assign owners.
- **Acceptance decisions required:** 7 ADR acceptances + 1 plan approval + 1 shell decision.
- **Evidence required:** the spike evidence bundle (§4); this review package; the migrated specs; each ADR's "supporting evidence."
- **Closure criteria:** all seven ADRs `Status: Accepted` (deciders + date); PLAN `Status: Approved` with conditions closed; shell decision recorded; the completed record saved as `specs/reviews/REVIEW-<date>-adrs-and-skeleton.md`.

## 6. Human Decision Checklist
- [ ] Baseline v1.0 cut (Gate 2 prerequisite).
- [ ] Shell spike run; Tauri or Electron decided; evidence recorded.
- [ ] ADR-001 Accepted (with shell decision).
- [ ] ADR-002 Accepted.
- [ ] ADR-003 Accepted (operational NFR-029 reading + rounding default confirmed).
- [ ] ADR-004 Accepted (ADC-08 noted as pre-pilot follow-up).
- [ ] ADR-005 Accepted (tamper-evidence R2 confirmed).
- [ ] ADR-006 Accepted.
- [ ] ADR-007 Accepted (severity values as OQ-8 configuration).
- [ ] PLAN-F-02-02 Approved; three open conditions closed/owned.
- [ ] Synthetic materiality default + fixture layouts confirmed.

## 7. Gate 3 Exit Checklist
- [ ] All seven ADRs `Status: Accepted` (deciders + date recorded in each ADR).
- [ ] PLAN-F-02-02 `Status: Approved`; review-record link added; open conditions closed.
- [ ] Shell decision + spike evidence recorded.
- [ ] Design-panel review record saved (`specs/reviews/REVIEW-<date>-adrs-and-skeleton.md`); dissent preserved.
- [ ] No open BLOCKER/CRITICAL findings.
- [ ] Ready to proceed to Gate 4 (environment + CI + trace gate + golden dataset).
