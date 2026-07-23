# Standard — Financial Determinism

**Layer:** standard (normative, leaf). Referenced by skills and recipes. References no agents.
**Origin / authority:** `specs/adr/ADR-003-exact-decimal-and-determinism.md`; `specs/06-architecture.md §12.2`; `NFR-021`, `NFR-029`, `NFR-036`, `NFR-037`, `NFR-048`, `NFR-059`.

## Rule

1. **Exact decimal only.** Financial computation uses exact decimal arithmetic. **No floats** anywhere on the compute path (`NFR-059`, `ADR-003`, `ASR-06`). Money handling lives in `domain/money.py`.
2. **No non-deterministic inputs on the compute path.** No wall-clock, locale, random number generation, or hash-iteration ordering influences a computed result. Time enters only through an injected `Clock` port — "no wall-clock in domain" (`ADR-003`, `domain/ports.py`, `AR-01`, `P-7`).
3. **Reproducibility.** The same verified inputs and configuration produce **byte-identical** outputs across platforms (Windows/macOS) and across AI providers (`NFR-021`, `NFR-029`). Results are replayable from recorded inputs and config version (`F-02-06`).
4. **Explicit ordering.** Aggregation and iteration order is explicit and deterministic; results do not depend on collection iteration order.
5. **LLM restriction.** An AI model may **never** produce, adjust, or approve any financial value, variance, severity, RAG, score, or finding. Deterministic logic decides; AI explains only (see [ai-governance.md](ai-governance.md)).

## Verification gates

Golden-dataset regression, determinism (repeated-run identity), and provider-swap invariance are **release gates** (`NFR-036`, `NFR-037`, `NFR-048`; tests under `tests/golden/`, `tests/determinism/`). These gates may not be weakened to make a change pass (see [remediation skill](../skills/remediation/SKILL.md) prohibition).

## Escalation

If a required rule, rounding behavior, or aggregation order is not defined in `specs/`, raise a **Red Card**. Do not invent numeric behavior.
