# Implements: FR-070 (presentation), FR-074/082 (minimal), NFR-025, NFR-026, NFR-067, F-02-02
# Minimal 9-step wizard frame + color-independent finding render. Text-mode (shell-neutral);
# proves keyboard operability + non-color severity encoding without a GUI toolkit. No Ask Fin, no Explain This.
from __future__ import annotations
from typing import List

STEPS = ["Review Setup", "Data Upload", "Upload Validation", "Processing", "Verification",
         "Analysis", "Findings", "Leadership Summary", "Export"]  # the fixed 9 steps

# Severity encoded by SHAPE/marker + text label - never by color alone (NFR-025).
SEVERITY_MARK = {"Critical": "[XXX]", "High": "[!!]", "Medium": "[=]", "Low": "[.]"}

class Wizard:
    def __init__(self):
        self.index = 0
    @property
    def total(self) -> int:
        return len(STEPS)
    def label(self) -> str:
        return "Step %d of %d: %s" % (self.index + 1, self.total, STEPS[self.index])
    def next(self) -> str:
        if self.index < self.total - 1:
            self.index += 1
        return self.label()
    def prev(self) -> str:
        if self.index > 0:
            self.index -= 1
        return self.label()
    def goto(self, i: int) -> str:
        if 0 <= i < self.total:
            self.index = i
        return self.label()
    def on_key(self, key: str) -> str:
        # keyboard-operable primary workflow (NFR-026): arrows/enter/tab-style + digit jump
        if key in ("Right", "Down", "Enter", "n", "\t"):
            return self.next()
        if key in ("Left", "Up", "p"):
            return self.prev()
        if key.isdigit():
            return self.goto(int(key) - 1)
        return self.label()

class SeverityView:
    @staticmethod
    def render(severity_label: str) -> str:
        # returns shape-marker + text; contains NO ANSI color codes (color-independent)
        return SEVERITY_MARK.get(severity_label, "[?]") + " " + severity_label

class FindingsView:
    # Reads via the FindingsQueryPort only (command/query segregation; ADR-007).
    def __init__(self, query_port):
        self._q = query_port
    def render(self, cycle_id: str) -> List[str]:
        lines = []
        for f in self._q.list(cycle_id):
            ev = f.get("evidence", {})
            lines.append("%s  Account %s  %s  variance %s (%s%%)  [source: %s]" % (
                SeverityView.render(f["severity"]), f["account"], f["finding_type"],
                ev.get("variance", ""), ev.get("variance_pct", ""), ", ".join(f.get("source_refs", []))))
        return lines
