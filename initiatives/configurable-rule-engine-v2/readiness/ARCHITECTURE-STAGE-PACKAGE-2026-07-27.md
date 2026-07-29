# Architecture Stage Package — 2026-07-27

- **Initiative:** FinSight Configurable Rule Engine V2
- **Stage:** Architecture
- **Package state:** Approved by Project Owner
- **Implementation authorization:** Workflow 1 — Review Management only
- **Requirements gate:** PASS
- **Requirements hashes:** Functional `0fe666b42290d6c12ac679a787f347155f8d2eb2fd6b03ab0957164984eb3297`; Non-functional `a49212a6c2bd9bd185831d4422d99018e99629afc4dd2c51ab622d8c52ce9a8b`
- **Independent Architecture review:** [PASS](../reviews/REVIEW-2026-07-27-architecture-stage.md)
- **Project Owner Architecture approval:** [Approved 2026-07-27](ARCHITECTURE-APPROVAL-2026-07-27.md)

## 1. Required Architecture artifacts

| Artifact | SHA-256 |
|---|---|
| [Application Architecture](../docs/APPLICATION-ARCHITECTURE.md) | `996a05a014514e08260c3511513f72446f7800a66b806d7f201cbab2afd17b7e` |
| [Configurable Rule Engine Design](../docs/RULE-ENGINE-DESIGN.md) | `0aa9faf5a5485e6ca38a8002d74053688dc75ef8ba2da930bccb619b7ccb604d` |
| [Persistence Model](../docs/PERSISTENCE-MODEL.md) | `6ce833bc8c21dd42ba6a86099bd6a7bf1153cd3a2a0fd942f72291cdb394c14a` |
| [UX/UI Design](../docs/UX-UI-DESIGN.md) | `e5805a8ec48f3dc16ac4d493b327ce86b34c5881490e48f285a6ecf8d2dc9264` |
| [Technical Implementation Plan](../plans/TECHNICAL-IMPLEMENTATION-PLAN.md) | `93bca498e0e2a4605a1a778548640debccea1485a68e5bc3e4401a074cb68845` |

## 2. Proposed Architecture Decision Records

| ADR | SHA-256 |
|---|---|
| [ADR-V2-001 — Configurable Deterministic Rule Engine](../adr/ADR-V2-001-configurable-deterministic-rule-engine.md) | `f1d548ad2886122f7ee62c7c5bd913b5814702f31e3d3825b5a07ba323a433e6` |
| [ADR-V2-002 — Sequential Multi-Actor Local Governance](../adr/ADR-V2-002-sequential-multi-actor-local-governance.md) | `f2648307d6394e01813cf5bbe55cb7caff7a70c33077130b4187b916a09f7bcb` |
| [ADR-V2-003 — Encrypted Authoritative Persistence and Recovery](../adr/ADR-V2-003-encrypted-authoritative-persistence-and-recovery.md) | `5ca87f8e5f5a0dd975117c9ec2acc952317e57473ad1843b8fb7110a5f7c2020` |
| [ADR-V2-004 — Windows Packaging and Support](../adr/ADR-V2-004-windows-packaging-and-support.md) | `01620967465b211623f806a7aa894ead702b6af954d729705ae89601489a0812` |
| [ADR-V2-005 — Private Engine-Bound Ask Fin](../adr/ADR-V2-005-private-engine-bound-ai.md) | `2c1fa98e3548e9d8643b283e14b60d16fd954ea27a12c816e05b39625ab46736` |
| [ADR-V2-006 — `SLV-001` and `WRL-001`](../adr/ADR-V2-006-slv001-workbook-safety-profile.md) | `0e8388db98260b450836a9de8049396b53b7289ddd52c5fd8c48cb2fcc22fde4` |
| [ADR-V2-007 — Ledger Consumers and Derived Records](../adr/ADR-V2-007-ledger-consumers-and-derived-records.md) | `f9b7cc45cb2d0d54f26c05e9d79dab68c4224020ad1f66aae53c483010acf5f8` |

## 3. Package coverage

The package jointly defines:

