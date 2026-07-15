"""Advanced strategy: node-split min-cost max-flow.

Handles restricted-zone weights and per-zone capacity by splitting
each zone ``v`` into ``v_in -> v_out`` (capacity ``max_drones``) and
running successive shortest augmenting paths with Dijkstra + Johnson
potentials. Priority zones get a small cost discount so they are
preferred without being mandatory.
"""

from __future__ import annotations

from models.network import Network
from models.zone import Zone
from pathfinding.pathfinder import PathFinder


class MinCostFlowFinder(PathFinder):
    """Weighted min-cost flow with node splitting for zone capacity."""

    def find_paths(self, network: Network) -> list[list[Zone]]:
        """Return cost-optimal start -> end paths (see module doc)."""
        # TODO: build the split/weighted residual graph, run min-cost
        # max-flow with potentials, then decompose flow into paths.
        raise NotImplementedError

    def _dijkstra(
        self,
        network: Network,
        source: Zone,
        potentials: dict[str, int],
    ) -> tuple[dict[str, int], dict[str, Zone]]:
        """Shortest-path pass with reduced (non-negative) costs.

        Args:
            network: The residual network.
            source: Start zone.
            potentials: Johnson potentials keeping reduced costs >= 0.

        Returns:
            A tuple ``(distances, parents)`` keyed by zone name.
        """
        # TODO: priority-queue Dijkstra over reduced edge costs.
        raise NotImplementedError
