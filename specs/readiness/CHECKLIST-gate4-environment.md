# Gate 4 Environment Readiness Checklist

> **Environment readiness is confirmed under the project-owner-approved baseline.** AI may scaffold and attach evidence; provisioning org infrastructure and code-signing certificates remains a human/ops action and is not fabricated here.

- **Purpose:** prove the build environment is born-gated so `T-001` can run test-first with green CI and a live traceability gate.
- **Required human approvers:** **Project Owner** confirms readiness (a readiness check, not a governance decision); **ops/human** provisions runners + certificates.
- **Evidence required:** logs/screenshots/output links attached per row.
- **Acceptance criteria:** every row checked with evidence; a change cannot merge without both-OS green CI **and** `TRACEABILITY: PASS`.
- **Prerequisites:** Gate 2 (baselined `specs/` to trace) and Gate 3 (the stack ADR Accepted, so the repo layout is unambiguous).

| # | Check | How to verify | Evidence | Pass? |
|---|---|---|---|---|
| 1 | Single repository stood up with the layer package layout (domain/application/infrastructure/delivery) per the layering ADR | inspect tree | {link} | {☐} |
| 2 | Plugin toolchain installed and pinned to a release tag | `.claude/settings.json`; `claude plugin details` | {log} | {☐} |
| 3 | CI matrix runs on **Windows AND macOS** | CI config + a green run on both OS for a trivial change | {logs, both OS} | {☐} |
| 4 | Traceability gate wired: `/sdd:trace --fail-on-orphans` gating merges on `^TRACEABILITY: PASS$` | CI config + trace output | {output} | {☐} |
| 5 | Test harness live: `pytest` + import-linter (architecture-fitness) contracts | passing run | {log} | {☐} |
| 6 | Architecture-fitness test present: core imports no UI/storage/AI; findings command port isolated to engine; DAL-only storage | import-linter contract + run | {log} | {☐} |
| 7 | ≥1 **synthetic** golden dataset present (GED + Budget, seeded to one expected finding) per PLAN §Implementation Assumptions | file in `tests/`; synthetic-only | {path} | {☐} |
| 8 | Dev-data-hygiene guard active (rejects real-data-shaped fixtures — NFR-018) | guard test | {log} | {☐} |
| 9 | Determinism harness ready: exact-decimal context pinned; Excel date-system/encoding pinned | unit/config | {log} | {☐} |
| 10 | Hooks re-verified in the repo (baseline-immutability exit 2; spec-lint active) | hook test | {log} | {☐} |

**Readiness confirmation** *(human):* {name, role} · {date} — "Gate 4 environment is ready; the merge gate is enforcing."
