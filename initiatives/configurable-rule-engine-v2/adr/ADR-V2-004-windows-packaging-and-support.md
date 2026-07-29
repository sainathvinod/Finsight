# ADR-V2-004 — Windows Packaging, Signing, and Support Matrix

- **Status:** Proposed
- **Date:** 2026-07-27
- **Deciders:** Project Owner; Desktop Engineer; Security Architect; Release Engineer
- **Preserves:** Root ADR-008 PySide6 desktop stack
- **Related contracts:** AC-02 and AC-07

## Context

V2 requires a distributable Windows executable and installer that work on restricted 8–16 GB corporate laptops, retain data during upgrade/uninstall, operate offline, and carry verifiable release provenance.

## Decision

The first supported Windows release will use:

- one Python/PySide6 codebase and headless deterministic core;
- a PyInstaller **one-directory** application bundle;
- a WiX Toolset v4 per-machine MSI;
- x86-64 Windows 11 Enterprise 24H2 and 25H2 as the initial qualification matrix;
- clean 8 GB and 16 GB virtual-machine test images;
- standard-user runtime after enterprise/admin installation;
- no installer-time downloads, self-updater, telemetry, or implicit network dependency; and
- deterministic build inputs pinned by lockfiles and a generated software bill of materials.

The MSI installs application binaries under Program Files and creates the machine-scoped protected data/key directories with the ACL required by ADR-V2-002/003, including the recovery-control registry directory outside replaceable store directories. The installer does not provision FinSight roles through the application.

The MSI also registers the signed least-privilege protected-activation helper with Windows Task Scheduler. The helper has no UI, network listener, approval capability, or independent policy logic; it can only reconcile due jobs through the normal store lock and activation service. Repair and upgrade preserve or replace task registration without losing durable due jobs. Default uninstall removes the helper/task with the binaries but retains encrypted due jobs; reinstall must reconcile every overdue job before baseline-dependent work. The macOS equivalent uses the approved signed `launchd` profile.

All shipped executable content and the MSI are Authenticode signed with the organization-approved code-signing certificate, SHA-256 digest, and RFC 3161 timestamp. Release evidence records:

- source commit;
- dependency lock and SBOM fingerprints;
- build environment/image;
- artifact hashes;
- signing certificate identity and timestamp evidence;
- malware scan result;
- clean-machine qualification result; and
- upgrade/uninstall test result.

Minor/patch upgrades are in-place and retain the encrypted store, key material, authorization source, preferences, recovery metadata, external registry/head, registry secret envelope, and current managed-recovery capsules. Schema migration is forward-only, transactional, and preceded by a verified consistent recovery point. Registry-format migration is separately append-only; rollback never lowers its accepted head, and an older incompatible binary enters recovery-only mode.

Uninstall removes application binaries but retains all user data by default. An interactive removal may offer a separate `Remove all FinSight data` action only by launching the same signed, identity-resolved, Reviewer-authorized whole-scope disposal component before binaries are removed. That action displays the exact active/managed-backup scope and discloses that the minimal content-free registry, registry-key envelope, and current continuity capsule remain to prevent old managed recovery from returning. Cancellation, authorization failure, or disposal failure retains the data. Silent enterprise uninstall always retains data unless accompanied by a separately created, verifiable disposal authorization artifact. A bare MSI property or checkbox may never bypass the governed disposal service. Only a separately documented administrator device-decommission procedure may remove the final registry authority.

Windows 10 Enterprise LTSC 2021 is not an initial supported target because its remaining lifecycle is too short for the proposed release baseline. Windows versions outside the published matrix are unsupported until separately qualified.

The inherited macOS parity requirement remains: the same headless core, rule definitions, fixtures, and business-result projection must behave equivalently. This ADR chooses the required Windows packaging path and does not remove macOS.

## Consequences

### Positive

- One predictable offline enterprise deployment artifact.
- Standard users can run the application after controlled installation.
- Signed/timestamped artifacts and build evidence support provenance.
- Upgrade and uninstall cannot silently erase review evidence.

### Costs and limitations

- One-directory packaging creates more installed files than a single executable but is more diagnosable and reliable for Qt/native dependencies.
- Supporting additional Windows releases, architectures, or installer contexts requires a qualification change.
- Code-signing certificate custody and build isolation become operational prerequisites.

## Rejected alternatives

- **Unsigned zip or wheel:** not a governed Windows deliverable.
- **Single-file self-extracting executable:** adds startup extraction and temporary-file complexity for Qt/SQLCipher.
- **MSIX as the only package:** enterprise deployment and machine-scoped shared-data constraints are less direct for the current environment.
- **Online bootstrapper/self-updater:** violates offline and controlled-change expectations.

## Verification

- Fresh install, first launch, standard-user operation, repair, upgrade, rollback-on-failed-migration, and uninstall tests.
- Scheduled-activation helper registration, signature, least privilege, due execution, missed-wake recovery, repair/upgrade, and uninstall behavior.
- Default-retain and separately confirmed/authorized interactive-removal uninstall tests, including retained registry/capsule continuity, reinstall, and separate device decommission.
- Signature and timestamp validation on every artifact.
- Offline runtime test with all network interfaces disabled.
- 8 GB/16 GB resource and NFR-081 performance tests.
- ACL and second-instance tests under distinct authorized Windows accounts.
- Reproducible manifest/SBOM/hash verification from a clean build environment.

## Approval effect

If accepted, this ADR fixes the Windows packaging/support baseline. It does not authorize a release or implementation before the full Architecture package is approved.
