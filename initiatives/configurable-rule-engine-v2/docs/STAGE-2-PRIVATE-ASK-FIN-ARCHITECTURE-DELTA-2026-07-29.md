# Stage 2 Private Ask Fin Architecture Delta

- **Status:** Governed implementation contract; implementation and verification pending
- **Date:** 2026-07-29
- **Parent architecture:** `APPLICATION-ARCHITECTURE.md`, AC-04/AC-06, ADR-V2-005, and ADR-V2-007
- **Stage 1 dependency:** One sealed deterministic Validation Run and its recorded canonical/result/evidence projections
- **Provider profile for Stage 2:** Local Ollama only

## 1. Decision

Stage 2 narrows the existing private-provider architecture to an Ollama process
reachable only on the same machine through an approved loopback endpoint. It
does not enable the organization-private external-provider option described as
a possible architecture profile in ADR-V2-005.

For Stage 2:

- no financial, vendor, workbook, transaction, prompt, response, or actor data
  is sent to a cloud or non-loopback endpoint;
- there is no cloud fallback;
- there is no internet, public search, external retrieval, or external
  embedding call;
- user-entered arbitrary provider URLs are rejected;
- Ollama is optional and failure never affects deterministic results;
- Explain This remains fully available without Ollama; and
- Ask Fin receives no command port, tool loop, filesystem browser, rule
  evaluator, SQL executor, or mutable object handle.

This is an additive architecture delta in the same application and repository.
It does not create an AI sidecar product or a second financial result path.

## 2. Runtime flow

```text
PySide6 Ask Fin panel
  → AskFinApplicationService
  → mode and selected-scope resolver
  → authorization + review-isolation guard
  → deterministic decision-boundary guard
  → AskFinGroundingQueryPort
  → finite GroundingBundle with stable Fact/Citation IDs
  → versioned local prompt assembler
  → LoopbackOllamaGateway
  → structured candidate response
  → deterministic schema/citation/claim/decision validator
  → cited answer or safe limitation/refusal
  → encrypted local Ask Fin interaction record
```

The mode resolver runs before retrieval:

- **Application Help Mode:** no sealed run is selected; retrieval is limited to
  approved local FinSight help content.
- **Financial Review Mode:** exactly one authorized Review Version and
  Validation Run are selected.
- **Authorized Comparison Mode:** exactly two explicit authorized Run
  identities are selected. This mode is never entered implicitly.

The deterministic decision-boundary guard runs before prompt construction. A
second output guard runs after model response parsing. Either guard may replace
the model path with a deterministic refusal.

## 3. Component contracts

### 3.1 `AskFinApplicationService`

Inputs:

- actor/access context;
- selected Review/Run or help context;
- optional contextual scope;
- user question;
- prompt-pack version; and
- approved Ollama profile ID.

Outputs:

- `SUPPORTED_ANSWER`;
- `INSUFFICIENT_EVIDENCE`;
- `DECISION_REFUSAL`;
- `HELP_ONLY`;
- `PROVIDER_UNAVAILABLE`;
- `POLICY_BLOCKED`; or
- `FAILED`.

It may call query/audit/provider ports only. It receives no application command
service.

### 3.2 `AskFinGroundingQueryPort`

The query port returns a finite immutable `GroundingBundle` containing:

- review/run/rule-set/publication identity;
- current contextual scope;
- approved Fact Records;
- approved Citation Records;
- data-completeness limitations;
- approved rule/help descriptions; and
- deterministic suggestion candidates answerable by this bundle.

Each Fact Record includes:

```text
fact_id
subject_type + subject_id
predicate
typed value + display value
currency/reporting period when applicable
source record/field IDs
review_version_id + validation_run_id
completeness state
```

Each Citation Record includes a stable internal target and plain label. The
delivery layer resolves the target through existing review, account, vendor,
transaction, finding, rule, result, or source-evidence navigation. Fake
non-navigable citation numbers are prohibited.

### 3.3 `LoopbackOllamaGateway`

The only allowed transport target is a configured local Ollama base URL
validated as follows:

- scheme is `http`;
- host is exactly `localhost`, `127.0.0.1`, or `[::1]`;
- `localhost` must resolve entirely to loopback addresses;
- port is explicit or defaults to `11434`;
- userinfo, fragments, redirects, and non-root base paths are rejected;
- environment/system proxies are ignored;
- redirects are disabled;
- requested paths are allowlisted to `/api/tags`, `/api/show`, and
  `/api/chat`; and
- every connected peer address is verified as loopback.

The gateway never accepts a request-supplied URL. Configuration stores only a
validated profile. Response size, prompt size, connection timeout, total
timeout, and concurrent-request count are bounded. Cancellation closes the
local request and changes no review state.

