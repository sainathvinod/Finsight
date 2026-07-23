# Standard — Accessibility

**Layer:** standard (normative, leaf). Referenced by skills and recipes. References no agents.
**Origin / authority:** `NFR-025`, `NFR-026`; `specs/07-ux-design.md`; `specs/08-ui-design-system.md`; existing `tests/accessibility/`.

## Rule

1. **Severity is never encoded by color alone.** Severity (Critical / High / Medium / Low) is conveyed by **icon + shape/marker + text label**, so it is distinguishable without color perception (`NFR-025`). The reference text-mode encoding in `delivery/wizard.py` (`[XXX]`, `[!!]`, `[=]`, `[.]` + label) demonstrates non-color severity marking.
2. **Keyboard operability.** Interactive flows are fully operable by keyboard; presentation must not depend on pointer-only interaction (`NFR-026`).
3. **Grounding.** Accessibility behavior derives from the approved UX design (`07`) and UI design system (`08`); do not invent visual or interaction rules beyond them.
4. **Verification.** Accessibility expectations are exercised under `tests/accessibility/` with the `accessibility` marker (see [testing.md](testing.md)).

## Escalation

If a UI element's accessible representation is not defined by `specs/07`/`08`, raise a **Red Card** rather than inventing one.
