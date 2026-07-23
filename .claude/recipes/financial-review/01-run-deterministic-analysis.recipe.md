# Recipe — Financial Review: 01 Run Deterministic Analysis

**Layer:** recipe (workflow engine). Composes the [financial-analysis skill](../../skills/financial-analysis/SKILL.md). References skills/standards/patterns; does not invoke agents.
**Phase:** Generate / Execute.

## Purpose
Drive the deterministic rules engine over a certified `VerifiedDataset` and collect its outputs for presentation. The engine computes; this recipe never computes.

## Required inputs
A certified `VerifiedDataset`; the approved rules catalog.

## Specification references
`specs/05-rules-catalog.md`, `specs/06-architecture.md §12–§13`; `DEC-001`, `DEC-002`.

## Standards / patterns
[financial-determinism](../../standards/financial-determinism.md), [architecture](../../standards/architecture.md); [financial-domain/deterministic-calculation](../../patterns/financial-domain/deterministic-calculation.md).

## Ordered steps
1. Confirm the dataset is certified (else stop — see data-verification).
2. Invoke the deterministic rules engine to produce values, findings, severity, and evidence.
3. Capture rule-set and config versions for replay.

## Outputs
Deterministic results (values, findings, evidence) for presentation.

## Stop conditions / escalation
Dataset not certified, or a required rule undefined → **Red Card**, stop.

## Prohibited behaviors
Computing/adjusting any value in this recipe or via AI; introducing analysis dimensions beyond department/GL account/vendor.
