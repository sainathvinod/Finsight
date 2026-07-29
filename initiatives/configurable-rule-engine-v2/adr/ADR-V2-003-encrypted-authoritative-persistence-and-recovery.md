# ADR-V2-003 — Encrypted Authoritative-Only Persistence, Atomic Runs, and Recovery

- **Status:** Proposed
- **Date:** 2026-07-27
- **Deciders:** Project Owner; Data Architect; Security Architect; Software Architect
- **Refines:** Root ADR-004, ADR-005, ADR-006, ADR-009, ADR-011, ADR-012, ADR-014, and ADR-015
- **Related contracts:** AC-01, AC-04, AC-05, AC-06, and AC-07

## Context

FinSight must preserve immutable, reproducible financial-review evidence without storing source workbook bytes or complete normalized, Working Dataset, or `VerifiedDataset` row stores. V2 also requires at-rest protection, shared sequential local actors, atomic result ledgers, complete backup/restore, append-only derived artifacts, and governed whole-scope disposal.

Root ADR-004’s earlier list of persisted extracted/verified rows is superseded by the later reconstruction model in ADR-011/012 and the V2 authoritative-only requirement.

## Decision

### Embedded encrypted store

SQLite remains the authoritative embedded persistence engine behind repository ports. Production stores use SQLCipher-compatible encrypted SQLite with:

- AES-256 database encryption as provided by the approved SQLCipher build;
- page authentication/integrity enabled;
- secure-delete and journal/WAL handling configured so plaintext financial content is not retained;
- exact decimal text or integer minor units, never `REAL`, for money; and
- schema migrations executed transactionally and recorded immutably.

The exact supported Python SQLCipher distribution is selected by an early dependency/build qualification, but plaintext SQLite is not a production fallback.

A random database key is generated at installation. On Windows it is wrapped using DPAPI machine protection and stored in a key file whose ACL permits only SYSTEM, administrators, and the deployment-approved FinSight user group. On the inherited macOS target, the equivalent key is held in System Keychain. Secrets are never stored in the database, logs, exports, or authorization manifest.

Audit events use an HMAC-SHA-256 chain over canonical event bytes, the preceding event MAC, and stream identity. A separate random audit key is wrapped through the platform key-protection port and is included only inside an encrypted portable backup. Chain verification runs at startup, before backup, and after restore. Within the stated local-administrator threat boundary, this detects event alteration, deletion, insertion, and reordering.

### Authoritative-only record model

The store retains:

- ReviewCycle, Working Candidate, Review Version/Generation, seven-state Review Status, append-only `VERIFIED`/`ANALYZED`/`SUMMARIZED`/`EXPORTED` analytical-state events, and publication metadata;
- generation-specific source bindings, filenames/path hints, fingerprints, and provenance, but not workbook bytes;
- extractor, schema/layout, correction, reversion, confirmation, verification-basis, and verified-fingerprint records;
- immutable rule/configuration versions, bindings, Protected Baseline Versions, and workspace Rule Set Versions;
- identity, role-assignment evidence, protected requests/decisions/activations, and append-only audit events;
- Validation Runs, Rule Executions, Rule Results, Findings, and deterministic comparison projections;
- working/published pointers, promotions, supersession, and replay metadata;
- Derived Record Generation Events and retained report/export/allowed Ask Fin content; and
- retention, backup, restore, temporary-disposal, and whole-scope-disposal evidence.

It does **not** retain:

- source workbook bytes;
- a complete normalized row store;
- a complete Working Dataset;
- a complete `VerifiedDataset`; or
- hidden AI reasoning.

Datasets are reconstructed from fingerprint-matching sources, the exact extractor/layout version, and correction/confirmation basis. A mismatched recomputed verified fingerprint blocks release to the engine and evidence consumers.

### Stable run identity and atomic authoritative ledger

