"""Workflow 1 tests for attributable, transactional HMAC audit streams.

Traces: FR-189/FR-190, NFR-090, AC-02, ADR-V2-003.
"""
from __future__ import annotations

import sqlite3
from types import SimpleNamespace

import pytest

from finsight.domain.identity import Actor
from finsight.infrastructure.audit_stream import (
    AuditIntegrityError,
    AuditScope,
    AuditStreamSqlite,
)
from finsight.infrastructure.disposal_registry import FilesystemDisposalRegistry
from finsight.infrastructure.migrations.runner import run_migrations
from finsight.infrastructure.persistence import SqliteUnitOfWork


AUDIT_KEY = bytes(range(32))
ACTOR = Actor("WINDOWS:S-1-5-21-100", r"CORP\reviewer", "WINDOWS_ACCOUNT")


class Clock:
    def now(self):
        return "2026-07-27T18:00:00Z"


class Ids:
    def __init__(self):
        self.value = 0

    def __call__(self):
        self.value += 1
        return "%03d" % self.value


def _context(path=":memory:"):
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys=ON")
    run_migrations(connection)
    dal = SimpleNamespace(conn=connection)
    return (
        connection,
        AuditStreamSqlite(dal, AUDIT_KEY, Clock(), Ids()),
        SqliteUnitOfWork(dal),
    )


def _anchored_context(tmp_path):
    connection = sqlite3.connect(tmp_path / "audit.db")
    connection.execute("PRAGMA foreign_keys=ON")
    run_migrations(connection)
    dal = SimpleNamespace(conn=connection)
    uow = SqliteUnitOfWork(dal)
    registry = FilesystemDisposalRegistry(
        str(tmp_path / "registry"),
        protection_key=b"r" * 32,
        clock=Clock(),
        id_factory=Ids(),
    )
    registry.create_fresh("store-001", ACTOR.actor_id)
    audit = AuditStreamSqlite(
        dal,
        AUDIT_KEY,
        Clock(),
        Ids(),
        anchor_registry=registry,
        after_commit=uow.after_commit,
    )
    return connection, audit, uow, registry


@pytest.mark.audit
def test_review_events_form_a_verified_hmac_chain_with_ordered_scopes():
    connection, audit, uow = _context()
    with uow.atomic():
        created = audit.append(
            review_id="rev_001",
            event_type="review_created",
            actor=ACTOR,
            payload={"status": "Draft"},
            correlation_id="corr-001",
            scopes=(
                AuditScope("Review", "rev_001"),
                AuditScope("WorkingCandidate", "cand_001"),
            ),
        )
        reopened = audit.append(
            review_id="rev_001",
            event_type="review_reopened",
            actor=ACTOR,
            payload={"status": "Draft"},
            correlation_id="corr-002",
            scopes=(AuditScope("Review", "rev_001"),),
        )

    assert created.stream_sequence == 1
    assert reopened.stream_sequence == 2
    assert reopened.prior_hmac == created.event_hmac
    assert [scope.resource_type for scope in audit.events(review_id="rev_001")[0].scopes] == [
        "Review",
        "WorkingCandidate",
    ]
    audit.verify_all()
    connection.close()


@pytest.mark.audit
def test_transaction_failure_rolls_back_event_scopes_and_stream_head():
    connection, audit, uow = _context()
    with pytest.raises(RuntimeError, match="injected"):
        with uow.atomic():
            audit.append(
                review_id="rev_rollback",
                event_type="review_created",
                actor=ACTOR,
                payload={"status": "Draft"},
                correlation_id="corr-rollback",
                scopes=(AuditScope("Review", "rev_rollback"),),
            )
            raise RuntimeError("injected transaction failure")

    assert connection.execute("SELECT COUNT(*) FROM v2_audit_events").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM v2_audit_event_scopes").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM v2_audit_streams").fetchone()[0] == 0
    connection.close()


