# Verifies: FR-190 and NFR-107 signed manifest tamper/time/rollback controls.
import base64
import copy
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from finsight.application.security import AuthorizationService, IdentityResolution
from finsight.domain.identity import Actor, Permission, Role
from finsight.infrastructure.authorization_manifest import (
    AuthorizationManifestError,
    InMemoryManifestVersionStore,
    ManifestRollbackError,
    ManifestSignatureError,
    ManifestTimeError,
    SignedAuthorizationManifestLoader,
    build_local_reviewer_bootstrap_policy,
    canonical_json_bytes,
)

pytestmark = pytest.mark.security

NOW = datetime(2026, 7, 27, 14, 0, tzinfo=timezone.utc)
ACTOR = Actor("S-1-5-21-1000", "ACME\\reviewer", "WINDOWS_ACCOUNT")


@pytest.fixture
def signing_key():
    return Ed25519PrivateKey.generate()


@pytest.fixture
def public_key_bytes(signing_key):
    return signing_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def _timestamp(value):
    return value.isoformat().replace("+00:00", "Z")


def _payload(version=1):
    return {
        "schema_version": "FINSIGHT-AUTHZ-1",
        "manifest_version": version,
        "key_id": "organization-key-1",
        "issued_at": _timestamp(NOW - timedelta(hours=2)),
        "effective_from": _timestamp(NOW - timedelta(hours=1)),
        "expires_at": _timestamp(NOW + timedelta(days=30)),
        "role_policy_version": "MVP-ROLE-POLICY-1",
        "custom_role_permissions": {
            "Review Opener": [Permission.REVIEW_LIST.value, Permission.REVIEW_OPEN.value]
        },
        "assignments": [
            {
                "assignment_id": "assignment-1",
                "actor_id": ACTOR.actor_id,
                "actor_source": ACTOR.source,
                "allow_roles": [Role.REVIEWER.value, "Review Opener"],
                "deny_roles": [],
                "allow_permissions": [],
                "deny_permissions": [],
                "effective_from": _timestamp(NOW - timedelta(minutes=30)),
                "effective_through": None,
                "assigning_actor_id": "security-admin-1",
                "assigned_at": _timestamp(NOW - timedelta(hours=2)),
                "assignment_version": 1,
            }
        ],
    }


def _signature(signing_key, payload):
    return signing_key.sign(canonical_json_bytes(payload))


def _loader(public_key_bytes, store=None):
    return SignedAuthorizationManifestLoader(
        {"organization-key-1": public_key_bytes},
        store or InMemoryManifestVersionStore(),
        now_provider=lambda: NOW,
    )


def test_valid_manifest_produces_verified_versioned_snapshot(
    signing_key, public_key_bytes
):
    payload = _payload()

    snapshot = _loader(public_key_bytes).load(
        payload, base64.b64encode(_signature(signing_key, payload)).decode("ascii")
    )

    assert snapshot.source_kind == "SIGNED_MANIFEST"
    assert snapshot.version == "1"
    assert snapshot.signature_verified
    assert snapshot.key_id == "organization-key-1"
    assert len(snapshot.fingerprint) == 64
    assert Role("Review Opener") in snapshot.policy.role_permissions
    decision = AuthorizationService().decide(
        IdentityResolution.resolved(ACTOR),
        Permission.REVIEW_OPEN,
        snapshot,
        NOW,
    )
    assert decision.allowed


def test_pre_store_verification_does_not_advance_the_durable_high_watermark(
    signing_key, public_key_bytes
):
    store = InMemoryManifestVersionStore()
    payload = _payload(version=4)

    verified = _loader(public_key_bytes, store).verify(
        payload,
        _signature(signing_key, payload),
    )

    assert verified.manifest_version == 4
    assert verified.canonical_document == canonical_json_bytes(payload)
    assert store.current() is None


def test_self_assignment_is_rejected_even_when_the_manifest_is_validly_signed(
    signing_key, public_key_bytes
):
    payload = _payload()
    payload["assignments"][0]["assigning_actor_id"] = ACTOR.actor_id

    with pytest.raises(AuthorizationManifestError, match="cannot assign"):
        _loader(public_key_bytes).verify(payload, _signature(signing_key, payload))


def test_base64_signature_file_bytes_are_accepted(signing_key, public_key_bytes):
    payload = _payload()
    encoded_file_content = base64.b64encode(_signature(signing_key, payload))

    snapshot = _loader(public_key_bytes).load(payload, encoded_file_content)

    assert snapshot.signature_verified