A Review Version/Generation has zero authoritative Validation Runs before validation starts and exactly one thereafter. The validation-start transaction creates one immutable run envelope, pins the Review Version, Rule Set Version, verified fingerprint, initiating Actor ID, and start timestamp, and appends the first attempt record/audit event. A uniqueness constraint on Generation ID prohibits any second Run ID. Retry after a canceled, failed, or interrupted attempt appends another attempt under that same Run ID.

The run envelope is authoritative identity but is not a completed financial result. Execution builds the complete ledger in memory or protected operation-scoped temporary storage. One final database transaction persists:

- the run completion event and terminal timestamp/status;
- all Rule Executions;
- all Rule Results;
- all Findings;
- deterministic summary/status projections;
- audit events;
- `Validation Complete` plus ordered `ANALYZED` and `SUMMARIZED` analytical-state events; and
- first-generation auto-publication when applicable.

If execution, cancellation, serialization, or persistence fails before commit, the run envelope and append-only attempt/audit outcome remain, but the transaction leaves zero authoritative Rule Execution, Rule Result, Finding, completion-seal, or `Validation Complete` records. The same generation can retry only under its existing Run ID. `INSERT OR REPLACE` is prohibited for immutable evidence.

The completion seal is inserted last under deferred transaction assertions; all dependent ledger, analytical, Review Status, and first-publication facts are invisible until the same transaction commits and roll back if seal/count validation fails.

### Append-only consumers

Reports, exports, and permitted Ask Fin interactions are separate Derived Records. Each generation attempt has an append-only Generation Event with terminal `Completed`, `Failed`, or `Blocked` outcome.

Native analytical events begin with `VERIFIED`: trigger `HUMAN_CONFIRMATION` for fresh verification or `INHERITED_VERIFICATION_BASIS` for reanalysis, which references the basis and preserves the original verifier/time. Validation completion appends `ANALYZED`, then `SUMMARIZED`. The first successfully completed PDF report or XLSX export appends `EXPORTED` whether the generation is working, published, historical, or superseded. This narrowly refines ADR-011 §7 for FR-171/FR-172: supersession leaves financial, verification, run/result, publication/supersession, and all prior lifecycle/artifact facts immutable, but does not prohibit this one additive historical artifact-state event or otherwise legal later lifecycle events.

Derived Record request creation serializes with promotion and pins the exact creation-time publication/supersession label. Promotion first therefore yields a permitted `Historical — Superseded` artifact rather than a block; request creation first preserves its earlier label even when promotion follows. Concurrent first exports may both produce immutable artifacts but exactly one appends `EXPORTED`.

Failed/blocked generation, Ask Fin output, screen viewing, and external delivery do not advance analytical state. Regeneration creates a new ID and content fingerprint, leaves an already exported generation at `EXPORTED`, and never overwrites a prior artifact or Validation Run. A migrated `LEGACY_SNAPSHOT` event records only the old row's explicit state with null prior/unknown transition actor-time; it does not fabricate native transitions.

### Backup and restore

FinSight creates a transactionally consistent portable encrypted backup with a fresh random content key. The required MVP profile asks the user for an explicit recovery passphrase that is never stored; an approved memory-hard KDF derives a key-encryption key that wraps the random content key. Exact algorithms and parameters are fixed by the pre-implementation security qualification and recorded in the package. An approved deployment may substitute an organization recovery-certificate profile through the same `BackupKeyProviderPort`. The package contains:

- the encrypted authoritative database;
- an encrypted inner manifest containing counts, relationships, fingerprints, and authoritative schema/application evidence;
- a minimal non-sensitive outer envelope containing Backup ID, store/registry lineage and required sequence, immutable scope-token epoch, capsule-signing public-key fingerprint, mandatory `STORE_LINEAGE` plus review/period membership-token digest, format version, selected key-provider/KDF parameters, salt/envelope identity, wrapped content/registry-secret keys, ciphertext hash, and package-integrity metadata; and
- no source workbooks or complete reconstructed row stores.

The external recovery-control journal—not the database catalog—is authoritative for managed backup `PREPARED`/`ACTIVE`/`RETIRED`/`REVOKED` lifecycle. Each custody-controlled FinSight-managed recovery root holds one separately signed current continuity capsule. It is updated after later backup/disposal actions and is never overwritten by an older database snapshot.

