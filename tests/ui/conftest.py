# UI test bootstrap. Qt runs headless (offscreen) so the suite works without a display.
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app, build_query_services


def _populate(db_path: str) -> None:
    d = os.path.dirname(db_path)
    ged = os.path.join(d, "ged.synthetic.xlsx")
    bud = os.path.join(d, "budget.synthetic.xlsx")
    build_synthetic_ged(ged)
    build_synthetic_budget(bud)
    app = build_app(db_path, FixedClock())
    app["orch"].run_review("2026-07", "July", "2026", ged, bud, approve=True)


@pytest.fixture
def populated_db(tmp_path):
    dbp = str(tmp_path / "fs.db")
    _populate(dbp)
    return dbp


@pytest.fixture
def empty_db(tmp_path):
    return str(tmp_path / "empty.db")


@pytest.fixture
def window_factory(qtbot):
    from finsight.delivery.desktop.main_window import MainWindow
    from finsight.delivery.desktop.controllers import AppController

    def make(db_path, ask_fin_backend=None):
        window = MainWindow(AppController(build_query_services(db_path),
                                          ask_fin_backend=ask_fin_backend))
        qtbot.addWidget(window)
        return window

    return make