def test_changed_content_with_original_signature_is_rejected(
    signing_key, public_key_bytes
):
    payload = _payload()
    signature = _signature(signing_key, payload)
    tampered = copy.deepcopy(payload)
    tampered["assignments"][0]["deny_permissions"] = [Permission.REVIEW_OPEN.value]

    with pytest.raises(ManifestSignatureError):
        _loader(public_key_bytes).load(tampered, signature)


def test_unknown_key_is_rejected_before_manifest_is_used(signing_key):
    payload = _payload()

    with pytest.raises(ManifestSignatureError, match="unknown"):
        SignedAuthorizationManifestLoader(
            {},
            InMemoryManifestVersionStore(),
            now_provider=lambda: NOW,
        ).load(payload, _signature(signing_key, payload))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("issued_at", NOW + timedelta(minutes=1), "future"),
        ("effective_from", NOW + timedelta(minutes=1), "not yet"),
        ("expires_at", NOW, "expired"),
    ],
)
def test_invalid_manifest_time_windows_are_rejected(
    signing_key, public_key_bytes, field, value, message
):
    payload = _payload()
    payload[field] = _timestamp(value)
    if field == "issued_at":
        payload["effective_from"] = _timestamp(value + timedelta(minutes=1))

    with pytest.raises(ManifestTimeError, match=message):
        _loader(public_key_bytes).load(payload, _signature(signing_key, payload))


def test_rollback_and_same_version_content_reuse_are_rejected(
    signing_key, public_key_bytes
):
    store = InMemoryManifestVersionStore()
    loader = _loader(public_key_bytes, store)
    version_two = _payload(version=2)
    loader.load(version_two, _signature(signing_key, version_two))

    version_one = _payload(version=1)
    with pytest.raises(ManifestRollbackError, match="high-watermark"):
        loader.load(version_one, _signature(signing_key, version_one))

    changed_version_two = _payload(version=2)
    changed_version_two["assignments"][0]["assignment_version"] = 2
    with pytest.raises(ManifestRollbackError, match="different content"):
        loader.load(
            changed_version_two,
            _signature(signing_key, changed_version_two),
        )


def test_same_manifest_version_and_hash_is_idempotent(signing_key, public_key_bytes):
    store = InMemoryManifestVersionStore()
    loader = _loader(public_key_bytes, store)
    payload = _payload(version=3)
    signature = _signature(signing_key, payload)

    first = loader.load(payload, signature)
    second = loader.load(payload, signature)

    assert first.fingerprint == second.fingerprint
    assert store.current().version == 3


def test_loaded_snapshot_fails_closed_after_manifest_expiry(
    signing_key, public_key_bytes
):
    payload = _payload()
    snapshot = _loader(public_key_bytes).load(
        payload, _signature(signing_key, payload)
    )

    decision = AuthorizationService().decide(
        IdentityResolution.resolved(ACTOR),
        Permission.REVIEW_OPEN,
        snapshot,
        NOW + timedelta(days=30),
    )

    assert not decision.allowed
    assert decision.reason == "AUTHORIZATION_SOURCE_INEFFECTIVE"


def test_mvp_role_permissions_cannot_be_redefined(signing_key, public_key_bytes):
    payload = _payload()
    payload["custom_role_permissions"][Role.REVIEWER.value] = [
        Permission.RULE_OPTIONAL_DRAFT_MANAGE.value
    ]

    with pytest.raises(AuthorizationManifestError, match="cannot be redefined"):
        _loader(public_key_bytes).load(payload, _signature(signing_key, payload))


def test_local_bootstrap_is_explicitly_unsigned_and_reviewer_only():
    snapshot = build_local_reviewer_bootstrap_policy(
        ACTOR, NOW - timedelta(minutes=1)
    )

    assert snapshot.source_kind == "LOCAL_BOOTSTRAP"
    assert snapshot.version == "LOCAL-REVIEWER-BOOTSTRAP-1"
    assert not snapshot.signature_verified
    assert snapshot.key_id is None
    assert snapshot.assignments[0].allow_roles == frozenset({Role.REVIEWER})
    assert not snapshot.assignments[0].allow_permissions
    assert AuthorizationService().decide(
        IdentityResolution.resolved(ACTOR),
        Permission.REVIEW_CREATE,
        snapshot,
        NOW,
    ).allowed
    assert not AuthorizationService().decide(
        IdentityResolution.resolved(ACTOR),
        Permission.RULE_OPTIONAL_DRAFT_MANAGE,
        snapshot,
        NOW,
    ).allowed
