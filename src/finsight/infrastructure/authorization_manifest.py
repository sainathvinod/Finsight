# Implements: FR-190, NFR-107; Architecture AC-02 signed role-assignment source.
"""Detached Ed25519 validation for the administrator-owned role manifest.

The application has no role-editing API.  This adapter only reads a complete,
versioned, externally administered snapshot after signature, time, and rollback
validation.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Mapping, Optional, Protocol, Union

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from finsight.application.security import (
    AuthorizationAssignment,
    AuthorizationPolicySnapshot,
    RolePermissionPolicy,
    default_mvp_policy,
)
from finsight.domain.identity import Actor, Permission, Role


class AuthorizationManifestError(ValueError):
    """Base class for fail-closed manifest rejection."""


class ManifestSignatureError(AuthorizationManifestError):
    pass


class ManifestTimeError(AuthorizationManifestError):
    pass


class ManifestRollbackError(AuthorizationManifestError):
    pass


@dataclass(frozen=True)
class ManifestVersionRecord:
    version: int
    fingerprint: str
    key_id: str


@dataclass(frozen=True)
class VerifiedAuthorizationManifest:
    """Complete cryptographically verified manifest prepared for durable acceptance."""

    snapshot: AuthorizationPolicySnapshot
    canonical_document: bytes
    detached_signature: bytes
    schema_version: str
    manifest_version: int
    issued_at: datetime
    effective_from: datetime
    expires_at: datetime
    key_id: str

    @property
    def version_record(self) -> ManifestVersionRecord:
        return ManifestVersionRecord(
            self.manifest_version,
            self.snapshot.fingerprint,
            self.key_id,
        )


class ManifestVersionStore(Protocol):
    """Rollback high-watermark store supplied by protected infrastructure."""

    def current(self) -> Optional[ManifestVersionRecord]: ...

    def record(self, value: ManifestVersionRecord) -> None: ...


class InMemoryManifestVersionStore:
    """Test/bootstrap implementation; production supplies a protected durable store."""

    def __init__(self) -> None:
        self._current: Optional[ManifestVersionRecord] = None

    def current(self) -> Optional[ManifestVersionRecord]:
        return self._current

    def record(self, value: ManifestVersionRecord) -> None:
        self._current = value


PublicKeyValue = Union[Ed25519PublicKey, bytes]
NowProvider = Callable[[], datetime]

_TOP_LEVEL_FIELDS = frozenset(
    {
        "schema_version",
        "manifest_version",
        "key_id",
        "issued_at",
        "effective_from",
        "expires_at",
        "role_policy_version",
        "custom_role_permissions",
        "assignments",
    }
)
_ASSIGNMENT_FIELDS = frozenset(
    {
        "assignment_id",
        "actor_id",
        "actor_source",
        "allow_roles",
        "deny_roles",
        "allow_permissions",
        "deny_permissions",
        "effective_from",
        "effective_through",
        "assigning_actor_id",
        "assigned_at",
        "assignment_version",
    }
)
_MVP_ROLES = frozenset(
    {
        Role.REVIEWER,
        Role.RULE_ADMINISTRATOR,
        Role.FINANCIAL_CONTROL_APPROVER,
    }
)


class SignedAuthorizationManifestLoader:
    """Validate and project one detached-signed external manifest."""

    def __init__(
        self,
        trusted_keys: Mapping[str, PublicKeyValue],
        version_store: ManifestVersionStore,
        now_provider: NowProvider = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._trusted_keys = dict(trusted_keys)
        self._version_store = version_store
        self._now_provider = now_provider

    def load(
        self,
        document: Union[bytes, str, Mapping[str, object]],
        detached_signature: Union[bytes, str],
    ) -> AuthorizationPolicySnapshot:
        verified = self.verify(document, detached_signature)
        self._version_store.record(verified.version_record)
        return verified.snapshot

    def verify(
        self,
        document: Union[bytes, str, Mapping[str, object]],
        detached_signature: Union[bytes, str],
    ) -> VerifiedAuthorizationManifest:
        """Verify without accepting; safe for the pre-store startup boundary."""

        parsed = _parse_document(document)
        _require_exact_fields(parsed, _TOP_LEVEL_FIELDS, "manifest")
        canonical = canonical_json_bytes(parsed)
        fingerprint = hashlib.sha256(canonical).hexdigest()

        key_id = _required_string(parsed, "key_id")
        public_key = self._trusted_keys.get(key_id)
        if public_key is None:
            raise ManifestSignatureError(f"unknown manifest key_id: {key_id}")
        verifier = (
            Ed25519PublicKey.from_public_bytes(public_key)
            if isinstance(public_key, bytes)
            else public_key
        )
        try:
            signature = _decode_signature(detached_signature)
            verifier.verify(signature, canonical)
        except (InvalidSignature, ValueError, TypeError) as exc:
            raise ManifestSignatureError("manifest signature validation failed") from exc

        if parsed["schema_version"] != "FINSIGHT-AUTHZ-1":
            raise AuthorizationManifestError("unsupported manifest schema_version")
        version = parsed["manifest_version"]
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise AuthorizationManifestError("manifest_version must be an integer >= 1")

        now = self._now_provider()
        _require_aware(now, "current time")
        issued_at = _parse_time(parsed["issued_at"], "issued_at")
        effective_from = _parse_time(parsed["effective_from"], "effective_from")
        expires_at = _parse_time(parsed["expires_at"], "expires_at")
        if not issued_at <= effective_from < expires_at:
            raise ManifestTimeError(
                "manifest requires issued_at <= effective_from < expires_at"
            )
        if issued_at > now:
            raise ManifestTimeError("manifest issued_at is in the future")
        if now < effective_from:
            raise ManifestTimeError("manifest is not yet effective")
        if now >= expires_at:
            raise ManifestTimeError("manifest has expired")

        policy = _parse_role_policy(parsed)
        assignments = _parse_assignments(parsed["assignments"], policy)
        candidate = ManifestVersionRecord(version, fingerprint, key_id)
        _reject_rollback(self._version_store.current(), candidate)
        snapshot = AuthorizationPolicySnapshot(
            source_kind="SIGNED_MANIFEST",
            version=str(version),
            fingerprint=fingerprint,
            key_id=key_id,
            signature_verified=True,
            policy=policy,
            assignments=assignments,
            valid_from=effective_from,
            valid_through=expires_at,
        )
        return VerifiedAuthorizationManifest(
            snapshot=snapshot,
            canonical_document=canonical,
            detached_signature=signature,
            schema_version=str(parsed["schema_version"]),
            manifest_version=version,
            issued_at=issued_at,
            effective_from=effective_from,
            expires_at=expires_at,
            key_id=key_id,
        )


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    """Canonical representation signed by administrators and verified by FinSight."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AuthorizationManifestError("manifest is not canonical-JSON compatible") from exc


