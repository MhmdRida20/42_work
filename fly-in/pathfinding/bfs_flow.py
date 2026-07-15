"""Baseline strategy: BFS-based multi-path (Edmonds-Karp style).

Repeatedly finds augmenting paths in a residual graph until none
remain, yielding a set of edge-disjoint paths that respect each
connection's capacity. Good enough for the easy and most medium maps.
"""

from __future__ import annotations

from models.network import Network
from models.zone import Zone
from pathfinding.pathfinder import PathFinder


class BFSFlowFinder(PathFinder):
    """Find edge-disjoint paths via repeated BFS augmentation."""

    def find_paths(self, network: Network) -> list[list[Zone]]:
        """Return edge-disjoint start -> end paths (see module doc)."""
        # TODO: build a residual graph, repeatedly BFS for an
        # augmenting path, and decompose the resulting flow into paths.
        raise NotImplementedError

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
        # TODO: standard breadth-first search with parent tracking.
        raise NotImplementedError
