"""Scheduler: assign drones to paths and pick the best flow value.

Given the candidate paths, decide how many to use and how to spread
the drones so the makespan (total turns) is minimised. Because the
simulator is cheap, the scheduler can try every feasible flow value
and keep the assignment with the fewest turns.
"""

from __future__ import annotations

from models.drone import Drone
from models.network import Network
from models.zone import Zone


class Scheduler:
    """Distribute drones across paths to minimise total turns."""

    def assign(
        self,
        network: Network,
        paths: list[list[Zone]],
        nb_drones: int,
    ) -> list[Drone]:
        """Create drones and assign each an optimal path.

        Args:
            network: The network (for the start zone).
            paths: Candidate start -> end paths.
            nb_drones: Number of drones to route.

        Returns:
            The list of drones, each with ``path`` populated.
        """
        # TODO: greedily assign each drone to the path that currently
        # finishes earliest (path length + queue position), balancing
        # the makespan across the chosen paths.
        raise NotImplementedError

    @staticmethod
    def path_cost(path: list[Zone]) -> int:
        """Return the weighted turn cost of a full path.

        Args:
            path: An ordered list of zones from start to end.

        Returns:
            The sum of ``entry_cost`` over every zone entered.
        """
        # TODO: sum entry_cost for each zone after the start.
        raise NotImplementedError
