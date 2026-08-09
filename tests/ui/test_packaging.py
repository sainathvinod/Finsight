# Verifies: R1 packaging — the official launch entry points start the application and exit cleanly in
# a headless smoke run (ADR-013 single-user desktop). Guards against the packaged app failing to
# compose (QApplication, single-instance lock, migrations, services, MainWindow) independent of CWD.
import os
import subprocess
import sys
import tempfile

import pytest

pytestmark = pytest.mark.ui

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SRC = os.path.join(_REPO, "src")


def _release_env(**extra):
    """The environment a released FinSight actually starts in.

    The session fixtures export a signed test role manifest for in-process composition, and a
    subprocess would inherit it — putting this smoke launch on the administrator-provisioned
    machine-shared path, whose deployment group and machine directories no clean machine (or CI
    runner) has. The release model is the unprovisioned single-user profile, so the manifest
    configuration is dropped here and the launch exercises what a recipient actually runs.
    """

    env = dict(os.environ, FINSIGHT_SMOKE="1", QT_QPA_PLATFORM="offscreen", PYTHONPATH=_SRC)
    for name in (
        "FINSIGHT_ROLE_MANIFEST",
        "FINSIGHT_ROLE_MANIFEST_SIGNATURE",
        "FINSIGHT_ROLE_MANIFEST_PUBLIC_KEY",
        "FINSIGHT_ROLE_MANIFEST_KEY_ID",
    ):
        env.pop(name, None)
    env.update(extra)
    return env


def _smoke_launch(argv):
    env = _release_env(FINSIGHT_DB=os.path.join(tempfile.mkdtemp(), "finsight.db"))
    # Run from a NEUTRAL directory so startup cannot depend on the repo working directory.
    return subprocess.run(argv, env=env, cwd=tempfile.gettempdir(),
                          capture_output=True, text=True, timeout=90)


# These two launch a real, unprovisioned single-user startup, so they resolve the store key
# through the platform key provider. On macOS that is the login keychain, which raises an
# authorization prompt when re-reading an existing item and times out headless — the deferred
# macOS defect recorded in .github/workflows/release-macos.yml. Windows uses in-process DPAPI
# with CRYPTPROTECT_UI_FORBIDDEN and has no equivalent, which is where this smoke matters for
# the release. Marked non-strict so it flips to xpass once the keychain ACL fix lands.
_MACOS_KEYCHAIN_PROMPT = pytest.mark.xfail(
    sys.platform == "darwin",
    strict=False,
    reason="deferred macOS login-keychain re-read prompt; not a Windows release blocker",
)


@_MACOS_KEYCHAIN_PROMPT
def test_python_m_finsight_launches_and_exits_clean():
    r = _smoke_launch([sys.executable, "-m", "finsight"])
    assert r.returncode == 0, r.stderr


def test_console_entrypoint_target_is_importable_and_callable():
    # The `finsight` console script maps to this target; it must import + expose main().
    r = _smoke_launch([sys.executable, "-c",
                       "from finsight.delivery.desktop.app import main; import inspect; "
                       "assert callable(main); print('entrypoint OK')"])
    assert r.returncode == 0 and "entrypoint OK" in r.stdout, r.stderr


@_MACOS_KEYCHAIN_PROMPT
def test_release_startup_ignores_user_environment_database_redirect():
    dbdir = tempfile.mkdtemp()
    db = os.path.join(dbdir, "finsight.db")
    env = _release_env(FINSIGHT_DB=db)
    result = subprocess.run(
        [sys.executable, "-m", "finsight"],
        env=env,
        cwd=tempfile.gettempdir(),
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stderr
    assert not os.path.exists(db)
    assert not os.path.exists(db + ".lock")
