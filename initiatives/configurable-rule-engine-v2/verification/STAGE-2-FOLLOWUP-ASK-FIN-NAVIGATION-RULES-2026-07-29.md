# Stage 2 Follow-Up Verification

> Historical verification record. The later
> [Ask Fin automatic-enablement verification](STAGE-2-ASK-FIN-SIMPLIFICATION-2026-07-29.md)
> supersedes the manual model-identity approval steps documented here.

- **Date:** 2026-07-29
- **Scope:** Local Ask Fin activation, integrated assistant drawer, global
  application Back navigation, and simplified Validation Rules
- **Delivery lane:** Focused Stage 2 correction
- **Packaging:** Not started
- **Remaining gate:** Project Owner hands-on review

## 1. Outcome

The focused correction is implemented without changing deterministic
financial calculations, sealed validation results, source evidence, finding
history, audit behavior, or the five protected baseline controls.

Verified product behavior:

- startup and Settings distinguish Ollama not installed, service not running,
  model not downloaded, model not approved, model verification failure,
  connection failure, timeout, and healthy states;
- endpoint, local model, model inventory, approved model identity, Test
  Connection, Refresh Status, Save Settings, setup guidance, and Copy Command
  are available in Settings;
- endpoint/model settings persist, while environment configuration has higher
  precedence;
- private financial prompts remain restricted to a normalized loopback HTTP
  endpoint with proxies and redirects disabled and peer/model identity
  verified;
- no cloud fallback exists;
- Ask Fin opens as an integrated, animated right-side drawer while the
  financial page remains visible;
- the drawer supports Escape and a theme-aware close action, retains
  per-review conversation history, supports object scope and Clear scope, and
  never displays internal citation keys in the conversation;
- recorded FinSight citations remain visible as source actions and continue to
  navigate to governed evidence;
- one global application-history Back action is shown on meaningful modern
  views, supports `Alt+Left`, and suppresses competing embedded Back controls;
- the normal Validation Rules page shows the business-facing rule list and
  details while detailed governance remains hidden until needed;
- core rule deletion is intercepted with a clear protected-control warning;
- optional rule create, edit, test, activate, disable, retire, history, and
  revalidation behavior remain available.

## 2. Real local Ollama acceptance

The verified development runtime was:

| Item | Verified value |
|---|---|
| Ollama executable | `/usr/local/bin/ollama` |
| Ollama service | `http://127.0.0.1:11434` |
| Ollama version | `0.32.3` |
| Model | `llama3.2:3b` |
| Approved model digest | `sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72` |
| Prompt contract | `stage2-private-v4` |

The focused capture runner executed the real deterministic May 2026
validation flow and then submitted:

```text
Why is Account 555035 over budget?
```

The local model returned a verified, released answer:

```text
Account 555035 has recorded GED spend of $1,250,000.00 against BGT of
$1,100,000.00, an unfavorable $150,000.00 variance.
```

One governed account citation was displayed. The internal citation token was
retained for verification and audit but removed from the user-facing
conversation.

## 3. Exact local development commands

Ollama Desktop was already installed on the verified macOS development
machine. FinSight does not install or launch system software automatically.

Launch the installed Ollama application:

```bash
open -a Ollama
```

Alternatively, run the local service in its own terminal with Ollama cloud
features disabled:

```bash
OLLAMA_NO_CLOUD=1 /usr/local/bin/ollama serve
```

Pull and verify the approved small local model:

```bash
/usr/local/bin/ollama pull llama3.2:3b
/usr/local/bin/ollama list
curl --fail http://127.0.0.1:11434/api/version
```

From the FinSight repository root, launch the integrated developer profile
with the exact verified model identity:

```bash
export FINSIGHT_AI_PROVIDER=ollama
export FINSIGHT_OLLAMA_BASE_URL=http://127.0.0.1:11434
export FINSIGHT_OLLAMA_MODEL=llama3.2:3b
export FINSIGHT_OLLAMA_MODEL_DIGEST=sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72
.venv/bin/python scripts/launch_mvp_demo.py
```

The same configuration can instead be approved and persisted through
**Settings → Ask Fin Setup → Test Connection → Save Settings**. Environment
configuration intentionally wins when both sources are present.

To reproduce the complete real-provider acceptance and screenshot set:

```bash
.venv/bin/python scripts/capture_stage2_followup_screenshots.py
```

## 4. Focused automated verification

| Check | Result |
|---|---|
| Consolidated impacted tests | **261 passed** in 30.39 seconds |
| Final drawer/rules/navigation correction subset | **59 passed** in 10.65 seconds |
| Changed-file Ruff check | **PASS** |
| `git diff --check` | **PASS** |
| Offscreen launch smoke with approved live configuration | **PASS** |
| Real local Ollama grounded question | **PASS**; one verified citation |
| Light/Dark screenshot runner | **PASS**; 10 PNGs |

