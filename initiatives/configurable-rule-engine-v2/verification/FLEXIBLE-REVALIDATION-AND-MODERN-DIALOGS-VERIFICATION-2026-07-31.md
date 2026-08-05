# Flexible Revalidation, Rule Governance, and Modern Dialogs — Verification

- **Date:** 2026-07-31
- **Scope:** Focused governed workflow and UX correction
- **Implementation:** Complete
- **Internal verification:** PASS
- **Independent financial-control review:** PASS
- **Independent UX/accessibility review:** PASS
- **Hands-on acceptance:** Pending Product Owner
- **Packaging:** Not started, as required

## Outcome

A Reviewer can now open **Review Rules / Revalidate** directly from a completed
financial review, retain the verified Budget/GED working data, govern optional
rules, confirm the exact active Rule Set, and create another deterministic
Validation Run without repeating upload, extraction, or data verification.

The implementation preserves the prior run and every immutable result. A
successor revalidation is explicitly presented as **Working** and does not move
the Published-generation pointer or append a supersession. Every validation
attempt receives one immutable Run ID at confirmation, before execution, and
that identity is retained through CONFIRMED, STARTED, FAILED, or COMPLETED
events. An asynchronous completion remains persisted to its originating review
but cannot be rendered into another review after the active review changes.

All operating-system-style message, text-entry, warning, and custom modal
construction in the desktop delivery layer was replaced with themed FinSight
in-application dialogs. File pickers remain native because they are operating
system resource selectors rather than product notices or confirmations.

## Acceptance mapping

| Requirement | Implemented and verified behavior | Status |
|---|---|---|
| Direct revalidation | Completed Review Results exposes **Review Rules / Revalidate** and reconstructs the already verified working data. | PASS |
| No repeated source workflow | Unchanged source fingerprint, verification basis, and dataset fingerprint are reused. Changed or unavailable source data fails closed with a reverification explanation. | PASS |
| Current Rule Set visible | Rules page shows active Rule Set identity, exact rules/versions, type, severity, lifecycle status, and configuration. | PASS |
| Draft explanation | Unresolved Draft banner identifies the rule and explains that it must be tested/activated or explicitly excluded. | PASS |
| Draft actions | Test, Activate, Exclude Draft Rule, Review, edit-as-new-version, disable, and retire paths are governed and audited. | PASS |
| Same-set rerun | A valid unchanged Rule Set may be confirmed and rerun; the UI explicitly identifies a same-rules rerun. | PASS |
| Exact pre-run confirmation | The in-app dialog lists working data, source reports, Rule Set ID/version, protected/optional/draft counts, prior Run ID, changes, and the exact included rule table. | PASS |
| Stable Run identity | Confirmation allocates the new Run ID; the same ID appears in confirmation, start, failure/completion, audit, and the retained run. | PASS |
| Rule selection integrity | The engine consumes only the sealed manifest. Draft, disabled, retired, excluded, hidden, stale, and superseded bindings do not execute. | PASS |
| Optional lifecycle | Draft → tested → active, version successor, disable, retire, explicit exclusion, and Superseded predecessor display are retained as append-only evidence. | PASS |
| Protected core rules | Delete/disable is unavailable; a protected-action dialog offers Return, Propose New Version, or Add Optional Rule without a destructive bypass. | PASS |
| Disabled-action explanations | Disabled controls use inline status, accessible description, tooltip, or actionable banner. | PASS |
| Run comparison | Added/removed/changed/unchanged rules and findings, version/status changes, and optional-rule effects are derived from retained recorded results. | PASS |
| Historical preservation | Prior runs, Rule Sets, rule versions, findings, and confirmation evidence remain immutable and reproducible. | PASS |
| Working vs Published | The new successor remains Working; the prior Published pointer remains unchanged and no premature supersession is recorded. | PASS |
| Ask Fin isolation | Revalidation clears stale conversation scope; run-specific context is rebuilt. A late result/error cannot surface under a newly active review. | PASS |
| Audit | Entry, proposal changes, draft exclusion, lifecycle actions, confirmation, start, completion/failure, prior/new IDs, and comparison are attributable and timestamped. | PASS |
| Modern dialogs | Information, Warning, Error, Confirmation, and Protected Action variants are frameless, theme-aware, keyboard-operable, Escape-safe, and restore focus. | PASS |
| Light/Dark | Rules, confirmation, protected action, retirement, and result-comparison states were captured and visually reviewed in both themes. | PASS |

## Financial-control hardening completed during independent review

The independent review found and closed four material boundary defects before
issuing PASS:

1. **Superseded optional predecessor:** activating an optional successor now
   appends the predecessor lifecycle transition and presents it as Superseded
   without rewriting history.
2. **Publication boundary:** successor revalidation no longer auto-publishes or
   supersedes the prior published generation.
