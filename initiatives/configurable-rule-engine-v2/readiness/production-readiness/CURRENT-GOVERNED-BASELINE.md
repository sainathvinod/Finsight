# FinSight Current Governed Baseline

**Record date:** 2026-07-29
**Status:** Preserved pre-stabilization baseline candidate; approval pending
**Release state:** **NO-GO**
**Production-code changes authorized by this record:** None

## 1. Source identity

| Item | Recorded value |
|---|---|
| Repository | `/Users/lakshminarayanana/Downloads/FinSight-AIConsulting` |
| Starting branch | `codex/configurable-rule-engine-v2` |
| Stabilization branch | `codex/production-readiness-stage1-2026-07-29` |
| Starting commit | `a298040a8408c04342818a65a186a0d72c87956a` |
| Starting commit time | `2026-07-25T19:38:24-04:00` |
| Starting subject | `feat(ui): rebuild Reviews home as rich per-review cards (walking-skeleton parity)` |
| Parent-repository remote | None configured |
| Release tag | None |
| Captured full-suite result | 4 failed, 1,212 passed, 2 subtests passed |
| Independent reproduction | Same counts; 77.90 seconds |

The starting commit alone does not contain the implemented V2 product. At
capture time, the working tree held 29 modified tracked files and 817 visible
untracked files, for 846 dirty paths, plus ignored generated/runtime/Release 1
areas. This record therefore treats the source/evidence archive—not the old
commit—as the complete preserved starting state.

## 2. Independent preservation

Snapshot root:

`/Users/lakshminarayanana/.codex/snapshots/FinSight-production-readiness-2026-07-29-a298040a`

| Preserved object | Size | SHA-256 | Verification |
|---|---:|---|---|
| `git-history.bundle` | 6.7 MB | `172bcdf9e6338d1949835497b5047e867e4a8d676069e1765fb927c7ea0de2e2` | `git bundle verify` PASS; complete history, four refs |
| `working-tree-source-and-evidence.tar.gz` | 241 MB | `b6d0effaf8afb9c168fcb678aba4ebdac55446f69920e49246177686d9d8e9b0` | 2,725 archived paths; checked for V2 engine, test, and closeout evidence |
| `production-readiness-program.txt` | source text | `6653b87ba7d23fa83bba14450f1abb69479661e9550c03ef9b1154e16998bc53` | Exact copy of first directive |
| `enterprise-rule-governance-reporting-and-distribution.txt` | source text | `1275c7dee199b1f08d76a7bdcedb1185b645e04039f0a16d417a6ac05accf92d` | Exact copy of Section 15 directive |

The working-tree archive excludes only `.git`, virtual environments, Python
bytecode, and reproducible test/lint/import caches. It includes production
source, tests, migrations, specifications, closeout evidence, generated
evidence, ignored fixtures, obsolete Release 1 outputs, and accidental output
for preservation and classification.

## 3. Starting repository health

- `git diff --check`: PASS before Stage 1 edits.
- `git fsck --no-dangling --no-reflogs --full`: PASS.
- Staged files: zero.
- Tracked diff: 4,481 insertions and 271 deletions across 29 files.
- Visible untracked files: 817.
- Untracked PNG evidence/captures: 585.
- `spec-driven` gitlink: `9a6b5e39d038b777ab7bffc479b904bed34b4a24`.
- Initial `.gitmodules`: missing.
- Authoritative V2 fixture workbooks: ignored by global `*.xlsx`.

The exact classification and disposition are in
[the source and artifact inventory](STAGE-01-SOURCE-AND-ARTIFACT-INVENTORY.md).

## 4. Baseline-only mechanical corrections

Stage 1 may correct reconstruction without changing product behavior:

1. `.gitmodules` now maps the pinned `spec-driven` gitlink to
   `https://github.com/sainathvinod/spec-driven-framework.git`.
2. `.gitignore` now permits only the two approved V2 synthetic fixture
   workbooks under the initiative fixture directory.
3. `.gitignore` identifies local generated evidence, outputs, accidental
   `--help`, and initiative screenshot trees as non-source. These remain
   preserved in the external archive.

These are candidate baseline mechanics. Their final source commit and clean
checkout verification remain part of the Stage 1 gate.

