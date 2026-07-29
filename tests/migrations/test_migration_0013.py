from __future__ import annotations

import sqlite3

from finsight.infrastructure.migrations import (
    m0001_baseline,
    m0002_ai_platform,
    m0003_review_lifecycle,
    m0004_v2_review_management,
    m0005_v2_source_intake,
    m0006_v2_integrated_review,
    m0007_configurable_rules_and_reanalysis,
    m0008_review_disposal,
    m0009_protected_core_governance,
    m0010_protected_core_governance_integrity,
    m0011_protected_request_baseline_binding,
    m0012_workspace_baseline_upgrade_governance,
    m0013_finding_explanations_and_review_status,
)


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    for migration in (
        m0001_baseline,
        m0002_ai_platform,
        m0003_review_lifecycle,
        m0004_v2_review_management,
        m0005_v2_source_intake,
        m0006_v2_integrated_review,
        m0007_configurable_rules_and_reanalysis,
        m0008_review_disposal,
        m0009_protected_core_governance,
        m0010_protected_core_governance_integrity,
        m0011_protected_request_baseline_binding,
        m0012_workspace_baseline_upgrade_governance,
        m0013_finding_explanations_and_review_status,
    ):
        migration.up(connection)
    return connection


def test_migration_0013_creates_append_only_explanation_and_review_ledgers():
    connection = _connection()
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert {
        "v2_finding_explanation_projections",
        "v2_finding_review_status_events",
        "v2_leadership_summary_projections",
    }.issubset(tables)
    triggers = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    for table in (
        "v2_finding_explanation_projections",
        "v2_finding_review_status_events",
        "v2_leadership_summary_projections",
    ):
        assert f"trg_{table}_no_update" in triggers
        assert f"trg_{table}_no_delete" in triggers
    assert {
        "trg_v2_finding_explanation_exact_sealed_finding",
        "trg_v2_finding_status_exact_review_run",
        "trg_v2_finding_status_initial_state",
        "trg_v2_finding_status_contiguous_history",
    }.issubset(triggers)
    status_values = connection.execute(
        "SELECT sql FROM sqlite_master "
        "WHERE type='table' AND name='v2_finding_review_status_events'"
    ).fetchone()[0]
    for value in ("New", "Acknowledged", "In Review", "Resolved", "Dismissed"):
        assert value in status_values
    assert m0013_finding_explanations_and_review_status.VERSION == 13
