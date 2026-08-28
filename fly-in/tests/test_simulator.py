"""Tests for the Simulator (M2): single-path, capacity-respecting runs."""

from __future__ import annotations

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
