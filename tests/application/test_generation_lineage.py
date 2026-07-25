# Verifies: R1-M2 — single-generation lineage linkage (ADR-011 §3/§8): every rule run and finding
# belongs to exactly one generation. On analysis the run and the cycle's findings are bound to the
# current (working) generation atomically, satisfying the finding⇒run generation-consistency trigger.
import os

import pytest

from finsight.app import build_app
from finsight.application.review_session import ReviewSession
from finsight.application.workflow import ReviewWorkflowService
from finsight.infrastructure.lifecycle_repositories import ReviewGenerationRepoSqlite
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def _analyze(tmp_path, cid="A"):
    c = build_app(str(tmp_path / "fs.db"), FixedClock())
    wf = ReviewWorkflowService(c.orch.engine)
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    wf.create_review(cid, "May", "2026"); s = ReviewSession(cid)
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s); wf.analyze(s)
    return c


def test_run_and_findings_bind_to_the_working_generation(tmp_path):
    c = _analyze(tmp_path)
    gid = ReviewGenerationRepoSqlite(c.dal).working_generation("A").generation_id
    run_gen = c.dal.conn.execute("SELECT generation_id FROM rule_runs WHERE cycle_id='A'").fetchone()[0]
    finding_gens = [r[0] for r in c.dal.conn.execute(
        "SELECT generation_id FROM findings WHERE cycle_id='A'").fetchall()]
    assert run_gen == gid                                      # run bound to the generation
    assert finding_gens and all(g == gid for g in finding_gens)  # every finding bound to the same generation


def test_lineage_is_internally_consistent(tmp_path):
    c = _analyze(tmp_path)
    # exactly one run per generation (partial unique index) and run.gen == every finding.gen
    rows = c.dal.conn.execute(
        "SELECT COUNT(DISTINCT generation_id) FROM (SELECT generation_id FROM rule_runs WHERE cycle_id='A' "
        "UNION ALL SELECT generation_id FROM findings WHERE cycle_id='A')").fetchone()[0]
    assert rows == 1                                           # one lineage: run + findings agree


def test_published_generation_owns_the_analyzed_lineage(tmp_path):
    c = _analyze(tmp_path)
    gens = ReviewGenerationRepoSqlite(c.dal)
    published = gens.published_generation("A")                 # first-gen auto-published at ANALYZED
    assert published is not None and published.analytical_state.value == "ANALYZED"
    run_gen = c.dal.conn.execute("SELECT generation_id FROM rule_runs WHERE cycle_id='A'").fetchone()[0]
    assert run_gen == published.generation_id                 # trusted published generation owns the run


def test_batch_run_review_also_links_lineage(tmp_path):
    # the batch orchestrator path drives the same transitions, so it links lineage too
    c = build_app(str(tmp_path / "fs.db"), FixedClock())
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    c.orch.run_review("B", "May", "2026", ged, bud, approve=True)
    gid = ReviewGenerationRepoSqlite(c.dal).working_generation("B").generation_id
    assert c.dal.conn.execute("SELECT generation_id FROM rule_runs WHERE cycle_id='B'").fetchone()[0] == gid
    assert c.dal.conn.execute("SELECT COUNT(*) FROM findings WHERE cycle_id='B' AND generation_id IS NULL"
                              ).fetchone()[0] == 0             # no orphan (generation-less) findings
