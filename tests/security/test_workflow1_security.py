# Verifies: Workflow 1 fails closed before protected storage when actor identity is unresolved.
import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from finsight.app import AuthorizationConfigurationError, build_query_services
from finsight.application.security import (
    AuthorizationAssignment,
    AuthorizationPolicySnapshot,
    IdentityResolution,
    StaticRoleAssignmentSource,
    default_mvp_policy,
)
from finsight.domain.identity import Actor, Role
from finsight.infrastructure.authorization_manifest import canonical_json_bytes
from finsight.infrastructure.authorization_manifest import ManifestSignatureError
from finsight.infrastructure.identity import FixedIdentityProvider
from finsight.infrastructure.secure_store import TestEnvironmentStoreKeyProvider


class _UnresolvedIdentityProvider:
    def resolve_current_actor(self):
        return IdentityResolution.unresolved(
            "TEST_UNRESOLVED", "A stable test actor could not be resolved."
        )


def test_unresolved_identity_does_not_create_database_or_registry(tmp_path):
    database = tmp_path / "locked.db"

    try:
        build_query_services(
            str(database), identity_provider=_UnresolvedIdentityProvider()
        )
    except PermissionError:
        pass
    else:  # pragma: no cover - fail-closed contract
        raise AssertionError("unresolved identity unexpectedly opened review storage")

    assert not database.exists()
    assert not (tmp_path / "locked.db.registry").exists()


def test_identity_preflight_and_provider_cannot_be_supplied_together(tmp_path):
    database = tmp_path / "ambiguous.db"
    unresolved = IdentityResolution.unresolved("TEST", "unresolved")
    try:
        build_query_services(
            str(database),
            identity_provider=_UnresolvedIdentityProvider(),
            identity_resolution=unresolved,
        )
    except ValueError as exc:
        assert "not both" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("ambiguous identity inputs were accepted")
    assert not database.exists()


def test_missing_signed_role_manifest_does_not_open_storage(monkeypatch, tmp_path):
    monkeypatch.delenv("FINSIGHT_TEST_MODE", raising=False)
    for name in (
        "FINSIGHT_ROLE_MANIFEST",
        "FINSIGHT_ROLE_MANIFEST_SIGNATURE",
        "FINSIGHT_ROLE_MANIFEST_PUBLIC_KEY",
        "FINSIGHT_ROLE_MANIFEST_KEY_ID",
    ):
        monkeypatch.delenv(name, raising=False)
    database = tmp_path / "missing-manifest.db"
    identity = IdentityResolution.resolved(Actor("actor-1", "Reviewer", "TEST"))

    with pytest.raises(AuthorizationConfigurationError):
        build_query_services(
            str(database),
            identity_provider=FixedIdentityProvider(identity),
        )

    assert not database.exists()
    assert not (tmp_path / "missing-manifest.db.registry").exists()


def test_signed_manifest_is_composed_at_the_application_boundary(monkeypatch, tmp_path):
    actor = Actor("actor-1", "Reviewer", "TEST")
    now = datetime.now(timezone.utc)

    def timestamp(value):
        return value.isoformat().replace("+00:00", "Z")

    payload = {
        "schema_version": "FINSIGHT-AUTHZ-1",
        "manifest_version": 1,
        "key_id": "test-key-1",
        "issued_at": timestamp(now - timedelta(minutes=10)),
        "effective_from": timestamp(now - timedelta(minutes=5)),
        "expires_at": timestamp(now + timedelta(days=1)),
        "role_policy_version": "MVP-ROLE-POLICY-1",
        "custom_role_permissions": {},
        "assignments": [
            {
                "assignment_id": "assignment-1",
                "actor_id": actor.actor_id,
                "actor_source": actor.source,
                "allow_roles": [Role.REVIEWER.value],
                "deny_roles": [],
                "allow_permissions": [],
                "deny_permissions": [],
                "effective_from": timestamp(now - timedelta(minutes=5)),
                "effective_through": None,
                "assigning_actor_id": "security-admin-1",
                "assigned_at": timestamp(now - timedelta(minutes=10)),
                "assignment_version": 1,
            }
        ],
    }
    private_key = Ed25519PrivateKey.generate()
    manifest_path = tmp_path / "roles.json"
    signature_path = tmp_path / "roles.sig"
    public_key_path = tmp_path / "roles.pub"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    signature_path.write_bytes(
        base64.b64encode(private_key.sign(canonical_json_bytes(payload)))
    )
    public_key_path.write_bytes(
        base64.b64encode(
            private_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        )
    )
    monkeypatch.setenv("FINSIGHT_ROLE_MANIFEST", str(manifest_path))
    monkeypatch.setenv("FINSIGHT_ROLE_MANIFEST_SIGNATURE", str(signature_path))
    monkeypatch.setenv("FINSIGHT_ROLE_MANIFEST_PUBLIC_KEY", str(public_key_path))
    monkeypatch.setenv("FINSIGHT_ROLE_MANIFEST_KEY_ID", "test-key-1")

    services = build_query_services(
        str(tmp_path / "signed-manifest.db"),
        identity_provider=FixedIdentityProvider(IdentityResolution.resolved(actor)),
    )

    availability = services.review_management.availability()
    assert availability.can_create
    assert availability.role_labels == (Role.REVIEWER.value,)


