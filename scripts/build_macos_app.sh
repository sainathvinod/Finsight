#!/usr/bin/env bash
# Build the native FinSight.app + FinSight.dmg (target-product §23; ADR-008 §3).
#   Reproducible recipe: PyInstaller windowed --onedir bundle, then an hdiutil DMG with an /Applications
#   symlink for drag-to-install. Run on macOS with the project venv active.
#
#   Headless-verifiable afterwards (scripts/verify_macos_app.py): bundle structure + a
#   QT_QPA_PLATFORM=offscreen FINSIGHT_SMOKE=1 launch that exits 0 + the DMG mounts.
#   NOT verifiable headless (RED CARD DoD-A): a real Finder double-click on a display, and
#   Gatekeeper/notarization — those require a GUI session and are a separate signing step.
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python}"
echo "==> Installing PyInstaller (if needed)"
"$PY" -m pip install --quiet --upgrade pyinstaller

echo "==> Building FinSight.app"
rm -rf build/pyinstaller dist/FinSight dist/FinSight.app dist/FinSight.dmg
"$PY" -m PyInstaller --clean --noconfirm \
    --distpath dist --workpath build/pyinstaller \
    packaging/finsight.spec

test -d dist/FinSight.app || { echo "ERROR: FinSight.app was not produced"; exit 1; }
echo "==> Built dist/FinSight.app"

echo "==> Staging + building DMG"
STAGE="build/dmg-stage"
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -R dist/FinSight.app "$STAGE/FinSight.app"
ln -sf /Applications "$STAGE/Applications"
hdiutil create -volname "FinSight" -srcfolder "$STAGE" -ov -format UDZO dist/FinSight.dmg
echo "==> Built dist/FinSight.dmg"

echo "==> Verifying (headless)"
"$PY" scripts/verify_macos_app.py
echo "Done. Artifacts: dist/FinSight.app  dist/FinSight.dmg"
