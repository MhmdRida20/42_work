"""Abstract visualizer.

Kept decoupled from the simulator: the simulator feeds turn events to
a visualizer, so rendering never affects correctness. Concrete
visualizers (terminal, graphical) implement the hooks below.
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