@pytest.mark.audit
def test_database_triggers_reject_in_place_audit_mutation_and_deletion():
    connection, audit, uow = _context()
    with uow.atomic():
        event = audit.append(
            stream_type="SECURITY",
            event_type="identity_resolved",
            actor=ACTOR,
            payload={"source": "WINDOWS_ACCOUNT"},
            correlation_id="corr-security",
        )

    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        connection.execute(
            "UPDATE v2_audit_events SET outcome='ALTERED' WHERE event_id=?",
            (event.event_id,),
        )
    connection.rollback()
    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        connection.execute(
            "DELETE FROM v2_audit_events WHERE event_id=?",
            (event.event_id,),
        )
    connection.rollback()
    audit.verify_all()
    connection.close()


@pytest.mark.audit
def test_offline_event_tampering_is_detected_by_chain_verification():
    connection, audit, uow = _context()
    with uow.atomic():
        event = audit.append(
            review_id="rev_tamper",
            event_type="review_created",
            actor=ACTOR,
            payload={"status": "Draft"},
            correlation_id="corr-tamper",
        )

    # Model an offline database attacker who can remove a trigger. HMAC verification,
    # not the trigger alone, remains the tamper-evidence boundary.
    connection.execute("DROP TRIGGER v2_audit_events_no_update")
    connection.execute(
        "UPDATE v2_audit_events SET canonical_payload=? WHERE event_id=?",
        ('{"status":"Closed"}', event.event_id),
    )
    connection.commit()
    with pytest.raises(AuditIntegrityError, match="HMAC"):
        audit.verify_all()
    connection.close()


@pytest.mark.audit
def test_wrong_audit_key_fails_closed_against_existing_stream():
    connection, audit, uow = _context()
    with uow.atomic():
        audit.append(
            review_id="rev_wrong_key",
            event_type="review_created",
            actor=ACTOR,
            payload={"status": "Draft"},
            correlation_id="corr-wrong-key",
        )

    wrong = AuditStreamSqlite(
        SimpleNamespace(conn=connection),
        b"x" * 32,
        Clock(),
        Ids(),
    )
    with pytest.raises(AuditIntegrityError, match="genesis"):
        wrong.verify_all()
    connection.close()


@pytest.mark.audit
def test_external_anchor_detects_tail_deletion_even_when_database_head_is_rewound(
    tmp_path,
):
    connection, audit, uow, registry = _anchored_context(tmp_path)
    with uow.atomic():
        events = [
            audit.append(
                review_id="rev_tail",
                event_type=f"event_{index}",
                actor=ACTOR,
                payload={"index": index},
                correlation_id=f"corr-{index}",
            )
            for index in range(1, 4)
        ]
    assert registry.audit_anchor("audit_review_rev_tail") == (
        3,
        events[2].event_hmac,
    )

    connection.execute("DROP TRIGGER v2_audit_events_no_delete")
    connection.execute("DROP TRIGGER v2_audit_event_scopes_no_delete")
    connection.execute(
        "DELETE FROM v2_audit_event_scopes WHERE event_id=?", (events[2].event_id,)
    )
    connection.execute(
        "DELETE FROM v2_audit_events WHERE event_id=?", (events[2].event_id,)
    )
    connection.execute(
        "UPDATE v2_audit_streams SET current_sequence=2,current_hmac=?,revision=2 "
        "WHERE stream_id='audit_review_rev_tail'",
        (events[1].event_hmac,),
    )
    connection.commit()

    with pytest.raises(AuditIntegrityError, match="External audit anchor"):
        audit.verify_all()
    connection.close()


@pytest.mark.audit
@pytest.mark.parametrize("deleted_index", [0, 1])
def test_audit_chain_detects_first_and_middle_event_deletion(
    tmp_path, deleted_index
):
    connection, audit, uow, _registry = _anchored_context(tmp_path)
    with uow.atomic():
        events = [
            audit.append(
                review_id="rev_gap",
                event_type=f"event_{index}",
                actor=ACTOR,
                payload={"index": index},
                correlation_id=f"corr-{index}",
            )
            for index in range(1, 4)
        ]
    deleted = events[deleted_index]
    connection.execute("DROP TRIGGER v2_audit_events_no_delete")
    connection.execute("DROP TRIGGER v2_audit_event_scopes_no_delete")
    connection.execute(
        "DELETE FROM v2_audit_event_scopes WHERE event_id=?", (deleted.event_id,)
    )
    connection.execute(
        "DELETE FROM v2_audit_events WHERE event_id=?", (deleted.event_id,)
    )
    connection.commit()

    with pytest.raises(AuditIntegrityError, match="sequence|prior"):
        audit.verify_all()
    connection.close()


