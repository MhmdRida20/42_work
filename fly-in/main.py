"""Fly-in entry point: parse -> solve -> simulate -> visualize."""

from __future__ import annotations

import sys

from parsing.errors import FlyInError
from parsing.parser import Parser
# Uncomment as you implement each stage:
# from pathfinding.bfs_flow import BFSFlowFinder
# from simulation.scheduler import Scheduler
# from simulation.simulator import Simulator
# from visualization.terminal import TerminalVisualizer


def main(argv: list[str]) -> int:
    """Run the simulation for the map given on the command line.

    Args:
        argv: Process arguments; ``argv[1]`` is the map file path.

    Returns:
        Exit code: 0 on success, non-zero on any handled error.
    """
    if len(argv) < 2:
        print("usage: python main.py <map_file>", file=sys.stderr)
        return 1

    try:
        parser = Parser()
        network, nb_drones = parser.parse_file(argv[1])
        # TODO: wire up the pipeline once the stages are implemented:
        #   paths = BFSFlowFinder().find_paths(network)
        #   drones = Scheduler().assign(network, paths, nb_drones)
        #   lines = Simulator(network, drones).run()
        #   TerminalVisualizer().show_network(network)  # + turns/summary
        _ = (network, nb_drones)
    except (FlyInError, NotImplementedError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
