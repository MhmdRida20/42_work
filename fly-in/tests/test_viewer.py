"""Tests for the window: the GraphicalViewer, and what opens it.

The tests have no screen. SDL's "dummy" video driver opens windows
that exist in memory only, and the loop is driven by events posted
before it starts. Each loop test posts a QUIT last, so a broken key
can fail a test but never leave it running forever.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator

import pygame
import pytest

from models.network import Network
from parsing.errors import VisualizationError
from parsing.parser import Parser
from pathfinding.space_time import SpaceTimeFinder
from simulation.scheduler import Scheduler
from simulation.simulator import Simulator
from visualization.frames import Recorder
from visualization.graphical import GraphicalViewer, GraphicalVisualizer
from visualization.layout import DEFAULT_SIZE, Layout, Point
from visualization.playback import Playback
from visualization.visualizer import VisualizerGroup

RESTRICTED_END = "maps/edge_restricted_end.map"


@pytest.fixture
def no_screen(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Open windows in memory only, and close pygame after the test."""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    yield
    pygame.quit()


def _plan(map_path: str) -> tuple[Network, Simulator]:
    """Parse and plan ``map_path``; return its network and a simulator."""
    network, nb_drones = Parser().parse_file(map_path)
    routes = SpaceTimeFinder(nb_drones).find_paths(network)
    drones = Scheduler().assign(network, routes, nb_drones)
    return network, Simulator(network, drones)


def _viewer(map_path: str = RESTRICTED_END) -> GraphicalViewer:
    """Plan, run and record a map; return a viewer of the run."""
    network, simulator = _plan(map_path)
    recorder = Recorder()
    recorder.show_network(network)
    simulator.run(recorder)
    metrics = simulator.metrics()
    return GraphicalViewer(network, recorder.frames, map_path, metrics)


def _run(viewer: GraphicalViewer, *keys: int) -> None:
    """Run ``viewer``: ``keys`` are pressed, then the window is closed."""
    pygame.display.init()
    for key in keys:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    viewer.run()


def _press(viewer: GraphicalViewer, *keys: int) -> None:
    """Hand ``keys`` to the viewer, as the loop does; no window needed."""
    for key in keys:
        viewer.handle(pygame.event.Event(pygame.KEYDOWN, key=key))


class _OneTurnClock:
    """Stand in for pygame.time.Clock: each picture is a turn later."""

    def tick(self, framerate: float = 0) -> int:
        """Return 600 ms, one turn at x1, without waiting."""
        return 600


