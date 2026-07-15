"""Custom exceptions for the Fly-in project.

Catching :class:`FlyInError` at the top level lets the program fail
with a clear message instead of an unhandled traceback (an unhandled
crash during review counts as non-functional).
"""

from __future__ import annotations


class FlyInError(Exception):
    """Base class for every Fly-in error."""


class ParseError(FlyInError):
    """Raised when the input map file is malformed."""

    def __init__(
        self,
        message: str,
        line_number: int | None = None,
    ) -> None:
        """Build a parse error, optionally tagged with a line number.

        Args:
            message: Human-readable cause of the error.
            line_number: 1-based line where the error occurred.
        """
        self.line_number = line_number
        if line_number is not None:
            message = f"line {line_number}: {message}"
        super().__init__(message)


class InvalidMapError(FlyInError):
    """Raised when a map parses but is logically invalid."""


class NoPathError(FlyInError):
    """Raised when no path exists from the start to the end zone."""
