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
            # utf-8-sig also reads a file saved with a byte-order mark.
            with open(path, encoding="utf-8-sig") as handle:
                lines = handle.readlines()
        except (OSError, UnicodeError) as err:
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
        network = Network()
        nb_drones: int | None = None

        for line_number, raw_line in enumerate(lines, start=1):
            line = self._strip_comment(raw_line).strip()
            if not line:
                continue

            try:
                keyword, sep, rest = line.partition(":")
                if sep != ":":
                    raise ParseError(f"invalid line syntax: {line!r}")
                keyword = keyword.strip()
                rest = rest.strip()

                if nb_drones is None and keyword != "nb_drones":
                    raise ParseError(
                        "the first line must declare nb_drones"
                    )

                if keyword == "nb_drones":
                    if nb_drones is not None:
                        raise ParseError("duplicate nb_drones declaration")
                    nb_drones = self._parse_positive_int(
                        rest, "nb_drones", line_number
                    )
                elif keyword in ("start_hub", "end_hub", "hub"):
                    self._parse_zone_line(
                        network, keyword, rest, line_number
                    )
                elif keyword == "connection":
                    self._parse_connection_line(network, rest, line_number)
                else:
                    raise ParseError(f"unknown line type: {keyword!r}")
            except ParseError as err:
                if err.line_number is None:
                    raise ParseError(str(err), line_number) from err
                raise

        if nb_drones is None:
            raise ParseError("missing nb_drones declaration")
        try:
            network.start
            network.end
        except ValueError as err:
            raise ParseError(str(err)) from err

        return network, nb_drones

    def _parse_zone_line(
        self,
        network: Network,
        keyword: str,
        rest: str,
        line_number: int,
    ) -> None:
        """Parse a ``start_hub:``/``end_hub:``/``hub:`` line.

        Args:
            network: The network being built; the zone is added to it.
            keyword: One of ``start_hub``, ``end_hub``, ``hub``.
            rest: The line content after the ``<keyword>:`` prefix.
            line_number: Line number for error reporting.

        Raises:
            ParseError: On malformed fields or metadata.
        """
        before, metadata_raw = self._split_metadata_block(rest, line_number)
        tokens = before.split()
        if len(tokens) != 3:
            raise ParseError(
                f"expected '<name> <x> <y>', got {before!r}", line_number
            )
        name, x_str, y_str = tokens
        if "-" in name:
            raise ParseError(
                f"zone name {name!r} must not contain dashes", line_number
            )
        try:
            x = self._strict_int(x_str)
            y = self._strict_int(y_str)
        except ValueError:
            raise ParseError(
                f"zone coordinates must be integers, got "
                f"{x_str!r} {y_str!r}",
                line_number,
            ) from None

        metadata = self._parse_metadata(metadata_raw, line_number)
        allowed = {"zone", "color", "max_drones"}
        unknown = set(metadata) - allowed
        if unknown:
            raise ParseError(
                f"unknown zone metadata key(s): {', '.join(sorted(unknown))}",
                line_number,
            )

        zone_type = metadata.get("zone", "normal")
        color = metadata.get("color")
        max_drones = self._parse_positive_int(
            metadata.get("max_drones", "1"), "max_drones", line_number
        )

        is_start = keyword == "start_hub"
        is_end = keyword == "end_hub"
        if zone_type == "blocked" and (is_start or is_end):
            raise ParseError(
                "start and end zones cannot be blocked", line_number
            )
        zone = self.factory.build(
            zone_type, name, x, y, color, max_drones,
            unlimited=(is_start or is_end),
        )
        try:
            network.add_zone(zone, is_start=is_start, is_end=is_end)
        except ParseError as err:
            raise ParseError(str(err), line_number) from err

    def _parse_connection_line(
        self,
        network: Network,
        rest: str,
        line_number: int,
    ) -> None:
        """Parse a ``connection: a-b [metadata]`` line.

        Args:
            network: The network being built; the edge is added to it.
            rest: The line content after the ``connection:`` prefix.
            line_number: Line number for error reporting.

        Raises:
            ParseError: On malformed fields or metadata.
        """
        before, metadata_raw = self._split_metadata_block(rest, line_number)
        name_a, dash, name_b = before.partition("-")
        name_a = name_a.strip()
        name_b = name_b.strip()
        if dash != "-" or not name_a or not name_b:
            raise ParseError(
                f"invalid connection syntax: {before!r}", line_number
            )

        metadata = self._parse_metadata(metadata_raw, line_number)
        allowed = {"max_link_capacity"}
        unknown = set(metadata) - allowed
        if unknown:
            raise ParseError(
                "unknown connection metadata key(s): "
                f"{', '.join(sorted(unknown))}",
                line_number,
            )

        max_link_capacity = self._parse_positive_int(
            metadata.get("max_link_capacity", "1"),
            "max_link_capacity",
            line_number,
        )
        try:
            network.add_connection(name_a, name_b, max_link_capacity)
        except ParseError as err:
            raise ParseError(str(err), line_number) from err

    def _split_metadata_block(
        self,
        rest: str,
        line_number: int,
    ) -> tuple[str, str]:
        """Split ``<fields> [key=value ...]`` into fields and raw metadata.

        Args:
            rest: The line content to split.
            line_number: Line number for error reporting.

        Returns:
            A tuple of (fields substring, raw metadata substring). The
            metadata substring is empty if no bracket block is present.

        Raises:
            ParseError: If the bracket block is malformed.
        """
        if "[" not in rest and "]" not in rest:
            return rest.strip(), ""
        if rest.count("[") != 1 or rest.count("]") != 1:
            raise ParseError(
                f"malformed metadata block: {rest!r}", line_number
            )
        open_idx = rest.index("[")
        close_idx = rest.index("]")
        if close_idx < open_idx:
            raise ParseError(
                f"malformed metadata block: {rest!r}", line_number
            )
        if rest[close_idx + 1:].strip():
            raise ParseError(
                f"unexpected text after metadata block: {rest!r}", line_number
            )
        return rest[:open_idx].strip(), rest[open_idx + 1:close_idx].strip()

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
        metadata: dict[str, str] = {}
        for token in raw.split():
            key, sep, value = token.partition("=")
            if sep != "=" or not key or not value:
                raise ParseError(
                    f"invalid metadata tag: {token!r}", line_number
                )
            if key in metadata:
                raise ParseError(
                    f"duplicate metadata key: {key!r}", line_number
                )
            metadata[key] = value
        return metadata

    def _parse_positive_int(
        self,
        value_str: str,
        field_name: str,
        line_number: int,
    ) -> int:
        """Parse and validate a positive integer field.

        Args:
            value_str: The raw string value to parse.
            field_name: Name used in the error message (e.g. ``nb_drones``).
            line_number: Line number for error reporting.

        Returns:
            The parsed positive integer.

        Raises:
            ParseError: If the value is not a positive integer.
        """
        try:
            value = self._strict_int(value_str)
        except ValueError:
            raise ParseError(
                f"{field_name} must be a positive integer, got {value_str!r}",
                line_number,
            ) from None
        if value <= 0:
            raise ParseError(
                f"{field_name} must be a positive integer, got {value}",
                line_number,
            )
        return value

    @staticmethod
    def _strict_int(text: str) -> int:
        """Convert ``text`` to an int written with plain digits only.

        Python's ``int()`` also accepts ``1_0``, ``+3`` and non-ASCII
        digits; a map number must look like ``42`` or ``-42``.

        Args:
            text: The raw number, without surrounding spaces.

        Returns:
            The integer value.

        Raises:
            ValueError: If ``text`` is not an optional ``-`` followed by
                the digits 0-9.
        """
        digits = text[1:] if text.startswith("-") else text
        if not (digits.isascii() and digits.isdigit()):
            raise ValueError(f"not a plain integer: {text!r}")
        return int(text)

    @staticmethod
    def _strip_comment(raw_line: str) -> str:
        """Return ``raw_line`` with any trailing ``#`` comment removed.

        Args:
            raw_line: A single raw line from the map file.

        Returns:
            The line with the comment (if any) stripped off.
        """
        idx = raw_line.find("#")
        if idx == -1:
            return raw_line
        return raw_line[:idx]