The model is invoked without tools and with external/network functionality
disabled. Model downloads and registry access are out of application scope;
FinSight never pulls a model automatically.

The approved profile pins an exact locally installed model name and digest.
`/api/show` must confirm that local manifest before a question is sent.
Cloud/remote Ollama model aliases, an unpinned model, or a runtime that cannot
prove the approved local model is present are blocked. The qualified runtime
also runs under an operating-system outbound-deny policy; loopback to FinSight
is allowed, while internet and private-network egress from the Ollama process
is denied.

The Stage 2 implementation profile is
`stage2-local-ollama-gguf-v1`. `FINSIGHT_OLLAMA_MODEL_DIGEST` supplies the
approved `sha256:<64 hex>` digest. If that digest is absent, the adapter remains
available for status reporting but generation is fail-closed as
`model_identity_unconfigured`. Before both availability and every prompt-bearing
request, the gateway verifies the exact model name/digest from `/api/tags` and
the local GGUF family/architecture plus `completion` capability from
`/api/show`. The chat response must repeat the exact approved model name.

### 3.4 `CandidateResponseVerifier`

Ollama must return JSON matching the versioned response schema:

```json
{
  "response_type": "answer|insufficient_evidence|refusal",
  "answer_blocks": [
    {
      "text": "string",
      "fact_ids": ["FACT-..."],
      "citation_ids": ["CIT-..."]
    }
  ],
  "limitations": ["string"],
  "non_binding_consideration_ids": ["CONSIDERATION-..."]
}
```

The verifier:

1. rejects malformed or oversized output;
2. rejects unknown/cross-review Fact and Citation IDs;
3. requires every material financial block to cite at least one exact Fact;
4. verifies referenced typed values against the GroundingBundle;
5. removes or blocks unsupported financial/entity/causal claims;
6. rejects final-decision or authorization language;
7. renders only approved consideration templates; and
8. returns `INSUFFICIENT_EVIDENCE` when a safe supported answer cannot be
   constructed.

The model never supplies the authoritative Budget, Actual, EAC, variance,
status, severity, threshold, or finding. It can select and summarize only the
recorded Fact Records.

Value verification is predicate-aware, not string-presence validation. For
example, a recorded BGT value cannot be described as an over-budget variance
merely because the same citation contains both values. Display amounts, dates,
counts, account/department identifiers, statuses, and directional variance
claims are bound to compatible fact predicates. Causal paraphrases are blocked
unless the cited record contains that exact governed causal statement.

The implemented claim contract is a closed allowlist. Every financial token
must resolve to one approved typed predicate and a compatible typed recorded
fact; an unknown label or unsupported synonym fails closed even when the same
characters occur elsewhere in the citation. BGT, Actual, ATD, ETC, EAC, Delta,
variance, utilization, GED Amount, and Invoice Amount remain distinct.

The allowlist applies to the complete assertion, not only to its financial
tokens. Before inference, FinSight deterministically compiles the retrieved
records into application-authored `SupportedClaim` entries with a stable
`claim_id`, one predicate, exact claim text, and one citation key. A provider
sentence is accepted only when, after insignificant whitespace and terminal
punctuation normalization, it equals exactly one supported claim template and
uses that claim's citation. The provider cannot add qualifiers, causal
language, authorization judgments, fraud assertions, delivery assertions, or
other non-numeric prose merely by attaching a valid citation. An arbitrary
sentence or paraphrase fails closed as `INSUFFICIENT_EVIDENCE`.

This material prompt-contract change is recorded by runtime prompt version
`stage2-private-v2`; preserved `stage2-private-v1` interaction audit records
remain distinguishable and unchanged.

## 4. Retrieval without embeddings

Stage 2 retrieval is deterministic local query, not semantic vector search.
There is no embedding model, vector database, external index, or approximate
nearest-neighbor retrieval.

The selected scope determines exact query keys:

- Finding → Finding, originating Rule Result/Rule Version, evidence, and
  contributing records;
- Account → canonical account, related Budget record, GED records, vendors,
  findings, and reconciliation result;
- Vendor → vendor-group projection, related accounts/transactions/findings;
- Department → approved department projection and underlying accounts;
- GED transaction → source record, account/vendor, findings, and lineage;
- Review → recorded Overview/Summary, findings, accounts, and completeness;
- Comparison → two explicitly selected preserved runs and their recorded
  comparison projection.

Global free-text questions are classified into an allowlisted intent and
resolved to exact ledger/repository filters. When the intent or subject is
ambiguous, Ask Fin requests a narrower selection or returns insufficient
evidence. It does not broaden retrieval to unrelated records.

