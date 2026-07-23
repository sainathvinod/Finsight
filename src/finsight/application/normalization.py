# Implements: FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, F-01-05, F-02-02 (Normalization service)
from __future__ import annotations
from typing import List, Dict, Any
from finsight.domain.money import to_decimal

SUBTOTAL_MARKER = "TOTAL FOR ACCOUNT"

def normalize_ged(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in rows:
        text = str(r.get("account_no") or r.get("dept_name") or "")
        if SUBTOTAL_MARKER in str(r.get("line_desc") or "") or SUBTOTAL_MARKER in text:
            continue  # structural noise: subtotal (FR-013)
        if not any(v not in (None, "") for v in r.values() if not str(v).startswith("_")):
            continue  # blank row
        acct = str(r.get("account_no") or "").strip()
        amt = to_decimal(r.get("amount"))
        out.append({"account": acct, "amount": amt, "raw_amount": r.get("amount"),
                    "confidence": "high" if amt is not None and acct else "low",
                    "source": r.get("_source", "")})
    return out

def normalize_budget(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in rows:
        acct = str(r.get("account_no") or "").strip()
        if not acct:
            continue
        out.append({"account": acct, "budget": to_decimal(r.get("budget")),
                    "atd": to_decimal(r.get("atd")), "source": r.get("_source", "")})
    return out
