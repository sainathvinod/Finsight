# Independent Review — Final MVP Remediation

- **Date:** 2026-07-28
- **Initiative:** Configurable Rule Engine V2
- **Scope:** Final UX, rule management, evidence, visualization, disposal, and appearance remediation
- **Reviewer:** Codex independent review agent `/root/independent_final_review`
- **Initial snapshot:** Git `HEAD` `a298040a8408c04342818a65a186a0d72c87956a` plus dirty working-tree file-set digest `f5cf7e580fb6022c601be6b6a03c38f14d2ba2d1aba67f1469187715164d9608`
- **Initial snapshot qualification:** 771 tracked/untracked, non-ignored regular files; no immutable final commit is claimed
- **Initial verdict:** **FAIL — TWO MAJOR DEFECTS**
- **Intermediate recheck snapshot:** Same Git `HEAD`; 804 tracked/untracked, non-ignored regular files; canonical file-set digest `266beb6205d753a557c86e4b3db7b2d5f4bddddbc60709622bc646310c6849bb`
- **Final recheck snapshot:** Same Git `HEAD`; 843 tracked/untracked, non-ignored regular files; canonical file-set digest `8045cfd5978f5ac820ac919e91fd34444ae663c9c739cd2d6eccb0dd08bb107d`
- **Material-defect recheck:** **PASS — BOTH MAJOR DEFECTS CLOSED**
- **Final verdict:** **PASS**
- **Windows packaging:** Out of scope for this review

## Review scope

The reviewer independently assessed:

1. the visible seven-step workflow;
2. Welcome, upload, Verify Data, Rules Repository, results, Findings, analytics,
   review-history, and disposal behavior;
3. the deterministic ledger as the only source of financial conclusions;
4. the exact five protected baseline controls and configurable-rule lifecycle;
5. reviewed-value provenance, reversibility, attribution, and source immutability;
6. the approved 986-result protected oracle and five expected findings;
7. structured rule/finding evidence and source navigation;
8. deterministic chart/table projections;
9. governed review disposal and unrelated-review/source-file isolation;
10. Light, Dark, and System Default behavior;
11. keyboard, focus, non-color cues, text scaling, and resizing; and
12. the explicit exclusion of Windows packaging.

## Initial evidence examined

| Evidence | Location or command | Result |
|---|---|---|
| Source snapshot | Git `HEAD` plus file-set digest recorded above | Qualified dirty snapshot; no immutable commit claimed |
| Focused independent test run | `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_financial_validation.py tests/application/test_financial_review.py tests/application/test_rule_management.py tests/application/test_review_disposal.py tests/application/test_authorization.py tests/ui/test_appearance.py tests/ui/test_integrated_financial_review.py tests/ui/test_review_deletion.py tests/accessibility` | **62 passed in 16.75s** |
| Import architecture | `PYTHONPATH=src .venv/bin/lint-imports --config .importlinter --no-cache` | **3 contracts kept; 0 broken** |
| Whitespace integrity | `git diff --check` | **PASS** |
| Independent capture | `QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/capture_mvp_screenshots.py /tmp/finsight-independent-capture.Jj8IOW` | **66 captures: 33 Light + 33 Dark; System Default resolved Light** |
| Synthetic projection | Direct runtime and fixture-oracle inspection | **986 protected scopes = 979 PASS / 5 FAIL / 2 NOT_EVALUATED; five findings; missing 1, duplicate 1, unmapped 1** |
| Light/Dark/responsive evidence | Final primary and 1180 × 860 galleries | No additional material visual defect |
| Disposal isolation | Application, UI, authorization, and migration tests | No additional material defect |

## Initial findings

| ID | Severity | Area | Observation | Required remediation | Final status |
|---|---|---|---|---|---|
| IR-01 | Major | Appearance / Settings | REM-FR-019 requires Light, Dark, and System Default in a Settings shell destination. The reviewed snapshot exposed only the compact header Theme menu and had no Settings page. | Add a keyboard-accessible Settings destination using the shared Appearance manager/control; preserve System following and persistence; add focused tests and Light/Dark evidence. | **CLOSED ON RECHECK** |
| IR-02 | Major | Protected baseline governance | Normal protected mutations were blocked and RBAC/separation policy existed, but the reviewed snapshot lacked the required protected candidate/request, different-person approval/rejection, immutable activation/version history, persistence, and governed UI path. | Implement the Rule Administrator request → different Financial Control Approver decision → immutable version/rule-set activation workflow, including rejection and bypass tests. | **CLOSED ON FINAL RECHECK** |

