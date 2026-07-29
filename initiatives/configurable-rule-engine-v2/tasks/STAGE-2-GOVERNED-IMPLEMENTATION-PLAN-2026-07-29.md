# Stage 2 Governed Implementation Plan

- **Status:** Approved scope translated to implementation plan; execution and verification pending
- **Date:** 2026-07-29
- **Lane:** Governed
- **Increment:** Modern results UX, deterministic Explain This, local private Ask Fin, and Leadership Summary
- **Stop condition:** Stage 2 verification and Project Owner hands-on review

## 1. Objective

Simplify FinSight around exception review while preserving the Stage 1
deterministic engine, canonical hierarchy, exact Decimal results, rule
governance, versioned history, evidence, replay, and audit.

The implementation extends the existing PySide6 modular monolith. It creates
no second repository, application, rule engine, persistence path, or financial
calculation path.

## 2. Governing artifacts

- `../docs/STAGE-2-MODERN-UX-AND-PRODUCT-DESIGN-2026-07-29.md`
- `../docs/STAGE-2-PRIVATE-ASK-FIN-ARCHITECTURE-DELTA-2026-07-29.md`
- `../docs/STAGE-2-LOCAL-INFERENCE-THREAT-MODEL-2026-07-29.md`
- `../docs/STAGE-2-ASK-FIN-GROUNDING-AND-DECISION-BOUNDARY-2026-07-29.md`
- `../docs/STAGE-2-ASK-FIN-PROMPT-PACK-1.0.0.md`
- Stage 1 canonical/financial verification artifacts
- parent Application Architecture, AC-04/AC-06, ADR-V2-005/007, and approved
  execution-lane policy

## 3. Work sequence

### W0 — Freeze trust baseline

1. Run the complete Stage 1 oracle/regression baseline.
2. Record fixture fingerprints, canonical/result projection fingerprints, 986
   baseline result counts, and five known findings.
3. Add architecture fitness tests preventing UI/Ask Fin imports of evaluator
   modules and preventing Ask Fin access to command ports.

**Exit:** Stage 1 projection is frozen and comparison-ready.

### W1 — Shared modern visual system

1. Replace cream-heavy tokens with neutral workspace, white panels, trust
   blue actions/navigation, teal Ask Fin, and semantic red/green/amber/gray.
2. Apply shared typography, spacing, radius, borders, tables, focus, empty
   states, dialogs/drawers, and Light/Dark/System palettes.
3. Update Home, Create Review, Upload, Verify Data, Review Rules, Validate,
   Results, Findings, Review Summary, Past Reviews, Settings, and Ask Fin
   without changing their governed task outcomes.
4. Preserve keyboard focus, screen-reader labels, zoom, resizing, and exact
   table alternatives.

**Exit:** One consistent design system at supported desktop sizes and themes.

### W2 — Simplified result information architecture

1. Replace the existing primary result tabs with Overview, Financial
   Analysis, GED Detail, Findings, and Review Summary.
2. Move Account, Vendor, Department, Budget vs Actual, and Reconciliation into
   Financial Analysis secondary navigation.
3. Move Data Quality/field coverage and Rule Results to reachable secondary
   views without deleting evidence.
4. Preserve selected Review Version, Run ID, Rule Set Version, and publication
   context across navigation.

**Exit:** All Stage 1 data remains reachable with materially fewer primary
destinations.

### W3 — Overview and financial drill-down

1. Build the six-card Overview from recorded projections only.
2. Render Budget-versus-Actual account rows with direct values, explicit
   favorable/unfavorable/incomplete labels, and Account Detail navigation.
3. Add concise findings severity and priority lists.
4. Implement Account, Vendor, Department, Budget vs Actual, Reconciliation,
   and GED transaction tables/drill-down.
5. Remove unsupported reference concepts: prior review comparison when absent,
   confidence, transaction type, materiality, delayed-posting policy, and
   invented Department Names.

**Exit:** The May 2026 fixture is understandable without reopening Excel, and
all source-supported values have evidence navigation.

### W4 — Findings workflow and deterministic Explain This

1. Make Findings the default exception-review workflow with plain-language
   titles and filters.
2. Add audited finding-review statuses: New, Acknowledged, In Review, Resolved,
   and Dismissed. Status changes never mutate Rule Results.
3. Implement the model-free Explain This renderer for core and optional rules.
4. Show What happened, Why flagged, Why it matters, evidence, contributing
   records, non-binding next step, and collapsed Technical Details.
5. Ensure every source citation selects the exact Budget/GED record and cell
   where applicable.

**Exit:** Every finding is explainable and traceable with Ollama disabled.

