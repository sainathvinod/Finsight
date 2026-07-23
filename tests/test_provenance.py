# Verifies: FR-001, FR-003, FR-010 (AC-2): provenance + fingerprint captured; source never modified
import unittest, tempfile, os, hashlib
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

class TestProvenance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ged = os.path.join(self.tmp, "ged.synthetic.xlsx")
        self.bud = os.path.join(self.tmp, "budget.synthetic.xlsx")
        build_synthetic_ged(self.ged); build_synthetic_budget(self.bud)
        self.app = build_app(os.path.join(self.tmp, "fs.db"), FixedClock())
    def test_provenance_and_readonly(self):
        before = sha256(self.ged), sha256(self.bud)
        self.app["orch"].run_review("2026-07", "July", "2026", self.ged, self.bud, approve=True)
        after = sha256(self.ged), sha256(self.bud)
        self.assertEqual(before, after)  # sources never modified (read-only ingest)
        recs = {r["doc_type"]: r for r in self.app["ingested_repo"].list("2026-07")}
        self.assertEqual(set(recs), {"GED", "BUDGET"})
        self.assertEqual(recs["GED"]["fingerprint"], before[0])       # fingerprint == source bytes
        self.assertEqual(recs["BUDGET"]["fingerprint"], before[1])
        for r in recs.values():                                       # full provenance tuple
            self.assertTrue(r["name"] and r["ts"] and r["actor"] and r["period"] and r["size"] > 0)
        acts = self.app["audit"].timeline("2026-07")
        self.assertIn("upload_ged", acts); self.assertIn("upload_budget", acts)

if __name__ == "__main__":
    unittest.main()
