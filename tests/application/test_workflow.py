# Verifies: step-oriented interactive workflow (stateless service + explicit ReviewSession) drives
# the same deterministic transitions, with the verification gate, safe stop, resume no-duplication,
# and invalid-transition rejection.
import os
import tempfile
import unittest

from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.review_session import ReviewSession
from finsight.application.errors import (
    DuplicateReviewError, MissingFileError, ValidationRejectedError,
    VerificationRequiredError, InvalidTransitionError,
)


def _files(tmp, corrupt_ged=False):
    ged = os.path.join(tmp, "g.xlsx")
    bud = os.path.join(tmp, "b.xlsx")
    build_synthetic_budget(bud)
    if corrupt_ged:
        with open(ged, "wb") as f:
            f.write(b"not a workbook")
    else:
        build_synthetic_ged(ged)
    return ged, bud


class TestWorkflowService(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "fs.db")
        self.ged, self.bud = _files(self.tmp)
        self.app = build_app(self.db, FixedClock())        # typed Container
        self.wf = ReviewWorkflowService(self.app.orch.engine)   # workflow drives the shared engine

    def _state(self, cid="2026-07"):
        return self.app.cycle_repo.get(cid).state.value

    def _session(self, cid="2026-07"):
        return ReviewSession(cid)

    def test_workflow_service_is_stateless(self):
        self.assertFalse(hasattr(self.wf, "_ctx"))          # no per-cycle mutable map

    def test_create_review(self):
        self.wf.create_review("2026-07", "July", "2026")
        self.assertEqual(self._state(), "Created")
        self.assertIn("setup", self.app.audit.timeline("2026-07"))

    def test_duplicate_cycle_rejected(self):
        self.wf.create_review("2026-07", "July", "2026")
        with self.assertRaises(DuplicateReviewError):
            self.wf.create_review("2026-07", "July", "2026")

    def test_missing_file_rejected_at_upload(self):
        self.wf.create_review("2026-07", "July", "2026")
        s = self._session()
        with self.assertRaises(MissingFileError):
            self.wf.upload(s, os.path.join(self.tmp, "nope.xlsx"), self.bud)

    def test_full_workflow_to_export(self):
        self.wf.create_review("2026-07", "July", "2026")
        s = self._session()
        up = self.wf.upload(s, self.ged, self.bud)
        self.assertEqual({i.doc_type for i in up.items}, {"GED", "BUDGET"})
        self.assertEqual(self._state(), "Intake")

        val = self.wf.process(s)
        self.assertTrue(val.available)
        self.assertEqual(self._state(), "Processed")

        self.wf.verify(s)
        self.assertEqual(self._state(), "Verified")

        res = self.wf.analyze(s)
        self.assertEqual(self._state(), "Analyzed")
        self.assertEqual(res.finding_count, 1)
        self.assertEqual(res.config_version, "cfg-synthetic-1")

        summary = self.wf.summarize(s)
        self.assertEqual(self._state(), "Summarized")
        self.assertEqual(summary.finding_count, 1)

        exp = self.wf.export(s)
        self.assertEqual(self._state(), "Exported")
        self.assertIn("config_version", exp.content)

    def test_analysis_blocked_before_verification(self):
        self.wf.create_review("2026-07", "July", "2026")
        s = self._session()
        self.wf.upload(s, self.ged, self.bud)
        self.wf.process(s)
        with self.assertRaises(VerificationRequiredError):
            self.wf.analyze(s)
        self.assertEqual(self._state(), "Processed")
        self.assertNotIn("analyze", self.app.audit.timeline("2026-07"))

    def test_validation_rejection_cannot_verify(self):
        ged_bad, bud = _files(self.tmp, corrupt_ged=True)
        self.wf.create_review("2026-08", "Aug", "2026")
        s = self._session("2026-08")
        self.wf.upload(s, ged_bad, bud)
        val = self.wf.process(s)
        self.assertFalse(val.available)
        self.assertIn("could not be read", val.rejected_reason)
        with self.assertRaises(ValidationRejectedError):
            self.wf.verify(s)
        self.assertNotIn("verify", self.app.audit.timeline("2026-08"))

    def test_findings_persisted_once(self):
        self.wf.create_review("2026-07", "July", "2026")
        s = self._session()
        self.wf.upload(s, self.ged, self.bud)
        self.wf.process(s)
        self.wf.verify(s)
        self.wf.analyze(s)
        self.wf.analyze(s)   # idempotent
        self.assertEqual(len(self.app.finding_repo.list("2026-07")), 1)
        self.assertEqual(self.app.audit.timeline("2026-07").count("finding"), 1)

    def test_invalid_transitions_rejected(self):
        self.wf.create_review("2026-07", "July", "2026")
        s = self._session()
        with self.assertRaises(InvalidTransitionError):
            self.wf.process(s)          # no upload yet
        self.wf.upload(s, self.ged, self.bud)
        self.wf.process(s)
        self.wf.verify(s)
        self.wf.analyze(s)
        with self.assertRaises(InvalidTransitionError):
            self.wf.export(s)            # summary not generated yet

    def test_resume_no_duplicate(self):
        self.wf.create_review("2026-07", "July", "2026")
        s = self._session()
        self.wf.upload(s, self.ged, self.bud)
        self.wf.process(s)
        self.wf.verify(s)
        self.wf.analyze(s)

        app2 = build_app(self.db, FixedClock())              # new session, same database
        wf2 = ReviewWorkflowService(app2.orch.engine)
        s2 = ReviewSession("2026-07")
        wf2.open_review("2026-07")
        wf2.upload(s2, self.ged, self.bud)                   # all idempotent (already past these states)
        wf2.process(s2)
        wf2.verify(s2)
        wf2.analyze(s2)
        wf2.summarize(s2)
        wf2.export(s2)

        tl = app2.audit.timeline("2026-07")
        for step in ("setup", "upload_ged", "verify", "analyze", "finding", "summarize", "export"):
            self.assertEqual(tl.count(step), 1)
        self.assertEqual(len(app2.finding_repo.list("2026-07")), 1)


if __name__ == "__main__":
    unittest.main()
