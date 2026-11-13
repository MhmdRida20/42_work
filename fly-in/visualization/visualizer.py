"""Abstract visualizer, and a group of visualizers shown as one.

Kept decoupled from the simulator: the simulator feeds turn events to
a visualizer, so rendering never affects correctness. Concrete
visualizers (terminal, graphical) implement the hooks below. A
VisualizerGroup lets several of them follow the same run.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.network import Network


class Visualizer(ABC):
    """Render simulation events. One method per lifecycle stage."""

    @abstractmethod
    def show_network(self, network: Network) -> None:
        """Display the parsed network before the simulation starts."""
        raise NotImplementedError

    @abstractmethod
    def show_turn(self, turn_number: int, line: str, network: Network) -> None:
        """Display one turn: its movements and the zone states after it.

        Args:
            turn_number: 1-based turn index.
            line: The formatted movement line for this turn.
            network: The network, read for where every drone now is.
        """
        raise NotImplementedError

    @abstractmethod
    def show_summary(self, metrics: dict[str, float]) -> None:
        """Display end-of-run metrics (turns, drones/turn, ...)."""
        raise NotImplementedError


class VisualizerGroup(Visualizer):
    """Several visualizers shown as one: each call goes to all of them.

    This is the Composite pattern: the simulator still talks to one
    visualizer, so the terminal view and the window can follow the
    same run without the simulator knowing there are two.

    Attributes:
        visualizers: The visualizers, called in this order.
    """

    def __init__(self, visualizers: list[Visualizer]) -> None:
        """Group ``visualizers``; each call reaches them in this order.

        Args:
            visualizers: The visualizers to call, first to last.
        """
        self.visualizers = visualizers

    def show_network(self, network: Network) -> None:
        """Show the network on every visualizer."""
        for visualizer in self.visualizers:
            visualizer.show_network(network)

    def show_turn(self, turn_number: int, line: str, network: Network) -> None:
        """Show one turn on every visualizer."""
        for visualizer in self.visualizers:
            visualizer.show_turn(turn_number, line, network)

    def show_summary(self, metrics: dict[str, float]) -> None:
        """Show the metrics on every visualizer, in order."""
        for visualizer in self.visualizers:
            visualizer.show_summary(metrics)
