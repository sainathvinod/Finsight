# Implements: V2 NFR-085/086/088, ADR-V2-003, AC-07 — fail-closed SQLCipher store and OS key protection.
"""Encrypted-store bootstrap for FinSight.

The authoritative database is always opened through SQLCipher.  The module intentionally has no
``sqlite3`` fallback: unavailable cipher support, an unavailable platform key store, a wrong key, or an
unverifiable database is a startup failure.  Tests use an explicit test-only key mode so they do not
write secrets to a developer's OS credential store.
"""
from __future__ import annotations

import base64
import ctypes
import hashlib
import hmac
import json
import os
import secrets
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class SecureStoreError(RuntimeError):
    """Raised when the encrypted store cannot be admitted without weakening protection."""


SQLCIPHER_PROFILE_ID = "SQLCIPHER-4.12.0-COMMUNITY-001"
SQLCIPHER_VERSION = "4.12.0 community"
SQLCIPHER_PAGE_SIZE = "4096"
SQLCIPHER_KDF_ITERATIONS = "256000"
SQLCIPHER_HMAC_ALGORITHM = "HMAC_SHA512"
SQLCIPHER_KDF_ALGORITHM = "PBKDF2_HMAC_SHA512"


@dataclass(frozen=True)
class StoreKeyMaterial:
    store_id: str
    database_key: bytes
    audit_key: bytes
    registry_key: bytes
    provider: str

    def __post_init__(self) -> None:
        for name in ("database_key", "audit_key", "registry_key"):
            if len(getattr(self, name)) != 32:
                raise ValueError(f"{name} must contain exactly 32 bytes")


class StoreKeyProvider(Protocol):
    def load_or_create(self, database_path: str) -> StoreKeyMaterial: ...


class ResolvedStoreKeyProvider:
    """Adapter used after pre-store registry admission has already resolved platform key material."""

    def __init__(self, material: StoreKeyMaterial):
        self._material = material
        self.machine_shared = not material.provider.startswith("TEST")

    def load_or_create(self, database_path: str) -> StoreKeyMaterial:
        return self._material


def _derive(root: bytes, purpose: bytes) -> bytes:
    return hmac.new(root, b"FinSight/V2/" + purpose, hashlib.sha256).digest()


def _material(store_id: str, root: bytes, provider: str) -> StoreKeyMaterial:
    if len(root) != 32:
        raise SecureStoreError("The protected FinSight store key has an invalid length.")
    return StoreKeyMaterial(
        store_id=store_id,
        database_key=_derive(root, b"database"),
        audit_key=_derive(root, b"audit-stream"),
        registry_key=_derive(root, b"recovery-registry"),
        provider=provider,
    )


def _metadata_path(database_path: str) -> Path:
    return Path(database_path + ".keymeta")


