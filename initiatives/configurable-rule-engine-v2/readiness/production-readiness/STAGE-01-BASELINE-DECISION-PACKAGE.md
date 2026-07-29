# Stage 1 Baseline Decision Package

**Stage:** Baseline Freeze and SDD Reconciliation
**Prepared:** 2026-07-29
**Package status:** Candidate; independent review and human decisions pending
**Progression decision:** **NO-GO to Stage 2 until this gate passes**

## 1. Purpose

This package preserves the implemented FinSight state, separates source from
generated and obsolete artifacts, records current defects, creates the
production-readiness source hierarchy, and presents every decision required
before financial-correctness implementation may begin.

It does not approve any decision and does not authorize production behavior
changes.

## 2. Package contents

| Artifact | Purpose | State |
|---|---|---|
| [Master Plan](PRODUCTION-READINESS-MASTER-PLAN.md) | Nine-stage governed delivery and release rules | Candidate |
| [Current Baseline](CURRENT-GOVERNED-BASELINE.md) | Exact source/snapshot/test/release state | Candidate |
| [Directive Record](STAGE-01-GOVERNING-DIRECTIVE-RECORD.md) | Source hashes, authority, and clause interpretation | Candidate |
| [Source Inventory](STAGE-01-SOURCE-AND-ARTIFACT-INVENTORY.md) | Dirty/generated/obsolete/accidental classification and disposition | Candidate |
| [Normative Hierarchy](STAGE-01-NORMATIVE-SOURCE-HIERARCHY.md) | Authority, frozen-snapshot, status, and supersession overlay | Candidate |
| [Requirements Delta](PRODUCTION-READINESS-REQUIREMENTS-DELTA.md) | Durable IDs for the new program and Section 15 | Pending approval |
| [Traceability](UPDATED-REQUIREMENTS-TRACEABILITY-MATRIX.md) | Source-to-stage-to-evidence mapping | Pending approval |
| [Decision Register](STAGE-01-PRODUCT-AND-FINANCIAL-CONTROL-DECISIONS.md) | Product/Financial Control selections and approvals | **Decisions open** |
| [Scope Freeze](STAGE-01-FIRST-RELEASE-SCOPE-FREEZE.md) | Candidate included/deferred release scope | Not effective |
| Starting worktree JSON/TSV | Exact generated path/hash/class inventory | Generated and hashed |
| Stage 1 independent review | Independent package verification | Pending |

The exact candidate decision artifacts to approve are:

| Artifact | SHA-256 |
|---|---|
| Normative Source Hierarchy | `cbee7bc85dd76ad90944324230f51870449445fd65fac2a0b2bef43fb571a08c` |
| Production-Readiness Requirements Delta | `de5323ee16ce5683622e6fb736dcce6a69dbef73a962f8acc095b5b805ecce85` |
| Updated Requirements Traceability Matrix | `4c5f5d678d915d7d41f8bfa8e7cf5a44a179f025aae3284b58d2431e742f184a` |
| Product and Financial Control Decisions | `1adaa804a2c4840d988c4375d69a6567c45c36174bcb120bae6d3ef6b7b57ca8` |
| Candidate First-Release Scope Freeze | `c322babbda195662370878e0b09a210bc3ade0dadfbc67dc7328429912643acf` |
| Source and Artifact Inventory | `a9850e466a6061eff041aef2ed1b800154c50e2e177ac944a2dd2ab01c07d762` |
| Production-Readiness Master Plan | `a94fb84d361b3feddd9685fe293e05bdc59c721490ef0efd77fa95a5b6743609` |

## 3. Preservation completed

- Dedicated branch:
  `codex/production-readiness-stage1-2026-07-29`.
- Starting commit:
  `a298040a8408c04342818a65a186a0d72c87956a`.
- Complete Git bundle:
  `172bcdf9e6338d1949835497b5047e867e4a8d676069e1765fb927c7ea0de2e2`.
- Working source/evidence archive:
  `b6d0effaf8afb9c168fcb678aba4ebdac55446f69920e49246177686d9d8e9b0`.
