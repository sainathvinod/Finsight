# Stage 2 — Ask Fin Natural-Language and Evidence Refinement Verification

**Date:** 2026-07-30  
**Scope:** Focused Ask Fin refinement only  
**Verdict:** PASS — ready for hands-on review  
**Packaging:** Not started

## Result

Ask Fin now classifies each message deterministically before retrieval, answers
ordinary review questions from the active sealed Validation Run, preserves
conversation scope for follow-ups, and presents responses as an embedded chat
with readable, expandable, navigable evidence.

The refinement preserves the approved safety boundaries:

- local Ollama only;
- normalized loopback HTTP only;
- no proxies, redirects, external retrieval, cloud provider, or fallback;
- active-review and active-validation-run isolation;
- protected decision refusals before model invocation;
- exact closed-claim and citation verification;
- fail-closed handling for fabricated values, unsupported calculations,
  invalid citations, wrong-record support, unsupported causal language, and
  uncited factual sentences;
- successful responses remain audit-gated.

## Implemented behavior

### Deterministic intent handling

The pre-retrieval classifier distinguishes:

1. greeting or social acknowledgement;
2. application help;
3. review summary;
4. findings summary;
5. account question;
6. vendor question;
7. department question;
8. GED transaction question;
9. evidence request;
10. comparison request;
11. clarification or contextual follow-up;
12. unsupported question;
13. prohibited decision request.

Greetings, thanks, help questions, and ambiguous text bypass financial
retrieval and the local model. Their audit records identify the response as a
FinSight deterministic intent response rather than falsely attributing it to
Ollama.

### Grounded business responses

Supported financial questions now use an application-authored response plan
over exact claims from the sealed run. The local-model response must first pass
the existing closed-claim verifier; FinSight then renders a consistent
business-readable response whose depth matches the question.

The account-overrun response includes:

- account number and name;
- BGT;
- summed GED spend;
- unfavorable variance and percentage;
- recorded contributing vendors;
- transaction count;
- the protected rule and version;
- the recorded threshold;
- contributing source-row range;
- key transactions from the Rule Engine's recorded
  `largest_transactions` order;
- additional vendor-covering transaction examples;
- Budget and GED source locations.

Ask Fin does not create a new financial ranking. Key transactions consume the
ranking already recorded by deterministic financial analytics, while the
additional transaction examples provide evidence coverage without calculating
materiality in the AI layer.

### Conversation scope

Resolved account, vendor, finding, department, and transaction context is
retained only for the active review and Validation Run. Natural follow-ups such
as `Why?`, `Show supporting evidence`, `Which vendor?`, and
`What should I inspect next?` remain inside that object scope.

Cross-review contexts and stale Validation Run contexts fail closed. Changing
reviews or runs clears the cached conversation scope in the desktop UI.

### Chat and evidence presentation

The Ask Fin drawer now provides:

- right-aligned user bubbles;
- left-aligned Fin bubbles;
- a visible loading bubble;
- multiline keyboard-friendly composer;
- suggested prompts only before the first message;
- structured labels, paragraphs, and bullets;
- context-aware follow-up chips;
- a verified-source count;
- expandable evidence grouped by business object;
- plain-language file, worksheet, row, cell, account, vendor, transaction,
  amount, rule, and rule-version labels;
- source navigation actions;
- active Validation Run identification;
- smooth auto-scroll;
- accessible names, focus behavior, and light/dark styling.

## Focused automated verification

### AI, grounding, privacy, and safety

```text
.venv/bin/pytest -q tests/ai \
  tests/integration/test_private_ask_fin_v2_grounding.py \
  tests/integration/test_private_ask_fin_natural_language_refinement.py

474 passed, 2 subtests passed in 18.62s
```

This selection covers provider security, loopback enforcement, proxy and
redirect rejection, model identity checks, prompt construction, context
budgets, response validation, closed claims, citations, review/run isolation,
decision refusals, natural-language variants, evidence depth, and historical
compatibility.

### Chat UI, accessibility, and launch

```text
.venv/bin/pytest -q \
  tests/ui/test_ask_fin_setup_and_drawer.py \
  tests/ui/test_stage2_private_ask_fin_dialog.py \
  tests/ui/test_ask_fin_ui.py \
  tests/accessibility \
  tests/ui/test_desktop.py::test_shell_launches \
  tests/ui/test_packaging.py

64 passed in 20.11s
```

### Code-quality checks

```text
Ruff: PASS for every changed Python file
git diff --check: PASS
Integrated offscreen launch smoke: PASS
```

The existing global appearance suite was also checked: `11 passed, 2 failed`.
The two failures predate and are outside this Ask Fin refinement:

1. the header Appearance control compresses below its minimum-size hint at
   200% text scaling;
2. an older Settings test expects a hidden embedded Back button to be
   focusable even though the shell uses the global Back button.

All impacted Ask Fin accessibility and launch tests pass.

## Live local Ollama verification

Runtime:

```text
Ollama: 0.32.3
Endpoint: http://127.0.0.1:11434
Model: llama3.2:3b
Digest observed locally:
a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72
Cloud fallback: none
```

The approved synthetic May 2026 Budget and GED review was used.