The registry secret bundle is platform protected on the source machine and recovery-wrapped in each admitted encrypted package. The source can sign later content-free capsule updates without retaining/re-entering the backup passphrase. An admitted replacement-machine restore unwraps and reseals the same lineage/token epoch under its local platform protection.

Restore occurs into a quarantined new store, verifies package integrity and the full manifest, runs compatible migrations, checks referential/audit/analytical-state invariants, and atomically swaps the store only on complete success. Before and immediately before any store activation, the external registry must admit the Backup ID and every registry-qualified membership token. Restored catalog/tombstone rows remain projections and cannot reactivate an externally retired/revoked package. Restore never merges into a live store and never lowers an accepted registry head.

FinSight records each backup it creates as a managed recovery copy while its path remains under FinSight control. Governed disposal removes or rewrites every registered managed copy before reporting completion. Copies made outside FinSight are identified as outside its control and are governed by organizational policy.

### Temporary artifacts and disposal

All financial temporary files live in a dedicated ACL-restricted operation directory, use opaque names, and are removed before success/cancel/failure reports completion. Startup crash recovery disposes orphaned operation directories before review data becomes available and appends content-free disposal evidence.

Whole-scope disposal is a separate resumable job for one complete review, one complete period, or all local data. `DisposalRegistryPort` owns the content-free external recovery-control authority: a canonical append-only HMAC-chained journal plus a platform-protected head outside every replaceable SQLCipher store and ordinary database backup.

Journal events cover genesis/cutover/format migration, authoritative managed-backup lifecycle, and disposal `PREPARED`/`COMMITTED`/`ABORTED`. Each carries registry/store lineage, sequence/prior hash, operation ID, token epoch, opaque scope tokens, affected Backup IDs/hashes, prior/resulting store heads, Actor/time/bounded reason/outcome, and record MAC. Every package includes `STORE_LINEAGE`; all-data disposal revokes that token. The scope-token epoch is immutable within one registry lineage for the MVP.

The protected head contains committed and optional pending sequence/tail/operation tuples. Under the exclusive recovery lock, an append is: append/fsync journal entry; atomically publish pending; reread/verify; atomically promote pending. Startup adopts a valid authenticated suffix or pending entry and fails closed on missing/truncated pending data, invalid HMAC, conflicting operation, or lineage/sequence ambiguity.

The disposal job:

1. freezes, inventories, and separately confirms the selected scope and external-copy limitation;
2. acquires exclusive store/recovery coordination;
3. durably appends `DISPOSAL_PREPARED` and publishes that head to each current managed-recovery continuity capsule before deleting or replacing anything;
4. rebuilds and validates the retained graph under a new store key with a tombstone referencing the prepared registry operation;
5. appends authoritative `BACKUP_REVOKED`, removes affected managed packages, and revokes provider envelopes when supported;
6. atomically activates the rebuilt store and destroys the prior store key;
7. durably appends `DISPOSAL_COMMITTED` referencing the resulting store/tombstone hash, advances the protected head/capsules, and verifies zero residual managed records.

The rebuilt-store tombstone references operation ID plus the `DISPOSAL_PREPARED` entry; the later committed entry references the tombstone/resulting-store hash. An unresolved prepare blocks every affected restore. Startup reconciles operation ID, prior/resulting store heads, keys, packages, and capsules: it commits when activation occurred, or may append `DISPOSAL_ABORTED` only when the original store is proven intact and no destructive activation occurred. Ambiguity fails closed.

Fresh install creates registry genesis and `STORE_LINEAGE` before its store. Legacy cutover inventories trustworthy evidence and attests it; pre-registry packages are `Legacy — unmanaged`, migration-quarantine-only, and must be re-backed-up under V2 before production activation. Registry format migration is append-only; binary/schema rollback never lowers its head.

