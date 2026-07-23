# Implements: F-08-01, NFR-005, NFR-057, ADR-004
# Versioned SQLite migration runner. Transactional per-migration, applied exactly once, in order.
# Safe on new databases (initialize) and on legacy pre-migration databases (adopt without data loss).
# Contains NO UI or business logic; storage concern only.
from __future__ import annotations
import sqlite3
import datetime
from typing import Callable, List, Optional, Sequence, Tuple

from finsight.infrastructure.migrations import m0001_baseline
from finsight.infrastructure.migrations import m0002_ai_platform

Migration = Tuple[int, str, Callable[[sqlite3.Connection], None]]


class MigrationError(RuntimeError):
    """Raised when a migration cannot be applied. The failed migration is rolled back and not recorded."""


# Ordered registry. Append new migrations; never renumber, rewrite, or remove an applied migration.
MIGRATIONS: List[Migration] = [
    (m0001_baseline.VERSION, m0001_baseline.NAME, m0001_baseline.up),
    (m0002_ai_platform.VERSION, m0002_ai_platform.NAME, m0002_ai_platform.up),
]

_META_DDL = (
    "CREATE TABLE IF NOT EXISTS schema_migrations("
    "version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_ts TEXT NOT NULL)"
)


def _iso_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_meta(conn: sqlite3.Connection) -> None:
    conn.execute(_META_DDL)


def applied_versions(conn: sqlite3.Connection) -> List[int]:
    _ensure_meta(conn)
    return [int(r[0]) for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]


def current_version(conn: sqlite3.Connection) -> int:
    _ensure_meta(conn)
    row = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()
    return int(row[0])


def run_migrations(
    conn: sqlite3.Connection,
    migrations: Optional[Sequence[Migration]] = None,
    clock=None,
) -> List[int]:
    """Apply all pending migrations in order. Returns the list of versions applied this call.

    - New database: creates schema_migrations, then applies every migration.
    - Legacy pre-migration database: baseline is idempotent (IF NOT EXISTS), so it adopts the
      existing schema and records version 1 without recreating tables or losing data.
    - Idempotent: already-applied versions are skipped; repeated startup applies nothing.
    - Transactional: each migration + its version record commit together, or roll back together.
    - Never resets or recreates a user database.
    """
    regs = list(MIGRATIONS if migrations is None else migrations)

    versions = [m[0] for m in regs]
    if versions != sorted(versions) or len(set(versions)) != len(versions):
        raise MigrationError("Migrations must have unique, strictly increasing versions: %r" % versions)

    old_isolation = conn.isolation_level
    conn.isolation_level = None  # manual transaction control so DDL is transactional
    applied: List[int] = []
    try:
        already = set(applied_versions(conn))  # also ensures the meta table exists (autocommit)
        for version, name, up in regs:
            if version in already:
                continue
            try:
                conn.execute("BEGIN")
                up(conn)
                conn.execute(
                    "INSERT INTO schema_migrations(version, name, applied_ts) VALUES(?, ?, ?)",
                    (version, name, clock.now() if clock is not None else _iso_now()),
                )
                conn.execute("COMMIT")
            except Exception as exc:  # fail safely: roll back this migration, record nothing
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise MigrationError(
                    "Migration %d (%s) failed and was rolled back: %s" % (version, name, exc)
                ) from exc
            applied.append(version)
    finally:
        conn.isolation_level = old_isolation  # restore the app's transaction model for the UnitOfWork
    return applied