3. **Pre-execution Run ID:** migration 0016 adds an immutable confirmation-bound
   Run identity and upgrades existing migration-0015 attempt evidence.
4. **Active-review isolation:** UI completion/error delivery is gated by the
   originating review even when a background validation finishes after the
   user changes reviews.

The migration-0015 confirmation, attempt, and exclusion ledgers were also
added to governed whole-review disposal inventory and deletion ordering. Their
ordinary append-only protections remain fail-closed; deletion is possible only
through the existing exact, separately confirmed disposal capability.

## Dialog and accessibility behavior

The shared dialog layer provides:

- semantic title and consequence text;
- safe default focus rather than defaulting to a destructive action;
- modal keyboard containment and Escape where cancellation is safe;
- focus restoration to the triggering control;
- accessible names and descriptions for the dialog and its actions;
- live Light/Dark theme refresh without native title-bar controls;
- required-input validation for governed text prompts; and
- consistent information, warning, error, confirmation, and protected-control
  visuals.

A source scan found no `QMessageBox`, `QInputDialog`, or direct `QDialog(...)`
construction remaining under `src/finsight/delivery/desktop`.

## Verification results

### Terminal full regression

```text
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
  --disable-warnings --maxfail=1
```

Result: **PASS — 1,300 passed, 1 skipped, 2 subtests passed in 186.40s**.

The single skip is the existing opt-in live local-Ollama integration case; the
deterministic rule, financial, persistence, UI, security, and local-only Ask Fin
test suites all ran in the terminal result.

### Independent financial-control suite

Result: **PASS — 65 passed in the independent rerun**.

Coverage included rule management, protected governance, financial review,
migrations 0015–0016, the independent financial oracle, all five core rules,
revalidation UI, and asynchronous active-review isolation.

### Independent UX/accessibility suite

Result: **PASS — 53 passed**.

Coverage included the direct revalidation route, draft status/actions,
disabled-action explanations, exact Rule Set confirmation, protected controls,
dialog semantics, keyboard/Escape/focus restoration, Light/Dark construction,
and the removal of native message/text/custom modal construction.

### Migration-head and upgrade verification

```text
.venv/bin/python -m pytest -q \
  tests/ai/test_migration_0002.py \
  tests/migrations/test_migration_0016.py \
  tests/application/test_reconstruction_architecture.py
```

Result: **PASS — 12 passed**.

### Architecture and static checks

- Import architecture: **PASS — 3 contracts kept, 0 broken across 240 files / 1,036 dependencies**.
- Task-scoped Ruff check: **PASS**.
- `git diff --check`: **PASS**.
- Screenshot capture harness: **PASS — 12 PNGs at 1440 × 1000**.
- Repository-wide Ruff is not a configured release gate and currently reports
  322 pre-existing style findings in legacy modules/tests outside this focused
  change; no automatic bulk rewrite was performed.

## Screenshot evidence

| State | Light | Dark |
|---|---|---|
| Draft rule and available actions | [Light](screenshots/flexible-revalidation-and-modern-dialogs/light/01-revalidation-draft-actions.png) | [Dark](screenshots/flexible-revalidation-and-modern-dialogs/dark/01-revalidation-draft-actions.png) |
| Active Rule Set ready | [Light](screenshots/flexible-revalidation-and-modern-dialogs/light/02-active-rule-set-ready.png) | [Dark](screenshots/flexible-revalidation-and-modern-dialogs/dark/02-active-rule-set-ready.png) |
| Exact pre-validation confirmation | [Light](screenshots/flexible-revalidation-and-modern-dialogs/light/03-pre-validation-rule-set-confirmation.png) | [Dark](screenshots/flexible-revalidation-and-modern-dialogs/dark/03-pre-validation-rule-set-confirmation.png) |
| Protected core action | [Light](screenshots/flexible-revalidation-and-modern-dialogs/light/04-protected-core-action.png) | [Dark](screenshots/flexible-revalidation-and-modern-dialogs/dark/04-protected-core-action.png) |
| Optional-rule retirement warning | [Light](screenshots/flexible-revalidation-and-modern-dialogs/light/05-optional-rule-retirement-warning.png) | [Dark](screenshots/flexible-revalidation-and-modern-dialogs/dark/05-optional-rule-retirement-warning.png) |
| New Working run and comparison | [Light](screenshots/flexible-revalidation-and-modern-dialogs/light/06-new-validation-run-comparison.png) | [Dark](screenshots/flexible-revalidation-and-modern-dialogs/dark/06-new-validation-run-comparison.png) |

## Task-scoped implementation inventory

The workspace also contains approved, uncommitted Ask Fin work from preceding
stages. The inventory below identifies files materially touched by this focused
revalidation/dialog correction rather than claiming every dirty-tree file was
created by this task.

