# Stage 01 — Source and Artifact Inventory

**Program:** FinSight Production-Readiness and Governed Release
**Stage:** Stage 1 — Baseline Freeze and SDD Reconciliation
**Inventory date:** 2026-07-29
**Inventory mode:** Read-only repository and filesystem inspection
**Status:** Inventory complete; clean Git baseline not yet established
**Approval state:** Input to the Stage 1 decision package; not a release approval

## 1. Purpose

This inventory records the exact FinSight source and artifact state that existed
before production-readiness implementation began. It separates source-of-truth
material from generated, temporary, obsolete, and accidental content so that the
project can create a clean and reproducible stabilization baseline without
discarding prior work.

This document does not authorize deletion. All cleanup or relocation must occur
only after the preservation evidence below is retained and the disposition is
approved.

## 2. Exact starting point

At the beginning of the inventory, the shared working tree was:

| Item | Observed value |
|---|---|
| Repository root | `/Users/lakshminarayanana/Downloads/FinSight-AIConsulting` |
| Starting branch | `codex/configurable-rule-engine-v2` |
| Starting commit | `a298040a8408c04342818a65a186a0d72c87956a` |
| Commit subject | `feat(ui): rebuild Reviews home as rich per-review cards (walking-skeleton parity)` |
| Commit date | `2026-07-25T19:38:24-04:00` |
| Tracked modified files | 29 |
| Visible untracked files | 817 |
| Total dirty paths represented with `-uall` | 846 |
| Staged files | 0 |
| Tracked diff | 4,481 insertions; 271 deletions |
| Parent-repository remotes | None configured |
| Tags pointing at the starting commit | None |

The original counts above came from:

```text
git status --porcelain=v1 -uall
```

They are the authoritative pre-baseline counts. A normal short status collapsed
untracked directories into 164 display entries; that compressed display is not
the individual file count.

During the shared Stage 1 work, a preservation branch named
`codex/production-readiness-stage1-2026-07-29` was created at the same commit.
Both branch references initially identified
`a298040a8408c04342818a65a186a0d72c87956a`. Creating that branch alone did not
capture modified or untracked content. The separately verified external
preservation set in Section 3 captures that working state.

## 3. Verified external preservation evidence

The preservation set is outside the repository so that later source cleanup
cannot erase the original state.

| Preservation artifact | SHA-256 | Verification |
|---|---|---|
| `/Users/lakshminarayanana/.codex/snapshots/FinSight-production-readiness-2026-07-29-a298040a/git-history.bundle` | `172bcdf9e6338d1949835497b5047e867e4a8d676069e1765fb927c7ea0de2e2` | `git bundle verify` passed |
| `/Users/lakshminarayanana/.codex/snapshots/FinSight-production-readiness-2026-07-29-a298040a/working-tree-source-and-evidence.tar.gz` | `b6d0effaf8afb9c168fcb678aba4ebdac55446f69920e49246177686d9d8e9b0` | SHA-256 verified; archive contains 2,725 paths |

The Git bundle preserves committed repository history. The working-tree archive
preserves source and evidence that were not represented by the starting commit.
Neither artifact should be treated as a release package. Both are baseline
recovery evidence and should remain access-controlled and immutable through the
Stage 1 gate.

Additional observed working-state fingerprints were:

| Inventory fingerprint | SHA-256 |
|---|---|
| Binary full-index tracked diff | `bfa971a7bfb47b7a64425f21afd5d0d86b3ffbbaec6df8510f3cb1905494dfd6` |
| Modified-path list | `ec7ebddd5df7c8f1f9cca0176260fd2fcff4409a5507cd969494731cf64048f9` |
| Visible untracked-path list | `963bca7022d8c85d2cb122c80f0a5a2225e850f12743cb95f5961cb7255e2258` |
| Ordered visible untracked path/content set | `388e698d5ef809f6f9f1eb53254bf56e094a69c7ef0d15c903a59091ff484dad` |

