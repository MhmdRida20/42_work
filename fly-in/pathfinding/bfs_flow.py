"""Baseline strategy: BFS-based multi-path (Edmonds-Karp style).

Repeatedly finds augmenting paths in a residual graph until none
remain, yielding a set of edge-disjoint paths that respect each
connection's capacity. Good enough for the easy and most medium maps.
"""

from __future__ import annotations

from collections import deque

from models.network import Network
from models.zone import Zone
from parsing.errors import NoPathError
from pathfinding.pathfinder import PathFinder


class BFSFlowFinder(PathFinder):
    """Find edge-disjoint paths via repeated BFS augmentation.

    For now this returns a single shortest path (multi-path
    augmentation is added in a later milestone).
    """

    def find_paths(self, network: Network) -> list[list[Zone]]:
        """Return edge-disjoint start -> end paths (see module doc)."""
        path = self._bfs(network, network.start, network.end)
        if path is None:
            raise NoPathError(
                f"no path from {network.start.name!r} to "
                f"{network.end.name!r}"
            )
        return [path]

    def _bfs(
        self,
        network: Network,
        source: Zone,
        sink: Zone,
    ) -> list[Zone] | None:
        """Return a shortest source -> sink path, or None if none.

        Args:
            network: The (residual) network to search.
            source: Start zone.
            sink: End zone.

        Returns:
            The path as an ordered list of zones, or None.
        """
        if source is sink:
            return [source]

        parents: dict[str, Zone] = {}
        visited = {source.name}
        queue: deque[Zone] = deque([source])

        while queue:
            current = queue.popleft()
            for connection in network.neighbors(current):
                neighbor = connection.other_end(current)
                if neighbor.name in visited or not neighbor.is_accessible:
                    continue
                visited.add(neighbor.name)
                parents[neighbor.name] = current
                if neighbor is sink:
                    return self._reconstruct(parents, source, sink)
                queue.append(neighbor)

        return None

    @staticmethod
    def _reconstruct(
        parents: dict[str, Zone],
        source: Zone,
        sink: Zone,
    ) -> list[Zone]:
        """Rebuild the source -> sink path from a BFS parent map.

        Args:
            parents: Map of zone name to the zone it was reached from.
            source: Start zone.
            sink: End zone.

        Returns:
            The path as an ordered list of zones, from source to sink.
        """
        path = [sink]
        while path[-1] is not source:
            path.append(parents[path[-1].name])
        path.reverse()
        return path
