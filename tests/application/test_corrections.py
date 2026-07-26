# Verifies: user-correction subsystem (target-product §10-11; FR-028/029, NFR-056, ADR-003/005/006/011).
#   - A correction is captured with the immutable ORIGINAL and the CURRENT corrected value.
#   - The original extracted value is NEVER overwritten across repeated edits.
#   - Analysis runs on the APPROVED corrected dataset: a correction re-fingerprints the verified data,
#     and reverting restores the original fingerprint exactly (determinism).
#   - Every save/revert is an append-only audit fact carrying the full detail (§19).
#   - Corrections are pre-verification only; invalid values and unknown fields are rejected.
#   - The source file bytes are never touched (corrections are additive, DB-only).
import os
import tempfile
import unittest
from decimal import Decimal

from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.review_session import ReviewSession
from finsight.application.corrections import CorrectionService
from finsight.application.analysis import verified_dataset_fingerprint
from finsight.application.errors import InvalidCorrectionError


class TestCorrections(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ged = os.path.join(self.tmp, "g.xlsx"); build_synthetic_ged(self.ged)
        self.bud = os.path.join(self.tmp, "b.xlsx"); build_synthetic_budget(self.bud)
        self.ged_bytes = open(self.ged, "rb").read()
        self.app = build_app(os.path.join(self.tmp, "fs.db"), FixedClock())
        self.engine = self.app.orch.engine
        self.wf = ReviewWorkflowService(self.engine)
        self.corr = CorrectionService(self.app.extraction_override_repo, self.app.cycle_repo,
                                      self.app.audit, self.app.uow, self.app.clock)

    def _processed(self, cid="2026-07"):
        self.wf.create_review(cid, "July", "2026")
        s = ReviewSession(cid)
        self.wf.upload(s, self.ged, self.bud)
        self.wf.process(s)
        return s

    def _first_ged_amount(self, s):
        row = s.ctx["extracted"]["ged_valid"][0]
        return row["source"], str(row["amount"])

    def test_correction_captures_original_and_current(self):
        s = self._processed(); cid = "2026-07"
        src, original = self._first_ged_amount(s)
        self.corr.save(cid, "GED", src, "amount", original, "12345")
        ov = self.app.extraction_override_repo.get(cid, "GED", src, "amount")
        self.assertEqual(ov.original_value, original)
        self.assertEqual(ov.current_value, "12345")
        self.assertFalse(ov.reverted)

    def test_original_is_never_overwritten_across_edits(self):
        s = self._processed(); cid = "2026-07"
        src, original = self._first_ged_amount(s)
        self.corr.save(cid, "GED", src, "amount", original, "100")
        self.corr.save(cid, "GED", src, "amount", "100", "200")   # a second edit
        ov = self.app.extraction_override_repo.get(cid, "GED", src, "amount")
        self.assertEqual(ov.original_value, original)             # STILL the extracted original
        self.assertEqual(ov.current_value, "200")
        self.assertEqual(ov.version, 2)

    def test_correction_re_fingerprints_and_revert_restores(self):
        s = self._processed(); cid = "2026-07"
        ex = s.ctx["extracted"]
        src, original = self._first_ged_amount(s)
        fp_before = verified_dataset_fingerprint(self.engine.build_verified(cid, ex, approve=True))
        self.corr.save(cid, "GED", src, "amount", original, str(Decimal(original) + Decimal("1000")))
        fp_after = verified_dataset_fingerprint(self.engine.build_verified(cid, ex, approve=True))
        self.assertNotEqual(fp_before, fp_after)                  # analysis input changed
        self.corr.revert(cid, "GED", src, "amount")
        fp_reverted = verified_dataset_fingerprint(self.engine.build_verified(cid, ex, approve=True))
        self.assertEqual(fp_reverted, fp_before)                  # reverted == original, exactly

    def test_analysis_runs_on_corrected_dataset(self):
        s = self._processed(); cid = "2026-07"
        src, original = self._first_ged_amount(s)
        self.corr.save(cid, "GED", src, "amount", original, str(Decimal(original) + Decimal("777")))
        self.wf.verify(s)
        result = self.wf.analyze(s)
        corrected_fp = verified_dataset_fingerprint(s.ctx["vds"])
        run = self.app.run_repo.list(cid)[0] if hasattr(self.app.run_repo, "list") else None
        # The analysis input fingerprint IS the corrected verified-dataset fingerprint.
        self.assertEqual(result.input_fingerprint, corrected_fp)

    def test_every_correction_is_audited(self):
        s = self._processed(); cid = "2026-07"
        src, original = self._first_ged_amount(s)
        self.corr.save(cid, "GED", src, "amount", original, "500", reason="typo in source")
        self.corr.revert(cid, "GED", src, "amount")
        events = self.app.audit.events(cid)
        saved = [e for e in events if e["action"] == "correction_saved"]
        reverted = [e for e in events if e["action"] == "correction_reverted"]
        self.assertEqual(len(saved), 1)
        d = saved[0]["detail"]
        self.assertEqual((d["source_ref"], d["field"], d["original_value"], d["corrected_value"]),
                         (src, "amount", original, "500"))
        self.assertEqual(d["reason"], "typo in source")
        self.assertEqual(len(reverted), 1)

    def test_corrections_rejected_after_verification(self):
        s = self._processed(); cid = "2026-07"
        src, original = self._first_ged_amount(s)
        self.wf.verify(s)                                         # now VERIFIED
        with self.assertRaises(InvalidCorrectionError):
            self.corr.save(cid, "GED", src, "amount", original, "1")

    def test_invalid_values_and_fields_rejected(self):
        s = self._processed(); cid = "2026-07"
        src, original = self._first_ged_amount(s)
        with self.assertRaises(InvalidCorrectionError):
            self.corr.save(cid, "GED", src, "amount", original, "not-a-number")
        with self.assertRaises(InvalidCorrectionError):
            self.corr.save(cid, "GED", src, "confidence", original, "high")   # not an editable field

    def test_source_file_bytes_are_never_modified(self):
        s = self._processed(); cid = "2026-07"
        src, original = self._first_ged_amount(s)
        self.corr.save(cid, "GED", src, "amount", original, "999")
        self.assertEqual(open(self.ged, "rb").read(), self.ged_bytes)   # source untouched

    def test_corrections_are_deterministic(self):
        # Same correction applied in two independent reviews yields the same verified fingerprint.
        fps = []
        for cid in ("2026-07", "2026-08"):
            month = "July" if cid == "2026-07" else "August"
            self.wf.create_review(cid, month, "2026")
            s = ReviewSession(cid)
            self.wf.upload(s, self.ged, self.bud); self.wf.process(s)
            src, original = self._first_ged_amount(s)
            self.corr.save(cid, "GED", src, "amount", original, "4242")
            fps.append(verified_dataset_fingerprint(
                self.engine.build_verified(cid, s.ctx["extracted"], approve=True)))
        self.assertEqual(fps[0], fps[1])


if __name__ == "__main__":
    unittest.main()
