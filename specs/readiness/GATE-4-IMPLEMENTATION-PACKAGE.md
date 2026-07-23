# Gate 4 Implementation Package (environment · CI · fitness · golden · determinism · T-001)

> **Environment readiness is authorized under the project-owner-approved baseline.** This package is the design/config specification for Gate-4 execution. Standing up the repo/CI/runners/certs remains human/ops work; CI results and live-infrastructure evidence are not fabricated here.

## 1. Gate 4 Readiness Summary
All eight Gate-4 packages are designed and implementation-ready to instantiate the moment Gates 1–3 complete (baseline v1.0; ADR-001–007 Accepted incl. the shell decision; PLAN-F-02-02 Approved). The core stack is **Python** (ADR-001, directional/recommended); the shell (Tauri/Electron) affects only the **delivery** layer, so every package below is shell-agnostic except where noted. **Two execution-clarifications must be acknowledged (see §11 filter)** — the CI traceability gate must be **two-tier** (per-merge = no-orphans; full `TRACEABILITY: PASS` = feature-completion/release), and the **Gate-4-vs-T-001 boundary** must be read as *Gate 4 = human/ops provisioning; T-001 = the scaffold task that produces the green environment*. Neither is new scope; both are sequencing disambiguations.

## 2. Repository Package (per ADR-002)
Dependencies point inward: **delivery → application → domain**; **infrastructure implements domain ports** (domain imports nothing outward). A composition root wires implementations to ports.

```
finsight/
├── pyproject.toml                    # build + pinned deps (no external fonts/services)
├── .claude/settings.json             # plugins pinned to a release tag
├── ci/                               # CI pipeline config (§3)
├── .importlinter                     # architecture-fitness contracts (§5)
├── src/finsight/
│   ├── domain/                       # DETERMINISTIC CORE — pure; imports no UI/storage/AI/framework
│   │   ├── ports/                    #   interfaces only: FindingsQueryPort, FindingsCommandPort,
│   │   │                             #   AuditEventPort, Repository*, DocumentReader, AIProviderPort
│   │   ├── review_cycle/             #   ReviewCycle aggregate + two-region state model (ADR-006)
│   │   ├── verified_dataset/         #   VerifiedDataset (frozen; module-private factory; guard) (ADR-006)
│   │   ├── findings/                 #   Finding contract, severity (R-FND-02), lifecycle (ADR-007)
│   │   ├── rules/                    #   engine + R-BUD-01, R-BUD-02, R-FND-02 (ADR-003)
│   │   └── money/                    #   Decimal context + minor-units helpers (ADR-003)
│   ├── application/                  # use-cases / orchestration (no business truth)
│   │   ├── orchestrator/             #   fixed deterministic step sequencer (C-02)
│   │   ├── pipeline/                 #   extraction pipeline: read→normalize→validate→lineage (F-01-05)
│   │   ├── intake/ extraction/ verification/ readiness/ reporting/ export/
│   ├── infrastructure/               # implements ports; ONLY layer touching storage/format/AI
│   │   ├── persistence/              #   SQLite DAL + repositories (ADR-004)
│   │   ├── audit/                    #   AuditEventPort implementation (ADR-005)
│   │   ├── readers/                  #   ExcelReader (F-01-05; infra)
│   │   └── ai/                       #   provider adapter STUB (deferred — ADC-03; excluded from skeleton)
│   ├── delivery/                     # replaceable shell (Tauri/Electron) + minimal UI
│   │   ├── shell/                    #   loopback bridge to the headless core
│   │   └── ui/                       #   minimal 9-step wizard (web tech)
│   └── app.py                        # composition root — wires impls to ports; the ONLY place
│                                     # FindingsCommandPort is injected into rules/engine (never delivery/ai)
├── tests/
│   ├── unit/ golden/ determinism/ crossplatform/ fitness/ accessibility/ security/
│   └── data/synthetic/               # golden datasets (§6) — synthetic only
└── specs/                            # the baselined source of truth (already present)
```
**Module ownership:** domain = deterministic truth (rules/findings/cycle/money); application = use-cases + the F-01-05 pipeline + orchestrator; infrastructure = DAL/audit/readers/AI-adapter; delivery = shell + UI. **Not implementation code — structure only.**

