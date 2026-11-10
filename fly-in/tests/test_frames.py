"""Tests for the Recorder: the run turned into frames for the replay."""

from __future__ import annotations

import pytest

from models.zone import RestrictedZone
from parsing.parser import Parser
from pathfinding.space_time import SpaceTimeFinder
from simulation.scheduler import Scheduler
from simulation.simulator import Simulator
from visualization.frames import Frame, Pose, Recorder


def _record(map_path: str) -> Recorder:
    """Plan and run a map with a Recorder attached; return it."""
    network, nb_drones = Parser().parse_file(map_path)
    routes = SpaceTimeFinder(nb_drones).find_paths(network)
    drones = Scheduler().assign(network, routes, nb_drones)
    simulator = Simulator(network, drones)
    recorder = Recorder()
    recorder.show_network(network)
    simulator.run(recorder)
    recorder.show_summary(simulator.metrics())
    return recorder


def test_restricted_end_frame_by_frame() -> None:
    """Every frame of edge_restricted_end.map, turn 0 included.

    D1 stops halfway along a-e on turn 2 and lands on turn 3; D1 then
    rests in the end, so it has no pose on turns 4 and 5.
    """
    assert _record("maps/edge_restricted_end.map").frames == [
        Frame(0, "", {}, 2, 0, {}),
        Frame(1, "D1-a", {1: Pose("a")}, 1, 0, {"s-a": 1}),
        Frame(
            2,
            "D1-a-e D2-a",
            {1: Pose("e", "a-e", 0.5), 2: Pose("a")},
            0,
            0,
            {"a-e": 1, "s-a": 1},
        ),
        Frame(3, "D1-e", {1: Pose("e"), 2: Pose("a")}, 0, 1, {"a-e": 1}),
        Frame(4, "D2-a-e", {2: Pose("e", "a-e", 0.5)}, 0, 1, {"a-e": 1}),
        Frame(5, "D2-e", {2: Pose("e")}, 0, 2, {"a-e": 1}),
    ]


def test_a_move_straight_to_the_end_is_recorded() -> None:
    """A drone never in play still gets a pose on the turn it moves."""
    frames = _record("maps/edge_start_to_end.map").frames

    assert [frame.poses for frame in frames] == [
        {},
        {1: Pose("e")},
        {2: Pose("e")},
        {3: Pose("e")},
    ]
    assert [(frame.waiting, frame.delivered) for frame in frames] == [
        (3, 0),
        (2, 1),
        (1, 2),
        (0, 3),
    ]


def test_flight_progress_follows_the_entry_cost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If restricted zones cost 3 turns, a flight is at 1/3, then 2/3."""

    def three_turns(self: RestrictedZone) -> int:
        """Stand in for RestrictedZone.entry_cost: 3 turns, not 2."""
        return 3

    monkeypatch.setattr(RestrictedZone, "entry_cost", property(three_turns))
    frames = _record("maps/edge_restricted_end.map").frames

    flight = [
        frame.poses[1].progress
        for frame in frames
        if 1 in frame.poses and frame.poses[1].link is not None
    ]
    assert flight == [pytest.approx(1 / 3), pytest.approx(2 / 3)]


def test_frames_keep_only_drones_in_play() -> None:
    """1000 drones, yet no frame holds more than 4 poses."""
    frames = _record("maps/edge_1000_drones.map").frames

    assert len(frames) == 502
    assert max(len(frame.poses) for frame in frames) == 4


def test_summary_keeps_the_metrics() -> None:
    """show_summary stores the run's metrics for the end of the replay."""
    recorder = _record("maps/edge_start_to_end.map")
    assert recorder.metrics["turns"] == 3
