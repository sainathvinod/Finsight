# Pattern — Provider Adapter (design-only, Release 2)

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Status:** DESIGN-ONLY — provider/model binding is deferred (`ADC-03`); no concrete provider is present.
**Governs against:** [architecture.md](../../standards/architecture.md), [ai-governance.md](../../standards/ai-governance.md); `XP-03`, `FR-104`, `NFR-046`, `DEC-016`.

## Convention (as specified)
AI inference sits behind a provider-adapter interface so that "providers are configuration, not code." The Ask Fin domain behavior depends on the interface, not on any concrete provider.

```
Ask Fin (domain behavior)  →  AI provider interface  →  concrete provider adapter
```

## Boundaries
- Swapping or adding a provider changes configuration + an adapter only; it never changes deterministic components (must preserve provider-swap invariance, `NFR-048`).
- Confidentiality order: local/on-device (future option, `DEC-016`) → approved enterprise-hosted (primary) → other consented external (advisory). Sensitive data never goes to an unapproved provider.
- **Ollama** is not a selected provider; it may be listed only as a possible future local adapter, clearly marked not-implemented.

## Checks (when built)
- Deterministic outputs are byte-identical across provider swaps.
