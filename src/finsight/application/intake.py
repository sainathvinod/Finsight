# Implements: FR-001, FR-003, FR-010, FR-007, NFR-012, NFR-062, F-02-02 (provenance + safe-rejection)
from __future__ import annotations
import os
from typing import Dict, List, Tuple
from finsight.domain.ingest import IngestedFile

def build_provenance(cycle, paths_by_type: Dict[str, str], hasher, clock, actor: str) -> Tuple[List[IngestedFile], List[str]]:
    # Read-only: hashes source bytes; never writes/modifies the source file (AC-2).
    files: List[IngestedFile] = []
    missing: List[str] = []
    period = cycle.month + " " + cycle.year
    for doc_type, path in paths_by_type.items():
        probe = hasher.probe(path)
        if not probe["exists"]:
            missing.append(doc_type)
            continue
        files.append(IngestedFile(cycle.cycle_id, doc_type, probe["name"], probe["sha256"],
                                  probe["size"], clock.now(), actor, period))
    return files, missing
