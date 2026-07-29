"""Backfill exact qualification, lineage, and baseline guards for governance."""
from __future__ import annotations

import sqlite3


VERSION = 10
NAME = "protected_core_governance_integrity"


def up(conn: sqlite3.Connection) -> None:
    """Install fail-closed guards even when migration 0009 already ran."""

    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_protected_request_exact_qualification "
        "BEFORE INSERT ON v2_protected_change_requests "
        "FOR EACH ROW WHEN NOT EXISTS("
        "SELECT 1 FROM v2_protected_candidate_tests t "
        "WHERE t.test_id=NEW.test_id "
        "AND t.rule_id=NEW.rule_id "
        "AND t.rule_version=NEW.candidate_version "
        "AND t.evidence_context_hash=NEW.evidence_context_hash "
        "AND t.status='COMPLETE') "
        "BEGIN SELECT RAISE(ABORT,'protected request qualification mismatch'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_protected_request_revision_lineage "
        "BEFORE INSERT ON v2_protected_change_requests "
        "FOR EACH ROW WHEN NEW.prior_request_id IS NOT NULL AND NOT EXISTS("
        "SELECT 1 FROM v2_protected_change_requests p "
        "JOIN v2_protected_change_decisions d "
        "ON d.request_id=p.request_id "
        "WHERE p.request_id=NEW.prior_request_id "
        "AND p.rule_id=NEW.rule_id) "
        "BEGIN SELECT RAISE(ABORT,'protected revision lineage mismatch'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_v2_protected_activation_current_head "
        "BEFORE INSERT ON v2_protected_change_activations "
        "FOR EACH ROW WHEN NEW.prior_baseline_id <> COALESCE(("
        "SELECT resulting_baseline_id FROM v2_protected_change_activations "
        "ORDER BY rowid DESC LIMIT 1),'FINSIGHT-CORE-2.0') "
        "BEGIN SELECT RAISE(ABORT,'protected activation predecessor mismatch'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_v2_protected_activation_exact_baseline "
        "BEFORE INSERT ON v2_protected_change_activations "
        "FOR EACH ROW WHEN "
        "NEW.resulting_baseline_id=NEW.prior_baseline_id OR "
        "(SELECT COUNT(*) FROM v2_core_rule_set_members "
        "WHERE rule_set_id=NEW.resulting_baseline_id)<>5 OR "
        "(SELECT COUNT(*) FROM v2_core_rule_set_members "
        "WHERE rule_set_id=NEW.resulting_baseline_id "
        "AND rule_id IN ('CORE-01','CORE-02','CORE-03','CORE-04','CORE-05'))<>5 OR "
        "NOT EXISTS(SELECT 1 FROM v2_core_rule_set_members "
        "WHERE rule_set_id=NEW.resulting_baseline_id "
        "AND rule_id=NEW.activated_rule_id "
        "AND rule_version=NEW.activated_rule_version) "
        "BEGIN SELECT RAISE(ABORT,'protected activation baseline mismatch'); END"
    )
