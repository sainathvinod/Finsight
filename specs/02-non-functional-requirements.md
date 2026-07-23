# FinSight — Non-Functional Requirements

**Document:** 02-non-functional-requirements.md
**Status:** Approved
**Date:** 2026-07-09
**Scope:** HOW WELL FinSight must behave. Contains no architecture, technology, framework, database, or implementation decisions. Where a quality attribute implies a mechanism (e.g., "encrypted at rest"), the requirement states the property; the mechanism belongs to the architecture phase.
**Companion documents:** 00-project-understanding.md · 01-functional-requirements.md · 09-decision-log.md

**Conventions:** `NFR-nnn` unique IDs · Priority Must/Should/Could. Earlier drafts used lifecycle tags to mark items needing confirmation; all such items are resolved and Approved in the current baseline, and quantitative targets are set under the approved baseline.

---

## 1. Performance

### NFR-001 — Analysis turnaround
- **Classification:** Must · **Status:** Approved
A full monthly cycle (ingest, extract, validate, analyze) for a typical single-department dataset (≤10,000 GED lines plus tracker/budget files) completes in ≤ 2 minutes on target hardware (8–16 GB corporate laptop). Target set under the approved baseline.

### NFR-002 — Interactive responsiveness
- **Classification:** Must · **Status:** Approved
User-facing interactions (navigation, filtering, opening findings) respond within 200 ms perceived; operations longer than 1 second show progress indication.

### NFR-003 — Long operations never block
- **Classification:** Must · **Status:** Approved
Ingestion, extraction, analysis, report generation, and AI calls run asynchronously; the UI remains responsive and the user can continue viewing other data while they run. *(Team NFR: asynchronous processes.)*

### NFR-004 — AI latency independence
- **Classification:** Must · **Status:** Approved
Slow or unavailable AI providers must not delay deterministic results; deterministic output is displayed as soon as it is ready, with AI narrative arriving (or failing) independently.

## 2. Reliability

### NFR-005 — No data loss on failure
- **Classification:** Must · **Status:** Approved
An application crash or forced shutdown never loses verified data, findings, audit records, or completed work; on restart the review cycle resumes from its last consistent state.

### NFR-006 — Resumable cycles
- **Classification:** Must · **Status:** Approved
A review cycle may be paused and resumed across application restarts and days without rework.

### NFR-007 — Graceful degradation without connectivity
- **Classification:** Must · **Status:** Approved
All deterministic functionality works fully offline. AI features degrade gracefully with clear status ("provider unavailable"), never blocking the monthly process. *(Supports variable connectivity — DEC-016.)*

### NFR-008 — Idempotent re-analysis
- **Classification:** Must · **Status:** Approved
Re-running analysis on the same verified inputs and configuration produces the same results without duplicating findings, reports, or audit anomalies.

## 3. Security

### NFR-009 — Protection of data at rest
- **Classification:** Must · **Status:** Approved
All financial data, findings, reports, and audit records stored by the application are protected against casual access outside the application (encryption at rest or equivalent OS-level protection; mechanism decided in architecture).

### NFR-010 — Protection of secrets
- **Classification:** Must · **Status:** Approved
Provider credentials/API keys are stored using platform-appropriate secure storage, never in plain text files or logs.

### NFR-011 — No unconsented egress
- **Classification:** Must · **Status:** Approved
The application transmits data externally only to the user-selected AI provider under an active consent (FR-096), and nowhere else. No telemetry, analytics, or update mechanism may carry user data without explicit separate consent.

### NFR-012 — Malicious/malformed input safety
- **Classification:** Must · **Status:** Approved
Ingested files are treated as untrusted input: malformed or hostile file content must not crash the application, execute code, or corrupt stored data.

### NFR-013 — Administrator-managed provider registry
- **Classification:** Must · **Status:** Approved
The organization-recommended provider list is managed through administrator-controlled configuration, auditable, and changeable without code changes (DEC-006/007).

## 4. Privacy

### NFR-014 — Informed consent quality
- **Classification:** Must · **Status:** Approved
Consent prompts state in plain language: the provider, the categories of data to be sent, whether masking is active, and the implications — understandable by a non-technical user. Consent is never bundled, defaulted-on, or buried.

