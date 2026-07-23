# FinSight — Decision Log

Every material decision, dated, with rationale and open risks. Newest decisions appended at the bottom. No decision is deleted; superseded decisions are marked as such.

**Status legend:** ✅ Decided · ⚠️ Decided with open risk · 🔄 Superseded · ❓ Open question

---

## Decisions

### DEC-001 — Meaning of "GED" ✅
**Date:** 2026-07-09
GED = **General Expense Detail** report: a GL journal-line report of actual spend by department/account/vendor, used to verify actuals against planned budget. The source PDFs never defined the acronym; confirmed by the team.

### DEC-002 — MVP analysis dimensions ✅
**Date:** 2026-07-09
MVP analysis is scoped to **department + GL account + vendor**. The source spec's project/workstream/funding-category dimensions do not exist in the actual data and are deferred until such mappings exist.

### DEC-003 — Delivery form factor ✅
**Date:** 2026-07-09
Desktop application first (Windows **and** macOS), architected for later conversion to a web application. Direction: Electron or Tauri UI shell over a **Python application core** (LangGraph/LangChain for the AI layer). Final stack validated during architecture design.
**Rationale:** AI ecosystem strength, web-tech UI makes web migration cheap, cross-platform.

### DEC-004 — Persistence: SQLite behind a DAL ✅
**Date:** 2026-07-09
"No database" means **no database server/infrastructure dependency**. MVP uses **SQLite (embedded)** accessed exclusively through a Data Access Layer. No component other than the DAL touches storage. DAL owns: audit logging, findings history, report history, configuration, trend data. Future migration (PostgreSQL/SQL Server) = new DAL implementation only, via repository interfaces.

### DEC-005 — Deterministic core / agent boundary ✅
**Date:** 2026-07-09
Pipeline is fixed: **Ingestion → Extraction/Enrichment → User Verification → Deterministic Rules Engine → Findings → Agent/AI Layer → Summaries/Q&A/Recommendations.**
The rules engine is the system of record for financial truth. Agents/LLMs may: classify documents, orchestrate workflow, answer NL questions, generate summaries/narratives/recommendations from rule outputs, narrate what-if scenarios. Agents/LLMs may NOT: decide which rules run, skip rules, modify outcomes, generate findings without rule evidence, or independently compute any financial value.
**Testable requirement:** same approved inputs ⇒ identical findings, statuses, severities, variances and rule outcomes regardless of LLM provider, agent framework, prompt, or model. Only wording/presentation may vary.

### DEC-006 — Consent rule ⚠️
**Date:** 2026-07-09
Users may configure and select any LLM provider. Organization-approved provider lists may be **recommended/preconfigured but are advisory**. No data is transmitted to any LLM without **explicit, informed user consent** — the final runtime authorization gate. Before consent, the app must disclose: provider in use, data to be transmitted, privacy/security implications. Every consent decision is logged (who, when, provider, operation). Consent is revocable in settings.
**⚠️ Open risk:** the original Amerisure spec required that confidential data *never* reach a public AI model (enforcement). This decision replaces enforcement with informed consent + audit. Selecting a non-approved provider will trigger an explicit warning state in the UI. **This decision must be validated with Amerisure security before production.**

### DEC-007 — Provider registry is advisory 🔄 supersedes earlier Q6 position
**Date:** 2026-07-09
Earlier position ("users cannot add arbitrary external providers") is superseded by DEC-006. Registry is admin-manageable, auditable, configurable without code changes — but advisory.

### DEC-008 — User model for MVP ✅
**Date:** 2026-07-09
Single-user desktop app. Logs local OS user identity into all audit records. Full RBAC deferred to web phase; architecture must allow adding roles without major redesign.

### DEC-009 — MVP phase order ✅
**Date:** 2026-07-09
**Phase 1:** Budget Review, GED Analysis, GED Reconciliation, Rules Engine, Audit Logging, Findings Storage.
**Phase 2:** Resource Loading, Contract Mapping, Resource Cost Visibility, Budget-to-Resource Analysis.
**Phase 3:** Invoice Review, SOW Validation, PO Matching, Rate Card Validation.
**Phase 4:** What-If Analysis, Forecasting, Resource Departure Impact, Advanced Executive Analytics.
**Rationale:** build where real data exists first (Phase 1 has samples); invoice review is sample-starved (see DEC-011).

