# FinSight — Development Methodology

**Document:** 11-development-methodology.md
**Status:** Approved
**Date:** 2026-07-16
**Scope:** How FinSight is **built, tested, reviewed, verified, and delivered** — the workflow, governance, traceability, quality gates, AI-assisted-development rules, and Definition of Done. This is **not** a product-design document; the design phase (00–10) is complete. This document governs *implementation*.
**Governing methodology:** Spec-Driven Development (DEC-010, NFR-073). This document operationalizes the SDD framework already adopted by the project (the `sdd` and `engineering-standards` plugins) for FinSight specifically.
**Sources of truth:** 00-project-understanding.md · 01-functional-requirements.md · 02-non-functional-requirements.md · 03-epics.md · 04-features.md · 05-rules-catalog.md · 06-architecture.md · 07-ux-design.md · 08-ui-design-system.md · 09-decision-log.md · 10-ai-and-agents.md · the Final Specification Review and Build-Readiness recommendations · DEC-001–DEC-034.
**Numbering note:** produced as `11-development-methodology.md` per the renumbering (DEC-031: UI took `08`, AI took `10`), ratified under the approved baseline.
**Provenance:** AI-drafted for human review and approved by the project owner. Process recommendations not fixed by a source item are the simplest option consistent with the approved NFRs; none weakens a governance requirement. This methodology is Approved in the current baseline.
**Status note:** this methodology is in effect under the approved baseline; `specs/` is the authoritative approved and enforced build baseline.

---

## 1. Development Philosophy

**Specifications determine truth. AI assists developers.** This deliberately mirrors the product itself — *rules determine financial truth; Fin explains* (10 §1). In development: the approved, baselined `specs/` are the single source of truth; tools (including AI) help engineers understand and draft, but never decide and never become authoritative.

Five philosophy commitments govern every choice below:

1. **Trust > AI applies to how we build, not just what we build.** Deterministic behavior must be testable, financial calculations reproducible, rules verifiable, cross-platform results identical, and accessibility continuously protected (NFR-021/029/036/059; DEC-005). These are *build-time* obligations, enforced by tests and gates, not aspirations.
2. **Match process weight to risk and change type.** The deterministic core, audit, and the deterministic/AI boundary get the most rigor; bug fixes and behavior-preserving refactors get the least. Ceremony that does not reduce a real risk is removed (NFR-032 "no shortcuts" is about *engineering discipline*, not paperwork).
3. **Humans are accountable for everything that ships.** Every artifact — human- or AI-generated — passes the same review, test, and traceability gates (NFR-074/075/080, DEC-010). No tool launders responsibility.
4. **Traceability is a property of the work, not a report we write later.** Code and tests carry their requirement IDs; the matrix is generated, not hand-maintained (traceability skill; NFR-033).
5. **Small, purposeful, reviewable changes.** No unreviewable bulk changesets enter the main line (NFR-080); a task is roughly half a day of work (framework `/sdd:tasks`).

## 2. Spec-Driven Development Workflow

FinSight builds on the two shipped plugins: **`sdd`** (17 commands · 5 spec agents · 6 method skills · 3 enforcement hooks) — the gated workflow engine — and **`engineering-standards`** (20 principal reviewer agents, convened as panels) — the review board. The full lifecycle is **10 gates in three movements**; commands refuse out-of-order work and name the exact command that clears the missing gate (refusals are navigation, not friction).

```
SHAPE THE SCOPE            APPROVE & SEAL              DELIVER (per feature, repeated)
specify → clarify →        workbook → baseline         plan → adr → tasks → implement → verify
decompose                  (human gate) (immutable)    (design panel) (as needed) (TDD)    (evidence)

Always on:  /sdd:status (next step) · /sdd:analyze (cross-artifact defects) · /sdd:trace (matrix + CI verdict)
Change:     /sdd:change → CR-### + impact analysis (baselines immutable; working specs edit then re-baseline)
```

