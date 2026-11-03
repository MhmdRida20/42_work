"""Simulator: the deterministic turn-by-turn engine.

This is where the movement and occupancy rules are enforced exactly.
It is deterministic (same input -> same output), and it never trusts
the plan: a planner bug shows up as a clean error, never as an illegal
turn.
"""

from __future__ import annotations

from models.connection import Connection
from models.drone import Drone, DroneState
from models.network import Network
from models.zone import Zone
from parsing.errors import SimulationError
from simulation.scheduler import Scheduler
from visualization.visualizer import Visualizer


class Simulator:
    """Run drones along their assigned paths, one turn at a time.

    Respects zone and connection capacity. A move into a restricted
    zone puts the drone on the connection first, and it must land when
    its flight ends. A zone repeated in a drone's path is a planned
    wait. Ties are broken by ascending drone id.
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

    def run(self, visualizer: Visualizer | None = None) -> list[str]:
        """Run until every drone is delivered.

        Args:
            visualizer: Optional. Shown each turn once it is played; it
                only reads the state, so it can't change the run.

        Returns:
            One formatted output line per turn (see spec VII.5).

        Raises:
            SimulationError: If a turn passes and no drone can move.
        """
        while not all(drone.delivered for drone in self.drones):
            line = self.step()
            if not line:
                raise SimulationError("no drone can move: the run is stuck")
            self.turns.append(line)
            for drone in self.drones:
                if drone.delivered and drone.arrival_turn is None:
                    drone.arrival_turn = len(self.turns)
            if visualizer is not None:
                visualizer.show_turn(len(self.turns), line, self.network)
        return self.turns

    def metrics(self) -> dict[str, float]:
        """Return the secondary metrics of a finished run (VII.6).

        Returns:
            The number of turns, the drones moved per turn on average,
            the average turn a drone is delivered on, and the total
            path cost (every drone's weighted moves, waits excluded).
        """
        turns = len(self.turns)
        moves = sum(len(line.split()) for line in self.turns)
        arrivals = [drone.arrival_turn or 0 for drone in self.drones]
        return {
            "turns": turns,
            "drones moved per turn": moves / turns if turns else 0.0,
            "average turns per drone": (
                sum(arrivals) / len(arrivals) if arrivals else 0.0
            ),
            "total path cost": sum(
                Scheduler.path_cost(drone.path) for drone in self.drones
            ),
        }

    def step(self) -> str:
        """Advance the simulation by exactly one turn.

        Returns:
            The space-separated movement line for this turn, e.g.
            ``D1-roof1 D2-corridorA`` (drones that don't move are
            omitted).

        Raises:
            SimulationError: If a blocked drone's zone is already full.
        """
        in_flight = [
            drone
            for drone in self.drones
            if drone.state is DroneState.IN_TRANSIT
        ]
        ready = [
            drone
            for drone in self.drones
            if drone.state is DroneState.AT_ZONE
            and drone.next_zone is not None
        ]
        movers = [
            drone for drone in ready if drone.next_zone is not drone.position
        ]
        waiters = [
            drone for drone in ready if drone.next_zone is drone.position
        ]

        # A zone repeated in a path is a planned wait: the drone keeps
        # its place, uses no connection and prints nothing this turn.
        for drone in waiters:
            drone.advance()

        # Leavers free their zone's capacity for this same turn, before
        # any entrant is validated.
        for drone in movers:
            if isinstance(drone.position, Zone):
                drone.position.occupants.remove(drone)

        for connections in self.network.adjacency.values():
            for connection in connections:
                connection.in_transit = 0

        moved: list[Drone] = []

        # A flying drone cannot wait. Its place in the zone was reserved
        # at take-off, but it still uses the connection this turn.
        for drone in in_flight:
            assert isinstance(drone.position, Connection)
            drone.position.in_transit += 1
            drone.remaining_transit -= 1
            if drone.remaining_transit == 0:
                drone.advance()
            moved.append(drone)

        for drone in sorted(movers, key=lambda d: d.id):
            current = drone.position
            next_zone = drone.next_zone
            assert isinstance(current, Zone) and next_zone is not None
            connection = self.network.connection_between(current, next_zone)

            if not next_zone.has_capacity() or not connection.can_traverse():
                # A drone with a lower id may have taken this place when
                # it looked free, so going back could overfill the zone.
                if not current.has_capacity():
                    raise SimulationError(
                        f"{drone.label} is blocked and {current.name} is full"
                    )
                current.occupants.append(drone)
                continue

            connection.in_transit += 1
            next_zone.occupants.append(drone)
            if next_zone.entry_cost > 1:
                drone.begin_transit(connection, next_zone.entry_cost)
            else:
                drone.advance()
            moved.append(drone)

        moved.sort(key=lambda d: d.id)
        return " ".join(
            f"{drone.label}-{drone.position.name}" for drone in moved
        )

    @property
    def turn_count(self) -> int:
        """Number of turns taken so far (the makespan)."""
        return len(self.turns)