### DEC-010 — Development methodology: spec-driven, AI-native ✅
**Date:** 2026-07-09
Structured markdown specs are the source of truth. Developer-built coding agents generate implementation code from approved specs. Humans remain accountable; all generated code reviewed; unit tests mandatory; deterministic financial logic must be verifiable; no AI-generated code bypasses quality gates.

### DEC-011 — Invoice review: assumed formats ⚠️
**Date:** 2026-07-09
No samples exist yet for invoices, POs, SOWs, rate cards, or contracts. Requirements and extraction models are documented as **"Assumed format — pending business validation."** Design must support PDF, Excel, and structured files. Sanitized/scrambled/synthetic samples to be obtained.

### DEC-012 — Resource loading schema (designed, not sampled) ✅
**Date:** 2026-07-09
No sample file exists; schema designed for extensibility. Initial fields: Resource ID, Resource Name, Resource Type (Employee/Contractor/Vendor Resource), Vendor, Contract/SOW Reference, Department, Account, Bill Rate, Cost Rate, Allocation %, Start Date, End Date, Status (Active/Inactive), Manager/Owner, Fiscal Period, Comments. Must support future forecasting, utilization, replacement scenarios, contract validation.

### DEC-013 — Contract Mappings View ✅
**Date:** 2026-07-09
View exposing relationships: Resources ↔ Contracts/SOWs ↔ Vendors ↔ Departments ↔ Accounts ↔ Budget Allocations. Purpose: which resources are funded by which contracts, vendor associations, charge destinations, billing-vs-contract alignment, budget impact.

### DEC-014 — Resource attrition impact ✅
**Date:** 2026-07-09
Data model supports "resource quits → budget impact" from day one (active/inactive status, period, cost). What-if simulation and backfill forecasting are Phase 4 UI features.

### DEC-015 — AI output visual distinction ✅
**Date:** 2026-07-09
Deterministic outputs and AI/probabilistic outputs must be visually distinct in the UI (color, sections, labeling). AI insights are an **optional feature** requiring a live LLM connection; the application is fully functional with AI disabled.

### DEC-016 — Target hardware ✅
**Date:** 2026-07-09
Standard corporate laptops, 8–16 GB RAM, restricted environments, variable connectivity. Enterprise-hosted LLMs are the primary model for MVP; local model support where practical, later.

### DEC-017 — Budget phasing is monthly ✅
**Date:** 2026-07-09
Planned budget exists at monthly granularity (team-confirmed). Resolves assumption A-04; FR-030 monthly variance analysis stands as written.

### DEC-018 — Real invoice sample received; Phase 3 partially validated ✅
**Date:** 2026-07-09
A real HCL America → Amerisure invoice (4044028319) validated the invoice-review requirement set. Key findings: (1) PO number field can be **blank** on real invoices — missing PO reference becomes a finding, not an assumption violation (FR-051 amended); (2) structure is summary page + line-item annexure with resource, service period, units (MHR/EA), rate, amount — confirming rate/hours/resource validation feasibility (FR-053–055); (3) non-labor line items exist (BEAT tax) — line-item type differentiation added (FR-121); (4) vendor-side project ID/name/segment exist on invoices — vendor project reference capture added (FR-122); (5) service-period-to-invoice-date lag (~6 weeks) confirms cross-month carry-forward need (FR-049); (6) delivery-location subtotals (onshore/offshore) are a billing-category dimension. Still unseen: other vendors' invoice formats, POs, SOWs, rate cards (A-05 remains partially open).

### DEC-019 — Requirements-phase discipline ✅
**Date:** 2026-07-09
Requirements documents define WHAT; parameter values, thresholds, matching semantics, tolerances, and cutoffs are Rules Catalog items and do not block requirements finalization. OQ-5, OQ-7, OQ-8, `clrd` semantics, accrual/reclass treatment, and reconciliation-eligible account scoping are formally reclassified as Rules Catalog inputs.

