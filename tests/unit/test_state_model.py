# Verifies: one authoritative review-state ordering; rank/reached for every state (incl VALIDATED
# compatibility); nine-step UI gating derives from it correctly.
import unittest
from finsight.domain.review_cycle import CycleState, STATE_ORDER, state_rank, has_reached
from finsight.delivery.desktop.views.workflow_meta import gates


class TestStateModel(unittest.TestCase):
    def test_single_authoritative_order(self):
        self.assertEqual([s.value for s in STATE_ORDER],
                         ["Created", "Intake", "Processed", "Verified", "Analyzed", "Summarized", "Exported"])

    def test_rank_defined_for_every_state(self):
        for s in CycleState:
            self.assertIsInstance(state_rank(s), int)   # includes VALIDATED (must not raise)
        # VALIDATED is a reserved/compat state ranked at INTAKE
        self.assertEqual(state_rank(CycleState.VALIDATED), state_rank(CycleState.INTAKE))

    def test_reached(self):
        self.assertTrue(has_reached(CycleState.ANALYZED, CycleState.VERIFIED))
        self.assertFalse(has_reached(CycleState.PROCESSED, CycleState.VERIFIED))
        self.assertTrue(has_reached("Exported", "Created"))       # accepts string values too

    def test_nine_step_gating_maps(self):
        _d, enabled, current = gates(None)          # no review -> only Setup
        self.assertEqual(current, 0)
        self.assertTrue(enabled[0])
        self.assertFalse(enabled[1])

        _d, _e, current = gates("Verified")          # Analysis is the current action
        self.assertEqual(current, 5)

        done, _e, current = gates("Exported")        # everything complete
        self.assertTrue(all(done))
        self.assertEqual(current, -1)


if __name__ == "__main__":
    unittest.main()
