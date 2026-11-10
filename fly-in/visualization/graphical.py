"""Graphical view: draw one moment of the replay with pygame-ce.

The SceneRenderer draws the map (links under zones under drones), then
the two bars around it, then the panels on top: the legend, the
summary at the end of the run and the tooltip. The moment comes from a
Playback and the pixels from a Layout, so the window shows exactly
what the recorded frames say. The picture is drawn again from nothing
each time; only the text, the slow part, is kept from one picture to
the next.
"""

from __future__ import annotations

import math
import os

from models.connection import Connection
from models.network import Network
from models.zone import PriorityZone, RestrictedZone, Zone
from visualization.frames import Frame
from visualization.layout import BOTTOM_BAR, MAX_SLOTS, TOP_BAR, Layout, Point
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
BAR: RGB = (16, 18, 23)
PANEL: RGB = (36, 39, 48)

NAME_SIZE = 16
SMALL_SIZE = 14
# The space between a panel's or a bar's edge and its text.
PAD = 8
# The one-character "...", written as an escape to keep the file ASCII.
ELLIPSIS = "\u2026"
# Each drone id turns the hue by the golden ratio of a full turn, so
# drones with neighbouring ids get clearly different colors.
GOLDEN = 0.6180339887

HINTS = (
    "Space play/pause   Left/Right step   Up/Down speed   "
    "Home/End first/last   R restart   N names   L legend   Q quit"
)
LEGEND = (
    "S start, E end: counters instead of places",
    "plain outline: normal zone",
    "double outline, P: priority zone",
    "dashed outline, 2: restricted, 2 turns to enter",
    "crossed out: blocked zone, never entered",
    "dark hole: a free place",
    "white ring in a zone: a reserved place",
    "used/max: drones inside or flying in",
    "dimmed drone: it waited this turn",
    "white ring on a drone: it is on a link",
    "glowing link: used this turn, load/capacity",
)