def build_local_reviewer_bootstrap_policy(
    actor: Actor,
    effective_from: datetime,
) -> AuthorizationPolicySnapshot:
    """Build the explicit local bootstrap policy; this is *not* a signed manifest.

    It grants exactly the MVP Reviewer role to one already-resolved local actor.
    Composition may use this bounded policy until an administrator provisions the
    externally signed manifest required by the production authorization profile.
    """

    _require_aware(effective_from, "effective_from")
    policy = default_mvp_policy()
    version = "LOCAL-REVIEWER-BOOTSTRAP-1"
    fingerprint_source = {
        "source_kind": "LOCAL_BOOTSTRAP",
        "version": version,
        "actor_id": actor.actor_id,
        "actor_source": actor.source,
        "role": Role.REVIEWER.value,
        "effective_from": _format_time(effective_from),
        "policy_version": policy.version,
    }
    fingerprint = hashlib.sha256(canonical_json_bytes(fingerprint_source)).hexdigest()
    assignment = AuthorizationAssignment(
        assignment_id=f"bootstrap:{actor.source}:{actor.actor_id}",
        actor_id=actor.actor_id,
        actor_source=actor.source,
        allow_roles=frozenset({Role.REVIEWER}),
        effective_from=effective_from,
        assigning_actor_id="finsight-local-bootstrap",
        assigned_at=effective_from,
        assignment_version=1,
    )
    return AuthorizationPolicySnapshot(
        source_kind="LOCAL_BOOTSTRAP",
        version=version,
        fingerprint=fingerprint,
        policy=policy,
        assignments=(assignment,),
        key_id=None,
        signature_verified=False,
        valid_from=effective_from,
        valid_through=None,
    )


