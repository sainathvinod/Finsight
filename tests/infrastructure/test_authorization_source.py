# Verifies: FR-189/190, NFR-090/107 — reloadable, immutable signed authorization.
from __future__ import annotations

import base64
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from finsight.domain.identity import Actor, Permission, Role
from finsight.infrastructure.audit_stream import AuditStreamSqlite
from finsight.infrastructure.authorization_manifest import (
    ManifestRollbackError,
    canonical_json_bytes,
)
from finsight.infrastructure.authorization_source import (
    AuthorizationManifestConfiguration,
    ReloadingSignedRoleAssignmentSource,
    prepare_authorization_source,
)
from finsight.infrastructure.migrations.runner import run_migrations
from finsight.infrastructure.persistence import SqliteUnitOfWork
from finsight.infrastructure.review_management_repository import (
    ReviewManagementRepositorySqlite,
)

pytestmark = pytest.mark.security

NOW = datetime(2026, 7, 27, 14, 0, tzinfo=timezone.utc)
NOW_TEXT = "2026-07-27T14:00:00Z"
ACTOR = Actor("actor-501", r"ACME\reviewer", "WINDOWS_ACCOUNT")


class _Clock:
    def now(self):
        return NOW_TEXT


class _Anchor:
    def __init__(self, current=None):
        self.value = current
        self.advances = []

    def current(self):
        return self.value

    def advance(self, value, actor_id):
        self.value = value
        self.advances.append((value, actor_id))


def _timestamp(value):
    return value.isoformat().replace("+00:00", "Z")


def _payload(version=1, *, assignments=True):
    values = []
    if assignments:
        values.append(
            {
                "assignment_id": f"assignment-{version}",
                "actor_id": ACTOR.actor_id,
                "actor_source": ACTOR.source,
                "allow_roles": [Role.REVIEWER.value],
                "deny_roles": [],
                "allow_permissions": [],
                "deny_permissions": [],
                "effective_from": _timestamp(NOW - timedelta(minutes=30)),
                "effective_through": None,
                "assigning_actor_id": "security-admin-1",
                "assigned_at": _timestamp(NOW - timedelta(hours=2)),
                "assignment_version": version,
            }
        )
    return {
        "schema_version": "FINSIGHT-AUTHZ-1",
        "manifest_version": version,
        "key_id": "organization-key-1",
        "issued_at": _timestamp(NOW - timedelta(hours=2)),
        "effective_from": _timestamp(NOW - timedelta(hours=1)),
        "expires_at": _timestamp(NOW + timedelta(days=30)),
        "role_policy_version": f"MVP-ROLE-POLICY-{version}",
        "custom_role_permissions": {},
        "assignments": values,
    }


def _write(paths, private_key, payload):
    manifest_path, signature_path = paths
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    signature_path.write_bytes(
        base64.b64encode(private_key.sign(canonical_json_bytes(payload)))
    )


def _configuration(paths, private_key):
    return AuthorizationManifestConfiguration(
        manifest_path=paths[0],
        signature_path=paths[1],
        key_id="organization-key-1",
        public_key=private_key.public_key(),
    )


def _source(tmp_path):
    private_key = Ed25519PrivateKey.generate()
    paths = (tmp_path / "roles.json", tmp_path / "roles.sig")
    payload = _payload()
    _write(paths, private_key, payload)
    configuration = _configuration(paths, private_key)
    prepared = prepare_authorization_source(
        NOW,
        configuration=configuration,
    )

    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    run_migrations(connection)
    dal = SimpleNamespace(conn=connection)
    repository = ReviewManagementRepositorySqlite(dal)
    uow = SqliteUnitOfWork(dal)
    ids = iter(f"{value:032x}" for value in range(1, 100))
    audit_ids = iter(f"{value:032x}" for value in range(100, 200))
    audit = AuditStreamSqlite(
        dal,
        b"a" * 32,
        _Clock(),
        lambda: next(audit_ids),
    )
    anchor = _Anchor(prepared.verified.version_record)
    source = ReloadingSignedRoleAssignmentSource(
        configuration=configuration,
        repository=repository,
        prepared=prepared,
        rollback_anchor=anchor,
        audit_stream=audit,
        id_factory=lambda: next(ids),
    )
    return (
        connection,
        repository,
        uow,
        audit,
        anchor,
        source,
        private_key,
        paths,
        prepared,
    )


