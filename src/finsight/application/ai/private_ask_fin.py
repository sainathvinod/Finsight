"""Stage 2 private Ask Fin orchestration.

The service is intentionally separate from the deterministic Rule Engine.  It
can explain only sealed V2 projections and fingerprint-matched source records.
It has no external retrieval seam and no provider fallback.
"""

from __future__ import annotations

import re
import time
from dataclasses import replace
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping, Optional, Sequence

from finsight.application.ai.errors import (
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ResponseFormatError,
)
from finsight.application.ai.private_contracts import (
    PRIVATE_ASK_FIN_PROMPT_VERSION,
    AskFinContext,
    AskFinMode,
    GroundedFinSightRecord,
    PrivateAskFinGrounding,
    PrivateAskFinRequest,
    PrivateAskFinResult,
    PrivateAskFinSession,
    PrivateAskFinStatus,
    PrivateCitation,
)
from finsight.application.ai.private_claims import (
    build_supported_claims,
    supported_claim_for_sentence,
)
from finsight.application.ai.private_grounding import (
    FINANCIAL_GREETING,
    HELP_GREETING,
    PrivateGroundingError,
    PrivateGroundingScopeError,
)
from finsight.application.ai.private_intent import (
    AskFinIntent,
    AskFinIntentClassification,
    application_help_response,
    clarification_response,
    classify_ask_fin_intent,
    social_response,
)
from finsight.application.ai.private_prompt import (
    build_deterministic_grounded_answer,
    build_private_prompt,
)
from finsight.application.ai.private_response import build_business_response
from finsight.application.ai.validation import ResponseValidator
from finsight.diagnostics import get_logger
from finsight.domain.ai.contracts import ProviderConfiguration
from finsight.domain.ai.local_endpoint import (
    is_cloud_style_model_alias,
    normalized_loopback_http_url,
)


_log = get_logger("ai.private_ask_fin")

LOCAL_MODEL_OUTAGE = (
    "Ask Fin is unavailable because local Ollama is not running or the "
    "selected local model could not be reached. "
    "Explain This and all deterministic financial results remain available."
)
INSUFFICIENT_EVIDENCE = (
    "I don’t have enough verified information in this review to answer that. "
    "I can show the available findings, source evidence, or supported review "
    "details instead."
)


def _apply_selected_context_intent(
    classification: AskFinIntentClassification,
    context: Optional[AskFinContext],
) -> AskFinIntentClassification:
    """Keep broad natural-language requests inside the selected object scope."""

    if context is None or classification.intent is not AskFinIntent.REVIEW_SUMMARY:
        return classification
    scoped_intent = {
        "account": AskFinIntent.ACCOUNT,
        "vendor": AskFinIntent.VENDOR,
        "department": AskFinIntent.DEPARTMENT,
        "transaction": AskFinIntent.GED_TRANSACTION,
        "finding": AskFinIntent.FINDINGS_SUMMARY,
    }.get(context.object_type.casefold())
    if scoped_intent is None:
        return classification
    return AskFinIntentClassification(
        scoped_intent,
        uses_prior_context=True,
    )


_GENERIC_CONTEXT_EVIDENCE = re.compile(
    r"^\s*(?:show|open|give|display)\s+(?:me\s+)?(?:the\s+)?"
    r"(?:supporting\s+|source\s+)?(?:evidence|sources?|rows?)"
    r"(?:\s+(?:for|behind)\s+(?:this|that|it))?[\s?.!]*$",
    re.IGNORECASE,
)
_SPECIFIC_CONTEXT_KINDS = frozenset(
    {"account", "vendor", "department", "transaction", "finding"}
)
_MISSING_OR_DUPLICATE_GED = re.compile(
    r"\b(?:missing|required|duplicate)\b.*\b(?:ged|amount|field|data|"
    r"transaction|journal|invoice)\b|"
    r"\bged\b.*\b(?:missing|required|duplicate)\b",
    re.IGNORECASE,
)
_SUPPORTED_FINDINGS_PLAN = re.compile(
    r"\b(?:what(?:'s|\s+is)\s+wrong|look\s+at\s+first|inspect\s+first|"
    r"highest[-\s]priority|most\s+important|top\s+findings?|priorities|"
    r"needs?\s+attention|why\s+is\s+(?:this|the\s+review)\s+incomplete|"
    r"summar(?:y|ize).*\bfindings?|which\s+findings?|"
    r"explain.*\bfinding|why.*\bfinding)\b",
    re.IGNORECASE,
)


def _selected_context_for_question(
    classification: AskFinIntentClassification,
    context: Optional[AskFinContext],
    question: str,
) -> Optional[AskFinContext]:
    """Use the last object scope only for a genuine follow-up."""

    if context is None:
        return None
    kind = context.object_type.casefold()
    if kind not in _SPECIFIC_CONTEXT_KINDS:
        # A broad review summary is not a specific evidence scope.
        return None
    if classification.intent is AskFinIntent.CLARIFICATION_FOLLOW_UP:
        return context
    if (
        classification.intent is AskFinIntent.EVIDENCE
        and _GENERIC_CONTEXT_EVIDENCE.fullmatch(question)
    ):
        return context
    lowered = question.casefold()
    context_identifiers = {
        context.object_id.casefold(),
        context.object_id.split("|")[-1].casefold(),
    }
    if any(
        len(identifier) >= 3 and identifier in lowered
        for identifier in context_identifiers
    ):
        return context
    if re.search(
        rf"\b(?:this|that|selected)\s+{re.escape(kind)}\b",
        question,
        re.IGNORECASE,
    ):
        return context
    if re.fullmatch(
        r"\s*(?:why|explain\s+this|tell\s+me\s+more|show\s+me\s+more)"
        r"[\s?.!]*",
        question,
        re.IGNORECASE,
    ):
        return context
    return None


def _supports_verified_review_plan(
    question: str,
    grounding: PrivateAskFinGrounding,
    classification: AskFinIntentClassification,
) -> bool:
    """Select only questions covered by a verified active-review plan.

    Common review summaries, finding explanations, and evidence requests are
    already fully represented by exact application-authored claims. They do
    not make local-model formatting or latency an answer gate. Entity-specific
    and genuinely unsupported requests retain the normal model and hard-fail
    paths.
    """

    if (
        grounding.mode is not AskFinMode.FINANCIAL_REVIEW
        or not grounding.validation_run_id
    ):
        return False
    if classification.intent in {
        AskFinIntent.REVIEW_SUMMARY,
        AskFinIntent.EVIDENCE,
        AskFinIntent.CLARIFICATION_FOLLOW_UP,
    }:
        return True
    if classification.intent is AskFinIntent.FINDINGS_SUMMARY:
        return (
            _SUPPORTED_FINDINGS_PLAN.search(question) is not None
            or (
                grounding.context is not None
                and grounding.context.object_type.casefold() == "finding"
            )
        )
    return (
        classification.intent is AskFinIntent.GED_TRANSACTION
        and _MISSING_OR_DUPLICATE_GED.search(question) is not None
    )


PREVALIDATION_FINANCIAL = (
    "Validation results are not available yet. Complete the review and run "
    "validation first. I can help you get to that step."
)
DECISION_REFUSAL = (
    "I can’t make or authorize that decision. I can summarize the facts, "
    "show the evidence, explain the applicable rule, and "
    "outline considerations for an authorized reviewer."
)
SAFE_RESPONSE_FAILURE = (
    "Ask Fin could not safely verify the local model response. No "
    "financial answer was used. Explain This and the deterministic results "
    "remain available."
)

_FINANCIAL_PREVALIDATION = re.compile(
    r"\b(?:over\s+budget|under\s+budget|actual\s+spend|budget\s+variance|"
    r"financial\s+results?|reconciliation|which\s+vendors?|top\s+findings?|"
    r"duplicate\s+ged|missing\s+ged|account\s+\d{3,})\b",
    re.IGNORECASE,
)

