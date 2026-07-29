# Implements: FR-189, NFR-108; Architecture AC-02.
"""Operating-system identity adapters for the canonical Actor contract."""
from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes
from typing import Callable, Optional

from finsight.application.security import IdentityResolution
from finsight.domain.identity import Actor


WindowsResolver = Callable[[], tuple[str, str]]
UidResolver = Callable[[], int]
AccountResolver = Callable[[int], str]


class WindowsSidIdentityProvider:
    """Resolve the current process token to a stable SID and domain-qualified name."""

    def __init__(
        self,
        resolver: Optional[WindowsResolver] = None,
        platform: Optional[str] = None,
    ) -> None:
        self._resolver = resolver
        self._platform = platform or sys.platform

    def resolve_current_actor(self) -> IdentityResolution:
        if self._resolver is None and self._platform != "win32":
            return IdentityResolution.unresolved(
                "WINDOWS_IDENTITY_UNAVAILABLE",
                "Windows account identity is unavailable on this platform.",
            )
        try:
            sid, account_name = (
                self._resolver() if self._resolver is not None else _resolve_windows_sid()
            )
            return IdentityResolution.resolved(
                Actor(
                    actor_id=sid,
                    display_name=account_name,
                    source="WINDOWS_ACCOUNT",
                )
            )
        except Exception:
            return IdentityResolution.unresolved(
                "WINDOWS_IDENTITY_UNRESOLVED",
                "A stable Windows security identifier could not be resolved.",
            )


class PlatformAccountIdentityProvider:
    """Portable macOS/POSIX adapter behind the same identity-provider boundary."""

    def __init__(
        self,
        uid_resolver: Optional[UidResolver] = None,
        account_resolver: Optional[AccountResolver] = None,
        platform: Optional[str] = None,
    ) -> None:
        self._uid_resolver = uid_resolver or _posix_uid
        self._account_resolver = account_resolver or _posix_account_name
        self._platform = platform or sys.platform

    def resolve_current_actor(self) -> IdentityResolution:
        if os.name != "posix" and self._platform not in {"darwin", "linux"}:
            return IdentityResolution.unresolved(
                "PLATFORM_IDENTITY_UNAVAILABLE",
                "A supported platform account provider is unavailable.",
            )
        try:
            uid = self._uid_resolver()
            account_name = self._account_resolver(uid)
            source = "MACOS_ACCOUNT" if self._platform == "darwin" else "POSIX_ACCOUNT"
            return IdentityResolution.resolved(
                Actor(
                    actor_id=f"uid:{uid}",
                    display_name=account_name,
                    source=source,
                )
            )
        except Exception:
            return IdentityResolution.unresolved(
                "PLATFORM_IDENTITY_UNRESOLVED",
                "A stable platform account identifier could not be resolved.",
            )


class DefaultLocalIdentityProvider:
    """Select the required Windows adapter or supported platform substitute."""

    def __init__(self, platform: Optional[str] = None) -> None:
        selected = platform or sys.platform
        self._provider = (
            WindowsSidIdentityProvider(platform=selected)
            if selected == "win32"
            else PlatformAccountIdentityProvider(platform=selected)
        )

    def resolve_current_actor(self) -> IdentityResolution:
        return self._provider.resolve_current_actor()


class FixedIdentityProvider:
    """Composition/test adapter that returns one already-resolved immutable outcome."""

    def __init__(self, resolution: IdentityResolution) -> None:
        self._resolution = resolution

    def resolve_current_actor(self) -> IdentityResolution:
        return self._resolution


def _resolve_windows_sid() -> tuple[str, str]:
    """Read TOKEN_USER, stringify the SID, and resolve its account name."""

    if sys.platform != "win32":
        raise OSError("Windows token APIs are unavailable")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel32.LocalFree.restype = wintypes.HLOCAL

    advapi32.OpenProcessToken.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    advapi32.OpenProcessToken.restype = wintypes.BOOL
    advapi32.GetTokenInformation.argtypes = [
        wintypes.HANDLE,
        ctypes.c_uint,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi32.GetTokenInformation.restype = wintypes.BOOL
    advapi32.ConvertSidToStringSidW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.LPWSTR),
    ]
    advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL

    token = wintypes.HANDLE()
    token_query = 0x0008
    token_user_class = 1
    if not advapi32.OpenProcessToken(
        kernel32.GetCurrentProcess(), token_query, ctypes.byref(token)
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    sid_string = wintypes.LPWSTR()
    try:
        size = wintypes.DWORD()
        advapi32.GetTokenInformation(
            token, token_user_class, None, 0, ctypes.byref(size)
        )
        if not size.value:
            raise ctypes.WinError(ctypes.get_last_error())
        buffer = ctypes.create_string_buffer(size.value)
        if not advapi32.GetTokenInformation(
            token,
            token_user_class,
            buffer,
            size,
            ctypes.byref(size),
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        sid = ctypes.cast(buffer, ctypes.POINTER(_TokenUser)).contents.user.sid
        if not sid:
            raise OSError("TOKEN_USER did not contain a SID")
        if not advapi32.ConvertSidToStringSidW(sid, ctypes.byref(sid_string)):
            raise ctypes.WinError(ctypes.get_last_error())
        account_name = _lookup_account_sid(advapi32, sid)
        return sid_string.value, account_name
    finally:
        if sid_string:
            kernel32.LocalFree(ctypes.cast(sid_string, wintypes.HLOCAL))
        kernel32.CloseHandle(token)


class _SidAndAttributes(ctypes.Structure):
    _fields_ = [("sid", ctypes.c_void_p), ("attributes", wintypes.DWORD)]


class _TokenUser(ctypes.Structure):
    _fields_ = [("user", _SidAndAttributes)]


def _lookup_account_sid(advapi32, sid: ctypes.c_void_p) -> str:
    advapi32.LookupAccountSidW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.c_void_p,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(ctypes.c_uint),
    ]
    advapi32.LookupAccountSidW.restype = wintypes.BOOL

    name_size = wintypes.DWORD()
    domain_size = wintypes.DWORD()
    sid_type = ctypes.c_uint()
    advapi32.LookupAccountSidW(
        None,
        sid,
        None,
        ctypes.byref(name_size),
        None,
        ctypes.byref(domain_size),
        ctypes.byref(sid_type),
    )
    if not name_size.value:
        raise ctypes.WinError(ctypes.get_last_error())
    name = ctypes.create_unicode_buffer(name_size.value)
    domain = ctypes.create_unicode_buffer(max(1, domain_size.value))
    if not advapi32.LookupAccountSidW(
        None,
        sid,
        name,
        ctypes.byref(name_size),
        domain,
        ctypes.byref(domain_size),
        ctypes.byref(sid_type),
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return f"{domain.value}\\{name.value}" if domain.value else name.value


def _posix_account_name(uid: int) -> str:
    # Imported lazily so the required Windows adapter remains importable on Windows.
    import pwd

    return pwd.getpwuid(uid).pw_name


def _posix_uid() -> int:
    return os.getuid()
