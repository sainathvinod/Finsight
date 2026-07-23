# Versioned output-schema descriptor. This is the human-readable schema embedded in the prompt that
# tells the model exactly what JSON to return. It is NOT a validator — the ResponseValidator
# (Phase 4C.4) enforces the schema; here we only describe it. Selection is by explicit version.
from __future__ import annotations

OUTPUT_SCHEMA_VERSION = "v1"

_OUTPUT_SCHEMA_V1 = (
    "Return a single JSON object with exactly these fields and no others:\n"
    "  \"answer_text\": string — the explanation, or an empty string if unable to answer.\n"
    "  \"unable_to_answer\": boolean — true when the context is insufficient to answer.\n"
    "  \"citations\": array of strings — citation keys taken verbatim from the context that support "
    "the answer (for example \"finding:<id>\"). Use an empty array if there are none.\n"
    "Do not invent findings, severity, amounts, or decisions. Do not include any additional field."
)

_REGISTRY = {OUTPUT_SCHEMA_VERSION: _OUTPUT_SCHEMA_V1}


def output_schema(version: str = OUTPUT_SCHEMA_VERSION) -> str:
    """Return the output-schema descriptor for a version. Raises KeyError for an unknown version."""
    try:
        return _REGISTRY[version]
    except KeyError:
        raise KeyError("Unknown output schema version: " + str(version))
