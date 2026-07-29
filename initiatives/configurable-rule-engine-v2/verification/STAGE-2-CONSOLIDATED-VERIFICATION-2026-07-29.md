# Stage 2 Consolidated Verification

- **Status:** Implementation and independent verification complete
- **Date:** 2026-07-29
- **Scope:** Modern FinSight UX, simplified Financial Review, deterministic
  Explain This, private local Ask Fin, audit, accessibility, and Stage 1
  non-regression
- **Independent verdicts:** Financial PASS; visual/accessibility PASS;
  privacy/security PASS
- **Remaining gate:** Project Owner hands-on review

## 1. Source and environment identity

| Evidence | Verified value |
|---|---|
| Branch | `codex/configurable-rule-engine-v2` |
| Base HEAD | `a298040` |
| Source state | Dirty Stage 2 working tree; final commit pending |
| Application version | `1.0.0` |
| Operating system used for this verification | macOS 26.5.2 arm64 |
| Python | 3.11.15 |
| PySide6 / Qt | 6.11.1 / 6.11.1 |
| openpyxl / cryptography | 3.1.5 / 49.0.0 |
| Prompt contract | `stage2-private-v2` |
| Prompt pack | `ASKFIN-PROMPT-PACK-1.0.0` |
| Grounding / decision policies | `ASKFIN-GROUNDING-1.0.0` / `ASKFIN-DECISION-1.0.0` |
| Local model profile | `stage2-local-ollama-gguf-v1` |

No approved Ollama model digest was configured in the verification
environment. Ask Fin therefore failed closed in the captured UI, as designed.
Deterministic validation, Findings, Explain This, and all recorded financial
results remained available.

## 2. Approved fixture identity

| Fixture | SHA-256 |
|---|---|
| `Sample_Budget_Report.xlsx` | `bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14` |
| `Sample_GED_Report.xlsx` | `2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c` |

The hashes match the Stage 1 verification record.

## 3. Stage 1 financial non-regression

The independent OOXML/Decimal oracle completed with
`overall_status: PASS`.

| Control | Verified result |
|---|---|
| Result ledger | 986 results: 979 PASS, 5 FAIL, 2 NOT_EVALUATED |
| Canonical hierarchy | 72 Department + Account scopes |
| Budget BGT | $10,372,000.00 |
| Budget ATD / eligible GED | $3,500,095.00 |
| Budget ETC | $5,882,000.00 |
| Budget EAC | $9,382,095.00 |
| Budget DELTA | $989,905.00 |
| Mapped GED | $3,498,245.00 |
| Unmapped GED | $1,850.00 |
| Known findings | Overrun, mapping, duplicate, required Amount, reconciliation |
| Incomplete record | GED row 87 Amount remains missing; dependent scopes remain NOT_EVALUATED |
| Protected/optional rule history | Versioned results, revalidation, replay, and comparison preserved |

The May 2026 workbook values are the only financial values shown in the
implementation and evidence captures. Prototype July values were not copied
into production paths.

## 4. Modern UX and navigation

The results information architecture contains exactly five primary sections:

1. Overview
2. Financial Analysis
3. GED Detail
4. Findings
5. Review Summary

Financial Analysis contains Account, Vendor, Department, Budget vs Actual,
and Reconciliation. GED Detail contains Transactions and Data Quality.
Findings contains the business-facing exception workflow and secondary rule
details.

Verified behavior includes:

- direct Budget, Actual, EAC, variance, and completeness values;
- text plus semantic color for favorable, unfavorable, and incomplete states;
- account, vendor, department, transaction, finding, and source drill-downs;
- audited finding statuses;
- deterministic leadership summary;
- Light, Dark, and System appearance behavior;
- keyboard-operable navigation and actions;
- screen-reader names for controls, tables, statuses, and evidence surfaces;
- no page-level horizontal overflow at 1100×720; wide tables scroll internally.

The unsupported prior-period Vendor column was removed. A concise disclosure
states that prior-period comparison is unavailable because the source reports
do not provide an authoritative comparison.

## 5. Screenshot evidence

