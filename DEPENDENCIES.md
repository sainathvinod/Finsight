# FinSight — Dependency Governance

**Scope:** build/release only. FinSight the product contains **no** version-management UI, **no** self-update capability, and **no** AI agent for dependency handling. Version validation belongs to the build/release pipeline, never to the financial-review workflow (Constitution §6; DEC-034).

**Single source of truth:** [build/versions.json](build/versions.json). Pins are mirrored in [requirements.txt](requirements.txt), [requirements-dev.txt](requirements-dev.txt), and [pyproject.toml](pyproject.toml). Change versions in `versions.json` first, then reconcile the pin files (CI's *verify-installed-matches-pins* step catches drift).

**Versions verified against PyPI / python.org / sqlite.org on 2026-07-17.** Do not assume; re-verify on each dependency review.

---

## 1. Dependency status report

| Component | Current (this env) | Required min | Latest stable | Pinned | Recommendation | Compatibility risk |
|---|---|---|---|---|---|---|
| Python | **3.9.6** | 3.10 | 3.14.6 | target 3.12 | **Upgrade — blocking.** 3.9 is EOL (2025-10) and below the pytest/coverage floor. Adopt 3.12 (supported to 2028-10). | **High** — EOL interpreter; no security fixes; blocks pinned toolchain. |
| SQLite (stdlib-bundled) | 3.51.0 | 3.35.0 | 3.53.3 | n/a (travels with Python) | No action; above floor with margin. | Low — bundled with the interpreter; not pip-managed. |
| openpyxl | 3.1.5 | 3.1.0 | 3.1.5 | 3.1.5 | Current — no action. | Low. |
| pytest | *not installed* | 8.0.0 | 9.1.1 | 9.1.1 | Install 9.1.1 (needs Python ≥3.10). | Medium — 9.x dropped 3.9; requires the Python upgrade first. |
| import-linter | *not installed* | 2.0 | 2.13 | 2.13 | Install 2.13. | Low. |
| ruff | *not installed* | 0.14.0 | 0.15.22 | 0.15.22 | Install 0.15.22. Pin exact (pre-1.0; rules shift between minors). | Low–Medium — pre-1.0 lints may change; exact pin protects CI stability. |
| coverage | *not installed* | 7.6.0 | 7.15.2 | 7.15.2 | Install 7.15.2 (needs Python ≥3.10). | Medium — 7.15.x dropped 3.9; requires the Python upgrade first. |

## 2. Missing dependency report

Four required dev/build dependencies are absent from the current environment. Install (after upgrading Python to ≥3.10):

```bash
# 1) Provision Python 3.12 (pyenv / official installer / OS package), then in the project venv:
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
# equivalently, the exact pins:
python -m pip install "pytest==9.1.1" "import-linter==2.13" "ruff==0.15.22" "coverage==7.15.2" "openpyxl==3.1.5"
```

`openpyxl==3.1.5` is already present and satisfies the runtime pin.

## 3. Pinning strategy (intentional; drift-detectable; upgrade-reviewable)

- **Exact pins (`==`)** for the whole dev/build toolchain and the runtime dependency — reproducible builds and byte-identical determinism (NFR-021/029) demand that no unpinned resolution changes behaviour between machines or over time.
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
