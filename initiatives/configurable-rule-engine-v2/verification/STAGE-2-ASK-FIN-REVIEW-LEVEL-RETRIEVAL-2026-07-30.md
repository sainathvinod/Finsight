# Stage 2 Ask Fin — Active-Review Retrieval Verification

Date: 2026-07-30  
Scope: Ask Fin review-level retrieval and response reliability only

## Outcome

Ask Fin now answers standard active-review questions from the current sealed
Validation Run whenever the required deterministic evidence exists. It no
longer reports insufficient verified information merely because the local
model paraphrases a claim, omits the required inline citation shape, adds
unrequested wording, or takes too long to format an answer that FinSight can
already produce deterministically.

The local Ollama runtime must still pass readiness and model-identity checks.
For standard review summaries, finding explanations, missing-GED explanations,
and evidence requests, FinSight then builds the response directly from exact
application-authored closed claims and runs the normal citation/value verifier
before display. Entity-specific free-form questions continue through the local
model path.

## Reproduced root cause

Live `llama3.2:3b` testing proved that the active review retrieval was already
finding the required records:

- review summary and deterministic leadership summary;
- persisted highest-priority findings;
- the CORE-04 missing-required-value finding;
- GED row 87 / cell O87;
- the highest-priority CORE-01 account and its Budget/GED source rows.

The response was rejected later because the small local model returned
substantive paraphrased prose without exact application-authored inline
citations. `build_business_response` was reached only after that model response
passed verification, so the already-verifiable deterministic response plan was
incorrectly blocked.

The trace also identified:

- a generic evidence request mixed several findings and an unrelated account;
- a broad review context was incorrectly treated as a specific evidence scope;
- explicit new topics could remain attached to the prior conversation object;
- the missing-GED explanation omitted the recorded department;
- the incomplete-review explanation omitted the recorded status and dependent
  not-evaluated limitation;
- literal fake citation examples in the prompt could be copied by the model.

## Implemented behavior

### Active-review response planning

After authorization, active-review enforcement, sealed-run reconstruction, and
local Ollama readiness checks, standard review-level intents use an
independently verified closed-claim response plan. The plan:

- reads only records from the active review and Validation Run;
- performs no financial calculation;
- emits only exact application-authored claims;
- requires every displayed sentence to carry a verified FinSight citation;
- records the result in the existing append-only Ask Fin audit stream;
- identifies its renderer as `finsight / deterministic-review-v1`.

### Evidence scope

- A generic `Show the supporting evidence` follows the last specific finding,
  account, vendor, department, or transaction scope.
- A broad review summary is not treated as a specific evidence object.
- If no specific conversation scope exists, generic evidence uses the active
  run's persisted highest-priority finding.
- An explicit account or other evidence target that does not exist in the
  active review fails closed; it is never replaced by an unrelated ranked
  account or generic review summary.
- Explicit review/topic/entity questions re-anchor to the active review instead
  of inheriting an unrelated prior object.

### Missing GED and incomplete review

The CORE-04 explanation now includes:

- missing field and failure reason;
- rule ID, rule name, and version;
- department number/name;
- account number/name;
- why the issue matters;
- exact workbook, worksheet, row, and cell evidence;
- a navigable transaction citation.

`Why is the review incomplete?` now combines the recorded review status, the
missing-value finding, and the deterministic limitation explaining which
dependent results were not evaluated.

### Prompt safety

Static fake citation keys were removed from the local-model prompt. The prompt
continues to require exact claims and inline citations using only keys present
in the current `FINSIGHT_CONTEXT`.

## Required question verification

With the approved sealed synthetic May 2026 review, all of the following return
status `OK`, active-run citations, and no insufficient-information fallback:

1. `Summarize this review.`
2. `What's wrong with this review?`
3. `What should I look at first?`
4. `Show the supporting evidence.`
5. `Tell me more about the missing GED amount.`
6. `Explain the highest-priority finding.`
7. `Why is the review incomplete?`
8. `Which findings are most important?`

