# FinSight — Constitution

- **Version:** 1.0
- **Status:** Adopted
- **Adopted:** ratified under the approved baseline (documentary date not recorded in repository)
- **Owner:** Project Owner (Aditi), accountable; amended only under an approved Change Request
- **Governing methodology:** Spec-Driven Development (DEC-010, NFR-073)

> This document is the governing constitution for FinSight. It **introduces no product scope**. It consolidates and formalizes principles, decision rights, quality bars, and terminology that already emerged and were approved across the specification set (00–12) and the decision log (DEC-001–DEC-034). It is deliberately durable: it contains principles, governance, rights, responsibilities, quality bars, and shared language — never implementation detail, technology choices, temporary decisions, or feature-specific behavior. Every clause traces to an existing approved source (§12).

---

## 1. Purpose

The Constitution is FinSight's governing document. It exists to answer one question: **"What principles govern every decision made on this project?"** — for the product and for how the product is built. It is:

- the source of project-wide **principles** (§3);
- the source of **decision rights** and **human accountability** (§4–§6);
- the source of **quality expectations** every artifact must satisfy (§7);
- the source of **shared terminology** (§9–§10);
- the foundation that **baselines, ADRs, plans, tasks, verification, and implementation** trace up to.

When any lower artifact (requirement, rule, plan, code, review) is in doubt, the Constitution is the tie-breaker on principle, governance, and language. It formalizes what FinSight already believes; it does not redesign FinSight.

## 2. Scope

- **Applies to:** every contributor (human or AI), every artifact under `specs/`, and every implementation artifact (code, tests, configuration) produced for FinSight, across all releases and phases.
- **Governs:** principles, decision rights, quality bars, governance expectations, and terminology.
- **Does not govern (deliberately):** product feature behavior (that is 01–10), rule parameter *values* (Rules Catalog / configuration, DEC-019), technology choices (ADRs), or any temporary or release-specific decision. Those live in their own artifacts and change on their own cadence; the Constitution stays stable while they evolve.
- **Precedence:** where an artifact conflicts with the Constitution on a matter of principle or governance, the Constitution prevails and the conflict is resolved through `/sdd:change`, never a silent edit.

## 3. Foundational Principles

Binding on every contributor, human or AI. A review finding that violates a principle defaults to **MAJOR** (severity taxonomy: code-review-standards skill, engineering-standards plugin). Principle numbering (`P-#`) is **stable forever** — a principle is superseded by amendment, never renumbered or deleted.

**Core principles (the non-negotiable framework core — P-1…P-7):**

1. **P-1 — Spec-first source of truth.** `specs/` is authoritative. When code and an approved spec disagree, one of them is defective; the resolution goes through `/sdd:change` — never a silent edit to either side.
2. **P-2 — Human accountability for AI-assisted work.** AI proposes; named humans approve. Every AI-suggested item carries `Source: AI-PROPOSED (<reason>)` and an approver of record. Accountability for shipped behavior always rests with a person.
3. **P-3 — Identical quality gates for all code.** Generated, AI-written, vendored, and hand-written code pass the same review, tests, and static analysis. There is no "it was generated" exemption.
4. **P-4 — No silent failure.** Every error is surfaced — logged, reported, or raised to the user as appropriate. Swallowed exceptions and defaulting fallbacks that mask bad data are defects, not defensive coding.
5. **P-5 — Traceable code.** Every implementation unit carries an `Implements:` annotation and every test a `Verifies:` annotation, so `/sdd:trace` can close the loop in both directions.
6. **P-6 — Reviewable changes.** A change is small enough for one qualified reviewer to understand in one sitting (guideline: ≤ ~400 changed lines); larger work is split first.
7. **P-7 — Determinism where money or compliance is computed.** Same inputs produce identical outputs: exact decimal arithmetic, pinned rounding rules, golden-dataset tests, and no wall-clock, locale, or iteration-order dependence in computation paths.

**FinSight principles (project-specific — P-8…P-16), consolidated from the approved set:**

