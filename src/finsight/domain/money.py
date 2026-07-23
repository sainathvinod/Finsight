# Implements: NFR-059, FR-014, F-02-02  (ADR-003 exact decimal / determinism)
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP, Context, localcontext
from typing import Optional

MONEY_CONTEXT = Context(prec=28, rounding=ROUND_HALF_UP)
_PLACEHOLDERS = {"", ".", "-", "none", "n/a", "na"}

def to_decimal(raw) -> Optional[Decimal]:
    # locale-free parse; placeholders/blank -> None. No float is ever used.
    if raw is None:
        return None
    if isinstance(raw, Decimal):
        return raw
    s = str(raw).strip()
    if s.lower() in _PLACEHOLDERS:
        return None
    s = s.replace(",", "")
    try:
        with localcontext(MONEY_CONTEXT):
            return +Decimal(s)
    except Exception:
        return None

def money_str(d: Optional[Decimal]) -> str:
    if d is None:
        return ""
    with localcontext(MONEY_CONTEXT):
        return format(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")

def pct(numer: Decimal, denom: Decimal) -> Optional[Decimal]:
    with localcontext(MONEY_CONTEXT):
        if denom == 0:
            return None
        return (numer / denom * Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
