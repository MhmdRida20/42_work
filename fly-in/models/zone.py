"""Zone hierarchy: the nodes of the drone network.

Each concrete zone knows its movement cost and whether it is
accessible. Start and end zones are special: they have unlimited
capacity regardless of their zone type, via the ``unlimited`` flag on
:class:`Zone`. A :class:`ZoneFactory` turns a parsed ``zone=<type>``
string into the matching subclass.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from parsing.errors import ParseError

# type_checking will help us use a class for type hints
# without importing it at runtime.

if TYPE_CHECKING:
    from models.drone import Drone


class Zone(ABC):
    """Abstract node in the network. Base class for all zone types."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        color: str | None = None,
        max_drones: int = 1,
        unlimited: bool = False,
    ) -> None:
        """Store zone metadata.

        Args:
            name: Unique zone name (no dashes or spaces).
            x: Integer x coordinate.
            y: Integer y coordinate.
            color: Optional color tag used for visualization.
            max_drones: Max simultaneous occupants (default 1).
            unlimited: True for the start/end zones, which may hold
                any number of drones regardless of ``max_drones``.
        """
        self.name = name
        self.x = x
        self.y = y
        self.color = color
        self.max_drones = max_drones
        self.unlimited = unlimited
        self.occupants: list[Drone] = []

    @property
    @abstractmethod
    def entry_cost(self) -> int:
        """Number of turns needed to move into this zone."""
        raise NotImplementedError

    @property
    def is_accessible(self) -> bool:
        """Whether drones may enter or traverse this zone."""
        return True

    def has_capacity(self) -> bool:
        """Return True if another drone may enter this turn."""
        return self.unlimited or len(self.occupants) < self.max_drones

    def __repr__(self) -> str:
        """Return a short debug representation."""
        return f"{type(self).__name__}({self.name!r})"


class NormalZone(Zone):
    """Standard zone: entering costs one turn."""

    @property
    def entry_cost(self) -> int:
        """Return the entry cost (1 turn)."""
        return 1


class RestrictedZone(Zone):
    """Sensitive zone: entering costs two turns (transit on edge)."""

    @property
    def entry_cost(self) -> int:
        """Return the entry cost (2 turns)."""
        return 2


class PriorityZone(Zone):
    """Preferred zone: costs one turn but pathfinding should favor it."""

    @property
    def entry_cost(self) -> int:
        """Return the entry cost (1 turn)."""
        return 1


class BlockedZone(Zone):
    """Inaccessible zone: never entered or traversed."""

    @property
    def entry_cost(self) -> int:
        """Blocked zones cannot be entered."""
        raise NotImplementedError("blocked zones are inaccessible")

    @property
    def is_accessible(self) -> bool:
        """Blocked zones are never accessible."""
        return False


class ZoneFactory:
    """Build the correct :class:`Zone` subclass from a type string."""

    _TYPES: dict[str, type[Zone]] = {
        "normal": NormalZone,
        "restricted": RestrictedZone,
        "priority": PriorityZone,
        "blocked": BlockedZone,
    }

    def build(
        self,
        zone_type: str,
        name: str,
        x: int,
        y: int,
        color: str | None = None,
        max_drones: int = 1,
        unlimited: bool = False,
    ) -> Zone:
        """Create a zone of the given type.

        Args:
            zone_type: One of ``normal``/``restricted``/``priority``/
                ``blocked``.
            name: Unique zone name.
            x: Integer x coordinate.
            y: Integer y coordinate.
            color: Optional color tag.
            max_drones: Max simultaneous occupants.
            unlimited: True for the start/end zones (see
                :attr:`Zone.unlimited`).

        Returns:
            The constructed zone.

        Raises:
            ParseError: If ``zone_type`` is not a known type.
        """
        zone_cls = self._TYPES.get(zone_type)
        if zone_cls is None:
            known = ", ".join(sorted(self._TYPES))
            raise ParseError(
                f"unknown zone type {zone_type!r} (expected one of: {known})"
            )
        return zone_cls(name, x, y, color, max_drones, unlimited)
