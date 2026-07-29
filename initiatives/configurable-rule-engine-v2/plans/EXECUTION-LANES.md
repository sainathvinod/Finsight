# FinSight Delivery Execution Lanes

- **Status:** Approved delivery policy
- **Effective date:** 2026-07-28
- **Scope:** FinSight implementation and remediation work
- **Approval gates:** Unchanged

This policy introduces two execution lanes inside the existing
Specification-Driven Development framework. The lanes determine the depth of
change control and verification; they do not create another product, repository,
workflow, or approval gate.

## 1. Governed Lane

Use the Governed Lane for any change that affects or may affect:

- architecture or dependency direction;
- business or financial logic;
- the deterministic rule engine or rule definitions;
- persistence, migrations, data models, source extraction, or reconciliation;
- authentication, authorization, security, privacy, audit, or governance;
- workflow states, navigation semantics, permissions, or user-task outcomes;
- report/export meaning, analytics calculations, or Ask Fin data boundaries;
- packaging, installation, runtime dependencies, or release behavior; or
- approved requirements, ADRs, architecture contracts, or other governed
  specifications.

Governed Lane work follows the applicable approved stage or workflow plan. Its
verification and review depth is proportional to the affected trust boundaries
and may include full regression, architecture fitness checks, security tests,
data and migration tests, independent review, specification updates, and the
existing stage gate.

## 2. Rapid UX Lane

Use the Rapid UX Lane only for a purely visual presentation change that leaves
all approved product behavior and trust boundaries unchanged.

Eligible examples include:

- spacing, alignment, sizing, and responsive layout;
- typography, color, borders, shadows, and surface styling;
- icon choice or placement using already-approved assets and dependencies;
- visual hierarchy and non-semantic static presentation copy;
- visual focus treatment and other presentation-only accessibility refinements;
- screenshot and theme polish; and
- presentation refactoring that preserves the same signals, service calls,
  enabled/disabled rules, navigation destinations, and data.

A change is **not** eligible when it adds or upgrades a runtime dependency,
changes which action is available, changes control meaning or task order, changes
data shown or persisted, changes an accessible control's behavior, or touches any
Governed Lane concern.

## 3. Rapid UX entry checklist

Before implementation, record that every answer below is **No**:

1. Does the change alter architecture, imports between layers, or runtime
   dependencies?
2. Does it alter business rules, calculations, validation, rule configuration,
   or financial meaning?
3. Does it alter persistence, migrations, source extraction, data models, audit,
   identity, authorization, security, or privacy?
4. Does it alter workflow state, navigation destination, action availability,
   keyboard behavior, permissions, or task outcome?
5. Does it require a requirements, ADR, architecture, governance, or release
   artifact to remain accurate?

If any answer is **Yes** or cannot be established confidently, use the Governed
Lane. If a Rapid UX change discovers a governed impact during implementation,
stop, document the impact, and reclassify the work before continuing.

## 4. Rapid UX execution and verification

For an eligible Rapid UX change:

1. Implement only the bounded presentation change.
2. Preserve the existing application services, persistence, security, audit,
   business logic, rule engine, and workflow semantics.
3. Run only:
   - UI tests directly covering the affected view or component;
   - accessibility tests directly covering the affected surface; and
   - the application launch smoke test.
4. Do **not** run the full regression suite.
5. Do **not** regenerate or revise unchanged requirements, architecture, ADR,
   governance, or specification artifacts.
6. Do **not** rerun architecture or governance reviews unless the implementation
   reveals a material effect on those artifacts.
7. Capture the affected screens at the relevant supported viewport, state, and
   appearance modes.
8. Record the lane classification, exact files changed, targeted checks and
   results, screenshot paths, and known limitations.
9. Stop and present the result for Project Owner hands-on review.

The Project Owner review is the Rapid UX stopping point. No later workflow or
unrelated remediation begins until that review is complete.

## 5. Decision table

| Change | Lane |
|---|---|
| Adjust card spacing, typography, or theme tokens without changing meaning | Rapid UX |
| Replace an existing icon through the already-qualified icon library | Rapid UX |
| Reorder or add a workflow step | Governed |
| Change when a button is enabled or who may use it | Governed |
| Change a rule, calculation, reconciliation, or finding | Governed |
| Change workbook extraction or displayed financial data | Governed |
| Add a runtime UI dependency | Governed |
| Change persistence, migrations, identity, audit, security, or packaging | Governed |
| Visual work whose behavioral impact is uncertain | Governed |

## 6. Relationship to stage-based delivery

The five approved gates remain:

1. Requirements;
2. Architecture;
3. Workflow Phase Implementation;
4. Final Product; and
5. Windows Packaging and Release.

The Governed Lane is the default for work that contributes to or changes a
governed stage. The Rapid UX Lane is a bounded execution shortcut for
presentation-only changes inside an already approved product contract. It never
waives or weakens a gate when the underlying change belongs to that gate.
