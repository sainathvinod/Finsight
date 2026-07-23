# Finding — <finding id>

<!-- Template (leaf). Scaffolding only — no normative rules, no agent references.
     Findings are created ONLY by the deterministic rules engine (ADR-007), never by AI.
     This scaffold documents the record shape; it does not authorize AI to create findings. -->

- **Finding ID:** <id>
- **Rule reference:** <rule ID from specs/05-rules-catalog.md>
- **Severity:** <Critical | High | Medium | Low>  <!-- rule-computed; shown with icon+shape+label, never color alone (NFR-025) -->
- **Period:** <review period>
- **Affected entities:** <department / GL account / vendor>   <!-- MVP dimensions, DEC-002 -->

## Evidence (deterministic values, not narrated)
| Value | Amount / detail | Source reference |
|---|---|---|

## Lifecycle
- **Status:** <New | Acknowledged | In review | Resolved | Dismissed>   <!-- FR-072 -->
- **Dismissal reason (if dismissed):** <required if status = Dismissed>

<!-- Explanation of this finding for humans is produced by Ask Fin (Release 2), grounded and cited;
     it never changes severity, evidence, or status. See .claude/standards/ai-governance.md. -->
