# Verifies: the Windows startup path a packaged client machine takes — per-user store ACLs,
# per-user key protection, and single-instance locking. These exercise the Windows branches by
# injection so they run on any build host; they do not replace execution on Windows itself.
import os
import subprocess
import sys

import pytest

from finsight.infrastructure import secure_store
from finsight.infrastructure.runtime_paths import user_runtime_paths
from finsight.infrastructure.secure_store import (
    SecureStoreError,
    WindowsDpapiStoreKeyProvider,
    WindowsDpapiUserStoreKeyProvider,
    provider_is_machine_shared,
)
from finsight.infrastructure.single_instance import SingleInstanceLock


# --- store ACLs -----------------------------------------------------------------------------


def test_single_user_windows_store_is_granted_to_the_signed_in_account(monkeypatch):
    monkeypatch.setenv("USERDOMAIN", "WORKSTATION")
    monkeypatch.setenv("USERNAME", "reviewer")

    command = secure_store._windows_user_acl_command(  # noqa: SLF001 - packaging contract
        secure_store.Path(r"C:\Users\reviewer\AppData\Local\FinSight\Stores\default")
    )

    assert command[0] == "icacls"
    assert "WORKSTATION\\reviewer:(OI)(CI)F" in command
    # SYSTEM by well-known SID: the literal name is localised on non-English Windows.
    assert "*S-1-5-18:(OI)(CI)F" in command
    # Inheritance must survive. The directory already sits in the user's profile, and stripping
    # inherited ACEs before the grant lands can lock a reviewer out of their own review data.
    assert "/inheritance:r" not in command
    # No deployment group: a clean machine has none, and requiring one needs an administrator.
    assert not any("FinSight Users" in part for part in command)


def test_machine_shared_windows_store_still_requires_the_deployment_group():
    command = secure_store._windows_acl_command(  # noqa: SLF001 - packaging contract
        secure_store.Path(r"C:\ProgramData\FinSight\Stores\default")
    )

    assert any("FinSight Users" in part for part in command)
    assert "/inheritance:r" in command


def test_enforce_store_permissions_selects_the_per_user_grant_on_windows(monkeypatch, tmp_path):
    """A clean Windows machine must not need an administrator-provisioned group to start."""

    issued = {}

    def fake_run(command, **kwargs):
        issued["command"] = command
        issued["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("USERNAME", "reviewer")
    monkeypatch.delenv("USERDOMAIN", raising=False)

    secure_store.enforce_store_permissions(
        str(tmp_path / "finsight.db"), machine_shared=False, os_name="nt"
    )

    assert issued["command"][0] == "icacls"
    assert any("reviewer" in part for part in issued["command"])
    assert not any("FinSight Users" in part for part in issued["command"])
    # A windowed build must not flash a console when the helper runs.
    assert "creationflags" in issued["kwargs"]


def test_machine_shared_grant_is_still_used_when_provisioned(monkeypatch, tmp_path):
    issued = {}

    def fake_run(command, **kwargs):
        issued["command"] = command
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    secure_store.enforce_store_permissions(
        str(tmp_path / "finsight.db"), machine_shared=True, os_name="nt"
    )

    assert any("FinSight Users" in part for part in issued["command"])


def test_machine_shared_acl_failure_fails_closed(monkeypatch, tmp_path):
    """The shared store sits outside every user profile, so its explicit ACL is the guarantee."""

    def failing_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 5, "", "access denied")

    monkeypatch.setattr(subprocess, "run", failing_run)

    with pytest.raises(SecureStoreError):
        secure_store.enforce_store_permissions(
            str(tmp_path / "finsight.db"), machine_shared=True, os_name="nt"
        )


def test_per_user_acl_refusal_does_not_prevent_opening_the_store(monkeypatch, tmp_path):
    """A machine that refuses the DACL rewrite must still be able to run FinSight.

    The per-user directory is pinned inside the reviewer's own profile and already inherits an
    ACL restricting it to that account; the icacls grant is additive hardening. Treating its
    refusal as fatal made locked-down corporate images and hosted CI runners unable to start
    FinSight at all.
    """

    def failing_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 5, "", "access denied")

    monkeypatch.setattr(subprocess, "run", failing_run)
    monkeypatch.setenv("USERNAME", "reviewer")

    secure_store.enforce_store_permissions(
        str(tmp_path / "finsight.db"), machine_shared=False, os_name="nt"
    )


