# Pattern — Grounded AI Explanation (design-only, Release 2)

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Status:** DESIGN-ONLY — the AI layer is specified but **not implemented** (`E-09`). No endpoints or models are asserted.
**Governs against:** [ai-governance.md](../../standards/ai-governance.md); `10 §4`; `FR-094`, `FR-099`, `NFR-050`.

## Convention (as specified)
An AI explanation is constructed from a grounded context assembled out of **already-computed** verified data, approved findings, evidence, and history — then narrated. The model receives facts; it does not compute them.

```
verified data + approved findings + evidence  →  grounded context  →  model narration (cited)
```

## Boundaries
- The explanation cites the evidence it draws on; when evidence is absent it states "evidence not found" and does not guess.
- The model never creates/changes findings, severity, or any value (see the AI-governance standard).

## Checks (when built)
- Every explanation is traceable to grounded evidence; no ungrounded claims.
