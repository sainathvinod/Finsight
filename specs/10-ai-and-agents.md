# FinSight — AI & Agents Design

**Document:** 10-ai-and-agents.md
**Status:** Approved
**Date:** 2026-07-16
**Scope:** Where AI genuinely adds value in FinSight, where it must not exist, whether agents are required, and — if so — the simplest architecture that satisfies the product vision. Covers the user-facing AI experience (Fin: Ask Fin, Explain This, Investigation Guidance), the trust/confidentiality model, an internal-agent evaluation, the deterministic-vs-AI responsibility matrix, governance, risks, and full traceability.
**Governing methodology:** Spec-driven development (DEC-010, NFR-073). **Derived artifact** — every capability below is justified by an approved source item or it is rejected. The burden of proof is on the capability.
**Sources of truth:** 00-project-understanding.md · 01-functional-requirements.md · 02-non-functional-requirements.md · 03-epics.md · 04-features.md · 05-rules-catalog.md · 06-architecture.md · 07-ux-design.md · 08-ui-design-system.md · 09-decision-log.md
**Companion / downstream:** 06-architecture.md (C-15 AI Assistance & Grounding, C-16 Consent & Provider Governance, `FindingsQueryPort`, XP-03) · 07-ux-design.md (S-19 consent, S-20 Ask/Q&A, §15 Explain This) · 08-ui-design-system.md (§5.5 AI container, §20 visual trust)
**Provenance:** AI-drafted for human review and approved by the project owner. New product concepts not named by a specific FR — the **Fin persona**, the **Ask Fin** surface wording, and the **narrowing of FR-093 to investigation-only guidance** — were recorded as decision-log entries (DEC-032–034) and accepted; they introduce no capability beyond approved scope. This document is Approved in the current baseline.
**Release reality (binding):** the entire AI layer is **Epic E-09 (AI Assistance — Optional), Release 2**, with **OQ-1** (Amerisure security validation of the consent model, DEC-006) and **OQ-3** (approved managed endpoint) resolved under the approved baseline. The Release-1 product is fully functional with **no AI configured** (FR-095). This document designs the R2 layer; it changes nothing in R1.

---

## 1. AI Vision

**FinSight is not an AI application. It is a guided monthly financial review assistant.** AI is a thin, optional, clearly-labeled layer whose only job is to help a human **understand** deterministic outputs faster and communicate them better. It never produces financial truth, never decides, and can be switched off with zero loss of function (FR-095, DEC-015).

The vision in one sentence: **the rules engine says what is true; Fin helps you understand it.** Everything else follows from that. The deterministic core (05-rules-catalog, C-07/C-09a) is and remains the source of truth (DEC-005, AP-01). AI is a translator and a guide, not a computer of values or a maker of decisions (AP-02, NFR-047).

Users meet **one** calm companion — **Fin** — that understands *their* review. They never meet a chatbot, a copilot, a bot, or a fleet of named agents. Fin is grounded, cited, optional, and reactive: it answers when asked and is silent otherwise.

## 2. Guiding Principles (locked design constraints)

**AI MAY:** explain · summarize · clarify · answer grounded questions · guide investigations · improve understanding · improve usability · translate technical findings into business language.

**AI MAY NOT:** create findings · approve reviews · override rules · modify source data · alter verified data · make business decisions · create financial scores · contact vendors · bypass verification · perform deterministic calculations · silently take actions · create or suppress exceptions.

These are not aspirations; they are enforced by the architecture, and each traces to approved scope:

| Constraint | Enforced by | Traces to |
|---|---|---|
| AI never computes a financial value, finding, severity, RAG, or score | AI reaches the core only via read-only `FindingsQueryPort`; it is never wired to `FindingsCommandPort` — "AI writes a finding" has no wired code path, enforced by construction + a mandatory CI architecture-fitness test (not by the compiler; Python — ADR-001/002) | DEC-005, NFR-047, TB-03, 05 Principle 2, R-FND-01/02, R-RPT-01 |
| AI never alters source or verified data | AI is downstream of verification; no write path to intake/extraction/verified store | FR-026, TB-01/TB-02, AP-03/AP-05 |
| AI never acts (approve/reject/pay/contact vendor) | FinSight takes no financial action at all; AI has no action surface | 00 §1, FR-059/083 |
| AI is grounded, cited, and declines the unsupported | grounding + citation + refusal policy (§4, §7) | FR-094/099, NFR-050 |
| AI is optional and removable | R1 complete with AI unconfigured; standing regression | FR-095, NFR-048, DEC-015 |
| AI is visibly distinct and attributed | UI "assistant" container, labeled + provider/model | FR-080, NFR-049, UI §5.5 |
| AI is reactive, never proactive | §9 rejects proactive behavior | product philosophy; UXP-07 |
| No unconsented egress; minimum data | consent gate + single egress chokepoint + minimization | FR-096, NFR-011/015, TB-04 |

