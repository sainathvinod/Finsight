# Implements: FR-001, FR-003, FR-010, F-02-02 (FileFingerprinter: sha256 provenance; read-only, never mutates)
from __future__ import annotations
import hashlib, os
from typing import Any, Dict

class FileHasher:
    def probe(self, path: str) -> Dict[str, Any]:
        name = os.path.basename(path)
        if not os.path.isfile(path):
            return {"exists": False, "sha256": None, "size": 0, "name": name}
        h = hashlib.sha256(); size = 0
        with open(path, "rb") as fh:            # read-only; source is never written
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk); size += len(chunk)
        return {"exists": True, "sha256": h.hexdigest(), "size": size, "name": name}
