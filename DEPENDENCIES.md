# FinSight — Dependency Governance

**Scope:** build/release only. FinSight the product contains **no** version-management UI, **no** self-update capability, and **no** AI agent for dependency handling. Version validation belongs to the build/release pipeline, never to the financial-review workflow (Constitution §6; DEC-034).

**Single source of truth:** [build/versions.json](build/versions.json). Pins are mirrored in [requirements.txt](requirements.txt), [requirements-dev.txt](requirements-dev.txt), and [pyproject.toml](pyproject.toml). Change versions in `versions.json` first, then reconcile the pin files (CI's *verify-installed-matches-pins* step catches drift).

**Versions verified against PyPI / python.org / sqlite.org on 2026-07-28.** Do not assume; re-verify on each dependency review.

---

## 1. Dependency status report

| Component | Current (this env) | Required min | Latest stable | Pinned | Recommendation | Compatibility risk |
|---|---|---|---|---|---|---|
| Python | **3.11.15** | 3.10 | 3.14.6 | target 3.12 | Meets the floor. Use 3.12 for release builds as planned; keep 3.11 in CI. | Low–Medium — supported, but not the selected release-build interpreter. |
| SQLite (stdlib-bundled) | 3.53.1 | 3.35.0 | 3.53.3 | n/a (travels with Python) | No action; above floor with margin. | Low — bundled with the interpreter; not pip-managed. |
| SQLCipher (via `sqlcipher3`) | 4.12.0 community / SQLite 3.51.1 | SQLCipher 4.x | 4.12.0 | via `sqlcipher3==0.6.2` | Qualified for encrypted local storage; startup verifies cipher activation and schema access. | Medium — native wheels must remain qualified on Windows and macOS release targets. |
| openpyxl | 3.1.5 | 3.1.0 | 3.1.5 | 3.1.5 | Current — no action. | Low. |
| cryptography | 49.0.0 | 49.0.0 | 49.0.0 | 49.0.0 | Qualified for Ed25519 authorization-manifest verification. | Low–Medium — security-sensitive dependency; retain exact pin and release review. |
| sqlcipher3 | 0.6.2 | 0.6.2 | 0.6.2 | 0.6.2 | Qualified; no plaintext database fallback is permitted. | Medium — native wheel and SQLCipher linkage require both-OS release verification. |
| PySide6 | 6.11.1 | 6.11.1 | 6.11.1 | 6.11.1 | Qualified for the desktop UI and accessibility tests. | Medium — native Qt runtime requires release-target smoke tests. |
| QtAwesome | 1.4.2 | 1.4.2 | 1.4.2 | 1.4.2 | Qualified for the bundled, cross-platform Phosphor icon language used by the desktop shell. | Low–Medium — packaged builds must retain QtAwesome font resources. |
| QtPy | 2.4.3 | 2.4.3 | 2.4.3 | 2.4.3 | Qualified compatibility layer required by QtAwesome. | Low. |
| pytest | 9.1.1 | 8.0.0 | 9.1.1 | 9.1.1 | Current — no action. | Low. |
| pytest-qt | 4.5.0 | 4.5.0 | 4.5.0 | 4.5.0 | Current — no action. | Low. |
| import-linter | 2.13 | 2.0 | 2.13 | 2.13 | Current — no action. | Low. |
| ruff | 0.15.22 | 0.14.0 | 0.16.0 | 0.15.22 | Pinned version meets the floor; review 0.16.0 separately after Workflow 1. | Low–Medium — pre-1.0 lint rules may change. |
| coverage | 7.15.2 | 7.6.0 | 7.15.2 | 7.15.2 | Current — no action. | Low. |

## 2. Environment readiness

No pinned Workflow 1 runtime, desktop, test, lint, or coverage dependency is missing from the project
virtual environment. To reproduce it on Python 3.10 or newer:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Workflow 1 dependency qualification evidence is recorded under
`initiatives/configurable-rule-engine-v2/verification/`.

## 3. Pinning strategy (intentional; drift-detectable; upgrade-reviewable)

- **Exact pins (`==`)** for the whole dev/build toolchain and runtime dependencies — reproducible builds and deterministic behavior require that no unpinned resolution changes behavior between machines or over time.
- **`required_min`** in `versions.json` is the *floor* that CI enforces as a hard gate. `pinned` is the exact version installed. `latest_stable` is the drift reference (WARN-only).
- **Detectable drift:** `build/validate_deps.py` compares installed vs min vs latest; CI's `pip check` + `--dry-run` step confirms the pins still resolve together.
- **Reviewable upgrades:** bumping a version is a one-line edit to `versions.json` + the pin files, reviewed like any change. The weekly scheduled CI run reports (never applies) new latest-stable versions.

## 4. Build-time validation process

Run before building/packaging or on demand:

```bash
python build/validate_deps.py
```

Exit-code contract:
- **Exit 1 (FAIL):** a required dependency is missing, or installed below `required_min`, or Python below its floor. Blocks the build.
- **Exit 0 with WARN:** installed ≥ min but < latest_stable (drift) — informational, non-blocking.
- **Exit 0 (PASS):** all required minimums met.

The script is network-free, read-only, and never mutates the environment or the product.

## 5. CI dependency-validation stage

Defined in [.github/workflows/dependency-validation.yml](.github/workflows/dependency-validation.yml). On every push/PR (and weekly), across `{ubuntu, windows, macos} × {3.10, 3.11, 3.12}`:

1. **Validate required minimums (blocking)** — `python build/validate_deps.py`; fails the build only on below-minimum/missing.
2. **Report outdated (non-blocking)** — `pip list --outdated`, `continue-on-error`.
3. **Verify installed matches pins** — `pip install --dry-run -r requirements-dev.txt` + `pip check` to catch pin/lock drift and conflicting transitive constraints.

Windows + macOS are the NFR-029 release targets; this stage composes with the both-OS determinism/test matrix (TASKS-F-02-02 T-021) rather than replacing it.

## 6. Upgrade / review workflow

1. Re-verify latest-stable from PyPI/python.org/sqlite.org (record the date in `versions.json.as_of`).
2. Edit `versions.json` (`pinned`, and `required_min` only when intentionally raising the floor).
3. Reconcile `requirements*.txt` and `pyproject.toml`.
4. Run `python build/validate_deps.py` locally; let CI run the full matrix.
5. Review as a normal change; the human decision to adopt a new floor is a governance action, not an automated one.
