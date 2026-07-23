# FinSight — UI Design System

**Document:** 08-ui-design-system.md
**Status:** Approved
**Date:** 2026-07-15
**Scope:** The **visual language and design system** of FinSight — visual identity, color, themes, typography, spacing, layout, the component library, and the visual/accessibility presentation of the experiences already defined in the UX document. This document decides *how FinSight looks and feels*, realizing the UX without changing it.
**Relationship to the UX document (binding):** 07-ux-design.md is the **source of truth for experience**. This document does **not** redesign workflows, create new experiences, change navigation, or alter the 8-step review lifecycle. It gives each already-defined screen (S-01–S-21) and step (Step 1–8) a visual realization. Where this document and the UX document could seem to differ, the UX document wins on behavior; this document wins only on presentation.
**Governing methodology:** Spec-driven development (DEC-010, NFR-073). Derived artifact; introduces no scope beyond the approved set.
**Sources of truth:** 00-project-understanding.md · 01-functional-requirements.md · 02-non-functional-requirements.md · 03-epics.md · 04-features.md · 05-rules-catalog.md · 06-architecture.md · 07-ux-design.md · 09-decision-log.md
**Provenance:** AI-drafted for human review and approved by the project owner. **Concrete token values (hex colors, px/rem sizes, spacing) are the approved set** — no source document specified a brand palette or type, so the values stand as a complete, usable set (brand-swappable via tokens); the *design rules and semantics* (light-default, color-independent meaning, contrast targets, AI distinction, severity encoding) are firm and trace to approved NFRs. This design system is Approved in the current baseline.
**Numbering note:** DEC-023 tentatively reserved `08` for "ai-and-agents." This document is produced as `08-ui-design-system.md` per current direction; a decision-log entry should record the renumbering (e.g., AI & agents → 10 or later) so the sequence stays consistent.

---

## 1. UI Vision

FinSight looks and feels like a **premium, calm, professional financial review platform built for Amerisure stakeholders** — not a generic AI product. The visual language makes the two product pillars visible at a glance:

- **Trust > AI** — the interface looks accurate, auditable, and reliable; deterministic content is primary and confident, AI content is clearly secondary, labeled, and restrained (never the visual hero).
- **Monthly Review in a Box** — the interface looks like a guided, orderly review process (the 8-step wizard is the spine), not a wall of dashboards.

The design should feel **premium, modern, refined, and intentional** — closer to Microsoft 365, Atlassian, Linear, and Apple-level clarity than to any AI-startup aesthetic. It should be **memorable through calm clarity and organization**, not through flash. A user opening FinSight should immediately feel *this is serious, trustworthy financial software.*

**Realization principle:** every visual decision serves comprehension, trust, and accessibility first; decoration never competes with information (echoing UXP-10 progressive disclosure and NFR-066).

## 2. Design Philosophy

**FinSight must not look like:** a ChatGPT/Copilot clone, an AI-startup website, a crypto or cyberpunk dashboard, a hacker terminal, a generic SaaS template, or a dark-mode-first product.

**FinSight must avoid:** neon gradients, glowing effects, futuristic "AI" visuals, purple-AI dashboard patterns, excessive animation, and flashy startup aesthetics.

**FinSight embraces:** a bright, clean, professional **light-first workspace**; layered neutral surfaces (never stark white everywhere); a single confident brand blue used with restraint; generous whitespace and a strict grid; typographic clarity with tabular numerals for financial data; and quiet, purposeful motion. The aesthetic is **enterprise-premium and finance-grade** — the visual equivalent of a well-run monthly close.

**Governing visual rule (from NFR-025):** *meaning is never carried by color alone.* Every status, severity, and state pairs color with an icon, a shape, and a text label. This is both an accessibility requirement and a core part of the FinSight look (labeled, legible, unambiguous).

## 3. Visual Branding Direction

- **Brand anchor:** a single **deep, professional "trust blue"** as the primary brand and action color — the finance/enterprise convention for stability and reliability — deliberately *not* the cliché AI purple. It is used with restraint: for primary actions, the active step, focus, and key emphasis, not as a wash across the UI.
- **Supporting accent:** a calm **teal** for secondary emphasis and links, used sparingly so the primary blue stays meaningful.
- **Neutrals do the heavy lifting.** Most of the interface is layered neutrals — a soft off-white canvas, white raised cards, and calibrated gray text/borders — giving a premium, uncluttered "workspace" feel.
- **Identity cues (memorable, not flashy):** (1) the **8-step progress stepper** as a consistent, signature header band inside every review; (2) the **Findings Hub** severity-rail layout (§12); (3) the **Review Complete** confirmation moment (§13); (4) the **deterministic-vs-AI visual separation** (§20). These recurring patterns *are* the FinSight visual signature.
- **Amerisure fit:** the palette is chosen to sit comfortably with a conservative insurance-enterprise brand; the exact brand blue and any logo lockup are set in the approved baseline (brand-swappable), and the token system is built so a brand-color swap is a token change, not a redesign.

