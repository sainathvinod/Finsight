# T-001 Implementation Assets (copy-ready specifications)

> **AI-prepared engineering assets, approved under the current baseline for use at T-001.** These are the exact contents T-001 instantiates. No rule/finding/verification/UI logic is implemented here. Platform/version placeholders (`<pin at T-001>`) are confirmed at execution.

## 1. T-001 Readiness Summary
Every foundation asset T-001 needs is specified below in copy-ready form: repo scaffold + Python layout, dependency strategy, CI workflow, import-linter contracts, traceability/annotation conventions, determinism standards, the synthetic golden fixture spec, dev-data-hygiene enforcement, and developer standards (tests/commits/branch protection). All align with ADR-001–007, PLAN-F-02-02, and GATE-4-IMPLEMENTATION-PACKAGE. The two carried-forward execution notes (two-tier trace gate; Gate-4-provisioning-vs-T-001-scaffold boundary) are reflected in the CI and checklist. No **new** blockers surfaced.

## 2. Repository Scaffold Specification (structure + Python layout + dependency strategy)

**Directory tree** (T-001 creates; empty packages with docstrings — no logic):
```
finsight/
├── pyproject.toml                 # deps + tooling config (§ below)
├── .importlinter                  # architecture-fitness contracts (§4)
├── .gitignore                     # exclude build/venv/secrets; NEVER commit real data
├── .python-version                # pinned interpreter
├── README.md                      # points to specs/ as source of truth
├── .claude/settings.json          # plugins pinned to a release tag
├── .github/workflows/ci.yml       # CI (§3)  [or platform equivalent]
├── src/finsight/
│   ├── __init__.py
│   ├── app.py                     # composition root (wiring skeleton only — no logic yet)
│   ├── domain/{__init__,ports,review_cycle,verified_dataset,findings,rules,money}/  # empty pkgs
│   ├── application/{__init__,orchestrator,pipeline,intake,extraction,verification,readiness,reporting,export}/
│   ├── infrastructure/{__init__,persistence,audit,readers,ai}/
│   └── delivery/{__init__,shell,ui}/
├── tests/
│   ├── unit/ golden/ determinism/ crossplatform/ fitness/ accessibility/ security/
│   └── data/synthetic/            # synthetic fixtures only (§7, §8)
└── specs/                         # baselined source of truth (already present)
```
**Package boundaries & dependency direction** (enforced by §4): `delivery → application → domain`; `infrastructure` implements `domain.ports`; `domain` imports nothing outward. `app.py` is the only place `FindingsCommandPort` is bound to `rules`/engine.

**Dependency management strategy** — `pyproject.toml` skeleton (versions pinned at T-001; offline-installable; no external-network deps; license-checked per NFR-079):
```toml
[project]
name = "finsight"
requires-python = "==<pin, e.g. 3.12.*>"
dependencies = [
  "<excel-reader, e.g. openpyxl==pin>",   # ExcelReader (F-01-05); stdlib sqlite3 + decimal need no dep
]
[project.optional-dependencies]
dev = [
  "pytest==<pin>", "import-linter==<pin>", "ruff==<pin>", "coverage==<pin>",
]
[tool.finsight]
# money precision/rounding confirmed at ADR-003 acceptance
```
Rules: runtime deps minimal (Excel reader + stdlib); a lock file pins exact versions; a dependency-audit step (license + known-vuln) runs in CI (NFR-079); no dependency may perform network egress (NFR-011).

## 3. CI Specification (`.github/workflows/ci.yml` — or platform equivalent)
Job names, order, matrix, artifacts, failure conditions, merge blockers:
```yaml
name: finsight-ci
on: { pull_request: { branches: [main] }, push: { branches: [main] } }
env: { PYTHONHASHSEED: "0" }          # ordering determinism (ADR-003)
jobs:
  fitness:                             # architecture-fitness — MERGE BLOCKER
    runs-on: ubuntu-latest
    steps: [checkout, setup-python(pinned), install-dev,
            "lint-imports",            # import-linter (§4) — fail on any contract violation
            "ruff check", "money-float-guard"]   # forbid float() on money paths (§6)
  test-matrix:                         # unit + golden + determinism on BOTH OS — MERGE BLOCKER
    strategy: { matrix: { os: [windows-latest, macos-latest] }, fail-fast: false }
    runs-on: ${{ matrix.os }}
    steps: [checkout, setup-python(pinned), install-dev,
            "pytest -m unit", "pytest -m golden", "pytest -m determinism",
            "upload-artifact golden-serialized-${{ matrix.os }}"]   # the serialized finding set
  crossplatform:                       # byte-identity across OS — MERGE BLOCKER (NFR-029)
    needs: test-matrix
    steps: [download both golden-serialized artifacts, "compare hashes → FAIL if differ"]
  accessibility-security:              # MERGE BLOCKER (DoD)
    steps: ["pytest -m accessibility", "pytest -m security"]   # keyboard path; no non-loopback listener; no secrets
  dev-data-hygiene:                    # MERGE BLOCKER (§8)
    steps: ["python tools/data_guard (§8 rules) → FAIL on any real-data-shaped fixture"]
  traceability:                        # TWO-TIER (§5)
    steps: ["/sdd:trace --fail-on-orphans",
            "per-merge: FAIL if any orphan OR any touched code unannotated",
            "on tag/release: FAIL unless matches ^TRACEABILITY: PASS$"]
# Branch protection (§9): main requires ALL jobs green on both OS + >=1 human review; no direct push; no force-push.
```
**Failure conditions:** any gate red blocks merge. **Artifacts:** per-OS serialized golden output (for the cross-platform compare); coverage; trace report.

