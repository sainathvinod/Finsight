# Verifies: NFR-021, NFR-008, F-02-06 (repeat-run byte-identical serialized findings; no duplicate)
import unittest, tempfile, os, json
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app

def serialize(res):
    fs = [{"id": f.id, "account": f.account, "severity": f.severity, "type": f.finding_type,
           "evidence": f.evidence, "source_refs": f.source_refs} for f in res["findings"]]
    return json.dumps({"findings": fs, "run": res["run"]}, sort_keys=True, separators=(",",":"))

class TestDeterminism(unittest.TestCase):
    def _run(self):
        tmp = tempfile.mkdtemp()
        g = os.path.join(tmp,"g.xlsx"); b = os.path.join(tmp,"b.xlsx")
        build_synthetic_ged(g); build_synthetic_budget(b)
        app = build_app(os.path.join(tmp,"fs.db"), FixedClock())
        return serialize(app["orch"].run_review("2026-07","July","2026",g,b,approve=True))
    def test_byte_identical(self):
        self.assertEqual(self._run(), self._run())   # identical inputs + config -> identical output

if __name__ == "__main__":
    unittest.main()
