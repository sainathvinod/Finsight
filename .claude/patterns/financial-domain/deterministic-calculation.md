# Pattern — Deterministic Calculation

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [financial-determinism.md](../../standards/financial-determinism.md); `06 §12.2`; `NFR-021`, `NFR-029`.

## Convention
A financial calculation is a pure function of its verified inputs and configuration version:
`result = f(verified_inputs, config_version)`. No wall-clock, locale, RNG, or iteration-order dependence. Same inputs + same config → byte-identical output on every platform and with any AI provider (AI is not on this path).

## Guidelines
- Sort/aggregate with explicit, stable ordering.
- Record `rule_set_version` and `config_version` with every run so it can be replayed (`F-02-06`).
- Keep the calculation in `domain/rules.py` / `domain/` — never in delivery, UI, or an AI prompt.

## Checks
- `tests/golden/` (fixed inputs → fixed expected output) and `tests/determinism/` pass.
