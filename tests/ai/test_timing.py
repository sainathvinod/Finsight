# Verifies: Phase 4C.6 production timing primitives. No real sleeping in tests (the seam is patched).
import unittest
from unittest import mock

from finsight.infrastructure import timing


class TestTiming(unittest.TestCase):
    def test_real_sleeper_delegates_to_time_sleep(self):
        with mock.patch.object(timing.time, "sleep") as sleep:
            timing.RealSleeper().sleep(1.5)
        sleep.assert_called_once_with(1.5)                 # delegated, never actually waited

    def test_monotonic_returns_float(self):
        self.assertIsInstance(timing.monotonic(), float)

    def test_monotonic_non_decreasing(self):
        a = timing.monotonic()
        b = timing.monotonic()
        self.assertGreaterEqual(b, a)


if __name__ == "__main__":
    unittest.main()