## 4. Emotional Design Goals

| Users should feel | The design delivers it by |
|---|---|
| **Confident** | Clear hierarchy, one obvious next action per step, evidence always reachable |
| **Calm** | Light, uncluttered surfaces; restrained color; quiet motion; generous spacing |
| **Informed** | "Step X of 8" always visible; plain-language states; explicit readiness and completion |
| **Organized** | Grouped findings, consistent cards, a strict grid, predictable layouts |
| **In control** | Verification confirmation, source traceability, human-decision framing, AI clearly optional |
| **Supported** | Guided wizard, contextual help, actionable errors, honest empty/loading states |

Users should **not** feel overwhelmed, confused, uncertain, or distracted — so the system defaults to *less on screen, leading with what matters* (progressive disclosure), and never uses attention-grabbing motion or color for decoration.

---

## 5. Color System

> All values are set in the approved baseline (brand-swappable via tokens). Contrast targets are firm (WCAG 2.2 AA minimum; AAA for primary body text where feasible — NFR-026). Meaning is never color-only (NFR-025).

### 5.1 Primitive palettes (light-first scales)

**Neutral (slightly cool "slate" — the workspace foundation):**

| Token | Hex | Typical use |
|---|---|---|
| neutral-0 | `#FFFFFF` | Raised cards, inputs (used deliberately, not everywhere) |
| neutral-25 | `#FBFCFE` | App canvas tint — premium off-white (avoids stark white) |
| neutral-50 | `#F4F6F9` | Section backgrounds, table zebra |
| neutral-100 | `#EAEEF3` | Subtle fills, hover |
| neutral-200 | `#DCE2EA` | Borders, dividers |
| neutral-300 | `#C2CAD6` | Strong borders, disabled |
| neutral-400 | `#98A2B3` | Placeholder, muted icons |
| neutral-500 | `#6B7686` | Secondary text |
| neutral-600 | `#4B5568` | Body text (secondary) |
| neutral-700 | `#343D4D` | Body text (primary on light) |
| neutral-800 | `#222A36` | Headings |
| neutral-900 | `#131922` | Max-emphasis text, dark-theme canvas |

**Primary — "Trust Blue" (brand + action):**

| Token | Hex | Use |
|---|---|---|
| primary-50 | `#EBF2FC` | Tinted backgrounds, selected rows |
| primary-100 | `#D2E2F7` | Hover on tint |
| primary-200 | `#A9C6EE` | Borders on primary tints |
| primary-300 | `#6E9CDD` | Disabled primary |
| primary-500 | `#215FA8` | Base brand, links |
| primary-600 | `#184C8A` | **Primary buttons / active step** |
| primary-700 | `#123B6E` | Pressed, emphasis |
| primary-800 | `#0E2E54` | Dark-theme primary surfaces |

**Secondary — "Calm Teal" (sparing accent):** teal-50 `#E6F3F3` · teal-500 `#0F7B82` · teal-600 `#0B646A` · teal-700 `#084C50`.

### 5.2 Semantic (status) colors — each dual-encoded with icon + label

| Semantic | Light hue (600) | Tint (50) | Paired icon | Text label examples |
|---|---|---|---|---|
| Success / positive | `#1E7A46` | `#E7F4EC` | check-circle | "Ready", "Verified", "Reconciled" |
| Warning / attention | `#A5670C` | `#FBF1DC` | alert-triangle | "Needs attention", "Low confidence" |
| Danger / error | `#B42318` | `#FBEAE8` | octagon / x-circle | "Error", "At risk", "Rejected" |
| Info / neutral notice | `#1570CD` | `#E7F1FC` | info-circle | "Note", "AI available" |

### 5.3 Severity colors (Findings — Critical/High/Medium/Low, FR-070)

Dual-encoded by **hue + distinct shape + label + weight**, ordered so intensity reads without color and is color-blind-safe (no reliance on red↔green):

