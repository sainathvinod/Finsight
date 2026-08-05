# June 2026 Fixture and Independent-Oracle Contract

**Prepared:** 2026-07-31  
**Status:** Draft; blocked by S1A-D07 and S1A-D10  
**Implementation authorization:** None  
**Purpose:** Requirements-level controlled-case contract for `FIX-JUN-001`,
`ORACLE-JUN-001`, and `VER-MOM-001`

## 1. Authority and boundary

This document defines the exact controlled changes that the later June
fixture and independent oracle must implement. It does not create or authorize
the workbooks. The approved May fixtures and sealed independent oracle remain
unchanged.

The future June package must use:

- Budget workbook `Sample_Budget_Report_June_2026.xlsx`, worksheet
  `Original Budget`;
- GED workbook `Sample_GED_Report_June_2026.xlsx`, worksheet `GED`;
- Department Number `00-0245` and the exact supplied Department Name
  `Applications Enginee`;
- reporting period June 2026;
- Budget detail rows in the same source-row positions as May;
- GED header row 7, detail beginning at row 8, account-total rows, and one
  department-total row; and
- only synthetic financial values and synthetic names for newly introduced
  parties.

No cost center, workstream, funding category, project, invoice source, or
other unsupported dimension may be invented.

## 2. Frozen May comparison identity

| Item | Exact May authority |
|---|---|
| Budget source | `Sample_Budget_Report.xlsx`; SHA-256 `bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14` |
| GED source | `Sample_GED_Report.xlsx`; SHA-256 `2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c` |
| Oracle | `STAGE-1-INDEPENDENT-ORACLE-2026-07-29.json`; SHA-256 `63637b6e2b18b15f73d5f087e734a7715eb64f9790195944c1df0d94de9ed06e` |
| Department | `00-0245` / `Applications Enginee` |
| Reporting period | May 2026 |
| May Budget BGT | `$10,372,000.00` |
| May Budget ATD | `$3,500,095.00` |
| May parseable GED | `$3,500,095.00`, explicitly partial because `GED!O87` is blank |
| May findings | 5: four High, one Medium; Overall `Incomplete`, `At Risk (Red)` |

## 3. Deterministic June row plan

The June GED workbook is derived from the May row structure by inserting rows
in this exact order. This makes every planned source row stable before the
fixture is generated.

| Operation | Position in the resulting June worksheet | Purpose |
|---|---:|---|
| Insert one row before the May account-525005 total | June row 22 | one present June payroll entry; the second expected entry is absent |
| Insert a new invalid-account transaction and its account-total row after the shifted 527015 total | June rows 46–47 | new coding issue for account 527999 |
| Insert one exact copy after the two shifted 533003 duplicate rows | June row 70 | three-row exact duplicate group |
| Insert one June transaction before the shifted 537015 total | June row 90 | under-to-over account and unusual increase |
| Insert one June transaction before the shifted 537040 total | June row 101 | delayed posting and reconciliation control |
| Insert three June transactions before the shifted 555035 total | June rows 296–298 | new/higher/lower vendor controls |

The resulting GED worksheet has 308 rows. The shifted department total is row
306 and blank report rows are 307–308. All account and department formulas must
be rewritten to their resulting exact ranges; presentation totals remain
excluded from transaction sums.

At minimum, the changed account totals are `O23=SUM(O11:O22)`,
`O45=SUM(O44:O44)`, `O47=SUM(O46:O46)`, `O76=SUM(O68:O75)`,
`O91=SUM(O81:O90)`, `O102=SUM(O95:O101)`,
`O299=SUM(O252:O298)`, and `O305=SUM(O300:O304)`. `O306` must sum every
resulting account-total cell exactly once, including new `O47`.

The original May transaction that was `GED!O87` becomes June `GED!O92` after
the insertions above. It receives a synthetic Amount of `$4,700.00`; no other
existing source value changes unless this contract explicitly identifies it.

## 4. Exact controlled source changes

### 4.1 Budget controls

