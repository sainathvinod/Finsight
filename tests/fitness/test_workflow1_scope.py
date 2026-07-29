# Verifies: Workflow 1 use cases remain independent of later financial workflows.
from pathlib import Path


def test_review_management_application_has_no_workflow2_plus_dependencies():
    source = Path("src/finsight/application/review_management.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "ExcelReader",
        "ExtractionPipeline",
        "RulesEngine",
        "Finding",
        "Analytics",
        "AskFin",
        "ReportingService",
        "ExportService",
    )
    assert [token for token in forbidden if token in source] == []


def test_review_management_view_contains_no_evaluator_or_storage_logic():
    source = Path(
        "src/finsight/delivery/desktop/views/review_management_view.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "sqlite3",
        "finsight.infrastructure",
        "openpyxl",
        "pandas",
        "RulesEngine",
    )
    assert [token for token in forbidden if token in source] == []
