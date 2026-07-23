# Pattern — Exact Decimal Money

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [financial-determinism.md](../../standards/financial-determinism.md); `ADR-003`; `NFR-059`.

## Convention
All monetary and computed financial values use exact `Decimal` — never `float`. Money handling is centralized in `domain/money.py`. Parsing, arithmetic, and rounding go through that module so behavior is uniform and deterministic.

## Example
```python
from decimal import Decimal
# Correct: exact decimal from string
amount = Decimal("1234.56")
# Wrong: float anywhere on the compute path
# amount = 1234.56   # forbidden — introduces non-determinism
```

## Checks
- No `float(...)` or float literals on the compute path.
- Repeated runs on identical inputs produce byte-identical output (`tests/determinism/`).
