# Verifies: FR-189, FR-190, NFR-107, NFR-108 deny-first authorization behavior.
from datetime import datetime, timedelta, timezone

import pytest

from finsight.application.security import (
    AuthorizationAssignment,
    AuthorizationContext,
    AuthorizationPolicySnapshot,
    AuthorizationService,
    IdentityResolution,
    RolePermissionPolicy,
    default_mvp_policy,
)
from finsight.domain.identity import Actor, Permission, Role

pytestmark = pytest.mark.security

NOW = datetime(2026, 7, 27, 14, 0, tzinfo=timezone.utc)
ACTOR = Actor("stable-42", "ACME\\reviewer", "TEST_IDP")


def _assignment(
    *,
    allow_roles=frozenset(),
    deny_roles=frozenset(),
    allow_permissions=frozenset(),
    deny_permissions=frozenset(),
    starts=NOW - timedelta(days=1),
    ends=None,
):
    return AuthorizationAssignment(
        assignment_id="assignment-1",
        actor_id=ACTOR.actor_id,
        actor_source=ACTOR.source,
        allow_roles=frozenset(allow_roles),
        deny_roles=frozenset(deny_roles),
        allow_permissions=frozenset(allow_permissions),
        deny_permissions=frozenset(deny_permissions),
        effective_from=starts,
        effective_through=ends,
        assigning_actor_id="security-admin",
        assigned_at=NOW - timedelta(days=2),
        assignment_version=1,
    )


def _snapshot(*assignments, policy=None):
    return AuthorizationPolicySnapshot(
        source_kind="TEST_POLICY",
        version="7",
        fingerprint="a" * 64,
        policy=policy or default_mvp_policy(),
        assignments=tuple(assignments),
    )


def _decide(permission, snapshot, identity=None, context=None):
    return AuthorizationService().decide(
        identity or IdentityResolution.resolved(ACTOR),
        permission,
        snapshot,
        NOW,
        context,
    )


def test_unresolved_identity_fails_closed_without_actor_attribution():
    decision = _decide(
        Permission.REVIEW_LIST,
        _snapshot(_assignment(allow_roles={Role.REVIEWER})),
        IdentityResolution.unresolved("NO_STABLE_ID", "not authenticated"),
    )

    assert not decision.allowed
    assert decision.reason == "IDENTITY_UNRESOLVED:NO_STABLE_ID"
    assert decision.actor_id is None


def test_reviewer_can_manage_reviews_but_not_manage_rules():
    snapshot = _snapshot(_assignment(allow_roles={Role.REVIEWER}))

    create = _decide(Permission.REVIEW_CREATE, snapshot)
    assert create.allowed
    assert create.effective_assignment_ids == ("assignment-1",)
    assert _decide(Permission.REVIEW_OPEN, snapshot).allowed
    assert _decide(Permission.REVIEW_CLOSE, snapshot).allowed
    assert not _decide(Permission.RULE_OPTIONAL_DRAFT_MANAGE, snapshot).allowed


def test_multiple_roles_union_their_ordinary_permissions():
    snapshot = _snapshot(
        _assignment(
            allow_roles={Role.REVIEWER, Role.RULE_ADMINISTRATOR}
        )
    )

    assert _decide(Permission.REVIEW_CREATE, snapshot).allowed
    assert _decide(Permission.RULE_OPTIONAL_DRAFT_MANAGE, snapshot).allowed


def test_explicit_permission_deny_wins_over_role_allow():
    snapshot = _snapshot(
        _assignment(
            allow_roles={Role.REVIEWER},
            deny_permissions={Permission.REVIEW_OPEN},
        )
    )

    decision = _decide(Permission.REVIEW_OPEN, snapshot)

    assert not decision.allowed
    assert decision.reason == "EXPLICIT_DENY"
    assert Permission.REVIEW_OPEN in decision.denied_permissions


def test_denied_role_permissions_win_over_union_of_allowed_roles():
    custom = Role("Review Opener")
    policy = RolePermissionPolicy(
        "custom-1",
        {
            **default_mvp_policy().role_permissions,
            custom: frozenset({Permission.REVIEW_OPEN}),
        },
    )
    snapshot = _snapshot(
        _assignment(
            allow_roles={custom, Role.REVIEWER},
            deny_roles={Role.REVIEWER},
        ),
        policy=policy,
    )

    assert not _decide(Permission.REVIEW_OPEN, snapshot).allowed


def test_assignment_window_is_start_inclusive_and_end_exclusive():
    starts_now = _snapshot(
        _assignment(allow_roles={Role.REVIEWER}, starts=NOW)
    )
    ends_now = _snapshot(
        _assignment(
            allow_roles={Role.REVIEWER},
            starts=NOW - timedelta(days=1),
            ends=NOW,
        )
    )

    assert _decide(Permission.REVIEW_LIST, starts_now).allowed
    assert not _decide(Permission.REVIEW_LIST, ends_now).allowed


def test_combined_role_actor_cannot_decide_own_protected_request():
    snapshot = _snapshot(
        _assignment(
            allow_roles={
                Role.RULE_ADMINISTRATOR,
                Role.FINANCIAL_CONTROL_APPROVER,
            }
        )
    )

    decision = _decide(
        Permission.RULE_PROTECTED_CHANGE_DECIDE,
        snapshot,
        context=AuthorizationContext(
            protected_requester_actor_id=ACTOR.actor_id
        ),
    )

    assert not decision.allowed
    assert decision.reason == "EXPLICIT_DENY"


def test_combined_role_actor_cannot_authorize_own_workspace_upgrade():
    snapshot = _snapshot(
        _assignment(
            allow_roles={
                Role.RULE_ADMINISTRATOR,
                Role.FINANCIAL_CONTROL_APPROVER,
            }
        )
    )

    decision = _decide(
        Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE,
        snapshot,
        context=AuthorizationContext(
            protected_requester_actor_id=ACTOR.actor_id
        ),
    )

    assert not decision.allowed
    assert decision.reason == "EXPLICIT_DENY"


def test_identity_provider_substitution_keeps_authorization_semantics():
    snapshot = _snapshot(_assignment(allow_roles={Role.REVIEWER}))
    renamed = Actor(ACTOR.actor_id, "renamed-user", ACTOR.source)

    original = _decide(Permission.REVIEW_CREATE, snapshot)
    replacement = _decide(
        Permission.REVIEW_CREATE,
        snapshot,
        IdentityResolution.resolved(renamed),
    )

    assert original.allowed == replacement.allowed
    assert original.allowed_permissions == replacement.allowed_permissions
