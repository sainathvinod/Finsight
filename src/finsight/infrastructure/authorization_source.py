# Implements: FR-189/190, NFR-085/090/107 — pre-store and reloadable signed authorization.
"""Production signed-role source with a cryptographic pre-store preparation boundary."""
from __future__ import annotations

import base64
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Mapping, Optional, Protocol

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from finsight.infrastructure.authorization_manifest import (
    ManifestRollbackError,
    ManifestVersionRecord,
    SignedAuthorizationManifestLoader,
    VerifiedAuthorizationManifest,
)
from finsight.domain.identity import Actor


class AuthorizationSourceConfigurationError(RuntimeError):
    """The administrator-owned signed source is absent, incomplete, or unreadable."""


class ManifestRollbackAnchorPort(Protocol):
    """External pre-store rollback authority implemented by the recovery registry."""

    def current(self) -> Optional[ManifestVersionRecord]: ...

    def advance(self, value: ManifestVersionRecord, actor_id: str) -> None: ...


@dataclass(frozen=True)
class AuthorizationManifestConfiguration:
    manifest_path: Path
    signature_path: Path
    key_id: str
    public_key: Ed25519PublicKey


@dataclass(frozen=True)
class PreparedAuthorizationSource:
    """Manifest verified before registry/database creation and ready for acceptance."""

    configuration: AuthorizationManifestConfiguration
    verified: VerifiedAuthorizationManifest


class _ObservedVersionStore:
    """Read-only high-watermark view used while cryptographically verifying a candidate."""

    def __init__(self, current: Optional[ManifestVersionRecord]) -> None:
        self._current = current

    def current(self) -> Optional[ManifestVersionRecord]:
        return self._current

    def record(self, value: ManifestVersionRecord) -> None:
        # Durable acceptance belongs to the repository/external anchor, never this verifier.
        return None


_MANIFEST_VARIABLES = (
    "FINSIGHT_ROLE_MANIFEST",
    "FINSIGHT_ROLE_MANIFEST_SIGNATURE",
    "FINSIGHT_ROLE_MANIFEST_PUBLIC_KEY",
    "FINSIGHT_ROLE_MANIFEST_KEY_ID",
)


def authorization_is_configured(
    environ: Optional[Mapping[str, str]] = None,
) -> bool:
    """Whether an administrator has begun provisioning a signed role manifest.

    True as soon as ANY manifest variable is present. A partially or incorrectly provisioned
    manifest therefore stays an error rather than silently degrading to the single-user
    bootstrap: only a wholly unconfigured machine takes the ADR-013 single-user path.
    """

    values = os.environ if environ is None else environ
    return any(values.get(name) for name in _MANIFEST_VARIABLES)


def configuration_from_environment(
    environ: Optional[Mapping[str, str]] = None,
) -> AuthorizationManifestConfiguration:
    values = os.environ if environ is None else environ
    manifest = values.get("FINSIGHT_ROLE_MANIFEST")
    signature = values.get("FINSIGHT_ROLE_MANIFEST_SIGNATURE")
    public_key_path = values.get("FINSIGHT_ROLE_MANIFEST_PUBLIC_KEY")
    key_id = values.get("FINSIGHT_ROLE_MANIFEST_KEY_ID")
    configured = (manifest, signature, public_key_path, key_id)
    if not any(configured):
        raise AuthorizationSourceConfigurationError(
            "A signed administrator-provisioned role manifest is required."
        )
    if not all(configured):
        raise AuthorizationSourceConfigurationError(
            "The signed role-manifest configuration is incomplete."
        )
    paths = tuple(Path(value) for value in configured[:3])
    for path in paths:
        if not path.is_file():
            raise AuthorizationSourceConfigurationError(
                "A configured role-manifest file is unavailable."
            )
    public_key = _load_public_key(paths[2])
    return AuthorizationManifestConfiguration(
        manifest_path=paths[0],
        signature_path=paths[1],
        key_id=str(key_id),
        public_key=public_key,
    )


def prepare_authorization_source(
    evaluated_at: datetime,
    *,
    configuration: Optional[AuthorizationManifestConfiguration] = None,
    rollback_record: Optional[ManifestVersionRecord] = None,
) -> PreparedAuthorizationSource:
    """Verify schema/key/signature/time before any registry or database is created."""

    selected = configuration or configuration_from_environment()
    verified = _read_and_verify(selected, evaluated_at, rollback_record)
    return PreparedAuthorizationSource(selected, verified)