Two complete Light/Dark evidence sets were generated from the real May 2026
deterministic workflow:

- `verification/screenshots/stage2/`: 48 PNGs at 1440×960
- `verification/screenshots/stage2-responsive-1100x720/`: 48 PNGs at 1100×720

Each set contains 24 Light and 24 Dark captures:

- Home
- Create Review
- Upload empty and extracted states
- Verify Budget and Verify GED
- pre-validation Ask Fin Help Mode/unavailable state
- Review Rules
- validation progress
- Overview
- all five Financial Analysis sections
- GED Detail
- transaction/source detail
- Findings
- Explain This
- contributing transactions and actions
- Review Summary
- private Ask Fin local-status state
- Past Reviews
- Settings

System Default resolved to the operating-system Light appearance during the
capture smoke check.

## 6. Source-capability honesty

| Source capability | Verified product behavior |
|---|---|
| Prior-period financial comparison | Omitted; explicit unavailable disclosure |
| Confidence | Not fabricated or shown as an authoritative GED field |
| Transaction type | Not inferred |
| Invoice reference | Source journal/invoice fields remain distinct |
| Materiality | Shown only when recorded by the originating Rule Version |
| Delayed-posting policy | No unsupported finding generated |
| Invalid `00-0999` department name | No department name invented |
| Missing GED row 87 Amount | Incomplete / NOT_EVALUATED; never converted to zero |
| Global Actual variance | Explicitly unavailable because the required Amount is missing |

Every approved Budget and GED field is displayed, available through
drill-down, used in a documented calculation, or listed in the field-coverage
technical view.

## 7. Findings and deterministic Explain This

Every recorded finding provides:

- a business-facing title and severity;
- What happened;
- Why FinSight flagged it;
- Why it matters;
- exact supporting evidence;
- Expected versus Actual values;
- a dedicated contributing-GED-transactions table;
- source row, vendor, journal/invoice reference, description, date, amount,
  workbook, and worksheet;
- an explicit empty state when no GED transaction contributes;
- non-binding review guidance;
- source navigation;
- contextual Ask Fin;
- collapsed rule, version, formula, run, and audit details.

All five core finding types were checked with Ollama unavailable:

| Rule | Key verified evidence |
|---|---|
| CORE-01 | Account 555035; BGT $1,100,000; GED $1,250,000; $150,000 overrun; rows 246–289 |
| CORE-02 | GED row 43; Department 00-0999 / Account 527015 |
| CORE-03 | GED rows 65 and 66; approved 15-field exact fingerprint |
| CORE-04 | GED Amount cell O87 is missing |
| CORE-05 | Budget row 11; ATD $1,850 versus mapped GED $0 |

The original sealed result remains unchanged when a user updates a finding's
review status. Status, actor, timestamp, prior value, new value, and reason are
recorded separately.

## 8. Private Ask Fin architecture and controls

The implemented pipeline is:

```text
Sealed deterministic results
→ authorized review-scoped retrieval
→ application-authored supported claims
→ loopback-only pinned Ollama provider
→ exact claim/citation verifier
→ audited response or fail-closed result
```

Material controls verified:

- Help Mode before validation and Financial Review Mode after a sealed run;
- active-review and selected-object scope enforcement;
- clear-context action;
- no internet retrieval, cloud AI fallback, or external embeddings;
- loopback HTTP endpoint only;
- environment proxy bypass prevented;
- redirects, non-loopback resolution, and unexpected peer addresses rejected;
- exact approved model name, SHA-256 digest, and local profile qualification;
- provider unavailable state leaves deterministic product features usable;
- every substantive answer sentence must exactly select one
  application-authored supported claim and its citation;
- arbitrary prose, unsupported causes, and relabeled financial values fail
  closed even when a valid citation is appended;
- decision/state-change requests are refused before provider invocation;
- decision language produced by the model is refused before release;
- audit persistence is mandatory; an audit failure withholds the answer;
- citations remain review-scoped and navigate to governed product objects;
- prompt, model, retrieved record keys, response, citations, latency, refusal,
  and failure state are recorded locally.

