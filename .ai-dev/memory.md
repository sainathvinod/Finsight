# FinSight Development Organization — Memory

This document is the organization's memory. Its purpose is to let every AI role begin with minimal context — loading a small, curated set of durable facts and current state rather than re-reading the repository. Reusing this memory instead of re-deriving context is a resource-efficiency requirement under the [Constitution](constitution.md).

Memory has two layers: **Static Memory** (durable, rarely changes) and **Operational Memory** (the current working state). The categories below mirror the Organizational Memory defined in the Constitution.

---

## Static Memory

Durable context that changes rarely and only through deliberate update.

- **Constitution:** [constitution.md](constitution.md) — the governing rules and chain of authority.
- **Manifesto:** [manifesto.md](manifesto.md) — why the organization exists and the culture it enforces.
- **Architecture principles:** Preserve the domain → application → infrastructure → delivery layering, with dependencies pointing inward; keep financial logic deterministic and exact-decimal. Authoritative detail lives in `specs/` (source of truth) and the ADRs referenced there.
- **Repository layout (orientation only):**
  - `specs/` — authoritative FinSight specifications (requirements, epics, features, rules, ADRs, plans, tasks).
  - `spec-driven/` — the SDD framework in use (externally managed).
  - `.claude/` — the **canonical executable layer**: three orchestration agents, skills, recipes, standards, templates, patterns, tech-stack profile.
  - `.ai-dev/` — the **AI Engineering Organization layer**: governance (Constitution), philosophy (Manifesto), workflow (Playbook), Memory, Bootstrap, and migration History.
  - `CLAUDE.md` — repository-level operating contract.
- **Executable roles:** the three orchestration agents in `.claude/agents/` (`finsight-po-ai-agent`, `finsight-architect-ai-agent`, `finsight-developer-ai-agent`). Independent review is a reusable capability, not a separate agent.
- **Development philosophy:** Specification First, AI Second; Trust > AI; deterministic logic decides while AI explains only; humans hold final authority. See the Manifesto for the full statement.

Static Memory is a set of pointers, not a copy. It references the authoritative documents rather than duplicating them.

---

## Operational Memory

The current working state. This is the layer that changes as work proceeds. Values below are placeholders and must be filled in by the responsible role or human; do not invent them.

