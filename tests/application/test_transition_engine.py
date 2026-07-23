# Verifies: the batch (Orchestrator.run_review) and step-oriented (ReviewWorkflowService) paths use
# the SAME TransitionEngine and produce equivalent results; and the workflow service does not reach
# into Orchestrator private methods.
import os
import inspect
import tempfile
import unittest
from collections import Counter

from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.review_session import ReviewSession
import finsight.application.workflow as workflow_mod


def _files(tmp, corrupt=False):
    ged = os.path.join(tmp, "g.xlsx")
    bud = os.path.join(tmp, "b.xlsx")
    build_synthetic_budget(bud)
    if corrupt:
        with open(ged, "wb") as f:
            f.write(b"nope")
    else:
        build_synthetic_ged(ged)
    return ged, bud


def _batch(corrupt=False):
    tmp = tempfile.mkdtemp()
    ged, bud = _files(tmp, corrupt)
    app = build_app(os.path.join(tmp, "fs.db"), FixedClock())
    app.orch.run_review("2026-07", "July", "2026", ged, bud, approve=True)
    return app


def _stepwise(corrupt=False):
    tmp = tempfile.mkdtemp()
    ged, bud = _files(tmp, corrupt)
    app = build_app(os.path.join(tmp, "fs.db"), FixedClock())
    wf = ReviewWorkflowService(app.orch.engine)
    s = ReviewSession("2026-07")
    wf.create_review("2026-07", "July", "2026")
    wf.upload(s, ged, bud)
    val = wf.process(s)
    if val.available:
        wf.verify(s)
        wf.analyze(s)
        wf.summarize(s)
        wf.export(s)
    return app


class TestEngineEquivalence(unittest.TestCase):
    def test_final_state_and_findings_equivalent(self):
        a, b = _batch(), _stepwise()
        self.assertEqual(a.cycle_repo.get("2026-07").state, b.cycle_repo.get("2026-07").state)
        self.assertEqual(a.finding_repo.list("2026-07"), b.finding_repo.list("2026-07"))

    def test_rule_run_metadata_equivalent(self):
        a, b = _batch(), _stepwise()
        ra, rb = a.run_repo.get_by_cycle("2026-07"), b.run_repo.get_by_cycle("2026-07")
        for k in ("ruleset_version", "config_version", "input_fingerprint", "finding_count"):
            self.assertEqual(ra[k], rb[k], k)

    def test_transition_audit_actions_equivalent(self):
        a, b = _batch(), _stepwise()

        def acts(app):
            c = Counter(app.audit.timeline("2026-07"))
            c.pop("setup", None)   # both have setup; timing differs, count is 1 either way
            return c
        self.assertEqual(acts(a), acts(b))

    def test_rejection_safe_stop_equivalent(self):
        for app in (_batch(corrupt=True), _stepwise(corrupt=True)):
            tl = app.audit.timeline("2026-07")
            self.assertIn("validate", tl)
            self.assertNotIn("verify", tl)
            self.assertNotIn("analyze", tl)
            self.assertEqual(app.finding_repo.list("2026-07"), [])


class TestNoPrivateCoupling(unittest.TestCase):
    def test_workflow_does_not_access_orchestrator_privates(self):
        src = inspect.getsource(workflow_mod)
        for forbidden in ("Orchestrator", "orch._", "._do_", "._prepare", "._drive", "._transition", "._build_"):
            self.assertNotIn(forbidden, src, "workflow.py must not contain %r" % forbidden)


if __name__ == "__main__":
    unittest.main()