| Severity | Hue (600) | Shape/icon | Label | Weight cue |
|---|---|---|---|---|
| **Critical** | `#B42318` (red) | filled **octagon** | "Critical" | boldest; leads the list |
| **High** | `#C15211` (burnt orange) | filled **triangle** | "High" | bold |
| **Medium** | `#2A6DB0` (blue) | **diamond** | "Medium" | medium |
| **Low** | `#5B6675` (slate) | small **dot/circle** | "Low" | regular |

Severity is always shown as a **badge = shape-icon + text label (+ color)**; color may be removed (high-contrast/color-blind) and the badge still reads correctly.

### 5.4 RAG status (Leadership summary — Green/Yellow/Red, FR-077)

Always paired with a **word label** so it is never color-only:

| RAG | Hue | Icon | Mandatory label |
|---|---|---|---|
| Green | `#1E7A46` | check-circle | **"On Track"** |
| Yellow | `#A5670C` | alert-triangle | **"Needs Attention"** |
| Red | `#B42318` | octagon | **"At Risk"** |

### 5.5 AI-content color treatment (NFR-049) — restrained, not "AI-purple"

AI-generated content uses a **neutral, clearly-bordered "assistant" container** — a subtle neutral-tint surface (`neutral-50`/`#F4F6F9` with a distinct 1px `neutral-300` left-accent border), an **"AI-generated" label**, a small assistant glyph, and **provider/model attribution**. It deliberately does **not** use brand blue, gradients, glow, or purple — AI is visually *subordinate and distinct*, never the hero (Trust > AI; §20).

### 5.6 Functional tokens (semantic aliases → primitives)

`surface/canvas` = neutral-25 · `surface/raised` = neutral-0 · `surface/sunken` = neutral-50 · `border/default` = neutral-200 · `border/strong` = neutral-300 · `text/primary` = neutral-800 · `text/secondary` = neutral-600 · `text/muted` = neutral-500 · `action/primary` = primary-600 · `action/primary-hover` = primary-700 · `focus/ring` = primary-500 (2px, 2px offset) · `link` = primary-600. Components reference **functional tokens only**, so theming (§6) is a token remap, not a component change.

---

## 6. Theme System

**Default theme is LIGHT (NFR-024).** Dark mode exists but is **never the default**. All four themes share one token contract; only token *values* change.

| Theme | Behavior | Notes |
|---|---|---|
| **Light (default)** | Bright, clean, premium; layered neutrals on an off-white canvas | The welcoming default experience; not stark white |
| **Dark** | Deep neutral canvas (`neutral-900`/`#131922`), raised surfaces one step lighter; primary/severity hues shifted to maintain AA contrast | Opt-in; follows OS if the user chooses "match system" |
| **High Contrast** | Maximum contrast (near-black text on white / white on black), **borders replace shadows**, thicker focus rings, no tinted fills relied upon for meaning | Honors OS high-contrast; meaning carried by borders/labels/shape |
| **System (auto)** | Follows OS light/dark (NFR-024) | User-selectable; light is still the product default when unset |

**Theme rules:** (1) severity/RAG/status keep their shape+label in every theme, so meaning survives even where hues compress (high contrast); (2) contrast is re-validated per theme to AA; (3) the AI-content treatment stays visually distinct in every theme; (4) theme choice persists per user and is exposed in Accessibility Settings (S-… / §13/§15). Theme switching is instant and never destructive.

---

## 7. Typography System

**Type family — system-first (enterprise, offline-safe):** `-apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`. Rationale: renders natively and professionally on Windows and macOS (parity, NFR-028), **loads no external font** (offline capability NFR-007; no external egress NFR-011), and reads as clean enterprise software — not trendy. Financial numerals use **tabular figures** (`font-variant-numeric: tabular-nums`) everywhere amounts align (tables, summaries) so columns line up and scan cleanly. No stylized/display or ultra-thin faces.

**Type scale (base 16px = 1rem; ~1.2 modular; weights 400/500/600 only):**

| Role | Size / line-height | Weight | Use |
|---|---|---|---|
| Display | 34 / 40 | 600 | Welcome greeting only |
| H1 | 28 / 36 | 600 | Screen title |
| H2 | 22 / 30 | 600 | Section title |
| H3 | 18 / 26 | 600 | Card/group title |
| H4 | 16 / 24 | 600 | Sub-group, finding title |
| Body-lg | 16 / 24 | 400 | Primary reading text, summary body |
| Body (default) | 14 / 22 | 400 | Default UI text |
| Body-sm | 13 / 20 | 400 | Dense tables, secondary detail |
| Caption | 12 / 16 | 400/500 | Metadata, timestamps, source refs |
| Label / Overline | 12 / 16 | 600 (slight tracking) | Section labels, badges, "Step X of 8" |
| Data / numeric | inherits size, **tabular** | 500 for emphasis | Amounts, variances, counts |