8. **P-8 — Trust > AI; the deterministic core is the system of record.** Every financial value, finding, variance, severity, status, reconciliation outcome, and score is produced only by deterministic logic. AI may explain, summarize, and assist, but never computes financial truth, generates a finding, or decides. *(DEC-005, AP-01, NFR-047)*
9. **P-9 — Verification before analysis.** No analysis runs on data a human has not explicitly verified. Verification is a hard gate, not a step that can be skipped or defaulted. *(FR-026, TB-02)*
10. **P-10 — Human decision ownership.** FinSight recommends; humans decide. It never approves, rejects, pays, posts, modifies a financial system, or contacts a vendor. 100% of financial actions remain human. *(00 §1, FR-059, FR-083)*
11. **P-11 — AI optionality.** The product is fully functional with no AI configured — every number, finding, status, and report section exists without AI. AI is an optional, removable layer. *(FR-095, DEC-015)*
12. **P-12 — One findings experience; change ≠ exception.** All analytical capabilities feed a single findings experience with no per-capability forks; change detection ("what's new") is surfaced separately from exception detection ("what's wrong") and never manufactures findings. *(AP-12, F-06-01, FR-041)*
13. **P-13 — Accessibility first.** FinSight is usable by everyone; meaning is **never** conveyed by color alone (severity, RAG, and status always pair color with icon/shape/label); primary workflows are keyboard- and screen-reader-operable. *(NFR-024–027, especially NFR-025)*
14. **P-14 — Auditability by design.** Every material action is recorded attributably and reconstructably, so any month's review can be reconstructed after the fact; audit is infrastructure, and logging is part of the Definition of Done. *(E-08, NFR-019, DoD)*
15. **P-15 — Configuration over hardcoding.** Business values — thresholds, tolerances, calendars, materiality, reference data, provider registry — are versioned configuration, never hard-coded; every analysis records the configuration version in force. *(AP-07, FR-107, DEC-019)*
16. **P-16 — Monthly Review in a Box.** FinSight is organized around the monthly **Review Cycle**, not around modules; the user completes a month's review through a guided process, not a menu of tools. *(DEC-022, FR-006, AP-04)*

## 4. Decision Rights

Every decision below is **made by a human role**. AI is never a listed decider (§5–§6). "Consulted" parties inform the decision; "Recorded in" is the mandatory evidence location.

| Decision | Decided by (human) | Consulted | Recorded in |
|---|---|---|---|
| Requirement approval / scope | Project Owner | Amerisure & finance stakeholders | `specs/workbooks/WORKBOOK-<date>.md` + decisions log |
| Architecture decision (technology binding) | Technical Lead / Software Architect | Design-review board via `/sdd:review-board` | `specs/adr/ADR-###-<slug>.md` |
| AI boundary change (what AI may/may not do) | Project Owner + Technical Lead | AI-governance reviewer; Amerisure security | Decision log + `specs/adr/` where structural |
| Rule change (logic) / new rule | Technical Lead | Finance Governance Lead; QA | `specs/adr/` (if structural) + Rules Catalog + `/sdd:change` |
| Rule **parameter values** (thresholds, cutoffs, materiality) | Finance (owner of the value) | Project Owner | Configuration (versioned, FR-107); Rules Catalog register (not a code change — DEC-019) |
| Change Request (post-baseline scope) | Project Owner (change authority) | Affected owners; design-review board | `specs/changes/CR-###.md` |
| Baseline approval | Project Owner + Technical Lead | Delivery team / stakeholders | `specs/baselines/v<major>.<minor>/BASELINE.md` (SHA-256 manifest + approval) |
| Merge / release readiness | Human reviewer(s) per §7; Project Owner for release | Design-review board (by trigger) | PR record + release checklist (11 §18) |
| Constitution amendment | Project Owner (sponsor) | Entire team; stakeholders where principles touch Amerisure | Amendment history (§11) + the CR |

**Locked rule (decision authority):** every "Decided by" cell is a named human role. No AI system, agent, or model appears as a decider anywhere in this table, now or by amendment.

## 5. Human Accountability

Human accountability is **mandatory** throughout FinSight and throughout its development. This is not a preference; it is a constitutional invariant.

