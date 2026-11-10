"""Graphical view: draw one moment of the replay with pygame-ce.

The SceneRenderer draws the map: links under zones under drones. The
moment comes from a Playback and the pixels from a Layout, so the
window shows exactly what the recorded frames say. The picture is
drawn again from nothing each time; only the text, the slow part, is
kept from one picture to the next.
"""

from __future__ import annotations

import math
import os

from models.connection import Connection
from models.network import Network
from models.zone import PriorityZone, RestrictedZone, Zone
from visualization.frames import Frame
from visualization.layout import MAX_SLOTS, Layout, Point
from visualization.playback import Playback

# Importing pygame prints a banner to stdout, where the movement lines
# go. This variable hides it, so it must be set before the import.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402

RGB = tuple[int, int, int]

BACKGROUND: RGB = (24, 26, 33)
LINK: RGB = (88, 94, 108)
GLOW: RGB = (255, 190, 60)
TEXT: RGB = (222, 226, 234)
MUTED: RGB = (150, 156, 170)
OUTLINE: RGB = (235, 238, 245)
BLOCKED: RGB = (62, 64, 70)
CROSS: RGB = (140, 142, 150)
NO_COLOR: RGB = (150, 150, 150)
WHITE: RGB = (255, 255, 255)

NAME_SIZE = 16
SMALL_SIZE = 14
# The one-character "...", written as an escape to keep the file ASCII.
ELLIPSIS = "\u2026"
# Each drone id turns the hue by the golden ratio of a full turn, so
# drones with neighbouring ids get clearly different colors.
GOLDEN = 0.6180339887


