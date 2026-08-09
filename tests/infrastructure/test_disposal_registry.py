"""Workflow 1 verification for the external Disposal Registry foundation.

Traces: AC-07; ADR-V2-003; Technical Implementation Plan, Workflow 1.
"""
from __future__ import annotations

import json
import os
import stat

import pytest

from finsight.application.disposal_registry import (
    DisposalRegistryPort,
    HeadPointer,
    RegistryAdmissionError,
    RegistryAlreadyExistsError,
    RegistryEventKind,
    StartupAdmissionStatus,
)
from finsight.infrastructure.disposal_registry import FilesystemDisposalRegistry


KEY = bytes(range(32))


class Clock:
    def __init__(self):
        self.tick = 0

    def now(self):
        self.tick += 1
        return "2026-07-27T12:00:%02dZ" % self.tick


class Ids:
    def __init__(self):
        self.value = 0

    def __call__(self):
        self.value += 1
        return "id-%03d" % self.value


def registry(tmp_path):
    return FilesystemDisposalRegistry(
        str(tmp_path / "DisposalRegistry"),
        protection_key=KEY,
        clock=Clock(),
        id_factory=Ids(),
    )


def create(tmp_path):
    r = registry(tmp_path)
    admission = r.create_fresh("store-lineage-1", r"DOMAIN\reviewer")
    return r, admission


def test_adapter_satisfies_port_and_fresh_genesis_is_content_free(tmp_path):
    r, admission = create(tmp_path)

    assert isinstance(r, DisposalRegistryPort)
    assert admission.status is StartupAdmissionStatus.CREATED
    assert admission.admitted
    assert admission.verified_event_count == 1
    assert admission.head.committed.sequence == 1
    assert admission.head.pending is None
    events = r.read_events()
    assert len(events) == 1
    assert events[0].event_kind is RegistryEventKind.GENESIS
    assert events[0].store_lineage_id == "store-lineage-1"
    assert events[0].registry_lineage_id == admission.lineage.registry_lineage_id
    assert events[0].token_epoch == admission.lineage.token_epoch

    raw = (tmp_path / "DisposalRegistry" / r.JOURNAL_NAME).read_text("utf-8")
    for prohibited in ("amount", "account_number", "department", "workbook", "finding"):
        assert prohibited not in raw.lower()


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission contract")
def test_registry_paths_have_restrictive_permissions(tmp_path):
    r, _ = create(tmp_path)
    root = tmp_path / "DisposalRegistry"
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert stat.S_IMODE((root / r.JOURNAL_NAME).stat().st_mode) == 0o600
    assert stat.S_IMODE((root / r.HEAD_NAME).stat().st_mode) == 0o600


@pytest.mark.skipif(os.name != "posix", reason="POSIX group permission contract")
def test_machine_shared_registry_uses_deployment_group_permissions(
    monkeypatch, tmp_path
):
    import grp

    root = tmp_path / "SharedRegistry"
    root.mkdir()
    group_name = grp.getgrgid(root.stat().st_gid).gr_name
    monkeypatch.setenv("FINSIGHT_POSIX_ACCESS_GROUP", group_name)
    r = FilesystemDisposalRegistry(
        str(root),
        protection_key=KEY,
        clock=Clock(),
        id_factory=Ids(),
        machine_shared=True,
    )

    r.create_fresh("store-lineage-1", r"DOMAIN\reviewer")

    assert stat.S_IMODE(root.stat().st_mode) == 0o770
    assert stat.S_IMODE((root / r.JOURNAL_NAME).stat().st_mode) == 0o660
    assert stat.S_IMODE((root / r.HEAD_NAME).stat().st_mode) == 0o660
    r.admit_startup()


def test_reopen_admits_same_immutable_lineage_and_epoch(tmp_path):
    _, created = create(tmp_path)
    reopened = registry(tmp_path).admit_startup()
    assert reopened.status is StartupAdmissionStatus.ADMITTED
    assert reopened.lineage == created.lineage
    assert reopened.head.committed == created.head.committed


