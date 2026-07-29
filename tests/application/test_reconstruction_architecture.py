# Verifies: Phase 6.4c — architecture/fitness guards for reconstruction & recovery.
# Reconstruction stays pure application (no Qt/sqlite/AI), performs NO durable write except the source
# path re-bind + its audit (no normalized-row persistence, no generation/promotion/supersession
# production behavior). Workflows 1 and 2 add only their separately governed V2 migrations.
import os
import re

from finsight.infrastructure.migrations.runner import MIGRATIONS

SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src", "finsight")


def _read(rel):
    with open(os.path.join(SRC, rel), encoding="utf-8") as fh:
        return fh.read()


def _imports(rel):
    return re.findall(r'^\s*(?:from|import)\s+([\w\.]+)', _read(rel), re.M)


def _forbid_imports(rel, forbidden):
    for mod in _imports(rel):
        for bad in forbidden:
            assert not (mod == bad or mod.startswith(bad + ".")), "%s imports %s" % (rel, mod)


def test_reconstruction_is_pure_application():
    _forbid_imports("application/reconstruction.py",
                    ("PySide6", "sqlite3", "finsight.infrastructure", "finsight.application.ai",
                     "hashlib", "openpyxl"))


def test_reconstruction_performs_no_generation_or_result_writes():
    src = _read("application/reconstruction.py")
    # The ONLY durable writes are the source-binding path re-bind (upsert) + audit. No results,
    # no normalized rows, no generation lifecycle.
    for tok in ("finding_repo", "run_repo.save", "review_generations", "generation_supersessions",
                "export_artifacts", "def promote", "def supersede", "normalized", "INSERT INTO findings",
                "INSERT INTO rule_runs"):
        assert tok not in src, tok
    assert "source_binding_repo" in src or "self._bindings" in src   # binding path-hint write exists


def test_schema_head_includes_stage2_private_ask_fin_audit():
    assert len(MIGRATIONS) == 14
    assert [m[0] for m in MIGRATIONS] == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
    ]
    assert MIGRATIONS[-1][1] == "private_ask_fin_audit"


def test_recovery_banner_has_no_repository_ai_or_file_io():
    _forbid_imports("delivery/desktop/components/recovery_banner.py",
                    ("finsight.infrastructure", "finsight.application.ai", "hashlib", "sqlite3"))


def test_delivery_workflow_view_does_not_read_raw_files():
    src = _read("delivery/desktop/views/workflow_view.py")
    # It may open a file PICKER (QFileDialog) but never reads bytes / hashes / touches storage.
    for tok in ("hashlib", "FileHasher", "sqlite3", "open("):
        assert tok not in src, tok
