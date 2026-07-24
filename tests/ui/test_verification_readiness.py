# Verifies: Phase 5.4 — verification representative-row preview, review readiness, and account-name
# enrichment. Pure readiness tested directly; the rest end-to-end through the real workflow with
# synthetic files (session-scoped). No network, no source mutation, no editing workflow.
import os

import pytest

from finsight.application.read_models.verification import (
    build_readiness, PREVIEW_ROW_CAP, ReviewReadinessSummary,
)
from tests.support import build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def _files(tmp_path):
    ged = os.path.join(str(tmp_path), "ged.xlsx")
    bud = os.path.join(str(tmp_path), "budget.xlsx")
    build_synthetic_ged(ged)
    build_synthetic_budget(bud)
    return ged, bud


def _process(w, tmp_path):
    ged, bud = _files(tmp_path)
    w._c.create_review("2026-07", "July", "2026")
    w._c.upload("2026-07", ged, bud)
    w._c._s.workflow.process(w._c._session_for("2026-07"))
    w._c.select_review("2026-07")


# ===================== readiness (pure, state-derived) =====================
class _Snap:
    def __init__(self, ged_valid, budget_valid, quarantined, available, rejected_reason=None):
        self.ged_valid = ged_valid
        self.budget_valid = budget_valid
        self.quarantined = quarantined
        self.available = available
        self.rejected_reason = rejected_reason


class TestReadiness:
    def test_not_uploaded(self):
        r = build_readiness("c", "Created", None)
        assert not r.required_sources_present
        assert "not uploaded" in r.blocking_reasons[0].lower()

    def test_processed_without_session_derives_passed(self):
        r = build_readiness("c", "Processed", None)
        assert r.normalized_data_available
        assert r.validation_status == "passed"
        assert "not yet verified" in " ".join(r.blocking_reasons).lower()

    def test_analysis_and_export_flags(self):
        assert build_readiness("c", "Analyzed", None).analysis_available
        assert build_readiness("c", "Exported", None).export_ready
        assert build_readiness("c", "Exported", None).blocking_reasons == ()   # clean/complete

    def test_validation_failed_from_snapshot(self):
        r = build_readiness("c", "Processed", _Snap(0, 0, 3, False, "bad columns"))
        assert r.validation_status == "failed"
        assert any("validation failed" in b.lower() for b in r.blocking_reasons)

    def test_quarantine_note_from_snapshot(self):
        r = build_readiness("c", "Processed", _Snap(10, 5, 2, True))
        assert r.accepted_rows == 15 and r.quarantined_rows == 2
        assert any("quarantined" in b.lower() for b in r.blocking_reasons)

    def test_is_immutable_dataclass(self):
        r = build_readiness("c", "Analyzed", None)
        assert isinstance(r, ReviewReadinessSummary)
        with pytest.raises(Exception):
            r.export_ready = True


# ===================== verification preview (end-to-end, session) =====================
def test_verification_preview_representative_rows(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    verify = w._workspace.panel(4)
    verify.refresh()
    ged_cols = verify.verification_preview_columns("GED")
    ged_rows = verify.verification_preview_values("GED")
    assert "account" in ged_cols and "amount" in ged_cols   # the normalized fields the engine uses
    assert 0 < len(ged_rows) <= PREVIEW_ROW_CAP        # representative, capped
    assert verify.verification_preview_columns("Budget Tracker")
    summary = verify.verification_source_summary("GED")
    assert summary["accepted"] >= 1

def test_verification_rows_are_stable_source_order(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    verify = w._workspace.panel(4)
    verify.refresh()
    first = verify.verification_preview_values("GED")
    verify.refresh()
    assert verify.verification_preview_values("GED") == first   # deterministic

def test_verification_unavailable_without_processing(window_factory, empty_db):
    w = window_factory(empty_db)
    w._c.create_review("2026-07", "July", "2026")
    verify = w._workspace.panel(4)
    verify.refresh()
    assert verify.verification_preview_columns("GED") == []
    assert not verify._approve.isEnabled()             # cannot approve unavailable data


# ===================== overview readiness =====================
def test_overview_readiness_summary(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    ov = w.view("overview")
    ov.refresh()
    r = ov.review_readiness_summary()
    assert r["required_sources_present"] and r["normalized_data_available"]
    assert r["validation_status"] == "passed"
    assert "not yet verified" in " ".join(r["blocking_reasons"]).lower()


# ===================== account/rule labels — names not authoritatively available =====================
def test_finding_labels_fall_back_to_canonical_ids(window_factory, populated_db):
    # The extraction pipeline does not retain account names and there is no runtime rule-name source,
    # so labels are the canonical code / rule id (Phase 5.4: no invented names).
    w = window_factory(populated_db)
    w._c.select_review("2026-07")
    fv = w.view("findings")
    fv.refresh()
    fid = fv.displayed_finding_ids()[0]
    assert fv.finding_account_label(fid) == "6100"      # account code (no name available)
    assert fv.finding_rule_label(fid) == "R-BUD-02"     # rule id (no name available)


# ===================== architecture =====================
def test_54_delivery_has_no_repo_ai_or_rawfile_imports():
    files = [
        os.path.join("src", "finsight", "delivery", "desktop", "views", "steps", "verify_steps.py"),
        os.path.join("src", "finsight", "delivery", "desktop", "views", "overview_view.py"),
        os.path.join("src", "finsight", "application", "read_models", "verification.py"),
    ]
    forbidden = ("finsight.infrastructure", "sqlite3", "urllib", "openpyxl", "ask_fin", "citations",
                 "provider")
    offenders = []
    for path in files:
        for line in open(path, encoding="utf-8"):
            s = line.strip()
            if s.startswith("import ") or s.startswith("from "):
                for tok in forbidden:
                    if tok in s:
                        offenders.append((os.path.basename(path), tok))
    assert offenders == []