def test_generic_append_is_canonical_chained_and_promoted(tmp_path):
    r, created = create(tmp_path)
    event = r.append_event(
        RegistryEventKind.FORMAT_MIGRATION,
        "operation-2",
        "store-lineage-1",
        r"DOMAIN\reviewer",
        reason_code="FORMAT_UPGRADE",
        outcome_code="COMPLETED",
    )
    assert event.sequence == 2
    assert event.prior_hash == created.head.committed.tail_hash
    admitted = r.admit_startup()
    assert admitted.status is StartupAdmissionStatus.ADMITTED
    assert admitted.head.committed == HeadPointer(2, event.entry_hash, "operation-2")
    assert admitted.head.pending is None

    lines = (tmp_path / "DisposalRegistry" / r.JOURNAL_NAME).read_bytes().splitlines()
    assert len(lines) == 2
    for line in lines:
        value = json.loads(line)
        assert line == json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        ).encode()


def test_audit_head_anchors_are_monotonic_and_content_free(tmp_path):
    r, _ = create(tmp_path)
    first = r.advance_audit_anchor(
        "audit_review_rev_001", 1, "a" * 64, r"DOMAIN\reviewer"
    )
    same = r.advance_audit_anchor(
        "audit_review_rev_001", 1, "a" * 64, r"DOMAIN\reviewer"
    )
    second = r.advance_audit_anchor(
        "audit_review_rev_001", 2, "b" * 64, r"DOMAIN\reviewer"
    )

    assert first == same
    assert second.sequence == first.sequence + 1
    assert r.audit_anchor("audit_review_rev_001") == (2, "b" * 64)
    assert r.audit_anchors() == {
        "audit_review_rev_001": (2, "b" * 64)
    }
    with pytest.raises(RegistryAdmissionError, match="monotonic"):
        r.advance_audit_anchor(
            "audit_review_rev_001", 1, "a" * 64, r"DOMAIN\reviewer"
        )
    raw = (tmp_path / "DisposalRegistry" / r.JOURNAL_NAME).read_text("utf-8")
    for prohibited in ("amount", "department", "account_number", "description"):
        assert prohibited not in raw.lower()


def test_committed_disposal_retires_only_its_hashed_audit_anchor(tmp_path):
    r, _ = create(tmp_path)
    disposed_stream = "audit_review_rev_001"
    retained_stream = "audit_review_rev_002"
    r.advance_audit_anchor(
        disposed_stream, 1, "a" * 64, r"DOMAIN\reviewer"
    )
    r.advance_audit_anchor(
        retained_stream, 1, "b" * 64, r"DOMAIN\reviewer"
    )
    import hashlib

    prepared = r.prepare_disposal(
        "review-disposal-001",
        r"DOMAIN\reviewer",
        scope_token="c" * 64,
        audit_stream_token=hashlib.sha256(
            disposed_stream.encode("utf-8")
        ).hexdigest(),
        inventory_fingerprint="d" * 64,
    )
    assert prepared.event_kind is RegistryEventKind.DISPOSAL_PREPARED
    assert r.audit_anchor(disposed_stream) == (1, "a" * 64)

    committed = r.commit_disposal(
        "review-disposal-001", r"DOMAIN\reviewer"
    )

    assert committed.event_kind is RegistryEventKind.DISPOSAL_COMMITTED
    assert r.audit_anchor(disposed_stream) is None
    assert r.audit_anchor(retained_stream) == (1, "b" * 64)
    assert set(r.audit_anchors()) == {retained_stream}
    with pytest.raises(RegistryAdmissionError, match="retired"):
        r.advance_audit_anchor(
            disposed_stream, 2, "e" * 64, r"DOMAIN\reviewer"
        )
    assert disposed_stream not in repr(prepared.control_payload)
    assert disposed_stream not in repr(committed.control_payload)


