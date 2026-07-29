"""Architecture guards for Upload & Extraction within the integrated MVP."""
from pathlib import Path


def _source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_source_intake_application_has_no_later_workflow_dependencies():
    source = _source("src/finsight/application/source_intake.py")
    forbidden = (
        "RulesEngine",
        "Finding",
        "Analytics",
        "AskFin",
        "ReportingService",
        "ExportService",
        "CorrectionEvent",
        "VerificationService",
    )
    assert [token for token in forbidden if token in source] == []


def test_source_intake_view_contains_no_file_or_storage_implementation():
    source = _source(
        "src/finsight/delivery/desktop/views/source_intake_view.py"
    )
    forbidden = (
        "sqlite3",
        "finsight.infrastructure",
        "openpyxl",
        "hashlib",
        "RulesEngine",
        "ValidationResult",
    )
    assert [token for token in forbidden if token in source] == []


def test_ready_source_pair_enters_the_integrated_financial_review_flow():
    source = _source(
        "src/finsight/delivery/desktop/views/source_intake_view.py"
    )
    assert "financialReviewRequested = Signal(object)" in source
    assert "self.financialReviewRequested.emit(result.review)" in source
