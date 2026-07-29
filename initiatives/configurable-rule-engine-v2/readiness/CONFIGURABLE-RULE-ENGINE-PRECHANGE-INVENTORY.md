# FinSight Configurable Rule Engine — Pre-Change Inventory

- **Recorded:** 2026-07-27
- **Purpose:** Preserve an evidence-based reference to the repository state before the configurable-rule-engine Product Owner stage.
- **Status:** Reference record only — this is not an SDD baseline, approval record, or verification record.
- **Working branch:** `codex/configurable-rule-engine-v2`
- **Source commit at branch creation:** `a298040a8408c04342818a65a186a0d72c87956a`
- **SDD framework checkout:** `spec-driven/` at `9a6b5e39d038b777ab7bffc479b904bed34b4a24`

## Preservation boundary

The configurable-rule-engine work remains within the existing FinSight repository and product. It must evolve the existing specifications and implementation through the governed workflow; it must not create a second product repository, duplicate the full specification set, or create a parallel `finsight_v2` application tree.

V2-specific planning and requirements artifacts are organized under `initiatives/configurable-rule-engine-v2/`. Existing FinSight specifications, architecture records, implementation, tests, and generated artifacts remain in place.

The following existing areas are outside the Product Owner stage's write scope:

- `src/`
- `tests/`
- existing specifications and ADRs
- existing plans, tasks, and readiness authorizations
- generated workbooks and manifests under `outputs/`
- UI-verification artifacts under `artifacts/`
- packaged or generated release artifacts
- the nested `spec-driven/` framework checkout

The pre-existing untracked `artifacts/` and `outputs/` directories were present when the branch was created. They are user/project artifacts and must not be deleted, moved, reformatted, staged, or overwritten by this stage.

## Existing specification alignment

The current specification set already establishes several foundations for the proposed evolution:

- deterministic financial truth and AI-explains-only boundaries;
- configurable rule parameters and governed enable/disable changes;
- configuration and rule-run versioning;
- exact-decimal, reproducible execution;
- extensible rule registration;
- findings with source evidence;
- audit history and historical replay;
- rule-engine outputs consumed by findings and reporting capabilities.

The new Product Owner work must extend these foundations rather than replace them.

## Material governance gaps to resolve

The existing working specifications do not yet fully define:

- user creation and editing of controlled rule definitions;
- the distinction among core mandatory, optional configurable, and informational/advisory rules;
- protected baseline governance for mandatory rules;
- the administrative authorization required to modify, disable, delete, or replace a core rule;
- immutable historical rule versions after replacement;
- default binding of the five core rules to every new validation workspace;
- testing obligations specific to protected core rules;
- rule-effect comparison between validation runs;
- the requirement that every financial validation result and validation-derived consumer use the deterministic rule engine as the single source of truth.

## Confirmed source-reader compatibility gaps

The synthetic source-of-truth manifest and the current implementation show that worksheet-name compatibility does not make the supplied reports readable by the current application:

1. `src/finsight/infrastructure/readers.py` treats GED row 4 as the header and row 5 as the first data row. The supplied real layout uses row 7 for the header and row 8 for the first possible detail row.
2. The current GED reader emits every row after its assumed header. It does not classify and exclude account-total and department-total rows from the transaction population.
3. The current Budget reader maps column B to Budget. The supplied real layout uses column B for Account Name and column C for BGT, followed by ATD, ETC, EAC, DELTA, and Notes in columns D through H.
4. The current worksheet names (`GED` and `Original Budget`) happen to match the synthetic workbooks, but the row and column contracts still do not match.

These are requirements and later application-integration gaps, not reasons to restructure the source workbooks. The V2 requirements must define the supplied real layouts explicitly. Application code remains unchanged until requirements, architecture, and implementation gates authorize a reader correction.

## SDD evidence status

The repository contains working specifications, a stakeholder workbook, plans, tasks, and readiness documents. It does not currently contain `specs/baselines/` or `specs/verification/`.

Therefore:

- this record does not claim that a formal immutable SDD baseline already exists;
- the existing Git commit is a technical preservation reference, not proof of business approval;
- the Product Owner stage may draft new artifacts but must not silently relabel current documents as baselined or verified;
- requirements changes must remain draft until independently reviewed and explicitly approved by a human.

## Product Owner stage write scope

This stage may create only:

- this pre-change inventory;
- a durable product-direction source record;
- a Product Owner product-definition/Implementation Brief;
- an independent requirements-review record for that brief.

The Project Owner's later explicit approval authorizes the initiative's detailed requirements and clarification artifacts after the approved amendments are incorporated. It does not authorize architecture or application-code changes.

Application code, tests, architecture decisions, and existing requirements are not authorized for modification in this stage.
