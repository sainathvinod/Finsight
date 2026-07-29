# Stage 1 Clean Reconstruction Verification

**Date:** 2026-07-29
**Stage:** 1 — Baseline Freeze and SDD Reconciliation
**Verification target:** `0966ab2e90a9edbcd43908e08152c8223081bf87`
**Result:** **PASS for source reconstruction; known product regression remains RED**
**Stage 2 authorization:** None

## 1. Purpose

This verification proves that the candidate source, governed documents,
approved synthetic fixtures, and pinned framework dependency can be recreated
from Git without the original dirty working tree. It does not claim that
FinSight is financially correct, release-ready, or eligible for Stage 2.

## 2. Reconstruction procedure

An isolated temporary directory was created with `mktemp -d`. The repository
was cloned with hardlink reuse disabled:

```text
git clone --no-hardlinks \
  --branch codex/production-readiness-stage1-2026-07-29 \
  /Users/lakshminarayanana/Downloads/FinSight-AIConsulting \
  <isolated-directory>
```

The checked-out commit was:

```text
0966ab2e90a9edbcd43908e08152c8223081bf87
```

The clone was clean before and after verification.

## 3. Framework dependency

Command:

```text
git submodule update --init --recursive
```

Result: **PASS**.

The `spec-driven` submodule was fetched from the recorded `.gitmodules` URL and
checked out at:

```text
9a6b5e39d038b777ab7bffc479b904bed34b4a24
```

## 4. Approved synthetic fixtures

Both required workbook fixtures were present in the clean clone, were valid
OOXML ZIP packages, and matched the preserved source hashes:

| Fixture | SHA-256 |
|---|---|
| `Sample_Budget_Report.xlsx` | `bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14` |
| `Sample_GED_Report.xlsx` | `2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c` |

## 5. Reproduced full-suite state

The clean clone used the already qualified local development dependency
environment from the source workstation; dependency installation and a
clean-machine product install are intentionally deferred to the packaging and
qualification stages.

Command:

```text
QT_QPA_PLATFORM=offscreen PYTHONPATH=src \
  <qualified-development-python> -m pytest -q
```

Result:

```text
4 failed, 1212 passed, 2 subtests passed in 82.23s
```

The four failures exactly reproduce the preserved starting baseline:

1. 200% text-scaling width for the header Appearance control;
2. missing keyboard focus on the Settings Back button;
3. Ask Fin drawer width below its required minimum in one test geometry; and
4. a desktop-layer import of infrastructure from `ask_fin_preferences.py`.

The red result is expected and honest. No failure was fixed, skipped,
quarantined, or reclassified during Stage 1.

## 6. Conclusion

The candidate is reproducible as source and accurately reproduces its known
test state. This satisfies the mechanical clean-reconstruction criterion but
does not satisfy financial-correctness, stabilization, packaging, pilot, or
release gates.

> **Reconstruction verdict: PASS. Product/release verdict: NO-GO.**