| Question | Result | Evidence |
|---|---|---|
| `Summarize this review.` | OK | 2 verified citations; active run matched |
| `Why is Account 555035 over budget?` | OK | 7 verified citations; active run matched |

Both responses completed without a failure state and committed local audit
records. The account response used the exact synthetic values:

```text
BGT: $1,100,000.00
GED spend: $1,250,000.00
Unfavorable variance: $150,000.00
Variance percentage: 13.64%
Budget evidence: Original Budget row 91, cell C91
GED evidence begins: GED row 246, cell O246
```

The screenshot harness also verified:

- automatic readiness with no manual digest-approval step;
- a visible conversational loading state;
- a grounded response with verified citations;
- expandable evidence;
- context-aware follow-up chips;
- one unavailable message, one Retry action, and no Open Setup action;
- successful Retry recovery.

## Screenshot evidence

| State | Light | Dark |
|---|---|---|
| Ready with initial suggestions | [Light](screenshots/ask-fin-natural-language-refinement/light/01-ready-immediately.png) | [Dark](screenshots/ask-fin-natural-language-refinement/dark/01-ready-immediately.png) |
| Loading | [Light](screenshots/ask-fin-natural-language-refinement/light/02-loading.png) | [Dark](screenshots/ask-fin-natural-language-refinement/dark/02-loading.png) |
| Evidence-rich grounded answer | [Light](screenshots/ask-fin-natural-language-refinement/light/03-grounded-answer.png) | [Dark](screenshots/ask-fin-natural-language-refinement/dark/03-grounded-answer.png) |
| Evidence expanded and follow-ups visible | [Light](screenshots/ask-fin-natural-language-refinement/light/04-evidence-expanded.png) | [Dark](screenshots/ask-fin-natural-language-refinement/dark/04-evidence-expanded.png) |
| Unavailable state | [Light](screenshots/ask-fin-natural-language-refinement/light/05-unavailable-single-message.png) | [Dark](screenshots/ask-fin-natural-language-refinement/dark/05-unavailable-single-message.png) |

The grounded-answer screenshot was visually compared with the prior
form-oriented Ask Fin screenshot. The revised experience has distinct message
bubbles, clearer speaker hierarchy, a persistent composer, structured
financial facts, expandable evidence, and contextual continuation controls.
No unrelated FinSight page was redesigned.

## Independent grounding and safety review

**Verdict: PASS**

The independent reviewer reported no material findings after inspecting the
latest tree and re-running the focused core, V2 grounding, natural-language,
and Ask Fin UI suites (`153 passed in 16.81s`).

The reviewer independently confirmed:

- classification occurs before retrieval;
- decision intent takes precedence;
- cross-review and stale-run contexts fail closed;
- invalid citations, values, calculations, causal claims, and uncited factual
  sentences remain hard failures;
- response depth only arranges verified sealed-run claims;
- evidence is readable, expandable, run-identified, and navigable;
- successful answers remain audit-gated and attributable;
- the live loopback Ollama summary and account questions returned verified
  active-run citations.

## Files changed

### Application and AI

- `src/finsight/application/ai/private_ask_fin.py`
- `src/finsight/application/ai/private_claims.py`
- `src/finsight/application/ai/private_contracts.py`
- `src/finsight/application/ai/private_grounding.py`
- `src/finsight/application/ai/private_intent.py`
- `src/finsight/application/ai/private_prompt.py`
- `src/finsight/application/ai/private_response.py`

### Desktop presentation

- `src/finsight/delivery/desktop/controllers/app_controller.py`
- `src/finsight/delivery/desktop/main_window.py`
- `src/finsight/delivery/desktop/theme/qss.py`
- `src/finsight/delivery/desktop/views/private_ask_fin_dialog.py`

### Tests and verification tooling

- `scripts/capture_ask_fin_simplification_screenshots.py`
- `tests/ai/test_private_ask_fin_stage2.py`
- `tests/integration/test_private_ask_fin_v2_grounding.py`
- `tests/integration/test_private_ask_fin_natural_language_refinement.py`
- `tests/ui/test_ask_fin_setup_and_drawer.py`
- `tests/ui/test_stage2_private_ask_fin_dialog.py`
- `initiatives/configurable-rule-engine-v2/verification/STAGE-2-ASK-FIN-NATURAL-LANGUAGE-REFINEMENT-2026-07-30.md`

## Hands-on launch

From the repository root:

```text
.venv/bin/python scripts/launch_mvp_demo.py \
  --data-dir artifacts/mvp-hands-on-store
```

Use the approved synthetic Budget and GED fixtures, complete validation, open
Financial Review, and select Ask Fin. Ollama and `llama3.2:3b` must already be
available locally.

## Known limitations

- FinSight still does not install, start, repair, update, or remove Ollama or
  its model. Runtime provisioning remains a governed release-stage concern.
- The two pre-existing global appearance assertions listed above remain open
  outside this focused Ask Fin refinement.
- No full product regression suite was run because this task explicitly used
  focused verification. The affected AI, privacy, chat UI, accessibility, and
  launch surfaces were covered.

## Stop condition

This refinement is complete and is stopped for hands-on review. Packaging and
release work have not begun.
