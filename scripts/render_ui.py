#!/usr/bin/env python
"""Render FinSight desktop screens to PNGs for visual verification (Product Owner §24).

Runs headless (offscreen Qt) and writes deterministic screenshots to a STABLE repository
directory — artifacts/ui-verification/ — never /tmp. Each screen is grabbed at a fixed size so
diffs are meaningful. This is a developer/verification tool, not part of the shipped product.

Usage:
    QT_QPA_PLATFORM=offscreen python scripts/render_ui.py [out_dir]
"""
from __future__ import annotations
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))
sys.path.insert(0, REPO_ROOT)  # for tests.support helpers

from PySide6.QtWidgets import QApplication  # noqa: E402
from finsight.app import build_app, build_query_services  # noqa: E402
from finsight.delivery.desktop.main_window import MainWindow  # noqa: E402
from finsight.delivery.desktop.controllers import AppController  # noqa: E402
from finsight.delivery.desktop.theme.qss import build_qss  # noqa: E402
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget  # noqa: E402


def _populated_db(workdir: str) -> str:
    ged = os.path.join(workdir, "ged.synthetic.xlsx")
    bud = os.path.join(workdir, "budget.synthetic.xlsx")
    build_synthetic_ged(ged)
    build_synthetic_budget(bud)
    db = os.path.join(workdir, "fs.db")
    app = build_app(db, FixedClock())
    app["orch"].run_review("2026-07", "July", "2026", ged, bud, approve=True)
    return db


def _grab(window: MainWindow, out_path: str) -> None:
    window.resize(1180, 860)
    window.grab().save(out_path)
    print(f"  wrote {os.path.relpath(out_path, REPO_ROOT)}")


def main() -> int:
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO_ROOT, "artifacts", "ui-verification")
    os.makedirs(out_dir, exist_ok=True)

    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(build_qss())

    with tempfile.TemporaryDirectory() as work:
        # 1. First-ever launch: empty DB -> dedicated Welcome screen.
        empty_db = os.path.join(work, "empty.db")
        w_empty = MainWindow(AppController(build_query_services(empty_db)))
        assert w_empty.current_view_key() == "welcome", w_empty.current_view_key()
        _grab(w_empty, os.path.join(out_dir, "01-welcome-first-launch.png"))

        # 1b. Create New Review -> dedicated Review-Period step (§5).
        w_empty.view("welcome").newReviewRequested.emit()
        _grab(w_empty, os.path.join(out_dir, "01b-create-review-period.png"))

        # 1c. After creating a review -> Data Upload with three source cards (§6).
        w_empty._c.create_review("2026-08", "August", "2026")
        w_empty.navigate("workspace")
        w_empty._workspace._apply(1)   # Data Upload step
        up = w_empty._workspace.panel(1)
        _grab(w_empty, os.path.join(out_dir, "01c-data-upload-three-sources.png"))

        # 1d. Missing-source two-step confirmation (§7): required present, invoice absent.
        ged = os.path.join(work, "g.xlsx"); bud = os.path.join(work, "b.xlsx")
        build_synthetic_ged(ged); build_synthetic_budget(bud)
        up.set_ged(ged); up.set_budget(bud)
        up._on_upload()                # step 1: first warning naming the missing source
        _grab(w_empty, os.path.join(out_dir, "01d-missing-source-step1.png"))
        up._continue1.click()          # step 2: explicit Continue-anyway choice
        _grab(w_empty, os.path.join(out_dir, "01e-missing-source-step2.png"))

        # 1f. Extraction review (§9): all records per source with lineage, at the Verification step.
        w_empty._c.upload("2026-08", ged, bud)
        w_empty._c._s.workflow.process(w_empty._c._session_for("2026-08"))
        w_empty._c.select_review("2026-08")
        w_empty.navigate("workspace")
        w_empty._workspace._apply(4)   # Verification step
        _grab(w_empty, os.path.join(out_dir, "01f-extraction-review.png"))

        # 1g. A user correction: edit the first GED amount -> marked cell + original in tooltip (§10-11).
        verify = w_empty._workspace.panel(4)
        gtab = verify._review.tab("GED")
        amount_col = list(gtab._records.columns).index("amount")
        gtab.edit_cell(0, amount_col, "12000")
        _grab(w_empty, os.path.join(out_dir, "01g-extraction-review-corrected.png"))

        # 2. Returning user: populated DB -> Dashboard home + key screens.
        pop_db = _populated_db(work)
        w = MainWindow(AppController(build_query_services(pop_db)))
        for key, name in [("dashboard", "02-dashboard-home"), ("reviews", "03-reviews-home"),
                          ("overview", "04-review-overview"), ("workspace", "05-workflow"),
                          ("findings", "06-findings"), ("audit", "07-audit"), ("askfin", "08-ask-fin")]:
            w.navigate(key)
            _grab(w, os.path.join(out_dir, f"{name}.png"))

        # 09. The visual leadership report (§14) incl. the Financial Map, on the completed review.
        w.navigate("workspace")
        w._workspace._apply(7)         # Leadership Report step
        w._workspace.panel(7).refresh()
        _grab(w, os.path.join(out_dir, "09-leadership-report.png"))

    print(f"Rendered screens to {os.path.relpath(out_dir, REPO_ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