- **Humans make decisions.** AI may explain, summarize, clarify, translate, and assist. AI may **never** approve, authorize, ratify, override, accept, reject, or make a decision on behalf of a human — in the product or in development.
- **A person owns every shipped behavior.** AI-proposed content is labeled `AI-PROPOSED` and carries an approver of record until a human ratifies it (P-2). Agent-generated code is human-reviewed and passes the same gates before acceptance (P-3, DEC-010).
- **Accountability does not transfer to a tool.** "The model did it" is never a defense; the accountable human role in §4 owns the outcome.
- **In development, the same rule holds:** developers own design, architecture, security, code-quality, review, and merge decisions; AI tools assist but are never authoritative and never the source of truth (11 §10).

## 6. AI Boundaries

Consolidated from DEC-005, NFR-047, and 10-ai-and-agents §2. These boundaries are structural, not advisory.

**AI (product-side, "Fin") MAY:** explain · summarize · clarify · answer grounded, cited questions · guide investigations (where to look) · translate technical findings into business language · improve understanding and usability.

**AI (product-side) MAY NOT:** create, change, or suppress findings or exceptions · compute any financial value, variance, severity, RAG, or score · approve/reject reviews or invoices · override rules or select/skip/reorder them · modify source or verified data · bypass verification · make business or financial decisions · recommend business/financial actions (approvals, rejections, spending changes) · contact vendors · take any action silently.

**AI (development-side) MAY:** help understand requirements/architecture, draft code and tests, and assist productivity. **MAY NOT:** become the source of truth, or make any decision reserved to humans in §4–§5. Specifications remain authoritative (P-1).

**Enforcement:** the boundary is enforced by design — the AI layer reaches the deterministic core only through a read-only interface and holds no capability to write findings, severities, or actions (architecture C-15/TB-03). Grounding, citation, and AI-off-completeness are verified by standing tests. Any change to these boundaries is a governed decision (§4) requiring human approval and, where structural, an ADR.

## 7. Quality Bars

"Good enough" is defined here once, measurably — never re-negotiated per pull request. Every implementation artifact must satisfy all applicable bars; they apply identically to human- and AI-generated work (P-3).

- **Determinism:** same verified inputs + configuration version ⇒ byte-identical findings/statuses/severities/variances, across AI providers and across Windows and macOS. Golden-dataset and provider-swap regressions **must pass to ship** — the hard release gate. *(NFR-021/029/036/037/048/059)*
- **Traceability:** every unit `Implements:` and every test `Verifies:` a requirement ID; `/sdd:trace` returns `TRACEABILITY: PASS` with zero orphans as a merge gate. *(NFR-033; P-5)*
- **Testing:** tests are written with the code (untested code is not done); every acceptance criterion of a shipped feature has an automated test naming the FR/NFR it verifies; rule packs meet golden-dataset acceptance; financial logic is human-verifiable against the Rules Catalog. *(NFR-035/036/076)*
- **Accessibility:** WCAG 2.2 AA for all user-facing surfaces; no meaning by color alone; keyboard- and screen-reader-operable; 200% zoom without breakage — verified per story, not at the end. *(NFR-024–027; P-13)*
- **Auditability:** every material action writes an attributable, timestamped, fingerprinted audit record; any month's review is reconstructable from the trail alone. *(NFR-019; P-14)*
- **AI transparency:** AI-generated content is visually distinct, labeled, attributed (provider/model), and cited to its evidence — in the app and in exports; AI declines the unsupported. *(NFR-049/050; FR-080/099)*
- **Reviewability:** every merge has ≥1 human review; design-review-board sign-off is required for triggering scope (plans, schema/DAL, security/consent/egress paths, UI surfaces, the AI layer). Reviewers are read-only. *(NFR-074/075/080; P-6)*
- **Data protection & hygiene:** data protected at rest; secrets in secure storage, never in logs/config; **no real customer data in development or testing — synthetic/sanitized only.** *(NFR-009/010/018)*
- **No silent failure / honesty under failure:** errors are visible and actionable; partial results are never presented as complete; rules below their minimum history report "insufficient history" rather than firing. *(NFR-062; FR-111; P-4)*
- **Performance:** budgets live as fit criteria in the NFRs; a merge may not regress a Baselined fit criterion. *(NFR-001–004)*

