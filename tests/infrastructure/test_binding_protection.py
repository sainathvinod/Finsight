# Verifies: Phase 6.4cA BLOCKER 4 — guarded source-binding writes. bind() allows INITIAL_BIND and
# matching-fingerprint PATH_REBIND, but REFUSES to overwrite a trusted source identity with different
# bytes. A changed source can never become current through a generic write; it needs re-verification.
import os

import pytest

from finsight.app import build_app
from finsight.application.review_session import ReviewSession
from finsight.application.workflow import ReviewWorkflowService
from finsight.domain.lifecycle import SourceBinding
from finsight.infrastructure.lifecycle_repositories import LifecycleConstraintError
from finsight.domain.review_cycle import CycleState
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def _container(tmp_path):
    c = build_app(os.path.join(str(tmp_path), "fs.db"), FixedClock())
    ReviewWorkflowService(c.orch.engine).create_review("A", "May", "2026")   # cycle A exists (FK)
    return c


def _bind(c, doc, path, fp):
    with c.uow.atomic():
        c.source_binding_repo.bind(SourceBinding("A", doc, path, fp, "t", "actor"))


def test_initial_bind_records_identity(tmp_path):
    c = _container(tmp_path)
    _bind(c, "GED", "/p1", "fp1")
    b = c.source_binding_repo.get("A", "GED")
    assert b.last_known_path == "/p1" and b.source_fingerprint == "fp1"


def test_matching_fingerprint_rebind_updates_path_only(tmp_path):
    c = _container(tmp_path)
    _bind(c, "GED", "/p1", "fp1")
    _bind(c, "GED", "/moved/p2", "fp1")                      # same identity, new location
    b = c.source_binding_repo.get("A", "GED")
    assert b.last_known_path == "/moved/p2" and b.source_fingerprint == "fp1"


def test_different_fingerprint_cannot_overwrite_binding(tmp_path):
    c = _container(tmp_path)
    _bind(c, "GED", "/p1", "fp1")
    with pytest.raises(LifecycleConstraintError):
        _bind(c, "GED", "/p3", "DIFFERENT")
    b = c.source_binding_repo.get("A", "GED")
    assert b.last_known_path == "/p1" and b.source_fingerprint == "fp1"   # identity preserved


def _drive(tmp_path, target):
    c = build_app(os.path.join(str(tmp_path), "fs.db"), FixedClock())
    wf = ReviewWorkflowService(c.orch.engine); wf.create_review("A", "May", "2026")
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    s = ReviewSession("A"); wf.upload(s, ged, bud); wf.process(s)
    if target in (CycleState.VERIFIED, CycleState.ANALYZED):
        wf.verify(s)
    if target == CycleState.ANALYZED:
        wf.analyze(s)
    return c


def test_verified_binding_protected_from_overwrite(tmp_path):
    c = _drive(tmp_path, CycleState.VERIFIED)
    original = c.source_binding_repo.get("A", "GED")
    with pytest.raises(LifecycleConstraintError):
        _bind(c, "GED", "/attacker.xlsx", "changed-fingerprint")
    assert c.source_binding_repo.get("A", "GED").source_fingerprint == original.source_fingerprint


def test_analyzed_binding_protected_from_overwrite(tmp_path):
    c = _drive(tmp_path, CycleState.ANALYZED)
    original = c.source_binding_repo.get("A", "GED")
    with pytest.raises(LifecycleConstraintError):
        _bind(c, "GED", "/attacker.xlsx", "changed-fingerprint")
    assert c.source_binding_repo.get("A", "GED").source_fingerprint == original.source_fingerprint


def test_rollback_on_refused_overwrite_preserves_prior_binding(tmp_path):
    c = _container(tmp_path)
    _bind(c, "GED", "/p1", "fp1")
    # a transaction that attempts a refused overwrite alongside other writes rolls back entirely
    with pytest.raises(LifecycleConstraintError):
        with c.uow.atomic():
            c.source_binding_repo.bind(SourceBinding("A", "BUDGET", "/pb", "fpb", "t", "a"))  # would insert
            c.source_binding_repo.bind(SourceBinding("A", "GED", "/p9", "DIFFERENT", "t", "a"))  # refused
    assert c.source_binding_repo.get("A", "GED").last_known_path == "/p1"      # unchanged
    assert c.source_binding_repo.get("A", "BUDGET") is None                    # rolled back
