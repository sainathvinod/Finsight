# Implements: FR-189, FR-190, NFR-107, NFR-108; Architecture AC-02.
"""Canonical, provider-neutral identity and authorization value types.

These types deliberately contain no operating-system, persistence, UI, or rule-engine
dependencies.  An actor's stable identity is its provider-qualified ``actor_id``;
``display_name`` is presentation metadata and is not part of identity equality.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar


@dataclass(frozen=True)
class Actor:
    """One resolved human actor from a replaceable identity provider."""

    actor_id: str
    display_name: str = field(compare=False)
    source: str

    def __post_init__(self) -> None:
        for field_name in ("actor_id", "display_name", "source"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

    @property
    def identity_source(self) -> str:
        """Compatibility-friendly explicit name used by audit projections."""

        return self.source


@dataclass(frozen=True, order=True)
class Role:
    """A role name that supports both the three MVP roles and future custom roles."""

    value: str

    REVIEWER: ClassVar["Role"]
    RULE_ADMINISTRATOR: ClassVar["Role"]
    FINANCIAL_CONTROL_APPROVER: ClassVar["Role"]

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("role value must be a non-empty string")
        if self.value != self.value.strip():
            raise ValueError("role value must not have leading or trailing whitespace")

    def __str__(self) -> str:
        return self.value


Role.REVIEWER = Role("Reviewer")
Role.RULE_ADMINISTRATOR = Role("Rule Administrator")
Role.FINANCIAL_CONTROL_APPROVER = Role("Financial Control Approver")


class Permission(str, Enum):
    """Allowlisted application permissions; financial rule decisions are not permissions."""

    REVIEW_LIST = "review.list"
    REVIEW_CREATE = "review.create"
    REVIEW_OPEN = "review.open"
    REVIEW_READ = "review.read"
    REVIEW_ADVANCE = "review.advance"
    REVIEW_CLOSE = "review.close"
    REVIEW_ARCHIVE = "review.archive"
    REVIEW_DISPOSAL_REQUEST = "review.disposal.request"

    RULE_BOUND_READ = "rule.bound.read"
    RULE_LIBRARY_READ = "rule.library.read"
    RULE_OPTIONAL_DRAFT_MANAGE = "rule.optional.draft.manage"
    RULE_OPTIONAL_LIFECYCLE_MANAGE = "rule.optional.lifecycle.manage"
    RULE_PROTECTED_DRAFT_MANAGE = "rule.protected.draft.manage"
    RULE_PROTECTED_CHANGE_REQUEST = "rule.protected.change.request"
    RULE_PROTECTED_CHANGE_DECIDE = "rule.protected.change.decide"
    RULE_PROTECTED_WORKSPACE_UPGRADE_REQUEST = "rule.protected.workspace_upgrade.request"
    RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE = (
        "rule.protected.workspace_upgrade.authorize"
    )

    ROLE_ASSIGNMENT_APPROVE = "role.assignment.approve"