Formula cells F/G retain the supplied `EAC = ATD + ETC` and
`DELTA = BGT - EAC` relationships.

| Case ID | June source cells | Account | May values | Required June values | Expected financial outcome |
|---|---|---|---|---|---|
| `JUN-BUD-01` | `Original Budget!C3:E3` | 525005 | BGT 2,850,000; ATD 1,075,000; ETC 1,575,000 | BGT 2,900,000; ATD 1,183,000; ETC 1,550,000 | changed Budget and GED values; no overrun |
| `JUN-BUD-02` | `Original Budget!C27:E27` | 533003 | BGT 22,000; ATD 3,175; ETC 10,000 | BGT 22,000; ATD 3,257.50; ETC 10,000 | reconciles the added duplicate copy; still under BGT |
| `JUN-BUD-03` | `Original Budget!C40:E40` | 537015 | BGT 175,000; ATD 58,400; ETC 90,000 | BGT 70,000; ATD 86,400; ETC 25,000 | GED exceeds BGT by 16,400; May under → June over |
| `JUN-BUD-04` | `Original Budget!C47:E47` | 537035 | BGT 95,000; ATD 6,300; ETC 55,000 | BGT 98,000; ATD 11,000; ETC 50,000 | May missing-Amount condition resolved and reconciliation restored |
| `JUN-BUD-05` | `Original Budget!C48:E48` | 537040 | BGT 280,000; ATD 92,000; ETC 155,000 | BGT 285,000; ATD 104,500; ETC 150,000 | intentional ATD-to-GED difference of 500 |
| `JUN-BUD-06` | `Original Budget!C91:E91` | 555035 | BGT 1,100,000; ATD 1,250,000; ETC 650,000 | BGT 1,240,000; ATD 1,300,000; ETC 500,000 | remains over BGT by 60,000 but improves from May's 150,000 overrun |

All other Budget detail values remain equal to May. Recalculated June detail
totals are therefore:

- BGT: `$10,465,000.00`;
- ATD: `$3,703,377.50`;
- ETC: `$5,632,000.00`;
- EAC: `$9,335,377.50`; and
- DELTA: `$1,129,622.50`.

The independent oracle must recompute these figures from detail rows, not copy
them from workbook total formulas.

### 4.2 GED controls

Every unlisted field on a carried-forward May row remains unchanged. Every new
row uses Department `00-0245` and Department Name `Applications Enginee`
except the deliberately invalid account combination in `JUN-GED-03`.