## Preserved controls

- Active review authorization remains mandatory.
- A context from another review is refused before retrieval.
- A context from a prior Validation Run is refused.
- Retrieval remains bounded to the active sealed review/run.
- Source fingerprint and preserved-run checks remain unchanged.
- Ollama remains loopback-only with no proxy, redirect, cloud, or external API
  fallback.
- Local provider readiness/model identity is checked before a financial answer.
- User decision requests are still refused before model invocation.
- Unsupported entity-specific questions remain fail-closed.
- Invalid model prose, citations, values, calculations, causes, and decisions
  are never displayed.
- Provider outage/readiness failure still returns the existing unavailable
  state; it is not converted into a financial answer.

## Focused automated verification

### AI, provider, privacy, and citation suites

```text
.venv/bin/python -m pytest -q \
  tests/ai/test_ask_fin.py \
  tests/ai/test_citations.py \
  tests/ai/test_ollama_provider.py \
  tests/ai/test_ollama_setup_status.py \
  tests/ai/test_private_ai_config.py \
  tests/ai/test_private_ask_fin_stage2.py
```

Result: `244 passed, 2 subtests passed`

### Grounding and natural-language suites

```text
.venv/bin/python -m pytest -q \
  tests/integration/test_private_ask_fin_v2_grounding.py \
  tests/integration/test_private_ask_fin_natural_language_refinement.py \
  tests/integration/test_private_ask_fin_review_level_retrieval.py
```

Result: `52 passed, 1 skipped`

The one default skip is the opt-in live Ollama test.

### Live loopback Ollama acceptance

```text
FINSIGHT_LIVE_OLLAMA_TEST=1 .venv/bin/python -m pytest -q \
  tests/integration/test_private_ask_fin_review_level_retrieval.py::\
test_live_local_model_answers_requested_active_review_questions
```

Result: `1 passed`

Verified runtime: local Ollama with `llama3.2:3b`; no external endpoint.

### Chat UI

```text
.venv/bin/python -m pytest -q \
  tests/ui/test_ask_fin_setup_and_drawer.py \
  tests/ui/test_stage2_private_ask_fin_dialog.py \
  tests/ui/test_ask_fin_ui.py
```

Result: `40 passed`

### Static checks

```text
.venv/bin/python -m ruff check <impacted Ask Fin source and test files>
.venv/bin/python -m py_compile <impacted Ask Fin source files>
git diff --check
```

Result: PASS

## Files changed for this defect

- `src/finsight/application/ai/private_ask_fin.py`
- `src/finsight/application/ai/private_claims.py`
- `src/finsight/application/ai/private_grounding.py`
- `src/finsight/application/ai/private_prompt.py`
- `src/finsight/application/ai/private_response.py`
- `tests/ai/test_private_ask_fin_stage2.py`
- `tests/integration/test_private_ask_fin_v2_grounding.py`
- `tests/integration/test_private_ask_fin_natural_language_refinement.py`
- `tests/integration/test_private_ask_fin_review_level_retrieval.py`

## Known limitation

This was a focused Ask Fin defect correction. No full product regression suite
was run. Standard review-level answers intentionally use deterministic
closed-claim composition after local readiness is established; entity-specific
free-form questions continue to use the local model and retain strict
fail-closed response verification.

## Independent review

Verdict: **PASS — no material findings remain.**

The independent reviewer reran the focused grounding, retrieval, response,
citation, and safety coverage, including the live local-Ollama acceptance test.
The review specifically confirmed that:

- all eight required active-review questions are answerable;
- generic no-scope evidence selects the recorded highest-priority finding;
- an unknown explicit evidence target fails closed;
- conversation scope, explicit topic reset, stale-run refusal, and cross-review
  isolation behave correctly;
- missing-GED evidence includes the recorded rule/version, department, account,
  workbook, worksheet, row, cell, reason, and impact;
- outages, unsupported questions, decision requests, fabricated values, and
  invalid citations remain fail-closed.
