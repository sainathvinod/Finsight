# Verifies: Phase 6.4cB — the derived mirror (cycles.state) never advances beyond its authoritative
# working generation (ADR-011 §7/§9). The reconciliation for the never-released 6.4cA anomaly is
# DIAGNOSTIC-ONLY (architect-directed): detect + report, never a repair that would fabricate facts.
import os

import pytest

from finsight.app import build_app
from finsight.application.review_session import ReviewSession
from finsight.application.workflow import ReviewWorkflowService
from finsight.infrastructure.lifecycle_repositories import detect_state_generation_divergence
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def _files(tmp_path):
    g = os.path.join(str(tmp_path), "g.xlsx"); b = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(g); build_synthetic_budget(b); return g, b


def test_normal_workflow_produces_no_state_generation_divergence(tmp_path):
    c = build_app(str(tmp_path / "fs.db"), FixedClock())
    wf = ReviewWorkflowService(c.orch.engine); ged, bud = _files(tmp_path)
    wf.create_review("A", "May", "2026"); s = ReviewSession("A")
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s); wf.analyze(s); wf.summarize(s); wf.export(s)
    assert detect_state_generation_divergence(c.dal) == []      # mirror never ahead of the generation


def test_diagnostic_detects_a_synthetic_6_4cA_divergence(tmp_path):
    # Simulate the never-released 6.4cA anomaly: mirror at EXPORTED while the generation stays VERIFIED.
    c = build_app(str(tmp_path / "fs.db"), FixedClock())
    wf = ReviewWorkflowService(c.orch.engine); ged, bud = _files(tmp_path)
    wf.create_review("A", "May", "2026"); s = ReviewSession("A")
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s)          # generation at VERIFIED
    with c.uow.atomic():
        c.dal.conn.execute("UPDATE cycles SET state='Exported' WHERE cycle_id='A'")   # mirror jumps ahead
    diverged = detect_state_generation_divergence(c.dal)
    assert diverged == [("A", "Exported", "VERIFIED")]
    # detection only — the generation is NOT mutated (no fabricated analytical facts)
    assert c.dal.conn.execute("SELECT analytical_state FROM review_generations WHERE cycle_id='A'"
                              ).fetchone()[0] == "VERIFIED"