### NFR-015 — Data minimization
- **Classification:** Must · **Status:** Approved
When data is sent to an AI provider, only the fields required for the specific operation are transmitted — never whole files or unfiltered datasets.

### NFR-016 — Masking effectiveness
- **Classification:** Should · **Status:** Approved
When masking is enabled, sensitive identifiers (vendor names, resource names, invoice numbers, amounts per configuration) are irreversibly absent from transmitted content; the token map never leaves the application.

### NFR-017 — Local data disposal
- **Classification:** Should · **Status:** Approved
The user can permanently delete stored data (a cycle, a period, or all data) with confirmation; deletion itself is audit-logged (record that deletion occurred, not the deleted content). *Justification: confidential data on a laptop needs an end-of-life story — offboarding, machine handover, or customer request.*

### NFR-018 — Development data hygiene
- **Classification:** Must · **Status:** Approved
No real customer data is used in development or testing; all fixtures and test datasets are sanitized, scrambled, or synthetic (DEC decision; also NFR-063).

## 5. Auditability

### NFR-019 — Complete attributable trail
- **Classification:** Must · **Status:** Approved
Every material action (ingestion, verification, correction, analysis, configuration change, consent, AI interaction, report, export) is logged with user identity, timestamp, and enough detail to reconstruct the review after the fact (FR-084–FR-090).

### NFR-020 — Tamper-evidence
- **Classification:** Should · **Status:** Approved
Audit records are protected such that alteration or deletion is detectable. *Justification: an audit trail that can be silently edited is not an audit trail.*

### NFR-021 — Reproducibility guarantee
- **Classification:** Must · **Status:** Approved
Given the same verified inputs and configuration version, FinSight reproduces identical findings, statuses, severities, variances, and rule outcomes — regardless of AI provider, model, prompt, or agent configuration. Only narrative wording and presentation may vary (DEC-005). This is a testable release criterion (NFR-048).

### NFR-022 — Versioned rule and configuration provenance
- **Classification:** Must · **Status:** Approved
Every analysis records the rule set version and configuration version in force; both are versioned artifacts whose history is retained (FR-107).

### NFR-023 — AI provenance
- **Classification:** Must · **Status:** Approved
Every AI-generated artifact records provider, model, and version, retrievable for any historical output.

## 6. Accessibility

### NFR-024 — OS display mode support
- **Classification:** Must · **Status:** Approved
Follows native OS light/dark mode; offers theme selection including color-vision-deficiency-safe palettes. *(Team NFR.)*

### NFR-025 — Color-independent meaning
- **Classification:** Must · **Status:** Approved
No information — especially severity and RAG status — is conveyed by color alone; icons, text, or patterns always accompany color.

### NFR-026 — Keyboard and assistive access
- **Classification:** Should · **Status:** Approved
Primary workflows are fully keyboard-navigable; controls carry accessible labels; contrast meets recognized accessibility guidance (e.g., WCAG AA-level contrast).

### NFR-027 — Text scaling
- **Classification:** Should · **Status:** Approved
Respects OS text-size settings without layout breakage.

## 7. Cross-Platform Support

### NFR-028 — Windows and macOS parity
- **Classification:** Must · **Status:** Approved
Full functional parity and a seamless, native-feeling experience on current enterprise versions of Windows and macOS. *(Team NFR.)*

### NFR-029 — Identical results across platforms
- **Classification:** Must · **Status:** Approved
The same inputs and configuration produce byte-identical deterministic results on both platforms. *Justification: platform-dependent floating-point or locale differences (date/number parsing) are classic silent variance bugs in financial software.*

### NFR-030 — Restricted-environment compatibility
- **Classification:** Must · **Status:** Approved
Installs and runs within locked-down corporate environments (no admin-rights assumptions beyond standard enterprise software installation; proxy-friendly network behavior).

## 8. Maintainability

### NFR-031 — Composable, fungible modules
- **Classification:** Must · **Status:** Approved
The system is built as composable modules with well-defined interfaces, replaceable independently (team NFR: composable/fungible code and architecture — realized concretely in the architecture phase).

### NFR-032 — No shortcuts principle
- **Classification:** Must · **Status:** Approved
Modern, disciplined engineering practice throughout; no expedient hacks that compromise the deterministic core, auditability, or the future web transition. *(Team NFR.)*

