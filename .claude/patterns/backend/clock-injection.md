# Pattern — Clock Injection (no wall-clock in domain)

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [financial-determinism.md](../../standards/financial-determinism.md); `ADR-003`.

## Convention
Time enters the domain only through an injected `Clock` port. The domain never calls `datetime.now()` or any wall-clock/locale/RNG source on the compute path, so results are reproducible and testable.

## Example
```python
# domain/ports.py
class Clock(Protocol):
    def now(self) -> datetime: ...

# domain code receives the clock; it never reads the system clock directly
def stamp(event, clock: Clock) -> Event:
    return event.with_time(clock.now())
```

## Checks
- No direct `datetime.now()` / `time.time()` in `domain/` or on the compute path.
- Tests inject a fixed clock and assert identical output across runs.
