# Verifies: R1-M5 — single-instance advisory lock (ADR-013 §3). One process may hold the lock for a
# database; a second acquisition is refused (so the caller never opens the DB); releasing frees it;
# a crashed instance's stale lock file does not block a fresh start. Never touches the database.
import os

import pytest

from finsight.infrastructure.single_instance import SingleInstanceLock

pytestmark = pytest.mark.ui


def _lock(tmp_path):
    return SingleInstanceLock(os.path.join(str(tmp_path), "finsight.db.lock"))


def test_first_acquires_second_refused(tmp_path):
    a = _lock(tmp_path); b = _lock(tmp_path)
    assert a.acquire() is True and a.held
    assert b.acquire() is False and not b.held      # second instance refused (must not open the DB)
    a.release()


def test_release_frees_the_lock(tmp_path):
    a = _lock(tmp_path); b = _lock(tmp_path)
    assert a.acquire()
    a.release()
    assert not a.held
    assert b.acquire() is True                       # freed -> another instance may start
    b.release()


def test_stale_lock_file_does_not_block(tmp_path):
    # A crashed instance leaves the lock FILE but no live OS lock; a fresh start must succeed.
    path = os.path.join(str(tmp_path), "finsight.db.lock")
    with open(path, "w") as fh:
        fh.write("99999")                            # stale pid marker, no held OS lock
    a = SingleInstanceLock(path)
    assert a.acquire() is True                       # not blocked by the stale file
    a.release()


def test_context_manager_holds_then_releases(tmp_path):
    path = os.path.join(str(tmp_path), "finsight.db.lock")
    with SingleInstanceLock(path) as held:
        assert held.held
        assert SingleInstanceLock(path).acquire() is False   # contended while inside the block
    assert SingleInstanceLock(path).acquire() is True        # released on exit


def test_lock_never_creates_or_touches_the_database(tmp_path):
    db = os.path.join(str(tmp_path), "finsight.db")
    lock = SingleInstanceLock(db + ".lock")
    assert lock.acquire()
    assert not os.path.exists(db)                    # only the .lock sidecar is created, never the DB
    lock.release()
