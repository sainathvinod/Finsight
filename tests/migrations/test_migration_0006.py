from finsight.infrastructure.migrations import m0006_v2_integrated_review
from finsight.infrastructure.persistence import Dal
from finsight.infrastructure.secure_store import TestEnvironmentStoreKeyProvider


def test_migration_0006_seeds_protected_core_catalog(tmp_path):
    dal = Dal(
        str(tmp_path / "finsight.db"),
        key_provider=TestEnvironmentStoreKeyProvider(),
    )
    try:
        rules = dal.conn.execute(
            "SELECT rule_id,version,baseline_status FROM v2_core_rule_versions "
            "WHERE version='1.0.0' ORDER BY rule_id"
        ).fetchall()
        members = dal.conn.execute(
            "SELECT rule_id FROM v2_core_rule_set_members "
            "WHERE rule_set_id='FINSIGHT-CORE-1.0' ORDER BY ordinal"
        ).fetchall()
        assert rules == [
            (f"CORE-0{number}", "1.0.0", "PROTECTED_BASELINE")
            for number in range(1, 6)
        ]
        assert members == [(f"CORE-0{number}",) for number in range(1, 6)]
        assert m0006_v2_integrated_review.VERSION == 6
    finally:
        dal.conn.close()