_DECISION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "explicit_approve",
        re.compile(
            r"(?:\bshould\s+(?:i|we)\s+|\bcan\s+(?:i|we)\s+|^\s*please\s+|^\s*)"
            r"(?:approve|authorize)\b|\bis\s+(?:this|it)\s+safe\s+to\s+approve\b",
            re.IGNORECASE,
        ),
    ),
    (
        "explicit_reject",
        re.compile(
            r"(?:\bshould\s+(?:i|we)\s+|^\s*please\s+|^\s*)reject\b",
            re.IGNORECASE,
        ),
    ),
    (
        "explicit_pay",
        re.compile(
            r"(?:\bshould\s+(?:i|we)\s+|^\s*please\s+|^\s*)"
            r"(?:pay|release|process|settle)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "payment_appropriateness",
        re.compile(
            r"\b(?:is|would|does)\s+(?:this|the)\s+"
            r"(?:invoice|payment|bill|charge)\b[^?.!]{0,60}\b"
            r"(?:appropriate|proper|valid|legitimate|reasonable|justified|"
            r"okay|ok|payable|ready\s+to\s+(?:pay|release|process)|"
            r"deserve\s+(?:payment|to\s+be\s+paid))\b|"
            r"\b(?:is|would)\s+it\b[^?.!]{0,40}\b"
            r"(?:appropriate|proper|okay|ok|reasonable|justified)\b"
            r"[^?.!]{0,40}\b(?:pay|release|process|settle)\b|"
            r"\bshould\s+(?:this|the)\s+(?:invoice|payment|bill|charge)\s+"
            r"be\s+(?:paid|approved|released|processed|settled|rejected)\b|"
            r"\b(?:can|may)\s+(?:this|the)\s+(?:invoice|payment|bill|charge)"
            r"\s+be\s+(?:paid|released|processed|settled)\b|"
            r"\b(?:would|is)\s+paying\b[^?.!]{0,50}\b"
            r"(?:appropriate|proper|reasonable|justified|acceptable|advisable|"
            r"warranted|okay|ok)\b|"
            r"\b(?:payment|paying|invoice|bill|charge)\b[^?.!]{0,50}\b"
            r"(?:appropriate|proper|reasonable|justified|acceptable|advisable|"
            r"warranted|payable)\b|"
            r"\b(?:can|may|should)\s+(?:i|we)\s+"
            r"(?:go\s+ahead\s+and\s+)?(?:pay|release|process|settle)\b|"
            r"\bshould\s+payment\s+be\s+(?:made|released|processed)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "change_budget",
        re.compile(
            r"(?:\bshould\s+(?:i|we)\s+|^\s*please\s+|^\s*)"
            r"(?:increase|decrease|change|adjust)\s+(?:the\s+)?budget\b|"
            r"\bdecide\s+whether\s+to\s+(?:increase|decrease|change|adjust)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reforecast",
        re.compile(
            r"(?:\bshould\s+(?:i|we)\s+|^\s*please\s+|^\s*)reforecast\b",
            re.IGNORECASE,
        ),
    ),
    (
        "alter_transaction",
        re.compile(
            r"(?:\bshould\s+(?:i|we)\s+|^\s*please\s+|^\s*)"
            r"(?:remove|delete|alter|change)\s+(?:this\s+|the\s+)?"
            r"(?:ged\s+)?(?:entry|transaction)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "finding_disposition",
        re.compile(
            r"(?:\bshould\s+(?:i|we)\s+|^\s*please\s+|^\s*)"
            r"(?:dismiss|resolve|accept)\s+(?:this\s+|the\s+)?finding\b",
            re.IGNORECASE,
        ),
    ),
    (
        "vendor_action",
        re.compile(
            r"(?:\bshould\s+(?:i|we)\s+|^\s*please\s+|^\s*)"
            r"(?:fire|terminate|drop)\s+(?:this\s+|the\s+)?vendor\b",
            re.IGNORECASE,
        ),
    ),
    (
        "escalation_decision",
        re.compile(
            r"(?:\bshould\s+(?:i|we)\s+|^\s*please\s+)"
            r"escalate\b|\bdecide\s+whether\s+to\s+escalate\b",
            re.IGNORECASE,
        ),
    ),
    (
        "make_decision",
        re.compile(
            r"\bmake\s+(?:the\s+)?(?:final\s+)?(?:financial\s+)?decision"
            r"(?:\s+for\s+me)?\b|\bdecide\s+(?:this|for\s+me|which)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "what_would_you_do",
        re.compile(r"\bwhat\s+would\s+you\s+do\b", re.IGNORECASE),
    ),
    (
        "pick_option",
        re.compile(
            r"\bpick\s+(?:the\s+)?(?:best|right)?\s*"
            r"(?:option|choice|action|one)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "right_decision",
        re.compile(
            r"\btell\s+me\s+(?:the\s+)?(?:right|best)\s+"
            r"(?:decision|choice|option|action|move|course|next\s+step)\b|"
            r"\bwhat(?:'s|\s+is)\s+(?:the\s+)?(?:right|best|prudent|sensible)"
            r"\s+(?:decision|choice|option|action|move|course|next\s+step)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "subtle_recommendation",
        re.compile(
            r"\b(?:recommend|advise|suggest)\b[^?.!]{0,100}\b(?:pay|payment|"
            r"approve|reject|release|process|settle|dismiss|escalate|"
            r"reforecast|increase|decrease|delete|remove|fire|terminate)\b|"
            r"\b(?:prudent|sensible|appropriate|best|right)\s+"
            r"(?:move|course|action|next\s+step)\s+(?:is|would\s+be)\b|"
            r"\bwhat\s+do\s+you\s+(?:recommend|advise|suggest)\b|"
            r"\bwhat\s+should\s+(?:i|we)\s+do\s+next\b|"
            r"\bhow\s+should\s+(?:i|we)\s+handle\s+this\b",
            re.IGNORECASE,
        ),
    ),
    (
        "yes_or_no",
        re.compile(r"\bgive\s+me\s+(?:a\s+)?yes\s+or\s+no\b", re.IGNORECASE),
    ),
    (
        "leadership_action",
        re.compile(
            r"\bwhich\s+(?:option|action)\s+should\s+(?:leadership|finance|we|i)"
            r"\s+(?:choose|take)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "delegated_decision",
        re.compile(
            r"\b(?:would|will|can|could)\s+you\s+(?:approve|authorize|reject|"
            r"pay|dismiss|resolve|accept|escalate|reforecast|fire|terminate|"
            r"delete|remove|alter)\b|"
            r"\b(?:i|we)\s+should\s+(?:approve|authorize|reject|pay|dismiss|"
            r"resolve|accept|escalate|reforecast|fire|terminate|delete|remove|"
            r"alter)\b|"
            r"\bdo\s+you\s+(?:recommend|think)\b[^?.!]*\b(?:approve|reject|"
            r"pay|paying|dismiss|escalate|reforecast|increase|decrease|delete|"
            r"remove|fire)\b|"
            r"\btell\s+me\s+(?:whether|if)\s+(?:i|we)\s+should\b",
            re.IGNORECASE,
        ),
    ),
)

_PROHIBITED_ANSWER_LANGUAGE = re.compile(
    r"\b(?:approval\s+granted|i\s+have\s+decided|you\s+should\s+(?:approve|"
    r"reject|pay|release|process|settle|dismiss|increase|decrease|reforecast|"
    r"delete|remove|alter|escalate|fire|terminate|contact)|"
    r"(?:this|the)\s+(?:invoice|payment|bill|charge)\s+(?:is|appears|seems)"
    r"\s+(?:appropriate|proper|valid|legitimate|reasonable|justified|"
    r"acceptable|advisable|warranted|payable|okay|ok)"
    r"\s+(?:to\s+pay|for\s+payment)|"
    r"(?:payment|the\s+payment)\s+(?:is|appears|seems)\s+"
    r"(?:appropriate|proper|reasonable|justified|acceptable|advisable|"
    r"warranted)|"
    r"paying\s+(?:this|the)\s+(?:invoice|bill|charge)\s+(?:is|appears|seems)"
    r"\s+(?:appropriate|proper|reasonable|justified|acceptable|advisable|"
    r"warranted)|"
    r"(?:this|the)\s+(?:invoice|bill|charge)\s+(?:can|may|should)\s+be\s+paid|"
    r"(?:this|the)\s+(?:invoice|bill|charge)\s+is\s+payable|"
    r"(?:it\s+is|it's)\s+(?:appropriate|proper|reasonable|justified|"
    r"acceptable|advisable|warranted|okay|ok)\s+to\s+pay|"
    r"(?:proceed\s+with|go\s+ahead\s+with)\s+(?:the\s+)?payment|"
    r"(?:finance|you|we)\s+(?:can|may|should)\s+(?:release|process|settle)"
    r"\s+(?:the\s+)?payment|"
    r"(?:i|ask\s+fin)\s+(?:recommend|advise|suggest)\b|"
    r"i\s+(?:would|recommend|advise|suggest)\s+(?:approv|"
    r"reject|pay|dismiss|escalat|reforecast|increas|decreas|delet|remov|"
    r"releas|process|settl|fir)\w*|"
    r"(?:best|right|prudent|sensible|appropriate)\s+"
    r"(?:action|decision|choice|move|course|next\s+step)\s+is|"
    r"reject\s+this\s+invoice|increase\s+the\s+budget|dismiss\s+the\s+finding|"
    r"safe\s+to\s+(?:approve|pay|release|process)|"
    r"no\s+further\s+review\s+is\s+necessary)\b",
    re.IGNORECASE,
)

_FINANCIAL_TOKEN = re.compile(
    r"(?:[-−+]?\$(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|"
    r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%|"
    r"\b\d{4}-\d{2}-\d{2}\b|"
    r"\bv?\d+\.\d+\.\d+\b|"
    r"(?<![A-Za-z0-9_-])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
    r"(?![A-Za-z0-9_-]))"
)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_INLINE_CITATION = re.compile(r"\[([a-z][a-z-]*:[^\[\]\s]+)\]")
_CAUSAL_CLAIM = re.compile(
    r"\b(?:because|caused(?:\s+by)?|driven\s+by|due\s+to|resulted\s+from|"
    r"associated\s+with|responsible\s+for|stems?\s+from|attributable\s+to|"
    r"triggered(?:\s+by)?|led\s+to|arose\s+from|owing\s+to|"
    r"drove|driving|resulted\s+in|originated\s+from|comes?\s+from|"
    r"contribut(?:e|es|ed|ing)\s+to|accounts?\s+for|traceable\s+to|"
    r"(?:is|was)\s+behind|root\s+cause|reason\s+for|because\s+of|"
    r"the\s+result\s+of)\b",
    re.IGNORECASE,
)

_CLAIM_PREDICATES = frozenset(
    {
        "account",
        "amount",
        "atd",
        "bgt",
        "count",
        "date",
        "delta",
        "department",
        "eac",
        "etc",
        "invoice_amount",
        "period",
        "source_row",
        "utilization",
        "variance",
        "version",
        "actual",
    }
)


def decision_boundary_trigger(question: str) -> Optional[str]:
    """Return a stable refusal trigger before any provider can be invoked."""

    state_change = _framed_state_change_decision(question)
    if state_change:
        return state_change
    for name, pattern in _DECISION_PATTERNS:
        if pattern.search(question):
            return name
    return None


def _string_fact_leaves(
    value: Any,
    path: tuple[str, ...] = (),
) -> tuple[tuple[str, str], ...]:
    """Flatten only display/string facts; internal cents are never citable prose."""

    output: list[tuple[str, str]] = []
    if isinstance(value, str):
        output.append((".".join(path), value))
    elif (
        isinstance(value, int)
        and not isinstance(value, bool)
        and path
        and (
            path[-1].casefold().endswith("_count")
            or path[-1].casefold()
            in {
                "count",
                "duplicate_transactions",
                "findings",
                "missing_required_data",
                "source_row",
                "row",
            }
            or (len(path) >= 2 and path[-2].casefold().endswith("_rows"))
        )
    ):
        output.append((".".join(path), str(value)))
    elif (
        isinstance(value, (int, float, Decimal))
        and not isinstance(value, bool)
        and len(path) >= 2
        and path[-2].casefold() in {"fields", "original_fields"}
        and path[-1].casefold()
        in {
            "invoice_amt",
            "amount",
            "bgt",
            "atd",
            "etc",
            "eac",
            "delta",
        }
    ):
        output.append((".".join(path), str(value)))
        try:
            output.append(
                (
                    ".".join(path),
                    f"${Decimal(str(value)):,.2f}",
                )
            )
        except (InvalidOperation, ValueError):
            pass
    elif isinstance(value, Mapping):
        for key, item in value.items():
            output.extend(_string_fact_leaves(item, path + (str(key),)))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            output.extend(_string_fact_leaves(item, path + (str(index),)))
    return tuple(output)


def _path_role(path: str) -> Optional[str]:
    parts = tuple(item.casefold() for item in path.split(".") if item)
    if not parts:
        return None
    leaf = parts[-1]
    parent = parts[-2] if len(parts) > 1 else ""
    exact = {
        "account_number": "account",
        "department_number": "department",
        "source_row": "source_row",
        "row": "source_row",
        "reporting_period": "period",
        "fiscal_period": "period",
        "journal_date": "date",
        "invoice_date": "date",
        "date": "date",
        "bgt": "bgt",
        "bgt_label": "bgt",
        "budget": "bgt",
        "budget_label": "bgt",
        "actual_ged": "actual",
        "actual_spend": "actual",
        "ged_label": "actual",
        "summed_ged_amount": "actual",
        "summed_ged_amount_label": "actual",
        "actual_label": "actual",
        "atd": "atd",
        "atd_label": "atd",
        "etc": "etc",
        "etc_label": "etc",
        "eac": "eac",
        "eac_label": "eac",
        "delta": "delta",
        "delta_label": "delta",
        "over_budget_amount": "variance",
        "over_budget_amount_label": "variance",
        "actual_variance": "variance",
        "actual_variance_label": "variance",
        "actual_variance_percentage_label": "variance",
        "variance_percentage": "variance",
        "variance": "variance",
        "variance_label": "variance",
        "budget_utilization": "utilization",
        "budget_utilization_label": "utilization",
        "count": "count",
        "duplicate_transactions": "count",
        "missing_required_data": "count",
        "amount": "amount",
        "amount_label": "amount",
        "invoice_amt": "invoice_amount",
        "invoice_amount": "invoice_amount",
        "invoice_amt_label": "invoice_amount",
        "invoice_amount_label": "invoice_amount",
        "findings": "count",
        "rule_version": "version",
    }
    if leaf in exact:
        return exact[leaf]
    if leaf.endswith("_count"):
        return "count"
    if parent.endswith("_rows") and leaf.isdigit():
        return "source_row"
    return None


_ROLE_PATTERNS: tuple[tuple[str, re.Pattern[str], int], ...] = (
    (
        "variance",
        re.compile(
            r"\b(?:over|under)\s+budget\b|\boverrun\b|\bvariance\b|"
            r"\bunfavorable\b|\bfavorable\b",
            re.IGNORECASE,
        ),
        0,
    ),
    ("utilization", re.compile(r"\bbudget\s+utilization\b", re.IGNORECASE), 0),
    ("delta", re.compile(r"\bdelta\b", re.IGNORECASE), 0),
    ("eac", re.compile(r"\beac\b|estimate\s+at\s+completion", re.IGNORECASE), 1),
    ("etc", re.compile(r"\betc\b|estimate\s+to\s+complete", re.IGNORECASE), 1),
    ("atd", re.compile(r"\batd\b|actual\s+to\s+date", re.IGNORECASE), 1),
    (
        "bgt",
        re.compile(
            r"\bbgt\b|\bplanned\s+(?:budget|amount|spend(?:ing)?)\b|"
            r"\bbudgeted\s+(?:amount|spend(?:ing)?)\b|"
            r"\bbudget\b",
            re.IGNORECASE,
        ),
        2,
    ),
    (
        "actual",
        re.compile(
            r"\b(?:ged\s+)?actual\b|\bged\s+spend\b|\brecorded\s+spend\b|"
            r"\bsummed\s+ged\b|\bactual\s+spend\b|\bvendor\s+spend\b",
            re.IGNORECASE,
        ),
        2,
    ),
    (
        "invoice_amount",
        re.compile(r"\binvoice\s+(?:amt|amount)\b", re.IGNORECASE),
        1,
    ),
    (
        "amount",
        re.compile(
            r"\b(?:ged|transaction|recorded)\s+amount\b|\bamount\b",
            re.IGNORECASE,
        ),
        3,
    ),
    ("amount", re.compile(r"\b(?:duplicate-copy\s+)?exposure\b", re.IGNORECASE), 2),
    ("account", re.compile(r"\baccount\b", re.IGNORECASE), 2),
    ("department", re.compile(r"\bdepartment\b|\bdept\b", re.IGNORECASE), 2),
    (
        "source_row",
        re.compile(r"\bsource\s+rows?\b|\brows?\b", re.IGNORECASE),
        2,
    ),
    ("date", re.compile(r"\bdate\b", re.IGNORECASE), 2),
    (
        "period",
        re.compile(
            r"\breporting\s+period\b|\bfiscal\s+period\b|\bperiod\b", re.IGNORECASE
        ),
        2,
    ),
    (
        "count",
        re.compile(
            r"\bcount\b|\btransactions?\b|\bfindings?\b|"
            r"\bmissing\b|\brequired\s+(?:data|values?)\b|"
            r"\brule\s+results?\b",
            re.IGNORECASE,
        ),
        3,
    ),
    ("version", re.compile(r"\bversion\b", re.IGNORECASE), 1),
)


def _context_role(text: str, start: int, end: int) -> Optional[str]:
    token = text[start:end]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", token):
        return "date"
    if re.fullmatch(r"\d{4}", token) and re.search(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
        r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?)\s+$",
        text[max(0, start - 12) : start],
        re.IGNORECASE,
    ):
        return "period"
    candidates: list[tuple[int, int, str]] = []
    for role, pattern, priority in _ROLE_PATTERNS:
        for match in pattern.finditer(text):
            distance = min(abs(match.end() - start), abs(match.start() - end))
            if distance <= 48:
                candidates.append((distance, priority, role))
    if not candidates:
        return None
    role = min(candidates)[2]
    return role if role in _CLAIM_PREDICATES else None


def _fact_supports_token(
    token: str,
    claim_role: Optional[str],
    leaves: Sequence[tuple[str, str]],
) -> bool:
    if claim_role not in _CLAIM_PREDICATES:
        # Closed claim contract: an amount/identifier without an approved
        # predicate is not supportable merely because its characters appear
        # somewhere in the cited JSON.
        return False
    compatible_fact_roles = {
        "actual": frozenset({"actual", "amount"}),
    }.get(claim_role, frozenset({claim_role}))
    for path, display in leaves:
        start = 0
        while True:
            index = display.find(token, start)
            if index < 0:
                break
            fact_role = _path_role(path) or _context_role(
                display, index, index + len(token)
            )
            if fact_role in compatible_fact_roles:
                return True
            start = index + len(token)
    return False


def _supports_causal_claim(
    sentence: str,
    leaves: Sequence[tuple[str, str]],
) -> bool:
    if not _CAUSAL_CLAIM.search(sentence):
        return True
    claim = _INLINE_CITATION.sub("", sentence)
    claim = re.sub(r"\s+", " ", claim).strip(" .").casefold()
    # Causal paraphrase is deliberately not inferred.  The model may repeat a
    # recorded causal/explanation statement, but cannot author a new cause.
    return any(
        claim and claim in re.sub(r"\s+", " ", value).strip(" .").casefold()
        for _path, value in leaves
    )


def _supports_directional_claim(
    sentence: str,
    leaves: Sequence[tuple[str, str]],
) -> bool:
    normalized = sentence.casefold()
    for phrase, expected_fragments in (
        (
            "over budget",
            (
                "over_budget",
                "variance",
                "actual",
                "explanation",
                "what_happened",
                "highest_priority_findings",
            ),
        ),
        ("under budget", ("variance", "actual", "explanation")),
    ):
        if phrase not in normalized:
            continue
        supported = False
        for path, value in leaves:
            path_normalized = path.casefold()
            if any(fragment in path_normalized for fragment in expected_fragments):
                if (
                    phrase in value.casefold()
                    or (phrase == "over budget" and "exceeded bgt" in value.casefold())
                    or (phrase == "over budget" and "overrun" in value.casefold())
                    or "over_budget" in path_normalized
                ):
                    supported = True
                    break
        if not supported:
            return False
    return True


_RECORDED_STATUS_CLAIM = re.compile(
    r"\b(?:attention\s+required|healthy|reconciled|unreconciled|"
    r"not\s+reconciled|critical|high|medium|low|passed|failed)\b",
    re.IGNORECASE,
)

_STATE_CHANGE_ACTIONS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "cancel",
        re.compile(
            r"\bcancell?(?:s|ed|ing|ation)?\b[^?.!]{0,35}\b"
            r"(?:invoice|payment|transaction|charge|bill)\b|"
            r"\b(?:invoice|payment|transaction|charge|bill)\b"
            r"[^?.!]{0,35}\bcancell?(?:s|ed|ing|ation)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "approve",
        re.compile(
            r"\bapprov(?:e|ed|es|ing|al)\b|\bsign(?:ed|ing)?\s+off\b|"
            r"\bgreen[\s-]?light(?:s|ed|ing)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "authorize",
        re.compile(r"\bauthoriz(?:e|ed|es|ing|ation)\b", re.IGNORECASE),
    ),
    (
        "pay",
        re.compile(
            r"\bpay(?:s|ing|ment|ments)?\b|\bpaid\b|\bpayable\b|"
            r"\b(?:releas(?:e|es|ed|ing)|process(?:es|ed|ing)?|"
            r"settl(?:e|es|ed|ing)|remit(?:s|ted|ting)?)\b"
            r"[^?.!]{0,30}\b(?:payment|invoice|bill|charge)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reject",
        re.compile(
            r"\breject(?:s|ed|ing|ion)?\b|"
            r"\b(?:deny|denies|denied|denying|decline|declines|declined|"
            r"declining)\b[^?.!]{0,30}\b(?:invoice|payment|finding|request)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "dismiss",
        re.compile(
            r"\bdismiss(?:es|ed|ing|al)?\b|"
            r"\b(?:waive|waives|waived|waiving|ignore|ignores|ignored|"
            r"ignoring|override|overrides|overrode|overriding)\b"
            r"[^?.!]{0,30}\bfinding\b",
            re.IGNORECASE,
        ),
    ),
    (
        "resolve",
        re.compile(
            r"\bresolv(?:e|es|ed|ing|ution)\b|"
            r"\b(?:close|closes|closed|closing|clear|clears|cleared|clearing)"
            r"\b[^?.!]{0,30}\bfinding\b|"
            r"\bmark(?:s|ed|ing)?\b[^?.!]{0,20}\bfinding\b"
            r"[^?.!]{0,20}\bresolved\b",
            re.IGNORECASE,
        ),
    ),
    (
        "accept",
        re.compile(
            r"\baccept(?:s|ed|ing|ance)?\b[^?.!]{0,30}\b"
            r"(?:finding|invoice|payment|variance)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "escalate",
        re.compile(
            r"\bescalat(?:e|es|ed|ing|ion)\b|"
            r"\b(?:elevate|elevates|elevated|elevating|refer|refers|referred|"
            r"referring)\b[^?.!]{0,35}\b(?:issue|finding|variance)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reforecast",
        re.compile(r"\breforecast(?:s|ed|ing)?\b", re.IGNORECASE),
    ),
    (
        "reallocate",
        re.compile(
            r"\breallocat(?:e|es|ed|ing|ion)\b|"
            r"\b(?:transfer|transfers|transferred|transferring|shift|shifts|"
            r"shifted|shifting|move|moves|moved|moving)\b"
            r"[^?.!]{0,35}\b(?:funds|budget|allocation)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "budget_change",
        re.compile(
            r"\b(?:increas(?:e|es|ed|ing)|decreas(?:e|es|ed|ing)|"
            r"adjust(?:s|ed|ing)?|chang(?:e|es|ed|ing)|"
            r"rais(?:e|es|ed|ing)|lower(?:s|ed|ing)?|"
            r"expand(?:s|ed|ing)?|boost(?:s|ed|ing)?|grow(?:s|n|ing)?|"
            r"reduc(?:e|es|ed|ing)|cut(?:s|ting)?|shrink(?:s|ing)?|"
            r"modif(?:y|ies|ied|ying)|revis(?:e|es|ed|ing)|"
            r"amend(?:s|ed|ing)?)\b"
            r"[^?.!]{0,35}\b(?:budget|allocation|spend(?:ing)?\s+ceiling)\b|"
            r"\b(?:budget|allocation|spend(?:ing)?\s+ceiling)\b"
            r"[^?.!]{0,35}\b(?:increas(?:e|es|ed|ing)|"
            r"decreas(?:e|es|ed|ing)|adjust(?:s|ed|ing)?|"
            r"chang(?:e|es|ed|ing)|rais(?:e|es|ed|ing)|"
            r"lower(?:s|ed|ing)?|expand(?:s|ed|ing)?|"
            r"boost(?:s|ed|ing)?|grow(?:s|n|ing)?|"
            r"reduc(?:e|es|ed|ing)|cut(?:s|ting)?|shrink(?:s|ing)?|"
            r"modif(?:y|ies|ied|ying)|revis(?:e|es|ed|ing)|"
            r"amend(?:s|ed|ing)?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "record_change",
        re.compile(
            r"\b(?:delet(?:e|es|ed|ing)|remov(?:e|es|ed|ing)|"
            r"alter(?:s|ed|ing)?|edit(?:s|ed|ing)?|"
            r"chang(?:e|es|ed|ing)|modif(?:y|ies|ied|ying)|"
            r"revis(?:e|es|ed|ing)|amend(?:s|ed|ing)?)\b"
            r"[^?.!]{0,35}\b(?:transaction|ged\s+entry|finding|rule|status)\b|"
            r"\b(?:transaction|ged\s+entry|finding|rule|status)\b"
            r"[^?.!]{0,35}\b(?:delet(?:e|es|ed|ing)|"
            r"remov(?:e|es|ed|ing)|alter(?:s|ed|ing)?|"
            r"edit(?:s|ed|ing)?|chang(?:e|es|ed|ing)|"
            r"modif(?:y|ies|ied|ying)|revis(?:e|es|ed|ing)|"
            r"amend(?:s|ed|ing)?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "rule_lifecycle",
        re.compile(
            r"\b(?:activate|activates|activated|activating|disable|disables|"
            r"disabled|disabling|retire|retires|retired|retiring|delete|"
            r"deletes|deleted|deleting)\b[^?.!]{0,30}\brule\b|"
            r"\brule\b[^?.!]{0,30}\b(?:activate|activates|activated|"
            r"activating|disable|disables|disabled|disabling|retire|retires|"
            r"retired|retiring|delete|deletes|deleted|deleting)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "vendor_change",
        re.compile(
            r"\b(?:fir(?:e|es|ed|ing)|terminat(?:e|es|ed|ing)|"
            r"drop(?:s|ped|ping)?)\b"
            r"[^?.!]{0,25}\bvendor\b",
            re.IGNORECASE,
        ),
    ),
)

_DECISION_FRAMING = re.compile(
    r"\b(?:appropriate|proper|prudent|sensible|advisable|warranted|"
    r"justified|acceptable|best|right|safe|recommend|advise|suggest|"
    r"wise|sound|preferable|good\s+idea|should|could|can|may|would|"
    r"yes\s+or\s+no|go\s+ahead)\b",
    re.IGNORECASE,
)
_SAFE_EVIDENCE_INTENT = re.compile(
    r"^\s*(?:what|which|show|summarize)\b[^?.!]{0,120}\b"
    r"(?:recorded\s+evidence|supporting\s+evidence|recorded\s+facts|"
    r"source\s+records?)\b[^?.!]{0,120}\bauthorized\s+reviewer\b"
    r"[^?.!]{0,80}\b(?:consider|review)\b",
    re.IGNORECASE,
)


def _state_change_action(text: str) -> Optional[str]:
    for name, pattern in _STATE_CHANGE_ACTIONS:
        if pattern.search(text):
            return name
    return None


def _framed_state_change_decision(text: str) -> Optional[str]:
    """Recognize a closed set of governed state changes plus decision framing."""

    if _SAFE_EVIDENCE_INTENT.search(text):
        return None
    action = _state_change_action(text)
    if action is None:
        return None
    if _DECISION_FRAMING.search(text):
        return f"state_change_{action}"
    return None


def _unsafe_output_decision_language(text: str) -> bool:
    if _PROHIBITED_ANSWER_LANGUAGE.search(text):
        return True
    return any(
        _framed_state_change_decision(sentence) is not None
        for sentence in _SENTENCE_SPLIT.split(text)
        if sentence.strip()
    )


def _supports_status_claim(
    sentence: str,
    leaves: Sequence[tuple[str, str]],
) -> bool:
    for match in _RECORDED_STATUS_CLAIM.finditer(sentence):
        value = match.group(0).casefold()
        if not any(value in display.casefold() for _path, display in leaves):
            return False
    return True


def _citation_evidence_details(
    record: GroundedFinSightRecord,
) -> Mapping[str, Any]:
    """Project readable evidence fields from one already-verified record."""

    facts = record.facts
    kind = record.object_type.casefold()
    details: dict[str, Any] = {
        key: value
        for key, value in dict(record.navigation_target).items()
        if value not in (None, "")
    }
    if kind in {"transaction", "budget-source"}:
        fields = facts.get("fields")
        cells = facts.get("cells")
        if not isinstance(fields, Mapping):
            fields = {}
        if not isinstance(cells, Mapping):
            cells = {}
        primary_field = "amount" if kind == "transaction" else "bgt"
        details.update(
            {
                "source_file": facts.get("source_file"),
                "source_role": facts.get("source_role"),
                "worksheet": facts.get("worksheet"),
                "source_row": facts.get("source_row"),
                "field": primary_field,
                "cell": cells.get(primary_field),
                "account_number": fields.get("account_number"),
                "account_name": fields.get("account_name"),
                "vendor": fields.get("vendor_name"),
                "transaction_reference": fields.get("journal_number"),
                "amount": fields.get(primary_field),
            }
        )
        details["cells"] = dict(cells)
        details["fields"] = dict(fields)
    elif kind in {"finding", "rule-result"}:
        explanation = facts.get("explain_this")
        supporting: Mapping[str, Any] = {}
        technical: Mapping[str, Any] = {}
        transactions: Sequence[Any] = ()
        if isinstance(explanation, Mapping):
            supporting_value = explanation.get("supporting_evidence")
            technical_value = explanation.get("technical_details")
            if isinstance(supporting_value, Mapping):
                supporting = supporting_value
            if isinstance(technical_value, Mapping):
                technical = technical_value
            transaction_value = explanation.get("contributing_transactions")
            if isinstance(transaction_value, (list, tuple)):
                transactions = transaction_value
        lineage = supporting.get("lineage")
        first_lineage = (
            next(
                (item for item in lineage if isinstance(item, Mapping)),
                {},
            )
            if isinstance(lineage, (list, tuple))
            else {}
        )
        first_transaction = next(
            (item for item in transactions if isinstance(item, Mapping)),
            {},
        )
        vendors = supporting.get("vendors")
        vendor_label = (
            ", ".join(str(item) for item in vendors if str(item))
            if isinstance(vendors, (list, tuple))
            else ""
        )
        details.update(
            {
                "source_file": (
                    first_lineage.get("source_file")
                    or first_lineage.get("workbook")
                ),
                "source_role": first_lineage.get("source_role"),
                "worksheet": (
                    first_lineage.get("worksheet")
                    or first_lineage.get("sheet")
                ),
                "source_row": first_lineage.get(
                    "row", first_lineage.get("source_row")
                ),
                "field": (
                    first_lineage.get("field")
                    or first_lineage.get("field_name")
                ),
                "cell": first_lineage.get("cell"),
                "account_number": supporting.get("account_number"),
                "account_name": supporting.get("account_name"),
                "vendor": vendor_label or first_transaction.get("vendor"),
                "transaction_reference": first_transaction.get(
                    "journal_or_invoice_reference"
                ),
                "amount": (
                    supporting.get("variance")
                    or first_transaction.get("amount_label")
                ),
                "rule_name": (
                    technical.get("rule_name")
                    or facts.get("rule_name")
                ),
                "rule_version": (
                    technical.get("rule_version")
                    or facts.get("rule_version")
                ),
                "validation_run_id": (
                    technical.get("validation_run_id")
                    or facts.get("validation_run_id")
                ),
                "lineage": list(lineage or ()),
                "contributing_transactions": list(transactions),
            }
        )
    elif kind == "account":
        details.update(
            {
                "account_number": facts.get("account_number"),
                "account_name": facts.get("account_name"),
                "amount": facts.get("summed_ged_amount_label"),
                "vendors": list(facts.get("vendors") or ()),
            }
        )
    return {
        key: value for key, value in details.items() if value not in (None, "")
    }


class PrivateAskFinService:
    """Private local explanation service over one authorized V2 review."""

    def __init__(
        self,
        *,
        authorization,
        grounding,
        provider,
        provider_configuration: ProviderConfiguration,
        audit,
        clock,
        active_review_id: Optional[Callable[[], Optional[str]]] = None,
        monotonic: Callable[[], float] = time.monotonic,
        validator: Optional[ResponseValidator] = None,
    ):
        self._authorization = authorization
        self._grounding = grounding
        self._provider = provider
        self._config = provider_configuration
        self._audit = audit
        self._clock = clock
        self._active_review_id = active_review_id
        self._monotonic = monotonic
        self._validator = validator or ResponseValidator()
        self._require_private_local_configuration()

    def provider_status(self):
        """Expose only the verified local provider's bounded status."""

        return self._provider.status()

    def session(
        self,
        *,
        user_id: str,
        review_id: str,
        context: Optional[AskFinContext] = None,
    ) -> PrivateAskFinSession:
        self._authorize(user_id, review_id)
        self._require_active_review(review_id)
        grounding = self._grounding.context(review_id, selected_context=context)
        greeting = (
            HELP_GREETING
            if grounding.mode is AskFinMode.APPLICATION_HELP
            else FINANCIAL_GREETING
        )
        scope_label = self._scope_label(grounding)
        return PrivateAskFinSession(
            mode=grounding.mode,
            greeting=greeting,
            suggested_questions=grounding.suggested_questions,
            review_id=review_id,
            reporting_period=grounding.reporting_period,
            validation_run_id=grounding.validation_run_id,
            scope_label=scope_label,
        )

    def ask(self, request: PrivateAskFinRequest) -> PrivateAskFinResult:
        started = self._monotonic()
        grounding: Optional[PrivateAskFinGrounding] = None
        trigger = decision_boundary_trigger(request.question)
        classification = classify_ask_fin_intent(
            request.question,
            has_context=request.context is not None,
            prohibited=trigger is not None,
        )
        selected_context = _selected_context_for_question(
            classification,
            request.context,
            request.question,
        )
        classification = _apply_selected_context_intent(
            classification,
            selected_context,
        )
        try:
            self._authorize(request.user_id, request.review_id)
            self._require_active_review(request.review_id)
        except Exception:
            # Authorization failures and unknown review identifiers fail closed.
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.REFUSED,
                answer="Ask Fin is not authorized for this review.",
                failure_state="authorization_denied",
                classification=classification,
            )

        if request.context and request.context.review_id != request.review_id:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.REFUSED,
                answer=INSUFFICIENT_EVIDENCE,
                failure_state="context_review_mismatch",
                refusal_trigger="cross_review_context",
                classification=classification,
            )

        if trigger:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.REFUSED,
                answer=DECISION_REFUSAL,
                refusal_trigger=trigger,
                classification=classification,
            )

        if classification.intent is AskFinIntent.GREETING_SOCIAL:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.OK,
                answer=social_response(request.question),
                classification=classification,
            )

        if classification.intent is AskFinIntent.APPLICATION_HELP:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.OK,
                answer=application_help_response(request.question),
                classification=classification,
            )

        if classification.intent is AskFinIntent.UNSUPPORTED:
            if classification.clarification_required:
                return self._complete(
                    request,
                    started,
                    grounding,
                    status=PrivateAskFinStatus.OK,
                    answer=clarification_response(request.question),
                    classification=classification,
                )
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.UNANSWERABLE,
                answer=INSUFFICIENT_EVIDENCE,
                failure_state="unsupported_question",
                classification=classification,
            )

        try:
            grounding = self._grounding.context(
                request.review_id,
                question=request.question,
                selected_context=selected_context,
            )
        except PrivateGroundingScopeError:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.REFUSED,
                answer=INSUFFICIENT_EVIDENCE,
                failure_state="scope_denied",
                refusal_trigger="cross_review_scope",
                classification=classification,
            )
        except PrivateGroundingError:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.UNANSWERABLE,
                answer=INSUFFICIENT_EVIDENCE,
                failure_state="sealed_grounding_unavailable",
                classification=classification,
            )
        except Exception:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.REFUSED,
                answer="Ask Fin is not authorized for this review.",
                failure_state="authorization_denied",
                classification=classification,
            )

        if (
            selected_context is not None
            and request.context is not None
            and request.context.validation_run_id
            and request.context.validation_run_id != grounding.validation_run_id
        ):
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.REFUSED,
                answer=(
                    "That follow-up belongs to an earlier validation run. "
                    "Open the current result and ask again."
                ),
                failure_state="context_validation_run_mismatch",
                refusal_trigger="stale_validation_run_context",
                classification=classification,
            )

        if (
            grounding.mode is AskFinMode.APPLICATION_HELP
            and _FINANCIAL_PREVALIDATION.search(request.question)
        ):
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.UNANSWERABLE,
                answer=PREVALIDATION_FINANCIAL,
                failure_state="validation_results_unavailable",
                classification=classification,
            )

        try:
            status = self._provider.status()
        except Exception:
            status = None
        if status is None or not status.generation_available:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.UNAVAILABLE,
                answer=LOCAL_MODEL_OUTAGE,
                failure_state=(
                    getattr(status, "reason", None) or "local_model_unavailable"
                ),
                provider="ollama",
            )

        if _supports_verified_review_plan(
            request.question,
            grounding,
            classification,
        ):
            planned = self._deterministic_review_response(
                request,
                started,
                grounding,
                classification=classification,
            )
            if planned is not None:
                return planned

        prompt = build_private_prompt(grounding, request.question.strip())
        try:
            raw = self._provider.generate(prompt, self._config)
        except (ProviderUnavailableError, ProviderTimeoutError):
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.UNAVAILABLE,
                answer=LOCAL_MODEL_OUTAGE,
                failure_state="local_model_unavailable",
                provider="ollama",
            )
        except ProviderError:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.FAILED,
                answer=SAFE_RESPONSE_FAILURE,
                failure_state="local_model_error",
                provider="ollama",
            )

        raw_model_version = str(raw.metadata.get("model_version") or raw.model)
        try:
            validated = self._validator.validate(
                raw.text, schema_version=prompt.schema_version
            )
        except ResponseFormatError:
            recovered = self._deterministic_recovery(
                request,
                started,
                grounding,
                failure_state="invalid_local_model_response",
                provider=raw.provider,
                model=raw.model,
                model_version=raw_model_version,
            )
            if recovered is not None:
                return recovered
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.FAILED,
                answer=SAFE_RESPONSE_FAILURE,
                failure_state="invalid_local_model_response",
                provider=raw.provider,
                model=raw.model,
                model_version=raw_model_version,
            )

        if validated.unable_to_answer:
            recovered = self._deterministic_recovery(
                request,
                started,
                grounding,
                failure_state="model_reported_insufficient_evidence",
                provider=raw.provider,
                model=raw.model,
                model_version=raw_model_version,
            )
            if recovered is not None:
                return recovered
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.UNANSWERABLE,
                answer=INSUFFICIENT_EVIDENCE,
                failure_state="insufficient_recorded_evidence",
                provider=raw.provider,
                model=raw.model,
                model_version=raw_model_version,
            )

        if _unsafe_output_decision_language(validated.answer_text):
            # The user's decision intent is rejected before the provider is
            # invoked.  For an otherwise supported read-only question, do not
            # let a small local model's unsolicited recommendation turn a
            # valid review question into a refusal.  Discard the model prose
            # and replace it only with application-authored closed claims
            # that pass the normal citation/value verifier.
            recovered = (
                self._deterministic_recovery(
                    request,
                    started,
                    grounding,
                    failure_state="unsafe_model_decision_language",
                    provider=raw.provider,
                    model=raw.model,
                    model_version=raw_model_version,
                )
                if _supports_verified_review_plan(
                    request.question,
                    grounding,
                    classification,
                )
                else None
            )
            if recovered is not None:
                return recovered
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.REFUSED,
                answer=DECISION_REFUSAL,
                failure_state="unsafe_model_decision_language",
                refusal_trigger="model_decision_language",
                provider=raw.provider,
                model=raw.model,
                model_version=raw_model_version,
            )
        verified = self._verify_answer(
            validated.answer_text,
            validated.citation_keys,
            grounding.records,
        )
        if verified is None:
            recovered = (
                self._deterministic_recovery(
                    request,
                    started,
                    grounding,
                    failure_state="model_response_verification_failed",
                    provider=raw.provider,
                    model=raw.model,
                    model_version=raw_model_version,
                )
                if _supports_verified_review_plan(
                    request.question,
                    grounding,
                    classification,
                )
                else None
            )
            if recovered is not None:
                return recovered
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.UNANSWERABLE,
                answer=INSUFFICIENT_EVIDENCE,
                failure_state="citation_or_value_verification_failed",
                provider=raw.provider,
                model=raw.model,
                model_version=raw_model_version,
            )
        response_metadata = build_business_response(
            grounding,
            request.question,
            classification.intent,
        )
        if response_metadata is not None:
            canonical_citations = self._verify_answer(
                response_metadata.answer_text,
                response_metadata.citation_keys,
                grounding.records,
            )
            if canonical_citations is None:
                return self._complete(
                    request,
                    started,
                    grounding,
                    status=PrivateAskFinStatus.FAILED,
                    answer=SAFE_RESPONSE_FAILURE,
                    failure_state="deterministic_response_verification_failed",
                    provider=raw.provider,
                    model=raw.model,
                    model_version=raw_model_version,
                    classification=classification,
                )
            # The model response has passed closed-claim verification. Render
            # the application-authored response plan so answer depth and
            # evidence structure stay consistent across local model versions.
            # This plan only arranges exact claims from the sealed run and is
            # verified again above before display.
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.OK,
                answer=response_metadata.answer_text,
                citations=canonical_citations,
                provider=raw.provider,
                model=raw.model,
                model_version=raw_model_version,
                classification=classification,
                resolved_context=response_metadata.resolved_context,
                follow_up_questions=response_metadata.follow_up_questions,
            )
        return self._complete(
            request,
            started,
            grounding,
            status=PrivateAskFinStatus.OK,
            answer=validated.answer_text,
            citations=verified,
            provider=raw.provider,
            model=raw.model,
            model_version=raw_model_version,
            classification=classification,
            resolved_context=(
                response_metadata.resolved_context
                if response_metadata is not None
                else grounding.context
            ),
            follow_up_questions=(
                response_metadata.follow_up_questions
                if response_metadata is not None
                else grounding.suggested_questions[:4]
            ),
        )

    def _deterministic_review_response(
        self,
        request: PrivateAskFinRequest,
        started: float,
        grounding: PrivateAskFinGrounding,
        *,
        classification: AskFinIntentClassification,
    ) -> Optional[PrivateAskFinResult]:
        """Return an active-run response without making model prose a gate."""

        business_response = build_business_response(
            grounding,
            request.question,
            classification.intent,
        )
        if business_response is None:
            return None
        verified = self._verify_answer(
            business_response.answer_text,
            business_response.citation_keys,
            grounding.records,
        )
        if verified is None:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.FAILED,
                answer=SAFE_RESPONSE_FAILURE,
                failure_state="deterministic_response_verification_failed",
                provider="finsight",
                model="deterministic-review-v1",
                classification=classification,
            )
        return self._complete(
            request,
            started,
            grounding,
            status=PrivateAskFinStatus.OK,
            answer=business_response.answer_text,
            citations=verified,
            provider="finsight",
            model="deterministic-review-v1",
            model_version="deterministic-review-v1",
            classification=classification,
            resolved_context=business_response.resolved_context,
            follow_up_questions=business_response.follow_up_questions,
        )

    def _deterministic_recovery(
        self,
        request: PrivateAskFinRequest,
        started: float,
        grounding: PrivateAskFinGrounding,
        *,
        failure_state: str,
        provider: str,
        model: str,
        model_version: str,
    ) -> Optional[PrivateAskFinResult]:
        classification = classify_ask_fin_intent(
            request.question,
            has_context=request.context is not None,
        )
        selected_context = _selected_context_for_question(
            classification,
            request.context,
            request.question,
        )
        classification = _apply_selected_context_intent(
            classification,
            selected_context,
        )
        business_response = build_business_response(
            grounding,
            request.question,
            classification.intent,
        )
        if business_response is not None:
            answer = business_response.answer_text
            citation_keys = business_response.citation_keys
            resolved_context = business_response.resolved_context
            follow_up_questions = business_response.follow_up_questions
        else:
            if classification.intent is AskFinIntent.EVIDENCE:
                # Evidence requests must resolve to a specific recorded object
                # through the current-run business-response plan.  The older
                # generic closed-claim fallback can summarize review records,
                # but using it here would make an unknown explicit target
                # appear answerable with unrelated evidence.
                return None
            candidate = build_deterministic_grounded_answer(
                grounding, request.question
            )
            if candidate is None:
                return None
            answer, citation_keys = candidate
            resolved_context = grounding.context
            follow_up_questions = grounding.suggested_questions[:4]
        verified = self._verify_answer(
            answer,
            citation_keys,
            grounding.records,
        )
        if verified is None:
            return None
        return self._complete(
            request,
            started,
            grounding,
            status=PrivateAskFinStatus.OK,
            answer=answer,
            citations=verified,
            failure_state=f"{failure_state}_recovered_from_closed_claims",
            provider=provider,
            model=model,
            model_version=model_version,
            classification=classification,
            resolved_context=resolved_context,
            follow_up_questions=follow_up_questions,
        )

    def _verify_answer(
        self,
        answer: str,
        citation_keys: Sequence[str],
        records: Sequence[GroundedFinSightRecord],
    ) -> Optional[tuple[PrivateCitation, ...]]:
        by_key = {item.citation_key: item for item in records}
        if not citation_keys or any(key not in by_key for key in citation_keys):
            return None
        inline = set(_INLINE_CITATION.findall(answer))
        if set(citation_keys) != inline:
            return None

        supported_claims = build_supported_claims(records)
        if not supported_claims:
            return None
        for sentence in _SENTENCE_SPLIT.split(answer):
            if not sentence.strip():
                continue
            sentence_citations = _INLINE_CITATION.findall(sentence)
            if not sentence_citations:
                return None
            leaves = tuple(
                leaf
                for key in sentence_citations
                for leaf in _string_fact_leaves(by_key[key].facts)
            )
            without_citations = _INLINE_CITATION.sub("", sentence)
            if (
                supported_claim_for_sentence(
                    without_citations,
                    sentence_citations,
                    supported_claims,
                )
                is None
            ):
                return None
            for match in _FINANCIAL_TOKEN.finditer(without_citations):
                token = match.group(0)
                claim_role = _context_role(
                    without_citations,
                    match.start(),
                    match.end(),
                )
                if not _fact_supports_token(token, claim_role, leaves):
                    return None
            if not _supports_directional_claim(without_citations, leaves):
                return None
            if not _supports_status_claim(without_citations, leaves):
                return None
            if not _supports_causal_claim(without_citations, leaves):
                return None
        return tuple(
            PrivateCitation(
                key=key,
                review_id=by_key[key].review_id,
                object_type=by_key[key].object_type,
                object_id=by_key[key].object_id,
                label=by_key[key].label,
                navigation_target=dict(by_key[key].navigation_target),
                evidence_details=_citation_evidence_details(by_key[key]),
            )
            for key in citation_keys
        )

    def _complete(
        self,
        request: PrivateAskFinRequest,
        started: float,
        grounding: Optional[PrivateAskFinGrounding],
        *,
        status: PrivateAskFinStatus,
        answer: str,
        citations: Sequence[PrivateCitation] = (),
        refusal_trigger: Optional[str] = None,
        failure_state: Optional[str] = None,
        provider: str = "finsight",
        model: str = "",
        model_version: str = "",
        classification: Optional[AskFinIntentClassification] = None,
        resolved_context: Optional[AskFinContext] = None,
        follow_up_questions: Sequence[str] = (),
    ) -> PrivateAskFinResult:
        elapsed = max(0, int((self._monotonic() - started) * 1000))
        effective_model = model or (
            "deterministic-intent-v1"
            if provider == "finsight"
            else self._config.model
        )
        mode = grounding.mode if grounding is not None else AskFinMode.APPLICATION_HELP
        retrieved = (
            tuple(item.citation_key for item in grounding.records)
            if grounding is not None
            else ()
        )
        effective_classification = classification or classify_ask_fin_intent(
            request.question,
            has_context=request.context is not None,
            prohibited=decision_boundary_trigger(request.question) is not None,
        )
        selected_context = _selected_context_for_question(
            effective_classification,
            request.context,
            request.question,
        )
        effective_classification = _apply_selected_context_intent(
            effective_classification,
            selected_context,
        )
        effective_context = resolved_context
        if effective_context is None and grounding is not None:
            effective_context = grounding.context
        if effective_context is not None and grounding is not None:
            effective_context = AskFinContext(
                review_id=effective_context.review_id,
                object_type=effective_context.object_type,
                object_id=effective_context.object_id,
                label=effective_context.label,
                validation_run_id=grounding.validation_run_id,
            )
        result = PrivateAskFinResult(
            status=status,
            mode=mode,
            answer_text=answer,
            citations=tuple(citations),
            review_id=request.review_id,
            reporting_period=(
                grounding.reporting_period if grounding is not None else ""
            ),
            validation_run_id=(
                grounding.validation_run_id if grounding is not None else None
            ),
            refusal_trigger=refusal_trigger,
            failure_state=failure_state,
            provider=provider,
            model=effective_model,
            model_version=model_version or effective_model,
            prompt_version=PRIVATE_ASK_FIN_PROMPT_VERSION,
            latency_ms=elapsed,
            retrieved_record_keys=retrieved,
            intent=effective_classification.intent.value,
            resolved_context=effective_context,
            follow_up_questions=tuple(follow_up_questions)[:4],
        )
        if not self._append_audit(request, grounding, result):
            # A displayed model answer without its mandatory local audit would
            # be unauditable financial guidance.  Preserve deterministic
            # refusal/outage messages, but never release a successful model
            # answer when the append-only interaction record did not commit.
            if result.status is PrivateAskFinStatus.OK:
                return replace(
                    result,
                    status=PrivateAskFinStatus.FAILED,
                    answer_text=SAFE_RESPONSE_FAILURE,
                    citations=(),
                    failure_state="audit_persistence_failed",
                )
        return result

    def _append_audit(
        self,
        request: PrivateAskFinRequest,
        grounding: Optional[PrivateAskFinGrounding],
        result: PrivateAskFinResult,
    ) -> bool:
        try:
            self._audit.append(
                {
                    "timestamp": self._clock.now(),
                    "user_id": request.user_id,
                    "review_id": request.review_id,
                    "validation_run_id": result.validation_run_id,
                    "scope": (
                        {
                            "review_id": request.context.review_id,
                            "object_type": request.context.object_type,
                            "object_id": request.context.object_id,
                            "label": request.context.label,
                        }
                        if request.context
                        else None
                    ),
                    "mode": result.mode.value,
                    "intent": result.intent,
                    "question": request.question,
                    "retrieved_records": list(result.retrieved_record_keys),
                    "provider": result.provider,
                    "model": result.model,
                    "model_version": result.model_version,
                    "prompt_version": result.prompt_version,
                    "response": result.answer_text,
                    "citations": [item.key for item in result.citations],
                    "refusal_trigger": result.refusal_trigger,
                    "latency_ms": result.latency_ms,
                    "failure_state": result.failure_state,
                    "status": result.status.value,
                    "resolved_context": (
                        {
                            "review_id": result.resolved_context.review_id,
                            "validation_run_id": (
                                result.resolved_context.validation_run_id
                            ),
                            "object_type": result.resolved_context.object_type,
                            "object_id": result.resolved_context.object_id,
                            "label": result.resolved_context.label,
                        }
                        if result.resolved_context is not None
                        else None
                    ),
                    "follow_up_questions": list(result.follow_up_questions),
                    "grounding_review_id": (
                        grounding.review_id if grounding is not None else None
                    ),
                }
            )
            return True
        except Exception:
            _log.error(
                "private Ask Fin audit append failed for review %s",
                request.review_id,
                exc_info=True,
            )
            return False

    def _authorize(self, user_id: str, review_id: str) -> None:
        if hasattr(self._authorization, "authorize"):
            self._authorization.authorize(user_id=user_id, review_id=review_id)
        else:
            self._authorization(user_id, review_id)

    def _require_active_review(self, review_id: str) -> None:
        if self._active_review_id is None:
            return
        active = self._active_review_id()
        if active and active != review_id:
            raise PrivateGroundingScopeError(
                "Ask Fin is scoped to the current active review."
            )

    def _require_private_local_configuration(self) -> None:
        if self._config.provider != "ollama":
            raise ValueError(
                "Private Ask Fin requires the verified local Ollama provider."
            )
        if is_cloud_style_model_alias(self._config.model):
            raise ValueError(
                "Private Ask Fin rejects cloud or remote Ollama model aliases."
            )
        try:
            normalized = normalized_loopback_http_url(self._config.base_url)
        except ValueError:
            raise ValueError(
                "Private Ask Fin permits only a loopback HTTP Ollama endpoint."
            )
        if normalized != self._config.base_url.rstrip("/"):
            raise ValueError(
                "Private Ask Fin permits only a normalized loopback Ollama endpoint."
            )

    @staticmethod
    def _scope_label(grounding: PrivateAskFinGrounding) -> str:
        values = [grounding.reporting_period, "review"]
        if grounding.context is not None:
            values.extend(
                (
                    grounding.context.object_type.title(),
                    grounding.context.label or grounding.context.object_id,
                )
            )
        return " · ".join(value for value in values if value)
