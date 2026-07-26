#!/usr/bin/env python
"""Headless verification of the built FinSight.app (target-product §23/§24; ADR-008).

Verifies exactly what a no-display environment CAN prove:
  1. Bundle structure: Contents/MacOS/FinSight, Contents/Info.plist, and a bundled Qt cocoa plugin.
  2. The frozen binary launches headless (QT_QPA_PLATFORM=offscreen FINSIGHT_SMOKE=1) and exits 0 —
     proving migrations run, services compose, and the window renders one event cycle.
  3. If dist/FinSight.dmg exists, that it mounts (hdiutil attach) and contains FinSight.app.

It CANNOT verify (RED CARD DoD-A, stated honestly): a real Finder double-click on a physical/Retina
display, on-screen pixels, or Gatekeeper/notarization acceptance — those require a GUI session.

Exit codes: 0 = all available checks passed; 2 = app not built yet; 1 = a check failed.
"""
from __future__ import annotations
import os
import plistlib
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(REPO, "dist", "FinSight.app")
DMG = os.path.join(REPO, "dist", "FinSight.dmg")


def _fail(msg):
    print("FAIL:", msg)
    sys.exit(1)


def main() -> int:
    if not os.path.isdir(APP):
        print("SKIP: dist/FinSight.app not built yet — run scripts/build_macos_app.sh on macOS.")
        return 2

    macos_bin = os.path.join(APP, "Contents", "MacOS", "FinSight")
    info = os.path.join(APP, "Contents", "Info.plist")
    if not os.path.isfile(macos_bin):
        _fail("missing Contents/MacOS/FinSight")
    if not os.path.isfile(info):
        _fail("missing Contents/Info.plist")
    with open(info, "rb") as fh:
        plist = plistlib.load(fh)
    if plist.get("CFBundleName") != "FinSight":
        _fail("Info.plist CFBundleName is not FinSight")

    # The cocoa platform plugin must be bundled or the app cannot create a window on macOS.
    cocoa = []
    for dp, _dirs, files in os.walk(os.path.join(APP, "Contents")):
        for f in files:
            if f in ("libqcocoa.dylib", "libqcocoa.so"):
                cocoa.append(os.path.join(dp, f))
    if not cocoa:
        _fail("no bundled Qt cocoa platform plugin (libqcocoa) — GUI would not start")
    print("OK: bundle structure (MacOS binary, Info.plist, cocoa plugin present)")

    # Frozen binary launches headless and exits 0.
    env = dict(os.environ, FINSIGHT_SMOKE="1", QT_QPA_PLATFORM="offscreen",
               FINSIGHT_DB=os.path.join(tempfile.mkdtemp(), "finsight.db"))
    r = subprocess.run([macos_bin], env=env, cwd=tempfile.gettempdir(),
                       capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        _fail("frozen binary smoke launch exited %d:\n%s" % (r.returncode, r.stderr[-2000:]))
    print("OK: frozen binary smoke launch exited 0 (migrations + services + window composed)")

    if os.path.isfile(DMG):
        out = subprocess.run(["hdiutil", "attach", "-nobrowse", "-readonly", DMG],
                             capture_output=True, text=True, timeout=120)
        if out.returncode != 0:
            _fail("DMG did not mount:\n" + out.stderr)
        mount = None
        for line in out.stdout.splitlines():
            if "/Volumes/" in line:
                mount = line.split("\t")[-1].strip()
        try:
            if not mount or not os.path.isdir(os.path.join(mount, "FinSight.app")):
                _fail("DMG does not contain FinSight.app")
            print("OK: DMG mounts and contains FinSight.app")
        finally:
            if mount:
                subprocess.run(["hdiutil", "detach", mount], capture_output=True)
    else:
        print("NOTE: dist/FinSight.dmg not present — DMG check skipped.")

    print("\nHeadless verification PASSED. NOT verified here (needs a display): Finder double-click, "
          "on-screen rendering, Gatekeeper/notarization.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
