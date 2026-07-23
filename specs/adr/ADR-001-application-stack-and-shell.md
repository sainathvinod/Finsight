# ADR-001 — Application Stack & Shell

- **Status:** Accepted · **Date:** 2026-07-16 · accepted as part of the project-owner-approved architecture baseline
- **Deciders:** Technical Lead / Software Architect (decided); design-review board (consulted) — per Constitution §4
- **Feature/plan:** cross-cutting; enables the Walking Skeleton (13) and E-14

## 1. Status
Accepted as part of the project-owner-approved architecture baseline. This ADR validates the directional stack in DEC-003 ("Electron **or** Tauri UI shell over a Python application core; final stack validated during architecture design").

## 2. Context
FinSight is a **single-user, desktop-first** application (DEC-003/008) that must: run with **parity on Windows and macOS** (NFR-028) in **restricted corporate environments** on **8–16 GB laptops** (NFR-030, DEC-016); work **fully offline** with **no external egress** except a consented AI provider (NFR-007/011); produce **byte-identical deterministic results** across platforms (NFR-029) using **exact decimal arithmetic** (NFR-059); keep the **domain core independent of the delivery shell** so a future web transition does not reimplement logic (NFR-070); and host an **optional, provider-abstracted AI layer** with **no autonomous agents** (DEC-034). The AI and data-processing ecosystem (extraction, decimal, SQLite, rules) is strongest in Python (DEC-003 rationale). A web-technology UI keeps the future web migration cheap (DEC-003).

## 3. Decision
- **Application core: Python 3.x**, run **headless** — the domain core (rules engine, findings, cycle model), application services, extraction, DAL, and the optional AI adapter. Rationale: exact-decimal support (`decimal.Decimal`), mature Excel/PDF extraction libraries, built-in `sqlite3`, testable without a UI (satisfies the headless-core requirement, ADR-002), and the strongest AI/data ecosystem (DEC-003).
- **UI: web technology** (HTML/CSS/JS) rendered in a **desktop shell**. For the MVP the shell is **Tauri** (system webview + a small native runtime). Rationale over Electron: markedly lower memory/footprint on 8–16 GB restricted laptops (NFR-030, DEC-016), a more restrictive default security posture (aligns with the confidentiality model), and a web-tech front end that carries over to the web migration (NFR-070). **Electron is the accepted fallback** if the Python-sidecar packaging (§9 OQ) or an Amerisure environment constraint favors it — ADR-002's boundary makes the shell replaceable without touching the core.
- **Shell ↔ core boundary: local, loopback-only.** The Python core runs as a **sidecar/child process**; the shell communicates over a **localhost-bound (127.0.0.1) or stdio IPC** channel. **No network listener is exposed beyond loopback** (NFR-011). The UI holds no business logic (06 C-01).
- **AI layer: a thin provider adapter (XP-03), not an agent framework.** DEC-003 mentioned LangGraph/LangChain directionally; per DEC-034 (no autonomous agents) and 10-ai-and-agents, the AI layer is a single grounded, retrieval-based call behind a pluggable adapter (stub/local provider for the skeleton). **This ADR does not select an AI provider** — that is a separate, deferred ADR (ADC-03); OQ-3 is resolved under the approved baseline.
- **Test tooling:** `pytest` for the Python core (unit, golden-dataset, determinism, provider-swap); an **architecture/import-contract test** in CI (ADR-002); a **CI matrix running Windows and macOS** (NFR-029). Minimal manual keyboard/screen-reader smoke for the skeleton UI.
- **Packaging:** desktop installers for Windows and macOS that install under standard user rights (NFR-030); the Python runtime is bundled (no system-Python dependency).

## 4. Alternatives Considered
| Alternative | Summary | Why not (for MVP) |
|---|---|---|
| **Electron shell** | Chromium + Node shell over Python core | Heavier memory/footprint (poor fit for 8 GB restricted laptops); larger attack surface. **Kept as accepted fallback** — easier Python integration and strong enterprise familiarity. |
| **Native UI (WinUI/AppKit or Qt)** | Platform-native or Qt UI | Two UIs or a heavy toolkit; no web-tech reuse for the future web migration (NFR-070); higher cross-platform-parity cost. |
| **Web app now** | Browser + server | Contradicts desktop-first, offline, single-user, restricted-egress constraints (DEC-003/016, NFR-007/011). Web is the *future* target, not MVP. |
| **Non-Python core (e.g., .NET/JVM)** | Core in another ecosystem | Weaker AI/extraction ecosystem; contradicts DEC-003 direction. |

## 5. Consequences
**Positive:** headless, testable Python core (enables ADR-002/ADR-003 and provider-swap regression); web-tech UI eases the web migration; Tauri fits restricted hardware and the confidentiality posture; shell is replaceable behind the local boundary.
**Negative (accepted):** Tauri adds a Rust toolchain and Python-sidecar packaging complexity (spike, §9); a two-process (shell + core) model adds a local IPC boundary to design and test; bundling Python increases installer size.

## 6. Dependencies
- **ADR-002** (layering/ports) — the shell/core boundary and the core's independence.
- **ADR-004** (SQLite via DAL) — the core owns persistence; the shell never touches storage.
- **ADR-003** (determinism) — cross-platform byte-identical results on this stack.
- Deferred: **ADC-03** (AI provider), **ADC-08** (at-rest/secrets), **ADC-04** (orchestration, minimal).

## 7. Verification Strategy
- CI builds and runs the core test suite on **both Windows and macOS** (NFR-029).
- An **architecture/import test** proves the core imports no UI/shell/storage/provider types (ADR-002).
- A **loopback-only assertion**: the core exposes no non-loopback listener (NFR-011).
- The Walking Skeleton (13) runs end-to-end on the chosen shell on both platforms.

## 8. Traceability
- **Serves:** DEC-003 (stack direction), DEC-016 (hardware), DEC-008 (single-user).
- **NFRs:** NFR-007 (offline), NFR-011 (no egress), NFR-028 (parity), NFR-029 (determinism), NFR-030 (restricted env), NFR-070/072 (web-migration/storage independence), NFR-059 (decimal, via Python).
- **Constitution:** P-7/P-8 (determinism), P-11 (AI optional), P-16 (desktop review platform). Realizes ADC-01.

## 9. Risks
- **Tauri Python-sidecar packaging** may be fiddly in restricted environments — mitigated by the spike (OQ) and the Electron fallback.
- **IPC boundary** adds complexity — mitigated by keeping the contract minimal (the core is headless and API-driven).

## 10. Open Questions (resolved under the approved baseline)
- **Spike (pre-skeleton):** validate Tauri + bundled-Python packaging and loopback IPC in the target restricted environment; if it fails acceptance, adopt the Electron fallback (no core change). *(Feeds AOQ-02.)*
- **OQ-3** (approved AI endpoint) — deferred; does not block this ADR (AI provider is a separate ADR; skeleton uses a stub).
