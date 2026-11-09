"""Tests for the Parser (M1): the example map and bad-map edge cases."""

from __future__ import annotations

from pathlib import Path

import pytest

from parsing.errors import ParseError
from parsing.parser import Parser


def test_parses_example_map() -> None:
    """The subject's example map parses into a consistent network."""
    network, nb_drones = Parser().parse_file("maps/example.map")

    assert nb_drones == 5
    assert network.start.name == "hub"
    assert network.end.name == "goal"
    assert network.start.unlimited is True
    assert network.end.unlimited is True
    assert network.zones["roof1"].entry_cost == 2  # restricted
    assert network.zones["corridorA"].max_drones == 2
    assert not network.zones["obstacleX"].is_accessible  # blocked

    connection_names = {
        conn.name
        for conns in network.adjacency.values()
        for conn in conns
    }
    assert "corridorA-tunnelB" in connection_names


def test_missing_start_hub_raises() -> None:
    """A map without a start_hub raises a ParseError."""
    with pytest.raises(ParseError):
        Parser().parse_file("maps/bad_missing_start.map")


def test_duplicate_connection_raises() -> None:
    """Declaring a-b and b-a raises a ParseError."""
    with pytest.raises(ParseError):
        Parser().parse_file("maps/bad_duplicate_connection.map")


def test_unknown_zone_type_raises() -> None:
    """An unrecognized zone= type raises a ParseError."""
    with pytest.raises(ParseError):
        Parser().parse_file("maps/bad_zone_type.map")


def test_zero_capacity_raises() -> None:
    """max_drones=0 is not a positive integer and raises a ParseError."""
    with pytest.raises(ParseError):
        Parser().parse_file("maps/bad_capacity_zero.map")


def test_self_loop_connection_raises() -> None:
    """A connection from a zone to itself raises a ParseError."""
    with pytest.raises(ParseError):
        Parser().parse_file("maps/bad_self_loop.map")


def test_nb_drones_must_be_first_line() -> None:
    """nb_drones declared after other lines raises a ParseError."""
    with pytest.raises(ParseError):
        Parser().parse_file("maps/bad_nb_drones_not_first.map")


def test_error_message_includes_line_number() -> None:
    """Parse errors are tagged with the offending line number."""
    with pytest.raises(ParseError, match="line 5") as exc_info:
        Parser().parse_file("maps/bad_zone_type.map")
    assert exc_info.value.line_number == 5


def test_comments_and_blank_lines_ignored() -> None:
    """`#` comments and blank lines don't affect parsing."""
    network, nb_drones = Parser().parse_lines(
        [
            "# a leading comment\n",
            "\n",
            "nb_drones: 1\n",
            "start_hub: a 0 0  # inline comment\n",
            "end_hub: b 1 0\n",
            "connection: a-b\n",
        ]
    )
    assert nb_drones == 1
    assert network.start.name == "a"
    assert network.end.name == "b"


def test_non_utf8_file_raises_parse_error(tmp_path: Path) -> None:
    """A file that isn't UTF-8 fails cleanly, without a traceback."""
    map_file = tmp_path / "latin1.map"
    map_file.write_bytes("# caf\xe9\nnb_drones: 1\n".encode("latin-1"))

    with pytest.raises(ParseError, match="cannot read file"):
        Parser().parse_file(str(map_file))


@pytest.mark.parametrize("value", ["1_0", "+3", "٣", "3.0"])
def test_nb_drones_needs_plain_digits(value: str) -> None:
    """int() accepts 1_0, +3 and Arabic digits; a map number may not."""
    with pytest.raises(ParseError, match="line 1"):
        Parser().parse_lines(
            [
                f"nb_drones: {value}\n",
                "start_hub: a 0 0\n",
                "end_hub: b 1 0\n",
                "connection: a-b\n",
            ]
        )


def test_coordinates_need_plain_digits() -> None:
    """A coordinate written 1_0 is rejected like any other non-integer."""
    with pytest.raises(ParseError, match="coordinates must be integers"):
        Parser().parse_lines(
            [
                "nb_drones: 1\n",
                "start_hub: a 1_0 0\n",
                "end_hub: b 1 0\n",
                "connection: a-b\n",
            ]
        )


def test_negative_coordinates_are_integers() -> None:
    """Coordinates can be negative: -2 is still an integer."""
    network, _ = Parser().parse_lines(
        [
            "nb_drones: 1\n",
            "start_hub: a -2 -3\n",
            "end_hub: b 1 0\n",
            "connection: a-b\n",
        ]
    )
    assert (network.start.x, network.start.y) == (-2, -3)


def test_file_with_byte_order_mark_parses(tmp_path: Path) -> None:
    """A UTF-8 file saved with a byte-order mark reads normally."""
    map_file = tmp_path / "bom.map"
    map_file.write_bytes(
        b"\xef\xbb\xbfnb_drones: 1\nstart_hub: a 0 0\nend_hub: b 1 0\n"
        b"connection: a-b\n"
    )

    _, nb_drones = Parser().parse_file(str(map_file))
    assert nb_drones == 1


def test_blocked_start_zone_raises() -> None:
    """Drones can't begin inside a blocked zone."""
    with pytest.raises(ParseError, match="line 2"):
        Parser().parse_lines(
            [
                "nb_drones: 1\n",
                "start_hub: a 0 0 [zone=blocked]\n",
                "end_hub: b 1 0\n",
                "connection: a-b\n",
            ]
        )


def test_blocked_end_zone_raises() -> None:
    """Drones can't be delivered into a blocked zone."""
    with pytest.raises(ParseError, match="line 3"):
        Parser().parse_lines(
            [
                "nb_drones: 1\n",
                "start_hub: a 0 0\n",
                "end_hub: b 1 0 [zone=blocked]\n",
                "connection: a-b\n",
            ]
        )
