# Verifies: migration 0004 (extraction_overrides) — additive, idempotent, non-destructive projection.
import sqlite3

import pytest

from finsight.infrastructure.migrations.runner import run_migrations, current_version


def _head():
    conn = sqlite3.connect(":memory:")
    run_migrations(conn)
    return conn


def _seed(conn):
    conn.execute("INSERT INTO cycles(cycle_id, month, year, state) VALUES('A','July','2026','Processed')")
    conn.execute(
        "INSERT INTO extraction_overrides(cycle_id, document_type, source_ref, field, original_value, "
        "current_value, actor, ts, version, reverted, reason) "
        "VALUES('A','GED','GED!R5','amount','8000','9000','u','t',1,0,'fix')")


def test_head_version_is_4():
    assert current_version(_head()) == 4


def test_overrides_table_exists():
    conn = _head()
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "extraction_overrides" in tables


def test_overrides_are_non_destructive_no_delete():
    conn = _head(); _seed(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM extraction_overrides WHERE cycle_id='A'")


def test_original_value_is_immutable():
    conn = _head(); _seed(conn)
    # current_value / reverted / version may change; original_value may not.
    conn.execute("UPDATE extraction_overrides SET current_value='1' WHERE cycle_id='A'")   # ok
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE extraction_overrides SET original_value='0' WHERE cycle_id='A'")


def test_migration_is_idempotent():
    conn = _head()
    assert run_migrations(conn) == []          # re-running applies nothing
