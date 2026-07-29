# ADR-V2-006 — `SLV-001` Reader and Workbook Safety Profile

- **Status:** Proposed
- **Date:** 2026-07-27
- **Deciders:** Project Owner; Software Architect; Security Architect; Performance Engineer
- **Related contract:** AC-01

## Context

The current reader does not match the supplied source reports: it assumes the wrong GED header/body rows and shifts the Budget financial columns. Workbook processing must also be bounded so a malformed or hostile `.xlsx` cannot exhaust a restricted corporate laptop or create partial review history.

## Decision

The only first-release layout is `SLV-001` exactly as defined by functional requirements §10:

- Budget worksheet `Original Budget`, header row 1, Account Name B, BGT C, ATD D, ETC E, EAC F, DELTA G, Notes H;
- GED worksheet `GED`, header row 7, body from row 8, all fields A:O;
- exact detail, total, separator, repeated-header, and Grand/Department Total classification;
- total rows retained as evidence but excluded from detail transaction/rule scopes; and
- malformed non-total GED body rows retained as transaction candidates for CORE-04.

Worksheet-name compatibility alone is insufficient. Headers, columns, boundaries, row types, metadata, and formula/cached-value rules must all pass.

The `WRL-001` intake profile is:

| Limit | Value |
|---|---:|
| Compressed `.xlsx` size | 64 MiB |
| Total declared uncompressed ZIP size | 512 MiB |
| One uncompressed ZIP entry | 128 MiB |
| Expansion ratio | 100:1 per entry and overall |
| ZIP entries | 10,000 |
| Worksheets | 32 |
| Rows per worksheet | 100,000 |
| Columns per worksheet | 256 |
| Populated cells per workbook | 2,000,000 |
| Formula cells | 250,000 |
| Merged ranges | 20,000 |
| Shared strings | 1,000,000 entries or 128 MiB |
| GED detail transactions | 10,000 |
| Intake/preflight wall time | 90 seconds |

All limits are inclusive. At-limit fixtures proceed; limit-plus-one fixtures fail before a ReviewCycle, Working Candidate, Review Version, source binding, correction basis, or extraction audit is persisted.

The reader:

- opens sources read-only;
- hashes the same byte stream used for extraction;
- never executes macros, ActiveX, embedded executables/OLE, formulas, or external links;
- rejects macro/ActiveX/OLE/executable and external-link package parts for V1;
- uses a bounded dual view or direct XML value reader to retain formula text and cached values;
- rejects encrypted/password-protected, malformed, duplicate-entry, traversal, ambiguous-dimension, or unsupported packages;
- cancels on the monotonic deadline; and
- cleans protected staging before reporting completion.

Extending a limit or layout requires a versioned profile/reader contract and security/performance review; it is not a permissive fallback.

## Consequences

The supplied reports become first-class supported inputs, CORE-04 can see missing values, and resource behavior is reproducible. Large legitimate workbooks above the profile require an approved future profile rather than an override.

## Verification

- One exact and one limit-plus-one fixture per ceiling.
- Supplied synthetic workbook golden extraction and row-classification tests.
- ZIP/XML/path/macro/external-link/password/formula abuse matrix.
- No-partial-persistence and protected-temp cleanup assertions.
- NFR-081 end-to-summary benchmark on the 10,000-transaction fixture.

## Approval effect

Approval binds the first release to `SLV-001` and `WRL-001`; it does not authorize reader implementation before the full Architecture gate.