| Case ID | Exact June source | Material values | Expected deterministic result | Status impact |
|---|---|---|---|---|
| `JUN-GED-01` | `GED!A22:O22` | Account 525005; Fiscal Period `2026-06`; Journal `PAY0192101`; Journal Date `2026-06-05`; payroll description; Amount `$108,000.00` | valid new June entry; contributes to account/YTD/current-period spend | none |
| `JUN-GED-02` | absence paired with `EXPECTED-GED-525005-2026-06-02`; searched detail population `GED!A8:O305` | expected second June payroll posting for account 525005 is absent | optional `R-GED-03` FAIL only under approved expected-entry reference version | yes; High under proposed config |
| `JUN-GED-03` | `GED!A46:O46`; total `GED!O47` | Department 00-0245; Account 527999; Fiscal Period `2026-06`; Journal `JUN26-CODE-001`; Journal Date `2026-06-18`; Amount `$2,400.00` | protected CORE-02 FAIL; no matching Budget key | yes; High |
| `JUN-GED-04` | `GED!A68:O70` | all 15 canonical fields match; account 533003; each Amount `$82.50` | one CORE-03 duplicate group of three; two excess copies; duplicate exposure `$165.00` | yes; Medium |
| `JUN-GED-05` | `GED!A90:O90` | Account 537015; Fiscal Period `2026-06`; Journal `JUN26-MECH-001`; Journal Date `2026-06-24`; Vendor `NORTHSTAR SYNTHETIC EQUIPMENT`; Invoice/Amount `$28,000.00` | CORE-01 FAIL on account; optional R-BUD-03 controlled increase | yes; High overrun plus configured optional severity |
| `JUN-GED-06` | `GED!O92` | Amount `$4,700.00`; all other carried source fields unchanged | CORE-04 now PASS for the formerly blank May record; account 537035 CORE-01/CORE-05 evaluable and PASS | resolves May missing-data finding |
| `JUN-GED-07` | `GED!A101:O101` | Account 537040; Fiscal Period `2026-06`; Journal `JUN26-LEASE-001`; Journal Date `2026-07-08`; Invoice Date `2026-06-30`; Vendor `SYNTHETIC SOFTWARE LEASING`; Invoice/Amount `$12,000.00` | optional R-GED-04 FAIL only against approved June cutoff; CORE-05 account difference `$500.00` because Budget ATD is 104,500 and GED is 104,000 | yes; delayed plus High reconciliation |
| `JUN-GED-08` | `GED!A296:O296` | Account 555035; Fiscal Period `2026-06`; Journal `JUN26-CONS-001`; Journal Date `2026-06-12`; Vendor `NORTHSTAR SYNTHETIC SERVICES LLC`; Invoice/Amount `$25,000.00` | new vendor and valid GED activity | no independent finding; comparison `New` |
| `JUN-GED-09` | `GED!A297:O297` | Account 555035; Fiscal Period `2026-06`; Journal `JUN26-CONS-002`; Journal Date `2026-06-19`; Vendor `TEKSYSTEMS, INC`; Invoice/Amount `$45,000.00` | continuing vendor with higher YTD spend | no independent finding; recurrence `Continuing`, neutral detail `Increased` |
| `JUN-GED-10` | `GED!A298:O298` | Account 555035; Fiscal Period `2026-06`; Journal `JUN26-CONS-003`; Journal Date `2026-06-26`; Vendor `HCL AMERICA INC`; credit Invoice/Amount `-$20,000.00` | continuing vendor with lower YTD spend | no independent finding; recurrence `Continuing`, neutral detail `Decreased` |
| `JUN-GED-11` | June current-period slice `Fiscal Period = 2026-06` | no PERR & KNIGHT row exists in June activity; prior vendor identity comes from May GED rows 259, 260, 267, 278, 283, and 288 | vendor no longer appearing in current-period activity; YTD presence remains explicitly labeled | no independent finding; current-period recurrence `Resolved` with detail `No current-period activity`; YTD recurrence `Continuing` |
| `JUN-GED-12` | carried June `GED!A44:O44` (May row 43 shifted by one) | Department remains `00-0999`; Account 527015; Amount `$1,850.00` | CORE-02 and account-527015 CORE-05 continue unchanged | yes; continuing/unmodified control |

June exact GED controls are:

- 266 transaction rows;
- 32 account-total rows;
- one department-total row;
- two blank rows;
- zero missing/unparseable required Amount values;
- parseable transaction Amount `$3,705,277.50`;
- mapped eligible GED Amount `$3,701,027.50`;
- unmapped eligible GED Amount `$4,250.00`; and
- no presentation subtotal/department-total contribution to GED spend.

## 5. Optional-rule configurations required before fixture execution

The following proposed values are part of S1A-D07 approval. If an authority
changes a value, this contract and its expected oracle results must be revised
before workbook generation.

| Configuration ID | Proposed exact value | Applies to | Boundary behavior |
|---|---|---|---|
| `CP-MOM-THRESHOLD-v1` | current Fiscal-Period GED Activity increase must be both `>= $5,000.00` and `>= 50.00%` versus the immediately prior fiscal-period activity | R-BUD-03 / account 537015 | equality at either threshold passes that component; zero prior uses amount threshold and labels percentage unavailable |
| `EXPECTED-GED-REF-v1` | expected key `EXPECTED-GED-525005-2026-06-02`, Department 00-0245, Account 525005, period 2026-06, one required matching payroll journal after the present `PAY0192101` | R-GED-03 | exactly one matching entry passes; zero fails; more than one is evaluated by duplicate/other configured rules, not silently accepted as the missing key |
| `CUTOFF-CALENDAR-v1` | June 2026 posting cutoff `2026-07-05`; Journal Date is the posting-date field | R-GED-04 / row 101 | on or before cutoff passes; after cutoff fails; row 101 is three days late |
| `CODING-REF-v1` | exact Budget Department+Account keys from the June Budget detail rows | protected CORE-02 | no fuzzy account mapping; 00-0245/527999 and 00-0999/527015 fail |

