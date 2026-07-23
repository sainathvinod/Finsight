# Runs a blocking application call off the UI thread so the event loop stays responsive.
# Result/error signals are delivered back on the UI thread (queued Qt connections).
from __future__ import annotations
from typing import Callable
from PySide6.QtCore import QObject, QRunnable, Signal, Slot, QThreadPool


class _Signals(QObject):
    result = Signal(object)
    error = Signal(object)


class _Task(QRunnable):
    def __init__(self, fn: Callable):
        super().__init__()
        self._fn = fn
        self.signals = _Signals()

    @Slot()
    def run(self):
        try:
            value = self._fn()
        except Exception as exc:  # delivered to on_error on the UI thread
            self.signals.error.emit(exc)
        else:
            self.signals.result.emit(value)


# Keep running tasks referenced so neither the QRunnable nor its signals object is garbage-collected
# before the queued cross-thread signal is delivered (a destroyed sender cancels pending events).
_ACTIVE = set()


def run_async(fn: Callable, on_result: Callable, on_error: Callable, pool: QThreadPool = None) -> _Task:
    """Execute fn() on a worker thread; call on_result(value) or on_error(exc) on the UI thread."""
    task = _Task(fn)
    _ACTIVE.add(task)

    def _cleanup(*_args):
        _ACTIVE.discard(task)

    task.signals.result.connect(on_result)
    task.signals.error.connect(on_error)
    task.signals.result.connect(_cleanup)
    task.signals.error.connect(_cleanup)
    (pool or QThreadPool.globalInstance()).start(task)
    return task
