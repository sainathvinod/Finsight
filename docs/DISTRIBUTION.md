# FinSight R1 — Distribution & Launch

FinSight Release 1 is a single-user, local **desktop** application (macOS/Linux/Windows) — the
deterministic "Monthly Review in a Box" workflow. It runs on Python 3.10+ with PySide6; the
deterministic core needs only `openpyxl` (no AI / no network).

## Artifacts (built into `dist/`)

Build outputs are git-ignored and reproducible with the commands below.

| Artifact | What it is | Launch |
|----------|------------|--------|
| `dist/finsight-1.0.0-py3-none-any.whl` | pip-installable wheel; creates a `finsight` launcher | `pip install "finsight-1.0.0-py3-none-any.whl[desktop]"` then `finsight` |
| `dist/finsight.pyz` | self-contained runnable zipapp (bundles the FinSight code) | `python dist/finsight.pyz` (needs PySide6 + openpyxl available) |

## Launch commands (in order of preference)

```bash
# 1. Installed wheel  →  a first-class `finsight` command
python -m pip install "dist/finsight-1.0.0-py3-none-any.whl[desktop]"
finsight

# 2. Zipapp           →  no install step
python dist/finsight.pyz

# 3. From source      →  developers
pip install -e ".[desktop]" && finsight        # or:  python -m finsight
```

## Build commands

```bash
# wheel (setuptools backend)
python -m build --wheel                          # -> dist/finsight-1.0.0-py3-none-any.whl

# zipapp (stdlib, no build backend needed)
rm -rf build/zipapp && cp -R src/finsight build/zipapp/finsight
python -m zipapp build/zipapp -o dist/finsight.pyz -p "/usr/bin/env python3" \
        -m "finsight.delivery.desktop.app:main"
```

## Runtime behavior

- **Data location:** a per-user application-support directory (never the current working directory).
  Override with `FINSIGHT_DB=/path/to/finsight.db`.
- **Single instance:** an advisory lock (`<db>.lock`) refuses a second instance on the same database
  without opening it; it auto-recovers from a crashed instance's stale lock (ADR-013 §3).
- **Optional AI (Ask Fin):** the deterministic review works with **no** provider. Set
  `FINSIGHT_AI_PROVIDER=ollama` (and `FINSIGHT_AI_DEMO_AUTHORIZED=1` for the demo consent gate) to
  enable it; otherwise Ask Fin shows an honest "AI unavailable" state and never blocks the workflow.
- **Headless smoke:** `FINSIGHT_SMOKE=1` launches, renders one event cycle, and exits 0 — used by the
  packaging tests to verify a clean start without a display.

## Verification performed

- Full automated suite green (707 tests) incl. an end-to-end UI walkthrough and packaging smoke tests.
- Clean-environment install: a fresh venv, `pip install` of the wheel + PySide6, launched `finsight`
  from a neutral directory — created its DB (migrations to v3) and exited cleanly.
- Second-instance refusal, restart/recovery, abandon/resume, and `provider=none` all verified.

## Not included in R1 (deferred / R2)

Native OS installers (`.app`/`.dmg`/MSI) via PyInstaller/Nuitka were **not** built — packaging is the
pip wheel + zipapp above. Second-generation re-verification, manual promotion, export supersession,
historical import, advanced AI, and the Review Health Score are R2 and intentionally absent.
