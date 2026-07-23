# ADR-003 — Exact Decimal Arithmetic & Determinism Strategy

- **Status:** Accepted · **Date:** 2026-07-16 · accepted as part of the project-owner-approved architecture baseline
- **Deciders:** Software Architect (decided); design-review board + QA (consulted) — Constitution §4
- **Feature/plan:** cross-cutting; enables the Walking Skeleton (13); realizes ADC-05

## 1. Status
Accepted as part of the project-owner-approved architecture baseline. Binds the determinism strategy that makes reproducibility (NFR-021) and cross-platform byte-identical results (NFR-029) achievable, and prevents cent-level float errors (NFR-059).

## 2. Context
FinSight's central promise is that **financial truth is deterministic**: the same verified inputs and configuration version yield **identical** findings, statuses, severities, and variances — across repeated runs, across AI providers, and across Windows and macOS (P-7/P-8, NFR-021/029/037/048). The classic silent-variance sources are binary floating point, locale-dependent parsing/sorting, wall-clock reads, and unstable iteration order (06 AR-01). A single visible-total cent error costs disproportionate trust (NFR-059 rationale).

## 3. Decision
- **Money and all financial computation use exact decimal**, never binary float. In the Python core use **`decimal.Decimal`** with a **pinned `decimal.Context`** (fixed precision and a **fixed rounding mode**, e.g. `ROUND_HALF_UP`) established once at the computation boundary; **`float` is forbidden on any computation path** touching amounts, variances, or severities.
- **Storage of amounts (with ADR-004):** amounts are persisted as **integer minor units** (or as exact decimal text), **never as SQLite `REAL`** (float). Parsing converts source values to `Decimal` immediately; the raw source string is preserved for lineage (FR-015).
- **No wall-clock on computation paths:** any needed time is **injected** (a clock passed in), never read from the system clock inside a rule or calculation. (Timestamps for audit are recorded at the edge, not inside computation.)
- **No locale-dependent parsing/sorting:** dates, periods, numbers, and identifiers are parsed with **explicit formats**; string comparison/sorting uses an explicit, locale-independent key. Currency/number formatting is a **presentation** concern, never a computation input.
- **Explicit, total ordering:** any rule that ranks/sorts (e.g., variance contributors) defines an **explicit tie-broken sort key** (e.g., by dimension identity) so ordering is stable; no reliance on set iteration order or hash randomization (set `PYTHONHASHSEED`/avoid hashing-dependent order in outputs).
- **Determinism target (operational reading of NFR-029):** the guarantee is that the **finding set — every finding, severity, variance, and status — is value-identical** across repeated runs, AI providers, and Windows/macOS, and its **serialized form is byte-identical**; byte-identity of intermediate artifacts is not required. To hold this against Excel, the `ExcelReader` (ADR-001) **pins the workbook date system (1900 vs 1904) and text encoding explicitly** and never relies on platform locale for parsing/formatting. *(This interprets NFR-029; it does not change it.)*
- **Versioned, fingerprinted runs:** every analysis records the **rule-set version + configuration version + input fingerprint** (FR-086, NFR-022), enabling exact replay (F-02-06).
- **Determinism is a release gate:** golden-dataset (NFR-036) and provider-swap (NFR-037) suites **must pass to ship** (NFR-048); the both-OS CI matrix (ADR-001) proves NFR-029.

## 4. Alternatives Considered
| Alternative | Why not |
|---|---|
| Binary float (`float`) for money | Introduces cent-level rounding errors and platform variance — violates NFR-059/029. |
| Store amounts as SQLite `REAL` | Float round-trips reintroduce the same errors at the storage boundary. |
| Rely on discipline (no enforced context/rounding) | Rounding drift and locale bugs are exactly the silent-variance class; must be pinned and tested, not trusted. |
| Fixed-point via scaled integers only | Viable (integer minor units) and used for storage, but `Decimal` in-core is clearer for multi-currency-scale and percentages; both are exact. |

## 5. Consequences
**Positive:** reproducible, byte-identical financial results; cent-accurate totals; replayable runs; the provider-swap and cross-platform gates are meetable.
**Negative (accepted):** `Decimal` is slower than `float` (irrelevant at single-department volumes — A-08); developers must route all money through the decimal boundary and avoid `float` (enforced by lint/review); explicit formats/keys add a little code.

## 6. Dependencies
- **ADR-001** (Python core; both-OS CI) · **ADR-004** (integer-minor-units / decimal-text storage, never `REAL`) · **ADR-006** (versioned run on the `VerifiedDataset`) · **ADR-007** (severity computed deterministically).

## 7. Verification Strategy
- **Golden-dataset tests:** a seeded synthetic month → exactly the expected findings/severities/evidence (NFR-036).
- **Determinism test:** repeated runs on the same `VerifiedDataset` + config version produce a value-identical finding set with byte-identical serialized finding output.
- **Cross-platform test:** identical results on Windows and macOS in the CI matrix (NFR-029).
- **Provider-swap regression:** swapping/disabling AI changes no deterministic output (NFR-037).
- **Static checks:** a lint/grep rule flags `float(` and `REAL` on money paths; a review checklist item.

## 8. Traceability
- **Serves:** DEC-005, P-7/P-8. **NFRs:** NFR-021/029/036/037/048/059; NFR-022 (versioning). **Rules:** R-BUD-01 (variance), R-FND-02 (severity), all R-* computation. Realizes **ADC-05**.

## 9. Risks
- **A stray `float` or locale call** silently breaks determinism — mitigated by the lint rule, both-OS CI, and golden tests catching divergence immediately.
- **Rounding-mode ambiguity** across rules — mitigated by a single pinned context established centrally.

## 10. Open Questions (resolved under the approved baseline)
- The exact precision/rounding-mode values are an implementation detail set in this ADR's decision at acceptance (a sensible default: sufficient precision for amounts + percentages, `ROUND_HALF_UP`); finance may confirm a rounding convention — a **configuration/parameter** matter (DEC-019), not a logic change.