@pytest.mark.audit
def test_rolled_back_database_stream_is_rejected_by_external_anchor(tmp_path):
    connection, audit, uow, registry = _anchored_context(tmp_path)
    with uow.atomic():
        first = audit.append(
            review_id="rev_rollback",
            event_type="first",
            actor=ACTOR,
            payload={},
            correlation_id="corr-first",
        )
    backup = sqlite3.connect(tmp_path / "older.db")
    connection.backup(backup)
    backup.close()
    with uow.atomic():
        second = audit.append(
            review_id="rev_rollback",
            event_type="second",
            actor=ACTOR,
            payload={},
            correlation_id="corr-second",
        )
    assert registry.audit_anchor("audit_review_rev_rollback") == (
        2,
        second.event_hmac,
    )
    connection.close()

    older = sqlite3.connect(tmp_path / "older.db")
    older_dal = SimpleNamespace(conn=older)
    older_audit = AuditStreamSqlite(
        older_dal,
        AUDIT_KEY,
        Clock(),
        Ids(),
        anchor_registry=registry,
        after_commit=SqliteUnitOfWork(older_dal).after_commit,
    )
    assert first.stream_sequence == 1
    with pytest.raises(AuditIntegrityError, match="External audit anchor"):
        older_audit.verify_all()
    older.close()


@pytest.mark.audit
def test_anchor_publication_failure_locks_all_later_uow_writes(tmp_path):
    connection = sqlite3.connect(tmp_path / "audit-lock.db")
    connection.execute("PRAGMA foreign_keys=ON")
    run_migrations(connection)
    dal = SimpleNamespace(conn=connection)
    uow = SqliteUnitOfWork(dal)
    registry = FilesystemDisposalRegistry(
        str(tmp_path / "registry-lock"),
        protection_key=b"r" * 32,
        clock=Clock(),
        id_factory=Ids(),
    )
    registry.create_fresh("store-locked", ACTOR.actor_id)

    class _FaultingRegistry:
        fail = True

        def advance_audit_anchor(self, *args):
            if self.fail:
                raise OSError("injected external-anchor outage")
            return registry.advance_audit_anchor(*args)

        def audit_anchor(self, stream_id):
            return registry.audit_anchor(stream_id)

        def audit_anchors(self):
            return registry.audit_anchors()

    faulting = _FaultingRegistry()
    audit = AuditStreamSqlite(
        dal,
        AUDIT_KEY,
        Clock(),
        Ids(),
        anchor_registry=faulting,
        after_commit=uow.after_commit,
    )

    with pytest.raises(OSError, match="external-anchor outage"):
        with uow.atomic():
            audit.append(
                review_id="rev_locked",
                event_type="first",
                actor=ACTOR,
                payload={},
                correlation_id="corr-first",
            )

    assert uow.last_commit_completed
    assert uow.control_plane_faulted
    assert connection.execute(
        "SELECT COUNT(*) FROM v2_audit_events"
    ).fetchone()[0] == 1

    with pytest.raises(RuntimeError, match="protected writes are locked"):
        with uow.atomic():
            audit.append(
                review_id="rev_locked",
                event_type="must_not_commit",
                actor=ACTOR,
                payload={},
                correlation_id="corr-second",
            )
    assert connection.execute(
        "SELECT COUNT(*) FROM v2_audit_events"
    ).fetchone()[0] == 1

    faulting.fail = False
    audit.verify_all(reconcile_committed_gap=True)
    uow.clear_control_plane_fault_after_verified_reconciliation()
    with uow.atomic():
        audit.append(
            review_id="rev_locked",
            event_type="second",
            actor=ACTOR,
            payload={},
            correlation_id="corr-third",
        )
    assert connection.execute(
        "SELECT COUNT(*) FROM v2_audit_events"
    ).fetchone()[0] == 2
    connection.close()
