# ADR-V2-001 — Configurable Deterministic Rule Engine and Result Ledger

- **Status:** Proposed
- **Date:** 2026-07-27
- **Deciders:** Project Owner; Software Architect; Finance Control Owner; Security Architect
- **Supersedes:** The hard-coded-rule execution path described by the root architecture; it does not delete or silently reclassify the approved legacy rule catalog
- **Related contracts:** AC-03 and AC-04

## Context

FinSight V2 must be a configurable financial-validation platform rather than an application containing five one-off checks. The five Core Mandatory rules are protected seed configuration, and future Optional Configurable and Informational/Advisory rules must use the same deterministic, versioned, auditable execution path.

The result ledger must be the only source of validation truth for findings, dashboards, reports, exports, analytics, and Ask Fin.

## Decision

FinSight will implement a pure, headless deterministic rule engine in the domain layer.

The engine has exactly two explicit inputs:

1. one immutable, fingerprint-verified reconstructed `VerifiedDataset`; and
2. one immutable workspace Rule Set Version.

The trusted, allowlisted evaluator registry is domain-core implementation selected by evaluator type/version pinned in the Rule Set; it is not user-supplied data or a third invocation input. Run ID, actor, timestamps, correlation ID, repositories, provider handles, and other orchestration context never enter the engine.

The engine returns an ordered, complete in-memory execution bundle containing:

- exactly one Rule Execution per selected rule;
- exactly one Rule Result per expected rule-and-scope pair;
- exactly one Finding for each failed control scope;
- no Finding for PASS, NOT_EVALUATED, OBSERVATION, or NO_OBSERVATION; and
- the deterministic business-result projection used for replay comparison.

The first-release evaluator families are exactly:

- required-field presence and approved-domain parseability;
- exact reference-key membership;
- exact uniqueness or duplicate grouping;
- two-decimal scalar comparison with `=`, `!=`, `<`, `<=`, `>`, or `>=`;
- grouped `SUM` or `COUNT` comparison/reconciliation; and
- finite `ALL` or `ANY` composition of those predicates.

Rule definitions are data, not executable content. They may not contain code, SQL, scripts, macros, commands, loops, recursion, unrestricted expressions, fuzzy matching, or non-allowlisted fields. Unknown schema versions, fields, evaluator types, operands, status policies, or dependencies fail closed before execution.

Canonical rule serialization is versioned UTF-8 JSON with:

- lexicographically ordered object keys;
- ordered arrays where order is meaningful;
- Unicode normalization defined by the serialization version;
- dates as ISO values;
- exact two-decimal financial values encoded as decimal strings, never binary floating point; and
- a SHA-256 content fingerprint over the canonical bytes.

Scope enumeration, dependency evaluation, calculation, evidence construction, result roll-up, severity resolution, and final ordering are deterministic. The engine uses a stable total order based on Rule Set order, stable Rule ID/version, evaluation grain, and canonical scope key.

Any unresolved input belonging to an otherwise enumerated scope produces NOT_EVALUATED under the rule contract. Failure to enumerate expected scopes blocks completion; it is never treated as an empty passing population.

All three classifications use this engine and result contract:

- Core Mandatory and Optional Configurable rules emit PASS, FAIL, or NOT_EVALUATED.
- Informational/Advisory rules emit OBSERVATION, NO_OBSERVATION, or NOT_EVALUATED.
- Only failed control results create Findings.

The five protected seed controls retain permanent IDs `R-VAL-01` through `R-VAL-05`. Their logic is configuration executed by the common engine, not UI code.

## Consequences

### Positive

- A sixth or hundredth approved rule can be introduced without a new validation pipeline.
- Every downstream consumer uses one persisted result contract.
- Historical runs remain replayable because definitions, configurations, manifests, and serialization are immutable and fingerprinted.
- Rule definitions remain safe to edit through a controlled UI.

### Costs and limitations

- The first release deliberately supports a small evaluator language rather than arbitrary formulas.
- New evaluator semantics require a governed product/architecture extension and a new evaluator/serialization version.
- Complete scope ledgers consume more storage than findings-only persistence.

## Rejected alternatives

- **Five hard-coded functions called by the UI:** not configurable and creates competing sources of truth.
- **User-authored Python/SQL/formulas:** unsafe, difficult to audit, and not reliably deterministic.
- **Findings-only output:** cannot prove PASS, NOT_EVALUATED, advisory, or complete-scope coverage.
- **AI-selected or AI-evaluated rules:** violates deterministic validation and reproducibility.

## Verification

- Golden fixtures for positive, negative, boundary, malformed, empty-population, and dependency cases.
- Repeated and cross-platform runs produce an identical business-result projection.
- Property tests cover scope ordering, exact Decimal behavior, and aggregation.
- Mutation and allowlist tests reject executable/unrecognized definitions.
- Completeness tests prove exactly one execution per selected rule and one result per expected scope.
- Provider-off/substitution tests prove AI has zero effect on the projection.

## Approval effect

If accepted, this ADR governs the Rule Engine Design and implementation plan. Until accepted as part of the complete Architecture package, it authorizes no code change.
