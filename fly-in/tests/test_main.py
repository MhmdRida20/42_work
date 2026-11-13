"""Tests for main.py: its arguments, --visual, Ctrl+C and a closed pipe."""

from __future__ import annotations

import os
import subprocess
import sys

import pygame
import pytest

from main import main
from simulation.simulator import Simulator
from visualization.graphical import GraphicalViewer
from visualization.visualizer import Visualizer

EXAMPLE = "maps/example.map"


def _without_pygame(*args: str) -> subprocess.CompletedProcess[str]:
    """Run main.py with ``args`` in a Python that cannot import pygame.

    ``sys.modules["pygame"] = None`` makes ``import pygame`` fail as
    if pygame were not installed.
    """
    code = (
        "import sys; sys.modules['pygame'] = None; from main import main; "
        f"raise SystemExit(main(['main.py', *{list(args)!r}]))"
    )
    return subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )


def test_missing_map_argument_prints_usage(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without a map, argparse prints how to call it and exits with 2."""
    with pytest.raises(SystemExit) as stop:
        main(["main.py"])
    assert stop.value.code == 2
    err = capsys.readouterr().err
    assert err.startswith("usage: python main.py [-h] [--visual] map_file\n")
    assert "error: the following arguments are required: map_file" in err


def test_an_unknown_option_prints_usage(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A mistyped --visual is not taken for something else: exit 2."""
    with pytest.raises(SystemExit) as stop:
        main(["main.py", EXAMPLE, "--vision"])
    assert stop.value.code == 2
    assert "unrecognized arguments: --vision" in capsys.readouterr().err


def test_help_explains_both_arguments(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--help prints the usage and what each argument does: exit 0."""
    with pytest.raises(SystemExit) as stop:
        main(["main.py", "--help"])
    assert stop.value.code == 0
    out = capsys.readouterr().out
    assert "map_file" in out
    assert "replay the run in a window" in out


def test_visual_prints_every_line_before_the_window_opens(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Piped, --visual prints the very same lines, then opens the window.

    GraphicalViewer.run is replaced: it notes what had been printed by
    the time the window would open.
    """
    assert main(["main.py", EXAMPLE]) == 0
    plain = capsys.readouterr().out
    printed: list[str] = []

    def note_the_output(viewer: GraphicalViewer) -> None:
        """Stand in for GraphicalViewer.run: note what was printed."""
        printed.append(capsys.readouterr().out)

    monkeypatch.setattr(GraphicalViewer, "run", note_the_output)
    assert main(["main.py", EXAMPLE, "--visual"]) == 0
    assert printed == [plain]
    assert capsys.readouterr().out == ""


def test_the_lines_reach_the_reader_before_the_window_opens() -> None:
    """Piped, the lines are sent before the window opens, not after.

    Output to a pipe waits in a buffer. Here the window is replaced by
    ``os._exit``, which ends Python without emptying that buffer, so
    only the lines already sent reach the reader.
    """
    code = (
        "import os; from visualization.graphical import GraphicalViewer; "
        "GraphicalViewer.run = lambda viewer: os._exit(0); "
        f"from main import main; main(['main.py', '{EXAMPLE}', '--visual'])"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert len(result.stdout.splitlines()) == 6


def test_on_a_terminal_the_summary_comes_before_the_window(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The colored run and its summary are shown, then the window opens."""
    printed: list[str] = []

    def note_the_output(viewer: GraphicalViewer) -> None:
        """Stand in for GraphicalViewer.run: note what was printed."""
        printed.append(capsys.readouterr().out)

    monkeypatch.setattr(GraphicalViewer, "run", note_the_output)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert main(["main.py", EXAMPLE, "--visual"]) == 0
    assert len(printed) == 1
    assert "total path cost" in printed[0]


def test_visual_replays_in_a_window_until_it_is_closed(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """No stand-ins: the window opens, reads a QUIT, and main returns 0.

    SDL's dummy driver opens the window in memory only.
    """
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    assert main(["main.py", EXAMPLE, "--visual"]) == 0
    assert not pygame.display.get_init()
    assert len(capsys.readouterr().out.splitlines()) == 6


def test_visual_without_a_screen_is_one_error_line(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The lines are printed; the window can't open: one line, exit 1."""
    monkeypatch.setenv("SDL_VIDEODRIVER", "no-such-driver")
    assert main(["main.py", EXAMPLE, "--visual"]) == 1
    captured = capsys.readouterr()
    assert len(captured.out.splitlines()) == 6
    assert captured.err.startswith("error: cannot open a window: ")
    assert captured.err.count("\n") == 1


def test_without_pygame_a_plain_run_still_works() -> None:
    """A run without --visual never imports pygame."""
    result = _without_pygame(EXAMPLE)
    assert (result.returncode, result.stderr) == (0, "")
    assert len(result.stdout.splitlines()) == 6


def test_without_pygame_visual_is_one_error_line() -> None:
    """Nothing is printed but the cause and its fix: exit 1."""
    result = _without_pygame(EXAMPLE, "--visual")
    assert (result.returncode, result.stdout) == (1, "")
    assert result.stderr == (
        "error: the graphical view needs pygame-ce: run make install\n"
    )


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
