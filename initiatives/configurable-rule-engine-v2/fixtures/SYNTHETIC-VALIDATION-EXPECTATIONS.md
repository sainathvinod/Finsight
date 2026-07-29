# V2 Synthetic Validation Expectations

- **Status:** Draft Requirements fixture oracle
- **Sources:** [Stage 2 manifest](../../../outputs/019fa405-6605-7950-a941-f7d459d322c7/Synthetic_Test_Data_Manifest.md); functional requirements §2.7, §11, and §12
- **Purpose:** Record every deterministic cross-rule effect of the four intentional Stage 2 scenarios without changing the completed synthetic workbooks or their original manifest.

The Stage 2 manifest identifies four intentional source-data scenarios. A scenario may affect more than its primary rule because all five controls run against the same confirmed `VerifiedDataset`. These secondary outcomes are expected engine behavior, not additional source-data defects.

## Scenario matrix

| Scenario | CORE-01 | CORE-02 | CORE-03 | CORE-04 | CORE-05 |
|---|---|---|---|---|---|
| TEST-01 — `00-0245 + 555035` overrun | `FAIL` for the Budget key | Transactions remain mapped | Fingerprints remain unique | Required fields remain valid | `PASS`; Budget ATD includes the same GED detail |
| TEST-02 — GED rows 65/66 duplicate | Budget key remains within BGT | Both rows remain mapped | One fingerprint group `FAIL`; all member rows cited | Both rows remain valid | `PASS`; exact duplicates remain in both the GED sum and synthetic Budget ATD |
| TEST-03 — missing GED `O87` for `00-0245 + 537035` | `NOT_EVALUATED` for only that exact Budget key | Row remains mapped because Amount is not a mapping key | Its null-token fingerprint remains evaluable and unique | Row 87 `FAIL` for missing Amount | `NOT_EVALUATED` for only that exact Budget key; no partial sum is used |
| TEST-04 — GED row 43 uses `00-0999 + 527015` | The unmatched row joins no Budget scope; `00-0245 + 527015` evaluates with an exact-key sum of zero and remains within BGT | Row 43 `FAIL` because the complete key is absent from Budget | Its fingerprint remains unique | The parseable six-character Department Number remains valid | Consequential `FAIL` for Budget key `00-0245 + 527015`: ATD `1,850.00` versus exact-key GED sum `0.00` |

## Expected run-level projection

| Output | Expected value |
|---|---|
| CORE-01 Rule Execution | `NOT_EVALUATED` because that precedence applies when TEST-03 blocks one scope; its TEST-01 failed scope remains visible |
| CORE-02 Rule Execution | `FAIL` |
| CORE-03 Rule Execution | `FAIL` |
| CORE-04 Rule Execution | `FAIL` |
| CORE-05 Rule Execution | `NOT_EVALUATED` because TEST-03 blocks one scope; the TEST-04 failed reconciliation scope remains visible |
| Overall Review Status | `Incomplete` |
| RAG Status | `At Risk (Red)` |
| Budget Overruns | `1` |
| Duplicate Transactions | `1` duplicate copy beyond the deterministic reference row |
| Missing Required Data | `1` transaction |
| Control Findings | `5`: one CORE-01 overrun, one CORE-02 mapping failure, one CORE-03 duplicate group, one CORE-04 required-field failure, and one consequential CORE-05 reconciliation failure |
| NOT_EVALUATED scope results | `2`: the TEST-03 exact Budget key under CORE-01 and CORE-05 |

The complete Rule Result ledger still retains every passing scope. A `NOT_EVALUATED` rule-level roll-up never conceals failed or passing scope results, and it never creates a failure Finding by itself.
