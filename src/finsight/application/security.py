# Implements: FR-189, FR-190, NFR-107, NFR-108; Architecture AC-02.
"""Replaceable identity and deny-first authorization application contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Iterable, Mapping, Optional, Protocol

from finsight.domain.identity import Actor, Permission, Role


class UnresolvedIdentityError(PermissionError):
    """Raised when an operation requires a stable actor but none resolved."""


@dataclass(frozen=True)
class IdentityResolution:
    """Explicit identity outcome; unresolved identity is data, never an exception leak."""

    actor: Optional[Actor]
    error_code: Optional[str] = field(default=None, compare=False)
    message: Optional[str] = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if self.actor is None and not self.error_code:
            raise ValueError("unresolved identity requires an error_code")
        if self.actor is not None and (self.error_code or self.message):
            raise ValueError("resolved identity must not contain an error")

    @classmethod
    def resolved(cls, actor: Actor) -> "IdentityResolution":
        return cls(actor=actor)

    @classmethod
    def unresolved(cls, error_code: str, message: str) -> "IdentityResolution":
        return cls(actor=None, error_code=error_code, message=message)

    @property
    def is_resolved(self) -> bool:
        return self.actor is not None

    def require_actor(self) -> Actor:
        if self.actor is None:
            raise UnresolvedIdentityError(
                self.message or self.error_code or "identity could not be resolved"
            )
        return self.actor


class IdentityProvider(Protocol):
    """Port implemented by Windows, platform, or approved enterprise adapters."""

    def resolve_current_actor(self) -> IdentityResolution: ...


@dataclass(frozen=True)
class RolePermissionPolicy:
    """Immutable versioned mapping from extensible roles to allowlisted permissions."""

    version: str
    role_permissions: Mapping[Role, frozenset[Permission]]

    def __post_init__(self) -> None:
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("policy version must be non-empty")
        copied: dict[Role, frozenset[Permission]] = {}
        for role, permissions in self.role_permissions.items():
            canonical_role = role if isinstance(role, Role) else Role(str(role))
            copied[canonical_role] = frozenset(Permission(value) for value in permissions)
        object.__setattr__(self, "role_permissions", MappingProxyType(copied))

    def permissions_for(self, role: Role) -> frozenset[Permission]:
        return self.role_permissions.get(role, frozenset())


@dataclass(frozen=True)
class AuthorizationAssignment:
    """One actor assignment from an immutable authorization source snapshot."""

    assignment_id: str
    actor_id: str
    actor_source: str
    allow_roles: frozenset[Role] = frozenset()
    deny_roles: frozenset[Role] = frozenset()
    allow_permissions: frozenset[Permission] = frozenset()
    deny_permissions: frozenset[Permission] = frozenset()
    effective_from: datetime = datetime.min.replace(tzinfo=timezone.utc)
    effective_through: Optional[datetime] = None
    assigning_actor_id: str = "external-administrator"
    assigned_at: datetime = datetime.min.replace(tzinfo=timezone.utc)
    assignment_version: int = 1

    def __post_init__(self) -> None:
        for field_name in (
            "assignment_id",
            "actor_id",
            "actor_source",
            "assigning_actor_id",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty")
        if self.assignment_version < 1:
            raise ValueError("assignment_version must be >= 1")
        _require_aware(self.effective_from, "effective_from")
        _require_aware(self.assigned_at, "assigned_at")
        if self.effective_through is not None:
            _require_aware(self.effective_through, "effective_through")
            if self.effective_through <= self.effective_from:
                raise ValueError("effective_through must be after effective_from")
        object.__setattr__(self, "allow_roles", _roles(self.allow_roles))
        object.__setattr__(self, "deny_roles", _roles(self.deny_roles))
        object.__setattr__(self, "allow_permissions", _permissions(self.allow_permissions))
        object.__setattr__(self, "deny_permissions", _permissions(self.deny_permissions))

    def is_effective(self, at: datetime) -> bool:
        _require_aware(at, "evaluation timestamp")
        return self.effective_from <= at and (
            self.effective_through is None or at < self.effective_through
        )

    def applies_to(self, actor: Actor, at: datetime) -> bool:
        return (
            actor.actor_id == self.actor_id
            and actor.source == self.actor_source
            and self.is_effective(at)
        )


@dataclass(frozen=True)
class AuthorizationPolicySnapshot:
    """One immutable effective authorization source snapshot."""

    source_kind: str
    version: str
    fingerprint: str
    policy: RolePermissionPolicy
    assignments: tuple[AuthorizationAssignment, ...]
    key_id: Optional[str] = None
    signature_verified: bool = False
    valid_from: Optional[datetime] = None
    valid_through: Optional[datetime] = None

    def __post_init__(self) -> None:
        for field_name in ("source_kind", "version", "fingerprint"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty")
        if self.source_kind == "SIGNED_MANIFEST" and (
            not self.signature_verified or not self.key_id
        ):
            raise ValueError("signed manifest snapshots require verified signature and key_id")
        if self.valid_from is not None:
            _require_aware(self.valid_from, "valid_from")
        if self.valid_through is not None:
            _require_aware(self.valid_through, "valid_through")
        if (
            self.valid_from is not None
            and self.valid_through is not None
            and self.valid_through <= self.valid_from
        ):
            raise ValueError("valid_through must be after valid_from")

    def is_effective(self, at: datetime) -> bool:
        _require_aware(at, "evaluation timestamp")
        return (self.valid_from is None or self.valid_from <= at) and (
            self.valid_through is None or at < self.valid_through
        )


class RoleAssignmentSource(Protocol):
    """Reloadable read-only port; the product exposes no role-editing operation."""

    def load_current(
        self,
        at: datetime,
        actor: Optional[Actor] = None,
    ) -> AuthorizationPolicySnapshot: ...


class StaticRoleAssignmentSource:
    """Explicit injection/test source; production composition uses a reloading signed source."""

    def __init__(self, snapshot: AuthorizationPolicySnapshot) -> None:
        self._snapshot = snapshot

    def load_current(
        self,
        at: datetime,
        actor: Optional[Actor] = None,
    ) -> AuthorizationPolicySnapshot:
        _require_aware(at, "evaluation timestamp")
        return self._snapshot


@dataclass(frozen=True)
class AuthorizationContext:
    """Operation facts that can trigger separation-of-duties denials."""

    protected_requester_actor_id: Optional[str] = None
    role_assignment_subject_actor_id: Optional[str] = None
    explicit_denied_permissions: frozenset[Permission] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "explicit_denied_permissions",
            _permissions(self.explicit_denied_permissions),
        )


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    permission: Permission
    reason: str
    actor_id: Optional[str]
    actor_source: Optional[str]
    snapshot_version: Optional[str]
    snapshot_fingerprint: Optional[str]
    effective_assignment_ids: tuple[str, ...] = ()
    effective_roles: frozenset[Role] = frozenset()
    denied_roles: frozenset[Role] = frozenset()
    allowed_permissions: frozenset[Permission] = frozenset()
    denied_permissions: frozenset[Permission] = frozenset()


class AuthorizationService:
    """Evaluate a versioned role snapshot with explicit-denial precedence."""

    def decide(
        self,
        identity: IdentityResolution,
        permission: Permission,
        snapshot: AuthorizationPolicySnapshot,
        evaluated_at: datetime,
        context: Optional[AuthorizationContext] = None,
    ) -> AuthorizationDecision:
        requested = Permission(permission)
        _require_aware(evaluated_at, "evaluation timestamp")
        if not identity.is_resolved:
            return AuthorizationDecision(
                allowed=False,
                permission=requested,
                reason=f"IDENTITY_UNRESOLVED:{identity.error_code}",
                actor_id=None,
                actor_source=None,
                snapshot_version=snapshot.version,
                snapshot_fingerprint=snapshot.fingerprint,
            )

        actor = identity.require_actor()
        if not snapshot.is_effective(evaluated_at):
            return AuthorizationDecision(
                allowed=False,
                permission=requested,
                reason="AUTHORIZATION_SOURCE_INEFFECTIVE",
                actor_id=actor.actor_id,
                actor_source=actor.source,
                snapshot_version=snapshot.version,
                snapshot_fingerprint=snapshot.fingerprint,
            )
        effective = tuple(
            assignment
            for assignment in snapshot.assignments
            if assignment.applies_to(actor, evaluated_at)
        )
        effective_assignment_ids = tuple(
            assignment.assignment_id for assignment in effective
        )
        allowed_roles = frozenset(
            role for assignment in effective for role in assignment.allow_roles
        )
        denied_roles = frozenset(
            role for assignment in effective for role in assignment.deny_roles
        )
        allowed_permissions = {
            item
            for role in allowed_roles
            for item in snapshot.policy.permissions_for(role)
        }
        denied_permissions = {
            item
            for role in denied_roles
            for item in snapshot.policy.permissions_for(role)
        }
        for assignment in effective:
            allowed_permissions.update(assignment.allow_permissions)
            denied_permissions.update(assignment.deny_permissions)

        auth_context = context or AuthorizationContext()
        denied_permissions.update(auth_context.explicit_denied_permissions)
        if (
            requested
            in {
                Permission.RULE_PROTECTED_CHANGE_DECIDE,
                Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE,
            }
            and auth_context.protected_requester_actor_id == actor.actor_id
        ):
            denied_permissions.add(requested)
        if (
            requested is Permission.ROLE_ASSIGNMENT_APPROVE
            and auth_context.role_assignment_subject_actor_id == actor.actor_id
        ):
            denied_permissions.add(requested)

        denied = frozenset(denied_permissions)
        granted = frozenset(allowed_permissions)
        if requested in denied:
            reason = "EXPLICIT_DENY"
            allowed = False
        elif requested in granted:
            reason = "ALLOWED"
            allowed = True
        else:
            reason = "NOT_GRANTED"
            allowed = False
        return AuthorizationDecision(
            allowed=allowed,
            permission=requested,
            reason=reason,
            actor_id=actor.actor_id,
            actor_source=actor.source,
            snapshot_version=snapshot.version,
            snapshot_fingerprint=snapshot.fingerprint,
            effective_assignment_ids=effective_assignment_ids,
            effective_roles=allowed_roles,
            denied_roles=denied_roles,
            allowed_permissions=granted,
            denied_permissions=denied,
        )


def default_mvp_policy(version: str = "MVP-ROLE-POLICY-1") -> RolePermissionPolicy:
    """Return the first-release role matrix without coupling it to the rule engine."""

    reviewer = frozenset(
        {
            Permission.REVIEW_LIST,
            Permission.REVIEW_CREATE,
            Permission.REVIEW_OPEN,
            Permission.REVIEW_READ,
            Permission.REVIEW_ADVANCE,
            Permission.REVIEW_CLOSE,
            Permission.REVIEW_ARCHIVE,
            Permission.REVIEW_DISPOSAL_REQUEST,
            Permission.RULE_BOUND_READ,
        }
    )
    rule_administrator = frozenset(
        {
            Permission.RULE_LIBRARY_READ,
            Permission.RULE_OPTIONAL_DRAFT_MANAGE,
            Permission.RULE_OPTIONAL_LIFECYCLE_MANAGE,
            Permission.RULE_PROTECTED_DRAFT_MANAGE,
            Permission.RULE_PROTECTED_CHANGE_REQUEST,
            Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_REQUEST,
        }
    )
    approver = frozenset(
        {
            Permission.RULE_BOUND_READ,
            Permission.RULE_PROTECTED_CHANGE_DECIDE,
            Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE,
        }
    )
    return RolePermissionPolicy(
        version=version,
        role_permissions={
            Role.REVIEWER: reviewer,
            Role.RULE_ADMINISTRATOR: rule_administrator,
            Role.FINANCIAL_CONTROL_APPROVER: approver,
        },
    )


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _roles(values: Iterable[Role]) -> frozenset[Role]:
    return frozenset(value if isinstance(value, Role) else Role(str(value)) for value in values)


def _permissions(values: Iterable[Permission]) -> frozenset[Permission]:
    return frozenset(Permission(value) for value in values)
