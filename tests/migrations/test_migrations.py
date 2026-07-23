# Verifies: F-08-01, NFR-005 (versioned migrations: init, legacy adoption, idempotency, ordering,
# transactional rollback, never-reset, Decimal-as-text preservation).
import os
import sqlite3
import tempfile
import unittest

from finsight.infrastructure.migrations.runner import (
    run_migrations, current_version, applied_versions, MigrationError,
)

BASELINE_TABLES = {"cycles", "findings", "rule_runs", "audit", "ingested_files", "config"}


class _FixedClock:
    def now(self):
        return "2026-07-17T00:00:00Z"


def _make_legacy_db(path):
    """A PRE-migration database: baseline tables + data, but NO schema_migrations table."""
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE cycles(cycle_id TEXT PRIMARY KEY, month TEXT, year TEXT, state TEXT)")
    c.execute("CREATE TABLE findings(id TEXT PRIMARY KEY, cycle_id TEXT, rule_id TEXT, severity TEXT, "
              "period TEXT, account TEXT, finding_type TEXT, evidence TEXT, source_refs TEXT, state TEXT)")
    c.execute("CREATE TABLE rule_runs(run_id TEXT PRIMARY KEY, cycle_id TEXT, ruleset_version TEXT, "
              "config_version TEXT, input_fingerprint TEXT, finding_count INTEGER)")
    c.execute("CREATE TABLE audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, cycle_id TEXT, action TEXT, "
              "actor TEXT, ts TEXT, detail TEXT)")
    c.execute("CREATE TABLE ingested_files(cycle_id TEXT, doc_type TEXT, name TEXT, fingerprint TEXT, "
              "size INTEGER, ts TEXT, actor TEXT, period TEXT, PRIMARY KEY(cycle_id, doc_type))")
    c.execute("CREATE TABLE config(version TEXT PRIMARY KEY, materiality_pct INTEGER, bands TEXT, "
              "period TEXT, created_ts TEXT)")
    c.execute("INSERT INTO cycles VALUES('2026-05','May','2026','Exported')")
    c.execute("INSERT INTO findings VALUES('F-leg-6100','2026-05','R-BUD-02','High','May 2026','6100',"
              "'over-budget','{\"variance\":\"3000.00\"}','[\"GED!6100\"]','New')")
    c.commit()
    c.close()


class TestMigrations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "fs.db")

    def _tables(self, conn):
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    def test_new_database_initializes_to_head(self):
        conn = sqlite3.connect(self.path)
        applied = run_migrations(conn, clock=_FixedClock())
        self.assertEqual(applied, [1])
        self.assertEqual(current_version(conn), 1)
        self.assertTrue(BASELINE_TABLES.issubset(self._tables(conn)))
        self.assertIn("schema_migrations", self._tables(conn))

    def test_legacy_database_upgrades_without_data_loss(self):
        _make_legacy_db(self.path)
        conn = sqlite3.connect(self.path)
        self.assertNotIn("schema_migrations", self._tables(conn))   # genuinely pre-migration
        applied = run_migrations(conn, clock=_FixedClock())
        self.assertEqual(applied, [1])                              # baseline adopted, recorded once
        self.assertEqual(current_version(conn), 1)
        # data preserved exactly, including Decimal-as-text
        self.assertEqual(conn.execute("SELECT cycle_id,state FROM cycles").fetchone(), ("2026-05", "Exported"))
        evidence = conn.execute("SELECT evidence FROM findings WHERE id='F-leg-6100'").fetchone()[0]
        self.assertIn("3000.00", evidence)

    def test_applied_once_and_not_reapplied(self):
        conn = sqlite3.connect(self.path)
        self.assertEqual(run_migrations(conn), [1])
        self.assertEqual(run_migrations(conn), [])                 # idempotent
        self.assertEqual(applied_versions(conn), [1])
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM schema_migrations WHERE version=1").fetchone()[0], 1)

    def test_repeated_startup_does_not_reapply(self):
        # Simulate repeated application startup on the same DB file.
        for _ in range(3):
            conn = sqlite3.connect(self.path)
            run_migrations(conn)
            conn.close()
        conn = sqlite3.connect(self.path)
        self.assertEqual(applied_versions(conn), [1])

    def test_ordering_and_uniqueness_enforced(self):
        conn = sqlite3.connect(self.path)
        with self.assertRaises(MigrationError):
            run_migrations(conn, migrations=[(2, "b", lambda c: None), (1, "a", lambda c: None)])
        with self.assertRaises(MigrationError):
            run_migrations(conn, migrations=[(1, "a", lambda c: None), (1, "dup", lambda c: None)])

    def test_failed_migration_rolls_back_and_records_nothing(self):
        conn = sqlite3.connect(self.path)
        run_migrations(conn)  # baseline -> v1

        def bad_up(c):
            c.execute("CREATE TABLE will_rollback(x)")
            raise RuntimeError("boom")

        with self.assertRaises(MigrationError):
            run_migrations(conn, migrations=[(1, "baseline", lambda c: None), (2, "bad", bad_up)])
        self.assertEqual(current_version(conn), 1)                 # v2 not recorded
        self.assertNotIn("will_rollback", self._tables(conn))      # its DDL rolled back

    def test_never_resets_existing_database(self):
        conn = sqlite3.connect(self.path)
        run_migrations(conn)
        conn.execute("INSERT INTO cycles VALUES('c1','Jan','2026','Created')")
        conn.commit()
        run_migrations(conn)  # re-run must not drop/recreate populated tables
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM cycles").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
