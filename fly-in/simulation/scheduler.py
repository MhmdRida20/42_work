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
from parsing.errors import NoPathError


class Scheduler:
    """Distribute drones across paths to minimise total turns.

    For now every drone is assigned to the single path found by the
    baseline BFS finder (balancing across multiple paths is added in a
    later milestone).
    """

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

        Raises:
            NoPathError: If no candidate path was supplied.
        """
        if not paths:
            raise NoPathError("no paths available to assign drones to")

        path = paths[0]
        drones = [Drone(i, network.start) for i in range(1, nb_drones + 1)]
        for drone in drones:
            drone.path = path
            network.start.occupants.append(drone)
        return drones

    @staticmethod
    def path_cost(path: list[Zone]) -> int:
        """Return the weighted turn cost of a full path.

        Args:
            path: An ordered list of zones from start to end.

        Returns:
            The sum of ``entry_cost`` over every zone entered.
        """
        return sum(zone.entry_cost for zone in path[1:])
