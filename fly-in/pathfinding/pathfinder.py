"""Abstract path finder (Strategy pattern).

Concrete strategies (BFS multi-path, min-cost flow) implement
:meth:`PathFinder.find_paths` and can be swapped without touching
the simulator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.network import Network
from models.zone import Zone


class PathFinder(ABC):
    """Compute a set of start -> end paths for the drones to follow."""

    @abstractmethod
    def find_paths(self, network: Network) -> list[list[Zone]]:
        """Return candidate paths from the start zone to the end zone.

        Args:
            network: The (blocked-pruned) network to search.

        Returns:
            A list of paths, each an ordered list of zones from start
            to end.

        Raises:
            NoPathError: If the end zone is unreachable.
        """
        raise NotImplementedError
