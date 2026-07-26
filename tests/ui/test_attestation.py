# Verifies: verification attestation with BRANCHING wording (Product Owner workflow §12).
#   - No-edit review shows the "reviewed & accurate" attestation; an edited review shows the
#     "edited & approved corrections" attestation.
#   - Analysis is blocked until the reviewer explicitly attests (checkbox gates approval).
#   - The verify audit fact records the attestation: whether corrections existed, the exact statement,
#     and the verified-dataset fingerprint it binds to (identifies the user + timestamp via the fact).
import os

from tests.support import build_synthetic_ged, build_synthetic_budget
from finsight.application.attestation import ATTESTATION_NO_EDIT, ATTESTATION_EDITED


def _process(w, tmp_path):
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    w._c.create_review("2026-07", "July", "2026")
    w._c.upload("2026-07", ged, bud)
    w._c._s.workflow.process(w._c._session_for("2026-07"))
    w._c.select_review("2026-07")


def test_attestation_is_no_edit_when_nothing_corrected(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    verify = w._workspace.panel(4)
    verify.refresh()
    assert verify.attestation_text() == ATTESTATION_NO_EDIT
    assert not verify._approve.isEnabled()               # analysis blocked until attested
    verify._attest_check.setChecked(True)
    assert verify._approve.isEnabled()


def test_attestation_switches_to_edited_after_a_correction(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    verify = w._workspace.panel(4)
    verify.refresh()
    verify._attest_check.setChecked(True)                # attest to the un-edited data...
    tab = verify._review.tab("GED")
    col = list(tab._records.columns).index("amount")
    tab.edit_cell(0, col, "9999")                        # ...then correct a value
    assert verify.attestation_text() == ATTESTATION_EDITED
    assert not verify._attest_check.isChecked()          # a changed attestation must be re-confirmed


def test_verify_records_branching_attestation_in_audit(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    # Correct a value, then verify -> the verify audit fact must record the EDITED attestation.
    verify = w._workspace.panel(4); verify.refresh()
    tab = verify._review.tab("GED")
    col = list(tab._records.columns).index("amount")
    tab.edit_cell(0, col, "9999")
    w._c.verify("2026-07")
    verify_events = [e for e in w._c.audit_timeline("2026-07") if e.action == "verify"]
    assert verify_events
    d = verify_events[-1].detail
    assert d["corrections_present"] is True
    assert d["attestation_statement"] == ATTESTATION_EDITED
    assert d.get("verified_fingerprint")                 # bound to the exact verified dataset


def test_no_edit_verify_records_no_edit_attestation(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    w._c.verify("2026-07")
    d = [e for e in w._c.audit_timeline("2026-07") if e.action == "verify"][-1].detail
    assert d["corrections_present"] is False
    assert d["attestation_statement"] == ATTESTATION_NO_EDIT