**For FinSight, the SHAPE and APPROVE movements are already done** (00–10 designed and approved; baseline established under the approved baseline). Day-to-day development lives in the **DELIVER movement**, one feature at a time, starting with the **walking skeleton** (DEC-022; §18/§20). Enforcement runs *outside the model* via hooks: session-status injection, **baseline immutability (PreToolUse hard block)**, and spec-lint on every edit — no prompt can edit a sealed baseline.

## 3. New Feature Delivery Process (full SDD — no bypass of traceability)

Every new feature follows the complete path. This is the high-rigor process because new behavior is where scope, cost, and risk enter.

```
Requirement (FR/NFR, baselined) → Feature (F-##-##) → Plan (PLAN-F-##-##, design panel)
→ ADR (when a load-bearing decision is made) → Tasks (T-###) → Implementation (TDD) → Verification (VERIFY-F-##-##)
```

1. **Precondition (gate):** the feature exists in baselined `04-features.md` and every FR/NFR it traces to is `Baselined`. `/sdd:plan` refuses otherwise.
2. **Plan** (`/sdd:plan F-##-##`): name components, contracts, failure behavior; list **every NFR that traces to the feature with its measurable fit criterion** and the design constraint it imposes; state test strategy (unit/golden/determinism); submit to the **design panel** (`software-architect, data-architect, integration-architect, security-engineer, qa-engineer`) via `/sdd:review-board`. Status → Approved only after the panel outcome is *approve* (or conditions resolved). Convene extra reviewers by trigger: **accessibility-engineer** for any UI feature, **security-engineer** for anything touching consent/egress/secrets/untrusted input, **ai-governance-reviewer** for anything touching the Fin layer.
3. **ADR** (`/sdd:adr`, when required): record load-bearing decisions (Nygard format + Traces-to + Verification); never inline a decision in a plan; accepted ADRs are append-only (supersede via a new ADR). The architecture's ADC-01–11 (06 §26) are raised here.
4. **Tasks** (`/sdd:tasks F-##-##`): decompose into ordered, ~half-day, individually testable `T-###` checkboxes; each names the FR/NFR IDs it verifies up front.
5. **Implement** (`/sdd:implement`, one task per invocation, **test-first**): write the failing test → minimal code → quality gates green → annotate `Implements: FR-###, F-##-##` (and `Verifies:` on tests) → tick the checkbox → commit `[F-##-##]`.
6. **Verify** (`/sdd:verify F-##-##`): execute every acceptance criterion with recorded evidence; statuses flip to **Verified only on a full pass — no partial credit**; the `/sdd:trace` verdict gates CI.

**Rule packs** (05) follow this path with the **binding golden-dataset acceptance** (04 §2.1): a seeded synthetic month produces exactly the expected findings, severities, and evidence.

## 4. Bug Fix Process (lightweight)

A **bug** is a deviation from *already-specified* behavior. Fixing it restores the spec; it does not change scope, so it does not need plan/tasks artifacts.

```
Bug (report) → Root cause → Fix → Test (regression) → Verify → Merge
```

- **Record** the bug against the FR/feature it violates (a one-line trace, not a plan). A bug with no owning requirement is a signal the spec is incomplete → escalate to a CR (§17).
- **Regression test first.** Reproduce with a failing test (for a rule/finance defect, extend the **golden dataset**); the fix makes it pass. This is non-negotiable for the deterministic core and audit (NFR-036).
- **Annotate & commit:** touched code keeps its `Implements:` trace; commit `[fix]` referencing the bug ID and the affected `F-##-##`.
- **Review:** peer review always; add the relevant specialist reviewer only if the fix touches their domain (security/accessibility/determinism).
- **Escalation rule:** if the "bug" is actually *intended behavior someone dislikes*, it is **not a bug** — it is a **change request** (§17). Fixing a spec deviation = bug; changing the spec = CR. This one distinction prevents scope creep disguised as bug fixing.

## 5. Refactoring Process (lightest)

A **refactor** changes structure, not behavior. If behavior is identical, existing tests are the safety net and no planning artifacts are created.

```
Refactor → Tests pass (incl. golden + determinism + provider-swap unchanged) → Review → Merge
```

