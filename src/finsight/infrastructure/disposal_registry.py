"""Filesystem adapter for the content-free Disposal Registry.

Implements ADR-V2-003 / AC-07's Workflow 1 foundation:

* canonical JSON-lines append-only journal;
* SHA-256 entry chain and purpose-separated HMAC-SHA-256 authentication;
* authenticated committed/pending head outside the replaceable database;
* deterministic startup reconciliation for interrupted head publication; and
* restrictive POSIX permissions.

The injected ``protection_key`` represents key bytes already unwrapped by the
platform protection adapter (DPAPI/Keychain in a production composition).  Key
storage and backup/disposal business operations are deliberately out of scope.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import stat
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple

from finsight.application.disposal_registry import (
    GENESIS_PRIOR_HASH,
    REGISTRY_FORMAT_VERSION,
    REGISTRY_SECURITY_PROFILE,
    DisposalRegistryPort,
    HeadPointer,
    ProtectedHead,
    RegistryAdmissionError,
    RegistryAlreadyExistsError,
    RegistryEvent,
    RegistryEventKind,
    RegistryLineage,
    RegistryValidationError,
    StartupAdmission,
    StartupAdmissionStatus,
)


_EVENT_KEYS = frozenset({
    "registry_lineage_id", "token_epoch", "sequence", "prior_hash", "event_id",
    "event_kind", "operation_id", "store_lineage_id", "actor_id", "occurred_at",
    "reason_code", "outcome_code", "control_payload", "record_mac", "entry_hash",
})
_EVENT_CORE_KEYS = _EVENT_KEYS - {"record_mac", "entry_hash"}
_HEAD_PAYLOAD_KEYS = frozenset({
    "registry_lineage_id", "token_epoch", "format_version", "security_profile",
    "committed", "pending", "updated_at",
})
_HEAD_KEYS = _HEAD_PAYLOAD_KEYS | {"protection_mac"}
_POINTER_KEYS = frozenset({"sequence", "tail_hash", "operation_id"})

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/\\-]{0,127}$")
_CODE_RE = re.compile(r"^(?:|[A-Z][A-Z0-9_.-]{0,63})$")
_HEX_64_RE = re.compile(r"^[0-9a-f]{64}$")
_AUDIT_ANCHOR_KEYS = frozenset({"stream_id", "sequence", "event_hmac"})
_MANIFEST_ANCHOR_KEYS = frozenset({"version", "fingerprint", "key_id"})
_DISPOSAL_KEYS = frozenset(
    {"scope_token", "audit_stream_token", "inventory_fingerprint"}
)


def _canonical(value: Any) -> bytes:
    """Canonical encoding for the closed, float-free registry schema."""
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _purpose_mac(key: bytes, purpose: bytes, payload: Dict[str, Any]) -> str:
    return hmac.new(key, purpose + b"\0" + _canonical(payload), hashlib.sha256).hexdigest()


def _entry_hash(core: Dict[str, Any], record_mac: str) -> str:
    return hashlib.sha256(_canonical({**core, "record_mac": record_mac})).hexdigest()


def _clock_now(clock: Any) -> str:
    value = clock.now() if hasattr(clock, "now") else clock()
    if not isinstance(value, str) or not value or len(value) > 64:
        raise RegistryValidationError("clock must return a non-empty bounded timestamp string")
    return value


def _validate_id(label: str, value: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise RegistryValidationError("%s must be an opaque bounded identifier" % label)
    return value


def _validate_code(label: str, value: str) -> str:
    if not isinstance(value, str) or _CODE_RE.fullmatch(value) is None:
        raise RegistryValidationError("%s must be an empty or uppercase bounded code" % label)
    return value


def _validate_control_payload(
    event_kind: RegistryEventKind,
    value: Optional[Mapping[str, object]],
) -> Dict[str, object]:
    payload = {} if value is None else dict(value)
    if event_kind is RegistryEventKind.AUDIT_HEAD_ADVANCED:
        if frozenset(payload) != _AUDIT_ANCHOR_KEYS:
            raise RegistryValidationError("audit-head control payload schema is invalid")
        _validate_id("stream_id", payload["stream_id"])
        sequence = payload["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            raise RegistryValidationError("audit-head sequence must be a positive integer")
        if (
            not isinstance(payload["event_hmac"], str)
            or _HEX_64_RE.fullmatch(payload["event_hmac"]) is None
        ):
            raise RegistryValidationError("audit-head event HMAC is invalid")
        return payload
    if event_kind is RegistryEventKind.AUTHORIZATION_MANIFEST_ACCEPTED:
        if frozenset(payload) != _MANIFEST_ANCHOR_KEYS:
            raise RegistryValidationError(
                "authorization-manifest control payload schema is invalid"
            )
        version = payload["version"]
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise RegistryValidationError(
                "authorization-manifest version must be a positive integer"
            )
        if (
            not isinstance(payload["fingerprint"], str)
            or _HEX_64_RE.fullmatch(payload["fingerprint"]) is None
        ):
            raise RegistryValidationError(
                "authorization-manifest fingerprint is invalid"
            )
        _validate_id("key_id", payload["key_id"])
        return payload
    if event_kind in (
        RegistryEventKind.DISPOSAL_PREPARED,
        RegistryEventKind.DISPOSAL_COMMITTED,
        RegistryEventKind.DISPOSAL_ABORTED,
    ):
        if frozenset(payload) != _DISPOSAL_KEYS:
            raise RegistryValidationError("disposal control payload schema is invalid")
        for field in sorted(_DISPOSAL_KEYS):
            if (
                not isinstance(payload[field], str)
                or _HEX_64_RE.fullmatch(payload[field]) is None
            ):
                raise RegistryValidationError(
                    f"disposal {field.replace('_', ' ')} is invalid"
                )
        return payload
    if payload:
        raise RegistryValidationError(
            "this registry event kind does not accept a control payload"
        )
    return payload


class FilesystemDisposalRegistry(DisposalRegistryPort):
    """Machine-local filesystem authority.

    The directory must live outside every SQLCipher store and ordinary backup.
    Existing authorities are never automatically recreated: missing or invalid
    state makes ``admit_startup`` fail closed.
    """

    JOURNAL_NAME = "registry.journal.jsonl"
    HEAD_NAME = "registry.head.json"

    def __init__(
        self,
        root: str,
        *,
        protection_key: bytes,
        clock: Any,
        id_factory: Callable[[], str],
        machine_shared: bool = False,
    ):
        if not isinstance(protection_key, bytes) or len(protection_key) < 32:
            raise ValueError("protection_key must contain at least 32 bytes")
        if not callable(id_factory):
            raise TypeError("id_factory must be callable")
        self._root = Path(root)
        self._journal = self._root / self.JOURNAL_NAME
        self._head = self._root / self.HEAD_NAME
        self._key = bytes(protection_key)
        self._clock = clock
        self._id_factory = id_factory
        self._machine_shared = bool(machine_shared)
        self._thread_lock = threading.RLock()

    # ---- public port -----------------------------------------------------
    def create_fresh(self, store_lineage_id: str, actor_id: str) -> StartupAdmission:
        store_lineage_id = _validate_id("store_lineage_id", store_lineage_id)
        actor_id = _validate_id("actor_id", actor_id)
        with self._exclusive(create_root=True):
            self._prepare_fresh_directory()
            lineage = RegistryLineage(
                registry_lineage_id=_validate_id("registry_lineage_id", self._id_factory()),
                token_epoch=_validate_id("token_epoch", self._id_factory()),
                format_version=REGISTRY_FORMAT_VERSION,
                security_profile=REGISTRY_SECURITY_PROFILE,
                created_at=_clock_now(self._clock),
            )
            event = self._build_event(
                lineage=lineage,
                sequence=1,
                prior_hash=GENESIS_PRIOR_HASH,
                event_kind=RegistryEventKind.GENESIS,
                operation_id=_validate_id("operation_id", self._id_factory()),
                store_lineage_id=store_lineage_id,
                actor_id=actor_id,
                reason_code="FRESH_INSTALL",
                outcome_code="CREATED",
                control_payload={},
                occurred_at=lineage.created_at,
            )
            self._create_journal(event)
            pointer = self._pointer(event)
            head = self._write_head(
                lineage, pointer, None, updated_at=_clock_now(self._clock)
            )
            return StartupAdmission(
                StartupAdmissionStatus.CREATED, lineage, head, verified_event_count=1
            )

    def admit_startup(self) -> StartupAdmission:
        with self._exclusive():
            return self._admit_locked()

    def append_event(
        self,
        event_kind: RegistryEventKind,
        operation_id: str,
        store_lineage_id: str,
        actor_id: str,
        *,
        reason_code: str = "",
        outcome_code: str = "",
        control_payload: Optional[Mapping[str, object]] = None,
    ) -> RegistryEvent:
        try:
            event_kind = (
                event_kind
                if isinstance(event_kind, RegistryEventKind)
                else RegistryEventKind(event_kind)
            )
        except (TypeError, ValueError) as exc:
            raise RegistryValidationError("event_kind is not an admitted registry event") from exc
        if event_kind is RegistryEventKind.GENESIS:
            raise RegistryValidationError("GENESIS may be created only by create_fresh")
        if event_kind in (
            RegistryEventKind.DISPOSAL_PREPARED,
            RegistryEventKind.DISPOSAL_COMMITTED,
            RegistryEventKind.DISPOSAL_ABORTED,
        ):
            raise RegistryValidationError(
                "disposal events require the governed disposal methods"
            )
        operation_id = _validate_id("operation_id", operation_id)
        store_lineage_id = _validate_id("store_lineage_id", store_lineage_id)
        actor_id = _validate_id("actor_id", actor_id)
        reason_code = _validate_code("reason_code", reason_code)
        outcome_code = _validate_code("outcome_code", outcome_code)
        control = _validate_control_payload(event_kind, control_payload)

        with self._exclusive():
            admission = self._admit_locked()
            return self._append_locked(
                admission,
                event_kind=event_kind,
                operation_id=operation_id,
                store_lineage_id=store_lineage_id,
                actor_id=actor_id,
                reason_code=reason_code,
                outcome_code=outcome_code,
                control_payload=control,
            )

    def read_events(self) -> Tuple[RegistryEvent, ...]:
        with self._exclusive():
            self._admit_locked()
            return self._read_and_verify_events()

    def advance_audit_anchor(
        self,
        stream_id: str,
        sequence: int,
        event_hmac: str,
        actor_id: str,
    ) -> RegistryEvent:
        stream_id = _validate_id("stream_id", stream_id)
        actor_id = _validate_id("actor_id", actor_id)
        payload = _validate_control_payload(
            RegistryEventKind.AUDIT_HEAD_ADVANCED,
            {
                "stream_id": stream_id,
                "sequence": sequence,
                "event_hmac": event_hmac,
            },
        )
        with self._exclusive():
            admission = self._admit_locked()
            events = self._read_and_verify_events()
            if self._audit_stream_retired(events, stream_id):
                raise RegistryAdmissionError(
                    "a retired audit stream cannot be advanced"
                )
            current_event, current = self._audit_anchor_from_events(events, stream_id)
            candidate = (sequence, event_hmac)
            if current == candidate and current_event is not None:
                return current_event
            if current is not None and (
                sequence != current[0] + 1 or sequence < current[0]
            ):
                raise RegistryAdmissionError(
                    "audit anchor is not the next monotonic stream head"
                )
            if current is None and sequence != 1:
                raise RegistryAdmissionError(
                    "first audit anchor must identify stream sequence one"
                )
            return self._append_locked(
                admission,
                event_kind=RegistryEventKind.AUDIT_HEAD_ADVANCED,
                operation_id=_validate_id(
                    "operation_id", "audit-anchor:" + self._id_factory()
                ),
                store_lineage_id=events[0].store_lineage_id,
                actor_id=actor_id,
                reason_code="AUDIT_HEAD",
                outcome_code="ADVANCED",
                control_payload=payload,
            )

    def audit_anchor(self, stream_id: str) -> Optional[Tuple[int, str]]:
        stream_id = _validate_id("stream_id", stream_id)
        with self._exclusive():
            self._admit_locked()
            events = self._read_and_verify_events()
            if self._audit_stream_retired(events, stream_id):
                return None
            _event, value = self._audit_anchor_from_events(
                events, stream_id
            )
            return value

    def audit_anchors(self) -> Mapping[str, Tuple[int, str]]:
        with self._exclusive():
            self._admit_locked()
            anchors: Dict[str, Tuple[int, str]] = {}
            events = self._read_and_verify_events()
            stream_ids = {
                str(event.control_payload["stream_id"])
                for event in events
                if event.event_kind is RegistryEventKind.AUDIT_HEAD_ADVANCED
            }
            for stream_id in stream_ids:
                if self._audit_stream_retired(events, stream_id):
                    continue
                _event, value = self._audit_anchor_from_events(events, stream_id)
                if value is not None:
                    anchors[stream_id] = value
            return anchors

    def advance_authorization_manifest_anchor(
        self,
        version: int,
        fingerprint: str,
        key_id: str,
        actor_id: str,
    ) -> RegistryEvent:
        actor_id = _validate_id("actor_id", actor_id)
        payload = _validate_control_payload(
            RegistryEventKind.AUTHORIZATION_MANIFEST_ACCEPTED,
            {
                "version": version,
                "fingerprint": fingerprint,
                "key_id": key_id,
            },
        )
        with self._exclusive():
            admission = self._admit_locked()
            events = self._read_and_verify_events()
            current_event, current = self._manifest_anchor_from_events(events)
            candidate = (version, fingerprint, key_id)
            if current == candidate and current_event is not None:
                return current_event
            if current is not None and (
                version < current[0]
                or (version == current[0] and candidate != current)
            ):
                raise RegistryAdmissionError(
                    "authorization manifest rollback or equivocation detected"
                )
            return self._append_locked(
                admission,
                event_kind=RegistryEventKind.AUTHORIZATION_MANIFEST_ACCEPTED,
                operation_id=_validate_id(
                    "operation_id", "authorization:" + self._id_factory()
                ),
                store_lineage_id=events[0].store_lineage_id,
                actor_id=actor_id,
                reason_code="AUTH_MANIFEST",
                outcome_code="ACCEPTED",
                control_payload=payload,
            )

    def authorization_manifest_anchor(self) -> Optional[Tuple[int, str, str]]:
        with self._exclusive():
            self._admit_locked()
            _event, value = self._manifest_anchor_from_events(
                self._read_and_verify_events()
            )
            return value

    def prepare_disposal(
        self,
        operation_id: str,
        actor_id: str,
        *,
        scope_token: str,
        audit_stream_token: str,
        inventory_fingerprint: str,
    ) -> RegistryEvent:
        operation_id = _validate_id("operation_id", operation_id)
        actor_id = _validate_id("actor_id", actor_id)
        payload = _validate_control_payload(
            RegistryEventKind.DISPOSAL_PREPARED,
            {
                "scope_token": scope_token,
                "audit_stream_token": audit_stream_token,
                "inventory_fingerprint": inventory_fingerprint,
            },
        )
        with self._exclusive():
            admission = self._admit_locked()
            events = self._read_and_verify_events()
            existing = self._disposal_event_from_events(events, operation_id)
            if existing is not None:
                if (
                    existing.event_kind is RegistryEventKind.DISPOSAL_PREPARED
                    and dict(existing.control_payload) == payload
                ):
                    return existing
                raise RegistryAdmissionError(
                    "disposal operation identity was already finalized or changed"
                )
            return self._append_locked(
                admission,
                event_kind=RegistryEventKind.DISPOSAL_PREPARED,
                operation_id=operation_id,
                store_lineage_id=events[0].store_lineage_id,
                actor_id=actor_id,
                reason_code="REVIEW_DISPOSAL",
                outcome_code="PREPARED",
                control_payload=payload,
            )

    def commit_disposal(self, operation_id: str, actor_id: str) -> RegistryEvent:
        return self._finalize_disposal(
            operation_id,
            actor_id,
            RegistryEventKind.DISPOSAL_COMMITTED,
            "COMMITTED",
        )

    def abort_disposal(self, operation_id: str, actor_id: str) -> RegistryEvent:
        return self._finalize_disposal(
            operation_id,
            actor_id,
            RegistryEventKind.DISPOSAL_ABORTED,
            "ABORTED",
        )

    def disposal_event(self, operation_id: str) -> Optional[RegistryEvent]:
        operation_id = _validate_id("operation_id", operation_id)
        with self._exclusive():
            self._admit_locked()
            return self._disposal_event_from_events(
                self._read_and_verify_events(), operation_id
            )

    def _finalize_disposal(
        self,
        operation_id: str,
        actor_id: str,
        target_kind: RegistryEventKind,
        outcome_code: str,
    ) -> RegistryEvent:
        operation_id = _validate_id("operation_id", operation_id)
        actor_id = _validate_id("actor_id", actor_id)
        with self._exclusive():
            admission = self._admit_locked()
            events = self._read_and_verify_events()
            current = self._disposal_event_from_events(events, operation_id)
            if current is None:
                raise RegistryAdmissionError(
                    "disposal operation was not prepared"
                )
            if current.event_kind is target_kind:
                return current
            if current.event_kind is not RegistryEventKind.DISPOSAL_PREPARED:
                raise RegistryAdmissionError(
                    "disposal operation has a conflicting terminal outcome"
                )
            return self._append_locked(
                admission,
                event_kind=target_kind,
                operation_id=operation_id,
                store_lineage_id=current.store_lineage_id,
                actor_id=actor_id,
                reason_code="REVIEW_DISPOSAL",
                outcome_code=outcome_code,
                control_payload=current.control_payload,
            )

    def _append_locked(
        self,
        admission: StartupAdmission,
        *,
        event_kind: RegistryEventKind,
        operation_id: str,
        store_lineage_id: str,
        actor_id: str,
        reason_code: str,
        outcome_code: str,
        control_payload: Mapping[str, object],
    ) -> RegistryEvent:
        lineage, committed = admission.lineage, admission.head.committed
        event = self._build_event(
            lineage=lineage,
            sequence=committed.sequence + 1,
            prior_hash=committed.tail_hash,
            event_kind=event_kind,
            operation_id=operation_id,
            store_lineage_id=store_lineage_id,
            actor_id=actor_id,
            reason_code=reason_code,
            outcome_code=outcome_code,
            control_payload=control_payload,
        )

        # AC-07 two-phase publication: durable entry -> protected pending
        # -> authenticated reread -> protected promotion.
        self._append_journal(event)
        self._write_head(
            lineage, committed, self._pointer(event), updated_at=_clock_now(self._clock)
        )
        reread = self._read_and_verify_events()
        if len(reread) != event.sequence or reread[-1] != event:
            raise RegistryAdmissionError(
                "new registry entry did not verify after durable append"
            )
        self._write_head(
            lineage, self._pointer(event), None, updated_at=_clock_now(self._clock)
        )
        return event

    @staticmethod
    def _audit_anchor_from_events(
        events: Tuple[RegistryEvent, ...],
        stream_id: str,
    ) -> Tuple[Optional[RegistryEvent], Optional[Tuple[int, str]]]:
        selected = None
        current = None
        for event in events:
            if event.event_kind is not RegistryEventKind.AUDIT_HEAD_ADVANCED:
                continue
            payload = event.control_payload
            if payload["stream_id"] != stream_id:
                continue
            candidate = (int(payload["sequence"]), str(payload["event_hmac"]))
            if current is None:
                if candidate[0] != 1:
                    raise RegistryAdmissionError(
                        "first audit anchor is not stream sequence one"
                    )
            elif candidate[0] != current[0] + 1:
                raise RegistryAdmissionError(
                    "audit anchor sequence is not monotonic"
                )
            current = candidate
            selected = event
        return selected, current

    @staticmethod
    def _disposal_event_from_events(
        events: Tuple[RegistryEvent, ...],
        operation_id: str,
    ) -> Optional[RegistryEvent]:
        selected = None
        for event in events:
            if (
                event.operation_id == operation_id
                and event.event_kind
                in (
                    RegistryEventKind.DISPOSAL_PREPARED,
                    RegistryEventKind.DISPOSAL_COMMITTED,
                    RegistryEventKind.DISPOSAL_ABORTED,
                )
            ):
                if (
                    selected is not None
                    and dict(selected.control_payload)
                    != dict(event.control_payload)
                ):
                    raise RegistryAdmissionError(
                        "disposal operation payload changed across its lifecycle"
                    )
                selected = event
        return selected

    @staticmethod
    def _audit_stream_retired(
        events: Tuple[RegistryEvent, ...],
        stream_id: str,
    ) -> bool:
        token = hashlib.sha256(stream_id.encode("utf-8")).hexdigest()
        return any(
            event.event_kind is RegistryEventKind.DISPOSAL_COMMITTED
            and event.control_payload["audit_stream_token"] == token
            for event in events
        )

    @staticmethod
    def _manifest_anchor_from_events(
        events: Tuple[RegistryEvent, ...],
    ) -> Tuple[Optional[RegistryEvent], Optional[Tuple[int, str, str]]]:
        selected = None
        current = None
        for event in events:
            if (
                event.event_kind
                is not RegistryEventKind.AUTHORIZATION_MANIFEST_ACCEPTED
            ):
                continue
            payload = event.control_payload
            candidate = (
                int(payload["version"]),
                str(payload["fingerprint"]),
                str(payload["key_id"]),
            )
            if current is not None and (
                candidate[0] < current[0]
                or (candidate[0] == current[0] and candidate != current)
            ):
                raise RegistryAdmissionError(
                    "authorization manifest anchor is not monotonic"
                )
            current = candidate
            selected = event
        return selected, current

    # ---- startup admission / crash reconciliation ----------------------
    def _admit_locked(self) -> StartupAdmission:
        self._require_existing_authority()
        events = self._read_and_verify_events()
        head = self._read_and_verify_head()
        lineage = self._lineage_from(events[0], head)
        self._verify_head_shape(head)
        committed_index = head.committed.sequence

        if committed_index < 1:
            raise RegistryAdmissionError("committed registry head must include GENESIS")
        if len(events) < committed_index:
            raise RegistryAdmissionError("registry journal is truncated before committed head")
        committed_event = events[committed_index - 1]
        if not self._pointer_matches(head.committed, committed_event):
            raise RegistryAdmissionError("committed registry head conflicts with journal")

        pending = head.pending
        if pending is not None:
            if pending.sequence != committed_index + 1:
                raise RegistryAdmissionError("pending registry head is not the next sequence")
            if len(events) == committed_index:
                # A protected pending marker without an appended entry may be
                # cleared only while the authenticated committed anchor still
                # exactly matches.  No financial/store state is changed here.
                cleared = self._write_head(
                    lineage, head.committed, None, updated_at=_clock_now(self._clock)
                )
                return StartupAdmission(
                    StartupAdmissionStatus.RECOVERED_CLEARED_PENDING,
                    lineage,
                    cleared,
                    verified_event_count=len(events),
                )
            if len(events) != pending.sequence:
                raise RegistryAdmissionError(
                    "pending registry head has an ambiguous journal suffix"
                )
            pending_event = events[pending.sequence - 1]
            if not self._pointer_matches(pending, pending_event):
                raise RegistryAdmissionError("pending registry head conflicts with journal")
            promoted = self._write_head(
                lineage, pending, None, updated_at=_clock_now(self._clock)
            )
            return StartupAdmission(
                StartupAdmissionStatus.RECOVERED_PENDING,
                lineage,
                promoted,
                verified_event_count=len(events),
            )

        if len(events) == committed_index:
            return StartupAdmission(
                StartupAdmissionStatus.ADMITTED,
                lineage,
                head,
                verified_event_count=len(events),
            )
        if len(events) != committed_index + 1:
            raise RegistryAdmissionError("registry has an ambiguous authenticated journal suffix")

        # Crash after fsync(entry N), before pending-head publication.  Adopt
        # exactly one valid chained suffix through the pending state.
        suffix = events[-1]
        pending_head = self._write_head(
            lineage, head.committed, self._pointer(suffix), updated_at=_clock_now(self._clock)
        )
        promoted = self._write_head(
            lineage, pending_head.pending, None, updated_at=_clock_now(self._clock)
        )
        return StartupAdmission(
            StartupAdmissionStatus.RECOVERED_APPENDED_SUFFIX,
            lineage,
            promoted,
            verified_event_count=len(events),
        )

    # ---- event encoding and verification -------------------------------
    def _build_event(
        self,
        *,
        lineage: RegistryLineage,
        sequence: int,
        prior_hash: str,
        event_kind: RegistryEventKind,
        operation_id: str,
        store_lineage_id: str,
        actor_id: str,
        reason_code: str,
        outcome_code: str,
        control_payload: Optional[Mapping[str, object]] = None,
        occurred_at: Optional[str] = None,
    ) -> RegistryEvent:
        control = _validate_control_payload(event_kind, control_payload)
        core = {
            "registry_lineage_id": lineage.registry_lineage_id,
            "token_epoch": lineage.token_epoch,
            "sequence": sequence,
            "prior_hash": prior_hash,
            "event_id": _validate_id("event_id", self._id_factory()),
            "event_kind": event_kind.value,
            "operation_id": operation_id,
            "store_lineage_id": store_lineage_id,
            "actor_id": actor_id,
            "occurred_at": occurred_at or _clock_now(self._clock),
            "reason_code": reason_code,
            "outcome_code": outcome_code,
            "control_payload": control,
        }
        mac = _purpose_mac(self._key, b"REGISTRY-EVENT-v1", core)
        return self._event_from_dict(
            {**core, "record_mac": mac, "entry_hash": _entry_hash(core, mac)}
        )

    def _read_and_verify_events(self) -> Tuple[RegistryEvent, ...]:
        self._require_regular_file(self._journal, "journal")
        try:
            raw = self._journal.read_bytes()
        except OSError as exc:
            raise RegistryAdmissionError("registry journal could not be read") from exc
        if not raw or not raw.endswith(b"\n"):
            raise RegistryAdmissionError("registry journal is empty or truncated")
        lines = raw.splitlines(keepends=True)
        events = []
        prior = GENESIS_PRIOR_HASH
        lineage_id = token_epoch = None
        for expected_sequence, raw_line in enumerate(lines, start=1):
            if raw_line in (b"\n", b"\r\n"):
                raise RegistryAdmissionError("registry journal contains an empty record")
            line = raw_line[:-1]
            try:
                value = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RegistryAdmissionError("registry journal contains invalid JSON") from exc
            if not isinstance(value, dict) or frozenset(value) != _EVENT_KEYS:
                raise RegistryAdmissionError("registry journal record schema is invalid")
            if line != _canonical(value):
                raise RegistryAdmissionError("registry journal record is not canonical")
            event = self._event_from_dict(value, admission=True)
            if event.sequence != expected_sequence:
                raise RegistryAdmissionError("registry journal sequence is not contiguous")
            if event.prior_hash != prior:
                raise RegistryAdmissionError("registry journal prior hash is invalid")
            if expected_sequence == 1 and event.event_kind is not RegistryEventKind.GENESIS:
                raise RegistryAdmissionError("first registry event is not GENESIS")
            if expected_sequence > 1 and event.event_kind is RegistryEventKind.GENESIS:
                raise RegistryAdmissionError("registry contains more than one GENESIS")
            if lineage_id is None:
                lineage_id, token_epoch = event.registry_lineage_id, event.token_epoch
            elif (
                event.registry_lineage_id != lineage_id
                or event.token_epoch != token_epoch
            ):
                raise RegistryAdmissionError("registry lineage or immutable token epoch changed")
            prior = event.entry_hash
            events.append(event)
        return tuple(events)

    def _event_from_dict(self, value: Dict[str, Any], admission: bool = False) -> RegistryEvent:
        error = RegistryAdmissionError if admission else RegistryValidationError
        try:
            if frozenset(value) != _EVENT_KEYS:
                raise ValueError("event keys")
            core = {key: value[key] for key in _EVENT_CORE_KEYS}
            sequence = value["sequence"]
            if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
                raise ValueError("sequence")
            for name in (
                "registry_lineage_id", "token_epoch", "event_id", "operation_id",
                "store_lineage_id", "actor_id",
            ):
                _validate_id(name, value[name])
            _validate_code("reason_code", value["reason_code"])
            _validate_code("outcome_code", value["outcome_code"])
            if (
                not isinstance(value["occurred_at"], str)
                or not value["occurred_at"]
                or len(value["occurred_at"]) > 64
            ):
                raise ValueError("occurred_at")
            if _HEX_64_RE.fullmatch(value["prior_hash"]) is None:
                raise ValueError("prior_hash")
            if _HEX_64_RE.fullmatch(value["record_mac"]) is None:
                raise ValueError("record_mac")
            if _HEX_64_RE.fullmatch(value["entry_hash"]) is None:
                raise ValueError("entry_hash")
            kind = RegistryEventKind(value["event_kind"])
            control_payload = _validate_control_payload(
                kind, value["control_payload"]
            )
            expected_mac = _purpose_mac(self._key, b"REGISTRY-EVENT-v1", core)
            if not hmac.compare_digest(value["record_mac"], expected_mac):
                raise ValueError("record_mac")
            expected_hash = _entry_hash(core, value["record_mac"])
            if not hmac.compare_digest(value["entry_hash"], expected_hash):
                raise ValueError("entry_hash")
            return RegistryEvent(
                registry_lineage_id=value["registry_lineage_id"],
                token_epoch=value["token_epoch"],
                sequence=sequence,
                prior_hash=value["prior_hash"],
                event_id=value["event_id"],
                event_kind=kind,
                operation_id=value["operation_id"],
                store_lineage_id=value["store_lineage_id"],
                actor_id=value["actor_id"],
                occurred_at=value["occurred_at"],
                reason_code=value["reason_code"],
                outcome_code=value["outcome_code"],
                control_payload=control_payload,
                record_mac=value["record_mac"],
                entry_hash=value["entry_hash"],
            )
        except RegistryValidationError as exc:
            raise error(str(exc)) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise error("registry event is invalid") from exc

    # ---- protected head -------------------------------------------------
    def _write_head(
        self,
        lineage: RegistryLineage,
        committed: HeadPointer,
        pending: Optional[HeadPointer],
        *,
        updated_at: str,
    ) -> ProtectedHead:
        payload = {
            "registry_lineage_id": lineage.registry_lineage_id,
            "token_epoch": lineage.token_epoch,
            "format_version": lineage.format_version,
            "security_profile": lineage.security_profile,
            "committed": self._pointer_dict(committed),
            "pending": self._pointer_dict(pending) if pending is not None else None,
            "updated_at": updated_at,
        }
        mac = _purpose_mac(self._key, b"REGISTRY-HEAD-v1", payload)
        encoded = _canonical({**payload, "protection_mac": mac}) + b"\n"
        self._atomic_replace(self._head, encoded)
        return self._head_from_dict({**payload, "protection_mac": mac})

    def _read_and_verify_head(self) -> ProtectedHead:
        self._require_regular_file(self._head, "head")
        try:
            raw = self._head.read_bytes()
        except OSError as exc:
            raise RegistryAdmissionError("protected registry head could not be read") from exc
        if not raw or not raw.endswith(b"\n") or raw.count(b"\n") != 1:
            raise RegistryAdmissionError("protected registry head is missing or truncated")
        line = raw[:-1]
        try:
            value = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RegistryAdmissionError("protected registry head contains invalid JSON") from exc
        if not isinstance(value, dict) or frozenset(value) != _HEAD_KEYS:
            raise RegistryAdmissionError("protected registry head schema is invalid")
        if line != _canonical(value):
            raise RegistryAdmissionError("protected registry head is not canonical")
        payload = {key: value[key] for key in _HEAD_PAYLOAD_KEYS}
        expected = _purpose_mac(self._key, b"REGISTRY-HEAD-v1", payload)
        if (
            not isinstance(value["protection_mac"], str)
            or not hmac.compare_digest(value["protection_mac"], expected)
        ):
            raise RegistryAdmissionError("protected registry head authentication failed")
        try:
            return self._head_from_dict(value)
        except (KeyError, TypeError, ValueError, RegistryValidationError) as exc:
            raise RegistryAdmissionError("protected registry head is invalid") from exc

    def _head_from_dict(self, value: Dict[str, Any]) -> ProtectedHead:
        if frozenset(value) != _HEAD_KEYS:
            raise ValueError("head keys")
        _validate_id("registry_lineage_id", value["registry_lineage_id"])
        _validate_id("token_epoch", value["token_epoch"])
        if value["format_version"] != REGISTRY_FORMAT_VERSION:
            raise ValueError("format version")
        if value["security_profile"] != REGISTRY_SECURITY_PROFILE:
            raise ValueError("security profile")
        updated = value["updated_at"]
        if not isinstance(updated, str) or not updated or len(updated) > 64:
            raise ValueError("updated_at")
        mac = value["protection_mac"]
        if not isinstance(mac, str) or _HEX_64_RE.fullmatch(mac) is None:
            raise ValueError("protection_mac")
        return ProtectedHead(
            registry_lineage_id=value["registry_lineage_id"],
            token_epoch=value["token_epoch"],
            format_version=value["format_version"],
            security_profile=value["security_profile"],
            committed=self._pointer_from_dict(value["committed"]),
            pending=(
                self._pointer_from_dict(value["pending"])
                if value["pending"] is not None
                else None
            ),
            updated_at=updated,
            protection_mac=mac,
        )

    def _pointer_from_dict(self, value: Any) -> HeadPointer:
        if not isinstance(value, dict) or frozenset(value) != _POINTER_KEYS:
            raise ValueError("pointer schema")
        sequence = value["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            raise ValueError("pointer sequence")
        if (
            not isinstance(value["tail_hash"], str)
            or _HEX_64_RE.fullmatch(value["tail_hash"]) is None
        ):
            raise ValueError("pointer tail")
        _validate_id("operation_id", value["operation_id"])
        return HeadPointer(sequence, value["tail_hash"], value["operation_id"])

    @staticmethod
    def _pointer_dict(pointer: HeadPointer) -> Dict[str, Any]:
        return {
            "sequence": pointer.sequence,
            "tail_hash": pointer.tail_hash,
            "operation_id": pointer.operation_id,
        }

    @staticmethod
    def _pointer(event: RegistryEvent) -> HeadPointer:
        return HeadPointer(event.sequence, event.entry_hash, event.operation_id)

    @staticmethod
    def _pointer_matches(pointer: HeadPointer, event: RegistryEvent) -> bool:
        return (
            pointer.sequence == event.sequence
            and hmac.compare_digest(pointer.tail_hash, event.entry_hash)
            and pointer.operation_id == event.operation_id
        )

    def _verify_head_shape(self, head: ProtectedHead) -> None:
        if head.pending is not None and head.pending.sequence <= head.committed.sequence:
            raise RegistryAdmissionError("pending registry head is not ahead of committed head")

    def _lineage_from(
        self, genesis: RegistryEvent, head: ProtectedHead
    ) -> RegistryLineage:
        if (
            head.registry_lineage_id != genesis.registry_lineage_id
            or head.token_epoch != genesis.token_epoch
        ):
            raise RegistryAdmissionError("protected head conflicts with journal lineage")
        return RegistryLineage(
            registry_lineage_id=genesis.registry_lineage_id,
            token_epoch=genesis.token_epoch,
            format_version=head.format_version,
            security_profile=head.security_profile,
            created_at=genesis.occurred_at,
        )

    # ---- durable filesystem operations ---------------------------------
    def _prepare_fresh_directory(self) -> None:
        if self._root.exists() and self._root.is_symlink():
            raise RegistryAlreadyExistsError("registry root cannot be a symbolic link")
        self._root.mkdir(
            parents=True,
            mode=0o770 if self._machine_shared else 0o700,
            exist_ok=True,
        )
        if self._journal.exists() or self._head.exists():
            raise RegistryAlreadyExistsError("registry authority already exists")
        unexpected = [p for p in self._root.iterdir() if p.name not in {".registry.lock"}]
        if unexpected:
            raise RegistryAlreadyExistsError("registry root is not empty")
        self._tighten_directory(self._root)

    def _create_journal(self, event: RegistryEvent) -> None:
        payload = _canonical(self._event_dict(event)) + b"\n"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(
                self._journal, flags, 0o660 if self._machine_shared else 0o600
            )
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if os.name == "posix":
                os.chmod(
                    self._journal, 0o660 if self._machine_shared else 0o600
                )
            self._fsync_directory()
        except OSError as exc:
            raise RegistryAlreadyExistsError("could not create fresh registry journal") from exc

    def _append_journal(self, event: RegistryEvent) -> None:
        self._require_regular_file(self._journal, "journal")
        payload = _canonical(self._event_dict(event)) + b"\n"
        flags = os.O_WRONLY | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(self._journal, flags)
            with os.fdopen(fd, "ab", buffering=0) as stream:
                written = stream.write(payload)
                if written != len(payload):
                    raise OSError("short registry journal write")
                os.fsync(stream.fileno())
            self._fsync_directory()
        except OSError as exc:
            raise RegistryAdmissionError("registry journal append failed") from exc

    def _atomic_replace(self, target: Path, payload: bytes) -> None:
        temp: Optional[Path] = None
        try:
            fd, raw_temp = tempfile.mkstemp(
                dir=str(self._root), prefix=target.name + ".new-"
            )
            temp = Path(raw_temp)
            if os.name == "posix":
                os.chmod(temp, 0o660 if self._machine_shared else 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, target)
            if os.name == "posix":
                os.chmod(target, 0o660 if self._machine_shared else 0o600)
            self._fsync_directory()
        except OSError as exc:
            try:
                if temp is not None and temp.exists() and not temp.is_symlink():
                    temp.unlink()
            except OSError:
                pass
            raise RegistryAdmissionError("protected registry head update failed") from exc

    def _require_existing_authority(self) -> None:
        if not self._root.exists() or not self._root.is_dir() or self._root.is_symlink():
            raise RegistryAdmissionError("registry authority is missing")
        self._require_restrictive(self._root, is_directory=True)
        self._require_regular_file(self._journal, "journal")
        self._require_regular_file(self._head, "head")

    def _require_regular_file(self, path: Path, label: str) -> None:
        try:
            info = path.lstat()
        except OSError as exc:
            raise RegistryAdmissionError("registry %s is missing" % label) from exc
        if not stat.S_ISREG(info.st_mode):
            raise RegistryAdmissionError("registry %s is not a regular file" % label)
        self._require_restrictive(path, is_directory=False)

    def _tighten_directory(self, path: Path) -> None:
        if os.name == "posix":
            os.chmod(path, 0o770 if self._machine_shared else 0o700)

    def _require_restrictive(self, path: Path, *, is_directory: bool) -> None:
        if os.name != "posix":
            return
        info = path.lstat()
        if self._machine_shared:
            try:
                import grp

                expected_group = grp.getgrnam(
                    os.environ.get("FINSIGHT_POSIX_ACCESS_GROUP", "finsight")
                ).gr_gid
            except (ImportError, KeyError) as exc:
                raise RegistryAdmissionError(
                    "registry deployment access group is unavailable"
                ) from exc
            if info.st_gid != expected_group:
                raise RegistryAdmissionError(
                    "registry path is not assigned to the approved access group"
                )
            expected_mode = 0o770 if is_directory else 0o660
        else:
            if info.st_uid != os.geteuid():
                raise RegistryAdmissionError(
                    "registry path is not owned by the current identity"
                )
            expected_mode = 0o700 if is_directory else 0o600
        if stat.S_IMODE(info.st_mode) != expected_mode:
            raise RegistryAdmissionError(
                "registry path permissions do not match the approved profile"
            )

    def _fsync_directory(self) -> None:
        if os.name != "posix":
            return
        flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            flags |= os.O_DIRECTORY
        fd = os.open(self._root, flags)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    @contextmanager
    def _exclusive(self, *, create_root: bool = False) -> Iterable[None]:
        """Serialize registry admission and mutation across threads/processes.

        The product also holds its store-level single-instance lock.  This
        separate recovery lock protects the authority before a store is opened
        and remains valid across store replacement.
        """
        with self._thread_lock:
            if self._root.exists() and self._root.is_symlink():
                raise RegistryAdmissionError("registry root cannot be a symbolic link")
            if not self._root.exists():
                if not create_root:
                    yield
                    return
                self._root.mkdir(
                    parents=True,
                    mode=0o770 if self._machine_shared else 0o700,
                    exist_ok=False,
                )
                self._tighten_directory(self._root)

            from finsight.infrastructure.single_instance import SingleInstanceLock

            lock_path = self._root / ".registry.lock"
            lock = SingleInstanceLock(str(lock_path))
            if not lock.acquire():
                raise RegistryAdmissionError("registry authority is in use")
            try:
                if os.name == "posix":
                    os.chmod(
                        lock_path, 0o660 if self._machine_shared else 0o600
                    )
                yield
            finally:
                lock.release()

    @staticmethod
    def _event_dict(event: RegistryEvent) -> Dict[str, Any]:
        return {
            "registry_lineage_id": event.registry_lineage_id,
            "token_epoch": event.token_epoch,
            "sequence": event.sequence,
            "prior_hash": event.prior_hash,
            "event_id": event.event_id,
            "event_kind": event.event_kind.value,
            "operation_id": event.operation_id,
            "store_lineage_id": event.store_lineage_id,
            "actor_id": event.actor_id,
            "occurred_at": event.occurred_at,
            "reason_code": event.reason_code,
            "outcome_code": event.outcome_code,
            "control_payload": dict(event.control_payload),
            "record_mac": event.record_mac,
            "entry_hash": event.entry_hash,
        }