The closed supported-claim catalog is intentionally more restrictive than
free-form model prose. This is the security boundary that prevents a valid
citation key from laundering an unsupported assertion.

## 9. Automated verification

| Check | Result |
|---|---|
| Full regression suite | 1,190 passed in 77.02 seconds |
| Focused UI/accessibility suite | 18 passed |
| Independent privacy/security suite | 465 passed |
| Focused Ask Fin contract tests | 103 passed |
| Import/layer contracts | 3 kept, 0 broken; 233 files / 995 dependencies |
| Stage 2 changed-file Ruff check | PASS |
| `git diff --check` | PASS |
| Independent financial oracle | PASS |
| Offscreen launch smoke | PASS |
| 1440×960 screenshot capture | PASS; 48 images |
| 1100×720 responsive capture | PASS; 48 images |

The repository-wide Ruff command still reports legacy style debt in
pre-existing files outside the Stage 2 changed-file gate. No bulk unrelated
formatting rewrite was performed. All Stage 2 implementation, migration,
capture, and focused test files pass Ruff.

## 10. Independent reviews

### Financial correctness — PASS

The reviewer independently confirmed:

- the unchanged 986-result ledger;
- exact Stage 1 totals and known findings;
- source-fingerprint preservation;
- exact source evidence;
- append-only validation and finding-status history;
- absence of copied walking-skeleton financial values.

### Visual/accessibility — PASS

The reviewer independently checked both themes and the 1100×720 minimum,
including:

- five-view hierarchy;
- nested financial analysis;
- visual resemblance to the approved walking skeleton;
- Findings and Explain This;
- contributing transactions;
- semantic text/color behavior;
- rules status clipping;
- Ask Fin scope/unavailable state;
- keyboard/accessibility evidence.

The automated review is not a substitute for a live assistive-technology
usability session.

### Privacy/security — PASS

The reviewer independently reproduced and verified:

- financial-role misbinding attacks;
- unsupported causal and arbitrary assertions;
- explicit and subtle decision requests;
- unsafe model-output decisions;
- proxy/redirect/peer-address attacks;
- model identity and digest mismatch;
- cross-review isolation;
- audit failure behavior;
- valid positive grounded claims.

Residual operational risks are documented below.

## 11. Changed-file inventory

### Production and application

```text
src/finsight/app.py
src/finsight/application/ai/__init__.py
src/finsight/application/ai/private_ask_fin.py
src/finsight/application/ai/private_claims.py
src/finsight/application/ai/private_contracts.py
src/finsight/application/ai/private_grounding.py
src/finsight/application/ai/private_prompt.py
src/finsight/application/financial_review.py
src/finsight/delivery/desktop/app.py
src/finsight/delivery/desktop/controllers/app_controller.py
src/finsight/delivery/desktop/theme/qss.py
src/finsight/delivery/desktop/theme/tokens.py
src/finsight/delivery/desktop/views/financial_review_view.py
src/finsight/delivery/desktop/views/private_ask_fin_dialog.py
src/finsight/delivery/desktop/views/rules_repository_view.py
src/finsight/domain/ai/local_endpoint.py
src/finsight/domain/financial_validation.py
src/finsight/domain/finding_explanations.py
src/finsight/infrastructure/ai/private_audit.py
src/finsight/infrastructure/ai/private_config.py
src/finsight/infrastructure/ai/providers/ollama.py
src/finsight/infrastructure/financial_review_repository.py
src/finsight/infrastructure/review_disposal.py
```

### Persistence migrations

```text
src/finsight/infrastructure/migrations/m0013_finding_explanations_and_review_status.py
src/finsight/infrastructure/migrations/m0014_private_ask_fin_audit.py
src/finsight/infrastructure/migrations/runner.py
```

### Launch and capture

```text
scripts/launch_mvp_demo.py
scripts/capture_stage2_screenshots.py
scripts/workflow1_demo_support.py
```

### Stage 2 tests