- **The proof of a good refactor is green tests, especially golden-dataset determinism** (NFR-036/037/029): if deterministic outputs change, it was not a refactor — it was a behavior change and must become a bug fix or CR.
- **No new artifacts.** No plan, no tasks, no ADR — unless the refactor changes an **architecture boundary** (layering, ports, DAL). Boundary-touching refactors get a **software-architect** review and, if the boundary decision itself changes, an ADR.
- **Small and purposeful** (NFR-080); named, behavior-preserving transformations (Refactoring canon). Bulk mechanical refactors are split into reviewable commits.

**Process-selection triage (the one decision that routes all work):**

| The change… | Route |
|---|---|
| adds or alters intended behavior/scope | **New feature / CR** (full SDD or `/sdd:change`) |
| restores specified behavior that broke | **Bug fix** (lightweight) |
| changes structure only, behavior byte-identical | **Refactor** (lightest) |

## 6. Repository Strategy

**One repository** for FinSight, containing everything that must stay in lockstep:

```
finsight/
├── specs/                     ← the enforced source of truth (constitution, 00–11, baselines, adr, plans, tasks, verification, workbooks, reviews, traceability.md)
├── src/                       ← application core (deterministic engine, rules, findings, cycle model) + delivery shell + DAL + AI (Fin) layer
├── tests/                     ← unit, golden-datasets (synthetic only), determinism, provider-swap, accessibility
├── .claude/ (settings, plugins pinned to release tags) · CI config · CHANGELOG.md
```

- **Rationale:** traceability links code ↔ spec **in one place**; the `Implements:`/`Verifies:` annotations and `/sdd:trace` scan one tree. Splitting spec and code across repos breaks the matrix and the baseline hook. The architecture's substitutability (DAL, provider adapter, web migration — NFR-070/072) is a **module boundary**, not a repo split.
- **Synthetic data only** lives in the repo; **no real customer data, ever** (NFR-018, DEC-010). A checked-in guard/lint rejects anything resembling real data in fixtures.
- **Plugins pinned to release tags** in committed settings so every teammate gets the same gated toolchain (zero-touch rollout).

## 7. Branching Strategy

**Trunk-based with short-lived branches** — the simplest strategy that keeps changes small and reviewable (NFR-080). Avoid heavyweight gitflow.

- `main` is always releasable and protected: merges require green CI (including `TRACEABILITY: PASS`), passing determinism/golden/accessibility suites, and required reviews.
- **Short-lived branches**, named by work item: `feat/F-02-01-rule-registration`, `fix/BUG-142-reclass-false-dup`, `refactor/dal-repo-interface`, `adr/ADR-005-decimal-arithmetic`, `chore/...`.
- **Branch life ≤ a few days**; long branches indicate a feature that should have been split at `/sdd:tasks`.
- **No direct commits to `main`.** No force-push to shared branches. Baselines are never edited (hook-enforced).

## 8. Commit Standards

Small, purposeful, traceable commits.

- **Format:** `<type>(<scope>): <summary>  [F-##-## | BUG-### | ADR-###]` where type ∈ {feat, fix, refactor, test, docs, chore, spec}. The **feature/task/bug ID is mandatory** so the commit joins the traceability chain.
- **Code annotations do the heavy lifting**, not commit prose: implementing units carry `Implements: FR-###, F-##-##`; tests carry `Verifies: FR-###/NFR-###`. `/sdd:trace` harvests these.
- **Test-first commits** are visible: a feature task shows the failing test then the implementation (or a single commit whose diff shows both), per `/sdd:implement`.
- **AI-assist disclosure:** if AI materially generated a change, note it in the commit trailer (e.g., `Assisted-by: <tool>`), consistent with human-accountability and provenance (NFR-074, ai-provenance). The human author remains the accountable committer.
- **`spec` commits precede `feat` commits** when behavior changes — the spec change lands (via CR) before the code that implements it (NFR-073).

## 9. Code Review Standards

Peer review is mandatory for **every** change; the framework review board convenes by trigger. Reviewers are **read-only** and report evidence, never edit the thing they judge.

