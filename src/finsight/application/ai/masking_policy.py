# Implements: Phase 4C.3, NFR-016, FR-098, ADR-009
#
# Deterministic redaction patterns for the MaskingService. This module owns HOW each sensitive
# category is recognized in free text; masking.py owns WHICH structured fields are transformed.
#
# Policy (approved Phase 4C architecture; Trust > AI):
#   - Redaction, NOT reversible tokenization. There is NO token map. Category-specific replacement
#     tokens (e.g. [REDACTED_EMAIL]) are one-way and irreversible for AI-bound content.
#   - Explicit, named, compiled patterns with a fixed precedence. No generic long-digit rule.
#   - Deterministic financial facts are NEVER masked (amounts, percentages, variances, GL/accounting
#     account numbers, invoice numbers, findings, rules, source refs, fingerprints, review ids). The
#     patterns are specific enough (formats or required labels) that ordinary financial values do not
#     match — bare unlabeled digit runs are intentionally left alone.
#   - Pure and deterministic: no I/O, no persistence, no retention of original values.
from __future__ import annotations
import re
from typing import Dict, Tuple

from finsight.application.ai.errors import MaskingError
from finsight.domain.ai.contracts import MaskCategory

# One-way replacement tokens per category. Applying masking again must never alter these (see the
# token-guard split in apply_text) — redaction is idempotent.
TOKENS: Dict[MaskCategory, str] = {
    MaskCategory.EMPLOYEE_NAME: "[REDACTED_EMPLOYEE_NAME]",
    MaskCategory.EMAIL: "[REDACTED_EMAIL]",
    MaskCategory.PHONE: "[REDACTED_PHONE]",
    MaskCategory.TAX_ID: "[REDACTED_TAX_ID]",
    MaskCategory.BANKING_ID: "[REDACTED_BANKING_ID]",
    MaskCategory.ACTOR: "[REDACTED_ACTOR]",
}

# Precedence 1: already-redacted tokens are never re-processed. apply_text splits on this so prior
# tokens survive a second pass unchanged (idempotence), regardless of configured employee names.
_REDACTED_TOKEN_RE = re.compile(r"(\[REDACTED_[A-Z_]+\])")

# --- 2. EMAIL: conventional address, case-insensitive, valid-looking domain. Not full RFC. ---
_EMAIL_RE = re.compile(
    r"(?<![A-Za-z0-9._%+\-])"
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)

# --- 3. IBAN: two letters, two check digits, 15-34 total alphanumerics, bounded. ---
# Contiguous (electronic) form only — deliberately conservative so an IBAN pattern can never run past
# its own token and swallow adjacent words (which would mask non-sensitive text).
_IBAN_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{2}\d{2}[A-Za-z0-9]{11,30}(?![A-Za-z0-9])")

# Separator between an explicit label and its value: whitespace / punctuation and an optional
# "number"/"no."/"#" connector word. Never consumes the value's own characters.
_SEP = r"[\s:#=]*(?:number|nbr|no\.?|#)?[\s:#=]*"


def _labeled(label_alt: str, value: str) -> "re.Pattern[str]":
    """Compile a label-anchored pattern. The label + separator are preserved on replacement; only the
    value is redacted. Value is right-bounded so it cannot capture part of a longer token."""
    return re.compile(
        r"(?<![A-Za-z0-9])(?P<lbl>%s)(?P<sep>%s)(?P<val>%s)(?![0-9A-Za-z])"
        % (label_alt, _SEP, value),
        re.IGNORECASE,
    )


# --- 4. SWIFT/BIC: only with a SWIFT/BIC label (8 or 11 chars). ---
_SWIFT_RE = _labeled(
    r"swift(?:\s*/\s*bic)?(?:\s+code)?|bic(?:\s+code)?",
    r"[A-Za-z]{6}[A-Za-z0-9]{2}(?:[A-Za-z0-9]{3})?",
)
# --- 5. ROUTING / ABA: exactly 9 digits, only with a routing/ABA label. ---
_ROUTING_RE = _labeled(r"routing|aba", r"\d{9}")
# --- 6. BANK ACCOUNT: 6-17 digits, only with a banking-specific label. Generic "account" is NOT a
#        banking label (it may be a GL/accounting account), so it is intentionally excluded. ---
_BANK_RE = _labeled(
    r"bank account|bank acct|checking account|savings account",
    r"\d{6,17}",
)

# --- 7. TAX IDENTIFIERS: distinctive formats without a label; a bare 9-digit only with a tax label. ---
_SSN_FMT_RE = re.compile(r"(?<![\d\-A-Za-z])\d{3}-\d{2}-\d{4}(?![\d\-A-Za-z])")
_EIN_FMT_RE = re.compile(r"(?<![\d\-A-Za-z])\d{2}-\d{7}(?![\d\-A-Za-z])")
_TAX_LABELED_RE = _labeled(r"ssn|social security|ein|tax id|taxpayer id|tin", r"\d{9}")

