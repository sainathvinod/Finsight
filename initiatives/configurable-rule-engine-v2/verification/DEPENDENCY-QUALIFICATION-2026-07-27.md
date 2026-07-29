# Workflow 1 Dependency and Security-Profile Qualification — 2026-07-27

- **Initiative:** FinSight Configurable Rule Engine V2
- **Workflow:** 1 — Review Management
- **Host used:** macOS, Python 3.11.15
- **Result:** **PASS for Workflow 1 implementation and local verification**
- **Windows release qualification:** Not performed; reserved for the approved Windows Packaging and
  Release gate

## Qualified implementation profile

| Component | Qualified value | Enforced behavior |
|---|---|---|
| SQLCipher binding | `sqlcipher3==0.6.2` | No `sqlite3` production fallback |
| SQLCipher runtime | `4.12.0 community` | Exact runtime match required |
| Store profile | `SQLCIPHER-4.12.0-COMMUNITY-001` | Persisted and checked on every open |
| Cipher page size | `4096` | Applied before schema access |
| KDF | `PBKDF2_HMAC_SHA512`, 256,000 iterations | Applied before schema access |
| HMAC | `HMAC_SHA512` | Applied before schema access |
| Database runtime | WAL, `synchronous=FULL`, foreign keys on, secure delete on | Verified after open |
| Manifest cryptography | `cryptography==49.0.0`, Ed25519 | Detached signature, time window, key ID, and rollback checks |
| Production runtime location | Machine-scoped (`ProgramData`, `/Library/Application Support`, or `/var/lib`) | No per-user or FinSight-specific environment path override |
| Windows key/ACL profile | DPAPI Local Machine; `FinSight Users`, SYSTEM, Administrators | Sequential authorized accounts share one protected machine store |
| macOS key/permission profile | System Keychain; deployment-provisioned `finsight` group | Sequential authorized accounts share one protected machine store |
| Desktop runtime | `PySide6==6.11.1` | Offscreen launch and UI/accessibility tests passed |

## Evidence

- A seeded confidential sentinel is absent from the database, WAL, SHM, journal, and temporary files.
- A valid key reopens persisted records; an incorrect key fails without modifying ciphertext.
- A legacy plaintext SQLite database is migrated through an atomic SQLCipher export and verified before
  replacement.
- A mismatched runtime or persisted security profile fails closed.
- The SQLCipher profile is applied before any schema read.
- The signed authorization manifest rejects altered content, unknown keys, invalid time windows,
  rollback, same-version equivocation, protected-role redefinition, and protected-role self-assignment.
- A valid signed manifest is authenticated before the protected store is opened or mutated; every
  operation reloads authorization and rechecks identity and permission immediately before commit.
- Accepted manifest, role, assignment, import, and authorization-decision history is immutable and
  versioned. A durable external HMAC anchor detects database-side manifest rollback.
- Audit HMAC chains are anchored in the external content-free registry. Deleted suffixes, database-head
  rewind, and post-commit anchor publication failures fail closed.
- Production startup refuses to open protected storage when identity or the signed role-manifest
  configuration is absent.
- Production key-provider selection depends only on the operating system. Environment variables cannot
  switch the release composition to the test key provider or local bootstrap roles.
- Tests and the developer screenshot/launch utilities inject the test provider and bounded local
  Reviewer policy explicitly. Test stores use owner-only permissions and synthetic data only.
- The two-actor security test proves two distinct sequential identities can create and reopen reviews
  in one machine-scoped store.
- Authorization revocation and actor changes at the commit boundary roll back the business action and
  preserve the exact denial evidence. If mandatory denial evidence cannot be retained, protected writes
  lock with cataloged error `FS-AUD-001`.

The complete regression result is recorded in
[Workflow 1 Verification](WORKFLOW-01-VERIFICATION-2026-07-27.md).

## Platform qualification boundary

The Windows SID, DPAPI machine-scope, and restrictive ACL adapters are implemented behind replaceable
ports. Their pure adapter behavior is covered where it can be simulated on macOS. Actual Windows token,
DPAPI, ACL, native-wheel, signed-executable, installer, clean-machine, upgrade, and uninstall execution
was deliberately not claimed in Workflow 1 because the Project Owner explicitly excluded Windows
packaging. Those checks remain mandatory release-gate work; a Windows package must fail release if any
one of them fails.

Likewise, the local macOS developer profile does not qualify an administrator-provisioned production
System Keychain and multi-user POSIX-group deployment. Production launch requires the machine location,
System Keychain item, access group, signed role assignments, and external registry to be provisioned.
The documented developer profile must never be used with real financial data.
