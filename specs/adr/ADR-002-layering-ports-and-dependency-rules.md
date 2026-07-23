# ADR-002 — Layering, Ports & Dependency Rules

- **Status:** Accepted · **Date:** 2026-07-16 · accepted as part of the project-owner-approved architecture baseline
- **Deciders:** Technical Lead / Software Architect + Project Owner (decided — this ADR establishes the AI/deterministic boundary, which Constitution §4 assigns to Project Owner + Technical Lead); design-review board (consulted)
- **Feature/plan:** cross-cutting; enables the Walking Skeleton (13); realizes ADC-02

## 1. Status
Accepted as part of the project-owner-approved architecture baseline. Formalizes the logical layering and ports in 06 §7 (with §7.1–7.3) as a binding, testable code structure.

## 2. Context
FinSight's central guarantees are structural, not conventional (NFR-047): the **deterministic core must be independent of delivery and storage** (so it is headless-testable and web-migratable — NFR-070), and the **AI layer must be unable to author findings** (Trust > AI — DEC-005, P-8). 06 §7 defines Clean-Architecture layers and **core-owned ports**; this ADR binds them so `/sdd:trace` and an import test can enforce them.

## 3. Decision
- **Four layers, dependencies point inward:** **delivery** (UI shell, AI experience surfaces) → **application** (orchestration, use-cases: intake, extraction, verification, reporting, consent) → **domain core** (rules engine, findings model, capabilities, Review-Cycle model) → and **infrastructure** (DAL, audit store, AI provider adapter) implementing **core-owned ports**. The **domain core imports no UI, storage, provider, or AI types.**
- **Package structure (Python):** `finsight/domain/` (core), `finsight/application/` (services/use-cases), `finsight/infrastructure/` (DAL, audit, provider adapters), `finsight/delivery/` (shell bridge, AI surfaces). A **composition root** (`finsight/app.py` or equivalent) wires concrete implementations to ports; nothing else constructs collaborators.
- **Core-owned ports (interfaces defined in the domain core, implemented outward):**
  - **`FindingsCommandPort`** — create/mutate findings, set severity. **Wired only to the Rules Engine and rule packs** (C-07/C-11) at the composition root; **never to the AI layer.**
  - **`FindingsQueryPort`** — read-only access to findings and verified data. The **only** core interface exposed to the AI layer (C-15) and to read-only surfaces (C-09b).
  - **`AuditEventPort`** — emit audit events; implemented by the audit store (ADR-005).
  - **Repository interfaces** — persistence; implemented by the DAL (ADR-004).
  - **`AIProviderPort`** — the AI provider adapter (XP-03), implemented in infrastructure; used only by C-15 (deferred provider selection, ADC-03).
- **Command/Query segregation for findings (06 §7.1):** the AI layer is handed only `FindingsQueryPort`; it is never wired to `FindingsCommandPort` at the composition root, so **there is no code path by which "AI writes a finding / sets a severity."** The core is Python (ADR-001), which has **no compile-time access control**, so this boundary is **not** enforced by the compiler; it is enforced by three concrete mechanisms: (1) construction — `FindingsCommandPort` is injected only into C-07/C-11 at the composition root; (2) a **mandatory CI architecture-fitness (import) test** that fails the build if any delivery/AI module references `FindingsCommandPort`; and (3) module-private construction of findings/severity (frozen types, no public constructor) plus a runtime guard. This is the enforcement of DEC-005/NFR-047 — behavioral tests (provider-swap, AI-off) are defense-in-depth, not the boundary.
- **Findings model/experience split (06 §7.3):** the finding **contract, severity, lifecycle** live in the core (C-09a, ADR-007); the **experience** (views/search/render) lives in delivery (C-09b) and reads via `FindingsQueryPort`.

## 4. Alternatives Considered
| Alternative | Why not |
|---|---|
| Layered-by-technology (MVC, no ports) | Delivery can call any core write; the AI boundary becomes a convention, not structural — fails NFR-047. |
| Single "services" layer | No enforced dependency direction; core cannot be lifted to web (NFR-070) or tested headless. |
| Guard the AI boundary with runtime checks only | Runtime guards are bypassable and after-the-fact; segregation makes the write path *absent*. |

## 5. Consequences
**Positive:** the AI/deterministic boundary and core independence are enforced by construction and a mandatory CI architecture-fitness test (not by convention, and — since the core is Python — not by the compiler); the core is headless-testable and web-migratable; modules are replaceable behind ports.
**Negative (accepted):** more interfaces and a composition root to maintain; a small discipline cost to keep imports clean (enforced by CI, so it does not decay).

## 6. Dependencies
- **ADR-001** (Python core, headless) · **ADR-004** (repository ports) · **ADR-005** (`AuditEventPort`) · **ADR-006** (`VerifiedDataset` as the engine's only input) · **ADR-007** (findings ports).

## 7. Verification Strategy
- **Import-contract test in CI** (e.g., import-linter): fails if `finsight/domain` imports UI/storage/provider/AI packages, or if `finsight/delivery` (AI) references `FindingsCommandPort`.
- **Headless test harness:** the core runs with in-memory/no-op ports (no UI, no real DB) — proves independence.
- **Composition-root review:** `FindingsCommandPort` is wired only to C-07/C-11.
- Standing item on the design board for any change near the ports (NFR-047).

## 8. Traceability
- **Serves:** DEC-005 (boundary), AP-08/09, TB-03. **NFRs:** NFR-031 (composable), NFR-047 (boundary enforced by design), NFR-070/072 (web/storage independence). **Constitution:** P-1, P-8. Realizes **ADC-02**; underpins ADR-005/006/007.

## 9. Risks
- **Boundary erosion** over time as AI features grow — mitigated by the CI import test + provider-swap/AI-off regressions + design-board check.
- **Over-abstraction** (ports nobody varies) — mitigated by YAGNI: only the ports named here exist; add more only when a second implementation appears.

## 10. Open Questions (resolved under the approved baseline)
- Minimal orchestration mechanism for the application layer (a simple deterministic sequencer for the skeleton; full ADR deferred — ADC-04/AOQ-03). No autonomous agents (DEC-034).
