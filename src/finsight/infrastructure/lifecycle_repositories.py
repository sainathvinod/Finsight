# SQLite adapters for the lifecycle persistence ports (ADR-011/012/014/015). Phase 6.4b.
#
# Convention (matches the rest of the DAL): repository methods execute statements but DO NOT commit —
# the application wraps writes in the shared SqliteUnitOfWork so a later service can atomically compose
# several writes + an audit event in ONE transaction (e.g. promotion = append supersession + move
# published pointer + audit). Nothing here implements such a business workflow; these are primitives.
#
# Enforcement split (ADR-011 §9): stable STRUCTURAL invariants are enforced by the schema/triggers
# (migration 0003). Complex SEMANTIC rules that need cross-row lookups are ALSO pre-validated here for
# clear errors; every write funnels rejections into a single LifecycleConstraintError (structural
# violations that reach the DB surface as sqlite3.IntegrityError and are wrapped to the same type).
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from typing import List, Optional

from finsight.domain.lifecycle import (
    SourceBinding, ReviewGeneration, GenerationSupersession, ExportArtifact,
    AnalyticalState, CreationReason, GenerationDisposition, IntakeStage, CycleDisposition,
)


class LifecycleConstraintError(RuntimeError):
    """A lifecycle persistence invariant was violated (repository pre-check or DB constraint/trigger)."""


@contextmanager
def _as_constraint_error():
    try:
        yield
    except sqlite3.IntegrityError as exc:
        raise LifecycleConstraintError(str(exc)) from exc


class SourceBindingRepoSqlite:
    def __init__(self, dal):
        self.dal = dal

    def upsert(self, b: SourceBinding) -> None:
        """Low-level unguarded write (INSERT or REPLACE identity+path). Prefer bind() on the workflow
        paths so a trusted source identity can never be silently overwritten."""
        with _as_constraint_error():
            self.dal.conn.execute(
                "INSERT INTO source_bindings(cycle_id,document_type,last_known_path,source_fingerprint,"
                "selected_at,actor) VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(cycle_id,document_type) DO UPDATE SET "
                "last_known_path=excluded.last_known_path, source_fingerprint=excluded.source_fingerprint, "
                "selected_at=excluded.selected_at, actor=excluded.actor",
                (b.cycle_id, b.document_type, b.last_known_path, b.source_fingerprint, b.selected_at,
                 b.actor))

    def bind(self, b: SourceBinding) -> None:
        """Guarded binding write with explicit semantics (Phase 6.4cA):
        - INITIAL_BIND: no existing binding -> record path + identity.
        - PATH_REBIND: existing binding with the SAME source_fingerprint -> update the path hint only.
        - SOURCE_CHANGE: existing binding with a DIFFERENT fingerprint -> REFUSED. A changed source
          must never become current through a generic write; it requires explicit re-verification.
        A trusted source identity (verified/analyzed review) is thus never silently replaced."""
        existing = self.get(b.cycle_id, b.document_type)
        if existing is not None and existing.source_fingerprint != b.source_fingerprint:
            raise LifecycleConstraintError(
                "refusing to overwrite the trusted source identity of %s/%s (changed source requires "
                "explicit re-verification)" % (b.cycle_id, b.document_type))
        self.upsert(b)

    def get(self, cycle_id: str, document_type: str) -> Optional[SourceBinding]:
        r = self.dal.conn.execute(
            "SELECT cycle_id,document_type,last_known_path,source_fingerprint,selected_at,actor "
            "FROM source_bindings WHERE cycle_id=? AND document_type=?",
            (cycle_id, document_type)).fetchone()
        return SourceBinding(*r) if r else None

    def list_for_cycle(self, cycle_id: str) -> List[SourceBinding]:
        rows = self.dal.conn.execute(
            "SELECT cycle_id,document_type,last_known_path,source_fingerprint,selected_at,actor "
            "FROM source_bindings WHERE cycle_id=? ORDER BY document_type", (cycle_id,)).fetchall()
        return [SourceBinding(*r) for r in rows]


_GEN_COLUMNS = ("generation_id,cycle_id,sequence_number,analytical_state,creation_reason,"
                "based_on_generation_id,verification_basis_generation_id,verified_fingerprint,"
                "extractor_version,verification_actor,verified_at,created_by,created_at,"
                "generation_disposition,legacy_metadata_incomplete")


