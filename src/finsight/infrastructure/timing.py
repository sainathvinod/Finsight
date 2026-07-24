# Implements: Phase 4C.6 — production timing primitives (infrastructure). Standard-library only,
# PySide6-free, no asyncio, no threading. The composition root injects these; tests inject fakes and
# never wait in real time.
from __future__ import annotations
import time


class RealSleeper:
    """Production Sleeper: performs a real (blocking) retry delay. Runs off the UI thread in delivery."""
    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


def monotonic() -> float:
    """Monotonic timing source for elapsed-duration measurement (never a wall clock)."""
    return time.perf_counter()