## 4. Import-Linter Contract Specification (`.importlinter`)
```ini
[importlinter]
root_package = finsight

[[contracts]]
name = Layered dependency direction
type = layers
layers = finsight.delivery | finsight.application | finsight.domain

[[contracts]]
name = C-DOMAIN-INDEP: domain imports nothing outward
type = forbidden
source_modules = finsight.domain
forbidden_modules = finsight.application, finsight.infrastructure, finsight.delivery

[[contracts]]
name = C-DAL-ONLY-STORAGE
type = forbidden
source_modules = finsight.domain, finsight.application, finsight.delivery
forbidden_modules = sqlite3      # + the chosen driver; only infrastructure.persistence may import it

[[contracts]]
name = C-COMMAND-PORT-ISOLATION
type = forbidden
source_modules = finsight.delivery, finsight.infrastructure.ai
forbidden_modules = finsight.domain.ports.findings_command
```
For each contract — **purpose · allowed · forbidden · fail example · pass example:**
- **Layered:** purpose = enforce inward dependencies. Allowed: delivery→application→domain. Forbidden: domain→application/delivery. *Fail:* `domain/rules/engine.py` imports `delivery.ui`. *Pass:* `delivery/shell` imports `application.orchestrator`.
- **C-DOMAIN-INDEP:** purpose = headless, web-migratable core. Forbidden: any domain import of outer layers. *Fail:* `domain/findings` imports `infrastructure.persistence`. *Pass:* `domain/findings` imports only `domain.ports`.
- **C-DAL-ONLY-STORAGE:** purpose = storage substitutability (ADR-004). Allowed: only `infrastructure.persistence` imports `sqlite3`. *Fail:* `application/reporting` imports `sqlite3`. *Pass:* `application` uses a `Repository` port.
- **C-COMMAND-PORT-ISOLATION:** purpose = Trust > AI boundary (ADR-002/007). Forbidden: delivery/AI referencing `FindingsCommandPort`. *Fail:* `delivery/ui` imports `findings_command`. *Pass:* `delivery`/`ai` reference only `FindingsQueryPort`.
- **Runtime-guard tests (pytest `-m fitness`, not import-linter):** constructing a `VerifiedDataset` outside the C-06 factory **raises**; constructing a `Finding` outside `FindingsCommandPort` **raises**.

## 5. Traceability & Annotation Specification (aligns `/sdd:trace --fail-on-orphans`)
- **`Implements` (on implementing units):** a top-of-unit comment — `# Implements: FR-###, F-02-02` (rule code adds the rule ID, e.g. `# Implements: FR-033, F-02-02, R-BUD-02`).
- **`Verifies` (on tests):** `# Verifies: FR-###` / `# Verifies: NFR-###` at the top of each test.
- **Required format:** IDs zero-padded (FR-030, NFR-021), comma-separated, one annotation line per unit/test; the feature ID `F-02-02` present on every skeleton unit.
- **Examples:**
```python
# Implements: FR-006, F-02-02
# (module docstring — ReviewCycle aggregate; no logic shown here)

# Verifies: FR-026, NFR-047
def test_engine_rejects_unverified_input(): ...
```
- **Expected outputs:** `/sdd:trace` enumerates all 122 FR / 80 NFR and resolves requirement→feature→plan; as tasks land, code/test columns fill for the skeleton's FRs.
- **Two-tier gate:** per-merge = **no orphans** + every touched unit/test annotated; feature-completion (T-023) + release = full `^TRACEABILITY: PASS$` (every Must in scope verified).
- **Orphan definitions:** *code→nothing* (`Implements:`/`Verifies:` citing a non-baselined/typo ID); *spec→nothing* (a baselined FR with no feature — none expected). Baselined-but-not-yet-implemented FRs are **planned, not orphaned**.

