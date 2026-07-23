# FinSight AI Development Manifesto

This document explains why the FinSight AI development ecosystem exists and the kind of development culture it enforces. It is written for everyone who touches this work: future Claude Code sessions, ChatGPT, Copilot, human developers, HCL reviewers, and project maintainers.

Read it before you assume what this environment is. This is not just an AI-agent setup. It is a governed, specification-driven development organization for FinSight. Its purpose is to help AI tools implement FinSight faster and more safely — without inventing scope, wasting tokens, bypassing review, or weakening financial-governance controls.

---

## 1. Purpose

The purpose of this ecosystem is to make AI a reliable contributor to FinSight, not an unpredictable one.

AI tools are fast, but speed without governance produces drift: invented requirements, silent scope creep, architecture erosion, and code that no one can trace back to an approved decision. In a financial-governance product, that drift is not a nuisance — it is a defect.

This ecosystem exists to channel AI capability through a disciplined process so that every contribution is:

- **Traceable** to an approved specification.
- **Reviewed** before it advances.
- **Deterministic** where financial truth is involved.
- **Owned** by a human at every decision point.

The goal is not to slow work down. It is to make fast work trustworthy.

---

## 2. Why This Exists

FinSight is a financial-governance system. The people who rely on it need to trust its outputs completely. That trust cannot survive if the software behind it is assembled from guesses.

AI development tools, left unconstrained, tend toward four failure modes:

- **AI drift** — the model's output diverges from what was actually asked.
- **Scope drift** — small, unrequested additions accumulate into unreviewed change.
- **Architecture drift** — layering and determinism rules erode one convenient shortcut at a time.
- **Token waste** — repeated repository reading and redundant reasoning burn resources without adding value.

This workflow exists to protect FinSight from all four. It replaces vague conversation and improvised process with a defined chain: specification first, then plan, then implementation, then verification, then governance review. Each link is explicit so that no one — human or AI — has to guess what "done" or "correct" means.

---

## 3. Development Philosophy

The philosophy is short enough to remember and strict enough to enforce.

**Specification First. AI Second.**
The specification is the authoritative source of truth. AI implements what the specification already decided; it does not decide for the specification.

**Trust > AI.**
When trust and AI convenience conflict, trust wins. Every time.

**Deterministic logic decides; AI explains only.**
Financial findings, severity, approvals, rejections, and financial truth are produced by deterministic, exact-decimal logic. AI may explain those outputs in plain language. AI may not create them, alter them, or override them.

**Humans own the decisions.**
Business decisions, scope, governance, and approvals belong to people. AI proposes and drafts; humans decide and approve.

**AI should reduce work, not create it.**
A contribution that generates more validation burden than it saves is a net loss. The measure of good AI work here is how much verifiable, review-ready progress it produces — not how much text it emits.

---

## 4. What We Are Building

We are building a governed development organization that happens to use AI, not an AI experiment that happens to produce software.

Its structure:

- **Least-privilege context.** Every session reads only the files needed for its assigned task. Nobody loads the whole repository "just in case."
- **Staged, independently reviewed work.** Every stage is reviewed on its own — as a separate, read-only execution of the review capability — before work moves forward. Passing one gate does not grant permission to skip the next, and generation never approves itself.
- **Full-chain testing.** Testing does not check code alone. It validates that the specification, plan, implementation, and results form one consistent chain with no broken links.
- **Governance as the final check.** The governance capability confirms that the final output actually matches the approved original requirements — not a drifted, reinterpreted, or "improved" version of them.

These responsibilities are now expressed as three orchestration agents plus reusable skills and recipes under [`.claude/`](../.claude/); see the [Playbook](playbook.md).
- **Structured artifacts as the communication medium.** Agents communicate through specifications, plans, tasks, and verification records — not through vague, unrecoverable conversation. Artifacts can be reviewed, traced, and trusted; chat cannot.
- **Resource discipline.** Unnecessary repository reading and repeated reasoning are treated as defects. Efficient work reuses established context instead of re-deriving it.

