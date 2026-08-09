# FinSight 2.0.0 — Packaging Report

**Date:** 2026-08-07 · **Target:** Windows x64 (primary) · **Verdict:** release pipeline complete;
installer produced by CI on `windows-latest`.

---

## 1. Release candidate identity

The active repository source is the Version 2 candidate: the V2 review-management workflow,
`FINSIGHT-CORE-2.0` protected rule set, `v2_*` persistence schema, and the Stage 2 private Ask Fin
surface. The version was stamped **1.0.0 → 2.0.0** across `pyproject.toml`, the Windows version
resource, and the installer.

No Release 1 artifact was inspected, reused, or packaged. The `dist/` directory contains stale R1
output and is excluded from this release; the pipeline rebuilds `dist/` from source on every run.

## 2. What the recipient does

Download `FinSight-2.0.0-Setup.exe` → run it → launch FinSight. No administrator rights, no
Python, Qt, SQLite, SQLCipher, environment variables, or terminal.

## 3. Windows blockers found and fixed

| # | Blocker | Resolution |
|---|---|---|
| 1 | **App could not start on any clean Windows machine.** `enforce_store_permissions` always ran `icacls` granting a `FinSight Users` group that does not exist on a fresh machine → `SecureStoreError` at startup. | The single-user path now grants the signed-in account, names SYSTEM by well-known SID (`*S-1-5-18`, locale-independent), and leaves inheritance intact so a partial grant cannot lock a reviewer out of their own data. |
| 2 | **Two instances could open the same store.** `msvcrt.locking()` locks from the current file position and the lock file is opened in append mode, so a second instance locked a *different* byte and acquired successfully — two processes sharing a single-writer SQLite store. | Seek to byte 0 before locking. Verified: reverting the fix makes the regression test fail exactly as the defect predicts. |
| 3 | **Every icon would render blank.** QtAwesome ships 24 font/charmap files as package data and has no PyInstaller hook. | Collected explicitly in the spec; CI fails the build if the fonts are absent from the bundle. |
| 4 | **Console windows would flash** in a windowed build. | Helper processes run with `CREATE_NO_WINDOW`; the executable is built `console=False`. |
| 5 | **Migrations could silently drop out of a build.** `collect_submodules` returned nothing because `finsight` was not importable at spec-evaluation time. | The spec puts `src` on `sys.path` first; all 18 migration modules now collect. |
| 6 | **No store could be opened on Windows at all.** `PRAGMA cipher_memory_security = ON` made SQLCipher's memory-sanitising allocator overflow the 1 MB default main-thread stack; the process died with `Windows fatal exception: stack overflow` on the first statement after the pragma — a hard crash with no Python traceback. | Memory security is enabled only where the platform can run it. See the security note below. |

### Security note — SQLCipher memory security on Windows

`cipher_memory_security` is a **runtime** memory-handling setting: it makes SQLCipher zero and
lock its working memory. Unlike page size, KDF iterations, and the HMAC/KDF algorithms it does
**not** participate in the on-disk format, so disabling it on Windows leaves the ciphertext
byte-compatible with macOS and a store portable between them (NFR-029) — asserted by test.

The cost is confined to memory hygiene: on Windows, freed key and page buffers are not explicitly
zeroed and may reach the page file. At-rest encryption, the KDF, the HMAC, and the key-protection
model are all unchanged. Revisit if a SQLCipher build lands whose Windows memory-security path no
longer overflows the stack, or if the application is moved onto a thread with a larger stack.

## 4. Runtime provisioning decision (PKG-02)

Recorded as **DEC-037**. Ollama and `llama3.2:3b` are **provisioned, not bundled**:

- **Licensing** — Ollama is MIT and redistributable; `llama3.2:3b` carries the separate Meta Llama
  Community License. Shipping weights in a commercial installer needs counsel sign-off that
  PKG-05 records as absent.
