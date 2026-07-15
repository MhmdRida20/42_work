"""Colored terminal visualizer using ANSI escape codes.

Drives colors from each zone's ``color`` metadata and prints the
per-turn movement lines plus a summary of secondary metrics.
"""

from __future__ import annotations

from models.network import Network
from visualization.visualizer import Visualizer

# Minimal ANSI color map. Extend as needed; unknown colors fall back
# to no styling (the spec allows any single-word color).
ANSI_COLORS: dict[str, str] = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "gray": "\033[90m",
}
ANSI_RESET = "\033[0m"


class TerminalVisualizer(Visualizer):
    """Render the simulation as colored terminal output."""

    def __init__(self, use_color: bool = True) -> None:
        """Create the visualizer.

        Args:
            use_color: Disable to emit plain text (e.g. when piped).
        """
        self.use_color = use_color

    def colorize(self, text: str, color: str | None) -> str:
        """Wrap ``text`` in ANSI codes for ``color`` if enabled.

        Args:
            text: The text to style.
            color: A color name, or None for no styling.

        Returns:
            The styled (or plain) string.
        """
        if not self.use_color or color is None:
            return text
        code = ANSI_COLORS.get(color)
        if code is None:
            return text
        return f"{code}{text}{ANSI_RESET}"

    def show_network(self, network: Network) -> None:
        """Print the network layout and a color legend."""
        # TODO: list zones (colored by metadata) and their connections.
        raise NotImplementedError

    def show_turn(self, turn_number: int, line: str) -> None:
        """Print a single turn's movement line."""
        # TODO: format and print the turn, coloring drone tokens.
        raise NotImplementedError

    def show_summary(self, metrics: dict[str, float]) -> None:
        """Print end-of-run metrics (turns, drones/turn, avg, cost)."""
        # TODO: pretty-print the secondary metrics.
        raise NotImplementedError