## 3. CI Package
**Matrix:** `windows-latest` and `macos-latest`, pinned Python. **Stages (ordered; each a merge-blocking gate unless noted):**
1. **Setup** — checkout, pinned Python, install, pin plugins.
2. **Lint/format + architecture-fitness (import-linter)** — §5 — **blocks**.
3. **Unit tests** (`pytest`) — **blocks**.
4. **Golden-dataset test** — §6 — **blocks**.
5. **Determinism test** — repeat-run identical + serialized-finding byte-identity — **blocks**.
6. **Cross-platform gate** — the Windows and macOS jobs must produce **identical** serialized golden output (compare artifact hashes across OS) — **blocks** (NFR-029).
7. **Accessibility smoke + security checks** (no non-loopback listener; no secrets in logs; §7) — **blocks** (DoD).
8. **Traceability gate** — **two-tier (see §4/§11):** per-merge = `/sdd:trace --fail-on-orphans` shows **no orphans + all touched code annotated**; **feature-completion/release** = full `^TRACEABILITY: PASS$`.
9. **Dev-data-hygiene guard** — §7 — **blocks**.
**Branch protection:** `main` requires all gates green on **both** OS + ≥1 human review; no direct pushes; baselines untouched (hook).
*(Illustrative shape only — instantiate the pipeline at Gate-4 execution once the repo/runners exist.)*

## 4. Traceability Package
- **Annotation strategy:** implementing units carry `Implements: FR-###, F-02-02` (+ `R-BUD-02` on rule code); tests carry `Verifies: FR-###/NFR-###`. Commits prefix `[F-02-02]`.
- **`Implements` strategy:** every unit that realizes a requirement names its baselined FR/feature IDs; the composition root and infra adapters annotate the ADR they realize where useful.
- **`Verifies` strategy:** every acceptance criterion (AC-1…16) maps to at least one test naming its FR/NFR.
- **Expected trace outputs:** pre-code, `/sdd:trace` enumerates all 122 FR / 80 NFR (now parseable) and resolves requirement→feature→plan; code/test columns are empty. As T-001…T-023 land, code/test columns fill for the skeleton's FRs; **full `TRACEABILITY: PASS` is reached at T-023 (verify)**.
- **Orphan-detection strategy:** *spec→nothing* (a baselined FR with no feature) and *code→nothing* (`Implements:`/`Verifies:` citing a non-existent/non-baselined ID). The per-merge gate fails on **orphans**, not on baselined-but-not-yet-implemented scope (those have feature links and are "planned," not orphaned).
- **Alignment:** `/sdd:trace --fail-on-orphans` per merge; full PASS at feature completion + release (NFR-048).

## 5. Architecture-Fitness Package (tests defined; ADR-002/006/007)
Implemented as **import-linter contracts** + a few **runtime-guard tests**. Pass = import-linter exits 0 and guard tests behave as specified.
- **C-DOMAIN-INDEP:** `finsight.domain` must import **no** `finsight.delivery`, `finsight.infrastructure`, `finsight.application`, and no UI/storage/AI/framework libraries. *Pass:* zero violations.
- **C-DAL-ONLY-STORAGE:** only `finsight.infrastructure.persistence` may import the SQLite/db library. *Pass:* no other module imports it.
- **C-DOMAIN-NO-AI / NO-UI / NO-STORAGE:** domain imports no AI-provider, no shell/UI, no DB types. *Pass:* zero violations.
- **C-COMMAND-PORT-ISOLATION:** `finsight.delivery.*` and `finsight.infrastructure.ai.*` must **not** reference `FindingsCommandPort`; only `finsight.domain.rules`/engine (wired at `app.py`) may. *Pass:* zero references outside the allowed set.
- **C-VERIFIEDDATASET-BOUNDARY:** the rules engine entrypoint accepts **only** a `VerifiedDataset`; constructing a `VerifiedDataset` outside the C-06 factory **raises** (guard test). *Pass:* engine has no other input; guard raises on illicit construction.
- **C-FINDINGS-BOUNDARY:** a `Finding` can be created **only** via `FindingsCommandPort` (frozen, no public constructor); illicit construction **raises** (guard test); AI/delivery hold only `FindingsQueryPort`. *Pass:* guard raises; query-only for AI/delivery.

