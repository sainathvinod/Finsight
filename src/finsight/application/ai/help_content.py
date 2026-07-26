# Implements: E-09 Ask Fin — deterministic content (FR-091/100/101/102, AIC-07/08; specs/10 §4.1-4.5).
#   STATIC, deterministic content only: the two opening greetings, the canonical one-click questions
#   (review + product-help), and the product-help answers. Every canonical question also has a
#   deterministic ANSWER path (assembled elsewhere from read models) so Ask Fin works with AI off
#   (FR-101/102, NFR-063). Product-help answers explain the SYSTEM (grounded in FinSight's own approved
#   behaviour + rules-catalog posture) and touch no confidential financial data (AIC-08, low egress).
#   Nothing here invents a financial rule, threshold, or conclusion.
from __future__ import annotations

# Product-help greeting (before any review exists) — the Product Owner's default opening.
GREETING_PRODUCT_HELP = "Hi! I'm Fin.\nWhat can I help you with today?"

# Review-loaded opening (specs/10 §4.1, locked wording). {period} = the active cycle, e.g. "July 2026".
REVIEW_GREETING_TEMPLATE = (
    "\U0001F44B Hi, I'm Fin.\n\n"
    "I've got {period} loaded and ready to discuss.\n\n"
    "Ask me anything about the review, findings, budgets, reconciliation, or changes from previous "
    "months.\n\n"
    "⚠️ Every answer is grounded in the information available for this review and includes "
    "supporting sources. Be sure to review the evidence before making important business decisions. "
    "⚠️")

# Canonical review questions (specs/10 §4.2 / FR-101) — one-click prompts, each with a deterministic
# answer path (assembled from read models). Order is the spec order.
REVIEW_QUESTIONS = (
    ("why_finding", "Why was this finding created?"),
    ("what_changed", "What changed since last month?"),
    ("highest_risk", "Show the highest-risk items."),
    ("reconciliation", "Explain reconciliation issues."),
    ("summarize", "Summarize this review for leadership."),
    ("investigate_next", "What should I investigate next?"),
)

# Product-help topics (AIC-08) — available before any review; explain the SYSTEM, not financial data.
HELP_TOPICS = (
    ("what_is_finsight", "What is FinSight?"),
    ("files_needed", "What files does FinSight need?"),
    ("how_severity", "How does FinSight decide severity?"),
    ("what_reconciliation", "What is reconciliation?"),
    ("what_verified", "What does “verified” mean?"),
    ("data_privacy", "Is my data private?"),
    ("how_create", "How do I create a review?"),
)

# Deterministic product-help answers — factual descriptions of FinSight's own approved behaviour.
# (Trust > AI: severity/reconciliation are deterministic; corrections are human-made; nothing leaves
# the machine.) These are the S-21 help content; Fin may narrate them but the text stands on its own.
HELP_ANSWERS = {
    "what_is_finsight": (
        "FinSight turns your monthly financial files into a verified, auditable review. It reads your "
        "GED and Budget workbooks, lets you review and correct the extracted data, then runs "
        "deterministic checks to produce findings, a leadership report, and a full audit trail. "
        "Deterministic logic decides everything financial; I only help you understand the results."),
    "files_needed": (
        "FinSight needs two workbooks: a GED (General Expense Detail) file and a Budget Tracker file, "
        "both in Excel (.xlsx) format. An invoice is optional — it is captured for your records and "
        "the audit trail, but invoice analysis is not available in this release."),
    "how_severity": (
        "Severity (Critical, High, Medium, or Low) is assigned by fixed deterministic rules — never "
        "by AI. A finding's severity comes from the rule that raised it and the configured thresholds, "
        "so it is reproducible and traceable. I never create or change a severity."),
    "what_reconciliation": (
        "Reconciliation compares your Budget against the GED (actual spending) to check that recorded "
        "spending lines up with the approved budget. FinSight does this deterministically — the same "
        "inputs always produce the same result."),
    "what_verified": (
        "“Verified” means you explicitly reviewed the extracted data (and any corrections you "
        "made) and confirmed it. FinSight analyses only data you have verified, and records your "
        "attestation — including whether you made corrections — in the audit trail."),
    "data_privacy": (
        "Everything runs on this computer. FinSight never uploads your files or sends anything to the "
        "internet. If AI assistance is enabled, I use a LOCAL AI (Ollama) on this machine only — your "
        "review data never leaves it, and I only ever read your results, never change them."),
    "how_create": (
        "Choose “Create New Review”, pick the month the data is for, then add your GED and Budget "
        "files. Review and verify the extracted data (correct anything that's wrong), run the analysis, "
        "and FinSight produces the findings, report, and audit trail."),
}

# Persistent, non-dismissable grounding warning shown with Ask Fin (specs/10 §4.1).
GROUNDING_WARNING = ("Every answer is grounded in the information available and includes supporting "
                     "sources. Review the evidence before making important business decisions.")

# The honest "no evidence" behaviour (specs/10 §4.3) — Fin never guesses.
NO_EVIDENCE = ("I couldn't find evidence for that in this review. I only answer from verified data, "
               "approved findings, summaries, and traceable evidence — I don't guess or use outside "
               "information.")
