# Verifies: FR-189 and NFR-108 Windows/default-platform identity adapters.
import os

import pytest

from finsight.infrastructure.identity import (
    DefaultLocalIdentityProvider,
    PlatformAccountIdentityProvider,
    WindowsSidIdentityProvider,
)

pytestmark = pytest.mark.security


def test_windows_provider_maps_sid_and_domain_account_to_actor():
    provider = WindowsSidIdentityProvider(
        resolver=lambda: ("S-1-5-21-1000", "ACME\\reviewer"),
        platform="darwin",
    )

    result = provider.resolve_current_actor()

    assert result.is_resolved
    assert result.require_actor().actor_id == "S-1-5-21-1000"
    assert result.require_actor().display_name == "ACME\\reviewer"
    assert result.require_actor().source == "WINDOWS_ACCOUNT"


def test_windows_provider_reports_explicit_unresolved_result():
    provider = WindowsSidIdentityProvider(
        resolver=lambda: (_ for _ in ()).throw(OSError("token failed")),
        platform="win32",
    )

    result = provider.resolve_current_actor()

    assert not result.is_resolved
    assert result.error_code == "WINDOWS_IDENTITY_UNRESOLVED"


def test_windows_provider_is_fail_closed_off_windows_without_injection():
    result = WindowsSidIdentityProvider(platform="darwin").resolve_current_actor()

    assert not result.is_resolved
    assert result.error_code == "WINDOWS_IDENTITY_UNAVAILABLE"


def test_platform_provider_uses_uid_as_stable_id_and_name_as_display_only():
    provider = PlatformAccountIdentityProvider(
        uid_resolver=lambda: 501,
        account_resolver=lambda uid: f"user-{uid}",
        platform="darwin",
    )

    result = provider.resolve_current_actor()

    assert result.require_actor().actor_id == "uid:501"
    assert result.require_actor().display_name == "user-501"
    assert result.require_actor().source == "MACOS_ACCOUNT"


@pytest.mark.skipif(
    os.name == "nt",
    reason="injects a POSIX platform, and the POSIX adapter reads the pwd module, "
    "which does not exist on Windows; the Windows SID adapter is covered separately",
)
def test_default_provider_resolves_supported_current_platform_account():
    result = DefaultLocalIdentityProvider(platform="darwin").resolve_current_actor()

    assert result.is_resolved
    assert result.require_actor().actor_id.startswith("uid:")
