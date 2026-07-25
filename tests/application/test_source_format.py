# Verifies: Phase 6.4cA BLOCKER 3 — ONE authoritative source-format policy shared by intake, dialogs,
# and recovery, matching the reader's REAL capability (openpyxl = .xlsx; legacy .xls is NOT supported).
# The prior false ".xls" UI claim is corrected. No duplicate extension literals across layers.
import os

import pytest

from finsight.app import build_app
from finsight.application import source_format as SF
from finsight.application.review_session import ReviewSession
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.reconstruction import ReviewReconstructionService, RecoveryStatus
from finsight.infrastructure.readers import ExcelReader
from finsight.infrastructure.lifecycle_repositories import ReviewGenerationRepoSqlite
from finsight.delivery.desktop.views.steps import intake_steps
from finsight.delivery.desktop.views import workflow_view
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def test_policy_is_xlsx_only_no_false_xls_claim():
    assert SF.SUPPORTED_EXTENSIONS == (".xlsx",)
    assert SF.is_supported("/x/report.xlsx") and SF.is_supported("/x/REPORT.XLSX")
    assert not SF.is_supported("/x/report.xls")          # legacy .xls is NOT supported (reader reality)
    assert not SF.is_supported("/x/report.csv") and not SF.is_supported("")
    assert ".xls," not in SF.ACCEPTED_LABEL and SF.ACCEPTED_LABEL == "Accepted: .xlsx"
    assert "*.xls;" not in SF.QT_FILE_FILTER              # dialog never offers bare .xls


def test_intake_and_recovery_and_locate_share_one_policy():
    # Delivery imports the SAME policy object — no separate literals.
    assert intake_steps._WORKBOOKS is SF.QT_FILE_FILTER
    assert workflow_view.QT_FILE_FILTER is SF.QT_FILE_FILTER
    assert intake_steps.ACCEPTED_LABEL is SF.ACCEPTED_LABEL


def test_reader_actually_reads_xlsx_and_rejects_non_xlsx(tmp_path):
    ged = os.path.join(str(tmp_path), "g.xlsx"); build_synthetic_ged(ged)
    assert ExcelReader().read(ged, "GED")                # .xlsx parses
    fake_xls = os.path.join(str(tmp_path), "legacy.xls")
    with open(fake_xls, "wb") as fh:
        fh.write(b"\xd0\xcf\x11\xe0not-an-xlsx")          # BIFF-ish bytes openpyxl cannot parse
    with pytest.raises(Exception):
        ExcelReader().read(fake_xls, "GED")              # reader genuinely cannot read .xls


def test_recovery_classifies_unsupported_consistently_with_intake(tmp_path):
    db = str(tmp_path / "fs.db")
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    c = build_app(db, FixedClock()); wf = ReviewWorkflowService(c.orch.engine)
    wf.create_review("A", "May", "2026"); s = ReviewSession("A")
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s)
    svc = ReviewReconstructionService(c.orch.engine, c.source_binding_repo,
                                      ReviewGenerationRepoSqlite(c.dal))
    xls = os.path.join(str(tmp_path), "candidate.xls")
    with open(xls, "wb") as fh:
        fh.write(b"whatever")
    # recovery rejects exactly what intake would never accept — one policy, no contradiction
    assert svc.classify_candidate("A", "GED", xls).status == RecoveryStatus.UNSUPPORTED_SOURCE
    assert not SF.is_supported(xls)
