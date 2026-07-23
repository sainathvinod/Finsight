# FinSight — Project Understanding

**Document purpose:** Demonstrate complete, shared understanding of the FinSight project — its objectives, business goals, users, workflows, scope, assumptions, constraints, and success criteria — before any architecture, design, or implementation decisions are made.

**Explicitly excluded from this document:** architecture, technology stacks, frameworks, databases, deployment models, agent frameworks, and implementation approaches.

**Sources:** "AI-enabled financial review assistant — High Level Requirements" (PDF), "AI Agent Specification: Budget, GED, and Invoice Review Assistant" (PDF), sample GED report (`ged_dept_ytd_00-0245`), sample Budget Tracker workbook, and clarification sessions with the project team (July 2026).

---

## 1. What FinSight Is

FinSight is an AI-enabled **financial review and governance assistant** built by HCLTech for its customer **Amerisure**, serving Application Engineering leadership and the staff who support the monthly financial review process.

It is a **read-only analytical tool**, not a transactional system. Each month, it takes in the financial artifacts that today are reviewed manually — budget files, General Expense Detail (GED) reports, invoices, purchase orders, statements of work, rate cards, and resource/contract information — extracts and organizes their contents, checks them against defined business rules, surfaces exceptions and variances, and produces leadership-ready summaries. Users can also ask natural-language questions about their financial position.

Two principles define its character:

1. **Financial truth is deterministic.** Every finding, variance, status, and severity comes from repeatable, auditable business rules. Given the same inputs, FinSight always produces the same findings.
2. **AI explains; it never decides.** AI capabilities summarize, narrate, prioritize, and answer questions about rule-engine outputs. AI never computes a financial value, generates a finding without rule evidence, or takes financial action. AI-derived content is always visually and experientially distinct from deterministic results.

FinSight recommends; humans decide. It never approves, rejects, pays, posts, or modifies anything in any financial system.

## 2. Why It Is Being Built

Amerisure's Application Engineering monthly financial review is currently a manual, fragmented process spread across spreadsheets, PDFs, emails, and human memory. The team's own working files show the reality: a GED extract is pasted into a tracking workbook and reconciled line-by-line by hand against an invoice tracker, with a "cleared" column marking progress. Budget-versus-actual comparison, GED completeness checking, and invoice validation each require cross-referencing multiple documents with no system support.

This costs significant skilled effort every month, and — more importantly — it creates governance risk: overages found late, duplicate or missing entries unnoticed, invoice errors slipping through, approvals delayed, and no single monthly view for leadership.

FinSight is being built to convert that manual process into a consistent, fast, auditable monthly governance layer — reducing effort while improving visibility, exception detection, and audit readiness.

## 3. Business Problems It Solves

| Current problem | Risk today | FinSight response |
|---|---|---|
| Manual budget-vs-actual comparison | Overages missed or found late | Automated variance detection with leadership interpretation |
| GED entries tracked separately, reconciled by hand | Missing, duplicate, late, or miscoded entries go unnoticed | Automated completeness, duplicate, timing, and anomaly checks |
| Invoice review across many documents | Wrong rates, hours, dates, codes slip through | Rule-based matching of invoices against POs, SOWs, rate cards, estimates, deliverables |
| Delayed approvals | Vendor payment delays; leadership lacks clarity | Clear per-invoice status recommendations with reasons |
| No single monthly summary | Leadership sees trends too late | One leadership-ready monthly summary with status, exceptions, risks, actions |
| Inconsistent tracking | Weak audit readiness | Complete audit trail of what was reviewed, found, and reported |
| No visibility into resource/contract cost structure | Budget impact of staffing changes unclear | Resource loading and contract-mapping visibility tying people, contracts, vendors, and accounts to budget |

## 4. Who the Users Are

**Primary user (MVP):** Application Engineering leadership — the budget owner who needs monthly answers: Are we over or under budget? Which vendors and accounts are causing pressure? Is the GED complete and clean? Which invoices need my attention? What are this month's risks and decisions?