The registry survives store replacement, all-data reset, upgrade, default/all-data uninstall, and reinstall. Only administrator device decommission may remove the final authority. An ordinary backup or restored database cannot replace or lower it. On a replacement machine, managed restore requires the current signed continuity capsule from the same custody-controlled recovery root and preserves its lineage under new local protection; absent/stale continuity fails closed.

The replacement machine treats that capsule as a signed checkpoint, not as reconstructed journal history. After package admission and secret-bundle unwrap, it creates a protected local segment anchored to the capsule hash/sequence/tail and appends an idempotent `RECOVERY_ADOPTION` successor before database activation. The checkpoint plus authenticated suffix remain authoritative; lineage, token epoch, and sequence never reset to genesis.

Without an independent online/organization currentness witness, an empty offline replacement machine cannot cryptographically distinguish an out-of-band stale clone of a once-valid package/capsule pair. Such clones are outside FinSight management under the explicit external-copy boundary and cannot be presented as a current managed recovery set.

Ordinary object deletion or selective rewriting of Closed/Archived evidence is prohibited.

## Consequences

### Positive

- Financial data is protected at rest.
- Historical truth is immutable and independently reproducible when matching sources remain available.
- A crash cannot create a partial authoritative ledger or silently replace published results, while the stable Run ID and attempt history remain attributable.
- Replacement-machine recovery includes governance, results, artifacts, and audit—not only transactions.

### Costs and limitations

- Historical row-level reconstruction depends on the user retaining matching source bytes.
- SQLCipher packaging and cross-platform qualification are release gates.
- The required MVP backup profile cannot recover if its passphrase is lost; an approved organization-certificate profile transfers that custody risk to the organization.
- Disposal can be slower because all registered managed copies must be reconciled.
- A managed replacement-machine restore requires both the selected backup and the current continuity capsule from its recovery set; FinSight fails closed when revocation continuity cannot be proved.
- Offline latest-capsule assurance depends on FinSight custody of the managed recovery root; an independently cloned stale pair is explicitly outside the managed guarantee.

## Rejected alternatives

- **Plain SQLite for production:** fails at-rest protection.
- **Persist complete normalized/verified rows for convenience:** contradicts authoritative-only reconstruction.
- **Persist partial results while rules run:** enables false/incomplete history.
- **Overwrite runs or exports:** destroys audit and replay evidence.
- **Machine-bound backup key only:** cannot restore on a replacement machine.

## Verification

- Storage inventory proves required authoritative classes exist and prohibited byte/row stores do not.
- SQLCipher-at-rest scan finds no seeded plaintext values in database, WAL, journal, temp, or backup.
- Fault injection at run-start, attempt, atomic-ledger, and promotion boundaries proves stable one-run identity and all-or-nothing result behavior.
- Reconstruction and verified-fingerprint tests cover moved, missing, mismatched, and extractor-divergent sources.
- Full backup/restore manifest comparison on a replacement machine.
- Analytical-state tests prove fresh/inherited/legacy origins, exact validation/first-export transitions, seal ordering, a Closed superseded `SUMMARIZED` generation's first historical artifact, request-label/promotion and concurrent-export races, failure, and regeneration.
- Registry tests cover fresh genesis, legacy cutover/pre-registry quarantine, signed-checkpoint replacement adoption and interruption, format migration, rollback refusal, backup lifecycle precedence, token epoch/`STORE_LINEAGE`, journal/pending-head crash states, all-data-uninstall residue, and reinstall.
- Disposal tests inject failure at registry prepare, capsule publication, store switch, registry commit, and cleanup; active and registered managed copies cannot resurrect the selected scope.
- Replacement-machine restore rejects revoked membership, unresolved prepared entries, absent/stale capsules, and registry rollback.
- Database triggers/repositories reject update/delete of immutable records.

## Approval effect

This proposal resolves the architecture direction for encryption, persistence, recovery, and disposal. The exact SQLCipher distribution and KDF parameter set must pass the pre-implementation dependency/security qualification recorded in the technical plan. No implementation is authorized until the complete Architecture package is approved.