**Deterministic-first is the default posture:** before proposing any AI capability, the question is *"can this be deterministic (a rule, a view, a static help page)?"* If yes, it stays deterministic. AI is proposed only where the value is genuinely *understanding/communication*, not computation.

## 3. Trust & Confidentiality Model

FinSight processes highly sensitive financial data on a single user's machine (DEC-008/016). Confidentiality is prioritized over convenience. The model, from strongest guarantee outward:

**3.1 The strongest guarantee is that AI is optional.** The most privacy-preserving configuration is **AI off** — and it is fully functional (FR-095). No confidential data can leak to a model that is never called. This is the baseline, not a fallback.

**3.2 When AI is on, it is retrieval-grounded, not data-dumped.** Fin never sees "the files." A turn works as: (1) the user asks; (2) a **deterministic retrieval step** selects only the specific verified data points, findings, and evidence relevant to the question (from the local store via `FindingsQueryPort`); (3) **only those minimal, already-verified snippets** form the model context; (4) the model composes a grounded, cited answer. Whole files, unfiltered datasets, and raw source are never transmitted (NFR-015 data minimization; FR-094 grounding). Retrieval is the confidentiality control, not just a quality control.

**3.3 Egress is consented, minimized, maskable, and single-pathed.**
- **Consent is the final runtime gate** (FR-096, DEC-006, S-19): before any transmission, C-16 discloses the provider, the exact data to be sent, whether masking is active, and the implications; consent is explicit, revocable, and logged (FR-088, NFR-014). Revocation stops future transmissions immediately.
- **One outbound path only** (TB-04, NFR-011): the consented provider, and nowhere else — no telemetry, no analytics, no update channel carries user data.
- **Masking/tokenization** (FR-098, NFR-016, R2): sensitive identifiers (vendor/resource names, amounts, invoice numbers) can be irreversibly masked before transmission; the token map never leaves the app.

**3.4 Provider abstraction and deployment options (confidentiality-ranked).** Fin is provider-agnostic behind an adapter (XP-03, FR-104, NFR-046). In descending confidentiality:
1. **Local / on-device model** — no egress at all; the strongest privacy posture. Recommended target where practical on corporate hardware (DEC-016 "local model support where practical, later"); constrained by 8–16 GB laptops (A-08/DEC-016), so treated as a **future option**, not the MVP default.
2. **Amerisure-approved, enterprise-hosted / on-prem endpoint** — the **primary production path** (A-06, DEC-016), inside Amerisure's trust boundary; consent-gated but low external exposure. **OQ-3 resolved under the approved baseline.**
3. **Other consented external providers** — permitted but **advisory-listed**; selecting a non-recommended provider triggers an explicit warning before consent (FR-097, DEC-006/007). Retail/public consumer AI is discouraged for confidential data and never a default.

**3.5 Auditability and explainability are part of trust.** Every AI interaction is logged (provider, model + version, data transmitted, masking applied, consent reference, prompt category, output — FR-087, NFR-023/052); every answer is cited to its evidence (FR-099, §7); model changes are governed events with a validation pass (NFR-051). A reviewer can reconstruct, for any historical AI answer, *what was sent, to whom, under which consent, and what came back* in under a minute (E-09 success signal).

**3.6 Challenge to convenience.** We explicitly reject the convenient defaults common to AI products: no "send everything for better answers," no background summarization without consent, no cloud logging of prompts outside the audited local store, no always-on assistant. Convenience never overrides the consent gate or minimization.

## 4. Ask Fin Experience

**Ask Fin** is the primary AI experience (S-20). It is a **reactive, grounded Q&A companion** over the current review's verified data and findings — not a general chatbot.

