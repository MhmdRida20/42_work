"""Smoke tests: verify every package still imports cleanly.

Real behavioral coverage lives in test_zone.py, test_network.py, and
test_parser.py (M1) and the corresponding files added for later
milestones.
"""

from __future__ import annotations

import models.connection
import models.drone
import models.network
import models.zone
import parsing.parser
import pathfinding.bfs_flow
import pathfinding.mincost_flow
import simulation.scheduler
import simulation.simulator
import visualization.terminal


def test_all_modules_import() -> None:
    """Every module in the project can be imported without error."""
    modules = (
        models.zone,
        models.connection,
        models.network,
        models.drone,
        parsing.parser,
        pathfinding.bfs_flow,
        pathfinding.mincost_flow,
        simulation.scheduler,
        simulation.simulator,
        visualization.terminal,
    )
    assert all(module is not None for module in modules)
