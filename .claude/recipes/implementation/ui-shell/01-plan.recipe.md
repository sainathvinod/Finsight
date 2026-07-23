# Recipe — UI Shell Implementation: 01 Plan

**Layer:** recipe (workflow engine). Composes the [ui-shell-implementation skill](../../../skills/ui-shell-implementation/SKILL.md). References skills/standards/tech-stack; does not invoke agents.
**Phase:** Plan.

## Purpose
Confirm the approved plan is sufficient to implement a delivery/UI-shell slice within its allowed-files list, with no unapproved framework.

## Required inputs
The reviewed, human-approved Plan and allowed-files list; [tech-stacks/finsight.yml](../../../tech-stacks/finsight.yml); `specs/07`/`08`.

## Standards
[accessibility](../../../standards/accessibility.md), [coding](../../../standards/coding.md), [architecture](../../../standards/architecture.md).

## Ordered steps
1. Confirm the slice targets the delivery ring (today: text-mode wizard) with no new framework.
2. Confirm workflow order and accessibility expectations.
3. Note expected tests.

## Outputs
An implementation readiness note.

## Stop conditions / escalation
Plan assumes an unapproved UI technology, or reorders the workflow → **Red Card** (record wizard drift).

## Prohibited behaviors
Introducing a web/GUI framework; encoding financial truth in the shell.