### DEC-020 — Epic structure ✅
**Date:** 2026-07-10
14 epics agreed (03-epics.md), sliced by business capability with two labeled enablers (E-02 Rules Engine, E-14 Desktop Foundation). Configuration dissolved as a standalone epic — configuration lives with the capability it configures; config-versioning infrastructure lives in E-08. Cross-cutting behaviors (audit behavior, lineage, determinism, testing, AI labeling) are Definition of Done clauses on every story, not epics. Resource+Contract merged; AI split into Platform/Trust vs. Insights/Q&A. First wave: E-14, E-01, E-02, E-08, E-06. WIP limit: 2–3 active epics.

### DEC-021 — Epic document final review ✅ LOCKED
**Date:** 2026-07-10 · **Lock confirmed by team 2026-07-10.** 03-epics.md is the epic baseline; all future epic changes are processed through this decision log, not by restructuring.
E-08 renamed to **Audit & Compliance** (stakeholder clarity; scope unchanged and note added that regulatory compliance beyond audit readiness is out of scope). Final integrity review found and fixed: FR-086 double-assignment documented as deliberate producer/consumer share (E-02 emits, E-08 stores); FR-020 ownership note corrected (extraction template under E-11 on E-01 infrastructure); NFR-053/054 (observability) added to E-14 traces. Review conclusion: no overlapping epics beyond documented shares, no missing epics, no epics that are disguised features, four dependency risks identified with mitigations (first-wave value delay → walking-skeleton slice; E-02 enabler starvation → protected capacity; E-12 external sample gate; E-09 OQ-1 late-invalidation → enforcement-mode fallback design). **Recommendation: lock and proceed to Features.** Lock takes effect on team confirmation.

### DEC-022 — Release-based delivery; "Monthly Review in a Box"; Trust > AI ✅
**Date:** 2026-07-10 · Team-approved
(1) **Release-based delivery mindset:** epics remain the map; delivery is organized as business-value releases cutting across epics. (2) **Release 1 = "Monthly Review in a Box"** — end-to-end monthly review (upload GED + Budget Tracker → verify → budget review, GED analysis, reconciliation → findings → executive summary → export) with full audit trail; the guiding lens for all future scope decisions. Build starts with a walking skeleton. (3) **Trust > AI:** value drivers in priority order — reconciliation automation, exception detection, auditability, executive reporting, invoice validation (when samples arrive); AI enhances, never defines. (4) **E-09 + E-10 merged** into *E-09 AI Assistance (Optional)*, Release 2; E-10 ID retired; MVP AI scope = single approved provider + consent + labeling + citations + audit; masking/multi-provider deferred within the epic; re-split via decision log if OQ-1 expands trust-control scope. (5) **E-13 deferred but visible** on the roadmap; must be re-justified before activation. (6) **A-09/A-10/A-11 remain prioritized internal decisions** — they continue to shape workflow, adoption, and export requirements.

### DEC-023 — Features baseline locked ✅
**Date:** 2026-07-10 · Team-approved
49 features across 9 decomposed epics locked in 04-features.md after per-epic brainstorming with adversarial review. Key rulings now binding: the **rule-pack pattern** (capability epics ship rules as features with golden-dataset acceptance; E-02 owns execution); **enabler-feature criteria** (legitimate only when another plan or the DoD names the dependency); the **workspace/finding boundary principle** (work-in-progress vs. what survives the workflow — applies to E-05 now, E-12 later); FR-041 split (tagging in extraction, consumption in rules); missing-entry detection kept in R1 where OQ-5 permits a reference-based baseline; F-03-04 run-rate projection demoted to R2 under the MVP lens; E-05 compressed 5→3 with the previously missing Automated Matching Rule Pack added; E-01/E-02 release tags retrofitted (historical import R2, replacement-rerun R2, cold-start honesty R1, replay R1). E-09/E-11/E-12/E-13 deliberately undecomposed (just-in-time). Document numbering: 05-rules-catalog, 06-architecture, 07-ux-design, 08-ai-and-agents, 10-dev-methodology; 09 remains this log.

---

## Proposed decisions — pending team ratification 🔶