Together these produce software that is fast to build and safe to trust.

---

## 5. What We Are Not Building

Naming the anti-goals keeps them out.

- We are **not** building an autonomous financial actor. FinSight is read-only and human-controlled. No AI approves, rejects, pays, updates a budget, changes governance state, or communicates with a vendor.
- We are **not** building a requirements generator. AI does not invent requirements, thresholds, business rules, architecture, or assumptions. Missing or ambiguous information stops the work; it does not get filled with plausible guesses.
- We are **not** building a review-optional pipeline. No stage advances by skipping its review.
- We are **not** building a tool that trades governance for speed. Speed that weakens financial-governance controls is not acceptable at any velocity.
- We are **not** building a system where AI output is trusted because it sounds confident. Confidence is not evidence. Traceability is.

If a task cannot be traced to an approved specification, requirement, feature, rule, plan, or task, the correct response is to stop and say so — not to proceed.

---

## 6. How Work Should Feel

Good work in this ecosystem has a recognizable feel.

- **Calm and deliberate**, not rushed. You know what you were asked to do, and you do exactly that.
- **Narrow and focused.** You hold only the context you need. You are not swimming through the whole repository to feel informed.
- **Honest about gaps.** When something needed for the task is missing or ambiguous, you name it plainly, explain why it blocks the work, and stop. Stopping to ask is a success, not a failure.
- **Small and reviewable.** Changes are modest, traceable, and easy for the next reviewer to check. No opportunistic edits to unrelated files.
- **Ending in something checkable.** Work concludes with an artifact someone can review and trace, not a claim that it is finished.

If work feels like guessing, sprawling, or racing ahead of review, that is the signal to stop and return to the specification.

---

## 7. Non-Negotiables

These rules do not bend for convenience, deadline, or cleverness.

1. **The specification is the source of truth.** Implementation serves the spec; the spec does not adapt to the implementation.
2. **Deterministic logic decides; AI explains only.** AI never creates findings, severity, financial truth, approvals, rejections, or financial actions.
3. **No autonomous financial action.** A human owns every decision. FinSight remains read-only and human-controlled.
4. **No hallucinated requirements, thresholds, business rules, architecture, or assumptions.** If information is missing or ambiguous, stop and state what is needed.
5. **Least-privilege context for every role.** Read only what the task requires.
6. **Independent review before advancing.** Every stage is reviewed on its own merits before the next begins.
7. **Full-chain validation by Testing.** The Testing role validates the entire chain, not only the code.
8. **Governance confirmation at the end.** The Governance Reviewer confirms the final output matches the approved original requirements.
9. **Structured artifacts over conversation.** Decisions and hand-offs live in reviewable artifacts.
10. **Resource efficiency is a requirement.** Avoid unnecessary repository reading and repeated reasoning.
11. **Preserve the architecture.** Maintain the domain → application → infrastructure → delivery layering, with dependencies pointing inward, and keep financial logic deterministic and exact-decimal.
12. **Traceability is mandatory.** Every implementation traces to an approved item. Untraceable work stops.

---

## 8. Success Definition

This ecosystem is succeeding when:

- Every piece of implemented work traces cleanly to an approved specification, and that trace can be checked by anyone.
- AI contributions reduce human effort, because they arrive review-ready rather than needing to be re-validated from scratch.
- No requirement, threshold, rule, or architectural decision in the codebase was invented by a tool.
- Financial truth is produced entirely by deterministic logic, and AI's role is limited to explaining it.
- Every decision that matters has a human owner who approved it.
- Reviews catch drift early, because each stage is checked before the next begins — and the Governance Reviewer confirms the finished product matches what was originally approved.
- The team moves quickly and still trusts the result, because the process — not the confidence of any single tool — is what earns that trust.

Success is not measured by how much AI produces. It is measured by how much of what AI produces is correct, traceable, reviewed, and trusted.
