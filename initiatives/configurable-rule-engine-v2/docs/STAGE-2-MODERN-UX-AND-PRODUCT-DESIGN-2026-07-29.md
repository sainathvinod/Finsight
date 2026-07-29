# Stage 2 Modern UX and Product Design

- **Status:** Governed implementation contract; implementation and verification pending
- **Date:** 2026-07-29
- **Visual authority:** Project Owner-supplied approved walking-skeleton screenshots
- **Financial authority:** The selected sealed Stage 1 Validation Run and its recorded projections
- **Product boundary:** One FinSight product, repository, desktop application, and deterministic result path

## 1. Outcome and non-negotiable boundaries

Stage 2 makes monthly financial review easier to scan and investigate. It does
not turn FinSight into a general-purpose BI product and does not change the
meaning of a Stage 1 financial result.

The reference screenshots govern layout, hierarchy, density, and interaction
direction. Their displayed departments, accounts, vendors, transactions,
confidence labels, statuses, amounts, comparisons, and policy language are
synthetic visual examples. They are not seed data and are never copied into a
real review.

All screens obey these invariants:

1. Financial values, control outcomes, severity, reconciliation, and findings
   come from one selected recorded Validation Run.
2. The UI may sort, filter, group, and format recorded values. It does not
   invoke evaluators or independently determine a pass, failure, risk, or
   financial total.
3. Missing or incomplete source support is displayed as `Unavailable` or
   `Incomplete`, with the reason. It is never replaced by a plausible value.
4. Source files, exact row lineage, original/reviewed/current values, immutable
   rule versions, prior runs, and audit history remain reachable.
5. Light, Dark, and System themes remain supported. Meaning uses text and
   icon/shape in addition to color.

## 2. Actual May 2026 capability contract

The approved Stage 1 fixtures are the implementation reference:

| Capability | May 2026 support | Stage 2 presentation |
|---|---|---|
| Reporting period | Supported: May 2026 YTD, with GED fiscal periods `2026-01` through `2026-05` | Show `May 2026` as the review period; show fiscal period per transaction |
| Department | Supported: `00-0245`, source name exactly `Applications Enginee` | Preserve the source text; do not expand it to “Application Engineering” |
| Department mismatch | Supported: intentional GED row 43 uses `00-0999` | Show as unmapped source evidence/finding, not as a second approved department name |
| Budget accounts | Supported: 71 six-digit detail accounts | Account analysis and Budget-versus-Actual rows |
| GED transactions | Supported: 258 transaction rows | Searchable GED table and drill-down |
| Vendors | Supported by GED `Vendor Name`; 23 distinct nonblank names in the approved fixture | Vendor analysis; blank vendor is `No vendor recorded` |
| Budget values | BGT, ATD, ETC, EAC, DELTA | Direct values with source terminology available in details |
| GED financial value | Amount; Invoice Amount when present | Amount drives recorded GED spend; Invoice Amount is evidence, not a substitute |
| Reconciliation | Supported by CORE-05 and recorded canonical projections | Financial Analysis → Reconciliation |
| Prior published review | Not supplied by the approved fixture | Do not show prior-period vendor change; show `Prior review unavailable` where context requires it |
| Confidence | No source field or approved derived policy | Omit confidence filters/badges; do not manufacture `high` or `low` |
| Transaction type | No source field | Omit; do not infer Invoice, Payroll, Credit, or Journal from descriptions |
| Invoice/reference ID | No invoice-number field | Show Journal Number; show Check Number, Invoice Date, and Invoice Amount separately when present |
| Materiality policy | No materiality threshold in the five baseline rules | Do not say “crossed materiality”; show a threshold only for a recorded rule version that actually has one |
| Delayed-posting policy | No approved cutoff rule | Do not create a delayed-posting finding |
| Financial decision requirement | Not a deterministic source field | Show only recorded follow-up/review state; do not claim a decision is required unless a governed rule/result supplies that fact |

The approved fixture contains one missing required GED Amount at row 87. A
complete GED total for its affected account is therefore not asserted. The UI
shows the parseable subtotal only when explicitly labeled `Incomplete — one
Amount is missing`; it never treats the blank as zero.

## 3. Information architecture

The primary review result navigation is exactly:

1. **Overview**
2. **Financial Analysis**
3. **GED Detail**
4. **Findings**
5. **Review Summary**

Financial Analysis uses focused secondary navigation:

- Account Analysis
- Vendor Analysis
- Department Analysis
- Budget vs Actual
- Reconciliation

Supporting technical views remain reachable without competing as permanent
primary tabs:

- Rule Results from Findings and Review Summary;
- Data Quality and field coverage from GED Detail and Review Summary;
- source evidence from any affected row or finding;
- validation-run comparison from Review Summary/history; and
- rule/configuration/audit metadata inside collapsed Technical Details.

The existing guided workflow remains intact. This navigation changes the
results experience, not the source review, confirmation, validation, rule
governance, lifecycle, or publication semantics.

## 4. Shared results shell

