"""Tests for the Network graph (M1)."""

from __future__ import annotations

import pytest

from models.network import Network
from models.zone import NormalZone
from parsing.errors import ParseError


def _small_network() -> Network:
    """Build a 3-zone linear network: start - mid - end."""
    network = Network()
    network.add_zone(NormalZone("start", 0, 0, unlimited=True), is_start=True)
    network.add_zone(NormalZone("mid", 1, 0))
    network.add_zone(NormalZone("end", 2, 0, unlimited=True), is_end=True)
    network.add_connection("start", "mid")
    network.add_connection("mid", "end")
    return network


def test_neighbors_and_endpoints() -> None:
    """neighbors() returns the incident connections for each zone."""
    network = _small_network()
    assert network.start.name == "start"
    assert network.end.name == "end"
    assert len(network.neighbors(network.zones["mid"])) == 2
    assert len(network.neighbors(network.start)) == 1


def test_duplicate_zone_name_rejected() -> None:
    """Adding two zones with the same name raises a ParseError."""
    network = Network()
    network.add_zone(NormalZone("a", 0, 0), is_start=True)
    with pytest.raises(ParseError):
        network.add_zone(NormalZone("a", 1, 1), is_end=True)


def test_second_start_rejected() -> None:
    """Adding a second start zone raises a ParseError."""
    network = Network()
    network.add_zone(NormalZone("a", 0, 0), is_start=True)
    with pytest.raises(ParseError):
        network.add_zone(NormalZone("b", 1, 1), is_start=True)


def test_connection_to_unknown_zone_rejected() -> None:
    """A connection referencing an unknown zone raises a ParseError."""
    network = Network()
    network.add_zone(NormalZone("a", 0, 0))
    with pytest.raises(ParseError):
        network.add_connection("a", "ghost")


def test_self_loop_rejected() -> None:
    """A connection from a zone to itself raises a ParseError."""
    network = Network()
    network.add_zone(NormalZone("a", 0, 0))
    with pytest.raises(ParseError):
        network.add_connection("a", "a")


def test_duplicate_connection_rejected_both_directions() -> None:
    """`a-b` and `b-a` are treated as the same duplicate connection."""
    network = Network()
    network.add_zone(NormalZone("a", 0, 0))
    network.add_zone(NormalZone("b", 1, 0))
    network.add_connection("a", "b")
    with pytest.raises(ParseError):
        network.add_connection("b", "a")


def test_connection_between_works_both_ways() -> None:
    """The same connection is found from either end."""
    network = _small_network()
    start, mid = network.start, network.zones["mid"]

    connection = network.connection_between(start, mid)
    assert connection is network.connection_between(mid, start)
    assert connection.name == "start-mid"


def test_connection_between_unlinked_zones_raises() -> None:
    """Asking for a connection that doesn't exist raises ValueError."""
    network = _small_network()
    with pytest.raises(ValueError):
        network.connection_between(network.start, network.end)
