# FinSight — UX Design

**Document:** 07-ux-design.md
**Status:** Approved
**Date:** 2026-07-15
**Scope:** The **user-experience** design of FinSight — user journeys, workflows, information architecture, navigation, decision points, trust mechanisms, system guidance, onboarding, accessibility requirements, and **screen responsibilities**. This document decides *what the experience must do and why*, not *how it looks*.
**Explicitly out of scope (deferred to a future UI Design phase):** colors, themes, typography, visual styling, component styling, branding, and design systems. Where meaning must not depend on color, this document states the *requirement*; it does not choose a palette. Symbols such as ✅/⚠ appear only as shorthand for *meaning states* (available / attention) — they illustrate information, not visual style.
**Governing methodology:** Spec-driven development (DEC-010, NFR-073). Derived artifact; introduces no scope beyond the approved set.
**Sources of truth:** 00-project-understanding.md · 01-functional-requirements.md · 02-non-functional-requirements.md · 03-epics.md (LOCKED) · 04-features.md (LOCKED) · 05-rules-catalog.md · 06-architecture.md (approved architecture baseline) · 09-decision-log.md
**Companion / downstream documents:** 06-architecture.md (screen→component mapping) · 10-ai-and-agents (AI narration surfaces) · a future UI Design document (visual language)
**Provenance:** AI-drafted from the approved artifacts and the team's UX vision, and approved by the project owner. Experience elements not directly required by a source FR (e.g., the double-confirmation trust check, the Review Health Score surface) were tagged proposed or `FUTURE` with justification and release/phase, and have been accepted (FUTURE items remain scheduled for their phase). This UX design is Approved in the current baseline.

---

## 1. UX Vision

FinSight should **not feel like a dashboard**, and should **not feel like an AI application**. It should feel like a **guided monthly financial review assistant** — a companion that walks the user through a structured review, step by step, and leaves them confident the review was completed correctly.

**The reference experience is guided tax/audit preparation (e.g., TurboTax), not a SaaS analytics portal.** The user is led through an explicit, numbered sequence of steps — *"you are on Step X of Y"* — with a clear next action at every point, rather than being dropped into a menu of modules to navigate. The product feels like *guided tax preparation* and a *guided audit workflow*, and deliberately unlike a *generic SaaS dashboard*, an *analytics portal*, or *menu-driven software*. At any moment the user knows which step they are on, what has already happened, and what happens next.

The organizing idea is **"Monthly Review in a Box"** (DEC-022): the user does not "use modules," they **complete a month's review**. Everything is scoped to a **Review Cycle** identified by month and year (FR-006, AP-04). The user thinks *"I need to complete my July review,"* never *"I need to open the GED module."*

The second organizing idea is **Trust > AI** (DEC-022). The experience is built so the user always trusts the numbers because they can see where every number came from, and because nothing important happens without their explicit review. AI, when present, only *explains* — it never decides, and it is always removable without loss (FR-095).

**Five wayfinding guarantees** — at every moment the user can answer:

1. **Where am I?** — the current review and the current **step (Step X of Y)** in the guided review.
2. **What has happened?** — completed steps, uploaded files, verified data, findings produced.
3. **What is happening?** — the current processing activity in plain language.
4. **What happens next?** — the next step and what it requires.
5. **Why is this available or unavailable?** — a concrete, named reason for every capability that cannot run (readiness).

These five guarantees are delivered by a single mechanism: the **guided review wizard** (§5), a fixed, numbered step sequence with a persistent "Step X of Y" indicator and a clear next action.

**The system is never mysterious.** Nothing hidden, nothing silent (NFR-062). Transparency and trust are the primary UX goals; efficiency and clarity serve them.

### 1.1 UX principles (binding)

| ID | Principle | Serves | Traces to |
|---|---|---|---|
| **UXP-01** | Guided step wizard, not a tool palette — the review is an explicit numbered sequence ("Step X of Y") with one clear next action, in the spirit of guided tax/audit preparation | Confidence, low training | FR-006/081, DEC-022, NFR-068 |
| **UXP-02** | Review-cycle centric — every surface is scoped to a month/year review | "Monthly Review in a Box" | FR-006, AP-04 |
| **UXP-03** | Verify before analyze — no result exists until the user has confirmed the data | Trust > AI | FR-026, TB-02 |
| **UXP-04** | Explainability in one interaction — from any number/finding, reach its rule, inputs, and source | Trust | NFR-067, FR-071 |
| **UXP-05** | One findings experience — never separate systems per capability | Coherence | AP-12, F-06-01 |
| **UXP-06** | Change ≠ exception — "what's new" is surfaced apart from "what's wrong" | Trust, low false alarm | §16.2 of 06, FR-041 |
| **UXP-07** | AI is visibly distinct, optional, and never load-bearing | Trust > AI | NFR-049, FR-095 |
| **UXP-08** | Nothing silent, nothing mysterious — every state, error, and unavailability is explained with a next step | Trust | NFR-055/062/064 |
| **UXP-09** | Accessible by default — meaning never by color alone; keyboard- and screen-reader-usable | Inclusion | NFR-024–027 |
| **UXP-10** | Progressive disclosure by severity — lead with what matters, detail on demand | Attention economy | NFR-066 |

---

## 2. User Personas

Per A-09 and DEC-008, the MVP is **single-user**; one person may embody more than one persona in different modes. Future web deployment adds roles (00 §10).

| Persona | Mode / goal | What the UX must give them | Source |
|---|---|---|---|
| **Operator** | Runs the review: uploads, verifies, reconciles, drives the cycle to readiness for the Leader | Efficient verification, a clear checklist of what's left, low-friction correction, an exception-only reconciliation queue | A-09; E-01/E-05 |
| **Leader** (budget owner) | Consumes findings, summary, and comparisons; makes decisions *outside* FinSight | A trustworthy summary answering "are we okay, and what changed?", one-click drill to evidence, decision-oriented findings view | A-09; E-07 |
| **Administrator** | Manages configuration (thresholds/reference data), the recommended AI-provider registry, and (R2) masking | A transparent, safe configuration surface with versioning and clear validity feedback | DEC-006/007; NFR-039–041 |
| **Auditor / Reviewer** | Reconstructs a past month after the fact | A cycle-timeline audit view and full lineage from any figure | E-08; NFR-019 |
| *Future roles* (PM, finance partner, vendor manager, executive) | Role-appropriate visibility in a shared/web deployment | Same core experience, scoped by role | 00 §10; NFR-071 (future) |

**Persona note:** because Operator and Leader are often the same person, the experience offers **two lenses on one review** (an Operator "work queue" lens and a Leader "decision" lens over the same findings — F-06-01), not two separate applications.

---

## 3. User Goals

| Goal | The user wants to… | Success looks like | Traces to |
|---|---|---|---|
| G-1 Complete the month | Finish this month's review start to finish, confidently | A closed, reproducible review with a leadership summary and full audit trail | DEC-022; E-07 |
| G-2 Trust the numbers | Believe every figure and finding | Any number traces to rule → inputs → source in one interaction | UXP-04; NFR-067 |
| G-3 Catch what matters | Not miss overages, duplicates, missing/late entries, mismatches | Seeded exceptions surface systematically; critical-first | E-03/04/05; NFR-066 |
| G-4 Spend less effort than today | Beat the manual paste-and-clear process | Materially less effort than the manual baseline | NFR-068 |
| G-5 Understand change | See what changed vs. last month, and what's new | Historical comparison and "what's new" (release-phased) | FR-078; §16 of 06 |
| G-6 Stay in control | Keep every financial decision human; never be surprised by the system | Recommendations only; no silent action; explicit gates | 00 §1; UXP-08 |
| G-7 Work regardless of AI | Complete a full review with AI off | Every number/finding/section present without AI | FR-095 |

