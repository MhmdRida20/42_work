"""Fly-in entry point: parse -> solve -> simulate -> visualize."""

from __future__ import annotations

import argparse
import os
import sys

from parsing.errors import FlyInError
from parsing.parser import Parser
from pathfinding.space_time import SpaceTimeFinder
from simulation.scheduler import Scheduler
from simulation.simulator import Simulator
from visualization.terminal import TerminalVisualizer
from visualization.visualizer import Visualizer, VisualizerGroup


def main(argv: list[str]) -> int:
    """Run the simulation for the map given on the command line.

    On a terminal, the run is shown with colors, zone states and the
    secondary metrics. Piped or redirected, only the movement lines are
    printed, exactly in the subject's format, so a checker can read
    them. With ``--visual``, a window then replays the run.

    Args:
        argv: Process arguments: the map file path and, optionally,
            ``--visual`` follow the program's name.

    Returns:
        Exit code: 0 on success, 1 on any handled error, 130 when
        stopped with Ctrl+C. Wrong arguments never return: argparse
        prints the usage and exits with 2.
    """
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Route drones through a network of zones, turn by turn.",
    )
    parser.add_argument("map_file", help="the map to solve")
    parser.add_argument(
        "--visual",
        action="store_true",
        help="replay the run in a window once it is over",
    )
    args = parser.parse_args(argv[1:])

    on_terminal = sys.stdout.isatty()
    try:
        network, nb_drones = Parser().parse_file(args.map_file)
        paths = SpaceTimeFinder(nb_drones).find_paths(network)
        drones = Scheduler().assign(network, paths, nb_drones)
        simulator = Simulator(network, drones)
        visualizers: list[Visualizer] = []
        if on_terminal:
            visualizers.append(TerminalVisualizer())
        if args.visual:
            # Imported here only, so a run without --visual never loads
            # pygame; without pygame, this import is a VisualizationError.
            from visualization.graphical import GraphicalVisualizer
            visualizers.append(GraphicalVisualizer(network, args.map_file))
        # The terminal first: its summary is printed before the window
        # opens and waits.
        group = VisualizerGroup(visualizers)
        group.show_network(network)
        lines = simulator.run(group)
        if not on_terminal:
            for line in lines:
                print(line)
            # Every line reaches the reader before a window opens.
            sys.stdout.flush()
        group.show_summary(simulator.metrics())
    except FlyInError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except BrokenPipeError:
        # Whatever reads our output (``head``, for example) stopped
        # early. Point stdout at the null device so Python's final
        # flush can't fail again on the closed pipe.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