def test_accept_and_reload_preserve_complete_immutable_history_and_import_audit(
    tmp_path,
):
    (
        connection,
        repository,
        uow,
        audit,
        anchor,
        source,
        private_key,
        paths,
        prepared,
    ) = _source(tmp_path)

    with uow.atomic():
        assert source.accept_prepared(NOW_TEXT, ACTOR)

    assert repository.current_authorization_manifest() == (
        prepared.verified.version_record
    )
    assert connection.execute(
        "SELECT COUNT(*) FROM v2_authorization_manifest_snapshots"
    ).fetchone()[0] == 1
    assert connection.execute(
        "SELECT COUNT(*) FROM v2_authorization_role_snapshots"
    ).fetchone()[0] == 3
    assert connection.execute(
        "SELECT assignment_id,actor_id,assigning_actor_id "
        "FROM v2_authorization_assignment_snapshots"
    ).fetchone() == ("assignment-1", ACTOR.actor_id, "security-admin-1")
    assert connection.execute(
        "SELECT accepted_by_actor_id,outcome "
        "FROM v2_authorization_manifest_import_events"
    ).fetchone() == (ACTOR.actor_id, "ACCEPTED")
    imported = audit.events(stream_type="SECURITY")
    assert [event.event_type for event in imported] == ["role_manifest_imported"]
    assert imported[0].actor_id == ACTOR.actor_id
    assert imported[0].payload["manifest_fingerprint"] == (
        prepared.verified.snapshot.fingerprint
    )

    revoked = _payload(version=2, assignments=False)
    _write(paths, private_key, revoked)
    with uow.atomic():
        snapshot = source.load_current(NOW, ACTOR)

    assert snapshot.assignments == ()
    assert repository.current_authorization_manifest().version == 2
    assert anchor.value.version == 2
    assert connection.execute(
        "SELECT COUNT(*) FROM v2_authorization_manifest_snapshots"
    ).fetchone()[0] == 2
    assert connection.execute(
        "SELECT COUNT(*) FROM v2_authorization_manifest_import_events"
    ).fetchone()[0] == 2
    assert [event.event_type for event in audit.events(stream_type="SECURITY")] == [
        "role_manifest_imported",
        "role_manifest_imported",
    ]

    for table in (
        "v2_authorization_manifest_snapshots",
        "v2_authorization_role_snapshots",
        "v2_authorization_assignment_snapshots",
        "v2_authorization_manifest_import_events",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="append_only"):
            connection.execute(f"DELETE FROM {table}")
        connection.rollback()
    connection.close()


def test_per_operation_reload_rejects_rollback_and_same_version_equivocation(
    tmp_path,
):
    (
        connection,
        repository,
        uow,
        _audit,
        _anchor,
        source,
        private_key,
        paths,
        _prepared,
    ) = _source(tmp_path)
    with uow.atomic():
        source.accept_prepared(NOW_TEXT, ACTOR)

    version_two = _payload(version=2)
    _write(paths, private_key, version_two)
    with uow.atomic():
        source.load_current(NOW, ACTOR)

    _write(paths, private_key, _payload(version=1))
    with pytest.raises(ManifestRollbackError):
        with uow.atomic():
            source.load_current(NOW, ACTOR)

    changed_version_two = _payload(version=2)
    changed_version_two["assignments"][0]["deny_permissions"] = [
        Permission.REVIEW_OPEN.value
    ]
    _write(paths, private_key, changed_version_two)
    with pytest.raises(ManifestRollbackError):
        with uow.atomic():
            source.load_current(NOW, ACTOR)

    assert repository.current_authorization_manifest().version == 2
    assert connection.execute(
        "SELECT COUNT(*) FROM v2_authorization_manifest_import_events"
    ).fetchone()[0] == 2
    connection.close()
