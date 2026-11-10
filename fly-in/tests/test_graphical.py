"""Tests for the SceneRenderer: the map drawn at one moment.

The renderer draws on a plain pygame Surface, which needs no window.
Most tests read pixels of edge_restricted_end.map in a 1280 x 800
window: s is at (480, 390), a at (640, 390), e at (800, 390), and a
drone's radius is 8 px. D1 flies a-e on turns 2 and 3; D2 moves into
a on turn 2 and waits there on turn 3.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pygame
import pytest

from parsing.parser import Parser
from pathfinding.space_time import SpaceTimeFinder
from simulation.scheduler import Scheduler
from simulation.simulator import Simulator
from visualization.frames import Frame, Pose, Recorder
from visualization.graphical import (
    BACKGROUND,
    BLOCKED,
    CROSS,
    ELLIPSIS,
    GLOW,
    LINK,
    NO_COLOR,
    OUTLINE,
    WHITE,
    SceneRenderer,
)
from visualization.layout import Layout, Point
from visualization.playback import Playback

RESTRICTED_END = "maps/edge_restricted_end.map"
# Every map with a solution, as in test_referee.py.
MAPS = [
    "maps/example.map",
    "maps/easy_linear.map",
    "maps/easy/01_linear_path.txt",
    "maps/easy/02_simple_fork.txt",
    "maps/easy/03_basic_capacity.txt",
    "maps/medium/01_dead_end_trap.txt",
    "maps/medium/02_circular_loop.txt",
    "maps/medium/03_priority_puzzle.txt",
    "maps/hard/01_maze_nightmare.txt",
    "maps/hard/02_capacity_hell.txt",
    "maps/hard/03_ultimate_challenge.txt",
    "maps/challenger/01_the_impossible_dream.txt",
    "maps/edge_start_to_end.map",
    "maps/edge_restricted_end.map",
    "maps/edge_two_restricted.map",
    "maps/edge_priority_tie.map",
    "maps/edge_crowded_tie.map",
    "maps/edge_1000_drones.map",
]


def _replay(map_path: str) -> tuple[Playback, Layout, SceneRenderer]:
    """Record a run of the map; return its playback, layout, renderer."""
    network, nb_drones = Parser().parse_file(map_path)
    routes = SpaceTimeFinder(nb_drones).find_paths(network)
    drones = Scheduler().assign(network, routes, nb_drones)
    recorder = Recorder()
    recorder.show_network(network)
    Simulator(network, drones).run(recorder)
    layout = Layout(network, 1280, 800)
    return Playback(recorder.frames), layout, SceneRenderer(network)


def _draw(
    renderer: SceneRenderer, layout: Layout, playback: Playback, time: float
) -> pygame.Surface:
    """Return a new picture of the moment ``time``."""
    surface = pygame.Surface((layout.width, layout.height))
    playback.time = time
    renderer.draw(surface, layout, playback)
    return surface


def _at(surface: pygame.Surface, point: Point) -> pygame.Color:
    """Return the color of the pixel at ``point``."""
    return surface.get_at((round(point[0]), round(point[1])))


def _amber(surface: pygame.Surface, area: pygame.Rect) -> int:
    """Count the pixels of ``area`` that look like GLOW text.

    Text is smoothed into the background, so few of its pixels have
    exactly the GLOW color.
    """
    count = 0
    for x in range(area.left, area.right):
        for y in range(area.top, area.bottom):
            color = surface.get_at((x, y))
            if color.r > 200 and color.b < 120:
                count += 1
    return count


def test_importing_the_view_prints_nothing() -> None:
    """pygame's banner would land among the movement lines on stdout."""
    env = dict(os.environ)
    env.pop("PYGAME_HIDE_SUPPORT_PROMPT", None)
    result = subprocess.run(
        [sys.executable, "-c", "import visualization.graphical"],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert result.stdout == ""


@pytest.mark.parametrize("map_path", MAPS)
def test_every_map_draws_at_every_moment(map_path: str) -> None:
    """Each turn draws halfway through and at its end.

    Before the first turn no drone is drawn, so each zone's centre
    shows its fill, or the cross of a blocked zone.
    """
    playback, layout, renderer = _replay(map_path)
    surface = _draw(renderer, layout, playback, 0)
    for zone in renderer.network.zones.values():
        fill = SceneRenderer.zone_color(zone, 0)
        expected = fill if zone.is_accessible else pygame.Color(CROSS)
        assert _at(surface, layout.centers[zone.name]) == expected

    for turn in range(1, playback.last + 1):
        for time in (turn - 0.5, turn):
            playback.time = time
            renderer.draw(surface, layout, playback)


def test_zone_colors_come_from_the_map() -> None:
    """Known names in any case; rainbow turns; the rest is gray or dark."""
    network, _ = Parser().parse_lines(
        [
            "nb_drones: 1",
            "start_hub: s 0 0 [color=DarkRed]",
            "hub: a 1 0 [color=Rainbow]",
            "hub: b 2 0 [color=sky]",
            "hub: c 3 0",
            "hub: d 4 0 [zone=blocked color=red]",
            "end_hub: e 5 0 [color=lime]",
            "connection: s-a",
            "connection: a-e",
        ]
    )
    zones = network.zones
    color = SceneRenderer.zone_color

    assert color(zones["s"], 0) == pygame.Color("darkred")
    assert color(zones["e"], 0) == pygame.Color("lime")
    assert color(zones["a"], 0) == pygame.Color(255, 0, 0)
    assert color(zones["a"], 1) == pygame.Color(127, 255, 0)
    assert color(zones["b"], 0) == pygame.Color(NO_COLOR)
    assert color(zones["c"], 0) == pygame.Color(NO_COLOR)
    assert color(zones["d"], 0) == pygame.Color(BLOCKED)


def test_badges_mark_the_start_the_end_and_the_types() -> None:
    """The start and the end come first: this start is also priority."""
    network, _ = Parser().parse_lines(
        [
            "nb_drones: 1",
            "start_hub: s 0 0 [zone=priority]",
            "hub: p 1 0 [zone=priority]",
            "hub: r 2 0 [zone=restricted]",
            "hub: n 3 0",
            "end_hub: e 4 0 [zone=restricted]",
            "connection: s-p",
            "connection: p-e",
        ]
    )
    renderer = SceneRenderer(network)
    badges = [renderer.badge(zone) for zone in network.zones.values()]
    assert badges == ["S", "P", "2", "", "E"]


def test_a_zone_type_shows_without_its_color() -> None:
    """Dashes, a second outline, a badge, a bigger circle, a cross.

    Gray zones on one row, 160 px apart at y 390: s at x 240, r 400,
    p 560, n 720, b 880 and e 1040. Each point is checked on a typed
    zone and, where it helps, at the same spot on the plain zone n.
    """
    network, _ = Parser().parse_lines(
        [
            "nb_drones: 1",
            "start_hub: s 0 0",
            "hub: r 1 0 [zone=restricted]",
            "hub: p 2 0 [zone=priority]",
            "hub: n 3 0",
            "hub: b 4 0 [zone=blocked max_drones=4]",
            "end_hub: e 5 0",
            "connection: s-r",
            "connection: r-p",
            "connection: p-n",
            "connection: n-e",
        ]
    )
    playback = Playback([Frame(0, "", {}, 1, 0, {})])
    layout = Layout(network, 1280, 800)
    surface = _draw(SceneRenderer(network), layout, playback, 0)
    expected = {
        (423, 380): NO_COLOR,  # r: a gap between two dashes
        (743, 380): OUTLINE,  # n: the same spot, on a plain outline
        (560, 419): OUTLINE,  # p: its second outline, 29 px down
        (720, 419): BACKGROUND,  # n: nothing there
        (427, 363): OUTLINE,  # r: its badge
        (747, 363): BACKGROUND,  # n: no badge
        (1040, 419): NO_COLOR,  # e: bigger, so 29 px down is inside
        (880, 415): CROSS,  # b: the outline of a blocked zone
        (880, 376): BLOCKED,  # b: no places, though it holds 4
    }
    for point, color in expected.items():
        assert _at(surface, point) == pygame.Color(color), point


def test_neighbouring_drones_get_far_apart_hues() -> None:
    """Each id turns the hue by 0.618 of a full turn: 222.5 degrees."""
    hues = [SceneRenderer.drone_color(drone).hsva[0] for drone in (1, 2, 3)]
    assert hues == pytest.approx([222.5, 85.0, 307.5], abs=1)


def test_a_link_glows_while_its_turn_plays() -> None:
    """a-e is free on turn 1 and used on turn 2, from its very start.

    The pixel checked is between the middle of a-e and e, where no
    drone passes on these turns.
    """
    playback, layout, renderer = _replay(RESTRICTED_END)
    on_link = (760, 390)
    link, glow = pygame.Color(LINK), pygame.Color(GLOW)

    assert _at(_draw(renderer, layout, playback, 1), on_link) == link
    assert _at(_draw(renderer, layout, playback, 1.5), on_link) == glow
    assert _at(_draw(renderer, layout, playback, 2), on_link) == glow


def test_a_used_link_shows_its_load_beside_its_middle() -> None:
    """On turn 2, "1/1" is written 19 px above the middle of a-e."""
    playback, layout, renderer = _replay(RESTRICTED_END)
    label = pygame.Rect(700, 362, 40, 16)

    assert _amber(_draw(renderer, layout, playback, 1), label) == 0
    assert _amber(_draw(renderer, layout, playback, 2), label) > 0


def test_a_flying_drone_has_a_white_ring() -> None:
    """After turn 2, D1 is on the middle of a-e and D2 is inside a.

    The ring is 3 px out from the 8 px disc, so it crosses the point
    10 px under D1. Under D2, which isn't flying, is a's gray.
    """
    playback, layout, renderer = _replay(RESTRICTED_END)
    surface = _draw(renderer, layout, playback, 2)

    assert _at(surface, (720, 400)) == pygame.Color(WHITE)
    assert _at(surface, (640, 400)) == pygame.Color(NO_COLOR)


def test_a_drone_that_waited_is_dimmed() -> None:
    """D2 moves into a on turn 2, then waits there on turn 3."""
    playback, layout, renderer = _replay(RESTRICTED_END)
    left_of_id = (634, 390)
    bright = SceneRenderer.drone_color(2)
    dimmed = bright.lerp(BACKGROUND, 0.6)

    assert _at(_draw(renderer, layout, playback, 2), left_of_id) == bright
    assert _at(_draw(renderer, layout, playback, 3), left_of_id) == dimmed


def test_a_place_reserved_by_a_flying_drone_has_a_ring() -> None:
    """D1 flies into a on turn 1, D2 on turn 2: each reserves a place.

    a holds 2: its places are 14.3 px above and below its centre, and
    a ring passes 7 px right of its place. While turn 2 plays, the
    places still show turn 1: only the upper one is reserved.
    """
    network, _ = Parser().parse_lines(
        [
            "nb_drones: 2",
            "start_hub: s 0 0",
            "hub: a 1 0 [zone=restricted max_drones=2]",
            "end_hub: e 2 0",
            "connection: s-a [max_link_capacity=2]",
            "connection: a-e",
        ]
    )
    frames = [
        Frame(0, "", {}, 2, 0, {}),
        Frame(1, "D1-s-a", {1: Pose("a", "s-a", 0.5)}, 1, 0, {"s-a": 1}),
        Frame(
            2,
            "D1-a D2-s-a",
            {1: Pose("a"), 2: Pose("a", "s-a", 0.5)},
            0,
            0,
            {"s-a": 2},
        ),
    ]
    playback = Playback(frames)
    layout = Layout(network, 1280, 800)
    renderer = SceneRenderer(network)
    upper, lower = (647, 376), (647, 404)
    white, gray = pygame.Color(WHITE), pygame.Color(NO_COLOR)

    surface = _draw(renderer, layout, playback, 1.5)
    assert (_at(surface, upper), _at(surface, lower)) == (white, gray)
    assert renderer.count_text(network.zones["a"], playback) == "1/2"
    surface = _draw(renderer, layout, playback, 2)
    assert _at(surface, lower) == white
    assert renderer.count_text(network.zones["a"], playback) == "2/2"


def test_counts_show_the_last_turn_over() -> None:
    """Waiting in the start, used/max in a, delivered in the end."""
    playback, _, renderer = _replay(RESTRICTED_END)
    network = renderer.network
    zones = (network.start, network.zones["a"], network.end)

    playback.time = 0
    assert [renderer.count_text(zone, playback) for zone in zones] == [
        "2 waiting",
        "0/1",
        "0/2 delivered",
    ]
    playback.time = 2.5
    assert [renderer.count_text(zone, playback) for zone in zones] == [
        "0 waiting",
        "1/1",
        "0/2 delivered",
    ]
    playback.time = 3
    assert [renderer.count_text(zone, playback) for zone in zones] == [
        "0 waiting",
        "1/1",
        "1/2 delivered",
    ]


def test_a_blocked_zone_has_no_count() -> None:
    """obstacleX in example.map is never entered: nothing to count."""
    playback, _, renderer = _replay("maps/example.map")
    obstacle = renderer.network.zones["obstacleX"]
    assert renderer.count_text(obstacle, playback) == ""


def test_names_are_cut_to_fit_between_zones() -> None:
    """On the Challenger zones are 50 px apart: long names are cut.

    In a window twice as big there is room for them.
    """
    network, _ = Parser().parse_file(
        "maps/challenger/01_the_impossible_dream.txt"
    )
    renderer = SceneRenderer(network)
    small = Layout(network, 1280, 800)
    big = Layout(network, 2560, 1600)

    assert renderer.name_label("gate_hell1", small) == "gate_" + ELLIPSIS
    assert renderer.name_label("maze_trap_a1", small) == "maze" + ELLIPSIS
    assert renderer.name_label("start", small) == "start"
    assert renderer.name_label("gate_hell1", big) == "gate_hell1"


def test_names_can_be_turned_off() -> None:
    """With show_names off (the N key), the picture changes."""
    playback, layout, renderer = _replay(RESTRICTED_END)
    named = _draw(renderer, layout, playback, 0)
    renderer.show_names = False
    unnamed = _draw(renderer, layout, playback, 0)

    assert pygame.image.tobytes(named, "RGB") != pygame.image.tobytes(
        unnamed, "RGB"
    )
