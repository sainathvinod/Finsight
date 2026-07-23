# Pattern — Guided Review Wizard (spec = 8 steps)

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** `specs/07-ux-design.md §5`; `DEC-024`; `specs/constitution.md` glossary "Guided Review Wizard".

## Convention (authoritative spec sequence)
The Guided Review Wizard has **8 steps**, with a persistent "Step X of 8":

```
Create → Upload → Validate → Verify → Analyze → Findings → Summary → Complete
```

## Known drift (do not "fix" here)
The current text-mode `delivery/wizard.py` implements a **9-label** sequence
("Review Setup, Data Upload, Upload Validation, Processing, Verification, Analysis,
Findings, Leadership Summary, Export"). This spec-vs-code drift is **recorded, not repaired**
by this AI-engineering migration — changing product behavior is out of scope and would need a
separate governed change. When authoring UI work, follow the spec's 8-step definition (`DEC-024`)
and raise the drift for a human decision.

## Checks
- New UI flows reference the 8-step spec sequence; any deviation is flagged, not silently adopted.