- **Size** — bundling gives a ~3 GB installer, against a qualification target of restricted
  8–16 GB corporate laptops.
- **Optionality** — FR-095 requires the deterministic review to be complete with no AI provider.
  An AI runtime must never be an install precondition.

`provision_ask_fin.ps1` detects Ollama, installs it silently if missing, starts the loopback
service, pulls the model, and verifies it — offered as an unticked installer task and a Start Menu
entry. The user never opens a terminal. Failure is non-fatal by construction: the installer
invokes it with a trailing `exit 0` so a provisioning problem cannot make a successful FinSight
installation report as failed.

## 5. Verification performed

**On this host (macOS):**

| Check | Result |
|---|---|
| Full test suite | **1322 passed**, 1 skipped |
| Windows-path tests (injection) | 12 passed — ACL selection, DPAPI scope, store location, lock byte, startup chain |
| Architecture contracts | import-linter 3/3 kept |
| Lint | ruff clean on every changed and new file |
| Windows wheel availability | `sqlcipher3`, `cryptography`, `openpyxl`, `PySide6`, `QtAwesome` all resolve for `win_amd64`/cp312 |
| `sqlcipher3` native shape | single self-contained `.pyd`; no external DLL to collect |
| PyInstaller spec | builds end to end; bundle complete; only benign optional-import warnings |
| Icon | valid multi-resolution `.ico` (16–256 px), generated from the theme tokens |
| Workflow YAML | all three workflows parse; every step has `uses` or `run` |

**Delegated to CI on `windows-latest`** (cannot execute on macOS — PyInstaller freezes the host
interpreter and bootloader, proved here by the Windows spec producing an `arm64` Darwin binary):

runtime imports · full suite · architecture contracts · icon generation · PyInstaller freeze ·
bundle completeness · packaged launch smoke · **encrypted-store assertion** (fails if the store is
plaintext SQLite) · installer build · SHA-256 + size + commit evidence · **silent install → launch
→ uninstall → review-data-retained** lifecycle · artifact upload · Release publication.

## 6. Deliverables

| Deliverable | Location |
|---|---|
| Windows release pipeline | `.github/workflows/release-windows.yml` |
| macOS pipeline (secondary) | `.github/workflows/release-macos.yml` |
| PyInstaller specification | `build/windows/finsight.spec` |
| Frozen entry point | `build/windows/finsight_win_entry.py` |
| Windows version resource | `build/windows/version_info.txt` |
| Installer | `build/windows/finsight.iss` |
| Icon + generator | `build/windows/finsight.ico`, `make_icon.py` |
| Runtime provisioning | `build/windows/provision_ask_fin.ps1` |
| Local Windows build | `build/windows/build_windows.ps1` |
| Release documentation | `docs/RELEASE-WINDOWS.md` |
| Packaging decision | `specs/09-decision-log.md` — DEC-037 |
| Delivered rule scope | `specs/09-decision-log.md` — DEC-036 |

## 7. Open items — not blockers for producing the installer

1. **Code signing (PKG-06).** The installer is unsigned, so Windows SmartScreen warns on first
   run. This needs the organization's Authenticode certificate and is the most visible rough edge
   for a non-technical recipient. Add the certificate as a repository secret and a signing step to
   the workflow.
2. **SBOM and third-party notices (PKG-05).**
3. **Two departures from ADR-V2-004** (Status: *Proposed*) recorded in DEC-037: per-user Inno
   Setup executable rather than a WiX per-machine MSI, and an explicit user-initiated download in
   the provisioning helper. Both need ratification or reversal.
4. **Enterprise machine-scoped deployment** and the protected-activation Task Scheduler helper
   described in ADR-V2-004 are unaddressed; they are a separate package.
5. **macOS second-launch keychain defect** — documented at the top of the macOS workflow, deferred
   to the macOS milestone.
6. **Detection scope** — five protected baseline rules; the gap against the Rules Catalog is
   recorded in DEC-036. No month-over-month comparison in this release.
