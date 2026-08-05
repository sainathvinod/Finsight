"""SQLite adapter for V2 review corrections and sealed validation ledgers."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from finsight.domain.finding_explanations import (
    FindingReviewStatus,
    build_leadership_summary,
    legacy_explanation,
)
from finsight.domain.financial_validation import (
    CORE_RULE_SET_ID,
    RuleDefinitionVersion,
    RuleSetManifest,
    ValidationEvaluation,
)

_CORE_RULE_IDS = frozenset(
    {"CORE-01", "CORE-02", "CORE-03", "CORE-04", "CORE-05"}
)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


class FinancialReviewRepositorySqlite:
    def __init__(self, dal):
        self._dal = dal

    def current_rule_set_id(self, review_id: str) -> str | None:
        row = self._dal.conn.execute(
            "SELECT current_rule_set_id FROM v2_review_cycle_pointers "
            "WHERE review_id=?",
            (review_id,),
        ).fetchone()
        return row[0] if row and row[0] else None

    def current_protected_baseline_id(self) -> str:
        """Return the latest governed global baseline without rebinding workspaces."""

        row = self._dal.conn.execute(
            "SELECT resulting_baseline_id FROM v2_protected_change_activations "
            "ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        return str(row[0]) if row else CORE_RULE_SET_ID

    def rule_set_manifest(self, rule_set_id: str) -> RuleSetManifest | None:
        workspace_set = self._dal.conn.execute(
            "SELECT version,protected_baseline_id FROM v2_rule_set_versions "
            "WHERE rule_set_id=?",
            (rule_set_id,),
        ).fetchone()
        if workspace_set is not None:
            rows = self._dal.conn.execute(
                "SELECT m.ordinal,r.rule_id,r.name,r.version,r.severity,"
                "r.baseline_status,r.evaluator_key,r.classification,r.purpose,"
                "r.required_fields_json,r.grouping_keys_json,r.parameters_json "
                "FROM v2_rule_set_members m "
                "JOIN v2_rule_definition_versions r "
                "ON r.rule_id=m.rule_id AND r.version=m.rule_version "
                "WHERE m.rule_set_id=? AND m.enabled=1 ORDER BY m.ordinal",
                (rule_set_id,),
            ).fetchall()
            return RuleSetManifest(
                rule_set_id,
                str(workspace_set[0]),
                tuple(
                    RuleDefinitionVersion(
                        rule_id=row[1],
                        name=row[2],
                        version=row[3],
                        severity=row[4],
                        baseline_status=row[5],
                        evaluator_key=row[6],
                        ordinal=int(row[0]),
                        classification=row[7],
                        purpose=row[8],
                        required_fields=tuple(json.loads(row[9])),
                        grouping_keys=tuple(json.loads(row[10])),
                        parameters=json.loads(row[11]),
                    )
                    for row in rows
                ),
                workspace_set[1],
            )
        rule_set = self._dal.conn.execute(
            "SELECT version FROM v2_core_rule_set_versions WHERE rule_set_id=?",
            (rule_set_id,),
        ).fetchone()
        if rule_set is None:
            return None
        rows = self._dal.conn.execute(
            "SELECT m.ordinal,r.rule_id,r.name,r.version,r.severity,"
            "r.baseline_status,r.evaluator_key "
            "FROM v2_core_rule_set_members m "
            "JOIN v2_core_rule_versions r "
            "ON r.rule_id=m.rule_id AND r.version=m.rule_version "
            "WHERE m.rule_set_id=? ORDER BY m.ordinal",
            (rule_set_id,),
        ).fetchall()
        return RuleSetManifest(
            rule_set_id,
            rule_set[0],
            tuple(
                RuleDefinitionVersion(
                    rule_id=row[1],
                    name=row[2],
                    version=row[3],
                    severity=row[4],
                    baseline_status=row[5],
                    evaluator_key=row[6],
                    ordinal=int(row[0]),
                )
                for row in rows
            ),
            rule_set_id,
        )

    def ensure_initial_rule_set(
        self,
        review_id: str,
        *,
        actor_id: str,
        created_at: str,
    ) -> str:
        current = self.current_rule_set_id(review_id)
        if current and self._dal.conn.execute(
            "SELECT 1 FROM v2_rule_set_versions WHERE rule_set_id=?",
            (current,),
        ).fetchone():
            return current
        rule_set_id = f"ruleset_{review_id}_1"
        protected_baseline_id = self.current_protected_baseline_id()
        definitions = self._dal.conn.execute(
            "SELECT m.ordinal,m.rule_id,m.rule_version "
            "FROM v2_core_rule_set_members m WHERE m.rule_set_id=? ORDER BY m.ordinal",
            (protected_baseline_id,),
        ).fetchall()
        payload = {
            "review_id": review_id,
            "version": 1,
            "protected_baseline_id": protected_baseline_id,
            "members": [
                [int(row[0]), row[1], row[2], True] for row in definitions
            ],
        }
        self._dal.conn.execute(
            "INSERT OR IGNORE INTO v2_rule_set_versions("
            "rule_set_id,review_id,version,predecessor_rule_set_id,"
            "protected_baseline_id,content_hash,created_by,created_at,reason"
            ") VALUES(?,?,1,NULL,?,?,?,?,?)",
            (
                rule_set_id,
                review_id,
                protected_baseline_id,
                _digest(payload),
                actor_id,
                created_at,
                "INITIAL_PROTECTED_BASELINE",
            ),
        )
        for ordinal, rule_id, rule_version in definitions:
            self._dal.conn.execute(
                "INSERT OR IGNORE INTO v2_rule_set_members("
                "rule_set_id,ordinal,rule_id,rule_version,enabled) VALUES(?,?,?,?,1)",
                (rule_set_id, int(ordinal), rule_id, rule_version),
            )
        return rule_set_id

    def create_successor_rule_set(
        self,
        review_id: str,
        *,
        members: list[dict[str, Any]],
        actor_id: str,
        created_at: str,
        reason: str,
    ) -> str:
        predecessor = self.current_rule_set_id(review_id)
        if not predecessor:
            predecessor = self.ensure_initial_rule_set(
                review_id, actor_id=actor_id, created_at=created_at
            )
        previous = self._dal.conn.execute(
            "SELECT version,protected_baseline_id FROM v2_rule_set_versions "
            "WHERE rule_set_id=? AND review_id=?",
            (predecessor, review_id),
        ).fetchone()
        if previous is None:
            raise ValueError("The current workspace Rule Set is unavailable.")
        version = int(previous[0]) + 1
        rule_set_id = f"ruleset_{review_id}_{version}"
        ordered = sorted(members, key=lambda item: int(item["ordinal"]))
        payload = {
            "review_id": review_id,
            "version": version,
            "predecessor": predecessor,
            "protected_baseline_id": previous[1],
            "members": ordered,
        }
        self._dal.conn.execute(
            "INSERT INTO v2_rule_set_versions("
            "rule_set_id,review_id,version,predecessor_rule_set_id,"
            "protected_baseline_id,content_hash,created_by,created_at,reason"
            ") VALUES(?,?,?,?,?,?,?,?,?)",
            (
                rule_set_id,
                review_id,
                version,
                predecessor,
                previous[1],
                _digest(payload),
                actor_id,
                created_at,
                reason,
            ),
        )
        for item in ordered:
            self._dal.conn.execute(
                "INSERT INTO v2_rule_set_members("
                "rule_set_id,ordinal,rule_id,rule_version,enabled) VALUES(?,?,?,?,?)",
                (
                    rule_set_id,
                    int(item["ordinal"]),
                    item["rule_id"],
                    item["rule_version"],
                    int(bool(item["enabled"])),
                ),
            )
        self._dal.conn.execute(
            "UPDATE v2_review_cycle_pointers SET current_rule_set_id=?,revision=revision+1 "
            "WHERE review_id=?",
            (rule_set_id, review_id),
        )
        return rule_set_id

    def rule_set_members(self, rule_set_id: str) -> list[dict[str, Any]]:
        rows = self._dal.conn.execute(
            "SELECT ordinal,rule_id,rule_version,enabled FROM v2_rule_set_members "
            "WHERE rule_set_id=? ORDER BY ordinal",
            (rule_set_id,),
        ).fetchall()
        return [
            {
                "ordinal": int(row[0]),
                "rule_id": row[1],
                "rule_version": row[2],
                "enabled": bool(row[3]),
            }
            for row in rows
        ]

    def rule_set_history(self, review_id: str) -> list[dict[str, Any]]:
        rows = self._dal.conn.execute(
            "SELECT rule_set_id,version,predecessor_rule_set_id,"
            "protected_baseline_id,content_hash,created_by,created_at,reason "
            "FROM v2_rule_set_versions WHERE review_id=? ORDER BY version",
            (review_id,),
        ).fetchall()
        keys = (
            "rule_set_id",
            "version",
            "predecessor_rule_set_id",
            "protected_baseline_id",
            "content_hash",
            "created_by",
            "created_at",
            "reason",
        )
        return [
            {**dict(zip(keys, row)), "members": self.rule_set_members(row[0])}
            for row in rows
        ]

    def append_rule_version(self, value: Mapping[str, Any]) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_rule_definition_versions("
            "rule_id,version,classification,name,purpose,severity,baseline_status,"
            "evaluator_key,parameters_json,required_fields_json,grouping_keys_json,"
            "predecessor_version,created_by,created_at,content_hash"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                value["rule_id"],
                value["version"],
                value["classification"],
                value["name"],
                value["purpose"],
                value["severity"],
                value["baseline_status"],
                value["evaluator_key"],
                _json(value["parameters"]),
                _json(list(value["required_fields"])),
                _json(list(value["grouping_keys"])),
                value.get("predecessor_version"),
                value["created_by"],
                value["created_at"],
                value["content_hash"],
            ),
        )

    def append_rule_lifecycle(self, value: Mapping[str, Any]) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_rule_lifecycle_events("
            "event_id,rule_id,rule_version,ordinal,status,actor_id,occurred_at,reason,event_hash"
            ") VALUES(?,?,?,?,?,?,?,?,?)",
            (
                value["event_id"],
                value["rule_id"],
                value["rule_version"],
                int(value["ordinal"]),
                value["status"],
                value["actor_id"],
                value["occurred_at"],
                value["reason"],
                value["event_hash"],
            ),
        )

    def next_rule_lifecycle_ordinal(self, rule_id: str, version: str) -> int:
        row = self._dal.conn.execute(
            "SELECT COALESCE(MAX(ordinal),0)+1 FROM v2_rule_lifecycle_events "
            "WHERE rule_id=? AND rule_version=?",
            (rule_id, version),
        ).fetchone()
        return int(row[0])

    def rule_version(
        self, rule_id: str, version: str
    ) -> dict[str, Any] | None:
        row = self._dal.conn.execute(
            "SELECT rule_id,version,classification,name,purpose,severity,"
            "baseline_status,evaluator_key,parameters_json,required_fields_json,"
            "grouping_keys_json,predecessor_version,created_by,created_at,content_hash "
            "FROM v2_rule_definition_versions WHERE rule_id=? AND version=?",
            (rule_id, version),
        ).fetchone()
        if row is None:
            return None
        keys = (
            "rule_id",
            "version",
            "classification",
            "name",
            "purpose",
            "severity",
            "baseline_status",
            "evaluator_key",
            "parameters",
            "required_fields",
            "grouping_keys",
            "predecessor_version",
            "created_by",
            "created_at",
            "content_hash",
        )
        value = dict(zip(keys, row))
        for key in ("parameters", "required_fields", "grouping_keys"):
            value[key] = json.loads(value[key])
        lifecycle = self._dal.conn.execute(
            "SELECT status,reason FROM v2_rule_lifecycle_events "
            "WHERE rule_id=? AND rule_version=? ORDER BY ordinal DESC LIMIT 1",
            (rule_id, version),
        ).fetchone()
        value["lifecycle_status"] = lifecycle[0] if lifecycle else None
        value["lifecycle_reason"] = lifecycle[1] if lifecycle else None
        value["display_lifecycle_status"] = (
            "SUPERSEDED"
            if lifecycle
            and lifecycle[0] == "RETIRED"
            and str(lifecycle[1]).startswith("SUPERSEDED_BY_")
            else value["lifecycle_status"]
        )
        return value

    def latest_rule_version(self, rule_id: str) -> dict[str, Any] | None:
        rows = self._dal.conn.execute(
            "SELECT version FROM v2_rule_definition_versions WHERE rule_id=? ORDER BY rowid DESC",
            (rule_id,),
        ).fetchall()
        return self.rule_version(rule_id, rows[0][0]) if rows else None

    def rule_version_history(self, rule_id: str) -> list[dict[str, Any]]:
        """Return every immutable definition version in creation order."""

        rows = self._dal.conn.execute(
            "SELECT version FROM v2_rule_definition_versions "
            "WHERE rule_id=? ORDER BY rowid",
            (rule_id,),
        ).fetchall()
        return [
            value
            for (version,) in rows
            if (value := self.rule_version(rule_id, version)) is not None
        ]

    def latest_optional_rule_versions(self) -> list[dict[str, Any]]:
        """Return the latest immutable version for every optional rule."""

        rows = self._dal.conn.execute(
            "SELECT rule_id,version FROM v2_rule_definition_versions d "
            "WHERE classification='OPTIONAL_CONFIGURABLE' AND rowid=("
            "SELECT MAX(newer.rowid) FROM v2_rule_definition_versions newer "
            "WHERE newer.rule_id=d.rule_id"
            ") ORDER BY created_at,rule_id"
        ).fetchall()
        return [
            value
            for rule_id, version in rows
            if (value := self.rule_version(rule_id, version)) is not None
        ]

    def append_rule_proposal_draft_event(
        self, value: Mapping[str, Any]
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_rule_proposal_draft_events("
            "event_id,review_id,rule_id,rule_version,action,actor_id,"
            "occurred_at,reason,event_hash) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                value["event_id"],
                value["review_id"],
                value["rule_id"],
                value["rule_version"],
                value["action"],
                value["actor_id"],
                value["occurred_at"],
                value["reason"],
                value["event_hash"],
            ),
        )

    def current_rule_proposal_draft_exclusions(
        self, review_id: str
    ) -> list[dict[str, Any]]:
        rows = self._dal.conn.execute(
            "SELECT e.rule_id,e.rule_version,e.action,e.actor_id,e.occurred_at,"
            "e.reason FROM v2_rule_proposal_draft_events e WHERE e.review_id=? "
            "AND e.rowid=(SELECT MAX(newer.rowid) "
            "FROM v2_rule_proposal_draft_events newer "
            "WHERE newer.review_id=e.review_id AND newer.rule_id=e.rule_id "
            "AND newer.rule_version=e.rule_version) "
            "ORDER BY e.occurred_at,e.rule_id,e.rule_version",
            (review_id,),
        ).fetchall()
        keys = (
            "rule_id",
            "rule_version",
            "action",
            "actor_id",
            "occurred_at",
            "reason",
        )
        return [
            dict(zip(keys, row))
            for row in rows
            if row[2] == "EXCLUDED"
        ]

    def current_protected_rule(self, rule_id: str) -> dict[str, Any] | None:
        baseline_id = self.current_protected_baseline_id()
        row = self._dal.conn.execute(
            "SELECT rule_version FROM v2_core_rule_set_members "
            "WHERE rule_set_id=? AND rule_id=?",
            (baseline_id, rule_id),
        ).fetchone()
        return self.rule_version(rule_id, row[0]) if row else None

    def protected_baseline_members(
        self, baseline_id: str | None = None
    ) -> list[dict[str, Any]]:
        selected = baseline_id or self.current_protected_baseline_id()
        rows = self._dal.conn.execute(
            "SELECT ordinal,rule_id,rule_version FROM v2_core_rule_set_members "
            "WHERE rule_set_id=? ORDER BY ordinal",
            (selected,),
        ).fetchall()
        return [
            {
                "ordinal": int(row[0]),
                "rule_id": str(row[1]),
                "rule_version": str(row[2]),
                "enabled": True,
            }
            for row in rows
        ]

    def protected_baseline_projection(
        self, baseline_id: str | None = None
    ) -> dict[str, Any] | None:
        selected = baseline_id or self.current_protected_baseline_id()
        row = self._dal.conn.execute(
            "SELECT version,created_at FROM v2_core_rule_set_versions "
            "WHERE rule_set_id=? AND status='PROTECTED_BASELINE'",
            (selected,),
        ).fetchone()
        if row is None:
            return None
        members = self.protected_baseline_members(selected)
        effective = self._dal.conn.execute(
            "SELECT activated_at FROM v2_protected_change_activations "
            "WHERE resulting_baseline_id=?",
            (selected,),
        ).fetchone()
        payload = {
            "baseline_id": selected,
            "version": str(row[0]),
            "members": members,
        }
        return {
            **payload,
            "baseline_hash": _digest(payload),
            "effective_at": str(effective[0]) if effective else str(row[1]),
        }

    def list_workspace_upgrade_candidates(self) -> list[dict[str, Any]]:
        """Return governance-safe workspace metadata without financial/source data."""

        target = self.protected_baseline_projection()
        if target is None:
            return []
        rows = self._dal.conn.execute(
            "SELECT p.review_id,p.current_rule_set_id,s.version,s.content_hash,"
            "s.protected_baseline_id "
            "FROM v2_review_cycle_pointers p "
            "JOIN v2_rule_set_versions s "
            "ON s.rule_set_id=p.current_rule_set_id "
            "ORDER BY p.review_id"
        ).fetchall()
        candidates: list[dict[str, Any]] = []
        for review_id, rule_set_id, version, content_hash, source_id in rows:
            latest = self.latest_run(str(review_id))
            published = self._dal.conn.execute(
                "SELECT published_generation_id FROM v2_review_cycle_pointers "
                "WHERE review_id=?",
                (review_id,),
            ).fetchone()
            if source_id == target["baseline_id"]:
                state = "UP_TO_DATE"
                reason = "Workspace already uses the effective protected baseline."
            elif latest is None:
                state = "NOT_ELIGIBLE"
                reason = (
                    "A complete authoritative Validation Run is required before "
                    "an existing workspace can be upgraded."
                )
            elif (
                latest["rule_set_id"] != rule_set_id
                or not published
                or published[0] != latest["generation_id"]
            ):
                state = "NOT_ELIGIBLE"
                reason = (
                    "The latest complete Validation Run is not authoritative for "
                    "the current workspace Rule Set."
                )
            else:
                state = "UPGRADE_AVAILABLE"
                reason = (
                    "A newer effective protected baseline is available for "
                    "governed workspace adoption."
                )
            source = self.protected_baseline_projection(str(source_id))
            candidates.append(
                {
                    "review_id": str(review_id),
                    "current_rule_set_id": str(rule_set_id),
                    "current_rule_set_version": int(version),
                    "current_rule_set_content_hash": str(content_hash),
                    "source_baseline_id": str(source_id),
                    "source_baseline_version": (
                        source["version"] if source is not None else None
                    ),
                    "source_baseline_hash": (
                        source["baseline_hash"] if source is not None else None
                    ),
                    "latest_run_id": (
                        str(latest["run_id"]) if latest is not None else None
                    ),
                    "latest_generation_id": (
                        str(latest["generation_id"])
                        if latest is not None
                        else None
                    ),
                    "target_baseline_id": target["baseline_id"],
                    "target_baseline_version": target["version"],
                    "target_baseline_hash": target["baseline_hash"],
                    "target_effective_at": target["effective_at"],
                    "upgrade_available": state == "UPGRADE_AVAILABLE",
                    "upgrade_state": state,
                    "upgrade_reason": reason,
                }
            )
        return candidates

    def workspace_upgrade_status(
        self, review_id: str
    ) -> dict[str, Any] | None:
        candidate = next(
            (
                value
                for value in self.list_workspace_upgrade_candidates()
                if value["review_id"] == review_id
            ),
            None,
        )
        if candidate is None:
            return None
        requests = self.list_workspace_upgrade_requests(review_id=review_id)
        latest_request = requests[0] if requests else None
        result = {
            **candidate,
            "current_baseline_id": candidate["source_baseline_id"],
            "current_global_baseline_id": candidate["target_baseline_id"],
            "latest_request": latest_request,
            "pending_request_id": None,
        }
        if latest_request is not None and latest_request["status"] == "PENDING_APPROVAL":
            result["state"] = latest_request["state"]
            result["pending_request_id"] = latest_request["request_id"]
        elif (
            latest_request is not None
            and latest_request["status"] == "APPLIED"
            and latest_request["target_baseline_id"]
            == candidate["source_baseline_id"]
        ):
            latest = self.latest_run(review_id)
            if (
                latest is not None
                and latest["rule_set_id"] == candidate["current_rule_set_id"]
            ):
                result["state"] = "VALIDATED"
            else:
                result["state"] = "APPLIED_REVALIDATION_REQUIRED"
        else:
            result["state"] = candidate["upgrade_state"]
        result["workspace_upgrade_state"] = result["state"]
        return result

    def append_workspace_upgrade_request(
        self, value: Mapping[str, Any]
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_workspace_baseline_upgrade_requests("
            "request_id,request_type,review_id,requested_rule_set_id,"
            "requested_rule_set_content_hash,source_baseline_id,"
            "target_baseline_id,target_baseline_hash,requested_run_id,"
            "requested_generation_id,requester_actor_id,requested_at,reason,"
            "initial_status,request_hash"
            ") VALUES(?,'WORKSPACE_BASELINE_UPGRADE',?,?,?,?,?,?,?,?,?,?,?,"
            "'PENDING_APPROVAL',?)",
            (
                value["request_id"],
                value["review_id"],
                value["requested_rule_set_id"],
                value["requested_rule_set_content_hash"],
                value["source_baseline_id"],
                value["target_baseline_id"],
                value["target_baseline_hash"],
                value["requested_run_id"],
                value["requested_generation_id"],
                value["requester_actor_id"],
                value["requested_at"],
                value["reason"],
                value["request_hash"],
            ),
        )

    def workspace_upgrade_request(
        self, request_id: str
    ) -> dict[str, Any] | None:
        rows = self._workspace_upgrade_request_rows(
            "WHERE r.request_id=?", (request_id,)
        )
        return rows[0] if rows else None

    def list_workspace_upgrade_requests(
        self, *, review_id: str | None = None
    ) -> list[dict[str, Any]]:
        if review_id is None:
            return self._workspace_upgrade_request_rows(
                "ORDER BY r.requested_at DESC,r.request_id DESC", ()
            )
        return self._workspace_upgrade_request_rows(
            "WHERE r.review_id=? "
            "ORDER BY r.requested_at DESC,r.request_id DESC",
            (review_id,),
        )

    def _workspace_upgrade_request_rows(
        self, suffix: str, parameters: tuple[Any, ...]
    ) -> list[dict[str, Any]]:
        rows = self._dal.conn.execute(
            "SELECT r.request_id,r.request_type,r.review_id,"
            "r.requested_rule_set_id,r.requested_rule_set_content_hash,"
            "r.source_baseline_id,r.target_baseline_id,"
            "r.target_baseline_hash,r.requested_run_id,"
            "r.requested_generation_id,r.requester_actor_id,r.requested_at,"
            "r.reason,r.initial_status,r.request_hash,"
            "d.decision,d.approver_actor_id,d.decided_at,d.reason,"
            "a.resulting_rule_set_id,a.applied_at,a.application_hash "
            "FROM v2_workspace_baseline_upgrade_requests r "
            "LEFT JOIN v2_workspace_baseline_upgrade_decisions d "
            "ON d.request_id=r.request_id "
            "LEFT JOIN v2_workspace_baseline_upgrade_applications a "
            "ON a.request_id=r.request_id "
            + suffix,
            parameters,
        ).fetchall()
        keys = (
            "request_id",
            "request_type",
            "review_id",
            "requested_rule_set_id",
            "requested_rule_set_content_hash",
            "source_baseline_id",
            "target_baseline_id",
            "target_baseline_hash",
            "requested_run_id",
            "requested_generation_id",
            "requester_actor_id",
            "requested_at",
            "reason",
            "initial_status",
            "request_hash",
            "decision",
            "approver_actor_id",
            "decided_at",
            "decision_reason",
            "resulting_rule_set_id",
            "applied_at",
            "application_hash",
        )
        output = []
        for row in rows:
            value = dict(zip(keys, row))
            source = self.protected_baseline_projection(
                str(value["source_baseline_id"])
            )
            target = self.protected_baseline_projection(
                str(value["target_baseline_id"])
            )
            requested_set = self._dal.conn.execute(
                "SELECT version,content_hash FROM v2_rule_set_versions "
                "WHERE rule_set_id=?",
                (value["requested_rule_set_id"],),
            ).fetchone()
            resulting_set = (
                self._dal.conn.execute(
                    "SELECT version,content_hash FROM v2_rule_set_versions "
                    "WHERE rule_set_id=?",
                    (value["resulting_rule_set_id"],),
                ).fetchone()
                if value["resulting_rule_set_id"]
                else None
            )
            source_versions = {
                item["rule_id"]: item["rule_version"]
                for item in (source["members"] if source else [])
            }
            target_versions = {
                item["rule_id"]: item["rule_version"]
                for item in (target["members"] if target else [])
            }
            protected_rule_ids = sorted(
                set(source_versions) | set(target_versions)
            )
            source_rule_evidence = []
            target_rule_evidence = []
            for rule_id in protected_rule_ids:
                for version, evidence in (
                    (
                        source_versions.get(rule_id),
                        source_rule_evidence,
                    ),
                    (
                        target_versions.get(rule_id),
                        target_rule_evidence,
                    ),
                ):
                    definition = (
                        self.rule_version(rule_id, str(version))
                        if version is not None
                        else None
                    )
                    if definition is None:
                        continue
                    parameters = dict(definition["parameters"])
                    evidence.append(
                        {
                            "rule_id": rule_id,
                            "rule_version": str(version),
                            "definition_content_hash": definition[
                                "content_hash"
                            ],
                            "configuration": parameters,
                            "configuration_hash": _digest(parameters),
                        }
                    )
            optional_bindings = [
                item
                for item in self.rule_set_members(
                    str(value["requested_rule_set_id"])
                )
                if item["rule_id"] not in _CORE_RULE_IDS
            ]
            resulting_optional_bindings = (
                [
                    item
                    for item in self.rule_set_members(
                        str(value["resulting_rule_set_id"])
                    )
                    if item["rule_id"] not in _CORE_RULE_IDS
                ]
                if value["resulting_rule_set_id"]
                else None
            )
            value.update(
                {
                    "source_baseline_version": (
                        source["version"] if source else None
                    ),
                    "source_baseline_hash": (
                        source["baseline_hash"] if source else None
                    ),
                    "source_baseline_effective_at": (
                        source["effective_at"] if source else None
                    ),
                    "target_baseline_version": (
                        target["version"] if target else None
                    ),
                    "target_baseline_effective_at": (
                        target["effective_at"] if target else None
                    ),
                    "protected_rule_ids": protected_rule_ids,
                    "protected_member_changes": [
                        {
                            "rule_id": rule_id,
                            "source_rule_version": source_versions.get(
                                rule_id
                            ),
                            "target_rule_version": target_versions.get(
                                rule_id
                            ),
                            "changed": source_versions.get(rule_id)
                            != target_versions.get(rule_id),
                        }
                        for rule_id in protected_rule_ids
                    ],
                    "source_protected_rule_evidence": (
                        source_rule_evidence
                    ),
                    "target_protected_rule_evidence": (
                        target_rule_evidence
                    ),
                    "requested_rule_set_version": (
                        int(requested_set[0]) if requested_set else None
                    ),
                    "resulting_rule_set_version": (
                        int(resulting_set[0]) if resulting_set else None
                    ),
                    "resulting_rule_set_content_hash": (
                        str(resulting_set[1]) if resulting_set else None
                    ),
                    "preserved_optional_advisory_binding_count": len(
                        optional_bindings
                    ),
                    "preserved_optional_advisory_binding_hash": _digest(
                        optional_bindings
                    ),
                    "preserved_optional_advisory_rule_ids": [
                        item["rule_id"] for item in optional_bindings
                    ],
                    "resulting_optional_advisory_binding_hash": (
                        _digest(resulting_optional_bindings)
                        if resulting_optional_bindings is not None
                        else None
                    ),
                }
            )
            value["status"] = (
                "APPLIED"
                if value["resulting_rule_set_id"]
                else (value["decision"] or value["initial_status"])
            )
            current = self.current_rule_set_id(str(value["review_id"]))
            target = self.current_protected_baseline_id()
            latest = self.latest_run(str(value["review_id"]))
            stale_reasons = []
            if current != value["requested_rule_set_id"]:
                stale_reasons.append("WORKSPACE_RULE_SET_CHANGED")
            if target != value["target_baseline_id"]:
                stale_reasons.append("TARGET_BASELINE_CHANGED")
            if (
                latest is None
                or latest["run_id"] != value["requested_run_id"]
                or latest["generation_id"]
                != value["requested_generation_id"]
            ):
                stale_reasons.append("AUTHORITATIVE_RUN_CHANGED")
            pending = value["status"] == "PENDING_APPROVAL"
            value["binding_drift_reasons"] = tuple(stale_reasons)
            value["stale"] = pending and bool(stale_reasons)
            value["stale_reasons"] = (
                tuple(stale_reasons) if pending else ()
            )
            if pending:
                value["state"] = (
                    "STALE_PENDING"
                    if value["stale"]
                    else "PENDING_APPROVAL"
                )
            else:
                value["state"] = value["status"]
            output.append(value)
        return output

    def append_workspace_upgrade_decision(
        self, value: Mapping[str, Any]
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_workspace_baseline_upgrade_decisions("
            "request_id,decision,approver_actor_id,decided_at,reason,"
            "decision_hash) VALUES(?,?,?,?,?,?)",
            (
                value["request_id"],
                value["decision"],
                value["approver_actor_id"],
                value["decided_at"],
                value["reason"],
                value["decision_hash"],
            ),
        )

    def apply_workspace_baseline_upgrade(
        self,
        request: Mapping[str, Any],
        *,
        actor_id: str,
        applied_at: str,
    ) -> str:
        """Atomically create and bind one exact governed workspace successor."""

        review_id = str(request["review_id"])
        predecessor = str(request["requested_rule_set_id"])
        if self.current_rule_set_id(review_id) != predecessor:
            raise ValueError("The workspace Rule Set changed after this request.")
        if (
            self.current_protected_baseline_id()
            != request["target_baseline_id"]
        ):
            raise ValueError("The effective protected baseline changed after this request.")
        latest = self.latest_run(review_id)
        if (
            latest is None
            or latest["run_id"] != request["requested_run_id"]
            or latest["generation_id"] != request["requested_generation_id"]
            or latest["rule_set_id"] != predecessor
        ):
            raise ValueError("The authoritative Validation Run changed after this request.")
        previous = self._dal.conn.execute(
            "SELECT version,protected_baseline_id,content_hash "
            "FROM v2_rule_set_versions "
            "WHERE rule_set_id=? AND review_id=?",
            (predecessor, review_id),
        ).fetchone()
        if (
            previous is None
            or previous[1] != request["source_baseline_id"]
            or previous[2] != request["requested_rule_set_content_hash"]
        ):
            raise ValueError("The requested workspace Rule Set is unavailable.")
        target = self.protected_baseline_projection(
            str(request["target_baseline_id"])
        )
        if (
            target is None
            or target["baseline_hash"] != request["target_baseline_hash"]
            or len(target["members"]) != 5
            or {item["rule_id"] for item in target["members"]}
            != _CORE_RULE_IDS
        ):
            raise ValueError("The exact target protected baseline is unavailable.")
        prior_members = self.rule_set_members(predecessor)
        source_members = self.protected_baseline_members(
            str(request["source_baseline_id"])
        )
        prior_core = {
            (item["ordinal"], item["rule_id"], item["rule_version"])
            for item in prior_members
            if item["rule_id"] in _CORE_RULE_IDS and item["enabled"]
        }
        expected_source = {
            (item["ordinal"], item["rule_id"], item["rule_version"])
            for item in source_members
        }
        if prior_core != expected_source:
            raise ValueError("The source protected baseline binding is inconsistent.")
        optional_members = [
            dict(item)
            for item in prior_members
            if item["rule_id"] not in _CORE_RULE_IDS
        ]
        members = [dict(item) for item in target["members"]] + optional_members
        ordinals = [int(item["ordinal"]) for item in members]
        if len(ordinals) != len(set(ordinals)):
            raise ValueError("The target baseline conflicts with optional-rule ordering.")

        version = int(previous[0]) + 1
        rule_set_id = f"ruleset_{review_id}_{version}"
        ordered = sorted(members, key=lambda item: int(item["ordinal"]))
        payload = {
            "review_id": review_id,
            "version": version,
            "predecessor": predecessor,
            "protected_baseline_id": request["target_baseline_id"],
            "members": ordered,
        }
        self._dal.conn.execute(
            "INSERT INTO v2_rule_set_versions("
            "rule_set_id,review_id,version,predecessor_rule_set_id,"
            "protected_baseline_id,content_hash,created_by,created_at,reason"
            ") VALUES(?,?,?,?,?,?,?,?,?)",
            (
                rule_set_id,
                review_id,
                version,
                predecessor,
                request["target_baseline_id"],
                _digest(payload),
                actor_id,
                applied_at,
                f"PROTECTED_BASELINE_UPGRADE:{request['request_id']}",
            ),
        )
        for item in ordered:
            self._dal.conn.execute(
                "INSERT INTO v2_rule_set_members("
                "rule_set_id,ordinal,rule_id,rule_version,enabled"
                ") VALUES(?,?,?,?,?)",
                (
                    rule_set_id,
                    int(item["ordinal"]),
                    item["rule_id"],
                    item["rule_version"],
                    int(bool(item["enabled"])),
                ),
            )
        updated = self._dal.conn.execute(
            "UPDATE v2_review_cycle_pointers "
            "SET current_rule_set_id=?,revision=revision+1 "
            "WHERE review_id=? AND current_rule_set_id=?",
            (rule_set_id, review_id, predecessor),
        )
        if updated.rowcount != 1:
            raise ValueError("The workspace Rule Set changed during approval.")
        application = {
            "request_id": request["request_id"],
            "review_id": review_id,
            "prior_rule_set_id": predecessor,
            "resulting_rule_set_id": rule_set_id,
            "source_baseline_id": request["source_baseline_id"],
            "target_baseline_id": request["target_baseline_id"],
            "applied_by_actor_id": actor_id,
            "applied_at": applied_at,
        }
        application["application_hash"] = _digest(application)
        self._dal.conn.execute(
            "INSERT INTO v2_workspace_baseline_upgrade_applications("
            "request_id,review_id,prior_rule_set_id,resulting_rule_set_id,"
            "source_baseline_id,target_baseline_id,applied_by_actor_id,"
            "applied_at,application_hash) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                application["request_id"],
                application["review_id"],
                application["prior_rule_set_id"],
                application["resulting_rule_set_id"],
                application["source_baseline_id"],
                application["target_baseline_id"],
                application["applied_by_actor_id"],
                application["applied_at"],
                application["application_hash"],
            ),
        )
        return rule_set_id

    def append_protected_change_request(
        self, value: Mapping[str, Any]
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_protected_change_requests("
            "request_id,rule_id,requested_baseline_id,"
            "predecessor_version,candidate_version,"
            "change_kind,requested_action,reason,proposed_effective_at,"
            "requester_actor_id,requested_at,candidate_content_hash,"
            "evidence_context_hash,before_definition_json,after_definition_json,test_id,"
            "prior_request_id,initial_status"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                value["request_id"],
                value["rule_id"],
                value["requested_baseline_id"],
                value["predecessor_version"],
                value["candidate_version"],
                value["change_kind"],
                "REPLACE",
                value["reason"],
                value["proposed_effective_at"],
                value["requester_actor_id"],
                value["requested_at"],
                value["candidate_content_hash"],
                value["evidence_context_hash"],
                _json(value["before_definition"]),
                _json(value["after_definition"]),
                value["test_id"],
                value.get("prior_request_id"),
                "PENDING_APPROVAL",
            ),
        )

    def protected_change_request(
        self, request_id: str
    ) -> dict[str, Any] | None:
        rows = self._protected_change_request_rows(
            "WHERE r.request_id=?", (request_id,)
        )
        return rows[0] if rows else None

    def list_protected_change_requests(self) -> list[dict[str, Any]]:
        return self._protected_change_request_rows(
            "ORDER BY r.requested_at DESC,r.request_id DESC", ()
        )

    def _protected_change_request_rows(
        self, suffix: str, parameters: tuple[Any, ...]
    ) -> list[dict[str, Any]]:
        rows = self._dal.conn.execute(
            "SELECT r.request_id,r.rule_id,r.requested_baseline_id,"
            "r.predecessor_version,"
            "r.candidate_version,r.change_kind,r.reason,r.proposed_effective_at,"
            "r.requester_actor_id,r.requested_at,r.candidate_content_hash,"
            "r.evidence_context_hash,r.before_definition_json,"
            "r.after_definition_json,r.test_id,"
            "r.prior_request_id,r.initial_status,"
            "d.decision,d.approver_actor_id,d.decided_at,d.reason,"
            "a.prior_baseline_id,a.resulting_baseline_id,a.activated_at,"
            "t.metrics_json,t.dataset_fingerprint,t.ledger_hash "
            "FROM v2_protected_change_requests r "
            "JOIN v2_protected_candidate_tests t "
            "ON t.test_id=r.test_id "
            "LEFT JOIN v2_protected_change_decisions d "
            "ON d.request_id=r.request_id "
            "LEFT JOIN v2_protected_change_activations a "
            "ON a.request_id=r.request_id "
            + suffix,
            parameters,
        ).fetchall()
        keys = (
            "request_id",
            "rule_id",
            "requested_baseline_id",
            "predecessor_version",
            "candidate_version",
            "change_kind",
            "reason",
            "proposed_effective_at",
            "requester_actor_id",
            "requested_at",
            "candidate_content_hash",
            "evidence_context_hash",
            "before_definition",
            "after_definition",
            "test_id",
            "prior_request_id",
            "initial_status",
            "decision",
            "approver_actor_id",
            "decided_at",
            "decision_reason",
            "prior_baseline_id",
            "resulting_baseline_id",
            "activated_at",
            "qualification_metrics",
            "qualification_dataset_fingerprint",
            "qualification_ledger_hash",
        )
        output: list[dict[str, Any]] = []
        for row in rows:
            value = dict(zip(keys, row))
            value["before_definition"] = json.loads(
                value["before_definition"]
            )
            value["after_definition"] = json.loads(
                value["after_definition"]
            )
            value["qualification_metrics"] = json.loads(
                value["qualification_metrics"]
            )
            value["status"] = value["decision"] or value["initial_status"]
            output.append(value)
        return output

    def append_protected_candidate_test(
        self, value: Mapping[str, Any]
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_protected_candidate_tests("
            "test_id,rule_id,rule_version,evidence_context_hash,"
            "dataset_fingerprint,status,metrics_json,ledger_hash,actor_id,tested_at"
            ") VALUES(?,?,?,?,?,'COMPLETE',?,?,?,?)",
            (
                value["test_id"],
                value["rule_id"],
                value["rule_version"],
                value["evidence_context_hash"],
                value["dataset_fingerprint"],
                _json(value["metrics"]),
                value["ledger_hash"],
                value["actor_id"],
                value["tested_at"],
            ),
        )

    def append_protected_change_decision(
        self, value: Mapping[str, Any]
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_protected_change_decisions("
            "request_id,decision,approver_actor_id,decided_at,reason,decision_hash"
            ") VALUES(?,?,?,?,?,?)",
            (
                value["request_id"],
                value["decision"],
                value["approver_actor_id"],
                value["decided_at"],
                value["reason"],
                value["decision_hash"],
            ),
        )

    def activate_protected_change(
        self,
        request: Mapping[str, Any],
        *,
        activated_at: str,
        activation_hash: str,
    ) -> str:
        """Seal a new five-member baseline; existing workspace pointers do not move."""

        prior_baseline_id = self.current_protected_baseline_id()
        members = self.protected_baseline_members(prior_baseline_id)
        if len(members) != 5:
            raise ValueError("The active protected baseline is incomplete.")
        candidate = self.rule_version(
            str(request["rule_id"]), str(request["candidate_version"])
        )
        if (
            candidate is None
            or candidate["content_hash"] != request["candidate_content_hash"]
            or candidate["lifecycle_status"] != "TESTED"
        ):
            raise ValueError("The exact immutable Tested candidate is unavailable.")
        replaced = False
        for item in members:
            if item["rule_id"] == request["rule_id"]:
                item["rule_version"] = request["candidate_version"]
                replaced = True
        if not replaced:
            raise ValueError("The protected Rule ID is not in the active baseline.")

        baseline_sequence = int(
            self._dal.conn.execute(
                "SELECT COUNT(*) FROM v2_protected_change_activations"
            ).fetchone()[0]
        ) + 1
        resulting_baseline_id = (
            f"FINSIGHT-CORE-GOV-{baseline_sequence:04d}-"
            f"{str(request['request_id'])[-8:]}"
        )
        baseline_version = f"2.0.{baseline_sequence}"
        self._dal.conn.execute(
            "INSERT INTO v2_core_rule_versions("
            "rule_id,version,name,severity,baseline_status,evaluator_key,created_at"
            ") VALUES(?,?,?,?,?,?,?)",
            (
                candidate["rule_id"],
                candidate["version"],
                candidate["name"],
                candidate["severity"],
                "PROTECTED_BASELINE",
                candidate["evaluator_key"],
                activated_at,
            ),
        )
        self._dal.conn.execute(
            "INSERT INTO v2_core_rule_set_versions("
            "rule_set_id,version,status,created_at) VALUES(?,?,?,?)",
            (
                resulting_baseline_id,
                baseline_version,
                "PROTECTED_BASELINE",
                activated_at,
            ),
        )
        for item in members:
            self._dal.conn.execute(
                "INSERT INTO v2_core_rule_set_members("
                "rule_set_id,ordinal,rule_id,rule_version) VALUES(?,?,?,?)",
                (
                    resulting_baseline_id,
                    int(item["ordinal"]),
                    item["rule_id"],
                    item["rule_version"],
                ),
            )
        self._dal.conn.execute(
            "INSERT INTO v2_protected_change_activations("
            "request_id,prior_baseline_id,resulting_baseline_id,"
            "activated_rule_id,activated_rule_version,activated_at,activation_hash"
            ") VALUES(?,?,?,?,?,?,?)",
            (
                request["request_id"],
                prior_baseline_id,
                resulting_baseline_id,
                request["rule_id"],
                request["candidate_version"],
                activated_at,
                activation_hash,
            ),
        )
        return resulting_baseline_id

    def append_rule_test(self, value: Mapping[str, Any]) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_rule_test_runs("
            "test_id,review_id,rule_id,rule_version,dataset_fingerprint,status,"
            "metrics_json,ledger_hash,actor_id,tested_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                value["test_id"],
                value["review_id"],
                value["rule_id"],
                value["rule_version"],
                value["dataset_fingerprint"],
                value["status"],
                _json(value["metrics"]),
                value["ledger_hash"],
                value["actor_id"],
                value["tested_at"],
            ),
        )

    def latest_successful_rule_test(
        self, review_id: str, rule_id: str, version: str
    ) -> dict[str, Any] | None:
        row = self._dal.conn.execute(
            "SELECT test_id,dataset_fingerprint,metrics_json,ledger_hash,actor_id,tested_at "
            "FROM v2_rule_test_runs WHERE review_id=? AND rule_id=? AND rule_version=? "
            "AND status='COMPLETE' ORDER BY rowid DESC LIMIT 1",
            (review_id, rule_id, version),
        ).fetchone()
        if not row:
            return None
        return {
            "test_id": row[0],
            "dataset_fingerprint": row[1],
            "metrics": json.loads(row[2]),
            "ledger_hash": row[3],
            "actor_id": row[4],
            "tested_at": row[5],
        }

    def append_correction(self, value: Mapping[str, Any]) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_review_correction_events("
            "correction_id,review_id,candidate_id,record_id,source_role,worksheet_name,"
            "source_row,field_name,source_cell,original_value_json,prior_value_json,"
            "new_value_json,action,actor_id,occurred_at,predecessor_correction_id,event_hash"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                value["correction_id"],
                value["review_id"],
                value["candidate_id"],
                value["record_id"],
                value["source_role"],
                value["worksheet_name"],
                int(value["source_row"]),
                value["field_name"],
                value["source_cell"],
                _json(value.get("original_value")),
                _json(value.get("prior_value")),
                _json(value.get("new_value")),
                value["action"],
                value["actor_id"],
                value["occurred_at"],
                value.get("predecessor_correction_id"),
                value["event_hash"],
            ),
        )

    def correction_history(self, review_id: str) -> list[dict[str, Any]]:
        rows = self._dal.conn.execute(
            "SELECT correction_id,candidate_id,record_id,source_role,worksheet_name,"
            "source_row,field_name,source_cell,original_value_json,prior_value_json,"
            "new_value_json,action,actor_id,occurred_at,predecessor_correction_id,event_hash "
            "FROM v2_review_correction_events WHERE review_id=? ORDER BY rowid",
            (review_id,),
        ).fetchall()
        keys = (
            "correction_id", "candidate_id", "record_id", "source_role",
            "worksheet_name", "source_row", "field_name", "source_cell",
            "original_value", "prior_value", "new_value", "action", "actor_id",
            "occurred_at", "predecessor_correction_id", "event_hash",
        )
        result = []
        for row in rows:
            item = dict(zip(keys, row))
            for key in ("original_value", "prior_value", "new_value"):
                item[key] = json.loads(item[key])
            result.append(item)
        return result

    def current_corrections(self, review_id: str) -> list[dict[str, Any]]:
        history = self.correction_history(review_id)
        latest: dict[tuple[str, str], dict[str, Any]] = {}
        for item in history:
            latest[(item["record_id"], item["field_name"])] = item
        return sorted(
            latest.values(),
            key=lambda item: (
                item["source_role"], int(item["source_row"]), item["field_name"]
            ),
        )

    def current_correction(
        self, review_id: str, record_id: str, field_name: str
    ) -> dict[str, Any] | None:
        row = self._dal.conn.execute(
            "SELECT correction_id,new_value_json FROM v2_review_correction_events "
            "WHERE review_id=? AND record_id=? AND field_name=? ORDER BY rowid DESC LIMIT 1",
            (review_id, record_id, field_name),
        ).fetchone()
        return (
            {"correction_id": row[0], "new_value": json.loads(row[1])}
            if row else None
        )

    def append_confirmation(self, confirmation: Mapping[str, Any]) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_review_confirmations("
            "confirmation_id,review_id,candidate_id,generation_id,dataset_fingerprint,"
            "budget_sha256,ged_sha256,correction_count,attestation_text,actor_id,confirmed_at"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                confirmation["confirmation_id"],
                confirmation["review_id"],
                confirmation["candidate_id"],
                confirmation["generation_id"],
                confirmation["dataset_fingerprint"],
                confirmation["budget_sha256"],
                confirmation["ged_sha256"],
                int(confirmation["correction_count"]),
                confirmation["attestation_text"],
                confirmation["actor_id"],
                confirmation["confirmed_at"],
            ),
        )
        self._dal.conn.execute(
            "INSERT INTO v2_generation_review_bases("
            "generation_id,review_id,candidate_id,confirmation_id,dataset_fingerprint,"
            "department_number,department_name,reporting_period,budget_filename,"
            "ged_filename,budget_sha256,ged_sha256,budget_record_count,"
            "ged_transaction_count,correction_count,extractor_profile_version,created_at"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                confirmation["generation_id"],
                confirmation["review_id"],
                confirmation["candidate_id"],
                confirmation["confirmation_id"],
                confirmation["dataset_fingerprint"],
                confirmation["department_number"],
                confirmation["department_name"],
                confirmation["reporting_period"],
                confirmation["budget_filename"],
                confirmation["ged_filename"],
                confirmation["budget_sha256"],
                confirmation["ged_sha256"],
                int(confirmation["budget_record_count"]),
                int(confirmation["ged_transaction_count"]),
                int(confirmation["correction_count"]),
                confirmation["extractor_profile_version"],
                confirmation["confirmed_at"],
            ),
        )

    def generation_basis(self, review_id: str) -> dict[str, Any] | None:
        row = self._dal.conn.execute(
            "SELECT generation_id,candidate_id,confirmation_id,dataset_fingerprint,"
            "department_number,department_name,reporting_period,budget_filename,ged_filename,"
            "budget_sha256,ged_sha256,budget_record_count,ged_transaction_count,"
            "correction_count,extractor_profile_version,created_at "
            "FROM v2_generation_review_bases WHERE review_id=? ORDER BY rowid DESC LIMIT 1",
            (review_id,),
        ).fetchone()
        if not row:
            return None
        keys = (
            "generation_id", "candidate_id", "confirmation_id", "dataset_fingerprint",
            "department_number", "department_name", "reporting_period", "budget_filename",
            "ged_filename", "budget_sha256", "ged_sha256", "budget_record_count",
            "ged_transaction_count", "correction_count", "extractor_profile_version",
            "created_at",
        )
        return dict(zip(keys, row))

    def append_reanalysis_basis(self, value: Mapping[str, Any]) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_reanalysis_generation_bases("
            "generation_id,review_id,source_generation_id,dataset_fingerprint,"
            "rule_set_id,created_by,created_at) VALUES(?,?,?,?,?,?,?)",
            (
                value["generation_id"],
                value["review_id"],
                value["source_generation_id"],
                value["dataset_fingerprint"],
                value["rule_set_id"],
                value["created_by"],
                value["created_at"],
            ),
        )

    def append_validation_rule_set_confirmation(
        self, value: Mapping[str, Any]
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_validation_rule_set_confirmations("
            "confirmation_id,run_id,review_id,rule_set_id,rule_set_version,"
            "dataset_fingerprint,source_generation_id,source_data_version,"
            "prior_run_id,rules_json,excluded_drafts_json,changes_json,"
            "actor_id,confirmed_at,confirmation_hash) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                value["confirmation_id"],
                value["run_id"],
                value["review_id"],
                value["rule_set_id"],
                str(value["rule_set_version"]),
                value["dataset_fingerprint"],
                value["source_generation_id"],
                value["source_data_version"],
                value.get("prior_run_id"),
                _json(value["rules"]),
                _json(value.get("excluded_drafts", ())),
                _json(value.get("changes", ())),
                value["actor_id"],
                value["confirmed_at"],
                value["confirmation_hash"],
            ),
        )

    def validation_rule_set_confirmation(
        self, confirmation_id: str
    ) -> dict[str, Any] | None:
        row = self._dal.conn.execute(
            "SELECT confirmation_id,run_id,review_id,rule_set_id,rule_set_version,"
            "dataset_fingerprint,source_generation_id,source_data_version,"
            "prior_run_id,rules_json,excluded_drafts_json,changes_json,"
            "actor_id,confirmed_at,confirmation_hash "
            "FROM v2_validation_rule_set_confirmations WHERE confirmation_id=?",
            (confirmation_id,),
        ).fetchone()
        if row is None:
            return None
        keys = (
            "confirmation_id",
            "run_id",
            "review_id",
            "rule_set_id",
            "rule_set_version",
            "dataset_fingerprint",
            "source_generation_id",
            "source_data_version",
            "prior_run_id",
            "rules",
            "excluded_drafts",
            "changes",
            "actor_id",
            "confirmed_at",
            "confirmation_hash",
        )
        value = dict(zip(keys, row))
        for key in ("rules", "excluded_drafts", "changes"):
            value[key] = json.loads(value[key])
        value["events"] = self.validation_attempt_events(confirmation_id)
        return value

    def append_validation_attempt_event(
        self, value: Mapping[str, Any]
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_validation_attempt_events("
            "event_id,confirmation_id,ordinal,event_type,run_id,actor_id,"
            "occurred_at,reason,payload_json,event_hash) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                value["event_id"],
                value["confirmation_id"],
                int(value["ordinal"]),
                value["event_type"],
                value.get("run_id"),
                value["actor_id"],
                value["occurred_at"],
                value["reason"],
                _json(value.get("payload", {})),
                value["event_hash"],
            ),
        )

    def next_validation_attempt_ordinal(self, confirmation_id: str) -> int:
        row = self._dal.conn.execute(
            "SELECT COALESCE(MAX(ordinal),0)+1 FROM v2_validation_attempt_events "
            "WHERE confirmation_id=?",
            (confirmation_id,),
        ).fetchone()
        return int(row[0])

    def validation_attempt_events(
        self, confirmation_id: str
    ) -> list[dict[str, Any]]:
        rows = self._dal.conn.execute(
            "SELECT event_id,confirmation_id,ordinal,event_type,run_id,actor_id,"
            "occurred_at,reason,payload_json,event_hash "
            "FROM v2_validation_attempt_events WHERE confirmation_id=? "
            "ORDER BY ordinal",
            (confirmation_id,),
        ).fetchall()
        keys = (
            "event_id",
            "confirmation_id",
            "ordinal",
            "event_type",
            "run_id",
            "actor_id",
            "occurred_at",
            "reason",
            "payload",
            "event_hash",
        )
        output = []
        for row in rows:
            value = dict(zip(keys, row))
            value["ordinal"] = int(value["ordinal"])
            value["payload"] = json.loads(value["payload"])
            output.append(value)
        return output

    def append_validation_confirmation_run_link(
        self, value: Mapping[str, Any]
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_validation_confirmation_run_links("
            "confirmation_id,run_id,prior_run_id,linked_at,link_hash) "
            "VALUES(?,?,?,?,?)",
            (
                value["confirmation_id"],
                value["run_id"],
                value.get("prior_run_id"),
                value["linked_at"],
                value["link_hash"],
            ),
        )

    def validation_confirmation_for_run(
        self, run_id: str
    ) -> dict[str, Any] | None:
        row = self._dal.conn.execute(
            "SELECT confirmation_id FROM v2_validation_confirmation_run_links "
            "WHERE run_id=?",
            (run_id,),
        ).fetchone()
        return self.validation_rule_set_confirmation(row[0]) if row else None

    def persist_validation(
        self,
        *,
        run_id: str,
        review_id: str,
        generation_id: str,
        actor_id: str,
        started_at: str,
        completed_at: str,
        ledger_hash: str,
        completion_seal: str,
        evaluation: ValidationEvaluation,
        finding_explanations: tuple[Mapping[str, Any], ...] = (),
        leadership_summary: Mapping[str, Any] | None = None,
        revalidation_reason: str = "INITIAL_VALIDATION",
    ) -> None:
        predecessor = self.latest_run(review_id)
        self._dal.conn.execute(
            "INSERT INTO v2_validation_runs("
            "run_id,review_id,generation_id,rule_set_id,dataset_fingerprint,status,"
            "started_at,completed_at,actor_id,metrics_json,ledger_hash,completion_seal"
            ") VALUES(?,?,?,?,?,'COMPLETE',?,?,?,?,?,?)",
            (
                run_id,
                review_id,
                generation_id,
                evaluation.protected_baseline_id,
                evaluation.dataset_fingerprint,
                started_at,
                completed_at,
                actor_id,
                _json(dict(evaluation.metrics)),
                ledger_hash,
                completion_seal,
            ),
        )
        if self._dal.conn.execute(
            "SELECT 1 FROM v2_rule_set_versions WHERE rule_set_id=?",
            (evaluation.rule_set_id,),
        ).fetchone():
            self._dal.conn.execute(
                "INSERT INTO v2_validation_run_rule_sets("
                "run_id,rule_set_id,predecessor_run_id,revalidation_reason) VALUES(?,?,?,?)",
                (
                    run_id,
                    evaluation.rule_set_id,
                    predecessor["run_id"] if predecessor else None,
                    revalidation_reason,
                ),
            )
        execution_ids: dict[str, str] = {}
        for ordinal, execution in enumerate(evaluation.executions, 1):
            execution_id = f"{run_id}_{execution.rule_id.lower()}"
            execution_ids[execution.rule_id] = execution_id
            table = (
                "v2_rule_executions"
                if execution.baseline_status == "PROTECTED_BASELINE"
                else "v2_optional_rule_executions"
            )
            self._dal.conn.execute(
                f"INSERT INTO {table}("
                "execution_id,run_id,ordinal,rule_id,rule_version,rule_name,"
                "baseline_status,status,pass_count,fail_count,not_evaluated_count"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    execution_id,
                    run_id,
                    ordinal,
                    execution.rule_id,
                    execution.version,
                    execution.rule_name,
                    execution.baseline_status,
                    execution.status.value,
                    execution.pass_count,
                    execution.fail_count,
                    execution.not_evaluated_count,
                ),
            )
        for ordinal, result in enumerate(evaluation.scope_results, 1):
            optional = not result.rule_id.startswith("CORE-")
            table = (
                "v2_optional_rule_scope_results"
                if optional
                else "v2_rule_scope_results"
            )
            self._dal.conn.execute(
                f"INSERT INTO {table}("
                "result_id,run_id,execution_id,ordinal,rule_id,scope_id,status,"
                "department_number,account_number,source_records_json,expected,actual,"
                "explanation,evidence_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    f"{run_id}_result_{ordinal:04d}",
                    run_id,
                    execution_ids[result.rule_id],
                    ordinal,
                    result.rule_id,
                    result.scope_id,
                    result.status.value,
                    result.department_number,
                    result.account_number,
                    _json(list(result.source_records)),
                    result.expected,
                    result.actual,
                    result.explanation,
                    _json(
                        {
                            "references": list(result.evidence),
                            "details": list(result.evidence_details),
                        }
                    ),
                ),
            )
        expected_finding_ids: set[str] = set()
        for finding in evaluation.findings:
            table = (
                "v2_validation_findings"
                if finding.rule_id.startswith("CORE-")
                else "v2_optional_validation_findings"
            )
            persisted_finding_id = f"{run_id}_{finding.finding_id}"
            expected_finding_ids.add(persisted_finding_id)
            self._dal.conn.execute(
                f"INSERT INTO {table}("
                "finding_id,run_id,rule_id,rule_name,severity,department_number,"
                "account_number,source_records_json,original_or_edited_value,expected,"
                "actual,explanation,recommended_action,evidence_json"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    persisted_finding_id,
                    run_id,
                    finding.rule_id,
                    finding.rule_name,
                    finding.severity,
                    finding.department_number,
                    finding.account_number,
                    _json(list(finding.source_records)),
                    finding.original_or_edited_value,
                    finding.expected,
                    finding.actual,
                    finding.explanation,
                    finding.recommended_action,
                    _json(
                        {
                            "references": list(finding.evidence),
                            "details": list(finding.evidence_details),
                        }
                    ),
                ),
            )
        provided_finding_ids = {
            str(item["finding_id"]) for item in finding_explanations
        }
        if provided_finding_ids != expected_finding_ids:
            raise ValueError(
                "Every sealed finding requires exactly one deterministic "
                "explanation projection."
            )
        for projection in finding_explanations:
            finding_id = str(projection["finding_id"])
            self._insert_finding_explanation(
                finding_id=finding_id,
                run_id=run_id,
                projection=projection,
                created_at=completed_at,
            )
            initial = {
                "event_id": f"{finding_id}_status_0001",
                "review_id": review_id,
                "run_id": run_id,
                "finding_id": finding_id,
                "ordinal": 1,
                "previous_status": None,
                "status": FindingReviewStatus.NEW.value,
                "event_kind": "INITIAL_ASSIGNMENT",
                "review_required": True,
                "actor_id": actor_id,
                "occurred_at": completed_at,
                "reason": "SEALED_FINDING_CREATED",
            }
            initial["event_hash"] = _digest(initial)
            self.append_finding_review_status(initial)
        if leadership_summary is None:
            raise ValueError(
                "Every sealed Validation Run requires a deterministic "
                "leadership-summary projection."
            )
        self._dal.conn.execute(
            "INSERT INTO v2_leadership_summary_projections("
            "run_id,projection_json,content_hash,created_at) VALUES(?,?,?,?)",
            (
                run_id,
                _json(dict(leadership_summary)),
                _digest(dict(leadership_summary)),
                completed_at,
            ),
        )

    def _insert_finding_explanation(
        self,
        *,
        finding_id: str,
        run_id: str,
        projection: Mapping[str, Any],
        created_at: str,
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_finding_explanation_projections("
            "finding_id,run_id,projection_json,content_hash,created_at) "
            "VALUES(?,?,?,?,?)",
            (
                finding_id,
                run_id,
                _json(dict(projection)),
                _digest(dict(projection)),
                created_at,
            ),
        )

    def ensure_finding_explanation(
        self,
        *,
        review_id: str,
        run_id: str,
        finding_id: str,
        projection: Mapping[str, Any],
        actor_id: str,
        occurred_at: str,
    ) -> None:
        """Materialize a retained pre-0013 explanation before status review."""

        existing = self._dal.conn.execute(
            "SELECT 1 FROM v2_finding_explanation_projections "
            "WHERE finding_id=? AND run_id=?",
            (finding_id, run_id),
        ).fetchone()
        if existing:
            return
        self._insert_finding_explanation(
            finding_id=finding_id,
            run_id=run_id,
            projection=projection,
            created_at=occurred_at,
        )
        event = {
            "event_id": f"{finding_id}_status_0001",
            "review_id": review_id,
            "run_id": run_id,
            "finding_id": finding_id,
            "ordinal": 1,
            "previous_status": None,
            "status": FindingReviewStatus.NEW.value,
            "event_kind": "INITIAL_ASSIGNMENT",
            "review_required": True,
            "actor_id": actor_id,
            "occurred_at": occurred_at,
            "reason": "RETAINED_FINDING_ENTERED_REVIEW_WORKFLOW",
        }
        event["event_hash"] = _digest(event)
        self.append_finding_review_status(event)

    def append_finding_review_status(
        self, value: Mapping[str, Any]
    ) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_finding_review_status_events("
            "event_id,review_id,run_id,finding_id,ordinal,previous_status,"
            "status,event_kind,review_required,actor_id,occurred_at,reason,"
            "event_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                value["event_id"],
                value["review_id"],
                value["run_id"],
                value["finding_id"],
                int(value["ordinal"]),
                value.get("previous_status"),
                value["status"],
                value["event_kind"],
                int(bool(value["review_required"])),
                value["actor_id"],
                value["occurred_at"],
                value["reason"],
                value["event_hash"],
            ),
        )

    def finding_review_history(
        self, review_id: str, finding_id: str
    ) -> list[dict[str, Any]]:
        rows = self._dal.conn.execute(
            "SELECT e.event_id,e.run_id,e.finding_id,e.ordinal,"
            "e.previous_status,e.status,e.event_kind,e.review_required,"
            "e.actor_id,e.occurred_at,e.reason,e.event_hash "
            "FROM v2_finding_review_status_events e "
            "JOIN v2_validation_runs r ON r.run_id=e.run_id "
            "WHERE r.review_id=? AND e.finding_id=? ORDER BY e.ordinal",
            (review_id, finding_id),
        ).fetchall()
        keys = (
            "event_id",
            "run_id",
            "finding_id",
            "ordinal",
            "previous_status",
            "status",
            "event_kind",
            "review_required",
            "actor_id",
            "occurred_at",
            "reason",
            "event_hash",
        )
        return [
            {
                **dict(zip(keys, row)),
                "ordinal": int(row[3]),
                "review_required": bool(row[7]),
            }
            for row in rows
        ]

    def next_finding_review_status_ordinal(
        self, finding_id: str
    ) -> int:
        row = self._dal.conn.execute(
            "SELECT COALESCE(MAX(ordinal),0)+1 "
            "FROM v2_finding_review_status_events WHERE finding_id=?",
            (finding_id,),
        ).fetchone()
        return int(row[0])

    def finding_location(
        self, review_id: str, finding_id: str
    ) -> dict[str, str] | None:
        row = self._dal.conn.execute(
            "SELECT findings.run_id FROM ("
            "SELECT finding_id,run_id FROM v2_validation_findings "
            "UNION ALL SELECT finding_id,run_id "
            "FROM v2_optional_validation_findings"
            ") findings JOIN v2_validation_runs runs "
            "ON runs.run_id=findings.run_id "
            "WHERE runs.review_id=? AND findings.finding_id=?",
            (review_id, finding_id),
        ).fetchone()
        return {"run_id": str(row[0])} if row else None

    def finding_explanation_projection(
        self, review_id: str, finding_id: str
    ) -> dict[str, Any] | None:
        row = self._dal.conn.execute(
            "SELECT e.projection_json FROM "
            "v2_finding_explanation_projections e "
            "JOIN v2_validation_runs r ON r.run_id=e.run_id "
            "WHERE r.review_id=? AND e.finding_id=?",
            (review_id, finding_id),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def latest_run(self, review_id: str) -> dict[str, Any] | None:
        row = self._dal.conn.execute(
            "SELECT run_id,generation_id,rule_set_id,dataset_fingerprint,status,"
            "started_at,completed_at,actor_id,metrics_json,ledger_hash,completion_seal "
            "FROM v2_validation_runs WHERE review_id=? AND status='COMPLETE' "
            "ORDER BY rowid DESC LIMIT 1",
            (review_id,),
        ).fetchone()
        if not row:
            return None
        keys = (
            "run_id", "generation_id", "rule_set_id", "dataset_fingerprint",
            "status", "started_at", "completed_at", "actor_id", "metrics",
            "ledger_hash", "completion_seal",
        )
        result = dict(zip(keys, row))
        result["metrics"] = json.loads(result["metrics"])
        result["protected_baseline_id"] = result["rule_set_id"]
        mapping = self._dal.conn.execute(
            "SELECT rule_set_id,predecessor_run_id,revalidation_reason "
            "FROM v2_validation_run_rule_sets WHERE run_id=?",
            (result["run_id"],),
        ).fetchone()
        if mapping:
            result["rule_set_id"] = mapping[0]
            result["predecessor_run_id"] = mapping[1]
            result["revalidation_reason"] = mapping[2]
        else:
            result["predecessor_run_id"] = None
            result["revalidation_reason"] = "LEGACY_OR_INITIAL_VALIDATION"
        return result

    def run_projection(
        self, review_id: str, run_id: str | None = None
    ) -> dict[str, Any] | None:
        run = (
            self._run_by_id(review_id, run_id)
            if run_id is not None
            else self.latest_run(review_id)
        )
        if run is None:
            return None
        run_id = run["run_id"]
        execution_rows = self._dal.conn.execute(
            "SELECT ordinal,rule_id,rule_name,rule_version,baseline_status,status,"
            "pass_count,fail_count,not_evaluated_count FROM v2_rule_executions "
            "WHERE run_id=? UNION ALL "
            "SELECT ordinal,rule_id,rule_name,rule_version,baseline_status,status,"
            "pass_count,fail_count,not_evaluated_count FROM v2_optional_rule_executions "
            "WHERE run_id=? ORDER BY ordinal",
            (run_id, run_id),
        ).fetchall()
        execution_keys = (
            "ordinal", "rule_id", "rule_name", "version", "baseline_status", "status",
            "pass_count", "fail_count", "not_evaluated_count",
        )
        finding_rows = self._dal.conn.execute(
            "SELECT finding_id,rule_id,rule_name,severity,department_number,"
            "account_number,source_records_json,original_or_edited_value,expected,"
            "actual,explanation,recommended_action,evidence_json "
            "FROM v2_validation_findings WHERE run_id=? UNION ALL "
            "SELECT finding_id,rule_id,rule_name,severity,department_number,"
            "account_number,source_records_json,original_or_edited_value,expected,"
            "actual,explanation,recommended_action,evidence_json "
            "FROM v2_optional_validation_findings WHERE run_id=?",
            (run_id, run_id),
        ).fetchall()
        finding_keys = (
            "finding_id", "rule_id", "rule_name", "severity", "department_number",
            "account_number", "source_records", "original_or_edited_value",
            "expected", "actual", "explanation", "recommended_action", "evidence",
        )
        scope_rows = self._dal.conn.execute(
            "SELECT ordinal,rule_id,scope_id,status,department_number,account_number,"
            "source_records_json,expected,actual,explanation,evidence_json "
            "FROM v2_rule_scope_results WHERE run_id=? UNION ALL "
            "SELECT ordinal,rule_id,scope_id,status,department_number,account_number,"
            "source_records_json,expected,actual,explanation,evidence_json "
            "FROM v2_optional_rule_scope_results WHERE run_id=? ORDER BY ordinal",
            (run_id, run_id),
        ).fetchall()
        scope_keys = (
            "ordinal", "rule_id", "scope_id", "status", "department_number", "account_number",
            "source_records", "expected", "actual", "explanation", "evidence",
        )
        explanation_rows = self._dal.conn.execute(
            "SELECT finding_id,projection_json "
            "FROM v2_finding_explanation_projections WHERE run_id=?",
            (run_id,),
        ).fetchall()
        explanations = {
            str(finding_id): json.loads(projection)
            for finding_id, projection in explanation_rows
        }
        status_rows = self._dal.conn.execute(
            "SELECT event_id,run_id,finding_id,ordinal,previous_status,status,"
            "event_kind,review_required,actor_id,occurred_at,reason,event_hash "
            "FROM v2_finding_review_status_events WHERE run_id=? "
            "ORDER BY finding_id,ordinal",
            (run_id,),
        ).fetchall()
        status_keys = (
            "event_id",
            "run_id",
            "finding_id",
            "ordinal",
            "previous_status",
            "status",
            "event_kind",
            "review_required",
            "actor_id",
            "occurred_at",
            "reason",
            "event_hash",
        )
        status_history: dict[str, list[dict[str, Any]]] = {}
        for row in status_rows:
            value = dict(zip(status_keys, row))
            value["ordinal"] = int(value["ordinal"])
            value["review_required"] = bool(value["review_required"])
            status_history.setdefault(str(value["finding_id"]), []).append(
                value
            )
        basis = self.generation_basis(review_id) or {}
        run["executions"] = []
        for row in execution_rows:
            item = {
                key: value
                for key, value in dict(zip(execution_keys, row)).items()
                if key != "ordinal"
            }
            presentation = self._rule_presentation(
                item["rule_id"], item["version"], item["rule_name"]
            )
            item.update(presentation)
            run["executions"].append(item)
        version_by_rule = {
            item["rule_id"]: item["version"] for item in run["executions"]
        }
        run["findings"] = []
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        for row in sorted(
            finding_rows,
            key=lambda value: (
                severity_order.get(value[3], 9), value[1], value[0]
            ),
        ):
            item = dict(zip(finding_keys, row))
            item["source_records"] = json.loads(item["source_records"])
            evidence = json.loads(item["evidence"])
            if isinstance(evidence, dict):
                item["evidence"] = evidence.get("references", [])
                item["evidence_details"] = evidence.get("details", [])
            else:
                item["evidence"] = evidence
                item["evidence_details"] = []
            item["rule_version"] = version_by_rule.get(
                item["rule_id"], "Unavailable"
            )
            explanation = explanations.get(item["finding_id"])
            if explanation is None:
                explanation = legacy_explanation(item, run, basis)
            history = status_history.get(item["finding_id"], [])
            item["business_title"] = explanation["business_title"]
            item["review_required"] = bool(
                history[-1]["review_required"]
                if history
                else explanation.get("review_required", True)
            )
            item["review_status"] = (
                history[-1]["status"]
                if history
                else FindingReviewStatus.NEW.value
            )
            item["review_status_history"] = history
            item["explain_this"] = explanation
            item["what_happened"] = explanation["what_happened"]
            item["recommended_next_step"] = explanation[
                "recommended_next_step"
            ]
            run["findings"].append(item)
        run["scope_results"] = []
        for row in scope_rows:
            item = dict(zip(scope_keys, row))
            item.pop("ordinal")
            item["source_records"] = json.loads(item["source_records"])
            evidence = json.loads(item["evidence"])
            if isinstance(evidence, dict):
                item["evidence"] = evidence.get("references", [])
                item["evidence_details"] = evidence.get("details", [])
            else:
                item["evidence"] = evidence
                item["evidence_details"] = []
            item["rule_version"] = version_by_rule.get(
                item["rule_id"], "Unavailable"
            )
            run["scope_results"].append(item)
        run["basis"] = basis
        run["completion"] = self.completion(review_id, run_id=run_id)
        summary_row = self._dal.conn.execute(
            "SELECT projection_json FROM v2_leadership_summary_projections "
            "WHERE run_id=?",
            (run_id,),
        ).fetchone()
        manifest = self.rule_set_manifest(run["rule_set_id"])
        rule_set_version = manifest.version if manifest else "Unavailable"
        if summary_row:
            leadership = json.loads(summary_row[0])
        else:
            leadership = build_leadership_summary(
                review_id=review_id,
                run_id=run_id,
                generation_id=run["generation_id"],
                rule_set_id=run["rule_set_id"],
                rule_set_version=rule_set_version,
                completed_at=run["completed_at"],
                metrics=run["metrics"],
                findings=run["findings"],
                basis=basis,
            )
        current_finding_status = {
            item["finding_id"]: item["review_status"]
            for item in run["findings"]
        }
        current_review_required = {
            item["finding_id"]: item["review_required"]
            for item in run["findings"]
        }
        leadership["finding_review_status_snapshot"] = current_finding_status
        leadership["finding_review_required_snapshot"] = (
            current_review_required
        )
        for section in (
            "highest_priority_findings",
            "items_requiring_human_review",
        ):
            for item in leadership.get(section, []):
                item["review_status"] = current_finding_status.get(
                    item["finding_id"],
                    item.get("review_status", FindingReviewStatus.NEW.value),
                )
                item["review_required"] = current_review_required.get(
                    item["finding_id"], item.get("review_required", True)
                )
        leadership["items_requiring_human_review"] = [
            item
            for item in leadership.get("items_requiring_human_review", [])
            if item.get("review_required", True)
        ]
        run["leadership_summary"] = leadership
        pointers = self._dal.conn.execute(
            "SELECT working_generation_id,published_generation_id "
            "FROM v2_review_cycle_pointers WHERE review_id=?",
            (review_id,),
        ).fetchone()
        if pointers and pointers[1] == run["generation_id"]:
            run["publication_state"] = "Published"
        elif pointers and pointers[0] == run["generation_id"]:
            run["publication_state"] = "Working"
        else:
            run["publication_state"] = "Historical"
        run["confirmation"] = self.validation_confirmation_for_run(run_id)
        return run

    def _rule_presentation(
        self, rule_id: str, version: str, fallback_name: str
    ) -> dict[str, Any]:
        definition = self.rule_version(rule_id, version)
        if definition:
            return {
                "purpose": definition["purpose"],
                "required_fields": definition["required_fields"],
                "grouping_keys": definition["grouping_keys"],
            }
        legacy_purpose = {
            "CORE-01": (
                "Total GED actual spending must not exceed BGT for the same "
                "Department Number + Account Number."
            ),
            "CORE-02": (
                "Every GED transaction must map to a valid Budget "
                "Department Number + Account Number."
            ),
            "CORE-03": (
                "Flag exact duplicate GED transactions using all material fields."
            ),
            "CORE-04": (
                "Required GED fields must be present and parseable."
            ),
            "CORE-05": (
                "Budget ATD must equal summed GED Amount for each exact account scope."
            ),
        }
        return {
            "purpose": legacy_purpose.get(rule_id, fallback_name),
            "required_fields": [],
            "grouping_keys": [],
        }

    def _run_by_id(self, review_id: str, run_id: str) -> dict[str, Any] | None:
        row = self._dal.conn.execute(
            "SELECT run_id,generation_id,rule_set_id,dataset_fingerprint,status,"
            "started_at,completed_at,actor_id,metrics_json,ledger_hash,completion_seal "
            "FROM v2_validation_runs WHERE review_id=? AND run_id=? AND status='COMPLETE'",
            (review_id, run_id),
        ).fetchone()
        if not row:
            return None
        keys = (
            "run_id", "generation_id", "rule_set_id", "dataset_fingerprint",
            "status", "started_at", "completed_at", "actor_id", "metrics",
            "ledger_hash", "completion_seal",
        )
        result = dict(zip(keys, row))
        result["metrics"] = json.loads(result["metrics"])
        result["protected_baseline_id"] = result["rule_set_id"]
        mapping = self._dal.conn.execute(
            "SELECT rule_set_id,predecessor_run_id,revalidation_reason "
            "FROM v2_validation_run_rule_sets WHERE run_id=?",
            (run_id,),
        ).fetchone()
        if mapping:
            result["rule_set_id"] = mapping[0]
            result["predecessor_run_id"] = mapping[1]
            result["revalidation_reason"] = mapping[2]
        else:
            result["predecessor_run_id"] = None
            result["revalidation_reason"] = "LEGACY_OR_INITIAL_VALIDATION"
        return result

    def run_history(self, review_id: str) -> list[dict[str, Any]]:
        run_ids = [
            row[0]
            for row in self._dal.conn.execute(
                "SELECT run_id FROM v2_validation_runs WHERE review_id=? "
                "AND status='COMPLETE' ORDER BY rowid",
                (review_id,),
            ).fetchall()
        ]
        return [
            projection
            for run_id in run_ids
            if (projection := self.run_projection(review_id, run_id)) is not None
        ]

    def compare_runs(
        self, review_id: str, prior_run_id: str, current_run_id: str
    ) -> dict[str, Any]:
        prior = self.run_projection(review_id, prior_run_id)
        current = self.run_projection(review_id, current_run_id)
        if prior is None or current is None:
            raise ValueError("Both retained Validation Runs are required for comparison.")
        prior_rules = {item["rule_id"]: item for item in prior["executions"]}
        current_rules = {item["rule_id"]: item for item in current["executions"]}
        added_rules = sorted(set(current_rules) - set(prior_rules))
        removed_rules = sorted(set(prior_rules) - set(current_rules))
        changed_rules = []
        unchanged_rules = []
        rule_status_changes = []
        rule_version_changes = []
        for rule_id in sorted(set(prior_rules) & set(current_rules)):
            before = prior_rules[rule_id]
            after = current_rules[rule_id]
            fields = (
                "version",
                "status",
                "pass_count",
                "fail_count",
                "not_evaluated_count",
            )
            if any(before[field] != after[field] for field in fields):
                change = {
                    "rule_id": rule_id,
                    "before": before,
                    "after": after,
                }
                changed_rules.append(change)
                if before["status"] != after["status"]:
                    rule_status_changes.append(change)
                if before["version"] != after["version"]:
                    rule_version_changes.append(change)
            else:
                unchanged_rules.append(after)
        def finding_identity(item: Mapping[str, Any]) -> tuple[Any, ...]:
            return (
                item["rule_id"],
                item["department_number"],
                item["account_number"],
                tuple(item["source_records"]),
            )

        prior_findings = {
            finding_identity(item): item for item in prior["findings"]
        }
        current_findings = {
            finding_identity(item): item for item in current["findings"]
        }
        changed_findings = []
        unchanged_findings = []
        finding_status_changes = []
        for key in sorted(set(prior_findings) & set(current_findings)):
            before = prior_findings[key]
            after = current_findings[key]
            fields = (
                "rule_version",
                "severity",
                "expected",
                "actual",
                "explanation",
                "recommended_action",
                "review_status",
                "review_required",
            )
            if any(before.get(field) != after.get(field) for field in fields):
                change = {
                    "rule_id": after["rule_id"],
                    "source_records": after["source_records"],
                    "before": before,
                    "after": after,
                }
                changed_findings.append(change)
                if (
                    before.get("review_status")
                    != after.get("review_status")
                    or before.get("review_required")
                    != after.get("review_required")
                ):
                    finding_status_changes.append(change)
            else:
                unchanged_findings.append(after)
        added_keys = set(current_findings) - set(prior_findings)
        removed_keys = set(prior_findings) - set(current_findings)
        findings_added = [
            current_findings[key] for key in sorted(added_keys)
        ]
        findings_removed = [
            prior_findings[key] for key in sorted(removed_keys)
        ]
        optional_rule_ids = {
            rule_id
            for rule_id, item in {**prior_rules, **current_rules}.items()
            if item.get("baseline_status") != "PROTECTED_BASELINE"
        }
        optional_rule_effects = []
        for rule_id in sorted(optional_rule_ids):
            before = prior_rules.get(rule_id)
            after = current_rules.get(rule_id)
            added_count = sum(
                item["rule_id"] == rule_id for item in findings_added
            )
            removed_count = sum(
                item["rule_id"] == rule_id for item in findings_removed
            )
            changed_count = sum(
                item["rule_id"] == rule_id for item in changed_findings
            )
            unchanged_count = sum(
                item["rule_id"] == rule_id for item in unchanged_findings
            )
            if before is None:
                effect = "ADDED"
            elif after is None:
                effect = "REMOVED"
            elif (
                before["version"] != after["version"]
                or before["status"] != after["status"]
                or added_count
                or removed_count
                or changed_count
            ):
                effect = "CHANGED"
            else:
                effect = "UNCHANGED"
            optional_rule_effects.append(
                {
                    "rule_id": rule_id,
                    "effect": effect,
                    "before": before,
                    "after": after,
                    "findings_added": added_count,
                    "findings_removed": removed_count,
                    "findings_changed": changed_count,
                    "findings_unchanged": unchanged_count,
                }
            )
        return {
            "review_id": review_id,
            "prior_run_id": prior_run_id,
            "current_run_id": current_run_id,
            "prior_rule_set_id": prior["rule_set_id"],
            "current_rule_set_id": current["rule_set_id"],
            "rules_added": added_rules,
            "rules_removed": removed_rules,
            "rules_changed": changed_rules,
            "rules_unchanged": unchanged_rules,
            "rule_status_changes": rule_status_changes,
            "rule_version_changes": rule_version_changes,
            "findings_added": findings_added,
            "findings_removed": findings_removed,
            "findings_resolved": findings_removed,
            "findings_changed": changed_findings,
            "findings_unchanged": unchanged_findings,
            "finding_status_changes": finding_status_changes,
            "status_changes": [
                *rule_status_changes,
                *finding_status_changes,
            ],
            "optional_rule_effects": optional_rule_effects,
        }

    def append_completion(self, value: Mapping[str, Any]) -> None:
        self._dal.conn.execute(
            "INSERT INTO v2_review_completion_events("
            "completion_id,review_id,generation_id,run_id,completed_by,completed_at,"
            "completion_note,seal_hash) VALUES(?,?,?,?,?,?,?,?)",
            (
                value["completion_id"],
                value["review_id"],
                value["generation_id"],
                value["run_id"],
                value["completed_by"],
                value["completed_at"],
                value["completion_note"],
                value["seal_hash"],
            ),
        )

    def completion(
        self, review_id: str, *, run_id: str | None = None
    ) -> dict[str, Any] | None:
        where = "review_id=?"
        parameters: tuple[Any, ...] = (review_id,)
        if run_id is not None:
            where += " AND run_id=?"
            parameters += (run_id,)
        row = self._dal.conn.execute(
            "SELECT completion_id,generation_id,run_id,completed_by,completed_at,"
            "completion_note,seal_hash FROM v2_review_completion_events WHERE "
            + where
            + " ORDER BY rowid DESC LIMIT 1",
            parameters,
        ).fetchone()
        keys = (
            "completion_id", "generation_id", "run_id", "completed_by",
            "completed_at", "completion_note", "seal_hash",
        )
        return dict(zip(keys, row)) if row else None
