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
from finsight.infrastructure.migrations import m0003_review_lifecycle
from finsight.infrastructure.migrations import m0004_v2_review_management
from finsight.infrastructure.migrations import m0005_v2_source_intake
from finsight.infrastructure.migrations import m0006_v2_integrated_review
from finsight.infrastructure.migrations import m0007_configurable_rules_and_reanalysis
from finsight.infrastructure.migrations import m0008_review_disposal
from finsight.infrastructure.migrations import m0009_protected_core_governance
from finsight.infrastructure.migrations import (
    m0010_protected_core_governance_integrity,
)
from finsight.infrastructure.migrations import (
    m0011_protected_request_baseline_binding,
)
from finsight.infrastructure.migrations import (
    m0012_workspace_baseline_upgrade_governance,
)
from finsight.infrastructure.migrations import (
    m0013_finding_explanations_and_review_status,
)
from finsight.infrastructure.migrations import m0014_private_ask_fin_audit
from finsight.infrastructure.migrations import (
    m0015_validation_rule_set_confirmation,
)
from finsight.infrastructure.migrations import m0016_validation_run_identity

Migration = Tuple[int, str, Callable[[sqlite3.Connection], None]]


class MigrationError(RuntimeError):
    """Raised when a migration cannot be applied. The failed migration is rolled back and not recorded."""


# Ordered registry. Append new migrations; never renumber, rewrite, or remove an applied migration.
MIGRATIONS: List[Migration] = [
    (m0001_baseline.VERSION, m0001_baseline.NAME, m0001_baseline.up),
    (m0002_ai_platform.VERSION, m0002_ai_platform.NAME, m0002_ai_platform.up),
    (m0003_review_lifecycle.VERSION, m0003_review_lifecycle.NAME, m0003_review_lifecycle.up),
    (
        m0004_v2_review_management.VERSION,
        m0004_v2_review_management.NAME,
        m0004_v2_review_management.up,
    ),
    (
        m0005_v2_source_intake.VERSION,
        m0005_v2_source_intake.NAME,
        m0005_v2_source_intake.up,
    ),
    (
        m0006_v2_integrated_review.VERSION,
        m0006_v2_integrated_review.NAME,
        m0006_v2_integrated_review.up,
    ),
    (
        m0007_configurable_rules_and_reanalysis.VERSION,
        m0007_configurable_rules_and_reanalysis.NAME,
        m0007_configurable_rules_and_reanalysis.up,
    ),
    (
        m0008_review_disposal.VERSION,
        m0008_review_disposal.NAME,
        m0008_review_disposal.up,
    ),
    (
        m0009_protected_core_governance.VERSION,
        m0009_protected_core_governance.NAME,
        m0009_protected_core_governance.up,
    ),
    (
        m0010_protected_core_governance_integrity.VERSION,
        m0010_protected_core_governance_integrity.NAME,
        m0010_protected_core_governance_integrity.up,
    ),
    (
        m0011_protected_request_baseline_binding.VERSION,
        m0011_protected_request_baseline_binding.NAME,
        m0011_protected_request_baseline_binding.up,
    ),
    (
        m0012_workspace_baseline_upgrade_governance.VERSION,
        m0012_workspace_baseline_upgrade_governance.NAME,
        m0012_workspace_baseline_upgrade_governance.up,
    ),
    (
        m0013_finding_explanations_and_review_status.VERSION,
        m0013_finding_explanations_and_review_status.NAME,
        m0013_finding_explanations_and_review_status.up,
    ),
    (
        m0014_private_ask_fin_audit.VERSION,
        m0014_private_ask_fin_audit.NAME,
        m0014_private_ask_fin_audit.up,
    ),
    (
        m0015_validation_rule_set_confirmation.VERSION,
        m0015_validation_rule_set_confirmation.NAME,
        m0015_validation_rule_set_confirmation.up,
    ),
    (
        m0016_validation_run_identity.VERSION,
        m0016_validation_run_identity.NAME,
        m0016_validation_run_identity.up,
    ),
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
    # Migration 0008 uses a connection-local SQLite function in guarded delete
    # triggers. Re-register its fail-closed fallback on every reopened database
    # without replacing a governed disposal callback.
    m0008_review_disposal.ensure_disposal_guard_function(conn)
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
