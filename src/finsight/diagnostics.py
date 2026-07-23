# Application logging/diagnostics. Standard-library only (no new dependency). Framework-independent
# (no PySide6). This is operational logging for support/debugging — it is DISTINCT from the
# append-only domain audit trail (ADR-005), which records financial actions.
#
# Privacy: never log raw financial rows, workbook contents, or (future) AI prompts. Log event
# names, cycle_id, fingerprints/filenames, severities, and exception diagnostics only.
from __future__ import annotations
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_ROOT = "finsight"
_configured = False


def app_support_dir() -> str:
    """Per-user application-support directory (created if missing). macOS/Windows/Linux aware."""
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/FinSight")
    elif os.name == "nt":
        base = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "FinSight")
    else:
        base = os.path.join(os.path.expanduser("~/.local/share"), "FinSight")
    os.makedirs(base, exist_ok=True)
    return base


def configure_logging(level: str = None, console: bool = False, log_dir: str = None) -> None:
    """Initialize rotating file logging under the app-support dir. Idempotent, and never raises —
    a logging failure must not prevent FinSight from launching."""
    global _configured
    if _configured:
        return
    try:
        directory = log_dir or os.path.join(app_support_dir(), "logs")
        os.makedirs(directory, exist_ok=True)
        lvl = (level or os.environ.get("FINSIGHT_LOG_LEVEL", "INFO")).upper()
        logger = logging.getLogger(_ROOT)
        logger.setLevel(lvl)
        logger.propagate = False
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        handler = RotatingFileHandler(os.path.join(directory, "finsight.log"),
                                      maxBytes=1_000_000, backupCount=5, encoding="utf-8")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        if console or os.environ.get("FINSIGHT_LOG_CONSOLE"):
            stream = logging.StreamHandler()
            stream.setFormatter(fmt)
            logger.addHandler(stream)
        _configured = True
        logger.info("logging initialized dir=%s level=%s", directory, lvl)
    except Exception:  # logging must never block startup
        pass


def get_logger(name: str) -> logging.Logger:
    """A child logger under the `finsight` root (e.g. get_logger('workflow'))."""
    return logging.getLogger(_ROOT + "." + name)