- Both governing source texts preserved with their original hashes.
- Exact 1,760-path manifest generated:
  - JSON:
    `296bed9328f818d23764f93cc127150fec9e8da3a407796696613d8ea327af21`;
  - TSV:
    `6be3645a3991c891e53ec523040b88936167216c5e388965eafede9f82ccdcb0`.
- Candidate source/config commit:
  `31f7f36e3f0be5c0fb301343512e8019d6bb2bcd`.
- Candidate test/tooling commit:
  `f3232afde5776a43211d62e894294775b3acf643`.
- Archive and bundle verification passed.
- No cleanup, reset, rebase, stash, or source deletion was used.

## 4. Baseline mechanics corrected

- the `spec-driven` gitlink now has a candidate `.gitmodules` mapping;
- approved V2 synthetic XLSX fixtures are no longer silently ignored; and
- local generated/runtime/screenshot/accidental paths are explicitly separated
  from release source while remaining preserved externally.

These changes affect source reconstruction only.

One governed-document divergence also requires acceptance as part of the
normative hierarchy: the Architecture-gate Technical Implementation Plan hash
was `93bca498...`, while the current workspace copy is `8df4ae8e...`. The
accepted historical hash remains authoritative. The current copy is preserved
as later delivery guidance and is not silently promoted to approved
Architecture.

## 5. Decisions requiring approval

The complete options, recommendations, consequences, authorities, and blank
approval records are in the decision register.

The nine decisions explicitly required by the production-readiness directive are:

1. permanent protected Rule IDs;
2. CORE-04 scope and disposition of Budget formula checks;
3. Advisory-rule release scope;
4. managed backup/restore release obligation;
5. mandatory PDF/XLSX export scope;
6. Ask Fin inclusion in release 1;
7. supported Budget/GED layout;
8. supported Windows hardware baseline; and
9. local-AI deployment topology.

The reconciliation also surfaces:

10. inherited macOS release-parity disposition;
11. enterprise audit/Ask Fin/backup retention policy;
12. report-size and default-detail policy; and
13. configurable enterprise confidentiality label.

Section 15 strongly directs complete PDF/XLSX and Ask Fin inclusion, but those
choices still require a durable Stage 1 approval record. None of the other open
choices may be inferred from the implementation.

## 6. Stage 1 exit checklist

- [x] Current repository and closeout evidence preserved externally.
- [x] Starting branch/commit and archive hashes recorded.
- [x] Controlled Stage 1 branch created.
- [x] Current full-regression result and release NO-GO preserved.
- [x] Fixture-ignore and submodule reconstruction defects identified.
- [x] Generated/runtime/obsolete/accidental areas classified.
- [x] Exact starting path/hash manifest generated and frozen.
- [ ] Source/test/migration/governed-document candidate committed
      (source and test commits complete; governed-document commit pending).
- [ ] Clean-checkout fixture and submodule reconstruction passed.
- [ ] Normative-source hierarchy independently reviewed.
- [ ] Historical statuses and supersessions accepted through an overlay.
- [ ] S1-D01 through S1-D13 each contain an approved selection, rationale,
      actor, timestamp, and authority.
- [ ] Different-person Financial Control approval is recorded for S1-D01/S1-D02 as
      applicable.
- [ ] Requirements delta and traceability independently reviewed.
- [ ] Candidate first-release scope approved.
- [ ] No ambiguity remains for Stage 2 deterministic behavior.
- [ ] Independent Stage 1 review returns PASS.
- [ ] Product Owner records Stage 1 PASS.

## 7. Required gate response

The Product Owner must approve or amend the selected options in
`STAGE-01-PRODUCT-AND-FINANCIAL-CONTROL-DECISIONS.md`. Protected identity and
CORE-04 also require the designated Financial Control authority and separation
of duties.

Until then:

- Stage 1 is **not complete**;
- Stage 2 is **blocked**;
- no product defect is reinterpreted as policy;
- no production behavior is changed; and
- packaging and release remain **NO-GO**.