**4.1 Opening state (locked wording).** When the user opens Ask Fin, display exactly:

> 👋 Hi, I'm Fin.
>
> I've got {Month Year} loaded and ready to discuss.
>
> Ask me anything about the review, findings, budgets, reconciliation, or changes from previous months.
>
> ⚠️ Every answer is grounded in the information available for this review and includes supporting sources. Be sure to review the evidence before making important business decisions. ⚠️

*(`{Month Year}` is the active review cycle, e.g., "July 2026". The warning is persistent, not a one-time dismissable notice.)*

**4.2 Default suggested questions (one-click prompts, S-20 / FR-101 question library):**

- ☐ Why was this finding created?
- ☐ What changed since last month?
- ☐ Show the highest-risk items.
- ☐ Explain reconciliation issues.
- ☐ Summarize this review for leadership.
- ☐ What should I investigate next?

These map to deterministic capabilities where possible (e.g., "highest-risk items" is a deterministic findings sort — FR-102/FR-082; "what changed" is deterministic MoM — R-HST-02) with Fin adding plain-language narration; the deterministic answer exists even with AI off.

**4.3 Ask Fin rules (grounding — FR-094, NFR-050).** Fin may answer **only** from: verified data · approved findings · approved summaries · traceable evidence · approved historical comparisons · approved review artifacts. Fin must **never** answer from: unsupported assumptions · external internet information · model training/world knowledge · fabricated conclusions · unverified review information. **If evidence does not exist, Fin states explicitly that evidence was not found** — it does not guess, extrapolate, or fill gaps (the single most important trust behavior).

**4.4 Reactive only.** Ask Fin opens only when the user opens it; it answers only when asked (§9). No proactive messages.

**4.5 Availability & fallback.** Ask Fin is R2 and requires a configured, consented provider. When AI is off/unavailable, the surface explains AI is optional and points to the **deterministic question library and search** (FR-101/102) — every canonical question has a deterministic answer path, so the review is never blocked (NFR-063).

*Traceability:* FR-094/095/099/100/101/102, NFR-004/049/050/063 · E-09 · C-15/C-16 · S-20 · UI §5.5/§20 · DEC-005/006/015.

## 5. Explain This Experience

**Explain This** helps a user understand a **deterministic finding** (07 §15; FR-091). It is the second primary AI experience and the clearest expression of "AI translates, it does not decide."

**Explain This MAY:** explain why the finding exists · which rule triggered · the threshold comparison · the supporting evidence · the source data.
**Explain This MAY NOT:** create findings · change findings · override findings · create new conclusions.

**The division is absolute:** the rules engine (R-FND-01/02, C-09a) *creates* the finding and *owns* its severity and evidence; Fin *narrates* that existing record in plain, business-appropriate language. Every element Explain This states must already exist in the finding's deterministic evidence — Fin adds wording, not facts (FR-094).

