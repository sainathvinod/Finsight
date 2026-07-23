# Implements: F-02-02  (ADR-002 core-owned ports; ADR-004 DAL owns transactions; ADR-005 audit port)
from __future__ import annotations
from typing import Protocol, List, Dict, Any, Optional, ContextManager

class Clock(Protocol):
    def now(self) -> str: ...  # ISO timestamp, injected (ADR-003: no wall-clock in domain)

class DocumentReader(Protocol):
    def read(self, path: str, doc_type: str) -> List[Dict[str, Any]]: ...  # rows with _source refs

class FileFingerprinter(Protocol):
    def probe(self, path: str) -> Dict[str, Any]: ...  # {exists, sha256, size, name} - read-only

class UnitOfWork(Protocol):
    def atomic(self) -> ContextManager[None]: ...  # all-or-nothing transition (ADR-004; NFR-005/057)

class AuditEventPort(Protocol):
    def emit(self, cycle_id: str, action: str, actor: str, detail: Dict[str, Any]) -> None: ...

class FindingsCommandPort(Protocol):
    def add(self, finding: Any) -> None: ...          # wired ONLY to rules/engine (ADR-007)

class FindingsQueryPort(Protocol):
    def list(self, cycle_id: str) -> List[Dict[str, Any]]: ...  # read-only; the side AI/delivery hold

class ReviewCycleRepo(Protocol):
    def save(self, cycle: Any) -> None: ...
    def get(self, cycle_id: str) -> Any: ...

class IngestedFileRepo(Protocol):
    def save(self, f: Any) -> None: ...
    def list(self, cycle_id: str) -> List[Dict[str, Any]]: ...

class RuleRunRepo(Protocol):
    def save(self, run: Dict[str, Any]) -> None: ...
    def get_by_cycle(self, cycle_id: str) -> Optional[Dict[str, Any]]: ...

class ConfigRepo(Protocol):
    def save(self, cfg: Dict[str, Any]) -> None: ...
    def active(self) -> Dict[str, Any]: ...
