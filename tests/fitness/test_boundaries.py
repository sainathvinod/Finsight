# Verifies: NFR-047, NFR-031 (ADR-002: domain imports nothing outward; DAL-only storage; command-port isolation)
import unittest, os, re

SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src", "finsight")

def _read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()

def imports_of(pkg):
    out = []
    base = os.path.join(SRC, pkg)
    for dp, _, fns in os.walk(base):
        for fn in fns:
            if fn.endswith(".py"):
                txt = _read(os.path.join(dp, fn))
                out += re.findall(r'^\s*(?:from|import)\s+([\w\.]+)', txt, re.M)
    return out

class TestBoundaries(unittest.TestCase):
    def test_domain_imports_nothing_outward(self):
        for mod in imports_of("domain"):
            self.assertFalse(mod.startswith("finsight.application"), mod)
            self.assertFalse(mod.startswith("finsight.infrastructure"), mod)
            self.assertFalse(mod.startswith("finsight.delivery"), mod)
            self.assertNotEqual(mod, "sqlite3")          # domain never touches storage
            self.assertNotEqual(mod, "openpyxl")         # domain never touches a format lib
    def test_only_persistence_imports_sqlite(self):
        for pkg in ("domain","application","delivery"):
            self.assertNotIn("sqlite3", imports_of(pkg), pkg)
    def test_command_factory_isolated(self):
        # delivery must not import the finding factory (creation) — read-only side only
        deliv = _read(os.path.join(SRC,"delivery","__init__.py"))
        self.assertNotIn("make_finding", deliv)
    def test_verification_is_only_factory_importer(self):
        importers = []
        for dp, _, fns in os.walk(SRC):
            for fn in fns:
                if fn.endswith(".py"):
                    p = os.path.join(dp, fn)
                    if "_make_verified_dataset" in _read(p):
                        importers.append(os.path.basename(p))
        # only defined in verified_dataset.py and imported by verification.py
        self.assertEqual(set(importers), {"verified_dataset.py", "verification.py"})

if __name__ == "__main__":
    unittest.main()