No Blocker or Critical defect and no other material defect was found.

## Initial known evidence limitations

- Native screen-reader smoke remains a hands-on desktop activity.
- System visual evidence is headless plus automated operating-system change tests.
- Missing-source recovery has automated persistence coverage but no final manual
  demonstration.
- Windows packaging is explicitly outside this gate.
- The reviewed source was a digest-qualified dirty tree rather than an immutable
  commit.

## Material-defect recheck

- **Recheck required:** Yes, limited to IR-01 and IR-02 and their regression impact
- **Intermediate recheck:** IR-01 closed. IR-02 remained partially open because
  the first remediation created a future Protected Baseline Version but supplied
  no governed path to apply it to an existing workspace, create a successor
  workspace Rule Set Version, and revalidate the retained review.
- **Final rechecked snapshot:** Git `HEAD`
  `a298040a8408c04342818a65a186a0d72c87956a`; 843 tracked/untracked,
  non-ignored regular files; canonical path-plus-NUL-plus-bytes SHA-256
  `8045cfd5978f5ac820ac919e91fd34444ae663c9c739cd2d6eccb0dd08bb107d`.
  This review-record update was appended after snapshot qualification and is
  therefore not part of that implementation/evidence digest.

### Independent recheck evidence

| Evidence | Command or artifact | Result |
|---|---|---|
| Final source qualification | Independent canonical file-set digest recomputation and `git rev-parse HEAD` | **Exact match: 843 files and the recorded final digest/HEAD** |
| Focused regression | `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/ui/test_appearance.py tests/application/test_protected_rule_governance.py tests/application/test_authorization.py tests/security/test_workspace_baseline_upgrade_security.py tests/migrations/test_migration_0012.py tests/migrations/test_migrations.py tests/ui/test_protected_rule_governance.py tests/ui/test_integrated_financial_review.py tests/accessibility` | **82 passed in 24.00s** |
| Working-tree integrity | `git diff --check` | **PASS** |
| Independent visual recapture | `QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/capture_mvp_screenshots.py /tmp/finsight-final-recheck.1gSmax` | **96 captures: 48 Light + 48 Dark at 1280 × 900; System Default resolved Light** |
| Settings evidence | Primary and responsive `01a-settings-appearance.png` in Light and Dark; focused appearance/accessibility tests | **IR-01 CLOSED** |
| Protected-change governance | Screens `13a`–`13e`; protected application, migration, authorization, and UI tests | **Immutable request/qualification, different-person decision, activation, retained history, and global Approver route verified** |
| Existing-workspace adoption | Screens `28a`–`28i`; workspace-upgrade application, migration 0012, authorization, security, UI, and reanalysis tests | **Exact request-time Rule Set/run/target, distinct approval, successor Rule Set, preserved optional bindings/history/other workspaces, and Reviewer revalidation verified** |
| Authorization and audit boundary | Production-composed role tests and exact NFR-090 event-schema assertions | **Self-decision records one DENY and zero ALLOW with no mutation; request/rejection/application evidence is attributable, nonblank, transition-complete, and exactly once** |

### Recheck disposition

- **IR-01:** **CLOSED.** Settings is a keyboard-accessible shell destination
  backed by the same persisted Light, Dark, and System Default appearance
  manager used by the header control. Light/Dark and responsive evidence is
  readable, and System following remains automated-test evidence.
- **IR-02:** **CLOSED.** The five protected controls now use an immutable
  candidate/request/different-person decision/activation lifecycle. A separate
  governed existing-workspace adoption path binds the exact retained Rule Set,
  Validation Run, source baseline, and target baseline; approval creates one
  successor workspace Rule Set without rewriting prior runs or other
  workspaces, and Reviewer revalidation creates the required successor
  `RULESET_REANALYSIS` Review Version and Validation Run.
- **Remaining material findings:** **None.**

## Final verdict

**PASS — BOTH INITIAL MAJOR DEFECTS ARE CLOSED.**

The initial review verdict remains historically **FAIL** for its recorded
snapshot. The intermediate recheck closed IR-01 but correctly kept IR-02 open
until existing-workspace baseline adoption and revalidation were implemented.
The final digest-qualified snapshot passes the bounded independent recheck with
no remaining material defect. Native screen-reader smoke, Project Owner hands-on
acceptance, and Windows Packaging and Release remain separate activities; no
claim is made that any of them has passed.