The full, itemized **Definition of Done** (which composes these bars) is maintained in 11-development-methodology §15; a feature is complete only when every applicable clause is satisfied.

## 8. Governance Expectations

- **Spec-driven, gate-checked flow.** New scope follows the full SDD path (requirement → feature → plan → ADR → tasks → implement → verify); bug fixes and behavior-preserving refactors use lighter paths (11 §3–§5). Process weight matches risk; ceremony that reduces no real risk is removed.
- **Baselines are immutable.** A baseline is a sealed, hashed, approved snapshot; it is never edited (hook-enforced). Scope changes flow through `/sdd:change` and are re-baselined at the boundary; rejected CRs remain on file.
- **Enforcement is ambient, not remembered.** Hooks (baseline immutability, spec-lint, session status), command gate-order refusals, and the CI trace gate make the rules structural rather than matters of discipline. Refusals are navigation, not friction.
- **Reviews carry evidence, preserve dissent.** Findings cite file:line or a spec ID and a canon/standard; dissent is preserved, never averaged; reviewers do not edit what they judge.
- **No shortcuts.** No expedient hack may compromise the deterministic core, auditability, the deterministic/AI boundary, or the future web-transition posture. *(NFR-032)*
- **Technical debt is tracked, owned, and bounded** by the hard lines above; YAGNI is enforced — no speculative engine or framework before two features demonstrably need it.

## 9. Shared Language Principles

- **One term, one meaning.** Every term used in requirements has exactly one meaning; the Glossary (§10) is the arbiter. Terms not listed there may not carry specialized meaning in specs.
- **Ubiquitous language.** The words in the specs, the UI, and the code are the same words. Code identifiers match the domain nouns the specs use; divergence (e.g., code says "package" where specs say "shipment") is a defect.
- **Definitions are testable.** Each glossary entry is a single, testable sense with a named authority.
- **The Glossary is durable.** New terms are added by amendment (§11); a term's meaning changes only through a Change Request.

## 10. Glossary

The authoritative FinSight terminology. Single, testable definitions; authority cites the approved source.

