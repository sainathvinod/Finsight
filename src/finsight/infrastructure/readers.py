# Implements: FR-001, FR-011, FR-012, FR-013, F-01-05, F-02-02 (DocumentReader + ExcelReader via openpyxl)
from __future__ import annotations
from typing import List, Dict, Any

class ExcelReader:
    # DocumentReader implementation (infrastructure). Pins nothing locale-dependent.
    def read(self, path: str, doc_type: str) -> List[Dict[str, Any]]:
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        if doc_type == "GED":
            return self._read_ged(wb)
        if doc_type == "BUDGET":
            return self._read_budget(wb)
        raise ValueError("unknown doc_type: " + doc_type)

    def _read_ged(self, wb) -> List[Dict[str, Any]]:
        ws = wb["GED"]
        cols = ["dept_no","dept_name","account_no","account_name","fiscal_period","journal_no",
                "journal_date","invoice_amount","check_no","invoice_date","vendor","agency",
                "journal_desc","line_desc","amount"]
        header_row = 4  # rows 1-3 are preamble (FR-013)
        out = []
        for r in range(header_row + 1, ws.max_row + 1):
            vals = [ws.cell(row=r, column=ci + 1).value for ci in range(len(cols))]
            row = dict(zip(cols, vals)); row["_source"] = "GED!R" + str(r)
            out.append(row)
        return out

    def _read_budget(self, wb) -> List[Dict[str, Any]]:
        ws = wb["Original Budget"]
        cols = ["account_no","budget","atd","etc","eac","delta","notes"]
        out = []
        for r in range(2, ws.max_row + 1):  # row 1 = header
            vals = [ws.cell(row=r, column=ci + 1).value for ci in range(len(cols))]
            row = dict(zip(cols, vals)); row["_source"] = "Original Budget!R" + str(r)
            out.append(row)
        return out
