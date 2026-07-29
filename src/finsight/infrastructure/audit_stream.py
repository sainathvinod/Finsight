# Implements: V2 FR-084/189/190, NFR-090, AC-02, ADR-V2-003 — attributable HMAC audit streams.
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from finsight.application.disposal_registry import RegistryEventKind


class AuditIntegrityError(RuntimeError):
    """An append-only audit stream cannot be verified or advanced safely."""


@dataclass(frozen=True)
class AuditScope:
    resource_type: str
    resource_id: str


@dataclass(frozen=True)
class ChainedAuditEvent:
    event_id: str
    stream_id: str
    stream_sequence: int
    schema_version: int
    actor_id: str
    actor_display: str
    identity_source: str
    occurred_at: str
    event_type: str
    payload: dict
    correlation_id: str
    outcome: str
    prior_hmac: str
    event_hmac: str
    scopes: Tuple[AuditScope, ...]


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class AuditStreamSqlite:
    """Append/verify HMAC-SHA256 audit events.

    The caller owns the Unit of Work. ``append`` inserts the event and advances the stream head with a
    compare-and-swap inside that transaction; it never commits on its own.
    """

    SCHEMA_VERSION = 1

    def __init__(
        self,
        dal,
        key: bytes,
        clock,
        id_factory,
        *,
        anchor_registry=None,
        after_commit=None,
    ):
        if len(key) != 32:
            raise ValueError("Audit HMAC key must contain exactly 32 bytes.")
        self._dal = dal
        self._key = key
        self._clock = clock
        self._id = id_factory
        self._anchor_registry = anchor_registry
        self._after_commit = after_commit
        if (anchor_registry is None) != (after_commit is None):
            raise ValueError(
                "Audit rollback anchoring requires both registry and after-commit callback."
            )

    @staticmethod
    def review_stream_id(review_id: str) -> str:
        return "audit_review_" + review_id

    @staticmethod
    def global_stream_id(stream_type: str) -> str:
        return "audit_global_" + stream_type.lower()

    def _stream_identity(self, review_id: Optional[str], stream_type: str) -> tuple[str, str, Optional[str]]:
        normalized = stream_type.upper()
        if review_id is not None:
            if normalized != "REVIEW":
                raise ValueError("A review-scoped event must use the REVIEW stream type.")
            return self.review_stream_id(review_id), normalized, review_id
        if normalized not in ("GLOBAL", "RULE_GOVERNANCE", "SECURITY", "DISPOSAL"):
            raise ValueError("Unsupported global audit stream type.")
        return self.global_stream_id(normalized), normalized, None

    def _genesis(self, stream_id: str, stream_type: str, review_id: Optional[str]) -> str:
        value = _canonical(
            {
                "schema_version": self.SCHEMA_VERSION,
                "stream_id": stream_id,
                "stream_type": stream_type,
                "review_id": review_id,
            }
        ).encode("utf-8")
        return hmac.new(self._key, b"FinSight/Audit/Genesis\0" + value, hashlib.sha256).hexdigest()

    def ensure_stream(self, *, review_id: Optional[str] = None, stream_type: str = "REVIEW") -> str:
        stream_id, normalized, scope_review = self._stream_identity(review_id, stream_type)
        row = self._dal.conn.execute(
            "SELECT stream_type,review_id,genesis_hmac,current_sequence,current_hmac "
            "FROM v2_audit_streams WHERE stream_id=?",
            (stream_id,),
        ).fetchone()
        expected = self._genesis(stream_id, normalized, scope_review)
        if row is None:
            self._dal.conn.execute(
                "INSERT INTO v2_audit_streams(stream_id,stream_type,review_id,genesis_hmac,"
                "current_sequence,current_hmac,revision) VALUES(?,?,?,?,0,?,0)",
                (stream_id, normalized, scope_review, expected, expected),
            )
            return stream_id
        if row[0] != normalized or row[1] != scope_review or row[2] != expected:
            raise AuditIntegrityError("Audit stream identity or genesis protection does not match.")
        return stream_id

    def append(
        self,
        *,
        event_type: str,
        actor,
        payload: dict,
        correlation_id: str,
        outcome: str = "SUCCEEDED",
        review_id: Optional[str] = None,
        stream_type: str = "REVIEW",
        scopes: Sequence[AuditScope] = (),
        event_id: Optional[str] = None,
        occurred_at: Optional[str] = None,
    ) -> ChainedAuditEvent:
        if not event_type or not correlation_id or not outcome:
            raise ValueError("Audit event type, correlation ID, and outcome are required.")
        if not isinstance(payload, dict):
            raise TypeError("Audit payload must be a structured mapping.")
        stream_id = self.ensure_stream(review_id=review_id, stream_type=stream_type)
        row = self._dal.conn.execute(
            "SELECT current_sequence,current_hmac,revision FROM v2_audit_streams WHERE stream_id=?",
            (stream_id,),
        ).fetchone()
        if row is None:  # pragma: no cover - ensure_stream invariant
            raise AuditIntegrityError("Audit stream disappeared during append.")
        prior_sequence, prior_hmac, revision = int(row[0]), str(row[1]), int(row[2])
        sequence = prior_sequence + 1
        eid = event_id or ("aud_" + self._id())
        timestamp = occurred_at or self._clock.now()
        identity_source = getattr(actor.identity_source, "value", actor.identity_source)
        body = {
            "event_id": eid,
            "stream_id": stream_id,
            "stream_sequence": sequence,
            "schema_version": self.SCHEMA_VERSION,
            "actor": {
                "actor_id": actor.actor_id,
                "display_name": actor.display_name,
                "identity_source": str(identity_source),
            },
            "occurred_at": timestamp,
            "event_type": event_type,
            "payload": payload,
            "correlation_id": correlation_id,
            "outcome": outcome,
            "scopes": [
                {"ordinal": ordinal, "resource_type": scope.resource_type, "resource_id": scope.resource_id}
                for ordinal, scope in enumerate(scopes, 1)
            ],
        }
        canonical_payload = _canonical(payload)
        digest = hmac.new(
            self._key,
            b"FinSight/Audit/Event\0"
            + bytes.fromhex(prior_hmac)
            + _canonical(body).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        self._dal.conn.execute(
            "INSERT INTO v2_audit_events(event_id,stream_id,stream_sequence,schema_version,actor_id,"
            "actor_display,identity_source,occurred_at,event_type,canonical_payload,correlation_id,"
            "outcome,prior_hmac,event_hmac) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                eid,
                stream_id,
                sequence,
                self.SCHEMA_VERSION,
                actor.actor_id,
                actor.display_name,
                str(identity_source),
                timestamp,
                event_type,
                canonical_payload,
                correlation_id,
                outcome,
                prior_hmac,
                digest,
            ),
        )
        for ordinal, scope in enumerate(scopes, 1):
            self._dal.conn.execute(
                "INSERT INTO v2_audit_event_scopes(event_id,ordinal,resource_type,resource_id) "
                "VALUES(?,?,?,?)",
                (eid, ordinal, scope.resource_type, scope.resource_id),
            )
        changed = self._dal.conn.execute(
            "UPDATE v2_audit_streams SET current_sequence=?,current_hmac=?,revision=revision+1 "
            "WHERE stream_id=? AND revision=? AND current_sequence=? AND current_hmac=?",
            (sequence, digest, stream_id, revision, prior_sequence, prior_hmac),
        ).rowcount
        if changed != 1:
            raise AuditIntegrityError("Concurrent audit-stream head change detected.")
        if self._anchor_registry is not None:
            stream_actor_id = actor.actor_id
            self._after_commit(
                lambda: self._anchor_registry.advance_audit_anchor(
                    stream_id,
                    sequence,
                    digest,
                    stream_actor_id,
                )
            )
        return ChainedAuditEvent(
            eid,
            stream_id,
            sequence,
            self.SCHEMA_VERSION,
            actor.actor_id,
            actor.display_name,
            str(identity_source),
            timestamp,
            event_type,
            dict(payload),
            correlation_id,
            outcome,
            prior_hmac,
            digest,
            tuple(scopes),
        )

    def events(self, *, review_id: Optional[str] = None, stream_type: str = "REVIEW"):
        stream_id, _normalized, _review = self._stream_identity(review_id, stream_type)
        rows = self._dal.conn.execute(
            "SELECT event_id,stream_sequence,schema_version,actor_id,actor_display,identity_source,"
            "occurred_at,event_type,canonical_payload,correlation_id,outcome,prior_hmac,event_hmac "
            "FROM v2_audit_events WHERE stream_id=? ORDER BY stream_sequence",
            (stream_id,),
        ).fetchall()
        result = []
        for row in rows:
            scope_rows = self._dal.conn.execute(
                "SELECT resource_type,resource_id FROM v2_audit_event_scopes "
                "WHERE event_id=? ORDER BY ordinal",
                (row[0],),
            ).fetchall()
            result.append(
                ChainedAuditEvent(
                    event_id=row[0],
                    stream_id=stream_id,
                    stream_sequence=int(row[1]),
                    schema_version=int(row[2]),
                    actor_id=row[3],
                    actor_display=row[4],
                    identity_source=row[5],
                    occurred_at=row[6],
                    event_type=row[7],
                    payload=json.loads(row[8]),
                    correlation_id=row[9],
                    outcome=row[10],
                    prior_hmac=row[11],
                    event_hmac=row[12],
                    scopes=tuple(AuditScope(*scope) for scope in scope_rows),
                )
            )
        return result

    def prepare_review_disposal(
        self,
        *,
        operation_id: str,
        review_id: str,
        scope_token: str,
        inventory_fingerprint: str,
        actor_id: str,
    ) -> None:
        """Publish the content-free prepare record before the database commit."""

        if self._anchor_registry is None:
            return
        stream_token = hashlib.sha256(
            self.review_stream_id(review_id).encode("utf-8")
        ).hexdigest()
        self._anchor_registry.prepare_disposal(
            operation_id,
            actor_id,
            scope_token=scope_token,
            audit_stream_token=stream_token,
            inventory_fingerprint=inventory_fingerprint,
        )

    def commit_review_disposal(self, operation_id: str, actor_id: str) -> None:
        if self._anchor_registry is not None:
            self._anchor_registry.commit_disposal(operation_id, actor_id)

    def abort_review_disposal(self, operation_id: str, actor_id: str) -> None:
        if self._anchor_registry is not None:
            self._anchor_registry.abort_disposal(operation_id, actor_id)

    def verify_all(self, *, reconcile_committed_gap: bool = False) -> None:
        rows = self._dal.conn.execute(
            "SELECT stream_id,stream_type,review_id,genesis_hmac,current_sequence,current_hmac "
            "FROM v2_audit_streams ORDER BY stream_id"
        ).fetchall()
        verified_heads = {}
        for row in rows:
            self._verify(row)
            stream_id = str(row[0])
            sequence = int(row[4])
            tail = str(row[5])
            if sequence > 0:
                verified_heads[stream_id] = (sequence, tail)
                self._verify_external_anchor(
                    stream_id,
                    sequence,
                    tail,
                    reconcile_committed_gap=reconcile_committed_gap,
                )
        if self._anchor_registry is not None:
            if reconcile_committed_gap:
                self._reconcile_committed_disposals()
            anchored = dict(self._anchor_registry.audit_anchors())
            if set(anchored) != set(verified_heads):
                raise AuditIntegrityError(
                    "External audit anchors do not match the stored stream set."
                )
            for stream_id, head in verified_heads.items():
                if anchored.get(stream_id) != head:
                    raise AuditIntegrityError(
                        "External audit anchor does not match the verified stream head."
                    )

    def _reconcile_committed_disposals(self) -> None:
        exists = self._dal.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='v2_review_disposal_tombstones'"
        ).fetchone()
        if exists is None:
            return
        rows = self._dal.conn.execute(
            "SELECT operation_id,scope_token,audit_stream_token,"
            "inventory_fingerprint,actor_id "
            "FROM v2_review_disposal_tombstones ORDER BY disposed_at,tombstone_id"
        ).fetchall()
        for operation_id, scope_token, stream_token, inventory_hash, actor_id in rows:
            event = self._anchor_registry.disposal_event(operation_id)
            if event is None:
                raise AuditIntegrityError(
                    "A committed review disposal has no external prepare record."
                )
            expected = {
                "scope_token": scope_token,
                "audit_stream_token": stream_token,
                "inventory_fingerprint": inventory_hash,
            }
            if dict(event.control_payload) != expected:
                raise AuditIntegrityError(
                    "The disposal tombstone does not match its external control record."
                )
            if event.event_kind is RegistryEventKind.DISPOSAL_PREPARED:
                self._anchor_registry.commit_disposal(operation_id, actor_id)
            elif event.event_kind is not RegistryEventKind.DISPOSAL_COMMITTED:
                raise AuditIntegrityError(
                    "A committed review disposal has a conflicting external outcome."
                )

    def _verify_external_anchor(
        self,
        stream_id: str,
        sequence: int,
        event_hmac: str,
        *,
        reconcile_committed_gap: bool,
    ) -> None:
        if self._anchor_registry is None:
            return
        anchor = self._anchor_registry.audit_anchor(stream_id)
        if anchor == (sequence, event_hmac):
            return
        prior_sequence = 0 if anchor is None else int(anchor[0])
        if not reconcile_committed_gap or sequence != prior_sequence + 1:
            raise AuditIntegrityError(
                "External audit anchor does not match the verified stream head."
            )
        actor_row = self._dal.conn.execute(
            "SELECT actor_id FROM v2_audit_events WHERE stream_id=? "
            "AND stream_sequence=?",
            (stream_id, sequence),
        ).fetchone()
        if actor_row is None:
            raise AuditIntegrityError(
                "The committed audit event required for anchor recovery is missing."
            )
        self._anchor_registry.advance_audit_anchor(
            stream_id, sequence, event_hmac, str(actor_row[0])
        )

    def _verify(self, stream_row) -> None:
        stream_id, stream_type, review_id, genesis, stored_sequence, stored_tail = stream_row
        expected_genesis = self._genesis(stream_id, stream_type, review_id)
        if not hmac.compare_digest(genesis, expected_genesis):
            raise AuditIntegrityError("Audit genesis HMAC mismatch.")
        prior = expected_genesis
        expected_sequence = 0
        for event in self.events(review_id=review_id, stream_type=stream_type):
            expected_sequence += 1
            if event.stream_sequence != expected_sequence or event.prior_hmac != prior:
                raise AuditIntegrityError("Audit sequence or prior HMAC is discontinuous.")
            body = {
                "event_id": event.event_id,
                "stream_id": stream_id,
                "stream_sequence": event.stream_sequence,
                "schema_version": event.schema_version,
                "actor": {
                    "actor_id": event.actor_id,
                    "display_name": event.actor_display,
                    "identity_source": event.identity_source,
                },
                "occurred_at": event.occurred_at,
                "event_type": event.event_type,
                "payload": event.payload,
                "correlation_id": event.correlation_id,
                "outcome": event.outcome,
                "scopes": [
                    {
                        "ordinal": ordinal,
                        "resource_type": scope.resource_type,
                        "resource_id": scope.resource_id,
                    }
                    for ordinal, scope in enumerate(event.scopes, 1)
                ],
            }
            expected = hmac.new(
                self._key,
                b"FinSight/Audit/Event\0"
                + bytes.fromhex(prior)
                + _canonical(body).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(event.event_hmac, expected):
                raise AuditIntegrityError("Audit event HMAC mismatch.")
            prior = expected
        if int(stored_sequence) != expected_sequence or not hmac.compare_digest(str(stored_tail), prior):
            raise AuditIntegrityError("Audit stream head does not match its verified event chain.")