## 6. Determinism Specification (ADR-003)
- **Decimal:** one shared pinned `decimal.Context` in `domain/money` (precision `<pin at ADR-003 acceptance>`, rounding `ROUND_HALF_UP`); **all monetary values are `Decimal`**; **`float(` forbidden** on `domain/money`, `domain/rules`, `application` (a CI `money-float-guard` grep/AST check fails the build on violation); amounts persisted/loaded as **integer minor units** (never SQLite `REAL`).
- **Clock injection:** a `Clock` port is injected into services needing time; **`datetime.now()`/wall-clock reads are forbidden in `domain`** (fitness/lint check); audit timestamps are stamped at the infrastructure edge.
- **Date handling:** the `ExcelReader` **pins the workbook date system (1900 vs 1904)** and parses with explicit formats; no locale-dependent date parsing.
- **Encoding:** UTF-8 end-to-end; explicit `encoding="utf-8"` on all file IO.
- **Ordering:** every ranked/sorted output uses an **explicit tie-broken key**; `PYTHONHASHSEED=0` set in CI; no reliance on set/dict-iteration order in serialized outputs.
- **Cross-platform consistency:** the serialized finding set is compared **byte-for-byte** across the Windows and macOS CI jobs (§3 `crossplatform`).

## 7. Golden Dataset Specification (executable spec — synthetic only; no files created)
A fixture-spec a T-001 builder converts to two `.xlsx` files under `tests/data/synthetic/` (all data fictional; `SYNTHETIC` marker required):
```yaml
ged_synthetic:                     # sheet "GED"
  preamble_rows: 3                 # title/preamble block (FR-013)
  header_row: 4
  columns: [dept_no, dept_name, account_no, account_name, fiscal_period,
            journal_no, journal_date, invoice_amount, check_no, invoice_date,
            vendor, agency, journal_desc, line_desc, amount]
  rows:
    - {account_no: "6100", vendor: "Acme-Synth",  amount: "8000.00", fiscal_period: "2026-05"}
    - {account_no: "6100", vendor: "Acme-Synth",  amount: "5000.00", fiscal_period: "2026-05"}
    - {account_no: "6200", vendor: "Globex-Synth", amount: "4000.00", fiscal_period: "2026-05"}
    - {row_type: subtotal, text: "TOTAL FOR ACCOUNT 6100", amount: "13000.00"}   # subtotal (FR-013)
    - {row_type: blank}                                                          # blank row
    - {account_no: "6200", vendor: "Globex-Synth", amount: "-200.00"}            # credit/negative
    - {account_no: "6200", vendor: "Globex-Synth", amount: "."}                  # placeholder
budget_synthetic:                  # workbook sheets: Details, Actuals, "Original Budget"
  original_budget:
    - {account_no: "6100", budget: "10000.00", atd: "13000.00", etc: "0.00", eac: "13000.00", delta: "3000.00"}
    - {account_no: "6200", budget: "5000.00",  atd: "3800.00",  etc: "0.00", eac: "3800.00",  delta: "-1200.00"}
  details: [ {account_no: "6100", vendor: "Acme-Synth", invoice_no: "SYN-001", status: "open"} ]   # minimal
  actuals: [ {account_no: "6100", cleared: false} ]                                                 # minimal
expected_finding:
  count: 1
  rule: R-BUD-02
  account_no: "6100"
  type: "over-budget"
  planned: "10000.00"   # = budget
  actual: "13000.00"    # = actuals-to-date  (per 05 R-BUD-01 "prefer workbook figures")
  variance_amount: "3000.00"
  variance_pct: "30"
  severity: "<per synthetic bands in ConfigVersion>"
  source_refs: "cell references to GED + Original Budget rows"
  # account 6200 is within the synthetic materiality default → NO finding
acceptance_criteria:
  - exactly_one_finding: true
  - finding_matches: expected_finding
  - evidence_traces_to_source: true
determinism_assertions:
  - repeat_run_identical: true            # NFR-021
  - windows_equals_macos: true            # NFR-029
  - no_duplicate_on_rerun: true           # NFR-008
```

## 8. Dev-Data-Hygiene Specification (NFR-018)
- **Rules:** only synthetic/sanitized data in the repo; all fixtures under `tests/data/synthetic/`; every fixture carries a `SYNTHETIC` marker (filename suffix `.synthetic.xlsx` and/or an internal marker sheet/cell); no real vendor/account names, real amounts, or production file-name conventions.
- **Checks (`tools/data_guard`, run in CI + pre-commit):** (a) FAIL if any `.xlsx`/`.csv` exists outside `tests/data/synthetic/`; (b) FAIL if a fixture lacks the `SYNTHETIC` marker; (c) FAIL on matches to a real-data denylist/pattern set (real entity names, production export naming); (d) FAIL on committing files matching the customer's real export pattern.
- **Validation (a T-001 acceptance test):** a planted real-data-shaped fixture **must be rejected** by the guard.