## 6. Golden Dataset Package (synthetic only; per PLAN §Implementation Assumptions)
Two synthetic Excel fixtures (fictional entities, fabricated amounts — clearly synthetic, marked `SYNTHETIC`), designed to yield **exactly one** deterministic finding:
- **Synthetic GED** — one sheet with the FR-011 columns (dept #/name, account #/name, fiscal period, journal #/date, invoice amount, check #, invoice date, vendor, agency, descriptions, amount), plus quirks (title/preamble block; a `TOTAL FOR ACCOUNT` subtotal row per group; a blank row; a merged/repeated header; one credit/negative amount; one `.` placeholder). Fictional data, e.g., dept 9000 "Demo Dept"; accounts 6100/6200; vendors "Acme-Synth", "Globex-Synth".
- **Synthetic Budget Tracker** — three sheets (FR-012). *Original Budget* per account: budget, actuals-to-date, estimate-to-complete, estimate-at-completion, delta, notes. *Details* + *Actuals* minimal. Figures set so **account 6100 breaches** the synthetic materiality default (e.g., planned=budget 10,000; actual=actuals-to-date 13,000 → +30% variance > synthetic materiality) while 6200 stays within.
- **Known variance:** account 6100 over-budget by the fabricated margin above the synthetic threshold.
- **Expected finding:** exactly one `Budget over-spend` finding on account 6100, with the computed variance evidence and the severity R-FND-02 assigns under the synthetic bands; account 6200 produces none.
- **Determinism assertions:** repeated runs → byte-identical serialized finding; Windows and macOS → identical; no duplicate on re-run.
*(All values fictional; the real-file structural validation is the documented pre-pilot condition — PLAN §Implementation Assumptions.)*

## 7. Dev-Data-Hygiene Package (NFR-018)
- **Rules:** development/test data is **synthetic/sanitized only**; no real vendor/account names, real amounts, or real customer identifiers may enter the repo; all fixtures live under `tests/data/synthetic/` and carry a `SYNTHETIC` marker.
- **Checks (CI + pre-commit):** (a) reject any data file (`.xlsx`, `.csv`) outside `tests/data/synthetic/`; (b) reject any fixture lacking the `SYNTHETIC` header/marker; (c) a denylist/pattern scan for real-data markers (e.g., real entity-name patterns, production file-name conventions); (d) block committing files matching the customer's real export naming.
- **Validations:** CI **fails** if any check trips; a planted real-data-shaped fixture must be rejected (this is a T-001 acceptance test).

## 8. Determinism Package (implementation-ready controls; ADR-003)
- **Decimal:** a single pinned `decimal.Context` (defined precision + `ROUND_HALF_UP`) established centrally in `domain/money`; **`float` forbidden** on any money path (lint denylist for `float(` in `domain/rules`, `domain/money`, `application`); amounts stored/loaded as **integer minor units** (never SQLite `REAL`).
- **Locale:** no locale-dependent parsing/formatting; explicit date/number formats; formatting is presentation-only, never a computation input.
- **Encoding:** UTF-8 end-to-end; explicit `encoding=` on all file IO.
- **Time:** a `Clock` is injected; `datetime.now()`/wall-clock reads **forbidden in `domain`** (fitness/lint check); audit timestamps stamped at the edge.
- **Date:** the `ExcelReader` **pins the workbook date system (1900 vs 1904)** and parses with explicit formats.
- **Ordering:** explicit tie-broken sort keys on any ranked output; `PYTHONHASHSEED=0` in CI; no reliance on set/dict-iteration order in outputs.
- **Cross-platform:** the both-OS CI job compares the serialized finding set byte-for-byte (§3 stage 6).

## 9. T-001 Execution Package
*(T-001 = "Repository & environment scaffold" — the first spec-traced task; it **produces** the green environment.)*
- **Prerequisites to START T-001:** Gates 1–3 complete (baseline v1.0; ADR-001–007 Accepted incl. shell decision; PLAN Approved) **and** Gate-4 **provisioning** done (repo created, both-OS runners available, plugins pinned, code-signing certs if needed). *(Provisioning ≠ scaffold — see §11.)*
- **Outputs (T-001 delivers):** the §2 package structure; the §3 CI pipeline; the §5 import-linter contracts; the `pytest` harness; the §6 golden-dataset framework + ≥1 golden dataset; the §7 dev-data guard; the §8 determinism config; the trace gate wired (§4).
- **Evidence:** both-OS CI **green on a trivial change** (logs); import-linter runs green on the scaffolded packages; `/sdd:trace` executes and emits a verdict (no orphans on the trivial state); golden dataset present + a passing trivial determinism check; the dev-data guard **rejects a planted real-data-shaped fixture**.
- **Tests (T-001-level):** a trivial "core boots headless" unit test passing on both OS; the fitness contracts passing on the (skeleton-empty) structure; the guard rejection test.
- **Completion criteria:** all outputs present; CI green on both OS; trace gate operational (per-merge no-orphans mode); `Implements:`/`Verifies:` annotation conventions in place; T-001 checkbox ticked; commit `[F-02-02]`. *(This satisfies the AUTHORIZATION-T-001 G4a/b/c rows — which are T-001 outputs, verified at T-001 completion.)*

## 10. Gate 4 Completion Checklist
- [ ] Gates 1–3 complete (baseline, ADRs Accepted + shell decided, plan Approved).
- [ ] Repo created; plugins pinned; both-OS runners available; certs provisioned (human/ops).
- [ ] `T-001` executed → §2 structure, §3 CI, §5 fitness, §6 golden, §7 guard, §8 determinism, §4 trace gate all in place.
- [ ] Both-OS CI green on a trivial change (logs captured).
- [ ] Architecture-fitness contracts pass on the scaffold.
- [ ] Trace gate operational (per-merge no-orphans); full PASS reserved for T-023/release.
- [ ] Golden dataset present (synthetic); dev-data guard active (rejects a planted real-data fixture).
- [ ] Determinism config in force (pinned Decimal context; injected clock; UTF-8; pinned Excel date system; PYTHONHASHSEED).
- [ ] Human confirms environment readiness.

## 11. Implementation-Blocker Findings (filtered)
Two execution-clarifications that would otherwise block CI/T-001 (neither is new scope, architecture, or requirements):
- **B-1 — CI traceability gate must be two-tier.** Full `TRACEABILITY: PASS` requires every Must FR/NFR to have a verified chain — which cannot hold mid-skeleton (most FRs are baselined-but-not-yet-implemented). **Per-merge gate = `--fail-on-orphans` (no orphans; all touched code annotated); full `TRACEABILITY: PASS` = the T-023 feature-completion + release gate.** Without this split, CI blocks every development merge.
- **B-2 — Gate-4-vs-T-001 boundary.** `AUTHORIZATION-T-001` lists green CI / trace / golden as authorization prerequisites, but `TASKS-F-02-02` T-001 *produces* exactly those. **Read as: authorization to START T-001 needs Gate-4 *provisioning* (repo/runners/plugins/certs) + Gates 1–3; the green-CI/trace/golden rows are T-001 *outputs* verified at T-001 completion.** Without this reading, authorization deadlocks.