def _gen_from_row(r) -> ReviewGeneration:
    return ReviewGeneration(
        generation_id=r[0], cycle_id=r[1], sequence_number=r[2],
        analytical_state=AnalyticalState(r[3]), creation_reason=CreationReason(r[4]),
        based_on_generation_id=r[5], verification_basis_generation_id=r[6],
        verified_fingerprint=r[7], extractor_version=r[8], verification_actor=r[9],
        verified_at=r[10], created_by=r[11], created_at=r[12],
        generation_disposition=GenerationDisposition(r[13]), legacy_metadata_incomplete=bool(r[14]))


class ReviewGenerationRepoSqlite:
    def __init__(self, dal):
        self.dal = dal

    def insert(self, g: ReviewGeneration) -> None:
        # Repo-level SEMANTIC pre-checks (clear errors); triggers/constraints are the backstop.
        self._require_same_cycle(g.based_on_generation_id, g.cycle_id, "lineage parent")
        self._require_same_cycle(g.verification_basis_generation_id, g.cycle_id, "verification basis")
        with _as_constraint_error():
            self.dal.conn.execute(
                "INSERT INTO review_generations(%s) VALUES(%s)" % (_GEN_COLUMNS, ",".join("?" * 15)),
                (g.generation_id, g.cycle_id, int(g.sequence_number), g.analytical_state.value,
                 g.creation_reason.value, g.based_on_generation_id, g.verification_basis_generation_id,
                 g.verified_fingerprint, g.extractor_version, g.verification_actor, g.verified_at,
                 g.created_by, g.created_at, g.generation_disposition.value,
                 1 if g.legacy_metadata_incomplete else 0))

    def _require_same_cycle(self, generation_id: Optional[str], cycle_id: str, label: str) -> None:
        if generation_id is None:
            return
        ref = self.get(generation_id)
        if ref is None or ref.cycle_id != cycle_id:
            raise LifecycleConstraintError("%s %r must belong to cycle %r" % (label, generation_id, cycle_id))

    def get(self, generation_id: str) -> Optional[ReviewGeneration]:
        r = self.dal.conn.execute(
            "SELECT %s FROM review_generations WHERE generation_id=?" % _GEN_COLUMNS,
            (generation_id,)).fetchone()
        return _gen_from_row(r) if r else None

    def list_for_cycle(self, cycle_id: str) -> List[ReviewGeneration]:
        rows = self.dal.conn.execute(
            "SELECT %s FROM review_generations WHERE cycle_id=? ORDER BY sequence_number" % _GEN_COLUMNS,
            (cycle_id,)).fetchall()
        return [_gen_from_row(r) for r in rows]

    def next_sequence_number(self, cycle_id: str) -> int:
        r = self.dal.conn.execute(
            "SELECT COALESCE(MAX(sequence_number),0) FROM review_generations WHERE cycle_id=?",
            (cycle_id,)).fetchone()
        return int(r[0]) + 1

    def working_generation(self, cycle_id: str) -> Optional[ReviewGeneration]:
        return self._pointer(cycle_id, "working_generation_id")

    def published_generation(self, cycle_id: str) -> Optional[ReviewGeneration]:
        return self._pointer(cycle_id, "published_generation_id")

    def _pointer(self, cycle_id: str, column: str) -> Optional[ReviewGeneration]:
        r = self.dal.conn.execute(
            "SELECT %s FROM cycles WHERE cycle_id=?" % column, (cycle_id,)).fetchone()
        return self.get(r[0]) if r and r[0] else None


