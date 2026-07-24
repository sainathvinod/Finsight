# Implements: Phase 4C.4, FR-099 (AI answer citation) — deterministic ResponseValidator.
#
# Provider output is UNTRUSTED input. The validator is pure, deterministic, provider-independent, and
# fail-closed: it REJECTS malformed output rather than repairing it. It never infers missing fields,
# coerces types, extracts JSON from prose, removes unexpected fields, invents citations, or silently
# deduplicates. Rules are selected by schema version; unknown versions are rejected.
#
# It raises ResponseFormatError carrying a NON-SENSITIVE machine `code` only — never the raw provider
# text, the answer text, or any prompt/original value (ADR-009/ADR-010).
from __future__ import annotations
import json
from typing import List, Optional

from finsight.application.ai.contracts import (
    DEFAULT_SCHEMA_VERSION, ResponseValidationLimits, ValidatedResponse,
)
from finsight.application.ai.errors import ResponseFormatError

_REQUIRED_FIELDS = frozenset({"answer_text", "unable_to_answer", "citations"})


class ResponseValidator:
    """Validate raw provider text against an approved, versioned output schema. Returns a
    ValidatedResponse only after ALL checks pass; otherwise raises ResponseFormatError. Configured
    with injected size limits (unlimited by default). No mutation, repair, coercion, I/O, or logging."""

    def __init__(self, limits: Optional[ResponseValidationLimits] = None):
        self._limits = limits if limits is not None else ResponseValidationLimits()

    def validate(self, raw_text: str, *,
                 schema_version: str = DEFAULT_SCHEMA_VERSION) -> ValidatedResponse:
        rule = _RULES.get(schema_version)
        if rule is None:
            raise ResponseFormatError("unsupported response schema version",
                                      code="unsupported_schema_version")
        return rule(self, raw_text)

    # --- schema v1 ---
    def _validate_v1(self, raw_text: str) -> ValidatedResponse:
        obj = self._parse_object(raw_text)
        self._check_keys(obj)
        answer_text = self._require_str(obj["answer_text"])
        unable = self._require_bool(obj["unable_to_answer"])
        citations = self._require_citation_list(obj["citations"])
        self._check_sizes(answer_text, citations)
        self._check_cross_field(answer_text, unable, citations)
        return ValidatedResponse(answer_text, unable, tuple(citations))

    def _parse_object(self, raw_text: str) -> dict:
        # json.loads tolerates only surrounding whitespace; markdown fences and prose before/after the
        # object are NOT valid JSON and raise here (no extraction is attempted).
        try:
            obj = json.loads(raw_text)
        except (ValueError, TypeError):
            raise ResponseFormatError("response is not valid JSON", code="invalid_json")
        if not isinstance(obj, dict):
            raise ResponseFormatError("response is not a single JSON object", code="not_object")
        return obj

    def _check_keys(self, obj: dict) -> None:
        keys = set(obj.keys())
        if _REQUIRED_FIELDS - keys:
            raise ResponseFormatError("response is missing required fields", code="missing_field")
        if keys - _REQUIRED_FIELDS:
            raise ResponseFormatError("response has unexpected fields", code="extra_field")

    def _require_str(self, value) -> str:
        if value is None:
            raise ResponseFormatError("field is null", code="null_field")
        if not isinstance(value, str):
            raise ResponseFormatError("field must be a string", code="wrong_type")
        return value

    def _require_bool(self, value) -> bool:
        if value is None:
            raise ResponseFormatError("field is null", code="null_field")
        if not isinstance(value, bool):     # checked before int: bool subclasses int in Python
            raise ResponseFormatError("field must be a boolean", code="wrong_type")
        return value

    def _require_citation_list(self, value) -> List[str]:
        if value is None:
            raise ResponseFormatError("citations is null", code="null_field")
        if not isinstance(value, list):
            raise ResponseFormatError("citations must be an array", code="wrong_type")
        for item in value:
            # bool excluded explicitly (bool is a str? no — but a JSON true is not a citation string).
            if isinstance(item, bool) or not isinstance(item, str):
                raise ResponseFormatError("citation must be a string", code="wrong_type")
            if item == "":
                raise ResponseFormatError("citation string is empty", code="empty_citation")
        if len(value) != len(set(value)):
            raise ResponseFormatError("duplicate citations", code="duplicate_citation")
        return value

    def _check_sizes(self, answer_text: str, citations: List[str]) -> None:
        lim = self._limits
        if lim.max_answer_chars is not None and len(answer_text) > lim.max_answer_chars:
            raise ResponseFormatError("answer_text exceeds configured limit", code="answer_too_long")
        if lim.max_citations is not None and len(citations) > lim.max_citations:
            raise ResponseFormatError("too many citations", code="too_many_citations")
        if lim.max_citation_key_chars is not None:
            for c in citations:
                if len(c) > lim.max_citation_key_chars:
                    raise ResponseFormatError("citation key exceeds configured limit",
                                              code="citation_key_too_long")

    def _check_cross_field(self, answer_text: str, unable: bool, citations: List[str]) -> None:
        if unable:
            # A refusal may carry a concise explanation in answer_text, but must cite nothing.
            if citations:
                raise ResponseFormatError("unable_to_answer=true with citations",
                                          code="unable_with_citations")
            return
        # substantive answer: requires non-empty text AND at least one citation
        if answer_text == "":
            raise ResponseFormatError("substantive answer has empty text", code="empty_answer")
        if not citations:
            raise ResponseFormatError("substantive answer has no citations", code="no_citations")


# Version-aware rule registry (mirrors prompt/schema.py). Unknown versions are rejected in validate().
_RULES = {"v1": ResponseValidator._validate_v1}
