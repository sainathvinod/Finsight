"""Application boundary for FinSight's external recovery-control authority.

Implements the Workflow 1 foundation of Architecture Contract AC-07 and
ADR-V2-003.  These types intentionally contain control-plane identifiers only:
no workbook values, normalized rows, findings, descriptions, or other financial
content belong in the Disposal Registry.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Protocol, Tuple, runtime_checkable


GENESIS_PRIOR_HASH = "0" * 64
REGISTRY_FORMAT_VERSION = 1
REGISTRY_SECURITY_PROFILE = "HMAC-SHA256-v1"


class RegistryEventKind(str, Enum):
    """Closed set of control-plane events admitted by the V2 registry."""

    GENESIS = "GENESIS"
    LEGACY_CUTOVER = "LEGACY_CUTOVER"
    FORMAT_MIGRATION = "FORMAT_MIGRATION"
    RECOVERY_ADOPTION = "RECOVERY_ADOPTION"
    BACKUP_PREPARED = "BACKUP_PREPARED"
    BACKUP_ACTIVE = "BACKUP_ACTIVE"
    BACKUP_RETIRED = "BACKUP_RETIRED"
    BACKUP_REVOKED = "BACKUP_REVOKED"
    DISPOSAL_PREPARED = "DISPOSAL_PREPARED"
    DISPOSAL_COMMITTED = "DISPOSAL_COMMITTED"
    DISPOSAL_ABORTED = "DISPOSAL_ABORTED"
    AUTHORIZATION_MANIFEST_ACCEPTED = "AUTHORIZATION_MANIFEST_ACCEPTED"
    AUDIT_HEAD_ADVANCED = "AUDIT_HEAD_ADVANCED"


class StartupAdmissionStatus(str, Enum):
    CREATED = "CREATED"
    ADMITTED = "ADMITTED"
    RECOVERED_PENDING = "RECOVERED_PENDING"
    RECOVERED_APPENDED_SUFFIX = "RECOVERED_APPENDED_SUFFIX"
    RECOVERED_CLEARED_PENDING = "RECOVERED_CLEARED_PENDING"


@dataclass(frozen=True)
class RegistryLineage:
    """Immutable identity and token epoch for one recovery-control lineage."""

    registry_lineage_id: str
    token_epoch: str
    format_version: int
    security_profile: str
    created_at: str


@dataclass(frozen=True)
class RegistryEvent:
    """One canonical, HMAC-authenticated append-only journal record."""

    registry_lineage_id: str
    token_epoch: str
    sequence: int
    prior_hash: str
    event_id: str
    event_kind: RegistryEventKind
    operation_id: str
    store_lineage_id: str
    actor_id: str
    occurred_at: str
    reason_code: str
    outcome_code: str
    control_payload: Mapping[str, object]
    record_mac: str
    entry_hash: str


@dataclass(frozen=True)
class HeadPointer:
    sequence: int
    tail_hash: str
    operation_id: str


@dataclass(frozen=True)
class ProtectedHead:
    """Authenticated committed/pending head.

    ``protection_mac`` is produced with key material supplied by the platform
    protection boundary.  The adapter never persists that key.
    """

    registry_lineage_id: str
    token_epoch: str
    format_version: int
    security_profile: str
    committed: HeadPointer
    pending: Optional[HeadPointer]
    updated_at: str
    protection_mac: str


@dataclass(frozen=True)
class StartupAdmission:
    """Successful startup result.

    Integrity failures do not produce a partially trusted object; the adapter
    raises ``RegistryAdmissionError`` and the application must remain closed.
    """

    status: StartupAdmissionStatus
    lineage: RegistryLineage
    head: ProtectedHead
    verified_event_count: int

    @property
    def admitted(self) -> bool:
        return True


class RegistryError(RuntimeError):
    """Base error for recovery-control authority operations."""


class RegistryAlreadyExistsError(RegistryError):
    """Fresh genesis was requested where registry authority already exists."""


class RegistryAdmissionError(RegistryError):
    """The registry could not be authenticated and startup must fail closed."""


class RegistryValidationError(RegistryError):
    """A caller supplied an invalid control-plane event."""


@runtime_checkable
class DisposalRegistryPort(Protocol):
    """Replaceable application port; backup/disposal workflows build on this."""

    def create_fresh(self, store_lineage_id: str, actor_id: str) -> StartupAdmission:
        ...

    def admit_startup(self) -> StartupAdmission:
        ...

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
        ...

    def read_events(self) -> Tuple[RegistryEvent, ...]:
        ...

    def advance_audit_anchor(
        self,
        stream_id: str,
        sequence: int,
        event_hmac: str,
        actor_id: str,
    ) -> RegistryEvent:
        ...

    def audit_anchor(self, stream_id: str) -> Optional[Tuple[int, str]]:
        ...

    def audit_anchors(self) -> Mapping[str, Tuple[int, str]]:
        ...

    def advance_authorization_manifest_anchor(
        self,
        version: int,
        fingerprint: str,
        key_id: str,
        actor_id: str,
    ) -> RegistryEvent:
        ...

    def authorization_manifest_anchor(self) -> Optional[Tuple[int, str, str]]:
        ...

    def prepare_disposal(
        self,
        operation_id: str,
        actor_id: str,
        *,
        scope_token: str,
        audit_stream_token: str,
        inventory_fingerprint: str,
    ) -> RegistryEvent:
        ...

    def commit_disposal(self, operation_id: str, actor_id: str) -> RegistryEvent:
        ...

    def abort_disposal(self, operation_id: str, actor_id: str) -> RegistryEvent:
        ...

    def disposal_event(self, operation_id: str) -> Optional[RegistryEvent]:
        ...
