# FinSight MVP — Design QA

> **Historical verification record.** This document records the focused visual
> state at the named 2026-07-28/29 checkpoints. It is not current release-gate
> evidence. The 2026-07-29 governed closeout subsequently reproduced a failing
> 200% appearance-control test and an order-dependent Ask Fin drawer-width test.
> Current product status is **NO-GO** pending the production-readiness
> stabilization stages.

- **Date:** 2026-07-29
- **Latest scope:** Ask Fin automatic local enablement and simplified
  unavailable state
- **Source visual truth:** the user's attached dark-mode Ask Fin screenshot and
  the stored 1440 × 960 pre-remediation unavailable state at
  `initiatives/configurable-rule-engine-v2/verification/screenshots/stage2/dark/11-private-ask-fin-local-status.png`
- **Latest implementation:** `initiatives/configurable-rule-engine-v2/verification/screenshots/ask-fin-simplified/{light,dark}/`
- **Combined same-state comparison:** `artifacts/design-qa/ask-fin-simplified/02-unavailable-before-after-drawer-focus.png`
- **Normalization:** the stored source and implementation comparison inputs are
  both 1440 × 960 Qt captures of the validated May 2026 synthetic review in
  Dark mode. The same final states were also captured in Light mode.
- **Landing reference viewport:** approximately 2048 × 1104 desktop
- **Primary application viewport:** 1280 × 900 desktop
- **Responsive desktop viewport:** 1180 × 860
- **Landing reference:** user-provided mockup attached inline to the 2026-07-28
  landing-page remediation request. The chat attachment was visually available
  for direct comparison, but the client did not expose a reusable filesystem path.
- **Earlier workflow reference:** approved walking-skeleton captures in
  `artifacts/ui-verification/`
- **Implementation evidence:** `initiatives/configurable-rule-engine-v2/verification/screenshots/mvp-end-to-end/`

## Latest focused comparison — Ask Fin simplification

The attached source showed that a locally available model could still leave
the composer disabled behind an identity-approval/setup prompt. The corrected
healthy state opens directly into an enabled question field after FinSight
verifies the loopback Ollama runtime and installed local model. There is no
Open Setup action, manual digest approval prompt, or duplicate setup message.

The unavailable state now removes the disabled transcript and composer
entirely. One compact card says that Ask Fin could not connect to local Ollama
and provides one Retry action. Privacy, review scope, and the deterministic
financial results remain visible.

### Findings

The first post-change capture exposed a material P2 layout defect: hiding the
conversation surface allowed the remaining drawer cards to expand vertically.
An unavailable-only expanding filler now keeps those cards top-aligned, and
the Light/Dark evidence was recaptured. No actionable P0, P1, or P2 visual
differences remain. The focused comparison makes the removal of the disabled
composer, duplicated outage copy, and setup friction directly visible.

### Latest iteration history

1. **Before:** Ask Fin displayed a full disabled conversation interface and a
   second outage explanation, while the user-facing setup flow required manual
   local model identity approval.
2. **Correction:** automatic local verification enables the healthy composer;
   the unavailable state was reduced to one message and one Retry action.
3. **Visual correction:** the unavailable drawer was constrained to a compact,
   top-aligned state after the first capture revealed vertical expansion.
4. **Post-fix evidence:** the same real local question produced a grounded
   answer with one source citation without a digest environment setting; Retry
   restored the composer after the simulated outage.

## Prior focused comparison — landing scale

The accepted landing structure was preserved exactly while the center content
was reduced to normal desktop scale. The full-view comparison verifies the
unchanged sidebar, header controls, copy, action order, side-by-side layout,
cream/navy palette, and Light/Dark treatment. It also makes the requested
proportional changes directly visible: the display title is about 21% smaller,
the subtitle and description are modestly smaller, the cards and medallions are
smaller, the internal padding is tighter, and the full hero begins higher.

No separate crop was needed: at 1280 × 900 the combined comparison keeps the
complete hero, card typography, icon medallions, borders, buttons, and shell
labels readable at once. Automated checks additionally exercised keyboard
activation, accessible names/descriptions, narrow-width reflow, and 200% text
scaling. The focused launch smoke completed without a fatal Qt error.

### Findings

No actionable P0, P1, or P2 differences remain. Typography, spacing, colors,
icon assets, copy, button states, and the side-by-side desktop composition match
the requested compact-scale direction. There are no remaining P3 items within
the user-authorized scope.

### Latest iteration history

1. **Before:** the accepted page had the right information architecture and
   visual language, but its 94 pt title and 310 px cards made the center read
   like a presentation.
2. **Correction:** the title cap was reduced to 74 pt, supporting type was
   stepped down, action cards were reduced to 260 px minimum height and a
   760 px combined width, medallions became 60 px, padding/gaps were tightened,
   and the hero spacer was reduced.
