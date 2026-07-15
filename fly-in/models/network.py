"""Network: the graph of zones and their connections.

No third-party graph library is used (networkx / graphlib are
forbidden). BFS / Dijkstra / flow are implemented by hand in the
``pathfinding`` package.
"""

from __future__ import annotations

from models.connection import Connection
from models.zone import Zone


class Network:
    """An undirected graph of zones with adjacency lookup."""

    def __init__(self) -> None:
        """Create an empty network."""
        self.zones: dict[str, Zone] = {}
        self.adjacency: dict[str, list[Connection]] = {}
        self._start: Zone | None = None
        self._end: Zone | None = None

    @property
    def start(self) -> Zone:
        """Return the unique start zone.

        Raises:
            ValueError: If no start zone has been set.
        """
        if self._start is None:
            raise ValueError("network has no start zone")
        return self._start

    @property
    def end(self) -> Zone:
        """Return the unique end zone.

        Raises:
            ValueError: If no end zone has been set.
        """
        if self._end is None:
            raise ValueError("network has no end zone")
        return self._end

    def add_zone(
        self,
        zone: Zone,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:
        """Register a zone in the network.

        Args:
            zone: The zone to add.
            is_start: True if this is the unique start zone.
            is_end: True if this is the unique end zone.

        Raises:
            ParseError: On a duplicate name or a second start/end.
        """
        # TODO: reject duplicate names; set _start/_end when flagged
        # (rejecting a second start or end); initialise adjacency.
        raise NotImplementedError

    def add_connection(
        self,
        name_a: str,
        name_b: str,
        max_link_capacity: int = 1,
    ) -> None:
        """Create a bidirectional connection between two zones.

        Args:
            name_a: Name of the first zone (must already exist).
            name_b: Name of the second zone (must already exist).
            max_link_capacity: Max drones crossing per turn.

        Raises:
            ParseError: If a zone is unknown or the edge is a
                duplicate (``a-b`` equals ``b-a``).
        """
        # TODO: validate both zones exist, reject duplicates and
        # self-loops, build a Connection and store it in adjacency.
        raise NotImplementedError

    def neighbors(self, zone: Zone) -> list[Connection]:
        """Return the connections incident to ``zone``.

        Args:
            zone: The zone whose edges are requested.

        Returns:
            The list of incident connections (empty if none).
        """
        return self.adjacency.get(zone.name, [])