The June Rule Set contains exactly the five protected core rules plus active
optional R-BUD-03, R-GED-03, and R-GED-04: eight selected rules. R-GED-06
amount anomaly is excluded because May and June do not meet its approved
trailing-history minimum. Optional R-GED-05 is excluded because no separate
finance-maintained vendor reference is approved. Excluded rules create no
Rule Execution, Rule Result, observation, or Finding.

## 6. Expected core and optional outcomes

| Rule / check | June expected outcome | Exact evidence |
|---|---|---|
| CORE-01 Budget Overrun | two account Findings: 537015 over `$16,400.00`; 555035 over `$60,000.00` | Budget rows 40/91 and their complete GED populations including rows 90 and 296–298 |
| CORE-02 Valid Account Coding | two transaction Findings: June rows 44 and 46 | Budget key set plus GED A/C cells |
| CORE-03 Duplicate Transactions | one group Finding, rows 68–70, exposure `$165.00` | all 15 canonical GED fields on all three rows |
| CORE-04 Complete and Correct Data | zero missing-Amount Findings; formerly blank row 92 passes | `GED!O92 = 4700.00` and complete required-field population |
| CORE-05 Budget-to-GED Reconciliation | two Findings: account 527015 difference `$1,850.00`; account 537040 difference `$500.00` | Budget D11/D48 and exact mapped GED populations |
| R-BUD-03 | one controlled Finding for 537015: May current-period `$11,926.00`, June current-period `$28,000.00`, increase `$16,074.00` / `134.78%` | May rows 84–85; June row 90; config version |
| R-GED-03 | one controlled missing-expected Finding for account 525005 | expected reference key plus present row 22 and verified absence in all other detail rows |
| R-GED-04 | one controlled delayed-posting Finding for June row 101, three days late | Journal Date, cutoff date/version, source row |
| R-GED-05 vendor expectation | excluded from the June Rule Set; no result | absence of governed vendor reference |
| R-GED-06 amount anomaly | excluded from the June Rule Set; no result | insufficient approved history |

The exact optional severities and resulting Overall Review Status remain
blocked by S1A-D07. The fixture may not be marked oracle-ready until those
values, the stable Rule IDs/versions, and positive/negative/boundary controls
are recorded.

## 7. May-to-June expected comparison controls