- **Always:** at least one human peer review. AI-generated code gets **the same** review as human code — no exceptions (NFR-075).
- **Trigger-based specialist/panel reviews** (via `/sdd:review-board` or `/engineering-standards:panel`):
  - **Design panel** (`software-architect, data-architect, integration-architect, security-engineer, qa-engineer`) — every **plan**, before code exists.
  - **security-engineer** — consent/egress/secrets/untrusted-input/at-rest paths (secure-defaults skill).
  - **accessibility-engineer** — any UI surface (keyboard, screen-reader, contrast, color-independence, 200% zoom).
  - **data-architect** — the DAL, schema, audit-event schema, migrations.
  - **ai-governance-reviewer** — any change to the Fin layer, grounding, citation, or consent.
- **Finding format (parsed by aggregators, verbatim):** `[SEVERITY] file:line — finding — grounded in <canon · spec-ID> — Fix: <concrete change>`. **Evidence or silence**; **dissent is preserved, never averaged**; a finding without file:line or a spec-ID is not a finding.
- **Merge bar:** no BLOCKER/CRITICAL findings open; conditions from a panel review resolved or ticketed as debt (§16) with an owner; CI green.

## 10. AI-Assisted Development Guidelines

AI-assisted development is **allowed, not required, and never a replacement for engineering judgment.**

