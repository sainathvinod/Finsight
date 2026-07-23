# Test Plan — <F-##-## / task id>

<!-- Template (leaf). Scaffolding only — no normative rules, no agent references.
     Markers and gates per .claude/standards/testing.md. -->

- **Traces to:** <acceptance criteria IDs>
- **Prepared:** <date>

## 1. Scope of verification
<Which acceptance criteria and which chain links are validated.>

## 2. Test cases
| Case | Marker (unit/golden/determinism/fitness/accessibility/audit/security) | Verifies (ID) | Expected (from specs) |
|---|---|---|---|

## 3. Determinism / regression gates (if applicable)
- [ ] Golden-dataset regression
- [ ] Determinism (repeated-run identity)
- [ ] Provider-swap invariance (AI layer only)
- [ ] Architecture fitness (import contracts)

## 4. Domain cases (if in scope)
- [ ] Original vs. corrected value; source unchanged; analysis uses certified value
- [ ] Audit event created per correction
- [ ] Findings appear only after a review is selected
- [ ] Fin explains but does not recompute (R2)

## 5. Evidence & how to reproduce
<Commands and expected results. No invented expected values — cite the spec.>
