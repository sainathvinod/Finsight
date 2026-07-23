# Verifies: typed composition container; deprecated string-key compatibility; desktop receives
# application services (not repositories); deterministic core imports with no PySide6.
import os
import sys
import subprocess
import tempfile
import unittest

from tests.support import FixedClock
from finsight.app import build_app, build_query_services, Container, AppServices


class TestComposition(unittest.TestCase):
    def _db(self):
        return os.path.join(tempfile.mkdtemp(), "fs.db")

    def test_container_has_typed_fields(self):
        c = build_app(self._db(), FixedClock())
        self.assertIsInstance(c, Container)
        for field in ("dal", "uow", "orch", "cycle_repo", "ingested_repo", "run_repo",
                      "finding_repo", "config_repo", "audit", "config", "clock"):
            self.assertTrue(hasattr(c, field), field)

    def test_string_key_compat_maps_to_attributes(self):
        c = build_app(self._db(), FixedClock())
        self.assertIs(c["orch"], c.orch)
        self.assertIs(c["cycle_repo"], c.cycle_repo)
        self.assertIs(c["audit"], c.audit)

    def test_app_services_expose_workflow_not_repositories(self):
        svc = build_query_services(self._db())
        self.assertIsInstance(svc, AppServices)
        for field in ("reviews", "findings", "audit", "summary", "workflow"):
            self.assertTrue(hasattr(svc, field), field)
        # no repository / dal handed to the UI-facing services object
        for leaked in ("cycle_repo", "finding_repo", "dal", "uow"):
            self.assertFalse(hasattr(svc, leaked), leaked)

    def test_core_import_does_not_load_pyside6(self):
        code = ("import sys; import finsight.app; "
                "assert not any(m == 'PySide6' or m.startswith('PySide6.') for m in sys.modules), 'PySide6 leaked'")
        env = dict(os.environ, PYTHONPATH=os.path.join(os.getcwd(), "src"))
        result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
