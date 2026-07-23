# FinSight — Architecture

**Document:** 06-architecture.md
**Status:** Draft for design-review board (spec-driven `design` panel) and team approval
**Date:** 2026-07-15
**Scope:** The **logical** architecture of FinSight — principles, structure, components, data flows, trust boundaries, and the reasoning that ties them to approved requirements. This document decides *shape*, not *technology*: it names no framework, database, library, or deployment product. Technology binding is deferred to Architecture Decision Records (§26) raised via `/sdd:adr` in the architecture-detailing phase.
**Governing methodology:** Spec-driven development (DEC-010, NFR-073). This document is a derived artifact; its source of truth is the approved artifact set below, and it introduces no scope beyond them.
**Sources of truth:** 00-project-understanding.md · 01-functional-requirements.md · 02-non-functional-requirements.md · 03-epics.md (LOCKED, DEC-021) · 04-features.md (LOCKED, DEC-023) · 09-decision-log.md
**Companion / downstream documents:** 05-rules-catalog (rule parameters) · 07-ux-design · 08-ai-and-agents · 10-dev-methodology
**Provenance:** AI-drafted from the approved artifacts, for human review and design-board sign-off before any status change (sdd:ai-provenance). Elements not directly derivable from a source artifact are tagged `PROPOSED` with justification, exactly as in the requirements documents; nothing here is `Baselined` until the design board and team approve it.

---

## 1. Purpose

This document defines the logical architecture that will satisfy FinSight's approved functional and non-functional requirements without weakening any Must, and without conflicting with any locked epic, locked feature, or logged decision. It exists to:

1. **Establish the load-bearing structure** — the components, their responsibilities, their boundaries, and the direction of dependency between them — that makes the two defining principles of FinSight (deterministic financial truth; AI explains, never decides) *structural facts* rather than conventions maintained by discipline (NFR-047).
2. **Make the architecture-significant requirements traceable** to the structural choices that satisfy them (§4, §27), so impact analysis on any requirement change is navigable in both directions (NFR-033).
3. **Give the implementation phase a stable spine** — the Review Cycle, the fixed pipeline, the trust boundaries — inside which features (04-features.md) are built as slices, starting with the walking skeleton (DEC-022, §21).
4. **Record the open architectural questions and decision candidates** (§25, §26) so that technology selection happens deliberately, as reviewed ADRs, not as incidental implementation choices.

This document does **not** design implementation details, choose technologies or frameworks, define rule parameters (those belong to 05-rules-catalog), or define screens (those belong to 07-ux-design).

## 2. Scope

**In scope:** logical components and their responsibilities; the Review-Cycle organizing model; the fixed data-flow pipeline; readiness, verification, deterministic-rules, findings, audit, AI, and historical-analysis architectures; security and trust boundaries; configurability and extension strategy; the web-migration posture; the walking-skeleton composition; architecture risks, mitigations, assumptions, open questions, and decision candidates; and full traceability back to requirements, epics, and features.

**Out of scope (deferred, by directive and by framework discipline):**

- **Technology and framework selection.** DEC-003 (desktop shell over an application core; AI-layer direction) and DEC-004 (embedded file-based persistence behind a Data Access Layer) are *directional* decisions already in the decision log; DEC-003 itself states the final stack is "validated during architecture design." This document treats them as constraints on shape (an embedded, substitutable persistence boundary; a web-tech-capable shell separable from the core) and defers their concrete binding to ADRs (§26).
- **Rule parameters, thresholds, tolerances, match semantics, cutoffs** — Rules Catalog (05), per DEC-019.
- **Screen layouts, interaction flows, visual language** — UX design (07); this document states only the boundaries UX must respect (verification gate, AI distinction, explainability-in-one-click).
- **Agent/prompt design and the AI orchestration graph** — AI & agents (08); this document states only the constraints the AI layer must satisfy (§15).
- **Phase 2–4 capability internals** (resource/contract, invoice, forecasting) beyond the extension seams that must exist now (§19) so those capabilities are extensions, not redesigns (NFR-044/045).