The consolidated impacted test set covered:

- Ollama setup states, provider hardening, model identity, and settings;
- grounding, citation verification, decision refusal, local audit, and
  cross-review isolation;
- no external endpoint, proxy, redirect, peer-address, or cloud fallback;
- integrated drawer state, contextual scope, Escape, and late-response
  isolation;
- global Back navigation, keyboard behavior, filter/review preservation, and
  duplicate-Back suppression;
- simplified rule list, protected warning, optional lifecycle, version
  history, active-rule revalidation, and historical reproducibility;
- impacted financial-results, accessibility, and architecture contracts.

Per the focused correction scope, the full repository regression suite was
not rerun and unchanged specifications were not regenerated.

## 5. Screenshot evidence

The final Light and Dark evidence is under:

```text
verification/screenshots/stage2-followup/
├── light/
│   ├── 01-ask-fin-grounded-answer.png
│   ├── 02-ask-fin-finding-scope.png
│   ├── 03-ask-fin-setup.png
│   ├── 04-simplified-validation-rules.png
│   └── 05-protected-core-rule-warning.png
└── dark/
    └── the same five states
```

The captures demonstrate the integrated drawer with the underlying page still
visible, a real grounded answer and source action, finding scope and Clear
scope, healthy setup status, global Back, the simplified five-rule page, and
the protected-core warning.

## 6. Changed-file inventory

### Production

```text
src/finsight/app.py
src/finsight/application/ai/private_contracts.py
src/finsight/application/ai/private_grounding.py
src/finsight/application/ai/private_prompt.py
src/finsight/application/rule_management.py
src/finsight/delivery/desktop/ask_fin_preferences.py
src/finsight/delivery/desktop/components/iconography.py
src/finsight/delivery/desktop/controllers/app_controller.py
src/finsight/delivery/desktop/main_window.py
src/finsight/delivery/desktop/theme/qss.py
src/finsight/delivery/desktop/views/financial_review_view.py
src/finsight/delivery/desktop/views/private_ask_fin_dialog.py
src/finsight/delivery/desktop/views/review_management_view.py
src/finsight/delivery/desktop/views/rules_repository_view.py
src/finsight/delivery/desktop/views/settings_view.py
src/finsight/delivery/desktop/views/source_intake_view.py
src/finsight/infrastructure/ai/providers/ollama.py
src/finsight/infrastructure/financial_review_repository.py
```

### Tests and verification

```text
tests/ai/test_ollama_setup_status.py
tests/ai/test_private_ask_fin_stage2.py
tests/application/test_rule_management.py
tests/ui/test_ask_fin_setup_and_drawer.py
tests/ui/test_global_back_navigation.py
tests/ui/test_protected_rule_governance.py
scripts/capture_stage2_followup_screenshots.py
initiatives/configurable-rule-engine-v2/verification/screenshots/stage2-followup/
initiatives/configurable-rule-engine-v2/verification/STAGE-2-FOLLOWUP-ASK-FIN-NAVIGATION-RULES-2026-07-29.md
```

## 7. Known limitations

- Ollama and the selected model remain separately installed and operated
  local dependencies; FinSight deliberately never installs them.
- FinSight blocks cloud endpoints and cloud-style model aliases, but host
  deployment policy remains responsible for separately sandboxing the Ollama
  daemon itself.
- The drawer retains conversation while navigating inside the same running
  review session; conversation persistence across application restarts was
  not requested.
- Live assistive-technology usability testing remains recommended in addition
  to automated keyboard and accessibility checks.
- Windows packaging remains a later approved release stage and was not
  started.

## 8. Independent review

**Verdict: PASS — no material defects found.**

The independent reviewer:

- reproduced the focused suite with **261 passed in 30.23 seconds**;
- confirmed the launch smoke with Ollama 0.32.3 and `llama3.2:3b`;
- independently exercised the real local question and observed the correct
  $150,000 unfavorable variance with one verified citation;
- inspected all 10 Light/Dark screenshots;
- confirmed that the earlier rule-review defects were resolved: keyboard
  focus, human-readable conditions, actual version history, table clipping,
  `Active Rule Set` wording, and optional-rule lifecycle coverage;
- confirmed local-only controls, refusal boundaries, citation routing,
  contextual scope, application-history Back behavior, and the simplified
  default governance presentation;
- confirmed that no packaging or unrelated release work was introduced.

Non-blocking review observations were limited to the separately operated
Ollama dependency, recommended live assistive-technology testing, recommended
manual smaller-window drawer testing, and the intentionally omitted full
regression run.
