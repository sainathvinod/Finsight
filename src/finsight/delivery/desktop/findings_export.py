# Phase 5.2 — deterministic findings CSV export (pure). Formats already-loaded FindingView objects
# into a CSV string. Contains ONLY deterministic reviewer fields — never AI explanations, prompts,
# model responses, raw evidence blobs, or fabricated data. No repository access, no I/O (the caller
# writes the file, following the existing export-in-view pattern).
from __future__ import annotations
import csv
import io
from typing import List

# Canonical, deterministic reviewer fields. Account/rule NAMES are intentionally NOT columns: the
# extraction pipeline does not retain account names in normalized data and there is no runtime
# rule-name source, so name columns would be misleading always-empty fields (Phase 5.4 finding).
_HEADERS = ["Finding ID", "Period", "Account", "Rule", "Severity", "Type", "State",
            "Source references"]


def findings_to_csv(findings: List) -> str:
    """Deterministic CSV for the given findings, in the order supplied by the caller."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(_HEADERS)
    for f in findings:
        writer.writerow([
            f.id, f.period, f.account, f.rule_id, f.severity, f.finding_type, f.state,
            "; ".join(f.source_refs),
        ])
    return buf.getvalue()
