"""Encrypted SQLite adapter for the Stage 2 private Ask Fin audit."""
from __future__ import annotations

import json
import uuid
from typing import Any, Mapping


class PrivateAskFinAuditRepositorySqlite:
    """Append/read only; the adapter exposes no update operation."""

    def __init__(self, dal, unit_of_work, id_factory=None):
        self._dal = dal
        self._uow = unit_of_work
        self._id = id_factory or (lambda: uuid.uuid4().hex)

    def append(self, value: Mapping[str, Any]) -> str:
        interaction_id = "askfin_" + self._id()
        with self._uow.atomic():
            self._dal.conn.execute(
                "INSERT INTO v2_private_ask_fin_interactions("
                "interaction_id,user_id,review_id,validation_run_id,scope_json,"
                "mode,question,retrieved_records_json,provider,model,model_version,"
                "prompt_version,response,citations_json,refusal_trigger,latency_ms,"
                "failure_state,status,grounding_review_id,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    interaction_id,
                    value["user_id"],
                    value["review_id"] or None,
                    value.get("validation_run_id"),
                    self._json(value.get("scope")),
                    value["mode"],
                    value["question"],
                    self._json(value.get("retrieved_records") or []),
                    value["provider"],
                    value["model"],
                    value["model_version"],
                    value["prompt_version"],
                    value["response"],
                    self._json(value.get("citations") or []),
                    value.get("refusal_trigger"),
                    value.get("latency_ms"),
                    value.get("failure_state"),
                    value["status"],
                    value.get("grounding_review_id") or None,
                    value["timestamp"],
                ),
            )
        return interaction_id

    def list_for_review(self, review_id: str) -> list[dict[str, Any]]:
        where = "review_id=?" if review_id else "review_id IS NULL"
        parameters = (review_id,) if review_id else ()
        rows = self._dal.conn.execute(
            "SELECT interaction_id,user_id,review_id,validation_run_id,scope_json,"
            "mode,question,retrieved_records_json,provider,model,model_version,"
            "prompt_version,response,citations_json,refusal_trigger,latency_ms,"
            "failure_state,status,grounding_review_id,created_at "
            f"FROM v2_private_ask_fin_interactions WHERE {where} "
            "ORDER BY created_at,interaction_id",
            parameters,
        ).fetchall()
        keys = (
            "interaction_id",
            "user_id",
            "review_id",
            "validation_run_id",
            "scope",
            "mode",
            "question",
            "retrieved_records",
            "provider",
            "model",
            "model_version",
            "prompt_version",
            "response",
            "citations",
            "refusal_trigger",
            "latency_ms",
            "failure_state",
            "status",
            "grounding_review_id",
            "timestamp",
        )
        output = []
        for row in rows:
            item = dict(zip(keys, row))
            for name in ("scope", "retrieved_records", "citations"):
                item[name] = json.loads(item[name]) if item[name] else None
            output.append(item)
        return output

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