**Deterministic-first, AI-optional (as in UX §15.2):** the deterministic explanation — rule, inputs, threshold comparison, source rows — is **available with AI off** (it is just the finding's evidence, rendered). The AI narration is an optional, labeled layer on top. With AI unavailable, Explain This still shows the full deterministic explanation.

*Traceability:* FR-091/094/095/099, NFR-050/067 · F-06-02 · R-FND-01/02, R-RPT-01 · C-09a/C-09b (+C-15) · UX §15 · UI §20 · DEC-005/015.

## 6. Investigation Guidance Experience

Users frequently ask *"What should I investigate next?"* Fin may help a reviewer decide **where to look**, never **what to do about money**.

**Fin MAY suggest:** areas to review · additional evidence to gather · relevant historical comparisons · supporting documentation to consult · questions a reviewer might want to ask.
**Fin MAY NOT recommend:** business actions · approvals · rejections · spending changes · financial decisions.

- **Allowed:** *"Consider reviewing contract amendments and prior-month spending patterns for this vendor."*
- **Not allowed:** *"You should reduce spending with this vendor."*

**Scope note (narrowing of FR-093, accepted in the approved baseline — DEC-033):** FR-093 permits "AI recommendation" suggestions from deterministic outputs. This document **narrows** that to *investigation guidance only* — suggestions about **where to look and what evidence to consult**, grounded in existing findings/data — and explicitly excludes business/financial-action recommendations, which remain human (00 §1, FR-059 "recommends, never acts"). The deterministic "Recommended Actions" in the leadership summary (FR-076) are **rule outputs**, not Fin outputs, and are unaffected. *Logged as decision-log entry DEC-033.*

Investigation guidance is **reactive** (the user asks) and **grounded** (suggestions reference the review's actual findings/history, cited). It never becomes proactive nudging (§9).

*Traceability:* FR-093 (narrowed), FR-094/099 · E-09 · C-15 · UX §15/§21 · DEC-005.

## 7. Sources & Evidence Model

Every Ask Fin answer, Explain This narration, and Investigation suggestion **must** carry its provenance. This is the mechanism that makes "Trust > AI" real in the AI layer.

- **"Sources Used"** appears with every response — the finding IDs and/or verified data points the answer is grounded in (FR-099).
- **Show Sources** expands the citation list; **View Evidence** opens the underlying finding/evidence/source rows (one interaction to the deterministic truth — NFR-067, UXP-04).
- The user can always answer **"Where did this answer come from?"** — every claim is checkable in one click.
- **No citation ⇒ no claim.** If Fin cannot ground a statement in retrievable evidence, it does not make the statement; it says evidence was not found (§4.3).
- **Visual treatment:** citations render inside the labeled AI container (UI §5.5), visually distinct from deterministic content, with provider/model attribution (NFR-049, FR-080).

*Traceability:* FR-099, NFR-050/067/049 · C-09a (`FindingsQueryPort`) · UI §20 · UX §15.

## 8. Additional Recommended AI Capabilities

Each candidate is admitted **only** with traceability; otherwise rejected (§9). All are R2, optional, grounded, cited.

| ID | Capability | What it does (understanding/communication only) | Justified by |
|---|---|---|---|
| **AIC-01** | Finding explanation (Explain This) | Narrates an existing finding in plain language | FR-091; §5 |
| **AIC-02** | Grounded Q&A (Ask Fin) | Answers questions over verified data/findings, cited | FR-100; §4 |
| **AIC-03** | Leadership-language translation | Rewrites technical findings/summary into leadership-appropriate narrative | FR-092; FR-076; NFR-049 |
| **AIC-04** | Monthly-summary narrative | Composes the narrative portions of the deterministic summary | FR-092; F-07-01 (AI slots) |
| **AIC-05** | "What changed" narration | Narrates the deterministic MoM/comparison result | FR-078/092; R-HST-02; §17 UX |
| **AIC-06** | Investigation guidance | Suggests where to look next (not what to decide) | FR-093 (narrowed); §6 |
| **AIC-07** | Question library assistance | Turns canonical questions into grounded answers; falls back to deterministic views | FR-101/102 |
| **AIC-08** | Process/onboarding explanation *(modest)* | Answers "how does FinSight decide severity / what is reconciliation?" grounded in the rules-catalog configuration and help content — low confidentiality (app config, not financial data) | NFR-068 (low training), NFR-034; FR-091; S-21 |

**Outside-the-box, admitted with care:**
- **AIC-08 (onboarding/process explanation)** materially lowers training cost (NFR-068) and touches **no confidential financial data** (it explains the *system*, grounded in configuration and help content) — so it is low-egress and high-value. Preferred implementation is **deterministic help content (S-21)** first, with Fin answering process questions grounded in that content and the rules-catalog config.
- **Accessibility benefit (noted, not a new capability):** for screen-reader/keyboard users, asking Fin can be an efficient alternative to navigating dense tables (NFR-026). This is a *usability benefit of AIC-02*, not a separate capability, and must never become the *only* path (deterministic search FR-102 always remains).

**Deliberately not admitted as "additional" because they are already deterministic (kept out of AI):** highest-risk sort (FR-082/102), MoM computation (R-HST-02), severity/RAG (R-FND-02/R-RPT-01), reconciliation matching (R-REC-*), anomaly detection (R-GED-06). AI may *narrate* these; it never *computes* them.

## 9. Rejected AI Concepts

Rejected because they violate a locked constraint (§2), duplicate a deterministic capability, or add risk without proportionate understanding value. The burden of proof was not met.

| ID | Rejected concept | Why rejected |
|---|---|---|
| **RJ-01** | AI that creates/edits/suppresses findings or exceptions | Violates DEC-005/NFR-047; findings are deterministic (R-FND-01) |
| **RJ-02** | AI-computed severity, RAG status, variances, or any financial value | Violates AP-01/DEC-005; these are rules (R-FND-02, R-RPT-01, R-BUD-01) |
| **RJ-03** | AI-generated Review Health Score (or any AI score) | "AI may not create financial scores" (§2); the score is deterministic + FUTURE (06 §16.3, DEC-029 proposal) |
| **RJ-04** | AI auto-correction of extracted/verified data | Violates FR-026/verification and "may not alter data" (§2, TB-01/02) |
| **RJ-05** | AI approving reviews / routing / acting on invoices / contacting vendors | FinSight takes no action (00 §1, FR-083); "may not act/approve" |
| **RJ-06** | Proactive AI (popups, unsolicited nudges, auto-start, continuous suggestions) | Explicitly rejected (§ Proactive); human initiation required |
| **RJ-07** | General-purpose chatbot / world-knowledge answers / internet retrieval | Violates grounding (FR-094, §4.3); confidentiality and trust risk |
| **RJ-08** | Multiple user-facing personas / named agents / "copilot"/"bot" branding | One personality: Fin (§ user-facing); avoids product-identity confusion |
| **RJ-09** | Autonomous multi-agent orchestration of the review pipeline | Non-determinism, cost, attack surface; orchestration is deterministic (C-02, AA-06); simplest-wins |
| **RJ-10** | AI that selects/skips/reorders rules or tunes thresholds silently | Violates DEC-005/NFR-047; config changes are human + governed (FR-107, R-FND-05) |
| **RJ-11** | Sending whole files/datasets to a provider "for better answers" | Violates data minimization (NFR-015) and confidentiality posture (§3) |
| **RJ-12** | Persistent cloud memory of prompts/data outside the audited local store | Violates NFR-011/052; retention is local, audited, at-rest-protected |

## 10. Internal Agent Evaluation

**Question asked honestly: does FinSight need agents at all?** An "agent" here means an autonomous, multi-step, tool-using, self-directing loop. Evaluating each candidate against three tests — *(a) does it need multi-step autonomy? (b) does it need to choose/act on its own? (c) is a single grounded call insufficient?*:

| Capability | Multi-step autonomy? | Self-direction/action? | Single grounded call enough? | Verdict |
|---|---|---|---|---|
| Explain This (AIC-01) | No | No | Yes (finding evidence in → narration out) | **No agent** |
| Ask Fin Q&A (AIC-02) | No (retrieve → answer) | No | Yes | **No agent** |
| Leadership narrative / summary (AIC-03/04) | No | No | Yes (deterministic summary in → prose out) | **No agent** |
| What-changed narration (AIC-05) | No | No | Yes (deterministic MoM in → prose out) | **No agent** |
| Investigation guidance (AIC-06) | No | No (suggests, never acts) | Yes | **No agent** |
| Onboarding/process (AIC-08) | No | No | Yes | **No agent** |

**Finding: FinSight needs no autonomous agents.** Every admitted capability is a **single, stateless, grounded transformation**: *deterministic retrieval → one model call → cited answer.* There is no task that requires the model to plan, loop, call tools autonomously, or act. Introducing agents would add non-determinism, latency, cost, confidentiality surface (more calls, more data movement), and user-facing complexity — all contrary to Trust > AI and simplest-wins, and unjustified by any FR.

**On DEC-005's allowance for agents in orchestration:** DEC-005 permits agents to *orchestrate workflow*; the architecture already made orchestration **deterministic** with only *optional* agent assist (C-02, AA-06). This document does not require agent orchestration and recommends against it for the MVP AI layer.

## 11. Internal Agent Recommendations

Since no autonomous agents are warranted, the recommendation is **not agents but a small set of hidden, stateless capability handlers** inside the single Fin service — prompt + retrieval configurations, not autonomous systems, never surfaced to the user. They exist only to keep prompts focused and grounded per task.

| Handler (internal, simple name) | Serves | Grounding source | Notes |
|---|---|---|---|
| **Explanation** | Explain This (AIC-01) | the specific finding's evidence | narration only |
| **Questions** | Ask Fin Q&A (AIC-02, AIC-07) | retrieved verified data/findings | declines when unsupported |
| **Summary** | Leadership narrative (AIC-03/04) | the deterministic summary | fills labeled AI slots |
| **Comparison** | What-changed narration (AIC-05) | deterministic MoM/history result | narrates, never computes |
| **Investigation** | Investigation guidance (AIC-06) | findings + history | suggests areas, not actions |

**Design rules for handlers:** (1) they are **not agents** — no autonomy, no tool-use loops, no self-direction; each is one grounded call; (2) they are **hidden** — the user only ever sees "Fin" (§ user-facing); (3) they share one grounding/citation/refusal contract (§4.3, §7); (4) **they could collapse into a single parametrized handler** — the five names are an organizing convenience, and the simplest viable implementation (one handler, five prompt templates) is preferred over five separate components. Start with one; split only if a concrete need appears (YAGNI, mirroring 04 §2.4 / 06 §19 guardrails).

## 12. Deterministic vs AI Responsibility Matrix

| Responsibility | Owner | Never |
|---|---|---|
| Extraction, normalization, verification | Deterministic (C-04/C-06) | AI never alters data |
| Findings creation, severity, evidence | Deterministic (C-07/C-09a, R-FND) | AI never creates/edits |
| Variances, MoM, run-rate, anomalies, reconciliation matching | Deterministic (R-BUD/GED/REC/HST) | AI never computes |
| RAG status, Review Health Score | Deterministic (R-RPT-01; score FUTURE) | AI never assigns/creates |
| Readiness assessment | Deterministic (R-RDY-07) | AI never decides readiness |
| Findings search/sort/filter | Deterministic (FR-102) | not AI-dependent |
| Explaining a finding in plain language | AI narration over deterministic evidence (Explanation) | AI adds no facts |
| Answering grounded questions | AI over retrieved verified data (Questions) | AI never uses world knowledge |
| Leadership-language summary narrative | AI over deterministic summary (Summary) | AI never invents figures |
| Narrating what changed | AI over deterministic comparison (Comparison) | AI never computes deltas |
| Suggesting where to investigate | AI guidance (Investigation) | AI never recommends business/financial action |
| Any financial decision or action | **Human, outside FinSight** | neither system acts |

**Rule of thumb:** if the answer is a number, a finding, a status, or an action → **deterministic (or human)**. If the answer is an explanation, a narration, or a grounded suggestion of where to look → **Fin**.

## 13. User Experience Flows

All flows are R2, reactive, grounded, cited, and degrade to deterministic-only when AI is off (FR-095, NFR-063). They realize UX S-19/S-20 and §15.

- **Explain This (from a finding).** User opens a finding → sees the deterministic explanation (rule, inputs, threshold, source) → optionally taps **Explain This** → (first time, or per policy) **consent prompt** (S-19) discloses exactly what will be sent → Fin returns a labeled, cited plain-language explanation → **Show Sources / View Evidence** available. AI off ⇒ deterministic explanation stands alone.
- **Ask Fin (grounded Q&A).** User opens Ask Fin → sees the locked welcome (§4.1) and suggested questions → asks (typed or one-click) → retrieval selects minimal verified evidence → consent (if not already active) → Fin answers with **Sources Used** → user drills to evidence. If unsupported, Fin states evidence was not found. AI off ⇒ deterministic question library/search (FR-101/102).
- **Investigation guidance.** User asks "What should I investigate next?" → Fin suggests grounded review areas/evidence/history/questions (never actions), cited → user decides. AI off ⇒ deterministic findings triage + "what changed" views.
- **Leadership summary narrative.** In Step 7, the deterministic summary renders complete; AI-narrative slots are labeled and (if AI on + consented) filled by the Summary handler, visibly distinct and attributed. AI off ⇒ slots stay empty; summary reads complete (FR-095).
- **Consent & revocation.** First transmission triggers the informed-consent flow (provider, exact data, masking, implications); consent is logged and revocable in settings; revocation halts future transmissions immediately (S-19, FR-096/088).

## 14. Architecture Considerations

Realizes the approved architecture without changing it (06).

- **Placement & boundary.** Fin lives in **C-15 (AI Assistance & Grounding)** in the delivery ring; it reaches the core **only through the read-only `FindingsQueryPort`** and holds no `FindingsCommandPort` — so it structurally cannot author findings or set severity (TB-03, §7.1 of 06, AP-02). It runs asynchronously and never delays deterministic results (NFR-004).
- **Retrieval-grounded (RAG over the local verified store).** A deterministic retrieval step selects minimal verified snippets (findings, evidence, verified data, approved comparisons) as the *only* context — the confidentiality and grounding control (§3.2, NFR-015, FR-094).
- **Provider abstraction (XP-03, FR-104, NFR-046).** One adapter interface; providers are configuration. Local/on-prem/enterprise-hosted/other are swappable with no change to deterministic components; adding a provider is configuration, not code.
- **Consent & egress (C-16, TB-04).** All transmission passes the single consented-egress chokepoint; no second outbound path exists (NFR-011). Masking/tokenization applied per config before transmission (FR-098, NFR-016).
- **Statelessness & simplicity.** One Fin service, one grounded call per turn, hidden handlers (§11) or a single parametrized handler. No agent runtime, no autonomous loops, no background jobs.
- **Failure behavior (NFR-063).** Provider slow/unavailable/refusing/malformed ⇒ degrade to deterministic-only with a clear "AI unavailable" status; never block, never fabricate.

## 15. Governance & Auditability

- **AI interaction audit (FR-087, NFR-023/052):** every call logs provider, model + version, data transmitted, masking applied, consent reference, prompt category (Explanation/Questions/Summary/Comparison/Investigation), and output — retained under the same at-rest protection as financial data (NFR-009), in the audited local store (C-14 via `AuditEventPort`).
- **Consent audit (FR-088):** every grant, scope, and revocation logged (who/when/provider/operation).
- **Provenance (NFR-023):** every AI artifact records provider/model/version, retrievable for any historical output; AI content is labeled and attributed in-app and in exports (NFR-049, FR-080/120).
- **Model change management (NFR-051):** provider/model changes are recorded events; after a change, a standard validation set of representative explanations/Q&A is reviewed before reliance.
- **Determinism unaffected (NFR-021/037/048):** the provider-swap regression proves that changing/disabling AI changes **no** deterministic output; this is a release gate. AI is, by construction, outside the reproducibility guarantee's surface.
- **Human accountability (DEC-010, NFR-074/075):** AI narration is a draft for human understanding; humans own every decision. Agent-generated *application code* (if the team builds Fin with coding agents) passes the same review/test/traceability gates as any code.

## 16. Risks & Guardrails

| ID | Risk | Guardrail |
|---|---|---|
| **GRD-01** | Hallucination / ungrounded claims | Retrieval-only grounding; no-citation ⇒ no-claim; "evidence not found" behavior; grounding/citation tests (FR-094/099, NFR-050) |
| **GRD-02** | Over-trust of AI narration | Visible AI distinction + labeling + attribution; deterministic-first; Sources/Evidence one click away (NFR-049/067) |
| **GRD-03** | Confidential-data egress | Consent gate + minimization + masking + single chokepoint + provider abstraction; local/on-prem option (§3, NFR-011/015/016) |
| **GRD-04** | **Prompt injection from ingested documents** | Ingested files are untrusted (NFR-012); document text enters the model **only as retrieved data, never as instructions**; system constraints (AI MAY-NOT) are not overridable by content; retrieval scoping + output validation (findings/citations must resolve to real IDs) |
| **GRD-05** | Boundary erosion (AI drifting into computation) | Structural: no `FindingsCommandPort` for AI; provider-swap + AI-off regressions; design-board standing check (NFR-047, TB-03) |
| **GRD-06** | Model drift changing tone/quality silently | Model-change governance + validation set (NFR-051) |
| **GRD-07** | Proactive/annoying behavior | Reactive-only design; no popups/auto-start (§9) |
| **GRD-08** | Consent fatigue / dark patterns | Informed, unbundled, non-defaulted consent; clear disclosure (NFR-014) |
| **GRD-09** | AI becoming load-bearing | FR-095 standing regression: full function with AI off; deterministic fallbacks for every AI surface |
| **GRD-10** | Availability/latency dependence | Async, latency-independent; graceful degradation (NFR-004/063) |

## 17. Traceability Mapping

| AI capability / element | FR | NFR | Epic/Feature | Architecture | UX | UI | Decisions |
|---|---|---|---|---|---|---|---|
| Foundational boundary (MAY/MAY-NOT) | FR-094 | NFR-047 | E-09 | C-15, TB-03, AP-02, `FindingsQueryPort` | §15 | §5.5/§20 | DEC-005 |
| Ask Fin (Q&A) | FR-100/101/102/094/099 | NFR-050/004/049 | E-09 | C-15 | S-20 | §5.5/§20 | DEC-005/006/015 |
| Explain This | FR-091/094/099 | NFR-050/067 | F-06-02 | C-09a/C-15 | §15 | §20 | DEC-005/015 |
| Investigation guidance | FR-093 (narrowed) | NFR-050 | E-09 | C-15 | §15/§21 | §5.5 | DEC-005; new (proposed) |
| Sources & Evidence | FR-099 | NFR-050/067/049 | E-06/E-09 | C-09a | §15 | §20 | — |
| Leadership narrative / summary | FR-092/080 | NFR-049 | F-07-01 | C-12/C-15 | §16 | §14 | DEC-015 |
| What-changed narration | FR-078/092 | NFR-049 | F-07-02/F-06-05 | C-13/C-15 | §17 | §14 | — |
| Onboarding/process (AIC-08) | FR-091 | NFR-068/034 | E-09 | C-15/C-01 | S-21 | — | — |
| Consent & provider governance | FR-096/097/098/104 | NFR-011/013/014/015/016/046 | E-09 | C-16, TB-04, XP-03 | S-19 | §20 | DEC-006/007/016 |
| Audit & provenance | FR-087/088 | NFR-019/023/051/052 | E-08/E-09 | C-14 | S-18 | — | DEC-010 |
| AI-off completeness | FR-095 | NFR-048/063 | E-09 | C-15 removable | all AI surfaces | — | DEC-015 |
| Fin persona (single) | — | NFR-049 | E-09 | C-15 | S-20 | §5.5 | new (proposed) |

**Decision-log entries from this phase** (ratified under the approved baseline — DEC-032–034, consistent with the DEC-024–031 batch): **(a) the Fin single-persona + Ask Fin surface** as the sole AI identity; **(b) the narrowing of FR-093** to investigation-only guidance (no business/financial-action recommendations); **(c) no autonomous agents in the AI layer** — grounded, stateless handlers only. Each is grounded above and introduces no new capability.

## 18. Final Recommended AI Architecture

**One optional, grounded companion — Fin — and nothing more.**

1. **Deterministic core is untouched and dominant.** All truth (data, findings, severity, RAG, variances, reconciliation, readiness, score) is deterministic (05, C-07/C-09a). AI computes none of it.
2. **AI is a single service (Fin) in C-15**, reachable only through the read-only `FindingsQueryPort` — structurally unable to author findings or act.
3. **No autonomous agents.** Each capability is one **grounded, stateless transformation**: deterministic retrieval → one model call → cited answer. Internally, up to five hidden handlers (Explanation, Questions, Summary, Comparison, Investigation) — ideally one parametrized handler — never surfaced to the user.
4. **Three user experiences:** **Explain This**, **Ask Fin**, and **Investigation Guidance** — all reactive, grounded, cited, labeled, and optional.
5. **Confidentiality-first:** AI-off is fully functional and the strongest guarantee; when on, retrieval-minimized, consent-gated, maskable, single-egress, provider-abstracted (local/on-prem preferred where practical).
6. **Governed and auditable:** every interaction and consent logged; every answer cited; determinism proven independent of AI; humans own every decision.
7. **Release-honest:** the whole layer is E-09 / Release 2, with OQ-1/OQ-3 resolved under the approved baseline; Release 1 ships and succeeds with no AI at all.

**The simplest solution wins:** FinSight does not need an AI platform, an agent framework, or a copilot. It needs one calm, grounded, optional companion that helps a human understand a deterministic review — and the discipline to keep it exactly that small.

---

*End of 10-ai-and-agents.md — the AI layer is optional, grounded, cited, reactive, single-persona (Fin), agent-free, and subordinate to the deterministic core. It changes nothing in Release 1 (FR-095); its production gating (OQ-1/OQ-3) is resolved under the approved baseline. Reviewed by the design-review board (AI-governance focus: ai-governance-reviewer, security-engineer, plus ux-designer for the Fin experience) and approved in the current baseline.*