---

## 4. User Journeys

Journeys are the backbone of the experience. Each names its trigger, steps, decision points (DP-##), and end state. The **primary journey J-1** is the monthly review lifecycle; others branch from or return to it.

**J-1 — Complete a monthly review (primary).** Launch → welcome → **create review (month/year)** → upload available documents → **Validate Review** (readiness) → [DP-1 continue anyway?] → processing → **verification (the trust gate)** → [DP-2 "I have reviewed this"] → analysis → **findings** (investigate, Explain This, triage) → **leadership summary** → export/share → review closed. *(Detailed in §5.)*

**J-2 — Return to an in-progress review.** Launch → Home shows in-progress reviews with their step ("Step X of 8") → resume exactly where left off (NFR-006). No rework; the step wizard shows what's done and what's next.

**J-3 — Correct a wrong upload.** During upload/verification the user notices a wrong file → replace it → the system re-runs affected stages forward (idempotent) and tells the user what will re-run (F-01-04; R1 = duplicate-upload warning, R2 = versioned replacement).

**J-4 — Investigate a finding.** From findings → open a finding → see evidence, rule, inputs, source rows (Explain This) → optionally mark lifecycle state (Acknowledged / In review / Resolved / Dismissed-with-reason). Ends back in findings.

**J-5 — Compare to last month (R2/history-dependent).** From a completed review or history → choose a prior review → see improvements, regressions, continued and new risks.

**J-6 — Reconcile (Operator).** Within Step 6 (Review Findings) → open the reconciliation matching sub-task (§14.1) → confirm probable matches, resolve unmatched, carry forward aged items → residual items become findings at close, in the same Findings Hub.

**J-7 — Ask a question (R2, AI-optional).** From any review surface → ask a natural-language question over the current verified data/findings → grounded, cited answer, visibly AI-labeled; declines if unsupported (FR-100, FR-094/099). Available only when an AI provider is configured and consented (FR-096); a deterministic question library works without AI (FR-101/102).

**J-8 — Configure (Administrator).** Settings → adjust thresholds/reference data/provider registry → see validity feedback and version history; changes are audited (FR-107).

**J-9 — Reconstruct a past review (Auditor).** Audit → pick a month → cycle timeline of who did what, which rules/config versions ran, what was produced (E-08).

**J-10 — First-run onboarding.** First launch → brief orientation → optional historical import to establish baselines (F-01-10, R2) → create first review. *(Detailed in §5.1.)*

---

## 5. Review Lifecycle Experience — The Guided Review Wizard

The review is delivered as an **explicit, numbered, guided wizard** — the spine of the product and the direct expression of UXP-01 (guided tax/audit preparation, not a dashboard). It mirrors the architecture's cycle state model (06 §6.2) but is *presented* to the user as a linear, progress-tracked sequence of **8 steps**. A persistent **step indicator** ("**Step X of 8**") and a **progress stepper** are visible throughout, so the five wayfinding guarantees (§1) hold continuously.

```
  ●───────●───────●───────◐ (you are here)───○───────○───────○───────○
 Step 1  Step 2  Step 3   Step 4        Step 5  Step 6  Step 7  Step 8
 Create  Upload  Validate VERIFY DATA   Analyze Review  Leader  Complete
 Review  Docs    Review   (trust gate)  Review  Findings Summary Review
                    │        │(HARD GATE)
              why ready?  "I have reviewed" → Review Complete handoff (§12)
```

- **The eight steps** (each detailed in §9–§19): **Step 1 Create Review** · **Step 2 Upload Documents** · **Step 3 Validate Review** · **Step 4 Verify Data** · **Step 5 Analyze Review** · **Step 6 Review Findings** · **Step 7 Leadership Summary** · **Step 8 Complete Review.**
- **Always "Step X of 8."** Every review screen names the current step and its position; the stepper shows completed steps (done indicator + text label, not color alone — NFR-025), the current step, and upcoming steps with what each needs. The user rarely feels they are "navigating between modules"; they feel guided through a process.
- **One clear next action.** Each step ends with a single primary action that advances the wizard (e.g., *Continue to Verification*), reinforcing "what happens next."
- **Steps advance forward; revisiting is read-only.** Completed steps can be reviewed; re-entry (a corrected file, a config change) returns to the earliest affected step and re-runs forward, idempotently (NFR-008) — the user is told what will re-run (J-3).
- **Processing is shown within steps, not as its own step.** File reading/extraction is the transition *into* Step 4; deterministic computation is Step 5 itself — each communicated in plain language (§13), never as a separate "module."
- **Home is not a step.** The Welcome / Recent Reviews home (§9) is where a review is started or resumed; the numbered wizard begins once inside a review.

**Step responsibilities (summary; detailed per step in §9–§19):**

| Step | Name | User's job | System's job | Gate? |
|---|---|---|---|---|
| **1** | Create Review | Name the review by month/year | Establish the cycle; set the "you are on Step 1 of 8" frame | — |
| **2** | Upload Documents | Add the files they have | Accept, record provenance, never force uploads | — |
| **3** | Validate Review | Decide to proceed | Explain what's ready/not-ready and why (readiness) | soft (DP-1) |
| **4** | **Verify Data** | **Review / correct / confirm the extracted data** | **Present data honestly; block analysis until confirmed; deliver the "Review Complete" handoff** | **HARD (DP-2)** |
| **5** | Analyze Review | Wait, informed | Run deterministic analysis (incl. reconciliation matching); plain-language progress | — |
| **6** | Review Findings | Investigate, triage, resolve | Present one findings experience, prioritized; Operator work-queue + Leader lenses | — |
| **7** | Leadership Summary | Read, share | Generate the leadership summary (AI-optional); export | — |
| **8** | Complete Review | Confirm the review is done | Freeze, retain, keep reproducible; offer compare/what's-new | — |

*Cross-cycle experiences — Historical Comparison (§17), What's New (§19), and the FUTURE Review Health (§18) — are reached from a completed review (Step 8) or from the home, not as steps in the wizard.*

### 5.1 Onboarding (J-10)

First launch is not a blank dashboard. It is a short, skippable orientation that: (1) states what FinSight does in one screen ("a guided monthly financial review — you stay in control; AI only explains"); (2) offers optional **historical import** to establish baselines so history-dependent checks work sooner (F-01-10, R2; with AP-11 honesty that early months have limited baselines); (3) leads directly into **Create Review**. Low training is a requirement (NFR-068); the product must be learnable by non-technical users without a manual.

---

## 6. Information Architecture

FinSight's IA is **review-cycle centric**, not module-centric (UXP-02). There is no "GED area" and no "Budget area" as top-level destinations; those are *lenses inside a review*.

```
FinSight
├── Home  (Welcome + Recent Reviews)     ← the front door; Recent Reviews is first-class here (§9)
│   ├── Recent Reviews                    ← prominent list: «Month Year» + status (Completed / In progress · Step X of 8)
│   ├── Create New Review                 ← starts Step 1 of the wizard
│   └── Review History / All Reviews      ← full, searchable list of past cycles
│
│   └── Review «Month Year»              ← the active cycle; the 8-STEP GUIDED WIZARD lives here (§5)
│        ├── Step 1 Create → Step 2 Upload → Step 3 Validate → Step 4 Verify
│        ├── Step 5 Analyze → Step 6 Review Findings → Step 7 Leadership Summary → Step 8 Complete
│        │        └── Findings (Step 6): single findings hub (Budget / GED / Reconciliation groups)
│        │                 ├── Finding → Explain This
│        │                 └── Reconciliation work view (Operator matching sub-task — §14.1)
│        └── (from Step 8) What's New (FUTURE) · Compare (R2)
├── Compare / History                    ← spans cycles (release-phased)
├── Review Health                         ← operational score, cross-cycle (FUTURE — §18)
├── Settings / Configuration             ← thresholds, reference data, AI provider, masking (Admin)
├── Audit                                ← cycle-timeline reconstruction (Auditor)
└── Help                                 ← guidance, glossary, "how a finding is produced"
```

**IA rules:**
- **Home leads with Recent Reviews, not only "Create."** Users revisit prior reviews frequently (comparison, audit, re-reading a summary), so the front door prominently lists recent completed and in-progress reviews with one-click resume/open, alongside Create New Review (§9, Change #5).
- **Everything analytical is scoped to a review, inside the wizard.** Capabilities (Budget/GED/Reconciliation/Invoice/Resource) never become top-level nav; they appear as *findings groups* and *summary sections* within Step 6/Step 7 (UXP-05, AP-12). Reconciliation is a *matching sub-task within Step 6*, not a separate destination (§14.1, Change #2).
- **Cross-cycle destinations** (Compare/History, Review Health, Audit) are separate because they legitimately span reviews, and are reached from Home or a completed review — never as wizard steps.
- **Configuration lives with the review's governance, not as a competing home.** It is reachable but not the front door (DEC-020: configuration is dissolved as a standalone concept — it belongs with what it configures).
- **Depth is bounded** (F-14-01 guardrail): the R1 information architecture contains only surfaces traceable to a locked R1 feature; anything else is rejected as scope creep (mapped in §8).

---

## 7. Navigation Model

- **Front door = Home with Recent Reviews**, not a dashboard (per the vision). Launch shows a welcome and a prominent Recent Reviews list (with each review's status and, if in-progress, its Step X of 8), so the user resumes or starts a review in one step (J-1/J-2, §9).
- **Primary in-review navigation = the guided step wizard** (§5) with its persistent **"Step X of 8" indicator and progress stepper**. It is both wayfinding and progress, and the dominant navigation surface — expressing UXP-01 (guided sequence, not a palette). The user advances via one clear next action per step.
- **The wizard enforces gates:** the **Step 4 → Step 5 (Verify → Analyze)** transition is not selectable until verification is confirmed (UXP-03, FR-026); **Step 3 (Validate Review)** offers an explicit, consciously-confirmed path to continue with a subset (DP-1). Steps ahead of an unmet gate are visibly not-yet-available with the reason shown.
- **Secondary navigation** (persistent, low-prominence): Home/switch-review, Settings, Audit, Help. These never compete with the wizard for attention.
- **Within-step navigation** is shallow and purpose-built: e.g., in Step 6, findings groups expand/collapse in place and the reconciliation matching sub-task opens as a focused work view with a clear "back to findings" (§14.1).
- **No dead ends:** every screen states the current step, what happens next, and offers the next action (UXP-08). Every "unavailable" states why and how to make it available (readiness).
- **Keyboard-first:** every primary workflow is fully keyboard-navigable, with a logical focus order following the step wizard (NFR-026).

---

## 8. Screen Inventory (screen responsibilities)

Screens are described by **responsibility, key information, primary actions, decision points, and traceability** — not layout or styling. `S-##` IDs are UX-local. Release/phase noted; R1 surfaces only are required for "Monthly Review in a Box."

| ID | Screen / surface | Responsibility | Key info shown | Primary actions | Release | Traces (feature · component) |
|---|---|---|---|---|---|---|
| **S-01** | Home — Welcome + **Recent Reviews** | Greet; **lead with Recent Reviews**; start/resume/open history | Prominent Recent Reviews list (Completed / In progress · Step X of 8); Create New Review; link to full history | Open/resume a recent review; Create review; browse all reviews | R1 | F-01-01 · C-01/C-02 |
| **S-02** | Create Review | Establish a cycle by month/year (date optional) | Month, Year (required), Date (optional) | Create | R1 | F-01-01, FR-006 · C-02 |
| **S-03** | Upload | Present all supported doc types; accept available files only | Doc-type slots, upload state, provenance | Upload per type; remove; proceed | R1 | F-01-02/03 · C-03 |
| **S-04** | Readiness | Explain what's ready/not-ready and why | Per-capability Available/Partial/Unavailable + reason | Upload more; Validate; Continue anyway (DP-1) | R1 | F-01-08, R-RDY-07 · C-05 |
| **S-05** | Continue-anyway confirmation | Prevent accidental incomplete review | Included capabilities; unavailable ones | Go back; Continue | R1 accepted | trust; NFR-062 · C-02 |
| **S-06** | Processing | Communicate current stage in plain language | Stage progress (reading/extracting/building/preparing) | Cancel/pause (safe) | R1 | F-14-03 · C-02/C-04 |
| **S-07** | Verify Data (Step 4) — the trust gate | Review/correct/confirm data; then deliver the **"Review Complete" confirmation** | Extracted values, low-confidence & quarantined highlights, source trace, corrections; **post-confirmation summary of what was verified** | Correct; bulk-approve high-confidence; per-doc approve/approve-with-corrections/reject; **confirm "I have reviewed"** (DP-2) → see Review Complete handoff | R1 | F-01-09, FR-026–029 · C-06 |
| **S-07b** | Review Complete (verification handoff) | Make verification feel intentional; confirm what was approved before analysis | "You have verified: ✓ Vendors ✓ Departments ✓ Accounts ✓ Amounts ✓ Dates — Analysis will now begin" | Begin analysis (advances to Step 5); go back to re-verify | R1 accepted | trust; FR-026 · C-06/C-02 |
| **S-08** | Analysis progress | Communicate analysis stages in plain language | Budget/GED/exceptions/preparing progress | — | R1 | F-14-03 · C-07 |
| **S-09** | Findings hub | One findings experience; grouped, prioritized | Groups (Budget/GED/Reconciliation…) with counts; severity per finding | Expand; filter/sort; open finding; triage | R1 | F-06-01/04 · C-09b |
| **S-10** | Finding investigation / Explain This | Understand a finding via its evidence | Rule, inputs, threshold comparison, source rows, related data | Explain This; set lifecycle state; trace to source | R1 | F-06-02, R-FND-01/02 · C-09a/C-09b |
| **S-11** | Reconciliation matching (Step 6 sub-task) | Operator **matching work** view — not a separate findings system (§14.1) | Match tiers (exact/probable/unmatched), cleared status, aged carry-forward | Confirm/reject probable; manual match/override (reason); clear; return to Findings | R1 | F-05-02, R-REC-* · C-10 |
| **S-12** | Leadership summary | Trustworthy, non-technical monthly summary | RAG, budget health, GED status, key risks, recommended attention, reconciliation status, "what changed" (thin) | Read; export/share | R1 | F-07-01, R-RPT-* · C-12 |
| **S-13** | Export / share | Self-describing, labeled output | Content preview, labels (period, config version, AI-marking) | Export summary/findings/data | R1 | F-07-04, FR-120 · C-12 |
| **S-14** | Compare / History | Understand change across cycles | Improvements, regressions, continued/new risks | Pick reviews; drill | R2 | F-07-02, R-HST-02 · C-13 |
| **S-15** | What's New | Surface change apart from findings | New vendors/accounts/patterns/dept activity | Review; (optionally) escalate as a question | FUTURE | §16.2 of 06, R-HST-04 · C-13 |
| **S-16** | Review Health | Operational (**not financial**) review-quality score | Score + trend, contributing signals | Read; drill to signals | **FUTURE only** — **not R1**; scheduled for a future release | §16.3 of 06, XP-05 · C-13 |
| **S-17** | Settings / Configuration | Transparent, safe config | Active thresholds/reference data/provider/masking; version history | Edit (versioned); view active config | R1 (core) | F-14-01, F-08-03 · C-18 |
| **S-18** | Audit trail | Reconstruct a review after the fact | Cycle timeline; who/what/when; rule & config versions | Search/filter; export | R1 | F-08-02 · C-14 |
| **S-19** | AI consent | Informed, final gate before any transmission | Provider, exact data, masking state, implications | Consent; decline; revoke | R2 (with AI) | FR-096, C-16 |
| **S-20** | Q&A / Ask | Grounded, cited NL answers; deterministic question library | Answer + citations (AI-labeled) or deterministic view | Ask; pick a canned question | R2 (AI) / R1 (library) | FR-100/101/102 · C-15/C-09b |
| **S-21** | Help / Guidance | Lower training; explain the process and terms | How a finding is produced; glossary; stage help | Read; contextual help | R1 | NFR-068, NFR-034 · C-01 |

---

## 9. Home, Recent Reviews & Review Creation Experience (S-01 → S-02)

### 9.1 Home & Recent Reviews (S-01) — a first-class landing experience

- **Launch is a welcome, not a dashboard** — and it does **not** center only on "Create New Review." Users revisit prior reviews frequently (to compare months, re-read a summary, answer an audit question, or resume in-progress work), so **Recent Reviews is a first-class part of the first screen**.
- The home greets the user (e.g., *"Good morning — welcome to FinSight"*) and prominently presents **Recent Reviews**, each with its status:

  ```
  Recent Reviews
    July 2026     — Completed
    June 2026     — Completed
    May 2026      — Completed
    April 2026    — In progress · Step 4 of 8 (Verify Data)   ▸ Resume
  ─────────────────────────────
    + Create New Review          ▸ starts Step 1
    View all reviews / history   ▸
  ```

- **One-click open/resume (J-2).** Opening a completed review lands on its Leadership Summary (Step 7 view, read-only); resuming an in-progress review returns to its exact step with no rework (NFR-006) — the status line already tells the user which step ("Step X of 8") they'll land on.
- **Create New Review** is present and obvious, but shares the stage with Recent Reviews rather than dominating it.
- **Review history access** — a "View all reviews" path leads to the full, searchable list of past cycles (feeding Comparison §17 and Audit §18/S-18).
- **Accessibility:** Recent Reviews is a keyboard-navigable list with screen-reader-announced status and step; status is conveyed by text, not color alone (NFR-025/026).
- **Traceability:** F-01-01 (review-cycle workspace, status, resume), NFR-006 (resumable) · C-01/C-02.

### 9.2 Create Review (Step 1 of 8) (S-02)

- **Create Review is Step 1** of the guided wizard. It asks for the primary cycle identifiers: **Month (required), Year (required), Date (optional)** (FR-005/006). These name the cycle (e.g., "July 2026 Review"). Month/year are proposed automatically where detectable from later uploads (FR-005) but confirmed by the user.
- **The mental model is set here:** the user has created *a review* and is now "on Step 1 of 8," not opened a tool. Everything after is inside this review.
- **Decision point:** none blocking; naming is low-friction. If a review for that month already exists, the system says so and offers to open it (no silent duplicate).
- **Traceability:** FR-006 (review-cycle grouping), FR-005 (period assignment), F-01-01 · C-02.

---

## 10. Upload Experience (Step 2 of 8, S-03)

- **All supported document types are presented** with their own upload action: GED Report, Budget Tracker, Invoices, Resource Sheets, Contracts, Rate Cards (and others as document types are added — XP-02). Each type is a labeled slot.
- **Upload only what you have.** FinSight **must not force** uploads for documents the user does not possess (per the vision; readiness handles the consequences). Empty slots are normal, not errors.
- **On each upload:** the file is accepted as read-only (never modifying the source — FR-003), provenance is recorded (name, fingerprint, user, timestamp — FR-010), the type and period are proposed for confirmation (FR-004/005), and unreadable/corrupt/password-protected/unsupported files are rejected with a **plain-language reason and next step** (FR-007, NFR-055/064). Duplicate/near-identical uploads warn before proceeding (FR-008).
- **The user always sees** what has been uploaded, to which type, and what is still empty — feeding the readiness step.
- **Wrong-file recovery (J-3):** remove/replace with the system stating what downstream work re-runs (F-01-04).
- **Accessibility:** uploads are keyboard-operable and screen-reader-labeled; drag-drop, if offered later (UI phase), must not be the only path (NFR-026).
- **Traceability:** FR-001/002/003/004/005/007/008/010 · C-03; untrusted-input safety NFR-012 (surfaced only as safe rejection, never a crash).

---

## 11. Readiness Validation Experience (Step 3 of 8, S-04, S-05)

Realizes the approved Capability Readiness guidance (06 §10; rule R-RDY-07). This is a signature trust moment: **the system tells the user exactly what it can and cannot do, and why, before doing anything.**

- **The user clicks "Validate Review."** FinSight evaluates available, classified, and (where already extracted) quality-checked data and presents a **readiness map**:

  ```
  Ready
    ✅ Budget Analysis
    ✅ GED Analysis
  Not Ready
    ⚠ Invoice Validation — Missing: Rate Card
    ⚠ Resource Analysis  — Missing: Resource Sheet
  ```

- **Every "not ready" states a concrete, named reason** and what would make it ready (NFR-055/064). Nothing is hidden; nothing silently fails (UXP-08). Statuses are conveyed by text + icon, never color alone (NFR-025).
- **The user chooses:** *upload more files* (return to S-03) or *Continue anyway* (proceed with the available subset — capabilities gate, not the whole review).
- **Double-confirmation trust check (S-05) accepted:** if the user chooses Continue anyway, FinSight shows a second confirmation restating what is included and what is unavailable:

  ```
  You are continuing with only:
    ✅ Budget Tracker
    ✅ GED Report
  Unavailable capabilities:
    ⚠ Invoice Validation
    ⚠ Resource Analysis
  Continue?   [ Go Back ]   [ Continue Review ]
  ```

  **Purpose:** prevent accidental incomplete reviews, increase confidence, and prevent users from later doubting the output ("did I forget something?"). *Justification for accepted:* not named by a specific FR, but directly serves NFR-062 (no silent failure), the verified-data trust principle, and the vision; it introduces no scope and can be accept/rejected by the team.
- **Traceability:** readiness R-RDY-07, FR-081/111, F-01-08 · C-05; confirmation pattern → trust goals, NFR-062.

---

## 12. Verification Experience (Step 4 of 8, S-07) — the most important experience

This is where **Trust > AI** becomes tangible (UXP-03, FR-026, TB-02) and the emotional center of the guided review. After extraction, FinSight does **not** analyze. It says, in effect, *"Here is the information I found,"* and hands control to the user. The step is framed explicitly — *"Step 4 of 8 — Verify Data"* — so the user understands this is a deliberate, meaningful checkpoint, not a formality.

- **What the user reviews:** the extracted financial information — vendors, departments, accounts, dates, amounts, budget values — presented for review against its source.
- **The system clearly distinguishes three states of every value** (text/icon, not color alone — NFR-025):
  - **Extracted** (as read from the file),
  - **Low-confidence** (highlighted for attention — FR-016),
  - **Corrected** (edited by the user; the original remains visible in lineage — FR-028).
  Quarantined rows are shown separately with their reason (FR-024/025), never dropped silently.
- **One-click source trace:** any row traces to its source file/sheet/row/cell (FR-027, NFR-067) — the user can always check "where did this come from?"
- **The user may review, correct, and confirm** per document: **approve / approve-with-corrections / reject** (FR-029). Corrections preserve original value, corrected value, user, and timestamp (FR-028), all audited (FR-085).
- **Low-friction by design:** high-confidence data can be **bulk-approved**; attention is directed to low-confidence and quarantined items (NFR-069). The gate is optimized, never bypassed.
- **Explicit confirmation gate (DP-2):** the user must explicitly confirm *"I have reviewed this information."* Only then does **Continue Review** become available. **Analysis cannot proceed until verification is complete** — this is enforced by the architecture (the Rules Engine consumes only a `VerifiedDataset` constructible solely at approval — 06 §11), so the UX gate reflects a structural guarantee, not a soft convention.
- **Per-document granularity:** verification is per document, so a user can verify and later analyze available documents while others remain unverified (06 §6.2) — consistent with readiness proceeding on a subset.

### 12.1 The "Review Complete" handoff (S-07b) — leaving verification with confidence

The moment the user confirms, verification must feel **intentional and meaningful** — an accomplishment, not a dismissed dialog. Before analysis begins, FinSight presents an explicit **Review Complete** confirmation that restates, in plain language, exactly what the user has approved:

```
  ✓ Review Complete

  You have verified:
    ✓ Vendors
    ✓ Departments
    ✓ Accounts
    ✓ Amounts
    ✓ Dates

  Analysis will now begin on the information you reviewed.

     [ Go back to re-verify ]        [ Begin Analysis → Step 5 ]
```

- **Purpose:** the user leaves Step 4 confident that (1) the extracted data is correct, (2) **they** approved precisely what will be analyzed, and (3) FinSight is acting only on reviewed information — the concrete embodiment of Trust > AI.
- **Honest to what was actually verified.** The checklist reflects the data categories present in *this* review (e.g., budget values appear when a Budget Tracker was verified); it never claims verification of data the user did not see. Where verification proceeded on a subset, the handoff names what will and will not be analyzed (consistent with readiness §11).
- **Reversible before commitment.** "Go back to re-verify" returns to the workspace; "Begin Analysis" advances the wizard to Step 5. No analysis has run until the user chooses to begin.
- **Accessibility:** the confirmation is announced to screen readers as a completion state; each ✓ item is text-labeled, never color-only (NFR-025/026).
- **accepted** — this explicit handoff is not named by a specific FR; it is grounded in FR-026 (the mandatory gate), the Trust > AI vision, and NFR-062 (nothing silent). It adds a confidence-building confirmation to the existing gate; it introduces no new scope and can be accepted/rejected by the team.

- **Traceability:** FR-016/026/027/028/029, NFR-069 · C-06; TB-02 gate; handoff → trust, NFR-062.

---

## 13. Analysis Experience (Step 5 of 8, S-08)

- After verification, FinSight performs deterministic analysis and communicates **plain-language stages** — *Analyzing Review · Budget Analysis · GED Analysis · Finding Exceptions · Preparing Results* — without technical implementation detail (NFR-003/055).
- **The UI never freezes** (NFR-002/003); analysis runs off the interaction thread (F-14-03) and the user can keep viewing other data.
- **Deterministic results appear as soon as ready**, independent of any AI (NFR-004); AI narration (if configured) arrives or fails separately and never blocks (UXP-07).
- **Honest at cold start:** if history-dependent checks lack minimum history, the experience says so ("some checks need more history") rather than pretending or firing unreliable findings (FR-111, AP-11).
- **Traceability:** NFR-002/003/004/055, FR-111 · C-07 (with progress via F-14-03).

---

## 14. Findings Experience (Step 6 of 8, S-09)

Realizes the Findings Hub principle: **one findings experience, never separate systems** (UXP-05, AP-12, F-06-01).

- **Findings are grouped by capability** with counts, e.g.:

  ```
  Budget Issues (3)          ▸
  GED Issues (4)             ▸
  Reconciliation Issues (2)  ▸
  ```

  Each group expands in place; the user never navigates to a different "system."
- **Severity is immediate and color-independent:** each finding shows **Critical / High / Medium / Low** via text + icon/shape, never color alone (NFR-025, FR-070). Critical/High are surfaced first on completion (FR-082, NFR-066 progressive disclosure).
- **Two lenses, one set of findings:** an **Operator work-queue** lens ("what do I need to resolve?") and a **Leader decision** lens ("what needs my decision?") over the same records (F-06-01) — no per-capability forks, no divergent statuses (a divergence is a trust defect).
- **Triage in place:** browse/filter/sort by severity, status, rule, capability, account, vendor, period (FR-074) — all without AI (FR-102). Lifecycle actions (Acknowledge / In review / Resolve / Dismiss-with-reason) are available per finding (FR-072); dismissal always requires a reason.
- **Reconciliation is part of this one experience (see §14.1)** — its exceptions render as a findings group here; its *matching work* is a focused sub-task, not a separate findings system.
- **Traceability:** FR-069/070/072/074/082/102, NFR-066/067 · C-09b (experience) over C-09a (contract).

### 14.1 Reconciliation — re-evaluated against "One Findings Experience"

**The question (Change #2):** should reconciliation be a separate major experience, or be folded into the Findings Hub? **Decision: fold the *outcomes* into the one Findings Hub, and keep reconciliation *matching* only as a focused Operator work sub-task within Step 6 — not a separate destination.** Reasoning:

1. **Two different things share the word "reconciliation."** *Matching work* (pairing GED lines to tracker entries, confirming probable matches, clearing) is **work-in-progress**; a *reconciliation exception* (a residual unmatched item that matters) is a **finding**. The product's own workspace/finding boundary already separates these (04 §2.3, 06 §13).
2. **All reconciliation findings live in the one Findings Hub.** Reconciliation exceptions appear as a findings group here (alongside Budget and GED), render through the same components, carry the same severity/lifecycle/Explain-This, and never form a parallel findings system. This *honors* One Findings Experience (UXP-05, AP-12) rather than violating it.
3. **The matching work needs a focused surface, but not a top-level one.** Confirming dozens of probable matches and clearing items is a distinct, high-volume Operator task that would clutter the Leader-facing findings list. So it is presented as a **focused work view opened from within Step 6** (S-11) — reachable from the Operator work-queue lens, with a clear "back to Findings." It is a *sub-task of the guided review*, not a module in the navigation and not a 9th wizard step.
4. **Why this improves UX:** the Operator gets an efficient, exception-only matching surface (E-05: touch only flagged/probable items) without the Leader ever seeing raw matching mechanics; the Leader sees only the reconciliation *findings* that survived, in the same inbox as everything else. Work and findings stay in sync (one record, two presentations, one state machine — a divergence would be a trust defect).
5. **Architecture fit is preserved.** This maps exactly to C-10 (reconciliation workspace producing into C-09a via the findings contract) with no change to the baselined architecture, features (F-05-02), or rules (R-REC-*). Nothing is redesigned; the *UX framing* is corrected so reconciliation is not perceived as a separate system.

**Net:** there is **no separate major Reconciliation experience** in the navigation. There is **one Findings Experience** (Step 6) that includes reconciliation findings, plus a **focused reconciliation matching sub-task** opened from within it for Operator work.

---

## 15. Explain This Experience (S-10)

The purpose is **understanding**, grounded in deterministic findings — **not AI-generated conclusions** (UXP-04, 06 §15.2).

- **From any finding, "Explain This" reveals** (all deterministic, all available with AI off — FR-095):
  - **Why it triggered** — the rule and the condition met,
  - **Supporting evidence** — the exact input values used,
  - **Threshold comparison** — the value vs. the configured parameter (e.g., observed vs. materiality/tolerance), with the configuration version in force,
  - **Related vendors/accounts and related data** — the entities and source rows involved,
  - **Source trace** — one-click to the originating file/sheet/row/cell (FR-071, NFR-067).
- **Deterministic first (R1):** this explanation is produced from the rule's evidence (R-FND-01/02, C-09a) — it is checkable, reproducible, and requires no AI.
- **Optional AI narration (R2):** where an AI provider is configured and consented, a plain-language narrative may accompany the deterministic explanation — **visibly distinct, labeled AI-generated, attributed (provider/model), and cited to the finding/data** (NFR-049/050, FR-091/099). It explains; it never adds a figure, finding, or conclusion absent from the deterministic result (FR-094). If AI is off/unavailable, the deterministic explanation stands alone, complete.
- **Traceability:** FR-071/091/094/099, NFR-050/067 · C-09a/C-09b (+ C-15 for the optional narrative).

---

## 16. Executive Summary Experience (Step 7 of 8, S-12)

- After findings review, FinSight generates the **leadership summary**, understandable by **non-technical leadership** and **useful even with AI disabled** (FR-095).
- **Contents** (fixed section structure — F-07-01 guardrail; deterministic — R-RPT-02): overall **RAG status** (deterministic, never AI — FR-077); **Budget Health**; **Critical Findings / Key Risks**; **Recommended Attention Areas** (deterministic references to findings; AI may narrate in R2); **Reconciliation Status**; and a thin **"What Changed"** section (FR-078, R1 thin / interactive R2).
- **AI-narrative slots exist but are labeled and empty until E-09**; the summary must read as complete without them (FR-095). Any AI content is visibly distinct and attributed (NFR-049).
- **Every figure is drillable** to its finding/evidence (UXP-04). The summary is a starting point for a decision the human makes outside FinSight (G-6).
- **Export** is self-describing and labeled — timestamp, period, data-as-of, configuration version, and identical AI-content labeling (FR-120) — because exported summaries live forever in email (S-13).

**Step 8 — Complete Review (the wizard's finish line).** After reading/exporting the summary, the user reaches an explicit **Complete Review** step that closes the guided sequence: FinSight confirms the review is finished ("July 2026 review complete"), records it as a completed, reproducible cycle (freeze/retain — F-07-03, F-02-06), and returns the user to Home where it now appears at the top of **Recent Reviews** (§9). From here the user is offered the cross-cycle next actions — Compare to a prior review (§17) and What's New (§19) — without those being wizard steps. Completing the review is a deliberate, satisfying end state, not a silent stop.

- **Traceability:** FR-076/077/078/079/080/095/116/120, F-07-03, R-RPT-* · C-12; completion → F-01-01 (cycle status), C-02.

---

## 17. Historical Comparison Experience (S-14) — R2

- Users can **compare completed reviews**, e.g. *"Compare August 2026 to July 2026."*
- FinSight shows change in plain, direction-labeled terms (text + icon, not color alone):

  ```
  ✅ Budget Variance Improved
  ⚠ Vendor Spend Increased
  ✅ Reconciliation Exceptions Reduced
  ⚠ Existing Risk Continued
  ```

- **Purpose:** help the user understand change over time — what improved, what worsened, which risks are new, which recur (FR-078, F-06-05 recurrence). Comparison is deterministic (R-HST-02/03); AI may narrate the story in R2, labeled.
- **Release honesty:** the interactive comparison view is **R2** (F-07-02); the R1 summary already carries a thin "what changed" (S-12). Cold-start: with only one review, comparison explains it needs a prior month.
- **Traceability:** FR-078, F-07-02, R-HST-02/03 · C-13.

---

## 18. Review Health Experience (S-16) — FUTURE ONLY accepted (explicitly deferred; not Release 1)

> **Deferral statement (binding):** The Review Health Score is a **valuable but intentionally deferred, FUTURE-only** concept. It is **not Release 1 functionality** and must not be elevated into R1. It is presented here so the experience vision is complete and the architectural seam (XP-05) exists — nothing more. It **requires future validation** (of its signals, weighting, and operational meaning) with stakeholders before it is built.

- Users would eventually see an overall **Review Health Score** with trend, e.g. *July 72 · August 85 · +13* (numbers illustrative only — the score would be computed deterministically by a configurable rule; no value is fixed here).
- **Critically, the score is operational, not financial** (06 §16.3). It represents **review quality and completeness** — driven by operational signals (critical findings, data-quality issues, reconciliation exceptions, risk indicators, open findings) — and must be **clearly distinguished from the financial RAG status** (FR-077) in label and presentation, so no one ever mistakes it for a financial rating.
- **Determinism & honesty:** it would be computed by a deterministic catalog rule (never AI — AP-01/02), configurable and versioned; drillable to its contributing signals (UXP-04).
- **Why deferred:** it is a governance/operational aggregate that layers on top of a working monthly review and depends on accumulated history and validated signals; the Release-1 review is complete and trustworthy without it (Trust > AI; "Monthly Review in a Box" needs no score).
- **Release honesty:** **FUTURE only** (06 §16.3, XP-05; E-13 "visible but deferred" posture). It introduces **no R1 scope** and appears in no R1 wizard step; any activation goes through the decision log with the validation above.
- **Traceability:** 06 §16.3, XP-05 · C-13 (future).

---

## 19. What's New Experience (S-15) — FUTURE

- FinSight **highlights change separately from findings**: New Vendor, New Account Usage, New Spending Pattern, New Department Activity.
- **New does not mean wrong.** Change detection and exception detection are **separate concepts** (UXP-06, 06 §16.2, FR-041 philosophy): "what's new" surfaces change for human attention; it never manufactures a finding. A new entity becomes a *finding* only if a separate exception rule independently fires.
- **Placement:** a distinct surface within the review (and referenced in the summary), never mixed into the findings inbox — so users are informed of change without alarm fatigue.
- **Release honesty:** detection of new entities beyond current month-over-month deltas is **FUTURE** (R-HST-04, XP-04); the R1 experience carries change only via the thin "what changed" summary section.
- **Traceability:** 06 §16.2, FR-078/032/041, R-HST-04 · C-13 (future).

---

## 20. Accessibility Requirements

FinSight must be usable by everyone (UXP-09; NFR-024–027). These are UX *requirements*; the visual realization (palettes, contrast values) is the future UI phase.

| Requirement | What the UX guarantees | Traces to |
|---|---|---|
| Screen-reader support | All content and controls carry accessible names/roles; findings, severities, readiness reasons, and errors are announced meaningfully | NFR-026 |
| Keyboard navigation | Every primary workflow (Step 1 Create → 2 Upload → 3 Validate → 4 Verify → 5 Analyze → 6 Findings → 7 Summary → 8 Complete) is fully keyboard-operable with logical focus order following the step wizard | NFR-026 |
| Adjustable text size | Respects OS text-size settings without layout breakage or loss of function | NFR-027 |
| OS display-mode support | Follows native light/dark mode; a theme picker (incl. color-vision-safe options) is a later UI story | NFR-024 |
| High-contrast support | The experience remains fully usable under high-contrast/OS accessibility settings | NFR-024/026 |
| Color-independent meaning | **No information — especially severity and RAG — is conveyed by color alone;** icon/text/shape always accompany color | NFR-025 (binding) |
| Low training requirement | Learnable by technical and non-technical users without a manual; contextual help and a glossary (S-21); guided lifecycle lowers the learning curve | NFR-068, NFR-034, UXP-01 |
| Responsive layout | Adapts across corporate-laptop and external-monitor sizes without horizontal scrolling of the page | NFR-065 |
| Actionable errors | Every error states what failed, the impact, and the next step — never a raw trace | NFR-055 |

Accessibility is **default, not a mode** — it is designed into the flows above, not bolted on. (DoD clause 8: no meaning by color alone; keyboard-reachable — enforced per story.)

---

## 21. Trust Mechanisms

The experience's trust is built from explicit, repeatable mechanisms (`TM-##`). These are what make "Trust > AI" felt, not just claimed.

| ID | Mechanism | Where | Traces to |
|---|---|---|---|
| **TM-01** | Verify-before-analyze hard gate — nothing is analyzed until the user confirms the data | S-07 | FR-026, TB-02 |
| **TM-02** | Readiness transparency — every capability's availability is explained with a reason | S-04 | R-RDY-07, NFR-062 |
| **TM-03** | Double-confirmation on incomplete reviews accepted | S-05 | trust; NFR-062 |
| **TM-04** | One-click explainability — any number/finding → rule, inputs, source | S-10 | NFR-067, FR-071 |
| **TM-05** | Deterministic-first, AI-distinct — AI content is labeled, attributed, cited, and removable | S-10/S-12/S-20 | NFR-049/050, FR-095 |
| **TM-06** | Correction lineage — original values are never lost when corrected | S-07 | FR-028, NFR-056 |
| **TM-07** | Reproducibility & history — any past review re-displays exactly | S-12/S-18 | FR-079, F-02-06 |
| **TM-08** | Human-in-control — recommendations only; no silent action; no vendor contact | all | 00 §1, FR-083 |
| **TM-09** | Cold-start honesty — "insufficient history" over unreliable results | S-08/S-14 | FR-111 |
| **TM-10** | Audit reconstruction — a reviewer can replay who/what/when for any month | S-18 | E-08, NFR-019 |
| **TM-11** | Consent as the final gate — nothing leaves the app without informed, revocable consent | S-19 | FR-096, NFR-014 |
| **TM-12** | Change ≠ exception — "new" is informational, never a manufactured finding | S-15 | §16.2 of 06, FR-041 |

---

## 22. Error Handling

Principle: **nothing silent, everything actionable** (UXP-08, NFR-062/055/064/063).

- **File errors (S-03):** unreadable/corrupt/password-protected/unsupported files are rejected with a plain-language reason and a specific next step; the rest of the upload continues (no all-or-nothing abort). Hostile/malformed input never crashes the app; it becomes a safe rejection message (NFR-012).
- **Data-quality failures (S-07):** failing rows are quarantined and reported, never dropped silently; the user is told what was excluded and why, and can correct or proceed with the valid remainder (FR-024/025, NFR-062).
- **Analysis/processing failure (S-06/S-08):** the user is told what failed, the impact, and the next step; partial results are never presented as complete (NFR-062).
- **AI failure (S-10/S-12/S-20):** slow/unavailable/refusing/malformed AI degrades gracefully to the deterministic-only experience with a clear "AI unavailable" status — never blocking the review, never substituting fabricated content (NFR-063, UXP-07).
- **Configuration errors (S-17):** invalid configuration is rejected with a clear message; a known-good state is always recoverable (NFR-040).
- **Recovery, not restart:** file/data errors guide the user to resolution (replace file, correct row, adjust template) without restarting the cycle (NFR-064); crash/force-kill loses no verified work and resumes from the last consistent state (NFR-005/006).
- **Traceability:** NFR-005/006/012/024/040/055/062/063/064; FR-007/024/025.

---

## 23. Empty States

Empty states are teaching moments, not dead ends (UXP-01/08).

| Context | Empty state experience |
|---|---|
| First launch / no reviews | Welcome + orientation (§5.1) + a single clear "Create your first review"; optional historical import (R2) |
| New review, nothing uploaded | Show all document-type slots with brief "what this is" help; make clear uploading only some files is fine |
| Readiness with a subset | Show what's ready and, for each unavailable capability, the concrete missing prerequisite and how to provide it |
| Findings with zero findings | A clear, reassuring "no exceptions found for [capabilities run]" — with which capabilities ran and which were unavailable, so "no findings" is never ambiguous |
| History/Compare with only one review | Explain a comparison needs a prior review; offer historical import |
| Cold start for history-based checks | State plainly that some checks need more months of history and will improve over time (FR-111) |
| AI not configured | Q&A/narration surfaces explain AI is optional and how to enable it; the deterministic experience is fully present regardless (FR-095) |

A "no findings" empty state must always state **what was checked** — an empty inbox after a partial review must not read as "all clear" (TM-02/TM-09).

---

## 24. UX Risks

| ID | Risk | Impact | Notes |
|---|---|---|---|
| **UXR-01** | Verification-gate friction — users find the mandatory review slow and resist adoption | High | Adoption killer if slower than manual (NFR-068); mitigated by bulk-approval/attention-routing (§25) |
| **UXR-02** | Alert fatigue — too many low-value findings bury the critical ones | High | Progressive disclosure + change≠exception + accounting-event awareness are the antidotes |
| **UXR-03** | "Dashboard drift" — the product creeps toward a module/dashboard feel, losing the guided-review identity | Med | The step wizard and review-centric IA are the guardrails (UXP-01/02) |
| **UXR-04** | AI over-trust — users treat AI narration as authoritative | High | Visible distinction, labeling, citation, and deterministic-first (TM-05); never load-bearing |
| **UXR-05** | Readiness confusion — users don't understand why a capability is unavailable | Med | Named reasons + next steps + double-confirmation (TM-02/03) |
| **UXR-06** | Score misread — Review Health Score mistaken for a financial rating | Med | Explicit "operational, not financial" framing and separation from RAG (§18) |
| **UXR-07** | Correction anxiety — users fear editing extracted values will lose the original | Med | Visible correction lineage; original always preserved (TM-06) |
| **UXR-08** | Over-confirmation — too many confirmations train users to click through | Med | Reserve hard gates for verification and incomplete-review continue; keep others informational |
| **UXR-09** | Screen-inventory creep — new screens not traceable to a locked feature | Med | S-inventory (§8) admits only feature-traceable R1 surfaces (F-14-01 guardrail) |
| **UXR-10** | Accessibility as afterthought — color-only meaning or keyboard gaps slip in | High | DoD clause 8 enforced per story; color-independence is binding (NFR-025) |

## 25. UX Recommendations

1. **Make verification fast, not optional.** Default to bulk-approving high-confidence data and route attention only to low-confidence/quarantined items (NFR-069) — protect the gate (TM-01) while beating the manual baseline (UXR-01/NFR-068).
2. **Keep the step wizard the hero.** The numbered "Step X of 8" sequence is the product's identity and its wayfinding; resist adding competing top-level destinations (UXR-03).
3. **Reserve hard gates.** Only verification (DP-2) and continue-anyway (DP-1) block; everything else informs (UXR-08).
4. **Design "no findings" and "unavailable" as first-class states** that always say what was and wasn't checked (§23; TM-02).
5. **Label and separate AI everywhere it appears**, and prove the AI-off experience is complete in usability testing (TM-05, FR-095).
6. **Test with both a technical Operator and a non-technical Leader** on a real month, measuring effort vs. the manual baseline (NFR-068) and comprehension of the summary without training.
7. **Instrument comprehension of readiness reasons and Review Health framing** to catch UXR-05/06 early.
8. **Accessibility acceptance per story**, not a final pass: keyboard path, screen-reader labels, and color-independence checked as findings are built (UXR-10).

## 26. Future UX Considerations

- **Web / multi-user experience** — role-appropriate views for PM, finance partner, vendor manager, executive; authenticated identity replacing local OS user (00 §10, NFR-071). The review-centric IA and step wizard carry over; roles filter visibility.
- **Interactive historical comparison and trend exploration** (S-14 depth) and **cross-cycle risk tracking** (recurrence) as the history corpus grows.
- **Review Health Score** (S-16) activation with tuned, transparent contributing signals.
- **What's New** (S-15) full entity-change detection (XP-04) and its relationship to the summary.
- **Richer Q&A** and AI narration surfaces as E-09 matures, always under the consent/labeling/citation discipline.
- **Extended document types** (invoices, POs, SOWs, rate cards, resource/contract sheets) surfaced through the same upload/readiness/verify/findings flow as they arrive (XP-02; OQ-2 samples resolved under the approved baseline).
- **Notifications** (external alerts) — explicitly out of MVP (FR-083); a future consideration only.

---

## 27. Traceability to Requirements, Features, Rules, and Architecture

This UX design is a derived artifact: every experience answers to approved scope and the baselined architecture, and introduces none of its own (new patterns are accepted/`FUTURE` and grounded).

**27.1 Experience → feature · rule · component**

| Experience (§) | Requirements | Features | Rules | Architecture component |
|---|---|---|---|---|
| Review creation (§9) | FR-005/006 | F-01-01 | — | C-02 |
| Upload (§10) | FR-001/002/003/004/007/008/010; NFR-012 | F-01-02/03/04 | R-RDY-01 (schema at extract) | C-03 |
| Readiness (§11) | FR-081/111; NFR-062 | F-01-08 | R-RDY-05/06/07 | C-05 |
| Processing (§13 in) | NFR-002/003/004/055 | F-14-03 | — | C-02/C-04/C-07 |
| Verification (§12) | FR-016/026/027/028/029; NFR-069 | F-01-09 | R-RDY-* (quality), gate to R-* | C-06 (TB-02) |
| Analysis (§13) | NFR-003/004/055; FR-111 | F-14-03 | R-BUD-*/R-GED-*/R-REC-* | C-07/C-11 |
| Findings (§14) | FR-069/070/072/074/082/102; NFR-066/067 | F-06-01/03/04 | R-FND-01/02/03 | C-09b over C-09a |
| Explain This (§15) | FR-071/091/094/099; NFR-050/067 | F-06-02 | R-FND-01/02 | C-09a/C-09b (+C-15 R2) |
| Reconciliation (§14/S-11) | FR-044–050 | F-05-02 | R-REC-01..05 | C-10 |
| Summary (§16) | FR-076/077/078/079/080/095/116/120 | F-07-01/03/04 | R-RPT-01/02/03 | C-12 |
| Historical comparison (§17) | FR-078/108/109 | F-07-02 (R2), F-06-05 | R-HST-02/03 | C-13 |
| Review Health (§18) | 06 §16.3 (FUTURE) | (future) | (future aggregate, XP-05) | C-13 |
| What's New (§19) | FR-078/032/041 (FUTURE detection) | (future) | R-HST-04 | C-13 |
| Configuration (S-17) | FR-103/104/105/106/107; NFR-039/040/041 | F-14-01, F-08-03 | CP-* register (§4 of 05) | C-18 |
| Audit (S-18) | FR-084–090; NFR-019 | F-08-02 | — | C-14 |
| Consent / Q&A (S-19/S-20) | FR-096/100/101/102 | E-09 (R2), F-06-04 | — | C-15/C-16, C-09b |
| Accessibility (§20) | NFR-024/025/026/027/065/055 | F-14-05 | — | C-01 |
| Error handling (§22) | NFR-005/006/012/040/055/062/063/064 | F-14-02, F-01-08 | — | C-01/C-05/C-06/C-17 |

**27.2 Trust mechanism → source** — see §21 (each TM cites its FR/NFR/architecture boundary).

**27.3 Coverage & no-conflict statements**

- **Every stage of the primary flow** described in the UX vision maps to a screen responsibility (§8) and an owning architecture component (§27.1); no experience is orphaned, and the flow matches the architecture's cycle state model (06 §6.2).
- **Every UX-visible R1 feature** has a screen; **R2/FUTURE experiences are marked as such** (Historical comparison R2; Review Health & What's New FUTURE; AI narration/Q&A R2) so the design is a complete vision while remaining release-honest (DEC-022/023). No R2/FUTURE experience is presented as R1 scope.
- **New UX patterns are grounded and labeled:** the double-confirmation trust check (S-05) is accepted, grounded in NFR-062 and the trust goals; the Review Health and What's New surfaces are `FUTURE`, grounded in 06 §16 — none introduces a requirement beyond the approved set; any elevation goes through the decision log (DEC-019 discipline).
- **UI concerns are deferred, not decided:** this document specifies information, actions, decisions, guidance, and accessibility *requirements* only — no colors, themes, typography, styling, or design system (per directive). The future UI phase realizes the visual language against these responsibilities.
- **No conflict introduced:** the design respects Trust > AI and Monthly Review in a Box (DEC-022), the verify-before-analyze gate (FR-026, TB-02), AI-optional completeness (FR-095), single-user MVP (DEC-008), color-independent meaning (NFR-025), and the catalog/architecture/requirements boundaries; it weakens no Must.

**27.4 Downstream obligation**

The future UI Design document will realize each screen responsibility (§8) into a visual design without changing its responsibilities, decisions, or accessibility requirements. Feature plans (`specs/plans/`) will reference these screen IDs; `/sdd:trace` will link experience → feature → plan → task → code → test.

---

*End of 07-ux-design.md — UX design only (journeys, workflows, information architecture, navigation, decisions, trust, guidance, onboarding, accessibility, and screen responsibilities). Visual design — colors, themes, typography, styling, branding, design systems — is deferred to a future UI Design phase. Reviewed by the team and the design-review board (UX + accessibility focus: ux-designer, accessibility-engineer, plus a Finance Operations reviewer for workflow fit) and approved in the current baseline.*
