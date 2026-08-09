"""Qualified machine-scoped runtime locations for the FinSight local store.

Workflow 1 supports sequential authenticated actors on one managed machine.
Authoritative review data therefore cannot live in an individual user's
profile.  Installer/deployment customization is deliberately not accepted
through process environment variables; a later packaging workflow may supply
an administrator-owned configuration adapter after validating its ACLs and
local-volume policy.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional


@dataclass(frozen=True)
class MachineRuntimePaths:
    store_path: str
    disposal_registry_root: str


def machine_runtime_paths(
    *,
    os_name: Optional[str] = None,
    platform: Optional[str] = None,
    environment: Optional[Mapping[str, str]] = None,
) -> MachineRuntimePaths:
    """Return the architecture-approved default paths for this platform.

    ``environment`` is used only to resolve Windows' system ProgramData
    location.  No FinSight-specific environment override is admitted.
    """

    effective_os = os.name if os_name is None else os_name
    effective_platform = sys.platform if platform is None else platform
    values = os.environ if environment is None else environment

    if effective_os == "nt":
        program_data = values.get("ProgramData") or r"C:\ProgramData"
        root = Path(program_data) / "FinSight"
    elif effective_platform == "darwin":
        root = Path("/Library/Application Support/FinSight")
    else:
        root = Path("/var/lib/finsight")

    return MachineRuntimePaths(
        store_path=str(root / "Stores" / "default" / "finsight.db"),
        disposal_registry_root=str(root / "Security" / "DisposalRegistry"),
    )


def user_runtime_paths(
    *,
    os_name: Optional[str] = None,
    platform: Optional[str] = None,
    environment: Optional[Mapping[str, str]] = None,
) -> MachineRuntimePaths:
    """Return the single-user store locations for the ADR-013 desktop scope.

    Used only when no administrator-provisioned signed role manifest is configured. ADR-013 scopes
    FinSight to one reviewer per installation, so the store belongs in that reviewer's own
    application-support directory, which needs no administrator rights to create. As with the
    machine-scoped locations, no FinSight-specific environment override is admitted.
    """

    effective_os = os.name if os_name is None else os_name
    effective_platform = sys.platform if platform is None else platform
    values = os.environ if environment is None else environment

    if effective_os == "nt":
        local_app_data = values.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        root = Path(local_app_data) / "FinSight"
    elif effective_platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / "FinSight"
    else:
        root = Path.home() / ".local" / "share" / "FinSight"

    return MachineRuntimePaths(
        store_path=str(root / "Stores" / "default" / "finsight.db"),
        disposal_registry_root=str(root / "Security" / "DisposalRegistry"),
    )
