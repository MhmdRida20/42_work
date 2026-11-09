"""Layout: where zones, drone places and link points are on screen.

The window has a bar at the top, a bar at the bottom, and the map area
between them. Map coordinates are grid positions, not distances, so
each axis is fitted to the map area on its own, and y points up as in
the subject's figures. Like frames.py, this module imports no pygame:
it is plain arithmetic, tested like the rest of the project.
"""

from __future__ import annotations

import math

from models.connection import Connection
from models.network import Network

Point = tuple[float, float]

DEFAULT_SIZE = (1280, 800)
MIN_SIZE = (800, 560)
TOP_BAR = 40
BOTTOM_BAR = 60
MARGIN = 60
MAX_SCALE = 160.0
MAX_SLOTS = 8


class Layout:
    """The screen positions of one network, for one window size.

    A resized window gets a new Layout.

    Attributes:
        network: The network laid out.
        width: The window width used, at least ``MIN_SIZE[0]``.
        height: The window height used, at least ``MIN_SIZE[1]``.
        zone_radius: The radius of a zone's circle, in pixels.
        drone_radius: The radius of a drone's disc, in pixels.
        centers: Zone name -> the pixel at the center of its circle.
        links: Connection name -> connection.
    """

    def __init__(self, network: Network, width: int, height: int) -> None:
        """Fit ``network`` into a window of ``width`` x ``height``.

        Args:
            network: The parsed network.
            width: The window width in pixels.
            height: The window height in pixels.
        """
        self.network = network
        self.width = max(width, MIN_SIZE[0])
        self.height = max(height, MIN_SIZE[1])
        area_width = self.width - 2 * MARGIN
        area_height = self.height - TOP_BAR - BOTTOM_BAR - 2 * MARGIN
        zones = network.zones.values()
        min_x = min(zone.x for zone in zones)
        max_y = max(zone.y for zone in zones)
        span_x = max(zone.x for zone in zones) - min_x
        span_y = max_y - min(zone.y for zone in zones)
        scale_x = self._scale(span_x, area_width)
        scale_y = self._scale(span_y, area_height)
        # A zone's radius is 28% of a grid step, kept between 10 and
        # 26 px; a drone is a third of a zone, at least 5 px.
        self.zone_radius = min(max(0.28 * min(scale_x, scale_y), 10.0), 26.0)
        self.drone_radius = max(5.0, self.zone_radius // 3)
        # A map smaller than the area is centered in it.
        left = MARGIN + (area_width - span_x * scale_x) / 2
        top = TOP_BAR + MARGIN + (area_height - span_y * scale_y) / 2
        self.centers: dict[str, Point] = {}
        on_spot: dict[tuple[int, int], int] = {}
        for zone in zones:
            # The parser accepts zones on the same coordinates: each one
            # after the first moves right by one zone radius.
            before = on_spot.get((zone.x, zone.y), 0)
            on_spot[(zone.x, zone.y)] = before + 1
            x = left + (zone.x - min_x) * scale_x + before * self.zone_radius
            # y points up: the zone with the highest y is at the top.
            y = top + (max_y - zone.y) * scale_y
            self.centers[zone.name] = (x, y)
        self.links: dict[str, Connection] = {
            connection.name: connection
            for incident in network.adjacency.values()
            for connection in incident
        }

    def slot(self, name: str, rank: int) -> Point:
        """Return where a drone inside zone ``name`` is drawn.

        The start, the end and the zones for one drone keep their
        drones at the center. Other zones have up to MAX_SLOTS places
        on a ring, the first at the top, then clockwise; a rank past
        the last place goes round the ring again.

        Args:
            name: The zone's name.
            rank: The drone's rank, from 0, among the drones inside.

        Returns:
            The pixel at the center of the drone's disc.
        """
        zone = self.network.zones[name]
        x, y = self.centers[name]
        places = min(zone.max_drones, MAX_SLOTS)
        if zone.unlimited or places == 1:
            return (x, y)
        # On screen y points down, so angles grow clockwise and -90
        # degrees is the top of the ring.
        angle = 2 * math.pi * rank / places - math.pi / 2
        ring = 0.55 * self.zone_radius
        return (x + ring * math.cos(angle), y + ring * math.sin(angle))

    def on_link(self, link: str, toward: str, progress: float) -> Point:
        """Return the point at ``progress`` along a flight on ``link``.

        Args:
            link: The connection's name, as in a Pose.
            toward: The zone the drone flies to, one end of ``link``.
            progress: 0 at the other end's center, 1 at ``toward``'s.

        Returns:
            The pixel at that point.

        Raises:
            ValueError: If ``toward`` is not an end of ``link``.
        """
        destination = self.network.zones[toward]
        origin = self.links[link].other_end(destination)
        x0, y0 = self.centers[origin.name]
        x1, y1 = self.centers[toward]
        return (x0 + (x1 - x0) * progress, y0 + (y1 - y0) * progress)

    @staticmethod
    def _scale(span: int, size: float) -> float:
        """Return the pixels per map unit on one axis, at most MAX_SCALE.

        Args:
            span: The highest minus the lowest coordinate on this axis.
            size: The size of the map area on this axis, in pixels.

        Returns:
            The scale. An axis with one value gets MAX_SCALE: any scale
            works there, because the centering puts that value in the
            middle of the area.
        """
        if span == 0:
            return MAX_SCALE
        return min(size / span, MAX_SCALE)
