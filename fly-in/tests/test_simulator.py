"""Tests for the Simulator: capacity, restricted transit and guards."""

from __future__ import annotations

import pytest

from models.drone import Drone
from parsing.errors import SimulationError
from parsing.parser import Parser
from pathfinding.bfs_flow import BFSFlowFinder
from simulation.scheduler import Scheduler
from simulation.simulator import Simulator


def _run(map_path: str) -> tuple[list[str], int]:
    """Parse, plan, and simulate a map, returning (lines, nb_drones)."""
    network, nb_drones = Parser().parse_file(map_path)
    paths = BFSFlowFinder().find_paths(network)
    drones = Scheduler().assign(network, paths, nb_drones)
    lines = Simulator(network, drones).run()
    return lines, nb_drones


def _run_lines(lines: list[str]) -> list[str]:
    """Parse, plan, and simulate a map given as text lines."""
    network, nb_drones = Parser().parse_lines(lines)
    paths = BFSFlowFinder().find_paths(network)
    drones = Scheduler().assign(network, paths, nb_drones)
    return Simulator(network, drones).run()


def test_linear_map_matches_benchmark_target() -> None:
    """2 drones on the linear map finish in <= 6 turns (subject VII.7)."""
    lines, _ = _run("maps/easy_linear.map")
    assert len(lines) <= 6


def test_linear_map_exact_schedule() -> None:
    """The linear map's greedy convoy schedule is fully deterministic."""
    lines, _ = _run("maps/easy_linear.map")
    assert lines == [
        "D1-a",
        "D1-b D2-a",
        "D1-c D2-b",
        "D1-d D2-c",
        "D1-goal D2-d",
        "D2-goal",
    ]


def test_output_format_is_space_separated_drone_zone_tokens() -> None:
    """Every non-empty turn line matches the 'D<id>-<zone>' format."""
    lines, _ = _run("maps/easy_linear.map")
    for line in lines:
        for token in line.split():
            drone_part, _, zone_part = token.partition("-")
            assert drone_part.startswith("D")
            assert drone_part[1:].isdigit()
            assert zone_part


def test_never_exceeds_zone_capacity() -> None:
    """No intermediate zone ever holds more drones than max_drones."""
    network, nb_drones = Parser().parse_file("maps/easy_linear.map")
    paths = BFSFlowFinder().find_paths(network)
    drones = Scheduler().assign(network, paths, nb_drones)
    simulator = Simulator(network, drones)

    while not all(d.delivered for d in drones):
        simulator.step()
        for zone in network.zones.values():
            if zone.unlimited:
                continue
            assert len(zone.occupants) <= zone.max_drones


def test_all_drones_eventually_delivered() -> None:
    """Every drone reaches the end zone by the time run() returns."""
    network, nb_drones = Parser().parse_file("maps/easy_linear.map")
    paths = BFSFlowFinder().find_paths(network)
    drones = Scheduler().assign(network, paths, nb_drones)
    Simulator(network, drones).run()
    assert all(d.delivered for d in drones)


def test_restricted_move_takes_two_turns() -> None:
    """The drone is on the connection, then lands on the next turn."""
    lines = _run_lines(
        [
            "nb_drones: 1\n",
            "start_hub: s 0 0\n",
            "end_hub: e 2 0\n",
            "hub: r 1 0 [zone=restricted]\n",
            "connection: s-r\n",
            "connection: r-e\n",
        ]
    )
    assert lines == ["D1-s-r", "D1-r", "D1-e"]


def test_example_map_restricted_schedule() -> None:
    """BFS takes the roof1 route, one drone every two turns."""
    lines, _ = _run("maps/example.map")
    assert len(lines) == 12
    assert lines[:3] == ["D1-hub-roof1", "D1-roof1", "D1-roof2 D2-hub-roof1"]


def test_restricted_end_zone() -> None:
    """The end zone can be restricted too."""
    lines = _run_lines(
        [
            "nb_drones: 1\n",
            "start_hub: s 0 0\n",
            "end_hub: e 1 0 [zone=restricted]\n",
            "connection: s-e\n",
        ]
    )
    assert lines == ["D1-s-e", "D1-e"]