## 5. Review isolation

Every query and cache key includes:

```text
actor/access-policy version
review_id
review_version_id
validation_run_id
publication state
scope kind + scope ID
grounding-policy version
```

Repository queries require this context and reject rows with a different Run
identity. Switching reviews clears in-memory prompt, grounding, response, and
suggestion state. A Review A interaction cannot cite Review B. The only
exception is an explicit authorized comparison that binds both run identities
and labels every fact by run.

Historical or working results remain explicitly labeled. Ask Fin defaults to
the published run and never silently follows a new working generation.

## 6. Persistence and audit delta

Ask Fin records are encrypted local Derived Records. Each interaction records:

| Field | Requirement |
|---|---|
| Interaction identity | Interaction ID, schema version, timestamp, correlation ID |
| Actor/context | Actor ID, access-policy version, Review/Version/Run/Rule Set, publication state |
| Mode/scope | Help, financial, or comparison; scope kind and stable ID |
| Input | User question; no credentials or hidden chain of thought |
| Retrieval | Retrieved Fact/Citation IDs, record fingerprints, grounding-policy version and bundle fingerprint |
| Provider | Ollama profile, model name, model digest/version, endpoint profile ID |
| Prompt | Prompt-pack/template version, canonical prompt fingerprint, and encrypted locally retained assembled prompt |
| Output | Terminal state, retained displayed response, citations, limitations |
| Safety | Decision-boundary trigger/rule IDs, refusal, blocked/unsupported claim counts |
| Performance | Start/end, latency, timeout/cancellation/failure code |

The assembled prompt and displayed response are retained only in the encrypted
interaction/Derived Record under the local retention policy. They never enter
an unencrypted file, clipboard export, or support bundle. The local diagnostic
log receives only correlation ID, component, timings, counts, and terminal
code. It does not receive the question, response, financial values, vendor
names, source text, or prompt.

No hidden model reasoning is requested or persisted. There are no API keys for
the local Ollama transport. If a future local profile introduces credentials,
they must use the platform secret adapter and must not enter the audit record.

The interaction append is mandatory before a successful model answer is
released. If the encrypted audit transaction cannot commit, the candidate
answer and citations are discarded and the caller receives `FAILED` with
`audit_persistence_failed`; FinSight never returns an unaudited `OK` answer.

## 7. Failure behavior

| Failure | User-visible result | State effect |
|---|---|---|
| Ollama not installed/not running | `Ask Fin is unavailable because the approved local model is not running. Explain This and all deterministic financial results remain available.` | None |
| Model missing | Name the approved missing local model and local support action; do not download | None |
| Timeout/cancel | Safe retry message; preserve question locally only under retention policy | None |
| Malformed/unsupported response | `I could not produce an answer supported by this review's recorded evidence.` | None |
| Unknown citation/cross-review fact | Block entire affected answer block and audit policy failure | None |
| Decision request | Deterministic refusal plus offered evidence help | None |
| Insufficient evidence | Explicit limitation; no guessed value or policy | None |
| Non-loopback or redirected endpoint | Block before prompt/payload transmission | None |
| Mandatory audit append failure | Discard candidate answer; safe failed state | None |

There is no retry against another provider and no cloud fallback.

## 8. Context-aware UI

Ask Fin may open from the header, Overview, account/vendor/department row, GED
transaction, finding, Explain This, and Leadership Summary.

The panel always displays and announces its current scope, for example:

```text
Scope: May 2026 · Account 555035 · Account over budget
```

The user can clear or change scope without changing the selected review/run.
Suggested questions are generated from deterministic capability flags and
available Fact types. A suggestion is shown only if the current bundle can
answer it.

Before validation, the panel shows the approved Help Mode greeting and static
workflow suggestions. After validation, it shows the Financial Review greeting
and review-specific suggestions. Provider unavailability does not remove
deterministic Explain This or static local Help content.

## 9. Dependency and test boundaries

- Domain and deterministic validation modules import no Ollama/HTTP/provider
  code.
- Delivery imports no transport adapter and cannot assemble grounding directly.
- The concrete gateway is wired only at the composition root.
- Network tests deny all non-loopback sockets during Ask Fin execution.
- Provider-off/substitution tests prove zero Stage 1 projection changes.
- Cross-review isolation, decision-boundary, malformed-output, citation,
  timeout, and audit tests are release-blocking for Stage 2.

Windows packaging and model distribution remain outside Stage 2. FinSight
detects an existing approved local Ollama runtime; it does not bundle, install,
download, or update Ollama or a model in this stage.