### Requirements and verification

- `initiatives/configurable-rule-engine-v2/requirements/GOVERNED-V2-DELTA-2026-07-27.md`
- `initiatives/configurable-rule-engine-v2/specs/01-functional-requirements.md`
- `initiatives/configurable-rule-engine-v2/verification/FLEXIBLE-REVALIDATION-AND-MODERN-DIALOGS-VERIFICATION-2026-07-31.md`
- `initiatives/configurable-rule-engine-v2/verification/FLEXIBLE-REVALIDATION-AND-MODERN-DIALOGS-INDEPENDENT-FINANCIAL-CONTROL-REVIEW-2026-07-31.md`
- `initiatives/configurable-rule-engine-v2/verification/FLEXIBLE-REVALIDATION-AND-MODERN-DIALOGS-INDEPENDENT-UX-REVIEW-2026-07-31.md`
- `scripts/capture_revalidation_dialog_screenshots.py`

### Application and persistence

- `src/finsight/application/financial_review.py`
- `src/finsight/application/rule_management.py`
- `src/finsight/infrastructure/financial_review_repository.py`
- `src/finsight/infrastructure/review_disposal.py`
- `src/finsight/infrastructure/migrations/m0015_validation_rule_set_confirmation.py`
- `src/finsight/infrastructure/migrations/m0016_validation_run_identity.py`
- `src/finsight/infrastructure/migrations/runner.py`

### Desktop presentation

- `src/finsight/delivery/desktop/app.py`
- `src/finsight/delivery/desktop/components/__init__.py`
- `src/finsight/delivery/desktop/components/confirmation_dialogs.py`
- `src/finsight/delivery/desktop/controllers/app_controller.py`
- `src/finsight/delivery/desktop/main_window.py`
- `src/finsight/delivery/desktop/theme/qss.py`
- `src/finsight/delivery/desktop/views/financial_review_view.py`
- `src/finsight/delivery/desktop/views/private_ask_fin_dialog.py`
- `src/finsight/delivery/desktop/views/review_management_view.py`
- `src/finsight/delivery/desktop/views/rules_repository_view.py`

### Tests

- `tests/application/test_rule_management.py`
- `tests/application/test_financial_review.py`
- `tests/application/test_protected_rule_governance.py`
- `tests/application/test_reconstruction_architecture.py`
- `tests/fitness/test_integrated_financial_review_architecture.py`
- `tests/migrations/test_migration_0015.py`
- `tests/migrations/test_migration_0016.py`
- `tests/migrations/test_migrations.py`
- `tests/ai/test_migration_0002.py`
- `tests/ui/test_in_app_dialogs.py`
- `tests/ui/test_revalidation_rules_workflow.py`
- `tests/ui/test_validation_async_review_isolation.py`
- `tests/ui/test_integrated_financial_review.py`
- `tests/ui/test_protected_rule_governance.py`
- `tests/ui/test_review_deletion.py`
- `tests/ui/test_ask_fin_setup_and_drawer.py`
- `tests/ui/test_stage2_private_ask_fin_dialog.py`

## Known limitations

- Live VoiceOver/NVDA verification was not performed in the headless automated
  environment. Semantic accessibility and keyboard behavior passed automated
  checks; native screen-reader confirmation remains a hands-on/release-stage
  activity.
- The current task intentionally does not implement Windows packaging or begin
  the packaging stage.
- The distinct governed promotion workflow for a Working successor remains
  outside this focused correction. This task correctly prevents implicit
  publication and preserves the prior Published pointer.
- Screenshot evidence is generated locally in the repository's ignored
  verification screenshot directory and is present in this workspace.

## Independent reviews

- [Financial-control review](FLEXIBLE-REVALIDATION-AND-MODERN-DIALOGS-INDEPENDENT-FINANCIAL-CONTROL-REVIEW-2026-07-31.md): **PASS — no material financial-control defect remains**.
- [UX/accessibility review](FLEXIBLE-REVALIDATION-AND-MODERN-DIALOGS-INDEPENDENT-UX-REVIEW-2026-07-31.md): **PASS — no material UX/accessibility defect remains**.

## Hands-on review path

1. Launch from the repository root with `.venv/bin/finsight`.
2. Open the retained May 2026 review.
3. Select **Review Rules / Revalidate**.
4. Inspect a Draft rule, test it, then either activate it or explicitly exclude
   it from the proposal.
5. Select **Create New Validation Run** and inspect the exact confirmation.
6. Run validation and verify the result subtitle says **Working**, shows a new
   Validation Run ID, and states that the prior run remains preserved.
7. Return to Rules and inspect the comparison and protected-core action dialog.
8. Repeat dialog checks in Light and Dark appearance modes.

Stop after this hands-on review. Do not begin packaging from this task.
