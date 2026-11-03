"""Drone: an agent moving from the start zone to the end zone."""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.connection import Connection
    from models.zone import Zone


class DroneState(Enum):
    """Lifecycle states of a drone during the simulation."""

    AT_ZONE = auto()
    IN_TRANSIT = auto()
    DELIVERED = auto()


class Drone:
    """A single drone with a position, an assigned path and a state."""

    def __init__(self, drone_id: int, start: Zone) -> None:
        """Create a drone sitting at the start zone.

        Args:
            drone_id: Unique identifier (printed as ``D<id>``).
            start: The zone the drone begins in.
        """
        self.id = drone_id
        self.position: Zone | Connection = start
        self.path: list[Zone] = []
        self.path_index: int = 0
        self.remaining_transit: int = 0
        self.state: DroneState = DroneState.AT_ZONE
        # Set by the simulator on the turn the drone is delivered.
        self.arrival_turn: int | None = None

    @property
    def label(self) -> str:
        """Return the output label, e.g. ``D1``."""
        return f"D{self.id}"

    @property
    def delivered(self) -> bool:
        """Whether the drone has reached the end zone."""
        return self.state is DroneState.DELIVERED

    @property
    def next_zone(self) -> Zone | None:
        """The zone this drone would move into next.

        Returns:
            The next zone on ``path``, or None if delivered or the
            path has not been assigned yet.
        """
        if self.state is DroneState.DELIVERED:
            return None
        if self.path_index + 1 >= len(self.path):
            return None
        return self.path[self.path_index + 1]

    def advance(self) -> None:
        """Commit a one-turn move into :attr:`next_zone`.

        Updates ``position`` and ``path_index``, and marks the drone
        delivered once it reaches the last zone of its path.

        Raises:
            ValueError: If there is no next zone to advance into.
        """
        next_zone = self.next_zone
        if next_zone is None:
            raise ValueError(f"{self.label} has no next zone to advance to")
        self.position = next_zone
        self.path_index += 1
        if self.path_index == len(self.path) - 1:
            self.state = DroneState.DELIVERED
        else:
            self.state = DroneState.AT_ZONE

    def begin_transit(self, connection: Connection, turns: int) -> None:
        """Leave the current zone and fly along ``connection``.

        Args:
            connection: The connection toward :attr:`next_zone`.
            turns: Total turns the movement takes.
        """
        self.position = connection
        self.remaining_transit = turns - 1
        self.state = DroneState.IN_TRANSIT