**Operational user:** the person who performs the monthly reconciliation today (analyst / PM / leader's delegate) — the one who currently pastes GED extracts into the tracker and clears lines by hand. FinSight automates and assists their workflow: ingesting files, verifying extraction, reviewing exceptions before the leadership summary is produced. *(Whether this is a distinct persona or the same individual as the leader varies; treated as an open question — see §11.)*

**Future users (post-MVP, especially web deployment):** project managers (project-level spend and exceptions), finance partners (full review detail), vendor managers (vendor-specific invoice issues), executives (aggregated portfolio view) — each with role-appropriate visibility.

The MVP is a **single-user** tool on an individual's desktop; the user's identity is recorded in all audit history.

## 5. Workflows It Supports

### 5.1 Monthly review cycle (core workflow)

1. **Ingest** — the user provides the month's files (Excel and/or PDF): budget, GED report, invoice tracker; later invoices, POs, SOWs, rate cards, resource/contract files.
2. **Extract & enrich** — FinSight classifies each document, extracts structured fields, and segments the data.
3. **User verification** — the user reviews and confirms (or corrects) the extracted data before any analysis runs. Nothing proceeds on unverified extraction.
4. **Deterministic validation** — business rules compare data across documents: budget vs. actuals, GED patterns, invoice-to-reference matching.
5. **Findings** — exceptions, variances, duplicates, missing items, and risks are produced with severity classification (Critical / High / Medium / Low), each traceable to the rule and data that produced it.
6. **Summarize & interact** — FinSight produces the monthly leadership summary (budget health, GED status, invoice exceptions, risks requiring decision, recommended actions; overall Green/Yellow/Red). The user may ask natural-language questions ("Which vendors are trending over budget?", "What changed from last month?").
7. **Human decision** — the user acts outside FinSight (approve invoices, contact vendors, escalate). FinSight records what it reported; it takes no action.

### 5.2 Capability areas

**Budget Review** — planned vs. actual by department, GL account, and vendor; overages, underspend, month-over-month anomalies, year-to-date variance, run-rate/forecast risk. Output is interpretation, not just numbers: what changed, why it matters, what decision is needed.

**GED Analysis & Reconciliation** — completeness (expected entries present), duplicates, delayed postings, unusual amounts vs. historical pattern, wrong coding, unexpected vendors; plus automation of today's manual GED-to-tracker reconciliation ("cleared" matching).

**Invoice Review** *(samples resolved under the approved baseline)* — match invoices against POs, SOWs, rate cards, approved estimates, staffing, deliverables; detect rate/hours/date/resource/code/category mismatches and duplicates; classify each invoice: Ready for approval / Needs clarification / Hold for review / Recommend rejection / Partial approval candidate. Always a recommendation, never an action.

**Resource & Contract Visibility** — resource loading (who, type, vendor, contract reference, department, account, rates, allocation, period, active/inactive status) and a contract-mappings view showing the relationships among resources, contracts/SOWs, vendors, departments, accounts, and budget allocations. The data model supports "what is the budget impact if a resource leaves?" from day one; the interactive analysis arrives later.

**Natural-language Q&A** — questions over the current month's verified data and findings, answered from rule-engine outputs.

## 6. Data Sources

All ingestion is **read-only**, from files the user provides (Excel and PDF expected; other structured formats considered).

| Source | Status | What we know |
|---|---|---|
| **GED report** | Sample in hand | GL journal-line detail per department: dept #/name, account #/name (~31 GL accounts), fiscal period, journal #/date, invoice amount, check #, invoice date, vendor, agency, descriptions, amount; account-level subtotal rows. |
| **Budget tracker workbook** | Sample in hand | Three parts: invoice-level Details (account, vendor, description, date, invoice #, status, owner, approver), Actuals (GED extract plus manual "cleared"/comment reconciliation columns), Original Budget per account (budget, actuals-to-date, estimate-to-complete, estimate-at-completion, delta). |
| **Invoices, POs, SOWs, rate cards, contracts** | One real invoice sample (DEC-018) | Formats assumed (PDF/Excel); related requirements approved under the current baseline. |
| **Resource loading sheet** | To be designed | No existing file; schema designed by the team for extensibility (see §5.2). |
| **Approved estimates, deliverable reports, allocation files** | Mentioned in source spec | Existence and format unconfirmed. |

Real production data is confidential. All build and test activity uses **sanitized, scrambled, or synthetic data only**.

## 7. Key Constraints

1. **Read-only MVP.** FinSight must not approve/reject invoices, update budgets, modify financial systems, change GED records, create payment instructions, or send vendor communications. Human approval is always required.
2. **Deterministic financial truth.** All findings, statuses, severities, variances, and computed values must be reproducible and auditable, and must be identical given the same inputs regardless of which AI provider/model/prompt is configured (only wording and presentation may vary). The product must remain fully functional with AI features disabled.
3. **AI output distinction.** Probabilistic/AI-generated content must be clearly distinguishable from deterministic results in the user experience.
4. **Data privacy and consent.** No data leaves the application to any AI provider without explicit, informed, logged user consent — the final authorization gate. The user must be shown which provider is used, what data would be transmitted, and the implications, before consenting; consent is revocable. Organization-approved provider lists may be preconfigured as recommendations. *(Governance note: the original Amerisure spec framed this as hard enforcement — "never send confidential data to a public model." The consent-based model is a team decision that must be validated with Amerisure security before production; see §11.)*
5. **Confidentiality in delivery.** Sensitive customer data must never be used during development; sanitized/synthetic data only.
6. **Auditability.** FinSight must record what data was accessed, what was extracted, what rules ran, what findings and outputs were generated, what was sent to any AI provider and under what consent, which model/version was used, and when — attributable to the user.
7. **Desktop delivery first.** MVP runs on individual users' machines (Windows and macOS, standard corporate laptops, 8–16 GB RAM, restricted environments, variable connectivity), with a possible future transition to a web application. *(How this is achieved is an architecture-phase decision.)*
8. **Configurability.** AI provider and other operational choices must be user/admin configurable rather than hard-coded. *(Mechanism is an architecture-phase decision.)*

## 8. Key Assumptions

1. **GED** stands for **General Expense Detail** — the actuals report reconciled against planned budget (confirmed by team; official Amerisure confirmation still worthwhile).
2. MVP analysis dimensions are **department + GL account + vendor**. Project/workstream/funding-category dimensions from the source spec do not exist in the actual data and are out of MVP scope unless mapping files surface.
3. The monthly cadence is the governing rhythm: one reporting month at a time, with history retained for trend and month-over-month analysis.
4. Sanitized invoice/PO/SOW/rate-card samples will eventually be provided; until then those requirements are assumptions, not validated facts.
5. Users will tolerate (and want) a verification checkpoint between extraction and analysis — accuracy is valued over one-click automation.
6. An Amerisure-approved enterprise AI endpoint is expected to exist and be the primary AI path for production use (resolved under the approved baseline).
7. The MVP is single-user; multi-user, role-based visibility becomes relevant with a future shared/web deployment.
8. Historical months' data (e.g., three-month averages) will be available inside the tool over time to support pattern-based checks; first months of operation will have limited baselines.

## 9. MVP Scope (phased)

**Phase 1 — foundation, where real data exists:** budget review (planned vs. actual, variances, trends), GED analysis (missing/duplicate/delayed/unusual/miscoded entries), GED-to-tracker reconciliation, the deterministic rules engine, findings with severity, audit logging, findings/report history, monthly leadership summary, extraction with user verification.

**Phase 2 — resource & contract visibility:** resource loading schema and ingestion, contract mappings view, resource cost visibility, budget-to-resource analysis.

**Phase 3 — invoice review (samples resolved under the approved baseline):** invoice ingestion and extraction; PO, SOW, rate card, estimate matching; per-invoice status recommendations; invoice exception reporting.

**Phase 4 — advanced analysis:** what-if analysis (including resource-departure budget impact and backfill estimation), forecasting, advanced executive analytics.

Natural-language Q&A and AI-generated narrative summaries are **optional features** available whenever an AI provider is configured and consented to; every underlying number and finding exists without them.

### Explicitly out of scope (all phases until re-decided)

Approving/rejecting/paying invoices; writing to any financial system; automated vendor communication; replacing Finance's judgment; multi-user RBAC in the desktop MVP; analysis by project/workstream/funding category (no data); autonomous financial decisions of any kind.

## 10. Future Scope

Web-based, centrally hosted deployment with full role-based access (leader, PM, finance partner, vendor manager, executive); direct connections to approved source systems replacing manual file upload; richer forecasting and scenario modeling; portfolio-level aggregation; possible local AI model support where practical.

## 11. Open Questions (resolved under the approved baseline)

All questions below are resolved under the project-owner-approved baseline (see 09-decision-log.md §"Open questions — resolved under the approved baseline"). The table is retained as context for what each question governed.

| # | Question | Why it matters |
|---|---|---|
| OQ-1 | Will Amerisure security validate the consent-based AI data-sharing model (vs. hard enforcement in the original spec)? | Production go/no-go on the AI features |
| OQ-2 | When will sanitized/synthetic samples of invoices, POs, SOWs, rate cards, contracts be available? | Phase 3 requirements are assumptions until then |
| OQ-3 | Does an Amerisure-approved enterprise AI endpoint exist, and what are its access mechanics? | Primary production AI path |
| OQ-4 | Do project/workstream/funding-category mapping files exist anywhere? | Could restore source-spec dimensions to scope |
| OQ-5 | For "missing GED entry" detection: is historical pattern the only baseline, or does finance maintain an expected-entries reference? | Defines an entire rule family's feasibility and design |
| OQ-6 | Who operates FinSight month-to-month — the leader, a delegate/analyst, or both? Are there two personas with different needs? | Shapes workflow, verification UX, and summary design |
| OQ-7 | What is the official monthly cutoff/calendar for GED postings? | Needed for "delayed entry" rules |
| OQ-8 | What variance tolerances count as material (e.g., % or $ thresholds per account/vendor)? | Needed to classify severity without guessing |

## 12. Success Criteria

From the source specification and team discussion, FinSight succeeds if it:

1. **Reduces manual effort** — measurably less time spent on monthly budget review, GED reconciliation, and invoice checking than the current manual process.
2. **Improves exception visibility** — missing/duplicate/delayed GED entries, budget overages, and invoice mismatches are surfaced systematically rather than by chance; fewer missed overages, duplicate invoices, and coding errors.
3. **Delivers leadership-ready output faster** — a complete, accurate monthly summary (budget health, GED status, invoice exceptions, risks, recommended actions) available early in the month with minimal preparation effort.
4. **Is trusted** — every financial finding is reproducible, explainable, and traceable to a rule and its input data; AI never blurs that line; reviewers and auditors can reconstruct any month's review.
5. **Improves governance and audit readiness** — a complete, attributable record of each monthly review cycle exists.
6. **Respects confidentiality** — no data leaves the user's control without informed, logged consent; development never touches real data.
7. **Keeps humans in charge** — 100% of financial actions remain human decisions; FinSight's recommendations demonstrably support, never replace, that judgment.
