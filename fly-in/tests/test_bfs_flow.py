"""Tests for the baseline BFS path finder (M2)."""

from __future__ import annotations

import pytest

from parsing.errors import NoPathError
from parsing.parser import Parser
from pathfinding.bfs_flow import BFSFlowFinder


def test_finds_shortest_path_on_example_map() -> None:
    """The finder returns one start -> end path through the network."""
    network, _ = Parser().parse_file("maps/example.map")
    paths = BFSFlowFinder().find_paths(network)

    assert len(paths) == 1
    path = paths[0]
    assert path[0] is network.start
    assert path[-1] is network.end
    assert path[0].name == "hub"
    assert path[-1].name == "goal"


def test_blocked_zones_are_never_used() -> None:
    """A blocked zone must not appear on any returned path."""
    network, _ = Parser().parse_file("maps/example.map")
    path = BFSFlowFinder().find_paths(network)[0]
    assert all(zone.name != "obstacleX" for zone in path)


def test_no_path_raises() -> None:
    """An unreachable end zone raises NoPathError."""
    network, _ = Parser().parse_lines(
        [
            "nb_drones: 1\n",
            "start_hub: a 0 0\n",
            "end_hub: b 1 0\n",
            "hub: island 5 5\n",
        ]
    )
    with pytest.raises(NoPathError):
        BFSFlowFinder().find_paths(network)