**ID conventions used in this document** (namespaces distinct from the framework's FR/NFR/E/F/T/ADR/CR grammar):

| Prefix | Meaning |
|---|---|
| `AP-##` | Architecture Principle (§3) |
| `ASR-##` | Architecture-Significant Requirement (§4) |
| `C-##` | Logical component (§7–8) |
| `DF-##` | Data-flow stage (§9) |
| `TB-##` | Trust boundary (§17) |
| `XP-##` | Extension point (§19) |
| `AR-##` | Architecture risk (§22) |
| `AA-##` | Architecture assumption (§24) |
| `AOQ-##` | Architecture open question (§25) |
| `ADC-##` | Architecture Decision Candidate — becomes a real `ADR-###` via `/sdd:adr` (§26) |

---

## 3. Architecture Principles

These principles are binding constraints on every component and every downstream plan. Each traces to a decision or requirement, and each names how it is *enforced* (a principle nothing enforces is only a suggestion — spec-driven design rule).

| ID | Principle | Statement | Traces to | Enforced by |
|---|---|---|---|---|
| **AP-01** | Deterministic core is the system of record | Every financial value, finding, variance, severity, status, and reconciliation outcome is produced only by the deterministic Rules Engine. Given the same verified inputs and configuration version, results are identical. | DEC-005, NFR-021, FR-077 | Golden-dataset + provider-swap regression (NFR-036/037/048); replay (F-02-06) |
| **AP-02** | AI explains, never decides | The AI layer may explain, summarize, narrate, recommend, and answer questions grounded in deterministic outputs. It may never compute a financial value, select/skip/alter a rule, or generate a finding. | DEC-005, FR-094, NFR-047 | Structural: AI has no write path to findings/rules; grounding + citation tests (NFR-050); AI-off completeness regression (FR-095) |
| **AP-03** | Nothing analyzed before it is verified | The Rules Engine consumes only data a human has explicitly approved. Verification is a hard gate, not a step that can be skipped or defaulted. | FR-026, DEC-005 | State machine cannot enter Analysis without a per-document approval record (§10–11) |
| **AP-04** | The Review Cycle is the organizing aggregate | The month/year Review Cycle is the spine of the system; capabilities are lenses on a cycle, not separate applications. Users complete "July 2026's review," not "the GED module." | FR-006, DEC-022 ("Monthly Review in a Box") | Cycle aggregate owns pipeline state; all artifacts key to a cycle (§6) |
| **AP-05** | Additive over immutable source | Ingested source content is never modified; verified data, corrections, and findings are additive layers with lineage to the original cell. | NFR-056, FR-003, FR-015 | Source immutability boundary (TB-01); raw-value preservation in the extraction contract |
| **AP-06** | Auditable and traceable by construction | Every material action writes an attributable audit record; every displayed number traces to rule → inputs → source rows. Audit is infrastructure, logging is Definition of Done. | E-08, NFR-019, NFR-067, FR-071 | Audit taps on every pipeline stage (§14); DoD clause 1 per story |
| **AP-07** | Configuration over code, versioned | Thresholds, tolerances, calendars, reference data, provider registry, and storage location are configuration — never hard-coded — and every change is versioned and recorded against the runs that used it. | NFR-039, FR-103, FR-107, NFR-022 | Config Registry (C-08/C-18); each run records config version (F-02-02) |
| **AP-08** | Composable, replaceable modules | Modules expose narrow interfaces and hide their internal representations; any module is replaceable behind its interface without editing callers. | NFR-031, NFR-032 | Composition root wiring; dependency-rule architecture test (ADC-02) |
| **AP-09** | Core independent of delivery and storage | Business logic, rules, findings, and audit contain no desktop-only or storage-specific assumptions; the core is drivable headless. | NFR-070, NFR-072 | Core imports no UI/storage/provider types; headless test harness (§20) |
| **AP-10** | No unconsented egress; privacy by design | Data leaves the application only to the user-selected AI provider under active consent, carrying only the minimum fields required. Nowhere else, ever. | NFR-011, NFR-015, FR-096 | Single egress chokepoint (TB-03); no other outbound path exists |
| **AP-11** | Honest under failure and cold start | Deterministic functionality works fully offline; AI degrades to deterministic-only with clear status; rules below their minimum history report "insufficient history" rather than firing. Partial results are never presented as complete. | NFR-007, NFR-062, NFR-063, FR-111 | Async isolation of AI (NFR-004); min-history declaration (F-02-05); quarantine reporting (FR-024/025) |
| **AP-12** | One findings experience; change ≠ exception | All analytical capabilities render through one Findings Hub with no per-capability forks. Change detection (what's new) and exception detection (what's wrong) are distinct concepts that never silently merge. | F-06-01, FR-041, FR-078 | Shared findings components (binding criterion, F-06-01); separate change vs. exception surfaces (§16) |

---

## 4. Architecture-Significant Requirements (ASRs)

The requirements below are *architecturally significant*: they materially shape structure, are expensive to retrofit, or are release/audit criteria. They are the constraints the design in §5–§21 is answerable to. (Full traceability for all requirements is in §27.)

| ASR | Requirement | Fit criterion (as approved) | Structural consequence |
|---|---|---|---|
| **ASR-01** | Reproducibility guarantee | Same verified inputs + config version ⇒ identical findings/statuses/severities/variances regardless of AI provider/model/prompt (NFR-021, DEC-005) | Deterministic core isolated from AI and from wall-clock/locale/RNG; replay from recorded inputs (F-02-06) |
| **ASR-02** | Determinism as release criterion | Provider-swap regression (NFR-037) and golden-dataset tests (NFR-036) must pass to ship (NFR-048) | Standing test seams around the Rules Engine; AI is a separable, disableable module |
| **ASR-03** | Mandatory verification gate | No analysis on unverified data (FR-026) | Pipeline state machine blocks Analysis without per-document approval (§10–11) |
| **ASR-04** | Deterministic/AI boundary enforced by design | AI never selects rules, alters outcomes, or computes values; enforced, not conventional (NFR-047) | AI layer is downstream of, and read-only to, findings; no AI edge into rules/config (§15) |
| **ASR-05** | No data loss / resumable / transactional | Crash never loses verified data, findings, audit; cycles resume; multi-step persistence is all-or-nothing (NFR-005/006/057) | Transactional persistence through the DAL; cycle state persisted at each stage transition |
| **ASR-06** | Cross-platform identical results | Byte-identical deterministic results on Windows and macOS (NFR-029) | Exact decimal arithmetic (NFR-059); platform-independent parsing/sorting in the core |
| **ASR-07** | Protection at rest and of secrets | Financial data/findings/reports/audit protected at rest; credentials in platform-secure storage (NFR-009/010) | At-rest protection boundary owned by the DAL; secrets isolated from config and logs (TB-04) |
| **ASR-08** | No unconsented egress | Only consented AI transmission leaves the app; no telemetry/analytics/update carries user data (NFR-011) | Single egress chokepoint gated by consent (TB-03) |
| **ASR-09** | Storage substitutability | Persistence replaceable (embedded now, server DB later) without business-logic change (NFR-072, DEC-004) | Repository interfaces; only the DAL touches storage |
| **ASR-10** | Web-migration core independence | Web transition must not reimplement deterministic logic (NFR-070) | Core independent of shell; identity/attribution generalizable (NFR-071) |
| **ASR-11** | Extensibility of rules, document types, providers | New rules/document types/providers are extensions, not redesigns (NFR-044/045/046) | Extension points XP-01..XP-05 (§19) |
| **ASR-12** | Performance and asynchrony | Full cycle ≤ 2 min on target hardware (proposed); long operations async; UI never freezes; AI latency independent (NFR-001/002/003/004) | Off-UI-thread processing; deterministic results render before AI narrative |
| **ASR-13** | Complete, attributable, tamper-evident audit | Every material action logged attributably; tamper-evidence (NFR-019/020); config/rule version provenance (NFR-022) | Audit service with append-only, versioned event schema (§14) |
| **ASR-14** | Accessibility of meaning | No meaning by color alone; severity/RAG conveyed with icon/text (NFR-025) | Severity/RAG are data carrying non-color encodings from the core, not UI-only styling |

---

## 5. System Context

FinSight is a **single-user, read-only, desktop-delivered analytical assistant** (DEC-003, DEC-008) that operates entirely on files the user provides and produces on-screen and exported governance output. It writes to no financial system and communicates with no vendor (00 §7 *Key Constraints*, item 1 "Read-only MVP"; FR-083).

**Actors and external entities:**

| Entity | Relationship to FinSight | Notes |
|---|---|---|
| **Operator** | Performs intake, verification, reconciliation; drives the cycle to readiness for the Leader | Persona A-09; may be the same person as the Leader |
| **Leader** | Consumes findings, summaries, Q&A; makes decisions *outside* FinSight | The budget owner; decisions are human (Success Criterion 7) |
| **Administrator** | Manages the recommended AI-provider registry, reference data, and thresholds as governed configuration | Advisory provider list (DEC-006/007); may be the same person in the MVP |
| **Source documents** | Read-only inbound: GED reports, Budget Trackers (Phase 1); invoices/POs/SOWs/rate cards/contracts (Phase 3); resource/contract sheets (Phase 2) | Excel now; PDF Phase 3 (FR-001/002). Untrusted input (NFR-012) |
| **AI provider(s)** | Optional, consent-gated outbound: explanation/narrative/recommendation/Q&A over deterministic outputs | Enterprise-hosted primary (DEC-016, A-06); consent is the final gate (FR-096) |
| **Operating system** | Host platform (Windows and macOS), local storage location, secure credential store, OS user identity | Parity required (NFR-028); OS user recorded in audit (DEC-008) |
| **Export recipients** | Stakeholders who do not use FinSight; receive exported summaries/data | Exports are self-describing and labeled (FR-120) |
| **Backup target** | User-chosen file/location for backup and restore | Single-machine deployment ⇒ backup is the DR story (NFR-060) |

**Context invariants (the box FinSight lives in):**

- The only outbound data path is to a consented AI provider (AP-10, TB-03). There is no telemetry, no auto-update carrying user data, no vendor communication (NFR-011, FR-083).
- Source files are inputs only; FinSight never modifies, moves, or deletes them (FR-003).
- All build/test data is sanitized, scrambled, or synthetic — never real customer data (NFR-018, DEC-010).

```
        Source files (Excel/PDF, read-only)
                    │
                    ▼
   ┌──────────────────────────────────────────────┐        (consent-gated, optional)
   │                 FinSight                       │  ─────────────────►  AI Provider
   │   desktop app, single user, offline-capable    │  ◄─────────────────  (narrative only)
   │   deterministic core + optional AI layer       │
   └──────────────────────────────────────────────┘
        │            │                    │
        ▼            ▼                    ▼
   Local storage  On-screen         Exported summary /
   (protected)    review & findings  data / audit (labeled)
```

---

## 6. Review-Cycle Architecture

The **Review Cycle** is FinSight's central organizing aggregate (AP-04) and the reason the system "feels like a monthly review platform, not a collection of modules." A Review Cycle is uniquely identified by **(Month, Year)** for a given scope (single department in the MVP, A-11) and owns the state and artifacts of one monthly review.

**6.1 What a Review Cycle owns**

- Its **identity and metadata** — month, year, name, scope, creating/operating user.
- Its **pipeline state** — where the review is in the fixed flow (§6.2), so it can be paused and resumed across days and restarts without rework (NFR-006, F-01-01).
- Its **artifacts, all keyed to the cycle** — ingested files and provenance; extracted/normalized data with lineage; quality and readiness assessment; verification decisions and corrections; the analysis run(s) and their config/rule versions; findings; reconciliation state; the leadership summary; exports; and the audit trail for the cycle.
- Its **relationship to prior cycles** — enabling historical comparison (§16) as a first-class capability, not a bolt-on.

**6.2 Cycle lifecycle (Harel-style state model, per software-architect canon)**

The cycle is modeled as **two orthogonal Harel regions** (not one flat track), because a review runs on a *set* of documents that are individually intaken, verified, and analyzed while the cycle as a whole is still in progress (multiple documents per cycle — DEC-022; "proceed on the available subset" — §10). A single linear "Analysis" state could not represent "GED verified and analyzed while the Budget Tracker is still being verified," so the flat FSM is the wrong shape.

- **Per-artifact region** — each ingested document/dataset carries its own status: `Ingested → Extracted → (Quarantined|Ready) → Verified → Analyzed`. Verification is per document (FR-026, FR-029).
- **Cycle region** — the cycle-level view (`Open → In progress → Summarized → Exported → Closed`) is a *projection* over the per-artifact statuses, plus the continuously-recomputed capability-readiness map (§10), not an independent linear track.

```
per-artifact:  Ingested ─▶ Extracted ─▶ [Quarantined | Ready] ─▶ Verified ─(only C-06 can produce)─▶ Analyzed
cycle (projection):  Open ─▶ In progress ─▶ Summarized ─▶ Exported ─▶ Closed
   readiness map recomputed on every status change (§10)  ·  pausable/resumable at any point (NFR-006)
   every transition emitted through AuditEventPort (AP-06)  ·  re-entry re-runs forward, idempotent (NFR-008)
```

- **"Analyzed but not verified" is unrepresentable *by construction*, not by a runtime guard.** The Rules Engine (C-07) consumes only a `VerifiedDataset` value, and the *only* constructor of `VerifiedDataset` is C-06 on recording an approval decision (ASR-03, AP-03). There is no code path that hands unverified data to a rule — the type does not exist until a human approves it. (ADC-10 states this as a construction guarantee, with tests as defense-in-depth.)
- **Re-entry is deterministic and idempotent:** replacing a document or re-running analysis returns *that artifact* to the earliest affected per-artifact state and re-runs forward, producing identical results and no duplicate findings/reports (NFR-008, F-01-04 R2, F-02-06).
- **Closed cycles are immutable inputs to history** (§16) and remain fully reproducible (F-07-03).

**6.3 Why review-centric, not module-centric**

Every capability (Budget, GED, Reconciliation, later Invoice/Resource) is a **lens on the current cycle's verified data and findings**, sharing one intake, one verification gate, one Findings Hub, one summary, one audit trail. This is the architectural realization of "Monthly Review in a Box" (DEC-022) and the approved review-centric guidance. Capabilities do not own their own intake, findings, or reporting — they contribute rule packs (§2.1 of 04-features.md) and views.

---

## 7. Major Architectural Components

The components below are **logical** (responsibilities and boundaries), organized by Clean-Architecture layer. **Dependencies point inward** (AP-08/09): the delivery layer depends on the application layer, which depends on the domain core; the domain core depends on nothing outward and knows nothing of UI, storage, or AI providers (software-architect: the dependency rule). Two refinements make the most safety-critical boundaries *structural* rather than test-enforced (§7.1–7.3).

```
┌─────────────────────────── DELIVERY (replaceable: desktop now, web later) ────────────────────────────┐
│  C-01 Application Shell & Experience     C-15 AI Assistance & Grounding (optional)                      │
├─────────────────────────── APPLICATION (orchestration & use-cases) ───────────────────────────────────┤
│  C-02 Review-Cycle Orchestrator   C-03 Document Intake   C-04 Extraction & Normalization                │
│  C-05 Data Quality & Readiness    C-06 Verification Workspace   C-10 Reconciliation Workspace           │
│  C-09b Findings Hub Experience   C-12 Executive Reporting & Export   C-13 Historical Analysis           │
│  C-16 Consent & Provider Governance   C-18b Configuration Transparency Surface                          │
├─────────────────────────── DOMAIN CORE (the system of record — pure, deterministic, headless) ─────────┤
│  C-07 Deterministic Rules Engine   C-09a Findings Domain Model   C-11 Analysis Capabilities / Rule Packs│
│  C-08 Rules & Configuration Registry (model)   Review-Cycle aggregate & state model (§6)                │
│  ── ports (core-owned interfaces) ──▶  FindingsQueryPort · FindingsCommandPort · AuditEventPort · Repositories│
├─────────────────────────── INFRASTRUCTURE (replaceable behind interfaces) ─────────────────────────────┤
│  C-17 Persistence & Data Access Layer (+ secure storage)   C-14 Audit & Provenance Service              │
│  C-18 Configuration & Reference Data store   AI Provider Adapters (behind C-15/C-16, via XP-03)         │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Layer placement rationale: the **domain core** (rules, findings *model*, capabilities, cycle model) is where reproducibility and the deterministic/AI boundary must be inviolable (ASR-01/04), so it is the innermost layer with no outward dependencies (NFR-070). **Audit and persistence** are infrastructure that the core reaches only through **core-owned ports** (interfaces defined in the core, implemented outward) so the core can be exercised headless in tests and lifted to the web unchanged (ASR-09/10). **AI assistance** sits in the delivery ring, reaching the core **only through a read-only query port**, precisely because it must be removable without touching the core (FR-095) and must be *structurally* incapable of authoring truth (§7.1).

### 7.1 The AI write boundary is structural (command/query segregation) — closes the NFR-047 "by design, not convention" obligation

The dependency rule alone does not stop the delivery ring from *calling inward*; Clean Architecture permits delivery→domain calls by design. So forbidding AI from authoring findings requires more than an import-direction test — it requires that the authoring capability **not be reachable** from C-15. FinSight enforces this with command/query segregation on the Findings Domain Model (C-09a):

- **`FindingsQueryPort`** — read-only access to findings and verified data. This is the **only** core interface exposed to C-15 (and to read-only surfaces generally).
- **`FindingsCommandPort`** — create/mutate findings and set severity. Reachable **only** by C-07 (Rules Engine) and C-11 (rule packs) at the composition root; it is never wired to C-15.

Consequently "AI authors a finding" or "AI sets a severity" has **no wired code path** — C-15 is never handed `FindingsCommandPort`. Because the core is Python (ADR-001, with no compile-time access control), this is enforced not by the compiler but **by construction and a mandatory CI architecture-fitness (import) test**, reinforced by module-private construction of findings/severity (frozen types, no public constructor) and a runtime guard — an enforced boundary, not a rule someone must remember (AP-02, NFR-047, DEC-005). The behavioral nets (provider-swap regression NFR-037, AI-off completeness FR-095, grounding/citation NFR-050) remain as defense-in-depth. The architecture-fitness test — C-15 references only `FindingsQueryPort` — is the enforcing gate (ADC-02/ADC-11).

### 7.2 Audit and persistence are reached through core-owned ports (dependency inversion)

The core (C-07, the cycle model) **emits audit events through a core-owned `AuditEventPort`**, implemented by C-14 in infrastructure — exactly as storage is reached through repository interfaces implemented by C-17. The core therefore imports no infrastructure type and stays headless-testable: a test harness supplies a no-op or in-memory `AuditEventPort` and `Repositories`. "Every component writes audit events" (§14) means "through the port," never a direct call outward (AP-06/AP-09, ADC-02/ADC-09).

### 7.3 Findings: domain model (core) vs. experience (delivery)

The single findings *record contract, severity computation, lifecycle state machine, and traceability links* live in the core as **C-09a Findings Domain Model** (maps to F-02-04 computation + FR-072 lifecycle). The *browse/search/filter, dual-lens views, and shared rendering components* live in the application/delivery ring as **C-09b Findings Hub Experience** (maps to F-06-01/02/04). The "one findings experience, no per-capability forks" binding criterion (AP-12) attaches to C-09b; the deterministic contract attaches to C-09a. This keeps the core headless (AP-09/NFR-070) and gives each module one hidden decision (Parnas), while C-09b consumes the core solely through `FindingsQueryPort` (§7.1).

---

## 8. Component Responsibilities

Each component states its single responsibility (Parnas: one hidden design decision), what it must never do, and its primary traceability.

**C-01 — Application Shell & Experience** *(Delivery; E-14)*
Hosts navigation between review-cycle surfaces and a settings surface; runs on Windows and macOS in restricted environments with parity; keeps the UI responsive while work runs off-thread; renders severity/RAG with non-color encodings; follows OS display modes. *Never:* embeds business logic or computes financial values (those live in the core). *Traces:* F-14-01/03/05, NFR-002/003/028/030/065, NFR-025. *(F-14-02 "Never Lose Work" is a documented shared responsibility: the UI-level crash-safety/resume experience here, the transactional/at-rest persistence in C-17.)*

**C-02 — Review-Cycle Orchestrator** *(Application)*
Owns the cycle state machine (§6.2); sequences the fixed pipeline; enforces the verification gate; drives re-entry/idempotent re-runs; reports cycle status and outstanding items. Orchestration may be workflow/agent-assisted (08), **but** it may never decide which rules run, skip rules, or alter outcomes (DEC-005, AP-02). *Traces:* F-01-01, FR-006/081, NFR-006, DEC-005.

**C-03 — Document Intake** *(Application)*
Accepts files; treats them as untrusted input; rejects unreadable/corrupt/password-protected/unsupported files with plain-language reasons; records full provenance (name, fingerprint, user, timestamp, period, classification); detects duplicate uploads; supports versioned replacement (R2). Proposes document type and period; the user's confirmation is authoritative. *Never:* modifies the source file (AP-05). *Traces:* F-01-02/03/04, FR-001–010, NFR-012.

**C-04 — Extraction & Normalization** *(Application; template-driven)*
Turns confirmed documents into structured data via a per-document-type extraction template; handles real-world structural noise (headers, subtotals, blanks, merged cells); normalizes dates/periods/amounts/identifiers including negatives/credits/placeholders using **exact decimal arithmetic** (NFR-059); preserves the raw value and cell-level lineage for every normalized value; assigns extraction confidence; tags accounting-event types (payroll/reclass/accrual-reversal) for downstream rules. *Traces:* F-01-05/06/07, FR-011–016, FR-041 (tagging half), NFR-056/059.

**C-05 — Data Quality & Readiness Assessment** *(Application)*
Runs schema and row-level quality checks; quarantines failing rows without blocking the month; cross-checks detail against the report's own subtotals; produces the per-cycle data-quality summary; and computes the **capability-readiness** view (§10). *Traces:* F-01-08, FR-021–025; readiness model grounded in FR-004/007/021–025/081/111.

**C-06 — Verification Workspace** *(Application; the trust gate TB-02)*
Presents extracted data for human review with one-click trace to source cell; highlights low-confidence and quarantined items; captures corrections (original preserved, user + timestamp recorded); records per-document approve / approve-with-corrections / reject decisions; optimizes for speed via bulk approval of high-confidence data. **No analysis proceeds without its approval records** (ASR-03). *Traces:* F-01-09, FR-026–029, NFR-069.

**C-07 — Deterministic Rules Engine** *(Domain core; E-02 — the system of record)*
Executes rules in a fixed, predictable sequence over verified data; every run records rule-set version, configuration version, and input fingerprints; produces findings with evidence; guarantees identical output for identical inputs+config; supports replay of any historical cycle. **Agents/AI can never select, skip, or alter rules** (DEC-005). *Traces:* F-02-01/02/06, FR-086, NFR-021/036/037/047/048/059.

**C-08 — Rules & Configuration Registry (definition / read model)** *(Domain core)*
Owns the **definition and read model** of rules (declared inputs, parameters, outputs, minimum-history need, Rules-Catalog ID) and the governed reference data they read (thresholds, tolerances, calendars, account lists, vendor expectations, reconciliation-eligible scope, expected-entries reference). Rule sets cannot vary per run or be altered by agents. *Persistence, versioning, and validation of these same items are owned by C-18* (model/store split); enable/disable is a versioned, logged change recorded through C-18. *Traces:* F-02-01/03, FR-103/105/106, NFR-044.

**C-09a — Findings Domain Model** *(Domain core; E-06 deterministic contract, §7.3)*
The deterministic heart of findings: the first-class **record contract** (ID, rule reference, severity, period, affected entities, evidence values, source references); **severity computation** by rule-defined configurable criteria (F-02-04); the **lifecycle state machine** (New → Acknowledged → In review → Resolved/Dismissed, dismissal requires reason, FR-072); and the **traceability links** to rule/inputs/source. Exposes `FindingsCommandPort` (writable only by C-07/C-11) and `FindingsQueryPort` (read-only; §7.1). Headless and AI-free by construction. *Traces:* F-02-04, FR-069/070 (computation), FR-071/072, NFR-067.

**C-09b — Findings Hub Experience** *(Application/Delivery; E-06 — one findings experience, AP-12)*
The single findings *experience*: browse/search/filter with no AI dependency; critical-first surfacing on analysis completion; progressive disclosure; the dual lens (Operator work queue, Leader "items needing my decision" view). Consumes C-09a solely through `FindingsQueryPort`. *Binding:* Budget, GED, Reconciliation — and later Invoice — findings render through the same components; no per-capability forks. *Traces:* F-06-01/02/04, FR-069/070 (presentation), FR-074/082/102, NFR-066/067.

**C-10 — Reconciliation Workspace** *(Application; E-05 — Operator surface)*
Auto-matches GED lines against tracker entries into exact/probable/unmatched tiers; supports manual match/unmatch/override with reason and audit; tracks cleared status (`clrd`-equivalent); keeps unmatched items visible with carry-forward and aging across cycles. Applies the **workspace/finding boundary** (§2.3 of 04): in-progress items are workspace tasks, not findings; residual unresolved items become findings with full lifecycle at cycle close or on escalation. *Traces:* F-05-01/02, FR-044–050.

**C-11 — Analysis Capabilities / Rule Packs** *(Domain core)*
The capability rule packs that run on C-07: Budget (variance, MoM, over/under-spend, run-rate, trends), GED (missing/duplicate/delayed/anomaly/coding, activity summarization), Reconciliation matching, and later Invoice and Resource/Contract packs. Each pack is a catalog entry with golden-dataset acceptance; each emits findings through C-09a's `FindingsCommandPort`. *Traces:* F-03-*, F-04-*, F-05-01; (Phase 2/3) E-11/E-12 packs; FR-030–068 as scheduled.

**C-12 — Executive Reporting & Export** *(Application; E-07)*
Produces the monthly leadership summary (deterministic RAG status computed by a catalog rule — never AI; budget health, GED status, key risks, recommended actions, thin "what changed"); retains and re-displays every report exactly; owns the single, uniformly-labeled export **machinery** (timestamp, period, config version, AI-content labeling) that consuming surfaces invoke — reports and findings/data here, and the audit export (FR-119) invoked *by* C-14's audit explorer, mirroring the "owned once by F-07-04, consumed as buttons" ruling (04-features §14). AI-narrative slots exist, labeled, and empty until E-09; the summary reads complete without them (FR-095). *Traces:* F-07-01/03/04, FR-076–080/083/116–120.

**C-13 — Historical Analysis & Comparison** *(Application; §16)*
Retains verified data, findings, reconciliation results, reports, and configurations across months; computes month-over-month deltas and comparison views; supplies trailing baselines to history-dependent rule packs; links recurring findings; distinguishes *new* from *wrong*. *Traces:* FR-078/108/109, F-06-05, F-07-02, F-02-05 (baseline computation), NFR-042.

**C-14 — Audit & Provenance Service** *(Infrastructure; E-08)*
The append-only, versioned event store that **implements the core-owned `AuditEventPort`** (§7.2): components emit events *through the port* — intake, verification, corrections, rule runs, config changes, AI interactions, consents, reports, exports — attributed, timestamped, fingerprinted; multi-month retention; searchable/filterable with a cycle-timeline lens; tamper-evidence (R2). The audit explorer invokes C-12's export machinery for audit export (FR-119). Diagnostic/operational logs are separate and never contain sensitive financial values. *Traces:* F-08-01/02/03/04, FR-084–090/107/108/119, NFR-019/020/022/023/053/058.

**C-15 — AI Assistance & Grounding** *(Delivery; E-09 — optional at runtime, §15)*
Generates explanations, narratives, recommendations, and NL answers **strictly from deterministic findings and verified data**, reaching the core **only through `FindingsQueryPort`** (§7.1) — it has no reference to `FindingsCommandPort` and so cannot author a finding or set a severity. Every claim carries citations to finding IDs/data points; every AI artifact is visually distinct and attributed (provider/model/version); declines questions unsupported by available data; runs asynchronously so it never delays deterministic results. Provider I/O sits behind an infrastructure adapter (XP-03). Fully removable — with it disabled, every number/finding/report section remains. *Traces:* FR-091–101 (AI explanation/narrative/recommendation/Q&A), F-06-02 (the deterministic investigation surface it augments), NFR-004/046/049/050/052/063.

**C-16 — Consent & Provider Governance** *(Application; part of E-09 trust controls)*
Manages the advisory recommended-provider registry (admin-controlled, auditable, configurable); presents the informed-consent flow before any transmission (provider, exact data, masking state, implications); records every consent grant/scope/revocation; warns on non-recommended providers; owns masking/tokenization (R2) whose token map never leaves the app. *Traces:* FR-096–098/104, NFR-011/013/014/015/016, DEC-006/007.

**C-17 — Persistence & Data Access Layer** *(Infrastructure; DEC-004)*
The **only** component that touches storage. Provides transactional, all-or-nothing persistence; protection at rest for all stored data; crash-safe/resumable state; content fingerprinting; backup/restore; permanent data disposal with logged fact-of-deletion. Exposes repository interfaces so the store is substitutable (embedded now → server DB later) without business-logic change. Secrets/credentials use platform-secure storage, isolated from config and never logged. *Traces:* F-14-02/04/06/07, DEC-004, NFR-005/006/009/010/057/058/060/061/072, NFR-017.

**C-18 — Configuration & Reference Data Management** *(Infrastructure; transparency view via C-01)*
Owns **persistence, versioning, and validation** of all configuration and reference data whose *definition/read model* lives in C-08 — with before/after values and user/timestamp; rejects invalid configuration with clear messages and preserves a recoverable known-good state; binds each analysis run to the config version it used. The active-configuration transparency view (thresholds, provider, masking) is a thin C-01 surface over C-18 (labeled **C-18b** in §7). *Traces:* F-14-01 (transparency), F-08-03, FR-103/105/106/107, NFR-039/040/041/022.

---

## 9. Data Flow Architecture

The pipeline is **fixed and one-directional through the deterministic core** (DEC-005). AI branches *off* the findings, never *into* the flow. Audit taps every stage.

```
 DF-01 Intake        DF-02 Extract &      DF-03 Quality &     DF-04 VERIFY        DF-05 Rules
 (provenance,        Normalize            Readiness           (human gate,        Engine
  classification) ─▶ (lineage, decimal ─▶ (quarantine,     ─▶  corrections,   ─▶  (fixed sequence,
                      tagging)             readiness view)      approvals)          versioned run)
                                                                                        │
                                                                                        ▼
                        (optional, consent-gated, async)                          DF-06 Findings
  AI Provider ◀── DF-09 AI Grounding ◀──────────────────────────────────────────  (first-class,
             narrative/explain/           reads findings + verified data only            severity, evidence)
             recommend/Q&A (cited)                                                       │
                                                                                        ▼
                                                            DF-08 Export ◀── DF-07 Summary & Reporting
                                                            (labeled)         (deterministic RAG,
                                                                               MoM, risks, actions)

  ══ DF-10 Audit & Provenance tap ═══ every stage writes attributed, fingerprinted events ═══
  ══ DF-11 Persistence (DAL) ═══════ every stage's state persists transactionally ═══════════
```

**Flow invariants:**

1. **The core is a straight line** DF-02 → DF-05 → DF-06 → DF-07; nothing downstream feeds back into rule selection or computation (ASR-04).
2. **DF-04 is a gate**, not a pass-through: DF-05 cannot begin for a document without its approval record (ASR-03).
3. **DF-09 (AI) reads only DF-06 findings and verified data**, has no write path into DF-05/DF-06, and runs asynchronously (ASR-04, ASR-12, NFR-004). Its output is labeled and cited (NFR-049/050).
4. **DF-10 audit and DF-11 persistence are cross-cutting** and present from the first stage (walking skeleton, §21); audit is Definition of Done, not a later stage.
5. **Re-entry** (corrected file, config change, re-run) re-executes forward from the earliest affected stage and is idempotent (NFR-008).

---

## 10. Readiness Validation Architecture

Realizes the approved "Capability Readiness Validation" and "Centralized Document Intake" guidance. `PROPOSED` as an architectural model; grounded in FR-004, FR-007, FR-021–025, FR-081, FR-111 (introduces no new requirement — it is the structural expression of these).

**Principle:** the system must never assume every document exists. Users upload only what they have; FinSight assesses **which capabilities are available, which are not, and why**, before analysis — and lets the review proceed on the available subset.

**10.1 Readiness model**

For the current cycle, C-05 computes a **capability-readiness map**: for each analysis capability, a status of **Available / Partially available / Unavailable**, each with a machine- and human-readable *reason*.

| Readiness input | Source | Example effect |
|---|---|---|
| Presence of required document types | C-03 classification (FR-004) | GED analysis needs a verified GED report; absent ⇒ GED capability Unavailable ("no GED report uploaded") |
| Data-quality outcome | C-05 checks (FR-021–025) | Excessive quarantine ⇒ capability Partially available with a stated caveat |
| Reference-data presence | C-08 registry (FR-105) | Missing expected-entries reference ⇒ missing-entry detection Unavailable (per OQ-5 posture) |
| Minimum-history satisfaction | rule min-history declaration (FR-111) | Below-minimum ⇒ history-based rules report "insufficient history," not silence |
| Verification state | C-06 (FR-026) | Unverified documents ⇒ dependent capabilities gated until verified |

**10.2 Behavior**

- Readiness is presented to the user **before analysis** and is part of cycle status (FR-081); missing prerequisites are named with a next step (NFR-055, NFR-064).
- Readiness **gates capabilities, not the whole review**: available capabilities run; unavailable ones are explained rather than silently absent (AP-11).
- Readiness assessment is **deterministic** (rule/reference-driven), so it is reproducible and auditable like everything else in the core.

---

## 11. Verification Architecture

Realizes the approved "Verified Data Principle" — the core trust boundary (TB-02). `Upload → Extract → Verify → Analyze` is enforced structurally (AP-03, ASR-03).

**11.1 The gate**

- The Rules Engine (C-07) consumes only a **`VerifiedDataset`** value, and the *only* constructor of that type is C-06 on recording a per-document approval decision (§6.2). "Run a rule on unapproved data" is therefore not a guarded path but an **absent** one — the input type does not exist until a human approves it (FR-026, ASR-03). Verification is per document/dataset, so available capabilities analyze their verified inputs while other documents in the same cycle are still being verified (§6.2 orthogonal regions, §10).
- Verification supports **Review, Correction, and Approval** (the approved three-part requirement): review with one-click source-cell traceability (FR-027); correction preserving the original value, corrected value, user, and timestamp in lineage (FR-028); and a per-document decision of approve / approve-with-corrections / reject (FR-029).

**11.2 Correction and lineage semantics**

- Corrections are **additive layers** over immutable source (AP-05, NFR-056): the raw value, the normalized value, and any human correction coexist and are all traceable to file/sheet/row/column (FR-015).
- Rejection triggers re-extraction or file replacement and returns the cycle to the appropriate earlier state (§6.2).
- Every verification action is audited (FR-085) and every corrected value remains visible in lineage thereafter (FR-028).

**11.3 Efficiency without weakening the gate**

Bulk approval of high-confidence data and attention directed to low-confidence/quarantined items keep the mandatory gate fast (NFR-069, F-01-09) — the gate is optimized, never bypassed.

---

## 12. Deterministic Rules Architecture

Realizes the approved "Deterministic Core Principle" and DEC-005. This is the architectural heart: **financial truth is generated exclusively by deterministic logic** (AP-01).

**12.1 Structure**

- **Engine vs. rules separation (E-02 vs. capability epics).** C-07 owns *how* rules execute — the fixed pipeline, versioning, parameterization, determinism guarantee, replay. C-11 rule packs own *that* specific rules exist and are correct. New rules are additions on the engine, never redesigns (NFR-044).
- **A rule declares** its inputs, parameters, outputs, Rules-Catalog ID, and minimum-history need (F-02-01). Parameters/thresholds/tolerances come from C-08 configuration (values live in 05-rules-catalog, per DEC-019), never hard-coded (AP-07).
- **Every run is a versioned, fingerprinted record:** rule-set version + configuration version + input fingerprint in, findings out, rule-execution audit event emitted (F-02-02, FR-086).

**12.2 Determinism as an enforced property (ASR-01/02)**

- The core reads **no wall-clock, no locale-dependent parsing/sorting, no randomness** on the computation path; time is injected, arithmetic is exact decimal (NFR-059), and ordering is explicit — so results are byte-identical across Windows and macOS (NFR-029) and across AI providers (NFR-021).
- **Replay (F-02-06):** any historical cycle re-runs against its recorded inputs and configuration with identical results — the mechanism behind report reproducibility (F-07-03) and auditor trust.
- **Standing regressions gate release:** golden-dataset determinism (NFR-036) and provider-swap (NFR-037) tests must pass to ship (NFR-048); AI on/off changes no deterministic output (FR-095).

**12.3 What the engine forbids by construction**

AI/agents have **no edge into the engine**: they cannot select, skip, reorder, or alter rules, and cannot compute or inject a financial value or a finding (DEC-005, NFR-047). This is an *absent code path*, made concrete by command/query segregation (§7.1): findings and severities are writable only through `FindingsCommandPort`, wired only to C-07/C-11 at the composition root and never to the AI layer, so "AI authors a finding" has no wired path — enforced by construction and a mandatory CI architecture-fitness test (Python has no compiler-enforced access control; ADR-001/002), not by discipline. The behavioral regressions (provider-swap NFR-037, AI-off completeness FR-095) are defense-in-depth confirming the boundary, not the boundary itself (ADC-02/ADC-04/ADC-11, §17 TB-03).

---

## 13. Findings Architecture

Realizes the approved "Findings Hub Principle": all analytical capabilities feed **one** findings experience (AP-12, E-06). Structurally this is two modules (§7.3): the **Findings Domain Model** C-09a in the core (record contract, severity computation, lifecycle) and the **Findings Hub Experience** C-09b in the application/delivery ring (views, search, rendering) reading the core through `FindingsQueryPort`.

- **One model, many producers.** Budget, GED, Reconciliation — and later Invoice, Resource — findings share one record contract in C-09a (F-02-04) and one set of rendering components in C-09b (binding criterion, F-06-01). No per-capability fork is permitted; a divergent per-capability findings surface is a defect, not a variation.
- **First-class records** (FR-069): each finding carries ID, rule reference, severity, period, affected entities, evidence values, and source references — enabling one-interaction traceability to rule → inputs → source rows (FR-071, NFR-067) and browse/search with no AI dependency (FR-102).
- **Severity is computed, never assigned by AI** (FR-070, split: computation in F-02-04, presentation in F-06-01); it carries non-color encoding so meaning survives without color (NFR-025, ASR-14).
- **Lifecycle** (FR-072): New → Acknowledged → In review → Resolved/Dismissed; dismissal requires a reason; all transitions audited. Recurrence linkage across months (F-06-05, R2) marks "third month in a row" distinctly from "new."
- **Workspace/finding boundary** (§2.3 of 04): during an active process (reconciliation now; invoice review later), in-progress items are workspace tasks and must not flood the findings inbox; residual unresolved items become findings at cycle close or on escalation. One underlying record, two presentations, one state machine — divergent statuses between surfaces are a trust defect.
- **Dual lens** (F-06-01): the same findings serve the Operator's work queue and the Leader's "items needing my decision" view — progressive disclosure by severity leads with what matters (NFR-066).

---

## 14. Audit Architecture

Realizes auditability as a first-class, by-construction property (AP-06, E-08, ASR-13).

- **Audit is infrastructure reached through a core-owned port; logging is Definition of Done.** The core and every component *emit events through the `AuditEventPort`* (§7.2); C-14 in infrastructure implements that port and owns the storage, taxonomy, viewer, and search. The core imports no C-14 type and stays headless-testable (a test supplies a no-op port). Each feature logging its own actions is DoD clause 1, enforced story by story (03-epics §4).
- **Versioned event taxonomy from day one** (F-08-01): a v1, evolvable schema covering ingestion, access, classification, period assignment, extraction, quarantine, corrections, verification decisions, rule runs (with rule-set + config versions + input fingerprint), configuration/rule changes, AI interactions (provider/model/version, data transmitted, masking, consent reference, prompt category, output), consent grants/revocations, report generation, and exports (FR-084–090).
- **Attributable and reconstructable** (NFR-019): every record carries user identity and timestamp with enough detail to reconstruct any month's review after the fact — surfaced via the cycle-timeline lens (F-08-02).
- **Provenance of truth** (NFR-022/023): every finding is explainable by the rule-set and configuration versions in force when it was produced (C-18, F-08-03), and every AI artifact by its provider/model/version.
- **Tamper-evidence** (NFR-020, F-08-04, R2, `PROPOSED`): alteration/deletion of audit records is detectable — an audit trail that can be silently edited is not an audit trail.
- **Separation of concerns** (NFR-053): diagnostic/operational logs are distinct from the governance audit trail and never contain sensitive financial values.
- **Integrity of "the same input"** (NFR-058): content fingerprints on ingested files and verified datasets make "same input" provable, not assumed — the foundation of reproducibility claims.

---

## 15. AI Architecture and Constraints

Realizes the approved "Explain This," AI-explains-never-decides, and consent guidance (AP-02, AP-10, E-09). AI is **optional at runtime** and **removable without loss** (FR-095, DEC-015).

**15.1 Position and permissions**

- **Downstream and read-only to the core — structurally.** C-15 reaches the core **only through `FindingsQueryPort`** (§7.1); it holds no reference to `FindingsCommandPort`, so it has no write path into rules, configuration, or findings and *cannot* be given one without a composition-root change caught in review (ASR-04). The permitted verbs are **explain, summarize, narrate, recommend, answer**; the forbidden verbs are **compute, decide, classify-as-finding, set-severity, reconcile, generate-a-variance** (DEC-005, FR-094, NFR-047).
- **Grounded and cited** (FR-094/099, NFR-050): every AI statement is grounded strictly in deterministic outputs and verified data and carries citations resolvable to finding IDs/data points; unsupported questions are declined rather than answered by invention.
- **Visibly distinct** (NFR-049, FR-080/120): AI content is visually and structurally separated, labeled AI-generated, and attributed with provider/model/version — in the app and in every export.
- **Latency-independent and fail-safe** (NFR-004/063): AI runs asynchronously; slow/unavailable/refusing/malformed AI degrades to deterministic-only presentation with clear status, never blocking the monthly process and never substituting fabricated content.

**15.2 "Explain This" specifically**

The **AI narrative explanation** capability (FR-091) attaches to the *deterministic* finding-investigation surface (F-06-02, which is itself no-AI): contextual explanations of findings and metrics **grounded in the deterministic finding and its evidence** — AI explains the finding, it does not generate it (approved guidance concept 9). The explanation is one lens on the same one-click explainability the deterministic layer already provides (NFR-067); with AI disabled, F-06-02's investigation view is fully functional without it (FR-095).

**15.3 Workflow orchestration caveat**

If agents assist workflow orchestration (C-02, detailed in 08), they operate strictly outside the deterministic core: they may sequence/classify/route, but the fixed rule pipeline and its outcomes are untouchable (DEC-005). This constraint is architectural, verified in review, not a matter of prompt discipline (NFR-047).

**15.4 Consent, egress, and privacy** *(see also §17, TB-03)*

- **Consent is the final runtime gate** (FR-096, DEC-006): before any transmission, C-16 discloses provider, exact data, masking state, and implications, requires explicit consent, and logs it; consent is revocable and revocation stops future transmissions immediately.
- **Data minimization** (NFR-015): only the fields needed for the specific operation are sent — never whole files or unfiltered datasets.
- **Masking/tokenization** (NFR-016, R2): where enabled, sensitive identifiers are irreversibly absent from transmitted content and the token map never leaves the app.
- **Advisory registry** (DEC-006/007): the recommended-provider list is admin-managed and auditable but advisory; non-recommended providers trigger an explicit warning state before consent.

---

## 16. Historical Analysis Architecture

Realizes the approved "Historical Review Comparison" and "What's New This Month" guidance as a **first-class capability** (C-13), and frames the **future** "Review Health Score."

**16.1 Comparison across cycles** (grounded in FR-078/108/109, F-06-05, F-07-02)

- Closed cycles are immutable, reproducible inputs (§6.3); C-13 computes deltas across them: what changed, what improved, what got worse, which risks recur, which are new.
- **Recurring-finding identity** (F-06-05) links the same rule+entities across months so "third month in a row" is distinct information; **month-over-month** deltas feed the thin "what changed" section of the summary (F-07-01, R1) and the interactive comparison view (F-07-02, R2).
- **Baselines for history-dependent rules** (F-02-05): trailing averages and history-derived expectations are supplied by C-13 to C-11 rule packs; below minimum history, rules report "insufficient history" (FR-111, AP-11).

**16.2 Change detection ≠ exception detection** (approved concept 10; grounded in FR-041 philosophy, FR-078)

FinSight distinguishes **new** (a vendor/account/spending pattern/department activity appearing for the first time) from **wrong** (a rule violation). "What's New This Month" surfaces change for human attention; it does **not** manufacture findings — new is not wrong. This mirrors the accounting-event awareness principle (FR-041) that keeps routine events from becoming false exceptions. Detection of *new* entities beyond current MoM deltas is a **future** extension (XP-04), not R1 scope.

**16.3 Review Health Score** *(FUTURE; `PROPOSED`; grounded in the approved guidance concept 8)*

A **future, deterministic, configurable** aggregate — **operational/governance-oriented, explicitly NOT a financial score** — computed from operational signals (critical findings, data-quality issues, reconciliation exceptions, risk indicators, open findings). Architectural constraints fixed now so the future feature fits without redesign:

- It is **computed by a deterministic catalog rule** (never by AI — AP-01/02), configurable and versioned like any rule (AP-07).
- It is **distinct from the financial RAG status** (FR-077) and must not be confused with it in model or presentation; it introduces **no R1 scope** and is carried as a roadmap item and extension point (XP-05), consistent with E-13's "visible but deferred" posture.

---

## 17. Security and Trust Boundaries

FinSight's trust model is a small number of hard boundaries, each enforced structurally.

| ID | Boundary | Guarantee | Enforcement | Traces to |
|---|---|---|---|---|
| **TB-01** | Source immutability | Source files are never modified; verified data/corrections/findings are additive layers with lineage | Intake operates on ingested copies only; no write path to source (C-03) | AP-05, FR-003/015, NFR-056 |
| **TB-02** | Verification gate | No analysis runs on unverified data | Rules Engine consumes only a `VerifiedDataset`, constructible **only** by C-06 on approval — analyzed-but-unverified is unrepresentable by construction (§6.2, §11.1) | AP-03, FR-026 |
| **TB-03** | Deterministic/AI boundary | AI cannot compute values, select/alter rules, or generate findings | Command/query segregation (§7.1): findings/severity writable only via `FindingsCommandPort` (wired to C-07/C-11, never C-15); AI holds only `FindingsQueryPort` — the write edge does not exist. Grounding/citation/AI-off tests are defense-in-depth | AP-02, DEC-005, NFR-047 |
| **TB-04** | Consented egress chokepoint | The only outbound data path is to a consented provider, minimum fields only | Single egress path gated by C-16 consent; no other outbound path exists | AP-10, NFR-011/015, FR-096 |
| **TB-05** | At-rest protection & secrets isolation | Stored data protected at rest; secrets in platform-secure storage, never in config/logs | Owned by the DAL (C-17); secrets isolated | ASR-07, NFR-009/010 |
| **TB-06** | Untrusted-input containment | Malformed/hostile files cannot crash, execute code, or corrupt storage | Files treated as untrusted at intake (C-03); defensive parsing | NFR-012 |

**Threat posture (MVP):** single-user desktop; the primary confidentiality risk is **unintended egress of confidential financial data to an AI provider** — mitigated by TB-03/TB-04, consent, minimization, and (R2) masking. Secondary risks: data-at-rest exposure on a lost laptop (TB-05, backup for continuity NFR-060, disposal NFR-017) and malicious input (TB-06). Multi-user authorization is deliberately out of MVP scope (DEC-008) but the identity model is web-generalizable (NFR-071, §20).

---

## 18. Configurability Strategy

Configuration over code, versioned and transparent (AP-07; NFR-039–041; team NFR "configure LLM, database, and anything the application needs").

- **What is configurable without code change:** analysis thresholds/tolerances/anomaly sensitivity/duplicate keys/cutoffs/reconciliation scope (FR-103); reference data — account lists/categories, vendor expectations, fiscal calendar, reconciliation-eligible accounts, expected-entries reference (FR-105); rule enable/disable as governed change (FR-106); AI provider registry and masking behavior (FR-104); storage location and operational choices (NFR-039).
- **Governance:** every configuration change is versioned with user/timestamp/before-after values (FR-107) and every analysis run records the config version it used (NFR-022) — so any historical finding is explainable by the thresholds then in force. Invalid configuration is rejected with clear messages and a known-good state is always recoverable (NFR-040).
- **Transparency:** the user can view the active configuration at any time, and analyses display the config version they used (NFR-041).
- **Separation of concerns:** configuration is dissolved as a standalone epic (DEC-020) — it lives *with* the capability it configures (C-08 for rule parameters/reference data; C-16 for provider registry), while config-*versioning infrastructure* lives with audit (E-08/C-18). This document does not re-introduce a configuration monolith.
- **Rule parameter *values*** are Rules-Catalog items (05), not architecture (DEC-019); this document fixes only that they are configuration, not code.

---

## 19. Extension Points

The seams that must exist now so future capabilities are extensions, not redesigns (ASR-11; NFR-044/045/046). Building them now costs little; retrofitting them later is expensive.

| ID | Extension point | Enables | Traces to |
|---|---|---|---|
| **XP-01** | Rule registration contract | New deterministic rules added to the catalog without touching unrelated modules; each declares inputs/params/outputs/min-history | NFR-044, F-02-01 |
| **XP-02** | Document-type & extraction-template contract | New ingestible document types (invoices/POs/SOWs/rate cards Phase 3; resource sheets Phase 2) as new templates + rule packs on shared intake/normalization/lineage machinery | NFR-045, F-01-05; E-11/E-12 epic notes |
| **XP-03** | AI provider adapter contract | New AI providers added as configuration/adapters with no change to deterministic components | NFR-046, FR-104 |
| **XP-04** | Analysis-dimension & change-detection headroom | Additional dimensions (project/workstream if data appears — OQ-4; invoice-level project dimension already anticipated, FR-122) and future "what's new" entity detection | NFR-043, FR-122, §16.2 |
| **XP-05** | Aggregate-metric hook | Future deterministic operational aggregates (Review Health Score, §16.3) computed as catalog rules | approved concept 8; E-13 posture |
| **XP-06** | Persistence substitution (repository interfaces) | Swap embedded store for a server database without business-logic change | NFR-072, DEC-004 |

**Guardrail (from 04-features §2 and the software-architect canon):** an extension point is a *narrow interface*, not a speculative framework. No generic engine is built before two features demonstrably need the same machinery (the "framework" tripwire, F-14-03). Rule-dependency management and a custom report builder were explicitly rejected as YAGNI (04-features §2.4) and are not reintroduced here.

---

## 20. Future Web-Migration Considerations

The MVP is desktop-first (DEC-003) and architected so a future web transition does not reimplement the core (NFR-070, ASR-10).

- **Core independence (AP-09):** business logic, rules, findings, and audit contain no desktop-only assumptions and depend on no UI/storage/provider types; the domain core is drivable from a desktop shell, a web backend, or a headless test harness unchanged. The web transition replaces the delivery ring (C-01, and the hosting of C-15), not the core (C-07/09/11) — this is the payoff of the layering in §7.
- **Storage substitutability (ASR-09, XP-06, DEC-004):** only the DAL touches storage; migrating from an embedded file-based store to a server database is a new DAL implementation behind existing repository interfaces.
- **Identity generalization (NFR-071, DEC-008):** actions attribute to a user identity modeled so "local OS user" generalizes to authenticated multi-user identities; adding roles (Leader/PM/finance partner/vendor manager/executive — 00 §10) is an additive change, not a redesign. Full RBAC remains out of MVP scope.
- **Dimensional and multi-user headroom (NFR-042/043):** data structures do not preclude multiple departments, added dimensions, or multi-user operation later, while MVP behavior stays single-department, single-user.
- **Discipline (NFR-032):** no expedient shortcut that compromises the deterministic core, auditability, or the web transition is acceptable — "no shortcuts" is a maintainability requirement, not an aspiration.

The web migration itself is **future scope**, not designed here; only the *posture* that keeps it cheap is fixed now.

---

## 21. Walking Skeleton Architecture

Release 1 build starts with a **walking skeleton** (DEC-022, 03-epics §Release plan): the thinnest possible end-to-end thread that proves the architecture's spine before any capability is built out.

**Skeleton thread (one of everything, wired end to end):**

```
one file  ─▶  one extraction (with lineage)  ─▶  one verification approval (the gate)
          ─▶  one deterministic rule  ─▶  one finding (with severity + evidence + trace)
          ─▶  one summary line  ─▶  one export line
   with:  audit ON from story one  ·  persistence transactional from story one  ·  config-versioned run
```

**What the skeleton must exercise (proving the load-bearing boundaries early):**

- The **Review-Cycle aggregate and state machine** (§6) create → intake → verify → analyze → report, resumable and audited.
- The **verification gate** (TB-02): the single rule cannot run until the single document is approved.
- The **deterministic core boundary** (TB-03): the rule and finding are produced with no AI in the path; the AI-off path is complete by construction (FR-095).
- **Persistence through the DAL** (C-17): the skeleton survives a force-kill mid-run with no lost verified data (NFR-005), and the cross-platform determinism test runs on the single rule from day one (NFR-029).
- **Audit taps** (C-14) on every step, from story one (DoD clause 1).

**Composition slices:** MVP slices of E-14 (shell, never-lose-work, data protection), E-01 (intake/extraction/verification), E-02 (engine, one rule, replay), E-08 (audit capture), E-06 (one finding), E-07 (one summary/export line). Capability breadth (Budget/GED/Reconciliation rule packs) is added *after* the skeleton walks — the first wave is E-14, E-01, E-02, E-08, E-06 (03-epics §2).

The skeleton is the architecture's first proof: if the boundaries in this document cannot support one thread end to end, they are wrong, and that is discovered on day one rather than at integration.

---

## 22. Architecture Risks

| ID | Risk | Likelihood | Impact | Notes |
|---|---|---|---|---|
| **AR-01** | Determinism leaks (floating-point, locale, wall-clock, ordering, hash-map iteration) silently break byte-identical cross-platform/provider results | Med | High | The project's central promise (NFR-021/029); classic silent-variance class |
| **AR-02** | The deterministic/AI boundary erodes over time as AI features grow (a convenience edge from AI into computation) | Med | High | Boundary must be structural, not disciplinary (NFR-047) |
| **AR-03** | Unintended egress — a future feature, telemetry, or auto-update opens a second outbound path around consent | Low | High | Violates the core confidentiality promise (NFR-011) |
| **AR-04** | E-02 (Rules Engine) enabler starvation — the whole first wave blocks on it; under-resourcing stalls E-03/04/05 | Med | High | Named dependency risk (DEC-021) |
| **AR-05** | Findings-experience fragmentation — capability teams build per-capability findings forks under delivery pressure | Med | Med | Violates AP-12/F-06-01 binding criterion |
| **AR-06** | Audit/config-version schema, decided earliest, is expensive to change and drifts under evolving needs | Med | Med | Watch item (04 §15); schema versioning is the mitigation |
| **AR-07** | Persistence coupling — components reach around the DAL, defeating storage substitutability and the web transition | Med | High | Defeats NFR-072/070 |
| **AR-08** | Consent-model invalidation — Amerisure security requires hard enforcement over consent (OQ-1), late-invalidating E-09 design | Med | High | Production gate; enforcement-mode fallback needed (DEC-021) |
| **AR-09** | Cold-start noise — history-dependent rules fire unreliably in early months, eroding trust when FinSight is first judged | Med | High | FR-111; the first months are the adoption test |
| **AR-10** | Verification-gate friction — the mandatory gate is slow enough that users resist adoption | Med | Med | Adoption killer if slower than paste-and-clear (NFR-068) |
| **AR-11** | Scope creep in the shell/foundation (E-14) and analysis views — "just polish" accretion | High | Med | Highest scope-creep risk in the product (04 §15) |
| **AR-12** | Phase 3 assumption risk — unseen invoice/PO/SOW/rate-card formats force extraction rework | Med | Med | A-05; gated on samples (OQ-2, DEC-011) |
| **AR-13** | Readiness/Review-Health concepts (new architectural guidance) drift into implied new requirements beyond their FR grounding | Low | Med | Kept `PROPOSED` and grounded (§10, §16.3); no R1 scope for Health Score |

## 23. Risk Mitigations

| Risk | Mitigation | Verified by |
|---|---|---|
| AR-01 | Exact decimal arithmetic (NFR-059); inject clock; forbid locale-dependent parse/sort and RNG in the core; explicit ordering | Golden-dataset + cross-platform determinism tests on both OSes as CI gate (NFR-029/036/048); ADC-05 |
| AR-02 | Command/query segregation (§7.1): findings/severity writable only via `FindingsCommandPort` (wired to C-07/C-11), AI holds only `FindingsQueryPort` — the write edge is unwired and blocked by the CI architecture-fitness test (frozen `Finding`, no public constructor) | Architecture-fitness test asserting C-15 references only `FindingsQueryPort` (ADC-02/11); provider-swap regression (NFR-037), AI-off completeness (FR-095), grounding/citation tests (NFR-050) as defense-in-depth |
| AR-03 | Single egress chokepoint (TB-04); "no other outbound path" is an architecture invariant reviewed on every change | Architecture test for outbound calls outside the consent chokepoint (ADC-07); design-board review |
| AR-04 | Protect E-02 capacity as a first-wave enabler (DEC-021); walking skeleton exercises the engine on day one | Release plan tracking; skeleton acceptance (§21) |
| AR-05 | One findings model + shared components as a binding criterion (F-06-01); no per-capability fork admitted | Review-board check that Budget/GED/Reconciliation findings render through the same components |
| AR-06 | Versioned event/config schema from v1, evolvable (F-08-01); decided consciously and early | Schema-version field present from story one; migration path tested |
| AR-07 | Only the DAL touches storage; repository interfaces; dependency-rule architecture test | Architecture test forbidding storage types outside the DAL (ADC-02/06) |
| AR-08 | Design E-09 with an enforcement-mode fallback so consent-vs-enforcement is a configuration posture, not a redesign (DEC-021) | Consent/enforcement toggle covered by tests; OQ-1 tracked as production gate |
| AR-09 | Minimum-history declarations; "insufficient history" over unreliable firing; report which rules ran with limited baselines (F-02-05, FR-111) | Cold-start behavior in golden tests; report discloses limited baselines |
| AR-10 | Bulk approval of high-confidence data; attention only to exceptions/low-confidence (NFR-069, F-01-09) | Pilot workflow-efficiency measurement vs. manual baseline (NFR-068) |
| AR-11 | R1 shell = navigation between R1 surfaces + one settings screen; any screen not tracing to a locked feature is rejected (F-14-01 guardrail); "framework" tripwire (F-14-03) | Feature-traceability check in review; scope watch items (04 §15) |
| AR-12 | Document-type/template extension point (XP-02); Phase 3 gated on samples; assumed-format requirements re-verified before build (DEC-011) | Extension-point conformance; sample-gate (OQ-2) before E-12 build |
| AR-13 | Readiness and Review-Health kept explicitly `PROPOSED`, grounded in existing FRs, deterministic, and free of new R1 scope (§10, §16) | This document's traceability (§27); design-board confirmation |

---

## 24. Assumptions

Architecture-specific assumptions (`AA-##`) build on the project Assumptions Register (A-01..A-13 in 01 §2) — those remain in force and are not restated. If any assumption fails, the dependent architectural choices must be revisited.

| ID | Assumption | If wrong | Depends on |
|---|---|---|---|
| **AA-01** | An embedded, file-based, server-less persistence store behind a DAL meets MVP needs at single-department volumes | Persistence strategy and performance targets revisited | DEC-004, A-08, NFR-001/042 |
| **AA-02** | A web-tech-capable desktop shell can be cleanly separated from the deterministic core | Web-migration posture (§20) weakens; more rework later | DEC-003, NFR-070 |
| **AA-03** | An enterprise-hosted AI endpoint is the primary production AI path, reached over proxy-friendly network behavior | AI adapter/consent design adjusts; local-model path elevated | A-06, DEC-016, NFR-030 |
| **AA-04** | Exact decimal arithmetic and platform-independent parsing/sorting are sufficient to guarantee byte-identical cross-platform results | Additional platform-normalization needed to hold NFR-029 | ASR-06, NFR-029/059 |
| **AA-05** | Single-user, single-department scope holds for the MVP; multi-user/multi-department is future | Identity/scope model exercised earlier than planned (headroom exists) | DEC-008, A-11, NFR-043/071 |
| **AA-06** | Workflow orchestration (possibly agent-assisted) can be implemented strictly outside the deterministic core without an edge into it | The deterministic/AI boundary (TB-03) needs re-examination | DEC-005, NFR-047 |
| **AA-07** | The capability-readiness model (§10) is fully derivable from existing FRs and introduces no new requirement | Readiness becomes a requirements-level change (raise via decision log) | §10 grounding; DEC-019 |

## 25. Open Questions

Architecture open questions (`AOQ-##`) plus the project open questions (OQ-1..OQ-8, 09) classified `AR` (architecture) or bearing on architecture. These do not block this document's approval as a *logical* architecture; they gate specific *technology* ADRs (§26) or production go/no-go.

| ID | Question | Blocks | Owner |
|---|---|---|---|
| **OQ-1** | Will Amerisure security validate consent-over-enforcement (DEC-006)? | E-09 production gate; AR-08 fallback | Aditi → Amerisure security |
| **OQ-3** | Does an Amerisure-approved managed AI endpoint exist, and its access mechanics? | ADC-03 (AI adapter/consent binding); AA-03 | Aditi → stakeholders |
| **AOQ-01** | Concrete persistence technology and its at-rest protection mechanism (embedded store choice; encryption vs. OS-level protection) | ADC-01, ADC-08 | Architecture phase (ADR) |
| **AOQ-02** | Desktop shell + application-core technology binding, and the core/shell separation mechanism | ADC-01 | Architecture phase (ADR) |
| **AOQ-03** | Workflow orchestration mechanism and whether/where agents assist it, without crossing TB-03 | ADC-04; 08-ai-and-agents | Architecture phase (ADR) + 08 |
| **AOQ-04** | Exact-decimal arithmetic standard and the cross-platform determinism test harness design | ADC-05 | Architecture phase (ADR) |
| **AOQ-05** | Consent/egress chokepoint mechanism and how "no second outbound path" is enforced in CI | ADC-07 | Architecture phase (ADR) |
| **AOQ-06** | Audit tamper-evidence approach (NFR-020, still `PROPOSED`) if accepted | ADC-09; F-08-04 | Supervisor approval + architecture |
| **AOQ-07** | Backup/restore format and data-disposal mechanism on single-machine deployment | ADC-01 (DAL scope) | Architecture phase (ADR) |

Rules-Catalog open questions (OQ-5/7/8) and internal-decision items (A-09/10/11) are **not** architecture blockers (DEC-019); the architecture accommodates any resolution via configuration (§18) and the workspace/finding and carry-forward designs (§13, C-10).

---

## 26. Architecture Decision Candidates

Each candidate below becomes a real, numbered `ADR-###` via `/sdd:adr` (Nygard format with Traces-to and Verification), submitted to the design review board before its status changes to Accepted. This section names the decisions to be made; it does **not** make the technology choices (per directive; DEC-003/DEC-004 are noted where they already set direction).

| ID | Decision to record | Direction already logged? | Traces to | Verification target |
|---|---|---|---|---|
| **ADC-01** | Desktop-shell + application-core stack, and the core/shell/storage separation | Directional: DEC-003 (shell over core); DEC-004 (embedded store behind DAL) — to be confirmed as ADRs | NFR-070/072, ASR-09/10 | Headless-core test harness; dependency-rule architecture test |
| **ADC-02** | Layering, dependency rule, and **core-owned ports** (`FindingsQueryPort`/`FindingsCommandPort`/`AuditEventPort`/repositories); domain core imports no UI/storage/provider/AI types and delivery reaches the core only through ports | New (this document's §7.1–7.3) | AP-08/09, NFR-031/070, NFR-047 | Architecture test: no forbidden inward-importing dependency; **C-15 references only `FindingsQueryPort`** (write edge unwired; enforced by the CI architecture-fitness test, not the compiler); audit/storage reached only via ports |
| **ADC-03** | AI-layer integration: provider adapter contract (behind XP-03), grounding & citation enforcement | Directional: DEC-003 (AI-layer direction); depends on OQ-3 | AP-02, NFR-046/050, FR-094/099 | Grounding/citation tests; AI-off completeness regression |
| **ADC-04** | Workflow orchestration mechanism (and agent role, if any) outside the deterministic core — orchestrator holds no `FindingsCommandPort`/rule-selection authority | New; depends on AOQ-03 | DEC-005, NFR-047, AA-06 | Architecture test: orchestrator has no write edge into rules/findings; provider-swap regression |
| **ADC-05** | Exact-decimal arithmetic standard + cross-platform determinism harness | New | ASR-01/06, NFR-029/036/059 | Golden-dataset + both-OS determinism CI gate |
| **ADC-06** | Persistence: repository interfaces & substitution strategy (embedded → server DB) | Directional: DEC-004 | ASR-09, NFR-072, XP-06 | Architecture test: only DAL touches storage; interface-swap test |
| **ADC-07** | Single consented-egress chokepoint & "no second outbound path" enforcement | New | AP-10, NFR-011/015, TB-04 | CI check for outbound calls outside the consent chokepoint |
| **ADC-08** | At-rest protection & secrets-storage mechanism | New; depends on AOQ-01 | ASR-07, NFR-009/010, TB-05 | Verify stored artifacts protected; secrets absent from logs/config |
| **ADC-09** | Audit via core-owned `AuditEventPort` (§7.2); event/config-version schema (v1, evolvable) and tamper-evidence approach | New; tamper-evidence pending AOQ-06/NFR-020 | ASR-13, NFR-019/020/022 | Core emits only through `AuditEventPort` (headless test with no-op port); reconstruct-a-month from audit alone; tamper-detection test (if accepted) |
| **ADC-10** | Review-Cycle state model: **two orthogonal Harel regions** (per-artifact + cycle projection); Rules Engine consumes only a `VerifiedDataset` constructible solely by C-06 | New (this document's §6.2) | AP-03/04, FR-006/026/029, NFR-006/008 | Type-level: analyzed-but-unverified unrepresentable by construction; state-machine tests as defense-in-depth; resume/idempotent re-run |
| **ADC-11** | Findings model/experience split (C-09a core contract + severity/lifecycle vs. C-09b delivery experience); shared-component rendering, no per-capability forks | New (§7.3) | AP-12, F-02-04, F-06-01, FR-069/070/072 | Architecture test: C-09b reads via `FindingsQueryPort` only; all capabilities render through shared C-09b components |

---

## 27. Traceability Back to Requirements, Epics, and Features

This architecture is a derived artifact: every component and boundary answers to approved scope, and it introduces none of its own. The tables below establish coverage in both directions (spec → architecture and architecture → spec), per the traceability skill.

**27.1 Epic → owning component(s)**

| Epic | Owning component(s) |
|---|---|
| E-01 Data Intake, Extraction & Verification | C-03, C-04, C-05, C-06 |
| E-02 Deterministic Rules Engine | C-07, C-08 |
| E-03 Budget Review & Analysis | C-11 (budget pack), C-09a/C-09b, C-12 |
| E-04 GED Analysis & Exception Detection | C-11 (GED pack), C-09a/C-09b |
| E-05 Reconciliation Automation | C-10, C-11 (match pack), C-09a/C-09b |
| E-06 Findings & Exception Management | C-09a (core model), C-09b (experience) |
| E-07 Executive Reporting & Export | C-12, C-13 (MoM) |
| E-08 Audit & Compliance | C-14, C-18 (config-version history) |
| E-09 AI Assistance (Optional) | C-15, C-16 |
| E-11 Resource & Contract Management *(Phase 2)* | C-04/C-11 via XP-02 (extension) |
| E-12 Invoice Review & Validation *(Phase 3)* | C-04/C-11 via XP-02 (extension) |
| E-13 Forecasting & What-If *(Deferred)* | C-11/C-13 via XP-05 (extension) |
| E-14 Desktop Application Foundation & Experience | C-01, C-17 (+ cross-cutting) |

**27.2 Architecture-Significant Requirement → satisfying structure**

| ASR | Satisfied by |
|---|---|
| ASR-01 Reproducibility | AP-01, C-07 (§12), replay F-02-06, ADC-05 |
| ASR-02 Determinism as release criterion | §12.2, standing regressions, ADC-05, C-15 removability |
| ASR-03 Verification gate | AP-03, §11, TB-02, C-02/C-06, ADC-10 |
| ASR-04 Deterministic/AI boundary | AP-02, §7.1 command/query segregation, §15, TB-03, ADC-02/04/11 |
| ASR-05 No data loss / resumable / transactional | C-17, §6.2, ADC-06/ADC-10 |
| ASR-06 Cross-platform identical results | §12.2, NFR-059, ADC-05 |
| ASR-07 At-rest & secrets | C-17, TB-05, ADC-08 |
| ASR-08 No unconsented egress | AP-10, TB-04, C-16, ADC-07 |
| ASR-09 Storage substitutability | C-17, XP-06, ADC-06 |
| ASR-10 Web-migration core independence | AP-09, §7 layering, §20 |
| ASR-11 Extensibility | §19 XP-01..05, ADC-03 |
| ASR-12 Performance & asynchrony | C-01/C-02 async, §15 AI async, §9 |
| ASR-13 Audit completeness & tamper-evidence | C-14, §14, ADC-09 |
| ASR-14 Accessibility of meaning | C-01, C-09a non-color severity encoding (rendered by C-09b) |

**27.3 Approved architectural guidance → realization**

| Approved concept | Realized in | Grounded in (no new scope) |
|---|---|---|
| 1. Review-centric architecture | §6 Review-Cycle; AP-04 | FR-006, DEC-022, F-01-01 |
| 2. Centralized document intake | C-03; §5; §10 | FR-001/002/004, E-01 |
| 3. Capability readiness validation | §10; C-05 (`PROPOSED` model) | FR-004/007/021–025/081/111 |
| 4. Verified data principle | §11; AP-03; TB-02 | FR-026, DEC-005 |
| 5. Deterministic core principle | §12; AP-01/02; TB-03 | DEC-005, FR-094/095, NFR-021/047 |
| 6. Findings hub principle | §13; C-09a/C-09b; AP-12 | E-06, F-02-04, F-06-01 |
| 7. Historical review comparison | §16.1; C-13 | FR-078/108/109, F-06-05, F-07-02 |
| 8. Review Health Score | §16.3 (FUTURE, `PROPOSED`); XP-05 | approved guidance; distinct from FR-077 |
| 9. Explain This | §15.2; C-15 (AI) augmenting C-09b/F-06-02 (deterministic surface) | FR-091 (AI explanation), FR-099, F-06-02 (surface), NFR-050/067 |
| 10. What's new this month (new ≠ wrong) | §16.2 (future detection via XP-04) | FR-078/032, FR-041 philosophy |

**27.4 Feature → primary component (Release 1 decomposed features)**

| Feature | Component |
|---|---|
| F-01-01 Monthly Review Cycle Workspace | C-02 |
| F-01-02/03/04 Upload / Recognition / Wrong-file | C-03 |
| F-01-05/06/07 Extraction framework / GED / Budget | C-04 |
| F-01-08 Data Quality Gate & Quarantine | C-05 |
| F-01-09 Verification Workspace | C-06 |
| F-02-01..06 Rules engine features | C-07, C-08 |
| F-03-01/02/03 Budget dashboard / variance / exception pack | C-11, C-12, C-09a/C-09b |
| F-04-01/02 GED summarization / exception pack | C-11, C-09a/C-09b |
| F-05-01/02 Matching pack / Reconciliation workspace | C-11, C-10 |
| F-06-01/04 Findings inbox / search · F-06-02/03 investigation / lifecycle | C-09b (experience) · C-09a (severity/lifecycle contract) |
| F-07-01/03/04 Summary / report history / export | C-12 |
| F-08-01/02/03 Audit capture / explorer / config history | C-14 (via `AuditEventPort`), C-18 |
| F-14-01/03/05/06 Shell / background / accessible / backup · F-14-02 never-lose-work · F-14-04 data-protection | C-01 · C-01+C-17 (shared) · C-17 |

**27.5 Coverage statements**

- **Every Phase-1 epic and Release-1 feature** has an owning component (27.1, 27.4); no epic is orphaned.
- **Every ASR** maps to a specific structural mechanism (27.2); no architecture-significant requirement is unaddressed.
- **Every approved architectural-guidance concept** is realized and grounded in existing scope (27.3); none introduces a requirement beyond the approved set — new framings (readiness §10, Review Health Score §16.3) are tagged `PROPOSED`, deterministic, and free of R1 scope, and any elevation to a requirement goes through the decision log (DEC-019 discipline).
- **No conflict introduced:** the architecture respects every logged decision (DEC-003/004 directional tech; DEC-005 boundary; DEC-006/007 consent; DEC-008 single-user; DEC-009 phasing; DEC-019 catalog/architecture split; DEC-020 configuration dissolution; DEC-022 release-based delivery/Trust > AI; DEC-023 feature lock), and weakens no Must.

**27.6 Downstream trace obligation**

Per the traceability skill, implementing units will carry `Implements: FR-###, F-##-##` and tests `Verifies: FR-###/NFR-###`; the decision candidates in §26 will be recorded as `ADR-###` with their own `Traces-to`; and `/sdd:trace` will assemble the full requirement → feature → plan → task → code → test matrix. This document supplies the missing middle: the structural layer that plans (05/07/08 and `specs/plans/`) elaborate against.

---

*End of 06-architecture.md — logical architecture only. Technology and framework binding deferred to ADRs (§26). Submit to the spec-driven design review board (`software-architect, data-architect, integration-architect, security-engineer, qa-engineer`, augmented by `ai-governance-reviewer` and `compliance-auditor` for the AI and audit boundaries) before any status change beyond Draft.*
