"""Simulator: the deterministic turn-by-turn engine.

This is where the movement and occupancy rules are enforced exactly.
Keep it pure and deterministic (same input -> same output) so it can
be tested and reused by the scheduler across candidate flow values.
"""

from __future__ import annotations

from models.connection import Connection
from models.drone import Drone
from models.network import Network
from models.zone import Zone


class Simulator:
    """Run drones along their assigned paths, one turn at a time.

    This milestone handles single-turn moves through normal/priority
    zones, respecting zone and connection capacity. Multi-turn
    restricted-zone transit and priority-aware tie-breaking are added
    in a later milestone; for now, ties are broken deterministically
    by ascending drone id.
    """

    def __init__(self, network: Network, drones: list[Drone]) -> None:
        """Set up a simulation.

        Args:
            network: The network the drones move through.
            drones: Drones with their paths already assigned.
        """
        self.network = network
        self.drones = drones
        self.turns: list[str] = []

    def run(self) -> list[str]:
        """Run until every drone is delivered.

        Returns:
            One formatted output line per turn (see spec VII.5).
        """
        while not all(drone.delivered for drone in self.drones):
            self.turns.append(self.step())
        return self.turns

    def step(self) -> str:
        """Advance the simulation by exactly one turn.

        Returns:
            The space-separated movement line for this turn, e.g.
            ``D1-roof1 D2-corridorA`` (drones that don't move are
            omitted).
        """
        movers = [
            drone
            for drone in self.drones
            if not drone.delivered and drone.next_zone is not None
        ]

        # Leavers free their zone's capacity for this same turn, before
        # any entrant is validated.
        for drone in movers:
            if isinstance(drone.position, Zone):
                drone.position.occupants.remove(drone)

        for connections in self.network.adjacency.values():
            for connection in connections:
                connection.in_transit = 0

        moved: list[Drone] = []
        for drone in sorted(movers, key=lambda d: d.id):
            current = drone.position
            next_zone = drone.next_zone
            assert isinstance(current, Zone) and next_zone is not None
            connection = self._connection_between(current, next_zone)

            if not next_zone.has_capacity() or not connection.can_traverse():
                current.occupants.append(drone)
                continue

            connection.in_transit += 1
            drone.advance()
            next_zone.occupants.append(drone)
            moved.append(drone)

        moved.sort(key=lambda d: d.id)
        return " ".join(
            f"{drone.label}-{drone.position.name}" for drone in moved
        )

    def _connection_between(self, a: Zone, b: Zone) -> Connection:
        """Return the connection linking ``a`` and ``b``.

        Args:
            a: One endpoint.
            b: The other endpoint.

        Returns:
            The connection between them.

        Raises:
            ValueError: If ``a`` and ``b`` are not directly connected.
        """
        for connection in self.network.neighbors(a):
            if connection.other_end(a) is b:
                return connection
        raise ValueError(f"no connection between {a.name} and {b.name}")

    @property
    def turn_count(self) -> int:
        """Number of turns taken so far (the makespan)."""
        return len(self.turns)
