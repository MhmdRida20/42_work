"""Tests for the Playback: the replay clock and the drones' positions.

Most tests replay edge_restricted_end.map in a 1280 x 800 window:
s is at (480, 390), a at (640, 390) and e at (800, 390), so the middle
of the link a-e is (720, 390). D1 leaves on turn 1, flies a-e on
turns 2 and 3; D2 leaves on turn 2, flies a-e on turns 4 and 5.
"""

from __future__ import annotations

import pytest

from parsing.parser import Parser
from pathfinding.space_time import SpaceTimeFinder
from simulation.scheduler import Scheduler
from simulation.simulator import Simulator
from visualization.frames import Frame, Pose, Recorder
from visualization.layout import Layout, Point
from visualization.playback import Playback

RESTRICTED_END = "maps/edge_restricted_end.map"


def _replay(map_path: str) -> tuple[Playback, Layout]:
    """Record a run of the map; return its playback and its layout."""
    network, nb_drones = Parser().parse_file(map_path)
    routes = SpaceTimeFinder(nb_drones).find_paths(network)
    drones = Scheduler().assign(network, routes, nb_drones)
    recorder = Recorder()
    recorder.show_network(network)
    Simulator(network, drones).run(recorder)
    return Playback(recorder.frames), Layout(network, 1280, 800)


def _at(playback: Playback, layout: Layout, time: float) -> dict[int, Point]:
    """Return the drones' positions at ``time``."""
    playback.time = time
    return playback.positions(layout)


def test_the_easing_is_gentle_at_both_ends() -> None:
    """A quarter of the turn covers 15.6% of the way, half covers half."""
    assert [Playback.ease(t) for t in (0, 0.25, 0.5, 0.75, 1)] == [
        0,
        0.15625,
        0.5,
        0.84375,
        1,
    ]


def test_time_counts_turns() -> None:
    """At x1 a turn lasts 600 ms; time 1.25 is a quarter of turn 2."""
    playback, _ = _replay(RESTRICTED_END)
    assert (playback.time, playback.turn, playback.progress) == (0, 0, 1)

    playback.update(300)
    assert (playback.time, playback.turn, playback.progress) == (0.5, 1, 0.5)
    playback.update(300)
    assert (playback.turn, playback.progress) == (1, 1)
    playback.update(150)
    assert (playback.turn, playback.progress) == (2, 0.25)


def test_speed_doubles_and_halves_between_bounds() -> None:
    """From x8 (75 ms a turn) down to x0.25 (2400 ms a turn)."""
    playback, _ = _replay(RESTRICTED_END)
    for _ in range(5):
        playback.faster()
    assert playback.speed == 8
    playback.update(75)
    assert playback.time == 1

    for _ in range(10):
        playback.slower()
    assert playback.speed == 0.25
    playback.update(600)
    assert playback.time == 1.25


def test_pause_stops_the_clock() -> None:
    """Paused, time doesn't move; played again, it goes on."""
    playback, _ = _replay(RESTRICTED_END)
    playback.toggle()
    playback.update(1000)
    assert (playback.playing, playback.time) == (False, 0)

    playback.toggle()
    playback.update(300)
    assert (playback.playing, playback.time) == (True, 0.5)


def test_playing_stops_on_the_last_turn() -> None:
    """5 turns take 3000 ms: the clock stops on turn 5, even overshot.

    Playing again from there restarts from turn 0.
    """
    playback, _ = _replay(RESTRICTED_END)
    playback.update(3000)
    assert (playback.time, playback.turn, playback.playing) == (5, 5, False)

    playback.toggle()
    assert (playback.time, playback.playing) == (0, True)
    playback.update(10_000)
    assert (playback.time, playback.playing) == (5, False)


def test_seek_and_steps_pause_inside_the_run() -> None:
    """Seeking and stepping pause, and never leave turns 0 to 5."""
    playback, _ = _replay(RESTRICTED_END)
    playback.seek(3)
    assert (playback.time, playback.playing) == (3, False)
    playback.next_turn()
    assert playback.time == 4
    playback.previous_turn()
    playback.previous_turn()
    assert playback.time == 2

    playback.seek(-2)
    playback.previous_turn()
    assert playback.time == 0
    playback.seek(99)
    playback.next_turn()
    assert playback.time == 5

    playback.restart()
    assert (playback.time, playback.playing) == (0, True)


def test_steps_from_the_middle_of_a_turn() -> None:
    """Halfway through turn 3, the frames around are 2 and 3."""
    playback, _ = _replay(RESTRICTED_END)
    playback.time = 2.5
    playback.next_turn()
    assert playback.time == 3

    playback.time = 2.5
    playback.previous_turn()
    assert playback.time == 2


def test_nothing_moves_before_the_first_turn() -> None:
    """On turn 0 both drones are in the start's counter."""
    playback, layout = _replay(RESTRICTED_END)
    assert playback.positions(layout) == {}
    assert playback.settled.waiting == 2


def test_a_drone_leaves_the_start_gently() -> None:
    """Turn 1: D1 goes from s to a, a quarter of the turn covers 25 px."""
    playback, layout = _replay(RESTRICTED_END)
    assert [_at(playback, layout, t) for t in (0.25, 0.5, 1)] == [
        {1: (505, 390)},
        {1: (560, 390)},
        {1: (640, 390)},
    ]


def test_a_two_turn_flight_stops_halfway() -> None:
    """D1 is on the middle of a-e after turn 2 and on e after turn 3.

    Meanwhile D2 leaves the start on turn 2 and waits in a on turn 3.
    """
    playback, layout = _replay(RESTRICTED_END)
    assert [_at(playback, layout, t) for t in (1.5, 2, 2.5, 3)] == [
        {1: (680, 390), 2: (560, 390)},
        {1: (720, 390), 2: (640, 390)},
        {1: (760, 390), 2: (640, 390)},
        {1: (800, 390), 2: (640, 390)},
    ]


def test_a_delivered_drone_joins_the_counter_when_its_turn_ends() -> None:
    """D1 lands on turn 3: the counter changes when that turn ends.

    On turn 4 D1 rests in the end, so only D2 is drawn.
    """
    playback, layout = _replay(RESTRICTED_END)
    playback.time = 2.99
    assert playback.settled.delivered == 0
    playback.time = 3
    assert playback.settled.delivered == 1

    assert _at(playback, layout, 3.5) == {2: (680, 390)}


def test_drones_inside_a_zone_take_its_slots_by_id() -> None:
    """The frame lists D2 first, yet D1 gets slot 0, at the top."""
    network, _ = Parser().parse_lines(
        [
            "nb_drones: 2",
            "start_hub: s 0 0",
            "hub: a 1 0 [max_drones=2]",
            "end_hub: e 2 0",
            "connection: s-a [max_link_capacity=2]",
            "connection: a-e",
        ]
    )
    frames = [
        Frame(0, "", {}, 2, 0, {}),
        Frame(1, "D1-a D2-a", {2: Pose("a"), 1: Pose("a")}, 0, 0, {}),
    ]
    playback = Playback(frames)
    playback.seek(1)

    assert playback.positions(Layout(network, 1280, 800)) == {
        1: pytest.approx((640, 375.7)),
        2: pytest.approx((640, 404.3)),
    }