**Status legend (proposed set):** 🔶 **Proposed** — AI-drafted (`AI-PROPOSED` per the ai-provenance discipline), emerged from the architecture (06), UX (07), UI (08), and AI & agents (10) phases; **awaiting team ratification** before becoming ✅ Decided. These entries do not alter any DEC-001–023 decision and introduce no capability beyond approved scope. On ratification, change 🔶 → ✅ and record the approval date.

### DEC-024 — Guided Review Wizard as the primary interaction model 🔶
**Date:** 2026-07-16 · Proposed (AI-PROPOSED) · from 07-ux-design.md §5/§7
The monthly review is delivered as an explicit, numbered **8-step wizard** (Create → Upload → Validate → Verify → Analyze → Findings → Summary → Complete) with a persistent "Step X of 8" indicator, in the paradigm of guided tax/audit preparation — not a dashboard or menu of modules.
**Rationale:** serves "Monthly Review in a Box" (DEC-022) and low-training adoption (NFR-068); makes wayfinding (where am I / what's done / what's next) structural.
**Consequences:** *(+)* orientation, confidence, guided flow. *(−)* a linear frame can feel rigid for power users — mitigated by read-only revisiting and resume. Adds a load-bearing stepper that must remain accessible.
**Alternatives considered:** dashboard/hub navigation (rejected — generic-SaaS feel, weak wayfinding); free-form module navigation (rejected — contradicts guided-review identity).
**Traces to:** FR-006, FR-081; NFR-068; F-01-01; C-02 (06 §6.2 cycle state model); 07 §5/§7; 08 §11 (stepper). Consistent with DEC-022.

### DEC-025 — Recent Reviews as a first-class landing experience 🔶
**Date:** 2026-07-16 · Proposed (AI-PROPOSED) · from 07-ux-design.md §9
The Home screen leads with a prominent **Recent Reviews** list (status + "Step X of 8" for in-progress) with one-click resume/open and review-history access, alongside — not behind — Create New Review.
**Rationale:** users revisit prior reviews frequently (comparison, audit, re-reading summaries, resuming); a create-only landing under-serves the dominant return-user journey.
**Consequences:** *(+)* fast resume/revisit; reinforces the review-cycle mental model. *(−)* Home must render review status/step reliably from persisted state (leans on NFR-006).
**Alternatives considered:** create-first welcome (rejected — ignores revisit behavior); a separate History destination only (rejected — buries the most common action).
**Traces to:** F-01-01; NFR-006; C-01/C-02; 07 §9 (S-01); 08 §8.

### DEC-026 — Reconciliation integrated into the single Findings Experience 🔶
**Date:** 2026-07-16 · Proposed (AI-PROPOSED) · from 07-ux-design.md §14.1
There is **no separate Reconciliation destination**. Reconciliation *findings* render in the one Findings Hub; the reconciliation *matching work* is a focused Operator sub-task opened from within Step 6. Upholds "One Findings Experience" while honoring the workspace/finding boundary.
**Rationale:** separates work-in-progress (matching) from surviving exceptions (findings) without forking the findings system (AP-12, F-06-01, 04 §2.3).
**Consequences:** *(+)* coherent findings model; no per-capability fork. *(−)* the "one record, two presentations, one state machine" contract must be enforced or statuses could diverge (a trust defect).
**Alternatives considered:** reconciliation as a top-level workspace (rejected — reads as a second findings system); folding matching into the inbox (rejected — floods the Leader with work-in-progress).
**Traces to:** FR-044–050; F-05-02; R-REC-01..05; C-10 → C-09a; 07 §14.1; 08 §12. Consistent with DEC-023 (workspace/finding boundary).