def _parse_document(
    document: Union[bytes, str, Mapping[str, object]],
) -> dict[str, object]:
    if isinstance(document, Mapping):
        return dict(document)
    raw = document.decode("utf-8") if isinstance(document, bytes) else document

    def reject_duplicate_keys(pairs):
        parsed = {}
        for key, value in pairs:
            if key in parsed:
                raise AuthorizationManifestError(f"duplicate JSON key: {key}")
            parsed[key] = value
        return parsed

    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AuthorizationManifestError("manifest is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise AuthorizationManifestError("manifest root must be an object")
    return value


def _parse_role_policy(parsed: Mapping[str, object]) -> RolePermissionPolicy:
    policy_version = _required_string(parsed, "role_policy_version")
    custom = parsed["custom_role_permissions"]
    if not isinstance(custom, dict):
        raise AuthorizationManifestError("custom_role_permissions must be an object")
    merged = dict(default_mvp_policy(policy_version).role_permissions)
    for raw_role, raw_permissions in custom.items():
        role = Role(raw_role)
        if role in _MVP_ROLES:
            raise AuthorizationManifestError("MVP role permissions cannot be redefined")
        if not isinstance(raw_permissions, list):
            raise AuthorizationManifestError(
                f"permissions for custom role {role} must be an array"
            )
        merged[role] = frozenset(_parse_permission(value) for value in raw_permissions)
    return RolePermissionPolicy(version=policy_version, role_permissions=merged)


def _parse_assignments(
    value: object,
    policy: RolePermissionPolicy,
) -> tuple[AuthorizationAssignment, ...]:
    if not isinstance(value, list):
        raise AuthorizationManifestError("assignments must be an array")
    parsed: list[AuthorizationAssignment] = []
    assignment_ids: set[str] = set()
    known_roles = set(policy.role_permissions)
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise AuthorizationManifestError(f"assignments[{index}] must be an object")
        _require_exact_fields(item, _ASSIGNMENT_FIELDS, f"assignments[{index}]")
        assignment_id = _required_string(item, "assignment_id")
        if assignment_id in assignment_ids:
            raise AuthorizationManifestError(f"duplicate assignment_id: {assignment_id}")
        assignment_ids.add(assignment_id)
        allow_roles = _parse_roles(item["allow_roles"], known_roles, index)
        deny_roles = _parse_roles(item["deny_roles"], known_roles, index)
        effective_through = (
            None
            if item["effective_through"] is None
            else _parse_time(item["effective_through"], "effective_through")
        )
        assignment_version = item["assignment_version"]
        if isinstance(assignment_version, bool) or not isinstance(
            assignment_version, int
        ):
            raise AuthorizationManifestError("assignment_version must be an integer")
        actor_id = _required_string(item, "actor_id")
        assigning_actor_id = _required_string(item, "assigning_actor_id")
        if actor_id == assigning_actor_id:
            raise AuthorizationManifestError(
                f"assignments[{index}] cannot assign a role to its assigning actor"
            )
        parsed.append(
            AuthorizationAssignment(
                assignment_id=assignment_id,
                actor_id=actor_id,
                actor_source=_required_string(item, "actor_source"),
                allow_roles=allow_roles,
                deny_roles=deny_roles,
                allow_permissions=_parse_permissions(item["allow_permissions"], index),
                deny_permissions=_parse_permissions(item["deny_permissions"], index),
                effective_from=_parse_time(item["effective_from"], "effective_from"),
                effective_through=effective_through,
                assigning_actor_id=assigning_actor_id,
                assigned_at=_parse_time(item["assigned_at"], "assigned_at"),
                assignment_version=assignment_version,
            )
        )
    return tuple(parsed)


def _parse_roles(value: object, known: set[Role], index: int) -> frozenset[Role]:
    if not isinstance(value, list):
        raise AuthorizationManifestError(
            f"assignments[{index}] role collection must be an array"
        )
    roles = frozenset(Role(item) for item in value)
    unknown = roles.difference(known)
    if unknown:
        raise AuthorizationManifestError(
            f"assignments[{index}] references unknown roles: "
            + ", ".join(sorted(role.value for role in unknown))
        )
    return roles


def _parse_permissions(value: object, index: int) -> frozenset[Permission]:
    if not isinstance(value, list):
        raise AuthorizationManifestError(
            f"assignments[{index}] permission collection must be an array"
        )
    return frozenset(_parse_permission(item) for item in value)


def _parse_permission(value: object) -> Permission:
    try:
        return Permission(value)
    except (TypeError, ValueError) as exc:
        raise AuthorizationManifestError(f"unknown permission: {value!r}") from exc


def _parse_time(value: object, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise AuthorizationManifestError(f"{field_name} must be an RFC 3339 string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AuthorizationManifestError(
            f"{field_name} must be an RFC 3339 timestamp"
        ) from exc
    _require_aware(parsed, field_name)
    return parsed


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _required_string(value: Mapping[str, object], field_name: str) -> str:
    item = value[field_name]
    if not isinstance(item, str) or not item.strip():
        raise AuthorizationManifestError(f"{field_name} must be a non-empty string")
    return item


def _require_exact_fields(
    value: Mapping[str, object],
    expected: frozenset[str],
    context: str,
) -> None:
    actual = set(value)
    missing = expected.difference(actual)
    unknown = actual.difference(expected)
    if missing or unknown:
        raise AuthorizationManifestError(
            f"{context} fields invalid; missing={sorted(missing)}, unknown={sorted(unknown)}"
        )


def _decode_signature(value: Union[bytes, str]) -> bytes:
    if isinstance(value, bytes):
        # Detached-signature files may contain either the raw 64-byte Ed25519
        # signature or its more portable base64 representation.
        if len(value) == 64:
            return value
        try:
            value = value.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ManifestSignatureError(
                "detached signature is neither raw Ed25519 nor valid base64"
            ) from exc
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ManifestSignatureError("detached signature is not valid base64") from exc


def _reject_rollback(
    current: Optional[ManifestVersionRecord],
    candidate: ManifestVersionRecord,
) -> None:
    if current is None:
        return
    if candidate.version < current.version:
        raise ManifestRollbackError(
            f"manifest version {candidate.version} is below high-watermark "
            f"{current.version}"
        )
    if candidate.version == current.version and candidate.fingerprint != current.fingerprint:
        raise ManifestRollbackError(
            "manifest version re-use with different content is not permitted"
        )


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise AuthorizationManifestError(f"{field_name} must be timezone-aware")
