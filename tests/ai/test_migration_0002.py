import os
import sqlite3
import tempfile
import unittest

from finsight.infrastructure.migrations.runner import run_migrations, current_version
from finsight.infrastructure.migrations import m0001_baseline
from finsight.infrastructure.persistence import Dal, FindingRepoSqlite
from tests.ai.support import make, seed_review

AI_TABLES = {"ai_user_preferences", "ai_conversations", "ai_messages", "ai_review_memory", "ai_interactions"}


class TestMigration0002(unittest.TestCase):
    def _tables(self, conn):
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    def _db(self):
        return os.path.join(tempfile.mkdtemp(), "fs.db")

    def test_fresh_creates_ai_tables(self):
        conn = sqlite3.connect(self._db())
        run_migrations(conn)
        self.assertTrue(AI_TABLES.issubset(self._tables(conn)))
        self.assertEqual(current_version(conn), 3)   # + lifecycle migration 0003

    def test_upgrade_from_0001_preserves_data(self):
        conn = sqlite3.connect(self._db())
        run_migrations(conn, migrations=[(1, "baseline", m0001_baseline.up)])   # v1 only
        self.assertEqual(current_version(conn), 1)
        conn.execute("INSERT INTO cycles VALUES('c1','May','2026','Exported')")  # 4-col v1 schema
        conn.commit()
        applied = run_migrations(conn)   # default MIGRATIONS -> v2 and v3 pending
        self.assertEqual(applied, [2, 3])
        self.assertTrue(AI_TABLES.issubset(self._tables(conn)))
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM cycles").fetchone()[0], 1)

    def test_idempotent(self):
        conn = sqlite3.connect(self._db())
        run_migrations(conn)
        self.assertEqual(run_migrations(conn), [])

    def test_foreign_key_cascade_deletes_messages(self):
        conn = sqlite3.connect(self._db())
        conn.execute("PRAGMA foreign_keys=ON")
        run_migrations(conn)
        conn.execute("INSERT INTO ai_conversations VALUES('cv','u','2026-07','t','ts','ts','keep')")
        conn.execute("INSERT INTO ai_messages VALUES('m1','cv','user','hi',1,'ts')")
        conn.commit()
        conn.execute("DELETE FROM ai_conversations WHERE conversation_id='cv'")
        conn.commit()
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM ai_messages").fetchone()[0], 0)

    def test_deterministic_data_unchanged(self):
        tmp, container, _ai = make()
        seed_review(container, tmp, "2026-07")
        before = container.finding_repo.list("2026-07")
        after = FindingRepoSqlite(Dal(os.path.join(tmp, "fs.db"))).list("2026-07")  # re-open; migrations re-run
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