### DEC-027 — Verification trust ritual (gate + Review Complete + double-confirmation) 🔶
**Date:** 2026-07-16 · Proposed (AI-PROPOSED) · from 07-ux-design.md §11/§12
Verification (Step 4) adopts three trust patterns: the mandatory **"I have reviewed this information"** gate before analysis; a **"Review Complete"** confirmation summarizing what was verified before analysis begins; and a **double-confirmation** when a user continues with an incomplete/subset readiness.
**Rationale:** makes Trust > AI tangible — the user feels they reviewed and approved what will be analyzed; prevents accidental incomplete reviews and later doubt (FR-026, NFR-062).
**Consequences:** *(+)* confidence; stronger audit posture. *(−)* added confirmations risk click-through fatigue — mitigated by reserving hard confirmations for verification and continue-anyway only.
**Alternatives considered:** single silent checkbox (rejected — under-weights the key trust moment); no continue-anyway guard (rejected — permits silent incomplete reviews).
**Traces to:** FR-026, FR-029; NFR-062, NFR-069; F-01-09; C-06 (TB-02); 07 §11 (S-05)/§12 (S-07/S-07b); 08 §13. Ratifies the `PROPOSED` UX patterns (Review Complete, double-confirmation).

### DEC-028 — Capability Readiness Validation as an explicit user-facing step 🔶
**Date:** 2026-07-16 · Proposed (AI-PROPOSED) · from 06-architecture.md §10 / 07-ux-design.md §11
Readiness is an explicit review step (Step 3, "Validate Review") reporting, per capability, **Available / Partially available / Unavailable with a named reason**, and **gates capabilities, not the whole review** (users may proceed on the available subset).
**Rationale:** users upload only what they have; the system must never assume every document exists or fail silently (FR-004/007/021–025/081/111).
**Consequences:** *(+)* transparency; no silent failure; review proceeds on partial data. *(−)* per-capability prerequisites (`CP-READINESS-REQUIREMENTS`) must be maintained.
**Alternatives considered:** analyze-whatever-exists silently (rejected — mystery, distrust); block until all docs present (rejected — contradicts "upload only what you have").
**Traces to:** FR-004/007/021–025/081/111; C-05; R-RDY-07 (05 §12); 06 §10 (AA-07); 07 §11 (S-04). Ratifies the `PROPOSED` readiness model.

### DEC-029 — Review Health Score is FUTURE-only, operational (not financial) 🔶
**Date:** 2026-07-16 · Proposed (AI-PROPOSED) · from 06-architecture.md §16.3 / 07-ux-design.md §18
The Review Health Score is **deferred (FUTURE-only), operational/governance-oriented (explicitly not a financial score), deterministic, and requires future validation** of its signals/weighting before build. It is **not Release 1** and appears in no R1 wizard step.
**Rationale:** valuable but non-essential; a working, trustworthy monthly review needs no score; prevents scope creep and confusion with the financial RAG status (FR-077).
**Consequences:** *(+)* protects R1 focus; clean separation from financial status. *(−)* a visible-but-inactive concept can invite premature requests — mitigated by the binding deferral statement.
**Alternatives considered:** ship a basic score in R1 (rejected — unvalidated signals, mistrust risk); drop entirely (rejected — the seam/roadmap value is real).
**Traces to:** FR-077 (distinct from RAG); XP-05, C-13 (06 §16.3); 07 §18 (S-16); 08 §18; E-13 posture. Consistent with the deterministic core (DEC-005).

### DEC-030 — UI Design System foundations 🔶
**Date:** 2026-07-16 · Proposed (AI-PROPOSED) · from 08-ui-design-system.md
The UI adopts: **Light mode as the default** (Dark, High-Contrast, System-auto exist but are never default); a **system-font typography stack** (offline-safe, no external egress); **meaning never carried by color alone** (severity/RAG/status = icon + shape + label + color); **AI content visually subordinate, labeled, and attributed** (no purple/gradient/glow "AI" aesthetic). Concrete brand token **values are `PROPOSED` pending Amerisure brand confirmation**; the rules/semantics are firm.
**Rationale:** realizes NFR-024/025/026/027/049/065 and the "premium, calm, finance-grade, not-an-AI-product" brief while keeping the deterministic/AI trust posture visible.
**Consequences:** *(+)* accessible-by-default; professional identity; brand-swap is a token change. *(−)* final palette/type blocked on Amerisure brand input (tracked `PROPOSED`); system fonts trade bespoke typography for reliability/offline safety.
**Alternatives considered:** dark-mode-first / AI-styled theme (rejected — brief forbids); bundled custom font (deferred — external-egress/offline concerns).
**Traces to:** NFR-024/025/026/027/049/065; FR-070/077/080/016/027/120; C-01; 08 (all). Consistent with DEC-015 (AI visually distinct).

