import os
import tempfile
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app, build_ai_services


def make():
    """Build a fresh Container + AI services on a temp database."""
    tmp = tempfile.mkdtemp()
    container = build_app(os.path.join(tmp, "fs.db"), FixedClock())
    ai = build_ai_services(container)
    return tmp, container, ai


def seed_review(container, tmp, cid, month="July", year="2026"):
    """Run a synthetic deterministic review so grounding has real facts for `cid`."""
    ged = os.path.join(tmp, f"g_{cid}.xlsx")
    bud = os.path.join(tmp, f"b_{cid}.xlsx")
    build_synthetic_ged(ged)
    build_synthetic_budget(bud)
    container.orch.run_review(cid, month, year, ged, bud, approve=True)
