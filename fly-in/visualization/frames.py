"""Frames: the run turned into data, one frame per turn.

The graphical view replays a run once it is computed. The Recorder is
a visualizer that draws nothing: after every turn it reads the network
and keeps what the screen needs, namely where each drone in play is,
how many drones wait in the start and how many are delivered, and how
busy each connection was. It imports no pygame, so it is tested like
the rest of the project.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.drone import Drone
from models.network import Network
from models.zone import Zone
from visualization.visualizer import Visualizer


@dataclass(frozen=True)
class Pose:
    """Where one drone is at the end of a turn.

    Attributes:
        zone: The zone the drone is in, or the zone it flies toward.
        link: The connection it is on while flying, else None.
        progress: 1.0 inside a zone; while flying, the share of the
            flight already done (1/2 after a restricted take-off).
    """

    zone: str
    link: str | None = None
    progress: float = 1.0


@dataclass(frozen=True)
class Frame:
    """The state of the run at the end of one turn.

    Attributes:
        turn: The turn number; 0 is the state before the first move.
        line: The turn's movement line, exactly as printed.
        poses: Drone id -> pose, for each drone between the start and
            the end, and for each drone that moved this turn.
        waiting: How many drones are in the start zone.
        delivered: How many drones are in the end zone.
        link_load: Connection name -> drones that used it this turn.
    """

    turn: int
    line: str
    poses: dict[int, Pose]
    waiting: int
    delivered: int
    link_load: dict[str, int]


class Recorder(Visualizer):
    """A visualizer that draws nothing and keeps one frame per turn."""

    def __init__(self) -> None:
        """Start with no frames and no known drone positions."""
        self.frames: list[Frame] = []
        self.metrics: dict[str, float] = {}
        self._last: dict[int, Pose] = {}

    def show_network(self, network: Network) -> None:
        """Record turn 0: every drone still waiting in the start."""
        self.capture(network, 0, "")

    def show_turn(self, turn_number: int, line: str, network: Network) -> None:
        """Record the state right after one turn."""
        self.capture(network, turn_number, line)

    def show_summary(self, metrics: dict[str, float]) -> None:
        """Keep the run's metrics for the end of the replay."""
        self.metrics = dict(metrics)

    def capture(self, network: Network, turn: int, line: str) -> Frame:
        """Turn the network's current state into a frame.

        Args:
            network: The network, read after the turn was played.
            turn: The turn number; 0 before the first move.
            line: The turn's movement line ("" for turn 0).

        Returns:
            The new frame, also appended to :attr:`frames`.
        """
        poses: dict[int, Pose] = {}
        waiting = 0
        delivered = 0
        for zone in network.zones.values():
            for drone in zone.occupants:
                pose = self._pose_of(drone, zone)
                # A drone seen for the first time (turn 0) hasn't moved.
                moved = self._last.get(drone.id, pose) != pose
                self._last[drone.id] = pose
                at_start = drone.position is network.start
                at_end = drone.position is network.end
                if at_start:
                    waiting += 1
                if at_end:
                    delivered += 1
                if moved or not (at_start or at_end):
                    poses[drone.id] = pose
        link_load = {
            connection.name: connection.in_transit
            for incident in network.adjacency.values()
            for connection in incident
            if connection.in_transit > 0
        }
        frame = Frame(turn, line, poses, waiting, delivered, link_load)
        self.frames.append(frame)
        return frame

    @staticmethod
    def _pose_of(drone: Drone, zone: Zone) -> Pose:
        """Return the pose of ``drone``, one of ``zone``'s occupants.

        ``occupants`` also holds the drones still flying toward the
        zone, because their place is reserved at take-off.
        """
        if drone.position is zone:
            return Pose(zone.name)
        flown = zone.entry_cost - drone.remaining_transit
        return Pose(zone.name, drone.position.name, flown / zone.entry_cost)
