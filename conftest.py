# Test bootstrap: make the src/ layout importable so `pytest` resolves the `finsight` package
# without requiring PYTHONPATH=src. (src layout; no editable install needed for the test run.)
import os
import sys
import base64

import pytest

# Workflow 1 tests use an explicit in-memory/test-secret profile. Production startup never consumes
# this key unless both test flags are deliberately set, and never falls back to plaintext storage.
os.environ.setdefault("FINSIGHT_TEST_MODE", "1")
os.environ.setdefault(
    "FINSIGHT_TEST_STORE_KEY_HEX",
    "7ec3c9291fb94a7d396d6ffa9ff21b26dd0de9c9e3c14d381b8100a0493af0bb",
)

_SRC = os.path.join(os.path.dirname(__file__), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


@pytest.fixture(scope="session")
def _signed_test_role_manifest(tmp_path_factory):
    """Create an explicit signed Reviewer manifest for legacy composition tests.

    Production never reads this fixture. Tests that exercise missing, invalid,
    or replacement manifests override/remove these values within their own
    monkeypatch scope.
    """

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from finsight.domain.identity import Role
    from finsight.infrastructure.authorization_manifest import canonical_json_bytes
    from finsight.infrastructure.identity import DefaultLocalIdentityProvider

    actor = DefaultLocalIdentityProvider().resolve_current_actor().require_actor()
    payload = {
        "schema_version": "FINSIGHT-AUTHZ-1",
        "manifest_version": 1,
        "key_id": "pytest-role-authority",
        "issued_at": "2000-01-01T00:00:00Z",
        "effective_from": "2000-01-01T00:00:01Z",
        "expires_at": "2100-01-01T00:00:00Z",
        "role_policy_version": "MVP-ROLE-POLICY-1",
        "custom_role_permissions": {},
        "assignments": [
            {
                "assignment_id": "pytest-reviewer-assignment",
                "actor_id": actor.actor_id,
                "actor_source": actor.source,
                "allow_roles": [Role.REVIEWER.value],
                "deny_roles": [],
                "allow_permissions": [],
                "deny_permissions": [],
                "effective_from": "2000-01-01T00:00:01Z",
                "effective_through": None,
                "assigning_actor_id": "pytest-security-administrator",
                "assigned_at": "2000-01-01T00:00:00Z",
                "assignment_version": 1,
            }
        ],
    }
    private_key = Ed25519PrivateKey.generate()
    root = tmp_path_factory.mktemp("signed-role-manifest")
    manifest_path = root / "roles.json"
    signature_path = root / "roles.sig"
    public_key_path = root / "roles.pub"
    manifest_path.write_bytes(canonical_json_bytes(payload))
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
    return {
        "FINSIGHT_ROLE_MANIFEST": str(manifest_path),
        "FINSIGHT_ROLE_MANIFEST_SIGNATURE": str(signature_path),
        "FINSIGHT_ROLE_MANIFEST_PUBLIC_KEY": str(public_key_path),
        "FINSIGHT_ROLE_MANIFEST_KEY_ID": "pytest-role-authority",
    }


@pytest.fixture(autouse=True)
def _explicit_test_store_composition(monkeypatch, _signed_test_role_manifest):
    """Tests inject the test key provider; release composition never selects it."""

    from finsight.infrastructure import secure_store

    for name, value in _signed_test_role_manifest.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        secure_store,
        "platform_key_provider",
        lambda: secure_store.TestEnvironmentStoreKeyProvider(),
    )
