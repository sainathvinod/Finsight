# Verifies: FinSight R1 traceability standard (Phase 6.4cB+). Every PRINCIPAL production module must
# carry a structural traceability header so a reviewer/auditor can map code to approved product intent
# without reverse-engineering it. This checker validates OBJECTIVE STRUCTURE only (presence of an
# "# Implements:" header + a purpose/responsibility line, and a trust/lifecycle note for trust-critical
# modules) — never subjective prose. It does not validate identifier correctness (that requires the
# spec/PO); it guards against headers going missing on new/materially-modified principal files.
import os

import pytest

SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src", "finsight")

# Principal production modules that MUST carry a traceability header. Grows as the bounded backfill
# (Milestone 7) confirms identifiers for the remaining feature views. New/materially-modified
# trust-critical modules are added here as they are authored.
PRINCIPAL = [
    "app.py",
    "application/transition_engine.py", "application/orchestrator.py", "application/workflow.py",
    "application/reconstruction.py", "application/review_working_set.py", "application/review_session.py",
    "application/source_format.py", "application/verification.py", "application/analysis.py",
    "application/pipeline.py", "application/lifecycle_ports.py",
    "domain/lifecycle.py",
    "infrastructure/persistence.py", "infrastructure/lifecycle_repositories.py",
    "infrastructure/migrations/m0001_baseline.py", "infrastructure/migrations/m0002_ai_platform.py",
    "infrastructure/migrations/m0003_review_lifecycle.py",
    "delivery/desktop/controllers/app_controller.py",
    "delivery/desktop/views/workflow_view.py",
    "delivery/desktop/components/recovery_banner.py",
]

# Modules authored/backfilled to the FULL Phase 6.4cB traceability standard: they must carry the
# richer header (Implements + Product purpose/System responsibility + a Trust/lifecycle/privacy note).
# Pre-existing modules retain their older "# Implements: <IDs> (<desc>)" headers until the Milestone 7
# bounded backfill upgrades them with PO-confirmed identifiers (do not churn stable files for prose).
NEW_STANDARD = {
    "application/review_working_set.py", "application/review_session.py",
    "application/lifecycle_ports.py", "infrastructure/lifecycle_repositories.py",
    "delivery/desktop/controllers/app_controller.py", "delivery/desktop/views/workflow_view.py",
    "delivery/desktop/components/recovery_banner.py",
}


def _head(rel, n=22):
    with open(os.path.join(SRC, rel), encoding="utf-8") as fh:
        return "".join(fh.readline() for _ in range(n))


@pytest.mark.parametrize("rel", PRINCIPAL)
def test_principal_module_has_implements_header(rel):
    # Objective structural minimum for every principal module.
    assert "# Implements:" in _head(rel), \
        "%s is missing an '# Implements:' traceability header" % rel


@pytest.mark.parametrize("rel", sorted(NEW_STANDARD))
def test_new_standard_module_has_full_header(rel):
    low = _head(rel).lower()
    assert "# implements:" in low, "%s missing '# Implements:'" % rel
    assert ("purpose" in low or "responsibility" in low), \
        "%s must state a Product purpose / System responsibility" % rel
    assert any(tok in low for tok in ("trust", "lifecycle", "privacy", "determinism", "constraint")), \
        "%s must document a trust/lifecycle/privacy/determinism constraint" % rel


def test_new_standard_is_subset_of_principal():
    assert NEW_STANDARD.issubset(set(PRINCIPAL))
