# Responsibility Map (old → new)

How each legacy responsibility maps into the layered architecture. Reviewer rigor is preserved as the reusable **review** capability executed independently (separate, read-only, fresh context), not as standalone agents.

| Current asset | Current responsibility | Target layer | Target asset | Migration action | Risk |
|---|---|---|---|---|---|
| product-owner | Approved task → Implementation Brief | agent + skill | `finsight-po-ai-agent` + `requirements` | MIGRATE → archive/remove | Low |
| product-owner-reviewer | Independent Brief review | skill (review mode) | `review` (requirements) + `recipes/requirements/04-review` | MIGRATE → remove | Low |
| architect | Brief → Technical Plan | agent + skill | `finsight-architect-ai-agent` + `architecture-design` | MIGRATE → archive/remove | Low |
| architecture-reviewer | Independent plan review | skill (review mode) | `review` (architecture) + `recipes/design/architecture/03-review` | MIGRATE → remove | Low |
| coding | Implement plan | agent + skills | `finsight-developer-ai-agent` + `backend-implementation` / `ui-shell-implementation` | MIGRATE → archive/remove | Low |
| code-reviewer | Independent code review | skill (review mode) | `review` (code) + implementation `04-review` recipes | MIGRATE → remove | Low |
| verification-testing | Full-chain verification | skill | `testing` + `recipes/testing/` | MIGRATE → archive/remove | Low |
| testing-reviewer | Independent test review | skill (review mode) | `review` (test) + `recipes/testing/04-review` | MIGRATE → remove | Low |
| governance-reviewer | Final end-to-end validation | skill + review mode | `governance` + `review` (governance) + `recipes/governance/` | MIGRATE → archive/remove | Low |
| remediation | Fix cited defects | skill | `remediation` + `recipes/remediation/` | MIGRATE → archive/remove | Low |
| remediation-reviewer | Independent remediation review | skill (review mode) | `review` (remediation) + `recipes/remediation/04-review` | MIGRATE → remove | Low |

## Duplication consolidated into standards

Rules repeated across the 11 contracts (spec authority, no-invention, determinism, layering, minimal-change, traceability, no autonomous financial action, independent review, Red Card escalation, human-only decisions) are consolidated into [`.claude/standards/`](../../.claude/standards/) and referenced — not restated — by skills and recipes. Origin principles remain in `.ai-dev/constitution.md`.