| Term | Definition (single, testable sense) | Authority |
|---|---|---|
| **FinSight** | An AI-enabled, read-only financial **review and governance assistant** built by HCLTech for Amerisure; not a transactional system. | 00 §1 |
| **Amerisure** | The customer; owner of the financial data and of the principles the Constitution encodes. | 00 §1 |
| **Monthly Review in a Box** | The organizing product concept: a complete monthly financial review, end to end, inside FinSight. | DEC-022 |
| **Review Cycle** | The central aggregate: one monthly review, identified by month and year, that owns its files, data, findings, summary, and audit trail. | FR-006, AP-04 |
| **Guided Review Wizard** | The primary interaction model: an explicit, numbered 8-step sequence ("Step X of 8") through the review. | DEC-024, 07 §5 |
| **Verification** | The mandatory human gate at which extracted data is reviewed, corrected, and approved before any analysis. | FR-026, 07 §12 |
| **VerifiedDataset** | The only input type the Rules Engine consumes; constructible solely upon human approval — making "analyzed-but-unverified" unrepresentable. | 06 §11, DEC (ADC-10) |
| **Deterministic** | Producing identical outputs for identical verified inputs and configuration version, independent of AI, provider, platform, locale, or time. | NFR-021, P-7/P-8 |
| **Deterministic Core / Rules Engine** | The system of record for financial truth; executes rules in a fixed, versioned, reproducible pipeline. | DEC-005, E-02 |
| **Rule** | A deterministic unit that detects an exception or computes a value from verified data, declaring its inputs, parameters, outputs, and minimum history. | 05, FR-069 |
| **Rule Pack** | A capability's set of catalog rules, shipped as a feature with golden-dataset acceptance. | 04 §2.1, 05 |
| **Finding** | A first-class, persistent record of a rule violation/exception: ID, rule reference, severity, period, affected entities, evidence, and source lineage. | FR-069, R-FND-01 |
| **Workspace (vs. Finding)** | Work-in-progress during an active process (e.g., reconciliation matching) that is not yet a finding; residual unresolved items become findings at close/escalation. | 04 §2.3, DEC-026 |
| **Reconciliation** | Matching GED activity against tracking records into exact/probable/unmatched tiers; exceptions surface in the one Findings experience. | E-05, DEC-026 |
| **Readiness (Capability Readiness)** | The pre-analysis assessment of which capabilities are Available / Partially available / Unavailable, and why. | 06 §10, DEC-028, R-RDY-07 |
| **GED** | General Expense Detail — a GL journal-line report of actual spend by department/account/vendor. | DEC-001 |
| **Budget Tracker** | The workbook of planned budget, actuals, and manual reconciliation columns ingested for budget review. | 00 §6 |
| **RAG status** | The deterministic overall review status — **On Track (Green) / Needs Attention (Yellow) / At Risk (Red)** — computed by rule, never by AI. | FR-077, R-RPT-01 |
| **Severity** | A finding's deterministic classification — **Critical / High / Medium / Low** — computed by configurable criteria; shown with icon+shape+label, never color alone. | FR-070, R-FND-02 |
| **Materiality** | The business-owned threshold at which a variance/anomaly becomes a finding; a configurable parameter, never hardcoded. | FR-033, OQ-8, DEC-019 |
| **Cleared (`clrd`)** | The reconciliation status marking a tracker entry as reconciled, per configured semantics. | FR-047, R-REC-03 |
| **Executive / Leadership Summary** | The monthly leadership-facing summary: RAG, budget health, GED status, risks, recommended attention, reconciliation status, and "what changed"; useful with AI off. | FR-076, 07 §16 |
| **Fin** | FinSight's single, optional, user-facing AI companion; the only AI identity users ever see. | DEC-032, 10 §1 |
| **Ask Fin** | The grounded, reactive Q&A experience over the review's verified data and findings, with sources. | DEC-032, 10 §4 |
| **Explain This** | The experience where Fin narrates an existing deterministic finding in plain language; explains, never generates. | FR-091, 10 §5 |
| **Investigation Guidance** | Fin's suggestions of where to look and what evidence to consult — never business/financial-action recommendations. | DEC-033, 10 §6 |
| **AI Optionality** | The property that FinSight is fully functional with no AI configured. | FR-095, P-11 |
| **Consent** | The explicit, informed, revocable, logged human authorization required before any data transmission to an AI provider. | FR-096, DEC-006 |
| **Masking** | Optional irreversible removal of sensitive identifiers before AI transmission; the token map never leaves the app. | FR-098, NFR-016 |
| **Configuration parameter** | A versioned, business-owned value a rule depends on (e.g., `CP-*`); changed by governed configuration, not code. | 05 §4, FR-107, DEC-019 |
| **Golden dataset** | A seeded synthetic month whose expected findings/severities/evidence verify a rule pack; synthetic data only. | NFR-036/038, 04 §2.1 |
| **Cold start** | Early operation with limited history; history-based rules report "insufficient history" rather than firing unreliably. | FR-111, P-4 |
| **Baseline** | An immutable, versioned, SHA-256-manifested, approved snapshot of the spec set; never edited. | WORKFLOW; 12 §8 |
| **ADR (Architecture Decision Record)** | An append-only record of a load-bearing technical decision, with context, decision, consequences, traces, and verification. | 06 §26; 12 §9 |
| **Change Request (CR)** | The governed mechanism to change baselined scope: CR-### + impact analysis; approved edits working specs and re-baselines at the boundary. | 11 §17 |
| **Traceability** | The bidirectional chain requirement → feature → plan → task → code → test → verification, proven by tooling. | NFR-033; traceability skill |
| **Operator / Leader / Administrator / Auditor** | The MVP personas: runs the review / consumes findings & decides / manages configuration / reconstructs a past review. (Single-user MVP; one person may hold several.) | A-09, DEC-008 |
| **Review Health Score** | A **FUTURE**, operational (not financial), deterministic aggregate of review quality; explicitly not Release 1 and distinct from RAG. | DEC-029, 06 §16.3 |
| **What's New** | Change detection (new vendors/accounts/patterns) surfaced separately from findings; **new ≠ wrong**. | FR-078, DEC (§16.2), P-12 |
| **AI-PROPOSED** | The provenance label on any AI-suggested item, carried until a named human ratifies it. | ai-provenance skill; P-2 |

