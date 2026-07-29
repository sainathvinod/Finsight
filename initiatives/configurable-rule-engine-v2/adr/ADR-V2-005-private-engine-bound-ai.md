# ADR-V2-005 — Private, Engine-Bound Ask Fin Boundary

- **Status:** Proposed
- **Date:** 2026-07-27
- **Deciders:** Project Owner; AI Governance Owner; Security Architect; Software Architect
- **Refines/supersedes:** Root AI provider policy wherever it permits public or merely user-consented external financial-data transmission
- **Related contracts:** AC-04 and AC-06

## Context

Ask Fin may explain recorded deterministic results but may not determine validation, mix review generations, expose financial content to a public model, or become necessary to complete a review.

## Decision

Ask Fin remains an optional, reactive, read-only explanation service downstream of one completed Validation Run.

Allowed providers are only:

- an on-device provider; or
- an organization-approved private provider profile whose endpoint, certificate/trust configuration, model identifiers, retention policy, and allowed operations are signed/admin-controlled.

Public, retail, user-entered, or otherwise unapproved endpoints are blocked before any financial/review payload is assembled or transmitted. Consent does not override provider approval. If no approved profile is available, Ask Fin is unavailable and the deterministic review remains complete.

An on-device provider performs no external transmission. Before any request to an approved organization-private external provider, a single application-owned egress chokepoint verifies an active, explicit, informed, revocable consent grant for the selected provider and operation. The consent surface is never defaulted on or bundled. It identifies in plain language:

- the exact provider/profile;
- the data categories and exact payload preview/projection to be transmitted;
- whether deterministic masking is active and what it changes;
- the privacy/retention implications; and
- how to decline or revoke.

The grant records Actor ID/time, provider/profile, consent-text version, payload/category policy and masking-policy versions, scope, and revocation state. Every external interaction references the exact active consent and records the transmitted-payload fingerprint. Revocation immediately blocks future transmission. Provider approval and active consent are independent gates; neither substitutes for the other.

One review-specific request binds exactly one:

- Review Version/Generation;
- Validation Run;
- Rule Set Version;
- publication state;
- versioned prompt template;
- versioned context-field/evidence allowlist;
- masking policy version; and
- provider/model profile.

The application constructs a finite Approved Grounding Corpus containing only the selected identity fields, Rule Executions, Rule Results, Findings, necessary confirmed Current Validation Values/provenance, and minimal cited source excerpts. It excludes:

- raw workbook bytes;
- complete Working or Verified datasets;
- unrelated rows/results;
- unconfirmed values;
- another generation;
- credentials, secrets, actor identity details, and local paths;
- general internet retrieval; and
- every write-capable command or object handle.

The provider returns structured candidate claims. A deterministic verifier converts only supported candidates into atomic Claim Records containing a stable Claim ID, subject/predicate/value, exact corpus record/field citations, and rendered text. Unsupported or mismatched claims are omitted or explicitly labeled unsupported; they are never displayed as supported financial facts.

Ask Fin has no port for:

- creating/updating/deleting rules, data, results, findings, approvals, audit, or lifecycle state;
- invoking validation;
- approving financial activity; or
- contacting external parties.

AI interaction persistence follows the configured retention policy. Required non-content provenance is always retained: selected run identity, provider/model/profile, corpus/prompt/masking versions, displayed Claim IDs/citations, blocked-claim outcomes, actor/time, and terminal Generation Event. Hidden model reasoning is never requested or stored.

All review-specific AI output is visibly labeled and identifies its exact run context. Product-help answers use a separate finite approved corpus and cannot be presented as review evidence.

## Consequences

### Positive

- AI cannot become a second financial-validation path.
- Public-model exposure is structurally blocked.
- No external financial context leaves the device without an attributable active consent.
- Every supported financial statement is traceable to an engine record.
- Provider absence or failure cannot block deterministic work.

### Costs and limitations

- Provider/model selection is constrained by organizational approval.
- Some natural-language output will be omitted when it cannot be reduced to supported claims.
- A full review dataset cannot be sent for broader conversational convenience.

## Rejected alternatives

- **Consent-only public providers:** prohibited by V2.
- **General chatbot with world knowledge or internet search:** not grounded in one review.
- **Agent/tool loop:** introduces autonomous action surface and unnecessary nondeterminism.
- **Free-text response accepted without claim verification:** cannot guarantee evidence fidelity.
- **AI-generated findings or severity:** violates engine-as-truth.

## Verification

- Proxy capture proves zero payload bytes reach public/unapproved endpoints.
- Context-minimization tests prove exact allowlist membership and no unrelated records.
- Egress tests prove zero transmission before consent, after revocation, with stale/mismatched scope, or through any path outside the chokepoint.
- Malicious prompt/provider tests prove zero write capability and no governed hash changes.
- Claim/citation fixtures reject unsupported or cross-generation statements.
- AI-off, unavailable, and provider-substitution regressions produce zero business-result projection changes.

## Approval effect

If accepted, this ADR is the only permitted V2 financial-context AI boundary. It authorizes no provider configuration or implementation before the complete Architecture package is approved.
