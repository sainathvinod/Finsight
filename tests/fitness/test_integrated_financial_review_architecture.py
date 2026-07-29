"""Architecture guards for the integrated deterministic financial-review path."""
from pathlib import Path


def _source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_pure_financial_engine_has_no_ui_io_persistence_or_ai_dependency():
    source = _source("src/finsight/domain/financial_validation.py")
    forbidden = (
        "PySide6",
        "sqlite3",
        "openpyxl",
        "finsight.infrastructure",
        "finsight.application.ai",
        "QWidget",
    )
    assert [token for token in forbidden if token in source] == []


def test_result_consumers_do_not_import_or_invoke_engine_evaluators():
    sources = "\n".join(
        _source(path)
        for path in (
            "src/finsight/delivery/desktop/views/financial_review_view.py",
            "src/finsight/delivery/desktop/views/review_management_view.py",
            "src/finsight/delivery/desktop/views/source_intake_view.py",
        )
    )
    forbidden = (
        "CoreFinancialValidationEngine",
        "domain.financial_validation",
        "_actual_not_over_budget",
        "_valid_mapping",
        "_exact_duplicates",
        "_required_fields",
        "_atd_reconciliation",
    )
    assert [token for token in forbidden if token in sources] == []


def test_controller_loads_governed_manifest_before_background_evaluation():
    source = _source(
        "src/finsight/delivery/desktop/controllers/app_controller.py"
    )
    manifest_load = source.index(
        "manifest = self._s.financial_review.rule_manifest(review_id)"
    )
    worker_definition = source.index("def work():", manifest_load)
    pure_dispatch = source.index(
        "evaluate_manifest(dataset, manifest)",
        worker_definition,
    )
    assert manifest_load < worker_definition < pure_dispatch
