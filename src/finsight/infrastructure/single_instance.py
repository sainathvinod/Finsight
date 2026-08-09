# Implements:
#   Feature: F-14-02 — Never Lose Work; F-14-04 — Data Protection (anchors, R1)
#   ADRs: ADR-013 §3/§5 (single-user / single-instance desktop scope); ADR-004 (single-writer SQLite)
#
# Product purpose:
#   An advisory single-instance lock acquired at startup. Only one FinSight process may use a given
#   database at a time; a second instance targeting the same DB is refused with a clear, non-destructive
#   message and does NOT open or modify the database (protecting the single-writer SQLite store).
#
# Trust / lifecycle constraints:
#   - Advisory, best-effort OS file lock (fcntl on POSIX, msvcrt on Windows) — scoped to the single-user
#     assumption (ADR-013), not a distributed/multi-writer guarantee.
#   - STALE-LOCK RECOVERY is automatic: an OS advisory lock is released when the holding process dies,
#     so a lock file left by a crashed instance does not block a fresh start (no manual PID reaping).
#   - Never deletes or truncates the DATABASE; only its own sidecar lock file. Independent of Ollama.
from __future__ import annotations
import os


def _try_lock(fh) -> bool:
    try:
        import fcntl
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            return False
    except ImportError:                      # non-POSIX (Windows)
        try:
            import msvcrt
            # msvcrt.locking locks bytes from the CURRENT file position. The handle is opened in
            # append mode, so without this seek the locked byte would be wherever the previous
            # holder's PID happened to end — and a second instance, seeking to a different end,
            # would lock a different byte and wrongly believe it was alone. Byte 0 is fixed, so
            # contention is detected the same way on every run (ADR-013 §3, single-writer store).
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False


def _unlock(fh) -> None:
    try:
        import fcntl
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
    except ImportError:
        try:
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass


class SingleInstanceLock:
    """Best-effort advisory lock on a sidecar lock file next to the database (ADR-013 §3)."""

    def __init__(self, lock_path: str):
        self._path = lock_path
        self._fh = None

    def acquire(self) -> bool:
        """Try to become the single instance. True if acquired; False if another live instance holds it
        (the caller must then refuse to open the database). Does not raise on contention."""
        parent = os.path.dirname(self._path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        fh = open(self._path, "a+")          # no truncation: never clobber a live holder's marker
        if not _try_lock(fh):
            fh.close()
            return False
        try:                                  # we own it now — record our pid for diagnostics
            fh.seek(0)
            fh.truncate()
            fh.write(str(os.getpid()))
            fh.flush()
        except OSError:
            pass
        self._fh = fh
        return True

    def release(self) -> None:
        if self._fh is not None:
            _unlock(self._fh)
            self._fh.close()
            self._fh = None

    @property
    def held(self) -> bool:
        return self._fh is not None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc):
        self.release()
