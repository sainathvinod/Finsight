"""Explicit developer-only composition for Workflow 1 demos and screenshots.

This module is never imported by the production entry point. It injects the
test key provider and a bounded local Reviewer policy directly, so environment
flags cannot switch release composition into this profile.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

from finsight.app import (
    build_private_ask_fin_backend,
    build_query_services,
)
from finsight.application.security import StaticRoleAssignmentSource
from finsight.infrastructure.authorization_manifest import (
    build_local_reviewer_bootstrap_policy,
)
from finsight.infrastructure.clock import SystemClock
from finsight.infrastructure.identity import DefaultLocalIdentityProvider
from finsight.infrastructure.secure_store import TestEnvironmentStoreKeyProvider
from finsight.domain.identity import Role


_DEMO_KEY = (
    "d9ee473851ad9251043ad35aeb3f48a36"
    "fd9e85444df9d4729f1c6bc736933e8"
)


def _demo_security():
    identity_provider = DefaultLocalIdentityProvider()
    resolution = identity_provider.resolve_current_actor()
    actor = resolution.require_actor()
    clock = SystemClock()
    evaluated_at = datetime.fromisoformat(
        clock.now().replace("Z", "+00:00")
    ).astimezone(timezone.utc)
    reviewer_snapshot = build_local_reviewer_bootstrap_policy(
        actor, evaluated_at
    )
    demo_assignment = replace(
        reviewer_snapshot.assignments[0],
        allow_roles=frozenset(
            {Role.REVIEWER, Role.RULE_ADMINISTRATOR}
        ),
    )
    assignment_source = StaticRoleAssignmentSource(
        replace(
            reviewer_snapshot,
            version="LOCAL-DEMO-REVIEWER-RULE-ADMIN-1",
            fingerprint=hashlib.sha256(
                (
                    reviewer_snapshot.fingerprint
                    + "|Reviewer|Rule Administrator"
                ).encode("utf-8")
            ).hexdigest(),
            assignments=(demo_assignment,),
        )
    )
    return identity_provider, resolution, assignment_source


def build_workflow1_demo_services(data_directory: Path):
    data_directory.mkdir(parents=True, exist_ok=True)
    os.environ["FINSIGHT_TEST_MODE"] = "1"
    os.environ["FINSIGHT_TEST_STORE_KEY_HEX"] = _DEMO_KEY
    identity_provider, _resolution, assignment_source = _demo_security()
    clock = SystemClock()
    return build_query_services(
        str(data_directory / "finsight.db"),
        clock=clock,
        identity_provider=identity_provider,
        role_assignment_source=assignment_source,
        key_provider=TestEnvironmentStoreKeyProvider(),
        registry_root=str(data_directory / "disposal-registry"),
    )


def build_workflow1_demo_private_ask_fin_backend(data_directory: Path):
    """Compose the local-only Stage 2 assistant with worker-local storage."""

    os.environ["FINSIGHT_TEST_MODE"] = "1"
    os.environ["FINSIGHT_TEST_STORE_KEY_HEX"] = _DEMO_KEY
    identity_provider, resolution, assignment_source = _demo_security()
    return build_private_ask_fin_backend(
        str(data_directory / "finsight.db"),
        identity_provider=identity_provider,
        identity_resolution=resolution,
        role_assignment_source=assignment_source,
        key_provider=TestEnvironmentStoreKeyProvider(),
        registry_root=str(data_directory / "disposal-registry"),
    )