def test_per_user_store_survives_icacls_being_unavailable(monkeypatch, tmp_path):
    """icacls missing or blocked by endpoint protection must not be fatal for a per-user store."""

    def missing_tool(command, **kwargs):
        raise FileNotFoundError("icacls is not available")

    monkeypatch.setattr(subprocess, "run", missing_tool)
    monkeypatch.setenv("USERNAME", "reviewer")

    secure_store.enforce_store_permissions(
        str(tmp_path / "finsight.db"), machine_shared=False, os_name="nt"
    )


def test_machine_shared_store_still_fails_when_icacls_is_unavailable(monkeypatch, tmp_path):
    def missing_tool(command, **kwargs):
        raise FileNotFoundError("icacls is not available")

    monkeypatch.setattr(subprocess, "run", missing_tool)

    with pytest.raises(SecureStoreError):
        secure_store.enforce_store_permissions(
            str(tmp_path / "finsight.db"), machine_shared=True, os_name="nt"
        )


def test_store_open_call_pattern_survives_a_refusing_icacls(monkeypatch, tmp_path):
    """The exact sequence open_encrypted_connection performs for a per-user store.

    It hardens the database and then each of the -wal and -shm sidecars. Every one of those calls
    used to raise, which is why a single refusing icacls failed hundreds of tests rather than one.
    """

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 5, "", "access denied"),
    )
    monkeypatch.setenv("USERNAME", "reviewer")

    database = tmp_path / "finsight.db"
    database.write_bytes(b"")
    for suffix in ("", "-wal", "-shm"):
        secure_store.enforce_store_permissions(
            str(database) + suffix, machine_shared=False, os_name="nt"
        )


def test_helper_processes_do_not_flash_a_console_window():
    flags = secure_store._no_console_window("nt")  # noqa: SLF001 - packaging contract
    assert flags.get("creationflags") == getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    assert secure_store._no_console_window("posix") == {}  # noqa: SLF001


# --- key protection -------------------------------------------------------------------------


def test_per_user_windows_key_provider_uses_current_user_dpapi_scope():
    """CRYPTPROTECT_LOCAL_MACHINE would require the machine-shared deployment posture."""

    assert WindowsDpapiUserStoreKeyProvider._LOCAL_MACHINE == 0
    assert WindowsDpapiStoreKeyProvider._LOCAL_MACHINE == 0x4
    assert WindowsDpapiUserStoreKeyProvider.machine_shared is False
    assert WindowsDpapiStoreKeyProvider.machine_shared is True


def test_provider_tags_classify_the_windows_single_user_store():
    assert provider_is_machine_shared("WINDOWS_DPAPI_USER") is False
    assert provider_is_machine_shared("WINDOWS_DPAPI_MACHINE") is True


def test_single_user_provider_selection_on_windows():
    """An unprovisioned Windows machine composes the per-user DPAPI adapter.

    Only ``single_user_key_provider`` is asserted here: the session fixture replaces
    ``platform_key_provider`` with the explicit test provider, so calling it would exercise the
    stub rather than the selector. The machine-shared class is covered by the scope test above.
    """

    assert isinstance(
        secure_store.single_user_key_provider(os_name="nt"),
        WindowsDpapiUserStoreKeyProvider,
    )


# --- store location -------------------------------------------------------------------------


def test_windows_single_user_store_lives_in_the_users_own_profile():
    paths = user_runtime_paths(
        os_name="nt",
        platform="win32",
        environment={"LOCALAPPDATA": r"C:\Users\reviewer\AppData\Local"},
    )

    normalized = paths.store_path.replace("\\", "/")
    assert normalized.startswith("C:/Users/reviewer/AppData/Local/FinSight/")
    # Never the machine-wide location, which needs an administrator to create.
    assert "ProgramData" not in paths.store_path


# --- single instance ------------------------------------------------------------------------