class SceneRenderer:
    """Draw the map at one moment of the replay.

    Attributes:
        network: The network drawn.
        show_names: Whether zone names are written (the N key).
    """

    def __init__(self, network: Network) -> None:
        """Start pygame's fonts; each font and text is made when needed.

        Args:
            network: The parsed network.
        """
        pygame.font.init()
        self.network = network
        self.show_names = True
        self._fonts: dict[int, pygame.font.Font] = {}
        self._texts: dict[tuple[str, int, RGB, RGB], pygame.Surface] = {}
        self._names: dict[str, str] = {}
        self._names_for: Layout | None = None

    def draw(
        self, surface: pygame.Surface, layout: Layout, playback: Playback
    ) -> None:
        """Draw the map at the moment ``playback`` is at.

        The links glow for the turn on screen; the places and the
        counts show the last turn that is over.

        Args:
            surface: Where to draw, as big as the layout's window.
            layout: The layout of that window.
            playback: The replay clock and its frames.
        """
        surface.fill(BACKGROUND)
        shown = playback.frames[playback.turn]
        for connection in layout.links.values():
            load = shown.link_load.get(connection.name, 0)
            self._draw_link(surface, layout, connection, load)
        for zone in self.network.zones.values():
            self._draw_zone(surface, layout, zone, playback.time)
            self._draw_places(surface, layout, zone, playback.settled)
            self._draw_labels(surface, layout, zone, playback)
        self._draw_drones(surface, layout, playback)

    def count_text(self, zone: Zone, playback: Playback) -> str:
        """Return the line under a zone's name, for the last turn over.

        The start counts the drones waiting in it, the end the drones
        delivered out of all of them, and any other zone its places:
        used (drones inside or flying in) out of its max.
        """
        settled = playback.settled
        if zone is self.network.start:
            return f"{settled.waiting} waiting"
        if zone is self.network.end:
            total = playback.frames[0].waiting
            return f"{settled.delivered}/{total} delivered"
        if not zone.is_accessible:
            return ""
        used = sum(
            1 for pose in settled.poses.values() if pose.zone == zone.name
        )
        return f"{used}/{zone.max_drones}"

    def name_label(self, name: str, layout: Layout) -> str:
        """Return the name of zone ``name`` as written in ``layout``.

        A name wider than the room to the nearest zone is cut with an
        ellipsis. The cut names are worked out once per layout.
        """
        if self._names_for is not layout:
            self._names = {
                each: self._fit(each, self._room(layout, each))
                for each in layout.centers
            }
            self._names_for = layout
        return self._names[name]

    def badge(self, zone: Zone) -> str:
        """Return the letter on a zone's badge, or "" for none.

        S and E mark the start and the end, P a priority zone, and a
        restricted zone shows how many turns it takes to enter.
        """
        if zone is self.network.start:
            return "S"
        if zone is self.network.end:
            return "E"
        if isinstance(zone, PriorityZone):
            return "P"
        if isinstance(zone, RestrictedZone):
            return str(zone.entry_cost)
        return ""

    @staticmethod
    def zone_color(zone: Zone, time: float) -> pygame.Color:
        """Return the fill of ``zone`` at replay time ``time``.

        Any word is a valid color in a map, and pygame knows 17 of the
        18 the maps use. ``rainbow`` turns its hue once every 4 turns;
        an unknown name, or none, gives gray; blocked zones are dark.
        """
        if not zone.is_accessible:
            return pygame.Color(BLOCKED)
        if zone.color is None:
            return pygame.Color(NO_COLOR)
        if zone.color.lower() == "rainbow":
            return SceneRenderer._hsv(time * 90 % 360, 100)
        try:
            return pygame.Color(zone.color)
        except ValueError:
            return pygame.Color(NO_COLOR)

    @staticmethod
    def drone_color(drone: int) -> pygame.Color:
        """Return the color of drone ``drone``: one hue per id."""
        return SceneRenderer._hsv(drone * GOLDEN % 1 * 360, 55)

    @staticmethod
    def _hsv(hue: float, saturation: float) -> pygame.Color:
        """Return the color of ``hue``, in degrees, at full brightness.

        It goes through the ``hsva`` property, which pygame and
        pygame-ce both have: ``Color.from_hsva`` is pygame-ce only.
        """
        color = pygame.Color(0, 0, 0)
        color.hsva = (hue, saturation, 100, 100)
        return color

    def _draw_link(
        self,
        surface: pygame.Surface,
        layout: Layout,
        connection: Connection,
        load: int,
    ) -> None:
        """Draw a link, thicker with capacity; a used one glows."""
        start = layout.centers[connection.zone_a.name]
        end = layout.centers[connection.zone_b.name]
        capacity = connection.max_link_capacity
        width = 1 + min(capacity, 5)
        if load == 0:
            pygame.draw.line(surface, LINK, start, end, width)
            return
        pygame.draw.line(surface, GLOW, start, end, width + 2)
        # load/capacity is written beside the middle of the link, off
        # the drone that stops there between the turns of a flight.
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        shift = width / 2 + layout.drone_radius + 10
        beside = (
            (start[0] + end[0]) / 2 + dy / length * shift,
            (start[1] + end[1]) / 2 - dx / length * shift,
        )
        text = f"{load}/{capacity}"
        self._write(surface, text, SMALL_SIZE, GLOW, BACKGROUND, beside)

    def _draw_zone(
        self, surface: pygame.Surface, layout: Layout, zone: Zone, time: float
    ) -> None:
        """Draw a zone's circle, the outline of its type and its badge."""
        center = layout.centers[zone.name]
        radius = self._radius(layout, zone)
        fill = self.zone_color(zone, time)
        pygame.draw.circle(surface, fill, center, radius)
        if not zone.is_accessible:
            x, y = center
            arm = radius * 0.6
            pygame.draw.circle(surface, CROSS, center, radius, 2)
            pygame.draw.line(
                surface, CROSS, (x - arm, y - arm), (x + arm, y + arm), 3
            )
            pygame.draw.line(
                surface, CROSS, (x - arm, y + arm), (x + arm, y - arm), 3
            )
            return
        if isinstance(zone, RestrictedZone):
            self._draw_dashes(surface, center, radius)
        else:
            pygame.draw.circle(surface, OUTLINE, center, radius, 2)
        if isinstance(zone, PriorityZone):
            pygame.draw.circle(surface, OUTLINE, center, radius + 4, 2)
        letter = self.badge(zone)
        if letter:
            spot = (center[0] + radius * 0.8, center[1] - radius * 0.8)
            size = min(max(7.0, radius * 0.45), 11.0)
            pygame.draw.circle(surface, OUTLINE, spot, size)
            self._write(
                surface, letter, round(size * 1.8), BACKGROUND, OUTLINE, spot
            )

    def _draw_places(
        self,
        surface: pygame.Surface,
        layout: Layout,
        zone: Zone,
        frame: Frame,
    ) -> None:
        """Draw a zone's places: a hole each, and a ring if reserved.

        The start and the end show counters instead, and a blocked
        zone has no places. The drones inside take the first places,
        so the drones still flying in have the next ones.
        """
        if zone.unlimited or not zone.is_accessible:
            return
        using = [
            pose for pose in frame.poses.values() if pose.zone == zone.name
        ]
        inside = sum(1 for pose in using if pose.link is None)
        places = min(zone.max_drones, MAX_SLOTS)
        if places > 1:
            # A zone for one drone keeps it at the centre: no hole.
            for rank in range(places):
                where = layout.slot(zone.name, rank)
                pygame.draw.circle(
                    surface, BACKGROUND, where, layout.drone_radius / 2
                )
        for rank in range(inside, len(using)):
            where = layout.slot(zone.name, rank)
            pygame.draw.circle(surface, WHITE, where, layout.drone_radius, 2)

    def _draw_labels(
        self,
        surface: pygame.Surface,
        layout: Layout,
        zone: Zone,
        playback: Playback,
    ) -> None:
        """Write the zone's name and its count under its circle."""
        x, y = layout.centers[zone.name]
        # Below the circle, and below a priority zone's second outline.
        top = y + self._radius(layout, zone) + 6
        if self.show_names:
            name = self.name_label(zone.name, layout)
            image = self._text(name, NAME_SIZE, TEXT, BACKGROUND)
            surface.blit(image, image.get_rect(midtop=(x, top)))
            top += image.get_height()
        count = self.count_text(zone, playback)
        if count:
            image = self._text(count, SMALL_SIZE, MUTED, BACKGROUND)
            surface.blit(image, image.get_rect(midtop=(x, top)))

    def _draw_drones(
        self, surface: pygame.Surface, layout: Layout, playback: Playback
    ) -> None:
        """Draw the drones in play, each with its id on it.

        A drone that waited this turn is dimmed; a drone on a link has
        a white ring.
        """
        positions = playback.positions(layout)
        if not positions:
            return
        poses = playback.frames[playback.turn].poses
        # There are no positions on turn 0, so turn - 1 is a real frame.
        before = playback.frames[playback.turn - 1].poses
        radius = layout.drone_radius
        for drone, point in positions.items():
            color = self.drone_color(drone)
            if before.get(drone) == poses[drone]:
                # The same pose at both ends of the turn: it waited.
                color = color.lerp(BACKGROUND, 0.6)
            pygame.draw.circle(surface, color, point, radius)
            if poses[drone].link is not None:
                pygame.draw.circle(surface, WHITE, point, radius + 3, 2)
            # The id's box has the drone's color: a long id makes a pill.
            box = (color.r, color.g, color.b)
            size = round(2 * radius)
            self._write(surface, str(drone), size, BACKGROUND, box, point)

    @staticmethod
    def _draw_dashes(
        surface: pygame.Surface, center: Point, radius: float
    ) -> None:
        """Draw a dashed circle: 12 dashes with gaps between them."""
        bounds = pygame.Rect(0, 0, round(2 * radius), round(2 * radius))
        bounds.center = (round(center[0]), round(center[1]))
        for dash in range(12):
            start = dash * math.pi / 6
            pygame.draw.arc(surface, OUTLINE, bounds, start, start + 0.3, 2)

    def _radius(self, layout: Layout, zone: Zone) -> float:
        """Return a zone's radius: the start and the end are bigger."""
        if zone in (self.network.start, self.network.end):
            return layout.zone_radius * 1.25
        return layout.zone_radius

    @staticmethod
    def _room(layout: Layout, name: str) -> float:
        """Return how wide the name of zone ``name`` may be written.

        A name may not reach the nearest other zone: the room is the
        distance to it, less a small gap.
        """
        here = layout.centers[name]
        nearest = min(
            math.dist(here, there)
            for other, there in layout.centers.items()
            if other != name
        )
        return nearest - 8

    def _fit(self, text: str, room: float) -> str:
        """Return ``text``, cut with an ellipsis if wider than ``room``."""
        font = self._font(NAME_SIZE)
        if font.size(text)[0] <= room:
            return text
        while len(text) > 1 and font.size(text + ELLIPSIS)[0] > room:
            text = text[:-1]
        return text + ELLIPSIS

    def _write(
        self,
        surface: pygame.Surface,
        text: str,
        size: int,
        ink: RGB,
        box: RGB,
        center: Point,
    ) -> None:
        """Write ``text`` centered on ``center``."""
        image = self._text(text, size, ink, box)
        surface.blit(image, image.get_rect(center=center))

    def _text(
        self, text: str, size: int, ink: RGB, box: RGB
    ) -> pygame.Surface:
        """Return ``text`` in ``ink`` on a ``box`` background.

        The box has the color of what is behind the text, so a line
        passing under a label doesn't cross its letters. Each text is
        drawn once, then reused: drawing text is the slow part.
        """
        key = (text, size, ink, box)
        if key not in self._texts:
            image = self._font(size).render(text, True, ink, box)
            self._texts[key] = image
        return self._texts[key]

    def _font(self, size: int) -> pygame.font.Font:
        """Return pygame's default font at ``size``, loaded once."""
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]