- **Developers may use** approved tools (e.g., Claude, GitHub Copilot, ChatGPT, and the team's own coding agents per DEC-010) for: understanding requirements/architecture, drafting code, drafting tests, and general productivity.
- **AI is never authoritative.** Developers remain responsible for **design, architecture, security, code quality, and all review and merge decisions.** Specifications remain the source of truth; **AI must never become it.** *(Rules determine truth, Fin explains ↔ specs determine truth, AI assists developers.)*
- **Same gates, no shortcuts:** AI-generated code passes identical review, testing, and traceability gates as human code (NFR-075); it must carry the same `Implements:`/`Verifies:` annotations and satisfy the same DoD.
- **Confidentiality (critical, mirrors the product):** developers must **never** paste real/confidential customer data into any AI tool; development uses **synthetic/sanitized data only** (NFR-018). Treat external AI tools like any external egress — governed and data-minimized.
- **Human accountability of agent-built code (DEC-010):** where the team's coding agents generate implementation from approved specs, every artifact is human-reviewed and gated before acceptance; humans own the result (NFR-074).
- **Disclosure:** material AI assistance is disclosed in the commit (§8); AI-*proposed* spec/requirement content is labeled `AI-PROPOSED` until a human ratifies (ai-provenance skill).

## 11. Testing Expectations

Testing is written **with** the code; untested code is not done (NFR-035). Suites follow the golden-testing skill.

| Suite | What it proves | Requirement |
|---|---|---|
| **Unit** | each unit's behavior + edge cases; each rule testable in isolation | NFR-035/076 |
| **Golden-dataset** | a seeded synthetic month → exactly the expected findings/severities/evidence (per rule pack) | NFR-036; 04 §2.1 |
| **Determinism** | same verified inputs + config version → byte-identical results; repeated-run comparison, injected clock, exact decimal, explicit ordering | NFR-021/059 |
| **Cross-platform** | byte-identical deterministic results on Windows **and** macOS (CI runs both) | NFR-029 |
| **Provider-swap regression** | swapping/disabling the AI provider changes **no** deterministic output; AI-off completeness | NFR-037/048; FR-095 |
| **Accessibility** | keyboard path, screen-reader semantics, color-independence, contrast, 200% zoom | NFR-024–027 |
| **Security** | no unconsented egress; secrets absent from logs/config; untrusted-input safety | NFR-011/012, ADC-07/08 |
| **Integration** | boundary behavior (verification gate, ports, DAL substitution) | ASR-03/09 |

- **Test-first** (TDD) is the implement loop (§3.5). **Financial logic is independently verifiable by a human against the Rules Catalog** (NFR-076) — tests are readable and explicit, no hidden behavior.
- **Golden datasets replicate real structural quirks** (subtotals, reclasses, accruals, credits, placeholders) with **synthetic data only** (NFR-038/018); their update process is reviewed (a golden change is a reviewed event, not a silent overwrite).

## 12. Accessibility Requirements (continuously protected)

Accessibility is a **per-story gate**, not a final pass (DoD; UXP-09; NFR-024–027). Every UI change:

- preserves **full keyboard operability** and logical focus order (following the step wizard);
- preserves **screen-reader** semantics (landmarks, `aria-current` on the stepper, `aria-live` for progress/findings, table header associations);
- carries **no meaning by color alone** — severity/RAG/status = icon + shape + label + color (NFR-025, the governing UI rule);
- holds **AA contrast** and **200% zoom without breakage** (NFR-026/027);
- is reviewed by **accessibility-engineer** for non-trivial UI, and validated by automated checks plus a manual keyboard/screen-reader pass.

A UI change that regresses any of the above **cannot merge**, regardless of functional correctness.

## 13. Traceability Requirements

Traceability is generated and gated, not asserted (traceability skill; NFR-033).

- **The chain:** `Requirement (FR/NFR) → Feature (F-##-##) → Plan (PLAN-F-##-##) → Task (T-###) → Code (Implements:) → Test (Verifies:) → Verification (VERIFY-F-##-##)`.
- **Annotations in code/tests** are the ground truth: `Implements: FR-###, F-##-##` on implementing units; `Verifies: FR-###/NFR-###` on tests. Rule code additionally cites its `R-<FAM>-##` (05).
- **`/sdd:trace`** regenerates `specs/traceability.md` by scanning `specs/` and the codebase; **do not hand-edit it**.
- **CI gate (merge-blocking):** CI runs `/sdd:trace --fail-on-orphans` and greps the verdict line `^TRACEABILITY: PASS$`. **PASS requires** every Must-priority FR/NFR to have a verified chain and **zero orphans** in both directions (spec→nothing, code→nothing). No merge lands with unimplemented Must scope or unannotated/unapproved code.
- **Orphans are defects:** untraceable code means either a missing approved requirement or scope nobody approved — both are fixed at the spec or the annotation, never by editing the matrix.

## 14. Documentation Requirements

- **Specs are the source of truth; spec changes precede code changes** (NFR-073). New behavior enters via a CR that edits the working specs *before* the implementing commit.
- **Decisions are recorded** as ADRs (`/sdd:adr`) or decision-log entries (material product/project decisions); never as tribal knowledge.
- **User-facing behavior, rules, and configuration parameters are documented and kept current with each release** (NFR-034) — including the Rules Catalog parameter register (05 §4), which is the human-readable contract for `CP-*` values.
- **The decision log stays append-only**; superseded decisions are marked, never deleted.
- **Keep `CHANGELOG.md`** (Keep-a-Changelog format); a version bump approves a changelog entry, not a prose diff.

## 15. Definition of Done

A feature is **not** done because code runs. Done requires **all** of the following (harmonizing the user's DoD with the framework's definition-of-done skill and the epics' 10-clause DoD, 03 §4):

**Functional** — requirement implemented; acceptance criteria satisfied; expected behavior verified (`/sdd:verify` full pass).
**Quality** — tests written *with* the code and passing (unit + golden + determinism + provider-swap where applicable); no open BLOCKER/CRITICAL defects.
**Accessibility** — accessibility requirements verified; keyboard navigation and screen-reader support preserved; no meaning by color alone (§12).
**Traceability** — `Requirement ↔ Feature ↔ Code ↔ Test` chain intact; **no orphaned implementation**; `TRACEABILITY: PASS`.
**Determinism & audit (FinSight-specific, non-negotiable)** — determinism/provider-swap suites pass (NFR-037/048); every material action the story introduces writes audit records through the audit port (DoD clause 1; E-08); lineage to source preserved.
**AI-labeled** — any AI-surfaced content is visually distinct, labeled, and attributed, including in exports (NFR-049).
**Config-governed** — any new parameter is configurable (not hard-coded), versioned, and recorded in analysis audit (FR-107).
**Honest under failure** — errors are visible, actionable, and never present partial results as complete (NFR-062).
**Review** — peer review complete; required governance/panel reviews complete with conditions resolved.
**Documentation** — spec/ADR/decision-log/changelog updates completed where required.
**Real-data-free** — all fixtures/tests synthetic (NFR-018).

Work is finished only when **every** clause is satisfied — for human- and AI-generated code alike.

## 16. Technical Debt Management

- **Debt is tracked, traced, and owned** — logged as items referencing the FR/feature/component they affect, with a named owner and a severity. Untracked debt is the debt that hurts.
- **Hard lines that debt may never cross** (NFR-032 no-shortcuts): the **deterministic core**, **auditability**, the **deterministic/AI boundary**, and the **web-transition posture**. Expedient hacks in these areas are rejected in review, not deferred as debt.
- **Panel conditions become debt items** with owners if not resolved before merge (§9); they are paid down within capacity, not silently forgotten.
- **YAGNI is enforced:** no generic engine/framework before two features demonstrably need the same machinery (the "framework" tripwire, 04/06 §19); rejected speculative features (rule-dependency management, custom report builder) return only via the decision log.
- **False-positive/tuning feedback** (R-FND-05) is human-reviewed evidence for parameter tuning — it never auto-changes rules (preserving determinism).

## 17. Change Management

Changes after baseline go through governed change control — the only way to edit sealed scope.

- **`/sdd:change`** raises a **CR-###** with impact analysis (which FRs, plans, tasks, code are touched); a human decides approve/reject; **approved changes edit the working specs now, and re-baseline is batched at the boundary**; **rejected CRs stay on file** (a resurfacing idea cites the old record).
- **Baselines are immutable** — never edited (PreToolUse hook hard-blocks writes under `specs/baselines/`, forever). You change the *future* baseline, not the sealed one.
- **CR vs bug (the routing rule again):** changing intended behavior = CR; restoring specified behavior = bug (§4).
- **Former open questions (now resolved under the approved baseline):** OQ-5/7/8 (rule parameter values) land as **configuration** (no code/spec change — DEC-019); OQ-1/OQ-3 (AI consent model/endpoint) are resolved; OQ-2 (invoice samples) is resolved for E-12 (DEC-011). Any subsequent change flows through a CR.

## 18. Release Readiness Criteria

A release ships only when **all** hold (NFR-048 is the hard gate):

1. **Determinism proven:** golden-dataset (NFR-036) and provider-swap (NFR-037) suites **pass** — the standing release gate; **cross-platform byte-identical** results on Windows and macOS (NFR-029).
2. **AI-off completeness:** every number, finding, status, and report section is present with **no AI configured** (FR-095 regression).
3. **Traceability PASS:** `/sdd:trace` verdict is `TRACEABILITY: PASS`, zero orphans; every in-scope feature **Verified** with recorded evidence.
4. **DoD across every story** in the release (§15), including accessibility and audit.
5. **Security & privacy:** no unconsented egress; secrets protected; dependency hygiene clean (no known-vulnerable versions — NFR-079); static analysis triaged (NFR-078).
6. **Reliability:** crash-safe/resumable verified (a mid-analysis force-kill loses no verified data — NFR-005); backup/restore succeeds on a replacement machine (NFR-060).
7. **Scope match:** Release 1 = **"Monthly Review in a Box"** (DEC-022) — upload GED + Budget Tracker → verify → budget/GED/reconciliation → findings → executive summary → export, with a full audit trail. AI (E-09) is **not** required for R1; its OQ-1/OQ-3 items are resolved under the approved baseline.

## 19. Governance & Compliance

- **Audit by construction:** every material action logs attributably (E-08; DoD clause); a reviewer can reconstruct any month's review from the audit trail alone.
- **Human accountability end-to-end** (DEC-010): humans approve baselines, decide CRs, and own every merge; AI proposes, humans dispose.
- **Enforcement is ambient, not remembered:** hooks (baseline immutability, spec-lint, status injection), command gate-order refusals, and the CI trace gate make the rules structural.
- **Quality gates apply to all code** regardless of origin (NFR-075); reviewers are read-only (no conflict of interest).
- **Development data hygiene:** synthetic/sanitized only; the confidentiality posture of the product extends to how it is built (NFR-018).
- **Standing determinism/AI-boundary check** on the design board for any change near the Fin layer or the rules engine (NFR-047).

## 20. Build Team Guidance

- **Start with the walking skeleton** (DEC-022): one file → one extraction (lineage) → one verification approval (the gate) → one deterministic rule → one finding → one summary line → one export, with **audit and transactional persistence on from story one** and the cross-platform determinism test running day one. Prove the boundaries before building breadth.
- **First wave, then WIP-limit:** land E-14, E-01, E-02, E-08, E-06 first (nothing works without them — 03 §2); actively work **2–3 epics at a time**, not the whole map.
- **Protect the enabler (E-02):** the Rules Engine blocks E-03/04/05; under-resourcing it stalls the first wave (AR-04). Give it protected capacity.
- **Prerequisite gates before coding** (Build-Readiness review): ratify DEC-024–034; operationalize `specs/` + constitution + first baseline; raise the skeleton's ADRs (ADC-01/02/05/06/09/10/11); generate the trace matrix and wire it into CI.
- **A day in the life (target rhythm):** `/sdd:status` (what's next) → `/sdd:plan` or pick the next unblocked `T-###` → test-first `/sdd:implement` → annotations + commit `[F-##-##]` → PR with required reviews → CI green (determinism + accessibility + trace PASS) → `/sdd:verify` on feature completion. Refusals along the way name the missing gate — treat them as navigation.
- **Practicality over ceremony:** a bug fix is five steps, a refactor is four, only a new feature is the full path. Do not manufacture artifacts a change does not need (§5 triage).

---

## 21. Traceability of this methodology

| Methodology area | Grounded in |
|---|---|
| Spec-driven workflow, gates, refusals | DEC-010, NFR-073; `sdd` plugin (WORKFLOW.md 10 gates) |
| Human accountability / agent-assisted build | NFR-074/075, DEC-010; ai-provenance skill |
| Definition of Done | 03 §4 (10 clauses), definition-of-done skill; NFR-035/049/062; FR-107; E-08 |
| Testing (unit/golden/determinism/provider-swap/cross-platform) | NFR-035/036/037/029/048/059/076; golden-testing skill; 04 §2.1 |
| Accessibility gate | NFR-024–027; UXP-09; 07 §20 / 08 §15 |
| Traceability annotations + CI gate | NFR-033; traceability skill; 06 §27 / 05 §20 / 07 §27 |
| Security/privacy validation | NFR-011/012/018/078/079; secure-defaults skill; ADC-07/08 |
| Change management | `/sdd:change`; DEC-019 (params as config); DEC-011 (invoice gate) |
| Release readiness | NFR-048/029/005/060; FR-095; DEC-022 |
| Repository/branching/commits | NFR-072/080; traceability skill (commit prefixes) |
| Technical debt / YAGNI | NFR-032; 04 §2.4 / 06 §19 |
| Build order (skeleton, first wave, WIP) | DEC-022, DEC-021; 03 §2 |

**Coverage & no-conflict:** this methodology introduces no product scope; it operationalizes the approved NFRs and the SDD framework for implementation. It is consistent with every logged decision (DEC-001–034) and weakens no Must. Its precondition — operationalization into `specs/` with a constitution and first baseline — is the Build-Readiness transition, not a design change.

---

*End of 11-development-methodology.md — how FinSight is built, tested, reviewed, verified, and delivered. Simplest process that preserves governance, traceability, and quality: full SDD for new features, lightweight for bugs, lightest for refactors; specifications remain the source of truth and AI assists but never decides. Submit to the team and design-review board; adopt on completion of Build-Readiness Gate 2 (operationalized `specs/` + constitution + first baseline).*
