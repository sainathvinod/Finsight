# Standard — Security

**Layer:** standard (normative, leaf). Referenced by skills and recipes. References no agents.
**Origin / authority:** `specs/adr/ADR-004-persistence-sqlite.md`; `specs/10-ai-and-agents.md §3`; `specs/02-non-functional-requirements.md`; `CLAUDE.md`. Only repository- and spec-grounded rules appear here; no compliance framework is claimed that the specs do not state.

## Rule

1. **Local, self-contained data.** Review data lives in a single local store (`ADR-004`). Encryption of data at rest is required **before any real (non-synthetic) data is used**; until then the product operates on synthetic data only.
2. **Synthetic thresholds are demonstration-only.** Synthetic thresholds and datasets are never treated as production configuration; real finance thresholds are human-owned and supplied before real-world use (`CLAUDE.md`).
3. **AI egress control.** When the AI layer exists, data may be transmitted to a provider only with informed consent, with data minimization/masking applied, and only to an approved provider (`10 §3`, `FR-097`, `DEC-006`, `DEC-007`; see [ai-governance.md](ai-governance.md)). Sensitive data must not reach an unapproved external provider.
4. **No secrets in the repository.** Credentials, tokens, and provider keys are never committed. Configuration references secrets; it does not embed them.
5. **Read-only posture.** FinSight does not write back to source systems (see [data-verification.md](data-verification.md), [architecture.md](architecture.md)); this is a security property as well as an architectural one.

## Not in scope / not claimed

Specific external compliance certifications, penetration-test results, or threat-model claims are **not** asserted by this standard. If a task requires a security control not grounded in `specs/`, raise a **Red Card** rather than inventing a compliance claim.
