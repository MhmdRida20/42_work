"""Tests for the terminal visualizer, the run hook and the metrics."""

from __future__ import annotations

import glob
import re
import sys

import pytest

from main import main
from models.network import Network
from parsing.parser import Parser
from pathfinding.space_time import SpaceTimeFinder
from simulation.scheduler import Scheduler
from simulation.simulator import Simulator
from visualization.terminal import (
    ANSI_COLORS,
    ANSI_RESET,
    TerminalVisualizer,
)
from visualization.visualizer import Visualizer

ANSI_CODE = re.compile(r"\033\[[0-9;]*m")


def _plain(text: str) -> str:
    """Remove every ANSI color code from ``text``."""
    return ANSI_CODE.sub("", text)


def _planned(map_path: str) -> tuple[Network, Simulator]:
    """Parse and plan a map, returning its network and simulator."""
    network, nb_drones = Parser().parse_file(map_path)
    routes = SpaceTimeFinder(nb_drones).find_paths(network)
    drones = Scheduler().assign(network, routes, nb_drones)
    return network, Simulator(network, drones)


class RecordingVisualizer(Visualizer):
    """Remember every turn it is shown, and print nothing."""

    def __init__(self) -> None:
        """Start with no turns seen."""
        self.turns: list[tuple[int, str]] = []

    def show_network(self, network: Network) -> None:
        """Ignore the network."""

    def show_turn(self, turn_number: int, line: str, network: Network) -> None:
        """Record the turn."""
        self.turns.append((turn_number, line))

    def show_summary(self, metrics: dict[str, float]) -> None:
        """Ignore the metrics."""


def test_known_color_is_wrapped_in_ansi_codes() -> None:
    """A map color becomes its code, then the text, then a reset."""
    text = TerminalVisualizer().colorize("hub", "red")
    assert text == f"{ANSI_COLORS['red']}hub{ANSI_RESET}"


def test_unknown_or_missing_color_stays_plain() -> None:
    """No color, an unknown color or colors switched off: plain text."""
    assert TerminalVisualizer().colorize("hub", None) == "hub"
    assert TerminalVisualizer().colorize("hub", "sparkly") == "hub"
    assert TerminalVisualizer(use_color=False).colorize("hub", "red") == "hub"


def test_color_names_ignore_case() -> None:
    """color=Red and color=red look the same."""
    visualizer = TerminalVisualizer()
    assert visualizer.colorize("a", "Red") == visualizer.colorize("a", "red")


def test_rainbow_colors_each_letter() -> None:
    """rainbow gives every letter its own color code."""
    text = TerminalVisualizer().colorize("abc", "rainbow")
    assert _plain(text) == "abc"
    assert text.count(ANSI_RESET) == 3


def test_every_map_color_has_a_look() -> None:
    """Each color the provided maps use is known, or is rainbow."""
    paths = glob.glob("maps/*/*.txt") + ["maps/example.map"]
    colors = set()
    for path in paths:
        network, _ = Parser().parse_file(path)
        colors |= {
            zone.color.lower()
            for zone in network.zones.values()
            if zone.color is not None
        }
    assert colors - set(ANSI_COLORS) == {"rainbow"}


def test_show_network_describes_every_zone(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Role, type, capacity and entry cost, and each connection."""
    network, _ = Parser().parse_file("maps/example.map")
    TerminalVisualizer(use_color=False).show_network(network)
    out = capsys.readouterr().out

    assert "hub        start, normal, any number of drones" in out
    assert "roof1      restricted, holds 1, 2 turns to enter" in out
    assert "corridorA  priority, holds 2" in out
    assert "obstacleX  blocked: never entered" in out
    assert "corridorA-tunnelB (2)" in out


def test_show_turn_prints_the_line_then_the_zone_states(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Each turn: the exact movement line, then where everyone is."""
    _, simulator = _planned("maps/edge_restricted_end.map")
    simulator.run(TerminalVisualizer(use_color=False))

    assert capsys.readouterr().out.splitlines() == [
        "D1-a",
        "    turn 1 | s 1 waiting | a 1/1: D1 | e 0/2 delivered",
        "D1-a-e D2-a",
        "    turn 2 | s 0 waiting | a 1/1: D2 | D1 to e via a-e"
        " | e 0/2 delivered",
        "D1-e",
        "    turn 3 | s 0 waiting | a 1/1: D2 | e 1/2 delivered",
        "D2-a-e",
        "    turn 4 | s 0 waiting | D2 to e via a-e | e 1/2 delivered",
        "D2-e",
        "    turn 5 | s 0 waiting | e 2/2 delivered",
    ]


def test_show_summary_prints_whole_numbers_without_decimals(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """6 prints as 6, and 1.2 as 1.20."""
    TerminalVisualizer(use_color=False).show_summary(
        {"turns": 6, "drones moved per turn": 1.2}
    )
    assert capsys.readouterr().out.splitlines() == [
        "",
        "Summary",
        "  turns                  6",
        "  drones moved per turn  1.20",
    ]


def test_run_shows_every_turn_to_the_visualizer() -> None:
    """The hook sees turns 1, 2, 3... with the same lines run returns."""
    _, simulator = _planned("maps/example.map")
    recorder = RecordingVisualizer()

    lines = simulator.run(recorder)

    assert recorder.turns == list(enumerate(lines, start=1))


def test_metrics_of_a_planned_run() -> None:
    """3 drones on one link: arrivals 1, 2, 3; waits cost nothing."""
    _, simulator = _planned("maps/edge_start_to_end.map")
    simulator.run()

    assert [drone.arrival_turn for drone in simulator.drones] == [1, 2, 3]
    assert simulator.metrics() == {
        "turns": 3,
        "drones moved per turn": 1.0,
        "average turns per drone": 2.0,
        "total path cost": 3,
    }


def test_metrics_of_the_example_map() -> None:
    """16 moves in 6 turns; arrivals 3, 4, 4, 5, 6; costs 4 x 3 + 4.

    Four drones go hub-corridorA-tunnelB-goal (cost 3 each) and D3 goes
    through roof1 (restricted, so 2 + 1 + 1 = 4).
    """
    _, simulator = _planned("maps/example.map")
    simulator.run()

    assert simulator.metrics() == {
        "turns": 6,
        "drones moved per turn": pytest.approx(16 / 6),
        "average turns per drone": pytest.approx(22 / 5),
        "total path cost": 16,
    }


def test_terminal_run_keeps_the_exact_lines(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """On a terminal, the piped output's lines all appear, untouched."""
    assert main(["main.py", "maps/example.map"]) == 0
    piped = capsys.readouterr().out.splitlines()

    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert main(["main.py", "maps/example.map"]) == 0
    shown = capsys.readouterr().out.splitlines()

    movement = [line for line in shown if line.startswith("D")]
    assert movement == piped
    assert any(ANSI_CODE.search(line) for line in shown)
    assert "Summary" in _plain("\n".join(shown))
