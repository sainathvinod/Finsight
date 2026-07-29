# Stage 1 Governing Directive Record

**Recorded:** 2026-07-29
**Status:** Source preserved; baseline adoption pending Stage 1 approval

## 1. Source records

| Source | Original location | Lines | SHA-256 |
|---|---|---:|---|
| FinSight Production-Readiness and Governed Release Program | `/Users/lakshminarayanana/.codex/attachments/8a5a1e10-6c8a-44d0-932f-b9af580ec704/pasted-text.txt` | 1,057 | `6653b87ba7d23fa83bba14450f1abb69479661e9550c03ef9b1154e16998bc53` |
| Enterprise Rule Governance, Complete Reporting, Audit History, and Final Distribution | `/Users/lakshminarayanana/.codex/attachments/816cbd88-afc7-4714-b051-3a9dc7c3abc8/pasted-text.txt` | 494 | `1275c7dee199b1f08d76a7bdcedb1185b645e04039f0a16d417a6ac05accf92d` |

Exact copies are preserved in the external Stage 1 snapshot under the descriptive
filenames recorded in [Current Governed Baseline](CURRENT-GOVERNED-BASELINE.md).

## 2. Operative direction

The first source:

- sets the final supported Windows product objective and non-negotiable safety
  boundaries;
- mandates nine sequential stages and stop-on-failed-gate behavior;
- authorizes only Stage 1 now;
- requires explicit Product Owner decisions before production implementation;
- defines detailed Stage 2–9 scopes and exit criteria;
- requires separation of implementation and independent approval;
- requires exact release evidence and a final binary GO/NO-GO decision; and
- prohibits packaging before Stages 1–6 pass.

The second source:

- preserves the five protected baseline controls;
- requires visible, user-confirmed exact active Rule Sets;
- requires every downstream result to originate only from the recorded engine
  results for that Rule Set;
- expands lifecycle-wide immutable audit requirements;
- mandates deterministic Leadership Summary audit disclosure;
- mandates complete selected-run PDF profiles and the specified XLSX evidence
  workbook;
- adds enterprise confidentiality, temporary-file, export-destination, metadata,
  and integrity requirements;
- mandates the independent reviewer matrix and Product Owner hands-on gate; and
- forbids final distribution until the signed, scanned, clean-machine-qualified,
  automatically provisioned candidate receives final GO.

## 3. Precedence and interpretation

The sources are current Product Owner direction for the production-readiness
program. They supersede conflicting release sequencing, minimum export scope,
manual local-AI setup, and incomplete final-distribution language.

They do not silently decide ambiguous protected-rule or release-profile choices.
Those items remain in
[the Stage 1 decision register](STAGE-01-PRODUCT-AND-FINANCIAL-CONTROL-DECISIONS.md).

Implementation convenience, the current code, existing tests, and historical
oracle expectations cannot resolve those decisions.

## 4. Preservation and change control

The external preserved text hashes match the original attachments. The
production-readiness requirements delta assigns durable requirement IDs without
editing frozen historical requirement snapshots. The delta becomes effective
only through the Stage 1 approval record.

Any future change must create a successor source/requirement version, retain
these hashes, state the reason, identify the actor/authority, update traceability,
and preserve historical replay.
