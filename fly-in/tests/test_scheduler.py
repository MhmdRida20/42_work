"""Tests for the Scheduler (M2)."""

from __future__ import annotations

import pytest

from parsing.errors import NoPathError
from parsing.parser import Parser
from pathfinding.bfs_flow import BFSFlowFinder
from simulation.scheduler import Scheduler


def test_assign_puts_every_drone_on_the_path() -> None:
    """Every requested drone gets the single path, starting at start."""
    network, nb_drones = Parser().parse_file("maps/easy_linear.map")
    paths = BFSFlowFinder().find_paths(network)

    drones = Scheduler().assign(network, paths, nb_drones)

    assert len(drones) == nb_drones
    assert {d.id for d in drones} == {1, 2}
    assert all(d.path == paths[0] for d in drones)
    assert all(d.position is network.start for d in drones)


def test_assign_hands_out_one_route_per_drone() -> None:
    """With several paths, drone i gets paths[i % len(paths)]."""
    network, _ = Parser().parse_file("maps/example.map")
    zones = network.zones
    first = [network.start, zones["roof1"], zones["roof2"], network.end]
    second = [
        network.start, zones["corridorA"], zones["tunnelB"], network.end
    ]

    drones = Scheduler().assign(network, [first, second], 3)

    assert [d.path for d in drones] == [first, second, first]


def test_assign_rejects_empty_paths() -> None:
    """Assigning with no candidate paths raises NoPathError."""
    network, _ = Parser().parse_file("maps/easy_linear.map")
    with pytest.raises(NoPathError):
        Scheduler().assign(network, [], 2)


def test_path_cost_sums_entry_costs() -> None:
    """path_cost sums entry_cost over every zone after the start."""
    network, _ = Parser().parse_file("maps/example.map")
    path = BFSFlowFinder().find_paths(network)[0]

    expected = sum(zone.entry_cost for zone in path[1:])
    assert Scheduler.path_cost(path) == expected


def test_path_cost_skips_planned_waits() -> None:
    """Waiting twice in hub costs nothing; roof1 costs 2, roof2 1."""
    network, _ = Parser().parse_file("maps/example.map")
    hub, roof1, roof2 = (
        network.zones[name] for name in ("hub", "roof1", "roof2")
    )
    path = [hub, hub, hub, roof1, roof2, network.end]

    assert Scheduler.path_cost(path) == 4