- **Current milestone:** Target-product guided-workflow build (Welcome → Date → 3-source upload → missing-file confirm → extraction review → corrections → attestation → analysis → report → history → memory → Ask Fin → accessibility → packaging), realized over the existing PySide6 delivery scaffold. Governed scoping completed via parity matrix (see decision-ready brief; next-available decision id = DEC-036).
- **Current task:** Ordered no-invent increments. DONE: #1 Welcome/first-launch (F-01-01); #2 dedicated Review-Period step (FR-005, F-01-03); #3 three-source upload + invoice-capture foundation, captured-not-analyzed (F-01-02, FR-004); #4 missing-source two-step confirmation + audit (DEC-027/028, §7); #5 per-source extraction review — all records + lineage + search/sort — and honest processing stages (F-01-09, FR-016/027, §8/§9). All committed, 742 tests passing. NEXT: #6 corrections subsystem + migration 0004 (FR-028/029; largest backend increment). #8 report "visual financial map" and #9 historical-comparison significance are gated by RED CARDs 1 and 3 below (need PO input).
- **Open Red Cards:** (added 2026-07 during target-product scoping; each requires a human/PO decision — do not invent)
  1. **Visual "financial map" undefined.** The target asks for a "visual financial map" in the report, but no spec defines a financial/flow/money map. *Blocks:* report visualization increment. *Needed:* PO defines it. If it is only visual styling of existing deterministic sections → buildable under F-07-01/F-03-01 + 08-ui-design-system.md with **no new analytical content**. If it is a new analytical artifact (sankey/treemap/flow) → collides with the F-07-01 fixed-section guardrail; ratify via a DEC + story or human-ratified F-07-05.
  2. **Invoice analysis (E-12, Phase 3).** Invoice *upload slot + provenance capture* is R1-authorized and invent-free (build it). Invoice *extraction/validation/reconciliation* is blocked: needs (a) logged PO decision promoting E-12 into the active release + confirmation build-gate OQ-2 satisfied; (b) sample documents/approved templates for each non-HCL invoice + PO/SOW/rate-card format (A-05: "unseen"); (c) finance-owned values CP-RATE-TOLERANCE, CP-HOURS-TOLERANCE, PO-balance tolerance, CP-INV-STATUS-CRITERIA, invoice materiality (OQ-8), duplicate keys/window; (d) an authoritative ruling on the OQ-2 "unseen vs. approved-in-baseline" spec contradiction. *Until supplied:* capture + provenance + render "Invoice Analysis — Unavailable"; run zero extraction.
  3. **Historical comparison beyond stored deterministic outputs.** Comparing stored deterministic outputs as **facts** is authorized (buildable). Blocked only if asked for a new comparison metric/baseline beyond FR-032/036/078/108–111 + R-HST, a history-derived baseline computation (R2), an AI-computed delta (forbidden — R-HST-02), or a new "significant-change" cutoff (CP-MOM-THRESHOLD/CP-TREND-N/CP-MINHISTORY are finance-owned). *Needed:* approved rule + finance-owned parameter, or confirmation the comparison stays descriptive over stored FR-079/FR-108 outputs.
  4. **New severity level / production threshold value.** Severity is a closed set (Critical/High/Medium/Low, FR-070/R-FND-02, never AI-assigned). Any new level, "Review Health Score", or hard-coded production numeric boundary is invention. *Needed:* approved spec change (normally refuse), or finance-owned values via governed config with explicit "demonstration-only" confirmation for synthetic values.
  5. **DoD "FinSight.app launches by double-click".** Out of R1 scope (`.app`/`.dmg` not built; packaging is a later phase, ADR-008) **and** environmentally uncertifiable headless (no display/Finder session). *Needed:* either drop double-click from DoD and accept the headless-smoke/wheel-launch criterion, or approve promoting the packaging phase (PyInstaller/notarization) **and** provide a GUI-capable acceptance environment + owner. Headless-verifiable substitute exists (bundle structure + `QT_QPA_PLATFORM=offscreen FINSIGHT_SMOKE=1` exit 0).
  6. **DoD "live Ollama answering".** Out of scope (Ask Fin = R2/E-09; consent gate FR-096; E-09 gate OQ-1 Open) **and** uncertifiable headless (no live model; non-deterministic). *Needed:* either replace with NullProvider + deterministic question-library fallback (FR-101/102, NFR-063) verification, or approve a live-provider acceptance run in an Ollama+model environment **and** confirm OQ-1 security validation.
- **Active remediation:** _none._
- **Known issues:** _none blocking._
- **Lessons learned:** The target workflow is almost entirely authorized by existing specs; only report **correction disclosure** needs a new amendment (DEC-036 extending F-07-01, to be logged before that increment). The rest builds on existing authority + the live PySide6 scaffold. Six items above are genuine human-decision stops and must be surfaced, not invented around.

---

## Memory Ownership

- The **Governance Reviewer** owns memory quality and confirms memory updates during final review.
- The role that discovers new operational information **proposes** the corresponding memory update.
- **Humans** resolve Red Cards and approve business and governance changes.
- Memory may not introduce new requirements, decisions, thresholds, or facts; it only records what is already approved.

---

## How memory is updated

- **Static Memory** changes only when a governing document, architecture principle, or repository structure changes. Update the pointer here; never copy content that belongs in the authoritative document.
- **Operational Memory** is updated as part of doing the work: the responsible role records the current milestone and task, opens and closes Red Cards, and notes active remediation and known issues. Every update should correspond to an artifact produced in the workflow (see the [Playbook](playbook.md)).
- **Lessons Learned** are appended when a review, verification, or governance step surfaces a durable improvement. They are additive and are not deleted when a task closes.
- **Open Red Cards** are added by any role that raises one and are cleared only after a human resolves the underlying issue, per the Constitution.

Memory records what is known and approved. It never introduces requirements, thresholds, decisions, dates, or metrics that do not already exist in the approved specifications or in a human decision.
