"""Connection: a bidirectional edge between two zones."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.zone import Zone


class Connection:
    """An undirected edge with an optional traversal capacity."""

    def __init__(
        self,
        zone_a: Zone,
        zone_b: Zone,
        max_link_capacity: int = 1,
    ) -> None:
        """Create a connection between two zones.

        Args:
            zone_a: One endpoint.
            zone_b: The other endpoint.
            max_link_capacity: Max drones crossing per turn (default 1).
        """
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity
        # Drones currently traversing this edge during the active turn.
        self.in_transit: int = 0

    @property
    def name(self) -> str:
        """Canonical connection id, ``<zone_a>-<zone_b>``."""
        return f"{self.zone_a.name}-{self.zone_b.name}"

    def other_end(self, zone: Zone) -> Zone:
        """Return the endpoint opposite to ``zone``.

        Args:
            zone: One endpoint of this connection.

        Returns:
            The other endpoint.

        Raises:
            ValueError: If ``zone`` is not part of this connection.
        """
        if zone is self.zone_a:
            return self.zone_b
        if zone is self.zone_b:
            return self.zone_a
        raise ValueError(f"{zone.name} is not on connection {self.name}")

    def can_traverse(self) -> bool:
        """Return True if another drone may cross this edge this turn."""
        return self.in_transit < self.max_link_capacity
