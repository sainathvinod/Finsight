---
name: ai-provider-integration
description: Expertise for the AI provider-adapter abstraction that Fin depends on — provider selection policy, confidentiality ordering, prompt/context/timeout/error/fallback handling, and keeping calculations outside the model. SPECIFIED-ONLY; no concrete provider implemented. Ollama is a documented future local option only. Expertise only — recipes own sequencing.
---

# Skill — AI Provider Integration

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.
**Status:** SPECIFIED-ONLY — provider/model binding is deferred (`ADC-03`). No provider is implemented; do not fabricate endpoints or model names.

## Purpose
Define how local or hosted model inference may support Fin behind a provider-adapter interface — "providers are configuration, not code" — so calculations stay outside the model and provider swaps do not change deterministic components.

## When to use
- Designing or reviewing the provider abstraction, provider selection policy, and confidentiality handling.

## When not to use
- Claiming a provider is operational; hardcoding a provider into Fin or backend business logic; sending sensitive data to an unapproved provider.

## Required inputs
- The approved provider/confidentiality policy from specs; the abstraction requirements.

## Authoritative sources
`specs/10-ai-and-agents.md §3, §14`; `XP-03`, `FR-104`, `NFR-046`, `NFR-048`; `DEC-006`, `DEC-007`, `DEC-016`.

## Capabilities (expertise)
- Preserve provider abstraction: Ask Fin → provider interface → concrete adapter.
- Apply confidentiality order: local/on-device (future option, `DEC-016`) → approved enterprise-hosted (primary) → other consented external (advisory). Prevent sensitive data from reaching unapproved providers.
- Define prompt, context, timeout, error, and deterministic-fallback handling; keep financial calculation outside the model.
- **Ollama:** document only as a possible future local adapter; it is not specified/selected and not implemented.

## Standards referenced
[ai-governance](../../standards/ai-governance.md), [architecture](../../standards/architecture.md), [security](../../standards/security.md), [financial-determinism](../../standards/financial-determinism.md).

## Templates referenced
_None._

## Patterns referenced
[ai-provider/provider-adapter](../../patterns/ai-provider/provider-adapter.md), [ai-provider/grounded-explanation](../../patterns/ai-provider/grounded-explanation.md).

## Recipes that orchestrate this skill
Composed within [`recipes/ask-fin/`](../../recipes/ask-fin/) (design-only, Release 2).

## Outputs
Design-level provider-abstraction guidance (no runtime implementation yet).

## Validation
Deterministic components unchanged across provider swaps; no sensitive data to unapproved providers; Ollama not presented as operational.

## Escalation
A task assumes a concrete provider exists, or would place calculation in the model → **Red Card**, stop.

## Traceability
Design cites the provider/confidentiality decisions (`DEC-006/007/016`, `XP-03`).
