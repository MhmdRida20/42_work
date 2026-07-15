"""Simulator: the deterministic turn-by-turn engine.

This is where the movement and occupancy rules are enforced exactly.
Keep it pure and deterministic (same input -> same output) so it can
be tested and reused by the scheduler across candidate flow values.
"""

from __future__ import annotations

from models.drone import Drone
from models.network import Network


class Simulator:
    """Run drones along their assigned paths, one turn at a time."""

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
        # TODO: loop calling step() until all drones are delivered,
        # collecting each non-empty turn line.
        raise NotImplementedError

    def step(self) -> str:
        """Advance the simulation by exactly one turn.

        Returns:
            The space-separated movement line for this turn, e.g.
            ``D1-roof1 D2-corridorA`` (drones that don't move are
            omitted).
        """
        # TODO: rules to enforce, in order:
        #   1. compute each drone's intended move
        #   2. free zones the drones leave (capacity frees this turn)
        #   3. validate zone capacity + connection capacity
        #   4. commit restricted transit (must arrive next turn)
        #   5. break ties deterministically; others wait
        #   6. mark end-zone arrivals as delivered
        raise NotImplementedError

    @property
    def turn_count(self) -> int:
        """Number of turns taken so far (the makespan)."""
        return len(self.turns)
