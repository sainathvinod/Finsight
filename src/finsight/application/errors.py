# Typed application errors surfaced to the UI. The UI maps these to restrained messages; it never
# shows stack traces (diagnostic detail stays in logs / the `detail` attribute).
from __future__ import annotations
from typing import Any, Optional


class FinsightAppError(Exception):
    """Base for user-surfaceable application errors."""

    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class MissingFileError(FinsightAppError):
    """A required source file is missing or unreadable."""


class UnsupportedWorkbookError(FinsightAppError):
    """A source workbook could not be parsed."""


class ValidationRejectedError(FinsightAppError):
    """Extraction/validation rejected the dataset; it cannot be verified."""


class VerificationRequiredError(FinsightAppError):
    """An action (e.g. analysis) requires prior human verification."""


class InvalidTransitionError(FinsightAppError):
    """The requested step is not valid for the review's current state."""


class DuplicateReviewError(FinsightAppError):
    """A review with the requested identifier already exists."""


class ReviewNotFoundError(FinsightAppError):
    """No persisted review exists for the requested identifier."""


class PersistenceError(FinsightAppError):
    """A persistence operation failed; the review is left in its last consistent state."""


class ExportError(FinsightAppError):
    """Producing or writing the export failed."""


class InvalidCorrectionError(FinsightAppError):
    """A user correction to an extracted value is not valid (unknown field, non-numeric amount, or the
    review is no longer in a state where corrections are allowed)."""