**Accessibility sizing (NFR-027):** base respects OS text-size; an in-app **Text Size** control (Default / Large / Larger) scales the rem base (≈100 / 112.5 / 125%); layouts use relative units so **200% browser/OS zoom** reflows without breakage or loss of function; minimum rendered body text stays ≥ 12px (prefer ≥ 14px); headings never rely on size alone for structure (semantic headings for screen readers, §15). Emphasis uses weight/label, not italics for critical meaning.

---

## 8. Layout System

- **Application shell (realizes C-01, S-01):** a persistent, slim primary navigation (Home, Settings, Audit, Help, switch-review) plus a top bar (review name, theme/text-size, help). Navigation is quiet and low-prominence so it never competes with the wizard (UXP navigation model, §7 of 07).
- **Inside a review:** a prominent **progress-stepper band** (the 8-step wizard, §11) sits directly under the top bar as the dominant orientation surface; the step content fills a centered content column.
- **Content width & density:** primary content column max ≈ 1200–1280px on wide monitors (comfortable line lengths); comfortable density default, with a **compact** density option for large data tables. Corporate-laptop layouts (≈1280–1440) are the primary target (NFR-065); external monitors get more whitespace, not more clutter.
- **Grid:** a 12-column responsive grid with consistent gutters; cards and tables snap to it. One-thing-per-region: each screen leads with a single primary object (the wizard step, the findings groups, the summary).
- **Elevation:** three restrained shadow levels (canvas → raised card → overlay); in High Contrast, **borders replace shadows** entirely. No heavy drop shadows, no glows.
- **Radius:** sm 4px (inputs, badges), md 8px (cards, buttons), lg 12px (modals, major panels), pill for status chips.

## 9. Spacing System

**4px base grid.** Named tokens: `space-1`=4, `space-2`=8, `space-3`=12, `space-4`=16, `space-5`=20, `space-6`=24, `space-8`=32, `space-10`=40, `space-12`=48, `space-16`=64. Rules: component internal padding uses 8/12/16; card padding 16–24; section rhythm 24–32; page margins 24–48 responsive. Generous spacing is a *feature* (calm, premium) — density is opt-in, not default. Vertical rhythm follows the type line-heights so text baselines feel aligned.

---

## 10. Component Library

All components reference **functional tokens** (§5.6), carry full keyboard + screen-reader semantics (§15), and pair any color meaning with icon/label (NFR-025).

