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
        self.remaining_transit: int = 0
        self.state: DroneState = DroneState.AT_ZONE

    @property
    def label(self) -> str:
        """Return the output label, e.g. ``D1``."""
        return f"D{self.id}"

    @property
    def delivered(self) -> bool:
        """Whether the drone has reached the end zone."""
        return self.state is DroneState.DELIVERED

    def step(self) -> None:
        """Advance the drone by one turn along its assigned path.

        Handles normal moves, multi-turn transit toward restricted
        zones, and waiting. Updates ``position``/``state`` in place.
        """
        # TODO: implement the per-drone state machine (AT_ZONE ->
        # IN_TRANSIT -> AT_ZONE, restricted 2-turn transit, delivery).
        raise NotImplementedError
