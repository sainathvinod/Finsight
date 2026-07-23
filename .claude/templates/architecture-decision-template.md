# Technical Implementation Plan — <F-##-##>

<!-- Template (leaf). Scaffolding only — no normative rules, no agent references.
     Produced by the design workflow (recipes/design/architecture/). For a durable
     architecture decision use the SDD ADR flow (specs/adr/) instead — this plan defers to it. -->

- **Traces to Brief:** <brief id> · **Approved items:** <IDs> · **Relevant ADRs:** <ADR-###>
- **Prepared:** <date>

## 1. Approach
<How the approved scope is realized while preserving layering and determinism.>

## 2. Components & responsibilities
| Component | Layer (domain/app/infra/delivery) | Responsibility | Port(s) |
|---|---|---|---|

## 3. Determinism & data boundaries
- Financial truth: <deterministic component> · AI role: <explain-only / n/a>
- Source-system boundary: <read-only; review-local corrections only>

## 4. Ordered tasks (each traceable)
1. <task> → <approved ID>

## 5. Allowed-files list (implementation authorization)
- `<path>` — <why>

## 6. Test strategy
<unit / golden / determinism / fitness / accessibility as applicable>

## 7. Stop conditions / Red Cards
- <missing ADR/decision; would require inventing architecture>