3. **Post-fix evidence:** the Light/Dark captures and combined comparison show a
   balanced desktop landing page with unchanged shell and application behavior.

## Method

The final landing mockup and the rendered PySide6 landing page were reviewed
together at the mockup's approximately 2048 × 1104 viewport. Full-view and
focused comparisons covered the sidebar/icon treatment, application header,
hero hierarchy, explanatory copy, action cards, disabled Past Reviews state,
and removal of the identity footer. The implementation was then recaptured in
Light and Dark at 2048 × 1104, 1280 × 900, and 1180 × 860.

The approved walking-skeleton states and the rest of the implemented PySide6
journey were previously captured at the same 1180 × 860 viewport and combined
side by side. System Default was exercised headlessly and resolved to the
operating-system Light appearance; runtime system-following and preference
persistence are also covered by automated tests.

The current approved requirements supersede older prototype content where they
conflict: the application uses the seven stages Create, Upload, Verify Data, Review
Rules, Validate, Review Results, and Complete; Upload accepts exactly Budget and GED;
and results use the seven approved result sections.

## Comparison evidence

### Final landing page

| Viewport and state | Light | Dark |
|---|---|---|
| Reference-sized desktop, 2048 × 1104, empty review store | [01-welcome.png](artifacts/design-qa/landing-2048x1104/light/01-welcome.png) | [01-welcome.png](artifacts/design-qa/landing-2048x1104/dark/01-welcome.png) |
| Primary desktop, 1280 × 900, empty review store — latest compact scale | [01-welcome.png](artifacts/design-qa/landing-scale-1280x900/light/01-welcome.png) | [01-welcome.png](artifacts/design-qa/landing-scale-1280x900/dark/01-welcome.png) |
| Responsive desktop, 1180 × 860, empty review store | [01-welcome.png](artifacts/design-qa/landing-1180x860/light/01-welcome.png) | [01-welcome.png](artifacts/design-qa/landing-1180x860/dark/01-welcome.png) |

The source mockup remains the focused comparison input for both visible regions:

- **Sidebar/header focus:** brand, grouped navigation labels, one consistent
  outline icon family, active/disabled states, Theme, Ask Fin, and no account
  identity block.
- **Hero/action focus:** display title, assistant subtitle, exact product
  description, equal side-by-side action cards, semantic card icons, and
  primary/secondary action treatment.

### Existing end-to-end workflow

| State | Combined visual |
|---|---|
| Create Review | [01-create-review-comparison.png](artifacts/design-qa/01-create-review-comparison.png) |
| Upload & Extraction | [02-upload-comparison.png](artifacts/design-qa/02-upload-comparison.png) |
| Verify Data | [03-verify-data-comparison.png](artifacts/design-qa/03-verify-data-comparison.png) |
| Executive Overview | [04-results-overview-comparison.png](artifacts/design-qa/04-results-overview-comparison.png) |
| Findings evidence | [05-findings-comparison.png](artifacts/design-qa/05-findings-comparison.png) |

## Focused review

