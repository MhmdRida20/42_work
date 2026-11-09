"""Tests for the Layout: where zones, drone places and links are drawn.

Unless a test says otherwise, the window is 1280 x 800. Its map area
spans x 60..1220 and y 100..680: a 60 px margin all round, plus a
40 px bar at the top and a 60 px bar at the bottom.
"""

from __future__ import annotations

import pytest

from parsing.parser import Parser
from visualization.layout import Layout

# s and e are low, a is high: 8 units wide and 2 units tall.
PEAK = [
    "start_hub: s -4 -1",
    "hub: a 0 1",
    "end_hub: e 4 -1",
    "connection: s-a",
    "connection: a-e",
]

# One row of zones with 1, 4 and 20 places, between two big hubs.
SLOTS = [
    "start_hub: s 0 0 [max_drones=25]",
    "hub: one 1 0",
    "hub: four 2 0 [max_drones=4]",
    "hub: many 3 0 [max_drones=20]",
    "end_hub: e 4 0 [max_drones=25]",
    "connection: s-one",
    "connection: one-four",
    "connection: four-many",
    "connection: many-e",
]


def _from_lines(
    lines: list[str], width: int = 1280, height: int = 800
) -> Layout:
    """Lay out a map given as lines, without its nb_drones line."""
    network, _ = Parser().parse_lines(["nb_drones: 1", *lines])
    return Layout(network, width, height)


def _from_file(map_path: str) -> Layout:
    """Lay out a map file in a 1280 x 800 window."""
    network, _ = Parser().parse_file(map_path)
    return Layout(network, 1280, 800)


def test_y_points_up_and_negative_coordinates_fit() -> None:
    """a (y = 1) is drawn above s and e (y = -1).

    8 units across 1160 px give 145 px a unit. 2 units in 580 px would
    give 290, capped at 160, so the map is centered vertically.
    """
    assert _from_lines(PEAK).centers == {
        "s": (60, 550),
        "a": (640, 230),
        "e": (1220, 550),
    }


def test_a_one_row_map_is_centered() -> None:
    """4 zones 160 px apart, in the middle of the area both ways."""
    layout = _from_file("maps/easy/01_linear_path.txt")
    assert list(layout.centers.values()) == [
        (400, 390),
        (560, 390),
        (720, 390),
        (880, 390),
    ]


def test_the_challenger_fills_the_map_area() -> None:
    """23 units wide, 4 tall: each axis has its own scale.

    With one scale for both, the map would be a strip 202 px tall.
    """
    layout = _from_file("maps/challenger/01_the_impossible_dream.txt")
    xs = [x for x, _ in layout.centers.values()]
    ys = [y for _, y in layout.centers.values()]

    assert (min(xs), max(xs)) == pytest.approx((60, 1220))
    assert (min(ys), max(ys)) == pytest.approx((100, 680))
    assert layout.centers["start"] == pytest.approx((60, 390))
    assert layout.centers["impossible_goal"] == pytest.approx((1220, 390))


def test_zone_radius_stays_between_10_and_26() -> None:
    """28% of a grid step, between 10 and 26 px; a drone is a third.

    One row: 160 px steps give 44.8, cut to 26. The Challenger:
    1160/23 px steps give about 14.1. 40 units across: 29 px steps
    give 8.1, raised to 10. A drone is never under 5 px.
    """
    row = _from_file("maps/easy/01_linear_path.txt")
    challenger = _from_file("maps/challenger/01_the_impossible_dream.txt")
    wide = _from_lines(["start_hub: s 0 0", "end_hub: e 40 0"])

    assert (row.zone_radius, row.drone_radius) == (26, 8)
    assert challenger.zone_radius == pytest.approx(0.28 * 1160 / 23)
    assert challenger.drone_radius == 5
    assert (wide.zone_radius, wide.drone_radius) == (10, 5)


def test_a_resized_window_gets_a_new_layout() -> None:
    """At 1600 x 900 both scales are capped, so the map is centered."""
    assert _from_lines(PEAK, 1600, 900).centers == {
        "s": (160, 600),
        "a": (800, 280),
        "e": (1440, 600),
    }


def test_a_window_below_the_minimum_is_laid_out_at_the_minimum() -> None:
    """A 300 x 200 window is laid out as 800 x 560."""
    small = _from_lines(PEAK, 300, 200)
    minimum = _from_lines(PEAK, 800, 560)

    assert (small.width, small.height) == (800, 560)
    assert small.centers == minimum.centers


def test_hubs_and_zones_for_one_drone_use_the_center() -> None:
    """The start, the end and a zone for one drone have no ring."""
    layout = _from_lines(SLOTS)

    assert layout.slot("one", 0) == layout.centers["one"]
    assert layout.slot("s", 7) == layout.centers["s"]
    assert layout.slot("e", 24) == layout.centers["e"]


def test_slots_go_clockwise_from_the_top() -> None:
    """4 places on a ring of 0.55 x 26 = 14.3 px around (640, 390)."""
    layout = _from_lines(SLOTS)

    assert [layout.slot("four", rank) for rank in range(5)] == [
        pytest.approx((640, 375.7)),
        pytest.approx((654.3, 390)),
        pytest.approx((640, 404.3)),
        pytest.approx((625.7, 390)),
        pytest.approx((640, 375.7)),
    ]


def test_a_big_zone_shows_8_places() -> None:
    """Capacity 20 shows 8 places, so rank 8 is back on rank 0's place.

    Rank 2 is a quarter turn after the top: on the right.
    """
    layout = _from_lines(SLOTS)

    assert layout.slot("many", 2) == pytest.approx((814.3, 390))
    assert layout.slot("many", 8) == pytest.approx(layout.slot("many", 0))


def test_a_point_on_a_link_is_measured_from_the_other_end() -> None:
    """The map writes a-e: flying to e and flying back to a both work."""
    layout = _from_lines(PEAK)

    assert layout.on_link("a-e", "e", 0.5) == (930, 390)
    assert layout.on_link("a-e", "a", 0.25) == (1075, 470)
    assert layout.on_link("s-a", "a", 1.0) == layout.centers["a"]
    with pytest.raises(ValueError):
        layout.on_link("a-e", "s", 0.5)


def test_zones_on_the_same_coordinates_stay_visible() -> None:
    """s, a and b share (0, 0): a moves right by one radius, b by two."""
    layout = _from_lines(
        [
            "start_hub: s 0 0",
            "hub: a 0 0",
            "hub: b 0 0",
            "end_hub: e 1 0",
            "connection: s-a",
            "connection: a-b",
            "connection: b-e",
        ]
    )
    assert layout.centers == {
        "s": (560, 390),
        "a": (586, 390),
        "b": (612, 390),
        "e": (720, 390),
    }