- **Buttons.** *Primary* (filled primary-600, one per view — the step's next action), *Secondary* (neutral outline), *Tertiary/Ghost* (text-only), *Danger* (danger-600, for destructive/reject — always with confirming label). Sizes sm/md/lg; clear hover/active/focus/disabled; min hit target 40px height, 44px on touch. Never color-only — icons/labels always present.
- **Form controls.** Text input, number input (tabular), select/combobox, checkbox, radio, toggle, date/period picker, textarea. States: default/hover/focus/error/disabled/read-only. Errors show an icon + message + `aria-describedby`; labels are always visible (no placeholder-as-label). File upload (drop zone + button; keyboard-operable; never drop-only — NFR-026).
- **Cards.** Raised surface, md radius, 16–24px padding, optional header/footer. The atomic container for findings, summary sections, readiness capabilities, recent-review items.
- **Data tables.** Tabular numerals, right-aligned amounts, sortable headers (aria-sort), sticky header, zebra optional (neutral-50), comfortable/compact density, row hover, keyboard row navigation. Wide tables scroll horizontally **within their own container** (never the page — NFR-065). Every cell that is a finding/figure is drillable to source (§20).
- **Status indicators.** Pill/badge = icon + label (+ tint). Used for review status, readiness, cleared/reconciled, verification state.
- **Severity indicators.** The badge system in §5.3 (shape-icon + label + color); appears on findings, group headers (as counts per severity), and summary risk items.
- **Accordions / expand-collapse.** Used for findings groups and readiness detail; header shows title + count/severity summary; `aria-expanded`; keyboard toggle; **default collapsed with critical-first surfaced** (progressive disclosure, NFR-066). Chevron icon indicates state (not color).
- **Progress stepper.** §11 (signature component).
- **Alerts (inline/banner).** Info/success/warning/danger variants; icon + heading + body + optional action; used for readiness reasons, errors, cold-start honesty. Never a bare color bar.
- **Notifications / toasts.** Brief, non-blocking confirmations (e.g., "File uploaded", "Corrections saved"); auto-dismiss with a persistent option; announced via `aria-live=polite`. No external/push notifications in MVP (FR-083).
- **Empty states.** §18. **Loading states.** §19.
- **Modals / drawers.** Confirmations (continue-anyway S-05, Review Complete S-07b), the source-trace drawer, Explain This panel. Focus-trapped, ESC-closable (unless a hard gate), returns focus on close.

## 11. Progress Stepper Design (signature)

The stepper visually *is* the guided review (07 §5). It realizes "Step X of 8" and the wizard identity.

- **Form:** a horizontal band of 8 nodes with connectors, each node = **number + short label** (Create · Upload · Validate · Verify · Analyze · Findings · Summary · Complete). A persistent **"Step X of 8"** text sits with it.
- **States (color + icon + label, never color-only):**
  - *Complete* — check icon + full-weight label + filled connector.
  - *Current* — filled primary-600 node, bold label, `aria-current="step"`.
  - *Upcoming* — outlined node, muted label.
  - *Blocked by gate* — the Verify→Analyze boundary shows a small **lock/gate affordance** with a tooltip ("Verify data to continue") until verification is confirmed (mirrors the hard gate; UX §7).
- **Responsive:** wide → full horizontal stepper; narrow/laptop → condensed ("Step 4 of 8 — Verify Data" with a compact progress bar and a prev/next affordance); it never wraps into an unreadable mess.
- **Accessibility:** rendered as an ordered list with `aria-current` on the active step; each step's state is in text; keyboard focusable; announced on advance via `aria-live`. Completed/current/upcoming are distinguishable without color (icon + weight + position).
- **Motion:** advancing a step uses a subtle ≤200ms transition; respects reduced-motion (instant) (§16).

## 12. Findings Hub Design (the signature screen — Step 6, S-09)

The Findings Hub is FinSight's most important screen and its signature experience. It must let a user instantly grasp **what is important, what can wait, and where issues exist** (UXP-05/10; NFR-066/067).

- **Layout — the "review inbox" with a severity rail.** A triage summary header (counts per severity: Critical/High/Medium/Low as badges) sits above **capability groups** (Budget, GED, Reconciliation …) rendered as accordions with per-group counts and their top severity. A left **severity/filter rail** lets the user scope by severity, status, capability, account, vendor, period (FR-074) — all deterministic, no AI (FR-102).
- **Hierarchy & density:** groups default **collapsed**, with **Critical/High surfaced first** on completion (FR-082); expanding a group reveals finding rows at comfortable density (compact option). Progressive disclosure keeps the default view calm.
- **Finding row:** severity badge (shape+label+color) · finding title · affected entity (account/vendor) · key evidence value (tabular) · status chip (New/Acknowledged/In review/Resolved/Dismissed) · "Explain This" and "View source" affordances. One row = one finding; consistent across every capability (no per-capability forks — AP-12).
- **Two lenses (F-06-01):** an **Operator work-queue** view (actionable, resolve-oriented) and a **Leader decision** view ("needs my decision") — a toggle over the *same* records, not two screens.
- **Reconciliation:** appears as a findings group here; the **matching sub-task** opens as a focused work drawer/view (S-11) and returns to the hub (UX §14.1) — one experience, not a separate system.
- **Evidence presentation:** every finding row exposes its computed evidence value and is one interaction from full evidence (§13 investigation / Explain This). Numbers are tabular and drillable.
- **Signature feel:** calm, organized, severity-led, evidence-forward — the visual opposite of an alert-spamming dashboard.

## 13. Verification Experience Design (the trust center — Step 4, S-07/S-07b)

The Verification screen is the trust center; its visual design must make the user feel *"I reviewed this. I approved this. FinSight is using my validated information."* (Trust > AI; FR-026; UX §12).

- **Framing:** clear "Step 4 of 8 — Verify Data" header; a short, reassuring lead ("Here is the information I found — please review before analysis").
- **Extracted values:** presented in clean, tabular, source-aligned tables; readable and unhurried. High-confidence data is calm and unadorned (it is fine).
- **Confidence indicators (FR-016) — never color-only:** low-confidence values carry a **"Needs review" chip (warning icon + label)** and are visually grouped/filterable to the top so attention goes there (NFR-069). High-confidence supports **bulk-approve**.
- **Corrected values (FR-028):** the original value shown struck-through/secondary with the corrected value primary and an **"Edited" badge**; a hover/expand reveals original → corrected, who, when (lineage). Corrections never hide the original.
- **Source traceability (FR-027, NFR-067):** every row has a **"View source"** affordance opening a **source drawer** that shows the file → sheet → row → cell the value came from — one interaction. This visible traceability is a core trust cue.
- **Quarantined rows (FR-024):** shown in a clearly separated, labeled section with reasons — never silently dropped; visually distinct from approved data.
- **Per-document decision:** approve / approve-with-corrections / reject as clear primary/secondary/danger actions; the mandatory **"I have reviewed this information"** confirmation gates **Continue Review** (the primary action is disabled with an explanatory tooltip until confirmed).
- **Review Complete confirmation (S-07b):** on confirm, a **calm, intentional completion panel** — not a flashy celebration — restates what was verified:

  > **✓ Review Complete** — You have verified: ✓ Vendors ✓ Departments ✓ Accounts ✓ Amounts ✓ Dates. *Analysis will now begin on the information you reviewed.* [ Go back to re-verify ] [ Begin Analysis → Step 5 ]

  Visual treatment: success icon + calm success tint, the verified-categories checklist (icon+label, honest to what was actually verified), and two clear actions. It should feel like a meaningful checkpoint passed, in keeping with the premium, composed tone (no confetti, no animation flourish beyond a subtle ≤200ms reveal).

## 14. Leadership Summary Design (Step 7, S-12)

- **Audience-appropriate:** understandable by non-technical leadership; **fully useful with AI disabled** (FR-095). Clean, print/PDF-friendly, section-card layout.
- **RAG status (FR-077):** a prominent status block using the RAG treatment (§5.4) — **icon + word label ("On Track/Needs Attention/At Risk") + color** — never color-only.
- **Sections (fixed structure, F-07-01):** Budget Health · Critical Findings / Key Risks · Recommended Attention Areas · Reconciliation Status · "What Changed" (thin). Each a card; figures are tabular and **drillable to their finding/evidence** (UXP-04).
- **AI-narrative slots (§5.5, NFR-049/080):** rendered in the distinct, labeled "AI-generated" container with provider/model attribution; **empty and unobtrusive until E-09**; the summary reads complete without them.
- **Export (FR-120):** exported summary carries visible labels — period, data-as-of, configuration version, generation timestamp, and identical AI-content labeling; layout is designed to survive as a shared PDF/print artifact.

## 15. Accessibility System

Accessibility is first-class (NFR-024–027; UXP-09; DoD clause 8). The design system bakes it in, not on.

- **Themes:** Light (default), Dark, High Contrast, System-auto (§6) — all AA-validated.
- **Color independence (NFR-025, governing rule):** every status/severity/RAG/state = icon/shape + text label + color; removing color never removes meaning. Validated in a color-blind simulation pass and by rendering the UI grayscale.
- **Contrast (NFR-026):** text and essential UI meet WCAG 2.2 **AA** (≥4.5:1 body, ≥3:1 large text/UI components); primary body text targets AAA where feasible; High Contrast exceeds AA.
- **Text size & zoom (NFR-027):** OS text-size respected; in-app Default/Large/Larger; **200% zoom reflows without breakage**; no fixed-height text containers that clip.
- **Keyboard (NFR-026):** every workflow fully keyboard-operable; visible 2px focus ring with offset (never suppressed); logical focus order follows the step wizard; skip-to-content link; no keyboard traps (modals trap intentionally and release on close).
- **Screen readers:** semantic landmarks and headings; ordered-list stepper with `aria-current`; `aria-live` for processing/analysis progress and toasts; findings and severities announced meaningfully; tables use header associations and `aria-sort`; form errors via `aria-describedby`.
- **Reduced motion (§16):** all non-essential motion honors `prefers-reduced-motion` (transitions become instant).
- **Low training (NFR-068):** consistent components, plain-language labels, contextual help, and the guided wizard reduce the learning curve.

## 16. Motion Guidelines

Motion is **quiet, fast, and purposeful** — never decorative or attention-grabbing (calm/professional goals; anti-pattern avoidance).

- **Durations:** micro-interactions ≤150ms; view/step transitions ≤200–250ms; easing is standard ease-out; no bounce, parallax, glow, or looping animation.
- **Purposeful only:** motion communicates state change (step advance, expand/collapse, drawer open, toast in/out) or draws attention to a *just-changed* result — never idle ambiance.
- **Reduced motion:** with `prefers-reduced-motion`, transitions are instant and any auto-progress indicators become static/determinate. No motion is ever required to understand state (state is always in text/icon too).
- **No "AI" motion tropes:** no typing shimmer, no glowing pulses, no animated gradients.

## 17. Responsive Design Strategy

- **Primary target:** corporate laptops (~1280–1440), then external monitors and smaller laptop widths (NFR-065). MVP is desktop (DEC-003); the system is fluid, not fixed.
- **Breakpoints (guidance):** compact (<1024) → condensed stepper, single-column cards, tables scroll within container; standard (1024–1439) → full stepper, primary content column; wide (≥1440) → more whitespace and optional side rails, never more clutter.
- **Rules:** the **page never scrolls horizontally**; wide tables/diagrams scroll inside their own `overflow` container; content reflows by priority (lead-with-what-matters holds at every width); touch targets ≥44px where touch is possible. Web/multi-user responsive posture is future (NFR-070/071) but the fluid system already anticipates it.

## 18. Empty State Design

Empty states are calm, instructive, and never dead ends (UXP-01/08; UX §23). Each = a quiet illustration-free card with a clear heading, one sentence of guidance, and the single next action.

| Context | Visual treatment |
|---|---|
| No reviews yet (Home) | Welcome heading + "Create your first review" primary action; optional "Import history" secondary |
| New review, no uploads | Document-type slots shown as calm outlined drop-zones with "what this is" captions; "uploading only some is fine" |
| Readiness with a subset | Ready capabilities (success chips) and, for each unavailable, a warning alert naming the missing prerequisite |
| Zero findings | Reassuring success state that **also states what was checked and which capabilities were unavailable** (never a bare "all clear") |
| History/Compare with one review | Informational card explaining a comparison needs a prior review |
| AI not configured | Quiet info note that AI is optional and how to enable it; deterministic experience visibly intact |

## 19. Loading State Design

- **Skeletons** for content areas (tables, cards) — neutral, shimmer-free (or minimal, reduced-motion-safe) — to signal structure without flashiness.
- **Staged, plain-language progress** for processing and analysis (UX §13): the exact user-facing stages (*Reading Files · Extracting Data · Building Review · Preparing Verification*; *Analyzing Review · Budget Analysis · GED Analysis · Finding Exceptions · Preparing Results*) shown as a determinate/stepped indicator with text — never a mysterious spinner alone (NFR-055/062).
- **Non-blocking:** long operations run without freezing the UI (NFR-002/003, F-14-03); deterministic results render as ready, independent of AI (NFR-004). AI-pending areas show a small, labeled "AI generating…" state that can fail gracefully to deterministic-only (NFR-063).
- **Accessibility:** progress is announced via `aria-live`; determinate progress exposes value to assistive tech.

## 20. Visual Trust Mechanisms

How the *look* enforces Trust > AI (realizing UX §21 trust mechanisms visually):

1. **Deterministic-primary, AI-distinct (NFR-049).** Deterministic numbers/findings use full brand/neutral treatment; AI content is confined to the restrained, labeled, attributed "assistant" container (§5.5) — visually secondary in every theme.
2. **Evidence-forward.** Findings and figures visibly expose "View source" / "Explain This" affordances; traceability is a visible, ever-present cue, not a hidden feature.
3. **Verification confirmation.** The Review Complete panel (§13) makes approval a visible, intentional act.
4. **Readiness transparency.** The readiness screen shows available/unavailable + reason as explicit alerts (never silent absence).
5. **Reproducibility & provenance made visible.** Reports and exports show period, data-as-of, and **configuration version** (FR-120); audit surfaces a cycle timeline. The design gives these metadata a consistent, quiet, always-present placement.
6. **Color-independent status.** Every trust-critical state reads without color (NFR-025) — trustworthy for every user.
7. **Calm over urgent.** No red-everywhere alarm aesthetic; severity is precise and proportionate, protecting attention (NFR-066) and trust.

## 21. Design Anti-Patterns To Avoid (binding)

Do **not** introduce: dark-mode-as-default; neon or gradient fills; glow/bloom/shadow-heavy effects; purple "AI" theming or animated-gradient AI panels; typing/shimmer/pulse "AI" motion; cyberpunk/hacker-terminal or crypto-dashboard aesthetics; generic SaaS-template chrome; flashy or experimental layouts; excessive or ambient animation; color-only status/severity; stark all-white screens; dense wall-of-numbers dashboards on entry; more than one primary action competing per view; decorative imagery that adds no information. Each of these violates the emotional goals (§4), an accessibility rule (§15), or the Trust > AI posture (§20).

## 22. Future UI Considerations

- **Amerisure brand finalization** — confirm the exact brand blue, logo lockup, and any secondary brand color; swap token values (system unchanged).
- **Charting/visualization system** — a calm, accessible chart language (color-blind-safe series, tabular tooltips, no chart-junk) for trends/comparison as those capabilities deepen (R2+); deliberately deferred here.
- **Web / multi-user theming** — role-based density and navigation, org-level theme governance (NFR-070/071).
- **Additional accessibility modes** — further color-vision palettes, dyslexia-friendly text option.
- **Localization / RTL** — the token/layout system should accommodate future localization and right-to-left mirroring.
- **Optional refined type family** — if brand calls for it, a licensed humanist sans may replace the system stack, provided it is bundled (no external egress, offline-safe).

---

## 23. Traceability

This design system realizes the UX (07) and the approved quality attributes; it changes no behavior.

| Design area | Realizes / satisfies |
|---|---|
| Light default + Dark + System themes (§6) | NFR-024 (OS display modes); UX §20 |
| Color-independent meaning; severity/RAG/status encoding (§5.3/5.4, §15, §21) | **NFR-025** (binding); FR-070 (severity), FR-077 (RAG) |
| Contrast, keyboard, focus, screen-reader, labels (§10, §15) | NFR-026 |
| Text sizing & 200% zoom (§7, §15) | NFR-027 |
| Responsive strategy (§17) | NFR-065 |
| High Contrast theme (§6, §15) | NFR-024/026 |
| Reduced motion (§16) | NFR-024-adjacent; DoD accessibility |
| AI-content visual distinction, labeling, attribution (§5.5, §14, §20) | **NFR-049**; FR-080; DEC-005/DEC-015 (AI visibly distinct, optional) |
| Confidence, corrected values, source trace, Review Complete (§13) | FR-016, FR-027, FR-028, FR-026; NFR-067; UX §12 |
| Findings Hub severity/hierarchy/evidence (§12) | FR-069/070/071/074/082/102; NFR-066/067; AP-12; UX §14 |
| Leadership summary + export labeling (§14) | FR-076/077/078/079/080/095/120; UX §16 |
| Progress stepper (§11) | UX §5/§7 (8-step wizard); F-01-01 |
| Loading/processing states (§19) | NFR-002/003/004/055/062/063; F-14-03; UX §13 |
| Empty/error states (§18, §10 alerts) | NFR-055/062/064; UX §22/§23 |
| System font, offline-safe, no external egress (§7) | NFR-007, NFR-011, NFR-028 |
| Application shell realization (§8) | C-01 (delivery); UX §6/§7 |

**Coverage & no-conflict statements:**
- Every **critical screen** requested has UI guidance: Home/Recent Reviews (§8, S-01), Create (§11 stepper/S-02), Upload (§10/S-03), Validate (§10 alerts/§18/S-04), Verification (§13/S-07), Review Complete (§13/S-07b), Analysis Progress (§19/S-08), Findings Hub (§12/S-09), Explain This (§12/§20/S-10), Leadership Summary (§14/S-12), Compare (§17/§22/S-14), Settings (§10/§6/S-17), Accessibility Settings (§6/§7/§15/S-17b).
- Every **required design-system element** is defined (§10–§19): buttons, form controls, cards, data tables, status/severity indicators, accordions/expand-collapse, progress stepper, alerts, notifications, empty states, loading states.
- **No workflow, experience, navigation, or lifecycle change** is introduced — this document maps to the UX screens/steps and realizes them visually only (per the binding relationship statement in the header).
- **Concrete values are set in the approved baseline** (brand-swappable via tokens); the design *rules and semantics* trace to firm NFRs/FRs above and weaken no Must.

---

*End of 08-ui-design-system.md — visual language and design system only. It realizes 07-ux-design.md without changing workflows, experiences, navigation, or the review lifecycle. Token values are the approved set (brand-swappable via tokens); the accessibility rules, theme model, AI-distinction, and severity/RAG encoding are firm and trace to approved NFRs/FRs. Reviewed by the design-review board (UI + accessibility: ux-designer, accessibility-engineer) and approved in the current baseline.*
