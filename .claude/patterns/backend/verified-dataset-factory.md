# Pattern — VerifiedDataset as the Only Analysis Input

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [data-verification.md](../../standards/data-verification.md); `ADR-006`; `ADC-10`.

## Convention
The rules engine accepts **only** a `VerifiedDataset`, and a `VerifiedDataset` can be constructed **only** through the verification path (`application/verification.py` → `domain/verified_dataset.py`). This makes "no analysis on unverified data" structurally enforced rather than merely documented.

## Example (existing enforcement)
- `domain/verified_dataset.py` is the sole factory/importer of the verified type.
- A fitness test (`tests/fitness/`, e.g. `test_verification_is_only_factory_importer`) asserts that only `verified_dataset.py` and `verification.py` construct it.

## Checks
- Analysis code paths take a `VerifiedDataset`, not raw intake data.
- Fitness test for the sole-factory constraint passes.
