# ADR-007 — Findings Domain Model

- **Status:** Accepted · **Date:** 2026-07-16 · accepted as part of the project-owner-approved architecture baseline
- **Deciders:** Technical Lead / Software Architect + Project Owner (decided — this ADR establishes the findings/AI boundary, which Constitution §4 assigns to Project Owner + Technical Lead); design-review board (consulted)
- **Feature/plan:** cross-cutting; enables the Walking Skeleton (13); realizes ADC-11

## 1. Status
Accepted as part of the project-owner-approved architecture baseline. Binds the findings contract and the model/experience split so **one findings experience** (P-12, AP-12) and **AI-explains-never-creates** (P-8, DEC-005) are structural, realizing 06 §7.3/§13 and 05 Family 4.

## 2. Context
Every exception FinSight detects must be a **first-class, severity-classified, fully traceable** record produced **only** by deterministic rules (FR-069/070/071, R-FND-01/02). All capabilities (Budget, GED, Reconciliation, later Invoice/Resource) must feed **one** findings experience with **no per-capability forks** (F-06-01). The AI layer may **explain** a finding but **never create, alter, or set the severity of** one (DEC-005, NFR-047). Severity computation and presentation are split (FR-070: computation F-02-04, presentation F-06-01).

## 3. Decision
- **Findings Domain Model (C-09a) lives in the domain core** and owns:
  - the **finding record contract:** unique ID, rule reference (and `R-<FAM>-##`), severity, reporting period, affected entities (account/vendor/document/row), computed **evidence values**, and **source references** (file/sheet/row/cell lineage) — FR-069/071;
  - **severity computation** by rule-defined, configurable criteria via the shared method **R-FND-02** (never AI-assigned; values are configuration — OQ-8/DEC-019); severity carries a **non-color encoding** (icon/shape/label) so meaning survives without color (NFR-025);
  - the **lifecycle state machine:** `New → Acknowledged → In review → Resolved / Dismissed`, dismissal requires a reason, all transitions audited (FR-072); (the skeleton exercises `New` + one transition).
- **Ports (from ADR-002):**
  - **`FindingsCommandPort`** — create/mutate findings, set severity — **wired only to the Rules Engine and rule packs (C-07/C-11)** at the composition root. `Finding` is a **frozen type with no public constructor** (created only via this port) with a **runtime guard**, so a finding cannot be fabricated outside the engine even in Python.
  - **`FindingsQueryPort`** — read-only — the **only** interface the AI layer (C-15) and the findings experience (C-09b) hold. AI therefore **cannot** author or alter a finding — enforced by construction (no `FindingsCommandPort` reference; frozen `Finding` with no public constructor) and a mandatory CI architecture-fitness test, not by the compiler (Python; see ADR-002).
- **Findings Hub Experience (C-09b) lives in delivery/application**, reads via `FindingsQueryPort`, and provides browse/severity presentation; the **"one experience, no per-capability fork"** binding criterion attaches here — every capability's findings render through the same components.
- **Evidence-first:** no finding exists without a rule reference and evidence (P-4/P-5); one-interaction traceability to rule → inputs → source (NFR-067) is a property of the contract, not a UI afterthought.
- **Workspace/finding boundary (04 §2.3, DEC-026):** in-progress items (e.g., reconciliation matching) are workspace tasks, not findings; residual unresolved items become findings at close/escalation. (Not exercised by the skeleton beyond one finding, but the contract must not preclude it.)

## 4. Alternatives Considered
| Alternative | Why not |
|---|---|
| One combined findings component (model + experience) in the core | Puts UI/experience concerns in the core — breaks headless independence (ADR-002/NFR-070); a god-component with multiple hidden decisions. |
| Per-capability findings types/surfaces | Violates One Findings Experience (P-12, F-06-01); divergent statuses become a trust defect. |
| AI writes narration into the finding record | Blurs deterministic/AI (DEC-005/NFR-047); AI holds only the query port — narration is a separate, labeled artifact, not part of the finding. |
| AI-assigned or AI-adjusted severity | Forbidden (P-8); severity is R-FND-02, deterministic, configurable. |

## 5. Consequences
**Positive:** findings are uniform, traceable, and deterministic across all capabilities; the AI boundary is structural; the core stays headless; severity is consistent and color-independent.
**Negative (accepted):** the model/experience split and two ports add structure; severity criteria are configuration that must be present (synthetic default for the skeleton; real values via OQ-8/config).

## 6. Dependencies
- **ADR-002** (ports; command/query segregation) · **ADR-006** (findings produced from a `VerifiedDataset` run) · **ADR-003** (deterministic severity/evidence) · **ADR-005** (finding/lifecycle events audited) · **ADR-004** (findings persisted).

## 7. Verification Strategy
- **Boundary test:** C-15/C-09b reference only `FindingsQueryPort`; `FindingsCommandPort` is reachable only from C-07/C-11 (import test).
- **Contract test:** a finding without a rule reference or evidence cannot be constructed.
- **Severity test:** R-FND-02 maps evidence → Critical/High/Medium/Low deterministically; severity renders with icon/label (color-independent, NFR-025).
- **Traceability test:** from a finding, reach rule + inputs + source in one hop (NFR-067).
- **Golden test:** the skeleton's one rule produces exactly the expected finding + severity + evidence.

## 8. Traceability
- **Serves:** E-06, AP-12, P-8/P-12, DEC-005/026. **FRs:** FR-069/070/071/072; FR-074/082 (experience). **NFRs:** NFR-025/047/066/067. **Rules:** R-FND-01/02, R-BUD-02 (skeleton producer). Realizes **ADC-11**.

## 9. Risks
- **Per-capability fork under delivery pressure** — mitigated by the shared-component binding criterion + review (AR-05 in 06).
- **Evidence/lineage omitted for speed** — mitigated by the contract test (no evidence ⇒ no finding).

## 10. Open Questions (resolved under the approved baseline)
- **OQ-8** severity/materiality **values** (configuration, not logic — DEC-019); the model is complete without them, using synthetic defaults for the skeleton.
- Full lifecycle/triage/recurrence breadth is R1/R2 feature work beyond the skeleton (one finding, minimal state).
