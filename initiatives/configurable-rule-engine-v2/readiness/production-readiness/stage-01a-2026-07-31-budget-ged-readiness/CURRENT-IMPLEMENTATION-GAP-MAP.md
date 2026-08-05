# Current Implementation Gap Map

**Prepared:** 2026-07-31  
**Method:** Read-only targeted implementation/test inspection  
**Purpose:** Requirements impact evidence, not implementation authorization  
**Tests run:** None

## Summary

| Area | Current state | SDD conclusion |
|---|---|---|
| SQLite/restart foundation | Partial and architecturally conflicting | Current SQLCipher store, migrations, lifecycle, corrections, runs, results, findings, and audit are durable. Complete source/verified rows are intentionally reconstructed, not stored. |
| Duplicate-review prevention | Partial | Same-period warning exists; exact source-pair block, likely predicate, prevalidation recheck, reasoned override, and concurrency claim do not. |
| Immutable revalidation | Implemented foundation | Successor runs preserve prior results and rule identities. Month-over-month comparison must remain a distinct domain concept. |
| Review-local optional rules | Conflicting | Review Rule Sets exist, but optional Rule Definitions are global and Delete maps to retirement. |
| Provider flexibility | Mostly new | Ollama-only local security is strong; external adapters/profiles/policies/credential references do not exist. |
| Ask Fin conversations | Partial | Grounding, citations, active-run isolation, refusal, and interaction audit exist; visible chat sessions are process memory and are cleared on revalidation. |
| June fixture/oracle | Missing | Only May fixtures/oracle exist. |
| Prior-period comparison | Missing/conflicting | Current comparison is same-review revalidation comparison, not May-versus-June financial comparison. |
| Five-area results UX | Strong partial foundation | Five tabs and financial drill-down exist; names, What's New, filters, and ten-section Leadership Summary are incomplete. |
| Integrated dialogs | Implemented foundation | Existing FinSight dialog component provides theme, focus, Escape, and accessibility behavior. |

## Evidence

### Durable persistence

- `src/finsight/infrastructure/migrations/m0005_v2_source_intake.py:30`
  intentionally excludes workbook bytes and detail rows.
- `src/finsight/application/review_working_set.py:5` defines selected source
  paths and normalized/verified data as reconstructed in-process state.
- `src/finsight/application/reconstruction.py:145` reopens the path hint,
  verifies the source fingerprint, and extracts again.
- `tests/application/test_reconstruction.py:83` asserts that source bytes and
  normalized rows are not stored.
- `src/finsight/infrastructure/secure_store.py:475` already enables foreign
  keys, WAL, full synchronous writes, secure deletion, and startup integrity
  checks.
- `src/finsight/infrastructure/migrations/runner.py:44` applies ordered
  transactional migrations through schema version 16.

Moving or deleting a source workbook currently leaves historical recorded
results available but prevents full data reconstruction/revalidation until a
matching source is rebound. S1A-D02 therefore changes architecture, not merely
schema coverage.

### Duplicate reviews

- `src/finsight/application/review_management.py:608` queries same-period
  review counts.
- `src/finsight/delivery/desktop/views/review_management_view.py:1070` presents
  a nonblocking reporting-period warning.
- `tests/ui/test_review_management.py:137` verifies that creation remains
  allowed.

No database identity claim currently combines department, period, Budget
fingerprint, and GED fingerprint.

### Optional rules

- `src/finsight/infrastructure/migrations/m0007_configurable_rules_and_reanalysis.py:46`
  gives Rule Definitions no owning Review ID.
- `src/finsight/application/rule_management.py:277` creates optional Drafts
  without review identity.
- `src/finsight/infrastructure/financial_review_repository.py:403` lists the
  latest optional definitions globally.
- `src/finsight/delivery/desktop/controllers/app_controller.py:696` maps Delete
  to retirement.

An ownership/scope migration and governed legacy backfill policy are required
if FR-226 is approved.

### Ask Fin providers and conversations

- `src/finsight/infrastructure/ai/private_config.py:73` and
  `src/finsight/domain/ai/contracts.py:188` allow Ollama/null provider paths.
- `src/finsight/infrastructure/ai/providers/ollama.py:126` enforces loopback,
  no proxies, redirect rejection, peer verification, and local-model identity.
- `src/finsight/delivery/desktop/ask_fin_preferences.py:28` stores nonsecret
  local convenience settings in `QSettings`, not a governed profile version.
- `src/finsight/delivery/desktop/views/private_ask_fin_dialog.py:694` keeps
  visible conversations in process memory.
- `src/finsight/delivery/desktop/views/private_ask_fin_dialog.py:1253` clears
  prior conversation state on revalidation rather than archiving it.
- `src/finsight/infrastructure/migrations/m0014_private_ask_fin_audit.py:11`
  persists interaction audit but does not define a durable conversation scope.

Provider flexibility and durable conversations require successor security/data
architecture. They are not presentation-only changes.

### Revalidation and comparison

- `src/finsight/application/financial_review.py:1193` creates a successor
  generation while preserving the prior published generation.
- `src/finsight/infrastructure/financial_review_repository.py:2375` retains run
  history and same-review run comparisons.
- `src/finsight/application/ai/private_grounding.py:914` currently interprets
  some `what changed` prompts through that same-review comparison.

May-versus-June comparison needs a separate comparison identity, policy,
projection, and two-run evidence corpus. Reusing the current revalidation
comparison would be a financial correctness defect.

### Results UX

- `src/finsight/delivery/desktop/views/financial_review_view.py:1493` exposes
  Overview, Financial Analysis, GED Detail, Findings, and Review Summary.
- `tests/ui/test_integrated_financial_review.py:118` asserts the current tabs.
- `src/finsight/delivery/desktop/views/financial_review_view.py:2515` explicitly
  reports that prior-period vendor comparison is unavailable.
- `src/finsight/delivery/desktop/views/financial_review_view.py:3887` lacks the
  requested GED finding-status and severity filters.
- `src/finsight/delivery/desktop/components/confirmation_dialogs.py:51`
  provides the reusable integrated FinSight dialog foundation.

## Missing high-risk verification

- exact, likely, concurrent, archived, and deleted duplicate-review cases;
- optional-rule isolation across reviews and approved delete/retire behavior;
- external provider adapters, authorization, credential-store failure, packet
  capture, and secret-leak scans;
- Ask Fin restart, prior-run archive, and provider-version isolation;
- June workbooks, June independent oracle, and May-to-June oracle;
- YTD/current-period comparison and two-period Ask Fin citations;
- updated five-area labels, What's New, GED filters, and Leadership Summary;
- operational backup/restore and replacement-machine recovery.

## Dependency order after approval

1. successor persistence, provider-security, rule-ownership/deletion,
   duplicate-identity, conversation, and comparison ADRs;
2. reviewed schema/migration and rollback plan;
3. bounded implementation workflows for persistence, rule ownership,
   duplicates, providers/conversations, fixtures/comparison, and results UX;
4. full governed verification and independent Financial Control,
   Security/Privacy, and UX review.

