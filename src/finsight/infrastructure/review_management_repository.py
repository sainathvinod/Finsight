# Implements: V2 FR-123/124/195/197, NFR-082, ADR-V2-003 — Workflow 1 persistence adapters.
from __future__ import annotations

import json
from typing import Optional, Sequence

from finsight.domain.review_management import (
    ManagedReview,
    ReportingPeriod,
    ReviewCycleRecord,
    ReviewDisposition,
    ReviewPointers,
    ReviewStatus,
    ReviewStatusEvent,
    StatusOwnerKind,
    WorkingCandidate,
)
from finsight.domain.identity import Role
from finsight.infrastructure.authorization_manifest import (
    ManifestRollbackError,
    ManifestVersionRecord,
    VerifiedAuthorizationManifest,
)
from finsight.infrastructure.review_disposal import ScopedReviewDisposalSqlite


class ReviewManagementRepositorySqlite:
    """Typed persistence adapter; transaction ownership remains with the application Unit of Work."""

    def __init__(self, dal):
        self._dal = dal
        self._review_disposal = ScopedReviewDisposalSqlite(dal)

    def ensure_authorization_transaction(self) -> None:
        """Acquire the write transaction before loading the authorization snapshot."""

        if not self._dal.conn.in_transaction:
            self._dal.conn.execute("BEGIN IMMEDIATE")

    def current_authorization_manifest(self) -> Optional[ManifestVersionRecord]:
        row = self._dal.conn.execute(
            "SELECT manifest_version,manifest_hash,key_id "
            "FROM v2_authorization_manifest_state WHERE singleton=1"
        ).fetchone()
        return ManifestVersionRecord(int(row[0]), row[1], row[2]) if row else None

    def accept_authorization_manifest(
        self,
        verified: VerifiedAuthorizationManifest,
        *,
        accepted_at: str,
        accepted_by_actor_id: str,
        import_event_id: str,
    ) -> bool:
        """Append a complete accepted manifest snapshot and advance its CAS high-watermark."""

        if not self._dal.conn.in_transaction:
            raise RuntimeError(
                "authorization manifests must be accepted inside a persistence transaction"
            )
        candidate = verified.version_record
        current = self.current_authorization_manifest()
        if current is not None:
            if candidate.version < current.version:
                raise ManifestRollbackError(
                    "authorization manifest version is below the accepted high-watermark"
                )
            if candidate.version == current.version and (
                candidate.fingerprint != current.fingerprint
                or candidate.key_id != current.key_id
            ):
                raise ManifestRollbackError(
                    "authorization manifest version equivocation detected"
                )

        exists = self._dal.conn.execute(
            "SELECT 1 FROM v2_authorization_manifest_snapshots "
            "WHERE manifest_fingerprint=?",
            (candidate.fingerprint,),
        ).fetchone()
        if exists:
            return False

        snapshot = verified.snapshot
        self._dal.conn.execute(
            "INSERT INTO v2_authorization_manifest_snapshots("
            "manifest_fingerprint,manifest_version,schema_version,key_id,canonical_manifest,"
            "detached_signature,issued_at,effective_from,expires_at,role_policy_version,accepted_at"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                candidate.fingerprint,
                candidate.version,
                verified.schema_version,
                candidate.key_id,
                verified.canonical_document,
                verified.detached_signature,
                _format_time(verified.issued_at),
                _format_time(verified.effective_from),
                _format_time(verified.expires_at),
                snapshot.policy.version,
                accepted_at,
            ),
        )
        mvp_roles = {
            Role.REVIEWER,
            Role.RULE_ADMINISTRATOR,
            Role.FINANCIAL_CONTROL_APPROVER,
        }
        for role in sorted(snapshot.policy.role_permissions, key=lambda item: item.value):
            permissions = snapshot.policy.permissions_for(role)
            self._dal.conn.execute(
                "INSERT INTO v2_authorization_role_snapshots("
                "manifest_fingerprint,role_name,is_mvp,permissions_json) VALUES(?,?,?,?)",
                (
                    candidate.fingerprint,
                    role.value,
                    int(role in mvp_roles),
                    _canonical_list(permission.value for permission in permissions),
                ),
            )
        for ordinal, assignment in enumerate(snapshot.assignments, 1):
            self._dal.conn.execute(
                "INSERT INTO v2_authorization_assignment_snapshots("
                "manifest_fingerprint,ordinal,assignment_id,actor_id,actor_source,"
                "allow_roles_json,deny_roles_json,allow_permissions_json,deny_permissions_json,"
                "effective_from,effective_through,assigning_actor_id,assigned_at,assignment_version"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    candidate.fingerprint,
                    ordinal,
                    assignment.assignment_id,
                    assignment.actor_id,
                    assignment.actor_source,
                    _canonical_list(role.value for role in assignment.allow_roles),
                    _canonical_list(role.value for role in assignment.deny_roles),
                    _canonical_list(
                        permission.value for permission in assignment.allow_permissions
                    ),
                    _canonical_list(
                        permission.value for permission in assignment.deny_permissions
                    ),
                    _format_time(assignment.effective_from),
                    (
                        _format_time(assignment.effective_through)
                        if assignment.effective_through is not None
                        else None
                    ),
                    assignment.assigning_actor_id,
                    _format_time(assignment.assigned_at),
                    assignment.assignment_version,
                ),
            )
        self._dal.conn.execute(
            "INSERT INTO v2_authorization_manifest_import_events("
            "event_id,manifest_fingerprint,manifest_version,key_id,prior_manifest_version,"
            "prior_manifest_fingerprint,accepted_at,accepted_by_actor_id,outcome) "
            "VALUES(?,?,?,?,?,?,?,?,'ACCEPTED')",
            (
                import_event_id,
                candidate.fingerprint,
                candidate.version,
                candidate.key_id,
                current.version if current else None,
                current.fingerprint if current else None,
                accepted_at,
                accepted_by_actor_id,
            ),
        )
        if current is None:
            self._dal.conn.execute(
                "INSERT INTO v2_authorization_manifest_state("
                "singleton,manifest_version,manifest_hash,key_id,accepted_at) VALUES(1,?,?,?,?)",
                (
                    candidate.version,
                    candidate.fingerprint,
                    candidate.key_id,
                    accepted_at,
                ),
            )
        elif candidate.version > current.version:
            changed = self._dal.conn.execute(
                "UPDATE v2_authorization_manifest_state SET manifest_version=?,manifest_hash=?,"
                "key_id=?,accepted_at=? WHERE singleton=1 AND manifest_version=? "
                "AND manifest_hash=? AND key_id=?",
                (
                    candidate.version,
                    candidate.fingerprint,
                    candidate.key_id,
                    accepted_at,
                    current.version,
                    current.fingerprint,
                    current.key_id,
                ),
            ).rowcount
            if changed != 1:
                raise ManifestRollbackError(
                    "authorization high-watermark changed concurrently"
                )
        return True

    def save_actor_snapshot(self, actor, occurred_at: str) -> int:
        row = self._dal.conn.execute(
            "SELECT snapshot_version,display_name,identity_source FROM v2_actor_snapshots "
            "WHERE actor_id=? ORDER BY snapshot_version DESC LIMIT 1",
            (actor.actor_id,),
        ).fetchone()
        if row and row[1] == actor.display_name and row[2] == actor.source:
            return int(row[0])
        version = (int(row[0]) + 1) if row else 1
        self._dal.conn.execute(
            "INSERT INTO v2_actor_snapshots(actor_id,snapshot_version,display_name,identity_source,"
            "captured_at) VALUES(?,?,?,?,?)",
            (actor.actor_id, version, actor.display_name, actor.source, occurred_at),
        )
        return version

    def create_bundle(
        self,
        *,
        review: ReviewCycleRecord,
        candidate: WorkingCandidate,
        pointers: ReviewPointers,
        status_event: ReviewStatusEvent,
        disposition_event_id: str,
        request_key: str,
        request_hash: str,
        actor,
    ) -> None:
        if pointers.review_id != review.review_id or candidate.review_id != review.review_id:
            raise ValueError("Review creation bundle has inconsistent Review IDs.")
        self.save_actor_snapshot(actor, review.created_at)
        self._dal.conn.execute(
            "INSERT INTO cycles(cycle_id,month,year,state) VALUES(?,?,?,?)",
            (
                review.review_id,
                review.period.month_name,
                f"{review.period.year:04d}",
                "Created",
            ),
        )
        self._dal.conn.execute(
            "INSERT INTO v2_review_cycles(review_id,selected_month,selected_year,creation_actor_id,"
            "creation_actor_display,identity_source,created_at,origin) VALUES(?,?,?,?,?,?,?,?)",
            (
                review.review_id,
                review.period.month,
                review.period.year,
                review.created_by,
                actor.display_name,
                actor.source,
                review.created_at,
                review.origin,
            ),
        )
        self._dal.conn.execute(
            "INSERT INTO v2_working_candidates(candidate_id,review_id,predecessor_generation_id,"
            "creation_trigger,extractor_profile_id,creator_actor_id,created_at) VALUES(?,?,?,?,?,?,?)",
            (
                candidate.candidate_id,
                candidate.review_id,
                candidate.predecessor_generation_id,
                candidate.creation_trigger,
                candidate.extractor_profile_id,
                candidate.created_by,
                candidate.created_at,
            ),
        )
        self._dal.conn.execute(
            "INSERT INTO v2_review_cycle_pointers(review_id,active_candidate_id,working_generation_id,"
            "published_generation_id,current_rule_set_id,revision) VALUES(?,?,?,?,?,?)",
            (
                pointers.review_id,
                pointers.active_candidate_id,
                pointers.working_generation_id,
                pointers.published_generation_id,
                pointers.current_rule_set_id,
                pointers.revision,
            ),
        )
        self._dal.conn.execute(
            "INSERT INTO v2_review_disposition_events(event_id,review_id,sequence,disposition,actor_id,"
            "occurred_at,reason) VALUES(?,?,?,?,?,?,?)",
            (
                disposition_event_id,
                review.review_id,
                1,
                review.disposition.value,
                review.created_by,
                review.created_at,
                "NEW_REVIEW",
            ),
        )
        self.append_status(status_event, origin="NATIVE")
        self._dal.conn.execute(
            "INSERT INTO v2_review_create_requests(idempotency_key,review_id,request_hash,actor_id,"
            "created_at) VALUES(?,?,?,?,?)",
            (request_key, review.review_id, request_hash, review.created_by, review.created_at),
        )

    def append_status(self, event: ReviewStatusEvent, *, origin: str = "NATIVE") -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_review_status_events(event_id,review_id,owner_kind,owner_id,sequence,"
            "previous_status,status,actor_id,occurred_at,reason,origin) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                event.event_id,
                event.review_id,
                event.owner_kind.value,
                event.owner_id,
                event.sequence,
                event.previous_status.value if event.previous_status else None,
                event.status.value,
                event.actor_id,
                event.occurred_at,
                event.reason,
                origin,
            ),
        )

    def create_request(self, key: str):
        row = self._dal.conn.execute(
            "SELECT review_id,request_hash,actor_id,created_at FROM v2_review_create_requests "
            "WHERE idempotency_key=?",
            (key,),
        ).fetchone()
        if not row:
            return None
        return {
            "review_id": row[0],
            "request_hash": row[1],
            "actor_id": row[2],
            "created_at": row[3],
        }

    def count(self, *, include_archived: bool = True) -> int:
        if include_archived:
            return int(self._dal.conn.execute("SELECT COUNT(*) FROM v2_review_cycles").fetchone()[0])
        return len(self.list(statuses=tuple(s for s in ReviewStatus if s != ReviewStatus.ARCHIVED)))

    def count_for_period(self, month: int, year: int) -> int:
        return int(
            self._dal.conn.execute(
                "SELECT COUNT(*) FROM v2_review_cycles WHERE selected_month=? AND selected_year=?",
                (month, year),
            ).fetchone()[0]
        )

    def get(self, review_id: str) -> Optional[ManagedReview]:
        rows = self._query("WHERE r.review_id=?", (review_id,))
        return rows[0] if rows else None

    def list(
        self,
        *,
        statuses: Optional[Sequence[ReviewStatus]] = None,
        include_archived: bool = False,
    ) -> list[ManagedReview]:
        if statuses is None and not include_archived:
            statuses = tuple(status for status in ReviewStatus if status != ReviewStatus.ARCHIVED)
        if statuses is None:
            return self._query("", ())
        normalized = tuple(ReviewStatus(status).value for status in statuses)
        if not normalized:
            return []
        placeholders = ",".join("?" for _ in normalized)
        return self._query(f"WHERE s.status IN ({placeholders})", normalized)

    def _query(self, where: str, parameters: Sequence[object]) -> list[ManagedReview]:
        rows = self._dal.conn.execute(
            "SELECT r.review_id,r.selected_month,r.selected_year,r.creation_actor_id,r.created_at,r.origin,"
            "p.active_candidate_id,p.working_generation_id,p.published_generation_id,p.revision,"
            "s.owner_kind,s.owner_id,s.status,"
            "COALESCE((SELECT d.disposition FROM v2_review_disposition_events d "
            "WHERE d.review_id=r.review_id ORDER BY d.sequence DESC LIMIT 1),'Active') "
            "FROM v2_review_cycles r JOIN v2_review_cycle_pointers p ON p.review_id=r.review_id "
            "JOIN v2_review_status_events s ON s.rowid=("
            "SELECT s2.rowid FROM v2_review_status_events s2 WHERE s2.review_id=r.review_id "
            "ORDER BY s2.rowid DESC LIMIT 1) "
            f"{where} ORDER BY r.selected_year DESC,r.selected_month DESC,r.created_at DESC,r.review_id",
            tuple(parameters),
        ).fetchall()
        result = []
        for row in rows:
            review = ReviewCycleRecord(
                review_id=row[0],
                period=ReportingPeriod(int(row[2]), int(row[1])),
                created_by=row[3],
                created_at=row[4],
                disposition=ReviewDisposition(row[13]),
                origin=row[5],
            )
            result.append(
                ManagedReview(
                    review=review,
                    status=ReviewStatus(row[12]),
                    status_owner_kind=StatusOwnerKind(row[10]),
                    status_owner_id=row[11],
                    candidate_id=row[6],
                    working_generation_id=row[7],
                    published_generation_id=row[8],
                    pointer_revision=int(row[9]),
                )
            )
        return result

    def status_history(self, review_id: str) -> list[dict]:
        rows = self._dal.conn.execute(
            "SELECT event_id,owner_kind,owner_id,sequence,previous_status,status,actor_id,occurred_at,"
            "reason,origin FROM v2_review_status_events WHERE review_id=? ORDER BY rowid",
            (review_id,),
        ).fetchall()
        keys = (
            "event_id",
            "owner_kind",
            "owner_id",
            "sequence",
            "previous_status",
            "status",
            "actor_id",
            "occurred_at",
            "reason",
            "origin",
        )
        return [dict(zip(keys, row)) for row in rows]

    def next_status_sequence(self, owner_kind: StatusOwnerKind, owner_id: str) -> int:
        row = self._dal.conn.execute(
            "SELECT COALESCE(MAX(sequence),0)+1 FROM v2_review_status_events "
            "WHERE owner_kind=? AND owner_id=?",
            (owner_kind.value, owner_id),
        ).fetchone()
        return int(row[0])

    def append_authorization_decision(
        self,
        *,
        event_id: str,
        actor_id: str,
        permission: str,
        resource_type: Optional[str],
        resource_id: Optional[str],
        decision: str,
        policy_version: str,
        manifest_version: Optional[int],
        authorization_source_kind: str,
        authorization_fingerprint: str,
        authorization_key_id: Optional[str],
        effective_assignment_ids: Sequence[str],
        effective_roles: Sequence[str],
        denied_roles: Sequence[str],
        reason_code: str,
        correlation_id: str,
        occurred_at: str,
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_authorization_decision_events(event_id,actor_id,permission,resource_type,"
            "resource_id,decision,policy_version,manifest_version,reason_code,correlation_id,occurred_at,"
            "authorization_source_kind,authorization_fingerprint,authorization_key_id,"
            "effective_assignment_ids,effective_roles,denied_roles) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                event_id,
                actor_id,
                permission,
                resource_type,
                resource_id,
                decision,
                policy_version,
                manifest_version,
                reason_code,
                correlation_id,
                occurred_at,
                authorization_source_kind,
                authorization_fingerprint,
                authorization_key_id,
                _canonical_list(effective_assignment_ids),
                _canonical_list(effective_roles),
                _canonical_list(denied_roles),
            ),
        )

    def next_disposition_sequence(self, review_id: str) -> int:
        row = self._dal.conn.execute(
            "SELECT COALESCE(MAX(sequence),0)+1 FROM v2_review_disposition_events WHERE review_id=?",
            (review_id,),
        ).fetchone()
        return int(row[0])

    def append_disposition(
        self,
        *,
        event_id: str,
        review_id: str,
        disposition: ReviewDisposition,
        actor_id: str,
        occurred_at: str,
        reason: str,
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_review_disposition_events(event_id,review_id,sequence,disposition,actor_id,"
            "occurred_at,reason) VALUES(?,?,?,?,?,?,?)",
            (
                event_id,
                review_id,
                self.next_disposition_sequence(review_id),
                disposition.value,
                actor_id,
                occurred_at,
                reason,
            ),
        )

    def append_diagnostic_event(
        self,
        *,
        diagnostic_event_id: str,
        correlation_id: str,
        code: str,
        category: str,
        user_safe_cause: str,
        user_safe_impact: str,
        permitted_remedies: Sequence[str],
        retryability: str,
        mutation_outcome: str,
        actor_id: Optional[str],
        component: str,
        occurred_at: str,
        taxonomy_version: str,
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_diagnostic_events("
            "diagnostic_event_id,correlation_id,code,category,user_safe_cause,"
            "user_safe_impact,permitted_remedies_json,retryability,mutation_outcome,"
            "actor_id,component,occurred_at,taxonomy_version,metadata_json"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'{}')",
            (
                diagnostic_event_id,
                correlation_id,
                code,
                category,
                user_safe_cause,
                user_safe_impact,
                json.dumps(
                    list(permitted_remedies),
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                retryability,
                mutation_outcome,
                actor_id,
                component,
                occurred_at,
                taxonomy_version,
            ),
        )

    def diagnostic_events(self, correlation_id: str) -> list[dict]:
        rows = self._dal.conn.execute(
            "SELECT diagnostic_event_id,correlation_id,code,category,user_safe_cause,"
            "user_safe_impact,permitted_remedies_json,retryability,mutation_outcome,"
            "actor_id,component,occurred_at,taxonomy_version "
            "FROM v2_diagnostic_events WHERE correlation_id=? ORDER BY occurred_at,"
            "diagnostic_event_id",
            (correlation_id,),
        ).fetchall()
        keys = (
            "diagnostic_event_id",
            "correlation_id",
            "code",
            "category",
            "user_safe_cause",
            "user_safe_impact",
            "permitted_remedies",
            "retryability",
            "mutation_outcome",
            "actor_id",
            "component",
            "occurred_at",
            "taxonomy_version",
        )
        result = []
        for row in rows:
            values = list(row)
            values[6] = json.loads(values[6])
            result.append(dict(zip(keys, values)))
        return result

    def storage_inventory(self, review_id: str) -> dict[str, int]:
        """Evidence that Workflow 1 creates no Workflow 2+ financial records."""

        tables = {
            "source_bindings": "source_bindings",
            "review_generations": "review_generations",
            "rule_runs": "rule_runs",
            "findings": "findings",
            "ingested_files": "ingested_files",
            "export_artifacts": "export_artifacts",
        }
        result = {}
        for label, table in tables.items():
            column = "cycle_id"
            result[label] = int(
                self._dal.conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE {column}=?", (review_id,)
                ).fetchone()[0]
            )
        result["v2_source_binding_versions"] = int(
            self._dal.conn.execute(
                "SELECT COUNT(*) FROM v2_source_binding_versions WHERE review_id=?",
                (review_id,),
            ).fetchone()[0]
        )
        result["v2_source_intake_summaries"] = int(
            self._dal.conn.execute(
                "SELECT COUNT(*) FROM v2_source_intake_summaries WHERE review_id=?",
                (review_id,),
            ).fetchone()[0]
        )
        return result

    def review_disposal_inventory(self, review_id: str) -> dict[str, int]:
        """Return the exact current database closure for a confirmation preview."""

        return self._review_disposal.inventory(review_id)

    def dispose_review(
        self,
        *,
        review_id: str,
        operation_id: str,
        tombstone_id: str,
        confirmation_fingerprint: str,
        actor_id: str,
        disposed_at: str,
        reason_code: str,
    ) -> dict:
        """Remove one authorized review scope inside the caller's transaction."""

        return self._review_disposal.dispose(
            review_id=review_id,
            operation_id=operation_id,
            tombstone_id=tombstone_id,
            confirmation_fingerprint=confirmation_fingerprint,
            actor_id=actor_id,
            disposed_at=disposed_at,
            reason_code=reason_code,
        )

    def review_disposal_tombstone(self, scope_token: str):
        return self._review_disposal.tombstone(scope_token)


def _canonical_list(values) -> str:
    return json.dumps(
        sorted(values),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _format_time(value) -> str:
    return value.isoformat().replace("+00:00", "Z")


class SqliteManifestVersionStore:
    """Protected manifest rollback high-watermark inside the encrypted store."""

    def __init__(self, dal, clock):
        self._dal = dal
        self._clock = clock

    def current(self) -> Optional[ManifestVersionRecord]:
        row = self._dal.conn.execute(
            "SELECT manifest_version,manifest_hash,key_id FROM v2_authorization_manifest_state "
            "WHERE singleton=1"
        ).fetchone()
        return ManifestVersionRecord(int(row[0]), row[1], row[2]) if row else None

    def record(self, value: ManifestVersionRecord) -> None:
        current = self.current()
        if current is None:
            self._dal.conn.execute(
                "INSERT INTO v2_authorization_manifest_state(singleton,manifest_version,manifest_hash,"
                "key_id,accepted_at) VALUES(1,?,?,?,?)",
                (value.version, value.fingerprint, value.key_id, self._clock.now()),
            )
            return
        if value.version < current.version or (
            value.version == current.version and value.fingerprint != current.fingerprint
        ):
            raise ValueError("Authorization manifest rollback or equivocation detected.")
        if value == current:
            return
        self._dal.conn.execute(
            "UPDATE v2_authorization_manifest_state SET manifest_version=?,manifest_hash=?,key_id=?,"
            "accepted_at=? WHERE singleton=1 AND manifest_version=? AND manifest_hash=?",
            (
                value.version,
                value.fingerprint,
                value.key_id,
                self._clock.now(),
                current.version,
                current.fingerprint,
            ),
        )
