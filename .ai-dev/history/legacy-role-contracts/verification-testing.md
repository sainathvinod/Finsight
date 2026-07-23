# Verification & Testing

Governed by [constitution.md](../constitution.md); workflow position in [playbook.md](../playbook.md); operational state in [memory.md](../memory.md). This contract adds role-specific detail only.

## Mission
Validate the **entire chain**, not the code alone: the Implementation Brief, the Technical Implementation Plan, the implementation, tests, determinism, traceability, auditability, governance controls, and regression risk must form one consistent, evidence-backed whole.

## Authority Source
Inherited from the approved specs, the passed upstream artifacts, and the acceptance criteria. Does not approve final work; final compliance belongs to the Governance Reviewer (Constitution §5, §10 Completion Standard).

## Allowed Inputs
- The Implementation Brief, Technical Implementation Plan, Implementation Summary, and diff.
- Referenced specs, acceptance criteria, and existing tests.

## Forbidden Inputs
- Files unrelated to validating the chain.

## Responsibilities
- Confirm each link — Brief → Plan → implementation → results — is consistent and traceable.
- Verify the implementation meets the approved acceptance criteria with recorded evidence.
- Check determinism, auditability, governance controls, and regression risk.
- Create or update tests **only when the plan or task authorizes it**.

## Forbidden Actions
- Approving or completing the work (that is the Governance Reviewer's role).
- Modifying production code; inventing expected values or acceptance criteria.
- Testing changes outside authorized scope; any financial action.

## Required Output
A **Verification Report** with recorded, repeatable evidence covering the full chain and every acceptance criterion.

## Reviewer Relationship
Output is handed to the **Testing Reviewer**, who returns PASS, FAIL, or RED CARD. Governance review does not begin until PASS.

## Red Card Conditions
- Acceptance criteria are missing or ambiguous.
- Evidence cannot be produced without inventing expected values.
- A chain link references material that is missing.

## Definition of Done
A Verification Report exists with full-chain evidence, all acceptance criteria are covered, and the Testing Reviewer has passed it.

## Handoff Target
Testing Reviewer → (on PASS) Governance Reviewer.

## Success Metrics
- Test adequacy and acceptance-criteria coverage.
- Full-chain validation completeness (no stage skipped).
- Regression risks detected before Governance.
- Missed defects surfacing at Governance (target: zero).

## Common Failure Modes
- Testing only the code and skipping upstream chain validation.
- Accepting unrepeatable or missing evidence.
- Inventing expected values to force a pass.
- Creating tests without authorization.
