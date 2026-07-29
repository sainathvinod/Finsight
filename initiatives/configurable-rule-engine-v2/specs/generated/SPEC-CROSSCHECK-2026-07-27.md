# FinSight V2 Post-PASS Independent Requirements Cross-Check — 2026-07-27

- **Verdict on the previously audited snapshot:** FAIL
- **Review type:** Independent inherited-contract cross-check after the first full PASS
- **Gate effect:** The earlier Architecture authorization was reopened; this record supersedes it until a fresh independent full review returns PASS
- **Implementation authorization:** None

## Snapshot cross-checked

| Register | SHA-256 |
|---|---|
| Functional Requirements | `17b34229bacc6fff698f3c096942f453b1d0422c894657efe7f3d29e0efdbcb0` |
| Non-functional Requirements | `eba5158c152972f25b3dc06d01ea1aa7beb1db28b54224e5bda32f713e2ebe18` |

## Material blockers found

1. V2 persisted-data and Review Version language conflicted with inherited ADR-011/ADR-012 reconstruction, ReviewGeneration, working/published, promotion, and supersession contracts.
2. Global protected-catalog activation and workspace/run selection both used `Rule Set Version`, creating incompatible scopes.
3. successor Review Version initialization contradicted the stated lifecycle transition contract.
4. unresolved identity permitted unattributed access to protected data, conflicting with root FR-084.
5. the complete-backup requirement omitted exports and Derived Record Generation Events.

## Repair disposition

The Draft Requirements package now:

- maps Review ID to ReviewCycle and Review Version to ReviewGeneration;
- keeps Draft/Data Uploaded work in a Working Candidate;
- preserves ADR-012 source binding and fingerprint-verified reconstruction without persisted full row stores;
- restores working/published generation selection and atomic promotion;
- uses reason-specific reverification, reanalysis, and exact replay;
- separates global Protected Baseline Version from workspace Rule Set Version;
- denies protected data access until a stable attributable Actor resolves;
- backs up every retained Derived Record and Generation Event; and
- adds atomic and verification coverage for these contracts.

These repairs are not self-approved. A new independent full Requirements review must evaluate the changed snapshots and return PASS before Architecture begins.

## Follow-up closure

The fresh [independent full Requirements recheck](SPEC-AUDIT-2026-07-27-RECHECK.md) returned PASS on FR-123–FR-203 and NFR-081–NFR-110. This FAIL remains historical evidence of why the gate was reopened; the recheck is the current gate evidence.
