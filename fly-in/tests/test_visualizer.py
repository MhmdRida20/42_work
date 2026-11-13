"""Tests for VisualizerGroup: several visualizers following one run."""

from __future__ import annotations

from models.network import Network
from parsing.parser import Parser
from pathfinding.space_time import SpaceTimeFinder
from simulation.scheduler import Scheduler
from simulation.simulator import Simulator
from visualization.frames import Recorder
from visualization.visualizer import Visualizer, VisualizerGroup


class _Log(Visualizer):
    """A visualizer that notes each call it gets in a shared list."""

    def __init__(self, name: str, calls: list[str]) -> None:
        """Note each call as ``name: call`` in ``calls``."""
        self.name = name
        self.calls = calls

    def show_network(self, network: Network) -> None:
        """Note the call."""
        self.calls.append(f"{self.name}: network")

    def show_turn(self, turn_number: int, line: str, network: Network) -> None:
        """Note the call and its turn."""
        self.calls.append(f"{self.name}: turn {turn_number}")

    def show_summary(self, metrics: dict[str, float]) -> None:
        """Note the call."""
        self.calls.append(f"{self.name}: summary")


def _follow(map_path: str, visualizer: Visualizer) -> None:
    """Plan and run ``map_path``, with ``visualizer`` following it."""
    network, nb_drones = Parser().parse_file(map_path)
    routes = SpaceTimeFinder(nb_drones).find_paths(network)
    drones = Scheduler().assign(network, routes, nb_drones)
    simulator = Simulator(network, drones)
    visualizer.show_network(network)
    simulator.run(visualizer)
    visualizer.show_summary(simulator.metrics())


def test_each_call_goes_to_every_visualizer_in_order() -> None:
    """The first visualizer, then the second, for every call.

    The order matters: in main.py the terminal prints its summary
    before the window opens and waits.
    """
    calls: list[str] = []
    group = VisualizerGroup([_Log("a", calls), _Log("b", calls)])
    _follow("maps/edge_start_to_end.map", group)
    assert calls == [
        "a: network",
        "b: network",
        "a: turn 1",
        "b: turn 1",
        "a: turn 2",
        "b: turn 2",
        "a: turn 3",
        "b: turn 3",
        "a: summary",
        "b: summary",
    ]


def test_a_group_changes_nothing_in_what_each_one_sees() -> None:
    """Two Recorders in a group record exactly what one records alone."""
    alone = Recorder()
    _follow("maps/example.map", alone)
    first, second = Recorder(), Recorder()
    _follow("maps/example.map", VisualizerGroup([first, second]))

    assert first.frames == second.frames == alone.frames
    assert first.metrics == second.metrics == alone.metrics
