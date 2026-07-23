# Recipe — Financial Review: 02 Present Findings

**Layer:** recipe (workflow engine). Composes the [financial-analysis skill](../../skills/financial-analysis/SKILL.md). References skills/standards/templates/patterns; does not invoke agents.
**Phase:** Generate.

## Purpose
Present the deterministic findings and evidence for humans — interpretation only, never new numbers.

## Required inputs
Deterministic results from `01-run-deterministic-analysis`.

## Standards / templates / patterns
[financial-determinism](../../standards/financial-determinism.md), [ai-governance](../../standards/ai-governance.md), [accessibility](../../standards/accessibility.md); [finding-template](../../templates/finding-template.md), [leadership-summary-template](../../templates/leadership-summary-template.md); [financial-domain/financial-evidence](../../patterns/financial-domain/financial-evidence.md), [ui/severity-non-color-encoding](../../patterns/ui/severity-non-color-encoding.md).

## Ordered steps
1. Render findings with rule reference, severity (icon+shape+label), period, entities, and evidence.
2. Present comparisons/spend views as produced by the engine.
3. Draft a leadership summary that presents (never recomputes) the results.

## Outputs
Findings presentation and a draft leadership summary.

## Stop conditions / escalation
A figure lacks evidence or a rule reference → **Red Card**.

## Prohibited behaviors
Altering severity/evidence; AI creating or narrating unverified numbers.
