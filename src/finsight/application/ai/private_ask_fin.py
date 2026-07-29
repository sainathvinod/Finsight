"""Stage 2 private Ask Fin orchestration.

The service is intentionally separate from the deterministic Rule Engine.  It
can explain only sealed V2 projections and fingerprint-matched source records.
It has no external retrieval seam and no provider fallback.
"""
from __future__ import annotations

import re
import time
from dataclasses import replace
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
from finsight.application.ai.private_prompt import build_private_prompt
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
    "I do not have enough recorded evidence in this review to answer that question."
)
PREVALIDATION_FINANCIAL = (
    "Validation results are not available yet. Complete the review and run "
    "validation first. I can help you get to that step."
)
DECISION_REFUSAL = (
    "I can’t make or authorize that decision. I can summarize the recorded "
    "facts, show the supporting evidence, explain the applicable rule, and "
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
    r"(?:[-−+]?\$[\d,]+(?:\.\d+)?|[-+]?\d+(?:\.\d+)?%|"
    r"\b\d{4}-\d{2}-\d{2}\b|"
    r"(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?(?![\w]))"
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
            or path[-1].casefold() in {"findings", "source_row", "row"}
            or (
                len(path) >= 2
                and path[-2].casefold().endswith("_rows")
            )
        )
    ):
        output.append((".".join(path), str(value)))
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
        "variance": "variance",
        "variance_label": "variance",
        "budget_utilization": "utilization",
        "budget_utilization_label": "utilization",
        "amount": "amount",
        "amount_label": "amount",
        "invoice_amt": "invoice_amount",
        "invoice_amount": "invoice_amount",
        "invoice_amt_label": "invoice_amount",
        "invoice_amount_label": "invoice_amount",
        "findings": "count",
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
    ("account", re.compile(r"\baccount\b", re.IGNORECASE), 2),
    ("department", re.compile(r"\bdepartment\b|\bdept\b", re.IGNORECASE), 2),
    ("source_row", re.compile(r"\bsource\s+row\b|\brow\b", re.IGNORECASE), 2),
    ("date", re.compile(r"\bdate\b", re.IGNORECASE), 2),
    (
        "period",
        re.compile(r"\breporting\s+period\b|\bfiscal\s+period\b|\bperiod\b", re.IGNORECASE),
        2,
    ),
    ("count", re.compile(r"\bcount\b|\btransactions?\b|\bfindings?\b", re.IGNORECASE), 3),
)


def _context_role(text: str, start: int, end: int) -> Optional[str]:
    token = text[start:end]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", token):
        return "date"
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
        ("over budget", ("over_budget", "variance", "actual", "explanation")),
        ("under budget", ("variance", "actual", "explanation")),
    ):
        if phrase not in normalized:
            continue
        supported = False
        for path, value in leaves:
            path_normalized = path.casefold()
            if any(fragment in path_normalized for fragment in expected_fragments):
                if phrase in value.casefold() or (
                    phrase == "over budget" and "exceeded bgt" in value.casefold()
                ) or "over_budget" in path_normalized:
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
        grounding = self._grounding.context(
            review_id, selected_context=context
        )
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
        try:
            self._authorize(request.user_id, request.review_id)
            self._require_active_review(request.review_id)
            if request.context and request.context.review_id != request.review_id:
                return self._complete(
                    request,
                    started,
                    grounding,
                    status=PrivateAskFinStatus.REFUSED,
                    answer=DECISION_REFUSAL,
                    failure_state="context_review_mismatch",
                    refusal_trigger="cross_review_context",
                )
            grounding = self._grounding.context(
                request.review_id,
                question=request.question,
                selected_context=request.context,
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
            )
        except PrivateGroundingError:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.UNANSWERABLE,
                answer=INSUFFICIENT_EVIDENCE,
                failure_state="sealed_grounding_unavailable",
            )
        except Exception:
            # Authorization failures and unknown review identifiers fail closed.
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.REFUSED,
                answer="Ask Fin is not authorized for this review.",
                failure_state="authorization_denied",
            )

        trigger = decision_boundary_trigger(request.question)
        if trigger:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.REFUSED,
                answer=DECISION_REFUSAL,
                refusal_trigger=trigger,
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
            )

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
            )
        except ProviderError:
            return self._complete(
                request,
                started,
                grounding,
                status=PrivateAskFinStatus.FAILED,
                answer=SAFE_RESPONSE_FAILURE,
                failure_state="local_model_error",
            )

        raw_model_version = str(
            raw.metadata.get("model_version") or raw.model
        )
        try:
            validated = self._validator.validate(
                raw.text, schema_version=prompt.schema_version
            )
        except ResponseFormatError:
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
        provider: str = "ollama",
        model: str = "",
        model_version: str = "",
    ) -> PrivateAskFinResult:
        elapsed = max(0, int((self._monotonic() - started) * 1000))
        effective_model = model or self._config.model
        mode = (
            grounding.mode
            if grounding is not None
            else AskFinMode.APPLICATION_HELP
        )
        retrieved = (
            tuple(item.citation_key for item in grounding.records)
            if grounding is not None
            else ()
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
            raise ValueError("Private Ask Fin requires the verified local Ollama provider.")
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