def test_the_loop_replays_the_run_until_the_window_closes(
    no_screen: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every turn is drawn, then the window is closed and pygame too.

    The stand-in clock makes each picture one turn later. The QUIT,
    posted with the fifth picture, is read on the next pass of the
    loop, which still draws once more.
    """
    viewer = _viewer()
    draw = viewer.renderer.draw
    drawn: list[float] = []

    def draw_and_quit_after_five(
        surface: pygame.Surface,
        layout: Layout,
        playback: Playback,
        mouse: Point | None = None,
    ) -> None:
        """Stand in for SceneRenderer.draw: draw and note the time."""
        draw(surface, layout, playback, mouse)
        drawn.append(playback.time)
        if len(drawn) == playback.last:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    monkeypatch.setattr(pygame.time, "Clock", _OneTurnClock)
    monkeypatch.setattr(viewer.renderer, "draw", draw_and_quit_after_five)
    viewer.run()

    assert drawn == [1, 2, 3, 4, 5, 5]
    assert not viewer.running
    assert not pygame.display.get_init()


def test_keys_pressed_in_the_window_reach_the_replay(no_screen: None) -> None:
    """Right twice: paused at the end of turn 2."""
    viewer = _viewer()
    _run(viewer, pygame.K_RIGHT, pygame.K_RIGHT)
    assert (viewer.playback.time, viewer.playback.playing) == (2, False)


def test_the_keys_drive_the_replay() -> None:
    """Each key, in order, and the replay's time, playing and speed.

    The replay starts playing at x1; any other key does nothing.
    """
    viewer = _viewer()
    playback = viewer.playback
    steps = [
        (pygame.K_SPACE, (0, False, 1)),
        (pygame.K_END, (5, False, 1)),
        (pygame.K_LEFT, (4, False, 1)),
        (pygame.K_HOME, (0, False, 1)),
        (pygame.K_RIGHT, (1, False, 1)),
        (pygame.K_UP, (1, False, 2)),
        (pygame.K_DOWN, (1, False, 1)),
        (pygame.K_r, (0, True, 1)),
        (pygame.K_a, (0, True, 1)),
    ]
    for key, expected in steps:
        _press(viewer, key)
        state = (playback.time, playback.playing, playback.speed)
        assert state == expected, key


def test_n_and_l_show_and_hide_the_names_and_the_legend() -> None:
    """Names on and legend off at first; each key flips one of them."""
    viewer = _viewer()
    renderer = viewer.renderer
    assert (renderer.show_names, renderer.show_legend) == (True, False)
    _press(viewer, pygame.K_n)
    assert (renderer.show_names, renderer.show_legend) == (False, False)
    _press(viewer, pygame.K_l)
    assert (renderer.show_names, renderer.show_legend) == (False, True)
    _press(viewer, pygame.K_n, pygame.K_l)
    assert (renderer.show_names, renderer.show_legend) == (True, False)


def test_escape_q_and_closing_the_window_stop_the_loop() -> None:
    """Each of the three stops a running loop."""
    viewer = _viewer()
    for event in (
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q),
        pygame.event.Event(pygame.QUIT),
    ):
        viewer.running = True
        viewer.handle(event)
        assert not viewer.running, pygame.event.event_name(event.type)


def test_a_resized_window_gets_a_new_layout() -> None:
    """The map is laid out again for the new size."""
    viewer = _viewer()
    assert (viewer.layout.width, viewer.layout.height) == DEFAULT_SIZE
    viewer.handle(pygame.event.Event(pygame.VIDEORESIZE, w=1000, h=700))
    assert (viewer.layout.width, viewer.layout.height) == (1000, 700)


def test_a_window_too_small_is_set_back_to_the_minimum(
    no_screen: None,
) -> None:
    """600 px wide is under the 800 px minimum: the window grows back."""
    viewer = _viewer()
    pygame.display.init()
    window = pygame.display.set_mode(DEFAULT_SIZE, pygame.RESIZABLE)
    viewer.handle(pygame.event.Event(pygame.VIDEORESIZE, w=600, h=700))
    assert window.get_size() == (800, 700)
    assert (viewer.layout.width, viewer.layout.height) == (800, 700)


def test_the_tooltip_needs_the_mouse_over_the_window(
    no_screen: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The mouse is handed to the renderer only while over the window."""
    seen: list[Point | None] = []
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (720, 390))
    for over_the_window in (True, False):
        viewer = _viewer()
        monkeypatch.setattr(
            viewer.renderer, "draw", lambda *args: seen.append(args[3])
        )
        monkeypatch.setattr(
            pygame.mouse, "get_focused", lambda: over_the_window
        )
        _run(viewer)
    assert seen == [(720, 390), None]


def test_no_screen_is_one_clean_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A display pygame cannot use: a VisualizationError, pygame closed."""
    monkeypatch.setenv("SDL_VIDEODRIVER", "no-such-driver")
    viewer = _viewer()
    with pytest.raises(VisualizationError, match="^cannot open a window: "):
        viewer.run()
    assert not pygame.display.get_init()


def test_ctrl_c_in_the_window_still_closes_pygame(
    no_screen: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ctrl+C goes on to main(), but pygame is closed on the way."""
    viewer = _viewer()

    def interrupted(*args: object) -> None:
        """Stand in for SceneRenderer.draw: Ctrl+C while drawing."""
        raise KeyboardInterrupt

    monkeypatch.setattr(viewer.renderer, "draw", interrupted)
    with pytest.raises(KeyboardInterrupt):
        viewer.run()
    assert not pygame.display.get_init()


def test_without_pygame_the_view_is_one_clean_error() -> None:
    """Importing the view with no pygame raises a VisualizationError.

    ``sys.modules["pygame"] = None`` makes ``import pygame`` fail as
    if pygame were not installed.
    """
    code = (
        "import sys; sys.modules['pygame'] = None; "
        "import visualization.graphical"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 1
    assert result.stderr.strip().endswith(
        "VisualizationError: "
        "the graphical view needs pygame-ce: run make install"
    )


def test_the_window_opens_only_once_the_run_is_over(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It records like a Recorder; the summary opens a window on that.

    GraphicalViewer.run is replaced, so no window opens: the test
    looks at the viewer that would have been shown.
    """
    opened: list[GraphicalViewer] = []
    monkeypatch.setattr(
        GraphicalViewer, "run", lambda viewer: opened.append(viewer)
    )
    network, simulator = _plan(RESTRICTED_END)
    recorder = Recorder()
    graphical = GraphicalVisualizer(network, RESTRICTED_END)
    group = VisualizerGroup([recorder, graphical])
    group.show_network(network)
    simulator.run(group)
    assert opened == []

    metrics = simulator.metrics()
    group.show_summary(metrics)
    assert len(opened) == 1
    viewer = opened[0]
    assert graphical.frames == recorder.frames
    assert viewer.playback.frames is graphical.frames
    assert viewer.renderer.title == RESTRICTED_END
    assert viewer.renderer.metrics == metrics
