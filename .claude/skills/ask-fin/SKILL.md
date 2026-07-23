---
name: ask-fin
description: Expertise for Fin, FinSight's grounded, reactive explanation companion over a review's verified data and findings. SPECIFIED-ONLY (Release 2) — not implemented. Fin explains and cites; it never computes financial truth, creates findings, or acts. Expertise only — recipes own sequencing.
---

# Skill — Ask Fin

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.
**Status:** SPECIFIED-ONLY — the AI layer is not implemented (`E-09`). Do not fabricate endpoints, models, or working behavior.

## Purpose
Define how Fin explains approved, deterministic results in plain language — grounded and cited — without ever becoming the source of financial truth.

## When to use
- Designing or reviewing grounded explanation behavior over a review's verified data, findings, comparisons, and history.

## When not to use
- Any request that would have Fin compute a value, create/change a finding or severity, approve/reject, modify data, contact a vendor, or act silently — all prohibited.

## Required inputs
- Already-computed verified data, approved findings, evidence, and history for the current review.

## Authoritative sources
`specs/10-ai-and-agents.md`; `DEC-032`; `RJ-01`–`RJ-12`; `FR-094`, `FR-095`, `FR-099`, `NFR-050`.

## Capabilities (expertise)
- Explain results, why a finding matters, and comparisons; cite the deterministic evidence.
- Guide users through existing review data and clarify terminology.
- State "evidence not found" when grounding is absent; never guess.

## Standards referenced
[ai-governance](../../standards/ai-governance.md), [financial-determinism](../../standards/financial-determinism.md), [audit-traceability](../../standards/audit-traceability.md), [security](../../standards/security.md).

## Templates referenced
_None._

## Patterns referenced
[ai-provider/grounded-explanation](../../patterns/ai-provider/grounded-explanation.md).

## Depends on (provider abstraction)
Fin's domain behavior depends on the AI provider interface, not on any concrete provider — see [ai-provider-integration](../ai-provider-integration/SKILL.md). Ask Fin → provider interface → provider adapter.

## Recipes that orchestrate this skill
[`recipes/ask-fin/`](../../recipes/ask-fin/) — `01-build-grounded-context`, `02-generate-explanation`, `03-validate-grounding`, `04-review` (all DESIGN-ONLY / Release 2).

## Outputs
Design-level grounded-explanation behavior (no runtime implementation yet).

## Validation
Every explanation traces to grounded evidence; no financial value/finding is created or altered.

## Escalation
A request would require Fin to compute truth, create a finding, or act → **Red Card**, stop.

## Traceability
Explanations cite the findings/evidence they draw on.
