# Verifies: FR-189 and NFR-107 canonical actor and extensible-role contracts.
from dataclasses import FrozenInstanceError

import pytest

from finsight.domain.identity import Actor, Permission, Role

pytestmark = pytest.mark.unit


def test_actor_identity_uses_stable_id_and_source_not_display_name():
    before_rename = Actor("S-1-5-21-42", "ACME\\old-name", "WINDOWS_ACCOUNT")
    after_rename = Actor("S-1-5-21-42", "ACME\\new-name", "WINDOWS_ACCOUNT")

    assert before_rename == after_rename
    assert hash(before_rename) == hash(after_rename)
    assert before_rename.identity_source == "WINDOWS_ACCOUNT"


def test_actor_is_immutable_and_requires_complete_identity():
    actor = Actor("uid:501", "reviewer", "MACOS_ACCOUNT")
    with pytest.raises(FrozenInstanceError):
        actor.actor_id = "uid:502"
    with pytest.raises(ValueError, match="actor_id"):
        Actor("", "reviewer", "MACOS_ACCOUNT")


def test_role_supports_mvp_constants_and_future_custom_names():
    custom = Role("Regional Audit Reviewer")

    assert Role.REVIEWER.value == "Reviewer"
    assert Role.RULE_ADMINISTRATOR.value == "Rule Administrator"
    assert Role.FINANCIAL_CONTROL_APPROVER.value == "Financial Control Approver"
    assert str(custom) == "Regional Audit Reviewer"
    assert Permission.REVIEW_CREATE.value == "review.create"


def test_role_rejects_ambiguous_whitespace():
    with pytest.raises(ValueError, match="whitespace"):
        Role(" Reviewer ")
