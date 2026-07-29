# Requirements Stage

The detailed V2 requirements are authored through the specification-driven workflow under `../specs/`:

1. specify draft FR/NFR delta registers;
2. clarify every blocking ambiguity;
3. obtain an independent full Requirements PASS;
4. record the HD-27 Requirements completion decision;
5. proceed to reviewed Architecture and design artifacts;
6. decompose and baseline through the governed SDD lifecycle before implementation.

The initiative specifications extend the existing FinSight specification set; they do not duplicate or silently rewrite it.

The clarification register is closed and the supplied-report V1 semantics and governance model are defined. The repaired FR-123–FR-203 and NFR-081–NFR-110 snapshots received a fresh independent full PASS and subsequently supported the approved Architecture stage. Their historical gate disposition did not independently authorize implementation.

## Current artifacts

- `../specs/01-functional-requirements.md` — FR-123–FR-203
- `../specs/02-non-functional-requirements.md` — NFR-081–NFR-110
- `../specs/03-existing-rule-disposition.md` — complete 57-rule preservation and future-migration register
- `../specs/clarifications/CLARIFICATION-PACKET-2026-07-27.md` — closed decision and downstream-routing record
- `../specs/generated/SPEC-AUDIT-2026-07-27.md` — initial independent audit and remediation record
- `../specs/generated/SPEC-AUDIT-2026-07-27-FULL-REVIEW.md` — historical first full Requirements PASS
- `../specs/generated/SPEC-CROSSCHECK-2026-07-27.md` — later independent FAIL that superseded the first PASS as gate evidence
- `../specs/generated/SPEC-AUDIT-2026-07-27-RECHECK.md` — current fresh independent full Requirements PASS
- `GOVERNED-V2-DELTA-2026-07-27.md` — explicit V2-to-parent consistency and future re-baselining record
- `REQUIREMENTS-PHASE-COMPLETION-2026-07-27.md` — HD-27 gate-completion record and Architecture authorization

The initial, first-PASS, and post-PASS cross-check verdicts are preserved as audit history. The recheck PASS is the current Architecture gate evidence. It does not authorize application implementation.

## Final MVP remediation delta

- [MVP Remediation Requirements Delta — 2026-07-28](MVP-REMEDIATION-DELTA-2026-07-28.md)

This additive delta records the Project Owner's later, approved Workflow Phase
Implementation remediation scope. It does not rewrite the independently reviewed
Requirements baseline or imply that remediation implementation has been verified.
