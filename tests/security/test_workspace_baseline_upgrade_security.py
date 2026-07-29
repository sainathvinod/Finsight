from __future__ import annotations

from datetime import datetime, timezone

from finsight.application.security import (
    AuthorizationAssignment,
    AuthorizationContext,
    AuthorizationPolicySnapshot,
    AuthorizationService,
    IdentityResolution,
    default_mvp_policy,
)
from finsight.domain.identity import Actor, Permission, Role


NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)


def _decision(actor: Actor, role: Role, permission: Permission, *, context=None):
    assignment = AuthorizationAssignment(
        assignment_id=f"assignment-{role.value}",
        actor_id=actor.actor_id,
        actor_source=actor.source,
        allow_roles=frozenset({role}),
        effective_from=datetime(2020, 1, 1, tzinfo=timezone.utc),
        assigning_actor_id="security-admin",
        assigned_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    snapshot = AuthorizationPolicySnapshot(
        source_kind="TEST_POLICY",
        version="workspace-upgrade-security-1",
        fingerprint="a" * 64,
        policy=default_mvp_policy(),
        assignments=(assignment,),
    )
    return AuthorizationService().decide(
        IdentityResolution.resolved(actor),
        permission,
        snapshot,
        NOW,
        context=context,
    )


def test_workspace_upgrade_permissions_are_separated_by_mvp_role():
    admin = Actor("TEST:admin", "Rule Administrator", "TEST")
    approver = Actor("TEST:approver", "Control Approver", "TEST")
    reviewer = Actor("TEST:reviewer", "Reviewer", "TEST")

    assert _decision(
        admin,
        Role.RULE_ADMINISTRATOR,
        Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_REQUEST,
    ).allowed
    assert not _decision(
        admin,
        Role.RULE_ADMINISTRATOR,
        Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE,
    ).allowed
    assert _decision(
        approver,
        Role.FINANCIAL_CONTROL_APPROVER,
        Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE,
    ).allowed
    assert not _decision(
        approver,
        Role.FINANCIAL_CONTROL_APPROVER,
        Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_REQUEST,
    ).allowed
    assert _decision(
        reviewer, Role.REVIEWER, Permission.RULE_BOUND_READ
    ).allowed


def test_combined_role_actor_is_explicitly_denied_own_upgrade_decision():
    actor = Actor("TEST:combined", "Combined Actor", "TEST")
    assignment = AuthorizationAssignment(
        assignment_id="assignment-combined",
        actor_id=actor.actor_id,
        actor_source=actor.source,
        allow_roles=frozenset(
            {
                Role.RULE_ADMINISTRATOR,
                Role.FINANCIAL_CONTROL_APPROVER,
            }
        ),
        effective_from=datetime(2020, 1, 1, tzinfo=timezone.utc),
        assigning_actor_id="security-admin",
        assigned_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    snapshot = AuthorizationPolicySnapshot(
        source_kind="TEST_POLICY",
        version="workspace-upgrade-security-1",
        fingerprint="b" * 64,
        policy=default_mvp_policy(),
        assignments=(assignment,),
    )

    decision = AuthorizationService().decide(
        IdentityResolution.resolved(actor),
        Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE,
        snapshot,
        NOW,
        context=AuthorizationContext(
            protected_requester_actor_id=actor.actor_id
        ),
    )

    assert not decision.allowed
    assert decision.reason == "EXPLICIT_DENY"
