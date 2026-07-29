"""Developer-only helpers for the bounded Workflow 2 demo profile.

The approved synthetic fixtures are the only workbooks selected automatically
by the developer launcher and screenshot capture. Production composition never
imports this module.
"""
from __future__ import annotations

from pathlib import Path

from finsight.domain.source_intake import SourceRole

from workflow1_demo_support import build_workflow1_demo_services


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIRECTORY = (
    REPOSITORY_ROOT
    / "initiatives"
    / "configurable-rule-engine-v2"
    / "fixtures"
)
BUDGET_FIXTURE = FIXTURE_DIRECTORY / "Sample_Budget_Report.xlsx"
GED_FIXTURE = FIXTURE_DIRECTORY / "Sample_GED_Report.xlsx"


def require_approved_fixtures() -> tuple[Path, Path]:
    """Return the approved fixtures after failing clearly if either is absent."""

    missing = [
        path.name
        for path in (BUDGET_FIXTURE, GED_FIXTURE)
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(
            "Workflow 2 approved fixture(s) are missing: " + ", ".join(missing)
        )
    return BUDGET_FIXTURE, GED_FIXTURE


def create_may_2026_intake(window, controller):
    """Create a fresh May 2026 Draft and open its Workflow 2 upload surface."""

    review = controller.create_managed_review(
        5,
        2026,
        "workflow2-demo-create",
    )
    window._show_source_intake(review)
    return window.view("source_intake")


def select_approved_pair(intake) -> None:
    """Select both approved fixture paths without committing either binding."""

    budget, ged = require_approved_fixtures()
    intake.select_source_path(SourceRole.BUDGET, str(budget))
    intake.select_source_path(SourceRole.GED, str(ged))


__all__ = [
    "BUDGET_FIXTURE",
    "FIXTURE_DIRECTORY",
    "GED_FIXTURE",
    "build_workflow1_demo_services",
    "create_may_2026_intake",
    "require_approved_fixtures",
    "select_approved_pair",
]
