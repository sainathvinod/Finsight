import pytest

from finsight.infrastructure.migrations import (
    m0007_configurable_rules_and_reanalysis,
)
from finsight.infrastructure.persistence import Dal
from finsight.infrastructure.secure_store import TestEnvironmentStoreKeyProvider


def test_migration_0007_preserves_v1_and_seeds_named_successor(tmp_path):
    dal = Dal(
        str(tmp_path / "finsight.db"),
        key_provider=TestEnvironmentStoreKeyProvider(),
    )
    try:
        v1 = dal.conn.execute(
            "SELECT COUNT(*) FROM v2_core_rule_versions WHERE version='1.0.0'"
        ).fetchone()[0]
        v2 = dal.conn.execute(
            "SELECT m.rule_id,r.name,r.version FROM v2_core_rule_set_members m "
            "JOIN v2_core_rule_versions r "
            "ON r.rule_id=m.rule_id AND r.version=m.rule_version "
            "WHERE m.rule_set_id='FINSIGHT-CORE-2.0' ORDER BY m.ordinal"
        ).fetchall()
        assert v1 == 5
        assert v2 == [
            ("CORE-05", "Budget-to-GED Reconciliation", "2.0.0"),
            ("CORE-01", "Budget Overrun", "2.0.0"),
            ("CORE-02", "Valid Account Coding", "2.0.0"),
            ("CORE-04", "Complete and Correct Data", "2.0.0"),
            ("CORE-03", "Duplicate Transactions", "2.0.0"),
        ]
        assert m0007_configurable_rules_and_reanalysis.VERSION == 7
    finally:
        dal.conn.close()


def test_configurable_rule_versions_are_append_only(tmp_path):
    dal = Dal(
        str(tmp_path / "finsight.db"),
        key_provider=TestEnvironmentStoreKeyProvider(),
    )
    try:
        with pytest.raises(Exception, match="append-only"):
            dal.conn.execute(
                "UPDATE v2_rule_definition_versions SET name='Changed' "
                "WHERE rule_id='CORE-01' AND version='2.0.0'"
            )
    finally:
        dal.conn.close()
