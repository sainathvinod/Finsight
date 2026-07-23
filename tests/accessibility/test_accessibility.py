# Verifies: NFR-025, NFR-026 (AC-13): color-independent severity; keyboard-operable 9-step wizard
import unittest
from finsight.delivery.wizard import Wizard, SeverityView, FindingsView, STEPS

class TestAccessibility(unittest.TestCase):
    def test_nine_steps_keyboard_traversable(self):
        w = Wizard()
        self.assertEqual(w.total, 9)
        self.assertTrue(w.label().startswith("Step 1 of 9"))
        # forward traversal by keyboard reaches step 9
        for _ in range(8):
            w.on_key("Right")
        self.assertTrue(w.label().startswith("Step 9 of 9"))
        # backward + digit jump
        w.on_key("Left"); self.assertTrue(w.label().startswith("Step 8 of 9"))
        self.assertTrue(w.on_key("1").startswith("Step 1 of 9"))
    def test_severity_color_independent(self):
        marks = {s: SeverityView.render(s) for s in ["Critical", "High", "Medium", "Low"]}
        for label, rendered in marks.items():
            self.assertIn(label, rendered)                 # text label present (not color-only)
            self.assertTrue(any(ch in rendered for ch in "[]!=.Xx"))  # shape/marker present
            self.assertNotIn("\x1b[", rendered)           # no ANSI color escape codes
        self.assertEqual(len(set(marks.values())), 4)      # each severity distinguishable by shape alone

    def test_findings_view_uses_query_port(self):
        class FakeQ:
            def list(self, cid):
                return [{"severity": "High", "account": "6100", "finding_type": "over-budget",
                         "evidence": {"variance": "3000.00", "variance_pct": "30.00"},
                         "source_refs": ["GED!6100"]}]
        lines = FindingsView(FakeQ()).render("c")
        self.assertEqual(len(lines), 1)
        self.assertIn("High", lines[0]); self.assertIn("6100", lines[0]); self.assertIn("source", lines[0])

if __name__ == "__main__":
    unittest.main()
