# FinSight — Human Approval Guide (for stakeholders and decision-makers)

*A plain-language guide to the decisions that need your sign-off before building begins. No software or finance background required. Where a technical term is unavoidable, it is explained the first time it appears.*

---

## 1. Executive Summary

**What FinSight is.** FinSight is a **guided monthly financial-review assistant**. Each month, the person responsible for reviewing a department's spending must check the budget against what was actually spent, look for missing, duplicated, or unusual entries, reconcile records, and produce a summary for leadership. Today that work is done by hand across spreadsheets, PDFs, and email. FinSight walks the user through that same review, step by step, and does the checking for them — like guided tax-preparation software walks you through a tax return.

**The problem it solves.** The current process is slow, easy to get wrong, and hard to audit. Overspending can be noticed too late; duplicate or missing entries can slip through; and there is no single, trustworthy monthly record.

**Two promises that define the product.** (1) **The numbers are always the system's, produced by fixed, repeatable rules — never guessed.** (2) The optional artificial-intelligence helper ("AI") only *explains* the numbers in plain language; **it can never change them, decide anything, or take action.** We call this **"Trust over AI."**

**Why this approval package exists.** The design of FinSight is now complete and fully documented. Before any building starts, the people accountable for the project must formally approve the decisions and the scope. This protects the organization: nothing gets built that wasn't approved, and there is a clear record of who approved what.

**Where the project stands today.** Everything that can be prepared without a human decision has been done: the full design is written, organized into a controlled structure, and checked for consistency. The project is now **waiting only on your approvals** to begin building a small, first working slice (explained in Section 5). No building has started.

---

## 2. Why FinSight Matters

**Challenges users face today**
- The monthly review is manual: copying data between spreadsheets, cross-checking by hand.
- Mistakes (a duplicate payment, a missing entry, an overspend) are easy to miss and often caught late.
- Producing a clear leadership summary takes real effort every month.
- There is no single, reliable, auditable record of what was reviewed.

**How FinSight helps**
- It guides the user through the review in clear steps, so nothing is skipped.
- It does the repetitive checking automatically and flags issues with their evidence.
- It produces a leadership-ready summary.
- It keeps a complete record of every action for audit.

**Expected benefits for users**
- Less manual effort each month, with attention focused on the things that actually need judgment.
- More confidence that problems are caught systematically rather than by chance.
- The ability to explain and trust every number, because each traces back to its source.

**Expected benefits for the business**
- Faster, more consistent monthly reviews.
- Better spending oversight and earlier warning of problems.
- A defensible audit trail and stronger financial governance.

*(These are the outcomes the product is designed to deliver; they are proven gradually as the product is built and piloted.)*

---

## 3. Approvals Required

These are the decisions that need a human sign-off. **None can be made by the software itself** — the project's rules require that people, not the AI, make every decision.

**a) Decision ratification**
- *What it is:* eleven design decisions made during the design phase (about the guided step-by-step experience, the single AI helper, and similar) are written down but still marked "proposed."
- *Why approval is needed:* they underpin the whole design; they should be officially confirmed before the scope is locked.
- *If approved:* the design rests on confirmed foundations.
- *If rejected (or changed):* the affected design areas are revised first.
- *Impact on FinSight / users:* confirms the product experience everyone has been designing toward.

**b) Constitution adoption**
- *What it is:* a short governing document listing the project's non-negotiable principles (e.g., the numbers are always exact and repeatable; the user must review data before it is analyzed; the AI never decides), a shared glossary of terms, and who is allowed to approve what.
- *Why approval is needed:* it is the rulebook everything else follows.
- *If approved:* the project has an agreed, stable set of ground rules.
- *If rejected:* the ground rules are re-agreed before proceeding.
- *Impact:* protects the product's trustworthiness for the life of the project.

