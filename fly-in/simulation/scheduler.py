"""Scheduler: create the drones and give each one its path.

A finder returns either one path shared by every drone (the BFS
baseline) or one timed route per drone (the space-time planner). The
scheduler handles both the same way.
"""

from __future__ import annotations

from models.drone import Drone
from models.network import Network
from models.zone import Zone
from parsing.errors import NoPathError


class Scheduler:
    """Create the drones in the start zone and hand out their paths."""

    def assign(
        self,
        network: Network,
        paths: list[list[Zone]],
        nb_drones: int,
    ) -> list[Drone]:
        """Create drones and give each one its path.

        Drone ``i`` (counting from 0) gets ``paths[i % len(paths)]``:
        with one path everyone shares it, with one route per drone
        each drone gets its own.

        Args:
            network: The network (for the start zone).
            paths: Start -> end paths, in drone id order.
            nb_drones: Number of drones to route.

        Returns:
            The list of drones, each with ``path`` populated.

        Raises:
            NoPathError: If no candidate path was supplied.
        """
        if not paths:
            raise NoPathError("no paths available to assign drones to")

        drones = [Drone(i, network.start) for i in range(1, nb_drones + 1)]
        for index, drone in enumerate(drones):
            drone.path = paths[index % len(paths)]
            network.start.occupants.append(drone)
        return drones

    @staticmethod
    def path_cost(path: list[Zone]) -> int:
        """Return the weighted turn cost of a full path.

        Args:
            path: An ordered list of zones from start to end. A zone
                repeated for a planned wait costs nothing.

        Returns:
            The sum of ``entry_cost`` over every zone entered.
        """
        return sum(
            there.entry_cost
            for here, there in zip(path, path[1:])
            if there is not here
        )