# --- 8. PHONE: formatted forms without a label; a bare 10-digit only with a phone label. ---
_PHONE_LABELED_RE = _labeled(r"phone|telephone|tel|mobile|cell", r"\d{10}")
_PHONE_FMT_RE = re.compile(
    r"(?<![\d\-A-Za-z+])"
    r"(?:\+?1[\s\-])?"                       # optional country code: 1- / +1 / "1 "
    r"(?:\(\d{3}\)\s*|\d{3}[\s\-])"          # area code: (555) or 555- or "555 "
    r"\d{3}[\s\-]\d{4}"                      # exchange + line, separated
    r"(?![\d\-A-Za-z])"
)

# Static pipeline in approved precedence order. Employee-name patterns (precedence 9) are appended
# per-configuration at runtime because they depend on the configured list. Each entry: (pattern,
# category, is_labeled). Labeled patterns preserve the label/separator on replacement.
_PIPELINE: Tuple[Tuple["re.Pattern[str]", MaskCategory, bool], ...] = (
    (_EMAIL_RE, MaskCategory.EMAIL, False),
    (_IBAN_RE, MaskCategory.BANKING_ID, False),
    (_SWIFT_RE, MaskCategory.BANKING_ID, True),
    (_ROUTING_RE, MaskCategory.BANKING_ID, True),
    (_BANK_RE, MaskCategory.BANKING_ID, True),
    (_SSN_FMT_RE, MaskCategory.TAX_ID, False),
    (_EIN_FMT_RE, MaskCategory.TAX_ID, False),
    (_TAX_LABELED_RE, MaskCategory.TAX_ID, True),
    (_PHONE_LABELED_RE, MaskCategory.PHONE, True),
    (_PHONE_FMT_RE, MaskCategory.PHONE, False),
)


def _normalize_name(raw: str) -> str:
    """Strip and collapse internal whitespace to a single space. Returns '' for empty/whitespace."""
    return re.sub(r"\s+", " ", raw.strip())


def build_employee_patterns(names: Tuple[str, ...]) -> Tuple["re.Pattern[str]", ...]:
    """Compile one pattern per configured employee name. Matching is exact against the complete
    normalized name, whitespace-normalized, case-insensitive (no fuzzy, no NER, no ML). Boundaries
    reject partial-word matches (Jane Smithson) and an adjacent alphabetic word on either side
    (Mary Jane Smith) so a configured name is never masked inside a different, longer name. Duplicate
    normalized names are deduplicated; empty/whitespace-only entries raise MaskingError."""
    seen: Dict[str, str] = {}
    for raw in names:
        norm = _normalize_name(raw)
        if not norm:
            raise MaskingError("configured employee name is empty or whitespace-only")
        seen.setdefault(norm.casefold(), norm)     # dedupe by casefold; first wins
    patterns = []
    for key in sorted(seen):                       # deterministic compile/apply order
        tokens = seen[key].split(" ")
        name_re = r"\s+".join(re.escape(t) for t in tokens)
        patterns.append(re.compile(
            r"(?<![A-Za-z0-9])"
            r"(?P<pre>[A-Za-z]+\s+)?"              # adjacent leading word → part of a longer name
            r"(?P<name>%s)(?![A-Za-z0-9])"
            r"(?P<post>\s+[A-Za-z]+)?" % name_re,  # adjacent trailing word → part of a longer name
            re.IGNORECASE,
        ))
    return tuple(patterns)


def _apply(pattern: "re.Pattern[str]", category: MaskCategory, labeled: bool,
           text: str, counts: Dict[str, int]) -> str:
    token = TOKENS[category]

    def repl(m: "re.Match[str]") -> str:
        counts[category.value] = counts.get(category.value, 0) + 1
        if labeled:
            return m.group("lbl") + m.group("sep") + token
        return token

    return pattern.sub(repl, text)


def _apply_employee(pattern: "re.Pattern[str]", text: str, counts: Dict[str, int]) -> str:
    token = TOKENS[MaskCategory.EMPLOYEE_NAME]

    def repl(m: "re.Match[str]") -> str:
        if m.group("pre") or m.group("post"):
            return m.group(0)                      # adjacent word → different/longer name; leave as-is
        counts[MaskCategory.EMPLOYEE_NAME.value] = counts.get(MaskCategory.EMPLOYEE_NAME.value, 0) + 1
        return token

    return pattern.sub(repl, text)


def _mask_segment(text: str, employee_patterns: Tuple["re.Pattern[str]", ...],
                  counts: Dict[str, int]) -> str:
    for pattern, category, labeled in _PIPELINE:
        text = _apply(pattern, category, labeled, text, counts)
    for pattern in employee_patterns:
        text = _apply_employee(pattern, text, counts)
    return text


def apply_text(text: str, employee_patterns: Tuple["re.Pattern[str]", ...],
               counts: Dict[str, int]) -> str:
    """Redact all sensitive categories from free text, accumulating per-category counts. Existing
    [REDACTED_*] tokens are protected (precedence 1) so masking is idempotent: apply twice == once."""
    if not text:
        return text
    parts = _REDACTED_TOKEN_RE.split(text)          # even indices: text; odd indices: prior tokens
    for i in range(0, len(parts), 2):
        parts[i] = _mask_segment(parts[i], employee_patterns, counts)
    return "".join(parts)
