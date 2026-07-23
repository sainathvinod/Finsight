# Implements: ADR-003 (Clock port). The wall-clock lives in infrastructure and is injected;
# the domain never reads the system clock. Used by the composition root for production runs.
from __future__ import annotations
import datetime


class SystemClock:
    def now(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
