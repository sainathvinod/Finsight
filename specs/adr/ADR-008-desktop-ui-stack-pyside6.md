# ADR-008 — Desktop UI Stack: PySide6

- **Status:** Accepted · **Date:** 2026-07-23 · accepted by the product owner as part of the authorized product-implementation phase
- **Deciders:** Technical Lead / Software Architect (decided); product owner (approved the stack in the Phase 0/Phase 2 authorization)
- **Feature/plan:** cross-cutting delivery-ring decision; enables the real desktop product (Phase 2+). **Supersedes the UI-shell portion of ADR-001** (Tauri/Electron web-shell + Python sidecar) and the directional Electron/Tauri mention in DEC-003.

## 1. Status
Accepted. Resolves the deferred GUI binding (ADR-001 left the shell as Tauri-with-Electron-fallback; `ADC-01`). The Python application core, layering (ADR-002), and determinism (ADR-003) are unchanged.

## 2. Context
The deterministic core, application services, extraction, SQLite DAL, and the optional AI adapter are all Python (ADR-001 §3). The product must run on macOS and Windows on restricted 8–16 GB laptops, fully offline, with byte-identical results, and must stay maintainable and editable through source. ADR-001 chose a web-technology shell (Tauri) over a Python sidecar, which introduces a second language (Rust), a web front end, and a loopback/stdio IPC boundary between shell and core.

## 3. Decision
- **UI: PySide6 (Qt for Python)** rendered **in-process** with the Python core. No web technology, no Rust shell, no sidecar, and **no IPC boundary** — the UI calls application-layer query/command services directly.
- **Dependency direction:** UI (delivery ring) → application services only. The UI constructs no repositories, executes no SQL, and holds no business logic; services are wired by the composition root (`finsight.app.build_query_services`). The headless core (ADR-002) is preserved: importing the core never imports PySide6, and the deterministic workflow runs with PySide6 absent.
- **Theming:** centralized design tokens + generated QSS (monochrome, single accent). **Testing:** `pytest-qt` for UI, alongside the existing `pytest` core suites and the import-contract fitness tests. **Packaging (later phase):** PyInstaller/Briefcase to a macOS `.app`/DMG and a Windows executable from one codebase.

## 4. Alternatives Considered
| Alternative | Summary | Why not |
|---|---|---|
| **Tauri** (ADR-001 MVP choice) | Rust shell + system webview + web front end + Python sidecar | Two extra languages/toolchains, a web front end, and a loopback IPC boundary to design/test; reintroduces a browser→Python seam. In-process PySide6 removes all of these for a single-user desktop product. |
| **Electron** (ADR-001 fallback) | Chromium shell + Python sidecar | Higher memory footprint on restricted laptops; same sidecar/IPC complexity. |
| **PySide6 (chosen)** | Qt UI in the same Python process | In-process calls to the existing core, first-class dense tables/forms, one language, one test runner, native macOS/Windows packaging. |

## 5. Consequences
**Positive:** no IPC/serialization boundary; the UI reuses the existing services directly; one language and one test toolchain; strong native table/form/accessibility support; straightforward cross-platform packaging.
**Negative (accepted):** larger installer (bundled Qt, ~60–120 MB); the web-migration path that a web-tech shell would have eased is deferred (the layering in ADR-002/NFR-070 keeps a future web delivery possible by re-implementing only the delivery ring); Qt is a substantial dependency to bundle.

## 6. Dependencies
`PySide6` (desktop optional dependency), `pytest-qt` (dev). The deterministic core and its `openpyxl`-only runtime footprint are unchanged; PySide6 is not a core runtime dependency.

## 7. Verification Strategy
`pytest-qt` UI tests (shell launch, navigation, empty states, real data rendering, keyboard navigation, non-color severity); the import-contract fitness tests confirm the UI holds no `sqlite3`/repository imports and the core stays headless; offscreen rendering used for automated visual checks.

## 8. Traceability
Supersedes ADR-001 (UI shell) and the Electron/Tauri direction in DEC-003. Preserves ADR-002 (layering, headless core), ADR-003 (determinism), NFR-028 (Windows/macOS parity), NFR-030 (restricted laptops), NFR-070 (delivery-replaceable core). AI provider selection remains deferred to `ADC-03`.

## 9. Open Questions
- Packaging specifics (PyInstaller vs Briefcase, code signing/notarization) are deferred to the packaging phase.
- Light/dark: light theme is delivered first; dark mode only if it can be finished to the same standard.