Every result page uses the walking-skeleton hierarchy:

1. compact breadcrumb and `Financial Review` title;
2. reporting period, lifecycle/publication status, Ask Fin, and Leadership
   Summary actions;
3. concise review metadata card;
4. five primary result tabs;
5. one focused content region using white cards on a neutral background.

The metadata card shows only recorded values:

- period;
- exact source filenames;
- approved Department Number and exact source Department Name;
- Budget-account and GED-transaction counts;
- distinct recorded vendor count;
- supported capabilities;
- Review Version, Run ID, Rule Set Version, and publication state in an
  accessible details affordance.

Prototype-only copy such as `Leader lens`, invented entity counts, skipped
resource types, and sample vendor/account names is prohibited.

## 5. Overview

### 5.1 KPI row

Use at most six high-value cards:

- Overall Status;
- Budget;
- Actual;
- EAC;
- Variance; and
- Findings Requiring Attention.

`Budget` is recorded BGT. `EAC` is recorded Budget EAC. `Actual` is the
recorded eligible GED spend projection. If any required contributing Amount is
missing, Actual is labeled `Incomplete` and displays a parseable subtotal only
with that qualifier.

The account-level Budget-versus-Actual variance is:

```text
Actual variance = recorded eligible GED spend − BGT
Variance % = Actual variance ÷ BGT
```

These values are supplied by the recorded canonical projection. Positive
Actual variance is unfavorable/over budget; negative is favorable/under
budget. Forecast variance based on EAC is labeled separately. FinSight never
silently re-labels source `DELTA = BGT − EAC` as Actual variance.

### 5.2 Primary account comparison

Show direct Budget and Actual bars by account, followed by exact amount,
variance, percentage, and `Over budget`, `Under budget`, `On budget`, or
`Incomplete` text. Each row opens Account Detail.

Default to the most material and attention-requiring rows, with `View all
accounts`. Do not duplicate the same account comparison in multiple large
charts on the page.

### 5.3 Findings and priority work

Use a compact severity summary and a short priority list. Each priority item
shows severity, business-facing title, affected source entity, short
deterministic explanation, review status, `Explain This`, and `Ask Fin`.
`View all findings` opens the full Findings workflow.

## 6. Financial Analysis

### 6.1 Account Analysis

Columns:

- Account Number and Account Name;
- Department Number;
- BGT;
- recorded GED Actual or explicit incomplete state;
- EAC;
- Actual variance and percentage;
- vendor count;
- GED transaction count; and
- finding count.

Selecting a row opens a detail drawer/page with source Budget values, GED
subtotal/completeness, contributing vendors and transactions, findings, and
source evidence.

### 6.2 Vendor Analysis

Columns:

- Vendor Name;
- current recorded spend;
- accounts;
- GED transactions; and
- findings.

Prior-review spend, change amount, and change percentage appear only when an
authorized prior published review with comparable scope exists and the
comparison is recorded. The current May 2026 fixture alone does not satisfy
that condition.

Selecting a vendor shows related accounts, transactions, findings, Journal
Numbers, available invoice/check fields, and source evidence.

### 6.3 Department Analysis

Columns:

- Department Number and exact source Department Name;
- account count;
- BGT;
- recorded GED Actual or incomplete state;
- EAC;
- variance and percentage; and
- findings.

The May 2026 reference review normally contains one approved department. The
intentional `00-0999` transaction appears as unmapped exception evidence and
must not receive an invented Department Name.

### 6.4 Budget vs Actual

Use one direct-value table plus one compact variance visualization. Columns:

- Account;
- Department;
- BGT;
- Actual;
- ETC;
- EAC;
- Actual variance;
- Actual variance percentage; and
- completeness/reconciliation status.

The source DELTA remains available in account/source details. An account with
incomplete GED input renders Actual and dependent variance as unavailable
rather than zero.

### 6.5 Reconciliation

Show CORE-05 status by Department Number + Account Number with Budget ATD,
summed GED Amount, difference, status, contributing row count, and `Show
Evidence`. `NOT_EVALUATED` is visually prominent and never grouped with pass.

## 7. GED Detail

The primary GED table uses only approved source fields:

- Source Row;
- Department Number and Department Name;
- Account Number and Account Name;
- Fiscal Period;
- Journal Number;
- Journal Date;
- Vendor Name;
- Journal Description;
- Journal Line Description;
- Amount; and
- Findings.

Secondary details expose Invoice Amount, Check Number, Invoice Date, and
Agency. Filters are Vendor, Account, Department, Fiscal Period, minimum and
maximum Amount, and finding status. Confidence and Transaction Type are absent
because the approved source does not contain them.

Selecting a transaction opens complete source-supported fields, related
account/vendor/findings, original and reviewed values, exact workbook,
worksheet, source row/cells, and direct evidence navigation.

## 8. Findings and deterministic Explain This

Findings is the primary exception workflow. Default business-facing titles map
to the five baseline outcomes:

