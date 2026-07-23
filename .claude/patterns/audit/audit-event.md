# Pattern — Audit Event Emission

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [audit-traceability.md](../../standards/audit-traceability.md); `ADR-005`; `FR-084`–`FR-090`.

## Convention
Meaningful actions emit an audit event through the domain-owned `AuditEventPort`, so any review can be reconstructed. The port keeps emission independent of the storage implementation.

## Example (existing shape)
```python
# domain/ports.py
class AuditEventPort(Protocol):
    def emit(self, cycle_id: str, action: str, actor: str, detail: dict) -> None: ...
```

## Guidelines
- Emit on: verification, correction, certification, rule run, export, and (R2) AI interaction.
- `detail` carries the event-specific fields listed in the audit standard.

## Checks
- Correcting or certifying data produces exactly one audit event with actor + timestamp + fingerprint (`tests/test_audit.py`, `tests/test_provenance.py`).