### NFR-033 — Requirement-traceable implementation
- **Classification:** Should · **Status:** Approved
Code modules and tests are traceable to the FR/NFR IDs they implement, enabling impact analysis when requirements change. *Justification: spec-driven development (DEC-010) only works if the spec→code link is navigable in both directions.*

### NFR-034 — Documented behavior
- **Classification:** Should · **Status:** Approved
Rules, configuration parameters, and user-facing behaviors are documented and kept current with each release.

## 9. Testability

### NFR-035 — Unit testing built along the way
- **Classification:** Must · **Status:** Approved
Unit tests are written with the code, not after; untested code is not done. *(Team NFR.)*

### NFR-036 — Deterministic core fully verifiable
- **Classification:** Must · **Status:** Approved
Every rule is testable in isolation with defined inputs/expected outputs; golden-dataset tests verify end-to-end determinism (same input files → same findings).

### NFR-037 — Provider-swap regression test
- **Classification:** Must · **Status:** Approved
A standing test verifies NFR-021: swapping/disabling the AI provider changes no deterministic output. *Justification: this is the project's central promise; it must be continuously proven, not asserted.*

### NFR-038 — Synthetic test fixtures
- **Classification:** Must · **Status:** Approved
Test datasets replicate real structural quirks (subtotal rows, reclasses, accruals, credits, placeholder values) without real data (NFR-018).

## 10. Configurability

### NFR-039 — Parameterized operation
- **Classification:** Must · **Status:** Approved
AI provider, storage location, thresholds, tolerances, fiscal calendar, reference data, and comparable operational choices are configurable without code changes. *(Team NFR: "configure LLM, database, and anything the application needs.")*

### NFR-040 — Safe configuration handling
- **Classification:** Must · **Status:** Approved
Invalid configuration is rejected with clear messages and cannot render the application unusable; a known-good state is always recoverable.

### NFR-041 — Configuration transparency
- **Classification:** Should · **Status:** Approved
The user can view the active configuration (thresholds, provider, masking state) at any time; analyses display the configuration version they used.

## 11. Scalability

### NFR-042 — Data growth headroom
- **Classification:** Should · **Status:** Approved
Performance targets hold with 3+ years of monthly history retained locally; degradation with growth is gradual, not cliff-edged.

### NFR-043 — Dimensional headroom
- **Classification:** Should · **Status:** Approved
Data structures do not preclude multiple departments, additional analysis dimensions (project/workstream if data appears — OQ-4), or multi-user operation in the future web deployment; MVP behavior remains single-department, single-user.

## 12. Extensibility

### NFR-044 — New rules without core change
- **Classification:** Must · **Status:** Approved
New deterministic rules can be added to the catalog without modifying unrelated modules; rules declare their inputs, parameters, outputs, and minimum-history needs (FR-111).

### NFR-045 — New document types
- **Classification:** Should · **Status:** Approved
Adding a new ingestible document type (new extraction template + rules) is an extension, not a redesign.

### NFR-046 — New AI providers
- **Classification:** Must · **Status:** Approved
Adding an AI provider is a configuration/extension activity requiring no change to deterministic components. *(Team NFR: switchable LLMs.)*

## 13. AI Governance

### NFR-047 — Deterministic/AI boundary enforcement
- **Classification:** Must · **Status:** Approved
The boundary defined in DEC-005 (AI never selects rules, alters outcomes, or computes financial values) is enforced by design and verifiable — not a convention that discipline alone maintains.

### NFR-048 — Determinism as release criterion
- **Classification:** Must · **Status:** Approved
No release ships unless the provider-swap regression (NFR-037) and golden-dataset determinism tests (NFR-036) pass.

### NFR-049 — Visible AI distinction
- **Classification:** Must · **Status:** Approved
AI-generated content is distinguishable at a glance — distinct visual treatment, labeling, and provider/model attribution — in the application and in all exports (FR-080, FR-120). *(Team NFR.)*

### NFR-050 — Grounded-output policy
- **Classification:** Must · **Status:** Approved
AI outputs are constrained to verified data and rule outputs (FR-094); unanswerable questions are declined, and AI answers carry citations (FR-099) so every claim is checkable.

### NFR-051 — Model change management
- **Classification:** Should · **Status:** Approved
Provider/model changes are recorded events; after a model change, a standard validation set of representative narratives/Q&A is reviewed before relying on the new model. *Justification: model updates silently change tone and quality; governance requires noticing.*