| Area | Result | Evidence |
|---|---|---|
| Welcome hierarchy | Pass after scale adjustment | `FinSight` remains the unambiguous upper-middle focal point at a 74 pt cap, followed by a more compact assistant subtitle, exact approved description, and two equal desktop action cards. Recent Reviews and all competing landing-page metadata remain absent. |
| Navigation consistency | Pass after remediation | The landing shell reproduces the mockup's FinSight brand, REVIEW WORKSPACE / APPLICATION / ASSISTANCE group labels, and labeled Home, Past Reviews, Rule Governance, Settings, and Ask Fin entries. Every entry uses the same Phosphor icon family through QtAwesome. The shell grows to a reference-proportional 330 px on wide screens, remains 260 px on standard desktop, and contracts to 240 px at the minimum supported width. The identity/avatar/role footer is absent. |
| Header hierarchy | Pass after remediation | Landing-only breadcrumbs and review metadata are hidden, leaving Theme and Ask Fin as quiet secondary actions in the top-right, matching the reference hierarchy. |
| Landing cards | Pass after scale adjustment | The 260 px cards are equal, aligned, softly elevated, and side by side at supported desktop widths. Their 60 px icon medallions, tighter padding, and 760 px combined width create the requested normal desktop density. The empty-store Past Review action remains visibly and semantically disabled. |
| Settings and appearance | Pass after remediation | A keyboard-accessible Settings destination exposes Light, Dark, and System Default through the shared appearance manager; the compact header menu remains a convenient secondary entry point. |
| Card alignment and form density | Pass | Warm surfaces, deliberate rounded cards, compact Create Review form, aligned upload cards, and balanced desktop spacing avoid a narrow wizard presentation. |
| Typography and copy | Pass | Clear heading/body hierarchy, restrained metadata, plain-language error copy, and business-first labels remain readable in both themes. |
| Tables and evidence | Pass | Headers, row states, scrolling, source references, original/current provenance, and evidence actions are readable at both tested desktop widths. |
| Charts | Pass after remediation | Legends no longer collide with axis titles, dense account labels are sampled legibly, exact-data tabs retain every value, and Light/Dark labels remain visible. |
| Status and error states | Pass | Success, warning, error, incomplete, disabled, selected, loading, and required-field states use text and structure as well as color. |
| Rules Repository | Pass after remediation | Protected status, purpose, version, fields, grouping keys, optional lifecycle controls, and disabled protected actions are visually distinct. The global governance queue shows the request-time baseline, before/after definitions, content hash, qualification evidence, future binding effect, requester, independent decision, and activated baseline without losing page context. A separate Workspace Baseline Upgrades card shows workspace status, request-time Rule Set/run, exact target, two-actor decision evidence, resulting Rule Set, and the required Reviewer revalidation action. Long immutable identifiers remain complete in the selectable detail pane while compact list labels avoid horizontal scrolling. |
| Findings evidence | Pass after remediation | Duplicate records `GED:GED:65` and `GED:GED:66` appear side by side; rule and finding views remain different and source evidence is actionable. |
| Delete Review dialog | Pass | Consequence copy is explicit, acknowledgement is required, permanent action is disabled initially, and Cancel is the safe focused default. |
| Light mode | Pass | Warm cream canvas, warm white cards, navy navigation/actions, soft borders, and reserved semantic colors match the requested financial visual direction. |
| Dark mode | Pass | Deep navy canvas/panels, off-white text, accessible borders/focus, and adjusted chart/status colors retain every label and control. |
| System mode | Pass with headless evidence limitation | System Default resolved to Light in the offscreen run; automated tests cover operating-system changes and persisted selection. A live OS-switch visual cannot be evidenced headlessly. |
| Keyboard focus and accessibility | Pass for latest scope | Native controls, visible focus rings, names/descriptions, non-color disabled state, keyboard navigation, and 200% text-scaling coverage passed the focused Rapid UX test selection. The full regression suite was intentionally not rerun for this presentation-only adjustment. Native screen-reader smoke remains a hands-on item. |
| Zoom and resizing | Pass | Landing evidence covers three desktop sizes. Cards stay side by side at 1180 × 860 and stack only below the narrow-desktop breakpoint; scrolling preserves access where large type or reduced height requires it. The full journey retains its existing responsive behavior. |

## Landing remediation iteration history

1. **Initial comparison:** the implemented page used a conventional dashboard
   hierarchy, a smaller heading, recent-review content, text-only navigation,
   and an account identity footer. These were material mismatches with the final
   reference.
2. **Structural correction:** removed Recent Reviews and the identity footer;
   hid landing breadcrumbs/context; replaced the copy with the approved wording;
   centered the hero; and rebuilt the action region as two equal cards.
3. **Asset and state correction:** added real Phosphor icons through QtAwesome
   for every sidebar and card action, retained clear labels, and preserved the
   required disabled Past Reviews behavior for an empty store.
4. **Visual correction:** increased display, subtitle, body, card, and brand
   typography; added the reference-proportional adaptive sidebar and wider-screen
   navigation density; applied warm cream/navy tokens, subtle borders, icon
   medallions, and restrained shadows; and verified the same treatment in Dark mode.
5. **Responsive correction:** fixed wrapped-description sizing and constrained
   display type at 200% text scaling so narrow windows do not gain a horizontal
   scroll path. Final evidence was recaptured at all three desktop viewports.
6. **Rapid scale correction:** reduced only the landing title, supporting copy,
   action-card dimensions, icon size, internal padding, section gaps, and hero
   offset. The shell, navigation, wording, themes, and behavior were unchanged.
   The focused Light/Dark comparison passed without P0/P1/P2 findings.

## Intentional differences from the walking skeleton

- The current approved seven-stage progress indicator replaces the older workflow
  rail.
- Upload accepts exactly two required reports, so the older optional Invoice card
  is not reproduced.
- Verify Data shows the full preserved Budget and GED report rows with governed
  working-copy editing, provenance, history, and attestation controls.
- The Results workspace is review-specific and consumes the deterministic sealed
  rule projection rather than reproducing the older portfolio dashboard.
- The final presentation uses the requested warm cream/navy theme and adds complete
  Light, Dark, and System appearance behavior.

No material layout break, clipped required content, hidden dark-mode label,
unexplained primary technical error, chart collision, or mobile-style desktop
presentation remains in the reviewed journey.

**Final result: passed**