**c) Workbook approval**
- *What it is:* a checklist of every requirement, capability, and rule in the product, in business language, for you to mark **Approve** or **Disapprove** item by item.
- *Why approval is needed:* it is the formal record that humans reviewed and accepted the scope — not the AI that drafted it.
- *If approved:* the scope is confirmed and can be "locked."
- *If rejected (per item):* that item is revised or removed before locking.
- *Impact:* ensures the product does exactly what stakeholders agreed to, with an audit record of the approval.

**d) Baseline approval**
- *What it is:* "locking" the approved design into a sealed, tamper-protected snapshot (the "baseline") that building will be measured against.
- *Why approval is needed:* it fixes the agreed scope so later changes must go through a formal change process.
- *If approved:* the team builds against a stable, agreed target.
- *If rejected:* scope stays open and building shouldn't start.
- *Impact:* prevents uncontrolled "scope creep" and gives a clear reference point.

**e) Architecture-decision acceptance**
- *What it is:* seven recorded technical decisions (explained in plain English in Section 4).
- *Why approval is needed:* they are the load-bearing engineering choices; building should not start against unconfirmed ones.
- *If approved:* the technology direction is settled.
- *If rejected:* the relevant decision is revised first.
- *Impact:* determines that the product will be reliable, trustworthy, and maintainable.

**f) Plan approval**
- *What it is:* the plan for the first small building slice (the "walking skeleton," Section 5).
- *Why approval is needed:* it defines exactly what will be built first, and what is deliberately left out.
- *If approved:* building of the first slice is authorized.
- *If rejected:* the plan is adjusted first.
- *Impact:* sets a focused, low-risk starting point.

**g) Authorization to begin the first task**
- *What it is:* the final "go" to start the very first piece of building work.
- *Why approval is needed:* building only begins on an explicit human authorization, once everything above is done.
- *If approved:* work starts.
- *If rejected/withheld:* work waits.
- *Impact:* the controlled, accountable start of construction.

---

## 4. Architecture Decisions in Plain English

There are seven recorded technical decisions ("Architecture Decision Records," or **ADRs** — simply written records of a technical choice).

**Decision 1 — What the software is built with (ADR-001).**
*What:* the "engine" that does the calculations is built with a reliable, widely-used programming language; the on-screen part uses standard web-page technology inside a lightweight desktop window.
*Why it matters:* it must run on ordinary Windows and Mac work laptops, work without an internet connection, and keep the door open to a future web version.
*Benefits:* reliable, portable, offline-capable, and cheaper to move to the web later.
*Risks:* installing this kind of app on tightly locked-down work laptops needs a quick proof-of-concept test first (a "spike"); a proven backup option is ready if needed.
*User impact:* it runs on their own laptop without special IT permissions.

**Decision 2 — Building a wall so the AI can never change the numbers (ADR-002).**
*What:* the software is organized so the calculation engine is walled off from the AI helper. The AI can only **read** results; it has **no ability** to create or change a number or a finding.
*Why it matters:* it turns "Trust over AI" from a promise into something built into the structure.
*Benefits:* users can always trust that the figures came from the rules, not from AI.
*Risks:* the wall is kept in place by automatic checks that must always run; the project treats those checks as essential.
*User impact:* confidence that AI never quietly alters the numbers.

**Decision 3 — Making the math exact and repeatable (ADR-003).**
*What:* money is handled with exact arithmetic (no rounding surprises), and the same inputs always produce the same result — on any laptop, every time.
*Why it matters:* a financial report cannot be a cent off or give different answers on different machines.
*Benefits:* results are reproducible and auditable.
*Risks:* it requires disciplined coding and testing, which are built into the process.
*User impact:* consistent, trustworthy figures they can stand behind.

**Decision 4 — Where the data is stored (ADR-004).**
*What:* data is kept in a simple, self-contained file on the user's laptop — no separate database server to install.
*Why it matters:* it works offline, is easy to back up (a single file), needs no IT server, and can later move to a shared server without redoing the product.
*Benefits:* simple, portable, private.
*Risks:* because it lives on one laptop, backups matter, and protecting the data (encryption) is added before any real data is used.
*User impact:* their review data stays on their own machine.

