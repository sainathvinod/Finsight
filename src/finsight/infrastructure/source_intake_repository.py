# Implements: V2 FR-126–FR-135/180–183, NFR-087/110, AC-01 — Workflow 2 storage.
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional


_SOURCE_ROLES = frozenset({"BUDGET", "GED"})
_XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


@dataclass(frozen=True, kw_only=True)
class SourceIntakeEvidence:
    evidence_type: str
    evidence_status: str
    ordinal: int = 1
    raw_scalar: Optional[str] = None
    normalized_scalar: Optional[str] = None
    worksheet_name: Optional[str] = None
    cell_reference: Optional[str] = None
    source_row: Optional[int] = None
    source_column: Optional[int] = None
    evidence_id: Optional[str] = None
    parser_profile_version: str = ""
    extraction_profile_version: str = ""
    metadata_policy_version: str = ""


@dataclass(frozen=True, kw_only=True)
class SourceIntakeSource:
    source_role: str
    artifact_id: str
    binding_id: str
    filename: str
    byte_size: int
    sha256: str
    path_hint: str
    selected_actor_id: str
    selected_at: str
    bound_actor_id: str
    bound_at: str
    worksheet_name: str
    upload_status: str
    compatibility_status: str
    extraction_status: str
    structural_issue_count: int = 0
    predecessor_binding_id: Optional[str] = None
    replacement_reason: str = "INITIAL_INTAKE"
    evidence: tuple[SourceIntakeEvidence, ...] = field(default_factory=tuple)


@dataclass(frozen=True, kw_only=True)
class SourceIntakeCommit:
    review_id: str
    candidate_id: str
    idempotency_key: str
    request_hash: str
    summary_id: str
    committed_actor_id: str
    committed_at: str
    selected_month: int
    selected_year: int
    resolved_department_number: Optional[str]
    resolved_department_name: Optional[str]
    department_evidence_status: str
    period_evidence_status: str
    department_match_status: str
    reporting_period_match_status: str
    budget_detail_count: int
    ged_transaction_count: int
    extraction_profile_version: str
    layout_profile_version: str
    safety_policy_version: str
    metadata_policy_version: str
    sources: tuple[SourceIntakeSource, ...]