These fingerprints describe the original inventory observation. They are not
expected to match after approved Stage 1 documentation and baseline corrections
are added.

## 4. Visible working-tree classification

The following table classifies all 817 files that Git reported as untracked at
the start of the inventory. The counts total exactly 817.

| Original path area | Visible untracked files | Size observed | Classification | Baseline disposition |
|---|---:|---:|---|---|
| `initiatives/configurable-rule-engine-v2/**` | 438 | 51 MB | Governed V2 documentation and generated verification evidence | Commit approved Markdown/JSON as governed records. Retain screenshots through the approved evidence mechanism with hashes. |
| `artifacts/**` | 225 | 40 MB including ignored runtime files | Generated QA evidence and local runtime/test state | Preserve approved visual evidence outside production source. Exclude databases, WAL/SHM files, locks, and transient state. |
| `src/finsight/**` | 60 | Included in 5.8 MB source tree | Production source, including new application, domain, delivery, infrastructure, security, and AI components | Must be reviewed and represented by the controlled baseline commit. |
| `tests/**` | 57 | Included in 6.9 MB test tree | Automated unit, integration, migration, security, accessibility, fitness, and UI tests | Must be committed with the source behavior they verify. |
| `--help/**` | 21 | 2.7 MB | Accidental screenshot output | Preserve only in the external snapshot; do not include in the source baseline. |
| `scripts/**` | 14 | 392 KB directory total | Financial oracle, verification, screenshot, demo, and launch support | Commit governed oracle/verification utilities. Separate or exclude disposable demo/capture helpers unless needed to reproduce formal evidence. |
| `outputs/**` | 1 | 84 KB directory total | Synthetic workbook output manifest; workbook files were ignored | Reconcile with the governed fixture set. Do not use local generated output as an implicit test dependency. |
| `design-qa.md` | 1 | 15,743 bytes | Governed visual-review record stored outside the initiative | Preserve and relocate or supersede under the governed initiative structure. |
| **Total** | **817** | — | — | — |

### 4.1 Governed initiative contents

The 438 visible untracked initiative files consisted of:

- 86 Markdown specification, requirements, ADR, plan, task, review, readiness,
  fixture-description, and verification records;
- 351 PNG verification screenshots; and
- 1 JSON independent-oracle result.

Their primary directory distribution was:

| Initiative area | Files |
|---|---:|
| `verification/**` | 366 |
| `readiness/**` | 12 |
| `docs/**` | 12 |
| `reviews/**` | 10 |
| `specs/**` | 9 |
| `adr/**` | 8 |
| `tasks/**` | 7 |
| `requirements/**` | 4 |
| `fixtures/**` visible metadata | 4 |
| `plans/**` | 3 |
| `briefs/**` | 2 |
| `README.md` | 1 |

These records are part of the SDD history, but their prior untracked state meant
they did not yet have Git identity, reviewable history, or clean-checkout
reproducibility.

### 4.2 Generated image evidence

The original visible state contained 585 untracked PNG files:

- 351 in the governed initiative verification tree;
- 213 in `artifacts/**`; and
- 21 in the accidental root `--help/**` directory.

The 351 initiative images are potentially governed evidence. The 213 artifact
images include working comparisons and intermediate captures and require
deduplication against final verification records. The 21 `--help` files are not
source or approved evidence.

## 5. Tracked modifications

The 29 tracked modifications were distributed as follows:

| Area | Files | Classification | Baseline disposition |
|---|---:|---|---|
| `src/finsight/**` | 14 | Production source and application composition | Review and preserve in the controlled source baseline |
| `tests/**` | 8 | Existing automated tests changed for V2 behavior | Preserve with corresponding implementation |
| `.importlinter`, `DEPENDENCIES.md`, `build/versions.json`, `conftest.py`, `pyproject.toml`, `requirements-dev.txt`, `requirements.txt` | 7 | Architecture, dependency, build, and test configuration | Review as baseline configuration; do not mix with generated build output |
| **Total** | **29** | — | — |