### NFR-052 — Prompt/response retention with privacy balance
- **Classification:** Should · **Status:** Approved
AI prompts and responses are retained for audit (FR-087) under the same at-rest protection as financial data (NFR-009).

## 14. Observability

### NFR-053 — Operational logging separate from audit
- **Classification:** Should · **Status:** Approved
Technical/diagnostic logs are distinct from the governance audit trail; diagnostic logs never contain sensitive financial values.

### NFR-054 — Self-diagnosis
- **Classification:** Should · **Status:** Approved
The application can report its own health: storage state, configuration validity, provider reachability, last successful cycle — enabling users to troubleshoot without support.

### NFR-055 — Actionable error surfaces
- **Classification:** Must · **Status:** Approved
Errors visible to users state what failed, the impact, and the next step — never raw technical traces.

## 15. Data Integrity

### NFR-056 — Source immutability
- **Classification:** Must · **Status:** Approved
Ingested source content is preserved unmodified (FR-003, FR-015); verified data, corrections, and findings are additive layers over it — original evidence is never destroyed.

### NFR-057 — Transactional consistency
- **Classification:** Must · **Status:** Approved
Multi-step persistence (e.g., completing verification, finishing an analysis) is all-or-nothing; interrupted operations never leave partially written, inconsistent state (pairs with NFR-005).

### NFR-058 — Content fingerprinting
- **Classification:** Should · **Status:** Approved
Ingested files and verified datasets carry content fingerprints used in audit records (FR-086) so "the same input" is provable, not assumed.

### NFR-059 — Financial arithmetic precision
- **Classification:** Must · **Status:** Approved
All monetary computation uses exact decimal arithmetic; binary floating-point must never introduce cent-level errors into findings or totals. *Justification: a leadership report that is one cent off in a visible total costs disproportionate trust; this is the cheapest trust insurance available.*

## 16. Disaster Recovery

### NFR-060 — User-initiated backup and restore
- **Classification:** Should · **Status:** Approved
The user can back up all application data (cycles, findings, reports, audit, configuration) to a file/location of their choosing and restore it on the same or a replacement machine. *Justification: single-machine deployment means a lost laptop is total data loss — including audit history — unless backup exists.*

### NFR-061 — Storage failure containment
- **Classification:** Should · **Status:** Approved
Storage corruption is detected and reported clearly; recovery guidance is provided; partial corruption does not silently produce wrong results.

## 17. Error Handling

### NFR-062 — No silent failure
- **Classification:** Must · **Status:** Approved
Every failed operation is visible to the user and recorded; the system never presents partial results as complete (quarantine reporting per FR-024/FR-025).

### NFR-063 — Safe failure of AI features
- **Classification:** Must · **Status:** Approved
AI errors (provider down, refusal, malformed output) degrade to deterministic-only presentation with clear status — never blocking, never substituting fabricated content.

### NFR-064 — Input error recovery
- **Classification:** Must · **Status:** Approved
File and data errors guide the user to resolution (replace file, correct row, adjust template) without restarting the cycle.

## 18. User Experience

### NFR-065 — Responsive layout
- **Classification:** Must · **Status:** Approved
The UI adapts across window sizes and screen resolutions typical of corporate laptops and external monitors. *(Team NFR.)*

### NFR-066 — Progressive disclosure by severity
- **Classification:** Should · **Status:** Approved
Default views lead with what matters (RAG status, Critical/High findings), with detail available on demand — leadership attention is the scarcest resource the product serves. *Justification: alert fatigue is a named failure mode; the antidote is prioritized presentation.*

### NFR-067 — Explainability in one click
- **Classification:** Must · **Status:** Approved
From any displayed number or finding, the user can reach its explanation — rule, inputs, source rows — within one interaction (FR-071). Trust is a UX requirement, not only an engineering one.

### NFR-068 — Workflow efficiency vs. manual baseline
- **Classification:** Should · **Status:** Approved
A complete monthly cycle (ingest through report), excluding decision time, takes materially less user effort than the current manual process — target ≤ 50% of current effort, measured with pilot users. *Justification: if FinSight is slower than paste-and-clear, adoption dies regardless of quality.*

