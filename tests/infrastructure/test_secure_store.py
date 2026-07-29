"""Workflow 1 security verification for the authoritative encrypted store.

Traces: NFR-085/NFR-086/NFR-088, ADR-V2-003, Architecture AC-07.
No upload, extraction, validation, analytics, AI, reporting, or packaging behavior is exercised.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import stat
from pathlib import Path

import pytest

from finsight.infrastructure.persistence import Dal
from finsight.infrastructure.secure_store import (
    ResolvedStoreKeyProvider,
    SQLCIPHER_HMAC_ALGORITHM,
    SQLCIPHER_KDF_ALGORITHM,
    SQLCIPHER_KDF_ITERATIONS,
    SQLCIPHER_PAGE_SIZE,
    SQLCIPHER_PROFILE_ID,
    MacOSKeychainStoreKeyProvider,
    SecureStoreError,
    StoreKeyMaterial,
    TestEnvironmentStoreKeyProvider,
    _windows_acl_command,
    enforce_store_permissions,
    open_encrypted_connection,
    platform_key_provider,
)


SENTINEL = "CONFIDENTIAL-PLAINTEXT-SENTINEL-4f5fd8c5a7f44bf8"


def _material(seed: bytes, store_id: str = "store-test-001") -> StoreKeyMaterial:
    def derive(label: bytes) -> bytes:
        return hashlib.sha256(seed + b"\0" + label).digest()

    return StoreKeyMaterial(
        store_id=store_id,
        database_key=derive(b"database"),
        audit_key=derive(b"audit"),
        registry_key=derive(b"registry"),
        provider="TEST_RESOLVED",
    )


def _provider(seed: bytes, store_id: str = "store-test-001"):
    return ResolvedStoreKeyProvider(_material(seed, store_id))


def _close(secure) -> None:
    secure.connection.close()


@pytest.mark.security
def test_new_store_has_sqlcipher_header_and_no_plaintext_sentinel(tmp_path):
    database = tmp_path / "finsight.db"
    secure = open_encrypted_connection(str(database), _provider(b"correct-key"))
    try:
        secure.connection.execute("CREATE TABLE protected_values(value TEXT NOT NULL)")
        secure.connection.execute("INSERT INTO protected_values(value) VALUES(?)", (SENTINEL,))
        secure.connection.commit()
        assert secure.cipher_version
    finally:
        _close(secure)

    raw = database.read_bytes()
    assert raw[:16] != b"SQLite format 3\x00"
    for protected_file in tmp_path.glob("finsight.db*"):
        assert SENTINEL.encode("utf-8") not in protected_file.read_bytes()


@pytest.mark.security
def test_restart_with_same_key_recovers_persisted_data(tmp_path):
    database = tmp_path / "finsight.db"
    provider = _provider(b"restart-key")
    first = open_encrypted_connection(str(database), provider)
    first.connection.execute("CREATE TABLE saved_reviews(review_id TEXT PRIMARY KEY)")
    first.connection.execute("INSERT INTO saved_reviews VALUES('rev_restart')")
    first.connection.commit()
    _close(first)

    reopened = open_encrypted_connection(str(database), provider)
    try:
        assert reopened.connection.execute(
            "SELECT review_id FROM saved_reviews"
        ).fetchone() == ("rev_restart",)
    finally:
        _close(reopened)


@pytest.mark.security
def test_qualified_cipher_and_durability_profile_is_explicit(tmp_path):
    secure = open_encrypted_connection(
        str(tmp_path / "profile.db"), _provider(b"profile-key")
    )
    try:
        assert secure.security_profile_id == SQLCIPHER_PROFILE_ID
        expected = {
            "cipher_page_size": SQLCIPHER_PAGE_SIZE,
            "kdf_iter": SQLCIPHER_KDF_ITERATIONS,
            "cipher_hmac_algorithm": SQLCIPHER_HMAC_ALGORITHM,
            "cipher_kdf_algorithm": SQLCIPHER_KDF_ALGORITHM,
            "cipher_memory_security": "1",
            "foreign_keys": "1",
            "journal_mode": "wal",
            "synchronous": "2",
            "secure_delete": "1",
        }
        observed = {}
        for name in expected:
            row = secure.connection.execute("PRAGMA " + name).fetchone()
            observed[name] = str(row[0]).lower() if name == "journal_mode" else str(row[0])
        assert observed == expected
    finally:
        _close(secure)


@pytest.mark.security
def test_unqualified_cipher_version_fails_closed(monkeypatch, tmp_path):
    import finsight.infrastructure.secure_store as secure_store

    monkeypatch.setattr(secure_store, "SQLCIPHER_VERSION", "unqualified-version")
    with pytest.raises(SecureStoreError, match="active SQLCipher"):
        open_encrypted_connection(
            str(tmp_path / "unqualified.db"), _provider(b"profile-key")
        )


@pytest.mark.security
def test_persisted_security_profile_mismatch_fails_closed(tmp_path):
    database = tmp_path / "profile-mismatch.db"
    provider = _provider(b"profile-mismatch-key")
    dal = Dal(str(database), key_provider=provider)
    dal.conn.execute(
        "INSERT INTO v2_store_security_profiles(profile_id,cipher_version,cipher_page_size,"
        "kdf_iterations,hmac_algorithm,kdf_algorithm,journal_mode,synchronous_mode,binding_name,"
        "binding_version,introduced_schema_version) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "UNQUALIFIED",
            "4.12.0 community",
            4096,
            256000,
            "HMAC_SHA512",
            "PBKDF2_HMAC_SHA512",
            "wal",
            "FULL",
            "sqlcipher3",
            "0.6.2",
            4,
        ),
    )
    dal.conn.execute(
        "UPDATE v2_store_security_profile_head SET profile_id='UNQUALIFIED' WHERE singleton=1"
    )
    dal.conn.commit()
    dal.conn.close()

    with pytest.raises(SecureStoreError, match="persisted store security profile"):
        Dal(str(database), key_provider=provider)


@pytest.mark.security
def test_wrong_key_fails_closed_without_modifying_ciphertext(tmp_path):
    database = tmp_path / "finsight.db"
    correct = _provider(b"correct-key")
    created = open_encrypted_connection(str(database), correct)
    created.connection.execute("CREATE TABLE protected_values(value TEXT NOT NULL)")
    created.connection.execute("INSERT INTO protected_values VALUES(?)", (SENTINEL,))
    created.connection.commit()
    _close(created)
    before = hashlib.sha256(database.read_bytes()).hexdigest()

    with pytest.raises(SecureStoreError):
        open_encrypted_connection(
            str(database),
            _provider(b"wrong-key", store_id="store-test-001"),
        )

    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    recovered = open_encrypted_connection(str(database), correct)
    try:
        assert recovered.connection.execute(
            "SELECT value FROM protected_values"
        ).fetchone() == (SENTINEL,)
    finally:
        _close(recovered)


@pytest.mark.security
def test_legacy_plaintext_database_is_atomically_migrated_to_sqlcipher(tmp_path):
    database = tmp_path / "legacy.db"
    legacy = sqlite3.connect(database)
    legacy.execute("CREATE TABLE retained_reviews(review_id TEXT, note TEXT)")
    legacy.execute(
        "INSERT INTO retained_reviews VALUES(?,?)",
        ("legacy-review", SENTINEL),
    )
    legacy.commit()
    legacy.close()
    assert database.read_bytes()[:16] == b"SQLite format 3\x00"
    assert SENTINEL.encode("utf-8") in database.read_bytes()

    secure = open_encrypted_connection(str(database), _provider(b"migration-key"))
    try:
        assert secure.connection.execute(
            "SELECT review_id,note FROM retained_reviews"
        ).fetchone() == ("legacy-review", SENTINEL)
    finally:
        _close(secure)

    assert database.read_bytes()[:16] != b"SQLite format 3\x00"
    for protected_file in Path(tmp_path).glob("legacy.db*"):
        assert SENTINEL.encode("utf-8") not in protected_file.read_bytes()


@pytest.mark.security
def test_release_platform_provider_ignores_test_environment_flags(monkeypatch):
    monkeypatch.setenv("FINSIGHT_TEST_MODE", "1")
    monkeypatch.setenv("FINSIGHT_TEST_STORE_KEY_HEX", "ab" * 32)

    try:
        provider = platform_key_provider()
    except SecureStoreError as exc:
        assert "No approved OS key-protection adapter" in str(exc)
        return

    assert not isinstance(provider, TestEnvironmentStoreKeyProvider)


@pytest.mark.security
@pytest.mark.skipif(os.name != "posix", reason="POSIX group permission profile")
def test_machine_shared_posix_profile_uses_deployment_group_modes(
    monkeypatch, tmp_path
):
    import grp

    shared = tmp_path / "shared"
    shared.mkdir()
    database = shared / "finsight.db"
    database.write_bytes(b"protected")
    group_name = grp.getgrgid(shared.stat().st_gid).gr_name
    monkeypatch.setenv("FINSIGHT_POSIX_ACCESS_GROUP", group_name)

    enforce_store_permissions(str(database), machine_shared=True)

    assert stat.S_IMODE(shared.stat().st_mode) == 0o770
    assert stat.S_IMODE(database.stat().st_mode) == 0o660


@pytest.mark.security
def test_windows_acl_targets_deployment_group_not_current_user(tmp_path):
    command = _windows_acl_command(tmp_path / "machine-store")

    assert "FinSight Users:(OI)(CI)F" in command
    assert "SYSTEM:(OI)(CI)F" in command
    assert "*S-1-5-32-544:(OI)(CI)F" in command
    current_user = os.environ.get("USERNAME")
    if current_user:
        assert all(current_user not in value for value in command)


@pytest.mark.security
def test_macos_provider_targets_system_keychain(monkeypatch):
    observed = {}

    class Result:
        returncode = 0
        stdout = __import__("base64").urlsafe_b64encode(b"k" * 32).decode()

    def run(command, **_kwargs):
        observed["command"] = command
        return Result()

    monkeypatch.setattr("subprocess.run", run)
    provider = MacOSKeychainStoreKeyProvider()

    assert provider._find("store-id") == b"k" * 32
    assert observed["command"][
        observed["command"].index("-k") + 1
    ] == "/Library/Keychains/System.keychain"
