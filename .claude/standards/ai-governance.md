# Standard — AI Governance

**Layer:** standard (normative, leaf). Referenced by skills and recipes. References no agents.
**Origin / authority:** `specs/10-ai-and-agents.md`; `specs/constitution.md §6`; `.ai-dev/constitution.md §3, §8, §9`; `RJ-01`–`RJ-12`, `P-8`, `P-10`, `FR-094`, `FR-095`, `FR-097`, `FR-099`, `NFR-050`; `DEC-006`, `DEC-007`, `DEC-016`, `DEC-032`.

## Human authority

1. **Humans hold all business and governance authority.** AI proposes and drafts; humans decide and approve. No AI step creates authority.
2. **Human-only decisions** (never made by AI): business scope, requirements, architecture decisions, finance thresholds, governance, and Red Card resolution.
3. **No autonomous financial action.** No approval, rejection, payment, budget update, GED change, or vendor communication. FinSight is read-only and human-controlled.

## Independent review

4. **Generation may never approve itself.** Every generated artifact is checked by an **independent review executed separately** — read-only, fresh context — before it advances. Self-approval is not verification. The mechanism is the [review skill](../skills/review/SKILL.md) run via [`recipes/review/run-independent-review.recipe.md`](../recipes/review/run-independent-review.recipe.md).

## Ask Fin ("Fin") boundaries

5. Fin is FinSight's single, reactive, **grounded** explanation companion over the current review's verified data and findings (`DEC-032`, `10 §1`). **Status: specified-only, Release 2 — not implemented.**
6. Fin **may**: explain and summarize results, answer grounded and cited questions, guide investigation, and translate to business language (`10 §2`, constitution §6).
7. Fin **must not**: create/change/suppress findings; compute any financial value, variance, severity, RAG, or score; approve or reject; override/select/skip rules; modify source or verified data; bypass verification; recommend financial actions; contact vendors; or act silently (`10 §2`, `RJ-01`–`RJ-12`, `P-8`, `P-10`).
8. **Grounding:** Fin answers only from verified data, approved findings, summaries, evidence, and history. When evidence is absent it states "evidence not found" and never guesses (`10 §4.3`, `FR-094`, `FR-099`, `NFR-050`).
9. **AI is optional.** The product works fully with AI switched off (`FR-095`); AI changes nothing in Release 1.

## Provider / local-inference policy

10. Confidentiality preference order (`10 §3.4`): (1) local/on-device model — **future option, deferred** (`DEC-016`); (2) enterprise-approved hosted endpoint — primary production path; (3) other consented external — advisory only, with consent and warning (`FR-097`, `DEC-006`, `DEC-007`). Sensitive data is not sent to an unapproved provider. Ollama is **not** a selected provider; it may be documented only as a possible future local option. See [ai-provider-integration skill](../skills/ai-provider-integration/SKILL.md).

## Escalation

If work would require an AI role to make a human-only decision, compute financial truth, or send data to an unapproved provider, raise a **Red Card** and stop.