## 9. Developer Standards Package
- **Test folder conventions:** `tests/{unit,golden,determinism,crossplatform,fitness,accessibility,security}/`; files `test_*.py`; pytest markers matching the folder (`-m unit`, `-m golden`, …); every test carries a `# Verifies:` annotation; synthetic data only under `tests/data/synthetic/`.
- **Commit conventions:** `<type>(<scope>): <summary>  [F-02-02 | BUG-### | ADR-###]`, type ∈ {feat, fix, refactor, test, docs, chore, spec}; the work-item ID is mandatory; **test-first** (failing test then implementation visible in the diff/sequence); `spec` commit precedes `feat` when behavior changes; `Assisted-by: <tool>` trailer when AI materially generated the change (human remains the accountable committer).
- **Branch protection conventions:** trunk-based; short-lived branches `feat/F-02-02-…`, `fix/…`, `chore/…`; `main` requires **all CI gates green on both OS + ≥1 human review**; no direct pushes; no force-push to shared branches; writes under `specs/baselines/` remain hook-blocked.

## 10. T-001 Implementation Checklist
- [ ] Repo scaffold created per §2 (empty packages + docstrings; no logic).
- [ ] `pyproject.toml` + lock with pinned versions; offline-installable; dependency audit passing.
- [ ] `.importlinter` contracts (§4) present and **passing** on the scaffold.
- [ ] Runtime-guard fitness tests (VerifiedDataset/Finding construction raises) present.
- [ ] CI workflow (§3) live; **green on a trivial change on Windows AND macOS**.
- [ ] `crossplatform` job compares serialized golden output byte-for-byte.
- [ ] Traceability gate wired (per-merge no-orphans); annotation conventions (§5) documented in README/CONTRIBUTING.
- [ ] Determinism controls (§6) in place (pinned Decimal context; money-float-guard; injected Clock; UTF-8; pinned Excel date system; `PYTHONHASHSEED=0`).
- [ ] Golden fixture built from §7 spec (synthetic) under `tests/data/synthetic/`; a trivial golden/determinism check passes.
- [ ] `tools/data_guard` (§8) active; rejects a planted real-data fixture.
- [ ] Developer standards (§9) documented; branch protection configured.
- [ ] `# Implements:`/`# Verifies:` annotations on T-001's own units/tests; `/sdd:trace` runs clean (no orphans); commit `[F-02-02]`; T-001 checkbox ticked.

## 11. Implementation-Blocker Findings (filtered)
**No new blockers.** The only outstanding execution notes are the two already recorded in GATE-4-IMPLEMENTATION-PACKAGE §11 — (B-1) two-tier trace gate; (B-2) Gate-4-provisioning-vs-T-001-scaffold boundary — both reflected in §3 and §10 above. Remaining prerequisites are the human Gate 1–3 acts and Gate-4 provisioning (repo/runners/certs). With those done, **T-001 is executable directly from this asset specification.**

## 12. Dependency governance (pins, drift detection, validation)
Version pinning is intentional and lives entirely in the build/release path — no version-management or self-update capability enters the product (Constitution §6; DEC-034). Authoritative artifacts:

| Artifact | Role |
|---|---|
| `build/versions.json` | Single source of truth: per-dependency `required_min` (CI hard floor), `pinned` (exact), `latest_stable` (drift reference), verified `as_of` date. |
| `requirements.txt` / `requirements-dev.txt` | Exact (`==`) pip pins; mirror `versions.json`. |
| `pyproject.toml` | `requires-python = ">=3.10"`; dev extras pinned to match. |
| `build/validate_deps.py` | Build-time validator: FAILs only on missing/below-minimum; WARNs on drift. Network-free, read-only. |
| `.github/workflows/dependency-validation.yml` | CI stage over `{ubuntu, windows, macos} × {3.10, 3.11, 3.12}`; blocking min-check + non-blocking outdated report + pin-drift check. |
| `DEPENDENCIES.md` | Human-readable status report + upgrade/review workflow. |

Verified latest-stable (2026-07-17): Python 3.14.6 (recommend build target 3.12; **3.9 is EOL and below the toolchain floor**), SQLite 3.53.3 (bundled), openpyxl 3.1.5, pytest 9.1.1, import-linter 2.13, ruff 0.15.22, coverage 7.15.2. The T-001 checklist item "`pyproject.toml` + lock with pinned versions … dependency audit passing" is satisfied by these artifacts; the audit **passes only once the environment is provisioned at Python ≥3.10 with the pinned toolchain installed** (see the current-environment gap in DEPENDENCIES.md §1–§2).