class SqliteSourceIntakeRepository:
    """Authoritative source-intake persistence with transaction ownership left to the caller."""

    def __init__(self, dal):
        self._dal = dal

    def commit_pair(
        self, value: SourceIntakeCommit | Mapping[str, Any]
    ) -> dict[str, Any]:
        """Append one complete Budget/GED intake pair.

        This method intentionally neither commits nor rolls back. The application
        service must invoke it inside the same Unit of Work as lifecycle and audit
        writes so bindings, metadata, status, and audit remain atomic.
        """

        commit = _coerce_commit(value)
        existing = self._idempotency(commit.review_id, commit.idempotency_key)
        if existing is not None:
            if existing["request_hash"] != commit.request_hash:
                raise ValueError("source-intake idempotency key was reused")
            replay = self._get_summary_by_id(
                commit.review_id, existing["summary_id"]
            )
            if replay is None:
                raise RuntimeError("source-intake idempotency record is orphaned")
            return replay

        sources = {source.source_role: source for source in commit.sources}
        if set(sources) != _SOURCE_ROLES or len(commit.sources) != 2:
            raise ValueError("source intake requires exactly one BUDGET and one GED")
        self._validate_commit(commit, sources)

        binding_ids: dict[str, str] = {}
        for role in ("BUDGET", "GED"):
            source = sources[role]
            artifact_id = self._ensure_artifact(source)
            self._append_binding(commit, source, artifact_id)
            self._append_evidence(commit, source)
            binding_ids[role] = source.binding_id

        predecessor, sequence = self._next_summary(commit)
        summary_hash = _canonical_hash(
            {
                "commit": asdict(commit),
                "predecessor_summary_id": predecessor,
                "summary_sequence": sequence,
            }
        )
        budget = sources["BUDGET"]
        ged = sources["GED"]
        self._dal.conn.execute(
            "INSERT INTO v2_source_intake_summaries("
            "summary_id,review_id,candidate_id,summary_sequence,predecessor_summary_id,"
            "budget_binding_id,ged_binding_id,selected_month,selected_year,"
            "resolved_department_number,resolved_department_name,department_evidence_status,"
            "period_evidence_status,department_match_status,reporting_period_match_status,"
            "budget_filename,ged_filename,budget_worksheet,ged_worksheet,budget_detail_count,"
            "ged_transaction_count,budget_upload_status,budget_compatibility_status,"
            "budget_extraction_status,budget_structural_issue_count,ged_upload_status,"
            "ged_compatibility_status,ged_extraction_status,ged_structural_issue_count,"
            "extraction_profile_version,layout_profile_version,safety_policy_version,"
            "metadata_policy_version,committed_actor_id,committed_at,summary_hash"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                commit.summary_id,
                commit.review_id,
                commit.candidate_id,
                sequence,
                predecessor,
                binding_ids["BUDGET"],
                binding_ids["GED"],
                commit.selected_month,
                commit.selected_year,
                commit.resolved_department_number,
                commit.resolved_department_name,
                commit.department_evidence_status,
                commit.period_evidence_status,
                commit.department_match_status,
                commit.reporting_period_match_status,
                budget.filename,
                ged.filename,
                budget.worksheet_name,
                ged.worksheet_name,
                commit.budget_detail_count,
                commit.ged_transaction_count,
                budget.upload_status,
                budget.compatibility_status,
                budget.extraction_status,
                budget.structural_issue_count,
                ged.upload_status,
                ged.compatibility_status,
                ged.extraction_status,
                ged.structural_issue_count,
                commit.extraction_profile_version,
                commit.layout_profile_version,
                commit.safety_policy_version,
                commit.metadata_policy_version,
                commit.committed_actor_id,
                commit.committed_at,
                summary_hash,
            ),
        )
        self._dal.conn.execute(
            "INSERT INTO v2_source_intake_idempotency("
            "review_id,idempotency_key,request_hash,summary_id,actor_id,committed_at"
            ") VALUES(?,?,?,?,?,?)",
            (
                commit.review_id,
                commit.idempotency_key,
                commit.request_hash,
                commit.summary_id,
                commit.committed_actor_id,
                commit.committed_at,
            ),
        )
        result = self._get_summary_by_id(commit.review_id, commit.summary_id)
        if result is None:
            raise RuntimeError("source-intake summary was not persisted")
        return result

    def get_current_pair(self, review_id: str) -> dict[str, dict[str, Any]]:
        pointer = self._dal.conn.execute(
            "SELECT active_candidate_id FROM v2_review_cycle_pointers WHERE review_id=?",
            (review_id,),
        ).fetchone()
        if pointer is None:
            return {}
        candidate_id = pointer[0]
        if candidate_id is None:
            saved = self._dal.conn.execute(
                "SELECT candidate_id FROM v2_source_intake_summaries "
                "WHERE review_id=? ORDER BY summary_sequence DESC LIMIT 1",
                (review_id,),
            ).fetchone()
            if saved is None:
                return {}
            candidate_id = saved[0]
        rows = self._dal.conn.execute(
            "SELECT h.source_role,b.binding_id,b.artifact_id,b.selected_filename,"
            "a.byte_size,a.sha256,b.path_hint,b.predecessor_binding_id,b.replacement_reason,"
            "b.binding_sequence,b.selected_actor_id,b.selected_at,b.bound_actor_id,b.bound_at,"
            "b.extraction_profile_version,b.layout_profile_version,b.safety_policy_version,"
            "a.media_type,a.file_extension,h.revision "
            "FROM v2_candidate_source_heads h "
            "JOIN v2_source_binding_versions b ON b.binding_id=h.current_binding_id "
            "JOIN v2_source_artifacts a ON a.artifact_id=b.artifact_id "
            "WHERE h.candidate_id=? ORDER BY h.source_role",
            (candidate_id,),
        ).fetchall()
        keys = (
            "source_role",
            "binding_id",
            "artifact_id",
            "filename",
            "byte_size",
            "sha256",
            "path_hint",
            "predecessor_binding_id",
            "replacement_reason",
            "binding_sequence",
            "selected_actor_id",
            "selected_at",
            "bound_actor_id",
            "bound_at",
            "extraction_profile_version",
            "layout_profile_version",
            "safety_policy_version",
            "media_type",
            "file_extension",
            "head_revision",
        )
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            item = dict(zip(keys, row))
            item["review_id"] = review_id
            item["candidate_id"] = candidate_id
            item["evidence"] = self._evidence_for_binding(item["binding_id"])
            result[item["source_role"]] = item
        return result

    def get_summary(self, review_id: str) -> Optional[dict[str, Any]]:
        row = self._dal.conn.execute(
            "SELECT summary_id FROM v2_source_intake_summaries WHERE review_id=? "
            "ORDER BY summary_sequence DESC LIMIT 1",
            (review_id,),
        ).fetchone()
        return self._get_summary_by_id(review_id, row[0]) if row else None

    def _validate_commit(
        self,
        commit: SourceIntakeCommit,
        sources: Mapping[str, SourceIntakeSource],
    ) -> None:
        review = self._dal.conn.execute(
            "SELECT r.selected_month,r.selected_year,p.active_candidate_id "
            "FROM v2_review_cycles r JOIN v2_review_cycle_pointers p "
            "ON p.review_id=r.review_id WHERE r.review_id=?",
            (commit.review_id,),
        ).fetchone()
        if review is None:
            raise ValueError("source intake review does not exist")
        if review[2] != commit.candidate_id:
            raise ValueError("source intake candidate is not active for the review")
        if (int(review[0]), int(review[1])) != (
            commit.selected_month,
            commit.selected_year,
        ):
            raise ValueError("source intake period differs from the persisted review")
        if commit.budget_detail_count < 0 or commit.ged_transaction_count < 0:
            raise ValueError("source record counts cannot be negative")
        for role, source in sources.items():
            if source.source_role != role:
                raise ValueError("source role mapping is inconsistent")
            if source.byte_size < 0 or source.structural_issue_count < 0:
                raise ValueError("source sizes and issue counts cannot be negative")
            if not _is_sha256(source.sha256):
                raise ValueError("source fingerprint must be lowercase SHA-256")
            ordinals: set[tuple[str, int]] = set()
            for evidence in source.evidence:
                if evidence.ordinal <= 0:
                    raise ValueError("metadata evidence ordinal must be positive")
                identity = (evidence.evidence_type, evidence.ordinal)
                if identity in ordinals:
                    raise ValueError("metadata evidence identity must be unique")
                ordinals.add(identity)

    def _ensure_artifact(self, source: SourceIntakeSource) -> str:
        by_id = self._dal.conn.execute(
            "SELECT source_role,byte_size,sha256 FROM v2_source_artifacts "
            "WHERE artifact_id=?",
            (source.artifact_id,),
        ).fetchone()
        if by_id is not None:
            if by_id != (source.source_role, source.byte_size, source.sha256):
                raise ValueError("source artifact ID identifies different bytes")
            return source.artifact_id

        by_fingerprint = self._dal.conn.execute(
            "SELECT artifact_id,byte_size FROM v2_source_artifacts "
            "WHERE source_role=? AND sha256=?",
            (source.source_role, source.sha256),
        ).fetchone()
        if by_fingerprint is not None:
            if int(by_fingerprint[1]) != source.byte_size:
                raise ValueError("source fingerprint has inconsistent byte size")
            return by_fingerprint[0]

        self._dal.conn.execute(
            "INSERT INTO v2_source_artifacts("
            "artifact_id,source_role,first_seen_filename,byte_size,sha256,media_type,"
            "file_extension,first_selected_actor_id,first_selected_at"
            ") VALUES(?,?,?,?,?,?,?,?,?)",
            (
                source.artifact_id,
                source.source_role,
                source.filename,
                source.byte_size,
                source.sha256,
                _XLSX_MEDIA_TYPE,
                ".xlsx",
                source.selected_actor_id,
                source.selected_at,
            ),
        )
        return source.artifact_id

    def _append_binding(
        self,
        commit: SourceIntakeCommit,
        source: SourceIntakeSource,
        artifact_id: str,
    ) -> None:
        head = self._dal.conn.execute(
            "SELECT current_binding_id,revision FROM v2_candidate_source_heads "
            "WHERE candidate_id=? AND source_role=?",
            (commit.candidate_id, source.source_role),
        ).fetchone()
        current_binding = head[0] if head else None
        if source.predecessor_binding_id is not None and (
            source.predecessor_binding_id != current_binding
        ):
            raise ValueError("source binding predecessor is stale")
        predecessor = current_binding
        sequence = int(head[1]) + 1 if head else 1
        self._dal.conn.execute(
            "INSERT INTO v2_source_binding_versions("
            "binding_id,review_id,candidate_id,source_role,artifact_id,selected_filename,"
            "path_hint,predecessor_binding_id,replacement_reason,binding_sequence,"
            "selected_actor_id,selected_at,bound_actor_id,bound_at,extraction_profile_version,"
            "layout_profile_version,safety_policy_version"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                source.binding_id,
                commit.review_id,
                commit.candidate_id,
                source.source_role,
                artifact_id,
                source.filename,
                source.path_hint,
                predecessor,
                source.replacement_reason,
                sequence,
                source.selected_actor_id,
                source.selected_at,
                source.bound_actor_id,
                source.bound_at,
                commit.extraction_profile_version,
                commit.layout_profile_version,
                commit.safety_policy_version,
            ),
        )
        if head is None:
            self._dal.conn.execute(
                "INSERT INTO v2_candidate_source_heads("
                "candidate_id,source_role,current_binding_id,revision,updated_actor_id,updated_at"
                ") VALUES(?,?,?,?,?,?)",
                (
                    commit.candidate_id,
                    source.source_role,
                    source.binding_id,
                    1,
                    source.bound_actor_id,
                    source.bound_at,
                ),
            )
            return
        changed = self._dal.conn.execute(
            "UPDATE v2_candidate_source_heads SET current_binding_id=?,revision=?,"
            "updated_actor_id=?,updated_at=? WHERE candidate_id=? AND source_role=? "
            "AND current_binding_id=? AND revision=?",
            (
                source.binding_id,
                sequence,
                source.bound_actor_id,
                source.bound_at,
                commit.candidate_id,
                source.source_role,
                current_binding,
                int(head[1]),
            ),
        ).rowcount
        if changed != 1:
            raise RuntimeError("source binding head changed concurrently")

    def _append_evidence(
        self, commit: SourceIntakeCommit, source: SourceIntakeSource
    ) -> None:
        for evidence in source.evidence:
            evidence_id = evidence.evidence_id or _evidence_id(
                source.binding_id, evidence.evidence_type, evidence.ordinal
            )
            self._dal.conn.execute(
                "INSERT INTO v2_metadata_evidence_records("
                "evidence_id,review_id,candidate_id,binding_id,source_role,evidence_type,"
                "ordinal,raw_scalar,normalized_scalar,evidence_status,worksheet_name,"
                "cell_reference,source_row,source_column,parser_profile_version,"
                "extraction_profile_version,metadata_policy_version"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    evidence_id,
                    commit.review_id,
                    commit.candidate_id,
                    source.binding_id,
                    source.source_role,
                    evidence.evidence_type,
                    evidence.ordinal,
                    evidence.raw_scalar,
                    evidence.normalized_scalar,
                    evidence.evidence_status,
                    evidence.worksheet_name,
                    evidence.cell_reference,
                    evidence.source_row,
                    evidence.source_column,
                    evidence.parser_profile_version
                    or commit.extraction_profile_version,
                    evidence.extraction_profile_version
                    or commit.extraction_profile_version,
                    evidence.metadata_policy_version
                    or commit.metadata_policy_version,
                ),
            )

    def _next_summary(
        self, commit: SourceIntakeCommit
    ) -> tuple[Optional[str], int]:
        row = self._dal.conn.execute(
            "SELECT summary_id,summary_sequence FROM v2_source_intake_summaries "
            "WHERE review_id=? AND candidate_id=? ORDER BY summary_sequence DESC LIMIT 1",
            (commit.review_id, commit.candidate_id),
        ).fetchone()
        return (row[0], int(row[1]) + 1) if row else (None, 1)

    def _idempotency(
        self, review_id: str, idempotency_key: str
    ) -> Optional[dict[str, Any]]:
        row = self._dal.conn.execute(
            "SELECT request_hash,summary_id,actor_id,committed_at "
            "FROM v2_source_intake_idempotency WHERE review_id=? AND idempotency_key=?",
            (review_id, idempotency_key),
        ).fetchone()
        if row is None:
            return None
        return dict(
            zip(("request_hash", "summary_id", "actor_id", "committed_at"), row)
        )

    def _get_summary_by_id(
        self, review_id: str, summary_id: str
    ) -> Optional[dict[str, Any]]:
        columns = (
            "summary_id",
            "review_id",
            "candidate_id",
            "summary_sequence",
            "predecessor_summary_id",
            "budget_binding_id",
            "ged_binding_id",
            "selected_month",
            "selected_year",
            "resolved_department_number",
            "resolved_department_name",
            "department_evidence_status",
            "period_evidence_status",
            "department_match_status",
            "reporting_period_match_status",
            "budget_filename",
            "ged_filename",
            "budget_worksheet",
            "ged_worksheet",
            "budget_detail_count",
            "ged_transaction_count",
            "budget_upload_status",
            "budget_compatibility_status",
            "budget_extraction_status",
            "budget_structural_issue_count",
            "ged_upload_status",
            "ged_compatibility_status",
            "ged_extraction_status",
            "ged_structural_issue_count",
            "extraction_profile_version",
            "layout_profile_version",
            "safety_policy_version",
            "metadata_policy_version",
            "committed_actor_id",
            "committed_at",
            "summary_hash",
        )
        row = self._dal.conn.execute(
            f"SELECT {','.join(columns)} FROM v2_source_intake_summaries "
            "WHERE review_id=? AND summary_id=?",
            (review_id, summary_id),
        ).fetchone()
        return dict(zip(columns, row)) if row else None

    def _evidence_for_binding(self, binding_id: str) -> list[dict[str, Any]]:
        columns = (
            "evidence_id",
            "evidence_type",
            "ordinal",
            "raw_scalar",
            "normalized_scalar",
            "evidence_status",
            "worksheet_name",
            "cell_reference",
            "source_row",
            "source_column",
            "parser_profile_version",
            "extraction_profile_version",
            "metadata_policy_version",
        )
        rows = self._dal.conn.execute(
            f"SELECT {','.join(columns)} FROM v2_metadata_evidence_records "
            "WHERE binding_id=? ORDER BY evidence_type,ordinal",
            (binding_id,),
        ).fetchall()
        return [dict(zip(columns, row)) for row in rows]


def _coerce_commit(
    value: SourceIntakeCommit | Mapping[str, Any]
) -> SourceIntakeCommit:
    if isinstance(value, SourceIntakeCommit):
        return value
    data = dict(value)
    data["sources"] = tuple(_coerce_source(item) for item in data["sources"])
    return SourceIntakeCommit(**data)


def _coerce_source(
    value: SourceIntakeSource | Mapping[str, Any]
) -> SourceIntakeSource:
    if isinstance(value, SourceIntakeSource):
        return value
    data = dict(value)
    data["evidence"] = tuple(
        item
        if isinstance(item, SourceIntakeEvidence)
        else SourceIntakeEvidence(**dict(item))
        for item in data.get("evidence", ())
    )
    return SourceIntakeSource(**data)


def _is_sha256(value: str) -> bool:
    return (
        len(value) == 64
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _canonical_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _evidence_id(binding_id: str, evidence_type: str, ordinal: int) -> str:
    payload = f"{binding_id}\0{evidence_type}\0{ordinal}".encode("utf-8")
    return "evi_" + hashlib.sha256(payload).hexdigest()[:32]
