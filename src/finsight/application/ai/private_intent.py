"""Deterministic natural-language intent handling for private Ask Fin.

Intent classification runs before any review-evidence retrieval.  It is
deliberately small, auditable, and independent from the local language model:
the model never decides whether a question is social, supported, or a
prohibited financial decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class AskFinIntent(str, Enum):
    GREETING_SOCIAL = "greeting_or_social_acknowledgement"
    APPLICATION_HELP = "application_help"
    REVIEW_SUMMARY = "review_summary"
    FINDINGS_SUMMARY = "findings_summary"
    ACCOUNT = "account_question"
    VENDOR = "vendor_question"
    DEPARTMENT = "department_question"
    GED_TRANSACTION = "ged_transaction_question"
    EVIDENCE = "evidence_request"
    COMPARISON = "comparison_request"
    CLARIFICATION_FOLLOW_UP = "clarification_or_follow_up"
    UNSUPPORTED = "unsupported"
    PROHIBITED_DECISION = "prohibited_decision"


@dataclass(frozen=True)
class AskFinIntentClassification:
    intent: AskFinIntent
    uses_prior_context: bool = False
    clarification_required: bool = False

    @property
    def requires_financial_grounding(self) -> bool:
        return self.intent in {
            AskFinIntent.REVIEW_SUMMARY,
            AskFinIntent.FINDINGS_SUMMARY,
            AskFinIntent.ACCOUNT,
            AskFinIntent.VENDOR,
            AskFinIntent.DEPARTMENT,
            AskFinIntent.GED_TRANSACTION,
            AskFinIntent.EVIDENCE,
            AskFinIntent.COMPARISON,
            AskFinIntent.CLARIFICATION_FOLLOW_UP,
        }


_SPACE = re.compile(r"\s+")
_SOCIAL = re.compile(
    r"^(?:(?:hi|hello|hey|good\s+(?:morning|afternoon|evening))"
    r"(?:\s+fin)?|(?:thank\s+you|thanks|thank\s+you\s+fin)|"
    r"how\s+are\s+you)[!,.?\s]*$",
    re.IGNORECASE,
)
_AMBIGUOUS = re.compile(
    r"^(?:sc|what|what\?|explain|explain\?|help\?)$",
    re.IGNORECASE,
)
_FOLLOW_UP = re.compile(
    r"^(?:why\??|show\s+(?:me\s+)?more|tell\s+me\s+more(?:\s+about\s+that)?|"
    r"what\s+(?:does\s+)?this\s+mean\??|explain\s+this(?:\s+in\s+simple\s+terms)?|"
    r"what\s+caused\s+that\??|which\s+vendor\??|"
    r"what\s+should\s+i\s+(?:inspect|look\s+at)\s+next\??)$",
    re.IGNORECASE,
)
_CONTEXTUAL_FOLLOW_UP = re.compile(
    r"^(?:show\s+(?:me\s+)?(?:the\s+)?(?:evidence|rows?|sources?)"
    r"(?:\s+that\s+caused\s+this)?|"
    r"show\s+me\s+where\s+this\s+came\s+from|"
    r"which\s+rows?\s+(?:caused|support)\s+(?:this|that))[\s?.!]*$",
    re.IGNORECASE,
)
_APP_HELP = re.compile(
    r"\b(?:how\s+(?:do|can)\s+i|where\s+(?:do|can)\s+i|what\s+(?:does|files?)|"
    r"how\s+does)\b.*\b(?:finsight|create|start|upload|file|verify|extract|"
    r"validation|rules?|findings?|evidence|reopen|past\s+review|settings?|"
    r"ask\s+fin|workflow)\b|"
    r"\b(?:supported\s+files?|using\s+finsight|finsight\s+work|"
    r"how\s+can\s+finsight\s+help)\b",
    re.IGNORECASE,
)
_EVIDENCE = re.compile(
    r"\b(?:show|open|give|display|find)\b.*\b(?:evidence|source|rows?|cells?|"
    r"workbook|worksheet)\b|"
    r"\bwhat\s+evidence\b|"
    r"\b(?:recorded|supporting|source)\s+evidence\b|"
    r"\b(?:where\s+(?:did\s+)?this\s+(?:come|came)\s+from|"
    r"which\s+rows?\s+(?:caused|support)|exact\s+evidence|source\s+details?)\b",
    re.IGNORECASE,
)
_COMPARISON = re.compile(
    r"\b(?:compare|comparison|previous\s+run|prior\s+run|what\s+changed|"
    r"changed\s+after|revalidation)\b",
    re.IGNORECASE,
)
_ACCOUNT = re.compile(
    r"\b(?:account|accounts|which\s+account|budget\s+overrun|over\s+budget|"
    r"under\s+budget|variance)\b",
    re.IGNORECASE,
)
_VENDOR = re.compile(
    r"\b(?:vendor|vendors|supplier|suppliers|who\s+contributed|"
    r"who\s+drove|contributed\s+most)\b",
    re.IGNORECASE,
)
_DEPARTMENT = re.compile(r"\b(?:department|departments|dept)\b", re.IGNORECASE)
_GED_TRANSACTION = re.compile(
    r"\b(?:ged|transaction|transactions|journal|invoice|duplicate|"
    r"missing\s+(?:amount|field|data)|required\s+(?:amount|field|data))\b",
    re.IGNORECASE,
)
_FINDINGS = re.compile(
    r"\b(?:findings?|issues?|exceptions?|what(?:'s|\s+is)\s+wrong|"
    r"needs?\s+attention|look\s+at\s+first|inspect\s+first|"
    r"highest[-\s]priority|priorities)\b",
    re.IGNORECASE,
)
_REVIEW_SUMMARY = re.compile(
    r"\b(?:summar(?:y|ize)|main\s+points|overview|review\s+status|"
    r"what\s+should\s+i\s+know|how\s+is\s+(?:this|the)\s+review)\b",
    re.IGNORECASE,
)
_NAMED_ACCOUNT_DETAIL = re.compile(
    r"^\s*(?:tell\s+me\s+about|explain)\s+"
    r"(?!this\b|that\b|it\b|the\s+review\b)"
    r"[A-Za-z0-9][A-Za-z0-9 '&()/.,–—-]{2,}\s*[?.!]*$",
    re.IGNORECASE,
)
_UNSUPPORTED_EXTERNAL = re.compile(
    r"\b(?:approved\s+)?(?:future\s+)?(?:cloud\s+)?forecast\b|"
    r"\b(?:market\s+forecast|weather|stock\s+price|exchange\s+rate)\b",
    re.IGNORECASE,
)


def _clean(value: str) -> str:
    return _SPACE.sub(" ", value.replace("’", "'").strip())


def classify_ask_fin_intent(
    question: str,
    *,
    has_context: bool = False,
    prohibited: bool = False,
) -> AskFinIntentClassification:
    """Classify one message without reading review data or calling a model."""

    clean = _clean(question)
    follow_up_clean = clean.rstrip(" .!?")
    if prohibited:
        return AskFinIntentClassification(AskFinIntent.PROHIBITED_DECISION)
    if _SOCIAL.fullmatch(clean):
        return AskFinIntentClassification(AskFinIntent.GREETING_SOCIAL)
    if _AMBIGUOUS.fullmatch(clean):
        if has_context and clean.casefold().rstrip("?") in {"what", "explain"}:
            return AskFinIntentClassification(
                AskFinIntent.CLARIFICATION_FOLLOW_UP,
                uses_prior_context=True,
            )
        return AskFinIntentClassification(
            AskFinIntent.UNSUPPORTED,
            clarification_required=True,
        )
    if has_context and _FOLLOW_UP.fullmatch(follow_up_clean):
        return AskFinIntentClassification(
            AskFinIntent.CLARIFICATION_FOLLOW_UP,
            uses_prior_context=True,
        )
    if _FOLLOW_UP.fullmatch(follow_up_clean):
        return AskFinIntentClassification(
            AskFinIntent.UNSUPPORTED,
            clarification_required=True,
        )
    if _APP_HELP.search(clean):
        return AskFinIntentClassification(AskFinIntent.APPLICATION_HELP)
    if has_context and _CONTEXTUAL_FOLLOW_UP.fullmatch(clean):
        return AskFinIntentClassification(
            AskFinIntent.CLARIFICATION_FOLLOW_UP,
            uses_prior_context=True,
        )
    if _EVIDENCE.search(clean):
        return AskFinIntentClassification(
            AskFinIntent.EVIDENCE,
            uses_prior_context=has_context,
        )
    if _COMPARISON.search(clean):
        return AskFinIntentClassification(AskFinIntent.COMPARISON)
    if _UNSUPPORTED_EXTERNAL.search(clean):
        return AskFinIntentClassification(AskFinIntent.UNSUPPORTED)
    if re.search(
        r"\bwhy\s+is\s+(?:this|the\s+review)\s+incomplete\b",
        clean,
        re.IGNORECASE,
    ):
        return AskFinIntentClassification(AskFinIntent.FINDINGS_SUMMARY)
    if _FINDINGS.search(clean):
        return AskFinIntentClassification(AskFinIntent.FINDINGS_SUMMARY)
    if _VENDOR.search(clean):
        return AskFinIntentClassification(
            AskFinIntent.VENDOR,
            uses_prior_context=has_context,
        )
    if _ACCOUNT.search(clean):
        return AskFinIntentClassification(
            AskFinIntent.ACCOUNT,
            uses_prior_context=has_context,
        )
    if _DEPARTMENT.search(clean):
        return AskFinIntentClassification(
            AskFinIntent.DEPARTMENT,
            uses_prior_context=has_context,
        )
    if _GED_TRANSACTION.search(clean):
        return AskFinIntentClassification(
            AskFinIntent.GED_TRANSACTION,
            uses_prior_context=has_context,
        )
    if _NAMED_ACCOUNT_DETAIL.fullmatch(clean):
        # The entity itself is resolved later against the active review's
        # account index. An unmatched name produces no financial answer.
        return AskFinIntentClassification(
            AskFinIntent.ACCOUNT,
            uses_prior_context=has_context,
        )
    if _REVIEW_SUMMARY.search(clean):
        return AskFinIntentClassification(AskFinIntent.REVIEW_SUMMARY)
    if has_context and _FOLLOW_UP.search(follow_up_clean):
        return AskFinIntentClassification(
            AskFinIntent.CLARIFICATION_FOLLOW_UP,
            uses_prior_context=True,
        )
    return AskFinIntentClassification(AskFinIntent.UNSUPPORTED)


def social_response(question: str) -> str:
    lowered = _clean(question).casefold()
    if lowered.startswith("good morning"):
        opening = "Good morning."
    elif lowered.startswith("good afternoon"):
        opening = "Good afternoon."
    elif lowered.startswith("good evening"):
        opening = "Good evening."
    elif lowered.startswith(("thanks", "thank you")):
        opening = "You’re welcome."
    elif lowered.startswith("how are you"):
        opening = "I’m ready to help."
    else:
        opening = "Hello."
    return (
        f"{opening} I’m Fin. I can help explain this review, summarize findings, "
        "show source evidence, or answer questions about accounts, vendors, "
        "departments, and GED transactions."
    )


def clarification_response(question: str) -> str:
    clean = _clean(question)
    return (
        f'I’m not sure what you mean by “{clean}.” You can ask me to summarize '
        "this review, explain a finding, or show evidence for a specific account "
        "or transaction."
    )


def application_help_response(question: str) -> str:
    lowered = _clean(question).casefold()
    if "file" in lowered or "upload" in lowered:
        return (
            "FinSight uses one Budget Report and one GED Report for each review. "
            "Open a review, choose Upload & Extraction, and select the two Excel "
            "files; FinSight then checks their layout, department, and period."
        )
    if "verify" in lowered or "extract" in lowered:
        return (
            "After upload, use Verify Data to review the extracted Budget and GED "
            "values. Any reviewed edits are audited, reversible, and applied only "
            "to the working copy used for validation."
        )
    if "rule" in lowered or "validation" in lowered:
        return (
            "FinSight runs the active versioned rule set against the reviewed "
            "working data. Review the selected rules, then run validation to "
            "create preserved rule results, findings, and evidence."
        )
    if "evidence" in lowered or "finding" in lowered:
        return (
            "Open Findings after validation, then choose Show Evidence to see the "
            "Budget and GED records, source locations, compared values, and rule "
            "that produced the result."
        )
    if "reopen" in lowered or "past review" in lowered:
        return (
            "Choose Past Reviews from the sidebar, select the review period, and "
            "open or resume the preserved review."
        )
    return (
        "FinSight guides you through creating a review, uploading Budget and GED "
        "files, verifying extracted data, reviewing rules, running validation, "
        "and investigating findings with source evidence."
    )
