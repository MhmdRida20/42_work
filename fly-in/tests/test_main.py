"""Tests for main.py: a missing argument, Ctrl+C and a closed pipe."""

from __future__ import annotations

import os
import sys

import pytest

from main import main
from simulation.simulator import Simulator
from visualization.visualizer import Visualizer


def test_missing_map_argument_prints_usage(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without a map, main prints how to call it and exits with 1."""
    assert main(["main.py"]) == 1
    assert "usage: python main.py <map_file>" in capsys.readouterr().err


def test_ctrl_c_stops_without_a_traceback(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ctrl+C in the middle of a run: one short line, exit code 130."""

    def interrupted(
        self: Simulator, visualizer: Visualizer | None = None
    ) -> list[str]:
        """Stand in for Simulator.run: Ctrl+C during the run."""
        raise KeyboardInterrupt

    monkeypatch.setattr(Simulator, "run", interrupted)

    assert main(["main.py", "maps/example.map"]) == 130
    assert capsys.readouterr().err == "interrupted\n"


def test_closed_pipe_stops_quietly(
    capfd: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The reader of our output stopped early: no traceback, exit 1.

    main() then points stdout at the null device with ``os.dup2``.
    Doing that for real would also cut off pytest's own capture, so
    the test records the call instead.
    """

    def closed_pipe(
        self: Simulator, visualizer: Visualizer | None = None
    ) -> list[str]:
        """Stand in for Simulator.run: the reader closed the pipe."""
        raise BrokenPipeError

    redirected: list[int] = []
    monkeypatch.setattr(Simulator, "run", closed_pipe)
    monkeypatch.setattr(
        os, "dup2", lambda fd, target: redirected.append(target)
    )

    assert main(["main.py", "maps/example.map"]) == 1
    assert redirected == [sys.stdout.fileno()]
    assert capfd.readouterr().err == ""
