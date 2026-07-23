# Pattern — Severity Non-Color Encoding

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [accessibility.md](../../standards/accessibility.md); `NFR-025`.

## Convention
Severity is conveyed by **icon + shape/marker + text label** — never by color alone — so it is legible without color perception.

## Example (existing text-mode reference)
```python
# delivery/wizard.py
SEVERITY_MARK = {"Critical": "[XXX]", "High": "[!!]", "Medium": "[=]", "Low": "[.]"}
# always paired with the severity's text label
```

## Guidelines
- In any richer shell, keep the shape/marker + label; color may be added but is never the sole channel.

## Checks
- `tests/accessibility/` asserts severity is distinguishable without color.