def test_authorization_manifest_anchor_rejects_rollback_and_equivocation(tmp_path):
    r, _ = create(tmp_path)
    accepted = r.advance_authorization_manifest_anchor(
        3, "c" * 64, "deployment-key-1", r"DOMAIN\reviewer"
    )
    repeated = r.advance_authorization_manifest_anchor(
        3, "c" * 64, "deployment-key-1", r"DOMAIN\reviewer"
    )

    assert accepted == repeated
    assert r.authorization_manifest_anchor() == (
        3,
        "c" * 64,
        "deployment-key-1",
    )
    with pytest.raises(RegistryAdmissionError, match="rollback"):
        r.advance_authorization_manifest_anchor(
            2, "b" * 64, "deployment-key-1", r"DOMAIN\reviewer"
        )
    with pytest.raises(RegistryAdmissionError, match="equivocation"):
        r.advance_authorization_manifest_anchor(
            3, "d" * 64, "deployment-key-1", r"DOMAIN\reviewer"
        )


def test_fresh_creation_never_overwrites_existing_authority(tmp_path):
    r, _ = create(tmp_path)
    with pytest.raises(RegistryAlreadyExistsError):
        r.create_fresh("store-lineage-2", r"DOMAIN\reviewer")


def test_recovery_lock_refuses_a_concurrent_process_boundary(tmp_path):
    r, _ = create(tmp_path)
    from finsight.infrastructure.single_instance import SingleInstanceLock

    lock = SingleInstanceLock(str(tmp_path / "DisposalRegistry" / ".registry.lock"))
    assert lock.acquire()
    try:
        with pytest.raises(RegistryAdmissionError, match="in use"):
            r.admit_startup()
    finally:
        lock.release()


@pytest.mark.parametrize("missing_name", [
    FilesystemDisposalRegistry.JOURNAL_NAME,
    FilesystemDisposalRegistry.HEAD_NAME,
])
def test_startup_fails_closed_when_authority_file_is_missing(tmp_path, missing_name):
    r, _ = create(tmp_path)
    (tmp_path / "DisposalRegistry" / missing_name).unlink()
    with pytest.raises(RegistryAdmissionError):
        r.admit_startup()


def test_startup_fails_closed_on_truncated_journal(tmp_path):
    r, _ = create(tmp_path)
    journal = tmp_path / "DisposalRegistry" / r.JOURNAL_NAME
    journal.write_bytes(journal.read_bytes()[:-1])
    with pytest.raises(RegistryAdmissionError, match="truncated"):
        r.admit_startup()


def test_startup_fails_closed_on_journal_tampering(tmp_path):
    r, _ = create(tmp_path)
    journal = tmp_path / "DisposalRegistry" / r.JOURNAL_NAME
    raw = journal.read_text("utf-8")
    journal.write_text(raw.replace("FRESH_INSTALL", "ALTERED_STATE"), encoding="utf-8")
    os.chmod(journal, 0o600)
    with pytest.raises(RegistryAdmissionError):
        r.admit_startup()


def test_startup_fails_closed_on_head_tampering(tmp_path):
    r, _ = create(tmp_path)
    head = tmp_path / "DisposalRegistry" / r.HEAD_NAME
    value = json.loads(head.read_text("utf-8"))
    value["committed"]["tail_hash"] = "f" * 64
    # The registry reads and writes the head as bytes, so the tampered copy must be written as
    # bytes too. write_text() translates "\n" to "\r\n" on Windows, which corrupts the record
    # before the authentication check is reached and raises a different admission error.
    head.write_bytes(
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    )
    os.chmod(head, 0o600)
    with pytest.raises(RegistryAdmissionError, match="authentication"):
        r.admit_startup()