def test_two_restricted_zones_in_a_row() -> None:
    """Each restricted zone costs its own two turns."""
    lines = _run_lines(
        [
            "nb_drones: 1\n",
            "start_hub: s 0 0\n",
            "end_hub: e 3 0\n",
            "hub: r1 1 0 [zone=restricted]\n",
            "hub: r2 2 0 [zone=restricted]\n",
            "connection: s-r1\n",
            "connection: r1-r2\n",
            "connection: r2-e\n",
        ]
    )
    assert lines == ["D1-s-r1", "D1-r1", "D1-r1-r2", "D1-r2", "D1-e"]


def test_connection_keeps_its_map_name() -> None:
    """A connection written backwards prints as written in the map."""
    lines = _run_lines(
        [
            "nb_drones: 1\n",
            "start_hub: s 0 0\n",
            "end_hub: e 2 0\n",
            "hub: r 1 0 [zone=restricted]\n",
            "connection: r-s\n",
            "connection: r-e\n",
        ]
    )
    assert lines == ["D1-r-s", "D1-r", "D1-e"]


def test_two_drones_fly_together_with_capacity_two() -> None:
    """Zone and link capacity 2 let two drones share the flight."""
    lines = _run_lines(
        [
            "nb_drones: 2\n",
            "start_hub: s 0 0\n",
            "end_hub: e 2 0\n",
            "hub: r 1 0 [zone=restricted max_drones=2]\n",
            "connection: s-r [max_link_capacity=2]\n",
            "connection: r-e [max_link_capacity=2]\n",
        ]
    )
    assert lines == ["D1-s-r D2-s-r", "D1-r D2-r", "D1-e D2-e"]


def test_landing_drone_still_uses_the_link() -> None:
    """On a link of capacity 1, D2 waits until D1 has landed."""
    lines = _run_lines(
        [
            "nb_drones: 2\n",
            "start_hub: s 0 0\n",
            "end_hub: e 2 0\n",
            "hub: r 1 0 [zone=restricted max_drones=2]\n",
            "connection: s-r\n",
            "connection: r-e\n",
        ]
    )
    assert lines == ["D1-s-r", "D1-r", "D1-e D2-s-r", "D2-r", "D2-e"]


def test_take_off_reserves_the_destination() -> None:
    """The link has room, but D2 can't leave for a zone that is taken."""
    lines = _run_lines(
        [
            "nb_drones: 2\n",
            "start_hub: s 0 0\n",
            "end_hub: e 2 0\n",
            "hub: r 1 0 [zone=restricted]\n",
            "connection: s-r [max_link_capacity=2]\n",
            "connection: r-e\n",
        ]
    )
    assert lines == ["D1-s-r", "D1-r", "D1-e D2-s-r", "D2-r", "D2-e"]


def test_stuck_run_stops_with_an_error() -> None:
    """A run where nothing can move raises instead of looping forever."""
    network, _ = Parser().parse_file("maps/example.map")
    drone = Drone(1, network.start)
    network.start.occupants.append(drone)

    with pytest.raises(SimulationError):
        Simulator(network, [drone]).run()


def test_blocked_drone_cannot_overfill_its_zone() -> None:
    """D1 takes D2's zone, so a blocked D2 has nowhere to go back to."""
    network, _ = Parser().parse_lines(
        [
            "nb_drones: 2\n",
            "start_hub: s 0 0\n",
            "end_hub: e 3 0\n",
            "hub: a 1 0\n",
            "hub: b 2 0\n",
            "connection: s-a\n",
            "connection: a-b\n",
            "connection: b-e\n",
        ]
    )
    zone_a, zone_b = network.zones["a"], network.zones["b"]
    first = Drone(1, zone_a)
    first.path = [zone_a, zone_b, network.end]
    zone_a.occupants.append(first)
    second = Drone(2, zone_b)
    second.path = [zone_b, zone_a, network.start]
    zone_b.occupants.append(second)

    with pytest.raises(SimulationError):
        Simulator(network, [first, second]).step()
