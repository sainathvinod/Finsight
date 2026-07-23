# Recipe — UI Shell Implementation: 02 Implement

**Layer:** recipe (workflow engine). Composes the [ui-shell-implementation skill](../../../skills/ui-shell-implementation/SKILL.md). References skills/standards/patterns; does not invoke agents.
**Phase:** Generate / Execute.

## Purpose
Implement the delivery-shell slice per the approved plan, minimal changes, within the allowed-files list.

## Required inputs
The Plan; the allowed-files list.

## Standards / patterns
[accessibility](../../../standards/accessibility.md), [coding](../../../standards/coding.md), [architecture](../../../standards/architecture.md), [ai-governance](../../../standards/ai-governance.md); [ui/severity-non-color-encoding](../../../patterns/ui/severity-non-color-encoding.md), [ui/review-before-analysis](../../../patterns/ui/review-before-analysis.md), [ui/eight-step-wizard](../../../patterns/ui/eight-step-wizard.md).

## Ordered steps
1. Implement the slice in authorized delivery files only.
2. Preserve keyboard operability and non-color severity encoding.
3. Preserve "no dashboard before review selected" and the 8-step order.
4. Add `# Implements: <ID>` annotations; write the Implementation Summary.

## Outputs
A delivery-shell diff + Implementation Summary.

## Stop conditions / escalation
Change requires an out-of-scope file, an unapproved framework, or workflow reordering → **Red Card**.

## Prohibited behaviors
Encoding financial truth in UI; introducing a framework; issuing a review verdict.
