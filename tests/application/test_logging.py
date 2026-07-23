# Verifies: logging initializes with rotation, fails safely, and does not log raw financial rows.
import logging
import os
import tempfile
import unittest

import finsight.diagnostics as diag
from finsight.diagnostics import configure_logging, get_logger
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app


def _reset_logging():
    diag._configured = False
    logging.getLogger("finsight").handlers = []


class TestLogging(unittest.TestCase):
    def setUp(self):
        _reset_logging()

    def tearDown(self):
        _reset_logging()

    def test_initializes_with_rotation(self):
        logdir = os.path.join(tempfile.mkdtemp(), "logs")
        configure_logging(level="INFO", log_dir=logdir)
        get_logger("test").info("event cid=X")
        self.assertTrue(os.path.exists(os.path.join(logdir, "finsight.log")))
        rotators = [h for h in logging.getLogger("finsight").handlers
                    if h.__class__.__name__ == "RotatingFileHandler"]
        self.assertTrue(rotators)
        self.assertGreater(rotators[0].maxBytes, 0)
        self.assertGreater(rotators[0].backupCount, 0)

    def test_failure_does_not_crash(self):
        # parent path is a regular file -> makedirs raises -> configure_logging swallows it
        blocker = os.path.join(tempfile.mkdtemp(), "afile")
        open(blocker, "w").close()
        configure_logging(level="INFO", log_dir=os.path.join(blocker, "logs"))  # must not raise
        self.assertFalse(diag._configured)   # did not complete, but the app can still launch

    def test_does_not_log_raw_financial_rows(self):
        tmp = tempfile.mkdtemp()
        logdir = os.path.join(tmp, "logs")
        configure_logging(level="INFO", log_dir=logdir)
        ged = os.path.join(tmp, "g.xlsx")
        bud = os.path.join(tmp, "b.xlsx")
        build_synthetic_ged(ged)
        build_synthetic_budget(bud)
        app = build_app(os.path.join(tmp, "fs.db"), FixedClock())
        app.orch.run_review("2026-07", "July", "2026", ged, bud, approve=True)
        content = open(os.path.join(logdir, "finsight.log"), encoding="utf-8").read()
        self.assertNotIn("Acme-Synth", content)   # vendor row content never logged
        self.assertNotIn("13000", content)         # raw amount never logged


if __name__ == "__main__":
    unittest.main()
