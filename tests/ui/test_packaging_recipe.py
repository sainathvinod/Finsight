# Verifies: the native macOS packaging RECIPE exists and is coherent (target-product §23).
#   The reproducible artifacts — PyInstaller spec, launcher, build script, headless verifier — are the
#   reviewable deliverable. Building the actual .app + a real Finder double-click is an environment-bound
#   step (RED CARD DoD-A) performed on macOS with a display, not in this headless suite.
import os
import subprocess
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _p(*parts):
    return os.path.join(_REPO, *parts)


def test_packaging_recipe_files_exist():
    for rel in (("packaging", "finsight.spec"), ("packaging", "finsight_launch.py"),
                ("scripts", "build_macos_app.sh"), ("scripts", "verify_macos_app.py")):
        assert os.path.isfile(_p(*rel)), rel


def test_launcher_targets_the_desktop_main():
    txt = open(_p("packaging", "finsight_launch.py"), encoding="utf-8").read()
    assert "from finsight.delivery.desktop.app import main" in txt


def test_spec_bundles_qt_and_all_finsight_submodules():
    spec = open(_p("packaging", "finsight.spec"), encoding="utf-8").read()
    assert 'collect_submodules("finsight")' in spec       # lazy service imports are bundled
    assert 'name="FinSight.app"' in spec                   # a macOS .app bundle
    assert "console=False" in spec                         # windowed (no terminal)


def test_verifier_skips_cleanly_when_app_not_built():
    # Honest: when the .app has not been built, verification reports SKIP (exit 2), never a false pass.
    r = subprocess.run([sys.executable, _p("scripts", "verify_macos_app.py")],
                       capture_output=True, text=True, timeout=60)
    if not os.path.isdir(_p("dist", "FinSight.app")):
        assert r.returncode == 2 and "SKIP" in r.stdout
    else:
        assert r.returncode == 0