### DEC-031 — Document numbering correction 🔶 supersedes the numbering note in DEC-023
**Date:** 2026-07-16 · Proposed (AI-PROPOSED)
`08` is **08-ui-design-system.md**; **AI & Agents is `10-ai-and-agents.md`** (created); Dev Methodology moves to `11` (or as the team prefers). This **supersedes the document numbering stated in DEC-023** (which reserved 08 for "ai-and-agents").
**Rationale:** a UI Design System phase was inserted after UX; the sequence must stay consistent and greppable.
**Consequences:** *(+)* consistent numbering. *(−)* companion-document reference lists in already-written docs need a light update (07 still lists "08-ai-and-agents" as a companion — a stale reference to correct on ratification).
**Alternatives considered:** give UI a non-08 number (rejected — 08 already used); leave DEC-023 numbering (rejected — now inaccurate).
**Traces to:** cross-references in 04/06/07/08/10 companion-document lists. Supersedes DEC-023 (numbering note only; DEC-023's feature baseline is unchanged).

---

### DEC-032 — Fin as the single AI persona 🔶
**Date:** 2026-07-16 · Proposed (AI-PROPOSED) · from 10-ai-and-agents.md §1/§4/§11
FinSight exposes a **single user-facing AI identity, "Fin"**. Users interact through one consistent companion via **Ask Fin**, **Explain This**, and **Investigation Guidance**. Users never see multiple agents, agent names, copilots, bots, assistants, or orchestrators. Any internal handlers (Explanation, Questions, Summary, Comparison, Investigation) are implementation details, invisible to users.
**Rationale:** aligns with Trust > AI; reduces complexity; improves user understanding; supports the Guided Review Wizard philosophy (DEC-024); creates a memorable, coherent FinSight identity rather than a generic AI tool.
**Consequences:** *(+)* one personality; one entry point; internal implementation stays invisible; consistent voice and guardrails across all AI surfaces. *(−)* all AI experiences must share one grounding/citation/refusal contract and one visual treatment; a single identity must be governed carefully so it never drifts toward a general chatbot.
**Alternatives considered:** multiple named agents / a "copilot" or "bot" surface (rejected — product-identity confusion, undermines Trust > AI, contradicts the not-a-chatbot vision); no named identity, generic "AI panel" (rejected — less memorable, weaker trust relationship).
**Traces to:** NFR-049 (AI visibly distinct); FR-091/100 (Explain This, Q&A); E-09; C-15 (AI Assistance & Grounding); 07 §15/S-20; 08 §5.5/§20; 10 §1/§4/§11. Consistent with DEC-005 (AI explains, never decides), DEC-015 (AI optional/distinct), DEC-024 (guided wizard). Release 2; production-gated on OQ-1/OQ-3.

### DEC-033 — Investigation guidance only (no business/financial-action recommendations) 🔶 refines FR-093
**Date:** 2026-07-16 · Proposed (AI-PROPOSED) · from 10-ai-and-agents.md §6
AI-generated guidance is limited to **investigation guidance**. Fin may suggest areas to review, supporting evidence to gather, relevant historical comparisons, supporting documentation, and follow-up questions a reviewer might ask. Fin may **not** suggest business decisions, financial actions, spending changes, approvals, or rejections. *Allowed:* "Consider reviewing contract amendments and prior-month spending patterns." *Not allowed:* "You should reduce spending with this vendor." This **narrows FR-093** ("AI recommendations from deterministic outputs") to investigation-only; the deterministic "Recommended Actions" in the leadership summary (FR-076) are rule outputs, not Fin outputs, and are unaffected.
**Rationale:** preserves human ownership of financial decisions and maintains Trust > AI; FinSight recommends understanding, never actions (00 §1, FR-059 "recommends, never acts").
**Consequences:** *(+)* users remain the decision-makers; AI supports understanding, not action; clearer, safer AI boundary. *(−)* FR-093's broader "recommendation" latitude is deliberately not exercised — a scope reduction to record so a future request to broaden it goes through change control.
**Alternatives considered:** allow FR-093's full "recommended-action" latitude (rejected — risks AI appearing to make financial decisions, eroding trust and human ownership); forbid all AI guidance (rejected — investigation guidance is genuinely useful and safely grounded).
**Traces to:** FR-093 (narrowed), FR-094/099; NFR-050; E-09; C-15; 07 §15/§21; 10 §6. Consistent with DEC-005; upholds 00 §1 human-decision ownership. Release 2.

### DEC-034 — No autonomous agents in the AI layer 🔶
**Date:** 2026-07-16 · Proposed (AI-PROPOSED) · from 10-ai-and-agents.md §10/§11/§18
FinSight does **not require autonomous agents**. All approved AI capabilities are implemented as **grounded, stateless assistance over deterministic outputs** — a single retrieval-grounded call per turn — delivered through Fin. Fin may internally use simple handlers (Explanation, Questions, Summary, Comparison, Investigation) that are implementation details, not autonomous agent systems, and may collapse into one parametrized handler.
**Rationale:** agent architectures add complexity, confidentiality exposure (more calls/data movement), cost, and non-determinism without measurable value for approved FinSight use cases; every admitted capability is a single grounded transformation. Simplest-wins; Trust > AI.
**Consequences:** *(+)* the deterministic core remains dominant; AI stays explainability-focused; architecture stays simple; users experience only Fin. *(−)* future capabilities that genuinely need multi-step autonomy would require a new decision and re-evaluation of the confidentiality/governance posture.
**Alternatives considered:** multi-agent autonomous orchestration of the AI layer (rejected — non-determinism, attack surface, cost, complexity); agent-orchestrated review pipeline (rejected — orchestration is deterministic per C-02/AA-06; DEC-005 permits but does not require agents).
**Traces to:** DEC-005 (agents permitted, not required); NFR-047 (deterministic/AI boundary), NFR-004/063; E-09; C-15 (`FindingsQueryPort`, TB-03), C-02/AA-06 (deterministic orchestration); 10 §10/§11/§18. Release 2.
**Supersede note:** subordinates the directional "LangGraph/LangChain for the AI layer" mention in DEC-003 — no agent framework is adopted, and the concrete AI-library/provider selection is deferred to the AI-provider ADR (ADC-03). DEC-003's desktop/Python-core/SQLite direction is unaffected.

---

## Open questions ❓

**Classification (per DEC-019):** RB = Requirements blocker · RC = Rules Catalog · AR = Architecture · FP = Future phase

| # | Question | Owner | Class | Status |
|---|----------|-------|-------|--------|
| OQ-1 | Amerisure security validation of the consent-over-enforcement model (DEC-006) | Aditi → Amerisure security | AR / production gate | Open — does not block requirements |
| OQ-2 | Obtain samples: other vendors' invoices, POs, SOWs, rate cards, contracts | Aditi → stakeholders | RC / Phase 3 design | Partially closed (DEC-018: one real invoice received) |
| OQ-3 | Confirm an Amerisure-approved managed LLM endpoint exists and its access mechanics | Aditi → stakeholders | AR | Open |
| OQ-4 | Obtain or confirm absence of project/workstream/funding-category mapping files (affects DEC-002 scope) | Aditi → stakeholders | FP (note: vendor project IDs now available on invoices — FR-122) | Open |
| OQ-5 | Expected GED "monthly patterns" baseline: history-derived or finance-maintained expected-entries reference? | Aditi → finance | RC | Open — reclassified per DEC-019 |
| OQ-6 | Who operates FinSight month-to-month — leader, delegate/analyst, or both? | Team (internal) | Requirements assumption (A-09: two personas) | Open — does not block; answerable internally |
| OQ-7 | Official monthly cutoff/calendar for GED postings | Aditi → finance | RC | Open — reclassified per DEC-019 |
| OQ-8 | Materiality thresholds per account/vendor (% / $) | Aditi → finance | RC | Open — reclassified per DEC-019 |
| OQ-9 | ~~Budget phasing: monthly, quarterly, or annual?~~ | Finance | — | **Closed 2026-07-09: monthly (DEC-017)** |
