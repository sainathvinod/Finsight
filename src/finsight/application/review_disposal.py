"""Content-free contracts for governed whole-review disposal.

The confirmation preview may identify the review while it is still present.
The durable receipt deliberately uses only opaque hashes and row counts; source
paths, workbook metadata, findings, and financial values never belong in it.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


def _frozen_counts(value: Mapping[str, int]) -> Mapping[str, int]:
    counts = {str(key): int(count) for key, count in value.items()}
    if any(count < 0 for count in counts.values()):
        raise ValueError("Disposal inventory counts cannot be negative.")
    return MappingProxyType(dict(sorted(counts.items())))


def review_scope_token(review_id: str) -> str:
    return hashlib.sha256(
        b"FinSight/ReviewDisposal/Scope/v1\0" + review_id.encode("utf-8")
    ).hexdigest()


def review_audit_stream_token(review_id: str) -> str:
    return hashlib.sha256(("audit_review_" + review_id).encode("utf-8")).hexdigest()


def inventory_fingerprint(inventory: Mapping[str, int]) -> str:
    canonical = json.dumps(
        dict(sorted((str(key), int(value)) for key, value in inventory.items())),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReviewDisposalPreview:
    """Authorized, short-lived confirmation context held in process memory."""

    confirmation_token: str
    review_id: str
    reporting_period: str
    status: str
    pointer_revision: int
    scope_token: str
    inventory_fingerprint: str
    inventory: Mapping[str, int]

    def __post_init__(self) -> None:
        if not self.confirmation_token or not self.review_id:
            raise ValueError("A disposal preview requires a token and Review ID.")
        if len(self.scope_token) != 64 or len(self.inventory_fingerprint) != 64:
            raise ValueError("Disposal fingerprints must be SHA-256 values.")
        object.__setattr__(self, "inventory", _frozen_counts(self.inventory))

    @property
    def period_label(self) -> str:
        """Controller-facing name used by the permanent-delete dialog."""

        return self.reporting_period


@dataclass(frozen=True)
class ReviewDisposalReceipt:
    """Exact result returned after the review scope has been removed."""

    operation_id: str
    tombstone_id: str
    review_id: str
    scope_token: str
    inventory_fingerprint: str
    actor_id: str
    disposed_at: str
    deleted_counts: Mapping[str, int]
    retained_shared_counts: Mapping[str, int]

    def __post_init__(self) -> None:
        if not self.operation_id or not self.tombstone_id or not self.review_id:
            raise ValueError("A disposal receipt requires operation and review identities.")
        if len(self.scope_token) != 64 or len(self.inventory_fingerprint) != 64:
            raise ValueError("Disposal fingerprints must be SHA-256 values.")
        object.__setattr__(self, "deleted_counts", _frozen_counts(self.deleted_counts))
        object.__setattr__(
            self,
            "retained_shared_counts",
            _frozen_counts(self.retained_shared_counts),
        )
