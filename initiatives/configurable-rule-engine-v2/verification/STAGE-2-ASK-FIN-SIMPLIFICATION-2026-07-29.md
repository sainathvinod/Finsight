# Stage 2 — Ask Fin Automatic Local Enablement Verification

**Date:** 2026-07-29
**Scope:** Ask Fin setup-friction removal only

## Result

Ask Fin now becomes ready automatically whenever the configured loopback
Ollama service and selected local model are available. Normal desktop use does
not require a saved digest, an identity-approval step, or a trip to Settings.

When Ollama is unavailable, the drawer shows one plain-language message and one
`Retry` action. The disabled conversation surface, `Open Setup` action, and
duplicate outage message are hidden.

## Security behavior retained

Automatic enablement does not weaken the local-only boundary:

- only normalized loopback HTTP endpoints are permitted;
- proxies and redirects are disabled;
- DNS resolution and the connected peer must remain loopback;
- cloud-style model aliases are rejected;
- the installed model must expose a valid SHA-256 digest and match the approved
  local GGUF profile;
- FinSight automatically pins the observed digest for each provider instance
  and re-verifies the digest and model profile immediately before every prompt;
- a managed `FINSIGHT_OLLAMA_MODEL_DIGEST` remains an optional deployment pin;
- there is no cloud fallback.

Legacy manually saved digest preferences are ignored and removed the next time
Ask Fin settings are saved.

## Focused verification

The following focused selection passed:

```text
200 passed, 2 subtests passed
```

Coverage included:

- local provider and automatic identity verification;
- model-swap, malformed-digest, non-loopback, proxy, redirect, and cloud-alias
  rejection;
- private grounding and response validation;
- simplified drawer states and Retry recovery;
- Settings copy and preference migration;
- integrated results and accessibility behavior.

Ruff passed for every changed Python file, `git diff --check` passed, and the
application launch smoke completed with `FINSIGHT_OLLAMA_MODEL_DIGEST` absent.
A final post-cleanup provider/UI/accessibility subset also passed with
`56 passed, 2 subtests passed`.

## Real local Ollama check

Configuration:

```text
Endpoint: http://127.0.0.1:11434
Model: llama3.2:3b
Configured digest: absent
Setup result: healthy
Generation available: true
```

Question:

```text
Why is Account 555035 over budget?
```

Grounded response:

```text
Account 555035 has recorded GED spend of $1,250,000.00 against BGT of
$1,100,000.00, an unfavorable $150,000.00 variance
```

The answer displayed one source citation. A simulated outage then displayed one
message, one Retry, and zero Open Setup actions. Selecting Retry restored the
ready composer against the live local Ollama service.

## Screenshot evidence

| State | Light | Dark |
|---|---|---|
| Ready immediately | [Light](screenshots/ask-fin-simplified/light/01-ready-immediately.png) | [Dark](screenshots/ask-fin-simplified/dark/01-ready-immediately.png) |
| Grounded answer | [Light](screenshots/ask-fin-simplified/light/02-grounded-answer.png) | [Dark](screenshots/ask-fin-simplified/dark/02-grounded-answer.png) |
| One-message unavailable state | [Light](screenshots/ask-fin-simplified/light/03-unavailable-single-message.png) | [Dark](screenshots/ask-fin-simplified/dark/03-unavailable-single-message.png) |

The combined before/after design comparison is available at
`artifacts/design-qa/ask-fin-simplified/02-unavailable-before-after-drawer-focus.png`.

## Known limitation

FinSight does not install, launch, or download Ollama or its models. If the
local runtime or selected model is absent, the user must make it available
outside FinSight and then select Retry.
