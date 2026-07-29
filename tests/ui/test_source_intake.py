"""Workflow 2 desktop UI tests for Upload & Extraction.

The tests use the approved synthetic Budget and GED reports end to end and
exercise only Workflow 2 presentation and navigation.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel

from finsight.delivery.desktop.components import ReviewProgress
from finsight.domain.review_management import ReviewStatus
from finsight.domain.source_intake import IntakeGateStatus, SourceRole


pytestmark = pytest.mark.ui

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE_ROOT = (
    _REPOSITORY_ROOT
    / "initiatives"
    / "configurable-rule-engine-v2"
    / "fixtures"
)
_BUDGET = _FIXTURE_ROOT / "Sample_Budget_Report.xlsx"
_GED = _FIXTURE_ROOT / "Sample_GED_Report.xlsx"
_BUDGET_SHA256 = (
    "bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14"
)
_GED_SHA256 = (
    "2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c"
)


def _create_may_review_and_open_intake(window, qtbot):
    management = window.view("review_management")
    management.show_create()
    management._month.setCurrentIndex(management._month.findData(5))
    management._year.setText("2026")
    qtbot.mouseClick(
        management._create_submit, Qt.MouseButton.LeftButton
    )
    assert management.current_screen() == "review_workspace"
    qtbot.mouseClick(
        management._review_continue, Qt.MouseButton.LeftButton
    )
    intake = window.view("source_intake")
    assert window.current_view_key() == "upload_extraction"
    return management.current_review_id(), intake


def _select_approved_pair(intake, qtbot):
    intake.select_source_path(SourceRole.BUDGET, str(_BUDGET))
    qtbot.waitUntil(lambda: intake._budget is not None, timeout=20_000)
    intake.select_source_path(SourceRole.GED, str(_GED))
    qtbot.waitUntil(lambda: intake._ged is not None, timeout=20_000)
    qtbot.waitUntil(lambda: intake.current_pair() is not None, timeout=5_000)


def _save_pair(intake, qtbot):
    assert intake._save_button.isEnabled()
    qtbot.mouseClick(intake._save_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: intake.window().current_view_key() == "verify_data",
        timeout=20_000,
    )


def test_upload_surface_uses_desktop_shell_two_cards_and_step_three(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.resize(1180, 720)
    window.show()

    _review_id, intake = _create_may_review_and_open_intake(window, qtbot)
    qtbot.waitUntil(intake.source_cards_side_by_side)

    progress = intake.findChild(ReviewProgress)
    assert progress is not None
    assert "Create complete" in progress.accessibleDescription()
    assert "Upload current" in progress.accessibleDescription()
    assert intake._upload_progress.isVisibleTo(intake)
    assert intake._home_nav.isVisibleTo(intake)
    assert intake._shell_crumb.isVisibleTo(intake)
    assert intake._shell_crumb.text() == "Upload & Extraction"
    assert intake._ask_fin_button.isVisibleTo(intake)
    assert intake._ask_fin_button.isEnabled()
    assert "does not make financial validation decisions" in (
        intake._ask_fin_button.accessibleDescription()
    )
    assert intake._budget_card.y() == intake._ged_card.y()
    assert intake._budget_card.x() < intake._ged_card.x()
    assert intake._budget_card.choose.text() == "Select .xlsx File"
    assert intake._ged_card.choose.text() == "Select .xlsx File"
    assert intake._pair_message.text() == (
        "Select both approved .xlsx reports to continue."
    )


def test_real_synthetic_pair_shows_status_metadata_fingerprints_and_counts(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.resize(1180, 720)
    window.show()
    review_id, intake = _create_may_review_and_open_intake(window, qtbot)

    _select_approved_pair(intake, qtbot)

    assert intake._budget_card.status.text() == "Compatible"
    assert intake._ged_card.status.text() == "Compatible"
    assert intake._budget_card.file_name.text() == "Sample_Budget_Report.xlsx"
    assert intake._ged_card.file_name.text() == "Sample_GED_Report.xlsx"
    assert intake._budget_card.upload_status.text() == "Selected"
    assert intake._ged_card.upload_status.text() == "Selected"
    assert intake._budget_card.extraction_status.text() == "Extraction complete"
    assert intake._ged_card.extraction_status.text() == "Extraction complete"
    assert intake._budget_card.worksheet.text() == "Original Budget · Compatible"
    assert intake._ged_card.worksheet.text() == "GED · Compatible"
    assert intake._budget_card.department_name.text() == (
        "Applications Enginee (confirmed from matched GED report)"
    )
    assert intake._ged_card.department_name.text() == "Applications Enginee"
    assert intake._budget_card.department.text() == "00-0245"
    assert intake._ged_card.department.text() == "00-0245"
    assert intake._budget_card.period.text() == (
        "Workspace assigned / no source period"
    )
    assert intake._ged_card.period.text() == "May 2026"
    assert intake._budget_card.record_count.text() == "71 Budget records"
    assert intake._ged_card.record_count.text() == "258 GED transactions"
    assert intake._budget_card.fingerprint.accessibleDescription() == (
        f"Full SHA-256 {_BUDGET_SHA256}"
    )
    assert intake._ged_card.fingerprint.accessibleDescription() == (
        f"Full SHA-256 {_GED_SHA256}"
    )
    assert intake.current_pair().gate_status is IntakeGateStatus.READY
    assert "metadata matches" in intake._pair_message.text()

    _save_pair(intake, qtbot)

    financial = intake.window().view("financial_review")
    assert len(financial.current_dataset().budget_details) == 71
    assert len(financial.current_dataset().ged_transactions) == 258
    assert financial._verify_progress.accessibleDescription().startswith(
        "Create complete; Upload complete; Verify Data current"
    )
    assert intake.current_review().status is ReviewStatus.DATA_UPLOADED
    assert (
        intake._c.source_intake_summary(review_id).pair.gate_status
        is IntakeGateStatus.READY
    )


def test_saved_source_summary_reopens_after_application_window_recreation(
    window_factory, empty_db, qtbot
):
    first = window_factory(empty_db)
    first.resize(1180, 720)
    first.show()
    review_id, intake = _create_may_review_and_open_intake(first, qtbot)
    _select_approved_pair(intake, qtbot)
    _save_pair(intake, qtbot)
    first.close()

    reopened = window_factory(empty_db)
    reopened.resize(1180, 720)
    reopened.show()
    management = reopened.view("review_management")
    management.show_past()
    assert management.past_review_ids() == [review_id]
    qtbot.mouseClick(
        management._past_cards[0].open_button, Qt.MouseButton.LeftButton
    )
    qtbot.waitUntil(
        lambda: reopened.current_view_key() == "verify_data",
        timeout=20_000,
    )
    restored = reopened.view("financial_review")
    assert len(restored.current_dataset().budget_details) == 71
    assert len(restored.current_dataset().ged_transactions) == 258
    assert restored._context.text().endswith("Data Uploaded")


def test_incompatible_file_has_clear_action_status_and_does_not_save(
    window_factory, empty_db, qtbot, tmp_path
):
    invalid = tmp_path / "Budget_Report.xls"
    shutil.copyfile(_BUDGET, invalid)
    window = window_factory(empty_db)
    window.resize(1180, 720)
    window.show()
    review_id, intake = _create_may_review_and_open_intake(window, qtbot)

    intake.select_source_path(SourceRole.BUDGET, str(invalid))
    qtbot.waitUntil(lambda: intake._budget is not None, timeout=20_000)
    intake.select_source_path(SourceRole.GED, str(_GED))
    qtbot.waitUntil(lambda: intake._ged is not None, timeout=20_000)

    assert intake._budget_card.status.text() == "Action required"
    assert intake._budget_card.issues.isVisible()
    assert "Only an .xlsx workbook" in intake._budget_card.issues.text()
    assert "FS-WRK-001" not in intake._budget_card.issues.text()
    assert "Correlation ID:" not in intake._budget_card.issues.text()
    assert not intake._save_button.isEnabled()
    assert "compatibility issue" in intake._pair_message.text()
    assert intake.current_pair() is None
    assert intake.current_review().status is ReviewStatus.DRAFT
    assert intake._c.source_intake_summary(review_id) is None


def test_ready_pair_advances_to_mandatory_verify_data(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.resize(1180, 720)
    window.show()
    _review_id, intake = _create_may_review_and_open_intake(window, qtbot)
    _select_approved_pair(intake, qtbot)
    _save_pair(intake, qtbot)

    financial = intake.window().view("financial_review")
    assert intake.window().current_view_key() == "verify_data"
    assert financial._data_tabs.count() == 2
    assert financial._data_tabs.tabText(0) == "Budget Data"
    assert financial._data_tabs.tabText(1) == "GED Data"
    assert not financial._budget_table.verticalHeader().isVisible()
    assert not financial._ged_table.verticalHeader().isVisible()
    assert (
        financial._budget_proxy.headerData(
            0, Qt.Orientation.Horizontal
        )
        == "Source Row"
    )
    assert financial._budget_proxy.index(0, 0).data() == "2"
    assert any(
        financial._ged_proxy.index(row, 0).data() == "8"
        for row in range(financial._ged_proxy.rowCount())
    )
    assert financial._data_tabs.minimumHeight() == 430
    assert not financial._source_details.isEnabled()
    assert "Select an extracted data value" in (
        financial._source_details.accessibleDescription()
    )
    assert "Selected Cell Evidence" not in [
        label.text()
        for label in financial._stack.widget(financial.VERIFY).findChildren(
            QLabel
        )
        if label.isVisibleTo(financial)
    ]
    assert not financial._continue_validation.isEnabled()


def test_verify_data_source_details_are_plain_language_and_on_demand(
    window_factory, empty_db, qtbot, monkeypatch
):
    window = window_factory(empty_db)
    window.resize(1280, 900)
    window.show()
    _review_id, intake = _create_may_review_and_open_intake(window, qtbot)
    _select_approved_pair(intake, qtbot)
    _save_pair(intake, qtbot)
    financial = window.view("financial_review")
    captured = []

    def capture_dialog(dialog):
        captured.append(dialog)
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(QDialog, "exec", capture_dialog)

    for tab_index, table, header, expected in (
        (
            0,
            financial._budget_table,
            "Account Name",
            (
                "Sample_Budget_Report.xlsx",
                "Original Budget",
                "2",
                "Account Name (column B)",
                "Promotional Items",
            ),
        ),
        (
            1,
            financial._ged_table,
            "Account Name",
            (
                "Sample_GED_Report.xlsx",
                "GED",
                "8",
                "Account Name (column D)",
                "Promotional Items",
            ),
        ),
    ):
        financial._data_tabs.setCurrentIndex(tab_index)
        model = table.model()
        column = next(
            index
            for index in range(model.columnCount())
            if model.headerData(index, Qt.Orientation.Horizontal) == header
        )
        table.setCurrentIndex(model.index(0, column))
        assert financial._source_details.isEnabled()
        qtbot.mouseClick(
            financial._source_details, Qt.MouseButton.LeftButton
        )

        dialog = captured[-1]
        labels = [
            label.text()
            for label in dialog.findChildren(QLabel)
            if label.objectName() != "SourceTechnicalDetails"
        ]
        copy = "\n".join(labels)
        for value in (
            "Source file",
            "Worksheet",
            "Source row",
            "Field / column",
            "Original value",
            "Current reviewed value",
            "Edited status",
            "Not edited",
            *expected,
        ):
            assert value in copy

        technical = dialog.findChild(QLabel, "SourceTechnicalDetails")
        toggle = dialog.findChild(
            type(financial._source_details),
            "SourceTechnicalDetailsToggle",
        )
        assert technical.isHidden()
        assert not toggle.isChecked()
        assert "BUDGET:Original Budget:2" not in copy
        assert "Original Budget!B2" not in copy
        toggle.click()
        assert not technical.isHidden()
        assert toggle.accessibleName() == "Hide technical details"