- the existing-codebase modular-monolith architecture and dependency rules;
- configurable deterministic rules, closed evaluator language, versioning, lifecycle, storage, protected governance, and the five baseline controls;
- exact Budget/GED intake, `SLV-001` extraction, `WRL-001` safety limits, metadata reconciliation, reviewed-copy reconstruction, and source immutability;
- stable one-run identity, append-only attempts, atomic complete ledger, Findings, status, publication, analytics, reports, and Derived Records;
- encrypted authoritative-only persistence, migrations, HMAC-chained audit, backup/restore, temporary-data handling, and governed disposal;
- three extensible roles, replaceable identity, Windows SID default, signed role assignments, and two-person protected change;
- future-dated protected activation with durable scheduling and fail-closed overdue reconciliation;
- summary-first UX, seven-state review lifecycle, Original/User-Reviewed/Current values, accessibility, and exact run identity;
- approved-private/on-device Ask Fin, explicit consent before external transmission, masking, minimal grounding, verified claims, and no write authority;
- Windows executable/MSI, signing, support matrix, upgrade/uninstall, scheduled helper, and release evidence; and
- the five approved SDD stage gates plus the seven strict end-to-end implementation workflows.

## 4. Internal consistency checks completed

- Requirements files still match the independently reviewed hashes.
- All relative Markdown links in the package resolve.
- `R-VAL-01` through `R-VAL-05`, CORE-01 through CORE-05, source layouts, severities, result statuses, and synthetic-oracle effects are consistent.
- The engine has exactly two explicit inputs: `VerifiedDataset` and `RuleSetVersion`.
- Validation Run identity is created at start; attempts reuse that Run ID; only the completion-sealed ledger is financial truth.
- Native and migrated analytical-state history, exact export transitions, authorized first historical export after supersession, request-label/promotion and concurrent-export behavior, and seal ordering are explicit and consistent.
- Candidate/Review Version boundaries and all seven Review Status values are consistent.
- Role/permission, distinct-person approval, signed manifest, scheduled activation, and workspace-baseline behavior are consistent.
- SQLCipher/DPAPI/Keychain, passphrase-default/optional-certificate backup, managed-copy disposal, and no-plaintext fallback are consistent.
- The external recovery-control registry owns managed-backup lifecycle and disposal revocation; its journal/head protocol, signed-capsule checkpoint adoption, restore precedence, migration, rollback, uninstall, and currentness boundary are explicit.
- Ask Fin provider approval and external-transmission consent are independent, mandatory gates.
- `SLV-001`, `WRL-001`, NFR-081, error taxonomy, Windows matrix, signing, upgrade, and uninstall contracts are consistent.
- The implementation plan uses only the five approved stage gates and the seven workflows in the required order.
- No application source, test, migration, dependency, package, installer, or synthetic fixture was changed during Architecture.

## 5. Independent review cycle

The independent reviewer `/root/architecture_stage_review`, who did not author the package, verified the initial frozen snapshot byte-for-byte and reviewed it across software, data, integration, security/privacy, finance-control, UX/accessibility, QA, Windows/release, and documentation/traceability lenses.

The initial disposition was FAIL with no Blocker or Critical finding and two Major findings:

1. the retained `VERIFIED` → `ANALYZED` → `SUMMARIZED` → `EXPORTED` lifecycle lacked an authoritative event model and exact transition/race contract; and
2. the asserted disposal registry lacked an implementation-ready authoritative persistence, crash recovery, restore-precedence, migration/uninstall, and replacement-machine contract.

Those related material defects and the one editorial counting observation were repaired as one batch across the Architecture, Persistence, UX/UI, Technical Plan, and relevant ADRs. The repaired snapshot above adds the append-only analytical event contract and the non-restorable recovery-control authority, including signed-capsule checkpoint adoption on an empty replacement machine.

The first same-reviewer recheck closed both original Major findings and the editorial observation but identified one new Major repair regression: the supersession-freeze wording incorrectly blocked the first authorized historical report/export for a Closed superseded `SUMMARIZED` generation, contrary to FR-171/FR-172.

The second repair narrows ADR-011 §7 explicitly through ADR-V2-007: supersession keeps all financial, verification, run/result, publication/supersession, and prior lifecycle/artifact facts immutable, while an authorized historical first PDF/XLSX may append the sole `SUMMARIZED` → `EXPORTED` event. Request creation serializes with promotion for an exact creation-time label; promotion first yields `Historical — Superseded` rather than a block. A dedicated Closed/superseded/no-prior-artifact case is required in persistence, UX, ADR, and workflow verification.

The second same-reviewer recheck returned **PASS**. It verified all 12 frozen Architecture/ADR hashes and both unchanged Requirements hashes, confirmed every finding closed, checked all 74 relative links across 38 initiative Markdown files, and found no new Blocker, Critical, or Major regression. The complete evidence trail is recorded in the [Independent Architecture Stage Review](../reviews/REVIEW-2026-07-27-architecture-stage.md).

The Project Owner approved this exact independently reviewed Architecture package on 2026-07-27 and
authorized Workflow 1 — Review Management only. Later workflows and Windows packaging remain blocked.
