# Pattern — Layering & Ports

**Layer:** pattern (leaf, example/convention). References standards and specs, never agents. Not a product requirement.
**Governs against:** [architecture.md](../../standards/architecture.md); `ADR-002`; `.importlinter`.

## Convention
Cross-layer capabilities are reached through **ports** declared in `domain/ports.py`, not by importing infrastructure from inner layers. Dependencies point inward: `delivery → application → domain`; infrastructure implements ports.

- Domain imports nothing from application/infrastructure/delivery (`.importlinter` *C-DOMAIN-INDEP*).
- `sqlite3` appears only in infrastructure (*C-DAL-ONLY-STORAGE*).

## Example (existing code shape)
```python
# domain/ports.py — capability the domain needs, defined without knowing the implementation
class AuditEventPort(Protocol):
    def emit(self, cycle_id: str, action: str, actor: str, detail: dict) -> None: ...

# infrastructure/audit.py — the implementation lives outside the domain
class SqliteAuditEvents:  # implements AuditEventPort
    ...
```

## Checks
- Run `lint-imports` — layering and storage contracts must pass.
- New side-effecting capability → add a port, not a direct infra import.