No tracked modification was staged during the original inventory.

## 6. Production source, migrations, and tests

The combined untracked `src`, `tests`, and `scripts` files contained
approximately 58,403 lines. The largest individual concentrations were:

| File | Lines observed | Risk |
|---|---:|---|
| `src/finsight/delivery/desktop/views/financial_review_view.py` | 5,996 | Large UI/result composition surface with high regression and merge risk |
| `src/finsight/domain/financial_validation.py` | 2,817 | Deterministic financial-rule trust boundary |
| `src/finsight/delivery/desktop/views/rules_repository_view.py` | 2,766 | Rule-governance UI and policy presentation |
| `src/finsight/infrastructure/financial_review_repository.py` | 2,292 | Historical-run, evidence, and persistence behavior |
| `src/finsight/application/review_management.py` | 1,949 | Review lifecycle orchestration |
| `src/finsight/application/rule_management.py` | 1,734 | Rule lifecycle and protected-governance orchestration |

The 60 untracked production files were distributed as:

- 13 application files;
- 15 delivery/UI files;
- 6 domain files; and
- 26 infrastructure files.

The infrastructure set included 11 sequential migrations:

```text
m0004_v2_review_management.py
m0005_v2_source_intake.py
m0006_v2_integrated_review.py
m0007_configurable_rules_and_reanalysis.py
m0008_review_disposal.py
m0009_protected_core_governance.py
m0010_protected_core_governance_integrity.py
m0011_protected_request_baseline_binding.py
m0012_workspace_baseline_upgrade_governance.py
m0013_finding_explanations_and_review_status.py
m0014_private_ask_fin_audit.py
```

The migration runner was tracked and modified, and the test corpus contained
new tests for each of these migrations. A baseline must preserve the order,
upgrade path, integrity expectations, and matching tests together.

## 7. Ignored and generated areas

The 817 untracked count intentionally excludes ignored files. Ignored content
must not be added to the 817 or 846 figures.

| Ignored/generated area | Size or evidence | Classification | Required treatment |
|---|---:|---|---|
| `.venv/**` | 1.3 GB | Reproducible local environment | Exclude from Git and release evidence |
| `dist/**` | 239 MB | Obsolete Release 1 application, DMG, wheel, and zipapp output | Do not use as V2 release evidence; quarantine/remove only after preservation approval |
| Generated portions of `build/**` | Build tree 102 MB total | Release 1 PyInstaller/zipapp/DMG staging | Exclude generated staging; retain tracked source files such as `build/versions.json` and `build/validate_deps.py` |
| `.pytest_cache`, `.ruff_cache`, `.import_linter_cache`, `__pycache__` | Reproducible caches | Temporary | Exclude |
| `.DS_Store`, `test-results.txt` | Local operating-system/test output | Temporary | Exclude |
| `artifacts/**/*.db`, `*.db-wal`, `*.db-shm`, locks | Approximately 12 MB observed | Runtime/test state; potentially sensitive | Never commit; retain only under explicit encrypted evidence policy |
| Root and fixture `*.xlsx` | Globally ignored | Potentially sensitive source or approved synthetic fixture | Resolve through the fixture decision in Section 8; never force-add unreviewed financial files |

### 7.1 Obsolete Release 1 package output

The ignored Release 1 output included:

- `dist/FinSight.dmg`;
- `dist/FinSight.app`;
- `dist/FinSight/`;
- `dist/finsight-1.0.0-py3-none-any.whl`;
- `dist/finsight.pyz`;
- `build/pyinstaller/**`;
- `build/zipapp/**`;
- `build/dmg-stage/**`; and
- `build/bdist.*`.

The package files were dated 2026-07-25 and predated the uncommitted V2 source.
They cannot prove V2 packaging readiness. The tracked
`docs/DISTRIBUTION.md` also describes Release 1 wheel/zipapp behavior and must be
superseded or clearly scoped during documentation reconciliation.

