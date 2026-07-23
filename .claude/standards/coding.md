# Standard — Coding

**Layer:** standard (normative, leaf). Referenced by skills and recipes. References no agents.
**Origin / authority:** `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.importlinter`, `DEPENDENCIES.md`, `build/versions.json`; `specs/adr/ADR-001-application-stack-and-shell.md`, `ADR-003`.

## Language & toolchain

1. **Language:** Python, `requires-python >= 3.10` (recommended build interpreter 3.12). Target version for tooling is `py310` (`pyproject.toml`).
2. **Runtime dependency:** `openpyxl==3.1.5` only. Do not add runtime dependencies without a spec/ADR basis and human approval.
3. **Dev toolchain (pinned):** `pytest==9.1.1`, `import-linter==2.13`, `ruff==0.15.22`, `coverage==7.15.2`. Pins are intentional — the single source of truth is `build/versions.json` (see `DEPENDENCIES.md`).
4. **Lint/format:** `ruff` (config in `pyproject.toml`).

## Structure & conventions

5. **Package root** is `finsight` with layers `finsight.domain`, `finsight.application`, `finsight.infrastructure`, `finsight.delivery`. Preserve inward dependencies (see [architecture.md](architecture.md)); the current tree lives under `src/finsight-V1/`.
6. **Determinism in code:** exact `Decimal` money (`domain/money.py`), time via injected `Clock` port only, no floats on the compute path (see [financial-determinism.md](financial-determinism.md)).
7. **Ports for crossing layers:** side-effecting capabilities (storage, audit, findings mutation, clock) are reached through `domain/ports.py`, not direct imports of infrastructure.
8. **Traceability annotations:** source files carry `# Implements: <ID>` for the approved items they realize (see [audit-traceability.md](audit-traceability.md)).
9. **Minimal change & least privilege:** edit only files a task authorizes; no opportunistic refactors (see [specification-authority.md](specification-authority.md)).

## Escalation

If implementing a task would require a new dependency, a new layer, or a float on the compute path, raise a **Red Card** and stop.