class SceneRenderer:
    """Draw the map at one moment of the replay.

    Attributes:
        network: The network drawn.
        title: What the top bar starts with, such as the map's path.
        metrics: The run's metrics, shown when the replay is over.
        show_names: Whether zone names are written (the N key).
        show_legend: Whether the legend is shown (the L key).
    """

    def __init__(
        self,
        network: Network,
        title: str = "",
        metrics: dict[str, float] | None = None,
    ) -> None:
        """Start pygame's fonts; each font and text is made when needed.

        Args:
            network: The parsed network.
            title: What the top bar starts with.
            metrics: The metrics of the run, as the simulator gave them.
        """
        pygame.font.init()
        self.network = network
        self.title = title
        self.metrics = dict(metrics or {})
        self.show_names = True
        self.show_legend = False
        self._fonts: dict[int, pygame.font.Font] = {}
        self._texts: dict[tuple[str, int, RGB, RGB], pygame.Surface] = {}
        self._fits: dict[tuple[str, float], str] = {}
        self._names: dict[str, str] = {}
        self._names_for: Layout | None = None

    def draw(
        self,
        surface: pygame.Surface,
        layout: Layout,
        playback: Playback,
        mouse: Point | None = None,
    ) -> None:
        """Draw the moment ``playback`` is at.

        The links glow for the turn on screen; the places and the
        counts show the last turn that is over.

        Args:
            surface: Where to draw, as big as the layout's window.
            layout: The layout of that window.
            playback: The replay clock and its frames.
            mouse: Where the mouse is, for the tooltip; None for none.
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
        self._draw_bars(surface, layout, playback)
        if self.show_legend:
            corner = (layout.width - PAD, layout.height - BOTTOM_BAR - PAD)
            self._draw_panel(surface, list(LEGEND), bottomright=corner)
        if self.metrics and playback.time == playback.last:
            top = (layout.width / 2, TOP_BAR + PAD)
            self._draw_panel(surface, self.summary_lines(), midtop=top)
        if mouse is not None:
            lines = self.tooltip(layout, playback, mouse)
            if lines:
                below = (mouse[0] + 16, mouse[1] + 16)
                self._draw_panel(surface, lines, topleft=below)

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

    def bar_texts(
        self, layout: Layout, playback: Playback
    ) -> tuple[str, str, str, str]:
        """Return the texts of the bars: title, turn, state, line.

        The line is the movement line of the turn on screen, exactly
        as printed, cut with an ellipsis if wider than the window.
        """
        if playback.playing:
            state = "playing"
        elif playback.time == playback.last:
            state = "done"
        else:
            state = "paused"
        line = playback.frames[playback.turn].line
        return (
            self.title,
            f"Turn {playback.turn} / {playback.last}",
            f"{state} x{playback.speed:g}",
            self._fit(line, layout.width - 2 * PAD),
        )

    def zone_lines(self, zone: Zone, playback: Playback) -> list[str]:
        """Return a zone's tooltip: its name, kind, count and drones.

        Like the counts, it shows the last turn that is over.
        """
        kind = type(zone).__name__.removesuffix("Zone").lower()
        if zone is self.network.start:
            kind = "start, " + kind
        elif zone is self.network.end:
            kind = "end, " + kind
        if not zone.is_accessible:
            kind += ", never entered"
        elif zone.entry_cost > 1:
            kind += f", {zone.entry_cost} turns to enter"
        lines = [zone.name, kind]
        count = self.count_text(zone, playback)
        if count:
            lines.append(count if zone.unlimited else f"used: {count}")
        here = [
            (drone, pose)
            for drone, pose in sorted(playback.settled.poses.items())
            if pose.zone == zone.name
        ]
        inside = [f"D{drone}" for drone, pose in here if pose.link is None]
        coming = [f"D{drone}" for drone, pose in here if pose.link is not None]
        # Drones resting in the start or the end are in its counter.
        if inside and not zone.unlimited:
            lines.append("inside: " + " ".join(inside))
        if coming:
            lines.append("flying in: " + " ".join(coming))
        return lines

    def drone_lines(self, drone: int, playback: Playback) -> list[str]:
        """Return a drone's tooltip: its id and what it does this turn."""
        pose = playback.frames[playback.turn].poses[drone]
        before = playback.frames[playback.turn - 1].poses.get(drone)
        if pose.link is not None:
            doing = f"flying to {pose.zone} on {pose.link}"
        elif before == pose:
            doing = f"waiting in {pose.zone}"
        else:
            doing = f"moving to {pose.zone}"
        return [f"D{drone}", doing]

    def tooltip(
        self, layout: Layout, playback: Playback, mouse: Point
    ) -> list[str]:
        """Return the tooltip of what is under ``mouse``, or [] if none.

        Drones are drawn over zones, so they are looked at first, the
        last one drawn, which is on top, first of all.
        """
        positions = playback.positions(layout)
        for drone in reversed(positions):
            if math.dist(positions[drone], mouse) <= layout.drone_radius:
                return self.drone_lines(drone, playback)
        for zone in self.network.zones.values():
            center = layout.centers[zone.name]
            if math.dist(center, mouse) <= self._radius(layout, zone):
                return self.zone_lines(zone, playback)
        return []

    def summary_lines(self) -> list[str]:
        """Return the panel shown when the replay is over.

        The metrics are written as in the terminal: whole numbers
        without decimals, the others with two.
        """
        lines = ["Run complete"]
        for name, value in self.metrics.items():
            if float(value).is_integer():
                lines.append(f"{name}: {int(value)}")
            else:
                lines.append(f"{name}: {value:.2f}")
        return lines

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

    def _draw_bars(
        self, surface: pygame.Surface, layout: Layout, playback: Playback
    ) -> None:
        """Draw the top bar and the bottom bar, with their texts.

        Top: the title on the left, the turn in the middle and the
        state on the right. Bottom: the movement line, then the keys.
        """
        width, height = layout.width, layout.height
        bottom = height - BOTTOM_BAR
        pygame.draw.rect(surface, BAR, (0, 0, width, TOP_BAR))
        pygame.draw.rect(surface, BAR, (0, bottom, width, BOTTOM_BAR))
        title, turn, state, line = self.bar_texts(layout, playback)
        middle = TOP_BAR / 2
        image = self._text(title, NAME_SIZE, TEXT, BAR)
        surface.blit(image, image.get_rect(midleft=(PAD, middle)))
        self._write(surface, turn, NAME_SIZE, TEXT, BAR, (width / 2, middle))
        image = self._text(state, NAME_SIZE, MUTED, BAR)
        surface.blit(image, image.get_rect(midright=(width - PAD, middle)))
        image = self._text(line, NAME_SIZE, TEXT, BAR)
        surface.blit(image, image.get_rect(midleft=(PAD, bottom + 18)))
        image = self._text(HINTS, SMALL_SIZE, MUTED, BAR)
        surface.blit(image, image.get_rect(midleft=(PAD, bottom + 42)))

    def _draw_panel(
        self, surface: pygame.Surface, lines: list[str], **anchor: Point
    ) -> None:
        """Draw ``lines`` on a framed panel, placed by ``anchor``.

        ``anchor`` is one point of the panel, such as ``topleft=(x, y)``.
        A panel that would cross an edge of the window is moved in.
        """
        images = [self._text(line, SMALL_SIZE, TEXT, PANEL) for line in lines]
        width = max(image.get_width() for image in images) + 2 * PAD
        height = sum(image.get_height() for image in images) + 2 * PAD
        panel = pygame.Surface((width, height))
        panel.fill(PANEL)
        y = PAD
        for image in images:
            panel.blit(image, (PAD, y))
            y += image.get_height()
        place = panel.get_rect(**anchor).clamp(surface.get_rect())
        surface.blit(panel, place)
        pygame.draw.rect(surface, LINK, place, 1)

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
        """Return ``text``, cut with an ellipsis if wider than ``room``.

        A cut text is kept, like a drawn one: cutting a long movement
        line one letter at a time takes about 18 ms.
        """
        key = (text, room)
        if key not in self._fits:
            font = self._font(NAME_SIZE)
            cut = text
            if font.size(cut)[0] > room:
                while len(cut) > 1 and font.size(cut + ELLIPSIS)[0] > room:
                    cut = cut[:-1]
                cut += ELLIPSIS
            self._fits[key] = cut
        return self._fits[key]

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