### NFR-069 — Low-friction verification
- **Classification:** Should · **Status:** Approved
The mandatory verification gate (FR-026) is optimized for speed: bulk approval of high-confidence data, attention directed only to exceptions and low-confidence items.

## 19. Future Web Migration

### NFR-070 — Core independence from desktop delivery
- **Classification:** Must · **Status:** Approved
Business logic, rules, findings, and audit capabilities contain no desktop-only assumptions; transitioning to a web-hosted deployment must not require reimplementing deterministic logic. *(Team NFR; mechanism is an architecture-phase concern.)*

### NFR-071 — Multi-user readiness in data design
- **Classification:** Should · **Status:** Approved
Records attribute actions to a user identity (FR-084) in a way that generalizes from "local OS user" to authenticated multi-user identities later (DEC-008).

### NFR-072 — Storage substitutability
- **Classification:** Must · **Status:** Approved
Persistence is replaceable (local file-based now, server database later) without changes to business logic — stated here as a quality attribute; realized via the architecture phase. *(Team NFR.)*

## 20. Development Methodology

### NFR-073 — Spec-driven development
- **Classification:** Must · **Status:** Approved
Structured specification documents (this document set) are the source of truth; implementation follows approved specs; spec changes precede code changes. *(Team NFR / DEC-010.)*

### NFR-074 — Agent-assisted implementation with human accountability
- **Classification:** Must · **Status:** Approved
Coding agents built by the team may generate implementation from approved specs; every generated artifact is human-reviewed before acceptance; humans remain accountable for all code. *(Team NFR / DEC-010.)*

### NFR-075 — Quality gates apply to all code
- **Classification:** Must · **Status:** Approved
AI-generated code passes the same review, testing, and traceability gates as human-written code — no exceptions (DEC-010).

### NFR-076 — Verifiable financial logic
- **Classification:** Must · **Status:** Approved
Deterministic financial logic is independently verifiable by a human reviewer against the Rules Catalog — readable, explicit, and free of hidden behavior.

## 21. Code Quality

### NFR-077 — Consistent standards
- **Classification:** Must · **Status:** Approved
A defined code standard (style, structure, naming, error handling) applies across the codebase and is enforced automatically where possible.

### NFR-078 — Static analysis
- **Classification:** Should · **Status:** Approved
Automated static analysis runs continuously; findings are triaged, not ignored. *Justification: with agent-generated code at volume, automated review is the only review that scales alongside human review.*

### NFR-079 — Dependency hygiene
- **Classification:** Should · **Status:** Approved
Third-party components are inventoried, license-checked, and kept current; known-vulnerable versions are not shipped. *Justification: enterprise customers audit supply chains; an intern-built tool must not fail on a scanner finding.*

### NFR-080 — Reviewability of changes
- **Classification:** Must · **Status:** Approved
Changes are small, purposeful, and reviewable; no unreviewable bulk-generated changesets enter the main line (supports NFR-074).

---

## 22. Team-NFR traceability

| Team NFR (as stated) | Covered by |
|---|---|
| No data to cloud/LLM without user consent | NFR-011, NFR-014, FR-096–FR-098 |
| Modern desktop architecture, no shortcuts | NFR-031, NFR-032 |
| Unit testing along the way | NFR-035–NFR-038 |
| Composable, fungible code and architecture | NFR-031, NFR-044–NFR-046 |
| Agents, memory, skills, code loop, sub-agents | NFR-047 (runtime boundary); NFR-073–NFR-075 (methodology); detail in 07-ai-and-agents.md |
| AI-native development principles | NFR-073–NFR-076 |
| Developers build agents that build the application | NFR-074, NFR-075 |
| Deterministic + AI outputs visually distinct | NFR-049, FR-080, FR-101/FR-120 |
| Configure LLM, database, anything — parameterized | NFR-039–NFR-041, NFR-046, NFR-072 |
| Native OS display modes, color-blind support | NFR-024–NFR-025 |
| Responsive across screen sizes | NFR-065 |
| Asynchronous, non-frozen screens | NFR-002–NFR-004 |
| Windows + macOS seamless | NFR-028–NFR-030 |
| Convertible to web application | NFR-070–NFR-072 |
| No database initially; data-access abstraction for later switch | NFR-072 (property stated here; design in architecture phase) |
