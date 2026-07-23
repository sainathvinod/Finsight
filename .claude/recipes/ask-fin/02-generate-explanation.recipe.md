# Recipe — Ask Fin: 02 Generate Explanation (DESIGN-ONLY, Release 2)

**Layer:** recipe (workflow engine). Composes the [ask-fin skill](../../skills/ask-fin/SKILL.md) via the [ai-provider-integration skill](../../skills/ai-provider-integration/SKILL.md). References skills/standards/patterns; does not invoke agents.
**Status:** DESIGN-ONLY — not implemented.

## Purpose
Describe how Fin narrates the grounded context into a plain-language, cited explanation without computing anything.

## Required inputs
The grounded context from `01-build-grounded-context`.

## Standards / patterns
[ai-governance](../../standards/ai-governance.md), [architecture](../../standards/architecture.md); [ai-provider/grounded-explanation](../../patterns/ai-provider/grounded-explanation.md), [ai-provider/provider-adapter](../../patterns/ai-provider/provider-adapter.md).

## Ordered steps (design)
1. Send the grounded context to the model through the provider adapter interface.
2. Produce an explanation that cites the evidence it draws on.
3. Provide deterministic fallback text if the model is unavailable.

## Outputs
A design-level explanation behavior (no runtime call).

## Stop conditions / escalation
A request would have Fin compute/create/act → **Red Card**, stop.

## Prohibited behaviors
Creating/altering findings/values/severity; overriding certified data; acting silently.
