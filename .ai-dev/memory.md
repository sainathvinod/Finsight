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

- **Current milestone:** _<placeholder — the objective currently being worked toward>_
- **Current task:** _<placeholder — the specific unit of work in progress, with its traceability reference>_
- **Open Red Cards:** _<placeholder — none / list each with what is missing, why it blocks, and the input needed>_
- **Active remediation:** _<placeholder — none / the FAIL being corrected and its originating review record>_
- **Known issues:** _<placeholder — none / issues observed but not currently blocking>_
- **Lessons learned:** _<placeholder — durable observations that should improve future work>_

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
