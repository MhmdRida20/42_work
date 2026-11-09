"""Playback: the replay clock, and where each drone is at any moment.

The window replays the recorded frames. The clock counts time in
turns: 2.5 means that two turns are over and the third is half done.
Turn k is the animation from frame k-1 to frame k, 600 ms long at x1,
eased so that drones start and stop gently. Like frames.py and
layout.py, this module imports no pygame.
"""

from __future__ import annotations

import math

from visualization.frames import Frame
from visualization.layout import Layout, Point

TURN_MS = 600.0
MIN_SPEED = 0.25
MAX_SPEED = 8.0


class Playback:
    """The replay clock over the frames of one run.

    Attributes:
        frames: The recorded frames; frame 0 is before the first turn.
        last: The last turn, ``len(frames) - 1``.
        time: Turns played so far, from 0 to ``last``.
        playing: Whether :meth:`update` moves time on.
        speed: How many times faster than 600 ms a turn plays.
    """

    def __init__(self, frames: list[Frame]) -> None:
        """Start before the first turn, playing at x1.

        Args:
            frames: The frames of a run, as the Recorder kept them.
        """
        self.frames = frames
        self.last = len(frames) - 1
        self.time = 0.0
        self.playing = True
        self.speed = 1.0

    @property
    def turn(self) -> int:
        """Return the turn on screen: running, or just over."""
        return math.ceil(self.time)

    @property
    def progress(self) -> float:
        """Return how much of the turn on screen is done, from 0 to 1."""
        return self.time - self.turn + 1

    @property
    def settled(self) -> Frame:
        """Return the frame of the last turn that is over.

        Counters, slots and used/max are drawn from it, so they change
        when a turn's animation ends: paused, the screen shows exactly
        the state after the turn.
        """
        return self.frames[math.floor(self.time)]

    def update(self, elapsed_ms: float) -> None:
        """Move time on by ``elapsed_ms`` of real time, if playing.

        Args:
            elapsed_ms: The real time since the last update.
        """
        if self.playing:
            self.time += elapsed_ms * self.speed / TURN_MS
            if self.time >= self.last:
                self.time = float(self.last)
                self.playing = False

    def toggle(self) -> None:
        """Pause, or play; playing from the last turn restarts the run."""
        if self.playing:
            self.playing = False
        elif self.time == self.last:
            self.restart()
        else:
            self.playing = True

    def restart(self) -> None:
        """Play again from before the first turn."""
        self.time = 0.0
        self.playing = True

    def seek(self, turn: int) -> None:
        """Pause on the end of ``turn``, kept between 0 and the last."""
        self.time = float(max(0, min(turn, self.last)))
        self.playing = False

    def next_turn(self) -> None:
        """Pause on the next frame."""
        self.seek(math.floor(self.time) + 1)

    def previous_turn(self) -> None:
        """Pause on the previous frame."""
        self.seek(math.ceil(self.time) - 1)

    def faster(self) -> None:
        """Double the speed, up to x8."""
        self.speed = min(self.speed * 2, MAX_SPEED)

    def slower(self) -> None:
        """Halve the speed, down to x0.25."""
        self.speed = max(self.speed / 2, MIN_SPEED)

    def positions(self, layout: Layout) -> dict[int, Point]:
        """Return where each drone of the turn on screen is drawn now.

        During turn k a drone moves from its place in frame k-1, or
        from the start's center if it was waiting there, to its place
        in frame k. A drone without a pose in frame k rests in the
        start or the end: it is part of a counter, not drawn.

        Args:
            layout: The layout of the current window.

        Returns:
            Drone id -> the pixel at the center of its disc.
        """
        turn = self.turn
        if turn == 0:
            # Before the first move every drone waits in the start.
            return {}
        before = self._places(self.frames[turn - 1], layout)
        after = self._places(self.frames[turn], layout)
        start = layout.centers[layout.network.start.name]
        eased = self.ease(self.progress)
        return {
            drone: self._between(before.get(drone, start), place, eased)
            for drone, place in after.items()
        }

    @staticmethod
    def ease(t: float) -> float:
        """Return smoothstep of ``t``: slow near 0 and 1, 1/2 at 1/2."""
        return t * t * (3 - 2 * t)

    @staticmethod
    def _places(frame: Frame, layout: Layout) -> dict[int, Point]:
        """Return where each drone with a pose in ``frame`` is drawn.

        Inside a zone the drones take its slots by id: the lowest id
        gets slot 0. A flying drone is on its link.
        """
        places: dict[int, Point] = {}
        taken: dict[str, int] = {}
        for drone in sorted(frame.poses):
            pose = frame.poses[drone]
            if pose.link is not None:
                places[drone] = layout.on_link(
                    pose.link, pose.zone, pose.progress
                )
            else:
                rank = taken.get(pose.zone, 0)
                taken[pose.zone] = rank + 1
                places[drone] = layout.slot(pose.zone, rank)
        return places

    @staticmethod
    def _between(a: Point, b: Point, t: float) -> Point:
        """Return the point ``t`` of the way from ``a`` to ``b``."""
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
