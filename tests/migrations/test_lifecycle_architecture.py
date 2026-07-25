# Verifies: Phase 6.4b — architecture/fitness guards for the lifecycle persistence layer.
# The domain records and application ports stay pure (no Qt/sqlite/AI); the migration layer is
# schema + honest backfill ONLY (no generation business workflow: no promotion/supersession/
# reconstruction); and NO normalized workbook rows are ever persisted.
import os
import re
import sqlite3
import tempfile

from finsight.infrastructure.migrations.runner import run_migrations

SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src", "finsight")


def _read(rel):
    with open(os.path.join(SRC, rel), encoding="utf-8") as fh:
        return fh.read()


def _imports(rel):
    # actual import targets only — comments that MENTION a module do not count as a dependency
    return re.findall(r'^\s*(?:from|import)\s+([\w\.]+)', _read(rel), re.M)


def _forbid(rel, forbidden):
    for mod in _imports(rel):
        for bad in forbidden:
            assert not (mod == bad or mod.startswith(bad + ".")), "%s imports %s" % (rel, mod)


def test_domain_lifecycle_records_are_pure():
    _forbid("domain/lifecycle.py",
            ("PySide6", "sqlite3", "finsight.application", "finsight.infrastructure",
             "finsight.delivery", "openpyxl"))


def test_application_lifecycle_ports_have_no_qt_sqlite_or_ai():
    _forbid("application/lifecycle_ports.py",
            ("PySide6", "sqlite3", "finsight.infrastructure", "finsight.application.ai"))


def test_lifecycle_repositories_have_no_qt_or_ai_dependency():
    _forbid("infrastructure/lifecycle_repositories.py",
            ("PySide6", "finsight.application.ai", "finsight.infrastructure.ai"))
    assert "make_finding" not in _read("infrastructure/lifecycle_repositories.py")


def test_migration_layer_implements_no_generation_business_workflow():
    src = _read("infrastructure/migrations/m0003_review_lifecycle.py")
    # Schema + backfill only — the migration must NOT contain promotion/supersession/reconstruction
    # workflow logic, and must not depend on the repositories or wire production behavior.
    for tok in ("def promote", "def supersede", "def reconstruct",
                "lifecycle_repositories", "def analyze", "def verify"):
        assert tok not in src
    # It does not append any supersession or write a source binding during migration.
    assert "INSERT INTO generation_supersessions" not in src
    assert "INSERT INTO source_bindings" not in src


def test_migration_persists_no_normalized_workbook_rows():
    conn = sqlite3.connect(os.path.join(tempfile.mkdtemp(), "fs.db"))
    run_migrations(conn)
    new_tables = {"source_bindings", "review_generations", "generation_supersessions",
                  "export_artifacts", "migration_diagnostics"}
    for table in new_tables:
        cols = list(conn.execute("PRAGMA table_info(%s)" % table))
        names = {c[1].lower() for c in cols}
        types = {(c[2] or "").upper() for c in cols}
        assert "BLOB" not in types                                  # no workbook bytes
        assert not (names & {"rows", "normalized", "normalized_rows", "workbook", "cells", "data_rows"})


def test_lifecycle_tables_reference_only_identity_not_source_bytes():
    # source_bindings stores a path HINT + fingerprint, never the bytes/rows (ADR-012).
    conn = sqlite3.connect(os.path.join(tempfile.mkdtemp(), "fs.db"))
    run_migrations(conn)
    cols = {c[1] for c in conn.execute("PRAGMA table_info(source_bindings)")}
    assert cols == {"cycle_id", "document_type", "last_known_path", "source_fingerprint",
                    "selected_at", "actor"}
