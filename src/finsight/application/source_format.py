# Implements: FR-001, FR-007 — the SINGLE authoritative source-format policy (Phase 6.4cA).
#
# One definition, shared by intake validation, the upload/locate file dialogs, moved-source
# classification, reconstruction, and user guidance. There must be no separate extension literals in
# delivery vs application code — recovery must accept exactly what intake legitimately accepts.
#
# TRUTH over claim: the reader is ExcelReader -> openpyxl.load_workbook, which parses the Office Open
# XML family only and CANNOT read legacy BIFF `.xls`. The specs name only `.xlsx` (PLAN-F-02-02); no
# requirement authorizes `.xls`. So `.xlsx` is the authoritative accepted format; the prior UI claim
# of `.xls` was false and is corrected to match reality (per the Phase 6.4cA directive).
from __future__ import annotations
import os

# Accepted source extensions (lowercase). openpyxl also parses `.xlsm`, but the product neither claims
# nor tests macro workbooks, so the declared+offered+accepted set is `.xlsx` only — kept consistent
# everywhere by importing from here.
SUPPORTED_EXTENSIONS = (".xlsx",)

# Qt file-dialog filter (upload + locate). Derived from SUPPORTED_EXTENSIONS so it can never drift.
QT_FILE_FILTER = "Excel workbook (%s);;All files (*)" % " ".join("*" + e for e in SUPPORTED_EXTENSIONS)

# Human-facing guidance shown on upload fields.
ACCEPTED_LABEL = "Accepted: " + ", ".join(SUPPORTED_EXTENSIONS)


def is_supported(path: str) -> bool:
    """True iff the path's extension is an accepted source workbook format."""
    return os.path.splitext(path or "")[1].lower() in SUPPORTED_EXTENSIONS