**Decision 5 — Keeping a complete record of everything (ADR-005).**
*What:* every meaningful action is recorded, so any past month's review can be reconstructed — who did what, when, and with which settings.
*Why it matters:* being auditable is one of the product's core reasons to exist.
*Benefits:* trust and readiness for audits.
*Risks:* making the record tamper-evident is planned as a later enhancement (the record is complete from the start; extra tamper-proofing comes next).
*User impact:* a defensible record if anyone asks "how was this month reviewed?"

**Decision 6 — Nothing is analyzed until the user approves it (ADR-006).**
*What:* the software is built so it literally cannot run its analysis on data the user has not first reviewed and confirmed.
*Why it matters:* the human stays in control; there are no surprises from unreviewed data.
*Benefits:* trust, and clear human ownership of what gets analyzed.
*Risks:* the review step must be quick so it doesn't slow people down; it is designed for speed.
*User impact:* they confirm the data first; every result is based on what they approved.

**Decision 7 — One consistent list of issues (ADR-007).**
*What:* every issue the system finds is shown in one consistent format — with a severity level, its supporting evidence, and a link to where it came from — no matter which kind of check found it.
*Why it matters:* one clear place to look, no confusion between different "systems."
*Benefits:* easy to understand, prioritize, and investigate.
*Risks:* the team must keep it unified as more checks are added; this is enforced.
*User impact:* a single, simple, consistent list of things needing attention.

---

## 5. The "Walking Skeleton" Explained

**What it is.** The first thing to be built is a deliberately tiny but *complete* version of the product, called the **walking skeleton**. It runs the whole process end-to-end — just with one of everything.

**Why we build it first.** It proves that all the important pieces work together *before* investing in building every feature. It is like building one fully working room of a house — with real plumbing, wiring, and a door that opens — to prove the foundations and utilities are sound, before building all the other rooms.

**What a user will be able to do with it.** Start a monthly review, upload two files (the expense-detail report — called the **GED**, short for *General Expense Detail* — and the budget file), let the system read them, **review and confirm** the data, run **one** budget check, see **one** finding (for example, an over-budget account) with its evidence, read **one** summary line, and produce **one** export. A small, but genuinely real, monthly review.

**What is intentionally left out (and added later).** The AI helper (called "Fin") is **not** in this first slice — the product works fully without it. Also excluded for now: invoice checking, most of the checking rules, historical comparisons, and polished screens. These come in later, planned stages.

**Important note about the data.** The first slice is built and tested using **made-up (synthetic) sample data only** — never real financial data. Before the product is used on real information, the actual "what counts as a problem" thresholds must be provided by finance (see the risks below).

---

## 6. Risks and Mitigations

**Risk: the results may not be trustworthy at launch because the thresholds aren't set yet.**
*What could happen:* the checks decide what is "over budget," "unusual," or a "duplicate" using values (thresholds) that the finance team has not yet provided; using placeholder values on real data could produce misleading results.
*How the project mitigates it:* the checking logic is built now using test data and placeholder values; the real thresholds are treated as a separate, owned task that must be completed by finance **before any real-world use.**

**Risk: installing the app on locked-down work laptops could be difficult.**
*What could happen:* corporate security settings can block software installation.
*How the project mitigates it:* a quick proof-of-concept test is done first; a well-established backup technology is ready if the preferred one doesn't fit the environment — with no impact on the product's inner workings.

**Risk: with a small team, approvals could become a formality.**
*What could happen:* one person approving everything reduces independent scrutiny.
*How the project mitigates it:* this guide plus explicit, recorded sign-offs and a review panel make each decision visible and accountable.

**Risk: building too much, too soon.**
*What could happen:* effort spreads thin and nothing is proven.
*How the project mitigates it:* the walking-skeleton-first approach and a strictly limited first scope keep the team focused.