def test_invalid_signature_is_rejected_before_store_or_registry_creation(
    monkeypatch,
    tmp_path,
):
    actor = Actor("actor-1", "Reviewer", "TEST")
    now = datetime.now(timezone.utc)

    def timestamp(value):
        return value.isoformat().replace("+00:00", "Z")

    payload = {
        "schema_version": "FINSIGHT-AUTHZ-1",
        "manifest_version": 1,
        "key_id": "test-key-1",
        "issued_at": timestamp(now - timedelta(minutes=10)),
        "effective_from": timestamp(now - timedelta(minutes=5)),
        "expires_at": timestamp(now + timedelta(days=1)),
        "role_policy_version": "MVP-ROLE-POLICY-1",
        "custom_role_permissions": {},
        "assignments": [
            {
                "assignment_id": "assignment-1",
                "actor_id": actor.actor_id,
                "actor_source": actor.source,
                "allow_roles": [Role.REVIEWER.value],
                "deny_roles": [],
                "allow_permissions": [],
                "deny_permissions": [],
                "effective_from": timestamp(now - timedelta(minutes=5)),
                "effective_through": None,
                "assigning_actor_id": "security-admin-1",
                "assigned_at": timestamp(now - timedelta(minutes=10)),
                "assignment_version": 1,
            }
        ],
    }
    private_key = Ed25519PrivateKey.generate()
    manifest_path = tmp_path / "invalid-roles.json"
    signature_path = tmp_path / "invalid-roles.sig"
    public_key_path = tmp_path / "invalid-roles.pub"
    manifest_path.write_bytes(canonical_json_bytes(payload))
    valid_signature = private_key.sign(canonical_json_bytes(payload))
    signature_path.write_bytes(
        base64.b64encode(valid_signature[:-1] + bytes([valid_signature[-1] ^ 1]))
    )
    public_key_path.write_bytes(
        base64.b64encode(
            private_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        )
    )
    monkeypatch.setenv("FINSIGHT_ROLE_MANIFEST", str(manifest_path))
    monkeypatch.setenv("FINSIGHT_ROLE_MANIFEST_SIGNATURE", str(signature_path))
    monkeypatch.setenv("FINSIGHT_ROLE_MANIFEST_PUBLIC_KEY", str(public_key_path))
    monkeypatch.setenv("FINSIGHT_ROLE_MANIFEST_KEY_ID", "test-key-1")
    database = tmp_path / "must-not-exist.db"

    with pytest.raises(ManifestSignatureError):
        build_query_services(
            str(database),
            identity_provider=FixedIdentityProvider(
                IdentityResolution.resolved(actor)
            ),
        )

    assert not database.exists()
    assert not (tmp_path / "must-not-exist.db.keymeta").exists()
    assert not (tmp_path / "must-not-exist.db.registry").exists()


def test_two_distinct_actors_sequentially_create_and_reopen_same_store(tmp_path):
    now = datetime.now(timezone.utc)
    actor_a = Actor("actor-a", "ACME\\reviewer-a", "WINDOWS_ACCOUNT")
    actor_b = Actor("actor-b", "ACME\\reviewer-b", "WINDOWS_ACCOUNT")
    assignments = tuple(
        AuthorizationAssignment(
            assignment_id=f"assignment-{actor.actor_id}",
            actor_id=actor.actor_id,
            actor_source=actor.source,
            allow_roles=frozenset({Role.REVIEWER}),
            effective_from=now - timedelta(days=1),
            assigning_actor_id="security-administrator",
            assigned_at=now - timedelta(days=1),
            assignment_version=1,
        )
        for actor in (actor_a, actor_b)
    )
    source = StaticRoleAssignmentSource(
        AuthorizationPolicySnapshot(
            source_kind="SIGNED_MANIFEST_TEST_PROJECTION",
            version="1",
            fingerprint="a" * 64,
            key_id="test-authority",
            signature_verified=True,
            policy=default_mvp_policy(),
            assignments=assignments,
            valid_from=now - timedelta(days=1),
            valid_through=now + timedelta(days=1),
        )
    )
    database = tmp_path / "shared-machine-store.db"
    registry = tmp_path / "shared-machine-registry"
    first = build_query_services(
        str(database),
        identity_provider=FixedIdentityProvider(
            IdentityResolution.resolved(actor_a)
        ),
        role_assignment_source=source,
        key_provider=TestEnvironmentStoreKeyProvider(),
        registry_root=str(registry),
    )
    created = first.review_management.create_review(
        5,
        2026,
        idempotency_key="actor-a-create",
    )
    first.review_management._repo._dal.conn.close()

    second = build_query_services(
        str(database),
        identity_provider=FixedIdentityProvider(
            IdentityResolution.resolved(actor_b)
        ),
        role_assignment_source=source,
        key_provider=TestEnvironmentStoreKeyProvider(),
        registry_root=str(registry),
    )
    reopened = second.review_management.open_review(created.review_id)
    events = second.review_management.audit_events(created.review_id)

    assert reopened.review_id == created.review_id
    assert reopened.review.created_by == actor_a.actor_id
    assert [event.event_type for event in events] == [
        "review_created",
        "review_reopened",
    ]
    assert events[0].actor_id == actor_a.actor_id
    assert events[1].actor_id == actor_b.actor_id
