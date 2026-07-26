# Implements: FR-026, FR-029, DEC-027 (explicit human verification attestation before analysis).
#   Target-product §12: the attestation wording BRANCHES on whether the reviewer corrected any extracted
#   value. The chosen statement is recorded in the audit trail (with the user, timestamp, whether
#   corrections existed, and the exact verified-dataset fingerprint) and analysis cannot proceed until
#   the human has attested. The statement is derived server-side from the persisted corrections — it is
#   never taken from untrusted UI text.
from __future__ import annotations

ATTESTATION_NO_EDIT = (
    "I have reviewed the extracted data and confirm that it is accurate. I understand that FinSight will "
    "base its validation and analysis on this verified data, and that this confirmation is recorded in "
    "the audit trail.")

ATTESTATION_EDITED = (
    "I have edited and reviewed the extracted data. I understand that FinSight will base its validation "
    "and analysis on my approved corrections, and that these changes will be recorded in the audit trail "
    "and report summary.")


def attestation_statement(has_corrections: bool) -> str:
    return ATTESTATION_EDITED if has_corrections else ATTESTATION_NO_EDIT
