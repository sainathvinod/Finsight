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