The Architecture-gate record identifies the accepted Technical Implementation
Plan by SHA-256
`93bca498e0e2a4605a1a778548640debccea1485a68e5bc3e4401a074cb68845`.
The current workspace copy hashes to
`8df4ae8e0f94995f010c0203465c777c0d14326d5ec6b72aab38f0e5eb9ad477`.
The accepted hash remains the historical Architecture authority; the current
copy is preserved as later delivery guidance but is not silently promoted to
an approved architecture revision. Approval of the Stage 1 hierarchy accepts
that classification, not the changed plan contents.

## 4.1 Candidate baseline commits

The preserved implementation has been divided into reviewable candidate
commits without changing the known product semantics:

| Commit | Purpose |
|---|---|
| `31f7f36e3f0be5c0fb301343512e8019d6bb2bcd` | V2 production source, migrations, dependency metadata, and reconstruction configuration |
| `f3232afde5776a43211d62e894294775b3acf643` | V2 automated tests, independent financial-oracle tooling, launch helpers, and screenshot-capture tooling |

The governed-document and fixture commit is
`0966ab2e90a9edbcd43908e08152c8223081bf87`.

An isolated `--no-hardlinks` clone at that commit successfully initialized the
pinned `spec-driven` submodule and reproduced both approved workbook hashes.
The full suite in that clone reproduced the same four known failures:
`4 failed, 1212 passed, 2 subtests passed in 82.23s`. See
[the clean reconstruction verification](STAGE-01-CLEAN-RECONSTRUCTION-VERIFICATION.md).

The exact pre-freeze manifest contains 1,760 classified paths:

| Manifest | SHA-256 |
|---|---|
| `STARTING-WORKTREE-MANIFEST.json` | `296bed9328f818d23764f93cc127150fec9e8da3a407796696613d8ea327af21` |
| `STARTING-WORKTREE-MANIFEST.tsv` | `6be3645a3991c891e53ec523040b88936167216c5e388965eafede9f82ccdcb0` |

## 5. Product behavior represented by the candidate

The preserved implementation includes:

- Review Management, Budget/GED intake and extraction, reviewed-copy
  verification, source evidence, audit, lifecycle, and Past Reviews;
- a configurable deterministic engine with five protected controls and optional
  rule lifecycle;
- recorded runs, results, findings, comparison, evidence, and replay;
- the current Overview, Financial Analysis, GED Detail, Findings, Explain This,
  and Review Summary experience; and
- local Ollama Ask Fin with loopback checks, grounding, citations, refusal,
  context isolation, and automatic readiness when the local provider is
  available.

This is a preservation statement, not a completion claim.

## 6. Known material baseline defects

The 2026-07-29 closeout remains authoritative current defect evidence:

- protected permanent identity differs between approved requirements and
  persistence;
- CORE-04 contains undocumented Budget/formula scopes;
- Overall Status/RAG and summary projections violate the approved policy;
- duplicate groups of three or more are undercounted;
- CORE-01/CORE-05 include later-period valid GED rows;
- successor reanalysis auto-publishes;
- post-validation source/edit successor behavior is incomplete;
- Advisory rules are modelled but not executable;
- the current full suite has four failures;
- legacy and V2 engine/result/AI paths coexist;
- source state was not reproducible from the old commit;
- modern enterprise PDF/XLSX, complete Audit History presentation, managed
  backup/restore, Windows packaging, automatic runtime/model provisioning,
  signing, lifecycle, and clean-machine qualification are incomplete.

No earlier verification PASS overrides these current defects.

## 7. Normative status

This file is a current Stage 1 status overlay. It does not rewrite frozen
Requirements or Architecture snapshots. Until Stage 1 approval:

- the two new directives govern preparation of the decision package;
- the existing approved Requirements/Architecture snapshots remain the
  effective implementation baseline where not contradicted;
- unresolved contradictions remain explicit decisions, not inferred defaults;
- Stage 2 and all production-code remediation remain blocked; and
- product and release status remain **NO-GO**.

## 8. Conditions to become the approved Stage 1 baseline

- complete source/artifact manifest and classifications;
- source, tests, migrations, governed documents, and approved synthetic fixtures
  committed on the stabilization branch;
- generated/runtime/obsolete/accidental artifacts excluded from source and
  preserved by hash;
- a clean-checkout reconstruction proves the fixture and submodule paths
  (**PASS at candidate commit `0966ab2`**);
- Stage 1 requirements/status overlays and traceability pass independent review;
- every Product Owner/Financial Control decision is approved;
- no ambiguity remains for Stage 2 deterministic behavior; and
- Product Owner records Stage 1 PASS.