def _read_metadata(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise SecureStoreError("The FinSight key metadata is unreadable or malformed.") from exc
    if (
        not isinstance(value, dict)
        or value.get("schema") != 1
        or not isinstance(value.get("store_id"), str)
        or not value["store_id"]
    ):
        raise SecureStoreError("The FinSight key metadata failed schema validation.")
    return value


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def enforce_store_permissions(path: str, *, machine_shared: bool = False) -> None:
    """Apply and verify restrictive local-store permissions.

    Test stores use owner-only POSIX modes. Production stores use the
    deployment-managed FinSight group so sequential authorized accounts can
    open the same machine-local review store. Windows grants only that group,
    SYSTEM, and Administrators. Failure is fatal.
    """

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        directory_mode = 0o770 if machine_shared else 0o700
        file_mode = 0o660 if machine_shared else 0o600
        if machine_shared:
            try:
                import grp

                group_name = os.environ.get(
                    "FINSIGHT_POSIX_ACCESS_GROUP", "finsight"
                )
                expected_group = grp.getgrnam(group_name).gr_gid
            except (ImportError, KeyError) as exc:
                raise SecureStoreError(
                    "The deployment-approved FinSight access group is unavailable."
                ) from exc
            if target.parent.stat().st_gid != expected_group:
                raise SecureStoreError(
                    "The FinSight store directory is not assigned to the approved access group."
                )
        os.chmod(target.parent, directory_mode)
        if target.exists():
            os.chmod(target, file_mode)
        if stat.S_IMODE(target.parent.stat().st_mode) != directory_mode:
            raise SecureStoreError(
                "The FinSight store directory permissions do not match the approved profile."
            )
        if target.exists() and stat.S_IMODE(target.stat().st_mode) != file_mode:
            raise SecureStoreError(
                "The FinSight store file permissions do not match the approved profile."
            )
        return

    # The installer provisions this local group and enrolls approved sequential
    # actors. Current-user grants would create a per-user store and are banned.
    command = _windows_acl_command(target.parent)
    completed = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
    if completed.returncode != 0:
        raise SecureStoreError("FinSight could not apply the required Windows store ACL.")


def _windows_acl_command(directory: Path) -> list[str]:
    deployment_group = "FinSight Users"
    return [
        "icacls",
        str(directory),
        "/inheritance:r",
        "/grant:r",
        f"{deployment_group}:(OI)(CI)F",
        "SYSTEM:(OI)(CI)F",
        "*S-1-5-32-544:(OI)(CI)F",
    ]


class TestEnvironmentStoreKeyProvider:
    """Explicit test-only key provider.

    Both flags are required so a stray key variable cannot silently bypass an OS key store.
    """

    machine_shared = False

    def load_or_create(self, database_path: str) -> StoreKeyMaterial:
        if os.environ.get("FINSIGHT_TEST_MODE") != "1":
            raise SecureStoreError("The test store-key provider is disabled outside test mode.")
        raw = os.environ.get("FINSIGHT_TEST_STORE_KEY_HEX", "")
        try:
            root = bytes.fromhex(raw)
        except ValueError as exc:
            raise SecureStoreError("The test store key is not valid hexadecimal.") from exc
        if len(root) != 32:
            raise SecureStoreError("The test store key must contain exactly 32 bytes.")
        store_id = "test-" + hashlib.sha256(os.path.abspath(database_path).encode()).hexdigest()[:24]
        return _material(store_id, root, "TEST_ENVIRONMENT")


class MacOSKeychainStoreKeyProvider:
    _SERVICE = "com.finsight.financial-review-store"
    _SYSTEM_KEYCHAIN = "/Library/Keychains/System.keychain"
    machine_shared = True

    def load_or_create(self, database_path: str) -> StoreKeyMaterial:
        if sys.platform != "darwin":
            raise SecureStoreError("The macOS Keychain provider is unavailable on this platform.")
        meta_path = _metadata_path(database_path)
        if meta_path.exists():
            metadata = _read_metadata(meta_path)
            if metadata.get("provider") != "MACOS_SYSTEM_KEYCHAIN":
                raise SecureStoreError("The FinSight key provider does not match this platform.")
            store_id = metadata["store_id"]
            root = self._find(store_id)
        else:
            store_id = secrets.token_hex(16)
            root = secrets.token_bytes(32)
            self._save(store_id, root)
            try:
                _atomic_json(
                    meta_path,
                    {
                        "schema": 1,
                        "store_id": store_id,
                        "provider": "MACOS_SYSTEM_KEYCHAIN",
                    },
                )
            except Exception:
                self._delete(store_id)
                raise
        enforce_store_permissions(str(meta_path), machine_shared=True)
        return _material(store_id, root, "MACOS_SYSTEM_KEYCHAIN")

    def _find(self, store_id: str) -> bytes:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-k",
                self._SYSTEM_KEYCHAIN,
                "-s",
                self._SERVICE,
                "-a",
                store_id,
                "-w",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode != 0:
            raise SecureStoreError("The FinSight database key is unavailable from macOS Keychain.")
        try:
            root = base64.urlsafe_b64decode(result.stdout.strip().encode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise SecureStoreError("The macOS Keychain returned invalid FinSight key material.") from exc
        if len(root) != 32:
            raise SecureStoreError("The macOS Keychain returned invalid FinSight key material.")
        return root

    def _save(self, store_id: str, root: bytes) -> None:
        encoded = base64.urlsafe_b64encode(root).decode("ascii")
        result = subprocess.run(
            [
                "security",
                "add-generic-password",
                "-U",
                "-k",
                self._SYSTEM_KEYCHAIN,
                "-s",
                self._SERVICE,
                "-a",
                store_id,
                "-w",
                encoded,
                "-T",
                os.path.realpath(sys.executable),
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode != 0:
            raise SecureStoreError("FinSight could not protect its database key in macOS Keychain.")

    def _delete(self, store_id: str) -> None:
        subprocess.run(
            [
                "security",
                "delete-generic-password",
                "-k",
                self._SYSTEM_KEYCHAIN,
                "-s",
                self._SERVICE,
                "-a",
                store_id,
            ],
            capture_output=True,
            timeout=15,
            check=False,
        )


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _blob(data: bytes) -> tuple[_DataBlob, object]:
    buffer = ctypes.create_string_buffer(data)
    value = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    return value, buffer


class WindowsDpapiStoreKeyProvider:
    """Machine-scope DPAPI protection for sequential local Windows actors."""

    _LOCAL_MACHINE = 0x4
    _UI_FORBIDDEN = 0x1
    machine_shared = True

    def load_or_create(self, database_path: str) -> StoreKeyMaterial:
        if os.name != "nt":
            raise SecureStoreError("The Windows DPAPI provider is unavailable on this platform.")
        meta_path = _metadata_path(database_path)
        if meta_path.exists():
            metadata = _read_metadata(meta_path)
            if metadata.get("provider") != "WINDOWS_DPAPI_MACHINE":
                raise SecureStoreError("The FinSight key provider does not match this platform.")
            try:
                protected = base64.b64decode(metadata["wrapped_key"], validate=True)
            except (KeyError, ValueError, TypeError) as exc:
                raise SecureStoreError("The protected FinSight key metadata is malformed.") from exc
            root = self._unprotect(protected)
            store_id = metadata["store_id"]
        else:
            store_id = secrets.token_hex(16)
            root = secrets.token_bytes(32)
            protected = self._protect(root)
            _atomic_json(
                meta_path,
                {
                    "schema": 1,
                    "store_id": store_id,
                    "provider": "WINDOWS_DPAPI_MACHINE",
                    "wrapped_key": base64.b64encode(protected).decode("ascii"),
                },
            )
        enforce_store_permissions(str(meta_path), machine_shared=True)
        return _material(store_id, root, "WINDOWS_DPAPI_MACHINE")

    def _protect(self, value: bytes) -> bytes:
        return self._crypt(value, protect=True)

    def _unprotect(self, value: bytes) -> bytes:
        return self._crypt(value, protect=False)

    def _crypt(self, value: bytes, *, protect: bool) -> bytes:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        incoming, incoming_buffer = _blob(value)
        outgoing = _DataBlob()
        flags = self._UI_FORBIDDEN | (self._LOCAL_MACHINE if protect else 0)
        if protect:
            ok = crypt32.CryptProtectData(
                ctypes.byref(incoming),
                "FinSight V2 store key",
                None,
                None,
                None,
                flags,
                ctypes.byref(outgoing),
            )
        else:
            ok = crypt32.CryptUnprotectData(
                ctypes.byref(incoming), None, None, None, None, flags, ctypes.byref(outgoing)
            )
        del incoming_buffer
        if not ok:
            raise SecureStoreError("Windows DPAPI could not unlock the FinSight database key.")
        try:
            return ctypes.string_at(outgoing.pbData, outgoing.cbData)
        finally:
            kernel32.LocalFree(outgoing.pbData)


def platform_key_provider() -> StoreKeyProvider:
    if os.name == "nt":
        return WindowsDpapiStoreKeyProvider()
    if sys.platform == "darwin":
        return MacOSKeychainStoreKeyProvider()
    raise SecureStoreError(
        "No approved OS key-protection adapter is available on this platform; plaintext fallback is disabled."
    )


def _raw_key_pragma(key: bytes) -> str:
    return 'PRAGMA key = "x\'' + key.hex() + '\'"'


def _quoted_sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _is_plaintext_sqlite(path: str) -> bool:
    try:
        with open(path, "rb") as handle:
            return handle.read(16) == b"SQLite format 3\x00"
    except FileNotFoundError:
        return False


def _apply_cipher_profile(connection) -> None:
    """Apply the qualified profile before the first schema access."""

    connection.execute(f"PRAGMA cipher_page_size = {SQLCIPHER_PAGE_SIZE}")
    connection.execute(f"PRAGMA kdf_iter = {SQLCIPHER_KDF_ITERATIONS}")
    connection.execute(
        f"PRAGMA cipher_hmac_algorithm = {SQLCIPHER_HMAC_ALGORITHM}"
    )
    connection.execute(f"PRAGMA cipher_kdf_algorithm = {SQLCIPHER_KDF_ALGORITHM}")
    connection.execute("PRAGMA cipher_plaintext_header_size = 0")
    connection.execute("PRAGMA cipher_memory_security = ON")


def _pragma_text(connection, name: str) -> str:
    row = connection.execute("PRAGMA " + name).fetchone()
    return str(row[0]) if row and row[0] is not None else ""


def _verify_cipher_connection(connection) -> str:
    version = _pragma_text(connection, "cipher_version")
    status = _pragma_text(connection, "cipher_status")
    observed = {
        "cipher_page_size": _pragma_text(connection, "cipher_page_size"),
        "kdf_iter": _pragma_text(connection, "kdf_iter"),
        "cipher_hmac_algorithm": _pragma_text(connection, "cipher_hmac_algorithm"),
        "cipher_kdf_algorithm": _pragma_text(connection, "cipher_kdf_algorithm"),
        "cipher_memory_security": _pragma_text(connection, "cipher_memory_security"),
    }
    expected = {
        "cipher_page_size": SQLCIPHER_PAGE_SIZE,
        "kdf_iter": SQLCIPHER_KDF_ITERATIONS,
        "cipher_hmac_algorithm": SQLCIPHER_HMAC_ALGORITHM,
        "cipher_kdf_algorithm": SQLCIPHER_KDF_ALGORITHM,
        "cipher_memory_security": "1",
    }
    if version != SQLCIPHER_VERSION or status != "1" or observed != expected:
        raise SecureStoreError("The database driver did not prove active SQLCipher encryption.")
    # A schema read is required to prove that an existing database key is correct.
    connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
    return version


def _configure_and_verify_runtime(connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = FULL")
    connection.execute("PRAGMA secure_delete = ON")
    runtime = {
        "foreign_keys": _pragma_text(connection, "foreign_keys"),
        "journal_mode": _pragma_text(connection, "journal_mode").lower(),
        "synchronous": _pragma_text(connection, "synchronous"),
        "secure_delete": _pragma_text(connection, "secure_delete"),
    }
    if runtime != {
        "foreign_keys": "1",
        "journal_mode": "wal",
        "synchronous": "2",
        "secure_delete": "1",
    }:
        raise SecureStoreError("The encrypted store did not accept its qualified durability profile.")
    quick = connection.execute("PRAGMA quick_check").fetchall()
    cipher = connection.execute("PRAGMA cipher_integrity_check").fetchall()
    foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
    if quick != [("ok",)] or cipher or foreign_keys:
        raise SecureStoreError("The encrypted store failed startup integrity verification.")


def migrate_plaintext_database(path: str, database_key: bytes) -> None:
    """Atomically convert one closed legacy SQLite database to SQLCipher.

    SQLCipher's documented ``sqlcipher_export`` path is used; no plaintext connection is accepted by
    normal operation. A live WAL/SHM causes a fail-closed stop rather than a potentially partial copy.
    The fully verified encrypted temporary file atomically replaces the plaintext path.
    """

    if not _is_plaintext_sqlite(path):
        return
    for suffix in ("-wal", "-shm"):
        sidecar = path + suffix
        if os.path.exists(sidecar) and os.path.getsize(sidecar):
            raise SecureStoreError(
                "The legacy FinSight store has an active SQLite sidecar and cannot be migrated safely."
            )
    try:
        from sqlcipher3 import dbapi2 as sqlcipher
    except ImportError as exc:  # pragma: no cover - exercised through open path
        raise SecureStoreError("SQLCipher support is required; plaintext fallback is disabled.") from exc

    parent = Path(path).parent
    descriptor, temporary = tempfile.mkstemp(prefix=Path(path).name + ".", suffix=".encrypting", dir=parent)
    os.close(descriptor)
    os.unlink(temporary)  # SQLCipher must create a brand-new empty target.
    connection = None
    try:
        connection = sqlcipher.connect(temporary)
        connection.execute(_raw_key_pragma(database_key))
        _apply_cipher_profile(connection)
        connection.execute(
            "ATTACH DATABASE "
            + _quoted_sql_string(os.path.abspath(path))
            + " AS legacy KEY ''"
        )
        connection.execute("SELECT sqlcipher_export('main', 'legacy')")
        connection.execute("DETACH DATABASE legacy")
        connection.commit()
        _verify_cipher_connection(connection)
        connection.close()
        connection = None

        verify = sqlcipher.connect(temporary)
        try:
            verify.execute(_raw_key_pragma(database_key))
            _apply_cipher_profile(verify)
            _verify_cipher_connection(verify)
            _configure_and_verify_runtime(verify)
        finally:
            verify.close()
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        _fsync_directory(parent)
    except Exception as exc:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
        try:
            os.unlink(temporary)
        except OSError:
            pass
        if isinstance(exc, SecureStoreError):
            raise
        raise SecureStoreError("The legacy database could not be migrated to SQLCipher.") from exc


@dataclass(frozen=True)
class SecureConnection:
    connection: object
    key_material: StoreKeyMaterial
    cipher_version: str
    security_profile_id: str


def open_encrypted_connection(
    database_path: str, key_provider: StoreKeyProvider | None = None
) -> SecureConnection:
    """Open or create the authoritative SQLCipher connection and prove encryption is active."""

    try:
        from sqlcipher3 import dbapi2 as sqlcipher
    except ImportError as exc:
        raise SecureStoreError("SQLCipher support is required; plaintext fallback is disabled.") from exc

    path = os.path.abspath(database_path)
    provider = key_provider or platform_key_provider()
    machine_shared = bool(getattr(provider, "machine_shared", True))
    enforce_store_permissions(path, machine_shared=machine_shared)
    material = provider.load_or_create(path)
    if os.path.exists(path) and _is_plaintext_sqlite(path):
        migrate_plaintext_database(path, material.database_key)

    connection = sqlcipher.connect(path)
    try:
        connection.execute(_raw_key_pragma(material.database_key))
        _apply_cipher_profile(connection)
        version = _verify_cipher_connection(connection)
        _configure_and_verify_runtime(connection)
        enforce_store_permissions(path, machine_shared=machine_shared)
        for suffix in ("-wal", "-shm"):
            if os.path.exists(path + suffix):
                enforce_store_permissions(
                    path + suffix, machine_shared=machine_shared
                )
        return SecureConnection(
            connection, material, version, SQLCIPHER_PROFILE_ID
        )
    except Exception as exc:
        connection.close()
        if isinstance(exc, SecureStoreError):
            raise
        raise SecureStoreError(
            "The encrypted FinSight store could not be opened with its protected key."
        ) from exc