```text
tests/accessibility/test_financial_results_accessibility.py
tests/ai/test_migration_0002.py
tests/ai/test_ollama_provider.py
tests/ai/test_private_ai_config.py
tests/ai/test_private_ask_fin_stage2.py
tests/application/test_finding_explanations.py
tests/application/test_reconstruction_architecture.py
tests/integration/test_private_ask_fin_v2_grounding.py
tests/migrations/test_migration_0003.py
tests/migrations/test_migration_0013.py
tests/migrations/test_migration_0014.py
tests/migrations/test_migrations.py
tests/ui/test_appearance.py
tests/ui/test_integrated_financial_review.py
tests/ui/test_stage2_private_ask_fin_dialog.py
tests/unit/test_financial_validation.py
```

### Specifications and verification

```text
initiatives/configurable-rule-engine-v2/docs/STAGE-2-MODERN-UX-AND-PRODUCT-DESIGN-2026-07-29.md
initiatives/configurable-rule-engine-v2/docs/STAGE-2-PRIVATE-ASK-FIN-ARCHITECTURE-DELTA-2026-07-29.md
initiatives/configurable-rule-engine-v2/docs/STAGE-2-LOCAL-INFERENCE-THREAT-MODEL-2026-07-29.md
initiatives/configurable-rule-engine-v2/docs/STAGE-2-ASK-FIN-GROUNDING-AND-DECISION-BOUNDARY-2026-07-29.md
initiatives/configurable-rule-engine-v2/docs/STAGE-2-ASK-FIN-PROMPT-PACK-1.0.0.md
initiatives/configurable-rule-engine-v2/tasks/STAGE-2-GOVERNED-IMPLEMENTATION-PLAN-2026-07-29.md
initiatives/configurable-rule-engine-v2/verification/STAGE-2-CONSOLIDATED-VERIFICATION-2026-07-29.md
initiatives/configurable-rule-engine-v2/verification/screenshots/stage2/
initiatives/configurable-rule-engine-v2/verification/screenshots/stage2-responsive-1100x720/
```

## 12. Launch and hands-on review

From the repository root:

```bash
.venv/bin/python scripts/launch_mvp_demo.py
```

Optional persistent review store:

```bash
.venv/bin/python scripts/launch_mvp_demo.py \
  --data-dir /absolute/writable/path
```

Recommended hands-on path:

1. Create or open the May 2026 review.
2. Inspect Overview and all five Financial Analysis sections.
3. Drill from account, vendor, department, and GED row to source evidence.
4. Inspect all five core findings with Ollama unavailable.
5. Confirm the contributing-transactions table and source navigation.
6. Change and reopen a finding review status.
7. Configure the approved local model name and exact digest, start Ollama,
   and test Help and Financial Review modes.
8. Test a contextual question, an insufficient-evidence question, and
   decision refusals.
9. Stop Ollama and confirm deterministic results remain available.
10. Compare Light, Dark, System, keyboard navigation, and resizing.

## 13. Known limitations and residual risks

- Windows executable/MSI packaging is outside Stage 2.
- Ollama and approved-model installation/distribution are outside Stage 2.
- Only the approved Budget and GED layouts are supported.
- No cloud/private-network AI provider, web search, external embeddings, or
  fallback exists.
- Private Ask Fin requires a pinned approved model name and exact SHA-256
  digest. Missing or mismatched configuration intentionally disables it.
- The captured screenshots verify the safe unavailable state, not live
  generation by a qualified local model.
- Outbound denial for the separately managed Ollama daemon remains a host
  deployment qualification.
- A fully compromised local administrator can inspect process memory or
  replace trusted local binaries.
- New supported Ask Fin claim types must be versioned and receive positive,
  negative, adversarial, and replay tests.
- The fixtures contain one primary department and no authoritative
  prior-period, confidence, or transaction-type fields.
- The intentional missing GED Amount makes the global Actual variance
  incomplete/unavailable.
- A live assistive-technology usability session remains recommended.

## 14. Completion statement

The governed Stage 2 implementation is ready for Project Owner hands-on
review. No Windows packaging or unrelated product expansion has begun.