class GenerationSupersessionRepoSqlite:
    """Append-only: no update/delete methods are provided; the DB blocks them structurally."""
    def __init__(self, dal):
        self.dal = dal

    def append(self, s: GenerationSupersession) -> None:
        if self.get_successor(s.prior_generation_id) is not None:
            raise LifecycleConstraintError(
                "generation %r has already been superseded" % s.prior_generation_id)
        with _as_constraint_error():
            self.dal.conn.execute(
                "INSERT INTO generation_supersessions(prior_generation_id,successor_generation_id,"
                "superseded_at,actor,reason) VALUES(?,?,?,?,?)",
                (s.prior_generation_id, s.successor_generation_id, s.superseded_at, s.actor, s.reason))

    def get_successor(self, prior_generation_id: str) -> Optional[GenerationSupersession]:
        r = self.dal.conn.execute(
            "SELECT prior_generation_id,successor_generation_id,superseded_at,actor,reason "
            "FROM generation_supersessions WHERE prior_generation_id=?",
            (prior_generation_id,)).fetchone()
        return GenerationSupersession(*r) if r else None

    def history_for_cycle(self, cycle_id: str) -> List[GenerationSupersession]:
        rows = self.dal.conn.execute(
            "SELECT s.prior_generation_id,s.successor_generation_id,s.superseded_at,s.actor,s.reason "
            "FROM generation_supersessions s JOIN review_generations g "
            "ON g.generation_id=s.prior_generation_id WHERE g.cycle_id=? "
            "ORDER BY s.superseded_at, s.prior_generation_id", (cycle_id,)).fetchall()
        return [GenerationSupersession(*r) for r in rows]


class ExportArtifactRepoSqlite:
    """Append-only: export identity is immutable; there is no overwrite method."""
    def __init__(self, dal):
        self.dal = dal

    def insert(self, a: ExportArtifact) -> None:
        with _as_constraint_error():
            self.dal.conn.execute(
                "INSERT INTO export_artifacts(export_id,cycle_id,generation_id,run_id,export_path,"
                "export_fingerprint,created_at,actor) VALUES(?,?,?,?,?,?,?,?)",
                (a.export_id, a.cycle_id, a.generation_id, a.run_id, a.export_path,
                 a.export_fingerprint, a.created_at, a.actor))

    def get(self, export_id: str) -> Optional[ExportArtifact]:
        r = self.dal.conn.execute(
            "SELECT export_id,cycle_id,generation_id,run_id,export_path,export_fingerprint,created_at,actor "
            "FROM export_artifacts WHERE export_id=?", (export_id,)).fetchone()
        return ExportArtifact(*r) if r else None

    def list_for_generation(self, generation_id: str) -> List[ExportArtifact]:
        return self._list("generation_id", generation_id)

    def list_for_cycle(self, cycle_id: str) -> List[ExportArtifact]:
        return self._list("cycle_id", cycle_id)

    def _list(self, column: str, value: str) -> List[ExportArtifact]:
        rows = self.dal.conn.execute(
            "SELECT export_id,cycle_id,generation_id,run_id,export_path,export_fingerprint,created_at,actor "
            "FROM export_artifacts WHERE %s=? ORDER BY created_at, export_id" % column,
            (value,)).fetchall()
        return [ExportArtifact(*r) for r in rows]


class CycleLifecycleRepoSqlite:
    """Cycle-level lifecycle primitives. Enum validation for the ALTER-added TEXT columns lives here
    (SQLite cannot add a CHECK via ALTER); same-cycle pointer + not-superseded is enforced by trigger."""
    def __init__(self, dal):
        self.dal = dal

    def set_working_generation(self, cycle_id: str, generation_id: Optional[str]) -> None:
        with _as_constraint_error():
            self.dal.conn.execute("UPDATE cycles SET working_generation_id=? WHERE cycle_id=?",
                                  (generation_id, cycle_id))

    def set_published_generation(self, cycle_id: str, generation_id: Optional[str]) -> None:
        with _as_constraint_error():
            self.dal.conn.execute("UPDATE cycles SET published_generation_id=? WHERE cycle_id=?",
                                  (generation_id, cycle_id))

    def set_intake_stage(self, cycle_id: str, stage) -> None:
        value = stage.value if isinstance(stage, IntakeStage) else IntakeStage(stage).value
        self.dal.conn.execute("UPDATE cycles SET intake_stage=? WHERE cycle_id=?", (value, cycle_id))

    def set_disposition(self, cycle_id: str, disposition) -> None:
        value = (disposition.value if isinstance(disposition, CycleDisposition)
                 else CycleDisposition(disposition).value)
        self.dal.conn.execute("UPDATE cycles SET disposition=? WHERE cycle_id=?", (value, cycle_id))

    def pointers(self, cycle_id: str):
        """(intake_stage, disposition, working_generation_id, published_generation_id) or None."""
        r = self.dal.conn.execute(
            "SELECT intake_stage,disposition,working_generation_id,published_generation_id "
            "FROM cycles WHERE cycle_id=?", (cycle_id,)).fetchone()
        return tuple(r) if r else None
