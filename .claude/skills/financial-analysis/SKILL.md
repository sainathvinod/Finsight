---
name: financial-analysis
description: Core FinSight domain expertise for interpreting and presenting deterministic financial-review results over General Expense Detail (GED) — spending analysis, comparisons, and findings. Deterministic core computes; this skill interprets and presents. Expertise only — recipes own sequencing.
---

# Skill — Financial Analysis

**Layer:** skill (composable expertise). Invoked by recipes, not the reverse. Provides no workflow sequencing and never invokes an orchestration agent.

## Purpose
Interpret and present the approved financial-review outputs — never to compute financial truth. Financial truth is produced by the deterministic rules engine.

## When to use
- Designing or presenting spending analysis, vendor/account/department views, comparison periods, and findings that the deterministic core has produced.
- Explaining what a finding means and what evidence supports it.

## When not to use
- Computing, adjusting, or approving any financial value, severity, or finding (deterministic-core only; never AI).
- Introducing analysis dimensions beyond the approved MVP set.

## Required inputs
- Certified `VerifiedDataset` and rule-engine outputs; the approved rules catalog.

## Authoritative sources
`specs/05-rules-catalog.md`, `specs/06-architecture.md` (§12–§13), `specs/00-project-understanding.md`; `DEC-001` (GED = General Expense Detail), `DEC-002` (dimensions: department + GL account + vendor).

## Capabilities (expertise)
- Interpret GED spend by department, GL account, and vendor (the approved MVP dimensions).
- Present comparison periods, transaction detail, issues/findings, severity, and supporting evidence — as produced by the rules engine.
- Distinguish clearly between facts, rules, and explanation.

## Standards referenced
[financial-determinism](../../standards/financial-determinism.md), [architecture](../../standards/architecture.md), [ai-governance](../../standards/ai-governance.md), [audit-traceability](../../standards/audit-traceability.md).

## Templates referenced
[finding-template](../../templates/finding-template.md), [leadership-summary-template](../../templates/leadership-summary-template.md).

## Patterns referenced
[financial-domain/deterministic-calculation](../../patterns/financial-domain/deterministic-calculation.md), [financial-domain/finding-guarded-constructor](../../patterns/financial-domain/finding-guarded-constructor.md), [financial-domain/financial-evidence](../../patterns/financial-domain/financial-evidence.md).

## Recipes that orchestrate this skill
[`recipes/financial-review/`](../../recipes/financial-review/) — `01-run-deterministic-analysis`, `02-present-findings`, `03-review`.

## Outputs
Interpreted, evidence-backed presentation of deterministic results (never new numbers).

## Validation
No financial value/finding/severity is created or altered outside the rules engine; results are reproducible and traceable to source data and rules.

## Escalation
A required rule or dimension is undefined, or presentation would require computing a value in the AI/interpretation layer → **Red Card**, stop.

## Traceability
Every presented figure/finding cites its rule reference and evidence.
