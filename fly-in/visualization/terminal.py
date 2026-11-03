"""Colored terminal visualizer using ANSI escape codes.

Before the run it lists the zones and connections. After each turn it
prints the movement line exactly as the subject defines it, then one
line of zone states: who waits in the start zone, who is in each busy
zone, who is still flying toward a restricted zone, and how many are
delivered. At the end it prints the secondary metrics. Zone names are
drawn in their map color.
"""

from __future__ import annotations

import textwrap

from models.drone import Drone
from models.network import Network
from models.zone import Zone
from visualization.visualizer import Visualizer

# 256-color codes for every color name the official maps use. Black is
# drawn on a light background so it stays readable on a dark terminal.
# Unknown names fall back to plain text: the subject allows any word.
ANSI_COLORS: dict[str, str] = {
    "black": "\033[30;47m",
    "blue": "\033[38;5;33m",
    "brown": "\033[38;5;130m",
    "crimson": "\033[38;5;161m",
    "cyan": "\033[38;5;51m",
    "darkred": "\033[38;5;124m",
    "gold": "\033[38;5;220m",
    "gray": "\033[38;5;245m",
    "green": "\033[38;5;40m",
    "lime": "\033[38;5;118m",
    "magenta": "\033[38;5;201m",
    "maroon": "\033[38;5;131m",
    "orange": "\033[38;5;208m",
    "purple": "\033[38;5;129m",
    "red": "\033[38;5;196m",
    "violet": "\033[38;5;177m",
    "yellow": "\033[38;5;226m",
}
# "rainbow" gives each letter the next of these colors.
RAINBOW = ["red", "orange", "yellow", "green", "blue", "violet"]
ANSI_BOLD = "\033[1m"
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
            color: A color name (any case), or None for no styling.

        Returns:
            The styled (or plain) string.
        """
        if not self.use_color or color is None:
            return text
        if color.lower() == "rainbow":
            return "".join(
                self.colorize(letter, RAINBOW[index % len(RAINBOW)])
                for index, letter in enumerate(text)
            )
        code = ANSI_COLORS.get(color.lower())
        if code is None:
            return text
        return f"{code}{text}{ANSI_RESET}"

    def show_network(self, network: Network) -> None:
        """Print every zone and connection, and how to read a turn."""
        zones = list(network.zones.values())
        connections = list(
            dict.fromkeys(
                connection
                for incident in network.adjacency.values()
                for connection in incident
            )
        )
        print(self._title(
            f"Network: {len(zones)} zones, {len(connections)} connections"
        ))
        width = max(len(zone.name) for zone in zones)
        for zone in zones:
            padding = " " * (width - len(zone.name))
            print(f"  {self._name(zone)}{padding}  "
                  f"{self._describe(zone, network)}")
        print(self._title("Connections (drones per turn)"))
        listed = ", ".join(
            f"{connection.name} ({connection.max_link_capacity})"
            for connection in connections
        )
        print(textwrap.fill(
            listed, width=79, initial_indent="  ", subsequent_indent="  "
        ))
        print(self._title("Each turn"))
        print("  The movement line, then the zone states: drones waiting in")
        print("  the start, each busy zone as used/max and its drones, the")
        print("  drones flying toward a restricted zone, and the deliveries.")
        print()

    def show_turn(self, turn_number: int, line: str, network: Network) -> None:
        """Print the movement line exactly, then the zone states."""
        print(line)
        total = sum(len(zone.occupants) for zone in network.zones.values())
        parts = [f"{self._name(network.start)} "
                 f"{len(self._inside(network.start))} waiting"]
        flying: list[str] = []
        for zone in network.zones.values():
            for drone in self._sorted(zone.occupants):
                if drone.position is not zone:
                    flying.append(f"{drone.label} to {self._name(zone)} "
                                  f"via {drone.position.name}")
            inside = self._inside(zone)
            if zone in (network.start, network.end) or not inside:
                continue
            labels = " ".join(drone.label for drone in inside)
            parts.append(f"{self._name(zone)} "
                         f"{len(inside)}/{zone.max_drones}: {labels}")
        parts.extend(flying)
        parts.append(f"{self._name(network.end)} "
                     f"{len(self._inside(network.end))}/{total} delivered")
        label = self.colorize(f"turn {turn_number}", "gray")
        print(f"    {label} | " + " | ".join(parts))

    def show_summary(self, metrics: dict[str, float]) -> None:
        """Print the secondary metrics, one per line."""
        print()
        print(self._title("Summary"))
        width = max(len(name) for name in metrics)
        for name, value in metrics.items():
            shown = (
                str(int(value)) if float(value).is_integer()
                else f"{value:.2f}"
            )
            print(f"  {name:<{width}}  {shown}")

    def _title(self, text: str) -> str:
        """Return ``text`` in bold when colors are on."""
        if not self.use_color:
            return text
        return f"{ANSI_BOLD}{text}{ANSI_RESET}"

    def _name(self, zone: Zone) -> str:
        """Return the zone's name in its map color."""
        return self.colorize(zone.name, zone.color)

    @staticmethod
    def _describe(zone: Zone, network: Network) -> str:
        """Return a zone's role, type, capacity and entry cost."""
        kind = type(zone).__name__.removesuffix("Zone").lower()
        if not zone.is_accessible:
            return f"{kind}: never entered"
        parts = [kind]
        if zone is network.start:
            parts.insert(0, "start")
        elif zone is network.end:
            parts.insert(0, "end")
        if zone.unlimited:
            parts.append("any number of drones")
        else:
            parts.append(f"holds {zone.max_drones}")
        if zone.entry_cost > 1:
            parts.append(f"{zone.entry_cost} turns to enter")
        return ", ".join(parts)

    @staticmethod
    def _sorted(drones: list[Drone]) -> list[Drone]:
        """Return the drones in id order."""
        return sorted(drones, key=lambda drone: drone.id)

    def _inside(self, zone: Zone) -> list[Drone]:
        """Return the drones really in ``zone``, in id order.

        ``occupants`` also holds the drones still flying toward the
        zone (their place is reserved), so compare positions.
        """
        return [d for d in self._sorted(zone.occupants) if d.position is zone]