def test_valid_pending_entry_is_promoted_on_startup(tmp_path):
    r, admission = create(tmp_path)
    lineage = admission.lineage
    event = r._build_event(
        lineage=lineage,
        sequence=2,
        prior_hash=admission.head.committed.tail_hash,
        event_kind=RegistryEventKind.FORMAT_MIGRATION,
        operation_id="operation-2",
        store_lineage_id="store-lineage-1",
        actor_id=r"DOMAIN\reviewer",
        reason_code="FORMAT_UPGRADE",
        outcome_code="COMPLETED",
    )
    r._append_journal(event)
    r._write_head(lineage, admission.head.committed, r._pointer(event),
                  updated_at="2026-07-27T12:01:00Z")

    recovered = registry(tmp_path).admit_startup()
    assert recovered.status is StartupAdmissionStatus.RECOVERED_PENDING
    assert recovered.head.committed == r._pointer(event)
    assert recovered.head.pending is None


def test_pending_without_entry_clears_only_from_matching_committed_anchor(tmp_path):
    r, admission = create(tmp_path)
    fake_pending = HeadPointer(2, "a" * 64, "operation-2")
    r._write_head(admission.lineage, admission.head.committed, fake_pending,
                  updated_at="2026-07-27T12:01:00Z")

    recovered = registry(tmp_path).admit_startup()
    assert recovered.status is StartupAdmissionStatus.RECOVERED_CLEARED_PENDING
    assert recovered.head.committed == admission.head.committed
    assert recovered.head.pending is None


def test_pending_without_entry_fails_if_committed_anchor_conflicts(tmp_path):
    r, admission = create(tmp_path)
    conflicting = HeadPointer(
        admission.head.committed.sequence,
        "b" * 64,
        admission.head.committed.operation_id,
    )
    r._write_head(
        admission.lineage,
        conflicting,
        HeadPointer(2, "a" * 64, "operation-2"),
        updated_at="2026-07-27T12:01:00Z",
    )
    with pytest.raises(RegistryAdmissionError, match="committed"):
        registry(tmp_path).admit_startup()


def test_single_valid_suffix_is_adopted_after_append_before_pending_crash(tmp_path):
    r, admission = create(tmp_path)
    event = r._build_event(
        lineage=admission.lineage,
        sequence=2,
        prior_hash=admission.head.committed.tail_hash,
        event_kind=RegistryEventKind.FORMAT_MIGRATION,
        operation_id="operation-2",
        store_lineage_id="store-lineage-1",
        actor_id=r"DOMAIN\reviewer",
        reason_code="FORMAT_UPGRADE",
        outcome_code="COMPLETED",
    )
    r._append_journal(event)  # simulate death before pending head publication

    recovered = registry(tmp_path).admit_startup()
    assert recovered.status is StartupAdmissionStatus.RECOVERED_APPENDED_SUFFIX
    assert recovered.head.committed == r._pointer(event)
    assert recovered.head.pending is None


def test_ambiguous_multiple_suffix_entries_fail_closed(tmp_path):
    r, admission = create(tmp_path)
    event2 = r._build_event(
        lineage=admission.lineage, sequence=2,
        prior_hash=admission.head.committed.tail_hash,
        event_kind=RegistryEventKind.FORMAT_MIGRATION, operation_id="operation-2",
        store_lineage_id="store-lineage-1", actor_id=r"DOMAIN\reviewer",
        reason_code="", outcome_code="",
    )
    event3 = r._build_event(
        lineage=admission.lineage, sequence=3, prior_hash=event2.entry_hash,
        event_kind=RegistryEventKind.FORMAT_MIGRATION, operation_id="operation-3",
        store_lineage_id="store-lineage-1", actor_id=r"DOMAIN\reviewer",
        reason_code="", outcome_code="",
    )
    r._append_journal(event2)
    r._append_journal(event3)
    with pytest.raises(RegistryAdmissionError, match="ambiguous"):
        registry(tmp_path).admit_startup()
