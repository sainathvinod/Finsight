# Verifies: missing-source two-step confirmation (Product Owner workflow §7).
#   - Uploading without all sources does NOT silently continue.
#   - Step 1 names the missing source(s) and the unavailable capabilities (never implies they ran).
#   - Step 2 is an explicit choice: "Upload remaining documents" vs "Continue anyway".
#   - "Upload remaining documents" / "Go back" cancels and preserves the already-selected files.
#   - "Continue anyway" proceeds AND records the decision in the append-only audit trail (§19).
import os

from finsight.application.abandonment import MEANINGFUL_ACTIONS


def _sources(tmp_path):
    from tests.support import build_synthetic_ged, build_synthetic_budget
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    return ged, bud


def _upload_panel(w, cid="2026-07"):
    w.navigate("workspace")
    w._c.create_review(cid, "July", "2026")
    return w._workspace.panel(1)


def test_upload_without_invoice_triggers_two_step_confirmation(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    ged, bud = _sources(tmp_path)
    up = _upload_panel(w)
    up.set_ged(ged); up.set_budget(bud)                  # no invoice
    up._on_upload()                                       # step 1
    assert "invoice" in up.message.text().lower()         # names the missing source
    assert up._continue1.isVisibleTo(up) and not up._upload.isVisibleTo(up)
    assert w._c.workflow_state("2026-07") == "Created"    # not advanced yet
    up._continue1.click()                                 # step 2
    assert up._remaining.isVisibleTo(up) and up._anyway.isVisibleTo(up)
    assert "audit" in up.message.text().lower()           # explicit that it is recorded


def test_upload_remaining_cancels_and_preserves_files(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    ged, bud = _sources(tmp_path)
    up = _upload_panel(w)
    up.set_ged(ged); up.set_budget(bud)
    up._on_upload(); up._continue1.click()               # into step 2
    up._remaining.click()                                 # back out
    assert up._upload.isVisibleTo(up) and not up._anyway.isVisibleTo(up)
    assert up._ged_card.path() == ged and up._bud_card.path() == bud   # selections preserved


def test_continue_anyway_proceeds_and_audits_the_decision(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    ged, bud = _sources(tmp_path)
    up = _upload_panel(w)
    up.set_ged(ged); up.set_budget(bud)
    up._on_upload(); up._continue1.click(); up._anyway.click()
    assert w._c.workflow_state("2026-07") == "Intake"     # proceeded
    timeline = w._c.audit_timeline("2026-07")
    actions = [e.action for e in timeline]
    assert "missing_source_acknowledged" in actions       # the decision is recorded
    assert "missing_source_acknowledged" in MEANINGFUL_ACTIONS   # counts as activity


def test_no_confirmation_when_all_sources_present(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    ged, bud = _sources(tmp_path)
    inv = os.path.join(str(tmp_path), "inv.pdf"); open(inv, "wb").write(b"%PDF x")
    up = _upload_panel(w)
    up.set_ged(ged); up.set_budget(bud); up.set_invoice(inv)
    up._on_upload()                                       # all three present -> no prompt, direct upload
    assert w._c.workflow_state("2026-07") == "Intake"
    actions = [e.action for e in w._c.audit_timeline("2026-07")]
    assert "missing_source_acknowledged" not in actions   # nothing was omitted