## 8. Reproducibility blockers

### 8.1 Approved synthetic XLSX fixtures are ignored

Many current tests and verification scripts directly reference:

```text
initiatives/configurable-rule-engine-v2/fixtures/Sample_Budget_Report.xlsx
initiatives/configurable-rule-engine-v2/fixtures/Sample_GED_Report.xlsx
```

The repository-wide `*.xlsx` ignore rule excluded both files from Git.
Their approved synthetic fixture hashes are:

| Fixture | SHA-256 |
|---|---|
| `Sample_Budget_Report.xlsx` | `bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14` |
| `Sample_GED_Report.xlsx` | `2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c` |

Root-level files with the same names had different hashes:

| Root file | SHA-256 |
|---|---|
| `Sample_Budget_Report.xlsx` | `58150a234af1554973049dd91a97efaa6049e0d81231686709e1fd4d30deb49c` |
| `Sample_GED_Report.xlsx` | `3d9984ab867e63beb8ce14fc8dfb89559f5c9ed3dd2b55c84dc038bd84d0b9ca` |

Therefore, a clean checkout of the original commit cannot reconstruct the test
environment and must not substitute the root workbooks by filename alone.

The clean baseline must use one approved mechanism:

1. a narrowly scoped Git exception for attested synthetic fixtures;
2. Git LFS or another governed binary store with immutable hashes; or
3. a deterministic fixture-provisioning step that verifies the two hashes
   before tests run.

No confidential or unreviewed workbook may be committed under the synthetic
fixture exception.

### 8.2 `spec-driven` gitlink lacks a parent mapping

The parent repository tracked `spec-driven` as a gitlink:

```text
160000 9a6b5e39d038b777ab7bffc479b904bed34b4a24 spec-driven
```

The nested checkout was clean on `main` at that exact commit and identified
`https://github.com/sainathvinod/spec-driven-framework.git` as its remote.
However, the original parent repository did not contain `.gitmodules`, so:

```text
git submodule status
```

failed with `no submodule mapping found in .gitmodules for path 'spec-driven'`.
A clean clone could not reconstruct this governed framework dependency through
normal Git operations.

Stage 1 must explicitly choose one of:

- add and verify a governed `.gitmodules` mapping pinned to the recorded commit;
- vendor an approved immutable copy with provenance; or
- remove the gitlink through an approved dependency decision.

The dependency must not remain an unexplained local nested repository.

### 8.3 Branch-only preservation is insufficient

Both Stage 1 branch names initially pointed at the same old commit. Modified,
untracked, ignored, and generated files are not stored in a branch reference.
The verified external bundle and archive must be retained until the controlled
baseline commit has been independently reconstructed.

### 8.4 No parent-repository remote

At the original observation, `git remote -v` returned no parent-repository
remote. The local `.git` directory was the only committed-history copy visible
to the inventory. Before release work, the approved baseline and governed
evidence must have a second controlled storage location.

## 9. Disposition policy

| Classification | Meaning | Default Stage 1 disposition |
|---|---|---|
| Production source | Runtime application behavior | Review and commit |
| Tests | Executable verification of source behavior | Review and commit with source |
| Migrations | Ordered persistence evolution | Review, test, and commit atomically with the runner |
| Governed documentation | Requirements, architecture, ADRs, plans, reviews, approvals, verification records | Reconcile status and commit |
| Generated screenshots/evidence | Reproducible or approved visual proof | Retain in governed evidence storage with manifest and hashes |
| Synthetic fixtures | Attested non-confidential test inputs | Store through the approved reproducible fixture mechanism |
| Temporary artifacts | Caches, virtual environments, bytecode, local test output | Exclude |
| Runtime state | Databases, WAL/SHM files, locks, local configuration | Exclude; never treat as source |
| Obsolete Release 1 artifacts | Old wheel, zipapp, macOS application, DMG, and build staging | Quarantine or remove after approval; never label as V2 |
| Accidental files | Root `--help` screenshots and similar command-output errors | Preserve only in external snapshot, then exclude |