### W5 — Ask Fin domain/application contracts

1. Add inward-owned ports/types for Ask Fin mode, scope, Fact/Citation Record,
   GroundingBundle, local provider, response verification, and interaction
   repository.
2. Implement exact-scope deterministic retrieval without embeddings.
3. Implement review isolation, authorization, deterministic suggestions,
   decision-intent guard, and approved consideration templates.
4. Implement structured response/citation/claim verification.
5. Add encrypted append-only interaction/audit persistence and migration.

**Exit:** Provider-independent application tests pass with a fake local
provider and no financial/result mutation.

### W6 — Ollama loopback integration

1. Implement the single loopback-only gateway and validated provider profile.
2. Disable proxies/redirects and enforce scheme/host/path/peer allowlists.
3. Add bounded request/response, timeout, cancellation, concurrency, model
   identity/digest logging, and safe unavailable states.
4. Wire the versioned prompt pack at the composition root.
5. Prove no automatic model download, external fallback, internet retrieval,
   or embedding call exists.

**Exit:** Local Ollama works when available and all non-loopback paths fail
closed before financial prompt transmission.

### W7 — Context-aware Ask Fin and Leadership Summary

1. Implement Help Mode and Financial Review Mode greetings.
2. Add entry points from header, Overview, account/vendor/department,
   transaction, finding, Explain This, and Leadership Summary.
3. Display and allow clearing/changing the exact current scope.
4. Render verified answers with clickable citations, limitations, and
   non-binding consideration labels.
5. Build ledger-derived Leadership Summary; optional model wording may be
   displayed only after claim verification.

**Exit:** Users can ask grounded questions without restating selected context,
and the deterministic summary remains complete when Ollama is unavailable.

### W8 — Consolidated verification

1. Run Stage 2 unit, application, persistence, UI, accessibility, security,
   privacy, launch, and full regression suites.
2. Re-run the independent Stage 1 financial oracle and projection comparison.
3. Capture Light and Dark screenshots for every major workflow and same-state
   result page.
4. Capture proxy/socket evidence for zero non-loopback AI transmission.
5. Verify every direct/subtle decision prompt, prompt injection, malformed
   response, missing evidence, cross-review attempt, citation, timeout, and
   provider-off scenario.
6. Perform one independent financial/architecture/accessibility review and one
   independent privacy/AI-boundary review; resolve material defects together.
7. Complete the Stage 2 verification record, exact changed-file inventory,
   launch/hands-on instructions, and limitations.

**Exit:** Both independent reviews return PASS and no Stage 1 projection field
changes unexpectedly.

## 4. Required test matrix

| Area | Minimum proof |
|---|---|
| Financial baseline | Exact Stage 1 oracle, 986 baseline results, known five findings, fixture hashes |
| Overview | Budget, Actual completeness, EAC, variance, findings from selected run |
| Semantics | Favorable/unfavorable/warning include text/icon and correct color |
| Navigation | Account, vendor, department, transaction, finding, citation and back-focus |
| Unsupported data | No invented prior review, confidence, type, threshold/materiality, policy, department name |
| Explain This | Ollama off; all five core findings; exact values/rows/rule versions; technical details collapsed |
| Finding status | Permission, append-only audit, reopen, no Rule Result mutation |
| Help Mode | Greeting, approved-help answers, financial-not-ready limitation |
| Financial Mode | Review-specific greeting/suggestions, citations, incomplete evidence |
| Decision boundary | All direct/subtle prompts plus adversarial variants refuse before model |
| Local privacy | Non-loopback denied, no proxy/redirect/fallback/search/embedding, model unavailable safe |
| Review isolation | Review A cannot retrieve/cite Review B; explicit authorized comparison only |
| Prompt injection | Source and user injection cannot change scope, tools, policy, or output contract |
| Audit | Required interaction/model/prompt/retrieval/citation/refusal/latency/failure provenance |
| Accessibility | Keyboard, screen reader, 200% scaling, focus restoration, chart tables, Light/Dark contrast |
| Performance | UI remains responsive; bounded local provider timeout/cancel; approved Stage 1 envelope preserved |

## 5. Stage boundaries

Not included:

- Windows executable, MSI, Ollama installer, or model distribution;
- cloud or organization-private network inference;
- internet/search/external embedding integration;
- arbitrary AI tools or autonomous actions;
- new accounting policy, materiality, delayed-posting, confidence, or
  transaction-type semantics;
- new source layouts;
- general-purpose BI/dashboard expansion; or
- unrelated final cosmetic polish.

Stage 2 stops after consolidated verification and Project Owner hands-on
review.