| Case ID | Identity | May evidence/value | June evidence/value | Expected recurrence | Expected trend/detail | Overall-status effect |
|---|---|---|---|---|---|---|
| `JUN-CMP-01` | account 537015 Budget health | Budget row 40; GED rows 77–85; under BGT by 116,600 | Budget row 40; GED rows 81–90; over BGT by 16,400 | Continuing | Worsened; under → over | yes |
| `JUN-CMP-02` | CORE-01 / account 555035 | overrun Finding 150,000; Budget row 91; GED rows 246–289 | overrun Finding 60,000; Budget row 91; GED rows 252–298 | Continuing | Improved | yes, favorable change |
| `JUN-CMP-03` | CORE-04 / May source-record identity | `GED!O87` blank; High Finding | equivalent carried transaction is complete at June `GED!O92 = 4,700`; no current Finding | Resolved | Not Applicable | yes, favorable data-quality change |
| `JUN-CMP-04` | CORE-03 / duplicate fingerprint scope | May rows 65–66; exposure 82.50 | June rows 68–70; exposure 165.00 | Continuing | Worsened | yes |
| `JUN-CMP-05A` | CORE-02 / May GED source-record scope at row 43 | May row 43, 1,850 invalid | no current Finding with the same stable source-record ID | Resolved | Not Applicable | yes |
| `JUN-CMP-05B` | CORE-02 / June GED source-record scope at row 44 | no prior Finding with the same stable source-record ID | June row 44, 1,850 invalid | New | Not Applicable | yes |
| `JUN-CMP-06` | CORE-05 / account 527015 | difference 1,850 | difference 1,850 | Continuing | Unchanged | yes |
| `JUN-CMP-07` | CORE-01 / account 537015 | no Finding | new overrun Finding 16,400 | New | Not Applicable | yes |
| `JUN-CMP-08` | CORE-02 / source-record 527999 | absent | June row 46, 2,400 invalid | New | Not Applicable | yes |
| `JUN-CMP-09` | CORE-05 / account 537040 | reconciled | difference 500 | New | Not Applicable | yes |
| `JUN-CMP-10` | new vendor identity `northstar synthetic services llc` | absent | June row 296; YTD/current-period 25,000 | New | Not Applicable | no finding by itself |
| `JUN-CMP-11` | vendor identity `teksystems, inc` | May YTD from recorded rows | June YTD = May YTD + 45,000 | Continuing | Changed / Increased | no finding by itself |
| `JUN-CMP-12` | vendor identity `hcl america inc` | May YTD from recorded rows | June YTD = May YTD - 20,000 | Continuing | Changed / Decreased | no finding by itself; favorable neutral spend change |
| `JUN-CMP-13A` | PERR & KNIGHT current-period activity | May rows 283/288 in period 2026-05 | no Fiscal Period 2026-06 row | Resolved | Not Applicable; detail `No current-period activity` | no finding by itself |
| `JUN-CMP-13B` | PERR & KNIGHT YTD identity | May YTD spend from recorded rows | same carried YTD spend in June | Continuing | Unchanged | no finding by itself |
| `JUN-CMP-14` | R-GED-03 expected key | rule not selected; no prior Rule Result | current missing-expected Finding | Missing Prior Evidence | Missing Prior Evidence; detail `First evaluated in June` | yes |
| `JUN-CMP-15` | R-GED-04 / governed delayed-posting scope | rule not selected; no prior Rule Result | current delayed Finding | Missing Prior Evidence | Missing Prior Evidence; detail `First evaluated in June` | yes |
| `JUN-CMP-16` | R-BUD-03 / account 537015 | rule not selected; no prior Rule Result | current unusual-increase Finding | Missing Prior Evidence | Missing Prior Evidence; detail `First evaluated in June` | yes |

Every comparison record cites the exact May published run, June published run,
comparison-policy version, both source projections, and whether the measure is
YTD, current Fiscal Period, YTD movement, or source-report snapshot. Vendor
spend change is neutral; it does not claim causation or financial harm without
a governed Rule Result.

## 8. Independent oracle contract

`ORACLE-JUN-001` and `VER-MOM-001` must be produced by a verifier that does not
import FinSight production calculation code. It must read XLSX package XML,
use `Decimal`, classify detail/total rows independently, and fail nonzero on
any difference.

The oracle must contain:

- source SHA-256 hashes and exact workbook/sheet/cell references;
- row-type counts and excluded presentation totals;
- every Budget row's BGT/ATD/ETC/EAC/DELTA controls;
- exact GED parseable/mapped/unmapped totals and every account/vendor sum;
- every core and activated optional Rule Result, status, Finding, severity,
  and evidence population;
- all comparison identities, recurrence and trend values, period bases, and
  both-period evidence;
- positive, negative, and exact-boundary controls for each optional rule; and
- a comparison against FinSight recorded projections with a zero-difference
  requirement.

## 9. Gate

This contract is ready for stakeholder decision presentation, not workbook
generation. Fixture work remains prohibited until:

1. S1A-D07 and S1A-D10 are approved;
2. optional Rule IDs, versions, severities, reference/calendar owners, and
   status aggregation are recorded;
3. Product Owner and Financial Control approve this exact case register; and
4. the successor Architecture gate authorizes the generator/oracle design.