Disposition must be path-specific. A directory such as `build` or `artifacts`
contains both potentially retained evidence/source and disposable generated
material; broad destructive commands are prohibited.

## 10. Clean-baseline acceptance criteria

Stage 1 has a clean source baseline only when all of the following are true:

1. The starting commit, original counts, classifications, snapshot paths, and
   hashes in this inventory have been independently verified.
2. The external Git bundle and working-tree archive remain readable and their
   SHA-256 values match Section 3.
3. Every intended production source file is tracked by the controlled baseline
   commit; no production behavior depends on an untracked file.
4. All migrations from `m0004` through `m0014`, the runner, persistence changes,
   and their migration tests are represented together.
5. The test suite and governed oracle/verification tools required for the
   baseline are tracked and resolve only reproducible dependencies.
6. The two approved synthetic workbook fixtures can be obtained on a clean
   machine and must match their approved hashes before tests execute.
7. The `spec-driven` dependency can be reconstructed from the parent repository
   without relying on a pre-existing nested checkout.
8. Governed V2 requirements, architecture, ADR, decision, plan, review,
   readiness, and verification records have reconciled Draft, Proposed,
   Approved, Superseded, and Deferred status.
9. Approved screenshot evidence has a manifest, immutable hashes, and a defined
   storage location; intermediate/duplicate captures are not mixed with source.
10. Runtime databases, secrets, workbooks not explicitly attested as synthetic,
    caches, local environments, obsolete package output, and accidental files
    are not committed.
11. `dist` and generated build staging cannot be mistaken for the V2 release
    candidate.
12. A fresh checkout of the candidate baseline reports no unexpected tracked or
    untracked changes before tests.
13. The fresh checkout can provision dependencies and fixtures, execute the
    governed test command, and reproduce the recorded result without files from
    the developer's existing working directory.
14. The candidate baseline commit has a complete source/artifact manifest and a
    second controlled copy outside the developer's local repository.
15. No release tag is created until the Product Owner approves the Stage 1
    decision package and independent baseline verification passes.

Ignored files may exist in a developer workspace, but no test, build,
verification, packaging, or runtime claim may depend on ignored local content
that the clean-checkout process cannot reproduce.

## 11. Required controlled commit boundaries

After classification approval, the preservation branch should receive
reviewable commits in this order:

1. source, dependency configuration, and migrations;
2. tests and governed verification/oracle tooling;
3. reconciled SDD specifications, ADRs, plans, reviews, and readiness records;
4. the approved synthetic-fixture mechanism and fixture attestations; and
5. the evidence manifest and any approved evidence-store references.

Generated screenshots, runtime databases, accidental output, old package
binaries, and caches must not be swept into these commits through a broad
`git add .`.

## 12. Evidence commands

The inventory used read-only commands including:

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1 -uall
git diff --stat
git diff --numstat
git diff --check
git diff --cached --name-only
git ls-files --others --exclude-standard
git check-ignore -v <path>
git ls-files -s spec-driven
git submodule status
git remote -v
git worktree list --porcelain
git fsck --no-dangling --no-reflogs --full
```

`git diff --check` and the repository integrity check completed without an
error. Those results mean the observed Git objects and tracked patch were
internally readable; they do not make the dirty working state a clean baseline.

## 13. Inventory conclusion

The original FinSight state contained substantial implemented V2 work, tests,
migrations, governed documentation, and evidence, but most of that work was not
represented by the starting commit. The verified external preservation set now
protects that state from accidental loss.

The project may proceed with Stage 1 reconciliation and controlled baseline
construction. It must not claim that the current branch reference alone is the
baseline, must not begin production-behavior stabilization from an
unreproducible checkout, and must not delete or broadly clean files until the
disposition and Product Owner decisions are approved.
