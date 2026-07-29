import json
import subprocess
import sys


def test_independent_ooxml_oracle_matches_the_approved_control_matrix():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/verify_stage1_financial_oracle.py",
            "--compact",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    oracle = json.loads(completed.stdout)
    assert oracle["oracle"]["implementation_dependency"] == "None"
    assert oracle["oracle"]["overall_status"] == "PASS"
    assert all(
        item["status"] == "PASS"
        for matrix_name in (
            "totals_control_matrix",
            "row_control_matrix",
            "known_issue_control_matrix",
            "rule_control_matrix",
        )
        for item in oracle[matrix_name].values()
    )
    assert oracle["financial_control_report"]["formula_failures"] == []
    assert oracle["financial_control_report"]["missing_amount_rows"] == [87]
