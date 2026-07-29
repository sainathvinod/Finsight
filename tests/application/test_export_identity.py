# Verifies: R1-M3 — immutable export & report identity (ADR-015 §3). An export carries an embedded
# manifest identifying the exact generation/run/versions/verified basis that produced it, and an
# immutable, append-only export_artifacts record is persisted. R1 is single-generation: status is
# always "current"; no supersession (R2).
import os

import pytest
from sqlcipher3 import dbapi2 as sqlcipher

from finsight.app import build_app
from finsight.application.review_session import ReviewSession
from finsight.application.workflow import ReviewWorkflowService
from finsight.infrastructure.lifecycle_repositories import (
    ExportArtifactRepoSqlite,
    ReviewGenerationRepoSqlite,
)
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def _export(tmp_path, cid="A"):
    c = build_app(str(tmp_path / "fs.db"), FixedClock())
    wf = ReviewWorkflowService(c.orch.engine)
    ged = os.path.join(str(tmp_path), "g.xlsx")
    bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged)
    build_synthetic_budget(bud)
    wf.create_review(cid, "May", "2026")
    s = ReviewSession(cid)
    wf.upload(s, ged, bud)
    wf.process(s)
    wf.verify(s)
    wf.analyze(s)
    wf.summarize(s)
    result = wf.export(s)
    return c, result


def test_export_embeds_manifest_identifying_the_generation(tmp_path):
    c, result = _export(tmp_path)
    gen = ReviewGenerationRepoSqlite(c.dal).published_generation("A")
    m = result.content["manifest"]
    assert m["generation_id"] == gen.generation_id and m["sequence_number"] == 1
    assert m["verified_source_fingerprint"] == gen.verified_fingerprint     # verified-dataset fp (ADR-015 §3)
    assert m["extractor_version"] == "extractor-v1" and m["creation_reason"] == "INITIAL_VERIFICATION"
    assert m["ruleset_version"] and m["config_version"] and m["run_id"]
    assert m["status"] == "current"                                        # single generation, no supersession


def test_immutable_export_artifact_persisted(tmp_path):
    c, _ = _export(tmp_path)
    exp = ExportArtifactRepoSqlite(c.dal)
    gen = ReviewGenerationRepoSqlite(c.dal).published_generation("A")
    arts = exp.list_for_cycle("A")
    assert len(arts) == 1
    a = arts[0]
    assert a.generation_id == gen.generation_id and a.export_fingerprint     # content hash present
    run_id = c.dal.conn.execute("SELECT run_id FROM rule_runs WHERE cycle_id='A'").fetchone()[0]
    assert a.run_id == run_id                                              # cycle/generation/run agree


def test_export_artifact_is_append_only(tmp_path):
    c, _ = _export(tmp_path)
    # DB blocks update/delete (migration 0003 append-only triggers)
    with pytest.raises(sqlcipher.IntegrityError):
        c.dal.conn.execute("UPDATE export_artifacts SET export_path='/x' WHERE cycle_id='A'")
    with pytest.raises(sqlcipher.IntegrityError):
        c.dal.conn.execute("DELETE FROM export_artifacts WHERE cycle_id='A'")


def test_export_fingerprint_is_deterministic(tmp_path):
    c, result = _export(tmp_path)
    fp1 = c.orch.engine.export.fingerprint(result.content)
    fp2 = c.orch.engine.export.fingerprint(result.content)
    stored = ExportArtifactRepoSqlite(c.dal).list_for_cycle("A")[0].export_fingerprint
    assert fp1 == fp2 == stored


def test_batch_run_review_persists_one_immutable_export(tmp_path):
    c = build_app(str(tmp_path / "fs.db"), FixedClock())
    ged = os.path.join(str(tmp_path), "g.xlsx")
    bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged)
    build_synthetic_budget(bud)
    c.orch.run_review("B", "May", "2026", ged, bud, approve=True)
    assert len(ExportArtifactRepoSqlite(c.dal).list_for_cycle("B")) == 1    # exactly one, no supersession
    assert c.dal.conn.execute("SELECT COUNT(*) FROM generation_supersessions").fetchone()[0] == 0
