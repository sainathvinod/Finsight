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

## Verification performed (at R1 completion)

These are point-in-time results recorded when this document was written; re-run the suite to reconfirm.

- Full automated suite green (700+ tests) incl. an end-to-end UI walkthrough and packaging smoke tests
  (`pytest -q` with `QT_QPA_PLATFORM=offscreen`).
- Clean-environment install: a fresh venv, `pip install` of the wheel + PySide6, launched `finsight`
  from a neutral directory — created its DB (migrations to v3) and exited cleanly.
- Both `dist/finsight.pyz` and the installed `finsight` launcher started headless and exited 0.
- Second-instance refusal, restart/recovery, abandon/resume, and `provider=none` all verified.

## Native macOS app (FinSight.app + DMG)

A reproducible native-packaging recipe is provided (target-product §23; ADR-001 §3 / ADR-008 §3):

| Artifact | Purpose |
|---|---|
| `packaging/finsight.spec` | PyInstaller spec — windowed `--onedir` `FinSight.app`; bundles the Qt runtime + cocoa plugin and all `finsight` submodules (lazy service imports). |
| `packaging/finsight_launch.py` | Frozen entry → `finsight.delivery.desktop.app:main`. |
| `scripts/build_macos_app.sh` | Builds `dist/FinSight.app`, then an `hdiutil` UDZO `dist/FinSight.dmg` with an `/Applications` symlink. |
| `scripts/verify_macos_app.py` | Headless verification (below). |

Build on macOS with the project venv:

```bash
PYTHON=.venv/bin/python bash scripts/build_macos_app.sh
```

**Headless-verifiable** (via `scripts/verify_macos_app.py`): the bundle structure
(`Contents/MacOS/FinSight`, `Info.plist`, the bundled `libqcocoa` plugin); a
`QT_QPA_PLATFORM=offscreen FINSIGHT_SMOKE=1` launch of the **frozen binary** that exits 0 (migrations
run, services compose, the window renders one event cycle); and that the DMG mounts and contains
`FinSight.app`.

**NOT verifiable in a headless environment (RED CARD DoD-A — honest limitation):** a real Finder
**double-click** on a physical/Retina display, on-screen pixel rendering, and Gatekeeper/notarization
(Developer ID signing) acceptance. Those require a GUI session and a separate signing step, so packaging
is **not declared complete** here — the recipe + headless checks are in place; the display-bound
double-click launch and notarization are the remaining environment/owner step.

## Not included in R1 (deferred / R2)

Second-generation re-verification, manual promotion, export supersession, historical import, advanced
AI, and the Review Health Score are R2 and intentionally absent.
