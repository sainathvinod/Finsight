from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QInputDialog,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableView,
    QTableWidget,
    QWidget,
)

from finsight.domain.source_intake import SourceRole


pytestmark = pytest.mark.ui

ROOT = Path(__file__).resolve().parents[2]
BUDGET = ROOT / "initiatives/configurable-rule-engine-v2/fixtures/Sample_Budget_Report.xlsx"
GED = ROOT / "initiatives/configurable-rule-engine-v2/fixtures/Sample_GED_Report.xlsx"


def _projection_table(container, first_header: str, *, columns: int | None = None):
    return next(
        table
        for table in container.findChildren(QTableView)
        if table.model() is not None
        and table.model().headerData(0, Qt.Orientation.Horizontal) == first_header
        and (columns is None or table.model().columnCount() == columns)
    )


def test_guided_mvp_runs_to_completion_and_reopens_read_only(
    window_factory, empty_db, qtbot, monkeypatch
):
    window = window_factory(empty_db)
    window.resize(1100, 720)
    window.show()
    management = window.view("review_management")
    management.show_create()
    management._month.setCurrentIndex(management._month.findData(5))
    management._year.setText("2026")
    qtbot.mouseClick(management._create_submit, Qt.MouseButton.LeftButton)

    assert window.current_view_key() == "upload_extraction"
    intake = window.view("source_intake")
    intake.select_source_path(SourceRole.BUDGET, str(BUDGET))
    qtbot.waitUntil(lambda: intake._budget is not None, timeout=20_000)
    intake.select_source_path(SourceRole.GED, str(GED))
    qtbot.waitUntil(lambda: intake._ged is not None, timeout=20_000)
    qtbot.waitUntil(lambda: intake.current_pair() is not None, timeout=5_000)
    qtbot.mouseClick(intake._save_button, Qt.MouseButton.LeftButton)

    qtbot.waitUntil(
        lambda: window.current_view_key() == "verify_data", timeout=20_000
    )
    financial = window.view("financial_review")
    assert len(financial.current_dataset().budget_details) == 71
    assert len(financial.current_dataset().ged_transactions) == 258
    assert financial._budget_model.rowCount() == 94
    assert financial._ged_model.rowCount() == 292
    assert not financial._continue_validation.isEnabled()
    assert financial._continue_validation.accessibleDescription()
    visible_unnamed_buttons = [
        button.text()
        for button in financial.findChildren(QPushButton)
        if button.isVisibleTo(financial) and not button.accessibleName().strip()
    ]
    assert visible_unnamed_buttons == []
    financial._search.setFocus()
    qtbot.keyClick(financial._search, Qt.Key.Key_Tab)
    assert financial.focusWidget() is financial._row_filter
    financial._data_tabs.setCurrentIndex(1)
    financial._row_filter.setCurrentText("GED transaction")
    assert financial._ged_proxy.rowCount() == 258
    financial._row_filter.setCurrentText("All rows")
    assert financial._pending == {}
    qtbot.mouseClick(financial._edit_button, Qt.MouseButton.LeftButton)
    assert financial._pending == {}
    assert not financial._save_changes.isEnabled()
    qtbot.mouseClick(financial._edit_button, Qt.MouseButton.LeftButton)

    financial._attestation.setChecked(True)
    assert financial._continue_validation.isEnabled()
    monkeypatch.setattr(
        QDialog,
        "exec",
        lambda _dialog: QDialog.DialogCode.Accepted,
    )
    financial._open_confirmation()
    assert window.current_view_key() == "rules_repository"
    rules = window.view("rules_repository")
    assert rules.rule_names() == [
        "Budget-to-GED Reconciliation",
        "Budget Overrun",
        "Valid Account Coding",
        "Complete and Correct Data",
        "Duplicate Transactions",
    ]
    assert "Active Rule Set" in rules._set_status.text()
    rules._continue()
    qtbot.waitUntil(
        lambda: window.current_view_key() == "financial_review_results",
        timeout=20_000,
    )
    projection = financial.current_projection()
    assert projection["metrics"]["rule_results"] == 986
    assert projection["metrics"]["scope_passed"] == 979
    assert projection["metrics"]["scope_failed"] == 5
    assert projection["metrics"]["scope_not_evaluated"] == 2
    assert len(projection["findings"]) == 5
    assert financial._results_tabs.count() == 5
    assert [
        financial._results_tabs.tabText(index)
        for index in range(financial._results_tabs.count())
    ] == [
        "Overview",
        "Financial Analysis",
        "GED Detail",
        "Findings",
        "Review Summary",
    ]
    assert [
        financial._analysis_tabs.tabText(index)
        for index in range(financial._analysis_tabs.count())
    ] == [
        "Account Analysis",
        "Vendor Analysis",
        "Department Analysis",
        "Budget vs Actual",
        "Reconciliation",
    ]
    assert [
        financial._ged_sections.tabText(index)
        for index in range(financial._ged_sections.count())
    ] == [
        "Transactions",
        "Data Quality",
    ]
    assert [
        financial._finding_sections.tabText(index)
        for index in range(financial._finding_sections.count())
    ] == [
        "Findings",
        "Rule Details",
    ]
    assert financial._results_tabs.accessibleName() == (
        "Financial Review result sections"
    )
    assert financial._analysis_tabs.accessibleName() == (
        "Financial analysis sections"
    )
    assert financial._ged_sections.accessibleName() == (
        "GED detail and data quality sections"
    )
    assert financial._finding_sections.accessibleName() == (
        "Findings and recorded rule details"
    )
    assert projection["metrics"]["financial_totals"]["bgt"] == "$10,372,000.00"
    assert projection["metrics"]["financial_totals"]["atd"] == "$3,500,095.00"
    assert projection["metrics"]["financial_totals"]["ged"] == "$3,500,095.00"
    assert projection["metrics"]["financial_totals"]["etc"] == "$5,882,000.00"
    assert projection["metrics"]["financial_totals"]["eac"] == "$9,382,095.00"
    assert projection["metrics"]["financial_totals"]["delta"] == "$989,905.00"
    assert projection["metrics"]["budget_records"] == 71
    assert projection["metrics"]["ged_transactions"] == 258
    assert len(
        projection["metrics"]["canonical_financial_dataset"]["accounts"]
    ) == 72
    assert len(projection["metrics"]["field_coverage"]) == 23
    assert {
        item["source_field"]
        for item in projection["metrics"]["field_coverage"]
    } == {
        "account_number",
        "account_name",
        "bgt",
        "atd",
        "etc",
        "eac",
        "delta",
        "notes",
        "department_number",
        "department_name",
        "fiscal_period",
        "journal_number",
        "journal_date",
        "invoice_amount",
        "check_number",
        "invoice_date",
        "vendor_name",
        "agency",
        "journal_description",
        "journal_line_description",
        "amount",
    }
    control_report = projection["metrics"]["financial_control_report"]
    assert control_report["budget"]["totals"]["etc"]["exact_decimal"] == (
        "5882000.00"
    )
    assert control_report["budget"]["totals"]["eac"]["exact_decimal"] == (
        "9382095.00"
    )
    assert control_report["budget"]["totals"]["delta"]["exact_decimal"] == (
        "989905.00"
    )
    assert (
        control_report["ged"]["total_eligible_amount"]["exact_decimal"]
        == "3500095.00"
    )
    assert (
        control_report["ged"]["total_eligible_amount"][
            "missing_or_unparseable_amount_count"
        ]
        == 1
    )
    financial_summary = projection["metrics"]["analytics"]["financial_summary"]
    assert financial_summary["ged_label"] == "Partial — $3,500,095.00"
    assert financial_summary["actual_variance_cents"] is None
    assert financial_summary["actual_variance_label"] == "Unavailable"
    assert (
        financial_summary["actual_variance_percentage_label"]
        == "Unavailable"
    )
    assert not financial_summary["complete"]

    metric_buttons = [
        button
        for button in financial.findChildren(QPushButton)
        if button.property("role") == "metricButton"
        and financial._overview_tab.isAncestorOf(button)
    ]
    metric_text = "\n".join(button.text() for button in metric_buttons)
    for expected in (
        "Overall Status",
        "Total Budget",
        "Actual Spend",
        "Estimate at Completion",
        "Variance",
        "Findings Requiring Attention",
        "$10,372,000.00",
        "$3,500,095.00",
        "$9,382,095.00",
        "Unavailable",
        "1 required amount(s) missing",
    ):
        assert expected in metric_text
    assert len(metric_buttons) == 6
    assert all(
        button.isEnabled()
        and button.focusPolicy() != Qt.FocusPolicy.NoFocus
        and button.toolTip()
        and button.accessibleName()
        for button in metric_buttons
    )

    vendor_spend = next(
        frame
        for frame in financial.findChildren(QFrame)
        if frame.accessibleName() == "Spend by vendor"
    )
    vendor_bars = vendor_spend.findChildren(QProgressBar)
    assert len(vendor_bars) == 8
    assert all(
        bar.accessibleName().endswith(".00") for bar in vendor_bars
    )

    # The comparison hierarchy is the authoritative Department + Account join.
    # Selecting an account exposes every Budget value, its contributing GED
    # transactions, governed outcomes, findings, and direct source navigation.
    financial._open_results_tab(financial._account_analysis_tab)
    assert (
        financial._results_tabs.currentWidget()
        is financial._financial_analysis_tab
    )
    assert (
        financial._analysis_tabs.currentWidget()
        is financial._account_analysis_tab
    )
    assert financial._budget_results_table.model().rowCount() == 71
    account_headers = [
        financial._budget_results_table.model().headerData(
            column, Qt.Orientation.Horizontal
        )
        for column in range(
            financial._budget_results_table.model().columnCount()
        )
    ]
    assert account_headers[:13] == [
        "Source Row",
        "Department",
        "Account",
        "Account Name",
        "BGT",
        "GED Actual",
        "EAC",
        "Actual Variance",
        "Variance %",
        "Vendors",
        "Transactions",
        "Findings",
        "Reconciliation",
    ]
    account_row = next(
        row
        for row in range(financial._budget_results_table.model().rowCount())
        if str(
            financial._budget_results_table.model().index(row, 2).data()
        )
        == "555035"
    )
    assert str(
        financial._budget_results_table.model().index(account_row, 7).data()
    ).startswith("Unfavorable · $150,000.00")
    assert str(
        financial._budget_results_table.model().index(account_row, 8).data()
    ).startswith("Unfavorable · ")
    financial._budget_results_table.activated.emit(
        financial._budget_results_table.model().index(account_row, 0)
    )
    account_index = financial._account_selector.findData("00-0245|555035")
    assert account_index >= 0
    assert financial._account_selector.currentIndex() == account_index
    assert financial._account_drilldown_card.isVisibleTo(financial)
    account = financial._selected_account_projection()
    assert account is not None
    assert account["bgt_label"] == "$1,100,000.00"
    assert account["summed_ged_amount_label"] == "$1,250,000.00"
    assert account["over_budget_amount_label"] == "$150,000.00"
    assert account["ged_transaction_count"] == len(
        account["contributing_ged_records"]
    )
    assert financial._account_transactions.rowCount() == (
        account["ged_transaction_count"]
    )
    assert financial._account_summary.verticalHeader().isHidden()
    assert financial._account_transactions.verticalHeader().isHidden()
    account_summary_labels = {
        financial._account_summary.item(row, 0).text()
        for row in range(financial._account_summary.rowCount())
    }
    assert {
        "BGT",
        "Budget ATD",
        "ETC",
        "EAC",
        "DELTA",
        "Summed GED Amount",
        "ATD − GED Difference",
        "Budget Utilization",
        "Rule Outcomes",
        "Finding Badges",
        "Original / Edited Provenance",
    } <= account_summary_labels

    qtbot.mouseClick(
        financial._account_budget_source, Qt.MouseButton.LeftButton
    )
    assert (
        financial._results_tabs.currentWidget()
        is financial._financial_analysis_tab
    )
    assert (
        financial._analysis_tabs.currentWidget()
        is financial._account_analysis_tab
    )
    assert (
        financial._budget_results_table.model()
        .index(financial._budget_results_table.currentIndex().row(), 0)
        .data()
        == account["budget_source_row"]
    )
    financial._open_results_tab(financial._comparison_tab)
    financial._account_selector.setCurrentIndex(account_index)
    selected_ged_row = financial._account_transactions.item(0, 0).text()
    qtbot.mouseClick(
        financial._account_ged_source, Qt.MouseButton.LeftButton
    )
    assert financial._results_tabs.currentWidget() is financial._ged_results_tab
    assert (
        financial._ged_sections.currentWidget()
        is financial._ged_transactions_tab
    )
    assert str(
        financial._ged_results_table.model()
        .index(financial._ged_results_table.currentIndex().row(), 0)
        .data()
    ) == selected_ged_row

    # GED Detail exposes the source-supported columns and filters the recorded
    # 258 transactions without inventing confidence, type, or prior-period data.
    ged_headers = [
        financial._ged_results_table.model().headerData(
            column, Qt.Orientation.Horizontal
        )
        for column in range(financial._ged_results_table.model().columnCount())
    ]
    assert ged_headers[:13] == [
        "Source Row",
        "Department",
        "Department Name",
        "Account",
        "Account Name",
        "Fiscal Period",
        "Journal Number",
        "Journal Date",
        "Vendor",
        "Journal Description",
        "Journal-line Description",
        "Amount",
        "Findings",
    ]
    assert "Confidence" not in ged_headers
    assert "Transaction Type" not in ged_headers
    assert financial._ged_results_table.accessibleName()
    for control in (
        financial._ged_vendor_filter,
        financial._ged_account_filter,
        financial._ged_department_filter,
        financial._ged_period_filter,
        financial._ged_min_filter,
        financial._ged_max_filter,
        financial._ged_finding_filter,
    ):
        assert control.accessibleName()
        assert control.focusPolicy() != Qt.FocusPolicy.NoFocus
    assert financial._ged_results_proxy.rowCount() == 258
    financial._ged_account_filter.setCurrentText("555035")
    assert 0 < financial._ged_results_proxy.rowCount() < 258
    assert all(
        str(financial._ged_results_proxy.index(row, 3).data()) == "555035"
        for row in range(financial._ged_results_proxy.rowCount())
    )
    financial._ged_account_filter.setCurrentText("All")
    financial._ged_finding_filter.setCurrentText("With finding")
    assert 0 < financial._ged_results_proxy.rowCount() < 258
    assert all(
        str(financial._ged_results_proxy.index(row, 12).data())
        != "No findings"
        for row in range(financial._ged_results_proxy.rowCount())
    )
    financial._ged_finding_filter.setCurrentText("All")
    assert financial._ged_results_proxy.rowCount() == 258
    financial._ged_results_table.selectRow(0)
    opened_dialogs = []
    monkeypatch.setattr(
        QDialog,
        "exec",
        lambda dialog: (
            opened_dialogs.append(dialog)
            or QDialog.DialogCode.Accepted
        ),
    )
    financial._open_selected_ged_details()
    transaction_dialog = opened_dialogs[-1]
    assert transaction_dialog.objectName() == "GEDTransactionDetailsDialog"
    transaction_evidence = next(
        table
        for table in transaction_dialog.findChildren(QTableWidget)
        if table.accessibleName()
        == "GED transaction original and reviewed source values"
    )
    assert transaction_evidence.rowCount() == 15
    assert transaction_evidence.columnCount() == 5
    assert transaction_evidence.horizontalHeaderItem(0).text() == "Field"
    assert transaction_evidence.horizontalHeaderItem(3).text() == (
        "Current Reviewed"
    )

    # Rule and finding evidence always identifies the exact governed rule
    # version, and every implicated source record remains selectable.
    financial._open_results_tab(financial._rule_results_tab)
    assert financial._results_tabs.currentWidget() is financial._findings_tab
    assert (
        financial._finding_sections.currentWidget()
        is financial._rule_results_tab
    )
    assert "Version" in [
        financial._rule_summary_model.headerData(
            column, Qt.Orientation.Horizontal
        )
        for column in range(financial._rule_summary_model.columnCount())
    ]
    assert all(
        projection["executions"][row]["version"]
        == financial._rule_summary_model.item(row, 1).text()
        for row in range(financial._rule_summary_model.rowCount())
    )
    for row in range(financial._rule_summary_model.rowCount()):
        financial._show_rule_evidence(
            financial._rule_summary_model.index(row, 0),
            financial._rule_summary_model.index(-1, -1),
        )
        scope_headers = [
            financial._rule_scope_model.headerData(
                column, Qt.Orientation.Horizontal
            )
            for column in range(financial._rule_scope_model.columnCount())
        ]
        assert "Rule Version" in scope_headers
        assert financial._rule_evidence_selector.count() >= 1
        assert financial._open_rule_evidence.isEnabled()
    assert all(
        finding["rule_version"] != "Unavailable"
        for finding in projection["findings"]
    )
    financial._open_results_tab(financial._finding_list_tab)
    assert financial._results_tabs.currentWidget() is financial._findings_tab
    assert (
        financial._finding_sections.currentWidget()
        is financial._finding_list_tab
    )
    assert financial._findings_proxy.rowCount() == 5
    assert not financial._finding_detail_panel.isVisibleTo(financial)
    assert "press Enter" in (
        financial._findings_result_table.accessibleDescription()
    )
    financial._findings_rule.setCurrentText("All rules")
    financial._findings_severity.setCurrentText("All severities")
    financial._findings_status.setCurrentText("All statuses")
    for row in range(financial._findings_proxy.rowCount()):
        current = financial._findings_proxy.index(row, 0)
        financial._show_finding_detail(
            current, financial._findings_proxy.index(-1, -1)
        )
        selected = financial._selected_finding
        assert selected["rule_version"] != "Unavailable"
        assert financial._finding_evidence_selector.count() == len(
            dict.fromkeys(selected["source_records"])
        )
        assert financial._open_finding.isEnabled()
        explanation = selected["explain_this"]
        assert financial._finding_what.text() == explanation["what_happened"]
        assert (
            financial._finding_why_flagged.text()
            == explanation["why_flagged"]
        )
        assert (
            financial._finding_why_matters.text()
            == explanation["why_it_matters"]
        )
        assert (
            financial._finding_next_step.text()
            == explanation["recommended_next_step"]
        )
        transactions = explanation["contributing_transactions"]
        assert financial._finding_transactions.rowCount() == len(
            transactions
        )
        assert financial._finding_transactions.columnCount() == 8
        if transactions:
            first = transactions[0]
            assert not financial._finding_transactions.isHidden()
            assert financial._finding_transactions_empty.isHidden()
            assert (
                financial._finding_transactions.item(0, 0).text()
                == str(first["source_row"])
            )
            assert (
                financial._finding_transactions.item(0, 1).text()
                == first["vendor"]
            )
            assert (
                financial._finding_transactions.item(0, 3).text()
                == (first["description"] or "No description recorded")
            )
            assert (
                financial._finding_transactions.item(0, 4).text()
                == str(first["date"])
            )
            assert (
                financial._finding_transactions.item(0, 5).text()
                == first["amount_label"]
            )
            assert (
                financial._finding_transactions.item(0, 6).text()
                == first["workbook"]
            )
            assert (
                financial._finding_transactions.item(0, 7).text()
                == first["worksheet"]
            )
        else:
            assert financial._finding_transactions.isHidden()
            assert not financial._finding_transactions_empty.isHidden()

    financial._findings_result_table.selectRow(0)
    financial._findings_result_table.activated.emit(
        financial._findings_proxy.index(0, 6)
    )
    assert financial._finding_detail_panel.isVisibleTo(financial)
    financial._set_finding_explanation_visible(False)
    financial._findings_result_table.activated.emit(
        financial._findings_proxy.index(0, 7)
    )
    assert financial._finding_detail_panel.isVisibleTo(financial)
    financial._set_finding_explanation_visible(False)
    keyboard_ask_fin = []
    monkeypatch.setattr(
        financial,
        "_ask_fin_for_finding",
        keyboard_ask_fin.append,
    )
    qtbot.mouseClick(
        financial._finding_ask_fin, Qt.MouseButton.LeftButton
    )
    assert keyboard_ask_fin
    keyboard_ask_fin.clear()
    financial._findings_result_table.activated.emit(
        financial._findings_proxy.index(0, 8)
    )
    assert keyboard_ask_fin
    assert keyboard_ask_fin[0]["finding_id"]
    qtbot.mouseClick(
        financial._explain_finding_button, Qt.MouseButton.LeftButton
    )
    assert financial._finding_detail_panel.isVisibleTo(financial)
    assert financial._finding_detail_panel.accessibleName() == (
        "Selected finding evidence"
    )
    assert [
        financial._finding_status_control.itemText(index)
        for index in range(financial._finding_status_control.count())
    ] == [
        "New",
        "Acknowledged",
        "In Review",
        "Resolved",
        "Dismissed",
    ]
    ask_fin_buttons = [
        button
        for button in financial.findChildren(QPushButton)
        if button.text() == "Ask Fin"
    ]
    assert ask_fin_buttons
    assert all(
        button.isEnabled() and button.accessibleName()
        for button in ask_fin_buttons
    )

    result_tables = financial.findChildren(QTableView)
    result_tables.extend(financial.findChildren(QTableWidget))
    for table in result_tables:
        if table.isAncestorOf(financial._results_tabs) or table is financial._results_tabs:
            continue
        if table.accessibleName():
            assert table.verticalHeader().isHidden(), table.accessibleName()

    financial._open_results_tab(financial._quality_tab)
    assert financial._results_tabs.currentWidget() is financial._ged_results_tab
    assert financial._ged_sections.currentWidget() is financial._quality_tab
    control_table = _projection_table(financial._quality_tab, "Control")
    coverage_table = _projection_table(
        financial._quality_tab, "Source", columns=8
    )
    assert control_table.model().rowCount() == 9
    assert coverage_table.model().rowCount() == 23
    results_page = financial._stack.currentWidget()
    widest_widgets = sorted(
        (
            (
                widget.minimumSizeHint().width(),
                type(widget).__name__,
                widget.objectName(),
                widget.accessibleName(),
            )
            for widget in results_page.widget().findChildren(QWidget)
        ),
        reverse=True,
    )
    assert results_page.horizontalScrollBar().maximum() == 0, (
        widest_widgets[:8]
    )

    # Every secondary analysis view is reachable through the five-view shell
    # and displays only values supported by the uploaded May 2026 reports.
    financial._open_results_tab(financial._vendor_analysis_tab)
    assert (
        financial._analysis_tabs.currentWidget()
        is financial._vendor_analysis_tab
    )
    assert financial._vendor_analysis_table.model().rowCount() >= 23
    assert financial._vendor_analysis_table.model().columnCount() == 6
    assert [
        financial._vendor_analysis_table.model().headerData(
            column, Qt.Orientation.Horizontal
        )
        for column in range(6)
    ] == [
        "Vendor",
        "Recorded Spend",
        "Accounts",
        "Transactions",
        "Findings",
        "Completeness",
    ]
    financial._open_results_tab(financial._department_analysis_tab)
    department_table = _projection_table(
        financial._department_analysis_tab, "Department"
    )
    assert department_table.model().rowCount() == 1
    assert "00-0245" in str(department_table.model().index(0, 0).data())
    assert "Applications Enginee" in str(
        department_table.model().index(0, 0).data()
    )
    assert department_table.model().index(0, 6).data() == (
        "Incomplete · Unavailable"
    )
    assert department_table.model().index(0, 7).data() == (
        "Incomplete · Unavailable"
    )

    financial._open_results_tab(financial._comparison_tab)
    comparison_table = _projection_table(
        financial._comparison_tab, "Account", columns=9
    )
    assert comparison_table.model().rowCount() == 71
    assert comparison_table.model().headerData(
        6, Qt.Orientation.Horizontal
    ) == "Actual Variance"
    assert comparison_table.model().headerData(
        7, Qt.Orientation.Horizontal
    ) == "Variance %"

    financial._open_results_tab(financial._reconciliation_tab)
    reconciliation_table = _projection_table(
        financial._reconciliation_tab, "Department", columns=9
    )
    assert reconciliation_table.model().rowCount() == 71
    assert reconciliation_table.model().headerData(
        3, Qt.Orientation.Horizontal
    ) == "Budget ATD"

    financial._open_results_tab(financial._finding_list_tab)
    assert financial._findings_result_table.isVisibleTo(financial)
    financial._set_finding_explanation_visible(True)
    assert financial._finding_comparison.isVisibleTo(financial)
    financial._findings_rule.setCurrentText("CORE-03")
    financial._findings_result_table.selectRow(0)
    financial._show_finding_detail(
        financial._findings_proxy.index(0, 0),
        financial._findings_proxy.index(-1, -1),
    )
    duplicate_row = next(
        row
        for row in range(financial._finding_comparison.rowCount())
        if financial._finding_comparison.item(row, 0).text()
        == "Duplicate records"
    )
    assert (
        financial._finding_comparison.item(duplicate_row, 1).text()
        == "GED:GED:65"
    )
    assert (
        financial._finding_comparison.item(duplicate_row, 2).text()
        == "GED:GED:66"
    )
    assert financial._finding_comparison.horizontalScrollBar().maximum() == 0
    financial._findings_rule.setCurrentText("All rules")
    financial._findings_severity.setCurrentText("High")
    assert financial._findings_proxy.rowCount() == 4
    financial._findings_rule.setCurrentText("CORE-02")
    assert financial._findings_proxy.rowCount() == 1

    # Review status changes are audited presentation metadata. They must not
    # mutate the sealed deterministic validation result or finding count.
    financial._findings_severity.setCurrentText("All severities")
    financial._findings_rule.setCurrentText("CORE-03")
    financial._findings_result_table.selectRow(0)
    financial._show_finding_detail(
        financial._findings_proxy.index(0, 0),
        financial._findings_proxy.index(-1, -1),
    )
    duplicate_finding_id = financial._selected_finding["finding_id"]
    monkeypatch.setattr(
        QInputDialog,
        "getText",
        lambda *_args, **_kwargs: (
            "Reviewer acknowledged the recorded duplicate evidence.",
            True,
        ),
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Ok,
    )
    financial._finding_status_control.setCurrentText("Acknowledged")
    financial._change_finding_status()
    projection_after_status = financial.current_projection()
    updated = next(
        item
        for item in projection_after_status["findings"]
        if item["finding_id"] == duplicate_finding_id
    )
    assert updated["review_status"] == "Acknowledged"
    assert projection_after_status["metrics"]["rule_results"] == 986
    assert projection_after_status["metrics"]["scope_passed"] == 979
    assert projection_after_status["metrics"]["scope_failed"] == 5
    assert projection_after_status["metrics"]["scope_not_evaluated"] == 2

    financial._open_results_tab(financial._review_summary_tab)
    assert (
        financial._results_tabs.currentWidget()
        is financial._review_summary_tab
    )
    review_summary_text = "\n".join(
        label.text()
        for label in financial._review_summary_tab.findChildren(
            type(financial._results_subtitle)
        )
    )
    assert "May 2026 Leadership Summary" in review_summary_text
    assert "Generated deterministically" in review_summary_text
    assert "5 recorded findings" in review_summary_text

    financial._complete_review()
    assert window.current_view_key() == "review_complete"
    assert financial._context.text().endswith("Closed")
    assert financial._complete_summary.isVisibleTo(financial)
    assert financial._complete_preservation.isVisibleTo(financial)
    assert (
        financial._complete_preservation.geometry().bottom()
        < financial._complete_results_button.geometry().top()
    )
    window._show_past_reviews()
    qtbot.waitUntil(lambda: bool(management._past_cards))
    past_text = " ".join(
        label.text()
        for label in management._past_cards[0].findChildren(
            type(management._past_title)
        )
    )
    assert "Overall status: Incomplete" in past_text
    assert "Findings: 5" in past_text
    assert "71 Budget records" in past_text
    assert management._shell_context.text().endswith("Closed")
    qtbot.mouseClick(
        management._past_cards[0].open_button, Qt.MouseButton.LeftButton
    )
    qtbot.waitUntil(
        lambda: window.current_view_key() == "financial_review_results",
        timeout=20_000,
    )
    qtbot.waitUntil(
        lambda: financial.current_dataset() is not None,
        timeout=20_000,
    )
    assert financial.current_projection()["completion"] is not None
    assert len(financial.current_dataset().budget_records) == 94
    assert len(financial.current_dataset().ged_records) == 292
    financial._open_results_tab(financial._account_analysis_tab)
    assert financial._budget_results_table.model().index(0, 0).data() == 2
    assert not financial._complete_button.isVisible()
    assert "Review Results current" in (
        financial._results_progress.accessibleDescription()
    )
    assert "Complete complete" in (
        financial._results_progress.accessibleDescription()
    )
