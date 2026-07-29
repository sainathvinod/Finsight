from finsight.infrastructure.runtime_paths import machine_runtime_paths


def test_windows_runtime_is_machine_scoped_and_uses_separate_registry():
    paths = machine_runtime_paths(
        os_name="nt",
        platform="win32",
        environment={"ProgramData": r"D:\ManagedData"},
    )

    normalized_store = paths.store_path.replace("\\", "/")
    normalized_registry = paths.disposal_registry_root.replace("\\", "/")
    assert normalized_store == "D:/ManagedData/FinSight/Stores/default/finsight.db"
    assert normalized_registry == "D:/ManagedData/FinSight/Security/DisposalRegistry"
    assert "/Users/" not in normalized_store


def test_macos_runtime_matches_approved_machine_scope():
    paths = machine_runtime_paths(os_name="posix", platform="darwin", environment={})

    assert (
        paths.store_path
        == "/Library/Application Support/FinSight/Stores/default/finsight.db"
    )
    assert (
        paths.disposal_registry_root
        == "/Library/Application Support/FinSight/Security/DisposalRegistry"
    )


def test_linux_fallback_is_machine_scoped():
    paths = machine_runtime_paths(os_name="posix", platform="linux", environment={})

    assert paths.store_path == "/var/lib/finsight/Stores/default/finsight.db"
    assert (
        paths.disposal_registry_root
        == "/var/lib/finsight/Security/DisposalRegistry"
    )


def test_finsight_environment_override_cannot_redirect_authoritative_store():
    paths = machine_runtime_paths(
        os_name="posix",
        platform="darwin",
        environment={
            "FINSIGHT_DB": "/tmp/untrusted.db",
            "FINSIGHT_MACHINE_ROOT": "/tmp/untrusted",
        },
    )

    assert paths.store_path.startswith("/Library/Application Support/FinSight/")
