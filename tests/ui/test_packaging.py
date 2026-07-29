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


def _smoke_launch(argv):
    env = dict(os.environ, FINSIGHT_SMOKE="1", QT_QPA_PLATFORM="offscreen",
               PYTHONPATH=_SRC, FINSIGHT_DB=os.path.join(tempfile.mkdtemp(), "finsight.db"))
    # Run from a NEUTRAL directory so startup cannot depend on the repo working directory.
    return subprocess.run(argv, env=env, cwd=tempfile.gettempdir(),
                          capture_output=True, text=True, timeout=90)


def test_python_m_finsight_launches_and_exits_clean():
    r = _smoke_launch([sys.executable, "-m", "finsight"])
    assert r.returncode == 0, r.stderr


def test_console_entrypoint_target_is_importable_and_callable():
    # The `finsight` console script maps to this target; it must import + expose main().
    r = _smoke_launch([sys.executable, "-c",
                       "from finsight.delivery.desktop.app import main; import inspect; "
                       "assert callable(main); print('entrypoint OK')"])
    assert r.returncode == 0 and "entrypoint OK" in r.stdout, r.stderr


def test_release_startup_ignores_user_environment_database_redirect():
    dbdir = tempfile.mkdtemp()
    db = os.path.join(dbdir, "finsight.db")
    env = dict(os.environ, FINSIGHT_SMOKE="1", QT_QPA_PLATFORM="offscreen", PYTHONPATH=_SRC,
               FINSIGHT_DB=db)
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