## 11. Amendment Process

- The Constitution is durable and changes rarely. Once first Approved, **every edit requires a Change Request (`CR-###`)**; an amendment row citing no CR is invalid and is flagged by the spec-lint hook and rejected in review.
- **Principle IDs (`P-#`) and glossary terms are stable forever** — superseded by amendment, never renumbered or deleted; the amendment history is the audit trail.
- Amendments are **sponsored by the Project Owner**, consulted with the entire team (and Amerisure stakeholders where a principle touches Amerisure governance), and recorded below with a version bump.
- The seven core principles (P-1…P-7) are the non-negotiable framework core; amendments append or refine FinSight principles (P-8+) and terminology, and do not weaken the core.

**Amendment history** — every row must cite a CR-###.

| Date | CR | Version | Sections changed | Summary | Approved by |
|---|---|---|---|---|---|
| Date not recorded in repository | — | 1.0 | initial | Initial constitution consolidating approved principles, decision rights, quality bars, and glossary (no new scope). | Adopted under project-owner approval |

## 12. Traceability to Existing Decisions

This Constitution invents nothing; it consolidates. Each element traces to its approved source.

| Constitution element | Consolidated from |
|---|---|
| P-1 Spec-first · P-5 Traceable · P-6 Reviewable | DEC-010, NFR-073, NFR-033, NFR-080 |
| P-2 Human accountability for AI work · P-3 Identical gates | DEC-010, NFR-074/075; ai-provenance skill |
| P-4 No silent failure | NFR-062, NFR-055 |
| P-7 Determinism · P-8 Deterministic core / Trust > AI | NFR-021/029/059, DEC-005, NFR-047, AP-01, DEC-022 |
| P-9 Verification before analysis | FR-026, TB-02, DEC-028 |
| P-10 Human decision ownership | 00 §1, FR-059, FR-083 |
| P-11 AI optionality | FR-095, DEC-015 |
| P-12 One findings experience; change ≠ exception | AP-12, F-06-01, FR-041, DEC-026 |
| P-13 Accessibility first | NFR-024–027, DEC-030 |
| P-14 Auditability by design | E-08, NFR-019 |
| P-15 Configuration over hardcoding | AP-07, FR-107, DEC-019 |
| P-16 Monthly Review in a Box | DEC-022, FR-006, AP-04, DEC-024 |
| Decision rights (§4) | 11 §9/§17, 12 §5–§9, DEC-004/006/010/019 |
| Human accountability & AI boundaries (§5–§6) | DEC-005, NFR-047, 10 §2, 11 §10 |
| Quality bars (§7) | NFR-009/010/018/019/021/024–027/029/035/036/037/048/049/050/059/062/074/075/076/078/080; DoD (03 §4, 11 §15) |
| Governance (§8) | WORKFLOW gates; NFR-032; 11; 12 |
| Glossary (§10) | 00–12, DEC-001–034 (per-term authority column) |
| Amendment process (§11) | spec-templates/constitution convention; `/sdd:change` |

**No-conflict statement:** every principle, right, bar, and term above restates an already-approved source; none introduces product scope, features, AI capabilities, technology choices, or new behavior. DEC-024–034 are ratified under the approved baseline, and this Constitution is adopted and in effect under the approved baseline.

---

*End of specs/constitution.md — FinSight's timeless governing document. It formalizes the values, rights, quality bars, and language that already exist across the specification set; it introduces no new scope. Ratify with the DEC-024–034 batch (Gate 1) and adopt at the first baseline (Gate 2); thereafter, amend only via Change Request.*
