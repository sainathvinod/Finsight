# Verifies: invoice-upload FOUNDATION (target-product §6 + RED CARD on invoice analysis).
#   The optional Invoice source is CAPTURED for provenance + audit + source-identity, but is NEVER
#   extracted or analyzed (no invoice rule catalog exists — E-12 / Phase 3). Capturing it must not
#   perturb the deterministic GED+Budget core: identical GED/Budget produce an identical result
#   whether or not an invoice was uploaded.
# Authority: FR-001/FR-003 (provenance, read-only), FR-004 (optional slots), NFR-012, ADR-005 (audit),
#   ADR-012 (source binding). No invoice rule is invented.
import os
import tempfile
import unittest

from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.review_session import ReviewSession


def _sources(tmp):
    ged = os.path.join(tmp, "g.xlsx"); bud = os.path.join(tmp, "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    inv = os.path.join(tmp, "invoice.pdf")
    with open(inv, "wb") as f:
        f.write(b"%PDF-1.4 synthetic invoice bytes for capture-only test")
    return ged, bud, inv


def _run(db, ged, bud, invoice=None, cid="2026-07"):
    app = build_app(db, FixedClock())
    wf = ReviewWorkflowService(app.orch.engine)
    wf.create_review(cid, "July", "2026")
    s = ReviewSession(cid)
    wf.upload(s, ged, bud, invoice)
    wf.process(s)
    wf.verify(s)
    result = wf.analyze(s)
    return app, result


class TestInvoiceCapture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ged, self.bud, self.inv = _sources(self.tmp)

    def test_invoice_is_captured_as_provenance_audit_and_binding(self):
        app, _ = _run(os.path.join(self.tmp, "with.db"), self.ged, self.bud, self.inv)
        cid = "2026-07"
        # Provenance: an INVOICE ingested-file record with the file's real name + fingerprint.
        docs = {d["doc_type"]: d for d in app.ingested_repo.list(cid)}
        self.assertIn("INVOICE", docs)
        self.assertEqual(docs["INVOICE"]["name"], "invoice.pdf")
        self.assertTrue(docs["INVOICE"]["fingerprint"])
        # Audit: an explicit, append-only upload_invoice fact (no material action disappears — §19).
        self.assertIn("upload_invoice", app.audit.timeline(cid))
        # Source identity captured (path hint + fingerprint), like any untrusted inbound file.
        self.assertIsNotNone(app.source_binding_repo.get(cid, "INVOICE"))

    def test_invoice_is_never_extracted_or_analyzed(self):
        app, _ = _run(os.path.join(self.tmp, "x.db"), self.ged, self.bud, self.inv)
        cid = "2026-07"
        # No finding cites the invoice, and no invoice rule ran — it is not part of the analysis.
        for f in app.finding_repo.list(cid):
            refs = " ".join(f.get("source_refs", []))
            self.assertNotIn("INVOICE", refs.upper())
            self.assertFalse(f.get("rule_id", "").upper().startswith("R-INV"))

    def test_capturing_an_invoice_does_not_change_deterministic_results(self):
        # Same GED/Budget, one run with an invoice and one without -> identical finding count.
        _app_no, res_no = _run(os.path.join(self.tmp, "no.db"), self.ged, self.bud, None)
        _app_yes, res_yes = _run(os.path.join(self.tmp, "yes.db"), self.ged, self.bud, self.inv)
        self.assertEqual(res_yes.finding_count, res_no.finding_count)
        self.assertGreaterEqual(res_no.finding_count, 1)


if __name__ == "__main__":
    unittest.main()
