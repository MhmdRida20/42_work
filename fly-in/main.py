"""Fly-in entry point: parse -> solve -> simulate -> visualize."""

from __future__ import annotations

import sys

from parsing.errors import FlyInError
from parsing.parser import Parser
from pathfinding.space_time import SpaceTimeFinder
from simulation.scheduler import Scheduler
from simulation.simulator import Simulator
from visualization.terminal import TerminalVisualizer


def main(argv: list[str]) -> int:
    """Run the simulation for the map given on the command line.

    On a terminal, the run is shown with colors, zone states and the
    secondary metrics. Piped or redirected, only the movement lines are
    printed, exactly in the subject's format, so a checker can read
    them.

    Args:
        argv: Process arguments; ``argv[1]`` is the map file path.

    Returns:
        Exit code: 0 on success, non-zero on any handled error.
    """
    if len(argv) < 2:
        print("usage: python main.py <map_file>", file=sys.stderr)
        return 1

    visualizer = TerminalVisualizer() if sys.stdout.isatty() else None
    try:
        network, nb_drones = Parser().parse_file(argv[1])
        paths = SpaceTimeFinder(nb_drones).find_paths(network)
        drones = Scheduler().assign(network, paths, nb_drones)
        simulator = Simulator(network, drones)
        if visualizer is not None:
            visualizer.show_network(network)
        lines = simulator.run(visualizer)
    except (FlyInError, NotImplementedError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if visualizer is None:
        for line in lines:
            print(line)
    else:
        visualizer.show_summary(simulator.metrics())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
