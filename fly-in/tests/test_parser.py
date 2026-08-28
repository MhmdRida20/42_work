"""Tests for the Parser (M1): the example map and bad-map edge cases."""

from __future__ import annotations

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
