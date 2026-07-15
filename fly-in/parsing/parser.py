"""Parser: read a map file into a :class:`Network` and drone count.

The parser is strict: any syntax or structural error raises a
:class:`ParseError` carrying the offending line number and cause.
"""

from __future__ import annotations

from models.network import Network
from models.zone import ZoneFactory
from parsing.errors import ParseError


class Parser:
    """Read and validate a Fly-in map file."""

    def __init__(self) -> None:
        """Create a parser with a fresh zone factory."""
        self.factory = ZoneFactory()

    def parse_file(self, path: str) -> tuple[Network, int]:
        """Parse a map file at ``path``.

        Args:
            path: Filesystem path to the map file.

        Returns:
            A tuple of the built network and the number of drones.

        Raises:
            ParseError: If the file cannot be read or is malformed.
        """
        try:
            with open(path, encoding="utf-8") as handle:
                lines = handle.readlines()
        except OSError as err:
            raise ParseError(f"cannot read file: {err}") from err
        return self.parse_lines(lines)

    def parse_lines(self, lines: list[str]) -> tuple[Network, int]:
        """Parse already-read lines into a network and drone count.

        Args:
            lines: The raw lines of the map file.

        Returns:
            A tuple of the built network and the number of drones.

        Raises:
            ParseError: On any syntax or structural error.
        """
        # TODO: implement the grammar:
        #   1. first meaningful line: ``nb_drones: <positive int>``
        #   2. ``start_hub:`` / ``end_hub:`` / ``hub:`` zone lines
        #   3. ``connection: a-b [metadata]`` lines
        #   4. ``#`` comments and blank lines ignored
        # Validate exactly one start and one end, unique names, valid
        # coords/metadata, no duplicate/self connections. Raise
        # ParseError(message, line_number) on the first problem.
        raise NotImplementedError

    def _parse_metadata(self, raw: str, line_number: int) -> dict[str, str]:
        """Parse a ``[key=value ...]`` metadata block into a dict.

        Args:
            raw: The bracketed metadata substring (without brackets).
            line_number: Line number for error reporting.

        Returns:
            A mapping of metadata keys to string values.

        Raises:
            ParseError: If the block is syntactically invalid.
        """
        # TODO: split on whitespace, then on '=', validating each tag.
        raise NotImplementedError