**Risk: over-relying on the AI helper.**
*What could happen:* people might trust AI explanations as if they were the source of truth.
*How the project mitigates it:* the AI is optional, always clearly labeled, cannot change any number, and the product works completely with the AI switched off.

---

## 7. Decisions Required Now

*You should be able to work from this checklist alone.*

- [ ] **Confirm the eleven proposed design decisions.** *These lock in the agreed product experience (the guided steps, the single AI helper, and related choices). Approving lets the scope be finalized.*
- [ ] **Adopt the Constitution (the project rulebook).** *Confirms the non-negotiable principles and who may approve what. Everything else follows it.*
- [ ] **Approve the Workbook (the scope checklist).** *Your item-by-item Approve/Disapprove is the formal record that humans accepted the scope. Pay closest attention to the items marked as proposed or assumption-based.*
- [ ] **Approve the Baseline (lock the scope).** *Seals the approved design as the stable target for building; later changes go through a formal change process.*
- [ ] **Accept the seven technical decisions (Section 4).** *Settles the engineering direction so building can begin against confirmed choices. One of them (the technology choice) depends on the quick installation test.*
- [ ] **Approve the first-slice Plan (the walking skeleton).** *Authorizes exactly what will be built first and what is left out.*
- [ ] **Authorize the first task.** *The explicit "go" to begin building, once everything above is done.*

*For each item: approving moves the project forward; declining pauses that area for revision. None of these can be approved by the software — they are human decisions by design.*

---

## 8. Implementation Readiness Summary

**What has already been completed (no approval needed):**
- The full product design — the problem, requirements, capabilities, checking rules, structure, the guided experience, and the optional AI approach — is written and internally consistent.
- The design has been organized into a controlled, checkable structure and passed automated consistency checks.
- All the preparation a computer can do without a human decision is finished: the scope checklist, the technical-decision records, the first-slice plan, and all the "ready-to-build" materials (including ready-to-use setup instructions for the team).

**What remains:**
- The seven human approvals in Section 7.
- Setting up the building environment (creating the project's code home and the automated quality checks) — a practical setup step by the team.
- Finance providing the real thresholds — required before real-world use, not before the first test slice.

**Why the remaining steps exist:**
- The approvals exist because **people, not software, must own every decision** — this is a core project principle and the source of the product's trustworthiness.
- The environment setup and the thresholds are practical steps that come at the right moment: setup just before building, and real thresholds just before real use.

---

## 9. Final Recommendation

**Current state.** FinSight is **thoroughly designed, fully documented, internally consistent, and prepared for construction.** An independent review found no unresolved contradictions in the design. Everything that could be prepared without a human decision has been done.

**Is it ready to proceed?** **Yes — pending the human approvals in Section 7.** The project is deliberately paused at the point where people must take ownership. There are no hidden design problems blocking progress; the remaining steps are the approvals and the practical setup.

**What is needed before building begins.** Complete the Section 7 checklist (confirm the design decisions, adopt the Constitution, approve the scope checklist, lock the baseline, accept the seven technical decisions, approve the first-slice plan, and authorize the first task), and set up the building environment. Two conditions should be tracked but do **not** block the first test slice: (1) finance provides the real thresholds before any real-world use; (2) the quick installation test confirms the app installs cleanly on the target laptops.

**Recommendation.** Proceed with the approvals to begin the small, low-risk first slice. It is designed precisely to prove the foundations work — on made-up data, with no AI, and with the human firmly in control — before any larger investment. Approving it commits the organization to a careful, well-governed start, not to the full product.

---

*This guide summarizes existing, approved design materials in plain language for decision-making. It introduces no new requirements, features, or approvals. The detailed source documents (the Constitution, decision log, technical-decision records, plan, scope checklist, and readiness packages) are available for anyone who wishes to go deeper.*