class ReloadingSignedRoleAssignmentSource:
    """Re-read and verify the signed manifest at every protected operation boundary."""

    def __init__(
        self,
        *,
        configuration: AuthorizationManifestConfiguration,
        repository,
        prepared: PreparedAuthorizationSource,
        rollback_anchor: Optional[ManifestRollbackAnchorPort] = None,
        audit_stream=None,
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        if prepared.configuration != configuration:
            raise ValueError("prepared authorization does not match source configuration")
        self._configuration = configuration
        self._repository = repository
        self._prepared = prepared
        self._rollback_anchor = rollback_anchor
        self._audit = audit_stream
        self._id = id_factory

    def accept_prepared(self, accepted_at: str, actor: Actor) -> bool:
        """Persist the pre-store verified snapshot inside the caller's transaction."""

        self._repository.ensure_authorization_transaction()
        return self._accept_verified(
            self._prepared.verified,
            accepted_at=accepted_at,
            actor=actor,
        )

    def load_current(self, at: datetime, actor: Optional[Actor] = None):
        """Reload external bytes and atomically accept/reuse the exact verified snapshot."""

        self._repository.ensure_authorization_transaction()
        database_record = self._repository.current_authorization_manifest()
        anchor_record = (
            self._rollback_anchor.current()
            if self._rollback_anchor is not None
            else None
        )
        high_watermark = _combine_high_watermarks(database_record, anchor_record)
        verified = _read_and_verify(
            self._configuration,
            at,
            high_watermark,
        )
        if self._rollback_anchor is not None:
            if actor is None:
                raise AuthorizationSourceConfigurationError(
                    "an attributable actor is required to advance authorization rollback state"
                )
            self._rollback_anchor.advance(verified.version_record, actor.actor_id)
        self._accept_verified(
            verified,
            accepted_at=_format_time(at),
            actor=actor,
        )
        return verified.snapshot

    def _accept_verified(
        self,
        verified: VerifiedAuthorizationManifest,
        *,
        accepted_at: str,
        actor: Optional[Actor],
    ) -> bool:
        if actor is None:
            raise AuthorizationSourceConfigurationError(
                "an attributable actor is required to accept an authorization manifest"
            )
        correlation_id = "corr_auth_manifest_" + self._id()
        accepted = self._repository.accept_authorization_manifest(
            verified,
            accepted_at=accepted_at,
            accepted_by_actor_id=actor.actor_id,
            import_event_id="auth_manifest_" + self._id(),
        )
        if accepted and self._audit is not None:
            self._audit.append(
                stream_type="SECURITY",
                event_type="role_manifest_imported",
                actor=actor,
                occurred_at=accepted_at,
                correlation_id=correlation_id,
                payload={
                    "manifest_version": verified.manifest_version,
                    "manifest_fingerprint": verified.snapshot.fingerprint,
                    "key_id": verified.key_id,
                    "schema_version": verified.schema_version,
                    "role_policy_version": verified.snapshot.policy.version,
                    "assignment_ids": [
                        assignment.assignment_id
                        for assignment in verified.snapshot.assignments
                    ],
                    "outcome": "ACCEPTED",
                },
            )
        return accepted


def _read_and_verify(
    configuration: AuthorizationManifestConfiguration,
    evaluated_at: datetime,
    rollback_record: Optional[ManifestVersionRecord],
) -> VerifiedAuthorizationManifest:
    try:
        document = configuration.manifest_path.read_bytes()
        signature = configuration.signature_path.read_bytes().strip()
    except OSError as exc:
        raise AuthorizationSourceConfigurationError(
            "The configured signed role manifest could not be read."
        ) from exc
    loader = SignedAuthorizationManifestLoader(
        {configuration.key_id: configuration.public_key},
        _ObservedVersionStore(rollback_record),
        now_provider=lambda: evaluated_at,
    )
    return loader.verify(document, signature)


def _load_public_key(path: Path) -> Ed25519PublicKey:
    try:
        raw = path.read_bytes().strip()
        if raw.startswith(b"-----BEGIN"):
            key = serialization.load_pem_public_key(raw)
            if not isinstance(key, Ed25519PublicKey):
                raise ValueError("not an Ed25519 public key")
            return key
        return Ed25519PublicKey.from_public_bytes(
            base64.b64decode(raw, validate=True)
        )
    except Exception as exc:
        raise AuthorizationSourceConfigurationError(
            "The configured role-manifest public key is invalid."
        ) from exc


def _combine_high_watermarks(
    database: Optional[ManifestVersionRecord],
    external: Optional[ManifestVersionRecord],
) -> Optional[ManifestVersionRecord]:
    if database is None:
        return external
    if external is None:
        return database
    if database.version == external.version:
        if (
            database.fingerprint != external.fingerprint
            or database.key_id != external.key_id
        ):
            raise ManifestRollbackError(
                "authorization rollback authorities disagree at the same version"
            )
        return database
    return database if database.version > external.version else external


def _format_time(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("authorization evaluation time must be timezone-aware")
    return value.isoformat().replace("+00:00", "Z")
