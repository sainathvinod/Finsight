# Verifies: FR-005/006/026/029/070/116 — step-oriented interactive workflow drives the same
# deterministic transitions as the orchestrator, with the verification gate, safe stop, resume
# no-duplication, and invalid-transition rejection.
import os
import tempfile
import unittest

from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app
from finsight.application.workflow import ReviewWorkflowService
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
        self.app = build_app(self.db, FixedClock())
        self.wf = ReviewWorkflowService(self.app["orch"])

    def _state(self, cid="2026-07"):
        return self.app["cycle_repo"].get(cid).state.value

    # --- setup ---
    def test_create_review(self):
        self.wf.create_review("2026-07", "July", "2026")
        self.assertEqual(self._state(), "Created")
        self.assertIn("setup", self.app["audit"].timeline("2026-07"))

    def test_duplicate_cycle_rejected(self):
        self.wf.create_review("2026-07", "July", "2026")
        with self.assertRaises(DuplicateReviewError):
            self.wf.create_review("2026-07", "July", "2026")

    def test_missing_file_rejected_at_upload(self):
        self.wf.create_review("2026-07", "July", "2026")
        with self.assertRaises(MissingFileError):
            self.wf.upload("2026-07", os.path.join(self.tmp, "nope.xlsx"), self.bud)

    # --- happy path through export ---
    def test_full_workflow_to_export(self):
        self.wf.create_review("2026-07", "July", "2026")
        up = self.wf.upload("2026-07", self.ged, self.bud)
        self.assertEqual({i.doc_type for i in up.items}, {"GED", "BUDGET"})
        self.assertEqual(self._state(), "Intake")

        val = self.wf.process("2026-07")
        self.assertTrue(val.available)
        self.assertIsNone(val.rejected_reason)
        self.assertEqual(self._state(), "Processed")

        self.wf.verify("2026-07")
        self.assertEqual(self._state(), "Verified")
        self.assertIn("verify", self.app["audit"].timeline("2026-07"))

        res = self.wf.analyze("2026-07")
        self.assertEqual(self._state(), "Analyzed")
        self.assertEqual(res.finding_count, 1)
        self.assertEqual(res.config_version, "cfg-synthetic-1")
        self.assertTrue(res.input_fingerprint)

        summary = self.wf.summarize("2026-07")
        self.assertEqual(self._state(), "Summarized")
        self.assertEqual(summary.finding_count, 1)
        self.assertEqual(summary.status_label, "Needs Attention")

        exp = self.wf.export("2026-07")
        self.assertEqual(self._state(), "Exported")
        self.assertIn("config_version", exp.content)
        self.assertTrue(exp.json_text.strip().startswith("{"))

    # --- verification gate ---
    def test_analysis_blocked_before_verification(self):
        self.wf.create_review("2026-07", "July", "2026")
        self.wf.upload("2026-07", self.ged, self.bud)
        self.wf.process("2026-07")
        with self.assertRaises(VerificationRequiredError):
            self.wf.analyze("2026-07")
        self.assertEqual(self._state(), "Processed")   # unchanged
        self.assertNotIn("analyze", self.app["audit"].timeline("2026-07"))

    # --- validation rejection safe stop ---
    def test_validation_rejection_cannot_verify(self):
        ged_bad, bud = _files(self.tmp, corrupt_ged=True)
        self.wf.create_review("2026-08", "Aug", "2026")
        self.wf.upload("2026-08", ged_bad, bud)
        val = self.wf.process("2026-08")
        self.assertFalse(val.available)
        self.assertIn("could not be read", val.rejected_reason)
        with self.assertRaises(ValidationRejectedError):
            self.wf.verify("2026-08")
        self.assertNotIn("verify", self.app["audit"].timeline("2026-08"))

    # --- findings persisted once; idempotent analysis ---
    def test_findings_persisted_once(self):
        self.wf.create_review("2026-07", "July", "2026")
        self.wf.upload("2026-07", self.ged, self.bud)
        self.wf.process("2026-07")
        self.wf.verify("2026-07")
        self.wf.analyze("2026-07")
        self.wf.analyze("2026-07")   # second call must not duplicate
        self.assertEqual(len(self.app["finding_repo"].list("2026-07")), 1)
        self.assertEqual(self.app["audit"].timeline("2026-07").count("finding"), 1)

    # --- invalid transitions ---
    def test_invalid_transitions_rejected(self):
        self.wf.create_review("2026-07", "July", "2026")
        with self.assertRaises(InvalidTransitionError):
            self.wf.process("2026-07")          # no upload yet
        self.wf.upload("2026-07", self.ged, self.bud)
        self.wf.process("2026-07")
        self.wf.verify("2026-07")
        self.wf.analyze("2026-07")
        with self.assertRaises(InvalidTransitionError):
            self.wf.export("2026-07")            # summary not generated yet

    # --- resume in a fresh session: no duplicate audit or findings ---
    def test_resume_no_duplicate(self):
        self.wf.create_review("2026-07", "July", "2026")
        self.wf.upload("2026-07", self.ged, self.bud)
        self.wf.process("2026-07")
        self.wf.verify("2026-07")
        self.wf.analyze("2026-07")

        app2 = build_app(self.db, FixedClock())          # new session on the same database
        wf2 = ReviewWorkflowService(app2["orch"])
        wf2.open_review("2026-07")
        wf2.upload("2026-07", self.ged, self.bud)        # all idempotent (already past these states)
        wf2.process("2026-07")
        wf2.verify("2026-07")
        wf2.analyze("2026-07")
        wf2.summarize("2026-07")
        wf2.export("2026-07")

        tl = app2["audit"].timeline("2026-07")
        for step in ("setup", "upload_ged", "verify", "analyze", "finding", "summarize", "export"):
            self.assertEqual(tl.count(step), 1)
        self.assertEqual(len(app2["finding_repo"].list("2026-07")), 1)


if __name__ == "__main__":
    unittest.main()