| Rule | Default title |
|---|---|
| CORE-01 | Account over budget |
| CORE-02 | Unmapped GED transaction |
| CORE-03 | Candidate duplicate GED transaction |
| CORE-04 | Missing or invalid required GED value |
| CORE-05 | Budget-to-GED reconciliation mismatch |

Optional rules supply their own approved versioned title templates. Rule IDs
and versions stay under Technical Details.

Each row shows severity, affected entity, what happened, finding-review
status, whether governed follow-up metadata exists, `Explain This`, and `Ask
Fin`. Filters include severity, status, rule, account, vendor, department, and
recorded review-required state.

Finding-review status values are `New`, `Acknowledged`, `In Review`,
`Resolved`, and `Dismissed`. Status changes append an attributable audit event.
They do not change the originating Rule Result or imply that FinSight made a
financial decision.

`Explain This` is deterministic and available without Ollama. It renders:

1. What happened;
2. Why FinSight flagged it;
3. Why it matters, using an approved non-decision template;
4. Supporting evidence;
5. Contributing transactions;
6. A non-binding next-step template; and
7. collapsed Technical Details.

The evidence section includes exact review/run identity, source file,
worksheet, row/cells, Budget/GED values, expected/actual comparison,
variance, rule/version, actual configured threshold when one exists, and
clickable source-record citations.

Contributing transactions use a readable table with Source Row, Vendor,
Journal Number, Description, Date, Amount, workbook, and worksheet. Technical
Details is collapsed by default and contains Rule ID/version, Rule Set
Version, Run ID, formula/comparison definition, evidence identifiers, and
audit metadata.

## 9. Leadership Summary

Leadership Summary is a ledger-derived, printable view containing:

- selected review/run identity;
- Overall Status;
- reporting period;
- Budget, Actual completeness, EAC, and material recorded variances;
- GED/reconciliation status;
- highest-priority findings;
- items recorded as requiring human review;
- deterministic non-binding next steps;
- data-quality limitations; and
- clickable evidence references.

The summary remains complete without Ask Fin. A local model may improve
wording only after all displayed claims have passed the Ask Fin grounding
contract. It cannot add values, causes, decisions, or findings.

## 10. Ask Fin settings presentation

Settings exposes one local Ask Fin profile:

- validated loopback base URL, default `http://127.0.0.1:11434`;
- approved locally installed model name and digest;
- connection/model status;
- Test Local Model action;
- local retention summary; and
- the statement `No cloud fallback or external retrieval`.

The control rejects non-loopback URLs and cloud/remote Ollama model aliases.
It never offers OpenAI, Anthropic, Gemini, Microsoft-hosted inference, public
search, external embeddings, or an arbitrary provider type.

## 11. Visual system

### Light

- page background: cool neutral, approximately `#F4F6F9`;
- cards/panels: `#FFFFFF`;
- primary action/navigation: trust blue, approximately `#15528C`;
- Ask Fin: restrained teal, approximately `#087F83`;
- primary text: deep slate, approximately `#172033`;
- secondary text: blue-gray, approximately `#657086`;
- border: approximately `#D8DEE8`;
- favorable: green; unfavorable: red; warning/incomplete: amber;
- status labels always include text/icon in addition to color.

Use a modern system sans-serif, tabular numerals, 4 px spacing increments,
8–12 px radii, restrained shadows, compact 36–42 px controls, and generous
but not presentation-scale whitespace.

### Dark and System

Dark uses the same hierarchy with deep slate/navy surfaces, lighter panels,
off-white text, visible borders/focus, and adjusted semantic colors meeting
WCAG 2.2 AA. System resolves through the existing appearance service. Theme
changes never recreate or recalculate a financial projection.

## 12. Responsive and accessible behavior

- Target desktop reference: 1440 × 960; supported minimum: 1100 × 720.
- At narrower widths, KPI cards wrap predictably and secondary tabs become an
  accessible overflow control. Financial tables scroll inside their card.
- Every chart has an exact-data table alternative.
- All rows, tabs, filters, drawers, citations, and status controls are keyboard
  operable.
- Focus returns to the invoking row after closing a detail or Explain This
  panel.
- Screen-reader names state value and semantic status, for example:
  `Account 555035, $150,000 over budget, unfavorable`.
- At 200% text scaling, primary identity, status, and actions remain reachable
  without page-level horizontal scrolling.
- Loading, empty, incomplete, and error states are announced and preserve the
  selected review/run context.

## 13. Acceptance mapping

Stage 2 design is acceptable only when:

- the five-result-tab structure is implemented consistently;
- reference-screen hierarchy is recognizable without copying synthetic data;
- actual May 2026 values and incomplete states are rendered honestly;
- no unsupported prior-period, confidence, transaction-type, materiality,
  policy, or department values appear;
- all verified Stage 1 data remains reachable;
- Findings supports deterministic Explain This and source navigation;
- Light and Dark screenshots cover all major workflows;
- keyboard, screen-reader, contrast, zoom, and resizing checks pass; and
- a same-viewport visual comparison confirms the implemented result pages
  follow the approved walking-skeleton direction.
