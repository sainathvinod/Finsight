# Test support: fixed clock + synthetic golden .xlsx builder (synthetic data only, NFR-018)
from __future__ import annotations
import openpyxl

class FixedClock:
    def now(self) -> str:
        return "2026-07-17T00:00:00Z"   # injected clock (ADR-003: deterministic)


def persist_confirmed_validation(financial, review_id, dataset):
    """Exercise the governed confirmation/start/persist validation boundary."""

    proposal = financial.validation_rule_set_proposal(review_id, dataset)
    confirmation = financial.confirm_validation_rule_set(
        review_id,
        dataset,
        proposal_hash=proposal["proposal_hash"],
    )
    manifest = financial.start_validation_attempt(
        confirmation["confirmation_id"], dataset
    )
    evaluation = financial.evaluate_manifest(dataset, manifest)
    return financial.persist_evaluation(
        review_id,
        dataset,
        evaluation,
        confirmation_id=confirmation["confirmation_id"],
    )

def build_synthetic_ged(path: str):
    # SYNTHETIC data only. Exactly designed to yield ONE finding (account 6100).
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "GED"
    ws["A1"] = "Amerisure - Demo (SYNTHETIC)"; ws["A2"] = "Year-To-Date for Period May"; ws["A3"] = ""
    header = ["dept_no","dept_name","account_no","account_name","fiscal_period","journal_no",
              "journal_date","invoice_amount","check_no","invoice_date","vendor","agency",
              "journal_desc","line_desc","amount"]
    ws.append([None])  # row4 header lives at row 4 -> pad row-index: we appended row1..3 via A1..A3, need explicit rows
    return _write_ged(wb, ws, header, path)

def _write_ged(wb, ws, header, path):
    # place header at row 4, data from row 5
    for ci, h in enumerate(header, start=1):
        ws.cell(row=4, column=ci, value=h)
    def row(vals):
        return {header[i]: vals[i] for i in range(len(header))}
    data = [
        # dept, deptname, acct, acctname, period, jno, jdate, invamt, chk, invdate, vendor, agency, jdesc, ldesc, amount
        ["9000","Demo","6100","Cloud","2026-05","J1","2026-05-01","8000","C1","2026-04-20","Acme-Synth","AG","svc","line","8000"],
        ["9000","Demo","6100","Cloud","2026-05","J2","2026-05-02","5000","C2","2026-04-21","Acme-Synth","AG","svc","line","5000"],
        ["","","","","","","","","","","","","","TOTAL FOR ACCOUNT 6100","13000"],   # subtotal -> skipped
        ["","","","","","","","","","","","","","",""],                                  # blank -> skipped
        ["9000","Demo","6200","Data","2026-05","J3","2026-05-03","4600","C3","2026-04-22","Globex-Synth","AG","svc","line","4600"],
        ["9000","Demo","6200","Data","2026-05","J4","2026-05-04",".","C4","2026-04-23","Globex-Synth","AG","svc","line","."],  # placeholder
        ["9000","Demo","9999","Misc","2026-05","J5","2026-05-05","-200","C5","2026-04-24","Initech-Synth","AG","credit","line","-200"],  # credit, no budget
    ]
    r = 5
    for d in data:
        for ci, v in enumerate(d, start=1):
            ws.cell(row=r, column=ci, value=v)
        r += 1
    wb.save(path)

def build_synthetic_budget(path: str):
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "Original Budget"
    ws.append(["account_no","budget","atd","etc","eac","delta","notes"])
    ws.append(["6100","10000","13000","0","13000","3000","SYNTHETIC"])
    ws.append(["6200","5000","4600","0","4600","-400","SYNTHETIC"])
    wb.create_sheet("Details"); wb.create_sheet("Actuals")
    wb.save(path)
