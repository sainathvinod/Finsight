# Directive Reconciliation

**Prepared:** 2026-07-31  
**Status:** Draft requirements-source record  
**Production behavior changed:** None

## 1. Source inventory

All three supplied files were read completely.

| Source | Lines | SHA-256 | Treatment |
|---|---:|---|---|
| `AI provider configuration...` | 194 | `d2e52c1122f8fd0a460c50d68e2d5385ee3035e1dbcc22857fbb9dbfb4266b08` | Supporting draft only; physically ends after `findings;` |
| `Use this prompt with Codex...` | 265 | `bf4125470a9f14769a419604a7494d13149edb9dc61ae6921c906f2bb8c71735` | Supporting draft only; physically ends after `GED completeness;` |
| `FinSight Production-Readiness Stage...` | 1,073 | `92084ef75720821ef54bd3e05a965aab4ec9eef86696eb57493399e344b8662f` | Complete proposed successor directive and primary source for this delta |

The two shorter sources are useful provenance but are incomplete. They cannot
govern clauses that appear only after their truncation points.

## 2. Source authority has two distinct states

### 2.1 Change-analysis authority

After S1A-D01 is approved, the complete 1,073-line 2026-07-31 directive governs
the drafting and conflict analysis for this proposed successor change. The two
truncated attachments remain supporting provenance only. The constitutions'
non-negotiable decision rights and deterministic/AI boundary still govern the
change process.

### 2.2 Current implementation authority

Until the successor Requirements and Architecture gates pass, existing
approved Requirements and Architecture artifacts remain the only
implementation authority. The current Production-Readiness Stage 01 package
and its open decisions remain effective gate evidence. The new directive is
not yet permission to change production behavior.

After those gates pass, the approved successor requirements and ADRs supersede
the exact affected lower-level clauses without rewriting their history.
Implementation and tests remain evidence, never policy authority.

## 3. Reconciled interpretations that do not require a new business choice

### 3.1 Department-neutral product

FinSight remains usable by any department with an approved compatible Budget
and GED layout. `Application Engineering` in the new source describes the
current synthetic example and intended pilot audience; it does not narrow the
product. This preserves the explicit prior stakeholder direction, FR-133, and
NFR-096.

### 3.2 Budget/GED-only stage

The complete source governs conflicts in the truncated drafts. This stage has
five primary result areas: Overview, Financial Analysis, GED Review, Findings,
and Leadership Summary. It does not add invoice, purchase-order, SOW,
rate-card, resource, deliverable, payment, or approval capabilities. Existing
GED invoice-related columns remain source fields only.

### 3.3 Conditional dimensions

Cost center, workstream, project, and funding category are shown only when an
approved source-layout version contains those fields. The current `SLV-001`
Budget/GED layouts do not contain project, workstream, or funding-category
dimensions, so the June fixtures must not invent them.

### 3.4 Deterministic authority

All financial totals, rule outcomes, findings, severities, comparison
classifications, evidence, and Leadership Summary figures originate from
recorded deterministic processing. Ask Fin explains those records and never
creates, changes, approves, or overrides them.

### 3.5 No packaging

This scope ends at hands-on acceptance readiness. It creates no MSI, EXE, DMG,
installer, or distribution artifact and makes no production-readiness claim.

### 3.6 Lifecycle vocabulary

The accepted lifecycle remains `Draft`, `Data Uploaded`, `Data Reviewed`,
`Validation Complete`, `Reviewed`, `Closed`, and `Archived`. New-source terms
such as `Files Uploaded`, `Data Verified`, `Rules Ready`, `Validated`, and
`Review Complete` are UX concepts mapped onto that model rather than parallel
persistent states. `Deleted` remains a governed disposition/tombstone outcome,
not a reversible lifecycle state.

### 3.7 Duplicate review versus revalidation

Duplicate-review controls apply between distinct ReviewCycle identities. A
governed revalidation inside the same ReviewCycle creates a successor immutable
Review Version and Validation Run and is not a duplicate-review attempt.

## 4. Material conflicts requiring decisions

| Conflict | Current accepted direction | New proposed direction | Required decision |
|---|---|---|---|
| Durable financial rows | Reconstruct normalized rows; do not persist complete normalized/Working/Verified row stores (FR-203, NFR-110, ADR-012) | Persist Budget/GED source data and verified extracted rows in SQLite | S1A-D02 |
| AI providers | First-release Ask Fin is local-only with no non-loopback model traffic (NFR-116) | Add approved Azure/OpenAI-compatible/Anthropic-compatible private endpoints | S1A-D03 and S1A-D04 |
| Optional-rule deletion | Ordinary deletion is logical retirement; Tested versions are immutable (FR-145, §2.11) | Physically delete never-used Draft or Tested optional rules | S1A-D05 |
| Likely duplicate | No approved cross-review similarity policy | Use `substantially identical` and `slightly altered` content | S1A-D06 |
| New financial checks | Only active governed rules may produce findings | June requires missing, delayed, unusual, coding, and comparison cases | S1A-D07 |
| Ask Fin retention | Retention is policy-controlled and S1-D11 is open | Persist full conversations across restart | S1A-D08 plus predecessor S1-D11 |
| Post-validation landing | FR-185 makes Review Summary the landing page | New source separates Overview and Leadership Summary | S1A-D09 |
| Prior-period financial meaning | Current GED source is YTD and no governed recurrence/normalization policy exists | Compare May and June accounts, vendors, findings, completeness, and trends | S1A-D10 |

## 5. Existing open decisions still in force

The 2026-07-31 directive provides useful evidence but does not itself fill the
attributable approval records in S1-D01 through S1-D13. At minimum, permanent
core Rule IDs, CORE-04 scope, backup/restore, retention, supported hardware,
and local-AI topology still require the named authorities.

## 6. SDD classification

This is a breaking, cross-cutting requirements change. It affects financial
data persistence, security boundaries, privacy, architecture, migrations,
audit, rules, test oracles, results UX, and Ask Fin. It therefore reopens the
Requirements gate and, after Requirements approval, requires successor ADRs
and Architecture re-approval.