def test_clean_windows_machine_reaches_a_working_startup_decision_chain(monkeypatch, tmp_path):
    """Every startup gate a fresh Windows install passes through, with no administrator.

    This is the decision chain, not the native calls: DPAPI and icacls themselves can only run on
    Windows. What it proves is that an unprovisioned machine selects the per-user store, the
    per-user key adapter, the local bootstrap authorization, and a grant that names no
    deployment group — so nothing in the chain demands an administrator.
    """

    from finsight.infrastructure.authorization_source import authorization_is_configured

    for name in (
        "FINSIGHT_ROLE_MANIFEST",
        "FINSIGHT_ROLE_MANIFEST_SIGNATURE",
        "FINSIGHT_ROLE_MANIFEST_PUBLIC_KEY",
        "FINSIGHT_ROLE_MANIFEST_KEY_ID",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\reviewer\AppData\Local")
    monkeypatch.setenv("USERNAME", "reviewer")
    monkeypatch.delenv("USERDOMAIN", raising=False)

    # 1. No administrator manifest is provisioned -> the single-user profile is selected.
    assert authorization_is_configured({}) is False

    # 2. The store resolves inside the reviewer's own profile.
    paths = user_runtime_paths(
        os_name="nt", platform="win32", environment=dict(os.environ)
    )
    assert "AppData" in paths.store_path and "ProgramData" not in paths.store_path

    # 3. The key is protected at current-user DPAPI scope, marked single-user.
    provider = secure_store.single_user_key_provider(os_name="nt")
    assert isinstance(provider, WindowsDpapiUserStoreKeyProvider)
    assert provider.machine_shared is False
    assert provider_is_machine_shared(provider._PROVIDER_TAG) is False  # noqa: SLF001

    # 4. The directory grant names the signed-in account and no deployment group.
    issued = {}

    def record(command, **_kwargs):
        issued["command"] = command
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", record)
    secure_store.enforce_store_permissions(
        str(tmp_path / "finsight.db"), machine_shared=False, os_name="nt"
    )
    assert not any("FinSight Users" in part for part in issued["command"])
    assert any("reviewer" in part for part in issued["command"])


class _FakeMsvcrt:
    """Byte-range lock table keyed by the descriptor's true position, as Windows behaves.

    msvcrt.locking() locks ``nbytes`` starting at the descriptor's CURRENT offset, so the real
    offset is read back with os.lseek rather than trusting what the caller intended.
    """

    LK_NBLCK = 1
    LK_UNLCK = 0

    def __init__(self):
        self.locked_positions = []
        self.held = set()

    def locking(self, fd, mode, _nbytes):
        position = os.lseek(fd, 0, os.SEEK_CUR)
        if mode == self.LK_NBLCK:
            if position in self.held:
                raise OSError("already locked")
            self.held.add(position)
            self.locked_positions.append(position)
        else:
            self.held.discard(position)


def test_windows_single_instance_locks_a_fixed_byte(monkeypatch, tmp_path):
    """The lock byte must not move once a PID has been written to the lock file.

    msvcrt.locking() locks from the current file position and the lock file is opened in append
    mode. Without seeking to a fixed byte first, the second instance — whose append cursor sits
    past the first instance's PID — locks a *different* byte, acquires successfully, and two
    processes end up sharing one single-writer SQLite store (ADR-013 §3).
    """

    fake = _FakeMsvcrt()
    monkeypatch.setitem(sys.modules, "fcntl", None)  # force the non-POSIX branch
    monkeypatch.setitem(sys.modules, "msvcrt", fake)

    lock_path = tmp_path / "finsight.db.lock"

    first = SingleInstanceLock(str(lock_path))
    assert first.acquire() is True
    assert fake.locked_positions == [0], "the first instance must lock byte 0"
    assert lock_path.read_text(), "the holder records its pid for diagnostics"

    # The lock file is now non-empty, so an append-mode cursor no longer starts at byte 0.
    second = SingleInstanceLock(str(lock_path))
    assert second.acquire() is False, "a second instance must be refused"
    assert fake.locked_positions == [0], "contention must be evaluated at the same fixed byte"

    first.release()

    third = SingleInstanceLock(str(lock_path))
    assert third.acquire() is True, "the lock must be reusable after release"
    third.release()
