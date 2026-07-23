# Pattern — Finding Guarded Constructor

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [architecture.md](../../standards/architecture.md), [ai-governance.md](../../standards/ai-governance.md); `ADR-007`; `RJ-01`, `FR-069`, `FR-070`.

## Convention
A `Finding` is created **only** by the deterministic rules engine, through the command port. Direct construction is guarded so that neither the AI/explanation side nor delivery can fabricate a finding.

## Example (existing enforcement)
```python
# domain/findings.py
@dataclass(frozen=True)
class Finding:
    ...  # created only via the rules engine / FindingsCommandPort (ADR-007)

# domain/ports.py — command/query segregation
class FindingsCommandPort(Protocol):
    def add(self, finding: Finding) -> None: ...   # wired ONLY to rules/engine
class FindingsQueryPort(Protocol):
    def list(self) -> list[Finding]: ...           # read-only; the AI/delivery side holds this
```

## Checks
- The AI/explanation path imports only the query port.
- Severity/evidence are rule-produced; explanations never set them.
